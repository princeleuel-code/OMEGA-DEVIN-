from __future__ import annotations

from dataclasses import asdict
from datetime import datetime
from typing import Iterable, List, Optional

import pandas as pd

from .schema import Candle


REQUIRED_OHLCV_COLS = ["ts", "open", "high", "low", "close", "volume"]


def load_ohlcv_csv(path: str, *, tz: Optional[str] = None) -> pd.DataFrame:
    """Load OHLCV CSV. Required columns: ts, open, high, low, close, volume.

    ts can be ISO string or epoch ms. Output index is tz-aware if tz provided.
    """
    df = pd.read_csv(path)
    missing = [c for c in REQUIRED_OHLCV_COLS if c not in df.columns]
    if missing:
        raise ValueError(f"Missing columns: {missing}")

    # Parse timestamp
    if pd.api.types.is_numeric_dtype(df["ts"]):
        df["ts"] = pd.to_datetime(df["ts"], unit="ms", utc=True)
    else:
        df["ts"] = pd.to_datetime(df["ts"], utc=True)

    if tz:
        df["ts"] = df["ts"].dt.tz_convert(tz)

    df = df.sort_values("ts").reset_index(drop=True)
    return df


def df_to_candles(df: pd.DataFrame) -> List[Candle]:
    out: List[Candle] = []
    for row in df.itertuples(index=False):
        out.append(
            Candle(
                ts=row.ts.to_pydatetime(),
                open=float(row.open),
                high=float(row.high),
                low=float(row.low),
                close=float(row.close),
                volume=float(row.volume),
            )
        )
    return out
