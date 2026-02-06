"""
VPIN (Volume-synchronized Probability of Informed Trading).

This implementation is designed for deterministic, dependency-free usage.

Notes:
- VPIN requires trade direction classification (buy-initiated vs sell-initiated).
  If the classification is synthetic/estimated, the result must be Tier C and
  must not gate trading decisions (see provenance firewall).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List, Optional


@dataclass(frozen=True)
class Trade:
    """
    Minimal trade event for VPIN.

    `is_buy` should represent aggressor side:
    - True: buy-initiated trade (buyer is taker)
    - False: sell-initiated trade (seller is taker)
    """

    price: float
    size: float
    is_buy: bool


@dataclass(frozen=True)
class VolumeBucket:
    bucket_id: int
    buy_volume: float
    sell_volume: float
    total_volume: float

    @property
    def imbalance(self) -> float:
        # Absolute imbalance normalized by bucket volume, range [0, 1].
        if self.total_volume <= 0:
            return 0.0
        return abs(self.buy_volume - self.sell_volume) / self.total_volume


def build_volume_buckets(trades: Iterable[Trade], *, bucket_volume: float) -> List[VolumeBucket]:
    """
    Split trades into fixed-volume buckets.

    Args:
        bucket_volume: target volume per bucket (must be > 0).
    """
    if bucket_volume <= 0:
        raise ValueError("bucket_volume must be > 0")

    buckets: List[VolumeBucket] = []
    buy = sell = total = 0.0
    bucket_id = 0

    def _emit() -> None:
        nonlocal buy, sell, total, bucket_id
        buckets.append(
            VolumeBucket(
                bucket_id=bucket_id,
                buy_volume=buy,
                sell_volume=sell,
                total_volume=total,
            )
        )
        bucket_id += 1
        buy = sell = total = 0.0

    for t in trades:
        if t.size <= 0:
            continue
        remaining = float(t.size)
        while remaining > 0:
            need = bucket_volume - total
            take = remaining if remaining <= need else need

            if t.is_buy:
                buy += take
            else:
                sell += take
            total += take
            remaining -= take

            if total >= bucket_volume - 1e-12:
                _emit()

    # Drop trailing partial bucket (common in streaming) to avoid bias.
    return buckets


def vpin_from_buckets(buckets: List[VolumeBucket], *, window_buckets: int) -> Optional[float]:
    """
    Compute VPIN as the mean bucket imbalance over a rolling window.
    Returns None if there are not enough buckets.
    """
    if window_buckets <= 0:
        raise ValueError("window_buckets must be > 0")
    if len(buckets) < window_buckets:
        return None
    window = buckets[-window_buckets:]
    return sum(b.imbalance for b in window) / window_buckets


def compute_vpin(
    trades: Iterable[Trade],
    *,
    bucket_volume: float,
    window_buckets: int,
) -> Optional[float]:
    buckets = build_volume_buckets(trades, bucket_volume=bucket_volume)
    return vpin_from_buckets(buckets, window_buckets=window_buckets)

