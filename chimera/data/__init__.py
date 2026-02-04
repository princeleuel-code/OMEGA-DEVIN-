"""
Data layer - ingestion, integrity, and features
"""

from .loader import DataLoader, OHLCV
from .integrity import IntegrityChecker, IntegrityResult
from .features import FeatureEngine
