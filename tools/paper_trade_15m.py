"""
15-minute (bar-count) paper-trade demo against the local dashboard API.

This is intentionally a *simulation harness*:
- It never places real orders.
- It requires REAL_DOM=true + a qualified symbol (e.g. BTCUSDT) to demonstrate the
  provenance firewall (Tier C cannot authorize trades).

Run:
  python3.12 -m tools.paper_trade_15m --symbol BTCUSDT --bars 15 --interval-ms 250
"""

from __future__ import annotations

import argparse
import json
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional, Tuple


@dataclass(frozen=True)
class EntryExit:
    side: str
    entry_price: float
    exit_price: float
    bars_held: int

    @property
    def pnl(self) -> float:
        if self.side.upper() == "SHORT":
            return self.entry_price - self.exit_price
        return self.exit_price - self.entry_price

    @property
    def pnl_pct(self) -> float:
        if self.entry_price <= 0:
            return 0.0
        return (self.pnl / self.entry_price) * 100.0


def _utc_date() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def _utc_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _http_json(method: str, url: str, *, payload: Optional[Dict[str, Any]] = None, timeout_s: float = 10.0) -> Any:
    body: Optional[bytes] = None
    req = urllib.request.Request(url=url, method=method.upper())
    if payload is not None:
        body = json.dumps(payload).encode("utf-8")
        req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, data=body, timeout=timeout_s) as resp:
            data = resp.read()
            if not data:
                return None
            return json.loads(data.decode("utf-8", errors="replace"))
    except urllib.error.HTTPError as e:
        raw = e.read()
        msg = raw.decode("utf-8", errors="replace") if raw else str(e)
        raise RuntimeError(f"HTTP {e.code} for {method} {url}: {msg}") from e
    except urllib.error.URLError as e:
        raise RuntimeError(f"Request failed for {method} {url}: {e}") from e


def _post(base: str, path: str, *, timeout_s: float = 10.0) -> Any:
    return _http_json("POST", f"{base}{path}", timeout_s=timeout_s)


def _get(base: str, path: str, *, timeout_s: float = 10.0) -> Any:
    return _http_json("GET", f"{base}{path}", timeout_s=timeout_s)


def _get_sim_status(base: str, symbol: str, *, timeout_s: float = 10.0) -> Dict[str, Any]:
    status = _get(base, "/api/sim/status", timeout_s=timeout_s)
    sym = symbol.upper()
    return (status or {}).get("status", {}).get(sym, {}) if isinstance(status, dict) else {}


def _wait_for_trade_permission(
    base: str,
    symbol: str,
    *,
    timeout_s: float,
    poll_s: float,
) -> Dict[str, Any]:
    deadline = time.time() + timeout_s
    sym = symbol.upper()
    last: Dict[str, Any] = {}
    while time.time() < deadline:
        resp = _get(base, f"/api/decision/{urllib.parse.quote(sym)}", timeout_s=10.0)
        if isinstance(resp, dict):
            last = resp
            if resp.get("can_trade") is True and resp.get("decision") == "TRADE":
                return resp
        time.sleep(poll_s)
    raise TimeoutError(f"Timed out waiting for TRADE permission for {sym}. Last: {last}")


def _extract_side_from_packet(packet: Dict[str, Any]) -> str:
    features = packet.get("features", {}) if isinstance(packet, dict) else {}
    imbalance = None
    if isinstance(features, dict):
        imbalance = (features.get("book_imbalance") or {}).get("value")
    try:
        imb = float(imbalance)
    except Exception:
        # If book_imbalance is missing, fall back to deterministic LONG.
        return "LONG"
    return "LONG" if imb >= 0.0 else "SHORT"


def _packet_summary(packet: Dict[str, Any], decision_resp: Dict[str, Any]) -> Dict[str, Any]:
    feats = packet.get("features", {}) if isinstance(packet, dict) else {}
    bids = (feats.get("real_dom_bids") or {}).get("value") if isinstance(feats, dict) else None
    asks = (feats.get("real_dom_asks") or {}).get("value") if isinstance(feats, dict) else None
    preview = {
        "book_imbalance": (feats.get("book_imbalance") or {}).get("value") if isinstance(feats, dict) else None,
        "bids_preview": bids[:5] if isinstance(bids, list) else [],
        "asks_preview": asks[:5] if isinstance(asks, list) else [],
    }
    return {
        "timestamp": packet.get("timestamp"),
        "symbol": packet.get("symbol"),
        "timeframe": packet.get("timeframe"),
        "bar_index": packet.get("bar_index"),
        "decision": packet.get("decision"),
        "confidence": packet.get("confidence"),
        "reason_codes": packet.get("reason_codes", []),
        "reason_text": packet.get("reason_text", ""),
        "evidence_pins": packet.get("evidence_pins", []),
        "resolution_conditions": packet.get("resolution_conditions", []),
        "conflict_info": packet.get("conflict_info"),
        "dom_check": decision_resp.get("dom_check"),
        "features_used": decision_resp.get("features_used"),
        "dom_preview": preview,
    }


