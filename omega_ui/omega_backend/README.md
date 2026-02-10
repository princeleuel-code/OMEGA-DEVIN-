## OMEGA Backend (FastAPI)

This is the backend API used by the canonical UI at `OMEGA-DEVIN-/omega_frontend/`.

### Quickstart (macOS)

From the repo root:

```bash
cd "omega_ui/omega_backend"

# Create a local venv (recommended). Keep it out of git.
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -U pip

# Install backend deps (from pyproject.toml).
python -m pip install "fastapi[standard]" websockets "psycopg[binary]" certifi python-multipart pandas numpy

# Start the API (REAL_DOM=true enables real orderbook connectivity; fail-closed if stale/disconnected).
env REAL_DOM=true python -m uvicorn app.main:app --host 127.0.0.1 --port 8001 --log-level info
```

Health check:

```bash
curl -fsS http://127.0.0.1:8001/healthz
```

Notes:
- The repo-wide verifier (`python3.12 run.py verify`) uses `unittest` and does not require these backend dependencies.
- If port `8001` is taken, you can choose another, but keep `OMEGA-DEVIN-/omega_frontend/.env` in sync (`VITE_API_URL`).
