from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

import pandas as pd


class Timeframe:
    """Supported timeframes for the research agent context store."""

    M1 = "1m"
    M5 = "5m"
    H1 = "1h"
    H4 = "4h"
    D1 = "1d"

    _MINUTES = {
        M1: 1,
        M5: 5,
        H1: 60,
        H4: 240,
        D1: 1440,
    }

    _PANDAS_RULE = {
        M1: "1min",
        M5: "5min",
        H1: "1H",
        H4: "4H",
        D1: "1D",
    }

    @classmethod
    def minutes(cls, tf: str) -> int:
        if tf not in cls._MINUTES:
            raise ValueError(f"Unsupported timeframe: {tf!r}")
        return int(cls._MINUTES[tf])

    @classmethod
    def pandas_rule(cls, tf: str) -> str:
        if tf not in cls._PANDAS_RULE:
            raise ValueError(f"Unsupported timeframe: {tf!r}")
        return str(cls._PANDAS_RULE[tf])

    @classmethod
    def all(cls) -> List[str]:
        return [cls.M1, cls.M5, cls.H1, cls.H4, cls.D1]


@dataclass(frozen=True)
class OHLCVSource:
    symbol: str
    timeframe: str
    path: Path
    fmt: str  # "csv" | "parquet"
    timestamp_col: str = "timestamp"
    open_col: str = "open"
    high_col: str = "high"
    low_col: str = "low"
    close_col: str = "close"
    volume_col: str = "volume"


