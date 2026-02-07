"""
Agents Module

Self-improvement and research agents for the trading system.
These agents analyze performance, propose improvements, and help
the system evolve over time.
"""

from agents.autonomy_agent import (
    AutonomyAgent,
    ResearchTask,
    Improvement,
    AgentConfig,
)

__all__ = [
    "AutonomyAgent",
    "ResearchTask",
    "Improvement",
    "AgentConfig",
]
