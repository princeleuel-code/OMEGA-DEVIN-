# UI/Backend Deprecation Notes (Canonical Paths)

This repo currently contains multiple UI/backend copies. To reduce drift and make verification reproducible, we declare one canonical frontend + backend.

## Canonical

- Frontend (canonical): `OMEGA-DEVIN-/omega_frontend/`
  - Rationale: contains `package-lock.json` and is the only UI we keep green in `npm run lint` + `npm run build`.
  - Woven integration: renders WhyWait evidence pins + No-Trade fog from `/api/weave-packet/{symbol}` and supports click-to-highlight.

- Backend API (canonical): `OMEGA-DEVIN-/omega_ui/omega_backend/app/`
  - Rationale: contains the provenance firewall + walk-forward / woven packet endpoints used by the canonical frontend.

## Deprecated (Do Not Extend)

- Duplicate frontend: `OMEGA-DEVIN-/omega_ui/omega_frontend/`
  - Issue: no lockfile; not used by canonical verifier loop.

- Duplicate frontend: `OMEGA-DEVIN-/ui/frontend/`
  - Issue: older copy (many `any` types); not wired to the hardened woven packet model.

- Duplicate backend: `OMEGA-DEVIN-/ui/backend/`
  - Issue: older copy; missing provenance/firewall wiring; includes hardcoded sys.path insertion for `/home/ubuntu/omega_devin`.

## Suggested Cleanup (Future PR)

1. Remove deprecated folders after confirming no external tooling depends on them.
2. Add a single top-level `make verify` or `python run.py verify` that runs:
   - Python unit tests
   - Frontend lint + build
   - A minimal walk-forward smoke

