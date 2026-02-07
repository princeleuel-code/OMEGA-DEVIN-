# OMEGA-DEVIN Trading System - Architecture Map

## Mission
A **fail-closed, self-improving FX trading brain** that:
- Trades only when conditions are clean (selection > prediction)
- Explains every action with reason codes
- Learns from mistakes (mistake -> lesson -> new rule/test -> never repeat)
- Evolves across regimes without collapsing into one brittle strategy
- **Thinks like a human trader** (sentiment awareness, self-improvement)
- **Operates with machine precision** (RL optimization, ensemble coordination)

## System Components

### 1. Chimera (Structure-Based Trading)
Core trading logic using market structure analysis.

### 2. AuctionFlow (Volume Profile Trading)
Volume-based analysis with auction market theory.

### 3. Learning Module (NEW)
Reinforcement Learning for adaptive decision-making.

### 4. Sentiment Module (NEW)
NLP-based market sentiment analysis.

### 5. Autonomy Agent (NEW)
Self-improvement research agent.

### 6. Ensemble Coordinator (NEW)
Multi-strategy decision coordination.

## Directory Structure

```
OMEGA-DEVIN/
├── ARCHITECTURE_MAP.md          # This file
├── README.md                    # Project overview
├── requirements.txt             # Dependencies
├── run.py                       # Main CLI runner
│
├── chimera/                     # Structure-based trading system
│   ├── core/
│   │   ├── decision_engine.py   # Central brain loop
│   │   ├── reason_codes.py      # Explicit veto vocabulary
│   │   ├── veto_cascade.py      # Safety gates
│   │   ├── truth_manifest.py    # Proof/audit layer
│   │   └── ensemble.py          # [NEW] Multi-strategy coordinator
│   ├── learning/                # [NEW] RL components
│   │   └── rl_agent.py          # Reinforcement learning agent
│   ├── evolution/
│   │   ├── genome.py            # Strategy as evolvable genome
│   │   ├── drq_loop.py          # Digital Red Queen adaptation
│   │   ├── map_elites.py        # Diversity archive
│   │   ├── mutations.py         # Genome mutations
│   │   └── behaviors.py         # Behavior descriptors
│   ├── evaluation/
│   │   ├── score.py             # Deterministic scoring
│   │   ├── backtest.py          # Walk-forward backtester
│   │   └── metrics.py           # Performance metrics
│   ├── data/
│   │   ├── loader.py            # Data ingestion
│   │   ├── integrity.py         # Gap/stale/monotonic checks
│   │   └── features.py          # Feature engineering
│   └── execution/
│       └── router.py            # LONG/SHORT/WAIT proposals
│
├── auctionflow/                 # Volume profile trading system
│   ├── profile/                 # Volume profile construction
│   ├── flow/                    # Order flow analysis
│   ├── strategy/                # Signal generation
│   ├── engine/                  # Veto and reason codes
│   └── backtest/                # Backtesting
│
├── omegaquant/                  # [NEW] Advanced AI components
│   └── sentiment/
│       ├── analyzer.py          # Sentiment analysis engine
│       └── news_loader.py       # News data ingestion
│
└── agents/                      # [NEW] Self-improvement agents
    └── autonomy_agent.py        # Research & improvement agent
```

## Data Flow (Enhanced)

```
[Market Data] ─────────────────────────────────────────┐
    │                                                   │
    ▼                                                   ▼
[Integrity Gate] ──► FAIL_CLOSED if bad data    [News/Sentiment]
    │                                                   │
    ▼                                                   ▼
[Feature Engine]                              [Sentiment Analyzer]
    │                                                   │
    ├───────────────────────────────────────────────────┤
    │                                                   │
    ▼                                                   ▼
┌─────────────────────────────────────────────────────────────┐
│                    ENSEMBLE COORDINATOR                      │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐    │
│  │ Chimera  │  │Auctionflow│  │ RL Agent │  │Sentiment │    │
│  │ Router   │  │  Signals  │  │  Policy  │  │  Filter  │    │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘    │
│       └─────────────┴─────────────┴─────────────┘           │
│                    [Agreement / Voting]                      │
└─────────────────────────┼───────────────────────────────────┘
                          ▼
                   [Veto Cascade] ──► Block with reason codes
                          ▼
                   [Decision Packet] ──► Log everything
                          ▼
                   [Truth Manifest] ──► Prove what happened
                          ▼
                   [Autonomy Agent] ──► Analyze & improve
```

