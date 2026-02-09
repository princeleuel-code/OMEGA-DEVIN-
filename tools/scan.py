from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from chimera.core.scanners import tvscreener_scan


def _repo_root() -> Path:
    # tools/scan.py -> repo root is one parent up
    return Path(__file__).resolve().parents[1]


def _utc_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _utc_date() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Market scanner CLI (non-critical).")
    parser.add_argument("--source", required=True, choices=["tvscreener"], help="Scanner source.")
    parser.add_argument("--asset", required=True, help="Asset class (e.g., forex, crypto, stocks).")
    parser.add_argument("--limit", type=int, default=50, help="Max rows to return.")
    parser.add_argument("--timeframe", default="1D", help="Timeframe hint (e.g., 1D, 1W, 60, 240).")
    parser.add_argument("--config", default=None, help="Path to scanners.yaml (optional).")
    args = parser.parse_args(argv)

    if args.source != "tvscreener":
        raise SystemExit(f"Unsupported source: {args.source}")

    rows = tvscreener_scan(
        asset_class=args.asset,
        filters=None,
        columns=None,
        sort=None,
        limit=args.limit,
        timeframe=args.timeframe,
        config_path=args.config,
    )

    root = _repo_root()
    out_dir = root / "data" / "scans" / _utc_date()
    out_dir.mkdir(parents=True, exist_ok=True)

    ts = _utc_stamp()
    out_path = out_dir / f"tvscreener_{args.asset}_{ts}.json"

    payload = {
        "source": "tvscreener",
        "asset_class": args.asset,
        "timeframe": args.timeframe,
        "ts": datetime.now(timezone.utc).isoformat(),
        "rows": rows,
    }
    out_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    print(str(out_path))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

