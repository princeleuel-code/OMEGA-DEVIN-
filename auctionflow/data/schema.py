from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass(frozen=True)
class Candle:
    ts: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float


@dataclass(frozen=True)
class Quote:
    ts: datetime
    bid: float
    ask: float
    bid_sz: Optional[float] = None
    ask_sz: Optional[float] = None


@dataclass(frozen=True)
class TradePrint:
    ts: datetime
    price: float
    size: float
    aggressor: Optional[str] = None  # 'buy'|'sell' if known
