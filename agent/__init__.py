"""Recursive research agent components.

This package implements a lightweight, offline-safe "Planner -> Executor -> Critic"
loop for designing and evaluating trading hypotheses on local datasets.

It is intentionally dependency-light (stdlib + pandas + existing Chimera modules).
"""

from .orchestrator import ResearchAgent, ResearchAgentConfig
from .registry import ExperimentRegistry

__all__ = ["ResearchAgent", "ResearchAgentConfig", "ExperimentRegistry"]

