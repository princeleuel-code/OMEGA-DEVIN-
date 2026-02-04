# OmegaQuant / Chimera - Architecture Map

## Mission
A **fail-closed, self-improving FX trading brain** that:
- Trades only when conditions are clean (selection > prediction)
- Explains every action with reason codes
- Learns from mistakes (mistake -> lesson -> new rule/test -> never repeat)
- Evolves across regimes without collapsing into one brittle strategy

## Directory Structure

```
omegaquant/
├── ARCHITECTURE_MAP.md          # This file
├── chimera/
│   ├── __init__.py
│   ├── core/
│   │   ├── __init__.py
│   │   ├── decision_engine.py   # Central brain loop
│   │   ├── reason_codes.py      # Explicit veto vocabulary
│   │   ├── veto_cascade.py      # Safety gates
│   │   └── truth_manifest.py    # Proof/audit layer
│   ├── evolution/
│   │   ├── __init__.py
│   │   ├── genome.py            # Strategy as evolvable genome
│   │   ├── drq_loop.py          # Digital Red Queen adaptation
│   │   ├── map_elites.py        # Diversity archive
│   │   ├── mutations.py         # Genome mutations
│   │   └── behaviors.py         # Behavior descriptors
│   ├── evaluation/
│   │   ├── __init__.py
│   │   ├── score.py             # Deterministic scoring
│   │   ├── backtest.py          # Walk-forward backtester
│   │   └── metrics.py           # Performance metrics
│   ├── data/
│   │   ├── __init__.py
│   │   ├── loader.py            # Data ingestion
│   │   ├── integrity.py         # Gap/stale/monotonic checks
│   │   └── features.py          # Feature engineering
│   └── execution/
│       ├── __init__.py
│       ├── router.py            # LONG/SHORT/WAIT proposals
│       └── daemon.py            # Minimal execution surface
├── config/
│   ├── default.yaml             # Default configuration
│   └── risk_limits.yaml         # Risk parameters
├── logs/
│   └── lessons_trading.md       # Mistake logbook
├── archive/
│   └── survivors/               # MAP-Elites champion storage
├── tasks/
│   └── todo_trading.md          # Build/verify checklist
└── tests/
    ├── test_decision_engine.py
    ├── test_veto_cascade.py
    └── test_backtest.py
```

## Data Flow

```
[Market Data] 
    │
    ▼
[Integrity Gate] ──► FAIL_CLOSED if bad data
    │
    ▼
[Feature Engine] ──► Compute indicators/structure
    │
    ▼
[Router] ──► Propose: LONG / SHORT / WAIT
    │
    ▼
[Veto Cascade] ──► Block with reason codes if unsafe
    │
    ▼
[Decision Packet] ──► Log everything
    │
    ▼
[Execution Daemon] ──► Only this touches keys (if live)
    │
    ▼
[Truth Manifest] ──► Prove what happened
```

## Core Principles

1. **Fail-Closed**: If anything is uncertain, do nothing
2. **Explicit Reason Codes**: Every NO must have a code
3. **Provable**: Every run produces verifiable artifacts
4. **Evolvable**: Strategies are genomes that can mutate/crossover
5. **Diverse**: Keep multiple survivors, not just "the best"