def _entry_exit_from_api(
    base: str,
    symbol: str,
    *,
    hold_bars: int,
    interval_ms: int,
    permission_timeout_s: float,
) -> Tuple[EntryExit, Dict[str, Any]]:
    sym = symbol.upper()

    # Start local simulation first so we have chart bars even when REAL_DOM is enabled.
    _post(base, f"/api/sim/start/{urllib.parse.quote(sym)}?interval_ms={int(interval_ms)}", timeout_s=10.0)

    # Require REAL_DOM policy to be enabled on the server.
    real_dom_resp = _post(base, f"/api/real-dom/start/{urllib.parse.quote(sym)}", timeout_s=10.0)
    if isinstance(real_dom_resp, dict) and real_dom_resp.get("success") is not True:
        raise RuntimeError(
            f"REAL_DOM start failed for {sym}: {real_dom_resp}. "
            "Server must be launched with REAL_DOM=true and have websocket deps installed."
        )

    decision = _wait_for_trade_permission(base, sym, timeout_s=permission_timeout_s, poll_s=0.25)

    sim_status = _get_sim_status(base, sym)
    entry_bars = int(sim_status.get("bars") or 0)

    chart = _get(base, f"/api/chart-data/{urllib.parse.quote(sym)}?bars=1", timeout_s=10.0)
    try:
        entry_price = float((chart or {}).get("current_price"))
    except Exception:
        entry_price = 0.0

    pkt_resp = _get(base, f"/api/weave-packet/{urllib.parse.quote(sym)}", timeout_s=10.0)
    pkt = (pkt_resp or {}).get("packet") if isinstance(pkt_resp, dict) else None
    if not isinstance(pkt, dict):
        raise RuntimeError(f"Missing weave packet for {sym}: {pkt_resp}")

    side = _extract_side_from_packet(pkt)

    # Hold for N new simulated bars.
    target_bars = entry_bars + int(hold_bars)
    deadline = time.time() + max(30.0, (hold_bars * interval_ms / 1000.0) * 10.0)
    last_status: Dict[str, Any] = sim_status
    while time.time() < deadline:
        last_status = _get_sim_status(base, sym)
        if int(last_status.get("bars") or 0) >= target_bars:
            break
        time.sleep(0.10)
    else:
        raise TimeoutError(f"Timed out waiting for {hold_bars} bars (target={target_bars}). Last status: {last_status}")

    chart2 = _get(base, f"/api/chart-data/{urllib.parse.quote(sym)}?bars=1", timeout_s=10.0)
    try:
        exit_price = float((chart2 or {}).get("current_price"))
    except Exception:
        exit_price = 0.0

    pkt_resp2 = _get(base, f"/api/weave-packet/{urllib.parse.quote(sym)}", timeout_s=10.0)
    pkt2 = (pkt_resp2 or {}).get("packet") if isinstance(pkt_resp2, dict) else None
    if not isinstance(pkt2, dict):
        pkt2 = {}

    exit_packet_summary = _packet_summary(pkt2, decision_resp=decision) if pkt2 else {}

    # Best-effort stop sim.
    try:
        _post(base, f"/api/sim/stop/{urllib.parse.quote(sym)}", timeout_s=5.0)
    except Exception:
        pass

    entry_exit = EntryExit(side=side, entry_price=entry_price, exit_price=exit_price, bars_held=hold_bars)
    report = {
        "ts": _utc_stamp(),
        "symbol": sym,
        "api_base": base,
        "interval_ms": int(interval_ms),
        "bars_held": int(hold_bars),
        "entry": {
            "bars_count": entry_bars,
            "price": entry_price,
            "side": side,
            "decision": decision.get("decision"),
            "confidence": decision.get("confidence"),
            "reason": decision.get("reason"),
            "dom_check": decision.get("dom_check"),
            "evidence_pins": decision.get("evidence_pins"),
            "resolution_conditions": decision.get("resolution_conditions"),
        },
        "exit": {
            "bars_count": int(last_status.get("bars") or 0),
            "price": exit_price,
            "packet_summary": exit_packet_summary,
        },
        "pnl": entry_exit.pnl,
        "pnl_pct": entry_exit.pnl_pct,
    }
    return entry_exit, report


def main() -> int:
    p = argparse.ArgumentParser(description="15-minute (bar-count) paper-trade demo via dashboard API.")
    p.add_argument("--api-base", default="http://127.0.0.1:8001", help="Dashboard API base URL")
    p.add_argument("--symbol", default="BTCUSDT", help="Symbol to trade (use a REAL_DOM qualified symbol)")
    p.add_argument("--bars", type=int, default=15, help="Bars to hold (treat as 'minutes' in this demo)")
    p.add_argument("--interval-ms", type=int, default=250, help="Simulation bar interval in milliseconds")
    p.add_argument("--timeout-seconds", type=int, default=45, help="Max seconds waiting for TRADE permission")
    p.add_argument(
        "--out-dir",
        default=str(Path("data") / "paper_trades"),
        help="Output directory root (date subfolder will be created)",
    )

    args = p.parse_args()
    base = str(args.api_base).rstrip("/")
    sym = str(args.symbol).upper()

    # Basic server check.
    _get(base, "/healthz", timeout_s=5.0)

    entry_exit, report = _entry_exit_from_api(
        base,
        sym,
        hold_bars=int(args.bars),
        interval_ms=int(args.interval_ms),
        permission_timeout_s=float(args.timeout_seconds),
    )

    out_dir = Path(args.out_dir) / _utc_date()
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"paper_trade_{sym}_{report['ts']}.json"
    out_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    # Minimal stdout for humans/log scraping.
    print(
        json.dumps(
            {
                "ok": True,
                "symbol": sym,
                "side": entry_exit.side,
                "entry": entry_exit.entry_price,
                "exit": entry_exit.exit_price,
                "pnl": entry_exit.pnl,
                "pnl_pct": entry_exit.pnl_pct,
                "bars": entry_exit.bars_held,
                "report": str(out_path),
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

