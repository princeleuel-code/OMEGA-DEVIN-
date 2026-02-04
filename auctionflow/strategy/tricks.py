from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Tuple

from auctionflow.data.schema import Candle


@dataclass(frozen=True)
class Sweep:
    kind: str  # 'sweep_high'|'sweep_low'
    level: float


def detect_liquidity_sweep(candles: List[Candle], *, lookback: int = 20) -> Optional[Sweep]:
    """Detect a simple sweep: current candle wicks past prior extreme then closes back inside."""
    if len(candles) < lookback + 1:
        return None
    cur = candles[-1]
    prev = candles[-(lookback+1):-1]
    prior_high = max(c.high for c in prev)
    prior_low = min(c.low for c in prev)

    if cur.high > prior_high and cur.close < prior_high:
        return Sweep("sweep_high", prior_high)
    if cur.low < prior_low and cur.close > prior_low:
        return Sweep("sweep_low", prior_low)
    return None


def detect_fvg(candles: List[Candle]) -> Optional[Tuple[str, float, float]]:
    """3-candle Fair Value Gap proxy.

    Returns (kind, low, high) where kind in {'bull_fvg','bear_fvg'}.
    bull: candle1 high < candle3 low
    bear: candle1 low > candle3 high
    """
    if len(candles) < 3:
        return None
    c1, c2, c3 = candles[-3], candles[-2], candles[-1]
    if c1.high < c3.low:
        return ("bull_fvg", c1.high, c3.low)
    if c1.low > c3.high:
        return ("bear_fvg", c3.high, c1.low)
    return None


def detect_bos(candles: List[Candle], *, lookback: int = 50) -> Optional[str]:
    """Break of structure proxy: close breaks above prior high or below prior low."""
    if len(candles) < lookback + 1:
        return None
    cur = candles[-1]
    prev = candles[-(lookback+1):-1]
    prior_high = max(c.high for c in prev)
    prior_low = min(c.low for c in prev)
    if cur.close > prior_high:
        return "bos_up"
    if cur.close < prior_low:
        return "bos_down"
    return None
