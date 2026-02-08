# IMMORTAL ENGINE - Fault-Tolerant Trading System
# Inspired by Elixir/OTP "Let It Crash" Philosophy
# 
# Architecture:
# - Supervisor pattern (auto-restart failed workers)
# - Pipeline pattern (data flows like a sentence)
# - Process isolation (each strategy in its own process)
# - Fail-closed design (no trade on error)
#
# The "Code as a Sentence" Protocol:
# data |> normalize() |> analyze() |> veto() |> execute() |> log()

from .supervisor import Supervisor, Worker
from .pipeline import Pipeline
from .brain import TradingBrain
from .veto import VetoGate
from .truth_manifest import TruthManifest

__all__ = [
    'Supervisor',
    'Worker', 
    'Pipeline',
    'TradingBrain',
    'VetoGate',
    'TruthManifest'
]
