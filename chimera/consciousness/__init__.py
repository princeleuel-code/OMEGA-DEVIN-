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
from .delta_print import (
    DeltaPrintIntelligence,
    DeltaPrintAnalysis,
    DeltaPrintZone,
    DeltaLevel,
    BigTrade,
    AbsorptionPattern,
    VolumeLedge,
    ValueArea,
    create_delta_print_intelligence,
)
from .unified_intelligence import (
    UnifiedIntelligence,
    UnifiedAnalysis,
    UnifiedSignal,
    VPINAnalysis,
    RegimeAnalysis,
    MarketRegimeUnified,
    InformedTradingLevel,
    SignalStrength,
    create_unified_intelligence,
)
from .fundamental_intelligence import (
    FundamentalIntelligence,
    FundamentalAnalysis,
    FundamentalHealth,
    ValuationStatus,
    ValuationMetrics,
    FinancialHealthScore,
    EarningsIntelligence,
    InsiderActivity,
    create_fundamental_intelligence,
)
from .complete_intelligence import (
    CompleteIntelligence,
    CompleteAnalysis,
    CompleteSignal,
    CompleteSignalStrength,
    ConfluenceType,
    create_complete_intelligence,
)

# NEW BREAKTHROUGH MODULES
from .smc_intelligence import (
    SMCIntelligence,
    SMCAnalysis,
    SMCZone,
    SwingPoint,
    StructureBreakEvent,
    StructureType,
    ZoneType,
    StructureBreak,
)
from .mtf_intelligence import (
    MTFIntelligence,
    MTFConfluence,
    TimeframeAnalysis,
    TimeframeType,
    TrendDirection,
    AlignmentType,
)
from .adaptive_regime import (
    AdaptiveRegimeIntelligence,
    RegimeAnalysis as AdaptiveRegimeAnalysis,
    RegimeParameters,
    MarketRegime as AdaptiveMarketRegime,
    VolatilityState,
    TrendStrength,
)
from .position_sizing import (
    PositionSizingIntelligence,
    PositionSizeResult,
    PortfolioRisk,
    RiskLevel,
    DrawdownState,
)
from .ultimate_intelligence import (
    UltimateIntelligence,
    UltimateAnalysis,
    TradeSetup,
    IntelligenceSignal,
    SignalStrength as UltimateSignalStrength,
    TradeType,
)
from .vpe_intelligence import (
    VPEIntelligence,
    VPEAnalysis,
    VolumeProfile,
    VolumeNode,
    KeyLevel,
    SignalCandle,
    VPETradeSetup,
    VPShape,
    CandlePattern,
    SignalStrength as VPESignalStrength,
)

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
    
    # Delta Print Intelligence (SURPASSES DeepCharts)
    "DeltaPrintIntelligence",
    "DeltaPrintAnalysis",
    "DeltaPrintZone",
    "DeltaLevel",
    "BigTrade",
    "AbsorptionPattern",
    "VolumeLedge",
    "ValueArea",
    "create_delta_print_intelligence",
    
    # Unified Intelligence (THE BREAKTHROUGH)
    "UnifiedIntelligence",
    "UnifiedAnalysis",
    "UnifiedSignal",
    "VPINAnalysis",
    "RegimeAnalysis",
    "MarketRegimeUnified",
    "InformedTradingLevel",
    "SignalStrength",
    "create_unified_intelligence",
    
    # Fundamental Intelligence (DEXTER INTEGRATION)
    "FundamentalIntelligence",
    "FundamentalAnalysis",
    "FundamentalHealth",
    "ValuationStatus",
    "ValuationMetrics",
    "FinancialHealthScore",
    "EarningsIntelligence",
    "InsiderActivity",
    "create_fundamental_intelligence",
    
    # Complete Intelligence (ULTIMATE INTEGRATION)
    "CompleteIntelligence",
    "CompleteAnalysis",
    "CompleteSignal",
    "CompleteSignalStrength",
    "ConfluenceType",
    "create_complete_intelligence",
    
    # Smart Money Concepts (SMC) Intelligence
    "SMCIntelligence",
    "SMCAnalysis",
    "SMCZone",
    "SwingPoint",
    "StructureBreakEvent",
    "StructureType",
    "ZoneType",
    "StructureBreak",
    
    # Multi-Timeframe (MTF) Intelligence
    "MTFIntelligence",
    "MTFConfluence",
    "TimeframeAnalysis",
    "TimeframeType",
    "TrendDirection",
    "AlignmentType",
    
    # Adaptive Regime Intelligence
    "AdaptiveRegimeIntelligence",
    "AdaptiveRegimeAnalysis",
    "RegimeParameters",
    "AdaptiveMarketRegime",
    "VolatilityState",
    "TrendStrength",
    "DrawdownState",
    
    # Position Sizing Intelligence
    "PositionSizingIntelligence",
    "PositionSizeResult",
    "PortfolioRisk",
    "RiskLevel",
    
    # ULTIMATE INTELLIGENCE (THE PINNACLE)
    "UltimateIntelligence",
    "UltimateAnalysis",
    "TradeSetup",
    "IntelligenceSignal",
    "UltimateSignalStrength",
    "TradeType",
    
    # VPE INTELLIGENCE (FOREST KNIGHT'S 7-FIGURE SYSTEM)
    "VPEIntelligence",
    "VPEAnalysis",
    "VolumeProfile",
    "VolumeNode",
    "KeyLevel",
    "SignalCandle",
    "VPETradeSetup",
    "VPShape",
    "CandlePattern",
    "VPESignalStrength",
]
