# RESEARCH_DIGEST — OMEGA-DEVIN-

**Date:** 2026-02-06  
**Purpose:** High-leverage research directions mapped to concrete implementation tasks. This is a roadmap, not performance claims.

## 1) Order Flow Intelligence (Highest Edge Potential)

### Tick Imbalance Bars

- Goal: replace arbitrary time bars with activity-driven bars that trigger on buy/sell imbalance.
- Implementation target:
  - New module (suggested): `chimera/orderflow/imbalance_bars.py` (UNIMPLEMENTED)
- Acceptance criteria:
  - Deterministic unit tests on a synthetic trade tape.
  - If inputs are synthetic (Tier C), outputs must be display-only and cannot affect trade permission/confidence.

### VPIN (Volume-synchronized Probability of Informed Trading)

- Goal: detect toxic flow regimes; high VPIN should trigger WAIT or tighter risk.
- Implementation target:
  - New module (suggested): `chimera/orderflow/vpin.py` (UNIMPLEMENTED)
- Integration target:
  - Produce a Tier B feature when computed from Tier A trade tape.
  - Produce Tier C when computed from candle-estimated or simulated tape.

## 2) Adversarial Robustness Suite (Anti-Overfit)

### Permutation Tests (Monte Carlo)

- Goal: show the strategy signal is not an artifact of ordering.
- Implementation target:
  - New module (suggested): `chimera/evaluation/robustness.py` (UNIMPLEMENTED)
- Minimal test:
  - A strategy should lose significance when returns are permuted.

### White’s Reality Check (Multiple Testing)

- Goal: correct for data snooping when many variants/genomes are tried.
- Implementation target:
  - Extend `chimera/evaluation/robustness.py` with a bootstrap-max null distribution.

### Regime Stress Testing

- Goal: backtests must report performance across synthetic regimes and real regimes (when real data loaders exist).
- Existing foundation:
  - Regime-tagged synthetic generator exists in `chimera/data/loader.py` (see `Generated ... bars with regime changes` in verifier output).

## 3) Online Regime Detection (Consistency Across Conditions)

### Online HMM Filter

- Goal: estimate latent market states (trend/range/high-vol/low-vol) in real time with state-transition probabilities.
- Existing code gap:
  - `chimera/intelligence/regime_classifier.py` exists but is heuristic (not a true online HMM).
- Implementation target:
  - New module (suggested): `chimera/intelligence/online_hmm.py` (UNIMPLEMENTED)
- Acceptance criteria:
  - Unit tests on synthetic sequences with known regime switches.
  - If regime is inferred from Tier C inputs in live mode, it must be advisory-only (cannot gate trade permission/confidence).

## Next Concrete Sprint (10-Day Target)

1. Implement VPIN + tick imbalance bars as pure functions with unit tests (no network).
2. Implement robustness suite (permutation + reality check) and wire into CLI as a report generator.
3. Implement online HMM regime filter and expose regime probabilities in the WeavePacket (advisory at first).

