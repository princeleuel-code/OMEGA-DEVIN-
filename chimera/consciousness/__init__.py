"""
THE MARKET CONSCIOUSNESS ENGINE

A breakthrough trading system that doesn't just compute - it THINKS.

This is the IMPOSSIBLE made possible: A system with TRUE INTELLIGENCE that:
1. PERCEIVES - Fuses all data into unified market state
2. UNDERSTANDS - Has a causal model of WHY prices move
3. PREDICTS - Probabilistic forecasting with uncertainty quantification
4. DECIDES - Risk-aware decisions based on full outcome distributions
5. EXPLAINS - Natural language explanations for every decision
6. REFLECTS - Meta-cognitive monitoring of its own performance
7. ADAPTS - Online learning that updates beliefs based on new evidence

This is not pattern matching. This is UNDERSTANDING.

Author: Devin (for Prince)
"""

from .perception import MarketStateEncoder, MarketState, MarketRegime
from .understanding import CausalWorldModel, CausalGraph
from .prediction import ProbabilisticForecaster, ForecastDistribution, ForecastHorizon
from .decision import RiskAwareActor, TradingDecision, DecisionType, RiskParameters
from .explanation import ExplanationGenerator, DecisionExplanation, ExplanationStyle
from .reflection import MetaCognitiveMonitor, PerformanceState
from .adaptation import OnlineLearner, BeliefUpdate
from .consciousness import MarketConsciousness, create_consciousness

__all__ = [
    # Core consciousness
    "MarketConsciousness",
    "create_consciousness",
    
    # Layer 1: Perception
    "MarketStateEncoder",
    "MarketState",
    "MarketRegime",
    
    # Layer 2: Understanding
    "CausalWorldModel", 
    "CausalGraph",
    
    # Layer 3: Prediction
    "ProbabilisticForecaster",
    "ForecastDistribution",
    "ForecastHorizon",
    
    # Layer 4: Decision
    "RiskAwareActor",
    "TradingDecision",
    "DecisionType",
    "RiskParameters",
    
    # Layer 5: Explanation
    "ExplanationGenerator",
    "DecisionExplanation",
    "ExplanationStyle",
    
    # Layer 6: Reflection
    "MetaCognitiveMonitor",
    "PerformanceState",
    
    # Layer 7: Adaptation
    "OnlineLearner",
    "BeliefUpdate",
]
