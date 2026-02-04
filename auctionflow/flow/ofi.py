from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from auctionflow.data.schema import Quote


@dataclass(frozen=True)
class OFIResult:
    ofi: float
    details: str


def ofi_from_quotes(quotes: List[Quote]) -> Optional[OFIResult]:
    """Basic OFI proxy using best bid/ask changes.

    Needs bid_sz/ask_sz. If sizes are missing, returns None.
    Interpretation:
      +OFI => net buying pressure, -OFI => net selling pressure.
    """
    if len(quotes) < 2:
        return None
    if any(q.bid_sz is None or q.ask_sz is None for q in quotes):
        return None

    ofi = 0.0
    for prev, cur in zip(quotes[:-1], quotes[1:]):
        # Bid-side contribution
        if cur.bid > prev.bid:
            ofi += float(cur.bid_sz)  # new higher bid: add size
        elif cur.bid == prev.bid:
            ofi += float(cur.bid_sz) - float(prev.bid_sz)
        # Ask-side contribution
        if cur.ask < prev.ask:
            ofi -= float(cur.ask_sz)  # new lower ask: subtract size
        elif cur.ask == prev.ask:
            ofi -= float(cur.ask_sz) - float(prev.ask_sz)

    return OFIResult(ofi=ofi, details=f"n={len(quotes)}")
