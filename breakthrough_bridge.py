#!/usr/bin/env python3
"""
Breakthrough bridge: Aether-style regime gating for Omega/Sakana workflows.

Purpose:
- Use entropy + seam as "tradable vs untradable" gate.
- Keep direction logic simple and separate.
- Produce walk-forward threshold recommendations with no look-ahead.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd


ANNUALIZATION_MAP = {
    "1m": np.sqrt(60 * 24 * 252),
    "5m": np.sqrt(12 * 24 * 252),
    "15m": np.sqrt(4 * 24 * 252),
    "1h": np.sqrt(24 * 252),
    "4h": np.sqrt(6 * 252),
    "1d": np.sqrt(252),
}


@dataclass(frozen=True)
class Thresholds:
    entropy_thr: float
    seam_thr: float


def _normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = [
        c.strip().lower().replace("<", "").replace(">", "").replace(" ", "_")
        for c in df.columns
    ]
    rename_map = {
        "time": "datetime",
        "date": "datetime",
        "tickvol": "tick_volume",
    }
    for src, dst in rename_map.items():
        if src in df.columns and dst not in df.columns:
            df = df.rename(columns={src: dst})
    if "datetime" in df.columns:
        df["datetime"] = pd.to_datetime(df["datetime"], errors="coerce")
    required = {"high", "low", "close"}
    missing = required.difference(df.columns)
    if missing:
        raise ValueError(f"Missing required columns: {sorted(missing)}")
    for c in ["open", "high", "low", "close"]:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")
    df = df.dropna(subset=["high", "low", "close"]).reset_index(drop=True)
    return df


def compute_features(df: pd.DataFrame, entropy_window: int = 64) -> pd.DataFrame:
    close = df["close"]
    ret = close.pct_change().fillna(0.0)
    trend = close.ewm(span=20, adjust=False).mean() > close.ewm(span=80, adjust=False).mean()

    # Rolling Shannon entropy of return buckets (normalized to 0..1)
    bins = np.array([-np.inf, -0.003, -0.002, -0.001, 0, 0.001, 0.002, 0.003, np.inf])
    entropy = np.full(len(df), np.nan)
    ret_vals = ret.values
    norm_denom = np.log(len(bins) - 1)
    for i in range(entropy_window, len(df)):
        chunk = ret_vals[i - entropy_window : i]
        hist, _ = np.histogram(chunk, bins=bins)
        if hist.sum() == 0:
            entropy[i] = 1.0
            continue
        p = hist / hist.sum()
        p = p[p > 0]
        entropy[i] = float((-np.sum(p * np.log(p))) / (norm_denom + 1e-12))

    # Seam proxy: ATR acceleration z-score
    prev_close = close.shift(1)
    tr = pd.concat(
        [
            (df["high"] - df["low"]).abs(),
            (df["high"] - prev_close).abs(),
            (df["low"] - prev_close).abs(),
        ],
        axis=1,
    ).max(axis=1)
    atr = tr.rolling(32).mean()
    seam = (atr - atr.rolling(16).mean()) / (atr.rolling(64).std() + 1e-9)

    out = pd.DataFrame(
        {
            "datetime": df["datetime"] if "datetime" in df.columns else pd.NaT,
            "close": close,
            "ret": ret,
            "fwd_ret": ret.shift(-1),
            "abs_fwd_ret": ret.shift(-1).abs(),
            "trend": trend,
            "entropy": entropy,
            "seam": seam,
        }
    )
    out = out.dropna().reset_index(drop=True)
    return out


def sharpe_proxy(series: pd.Series, annualizer: float) -> float:
    if len(series) < 2:
        return 0.0
    std = float(series.std())
    if std <= 1e-12:
        return 0.0
    return float(series.mean() / std * annualizer)


def evaluate_slice(
    df: pd.DataFrame,
    thresholds: Thresholds,
    annualizer: float,
) -> Dict[str, float]:
    base = df[df["trend"]]
    gated = df[(df["trend"]) & (df["entropy"] <= thresholds.entropy_thr) & (df["seam"] >= thresholds.seam_thr)]

    base_r = base["fwd_ret"]
    gated_r = gated["fwd_ret"]

    return {
        "base_trades": float(len(base)),
        "gated_trades": float(len(gated)),
        "base_hit": float((base_r > 0).mean()) if len(base_r) else float("nan"),
        "gated_hit": float((gated_r > 0).mean()) if len(gated_r) else float("nan"),
        "base_sharpe": sharpe_proxy(base_r, annualizer),
        "gated_sharpe": sharpe_proxy(gated_r, annualizer),
        "base_abs_move": float(base["abs_fwd_ret"].mean()) if len(base) else float("nan"),
        "gated_abs_move": float(gated["abs_fwd_ret"].mean()) if len(gated) else float("nan"),
    }


def find_thresholds_train(
    train_df: pd.DataFrame,
    annualizer: float,
    min_train_trades: int,
) -> Thresholds | None:
    ent_q = [0.2, 0.25, 0.3, 0.35, 0.4, 0.45, 0.5, 0.55, 0.6, 0.65]
    seam_q = [0.5, 0.55, 0.6, 0.65, 0.7, 0.75, 0.8, 0.85, 0.9]
    best: Tuple[float, float, float] | None = None  # (obj, ent_thr, seam_thr)

    for eq in ent_q:
        e_thr = float(train_df["entropy"].quantile(eq))
        for sq in seam_q:
            s_thr = float(train_df["seam"].quantile(sq))
            sel = train_df[
                (train_df["trend"])
                & (train_df["entropy"] <= e_thr)
                & (train_df["seam"] >= s_thr)
            ]
            if len(sel) < min_train_trades:
                continue
            r = sel["fwd_ret"]
            sh = sharpe_proxy(r, annualizer)
            # Penalize low-turnover parameter sets.
            obj = sh * min(1.0, len(sel) / 2500.0)
            if best is None or obj > best[0]:
                best = (obj, e_thr, s_thr)

    if best is None:
        return None
    return Thresholds(entropy_thr=best[1], seam_thr=best[2])


def walk_forward_search(
    feat_df: pd.DataFrame,
    timeframe: str,
    folds: int,
    min_train_trades: int,
    min_test_trades: int,
) -> Dict[str, object]:
    annualizer = ANNUALIZATION_MAP.get(timeframe.lower(), ANNUALIZATION_MAP["1h"])
    n = len(feat_df)
    fold_size = n // (folds + 1)
    if fold_size < 500:
        raise ValueError("Not enough rows for requested folds.")

    fold_reports: List[Dict[str, float]] = []
    used_thresholds: List[Thresholds] = []
    for k in range(folds):
        train_end = (k + 1) * fold_size
        test_end = min((k + 2) * fold_size, n)
        train_df = feat_df.iloc[:train_end]
        test_df = feat_df.iloc[train_end:test_end]
        if len(test_df) < 250:
            continue

        thr = find_thresholds_train(train_df, annualizer=annualizer, min_train_trades=min_train_trades)
        if thr is None:
            continue

        metrics = evaluate_slice(test_df, thresholds=thr, annualizer=annualizer)
        if metrics["gated_trades"] < float(min_test_trades):
            continue
        metrics["fold"] = float(k + 1)
        metrics["entropy_thr"] = float(thr.entropy_thr)
        metrics["seam_thr"] = float(thr.seam_thr)
        fold_reports.append(metrics)
        used_thresholds.append(thr)

    if not fold_reports:
        raise RuntimeError("No valid folds produced threshold candidates.")

    rep = pd.DataFrame(fold_reports)
    better = rep["gated_sharpe"] > rep["base_sharpe"]
    winners = rep[better]
    thr_source = winners if len(winners) > 0 else rep

    recommendation = {
        "entropy_threshold": float(thr_source["entropy_thr"].median()),
        "seam_threshold": float(thr_source["seam_thr"].median()),
    }
    summary = {
        "folds_evaluated": int(len(rep)),
        "gated_better_folds": int(better.sum()),
        "mean_base_sharpe": float(rep["base_sharpe"].mean()),
        "mean_gated_sharpe": float(rep["gated_sharpe"].mean()),
        "median_base_sharpe": float(rep["base_sharpe"].median()),
        "median_gated_sharpe": float(rep["gated_sharpe"].median()),
        "mean_trade_reduction": float((1.0 - rep["gated_trades"] / rep["base_trades"]).mean()),
        "mean_abs_move_uplift": float((rep["gated_abs_move"] - rep["base_abs_move"]).mean()),
    }

    return {
        "timeframe": timeframe,
        "rows_used": int(n),
        "recommendation": recommendation,
        "summary": summary,
        "folds": rep.to_dict(orient="records"),
        "disclaimer": (
            "Research output only. Regime gates must be re-validated with transaction costs, "
            "walk-forward retraining, and live paper-trading before deployment."
        ),
    }


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Aether/Omega breakthrough bridge (walk-forward regime gate search).")
    p.add_argument("--data", required=True, help="Path to OHLC CSV (e.g. XAUUSD_H1.csv).")
    p.add_argument("--timeframe", default="1h", choices=list(ANNUALIZATION_MAP.keys()))
    p.add_argument("--folds", type=int, default=6)
    p.add_argument("--min-train-trades", type=int, default=300)
    p.add_argument("--min-test-trades", type=int, default=100)
    p.add_argument("--output", default="", help="Optional output JSON file.")
    return p.parse_args()


def main() -> None:
    args = parse_args()
    data_path = Path(args.data).expanduser().resolve()
    if not data_path.exists():
        raise FileNotFoundError(f"Data file not found: {data_path}")

    raw = pd.read_csv(data_path)
    norm = _normalize_columns(raw)
    feat = compute_features(norm)
    report = walk_forward_search(
        feat_df=feat,
        timeframe=args.timeframe,
        folds=args.folds,
        min_train_trades=args.min_train_trades,
        min_test_trades=args.min_test_trades,
    )
    report["meta"] = {
        "data_file": str(data_path),
        "rows_raw": int(len(norm)),
        "rows_features": int(len(feat)),
    }

    text = json.dumps(report, indent=2)
    print(text)

    if args.output:
        out = Path(args.output).expanduser().resolve()
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(text + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
