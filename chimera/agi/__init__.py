"""
TRUE TRADING AGI - UNMATCHABLE
==============================
Multi-agent architecture for autonomous trading with recursive self-improvement.

Built from the ground up, inspired by Claude Code's architecture but
rebuilt for trading at the ATOM level.
"""

from .core import (
    TradingAGI,
    get_trading_agi,
    run_agi_analysis,
    get_agi_status,
    MetaAgent,
    PerceptionAgent,
    StrategyAgent,
    RiskAgent,
    ExecutionAgent,
    EvolutionAgent,
    BaseAgent,
    MemorySystem,
    Memory,
    MemoryType,
    ReasoningChain,
    Thought,
    ThoughtType,
    AgentType,
    SignalStrength,
)

from .advanced_reasoning import (
    AdvancedReasoningEngine,
    create_advanced_reasoning_engine,
    TreeOfThought,
    ThoughtNode,
    CausalReasoner,
    MetaCognition,
    ReasoningMode,
)

from .signal_intelligence import (
    SignalIntelligence,
    create_signal_intelligence,
    Signal,
    SignalCluster,
    SignalType,
    SignalSource,
    PriceActionAnalyzer,
    OrderFlowAnalyzer,
    MarketStructureAnalyzer,
    MomentumAnalyzer,
)

__all__ = [
    # Core AGI
    "TradingAGI",
    "get_trading_agi",
    "run_agi_analysis",
    "get_agi_status",
    
    # Agents
    "MetaAgent",
    "PerceptionAgent",
    "StrategyAgent",
    "RiskAgent",
    "ExecutionAgent",
    "EvolutionAgent",
    "BaseAgent",
    
    # Memory
    "MemorySystem",
    "Memory",
    "MemoryType",
    
    # Reasoning
    "ReasoningChain",
    "Thought",
    "ThoughtType",
    "AgentType",
    "SignalStrength",
    
    # Advanced Reasoning
    "AdvancedReasoningEngine",
    "create_advanced_reasoning_engine",
    "TreeOfThought",
    "ThoughtNode",
    "CausalReasoner",
    "MetaCognition",
    "ReasoningMode",
    
    # Signal Intelligence
    "SignalIntelligence",
    "create_signal_intelligence",
    "Signal",
    "SignalCluster",
    "SignalType",
    "SignalSource",
    "PriceActionAnalyzer",
    "OrderFlowAnalyzer",
    "MarketStructureAnalyzer",
    "MomentumAnalyzer",
]
