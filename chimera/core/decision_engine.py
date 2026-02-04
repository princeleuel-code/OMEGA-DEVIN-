"""
Decision Engine - Central brain loop

The heart of the system: reads market context, proposes actions, records why.
Fail-closed: if anything is off, do nothing.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from typing import Dict, List, Optional, Any
import logging

from .reason_codes import ReasonCode, ReasonRecord, create_reason
from .veto_cascade import VetoCascade, VetoResult, MarketContext, RiskState, VetoConfig
from .truth_manifest import TruthManifest


logger = logging.getLogger(__name__)


class Action(Enum):
    """Possible actions the engine can take"""
    LONG = auto()
    SHORT = auto()
    WAIT = auto()
    CLOSE_LONG = auto()
    CLOSE_SHORT = auto()
    FAIL_CLOSED = auto()


@dataclass
class Signal:
    """A trading signal from the strategy"""
    action: Action
    confidence: float  # 0.0 to 1.0
    entry_price: Optional[float] = None
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    size: float = 0.0
    reasons: List[ReasonRecord] = field(default_factory=list)
    
    def add_reason(self, code: ReasonCode, details: Optional[str] = None):
        self.reasons.append(create_reason(code, details))


@dataclass
class DecisionPacket:
    """Complete record of a decision"""
    timestamp: datetime
    symbol: str
    signal: Signal
    veto_result: VetoResult
    final_action: Action
    reasons: List[ReasonRecord]
    context_snapshot: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp.isoformat(),
            "symbol": self.symbol,
            "signal": {
                "action": self.signal.action.name,
                "confidence": self.signal.confidence,
                "entry_price": self.signal.entry_price,
                "stop_loss": self.signal.stop_loss,
                "take_profit": self.signal.take_profit,
                "size": self.signal.size,
                "reasons": [r.to_dict() for r in self.signal.reasons]
            },
            "veto": self.veto_result.to_dict(),
            "final_action": self.final_action.name,
            "reasons": [r.to_dict() for r in self.reasons],
            "context": self.context_snapshot
        }


class DecisionEngine:
    """
    Central decision-making loop.
    
    Flow:
    1. Receive market context
    2. Check data integrity
    3. Generate signal from strategy
    4. Run veto cascade
    5. Make final decision
    6. Record everything
    """
    
    def __init__(
        self,
        veto_config: Optional[VetoConfig] = None,
        manifest: Optional[TruthManifest] = None
    ):
        self.veto_cascade = VetoCascade(veto_config)
        self.manifest = manifest
        self.risk_state = RiskState()
        self._decision_history: List[DecisionPacket] = []
    
    def process(
        self,
        context: MarketContext,
        signal: Signal
    ) -> DecisionPacket:
        """
        Process a signal through the decision pipeline.
        
        Returns a complete DecisionPacket with the final action and all reasons.
        """
        all_reasons: List[ReasonRecord] = []
        
        # Step 1: Collect signal reasons
        all_reasons.extend(signal.reasons)
        
        # Step 2: Run veto cascade
        veto_result = self.veto_cascade.evaluate(
            context=context,
            risk_state=self.risk_state,
            proposed_size=signal.size
        )
        all_reasons.extend(veto_result.reasons)
        
        # Step 3: Determine final action
        if veto_result.blocked:
            # Veto triggered - fail closed
            final_action = Action.FAIL_CLOSED
            all_reasons.append(create_reason(
                ReasonCode.VETO_FAIL_CLOSED,
                f"Blocked by {len([r for r in veto_result.reasons if r.code.name.startswith('VETO_') or r.severity >= 2])} veto(s)"
            ))
        elif signal.action == Action.WAIT:
            # Strategy says wait
            final_action = Action.WAIT
        elif signal.confidence < 0.5:
            # Low confidence - wait
            final_action = Action.WAIT
            all_reasons.append(create_reason(
                ReasonCode.SIGNAL_WEAK_CONFLUENCE,
                f"Confidence {signal.confidence:.2f} < 0.5 threshold"
            ))
        else:
            # Signal is valid and not vetoed
            final_action = signal.action
            all_reasons.append(create_reason(
                ReasonCode.SIGNAL_VALID,
                f"Valid {signal.action.name} signal with confidence {signal.confidence:.2f}"
            ))
        
        # Step 4: Create decision packet
        packet = DecisionPacket(
            timestamp=datetime.utcnow(),
            symbol=context.symbol,
            signal=signal,
            veto_result=veto_result,
            final_action=final_action,
            reasons=all_reasons,
            context_snapshot={
                "bid": context.bid,
                "ask": context.ask,
                "spread_pips": context.spread_pips,
                "session_open": context.session_open,
                "volatility": context.volatility
            }
        )
        
        # Step 5: Record decision
        self._decision_history.append(packet)
        if self.manifest:
            self.manifest.add_decision(packet.to_dict())
        
        logger.info(
            f"Decision: {final_action.name} | "
            f"Signal: {signal.action.name} ({signal.confidence:.2f}) | "
            f"Vetoed: {veto_result.blocked} | "
            f"Reasons: {len(all_reasons)}"
        )
        
        return packet
    
    def update_risk_state(
        self,
        daily_pnl: Optional[float] = None,
        max_drawdown: Optional[float] = None,
        current_exposure: Optional[float] = None,
        trades_today: Optional[int] = None,
        open_positions: Optional[int] = None
    ):
        """Update the risk state"""
        if daily_pnl is not None:
            self.risk_state.daily_pnl = daily_pnl
        if max_drawdown is not None:
            self.risk_state.max_drawdown = max_drawdown
        if current_exposure is not None:
            self.risk_state.current_exposure = current_exposure
        if trades_today is not None:
            self.risk_state.trades_today = trades_today
        if open_positions is not None:
            self.risk_state.open_positions = open_positions
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get decision statistics"""
        if not self._decision_history:
            return {"total_decisions": 0}
        
        actions = [d.final_action for d in self._decision_history]
        vetoed = sum(1 for d in self._decision_history if d.veto_result.blocked)
        
        return {
            "total_decisions": len(self._decision_history),
            "action_counts": {
                action.name: actions.count(action) 
                for action in Action
            },
            "vetoed_count": vetoed,
            "veto_rate": vetoed / len(self._decision_history),
            "avg_confidence": sum(d.signal.confidence for d in self._decision_history) / len(self._decision_history)
        }
    
    def reset(self):
        """Reset the engine state"""
        self._decision_history = []
        self.risk_state = RiskState()


def create_wait_signal(reason: str = "No setup") -> Signal:
    """Factory for creating a WAIT signal"""
    signal = Signal(action=Action.WAIT, confidence=0.0)
    signal.add_reason(ReasonCode.SIGNAL_NO_SETUP, reason)
    return signal


def create_trade_signal(
    action: Action,
    confidence: float,
    entry: float,
    stop_loss: float,
    take_profit: float,
    size: float,
    reason: str
) -> Signal:
    """Factory for creating a trade signal"""
    signal = Signal(
        action=action,
        confidence=confidence,
        entry_price=entry,
        stop_loss=stop_loss,
        take_profit=take_profit,
        size=size
    )
    signal.add_reason(ReasonCode.SIGNAL_VALID, reason)
    return signal
