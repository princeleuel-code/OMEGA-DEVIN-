"""
Walk-forward evaluation (purged) with anti-fraud guardrails.

This is intentionally lightweight (stdlib only) so the verifier can run without
extra tooling beyond the repo's core dependencies.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

import random

from .backtest import Backtester, BacktestConfig, BacktestResult
from .metrics import PerformanceMetrics
from ..data.loader import OHLCV
from ..evolution.genome import StrategyGenome


@dataclass
class WalkForwardConfig:
    # Windowing
    train_bars: int = 250
    test_bars: int = 125
    step_bars: Optional[int] = None  # Default: test_bars
    n_folds: int = 5
    purge_bars: int = 5

    # Fold gates
    min_trades_per_fold: int = 3
    max_no_trade_rate: float = 0.99

    # Aggregate gates
    min_folds_passed: int = 1
    min_avg_return_pct: float = 0.0
    max_worst_drawdown_pct: float = 15.0

    # Bootstrap confidence interval on avg return
    bootstrap_samples: int = 1000

    def __post_init__(self) -> None:
        if self.step_bars is None:
            self.step_bars = self.test_bars

        if self.train_bars <= 0:
            raise ValueError("train_bars must be > 0")
        if self.test_bars <= 0:
            raise ValueError("test_bars must be > 0")
        if self.step_bars <= 0:
            raise ValueError("step_bars must be > 0")
        if self.n_folds <= 0:
            raise ValueError("n_folds must be > 0")
        if self.purge_bars < 0:
            raise ValueError("purge_bars must be >= 0")


@dataclass
class WalkForwardFold:
    fold_id: int
    train_start: int
    train_end: int
    test_start: int
    test_end: int
    metrics: Dict[str, Any]
    passed: bool
    fail_reasons: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "fold_id": self.fold_id,
            "train_bars": self.train_end - self.train_start,
            "test_bars": self.test_end - self.test_start,
            "train_period": f"{self.train_start} -> {self.train_end}",
            "test_period": f"{self.test_start} -> {self.test_end}",
            "metrics": self.metrics,
            "passed": self.passed,
            "fail_reasons": self.fail_reasons,
        }


@dataclass
class WalkForwardReport:
    symbol: str
    timestamp: str
    total_bars: int
    config: Dict[str, Any]
    folds: List[WalkForwardFold]
    aggregate: Dict[str, Any]
    gate_results: Dict[str, bool]
    passed_all_gates: bool
    verdict: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "symbol": self.symbol,
            "timestamp": self.timestamp,
            "total_bars": self.total_bars,
            "config": self.config,
            "folds": [f.to_dict() for f in self.folds],
            "aggregate": self.aggregate,
            "gate_results": self.gate_results,
            "passed_all_gates": self.passed_all_gates,
            "verdict": self.verdict,
        }


def _bootstrap_ci(values: List[float], samples: int) -> Optional[Tuple[float, float]]:
    if not values:
        return None
    if samples <= 0:
        return None
    if len(values) == 1:
        return (values[0], values[0])

    means: List[float] = []
    n = len(values)
    for _ in range(samples):
        resample = [values[random.randrange(0, n)] for _ in range(n)]
        means.append(sum(resample) / n)

    means.sort()
    lo_idx = int(0.025 * (samples - 1))
    hi_idx = int(0.975 * (samples - 1))
    return (means[lo_idx], means[hi_idx])


def _fold_pass_fail(config: WalkForwardConfig, result: BacktestResult) -> Tuple[bool, List[str]]:
    fail: List[str] = []

    tm = result.trade_metrics
    pm = result.performance_metrics

    if tm.total_trades < config.min_trades_per_fold:
        fail.append(f"TRADES_{tm.total_trades}<{config.min_trades_per_fold}")

    if pm.no_trade_rate > config.max_no_trade_rate:
        fail.append(f"NO_TRADE_{pm.no_trade_rate * 100:.1f}%>{config.max_no_trade_rate * 100:.0f}%")

    return (len(fail) == 0), fail


def walk_forward(
    data: List[OHLCV],
    genome: StrategyGenome,
    backtest_config: BacktestConfig,
    wf_config: Optional[WalkForwardConfig] = None,
) -> WalkForwardReport:
    cfg = wf_config or WalkForwardConfig()

    # Anti-fraud: costs must be on for any "edge" claim.
    if backtest_config.spread_pips <= 0:
        raise ValueError("spread_pips must be > 0 (costs must be on)")

    folds: List[WalkForwardFold] = []

    returns_pct: List[float] = []
    sharpe: List[float] = []
    drawdowns: List[float] = []
    trades: List[int] = []
    win_rates: List[float] = []
    profit_factors: List[float] = []

    total = len(data)
    for fold_id in range(cfg.n_folds):
        start_idx = fold_id * cfg.step_bars
        train_end = start_idx + cfg.train_bars
        test_start = train_end + cfg.purge_bars
        test_end = test_start + cfg.test_bars

        if test_end > total:
            break

        train_slice = data[start_idx:train_end]
        purge_slice = data[train_end:test_start]
        test_slice = data[test_start:test_end]
        data_slice = train_slice + purge_slice + test_slice

        # Trade only during the test segment, but compute features with prior context.
        trade_start_bar = len(train_slice) + len(purge_slice)

        backtester = Backtester(config=backtest_config)
        result_full = backtester.run(data_slice, genome, create_manifest=False, trade_start_bar=trade_start_bar)

        # Recompute performance metrics using only the test-period equity curve.
        test_equity = result_full.equity_curve[trade_start_bar:]
        pm = PerformanceMetrics.from_equity_curve(
            equity=test_equity,
            trades=result_full.trades,
            initial_capital=test_equity[0] if test_equity else backtest_config.initial_capital,
            bars_per_day=backtest_config.bars_per_day,
        )
        pm.no_trade_decisions = result_full.no_trade_decisions
        pm.no_trade_rate = result_full.performance_metrics.no_trade_rate

        # Inject trimmed metrics back into a lightweight view.
        result_full.performance_metrics = pm

        fold_passed, fail_reasons = _fold_pass_fail(cfg, result_full)

        metrics = {
            "total_return_pct": pm.total_return_pct,
            "sharpe_ratio": pm.sharpe_ratio,
            "max_drawdown_pct": pm.max_drawdown_pct,
            "win_rate": result_full.trade_metrics.win_rate,
            "profit_factor": result_full.trade_metrics.profit_factor,
            "total_trades": result_full.trade_metrics.total_trades,
            "no_trade_rate": pm.no_trade_rate,
            "expectancy": result_full.trade_metrics.expectancy,
        }

        folds.append(
            WalkForwardFold(
                fold_id=fold_id,
                train_start=start_idx,
                train_end=train_end,
                test_start=test_start,
                test_end=test_end,
                metrics=metrics,
                passed=fold_passed,
                fail_reasons=fail_reasons,
            )
        )

        returns_pct.append(float(pm.total_return_pct))
        sharpe.append(float(pm.sharpe_ratio))
        drawdowns.append(float(pm.max_drawdown_pct))
        trades.append(int(result_full.trade_metrics.total_trades))
        win_rates.append(float(result_full.trade_metrics.win_rate))
        profit_factors.append(float(result_full.trade_metrics.profit_factor))

    folds_passed = sum(1 for f in folds if f.passed)
    avg_return = sum(returns_pct) / len(returns_pct) if returns_pct else 0.0
    avg_sharpe = sum(sharpe) / len(sharpe) if sharpe else 0.0
    avg_trades = sum(trades) / len(trades) if trades else 0.0
    avg_win_rate = sum(win_rates) / len(win_rates) if win_rates else 0.0
    worst_drawdown = max(drawdowns) if drawdowns else 0.0
    best_return = max(returns_pct) if returns_pct else 0.0
    worst_return = min(returns_pct) if returns_pct else 0.0
    worst_sharpe = min(sharpe) if sharpe else 0.0

    ci = _bootstrap_ci(returns_pct, cfg.bootstrap_samples)
    ci_lower, ci_upper = (ci if ci else (None, None))

    aggregate = {
        "avg_return": round(avg_return, 4),
        "avg_sharpe": round(avg_sharpe, 4),
        "avg_trades": round(avg_trades, 2),
        "avg_win_rate": round(avg_win_rate, 4),
        "avg_profit_factor": float("inf") if profit_factors and all(p == float("inf") for p in profit_factors) else round(sum(profit_factors) / len(profit_factors), 4) if profit_factors else 0.0,
        "best_return": round(best_return, 4),
        "worst_return": round(worst_return, 4),
        "worst_sharpe": round(worst_sharpe, 4),
        "worst_drawdown": round(worst_drawdown, 4),
        "total_folds": float(len(folds)),
        "folds_passed": float(folds_passed),
        "pass_rate": round(folds_passed / len(folds), 4) if folds else 0.0,
        "return_ci_lower": ci_lower,
        "return_ci_upper": ci_upper,
    }

    gate_results = {
        "min_folds_passed": folds_passed >= cfg.min_folds_passed,
        "min_avg_return": avg_return >= cfg.min_avg_return_pct,
        "max_worst_drawdown": worst_drawdown <= cfg.max_worst_drawdown_pct,
        "has_trades": sum(trades) > 0,
        "positive_expectation": avg_return > 0 and (sum(profit_factors) / len(profit_factors) if profit_factors else 0.0) > 1.0,
    }

    passed_all = all(gate_results.values()) if gate_results else False
    verdict = "PASSED" if passed_all else "FAILED: No reliable out-of-sample edge detected"

    return WalkForwardReport(
        symbol=backtest_config.symbol,
        timestamp=datetime.now(timezone.utc).isoformat(),
        total_bars=len(data),
        config={
            "n_folds": cfg.n_folds,
            "train_bars": cfg.train_bars,
            "test_bars": cfg.test_bars,
            "step_bars": cfg.step_bars,
            "purge_bars": cfg.purge_bars,
            "spread_pips": backtest_config.spread_pips,
            "slippage_pips": backtest_config.slippage_pips,
            "commission_per_lot": backtest_config.commission_per_lot,
        },
        folds=folds,
        aggregate=aggregate,
        gate_results=gate_results,
        passed_all_gates=passed_all,
        verdict=verdict,
    )
