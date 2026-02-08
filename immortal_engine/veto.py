# VETO GATE - The Fail-Closed Safety System
# 
# Core principle: If ANYTHING is wrong, DON'T TRADE.
# 
# The veto gate checks every proposal against multiple safety rules.
# If ANY rule fails, the trade is vetoed with reason codes.
# 
# Interface: veto(proposal, context) -> allow/deny + reason_codes[]

from typing import Dict, Any, List, Tuple, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import json
import os


class VetoReason(Enum):
    """Standard veto reason codes"""
    # Data issues
    STALE_DATA = "STALE_DATA"
    MISSING_DATA = "MISSING_DATA"
    INVALID_PRICE = "INVALID_PRICE"
    
    # Risk issues
    MAX_DRAWDOWN_EXCEEDED = "MAX_DRAWDOWN_EXCEEDED"
    POSITION_SIZE_TOO_LARGE = "POSITION_SIZE_TOO_LARGE"
    DAILY_LOSS_LIMIT = "DAILY_LOSS_LIMIT"
    CORRELATION_RISK = "CORRELATION_RISK"
    
    # Market issues
    LOW_LIQUIDITY = "LOW_LIQUIDITY"
    HIGH_SPREAD = "HIGH_SPREAD"
    MARKET_CLOSED = "MARKET_CLOSED"
    VOLATILITY_SPIKE = "VOLATILITY_SPIKE"
    
    # Strategy issues
    LOW_CONFIDENCE = "LOW_CONFIDENCE"
    CONFLICTING_SIGNALS = "CONFLICTING_SIGNALS"
    STRATEGY_NOT_APPROVED = "STRATEGY_NOT_APPROVED"
    
    # System issues
    SYSTEM_OVERLOAD = "SYSTEM_OVERLOAD"
    NETWORK_LATENCY = "NETWORK_LATENCY"
    MANUAL_OVERRIDE = "MANUAL_OVERRIDE"


@dataclass
class VetoResult:
    """Result of a veto check"""
    allowed: bool
    reason_codes: List[VetoReason] = field(default_factory=list)
    details: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def __bool__(self):
        return self.allowed


@dataclass
class VetoRule:
    """A single veto rule"""
    name: str
    check: Callable[[Dict, Dict], Tuple[bool, Optional[VetoReason], Optional[str]]]
    enabled: bool = True
    

