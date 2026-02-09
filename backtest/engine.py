from __future__ import annotations

from dataclasses import asdict
from datetime import datetime
from typing import Any, Dict, List, Optional

import pandas as pd

from chimera.data.loader import OHLCV
from chimera.evaluation.backtest import Backtester, BacktestConfig, BacktestResult
from chimera.evolution.genome import StrategyGenome


def symbol_backtest_config(
    *,
    symbol: str,
    initial_capital: float = 10_000.0,
    spread_pips: float = 1.0,
    slippage_pips: float = 0.5,
    commission_per_lot: float = 0.0,
) -> BacktestConfig:
    """Return a BacktestConfig with symbol-specific pip sizing defaults."""

    pip_size = 0.0001
    pip_value = 10.0
    bars_per_day = 24.0  # for hourly bars by default

    # Heuristic symbol overrides for demo/simulation.
    if symbol.upper().endswith("JPY"):
        pip_size = 0.01
        pip_value = 10.0
    if symbol.upper() == "XAUUSD":
        # "Pips" are non-standard for metals; use a reasonable scale for simulation.
        pip_size = 0.01
        pip_value = 1.0

    return BacktestConfig(
        initial_capital=float(initial_capital),
        spread_pips=float(spread_pips),
        commission_per_lot=float(commission_per_lot),
        slippage_pips=float(slippage_pips),
        pip_value=float(pip_value),
        bars_per_day=float(bars_per_day),
        symbol=str(symbol),
        pip_size=float(pip_size),
    )


def df_to_ohlcv(df: pd.DataFrame, *, symbol: str) -> List[OHLCV]:
    if df.empty:
        return []
    if not isinstance(df.index, pd.DatetimeIndex):
        raise ValueError("OHLCV DataFrame must be indexed by timestamp")

    out: List[OHLCV] = []
    for ts, row in df.iterrows():
        ts_dt = ts.to_pydatetime()
        out.append(
            OHLCV(
                timestamp=ts_dt,
                open=float(row["open"]),
                high=float(row["high"]),
                low=float(row["low"]),
                close=float(row["close"]),
                volume=float(row.get("volume", 0.0)),
                symbol=str(symbol),
            )
        )
    return out


def run_backtest(
    *,
    bars: pd.DataFrame,
    genome: StrategyGenome,
    config: BacktestConfig,
    create_manifest: bool = True,
    trade_start_bar: int = 0,
) -> BacktestResult:
    data = df_to_ohlcv(bars, symbol=config.symbol)
    backtester = Backtester(config=config)
    return backtester.run(
        data,
        genome,
        create_manifest=create_manifest,
        trade_start_bar=int(trade_start_bar),
    )


def backtest_summary(result: BacktestResult) -> Dict[str, Any]:
    return {
        "genome_id": result.genome_id,
        "trade_count": len(result.trades),
        "final_equity": float(result.equity_curve[-1]) if result.equity_curve else 0.0,
        "trade_metrics": result.trade_metrics.to_dict(),
        "performance_metrics": result.performance_metrics.to_dict(),
        "total_decisions": int(result.total_decisions),
        "no_trade_rate": float(result.no_trade_decisions / result.total_decisions) if result.total_decisions else 0.0,
        "config": dict(result.config),
    }

