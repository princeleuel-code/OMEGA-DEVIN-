from __future__ import annotations

from dataclasses import dataclass
from typing import List, Tuple

import numpy as np

from auctionflow.data.schema import Candle


@dataclass(frozen=True)
class ProfileConfig:
    tick_size: float = 0.25
    value_area_pct: float = 0.70
    smooth_window: int = 3


@dataclass
class VolumeProfile:
    prices: np.ndarray            # bin centers
    volume: np.ndarray            # total volume per bin
    poc: float                    # price of max volume
    val: float                    # value area low
    vah: float                    # value area high
    total_volume: float


def build_volume_profile(candles: List[Candle], cfg: ProfileConfig) -> VolumeProfile:
    """Build a proxy volume-by-price profile from OHLCV candles.

    Note: With only OHLCV, we can't know the exact price-level volume.
    This function uses a robust proxy (uniform volume distribution across the candle range).
    """
    if not candles:
        raise ValueError("No candles")

    lo = min(c.low for c in candles)
    hi = max(c.high for c in candles)

    if cfg.tick_size <= 0:
        raise ValueError("tick_size must be > 0")

    # Build bins
    start = np.floor(lo / cfg.tick_size) * cfg.tick_size
    end = np.ceil(hi / cfg.tick_size) * cfg.tick_size
    prices = np.arange(start, end + cfg.tick_size, cfg.tick_size)

    vol = np.zeros_like(prices, dtype=float)

    for c in candles:
        if c.high <= c.low:
            # treat as single print at close
            idx = int(round((c.close - start) / cfg.tick_size))
            if 0 <= idx < len(vol):
                vol[idx] += c.volume
            continue

        a = int(np.floor((c.low - start) / cfg.tick_size))
        b = int(np.ceil((c.high - start) / cfg.tick_size))
        a = max(a, 0)
        b = min(b, len(vol) - 1)
        n = max(1, b - a + 1)
        vol[a : b + 1] += c.volume / n

    total = float(vol.sum())
    if total <= 0:
        raise ValueError("Total volume <= 0")

    poc_idx = int(np.argmax(vol))
    poc = float(prices[poc_idx])

    val, vah = _compute_value_area(prices, vol, cfg.value_area_pct)

    return VolumeProfile(
        prices=prices,
        volume=vol,
        poc=poc,
        val=val,
        vah=vah,
        total_volume=total,
    )


def _compute_value_area(prices: np.ndarray, vol: np.ndarray, pct: float) -> Tuple[float, float]:
    """Classic value area: start at POC and expand outward by highest-volume bins until pct reached."""
    if not (0 < pct < 1):
        raise ValueError("value_area_pct must be between 0 and 1")

    total = vol.sum()
    target = total * pct

    poc_i = int(np.argmax(vol))
    included = set([poc_i])
    cum = vol[poc_i]

    left = poc_i - 1
    right = poc_i + 1

    # expand outward picking the side with higher adjacent volume
    while cum < target and (left >= 0 or right < len(vol)):
        v_left = vol[left] if left >= 0 else -1
        v_right = vol[right] if right < len(vol) else -1

        if v_right > v_left:
            if right < len(vol):
                included.add(right)
                cum += vol[right]
                right += 1
            else:
                included.add(left)
                cum += vol[left]
                left -= 1
        else:
            if left >= 0:
                included.add(left)
                cum += vol[left]
                left -= 1
            else:
                included.add(right)
                cum += vol[right]
                right += 1

    idxs = sorted(included)
    return float(prices[idxs[0]]), float(prices[idxs[-1]])
