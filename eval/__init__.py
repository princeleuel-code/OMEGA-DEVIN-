"""Anti-overfit evaluation utilities for the research agent.

This wraps Chimera's existing walk-forward and robustness suite, and adds:
- Trade-order Monte Carlo (shuffle trades)
- Parameter sensitivity/stability bands
"""

from .trade_order_mc import trade_order_monte_carlo
from .sensitivity import generate_band_variants, parameter_stability_report

__all__ = ["trade_order_monte_carlo", "generate_band_variants", "parameter_stability_report"]

