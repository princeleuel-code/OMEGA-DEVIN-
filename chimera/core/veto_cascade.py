"""
Veto Cascade - Safety gates that block unsafe trades

Design rule: Profit comes from what you refuse to trade.
Every block must have an explicit reason code.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Callable, Any
from datetime import datetime, timedelta
import logging

from .reason_codes import ReasonCode, ReasonRecord, create_reason, is_blocking


logger = logging.getLogger(__name__)


@dataclass
class VetoResult:
    """Result of a veto check"""
    blocked: bool
    reasons: List[ReasonRecord] = field(default_factory=list)
    
    def add_reason(self, code: ReasonCode, details: Optional[str] = None, severity: int = 1):
        self.reasons.append(create_reason(code, details, severity))
        if is_blocking(code):
            self.blocked = True
    
    def to_dict(self) -> dict:
        return {
            "blocked": self.blocked,
            "reason_count": len(self.reasons),
            "reasons": [r.to_dict() for r in self.reasons]
        }


@dataclass
class MarketContext:
    """Current market state for veto checks"""
    symbol: str
    timestamp: datetime
    bid: float
    ask: float
    spread: float
    last_update: datetime
    volatility: Optional[float] = None
    session_open: bool = True
    news_pending: bool = False
    
    @property
    def spread_pips(self) -> float:
        """Convert spread to pips (assuming 4/5 decimal pricing)"""
        if "JPY" in self.symbol:
            return self.spread * 100
        return self.spread * 10000


@dataclass 
class RiskState:
    """Current risk state"""
    daily_pnl: float = 0.0
    max_drawdown: float = 0.0
    current_exposure: float = 0.0
    trades_today: int = 0
    open_positions: int = 0


@dataclass
class VetoConfig:
    """Configuration for veto thresholds"""
    # Data integrity
    max_data_age_seconds: float = 5.0
    
    # Risk limits
    max_daily_loss: float = -500.0  # USD
    max_drawdown_pct: float = 5.0   # Percent
    max_position_size: float = 1.0  # Lots
    max_exposure: float = 5.0       # Lots total
    max_trades_per_day: int = 10
    
    # Market conditions
    max_spread_pips: float = 3.0
    volatility_spike_threshold: float = 2.0  # Std devs
    
    # Session times (UTC hours)
    session_start_hour: int = 0   # Allow all hours for backtesting
    session_end_hour: int = 24    # Allow all hours for backtesting
    
    # Backtesting mode (disables some real-time checks)
    backtest_mode: bool = True


class VetoCascade:
    """
    Sequential veto checks - if any fails, trade is blocked.
    
    Order matters: check cheapest/fastest vetoes first.
    """
    
    def __init__(self, config: Optional[VetoConfig] = None):
        self.config = config or VetoConfig()
        self._veto_checks: List[Callable] = [
            self._check_data_integrity,
            self._check_risk_limits,
            self._check_market_conditions,
            self._check_session_time,
        ]
    
    def evaluate(
        self, 
        context: MarketContext, 
        risk_state: RiskState,
        proposed_size: float = 0.0
    ) -> VetoResult:
        """
        Run all veto checks in sequence.
        Returns as soon as a blocking condition is found.
        """
        result = VetoResult(blocked=False)
        
        for check in self._veto_checks:
            check(context, risk_state, proposed_size, result)
            
            # Early exit on critical block
            if result.blocked and any(r.severity >= 3 for r in result.reasons):
                logger.warning(f"Critical veto triggered: {result.reasons[-1].code.name}")
                break
        
        return result
    
    def _check_data_integrity(
        self, 
        context: MarketContext, 
        risk_state: RiskState,
        proposed_size: float,
        result: VetoResult
    ):
        """Check data is fresh and valid"""
        # Use context.timestamp as "now" for backtesting compatibility
        # In live trading, context.timestamp should be close to utcnow()
        now = context.timestamp
        age = (now - context.last_update).total_seconds()
        
        if age > self.config.max_data_age_seconds:
            result.add_reason(
                ReasonCode.DATA_STALE,
                f"Data age: {age:.1f}s > {self.config.max_data_age_seconds}s",
                severity=3
            )
        
        # Check for invalid prices
        if context.bid <= 0 or context.ask <= 0:
            result.add_reason(
                ReasonCode.DATA_INVALID_PRICE,
                f"Invalid bid/ask: {context.bid}/{context.ask}",
                severity=3
            )
        
        # Check spread sanity
        if context.spread < 0:
            result.add_reason(
                ReasonCode.DATA_INVALID_PRICE,
                f"Negative spread: {context.spread}",
                severity=3
            )
    
    def _check_risk_limits(
        self,
        context: MarketContext,
        risk_state: RiskState,
        proposed_size: float,
        result: VetoResult
    ):
        """Check risk limits are not exceeded"""
        
        # Daily loss limit
        if risk_state.daily_pnl <= self.config.max_daily_loss:
            result.add_reason(
                ReasonCode.RISK_MAX_DAILY_LOSS,
                f"Daily P&L: ${risk_state.daily_pnl:.2f} <= ${self.config.max_daily_loss:.2f}",
                severity=3
            )
        
        # Drawdown limit
        if risk_state.max_drawdown >= self.config.max_drawdown_pct:
            result.add_reason(
                ReasonCode.RISK_MAX_DRAWDOWN,
                f"Drawdown: {risk_state.max_drawdown:.1f}% >= {self.config.max_drawdown_pct:.1f}%",
                severity=3
            )
        
        # Position size limit
        if proposed_size > self.config.max_position_size:
            result.add_reason(
                ReasonCode.RISK_MAX_POSITION_SIZE,
                f"Size: {proposed_size:.2f} > {self.config.max_position_size:.2f} lots",
                severity=2
            )
        
        # Total exposure limit
        new_exposure = risk_state.current_exposure + proposed_size
        if new_exposure > self.config.max_exposure:
            result.add_reason(
                ReasonCode.RISK_MAX_EXPOSURE,
                f"Exposure: {new_exposure:.2f} > {self.config.max_exposure:.2f} lots",
                severity=2
            )
        
        # Trades per day limit
        if risk_state.trades_today >= self.config.max_trades_per_day:
            result.add_reason(
                ReasonCode.RISK_MAX_TRADES_PER_DAY,
                f"Trades today: {risk_state.trades_today} >= {self.config.max_trades_per_day}",
                severity=2
            )
    
    def _check_market_conditions(
        self,
        context: MarketContext,
        risk_state: RiskState,
        proposed_size: float,
        result: VetoResult
    ):
        """Check market conditions are suitable"""
        
        # Spread check
        if context.spread_pips > self.config.max_spread_pips:
            result.add_reason(
                ReasonCode.MARKET_SPREAD_TOO_WIDE,
                f"Spread: {context.spread_pips:.1f} pips > {self.config.max_spread_pips:.1f} pips",
                severity=2
            )
        
        # News blackout
        if context.news_pending:
            result.add_reason(
                ReasonCode.MARKET_NEWS_BLACKOUT,
                "High-impact news pending",
                severity=2
            )
        
        # Volatility spike
        if context.volatility and context.volatility > self.config.volatility_spike_threshold:
            result.add_reason(
                ReasonCode.MARKET_VOLATILITY_SPIKE,
                f"Volatility: {context.volatility:.2f} std devs",
                severity=2
            )
    
    def _check_session_time(
        self,
        context: MarketContext,
        risk_state: RiskState,
        proposed_size: float,
        result: VetoResult
    ):
        """Check we're in valid trading session"""
        hour = context.timestamp.hour
        
        if not (self.config.session_start_hour <= hour < self.config.session_end_hour):
            result.add_reason(
                ReasonCode.MARKET_SESSION_CLOSED,
                f"Hour {hour} outside session {self.config.session_start_hour}-{self.config.session_end_hour}",
                severity=1
            )
        
        # Weekend check (Friday after 21:00 UTC to Sunday 21:00 UTC)
        weekday = context.timestamp.weekday()
        if weekday == 4 and hour >= 21:  # Friday evening
            result.add_reason(
                ReasonCode.MARKET_WEEKEND_GAP_RISK,
                "Weekend gap risk - Friday close",
                severity=2
            )
        elif weekday in (5, 6):  # Saturday/Sunday
            result.add_reason(
                ReasonCode.MARKET_SESSION_CLOSED,
                "Weekend - market closed",
                severity=3
            )
