"""Lazy-loadable dataset context store.

This package is intentionally dependency-light (stdlib + pandas) so it can run in
offline/CI environments. Parquet support is optional and only activates when the
required engine (e.g., pyarrow) is installed.
"""

from .store import DataContextStore, Timeframe

__all__ = ["DataContextStore", "Timeframe"]

