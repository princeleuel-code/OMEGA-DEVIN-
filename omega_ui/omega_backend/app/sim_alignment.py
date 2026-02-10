"""
Helpers for keeping synthetic dashboard candles on the same price axis as REAL DOM.

This module is intentionally dependency-light (no FastAPI) so it can be unit-tested
under the repo's default verifier environment.
"""

from __future__ import annotations

from typing import Dict, List, Optional, Set


DEFAULT_ALIGNMENT_THRESHOLD_RATIO = 0.005  # 0.5%


def shift_history_prices(history: List[dict], delta: float) -> None:
    """Shift OHLC prices by delta (in-place)."""
    if not history:
        return
    for bar in history:
        for k in ("open", "high", "low", "close"):
            if k in bar:
                bar[k] = float(bar[k]) + float(delta)


def maybe_align_history_to_mid(
    symbol: str,
    history: List[dict],
    mid: Optional[float],
    *,
    aligned: Set[str],
    current_prices: Dict[str, float],
    threshold_ratio: float = DEFAULT_ALIGNMENT_THRESHOLD_RATIO,
) -> bool:
    """
    One-time alignment: if `mid` is available, shift the synthetic history so its
    last close matches `mid`. Returns True if the symbol was newly aligned.
    """
    if mid is None or not history:
        return False

    sym = symbol.upper()
    if sym in aligned:
        return False

    try:
        last_close = float(history[-1].get("close", mid))
    except Exception:
        last_close = float(mid)

    denom = max(abs(float(mid)), 1e-9)
    delta = float(mid) - last_close

    # Only shift when mismatch is material to avoid tiny jitter.
    if abs(delta) / denom > float(threshold_ratio):
        shift_history_prices(history, delta)

    # Keep current price consistent with the (possibly shifted) history.
    try:
        current_prices[sym] = float(history[-1].get("close", mid))
    except Exception:
        pass

    aligned.add(sym)
    return True