class VetoGate:
    """
    THE FAIL-CLOSED VETO GATE
    
    Every trade proposal must pass through this gate.
    If ANY check fails, the trade is blocked.
    
    Philosophy: It's better to miss a good trade than to take a bad one.
    
    Usage:
        gate = VetoGate()
        result = gate.check(proposal, context)
        if result.allowed:
            execute_trade(proposal)
        else:
            log_veto(result.reason_codes)
    """
    
    def __init__(self):
        self.rules: List[VetoRule] = []
        self.log_file = "logs/veto_decisions.json"
        self._setup_default_rules()
        
    def _setup_default_rules(self):
        """Setup the default safety rules"""
        
        # Rule 1: Data freshness
        def check_data_freshness(proposal: Dict, context: Dict) -> Tuple[bool, Optional[VetoReason], Optional[str]]:
            max_age_seconds = context.get("max_data_age_seconds", 60)
            data_age = context.get("data_age_seconds", 0)
            if data_age > max_age_seconds:
                return False, VetoReason.STALE_DATA, f"Data is {data_age}s old (max: {max_age_seconds}s)"
            return True, None, None
            
        # Rule 2: Price validity
        def check_price_validity(proposal: Dict, context: Dict) -> Tuple[bool, Optional[VetoReason], Optional[str]]:
            price = proposal.get("price", 0)
            if price <= 0:
                return False, VetoReason.INVALID_PRICE, f"Invalid price: {price}"
            return True, None, None
            
        # Rule 3: Position size
        def check_position_size(proposal: Dict, context: Dict) -> Tuple[bool, Optional[VetoReason], Optional[str]]:
            max_position_pct = context.get("max_position_pct", 0.05)  # 5% default
            position_pct = proposal.get("position_size_pct", 0)
            if position_pct > max_position_pct:
                return False, VetoReason.POSITION_SIZE_TOO_LARGE, f"Position {position_pct:.1%} > max {max_position_pct:.1%}"
            return True, None, None
            
        # Rule 4: Drawdown check
        def check_drawdown(proposal: Dict, context: Dict) -> Tuple[bool, Optional[VetoReason], Optional[str]]:
            max_drawdown = context.get("max_drawdown_pct", 0.10)  # 10% default
            current_drawdown = context.get("current_drawdown_pct", 0)
            if current_drawdown > max_drawdown:
                return False, VetoReason.MAX_DRAWDOWN_EXCEEDED, f"Drawdown {current_drawdown:.1%} > max {max_drawdown:.1%}"
            return True, None, None
            
        # Rule 5: Daily loss limit
        def check_daily_loss(proposal: Dict, context: Dict) -> Tuple[bool, Optional[VetoReason], Optional[str]]:
            max_daily_loss = context.get("max_daily_loss_pct", 0.02)  # 2% default
            daily_loss = context.get("daily_loss_pct", 0)
            if daily_loss > max_daily_loss:
                return False, VetoReason.DAILY_LOSS_LIMIT, f"Daily loss {daily_loss:.1%} > max {max_daily_loss:.1%}"
            return True, None, None
            
        # Rule 6: Confidence threshold
        def check_confidence(proposal: Dict, context: Dict) -> Tuple[bool, Optional[VetoReason], Optional[str]]:
            min_confidence = context.get("min_confidence", 0.60)
            confidence = proposal.get("confidence", 0)
            if confidence < min_confidence:
                return False, VetoReason.LOW_CONFIDENCE, f"Confidence {confidence:.1%} < min {min_confidence:.1%}"
            return True, None, None
            
        # Rule 7: Spread check
        def check_spread(proposal: Dict, context: Dict) -> Tuple[bool, Optional[VetoReason], Optional[str]]:
            max_spread_pct = context.get("max_spread_pct", 0.005)  # 0.5% default
            spread_pct = context.get("spread_pct", 0)
            if spread_pct > max_spread_pct:
                return False, VetoReason.HIGH_SPREAD, f"Spread {spread_pct:.2%} > max {max_spread_pct:.2%}"
            return True, None, None
            
        # Rule 8: Strategy approval
        def check_strategy_approved(proposal: Dict, context: Dict) -> Tuple[bool, Optional[VetoReason], Optional[str]]:
            strategy_id = proposal.get("strategy_id")
            approved_strategies = context.get("approved_strategies", [])
            if strategy_id and approved_strategies and strategy_id not in approved_strategies:
                return False, VetoReason.STRATEGY_NOT_APPROVED, f"Strategy {strategy_id} not in approved list"
            return True, None, None
            
        # Rule 9: Volatility check
        def check_volatility(proposal: Dict, context: Dict) -> Tuple[bool, Optional[VetoReason], Optional[str]]:
            max_volatility = context.get("max_volatility", 0.05)  # 5% default
            current_volatility = context.get("current_volatility", 0)
            if current_volatility > max_volatility:
                return False, VetoReason.VOLATILITY_SPIKE, f"Volatility {current_volatility:.1%} > max {max_volatility:.1%}"
            return True, None, None
            
        # Add all default rules
        self.add_rule("data_freshness", check_data_freshness)
        self.add_rule("price_validity", check_price_validity)
        self.add_rule("position_size", check_position_size)
        self.add_rule("drawdown", check_drawdown)
        self.add_rule("daily_loss", check_daily_loss)
        self.add_rule("confidence", check_confidence)
        self.add_rule("spread", check_spread)
        self.add_rule("strategy_approved", check_strategy_approved)
        self.add_rule("volatility", check_volatility)
        
    def add_rule(self, name: str, check: Callable, enabled: bool = True) -> 'VetoGate':
        """Add a veto rule (fluent interface)"""
        self.rules.append(VetoRule(name, check, enabled))
        return self
        
    def enable_rule(self, name: str) -> 'VetoGate':
        """Enable a rule by name"""
        for rule in self.rules:
            if rule.name == name:
                rule.enabled = True
        return self
        
    def disable_rule(self, name: str) -> 'VetoGate':
        """Disable a rule by name"""
        for rule in self.rules:
            if rule.name == name:
                rule.enabled = False
        return self
        
    def check(self, proposal: Dict, context: Dict) -> VetoResult:
        """
        Check a trade proposal against all rules.
        
        FAIL-CLOSED: If ANY rule fails, the trade is vetoed.
        
        Args:
            proposal: The trade proposal (signal, price, size, etc.)
            context: Current market/account context (balance, drawdown, etc.)
            
        Returns:
            VetoResult with allowed=True/False and reason_codes
        """
        reason_codes = []
        details = {}
        
        for rule in self.rules:
            if not rule.enabled:
                continue
                
            try:
                passed, reason, detail = rule.check(proposal, context)
                if not passed:
                    reason_codes.append(reason)
                    details[rule.name] = detail
            except Exception as e:
                # If a rule crashes, FAIL CLOSED
                reason_codes.append(VetoReason.SYSTEM_OVERLOAD)
                details[rule.name] = f"Rule crashed: {str(e)}"
                
        result = VetoResult(
            allowed=len(reason_codes) == 0,
            reason_codes=reason_codes,
            details=details
        )
        
        self._log_decision(proposal, context, result)
        return result
        
    def _log_decision(self, proposal: Dict, context: Dict, result: VetoResult):
        """Log veto decisions for audit trail"""
        os.makedirs(os.path.dirname(self.log_file), exist_ok=True)
        
        log_entry = {
            "timestamp": result.timestamp,
            "allowed": result.allowed,
            "reason_codes": [r.value for r in result.reason_codes],
            "details": result.details,
            "proposal_summary": {
                "signal": proposal.get("signal"),
                "symbol": proposal.get("symbol"),
                "confidence": proposal.get("confidence")
            }
        }
        
        try:
            with open(self.log_file, "a") as f:
                f.write(json.dumps(log_entry) + "\n")
        except:
            pass
            
    def get_stats(self) -> Dict[str, Any]:
        """Get veto statistics from log"""
        stats = {
            "total_checks": 0,
            "allowed": 0,
            "vetoed": 0,
            "veto_reasons": {}
        }
        
        try:
            with open(self.log_file, "r") as f:
                for line in f:
                    entry = json.loads(line)
                    stats["total_checks"] += 1
                    if entry["allowed"]:
                        stats["allowed"] += 1
                    else:
                        stats["vetoed"] += 1
                        for reason in entry["reason_codes"]:
                            stats["veto_reasons"][reason] = stats["veto_reasons"].get(reason, 0) + 1
        except:
            pass
            
        return stats


