"""
Tick Imbalance Bars (TIB).

This is a minimal, dependency-free builder that aggregates trades into bars
based on a signed tick imbalance threshold.

Reference concept:
- Trigger a new bar when buy/sell pressure becomes sufficiently imbalanced.

This module does not fetch trades; it only transforms an input trade tape.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List, Optional

from .vpin import Trade


@dataclass(frozen=True)
class ImbalanceBar:
    bar_id: int
    open: float
    high: float
    low: float
    close: float
    volume: float
    buy_ticks: int
    sell_ticks: int
    tick_imbalance: int  # buy_ticks - sell_ticks


def build_tick_imbalance_bars(
    trades: Iterable[Trade],
    *,
    imbalance_threshold: int,
    min_trades_per_bar: int = 1,
) -> List[ImbalanceBar]:
    """
    Build tick imbalance bars.

    Args:
        imbalance_threshold: absolute tick imbalance required to close a bar (must be > 0)
        min_trades_per_bar: guard against single-trade bars (must be >= 1)
    """
    if imbalance_threshold <= 0:
        raise ValueError("imbalance_threshold must be > 0")
    if min_trades_per_bar <= 0:
        raise ValueError("min_trades_per_bar must be >= 1")

    bars: List[ImbalanceBar] = []
    cur_open: Optional[float] = None
    cur_high: float = float("-inf")
    cur_low: float = float("inf")
    cur_close: Optional[float] = None
    cur_volume: float = 0.0
    buy_ticks = sell_ticks = 0
    n_trades = 0
    bar_id = 0

    def _reset() -> None:
        nonlocal cur_open, cur_high, cur_low, cur_close, cur_volume, buy_ticks, sell_ticks, n_trades
        cur_open = None
        cur_high = float("-inf")
        cur_low = float("inf")
        cur_close = None
        cur_volume = 0.0
        buy_ticks = 0
        sell_ticks = 0
        n_trades = 0

    def _emit() -> None:
        nonlocal bar_id
        assert cur_open is not None and cur_close is not None
        bars.append(
            ImbalanceBar(
                bar_id=bar_id,
                open=float(cur_open),
                high=float(cur_high),
                low=float(cur_low),
                close=float(cur_close),
                volume=float(cur_volume),
                buy_ticks=int(buy_ticks),
                sell_ticks=int(sell_ticks),
                tick_imbalance=int(buy_ticks - sell_ticks),
            )
        )
        bar_id += 1
        _reset()

    for t in trades:
        if t.size <= 0:
            continue

        if cur_open is None:
            cur_open = t.price
            cur_high = t.price
            cur_low = t.price

        cur_high = max(cur_high, t.price)
        cur_low = min(cur_low, t.price)
        cur_close = t.price
        cur_volume += t.size
        n_trades += 1

        if t.is_buy:
            buy_ticks += 1
        else:
            sell_ticks += 1

        imbalance = buy_ticks - sell_ticks
        if n_trades >= min_trades_per_bar and abs(imbalance) >= imbalance_threshold:
            _emit()

    return bars

