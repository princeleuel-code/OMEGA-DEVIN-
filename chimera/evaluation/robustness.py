"""
Adversarial Robustness Suite (anti-overfit).

This module provides:
- Permutation tests (shuffle return ordering to form a null distribution)
- A lightweight "Reality Check" style bootstrap-max procedure for multiple strategies
- Regime stress test scaffolding (scenario-based)

All functions are dependency-free and deterministic given a seed.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Dict, Iterable, List, Optional, Sequence, Tuple

import math
import random

from chimera.data.loader import OHLCV
from chimera.evaluation.backtest import Backtester, BacktestConfig
from chimera.evolution.genome import StrategyGenome


MetricFn = Callable[[Sequence[float]], float]


def mean(xs: Sequence[float]) -> float:
    if not xs:
        return 0.0
    return sum(xs) / len(xs)


def stdev(xs: Sequence[float]) -> float:
    if len(xs) < 2:
        return 0.0
    m = mean(xs)
    var = sum((x - m) ** 2 for x in xs) / (len(xs) - 1)
    return math.sqrt(var)


def sharpe_ratio(returns: Sequence[float], *, eps: float = 1e-12) -> float:
    """
    Un-annualized Sharpe: mean / std. This is for permutation comparisons only.
    """
    sd = stdev(returns)
    if sd <= eps:
        return 0.0
    return mean(returns) / sd


def _p_value_one_sided(null: Sequence[float], observed: float) -> float:
    # Plus-one correction for finite Monte Carlo.
    ge = sum(1 for x in null if x >= observed)
    return (ge + 1) / (len(null) + 1)


def permutation_test(
    values: Sequence[float],
    *,
    metric: MetricFn = mean,
    permutations: int = 1000,
    seed: int = 1337,
) -> Dict[str, object]:
    """
    Permutation test by shuffling ordering.

    Returns:
        dict with observed, p_value, and null_summary.
    """
    if permutations <= 0:
        raise ValueError("permutations must be > 0")
    rng = random.Random(seed)

    base = list(values)
    obs = float(metric(base))

    null: List[float] = []
    work = base[:]
    for _ in range(permutations):
        rng.shuffle(work)
        null.append(float(metric(work)))

    p = _p_value_one_sided(null, obs)
    null_sorted = sorted(null)
    return {
        "observed": obs,
        "p_value": p,
        "null_mean": mean(null_sorted),
        "null_p05": null_sorted[int(0.05 * (len(null_sorted) - 1))],
        "null_p95": null_sorted[int(0.95 * (len(null_sorted) - 1))],
    }


def permute_ohlcv_returns(
    bars: Sequence[OHLCV],
    *,
    seed: int,
) -> List[OHLCV]:
    """
    Create a null series by shuffling close-to-close returns and reconstructing OHLC.

    This preserves:
    - marginal return distribution
    - timestamps
    - candle shape proportions (via per-bar scaling)

    It destroys temporal ordering, which is the point of the null hypothesis.
    """
    n = len(bars)
    if n <= 2:
        return list(bars)

    closes = [b.close for b in bars]
    rets = [(closes[i] / closes[i - 1] - 1.0) for i in range(1, n)]

    rng = random.Random(seed)
    perm = rets[:]
    rng.shuffle(perm)

    out: List[OHLCV] = []
    out.append(bars[0])
    prev_close = bars[0].close

    for i in range(1, n):
        r = perm[i - 1]
        new_close = prev_close * (1.0 + r)

        base_close = bars[i].close
        scale = (new_close / base_close) if abs(base_close) > 1e-12 else 1.0

        o = bars[i].open * scale
        h = bars[i].high * scale
        l = bars[i].low * scale
        c = new_close

        # Ensure candle consistency.
        h = max(h, o, c)
        l = min(l, o, c)

        out.append(
            OHLCV(
                timestamp=bars[i].timestamp,
                open=float(o),
                high=float(h),
                low=float(l),
                close=float(c),
                volume=float(bars[i].volume),
                symbol=bars[i].symbol,
            )
        )
        prev_close = new_close

    return out


def _equity_returns(equity_curve: Sequence[float]) -> List[float]:
    rets: List[float] = []
    for i in range(1, len(equity_curve)):
        prev = equity_curve[i - 1]
        cur = equity_curve[i]
        if prev == 0:
            rets.append(0.0)
        else:
            rets.append((cur - prev) / prev)
    return rets


@dataclass(frozen=True)
class RealityCheckResult:
    observed_best_metric: float
    p_value: float
    strategies: int
    bootstrap_samples: int


def reality_check_bootstrap_max(
    strategy_returns: Sequence[Sequence[float]],
    *,
    metric: MetricFn = mean,
    bootstrap_samples: int = 1000,
    seed: int = 1337,
) -> RealityCheckResult:
    """
    Lightweight White's Reality Check style procedure:
    - compute observed best metric across strategies
    - bootstrap time indices with replacement
    - for each sample, compute best metric across strategies
    - p-value: proportion of bootstrap best >= observed best

    This is not a full WRC implementation (no centering by benchmark),
    but it is a practical multiple-testing guardrail.
    """
    if bootstrap_samples <= 0:
        raise ValueError("bootstrap_samples must be > 0")
    if not strategy_returns:
        raise ValueError("strategy_returns must be non-empty")

    lens = {len(r) for r in strategy_returns}
    if len(lens) != 1:
        raise ValueError("all strategy return series must have the same length")

    n = next(iter(lens))
    if n == 0:
        return RealityCheckResult(observed_best_metric=0.0, p_value=1.0, strategies=len(strategy_returns), bootstrap_samples=bootstrap_samples)

    observed = max(float(metric(r)) for r in strategy_returns)

    rng = random.Random(seed)
    null_best: List[float] = []
    for _ in range(bootstrap_samples):
        idx = [rng.randrange(0, n) for _ in range(n)]
        best = float("-inf")
        for r in strategy_returns:
            sample = [r[i] for i in idx]
            best = max(best, float(metric(sample)))
        null_best.append(best)

    p = _p_value_one_sided(null_best, observed)
    return RealityCheckResult(
        observed_best_metric=observed,
        p_value=p,
        strategies=len(strategy_returns),
        bootstrap_samples=bootstrap_samples,
    )


def robustness_report(
    *,
    bars: Sequence[OHLCV],
    genome: StrategyGenome,
    backtest_config: BacktestConfig,
    permutations: int = 200,
    seed: int = 1337,
) -> Dict[str, object]:
    """
    Convenience wrapper that runs:
    - observed backtest
    - permutation test over return-shuffled OHLCV series
    """
    backtester = Backtester(config=backtest_config)
    observed = backtester.run(list(bars), genome, create_manifest=False)
    obs_return = float(observed.performance_metrics.total_return_pct)
    obs_rets = _equity_returns(observed.equity_curve)

    null_returns: List[float] = []
    for i in range(permutations):
        perm_bars = permute_ohlcv_returns(bars, seed=seed + i)
        perm_res = backtester.run(perm_bars, genome, create_manifest=False)
        null_returns.append(float(perm_res.performance_metrics.total_return_pct))

    p = _p_value_one_sided(null_returns, obs_return)
    return {
        "observed": {
            "total_return_pct": obs_return,
            "sharpe_like": sharpe_ratio(obs_rets),
            "trades": int(observed.trade_metrics.total_trades),
        },
        "permutation_null": {
            "permutations": permutations,
            "p_value_return": p,
            "null_mean_return_pct": mean(null_returns),
            "null_p05_return_pct": sorted(null_returns)[int(0.05 * (len(null_returns) - 1))],
            "null_p95_return_pct": sorted(null_returns)[int(0.95 * (len(null_returns) - 1))],
        },
    }

