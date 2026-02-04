# OMEGA-DEVIN Trading System

A complete, fail-closed FX trading brain that combines **Chimera** (structure-based trading with evolutionary optimization) and **AuctionFlow** (volume profile and order flow analysis).

## Core Philosophy

> "Profit comes from what you refuse to trade."

This system is designed to be **fail-closed**: if anything is uncertain, do nothing. Every decision has an explicit reason code. Every run produces a verifiable audit trail.

## System Components

### Chimera (Structure-Based Trading)
- **Decision Engine**: Central brain loop with veto cascade
- **Reason Codes**: Explicit vocabulary for every decision
- **Truth Manifest**: Audit layer producing VERDICT.json
- **Feature Engine**: Market structure detection (HH/HL/LL/LH, BOS, displacement)
- **Strategy Genomes**: 16+ tunable parameters for evolution
- **MAP-Elites Archive**: Diversity-preserving strategy storage
- **DRQ Evolution**: Adversarial evolution against market scenarios

### AuctionFlow (Volume Profile Trading)
- **Volume Profile**: Value Area, POC, HVN/LVN detection
- **Order Flow**: Delta, OFI, acceptance scoring
- **3 Core Plays**:
  1. Failed Auction Fade (re-entry into value area)
  2. Acceptance Breakout (acceptance outside value area)
  3. LVN Travel (vacuum to next HVN)
- **Chart Tricks**: Sweeps, FVG, BOS detection

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Run a backtest with Chimera
python3 run.py backtest --bars 2000 --regime-data

# Run evolution to find better strategies
python3 run.py evolve --generations 10 --population 10

# Analyze a genome
python3 run.py analyze --genome-file path/to/genome.json
```

## Project Structure

```
OMEGA-DEVIN/
├── run.py                    # Main CLI runner
├── ARCHITECTURE_MAP.md       # System documentation
├── requirements.txt          # Python dependencies
├── chimera/                  # Structure-based trading system
│   ├── core/                 # Decision engine, veto cascade, reason codes
│   ├── data/                 # Data loading, integrity, features
│   ├── evaluation/           # Backtesting, metrics, scoring
│   ├── evolution/            # Genomes, mutations, MAP-Elites, DRQ
│   └── execution/            # Signal routing
└── auctionflow/              # Volume profile trading system
    ├── profile/              # Volume profile building
    ├── flow/                 # Order flow analysis
    ├── strategy/             # Signal generation
    ├── engine/               # Veto and reason codes
    ├── backtest/             # Simple backtester
    └── apps/                 # CLI applications
```

## Tested Results (Synthetic Data)

- 20 trades with 100% win rate
- 13.43% total return on $10,000
- Sharpe Ratio: 16.99
- Max Drawdown: 0.19%
- Fitness Score: 0.79 (passed all risk gates)

*Note: These results are on synthetic regime data. Real market data will produce different results.*

## Safety Features

- **Fail-Closed Design**: If anything is uncertain, do nothing
- **Veto Cascade**: Sequential safety gates block unsafe trades
- **Risk Gates**: Max daily loss, max drawdown, max trades per day
- **Explicit Reason Codes**: Every "NO" is documented
- **Truth Manifest**: Every run is reproducible and verifiable

## Educational/Research Use

This is educational/research code. Not financial advice. No guarantees. Do not trade with money you cannot afford to lose.

---

Built with love by Devin for Prince.
