"""
Ensemble Coordinator

Coordinates multiple strategy modules (Chimera, AuctionFlow, RL, Sentiment)
to produce unified trading decisions.

Key Features:
- Collects signals from multiple strategy modules
- Weighted voting or confidence-based selection
- Conflict resolution with fail-closed default
- Reason code aggregation
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

from chimera.core.reason_codes import ReasonCode

logger = logging.getLogger(__name__)


class SignalType(Enum):
    """Types of trading signals."""
    LONG = "long"
    SHORT = "short"
    CLOSE = "close"
    HOLD = "hold"


@dataclass
class StrategySignal:
    """A signal from a strategy module."""
    source: str  # chimera, auctionflow, rl, sentiment
    signal_type: SignalType
    confidence: float  # 0.0 to 1.0
    entry_price: Optional[float] = None
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    reason_codes: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "source": self.source,
            "signal_type": self.signal_type.value,
            "confidence": self.confidence,
            "entry_price": self.entry_price,
            "stop_loss": self.stop_loss,
            "take_profit": self.take_profit,
            "reason_codes": self.reason_codes,
            "metadata": self.metadata,
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class EnsembleConfig:
    """Configuration for the ensemble coordinator."""
    # Strategy weights (must sum to 1.0)
    weights: Dict[str, float] = field(default_factory=lambda: {
        "chimera": 0.4,
        "auctionflow": 0.3,
        "rl": 0.2,
        "sentiment": 0.1,
    })
    
    # Minimum confidence thresholds
    min_confidence_single: float = 0.7  # For single strategy
    min_confidence_ensemble: float = 0.6  # For ensemble decision
    
    # Agreement requirements
    require_agreement: bool = True  # Require multiple strategies to agree
    min_agreeing_strategies: int = 2
    
    # Conflict resolution
    conflict_resolution: str = "abstain"  # abstain, highest_confidence, weighted_vote
    
    # Veto power
    sentiment_veto_enabled: bool = True
    rl_veto_enabled: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "weights": self.weights,
            "min_confidence_single": self.min_confidence_single,
            "min_confidence_ensemble": self.min_confidence_ensemble,
            "require_agreement": self.require_agreement,
            "min_agreeing_strategies": self.min_agreeing_strategies,
            "conflict_resolution": self.conflict_resolution,
            "sentiment_veto_enabled": self.sentiment_veto_enabled,
            "rl_veto_enabled": self.rl_veto_enabled,
        }


@dataclass
class EnsembleDecision:
    """The final decision from the ensemble."""
    signal_type: SignalType
    confidence: float
    entry_price: Optional[float]
    stop_loss: Optional[float]
    take_profit: Optional[float]
    contributing_signals: List[StrategySignal]
    reason_codes: List[str]
    decision_method: str  # single, agreement, weighted_vote, abstain
    vetoed: bool = False
    veto_reasons: List[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "signal_type": self.signal_type.value,
            "confidence": self.confidence,
            "entry_price": self.entry_price,
            "stop_loss": self.stop_loss,
            "take_profit": self.take_profit,
            "contributing_signals": [s.to_dict() for s in self.contributing_signals],
            "reason_codes": self.reason_codes,
            "decision_method": self.decision_method,
            "vetoed": self.vetoed,
            "veto_reasons": self.veto_reasons,
            "timestamp": self.timestamp.isoformat(),
        }


class EnsembleCoordinator:
    """
    Coordinates multiple strategy modules to produce unified decisions.
    
    The coordinator collects signals from different strategies and
    combines them using configurable rules (voting, weighting, etc.)
    while maintaining the fail-closed principle.
    """
    
    def __init__(self, config: Optional[EnsembleConfig] = None):
        self.config = config or EnsembleConfig()
        self._validate_config()
        
        # Signal buffer
        self.current_signals: Dict[str, StrategySignal] = {}
        
        # Decision history
        self.decision_history: List[EnsembleDecision] = []
        
        logger.info("EnsembleCoordinator initialized")
    
    def _validate_config(self) -> None:
        """Validate configuration."""
        total_weight = sum(self.config.weights.values())
        if abs(total_weight - 1.0) > 0.01:
            logger.warning(f"Strategy weights sum to {total_weight}, normalizing to 1.0")
            for key in self.config.weights:
                self.config.weights[key] /= total_weight
    
    def submit_signal(self, signal: StrategySignal) -> None:
        """
        Submit a signal from a strategy module.
        
        Args:
            signal: The strategy signal to submit
        """
        self.current_signals[signal.source] = signal
        logger.debug(f"Received signal from {signal.source}: {signal.signal_type.value} ({signal.confidence:.2f})")
    
    def clear_signals(self) -> None:
        """Clear all current signals."""
        self.current_signals.clear()
    
    def get_decision(self) -> EnsembleDecision:
        """
        Get the ensemble decision based on current signals.
        
        Returns:
            EnsembleDecision with the final trading decision
        """
        if not self.current_signals:
            return self._create_abstain_decision("NO_SIGNALS")
        
        # Check for vetoes first
        veto_reasons = self._check_vetoes()
        if veto_reasons:
            decision = self._create_abstain_decision("VETOED")
            decision.vetoed = True
            decision.veto_reasons = veto_reasons
            return decision
        
        # Get active signals (non-HOLD with sufficient confidence)
        active_signals = self._get_active_signals()
        
        if not active_signals:
            return self._create_abstain_decision("NO_ACTIVE_SIGNALS")
        
        # Single signal case
        if len(active_signals) == 1:
            signal = active_signals[0]
            if signal.confidence >= self.config.min_confidence_single:
                return self._create_decision_from_signal(signal, "single")
            else:
                return self._create_abstain_decision("SINGLE_LOW_CONFIDENCE")
        
        # Multiple signals - check agreement
        if self.config.require_agreement:
            decision = self._decide_by_agreement(active_signals)
        else:
            decision = self._decide_by_weighted_vote(active_signals)
        
        # Store in history
        self.decision_history.append(decision)
        
        return decision
    
    def _check_vetoes(self) -> List[str]:
        """Check if any strategy is vetoing."""
        veto_reasons = []
        
        # Sentiment veto
        if self.config.sentiment_veto_enabled and "sentiment" in self.current_signals:
            sentiment_signal = self.current_signals["sentiment"]
            for code in sentiment_signal.reason_codes:
                if "VETO" in code:
                    veto_reasons.append(code)
        
        # RL veto (if RL recommends strong abstention)
        if self.config.rl_veto_enabled and "rl" in self.current_signals:
            rl_signal = self.current_signals["rl"]
            if rl_signal.signal_type == SignalType.HOLD and rl_signal.confidence > 0.8:
                veto_reasons.append("RL_STRONG_ABSTAIN")
        
        return veto_reasons
    
    def _get_active_signals(self) -> List[StrategySignal]:
        """Get signals that are proposing trades (not HOLD)."""
        active = []
        for signal in self.current_signals.values():
            if signal.signal_type != SignalType.HOLD:
                active.append(signal)
        return active
    
    def _decide_by_agreement(self, signals: List[StrategySignal]) -> EnsembleDecision:
        """
        Decide based on strategy agreement.
        
        Requires multiple strategies to agree on direction.
        """
        # Group by signal type
        signal_groups: Dict[SignalType, List[StrategySignal]] = {}
        for signal in signals:
            if signal.signal_type not in signal_groups:
                signal_groups[signal.signal_type] = []
            signal_groups[signal.signal_type].append(signal)
        
        # Find the signal type with most agreement
        best_type = None
        best_signals: List[StrategySignal] = []
        
        for signal_type, group in signal_groups.items():
            if len(group) >= self.config.min_agreeing_strategies:
                if len(group) > len(best_signals):
                    best_type = signal_type
                    best_signals = group
        
        if best_type is None:
            # No agreement - resolve conflict
            return self._resolve_conflict(signals)
        
        # Calculate ensemble confidence
        total_weight = sum(self.config.weights.get(s.source, 0.1) for s in best_signals)
        weighted_confidence = sum(
            s.confidence * self.config.weights.get(s.source, 0.1)
            for s in best_signals
        ) / total_weight if total_weight > 0 else 0
        
        if weighted_confidence < self.config.min_confidence_ensemble:
            return self._create_abstain_decision("AGREEMENT_LOW_CONFIDENCE")
        
        # Create decision
        return self._create_decision_from_signals(best_signals, "agreement", weighted_confidence)
    
    def _decide_by_weighted_vote(self, signals: List[StrategySignal]) -> EnsembleDecision:
        """
        Decide based on weighted voting.
        
        Each strategy's vote is weighted by its configured weight and confidence.
        """
        # Calculate weighted votes for each direction
        votes: Dict[SignalType, float] = {}
        
        for signal in signals:
            weight = self.config.weights.get(signal.source, 0.1)
            vote_strength = weight * signal.confidence
            
            if signal.signal_type not in votes:
                votes[signal.signal_type] = 0
            votes[signal.signal_type] += vote_strength
        
        # Find winning direction
        if not votes:
            return self._create_abstain_decision("NO_VOTES")
        
        winning_type = max(votes.keys(), key=lambda t: votes[t])
        winning_strength = votes[winning_type]
        
        # Normalize to confidence
        total_votes = sum(votes.values())
        confidence = winning_strength / total_votes if total_votes > 0 else 0
        
        if confidence < self.config.min_confidence_ensemble:
            return self._create_abstain_decision("VOTE_LOW_CONFIDENCE")
        
        # Get contributing signals
        contributing = [s for s in signals if s.signal_type == winning_type]
        
        return self._create_decision_from_signals(contributing, "weighted_vote", confidence)
    
    def _resolve_conflict(self, signals: List[StrategySignal]) -> EnsembleDecision:
        """
        Resolve conflicting signals.
        """
        method = self.config.conflict_resolution
        
        if method == "abstain":
            return self._create_abstain_decision("CONFLICT_ABSTAIN")
        
        elif method == "highest_confidence":
            best_signal = max(signals, key=lambda s: s.confidence)
            if best_signal.confidence >= self.config.min_confidence_single:
                return self._create_decision_from_signal(best_signal, "highest_confidence")
            else:
                return self._create_abstain_decision("CONFLICT_LOW_CONFIDENCE")
        
        elif method == "weighted_vote":
            return self._decide_by_weighted_vote(signals)
        
        else:
            return self._create_abstain_decision("UNKNOWN_CONFLICT_RESOLUTION")
    
    def _create_abstain_decision(self, reason: str) -> EnsembleDecision:
        """Create an abstain (HOLD) decision."""
        return EnsembleDecision(
            signal_type=SignalType.HOLD,
            confidence=1.0,  # High confidence in abstaining
            entry_price=None,
            stop_loss=None,
            take_profit=None,
            contributing_signals=list(self.current_signals.values()),
            reason_codes=[f"ENSEMBLE_{reason}"],
            decision_method="abstain",
        )
    
    def _create_decision_from_signal(
        self,
        signal: StrategySignal,
        method: str,
    ) -> EnsembleDecision:
        """Create a decision from a single signal."""
        return EnsembleDecision(
            signal_type=signal.signal_type,
            confidence=signal.confidence,
            entry_price=signal.entry_price,
            stop_loss=signal.stop_loss,
            take_profit=signal.take_profit,
            contributing_signals=[signal],
            reason_codes=signal.reason_codes + [f"ENSEMBLE_{method.upper()}"],
            decision_method=method,
        )
    
    def _create_decision_from_signals(
        self,
        signals: List[StrategySignal],
        method: str,
        confidence: float,
    ) -> EnsembleDecision:
        """Create a decision from multiple agreeing signals."""
        # Use the signal with highest confidence for price levels
        best_signal = max(signals, key=lambda s: s.confidence)
        
        # Aggregate reason codes
        all_codes = []
        for signal in signals:
            all_codes.extend(signal.reason_codes)
        all_codes.append(f"ENSEMBLE_{method.upper()}")
        all_codes.append(f"ENSEMBLE_AGREEMENT_{len(signals)}")
        
        return EnsembleDecision(
            signal_type=best_signal.signal_type,
            confidence=confidence,
            entry_price=best_signal.entry_price,
            stop_loss=best_signal.stop_loss,
            take_profit=best_signal.take_profit,
            contributing_signals=signals,
            reason_codes=list(set(all_codes)),
            decision_method=method,
        )
    
    def get_strategy_performance(self) -> Dict[str, Dict[str, Any]]:
        """
        Analyze performance of each strategy based on decision history.
        
        Returns:
            Performance metrics for each strategy
        """
        if not self.decision_history:
            return {}
        
        # Count contributions
        contributions: Dict[str, int] = {}
        agreements: Dict[str, int] = {}
        
        for decision in self.decision_history:
            for signal in decision.contributing_signals:
                source = signal.source
                contributions[source] = contributions.get(source, 0) + 1
                
                if signal.signal_type == decision.signal_type:
                    agreements[source] = agreements.get(source, 0) + 1
        
        # Calculate metrics
        performance = {}
        for source in contributions:
            total = contributions[source]
            agreed = agreements.get(source, 0)
            performance[source] = {
                "total_signals": total,
                "agreed_with_ensemble": agreed,
                "agreement_rate": agreed / total if total > 0 else 0,
            }
        
        return performance
    
    def adjust_weights(self, performance: Dict[str, Dict[str, Any]]) -> None:
        """
        Adjust strategy weights based on performance.
        
        This is a simple adjustment - in production you might use
        more sophisticated methods.
        """
        # Calculate new weights based on agreement rate
        new_weights = {}
        total = 0
        
        for source, metrics in performance.items():
            # Base weight on agreement rate (strategies that agree more get higher weight)
            weight = 0.1 + 0.4 * metrics.get("agreement_rate", 0.5)
            new_weights[source] = weight
            total += weight
        
        # Normalize
        for source in new_weights:
            new_weights[source] /= total
        
        # Apply with smoothing (don't change too drastically)
        for source in new_weights:
            old_weight = self.config.weights.get(source, 0.25)
            self.config.weights[source] = 0.7 * old_weight + 0.3 * new_weights[source]
        
        logger.info(f"Adjusted weights: {self.config.weights}")


def create_chimera_signal(
    signal_type: str,
    confidence: float,
    entry: Optional[float] = None,
    stop: Optional[float] = None,
    target: Optional[float] = None,
    reason_codes: Optional[List[str]] = None,
) -> StrategySignal:
    """Helper to create a Chimera strategy signal."""
    return StrategySignal(
        source="chimera",
        signal_type=SignalType(signal_type.lower()),
        confidence=confidence,
        entry_price=entry,
        stop_loss=stop,
        take_profit=target,
        reason_codes=reason_codes or [],
    )


def create_auctionflow_signal(
    signal_type: str,
    confidence: float,
    entry: Optional[float] = None,
    stop: Optional[float] = None,
    target: Optional[float] = None,
    reason_codes: Optional[List[str]] = None,
) -> StrategySignal:
    """Helper to create an AuctionFlow strategy signal."""
    return StrategySignal(
        source="auctionflow",
        signal_type=SignalType(signal_type.lower()),
        confidence=confidence,
        entry_price=entry,
        stop_loss=stop,
        take_profit=target,
        reason_codes=reason_codes or [],
    )


def create_rl_signal(
    signal_type: str,
    confidence: float,
    reason_codes: Optional[List[str]] = None,
) -> StrategySignal:
    """Helper to create an RL agent signal."""
    return StrategySignal(
        source="rl",
        signal_type=SignalType(signal_type.lower()),
        confidence=confidence,
        reason_codes=reason_codes or [],
    )


def create_sentiment_signal(
    signal_type: str,
    confidence: float,
    reason_codes: Optional[List[str]] = None,
) -> StrategySignal:
    """Helper to create a sentiment signal."""
    return StrategySignal(
        source="sentiment",
        signal_type=SignalType(signal_type.lower()),
        confidence=confidence,
        reason_codes=reason_codes or [],
    )
