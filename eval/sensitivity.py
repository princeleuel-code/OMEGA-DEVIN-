from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Sequence, Tuple

import random

import pandas as pd

from chimera.evaluation.walk_forward import WalkForwardConfig, walk_forward
from chimera.evolution.genome import GenomeConfig, StrategyGenome

from backtest.engine import df_to_ohlcv, symbol_backtest_config


@dataclass(frozen=True)
class BandVariant:
    genome: StrategyGenome
    param: str
    value: Any


def _clamp(x: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, x))


def generate_band_variants(
    base: StrategyGenome,
    *,
    band: float = 0.10,
    max_variants: int = 16,
    seed: int = 1337,
    include_bools: bool = False,
) -> List[BandVariant]:
    """Generate +/- band variants around a base genome (parameter stability band)."""
    if band <= 0:
        raise ValueError("band must be > 0")
    if max_variants <= 0:
        return []

    cfg = GenomeConfig()
    rng = random.Random(seed)

    float_params: List[Tuple[str, Tuple[float, float]]] = [
        ("min_confidence", (cfg.min_confidence[0], cfg.min_confidence[1])),
        ("atr_multiplier_sl", (cfg.atr_multiplier_sl[0], cfg.atr_multiplier_sl[1])),
        ("atr_multiplier_tp", (cfg.atr_multiplier_tp[0], cfg.atr_multiplier_tp[1])),
        ("risk_per_trade_pct", (cfg.risk_per_trade_pct[0], cfg.risk_per_trade_pct[1])),
        ("max_drawdown_pct", (cfg.max_drawdown_pct[0], cfg.max_drawdown_pct[1])),
        ("min_atr", (cfg.min_atr[0], cfg.min_atr[1])),
        ("max_spread_atr_ratio", (cfg.max_spread_atr_ratio[0], cfg.max_spread_atr_ratio[1])),
        ("min_volume_ratio", (cfg.min_volume_ratio[0], cfg.min_volume_ratio[1])),
        ("trend_affinity", (0.0, 1.0)),
        ("volatility_affinity", (0.0, 1.0)),
    ]
    int_params: List[Tuple[str, Tuple[int, int]]] = [
        ("min_swing_distance", (int(cfg.min_swing_distance[0]), int(cfg.min_swing_distance[1]))),
        ("max_trades_per_day", (int(cfg.max_trades_per_day[0]), int(cfg.max_trades_per_day[1]))),
        ("hold_bars_min", (int(cfg.hold_bars_min[0]), int(cfg.hold_bars_min[1]))),
        ("hold_bars_max", (int(cfg.hold_bars_max[0]), int(cfg.hold_bars_max[1]))),
    ]
    bool_params = ["require_displacement", "require_structure_break"]

    # Shuffle the parameter order so we don't bias toward the early fields.
    rng.shuffle(float_params)
    rng.shuffle(int_params)

    variants: List[BandVariant] = []

    def add_variant(param: str, value: Any) -> None:
        nonlocal variants
        g = StrategyGenome.from_dict(base.to_dict())
        # Ensure a new genome_id is generated.
        g.genome_id = ""
        setattr(g, param, value)

        # Keep timing constraints sane.
        if g.hold_bars_min > g.hold_bars_max:
            g.hold_bars_min, g.hold_bars_max = g.hold_bars_max, g.hold_bars_min

        # Re-run post-init by constructing anew (regenerates genome_id).
        g2 = StrategyGenome.from_dict(g.to_dict())
        variants.append(BandVariant(genome=g2, param=param, value=value))

    for param, (lo, hi) in float_params:
        if len(variants) >= max_variants:
            break
        base_val = float(getattr(base, param))
        down = _clamp(base_val * (1.0 - band), lo, hi)
        up = _clamp(base_val * (1.0 + band), lo, hi)
        add_variant(param, down)
        if len(variants) >= max_variants:
            break
        add_variant(param, up)

    for param, (lo, hi) in int_params:
        if len(variants) >= max_variants:
            break
        base_val = int(getattr(base, param))
        span = max(1, int(round((hi - lo) * band)))
        down = max(lo, base_val - span)
        up = min(hi, base_val + span)
        add_variant(param, int(down))
        if len(variants) >= max_variants:
            break
        add_variant(param, int(up))

    if include_bools:
        for param in bool_params:
            if len(variants) >= max_variants:
                break
            add_variant(param, not bool(getattr(base, param)))

    return variants[:max_variants]


def parameter_stability_report(
    *,
    bars: pd.DataFrame,
    base: StrategyGenome,
    symbol: str,
    timeframe: str,
    band: float = 0.10,
    max_variants: int = 12,
    seed: int = 1337,
    wf_config: Optional[WalkForwardConfig] = None,
) -> Dict[str, object]:
    """Run parameter stability evaluation (sensitivity band) using walk-forward."""
    variants = generate_band_variants(base, band=band, max_variants=max_variants, seed=seed)
    if not variants:
        return {"variants": 0, "pass_rate": 0.0, "return_std": 0.0, "details": []}

    # Use conservative but fast walk-forward defaults if none provided.
    wf_cfg = wf_config or WalkForwardConfig(n_folds=3, train_bars=150, test_bars=50, purge_bars=5, bootstrap_samples=100)
    bt_cfg = symbol_backtest_config(symbol=symbol)

    data = df_to_ohlcv(bars, symbol=symbol)

    returns: List[float] = []
    passed = 0
    details: List[Dict[str, object]] = []
    for v in variants:
        rep = walk_forward(data, v.genome, bt_cfg, wf_cfg)
        avg_ret = float(rep.aggregate.get("avg_return", 0.0))
        returns.append(avg_ret)
        is_pass = bool(rep.passed_all_gates)
        if is_pass:
            passed += 1
        details.append(
            {
                "param": v.param,
                "value": v.value,
                "genome_id": v.genome.genome_id,
                "passed": is_pass,
                "avg_return": avg_ret,
                "avg_sharpe": float(rep.aggregate.get("avg_sharpe", 0.0)),
                "pass_rate": float(rep.aggregate.get("pass_rate", 0.0)),
                "verdict": str(rep.verdict),
            }
        )

    # Std dev across avg_returns as a simple stability metric.
    m = sum(returns) / len(returns) if returns else 0.0
    var = sum((x - m) ** 2 for x in returns) / (len(returns) - 1) if len(returns) > 1 else 0.0
    ret_std = var ** 0.5

    return {
        "symbol": symbol,
        "timeframe": timeframe,
        "band": float(band),
        "variants": len(variants),
        "passed": int(passed),
        "pass_rate": float(passed / len(variants)),
        "return_std": float(ret_std),
        "details": details,
    }

