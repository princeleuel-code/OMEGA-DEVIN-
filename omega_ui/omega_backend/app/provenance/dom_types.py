"""
DOM (Depth of Market) data structures.

Kept dependency-free so the rest of the backend can import DOM types even when
optional websocket/provider dependencies are not installed.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


@dataclass(frozen=True)
class DOMLevel:
    """A single price level in an order book snapshot."""

    price: float
    size: float
    is_bid: bool
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "price": self.price,
            "size": self.size,
            "is_bid": self.is_bid,
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass(frozen=True)
class RealDOMSnapshot:
    """
    Normalized DOM snapshot (Tier A when sourced from a real provider).

    Note: provenance tiering is enforced by the firewall/provider registry, not
    by this structure.
    """

    symbol: str
    venue: str
    timestamp: datetime
    bids: List[DOMLevel]
    asks: List[DOMLevel]
    spread: float
    mid_price: float
    book_imbalance: float
    total_bid_size: float
    total_ask_size: float
    liquidity_walls: List[DOMLevel]
    is_real: bool = True

    def age_seconds(self, now: Optional[datetime] = None) -> float:
        now_dt = now or datetime.now(timezone.utc)
        ts = self.timestamp
        if ts.tzinfo is None:
            # Be tolerant of legacy naive timestamps.
            ts = ts.replace(tzinfo=timezone.utc)
        return (now_dt - ts).total_seconds()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "symbol": self.symbol,
            "venue": self.venue,
            "timestamp": self.timestamp.isoformat(),
            "bids": [b.to_dict() for b in self.bids],
            "asks": [a.to_dict() for a in self.asks],
            "spread": self.spread,
            "mid_price": self.mid_price,
            "book_imbalance": self.book_imbalance,
            "total_bid_size": self.total_bid_size,
            "total_ask_size": self.total_ask_size,
            "liquidity_walls": [l.to_dict() for l in self.liquidity_walls],
            "is_real": self.is_real,
            "watermark": None if self.is_real else "SYNTHETIC / EDUCATIONAL ONLY",
        }

