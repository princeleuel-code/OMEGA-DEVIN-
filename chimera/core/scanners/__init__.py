"""Market scanner adapters.

Non-critical components used to propose candidate symbols for downstream engines.
They must fail safely (return stale cached data or empty results) and never be
required for core trading decisions.
"""

from .tvscreener_adapter import healthcheck as tvscreener_healthcheck
from .tvscreener_adapter import scan as tvscreener_scan

__all__ = [
    "tvscreener_scan",
    "tvscreener_healthcheck",
]

