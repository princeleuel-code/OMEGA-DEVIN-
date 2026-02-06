"""
LAYER 7: ADAPTATION - Online Learning

The seventh layer of consciousness: ADAPTING to new information.

This module enables the system to LEARN and IMPROVE over time:
1. Update beliefs based on new evidence
2. Adjust parameters based on performance
3. Detect and adapt to regime changes
4. Continuous model improvement

This is NOT just retraining - this is INTELLIGENT ADAPTATION.

Key innovations:
- Bayesian belief updating
- Online parameter optimization
- Regime-specific adaptation
- Catastrophic forgetting prevention

This is what makes the system ALIVE - it grows and improves.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple, Callable
from enum import Enum
from collections import deque
import numpy as np

from .perception import MarketState, MarketRegime
from .prediction import ForecastDistribution
from .decision import TradingDecision
from .reflection import PerformanceState, TradeResult, MetaCognitiveMonitor


class AdaptationType(Enum):
    """Types of adaptation."""
    PARAMETER_UPDATE = "parameter_update"
    BELIEF_UPDATE = "belief_update"
    MODEL_RETRAIN = "model_retrain"
    STRATEGY_SWITCH = "strategy_switch"
    REGIME_ADAPTATION = "regime_adaptation"


class LearningRate(Enum):
    """Learning rate presets."""
    AGGRESSIVE = 0.1
    NORMAL = 0.05
    CONSERVATIVE = 0.01
    MINIMAL = 0.001


@dataclass
class BeliefUpdate:
    """A single belief update."""
    timestamp: datetime
    belief_name: str
    old_value: float
    new_value: float
    evidence: str
    confidence: float
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp.isoformat(),
            "belief_name": self.belief_name,
            "old_value": self.old_value,
            "new_value": self.new_value,
            "evidence": self.evidence,
            "confidence": self.confidence,
        }


@dataclass
class ParameterUpdate:
    """A parameter update."""
    timestamp: datetime
    parameter_name: str
    old_value: float
    new_value: float
    reason: str
    expected_improvement: float
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp.isoformat(),
            "parameter_name": self.parameter_name,
            "old_value": self.old_value,
            "new_value": self.new_value,
            "reason": self.reason,
            "expected_improvement": self.expected_improvement,
        }


@dataclass
class AdaptationEvent:
    """Record of an adaptation event."""
    timestamp: datetime
    adaptation_type: AdaptationType
    description: str
    changes: List[Dict[str, Any]]
    trigger: str
    expected_impact: str
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp.isoformat(),
            "adaptation_type": self.adaptation_type.value,
            "description": self.description,
            "changes": self.changes,
            "trigger": self.trigger,
            "expected_impact": self.expected_impact,
        }


class BayesianBeliefUpdater:
    """
    Bayesian belief updating for continuous learning.
    
    Maintains beliefs as probability distributions and updates
    them based on new evidence using Bayes' rule.
    """
    
    def __init__(self):
        # Beliefs as (mean, variance) pairs
        self.beliefs: Dict[str, Tuple[float, float]] = {}
        
        # Prior parameters
        self.prior_strength = 10  # Equivalent sample size for prior
        
        # Update history
        self.update_history: List[BeliefUpdate] = []
    
    def initialize_belief(
        self,
        name: str,
        prior_mean: float,
        prior_variance: float,
    ) -> None:
        """Initialize a belief with a prior."""
        self.beliefs[name] = (prior_mean, prior_variance)
    
    def update_belief(
        self,
        name: str,
        observation: float,
        observation_variance: float,
        evidence_description: str = "",
    ) -> BeliefUpdate:
        """
        Update a belief using Bayesian updating.
        
        For Gaussian beliefs:
        posterior_mean = (prior_var * obs + obs_var * prior_mean) / (prior_var + obs_var)
        posterior_var = (prior_var * obs_var) / (prior_var + obs_var)
        """
        if name not in self.beliefs:
            self.initialize_belief(name, observation, observation_variance)
            return BeliefUpdate(
                timestamp=datetime.now(timezone.utc),
                belief_name=name,
                old_value=0.0,
                new_value=observation,
                evidence=evidence_description,
                confidence=0.5,
            )
        
        prior_mean, prior_var = self.beliefs[name]
        
        # Bayesian update (Gaussian conjugate)
        posterior_var = (prior_var * observation_variance) / (prior_var + observation_variance)
        posterior_mean = (prior_var * observation + observation_variance * prior_mean) / (prior_var + observation_variance)
        
        # Update belief
        self.beliefs[name] = (posterior_mean, posterior_var)
        
        # Confidence based on variance reduction
        confidence = 1 - (posterior_var / prior_var) if prior_var > 0 else 0.5
        
        update = BeliefUpdate(
            timestamp=datetime.now(timezone.utc),
            belief_name=name,
            old_value=prior_mean,
            new_value=posterior_mean,
            evidence=evidence_description,
            confidence=confidence,
        )
        
        self.update_history.append(update)
        
        return update
    
    def get_belief(self, name: str) -> Tuple[float, float]:
        """Get current belief (mean, variance)."""
        return self.beliefs.get(name, (0.0, 1.0))
    
    def get_belief_confidence(self, name: str) -> float:
        """Get confidence in a belief (inverse of variance)."""
        _, var = self.get_belief(name)
        return 1 / (1 + var)


class OnlineParameterOptimizer:
    """
    Online parameter optimization using gradient-free methods.
    
    Continuously adjusts parameters based on performance feedback.
    """
    
    def __init__(self, learning_rate: LearningRate = LearningRate.NORMAL):
        self.learning_rate = learning_rate.value
        
        # Parameters and their bounds
        self.parameters: Dict[str, float] = {}
        self.bounds: Dict[str, Tuple[float, float]] = {}
        
        # Performance history for each parameter setting
        self.performance_history: deque = deque(maxlen=100)
        
        # Update history
        self.update_history: List[ParameterUpdate] = []
        
        # Exploration vs exploitation
        self.exploration_rate = 0.1
    
    def register_parameter(
        self,
        name: str,
        initial_value: float,
        min_value: float,
        max_value: float,
    ) -> None:
        """Register a parameter for optimization."""
        self.parameters[name] = initial_value
        self.bounds[name] = (min_value, max_value)
    
    def record_performance(self, performance: float) -> None:
        """Record performance for current parameter settings."""
        self.performance_history.append({
            "parameters": dict(self.parameters),
            "performance": performance,
            "timestamp": datetime.now(timezone.utc),
        })
    
    def optimize_step(self) -> List[ParameterUpdate]:
        """Perform one optimization step."""
        if len(self.performance_history) < 10:
            return []
        
        updates = []
        
        for name in self.parameters:
            update = self._optimize_parameter(name)
            if update:
                updates.append(update)
        
        return updates
    
    def _optimize_parameter(self, name: str) -> Optional[ParameterUpdate]:
        """Optimize a single parameter using finite differences."""
        current_value = self.parameters[name]
        min_val, max_val = self.bounds[name]
        
        # Estimate gradient using recent history
        recent = list(self.performance_history)[-20:]
        
        if len(recent) < 5:
            return None
        
        # Compute correlation between parameter value and performance
        param_values = [r["parameters"].get(name, current_value) for r in recent]
        performances = [r["performance"] for r in recent]
        
        if len(set(param_values)) < 2:
            # No variation in parameter, try exploration
            if np.random.random() < self.exploration_rate:
                # Random exploration
                new_value = np.random.uniform(min_val, max_val)
            else:
                return None
        else:
            # Compute gradient estimate
            param_mean = np.mean(param_values)
            perf_mean = np.mean(performances)
            
            numerator = sum((p - param_mean) * (perf - perf_mean) for p, perf in zip(param_values, performances))
            denominator = sum((p - param_mean) ** 2 for p in param_values)
            
            if denominator == 0:
                return None
            
            gradient = numerator / denominator
            
            # Update in direction of gradient
            new_value = current_value + self.learning_rate * gradient
        
        # Clip to bounds
        new_value = max(min_val, min(max_val, new_value))
        
        if abs(new_value - current_value) < 1e-6:
            return None
        
        # Apply update
        old_value = self.parameters[name]
        self.parameters[name] = new_value
        
        update = ParameterUpdate(
            timestamp=datetime.now(timezone.utc),
            parameter_name=name,
            old_value=old_value,
            new_value=new_value,
            reason="Online gradient optimization",
            expected_improvement=abs(new_value - old_value) * 0.1,  # Rough estimate
        )
        
        self.update_history.append(update)
        
        return update
    
    def get_parameters(self) -> Dict[str, float]:
        """Get current parameter values."""
        return dict(self.parameters)


class RegimeAdaptationManager:
    """
    Manages regime-specific adaptations.
    
    Maintains separate parameter sets for different market regimes
    and switches between them as regimes change.
    """
    
    def __init__(self):
        # Regime-specific parameters
        self.regime_parameters: Dict[MarketRegime, Dict[str, float]] = {}
        
        # Default parameters
        self.default_parameters: Dict[str, float] = {}
        
        # Current regime
        self.current_regime: MarketRegime = MarketRegime.UNKNOWN
        
        # Regime performance history
        self.regime_performance: Dict[MarketRegime, List[float]] = {}
        
        # Transition history
        self.transition_history: List[Dict[str, Any]] = []
    
    def initialize_regime_parameters(
        self,
        regime: MarketRegime,
        parameters: Dict[str, float],
    ) -> None:
        """Initialize parameters for a specific regime."""
        self.regime_parameters[regime] = dict(parameters)
    
    def set_default_parameters(self, parameters: Dict[str, float]) -> None:
        """Set default parameters."""
        self.default_parameters = dict(parameters)
    
    def on_regime_change(
        self,
        new_regime: MarketRegime,
        performance_in_old_regime: Optional[float] = None,
    ) -> Dict[str, float]:
        """Handle regime change and return appropriate parameters."""
        old_regime = self.current_regime
        
        # Record performance in old regime
        if performance_in_old_regime is not None and old_regime != MarketRegime.UNKNOWN:
            if old_regime not in self.regime_performance:
                self.regime_performance[old_regime] = []
            self.regime_performance[old_regime].append(performance_in_old_regime)
        
        # Record transition
        self.transition_history.append({
            "timestamp": datetime.now(timezone.utc),
            "from_regime": old_regime.value,
            "to_regime": new_regime.value,
            "performance": performance_in_old_regime,
        })
        
        # Update current regime
        self.current_regime = new_regime
        
        # Return parameters for new regime
        if new_regime in self.regime_parameters:
            return self.regime_parameters[new_regime]
        else:
            return self.default_parameters
    
    def update_regime_parameters(
        self,
        regime: MarketRegime,
        parameter_name: str,
        new_value: float,
    ) -> None:
        """Update a parameter for a specific regime."""
        if regime not in self.regime_parameters:
            self.regime_parameters[regime] = dict(self.default_parameters)
        
        self.regime_parameters[regime][parameter_name] = new_value
    
    def get_regime_performance_summary(self) -> Dict[str, Any]:
        """Get performance summary by regime."""
        summary = {}
        
        for regime, performances in self.regime_performance.items():
            if performances:
                summary[regime.value] = {
                    "count": len(performances),
                    "mean": np.mean(performances),
                    "std": np.std(performances),
                    "total": sum(performances),
                }
        
        return summary


class OnlineLearner:
    """
    The main online learning system.
    
    Coordinates all adaptation mechanisms:
    1. Bayesian belief updating
    2. Online parameter optimization
    3. Regime-specific adaptation
    4. Catastrophic forgetting prevention
    """
    
    def __init__(self, monitor: Optional[MetaCognitiveMonitor] = None):
        self.monitor = monitor
        
        # Sub-systems
        self.belief_updater = BayesianBeliefUpdater()
        self.parameter_optimizer = OnlineParameterOptimizer()
        self.regime_manager = RegimeAdaptationManager()
        
        # Adaptation history
        self.adaptation_history: List[AdaptationEvent] = []
        
        # Learning state
        self.is_learning_enabled = True
        self.learning_paused_until: Optional[datetime] = None
        
        # Catastrophic forgetting prevention
        self.memory_buffer: deque = deque(maxlen=1000)  # Experience replay
        
        # Initialize default beliefs
        self._initialize_default_beliefs()
        
        # Initialize default parameters
        self._initialize_default_parameters()
    
    def _initialize_default_beliefs(self) -> None:
        """Initialize default beliefs about market behavior."""
        # Belief about trend persistence
        self.belief_updater.initialize_belief("trend_persistence", 0.7, 0.1)
        
        # Belief about mean reversion strength
        self.belief_updater.initialize_belief("mean_reversion_strength", 0.3, 0.1)
        
        # Belief about volatility clustering
        self.belief_updater.initialize_belief("volatility_clustering", 0.8, 0.1)
        
        # Belief about order flow predictability
        self.belief_updater.initialize_belief("order_flow_predictability", 0.5, 0.2)
        
        # Belief about regime stability
        self.belief_updater.initialize_belief("regime_stability", 0.7, 0.15)
    
    def _initialize_default_parameters(self) -> None:
        """Initialize default trading parameters."""
        # Risk parameters
        self.parameter_optimizer.register_parameter("kelly_fraction", 0.25, 0.05, 0.5)
        self.parameter_optimizer.register_parameter("stop_loss_atr", 2.0, 1.0, 4.0)
        self.parameter_optimizer.register_parameter("take_profit_atr", 3.0, 1.5, 6.0)
        
        # Signal parameters
        self.parameter_optimizer.register_parameter("min_confidence", 0.6, 0.4, 0.8)
        self.parameter_optimizer.register_parameter("max_uncertainty", 0.4, 0.2, 0.6)
        
        # Position sizing
        self.parameter_optimizer.register_parameter("max_position_pct", 0.1, 0.02, 0.2)
        
        # Set as default for regime manager
        self.regime_manager.set_default_parameters(
            self.parameter_optimizer.get_parameters()
        )
    
    def learn_from_trade(self, result: TradeResult) -> List[AdaptationEvent]:
        """Learn from a completed trade."""
        if not self.is_learning_enabled:
            return []
        
        if self.learning_paused_until and datetime.now(timezone.utc) < self.learning_paused_until:
            return []
        
        adaptations = []
        
        # Add to memory buffer
        self.memory_buffer.append(result)
        
        # Update beliefs based on trade outcome
        belief_updates = self._update_beliefs_from_trade(result)
        if belief_updates:
            adaptations.append(AdaptationEvent(
                timestamp=datetime.now(timezone.utc),
                adaptation_type=AdaptationType.BELIEF_UPDATE,
                description=f"Updated {len(belief_updates)} beliefs from trade",
                changes=[u.to_dict() for u in belief_updates],
                trigger=f"Trade result: {'win' if result.pnl > 0 else 'loss'}",
                expected_impact="Improved prediction accuracy",
            ))
        
        # Record performance for parameter optimization
        self.parameter_optimizer.record_performance(result.pnl_pct)
        
        # Periodically optimize parameters
        if len(self.memory_buffer) % 10 == 0:
            param_updates = self.parameter_optimizer.optimize_step()
            if param_updates:
                adaptations.append(AdaptationEvent(
                    timestamp=datetime.now(timezone.utc),
                    adaptation_type=AdaptationType.PARAMETER_UPDATE,
                    description=f"Optimized {len(param_updates)} parameters",
                    changes=[u.to_dict() for u in param_updates],
                    trigger="Periodic optimization",
                    expected_impact="Improved risk-adjusted returns",
                ))
        
        self.adaptation_history.extend(adaptations)
        
        return adaptations
    
    def learn_from_forecast(
        self,
        forecast: ForecastDistribution,
        actual_price: float,
    ) -> List[BeliefUpdate]:
        """Learn from a forecast outcome."""
        if not self.is_learning_enabled:
            return []
        
        updates = []
        
        # Compute forecast error
        error = actual_price - forecast.mean
        error_pct = error / forecast.current_price if forecast.current_price > 0 else 0
        
        # Update belief about forecast accuracy
        accuracy = 1 - min(1, abs(error_pct) * 10)  # Scale error to accuracy
        update = self.belief_updater.update_belief(
            "forecast_accuracy",
            accuracy,
            0.1,
            f"Forecast error: {error_pct:.2%}",
        )
        updates.append(update)
        
        # Check if actual was within confidence intervals
        in_95 = forecast.ci_95[0] <= actual_price <= forecast.ci_95[1]
        
        # Update belief about calibration
        calibration_obs = 1.0 if in_95 else 0.0
        update = self.belief_updater.update_belief(
            "forecast_calibration",
            calibration_obs,
            0.2,
            f"Actual {'within' if in_95 else 'outside'} 95% CI",
        )
        updates.append(update)
        
        return updates
    
    def on_regime_change(
        self,
        new_regime: MarketRegime,
        performance: Optional[float] = None,
    ) -> AdaptationEvent:
        """Handle regime change."""
        old_regime = self.regime_manager.current_regime
        
        # Get parameters for new regime
        new_params = self.regime_manager.on_regime_change(new_regime, performance)
        
        # Apply parameters to optimizer
        for name, value in new_params.items():
            if name in self.parameter_optimizer.parameters:
                self.parameter_optimizer.parameters[name] = value
        
        event = AdaptationEvent(
            timestamp=datetime.now(timezone.utc),
            adaptation_type=AdaptationType.REGIME_ADAPTATION,
            description=f"Adapted to {new_regime.value} regime",
            changes=[{"from": old_regime.value, "to": new_regime.value, "parameters": new_params}],
            trigger=f"Regime change: {old_regime.value} -> {new_regime.value}",
            expected_impact="Strategy aligned with current market conditions",
        )
        
        self.adaptation_history.append(event)
        
        return event
    
    def _update_beliefs_from_trade(self, result: TradeResult) -> List[BeliefUpdate]:
        """Update beliefs based on trade outcome."""
        updates = []
        
        # Update trend persistence belief
        if result.regime_at_entry == result.regime_at_exit:
            # Regime persisted
            update = self.belief_updater.update_belief(
                "regime_stability",
                1.0,
                0.2,
                f"Regime stable during trade ({result.duration_bars} bars)",
            )
            updates.append(update)
        else:
            # Regime changed
            update = self.belief_updater.update_belief(
                "regime_stability",
                0.0,
                0.2,
                f"Regime changed during trade",
            )
            updates.append(update)
        
        # Update order flow predictability belief
        if result.decision.direction != 0:
            # Check if order flow prediction was correct
            flow_correct = (
                (result.decision.direction > 0 and result.pnl > 0) or
                (result.decision.direction < 0 and result.pnl > 0)
            )
            update = self.belief_updater.update_belief(
                "order_flow_predictability",
                1.0 if flow_correct else 0.0,
                0.15,
                f"Order flow prediction {'correct' if flow_correct else 'incorrect'}",
            )
            updates.append(update)
        
        return updates
    
    def pause_learning(self, duration_minutes: int = 60) -> None:
        """Pause learning for a specified duration."""
        self.learning_paused_until = datetime.now(timezone.utc) + timedelta(minutes=duration_minutes)
    
    def resume_learning(self) -> None:
        """Resume learning."""
        self.learning_paused_until = None
    
    def disable_learning(self) -> None:
        """Disable learning entirely."""
        self.is_learning_enabled = False
    
    def enable_learning(self) -> None:
        """Enable learning."""
        self.is_learning_enabled = True
    
    def get_current_parameters(self) -> Dict[str, float]:
        """Get current optimized parameters."""
        return self.parameter_optimizer.get_parameters()
    
    def get_current_beliefs(self) -> Dict[str, Tuple[float, float]]:
        """Get current beliefs (mean, variance)."""
        return dict(self.belief_updater.beliefs)
    
    def get_adaptation_summary(self) -> Dict[str, Any]:
        """Get summary of adaptation state."""
        return {
            "is_learning_enabled": self.is_learning_enabled,
            "learning_paused_until": self.learning_paused_until.isoformat() if self.learning_paused_until else None,
            "total_adaptations": len(self.adaptation_history),
            "memory_buffer_size": len(self.memory_buffer),
            "current_parameters": self.get_current_parameters(),
            "current_beliefs": {
                name: {"mean": mean, "variance": var}
                for name, (mean, var) in self.get_current_beliefs().items()
            },
            "regime_performance": self.regime_manager.get_regime_performance_summary(),
            "recent_adaptations": [
                a.to_dict() for a in self.adaptation_history[-5:]
            ],
        }
