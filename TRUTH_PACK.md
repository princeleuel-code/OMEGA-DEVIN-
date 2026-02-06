# TRUTH_PACK — OMEGA-DEVIN-

**Date:** 2026-02-06  
**Scope:** WOVEN chart intelligence + provenance firewall + REAL_DOM fail-closed + evaluation hardening

This document is intentionally evidence-first. Every claim includes a file path + line range and a reproducible command.

## Quick Verifier (One Command)

Run the repo verifier loop:

```bash
cd OMEGA-DEVIN- && python3.12 ./run.py verify --npm-ci
```

Evidence:
- Verifier entry point: `run.py` (`verify` subcommand) and its output includes compileall, unittests, CLI smokes, and frontend lint/build.

## Evidence Table (Load-Bearing Claims)

### Provenance Firewall (Tier A/B/C)

1. **Tier C is force-watermarked and cannot affect decisions**
   - Evidence: `omega_ui/omega_backend/app/provenance/__init__.py:21-42`
   - Repro: `python3.12 -m unittest -v tests.test_backend_woven_firewall.TestProvenanceFirewallGuard`

2. **Tier C is blocked from decision inputs (fail-closed)**
   - Evidence: `omega_ui/omega_backend/app/provenance/__init__.py:113-126`
   - Repro: `python3.12 -m unittest -v tests.test_backend_woven_firewall.TestProvenanceFirewallGuard.test_validate_decision_input_blocks_tier_c`

3. **Confidence computation ignores Tier C (Tier C cannot inflate confidence)**
   - Evidence: `omega_ui/omega_backend/app/provenance/__init__.py:128-156`
   - Repro: `python3.12 -m unittest -v tests.test_backend_woven_firewall.TestProvenanceFirewallGuard.test_tier_c_cannot_inflate_confidence`

### REAL_DOM Fail-Closed Policy

4. **Provider selection is pluggable; unqualified symbols default to `NoDOMProvider`**
   - Evidence: `omega_ui/omega_backend/app/provenance/market_data_provider.py:481-488`
   - Repro: `python3.12 -m unittest -v tests.test_backend_woven_firewall.TestRealDOMFailClosed`

5. **When `REAL_DOM=true`, trading is BLOCKED if provider is unqualified/disconnected/stale/warmup-not-met**
   - Evidence: `omega_ui/omega_backend/app/provenance/market_data_provider.py:516-571`
   - Repro: `python3.12 -m unittest -v tests.test_backend_woven_firewall.TestRealDOMFailClosed`

6. **Backend decision packet enforces fail-closed (DOM + firewall gates)**
   - Evidence: `omega_ui/omega_backend/app/main.py:1858-1969`
   - Repro: **UNVERIFIED in verifier loop** (requires backend deps and running API). Suggested repro:
     - `cd omega_ui/omega_backend && python3.12 -m uvicorn app.main:app --reload`
     - Then: `curl http://localhost:8000/api/weave-packet/BTCUSDT`

7. **Real DOM feed can be started via API (requires `REAL_DOM=true`)**
   - Evidence: `omega_ui/omega_backend/app/main.py:2082-2096`
   - Repro: **UNVERIFIED in verifier loop** (requires backend deps + running API). Suggested repro:
     - `REAL_DOM=true cd omega_ui/omega_backend && python3.12 -m uvicorn app.main:app --reload`
     - `curl -XPOST http://localhost:8000/api/real-dom/start/BTCUSDT`

### WOVEN "Why Wait" (Pins + Click-to-Highlight)

8. **Evidence pin schema + generation exists and sorts by severity**
   - Evidence: `omega_ui/omega_backend/app/provenance/why_wait.py:18-159`
   - Repro: `python3.12 -m unittest -v tests.test_backend_woven_firewall.TestWhyWaitPins`

9. **Decision packets include `evidence_pins`, `conflict_map`, and `resolution_conditions`**
   - Evidence: `omega_ui/omega_backend/app/main.py:1971-2009`
   - Repro: **UNVERIFIED in verifier loop** (requires backend deps + running API). Suggested repro:
     - `cd omega_ui/omega_backend && python3.12 -m uvicorn app.main:app --reload`
     - `curl http://localhost:8000/api/weave-packet/EURUSD`

10. **Canonical frontend renders No-Trade Fog + clickable pins; click highlights candles/zones**
   - Evidence:
     - No-trade overlay: `omega_frontend/src/App.tsx:2455-2526`
     - Candle mapping: `omega_frontend/src/App.tsx:2054-2075`
     - Zone rendering: `omega_frontend/src/App.tsx:856-909`
   - Repro: `cd omega_frontend && npm run dev` (manual, visual)

### Evaluation Hardening (Anti-Fraud)

11. **Sharpe/Sortino ratios are tiny-N guarded and capped**
   - Evidence: `chimera/evaluation/metrics.py:271-281`
   - Repro: `python3.12 -m unittest -v tests.test_metrics_hardening`

12. **Purged walk-forward uses a configurable purge gap and outputs bootstrap CI**
   - Evidence:
     - Purge config: `chimera/evaluation/walk_forward.py:22-42`
     - Bootstrap CI: `chimera/evaluation/walk_forward.py:109-120`
     - Report includes `return_ci_lower/upper`: `chimera/evaluation/walk_forward.py:243-261`
   - Repro: `python3.12 -m unittest -v tests.test_walk_forward`

13. **Embargo (trade_start_bar) prevents trading in train+purge windows**
   - Evidence: `chimera/evaluation/backtest.py:195-211`
   - Repro: `python3.12 ./run.py walkforward --bars 300 --regime-data --spread 1.0 --folds 2 --train-bars 100 --test-bars 50 --purge-bars 5 --bootstrap 50`

### Sakana Evolution (Auditability)

14. **Evolution always counts evaluation attempts (even for failing variants)**
   - Evidence: `agents/evolution_loop.py:1488-1509`
   - Repro: `python3.12 -m unittest -v tests.test_sakana_evolution_counts`

## Offline / Locking Status

- `omega_frontend/` has `package-lock.json` and uses `npm ci`, but offline installs are **UNVERIFIED** without a pre-populated npm cache.
- `omega_ui/omega_backend/` has `pyproject.toml` but no `poetry.lock`; fully pinned offline installs are **UNVERIFIED** until a lockfile and/or wheelhouse is added.
