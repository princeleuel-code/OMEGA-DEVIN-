from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional

import numpy as np

from auctionflow.data.schema import Candle
from auctionflow.engine.reasons import ReasonCode
from auctionflow.engine.veto import RiskConfig, VetoState, rr, veto
from auctionflow.strategy.signals import Signal, StrategyConfig, generate_signal
from auctionflow.utils.logging import log_jsonl


@dataclass
class TradeResult:
    ts_entry: str
    ts_exit: str
    kind: str
    side: str
    entry: float
    stop: float
    target: float
    exit: float
    outcome: str  # 'target'|'stop'|'timeout'
    r: float
    tags: List[str]


@dataclass
class BacktestSummary:
    trades: int
    win_rate: float
    avg_r: float
    total_r: float
    max_drawdown_r: float


def run_backtest(
    candles: List[Candle],
    *,
    strat: StrategyConfig = StrategyConfig(),
    risk: RiskConfig = RiskConfig(),
    log_path: Optional[str | Path] = None,
    timeout_bars: int = 120,
) -> Dict:
    state = VetoState()
    trade_results: List[TradeResult] = []

    equity = 0.0
    peak = 0.0
    max_dd = 0.0

    for i in range(0, len(candles)):
        if i < strat.session_lookback_candles + 5:
            continue

        window = candles[: i + 1]
        sig = generate_signal(window, strat)
        if sig is None:
            continue

        allowed, reasons = veto(sig, candles=window, state=state, cfg=risk)
        if not allowed:
            if log_path:
                log_jsonl(
                    log_path,
                    {
                        "action": ReasonCode.SKIP.value,
                        "ts": window[-1].ts.isoformat(),
                        "signal": sig.__dict__,
                        "reasons": reasons,
                    },
                )
            continue

        # Simulate trade forward
        entry_idx = i
        entry = sig.entry
        stop = sig.stop
        target = sig.target
        side = sig.side

        outcome = "timeout"
        exit_price = candles[min(i + 1, len(candles) - 1)].open
        exit_ts = candles[min(i + 1, len(candles) - 1)].ts

        for j in range(i + 1, min(len(candles), i + 1 + timeout_bars)):
            c = candles[j]
            if side == "long":
                if c.low <= stop:
                    outcome = "stop"
                    exit_price = stop
                    exit_ts = c.ts
                    break
                if c.high >= target:
                    outcome = "target"
                    exit_price = target
                    exit_ts = c.ts
                    break
            else:
                if c.high >= stop:
                    outcome = "stop"
                    exit_price = stop
                    exit_ts = c.ts
                    break
                if c.low <= target:
                    outcome = "target"
                    exit_price = target
                    exit_ts = c.ts
                    break

        this_rr = rr(entry, stop, target)
        r = this_rr if outcome == "target" else (-1.0 if outcome == "stop" else 0.0)

        trade_results.append(
            TradeResult(
                ts_entry=candles[entry_idx].ts.isoformat(),
                ts_exit=exit_ts.isoformat(),
                kind=sig.kind,
                side=side,
                entry=entry,
                stop=stop,
                target=target,
                exit=exit_price,
                outcome=outcome,
                r=float(r),
                tags=list(sig.tags),
            )
        )

        # Update risk state
        state.trades_today += 1
        state.daily_r += float(r)

        # Equity/drawdown in R
        equity += float(r)
        peak = max(peak, equity)
        dd = equity - peak
        max_dd = min(max_dd, dd)

        if log_path:
            log_jsonl(
                log_path,
                {
                    "action": ReasonCode.TRADE.value,
                    "ts": candles[entry_idx].ts.isoformat(),
                    "signal": sig.__dict__,
                    "result": trade_results[-1].__dict__,
                },
            )

    summary = _summarize(trade_results, max_dd)
    return {
        "summary": summary.__dict__,
        "trades": [t.__dict__ for t in trade_results],
    }


def _summarize(trades: List[TradeResult], max_dd: float) -> BacktestSummary:
    n = len(trades)
    if n == 0:
        return BacktestSummary(0, 0.0, 0.0, 0.0, 0.0)
    wins = sum(1 for t in trades if t.outcome == "target")
    total_r = float(sum(t.r for t in trades))
    avg_r = total_r / n
    return BacktestSummary(
        trades=n,
        win_rate=wins / n,
        avg_r=avg_r,
        total_r=total_r,
        max_drawdown_r=float(max_dd),
    )