## New Components

### Reinforcement Learning Agent (`chimera/learning/rl_agent.py`)
- **TradingEnvironment**: OpenAI Gym-compatible trading simulation
- **RLAgent**: Q-learning based policy with epsilon-greedy exploration
- **Abstention-first reward design**: Penalizes bad trades heavily

### Sentiment Analyzer (`omegaquant/sentiment/analyzer.py`)
- **Financial lexicon**: Domain-specific sentiment words
- **Confidence scoring**: Weighted by source reliability
- **Veto integration**: Can block trades during adverse sentiment

### Autonomy Agent (`agents/autonomy_agent.py`)
- **Performance analysis**: Identifies patterns in wins/losses
- **Improvement proposals**: Suggests parameter adjustments
- **Knowledge base**: Stores lessons learned

### Ensemble Coordinator (`chimera/core/ensemble.py`)
- **Multi-strategy signals**: Collects from Chimera, AuctionFlow, RL, Sentiment
- **Weighted voting**: Configurable strategy weights
- **Conflict resolution**: Abstain-first when strategies conflict

## Sakana-Style Evolution Loop (NEW)

The system implements a **DGM + DRQ hybrid** self-improvement loop inspired by Sakana AI's research.

### Evolution Loop (`agents/evolution_loop.py`)

**Truth Objects** (written every run for full reproducibility):
- `RUN_MANIFEST.json` - Git commit, data ranges, seeds, dependency versions
- `VARIANT_PATCH.json` - Exact config diffs per variant
- `EVAL_REPORT.json` - Walk-forward results per fold + aggregate
- `ARCHIVE_INDEX.json` - MAP-Elites buckets (regime x risk)
- `LIVE_GATING_STATE.json` - Active variant, canary mode, kill-switch status

**Walk-Forward Evaluation Harness**:
- Train window → test window, multiple folds
- Regime detection: trend / range / high-vol / low-vol
- Cost model: spread + slippage + commission always applied
- Integrity gates: FAIL_CLOSED on missing/gapped/non-monotonic data

**MAP-Elites Archive** (Quality-Diversity):
- Regime buckets: trend, range, high_vol, low_vol
- Risk buckets: dd<2%, 2-5%, >5%
- Stores top K variants per bucket with full provenance

**DRQ Champion Testing**:
- New variants must beat current champion out-of-sample
- Must also beat sampled historical champions
- Prevents cycling and ensures continual improvement

**Canary Deployment**:
- Paper trading or micro-size before live
- Kill-switch on max drawdown breach or anomalies
- Automatic revert to previous champion on failure

### Running Evolution

```bash
# Run Sakana-style evolution
python3 run.py sakana-evolve --rounds 10 --variants 5 --bars 1000

# With custom thresholds
python3 run.py sakana-evolve \
    --rounds 20 \
    --variants 10 \
    --max-dd 10.0 \
    --min-sharpe 0.5 \
    --output ./my_evolution
```

## Core Principles

1. **Fail-Closed**: If anything is uncertain, do nothing
2. **Explicit Reason Codes**: Every NO must have a code
3. **Provable**: Every run produces verifiable artifacts
4. **Evolvable**: Strategies are genomes that can mutate/crossover
5. **Diverse**: Keep multiple survivors, not just "the best"
6. **Self-Improving**: System analyzes and improves itself
7. **Sentiment-Aware**: Considers market mood and news
8. **Ensemble-Driven**: Multiple strategies vote on decisions
9. **Empirically Validated**: Changes must prove themselves out-of-sample
10. **Canary-First**: New policies paper trade before going live
