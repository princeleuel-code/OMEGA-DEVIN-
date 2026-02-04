"""
Data Integrity Checker - Validate data before trading

Checks for gaps, stale data, non-monotonic timestamps, and invalid prices.
If anything is wrong, the system fails closed.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import List, Optional, Tuple
import logging

from ..core.reason_codes import ReasonCode, ReasonRecord, create_reason
from .loader import OHLCV


logger = logging.getLogger(__name__)


@dataclass
class IntegrityResult:
    """Result of integrity check"""
    valid: bool = True
    issues: List[ReasonRecord] = field(default_factory=list)
    
    def add_issue(self, code: ReasonCode, details: str, severity: int = 2):
        self.issues.append(create_reason(code, details, severity))
        if severity >= 2:
            self.valid = False
    
    def to_dict(self) -> dict:
        return {
            "valid": self.valid,
            "issue_count": len(self.issues),
            "issues": [i.to_dict() for i in self.issues]
        }


@dataclass
class IntegrityConfig:
    """Configuration for integrity checks"""
    # Time gap threshold (in bar periods)
    max_gap_bars: int = 3
    
    # Expected bar interval (for gap detection)
    bar_interval_minutes: int = 60  # 1 hour bars
    
    # Price validation
    min_price: float = 0.0001
    max_price: float = 1000.0
    max_price_change_pct: float = 5.0  # Max % change between bars
    
    # Volume validation
    require_volume: bool = False
    min_volume: float = 0.0


class IntegrityChecker:
    """
    Validate data integrity before using it for trading.
    
    Checks:
    1. Timestamps are monotonically increasing
    2. No gaps larger than threshold
    3. Prices are valid (positive, within range)
    4. No extreme price jumps
    5. OHLC relationship is valid (L <= O,C <= H)
    """
    
    def __init__(self, config: Optional[IntegrityConfig] = None):
        self.config = config or IntegrityConfig()
    
    def check_series(self, data: List[OHLCV]) -> IntegrityResult:
        """
        Check integrity of a complete data series.
        """
        result = IntegrityResult()
        
        if not data:
            result.add_issue(
                ReasonCode.DATA_GAP,
                "Empty data series",
                severity=3
            )
            return result
        
        if len(data) < 2:
            result.add_issue(
                ReasonCode.DATA_GAP,
                f"Insufficient data: {len(data)} bars",
                severity=2
            )
            return result
        
        # Check each bar and transitions
        prev_bar = None
        for i, bar in enumerate(data):
            # Check individual bar validity
            bar_issues = self._check_bar(bar, i)
            for issue in bar_issues:
                result.issues.append(issue)
                if issue.severity >= 2:
                    result.valid = False
            
            # Check transition from previous bar
            if prev_bar:
                transition_issues = self._check_transition(prev_bar, bar, i)
                for issue in transition_issues:
                    result.issues.append(issue)
                    if issue.severity >= 2:
                        result.valid = False
            
            prev_bar = bar
        
        logger.info(
            f"Integrity check: {len(data)} bars, "
            f"valid={result.valid}, issues={len(result.issues)}"
        )
        
        return result
    
    def _check_bar(self, bar: OHLCV, index: int) -> List[ReasonRecord]:
        """Check a single bar for validity"""
        issues = []
        
        # Check OHLC relationship
        if not (bar.low <= bar.open <= bar.high):
            issues.append(create_reason(
                ReasonCode.DATA_INVALID_PRICE,
                f"Bar {index}: Open {bar.open} outside L-H range [{bar.low}, {bar.high}]",
                severity=2
            ))
        
        if not (bar.low <= bar.close <= bar.high):
            issues.append(create_reason(
                ReasonCode.DATA_INVALID_PRICE,
                f"Bar {index}: Close {bar.close} outside L-H range [{bar.low}, {bar.high}]",
                severity=2
            ))
        
        # Check price range
        for price_name, price in [("open", bar.open), ("high", bar.high), 
                                   ("low", bar.low), ("close", bar.close)]:
            if price < self.config.min_price:
                issues.append(create_reason(
                    ReasonCode.DATA_INVALID_PRICE,
                    f"Bar {index}: {price_name}={price} < min {self.config.min_price}",
                    severity=3
                ))
            if price > self.config.max_price:
                issues.append(create_reason(
                    ReasonCode.DATA_INVALID_PRICE,
                    f"Bar {index}: {price_name}={price} > max {self.config.max_price}",
                    severity=3
                ))
        
        # Check volume if required
        if self.config.require_volume and bar.volume < self.config.min_volume:
            issues.append(create_reason(
                ReasonCode.DATA_MISSING_FIELD,
                f"Bar {index}: volume={bar.volume} < min {self.config.min_volume}",
                severity=1
            ))
        
        return issues
    
    def _check_transition(
        self, 
        prev: OHLCV, 
        curr: OHLCV, 
        index: int
    ) -> List[ReasonRecord]:
        """Check transition between two consecutive bars"""
        issues = []
        
        # Check monotonic timestamps
        if curr.timestamp <= prev.timestamp:
            issues.append(create_reason(
                ReasonCode.DATA_NON_MONOTONIC,
                f"Bar {index}: timestamp {curr.timestamp} <= previous {prev.timestamp}",
                severity=3
            ))
        
        # Check for gaps
        expected_interval = timedelta(minutes=self.config.bar_interval_minutes)
        actual_interval = curr.timestamp - prev.timestamp
        max_interval = expected_interval * self.config.max_gap_bars
        
        if actual_interval > max_interval:
            gap_bars = actual_interval / expected_interval
            issues.append(create_reason(
                ReasonCode.DATA_GAP,
                f"Bar {index}: gap of {gap_bars:.1f} bars ({actual_interval})",
                severity=2
            ))
        
        # Check for extreme price jumps
        price_change = abs(curr.open - prev.close) / prev.close * 100
        if price_change > self.config.max_price_change_pct:
            issues.append(create_reason(
                ReasonCode.DATA_INVALID_PRICE,
                f"Bar {index}: {price_change:.2f}% jump from {prev.close} to {curr.open}",
                severity=2
            ))
        
        return issues
    
    def check_realtime(
        self,
        current_bar: OHLCV,
        last_update: datetime,
        max_age_seconds: float = 5.0
    ) -> IntegrityResult:
        """
        Check integrity for real-time data.
        
        Used during live trading to ensure data is fresh.
        """
        result = IntegrityResult()
        now = datetime.utcnow()
        
        # Check data freshness
        age = (now - last_update).total_seconds()
        if age > max_age_seconds:
            result.add_issue(
                ReasonCode.DATA_STALE,
                f"Data age {age:.1f}s > threshold {max_age_seconds}s",
                severity=3
            )
        
        # Check bar validity
        bar_issues = self._check_bar(current_bar, 0)
        for issue in bar_issues:
            result.issues.append(issue)
            if issue.severity >= 2:
                result.valid = False
        
        return result
