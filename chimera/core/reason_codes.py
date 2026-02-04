"""
Reason Codes - Explicit vocabulary for every decision

Every NO must have a code. No silent failures.
"""

from enum import Enum, auto
from dataclasses import dataclass
from typing import Optional
from datetime import datetime


class ReasonCategory(Enum):
    """Categories of reason codes"""
    DATA = auto()       # Data integrity issues
    RISK = auto()       # Risk limit violations
    MARKET = auto()     # Market condition issues
    SIGNAL = auto()     # Signal quality issues
    SYSTEM = auto()     # System/technical issues
    VETO = auto()       # Explicit veto triggers


class ReasonCode(Enum):
    """
    Explicit reason codes for every decision.
    Format: CATEGORY_SPECIFIC_REASON
    """
    # Data Integrity
    DATA_GAP = "Data gap detected - missing bars/ticks"
    DATA_STALE = "Data is stale - no updates within threshold"
    DATA_NON_MONOTONIC = "Timestamps not monotonically increasing"
    DATA_INVALID_PRICE = "Invalid price (zero, negative, or extreme)"
    DATA_MISSING_FIELD = "Required field missing from data"
    DATA_FEED_DISCONNECTED = "Data feed disconnected"
    
    # Risk Limits
    RISK_MAX_DAILY_LOSS = "Maximum daily loss limit reached"
    RISK_MAX_DRAWDOWN = "Maximum drawdown limit reached"
    RISK_MAX_POSITION_SIZE = "Position size exceeds limit"
    RISK_MAX_EXPOSURE = "Total exposure exceeds limit"
    RISK_MAX_TRADES_PER_DAY = "Maximum trades per day reached"
    RISK_CORRELATION_LIMIT = "Correlated position limit reached"
    
    # Market Conditions
    MARKET_SPREAD_TOO_WIDE = "Spread exceeds threshold"
    MARKET_LOW_LIQUIDITY = "Insufficient liquidity"
    MARKET_NEWS_BLACKOUT = "High-impact news window"
    MARKET_SESSION_CLOSED = "Market session closed"
    MARKET_VOLATILITY_SPIKE = "Abnormal volatility detected"
    MARKET_WEEKEND_GAP_RISK = "Weekend gap risk window"
    
    # Signal Quality
    SIGNAL_NO_SETUP = "No valid setup detected"
    SIGNAL_WEAK_CONFLUENCE = "Insufficient confluence"
    SIGNAL_CONFLICTING = "Conflicting signals"
    SIGNAL_REGIME_UNCERTAIN = "Market regime uncertain"
    SIGNAL_STRUCTURE_INVALID = "Market structure invalid"
    
    # System Issues
    SYSTEM_ERROR = "System error occurred"
    SYSTEM_TIMEOUT = "Operation timed out"
    SYSTEM_RESOURCE_LIMIT = "Resource limit reached"
    
    # Veto Triggers
    VETO_ANOMALY = "Anomaly detected - manual review required"
    VETO_MANUAL_OVERRIDE = "Manual override active"
    VETO_FAIL_CLOSED = "Fail-closed triggered - unknown condition"
    
    # Positive Outcomes
    SIGNAL_VALID = "Valid signal detected"
    TRADE_EXECUTED = "Trade executed successfully"
    WAIT_OPTIMAL = "Waiting is optimal action"


@dataclass
class ReasonRecord:
    """A single reason record with metadata"""
    code: ReasonCode
    category: ReasonCategory
    timestamp: datetime
    details: Optional[str] = None
    severity: int = 1  # 1=info, 2=warning, 3=critical
    
    def to_dict(self) -> dict:
        return {
            "code": self.code.name,
            "category": self.category.name,
            "message": self.code.value,
            "timestamp": self.timestamp.isoformat(),
            "details": self.details,
            "severity": self.severity
        }


def get_category(code: ReasonCode) -> ReasonCategory:
    """Get the category for a reason code based on its prefix"""
    name = code.name
    if name.startswith("DATA_"):
        return ReasonCategory.DATA
    elif name.startswith("RISK_"):
        return ReasonCategory.RISK
    elif name.startswith("MARKET_"):
        return ReasonCategory.MARKET
    elif name.startswith("SIGNAL_"):
        return ReasonCategory.SIGNAL
    elif name.startswith("SYSTEM_"):
        return ReasonCategory.SYSTEM
    elif name.startswith("VETO_"):
        return ReasonCategory.VETO
    else:
        return ReasonCategory.SYSTEM


def create_reason(code: ReasonCode, details: Optional[str] = None, severity: int = 1) -> ReasonRecord:
    """Factory function to create a reason record"""
    return ReasonRecord(
        code=code,
        category=get_category(code),
        timestamp=datetime.utcnow(),
        details=details,
        severity=severity
    )


# Quick lookup for blocking reasons (these prevent trading)
BLOCKING_REASONS = {
    ReasonCode.DATA_GAP,
    ReasonCode.DATA_STALE,
    ReasonCode.DATA_NON_MONOTONIC,
    ReasonCode.DATA_INVALID_PRICE,
    ReasonCode.DATA_FEED_DISCONNECTED,
    ReasonCode.RISK_MAX_DAILY_LOSS,
    ReasonCode.RISK_MAX_DRAWDOWN,
    ReasonCode.RISK_MAX_POSITION_SIZE,
    ReasonCode.RISK_MAX_EXPOSURE,
    ReasonCode.RISK_MAX_TRADES_PER_DAY,
    ReasonCode.MARKET_SPREAD_TOO_WIDE,
    ReasonCode.MARKET_NEWS_BLACKOUT,
    ReasonCode.MARKET_SESSION_CLOSED,
    ReasonCode.MARKET_VOLATILITY_SPIKE,
    ReasonCode.VETO_ANOMALY,
    ReasonCode.VETO_MANUAL_OVERRIDE,
    ReasonCode.VETO_FAIL_CLOSED,
    ReasonCode.SYSTEM_ERROR,
}


def is_blocking(code: ReasonCode) -> bool:
    """Check if a reason code blocks trading"""
    return code in BLOCKING_REASONS
