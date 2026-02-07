# REAL_DOM_POLICY — OMEGA-DEVIN-

**Date:** 2026-02-06  
**Goal:** If real DOM is required and unavailable, the system must **fail-closed** (no trade). Synthetic DOM may be displayed, but must never influence trade permission/confidence.

## Policy Summary (Fail-Closed)

1. `REAL_DOM=true` means:
   - The selected symbol must have a **qualified real L2 provider**, and that provider must be **CONNECTED**, **not stale**, and **warmed up**.
   - Otherwise: `allowed=false` and trading must be blocked.
   - Evidence: `omega_ui/omega_backend/app/provenance/market_data_provider.py:516-571`

2. No synthetic DOM for trading:
   - `NoDOMProvider` is explicitly synthetic and display-only.
   - Evidence: `omega_ui/omega_backend/app/provenance/market_data_provider.py:160-199`

3. Backend enforces fail-closed:
   - `dom_allowed` (registry) AND `provenance_firewall.can_trade(...)` must both pass for `TRADE`.
   - Evidence: `omega_ui/omega_backend/app/main.py:1947-1969`

## Qualified Providers / Symbols

### Binance L2 (Implemented)

- Provider: `BinanceL2Provider`
- Qualified symbols: pairs ending in `USDT`, `BUSD`, `BTC`, `ETH`, `BNB`
  - Evidence: `omega_ui/omega_backend/app/provenance/market_data_provider.py:221-249`
- Endpoints fallback (some environments return HTTP 451 on `stream.binance.com`):
  - Defaults: `stream.binance.com`, `stream.binance.us`, `data-stream.binance.vision`
  - Evidence: `omega_ui/omega_backend/app/provenance/market_data_provider.py:225-231`
  - Override env: `BINANCE_WS_BASE_URLS` (comma-separated)
  - Evidence: `omega_ui/omega_backend/app/provenance/market_data_provider.py:253-259`

### Coinbase L2 (Stub)

- Provider exists but is not implemented (will report `ERROR`).
- Evidence: `omega_ui/omega_backend/app/provenance/market_data_provider.py:201-219`

## Health, Staleness, Warmup

- Stale threshold env: `DOM_STALE_THRESHOLD_SEC` (default `5.0`)
  - Evidence: `omega_ui/omega_backend/app/provenance/market_data_provider.py:110-131`
- Warmup env: `DOM_SNAPSHOT_WARMUP` (default `10`)
  - Evidence: `omega_ui/omega_backend/app/provenance/market_data_provider.py:110-131`
- Fail-closed checks incorporate stale + warmup:
  - Evidence: `omega_ui/omega_backend/app/provenance/market_data_provider.py:521-561`

## Reconnection Backoff

- Backoff schedule:
  - attempts 1-3: 5s
  - attempts 4-6: 15s
  - attempts 7-10: 30s
  - attempts 11+: 60s
  - Evidence: `omega_ui/omega_backend/app/provenance/market_data_provider.py:54-63`

## API Surface (Backend)

- Start feed:
  - `POST /api/real-dom/start/{symbol}`
  - Evidence: `omega_ui/omega_backend/app/main.py:2082-2096`
- DOM snapshot + provenance:
  - `GET /api/dom/{symbol}`
  - Evidence: `omega_ui/omega_backend/app/main.py:2037-2079`

## Tests

- Fail-closed behaviors are covered by unit tests:
  - Evidence: `tests/test_backend_woven_firewall.py:107-164`
  - Repro: `cd OMEGA-DEVIN- && python3.12 -m unittest -v tests.test_backend_woven_firewall.TestRealDOMFailClosed`

