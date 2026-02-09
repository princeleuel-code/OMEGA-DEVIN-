"""Backtest wrappers for the research agent.

We reuse the existing Chimera backtest engine to avoid duplicating core trading
simulation logic.
"""

from .engine import run_backtest, symbol_backtest_config

__all__ = ["run_backtest", "symbol_backtest_config"]

