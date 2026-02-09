from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, List, Sequence

import random


def _max_drawdown_pct(equity: Sequence[float]) -> float:
    if not equity:
        return 0.0
    peak = equity[0]
    max_dd = 0.0
    for x in equity:
        if x > peak:
            peak = x
        if peak > 0:
            dd = (peak - x) / peak * 100.0
            if dd > max_dd:
                max_dd = dd
    return float(max_dd)


def _percentiles(xs: List[float], ps: Sequence[float]) -> Dict[str, float]:
    if not xs:
        return {f"p{int(p*100):02d}": 0.0 for p in ps}
    xs_sorted = sorted(xs)
    out: Dict[str, float] = {}
    n = len(xs_sorted)
    for p in ps:
        idx = int(p * (n - 1))
        out[f"p{int(p*100):02d}"] = float(xs_sorted[idx])
    return out


def trade_order_monte_carlo(
    trade_returns_pct: Sequence[float],
    *,
    initial_capital: float = 10_000.0,
    simulations: int = 500,
    seed: int = 1337,
) -> Dict[str, object]:
    """Monte Carlo on trade order by shuffling trade return percentages.

    Inputs are per-trade return percentages (e.g. Trade.pnl_pct), which makes the
    simulation approximately order-invariant under percent-risk sizing.
    """
    if simulations <= 0:
        raise ValueError("simulations must be > 0")

    base = [float(r) for r in trade_returns_pct]
    rng = random.Random(seed)

    def run_seq(seq: Sequence[float]) -> Dict[str, float]:
        eq = float(initial_capital)
        curve = [eq]
        for r_pct in seq:
            eq *= 1.0 + (r_pct / 100.0)
            curve.append(eq)
        return {
            "final_equity": float(eq),
            "max_drawdown_pct": _max_drawdown_pct(curve),
        }

    observed = run_seq(base)

    finals: List[float] = []
    dds: List[float] = []
    work = base[:]
    for _ in range(simulations):
        rng.shuffle(work)
        r = run_seq(work)
        finals.append(float(r["final_equity"]))
        dds.append(float(r["max_drawdown_pct"]))

    return {
        "simulations": int(simulations),
        "seed": int(seed),
        "observed": observed,
        "final_equity": _percentiles(finals, [0.05, 0.5, 0.95]),
        "max_drawdown_pct": _percentiles(dds, [0.05, 0.5, 0.95]),
    }