# Example usage
if __name__ == "__main__":
    # Create the veto gate
    gate = VetoGate()
    
    # Good proposal - should pass
    good_proposal = {
        "signal": "BUY",
        "symbol": "BTC",
        "price": 50000,
        "confidence": 0.85,
        "position_size_pct": 0.02
    }
    
    good_context = {
        "data_age_seconds": 5,
        "current_drawdown_pct": 0.03,
        "daily_loss_pct": 0.005,
        "spread_pct": 0.001,
        "current_volatility": 0.02
    }
    
    result = gate.check(good_proposal, good_context)
    print(f"Good proposal: allowed={result.allowed}, reasons={result.reason_codes}")
    
    # Bad proposal - should be vetoed
    bad_proposal = {
        "signal": "BUY",
        "symbol": "BTC",
        "price": 50000,
        "confidence": 0.40,  # Too low
        "position_size_pct": 0.10  # Too large
    }
    
    bad_context = {
        "data_age_seconds": 120,  # Stale
        "current_drawdown_pct": 0.15,  # Exceeded
        "daily_loss_pct": 0.03,  # Exceeded
        "spread_pct": 0.01,  # Too high
        "current_volatility": 0.08  # Too high
    }
    
    result = gate.check(bad_proposal, bad_context)
    print(f"\nBad proposal: allowed={result.allowed}")
    print(f"Reasons: {[r.value for r in result.reason_codes]}")
    print(f"Details: {result.details}")
