from __future__ import annotations

from enum import Enum


class ReasonCode(str, Enum):
    # Permission / veto
    VETO_DATA_GAP = "VETO_DATA_GAP"
    VETO_RR = "VETO_RR"
    VETO_MAX_TRADES = "VETO_MAX_TRADES"
    VETO_SPREAD = "VETO_SPREAD"
    VETO_INVALID_LEVELS = "VETO_INVALID_LEVELS"
    VETO_RISK = "VETO_RISK"

    # Actions
    TRADE = "TRADE"
    SKIP = "SKIP"
