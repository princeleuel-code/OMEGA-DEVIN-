from __future__ import annotations

from dataclasses import dataclass
from typing import List, Literal

import numpy as np

from auctionflow.data.schema import Candle


@dataclass(frozen=True)
class AcceptanceResult:
    score: float  # 0..1
    outside_closes: int
    lookback: int


def in_value_area(price: float, *, val: float, vah: float) -> bool:
    return val <= price <= vah


def acceptance_score(
    candles: List[Candle],
    *,
    val: float,
    vah: float,
    direction: Literal["up","down"],
) -> AcceptanceResult:
    """Compute a simple acceptance score: are closes holding outside value?

    - Up breakout: closes > VAH
    - Down breakout: closes < VAL

    Score uses close-outside ratio and volume-outside ratio.
    """
    if not candles:
        return AcceptanceResult(0.0, 0, 0)

    closes = np.array([c.close for c in candles], dtype=float)
    vols = np.array([max(c.volume, 0.0) for c in candles], dtype=float)

    if direction == "up":
        outside = closes > vah
    else:
        outside = closes < val

    outside_count = int(outside.sum())
    close_ratio = outside_count / len(candles)

    total_v = float(vols.sum())
    outside_v = float(vols[outside].sum()) if total_v > 0 else 0.0
    vol_ratio = (outside_v / total_v) if total_v > 0 else 0.0

    score = 0.6 * close_ratio + 0.4 * vol_ratio
    score = float(np.clip(score, 0.0, 1.0))

    return AcceptanceResult(score=score, outside_closes=outside_count, lookback=len(candles))


def failed_auction(prev: Candle, cur: Candle, *, val: float, vah: float) -> bool:
    """A failed auction: price closes outside value then returns inside."""
    prev_out = (prev.close > vah) or (prev.close < val)
    cur_in = val <= cur.close <= vah
    return prev_out and cur_in
