from __future__ import annotations

import hashlib
import json
import subprocess
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

import random

import pandas as pd

from chimera.evaluation.robustness import robustness_report
from chimera.evaluation.score import Scorer, ScorerConfig
from chimera.evaluation.walk_forward import WalkForwardConfig, walk_forward
from chimera.evolution.genome import GenomeConfig, StrategyGenome, create_default_genome, create_random_genome

from backtest.engine import backtest_summary, df_to_ohlcv, run_backtest, symbol_backtest_config
from eval.sensitivity import parameter_stability_report
from eval.trade_order_mc import trade_order_monte_carlo

from .registry import ExperimentRegistry, ExperimentRow


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _hash_dict(d: Dict[str, Any]) -> str:
    blob = json.dumps(d, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()


def _git_state(repo_root: Path) -> Dict[str, Any]:
    sha = "UNKNOWN"
    branch = "UNKNOWN"
    dirty = False
    try:
        sha = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=str(repo_root)).decode().strip()
        branch = subprocess.check_output(["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=str(repo_root)).decode().strip()
        status = subprocess.check_output(["git", "status", "--porcelain"], cwd=str(repo_root)).decode().strip()
        dirty = bool(status)
    except Exception:
        pass
    return {"sha": sha, "branch": branch, "dirty": dirty}


def _json_write(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")


@dataclass(frozen=True)
class CriticConfig:
    """Pass/fail gates for the research agent."""

    require_backtest_risk_gates: bool = True
    require_walk_forward_pass: bool = True

    # Robustness: smaller p-value implies observed return is unlikely under shuffled null.
    max_robustness_p_value_return: float = 0.20

    # Stability band: variants should not catastrophically flip verdict.
    min_stability_pass_rate: float = 0.25
    max_stability_return_std: float = 10.0

    # Monte Carlo trade order: fail if "bad-case" equity is consistently below start.
    require_mc_p05_equity_not_below_initial: bool = True


@dataclass(frozen=True)
class PlannerConfig:
    seed: int = 1337
    max_experiments: int = 12
    max_depth: int = 4

    # Genome exploration
    random_start_experiments: int = 2
    mutations_per_parent: int = 2
    mutation_strength: float = 0.15
    max_mutated_params: int = 4


@dataclass(frozen=True)
class EvaluationConfig:
    """Evaluation harness settings (anti-overfit)."""

    # Backtest costs (always on)
    initial_capital: float = 10_000.0
    spread_pips: float = 1.0
    slippage_pips: float = 0.5
    commission_per_lot: float = 0.0

    # Walk-forward
    wf: WalkForwardConfig = field(default_factory=lambda: WalkForwardConfig(n_folds=3, train_bars=150, test_bars=50, purge_bars=5, bootstrap_samples=200))

    # Robustness permutation suite
    robustness_permutations: int = 100
    robustness_seed: int = 1337

    # Monte Carlo (trade order shuffle)
    mc_simulations: int = 250
    mc_seed: int = 1337

    # Parameter stability band
    stability_band: float = 0.10
    stability_variants: int = 8
    stability_seed: int = 1337


@dataclass(frozen=True)
class ResearchAgentConfig:
    symbol: str
    timeframe: str
    planner: PlannerConfig = field(default_factory=PlannerConfig)
    evaluation: EvaluationConfig = field(default_factory=EvaluationConfig)
    critic: CriticConfig = field(default_factory=CriticConfig)

    scorer: ScorerConfig = field(default_factory=ScorerConfig)


@dataclass(frozen=True)
class PlannedExperiment:
    experiment_id: str
    parent_id: Optional[str]
    depth: int
    genome: StrategyGenome


class ResearchAgent:
    """Planner -> Executor -> Critic loop for hypothesis discovery.

    This is intentionally deterministic given the configured seed(s).
    """

    def __init__(
        self,
        *,
        config: ResearchAgentConfig,
        bars: pd.DataFrame,
        dataset_hash: str,
        run_dir: Path,
        repo_root: Path,
        registry: ExperimentRegistry,
    ) -> None:
        self.config = config
        self.bars = bars
        self.dataset_hash = dataset_hash
        self.run_dir = Path(run_dir)
        self.repo_root = Path(repo_root)
        self.registry = registry

        self._rng = random.Random(int(config.planner.seed))

    def run(self) -> Dict[str, Any]:
        self.run_dir.mkdir(parents=True, exist_ok=True)

        manifest = self._write_run_manifest()

        planned = self._plan_experiments()
        results: List[Dict[str, Any]] = []
        passed: List[Dict[str, Any]] = []

        for exp in planned:
            exp_dir = self.run_dir / "experiments" / exp.experiment_id
            exp_dir.mkdir(parents=True, exist_ok=True)

            evaluated_at = _utc_now_iso()
            try:
                eval_payload = self._execute(exp, exp_dir=exp_dir)
                passed_exp, fail_reasons = self._critic(eval_payload)
                score = float(eval_payload.get("scorecard", {}).get("fitness", -1.0))
            except Exception as e:
                eval_payload = {"error": f"{type(e).__name__}: {e}"}
                passed_exp = False
                fail_reasons = [f"EVAL_ERROR:{type(e).__name__}"]
                score = -1.0

            out = {
                "experiment_id": exp.experiment_id,
                "parent_id": exp.parent_id,
                "depth": exp.depth,
                "evaluated_at": evaluated_at,
                "symbol": self.config.symbol,
                "timeframe": self.config.timeframe,
                "dataset_hash": self.dataset_hash,
                "genome": exp.genome.to_dict(),
                "passed": bool(passed_exp),
                "score": float(score),
                "fail_reasons": list(fail_reasons),
                "results": eval_payload,
            }
            _json_write(exp_dir / "experiment.json", out)
            results.append(out)
            if passed_exp:
                passed.append(out)

            # Upsert into registry for cross-run leaderboard.
            self.registry.upsert(
                ExperimentRow(
                    experiment_id=exp.experiment_id,
                    run_id=str(manifest["run_id"]),
                    created_at=evaluated_at,
                    symbol=self.config.symbol,
                    timeframe=self.config.timeframe,
                    dataset_hash=self.dataset_hash,
                    genome_id=exp.genome.genome_id,
                    passed=bool(passed_exp),
                    score=float(score),
                    fail_reasons=list(fail_reasons),
                    artifacts_dir=str(exp_dir),
                    genome_json=exp.genome.to_dict(),
                    results_json=eval_payload,
                )
            )

        leaderboard = self.registry.leaderboard(symbol=self.config.symbol, timeframe=self.config.timeframe, limit=20, passed_only=True)
        _json_write(self.run_dir / "leaderboard.json", leaderboard)

        passed_sorted = sorted(passed, key=lambda r: float(r.get("score", -1.0)), reverse=True)
        report = {
            "run_id": manifest["run_id"],
            "created_at": manifest["created_at"],
            "symbol": self.config.symbol,
            "timeframe": self.config.timeframe,
            "dataset_hash": self.dataset_hash,
            "manifest": manifest,
            "experiments_total": len(results),
            "experiments_passed": len(passed),
            "best_passed": passed_sorted[0] if passed_sorted else None,
            "leaderboard": leaderboard,
            "experiments": [{"experiment_id": r["experiment_id"], "passed": r["passed"], "score": r["score"]} for r in results],
        }
        _json_write(self.run_dir / "run_report.json", report)
        return report

    def _write_run_manifest(self) -> Dict[str, Any]:
        # Keep run_id stable/traceable: prefer the run directory name if it
        # matches our convention, otherwise generate one.
        run_id = self.run_dir.name
        if not run_id.startswith("rqra_"):
            run_id = f"rqra_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}_{uuid.uuid4().hex[:8]}"

        bars_start = str(self.bars.index.min()) if not self.bars.empty else ""
        bars_end = str(self.bars.index.max()) if not self.bars.empty else ""

        cfg = {
            "symbol": self.config.symbol,
            "timeframe": self.config.timeframe,
            "planner": self.config.planner.__dict__,
            "critic": self.config.critic.__dict__,
            "evaluation": {
                "initial_capital": self.config.evaluation.initial_capital,
                "spread_pips": self.config.evaluation.spread_pips,
                "slippage_pips": self.config.evaluation.slippage_pips,
                "commission_per_lot": self.config.evaluation.commission_per_lot,
                "wf": self.config.evaluation.wf.__dict__,
                "robustness_permutations": self.config.evaluation.robustness_permutations,
                "robustness_seed": self.config.evaluation.robustness_seed,
                "mc_simulations": self.config.evaluation.mc_simulations,
                "mc_seed": self.config.evaluation.mc_seed,
                "stability_band": self.config.evaluation.stability_band,
                "stability_variants": self.config.evaluation.stability_variants,
                "stability_seed": self.config.evaluation.stability_seed,
            },
            "scorer": self.config.scorer.__dict__,
        }

        manifest = {
            "run_id": run_id,
            "created_at": _utc_now_iso(),
            "git": _git_state(self.repo_root),
            "dataset_hash": self.dataset_hash,
            "bars": {
                "count": int(len(self.bars)),
                "start": bars_start,
                "end": bars_end,
            },
            "seed": int(self.config.planner.seed),
            "config": cfg,
            "config_hash": _hash_dict(cfg),
        }
        _json_write(self.run_dir / "run_manifest.json", manifest)
        return manifest

    def _plan_experiments(self) -> List[PlannedExperiment]:
        pcfg = self.config.planner
        max_exps = max(1, int(pcfg.max_experiments))
        max_depth = max(0, int(pcfg.max_depth))

        planned: List[PlannedExperiment] = []

        # Start from a conservative default genome.
        base = create_default_genome()
        planned.append(self._mk_exp(genome=base, parent_id=None, depth=0))

        # Add a couple random starting points for diversity.
        for _ in range(max(0, int(pcfg.random_start_experiments))):
            planned.append(self._mk_exp(genome=create_random_genome(), parent_id=None, depth=0))

        # Expand by mutating parents in FIFO order until budget.
        idx = 0
        while len(planned) < max_exps and idx < len(planned):
            parent = planned[idx]
            idx += 1
            if parent.depth >= max_depth:
                continue
            for _ in range(max(0, int(pcfg.mutations_per_parent))):
                if len(planned) >= max_exps:
                    break
                child = self._mutate_genome(parent.genome)
                planned.append(self._mk_exp(genome=child, parent_id=parent.experiment_id, depth=parent.depth + 1))

        return planned[:max_exps]

    def _mk_exp(self, *, genome: StrategyGenome, parent_id: Optional[str], depth: int) -> PlannedExperiment:
        eid = uuid.uuid4().hex[:12]
        return PlannedExperiment(experiment_id=eid, parent_id=parent_id, depth=int(depth), genome=genome)

    def _mutate_genome(self, genome: StrategyGenome) -> StrategyGenome:
        cfg = GenomeConfig()
        pcfg = self.config.planner

        g = StrategyGenome.from_dict(genome.to_dict())
        g.genome_id = ""  # regenerate

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

        # Pick a handful of parameters to mutate.
        choices: List[Tuple[str, str]] = [("f", p[0]) for p in float_params] + [("i", p[0]) for p in int_params] + [("b", p) for p in bool_params]
        self._rng.shuffle(choices)
        k = max(1, min(int(pcfg.max_mutated_params), len(choices)))
        chosen = choices[:k]

        strength = float(pcfg.mutation_strength)

        float_bounds = {k: b for k, b in float_params}
        int_bounds = {k: b for k, b in int_params}

        def clamp(x: float, lo: float, hi: float) -> float:
            return max(lo, min(hi, x))

        for kind, name in chosen:
            if kind == "f":
                lo, hi = float_bounds[name]
                base_val = float(getattr(g, name))
                delta = (self._rng.random() * 2.0 - 1.0) * strength
                if lo == 0.0 and hi == 1.0:
                    new_val = clamp(base_val + delta, lo, hi)
                else:
                    new_val = clamp(base_val * (1.0 + delta), lo, hi)
                setattr(g, name, float(new_val))
            elif kind == "i":
                lo, hi = int_bounds[name]
                base_val = int(getattr(g, name))
                span = max(1, int(round((hi - lo) * strength)))
                new_val = max(lo, min(hi, base_val + self._rng.randint(-span, span)))
                setattr(g, name, int(new_val))
            else:
                setattr(g, name, not bool(getattr(g, name)))

        # Keep timing constraints sane.
        if g.hold_bars_min > g.hold_bars_max:
            g.hold_bars_min, g.hold_bars_max = g.hold_bars_max, g.hold_bars_min

        return StrategyGenome.from_dict(g.to_dict())

    def _execute(self, exp: PlannedExperiment, *, exp_dir: Path) -> Dict[str, Any]:
        symbol = self.config.symbol
        tf = self.config.timeframe
        ecfg = self.config.evaluation

        bt_cfg = symbol_backtest_config(
            symbol=symbol,
            initial_capital=ecfg.initial_capital,
            spread_pips=ecfg.spread_pips,
            slippage_pips=ecfg.slippage_pips,
            commission_per_lot=ecfg.commission_per_lot,
        )

        # 1) Backtest
        bt_res = run_backtest(bars=self.bars, genome=exp.genome, config=bt_cfg, create_manifest=False)
        bt_sum = backtest_summary(bt_res)
        _json_write(exp_dir / "backtest_summary.json", bt_sum)

        # 2) Scorecard (deterministic fitness + risk gates)
        scorer = Scorer(config=self.config.scorer)
        scorecard = scorer.score(bt_res).to_dict()
        _json_write(exp_dir / "scorecard.json", scorecard)

        # Convert once for the remaining suites.
        bars_ohlcv = df_to_ohlcv(self.bars, symbol=symbol)

        # 3) Walk-forward (purged)
        wf = walk_forward(bars_ohlcv, exp.genome, bt_cfg, ecfg.wf)
        wf_dict = wf.to_dict()
        _json_write(exp_dir / "walk_forward.json", wf_dict)

        # 4) Robustness suite (permutation null)
        rb = robustness_report(
            bars=bars_ohlcv,
            genome=exp.genome,
            backtest_config=bt_cfg,
            permutations=int(ecfg.robustness_permutations),
            seed=int(ecfg.robustness_seed),
        )
        _json_write(exp_dir / "robustness.json", rb)

        # 5) Monte Carlo on trade order (shuffle trades)
        trade_rets = [float(t.pnl_pct) for t in bt_res.trades]
        mc = trade_order_monte_carlo(
            trade_rets,
            initial_capital=float(bt_cfg.initial_capital),
            simulations=int(ecfg.mc_simulations),
            seed=int(ecfg.mc_seed),
        )
        _json_write(exp_dir / "trade_order_mc.json", mc)

        # 6) Parameter stability band (walk-forward over +/- band variants)
        stab = parameter_stability_report(
            bars=self.bars,
            base=exp.genome,
            symbol=symbol,
            timeframe=tf,
            band=float(ecfg.stability_band),
            max_variants=int(ecfg.stability_variants),
            seed=int(ecfg.stability_seed),
            wf_config=WalkForwardConfig(n_folds=2, train_bars=100, test_bars=50, purge_bars=5, bootstrap_samples=100),
        )
        _json_write(exp_dir / "stability_band.json", stab)

        return {
            "backtest": bt_sum,
            "scorecard": scorecard,
            "walk_forward": wf_dict,
            "robustness": rb,
            "trade_order_mc": mc,
            "stability_band": stab,
        }

    def _critic(self, payload: Dict[str, Any]) -> Tuple[bool, List[str]]:
        cfg = self.config.critic
        reasons: List[str] = []

        scorecard = payload.get("scorecard", {})
        if cfg.require_backtest_risk_gates and not bool(scorecard.get("passed_risk_gates", False)):
            reasons.append("BACKTEST_RISK_GATES_FAILED")

        wf = payload.get("walk_forward", {})
        if cfg.require_walk_forward_pass and not bool(wf.get("passed_all_gates", False)):
            reasons.append(f"WALK_FORWARD_FAILED:{wf.get('verdict', 'UNKNOWN')}")

        rb = payload.get("robustness", {})
        try:
            p = float(rb.get("permutation_null", {}).get("p_value_return", 1.0))
            if p > cfg.max_robustness_p_value_return:
                reasons.append(f"ROBUSTNESS_PVALUE_RETURN:{p:.3f}>{cfg.max_robustness_p_value_return:.3f}")
        except Exception:
            reasons.append("ROBUSTNESS_MISSING")

        stab = payload.get("stability_band", {})
        try:
            pr = float(stab.get("pass_rate", 0.0))
            rs = float(stab.get("return_std", 0.0))
            if pr < cfg.min_stability_pass_rate:
                reasons.append(f"STABILITY_PASS_RATE:{pr:.3f}<{cfg.min_stability_pass_rate:.3f}")
            if rs > cfg.max_stability_return_std:
                reasons.append(f"STABILITY_RETURN_STD:{rs:.3f}>{cfg.max_stability_return_std:.3f}")
        except Exception:
            reasons.append("STABILITY_MISSING")

        mc = payload.get("trade_order_mc", {})
        if cfg.require_mc_p05_equity_not_below_initial:
            try:
                p05 = float(mc.get("final_equity", {}).get("p05", 0.0))
                observed = mc.get("observed", {}) or {}
                initial = float(observed.get("final_equity", 0.0))
                # If observed is below start, p05 is not meaningful; still fail.
                if p05 < float(self.config.evaluation.initial_capital):
                    reasons.append("MC_FINAL_EQUITY_P05_BELOW_INITIAL")
                if initial < float(self.config.evaluation.initial_capital):
                    reasons.append("MC_OBSERVED_FINAL_EQUITY_BELOW_INITIAL")
            except Exception:
                reasons.append("MC_MISSING")

        return (len(reasons) == 0), reasons