@dataclass(frozen=True)
class TickSource:
    """Optional tick/quote source (bid/ask).

    The research agent does not require ticks, but the context store supports
    them for future microstructure modules.
    """

    symbol: str
    path: Path
    fmt: str  # "csv" | "parquet"
    timestamp_col: str = "timestamp"
    bid_col: str = "bid"
    ask_col: str = "ask"


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _normalize_ohlcv_df(df: pd.DataFrame, src: OHLCVSource) -> pd.DataFrame:
    cols = {
        src.timestamp_col: "timestamp",
        src.open_col: "open",
        src.high_col: "high",
        src.low_col: "low",
        src.close_col: "close",
        src.volume_col: "volume",
    }
    missing = [c for c in cols.keys() if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required OHLCV columns: {missing}")
    out = df[list(cols.keys())].rename(columns=cols).copy()
    out["timestamp"] = pd.to_datetime(out["timestamp"], utc=True, errors="raise")
    out = out.sort_values("timestamp")
    out = out.set_index("timestamp")
    # Ensure numeric dtype.
    for c in ["open", "high", "low", "close", "volume"]:
        out[c] = pd.to_numeric(out[c], errors="coerce")
    out = out.dropna(subset=["open", "high", "low", "close"])
    if "volume" in out.columns:
        out["volume"] = out["volume"].fillna(0.0)
    return out


def _normalize_ticks_df(df: pd.DataFrame, src: TickSource) -> pd.DataFrame:
    cols = {
        src.timestamp_col: "timestamp",
        src.bid_col: "bid",
        src.ask_col: "ask",
    }
    missing = [c for c in cols.keys() if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required tick columns: {missing}")
    out = df[list(cols.keys())].rename(columns=cols).copy()
    out["timestamp"] = pd.to_datetime(out["timestamp"], utc=True, errors="raise")
    out = out.sort_values("timestamp")
    out = out.set_index("timestamp")
    out["bid"] = pd.to_numeric(out["bid"], errors="coerce")
    out["ask"] = pd.to_numeric(out["ask"], errors="coerce")
    out = out.dropna(subset=["bid", "ask"])
    out["mid"] = (out["bid"] + out["ask"]) / 2.0
    out["spread"] = out["ask"] - out["bid"]
    return out


def _resample_ohlcv(df: pd.DataFrame, rule: str) -> pd.DataFrame:
    # Strict OHLCV aggregation; drops incomplete buckets.
    agg = {
        "open": "first",
        "high": "max",
        "low": "min",
        "close": "last",
        "volume": "sum",
    }
    res = (
        df.resample(rule, label="right", closed="right")
        .agg(agg)
        .dropna(subset=["open", "high", "low", "close"])
    )
    return res


class DataContextStore:
    """Lazy-loadable context store for OHLCV datasets.

    - Registers per-symbol per-timeframe sources (CSV or Parquet)
    - Loads only on first access (lazy)
    - Can derive higher timeframes by resampling the nearest available lower TF
    """

    def __init__(self) -> None:
        self._sources: Dict[Tuple[str, str], OHLCVSource] = {}
        self._cache: Dict[Tuple[str, str], pd.DataFrame] = {}
        self._file_hash: Dict[Path, str] = {}
        self._load_counts: Dict[Tuple[str, str], int] = {}
        self._tick_sources: Dict[str, TickSource] = {}
        self._tick_cache: Dict[str, pd.DataFrame] = {}
        self._tick_load_counts: Dict[str, int] = {}

    def register_ohlcv(self, src: OHLCVSource) -> None:
        if src.fmt not in ("csv", "parquet"):
            raise ValueError(f"Unsupported fmt: {src.fmt!r}")
        if not src.path.exists():
            raise FileNotFoundError(str(src.path))
        key = (src.symbol, src.timeframe)
        self._sources[key] = src
        # Reset any cached frames for this key.
        self._cache.pop(key, None)
        self._load_counts.pop(key, None)

    def dataset_hash(self, *, symbol: str, timeframe: str) -> str:
        src = self._get_source_or_raise(symbol, timeframe)
        if src.path not in self._file_hash:
            self._file_hash[src.path] = _sha256_file(src.path)
        return self._file_hash[src.path]

    def tick_dataset_hash(self, *, symbol: str) -> str:
        src = self._get_tick_source_or_raise(symbol)
        if src.path not in self._file_hash:
            self._file_hash[src.path] = _sha256_file(src.path)
        return self._file_hash[src.path]

    def debug_stats(self) -> Dict[str, object]:
        return {
            "sources": sorted([f"{s}:{tf}" for (s, tf) in self._sources.keys()]),
            "cache_keys": sorted([f"{s}:{tf}" for (s, tf) in self._cache.keys()]),
            "load_counts": {f"{s}:{tf}": n for (s, tf), n in self._load_counts.items()},
            "tick_sources": sorted(list(self._tick_sources.keys())),
            "tick_cache_keys": sorted(list(self._tick_cache.keys())),
            "tick_load_counts": dict(self._tick_load_counts),
        }

    def get_ohlcv(
        self,
        *,
        symbol: str,
        timeframe: str,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
        limit: Optional[int] = None,
    ) -> pd.DataFrame:
        """Fetch OHLCV bars for symbol/timeframe.

        If the requested timeframe is not explicitly registered, the store will
        attempt to derive it by resampling from the closest available lower TF.
        """

        df = self._get_or_build(symbol=symbol, timeframe=timeframe)

        out = df
        if start is not None:
            out = out[out.index >= pd.Timestamp(start, tz="UTC")]
        if end is not None:
            out = out[out.index <= pd.Timestamp(end, tz="UTC")]
        if limit is not None:
            out = out.tail(int(limit))
        return out.copy()

    def register_ticks(self, src: TickSource) -> None:
        if src.fmt not in ("csv", "parquet"):
            raise ValueError(f"Unsupported fmt: {src.fmt!r}")
        if not src.path.exists():
            raise FileNotFoundError(str(src.path))
        self._tick_sources[src.symbol] = src
        self._tick_cache.pop(src.symbol, None)
        self._tick_load_counts.pop(src.symbol, None)

    def get_ticks(
        self,
        *,
        symbol: str,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
        limit: Optional[int] = None,
    ) -> pd.DataFrame:
        df = self._get_or_load_ticks(symbol=symbol)

        out = df
        if start is not None:
            out = out[out.index >= pd.Timestamp(start, tz="UTC")]
        if end is not None:
            out = out[out.index <= pd.Timestamp(end, tz="UTC")]
        if limit is not None:
            out = out.tail(int(limit))
        return out.copy()

    def _get_source_or_raise(self, symbol: str, timeframe: str) -> OHLCVSource:
        key = (symbol, timeframe)
        if key not in self._sources:
            raise KeyError(f"No registered OHLCV source for {symbol}:{timeframe}")
        return self._sources[key]

    def _get_tick_source_or_raise(self, symbol: str) -> TickSource:
        if symbol not in self._tick_sources:
            raise KeyError(f"No registered tick source for {symbol}")
        return self._tick_sources[symbol]

    def _get_or_build(self, *, symbol: str, timeframe: str) -> pd.DataFrame:
        key = (symbol, timeframe)
        if key in self._cache:
            return self._cache[key]

        # Load directly if available.
        if key in self._sources:
            df = self._load_source(self._sources[key])
            self._cache[key] = df
            return df

        # Otherwise derive by resampling.
        target_min = Timeframe.minutes(timeframe)
        candidates: List[Tuple[int, str]] = []
        for (sym, tf), _src in self._sources.items():
            if sym != symbol:
                continue
            m = Timeframe.minutes(tf)
            if m <= target_min and target_min % m == 0:
                candidates.append((m, tf))
        if not candidates:
            raise KeyError(f"No source available to derive {symbol}:{timeframe}")

        # Choose the closest lower TF (max minutes).
        _, base_tf = max(candidates, key=lambda x: x[0])
        base_df = self._get_or_build(symbol=symbol, timeframe=base_tf)
        rule = Timeframe.pandas_rule(timeframe)
        derived = _resample_ohlcv(base_df, rule)
        self._cache[key] = derived
        return derived

    def _load_source(self, src: OHLCVSource) -> pd.DataFrame:
        key = (src.symbol, src.timeframe)
        self._load_counts[key] = int(self._load_counts.get(key, 0)) + 1

        if src.fmt == "csv":
            df = pd.read_csv(src.path)
            return _normalize_ohlcv_df(df, src)

        # Parquet is optional; we only attempt it if the engine exists.
        try:
            df = pd.read_parquet(src.path)
        except Exception as e:  # pragma: no cover (engine-dependent)
            raise ImportError(
                "Parquet support requires an installed engine (e.g., pyarrow). "
                f"Failed to read {src.path}: {type(e).__name__}: {e}"
            ) from e
        return _normalize_ohlcv_df(df, src)

    def _get_or_load_ticks(self, *, symbol: str) -> pd.DataFrame:
        if symbol in self._tick_cache:
            return self._tick_cache[symbol]

        src = self._get_tick_source_or_raise(symbol)
        self._tick_load_counts[symbol] = int(self._tick_load_counts.get(symbol, 0)) + 1

        if src.fmt == "csv":
            df = pd.read_csv(src.path)
            out = _normalize_ticks_df(df, src)
            self._tick_cache[symbol] = out
            return out

        try:
            df = pd.read_parquet(src.path)
        except Exception as e:  # pragma: no cover (engine-dependent)
            raise ImportError(
                "Parquet support requires an installed engine (e.g., pyarrow). "
                f"Failed to read {src.path}: {type(e).__name__}: {e}"
            ) from e
        out = _normalize_ticks_df(df, src)
        self._tick_cache[symbol] = out
        return out

    def to_json_registry(self) -> str:
        """Return a compact JSON snapshot of registered datasets."""
        rows = []
        for (sym, tf), src in sorted(self._sources.items()):
            rows.append(
                {
                    "symbol": sym,
                    "timeframe": tf,
                    "path": str(src.path),
                    "fmt": src.fmt,
                }
            )
        ticks = [{"symbol": sym, "path": str(src.path), "fmt": src.fmt} for sym, src in sorted(self._tick_sources.items())]
        return json.dumps({"datasets": rows, "ticks": ticks}, indent=2)
