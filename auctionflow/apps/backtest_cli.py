from __future__ import annotations

import argparse
import json
from pathlib import Path

from auctionflow.backtest.simple_backtest import run_backtest
from auctionflow.data.adapters import df_to_candles, load_ohlcv_csv


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", required=True, help="Path to OHLCV CSV (ts,open,high,low,close,volume)")
    ap.add_argument("--tz", default=None, help="Timezone for timestamps (e.g., America/New_York)")
    ap.add_argument("--log", default=None, help="Write JSONL events to this file")
    ap.add_argument("--out", default=None, help="Write full JSON results to this file")
    args = ap.parse_args()

    df = load_ohlcv_csv(args.csv, tz=args.tz)
    candles = df_to_candles(df)

    res = run_backtest(candles, log_path=args.log)

    s = res["summary"]
    print("=== AUCTIONFLOW BACKTEST ===")
    for k in ["trades","win_rate","avg_r","total_r","max_drawdown_r"]:
        print(f"{k}: {s[k]}")

    if args.out:
        Path(args.out).write_text(json.dumps(res, indent=2), encoding="utf-8")
        print(f"Wrote {args.out}")


if __name__ == "__main__":
    main()
