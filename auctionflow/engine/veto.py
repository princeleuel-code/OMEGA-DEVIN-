from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional, Tuple

from auctionflow.data.schema import Candle
from auctionflow.engine.reasons import ReasonCode
from auctionflow.strategy.signals import Signal


@dataclass(frozen=True)
class RiskConfig:
    max_trades_per_day: int = 5
    max_daily_loss: float = 2.0  # in R units (approx)
    min_rr: float = 1.8


@dataclass
class VetoState:
    trades_today: int = 0
    daily_r: float = 0.0
    last_day: Optional[str] = None  # YYYY-MM-DD


def _day_key(ts: datetime) -> str:
    return ts.date().isoformat()


def risk_rollover(state: VetoState, ts: datetime) -> None:
    dk = _day_key(ts)
    if state.last_day is None:
        state.last_day = dk
        return
    if dk != state.last_day:
        state.trades_today = 0
        state.daily_r = 0.0
        state.last_day = dk


def rr(entry: float, stop: float, target: float) -> float:
    risk = abs(entry - stop)
    if risk <= 0:
        return 0.0
    return abs(target - entry) / risk


def veto(signal: Signal, *, candles: List[Candle], state: VetoState, cfg: RiskConfig) -> Tuple[bool, List[str]]:
    """Return (allowed, reason_codes)."""
    reasons: List[str] = []

    # Basic sanity
    if signal.side == "long" and not (signal.stop < signal.entry < signal.target):
        reasons.append(ReasonCode.VETO_INVALID_LEVELS.value)
    if signal.side == "short" and not (signal.target < signal.entry < signal.stop):
        reasons.append(ReasonCode.VETO_INVALID_LEVELS.value)

    this_rr = rr(signal.entry, signal.stop, signal.target)
    if this_rr < cfg.min_rr:
        reasons.append(ReasonCode.VETO_RR.value)

    # Daily limits
    risk_rollover(state, candles[-1].ts)

    if state.trades_today >= cfg.max_trades_per_day:
        reasons.append(ReasonCode.VETO_MAX_TRADES.value)

    if state.daily_r <= -abs(cfg.max_daily_loss):
        reasons.append(ReasonCode.VETO_RISK.value)

    allowed = len(reasons) == 0
    return allowed, reasons
