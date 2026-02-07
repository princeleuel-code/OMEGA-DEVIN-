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

# NEW: 3 Trader YouTube Transcript Intelligence Modules
from .fractal_swing_intelligence import (
    FractalSwingIntelligence,
    FractalSwingAnalysis,
    SwingPoint as FractalSwingPoint,
    PreviousRange,
    ProminentWick,
    LiquiditySweep,
    RoundingPattern,
    SwingDirection,
    RoundingType,
    SweepType,
)
from .manipulation_candle_intelligence import (
    ManipulationCandleIntelligence,
    ManipulationAnalysis,
    ManipulationCandle,
    AbsorptionZone,
    DeltaAnalysis as ManipulationDeltaAnalysis,
    SessionProfile,
    ManipulationType,
    SessionType,
    DeltaDirection,
)
from .multi_profile_volume_intelligence import (
    MultiProfileVolumeIntelligence,
    MultiProfileAnalysis,
    VolumeProfile as MultiVolumeProfile,
    VolumeLevel,
    InstitutionalZone,
    ProfileConfluence,
    ProfileType,
    ProfileShape,
    ZoneType as InstitutionalZoneType,
)

# NEW: 4th YouTube Transcript - Session & Trade Management Intelligence
from .session_trade_management import (
    SessionTradeManagementIntelligence,
    SessionTradeAnalysis,
    SessionInfo,
    TradeManagementPlan,
    PartialCloseLevel,
    NewsEvent,
    TradingSession,
    SessionQuality,
    NewsImpact,
    TradeManagementAction,
    PsychologyState,
)

# BREAKTHROUGH: Self-Evolving Intelligence Engine
from .self_evolving_intelligence import (
    SelfEvolvingIntelligence,
    EvolutionAnalysis,
    EvolutionState,
    SignalStats,
    TradeRecord,
    EvolutionPhase,
    SignalPerformance,
    MarketRegime as EvolutionMarketRegime,
)

# BREAKTHROUGH: Institutional Flow Detection
from .institutional_flow_detection import (
    InstitutionalFlowDetection,
    InstitutionalFlowAnalysis,
    LargeOrderSignature,
    AccumulationDistributionPhase,
    SmartMoneyZone,
    LiquidityPool,
    InstitutionalActivity,
    OrderFlowType,
    LiquidityType,
    IcebergType,
)

# BREAKTHROUGH: Cross-Asset Correlation Intelligence
from .cross_asset_correlation import (
    CrossAssetCorrelationIntelligence,
    CrossAssetAnalysis,
    AssetCorrelation,
    DXYImpact,
    RiskSentiment,
    LeadingIndicator,
    IntermarketDivergence,
    MarketSentiment,
    CorrelationStrength,
    DivergenceType,
)

# UNMATCHABLE: Trading AGI - The Ultimate Self-Evolving Intelligence
from .trading_agi import (
    TradingAGI,
    get_trading_agi,
    run_agi_cycle,
    run_evolution_cycle,
    ThoughtChain,
    CodeImprovement,
    EvolutionGenome,
    AGIMode,
    ReasoningDepth,
    ReasoningEngine,
    CodeWriterEngine,
    EvolutionEngine,
    MarketAnalyzer,
)

# UNMATCHABLE: AGI Orchestrator - The Central Brain
from .agi_orchestrator import (
    AGIOrchestrator,
    get_orchestrator,
    run_agi_analysis,
    run_agi_learning,
    run_agi_evolution,
    get_agi_status,
    AGIState,
    AGIDecision,
    LearningEvent,
    ClawdbotIntegration,
)

# UNMATCHABLE: Self-Evolution Loop - Autonomous Improvement
from .self_evolution_loop import (
    SelfEvolutionLoop,
    get_evolution_loop,
    run_self_evolution,
    EvolutionPhase as SelfEvolutionPhase,
    EvolutionCandidate,
    EvolutionCycle,
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
    
    # FRACTAL SWING INTELLIGENCE (Dave's 4-6 Swing Rule)
    "FractalSwingIntelligence",
    "FractalSwingAnalysis",
    "FractalSwingPoint",
    "PreviousRange",
    "ProminentWick",
    "LiquiditySweep",
    "RoundingPattern",
    "SwingDirection",
    "RoundingType",
    "SweepType",
    
    # MANIPULATION CANDLE INTELLIGENCE (Funded Brothers)
    "ManipulationCandleIntelligence",
    "ManipulationAnalysis",
    "ManipulationCandle",
    "AbsorptionZone",
    "ManipulationDeltaAnalysis",
    "SessionProfile",
    "ManipulationType",
    "SessionType",
    "DeltaDirection",
    
    # MULTI-PROFILE VOLUME INTELLIGENCE (5 Volume Profiles)
    "MultiProfileVolumeIntelligence",
    "MultiProfileAnalysis",
    "MultiVolumeProfile",
    "VolumeLevel",
    "InstitutionalZone",
    "ProfileConfluence",
    "ProfileType",
    "ProfileShape",
    "InstitutionalZoneType",
    
    # SESSION & TRADE MANAGEMENT INTELLIGENCE (4th YouTube Transcript)
    "SessionTradeManagementIntelligence",
    "SessionTradeAnalysis",
    "SessionInfo",
    "TradeManagementPlan",
    "PartialCloseLevel",
    "NewsEvent",
    "TradingSession",
    "SessionQuality",
    "NewsImpact",
    "TradeManagementAction",
    "PsychologyState",
    
    # BREAKTHROUGH: Self-Evolving Intelligence Engine
    "SelfEvolvingIntelligence",
    "EvolutionAnalysis",
    "EvolutionState",
    "SignalStats",
    "TradeRecord",
    "EvolutionPhase",
    "SignalPerformance",
    "EvolutionMarketRegime",
    
    # BREAKTHROUGH: Institutional Flow Detection
    "InstitutionalFlowDetection",
    "InstitutionalFlowAnalysis",
    "LargeOrderSignature",
    "AccumulationDistributionPhase",
    "SmartMoneyZone",
    "LiquidityPool",
    "InstitutionalActivity",
    "OrderFlowType",
    "LiquidityType",
    "IcebergType",
    
    # BREAKTHROUGH: Cross-Asset Correlation Intelligence
    "CrossAssetCorrelationIntelligence",
    "CrossAssetAnalysis",
    "AssetCorrelation",
    "DXYImpact",
    "RiskSentiment",
    "LeadingIndicator",
    "IntermarketDivergence",
    "MarketSentiment",
    "CorrelationStrength",
    "DivergenceType",
    
    # UNMATCHABLE: Trading AGI - The Ultimate Self-Evolving Intelligence
    "TradingAGI",
    "get_trading_agi",
    "run_agi_cycle",
    "run_evolution_cycle",
    "ThoughtChain",
    "CodeImprovement",
    "EvolutionGenome",
    "AGIMode",
    "ReasoningDepth",
    "ReasoningEngine",
    "CodeWriterEngine",
    "EvolutionEngine",
    "MarketAnalyzer",
    
    # UNMATCHABLE: AGI Orchestrator - The Central Brain
    "AGIOrchestrator",
    "get_orchestrator",
    "run_agi_analysis",
    "run_agi_learning",
    "run_agi_evolution",
    "get_agi_status",
    "AGIState",
    "AGIDecision",
    "LearningEvent",
    "ClawdbotIntegration",
    
    # UNMATCHABLE: Self-Evolution Loop - Autonomous Improvement
    "SelfEvolutionLoop",
    "get_evolution_loop",
    "run_self_evolution",
    "SelfEvolutionPhase",
    "EvolutionCandidate",
    "EvolutionCycle",
]
