# WOVEN_SPEC_CHECKLIST — OMEGA-DEVIN-

**Date:** 2026-02-06  
**Definition:** "Woven" means the decision logic and its evidence are interlaced into the chart rendering, not a separate explanation overlay.

Canonical paths (see deprecations):
- Frontend: `omega_frontend/` (`DEPRECATION.md:7-15`)
- Backend: `omega_ui/omega_backend/app/` (`DEPRECATION.md:12-16`)

## Backend Packet Model

- [x] Decision packet contains decision + confidence + reason text
  - Evidence: `omega_ui/omega_backend/app/provenance/weave_packet.py:115-178`
- [x] Packet contains features with provenance fields (`tier`, `source`, `can_affect_decisions`)
  - Evidence: `omega_ui/omega_backend/app/provenance/weave_packet.py:76-96`
- [x] Packet contains evidence pins (top N) and conflict map list
  - Evidence: `omega_ui/omega_backend/app/main.py:1971-2009`
- [x] Packet is replayable per bar index
  - Evidence: `omega_ui/omega_backend/app/main.py:2017-2035`

## Provenance Firewall (Truth / Anti-Fake)

- [x] Tier C is watermarked and cannot affect decisions
  - Evidence: `omega_ui/omega_backend/app/provenance/__init__.py:37-42`
- [x] Tier C is blocked from decision input
  - Evidence: `omega_ui/omega_backend/app/provenance/__init__.py:113-126`
- [x] Tier C cannot inflate confidence
  - Evidence: `omega_ui/omega_backend/app/provenance/__init__.py:128-156`

## REAL_DOM (Fail-Closed)

- [x] Pluggable provider interface + registry
  - Evidence: `omega_ui/omega_backend/app/provenance/market_data_provider.py:95-158`
- [x] Fail-closed enforcement when `REAL_DOM=true`
  - Evidence: `omega_ui/omega_backend/app/provenance/market_data_provider.py:516-571`
- [x] Backend blocks trading when DOM not allowed
  - Evidence: `omega_ui/omega_backend/app/main.py:1947-1969`

## Frontend Woven Rendering

- [x] No-Trade Fog when decision is WAIT/SKIP
  - Evidence: `omega_frontend/src/App.tsx:2455-2468`
- [x] Evidence pins are clickable UI elements
  - Evidence: `omega_frontend/src/App.tsx:2473-2507`
- [x] Click-to-highlight maps absolute bar indices to local chart indices
  - Evidence: `omega_frontend/src/App.tsx:2054-2075`
- [x] Highlight rendering: candle outline + optional zone rectangle
  - Evidence: `omega_frontend/src/App.tsx:856-909`
- [x] Resolution conditions are displayed (text list)
  - Evidence: `omega_frontend/src/App.tsx:2509-2522`
- [ ] Resolution conditions are drawn on-chart (lines/zones with anchors)
  - Status: **Missing** (current conditions have no anchors; see `omega_ui/omega_backend/app/main.py:1981-1983`)

## Conflict Mode

- [x] Backend produces a `conflict_map` list in the packet
  - Evidence: `omega_ui/omega_backend/app/provenance/weave_packet.py:144-149`
- [ ] Frontend renders a conflict graph/table from `conflict_map`
  - Status: **Missing** (type exists but not rendered; see `omega_frontend/src/App.tsx:105-119`)

## Tests

- [x] Provenance firewall unit tests
  - Evidence: `tests/test_backend_woven_firewall.py:19-62`
- [x] REAL_DOM fail-closed unit tests
  - Evidence: `tests/test_backend_woven_firewall.py:71-164`
- [x] WhyWait pin schema/sorting unit test
  - Evidence: `tests/test_backend_woven_firewall.py:166-187`

