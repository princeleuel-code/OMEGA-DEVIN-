from __future__ import annotations

import argparse
import json
from pathlib import Path

from auctionflow.data.adapters import df_to_candles, load_ohlcv_csv
from auctionflow.profile.build import ProfileConfig, build_volume_profile
from auctionflow.profile.nodes import detect_nodes


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", required=True)
    ap.add_argument("--tz", default=None)
    ap.add_argument("--out", required=True)
    ap.add_argument("--tick", type=float, default=0.25)
    args = ap.parse_args()

    df = load_ohlcv_csv(args.csv, tz=args.tz)
    candles = df_to_candles(df)

    cfg = ProfileConfig(tick_size=args.tick)
    prof = build_volume_profile(candles, cfg)
    nodes = detect_nodes(prof, window=cfg.smooth_window)

    payload = {
        "poc": prof.poc,
        "val": prof.val,
        "vah": prof.vah,
        "total_volume": prof.total_volume,
        "top_nodes": [n.__dict__ for n in nodes[:20]],
    }

    Path(args.out).write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"Wrote {args.out}")


if __name__ == "__main__":
    main()
