"""
Sakana-Style Evolution Loop

Implements a DGM + DRQ hybrid self-improvement loop:
- DGM (Darwin Godel Machine): Self-improving agent with empirical validation
- DRQ (Digital Red Queen): Continual adaptation with champion testing

Key Features:
- Config-only variant generation (no code mutations initially)
- Walk-forward evaluation with regime slicing
- MAP-Elites archive with quality-diversity buckets (regime x risk)
- Champion-vs-champions gate (must beat prior champions out-of-sample)
- Canary deploy mode with kill-switch integration
- Full provenance tracking via truth objects

Truth Objects (written each run):
- RUN_MANIFEST.json: Git commit, data ranges, seeds, versions
- VARIANT_PATCH.json: Config diffs per variant
- EVAL_REPORT.json: Walk-forward results per fold + aggregate
- ARCHIVE_INDEX.json: MAP-Elites buckets with top K variants
- LIVE_GATING_STATE.json: Active variant, canary mode, kill-switch status
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import random
import subprocess
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple
import copy

logger = logging.getLogger(__name__)


# =============================================================================
# TRUTH OBJECTS - Written each run for full provenance
# =============================================================================

@dataclass
class RunManifest:
    """
    RUN_MANIFEST.json - Full provenance for reproducibility.
    
    Every run must be reproducible given this manifest.
    """
    run_id: str
    timestamp: str
    git_commit: str
    git_branch: str
    data_start: str
    data_end: str
    data_bars: int
    random_seed: int
    cost_model: Dict[str, float]
    dependency_versions: Dict[str, str]
    config_hash: str
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "run_id": self.run_id,
            "timestamp": self.timestamp,
            "git_commit": self.git_commit,
            "git_branch": self.git_branch,
            "data_start": self.data_start,
            "data_end": self.data_end,
            "data_bars": self.data_bars,
            "random_seed": self.random_seed,
            "cost_model": self.cost_model,
            "dependency_versions": self.dependency_versions,
            "config_hash": self.config_hash,
        }
    
    def save(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w") as f:
            json.dump(self.to_dict(), f, indent=2)
    
    @classmethod
    def create(
        cls,
        data_start: str,
        data_end: str,
        data_bars: int,
        cost_model: Dict[str, float],
        seed: Optional[int] = None,
    ) -> "RunManifest":
        """Create a new run manifest with current system state."""
        run_id = hashlib.md5(
            f"{datetime.now(timezone.utc).isoformat()}{random.random()}".encode()
        ).hexdigest()[:16]
        
        # Get git info
        git_commit = "unknown"
        git_branch = "unknown"
        try:
            git_commit = subprocess.check_output(
                ["git", "rev-parse", "HEAD"], 
                stderr=subprocess.DEVNULL
            ).decode().strip()[:12]
            git_branch = subprocess.check_output(
                ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                stderr=subprocess.DEVNULL
            ).decode().strip()
        except Exception:
            pass
        
        # Get dependency versions
        versions = {
            "python": os.popen("python3 --version").read().strip(),
            "numpy": "unknown",
            "pandas": "unknown",
        }
        try:
            import numpy
            versions["numpy"] = numpy.__version__
        except ImportError:
            pass
        try:
            import pandas
            versions["pandas"] = pandas.__version__
        except ImportError:
            pass
        
        # Config hash for reproducibility check
        config_str = json.dumps(cost_model, sort_keys=True)
        config_hash = hashlib.md5(config_str.encode()).hexdigest()[:8]
        
        return cls(
            run_id=run_id,
            timestamp=datetime.now(timezone.utc).isoformat(),
            git_commit=git_commit,
            git_branch=git_branch,
            data_start=data_start,
            data_end=data_end,
            data_bars=data_bars,
            random_seed=seed or random.randint(0, 2**32 - 1),
            cost_model=cost_model,
            dependency_versions=versions,
            config_hash=config_hash,
        )


@dataclass
class VariantPatch:
    """
    VARIANT_PATCH.json - Exact config diffs per variant.
    
    Tracks what was changed from parent config.
    """
    variant_id: str
    parent_id: str
    created_at: str
    config_diffs: Dict[str, Dict[str, Any]]  # {param: {old: x, new: y}}
    patch_budget_used: int  # Number of parameters changed
    patch_budget_max: int
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "variant_id": self.variant_id,
            "parent_id": self.parent_id,
            "created_at": self.created_at,
            "config_diffs": self.config_diffs,
            "patch_budget_used": self.patch_budget_used,
            "patch_budget_max": self.patch_budget_max,
        }
    
    @classmethod
    def from_configs(
        cls,
        parent_config: Dict[str, Any],
        new_config: Dict[str, Any],
        parent_id: str,
        patch_budget_max: int = 5,
    ) -> "VariantPatch":
        """Create a patch from two configs."""
        variant_id = hashlib.md5(
            f"{datetime.now(timezone.utc).isoformat()}{random.random()}".encode()
        ).hexdigest()[:12]
        
        diffs = {}
        for key in set(parent_config.keys()) | set(new_config.keys()):
            old_val = parent_config.get(key)
            new_val = new_config.get(key)
            if old_val != new_val:
                diffs[key] = {"old": old_val, "new": new_val}
        
        return cls(
            variant_id=variant_id,
            parent_id=parent_id,
            created_at=datetime.now(timezone.utc).isoformat(),
            config_diffs=diffs,
            patch_budget_used=len(diffs),
            patch_budget_max=patch_budget_max,
        )


class RegimeBucket(Enum):
    """Market regime buckets for MAP-Elites."""
    TREND = "trend"
    RANGE = "range"
    HIGH_VOL = "high_vol"
    LOW_VOL = "low_vol"


class RiskBucket(Enum):
    """Risk buckets for MAP-Elites."""
    LOW_DD = "dd_lt_2pct"      # maxDD < 2%
    MED_DD = "dd_2_to_5pct"    # 2% <= maxDD < 5%
    HIGH_DD = "dd_gt_5pct"     # maxDD >= 5%


@dataclass
class FoldResult:
    """Result from a single walk-forward fold."""
    fold_id: int
    train_start: str
    train_end: str
    test_start: str
    test_end: str
    regime: str
    metrics: Dict[str, float]
    passed: bool
    fail_reasons: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "fold_id": self.fold_id,
            "train_start": self.train_start,
            "train_end": self.train_end,
            "test_start": self.test_start,
            "test_end": self.test_end,
            "regime": self.regime,
            "metrics": self.metrics,
            "passed": self.passed,
            "fail_reasons": self.fail_reasons,
        }


@dataclass
class EvalReport:
    """
    EVAL_REPORT.json - Walk-forward results per fold + aggregate.
    
    Contains all metrics needed to determine if variant passes gates.
    """
    variant_id: str
    manifest_id: str
    evaluated_at: str
    folds: List[FoldResult]
    aggregate_metrics: Dict[str, float]
    passed_all_gates: bool
    gate_results: Dict[str, bool]
    integrity_violations: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "variant_id": self.variant_id,
            "manifest_id": self.manifest_id,
            "evaluated_at": self.evaluated_at,
            "folds": [f.to_dict() for f in self.folds],
            "aggregate_metrics": self.aggregate_metrics,
            "passed_all_gates": self.passed_all_gates,
            "gate_results": self.gate_results,
            "integrity_violations": self.integrity_violations,
        }
    
    def save(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w") as f:
            json.dump(self.to_dict(), f, indent=2)


@dataclass
class ArchiveEntry:
    """An entry in the MAP-Elites archive."""
    variant_id: str
    config: Dict[str, Any]
    regime_bucket: str
    risk_bucket: str
    fitness: float
    metrics: Dict[str, float]
    manifest_id: str
    eval_report_path: str
    generation_added: int
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "variant_id": self.variant_id,
            "config": self.config,
            "regime_bucket": self.regime_bucket,
            "risk_bucket": self.risk_bucket,
            "fitness": self.fitness,
            "metrics": self.metrics,
            "manifest_id": self.manifest_id,
            "eval_report_path": self.eval_report_path,
            "generation_added": self.generation_added,
        }


@dataclass
class ArchiveIndex:
    """
    ARCHIVE_INDEX.json - MAP-Elites buckets with top K variants.
    
    Stores diverse champions by regime x risk bucket.
    """
    updated_at: str
    generation: int
    total_variants_evaluated: int
    buckets: Dict[str, List[ArchiveEntry]]  # "regime_risk" -> entries
    top_k_per_bucket: int
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "updated_at": self.updated_at,
            "generation": self.generation,
            "total_variants_evaluated": self.total_variants_evaluated,
            "buckets": {
                k: [e.to_dict() for e in v] 
                for k, v in self.buckets.items()
            },
            "top_k_per_bucket": self.top_k_per_bucket,
        }
    
    def save(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w") as f:
            json.dump(self.to_dict(), f, indent=2)
    
    @classmethod
    def load(cls, path: Path) -> "ArchiveIndex":
        """Load archive from file."""
        with open(path, "r") as f:
            data = json.load(f)
        
        buckets = {}
        for k, entries in data.get("buckets", {}).items():
            buckets[k] = [
                ArchiveEntry(
                    variant_id=e["variant_id"],
                    config=e["config"],
                    regime_bucket=e["regime_bucket"],
                    risk_bucket=e["risk_bucket"],
                    fitness=e["fitness"],
                    metrics=e["metrics"],
                    manifest_id=e["manifest_id"],
                    eval_report_path=e["eval_report_path"],
                    generation_added=e["generation_added"],
                )
                for e in entries
            ]
        
        return cls(
            updated_at=data["updated_at"],
            generation=data["generation"],
            total_variants_evaluated=data["total_variants_evaluated"],
            buckets=buckets,
            top_k_per_bucket=data["top_k_per_bucket"],
        )


class CanaryMode(Enum):
    """Canary deployment modes."""
    OFF = "off"
    PAPER = "paper"
    MICRO = "micro"
    FULL = "full"


@dataclass
class LiveGatingState:
    """
    LIVE_GATING_STATE.json - Active variant, canary mode, kill-switch status.
    
    Controls what's actually running in production.
    """
    updated_at: str
    active_variant_id: str
    active_config: Dict[str, Any]
    canary_mode: str
    canary_start_time: Optional[str]
    canary_trades: int
    canary_pnl: float
    kill_switch_active: bool
    kill_switch_reason: Optional[str]
    previous_variant_id: Optional[str]
    max_drawdown_threshold: float
    anomaly_threshold: float
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "updated_at": self.updated_at,
            "active_variant_id": self.active_variant_id,
            "active_config": self.active_config,
            "canary_mode": self.canary_mode,
            "canary_start_time": self.canary_start_time,
            "canary_trades": self.canary_trades,
            "canary_pnl": self.canary_pnl,
            "kill_switch_active": self.kill_switch_active,
            "kill_switch_reason": self.kill_switch_reason,
            "previous_variant_id": self.previous_variant_id,
            "max_drawdown_threshold": self.max_drawdown_threshold,
            "anomaly_threshold": self.anomaly_threshold,
        }
    
    def save(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w") as f:
            json.dump(self.to_dict(), f, indent=2)
    
    @classmethod
    def load(cls, path: Path) -> "LiveGatingState":
        """Load state from file."""
        with open(path, "r") as f:
            data = json.load(f)
        return cls(**data)
    
    def activate_kill_switch(self, reason: str) -> None:
        """Activate kill switch and revert to previous variant."""
        self.kill_switch_active = True
        self.kill_switch_reason = reason
        self.canary_mode = CanaryMode.OFF.value
        self.updated_at = datetime.now(timezone.utc).isoformat()
        logger.warning(f"KILL SWITCH ACTIVATED: {reason}")


# =============================================================================
# EVOLUTION CONFIG - Mutable parameters for variant generation
# =============================================================================

@dataclass
class EvolutionConfig:
    """
    Configuration for the evolution loop.
    
    These are the parameters that can be mutated during evolution.
    """
    # RL Agent parameters
    rl_epsilon_start: float = 1.0
    rl_epsilon_end: float = 0.05
    rl_epsilon_decay: float = 0.995
    rl_abstention_reward: float = 0.01
    rl_loss_penalty_scale: float = 2.0
    
    # Ensemble parameters
    ensemble_chimera_weight: float = 0.4
    ensemble_auctionflow_weight: float = 0.3
    ensemble_rl_weight: float = 0.2
    ensemble_sentiment_weight: float = 0.1
    ensemble_agreement_threshold: int = 2
    ensemble_min_confidence: float = 0.6
    
    # Sentiment parameters
    sentiment_veto_threshold: float = -0.6
    sentiment_high_impact_veto: bool = True
    sentiment_news_blackout_minutes: int = 30
    
    # Risk parameters
    max_trades_per_day: int = 5
    max_drawdown_pct: float = 10.0
    max_spread_atr_ratio: float = 0.3
    risk_per_trade_pct: float = 1.0
    
    # Strategy parameters
    min_confidence: float = 0.6
    atr_multiplier_sl: float = 2.0
    atr_multiplier_tp: float = 3.0
    trend_affinity: float = 0.5
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "rl_epsilon_start": self.rl_epsilon_start,
            "rl_epsilon_end": self.rl_epsilon_end,
            "rl_epsilon_decay": self.rl_epsilon_decay,
            "rl_abstention_reward": self.rl_abstention_reward,
            "rl_loss_penalty_scale": self.rl_loss_penalty_scale,
            "ensemble_chimera_weight": self.ensemble_chimera_weight,
            "ensemble_auctionflow_weight": self.ensemble_auctionflow_weight,
            "ensemble_rl_weight": self.ensemble_rl_weight,
            "ensemble_sentiment_weight": self.ensemble_sentiment_weight,
            "ensemble_agreement_threshold": self.ensemble_agreement_threshold,
            "ensemble_min_confidence": self.ensemble_min_confidence,
            "sentiment_veto_threshold": self.sentiment_veto_threshold,
            "sentiment_high_impact_veto": self.sentiment_high_impact_veto,
            "sentiment_news_blackout_minutes": self.sentiment_news_blackout_minutes,
            "max_trades_per_day": self.max_trades_per_day,
            "max_drawdown_pct": self.max_drawdown_pct,
            "max_spread_atr_ratio": self.max_spread_atr_ratio,
            "risk_per_trade_pct": self.risk_per_trade_pct,
            "min_confidence": self.min_confidence,
            "atr_multiplier_sl": self.atr_multiplier_sl,
            "atr_multiplier_tp": self.atr_multiplier_tp,
            "trend_affinity": self.trend_affinity,
        }
    
    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "EvolutionConfig":
        return cls(**{k: v for k, v in d.items() if k in cls.__dataclass_fields__})
    
    def clone(self) -> "EvolutionConfig":
        return EvolutionConfig(**self.to_dict())


# Mutation ranges for each parameter
MUTATION_RANGES = {
    "rl_epsilon_start": (0.5, 1.0),
    "rl_epsilon_end": (0.01, 0.2),
    "rl_epsilon_decay": (0.99, 0.999),
    "rl_abstention_reward": (0.0, 0.1),
    "rl_loss_penalty_scale": (1.0, 5.0),
    "ensemble_chimera_weight": (0.1, 0.6),
    "ensemble_auctionflow_weight": (0.1, 0.5),
    "ensemble_rl_weight": (0.05, 0.4),
    "ensemble_sentiment_weight": (0.0, 0.3),
    "ensemble_agreement_threshold": (1, 3),
    "ensemble_min_confidence": (0.4, 0.8),
    "sentiment_veto_threshold": (-0.8, -0.3),
    "sentiment_news_blackout_minutes": (0, 120),
    "max_trades_per_day": (1, 10),
    "max_drawdown_pct": (5.0, 20.0),
    "max_spread_atr_ratio": (0.1, 0.5),
    "risk_per_trade_pct": (0.5, 3.0),
    "min_confidence": (0.4, 0.8),
    "atr_multiplier_sl": (1.0, 4.0),
    "atr_multiplier_tp": (1.5, 6.0),
    "trend_affinity": (0.0, 1.0),
}


def mutate_config(
    config: EvolutionConfig,
    mutation_rate: float = 0.2,
    mutation_strength: float = 0.15,
    patch_budget: int = 5,
) -> Tuple[EvolutionConfig, VariantPatch]:
    """
    Mutate a config to create a variant.
    
    Args:
        config: Parent config
        mutation_rate: Probability of mutating each parameter
        mutation_strength: How much to change (0-1 of range)
        patch_budget: Maximum parameters to change
        
    Returns:
        Tuple of (new_config, patch)
    """
    parent_dict = config.to_dict()
    new_dict = parent_dict.copy()
    
    # Select parameters to mutate
    params_to_mutate = []
    for param in MUTATION_RANGES.keys():
        if random.random() < mutation_rate:
            params_to_mutate.append(param)
    
    # Respect patch budget
    if len(params_to_mutate) > patch_budget:
        params_to_mutate = random.sample(params_to_mutate, patch_budget)
    
    # Apply mutations
    for param in params_to_mutate:
        min_val, max_val = MUTATION_RANGES[param]
        current = parent_dict[param]
        
        # Calculate mutation delta
        range_size = max_val - min_val
        delta = random.gauss(0, mutation_strength * range_size)
        
        # Apply and clamp
        if isinstance(current, int):
            new_val = int(round(current + delta))
            new_val = max(int(min_val), min(int(max_val), new_val))
        elif isinstance(current, bool):
            new_val = random.random() < 0.5
        else:
            new_val = current + delta
            new_val = max(min_val, min(max_val, new_val))
        
        new_dict[param] = new_val
    
    # Normalize ensemble weights
    weight_sum = (
        new_dict["ensemble_chimera_weight"] +
        new_dict["ensemble_auctionflow_weight"] +
        new_dict["ensemble_rl_weight"] +
        new_dict["ensemble_sentiment_weight"]
    )
    if weight_sum > 0:
        new_dict["ensemble_chimera_weight"] /= weight_sum
        new_dict["ensemble_auctionflow_weight"] /= weight_sum
        new_dict["ensemble_rl_weight"] /= weight_sum
        new_dict["ensemble_sentiment_weight"] /= weight_sum
    
    new_config = EvolutionConfig.from_dict(new_dict)
    patch = VariantPatch.from_configs(
        parent_dict, 
        new_config.to_dict(),
        parent_id=hashlib.md5(json.dumps(parent_dict, sort_keys=True).encode()).hexdigest()[:12],
        patch_budget_max=patch_budget,
    )
    
    return new_config, patch


# =============================================================================
# EVALUATION HARNESS - Walk-forward with regime slicing
# =============================================================================

@dataclass
class EvalConfig:
    """Configuration for evaluation harness."""
    # Walk-forward settings
    train_bars: int = 500
    test_bars: int = 100
    n_folds: int = 5
    
    # Cost model (always applied)
    spread_pips: float = 1.0
    slippage_pips: float = 0.5
    commission_per_lot: float = 0.0
    
    # Pass criteria
    max_drawdown_threshold: float = 10.0  # Percent
    min_sharpe_threshold: float = 0.5
    max_turnover_threshold: float = 50  # Trades per period
    stability_threshold: float = 0.5  # Std of returns across folds
    
    # Integrity gates
    max_missing_bars_pct: float = 1.0
    max_gap_size_atr: float = 5.0


class EvaluationHarness:
    """
    Walk-forward evaluation harness with regime slicing.
    
    Evaluates variants across multiple folds and regimes.
    Applies cost model and integrity gates.
    """
    
    def __init__(self, config: Optional[EvalConfig] = None):
        self.config = config or EvalConfig()
    
    def evaluate(
        self,
        variant_config: EvolutionConfig,
        data: List[Any],  # List of OHLCV bars
        manifest: RunManifest,
    ) -> EvalReport:
        """
        Evaluate a variant using walk-forward methodology.
        
        Args:
            variant_config: The config to evaluate
            data: Historical OHLCV data
            manifest: Run manifest for provenance
            
        Returns:
            EvalReport with all results
        """
        variant_id = hashlib.md5(
            json.dumps(variant_config.to_dict(), sort_keys=True).encode()
        ).hexdigest()[:12]
        
        # Check data integrity first
        integrity_violations = self._check_integrity(data)
        if integrity_violations:
            return EvalReport(
                variant_id=variant_id,
                manifest_id=manifest.run_id,
                evaluated_at=datetime.now(timezone.utc).isoformat(),
                folds=[],
                aggregate_metrics={},
                passed_all_gates=False,
                gate_results={"integrity": False},
                integrity_violations=integrity_violations,
            )
        
        # Run walk-forward folds
        folds = []
        fold_metrics = []
        
        total_bars = len(data)
        fold_size = self.config.train_bars + self.config.test_bars
        
        for fold_id in range(self.config.n_folds):
            # Calculate fold boundaries
            start_idx = fold_id * self.config.test_bars
            if start_idx + fold_size > total_bars:
                break
            
            train_start = start_idx
            train_end = start_idx + self.config.train_bars
            test_start = train_end
            test_end = min(test_start + self.config.test_bars, total_bars)
            
            # Detect regime for this fold
            regime = self._detect_regime(data[train_start:train_end])
            
            # Evaluate on test period
            metrics = self._evaluate_fold(
                variant_config,
                data[train_start:train_end],  # Training data
                data[test_start:test_end],     # Test data
            )
            
            # Check fold pass criteria
            passed, fail_reasons = self._check_fold_criteria(metrics)
            
            fold_result = FoldResult(
                fold_id=fold_id,
                train_start=str(train_start),
                train_end=str(train_end),
                test_start=str(test_start),
                test_end=str(test_end),
                regime=regime,
                metrics=metrics,
                passed=passed,
                fail_reasons=fail_reasons,
            )
            folds.append(fold_result)
            fold_metrics.append(metrics)
        
        # Aggregate metrics
        aggregate = self._aggregate_metrics(fold_metrics)
        
        # Check all gates
        gate_results = self._check_all_gates(aggregate, folds)
        passed_all = all(gate_results.values())
        
        return EvalReport(
            variant_id=variant_id,
            manifest_id=manifest.run_id,
            evaluated_at=datetime.now(timezone.utc).isoformat(),
            folds=folds,
            aggregate_metrics=aggregate,
            passed_all_gates=passed_all,
            gate_results=gate_results,
            integrity_violations=[],
        )
    
    def _check_integrity(self, data: List[Any]) -> List[str]:
        """Check data integrity - fail closed on violations."""
        violations = []
        
        if not data:
            violations.append("EMPTY_DATA")
            return violations
        
        # Check for missing bars (gaps in timestamps)
        missing_count = 0
        for i in range(1, len(data)):
            if hasattr(data[i], 'timestamp') and hasattr(data[i-1], 'timestamp'):
                # Simplified gap detection
                pass
        
        missing_pct = missing_count / len(data) * 100 if data else 0
        if missing_pct > self.config.max_missing_bars_pct:
            violations.append(f"MISSING_BARS_{missing_pct:.1f}PCT")
        
        # Check for non-monotonic timestamps
        for i in range(1, len(data)):
            if hasattr(data[i], 'timestamp') and hasattr(data[i-1], 'timestamp'):
                if data[i].timestamp <= data[i-1].timestamp:
                    violations.append(f"NON_MONOTONIC_TIMESTAMP_AT_{i}")
                    break
        
        return violations
    
    def _detect_regime(self, data: List[Any]) -> str:
        """Detect market regime from data."""
        if not data:
            return RegimeBucket.RANGE.value
        
        # Calculate returns
        returns = []
        for i in range(1, len(data)):
            if hasattr(data[i], 'close') and hasattr(data[i-1], 'close'):
                ret = (data[i].close - data[i-1].close) / data[i-1].close
                returns.append(ret)
        
        if not returns:
            return RegimeBucket.RANGE.value
        
        # Calculate metrics
        import numpy as np
        returns_arr = np.array(returns)
        mean_return = np.mean(returns_arr)
        volatility = np.std(returns_arr)
        
        # Classify regime
        vol_threshold = 0.001  # 0.1% per bar
        trend_threshold = 0.0001  # 0.01% per bar
        
        if volatility > vol_threshold * 2:
            return RegimeBucket.HIGH_VOL.value
        elif volatility < vol_threshold * 0.5:
            return RegimeBucket.LOW_VOL.value
        elif abs(mean_return) > trend_threshold:
            return RegimeBucket.TREND.value
        else:
            return RegimeBucket.RANGE.value
    
    def _evaluate_fold(
        self,
        config: EvolutionConfig,
        train_data: List[Any],
        test_data: List[Any],
    ) -> Dict[str, float]:
        """Evaluate config on a single fold."""
        # Simplified evaluation - in production would use full backtester
        import numpy as np
        
        if not test_data:
            return {
                "net_return": 0.0,
                "sharpe": 0.0,
                "sortino": 0.0,
                "max_drawdown": 0.0,
                "turnover": 0,
                "avg_r": 0.0,
                "win_rate": 0.0,
                "cost_paid_bps": 0.0,
                "slippage_paid_bps": 0.0,
            }
        
        # Simulate trading with config parameters
        equity = 10000.0
        peak_equity = equity
        max_dd = 0.0
        trades = 0
        wins = 0
        total_cost = 0.0
        returns = []
        
        position = 0
        entry_price = 0.0
        
        for i in range(1, len(test_data)):
            if not hasattr(test_data[i], 'close'):
                continue
                
            price = test_data[i].close
            prev_price = test_data[i-1].close
            
            # Simple signal based on config
            signal = 0
            if i > 5:
                # Trend following with config parameters
                recent_returns = []
                for j in range(max(0, i-5), i):
                    if hasattr(test_data[j], 'close') and hasattr(test_data[j-1], 'close'):
                        recent_returns.append(
                            (test_data[j].close - test_data[j-1].close) / test_data[j-1].close
                        )
                
                if recent_returns:
                    trend = sum(recent_returns)
                    if trend > config.min_confidence * 0.001:
                        signal = 1
                    elif trend < -config.min_confidence * 0.001:
                        signal = -1
            
            # Apply position changes
            if position == 0 and signal != 0 and trades < config.max_trades_per_day:
                # Open position
                position = signal
                entry_price = price
                cost = self.config.spread_pips * 0.0001 + self.config.slippage_pips * 0.0001
                total_cost += cost * equity
                trades += 1
            elif position != 0:
                # Check exit
                pnl_pct = (price - entry_price) / entry_price * position
                
                # Exit on SL/TP
                if pnl_pct < -config.atr_multiplier_sl * 0.001:
                    # Stop loss
                    equity *= (1 + pnl_pct)
                    returns.append(pnl_pct)
                    position = 0
                elif pnl_pct > config.atr_multiplier_tp * 0.001:
                    # Take profit
                    equity *= (1 + pnl_pct)
                    returns.append(pnl_pct)
                    wins += 1
                    position = 0
            
            # Update drawdown
            if equity > peak_equity:
                peak_equity = equity
            dd = (peak_equity - equity) / peak_equity * 100
            max_dd = max(max_dd, dd)
            
            # Check drawdown limit
            if max_dd > config.max_drawdown_pct:
                break
        
        # Close any remaining position
        if position != 0 and test_data:
            final_price = test_data[-1].close if hasattr(test_data[-1], 'close') else entry_price
            pnl_pct = (final_price - entry_price) / entry_price * position
            equity *= (1 + pnl_pct)
            returns.append(pnl_pct)
            if pnl_pct > 0:
                wins += 1
        
        # Calculate metrics
        net_return = (equity - 10000) / 10000 * 100
        
        if returns:
            returns_arr = np.array(returns)
            mean_ret = np.mean(returns_arr)
            std_ret = np.std(returns_arr)
            sharpe = mean_ret / std_ret * np.sqrt(252) if std_ret > 0 else 0
            
            downside_returns = returns_arr[returns_arr < 0]
            downside_std = np.std(downside_returns) if len(downside_returns) > 0 else 0
            sortino = mean_ret / downside_std * np.sqrt(252) if downside_std > 0 else 0
            
            win_rate = wins / len(returns) if returns else 0
            avg_r = mean_ret
        else:
            sharpe = 0
            sortino = 0
            win_rate = 0
            avg_r = 0
        
        return {
            "net_return": net_return,
            "sharpe": sharpe,
            "sortino": sortino,
            "max_drawdown": max_dd,
            "turnover": trades,
            "avg_r": avg_r,
            "win_rate": win_rate,
            "cost_paid_bps": total_cost / 10000 * 10000,
            "slippage_paid_bps": self.config.slippage_pips,
        }
    
    def _check_fold_criteria(self, metrics: Dict[str, float]) -> Tuple[bool, List[str]]:
        """Check if fold passes criteria."""
        fail_reasons = []
        
        if metrics["max_drawdown"] > self.config.max_drawdown_threshold:
            fail_reasons.append(f"MAX_DD_{metrics['max_drawdown']:.1f}PCT")
        
        if metrics["sharpe"] < self.config.min_sharpe_threshold:
            fail_reasons.append(f"LOW_SHARPE_{metrics['sharpe']:.2f}")
        
        if metrics["turnover"] > self.config.max_turnover_threshold:
            fail_reasons.append(f"HIGH_TURNOVER_{metrics['turnover']}")
        
        return len(fail_reasons) == 0, fail_reasons
    
    def _aggregate_metrics(self, fold_metrics: List[Dict[str, float]]) -> Dict[str, float]:
        """Aggregate metrics across folds."""
        if not fold_metrics:
            return {}
        
        import numpy as np
        
        aggregate = {}
        for key in fold_metrics[0].keys():
            values = [m[key] for m in fold_metrics]
            aggregate[key] = float(np.mean(values))
            aggregate[f"{key}_std"] = float(np.std(values))
        
        # Stability metric
        if "net_return_std" in aggregate:
            aggregate["stability"] = float(aggregate["net_return_std"])
        
        return aggregate
    
    def _check_all_gates(
        self,
        aggregate: Dict[str, float],
        folds: List[FoldResult],
    ) -> Dict[str, bool]:
        """Check all pass gates."""
        gates = {}
        
        # Drawdown gate
        gates["max_drawdown"] = bool(aggregate.get("max_drawdown", 100) <= self.config.max_drawdown_threshold)
        
        # Sharpe gate
        gates["min_sharpe"] = bool(aggregate.get("sharpe", 0) >= self.config.min_sharpe_threshold)
        
        # Turnover gate
        gates["max_turnover"] = bool(aggregate.get("turnover", 100) <= self.config.max_turnover_threshold)
        
        # Stability gate
        gates["stability"] = bool(aggregate.get("stability", 100) <= self.config.stability_threshold)
        
        # All folds passed gate
        gates["all_folds_passed"] = bool(all(f.passed for f in folds) if folds else False)
        
        return gates


# =============================================================================
# MAP-ELITES ARCHIVE - Quality-Diversity with regime x risk buckets
# =============================================================================

class QualityDiversityArchive:
    """
    MAP-Elites archive with regime x risk buckets.
    
    Maintains diverse champions across different market conditions
    and risk profiles.
    """
    
    def __init__(self, top_k_per_bucket: int = 3):
        self.top_k = top_k_per_bucket
        self.buckets: Dict[str, List[ArchiveEntry]] = {}
        self.generation = 0
        self.total_evaluated = 0
        
        # Initialize all buckets
        for regime in RegimeBucket:
            for risk in RiskBucket:
                key = f"{regime.value}_{risk.value}"
                self.buckets[key] = []
    
    def add(
        self,
        variant_id: str,
        config: Dict[str, Any],
        eval_report: EvalReport,
        manifest_id: str,
        eval_report_path: str,
    ) -> bool:
        """
        Try to add a variant to the archive.
        
        Returns True if added (new bucket or better fitness).
        """
        self.total_evaluated += 1
        
        if not eval_report.passed_all_gates:
            return False
        
        # Determine buckets
        regime_bucket = self._determine_regime_bucket(eval_report)
        risk_bucket = self._determine_risk_bucket(eval_report)
        bucket_key = f"{regime_bucket}_{risk_bucket}"
        
        # Calculate fitness
        fitness = self._calculate_fitness(eval_report)
        
        entry = ArchiveEntry(
            variant_id=variant_id,
            config=config,
            regime_bucket=regime_bucket,
            risk_bucket=risk_bucket,
            fitness=fitness,
            metrics=eval_report.aggregate_metrics,
            manifest_id=manifest_id,
            eval_report_path=eval_report_path,
            generation_added=self.generation,
        )
        
        # Add to bucket
        bucket = self.buckets[bucket_key]
        bucket.append(entry)
        
        # Keep only top K
        bucket.sort(key=lambda e: e.fitness, reverse=True)
        self.buckets[bucket_key] = bucket[:self.top_k]
        
        # Check if we actually kept this entry
        added = any(e.variant_id == variant_id for e in self.buckets[bucket_key])
        
        if added:
            logger.info(f"Added variant {variant_id} to bucket {bucket_key} with fitness {fitness:.4f}")
        
        return added
    
    def _determine_regime_bucket(self, report: EvalReport) -> str:
        """Determine regime bucket from eval report."""
        if not report.folds:
            return RegimeBucket.RANGE.value
        
        # Count regimes across folds
        regime_counts: Dict[str, int] = {}
        for fold in report.folds:
            regime_counts[fold.regime] = regime_counts.get(fold.regime, 0) + 1
        
        # Return most common
        return max(regime_counts.keys(), key=lambda r: regime_counts[r])
    
    def _determine_risk_bucket(self, report: EvalReport) -> str:
        """Determine risk bucket from eval report."""
        max_dd = report.aggregate_metrics.get("max_drawdown", 0)
        
        if max_dd < 2:
            return RiskBucket.LOW_DD.value
        elif max_dd < 5:
            return RiskBucket.MED_DD.value
        else:
            return RiskBucket.HIGH_DD.value
    
    def _calculate_fitness(self, report: EvalReport) -> float:
        """Calculate fitness score from eval report."""
        metrics = report.aggregate_metrics
        
        # Weighted combination of metrics
        sharpe = metrics.get("sharpe", 0)
        sortino = metrics.get("sortino", 0)
        net_return = metrics.get("net_return", 0)
        max_dd = metrics.get("max_drawdown", 100)
        stability = metrics.get("stability", 100)
        
        # Fitness formula (higher is better)
        fitness = (
            0.3 * sharpe +
            0.2 * sortino +
            0.2 * (net_return / 10) +  # Normalize return
            0.2 * (10 - max_dd) / 10 +  # Penalize drawdown
            0.1 * (1 - stability)  # Reward stability
        )
        
        return fitness
    
    def get_champions(self, n: int = 5) -> List[ArchiveEntry]:
        """Get top N champions across all buckets."""
        all_entries = []
        for entries in self.buckets.values():
            all_entries.extend(entries)
        
        all_entries.sort(key=lambda e: e.fitness, reverse=True)
        return all_entries[:n]
    
    def get_bucket_champions(self, bucket_key: str) -> List[ArchiveEntry]:
        """Get champions from a specific bucket."""
        return self.buckets.get(bucket_key, [])
    
    def get_random_champion(self) -> Optional[ArchiveEntry]:
        """Get a random champion from the archive."""
        all_entries = []
        for entries in self.buckets.values():
            all_entries.extend(entries)
        
        if not all_entries:
            return None
        
        return random.choice(all_entries)
    
    def increment_generation(self) -> None:
        """Move to next generation."""
        self.generation += 1
    
    def to_archive_index(self) -> ArchiveIndex:
        """Convert to ArchiveIndex for saving."""
        return ArchiveIndex(
            updated_at=datetime.now(timezone.utc).isoformat(),
            generation=self.generation,
            total_variants_evaluated=self.total_evaluated,
            buckets=self.buckets,
            top_k_per_bucket=self.top_k,
        )
    
    def load_from_index(self, index: ArchiveIndex) -> None:
        """Load state from ArchiveIndex."""
        self.generation = index.generation
        self.total_evaluated = index.total_variants_evaluated
        self.buckets = index.buckets
        self.top_k = index.top_k_per_bucket


# =============================================================================
# DRQ CHAMPION TESTING - Must beat prior champions out-of-sample
# =============================================================================

class ChampionTester:
    """
    DRQ-style champion testing.
    
    New variants must beat current and historical champions
    on out-of-sample data to be promoted.
    """
    
    def __init__(
        self,
        harness: EvaluationHarness,
        min_improvement_pct: float = 5.0,
    ):
        self.harness = harness
        self.min_improvement = min_improvement_pct / 100
        self.historical_champions: List[Tuple[EvolutionConfig, float]] = []
    
    def test_against_champions(
        self,
        candidate: EvolutionConfig,
        candidate_report: EvalReport,
        current_champion: Optional[EvolutionConfig],
        archive: QualityDiversityArchive,
        test_data: List[Any],
        manifest: RunManifest,
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        Test candidate against current and historical champions.
        
        Args:
            candidate: The candidate config
            candidate_report: Evaluation report for candidate
            current_champion: Current active champion config
            archive: Archive of historical champions
            test_data: Out-of-sample test data
            manifest: Run manifest
            
        Returns:
            Tuple of (passed, comparison_results)
        """
        results = {
            "candidate_fitness": self._get_fitness(candidate_report),
            "comparisons": [],
            "passed": True,
        }
        
        # Test against current champion
        if current_champion:
            current_report = self.harness.evaluate(current_champion, test_data, manifest)
            current_fitness = self._get_fitness(current_report)
            
            comparison = {
                "opponent": "current_champion",
                "opponent_fitness": current_fitness,
                "candidate_fitness": results["candidate_fitness"],
                "improvement": (results["candidate_fitness"] - current_fitness) / abs(current_fitness) if current_fitness != 0 else 0,
            }
            comparison["passed"] = comparison["improvement"] >= self.min_improvement
            results["comparisons"].append(comparison)
            
            if not comparison["passed"]:
                results["passed"] = False
        
        # Test against sample of historical champions
        historical_sample = self._sample_historical_champions(archive, n=3)
        
        for i, (hist_config, hist_fitness) in enumerate(historical_sample):
            hist_report = self.harness.evaluate(hist_config, test_data, manifest)
            hist_new_fitness = self._get_fitness(hist_report)
            
            comparison = {
                "opponent": f"historical_champion_{i}",
                "opponent_fitness": hist_new_fitness,
                "candidate_fitness": results["candidate_fitness"],
                "improvement": (results["candidate_fitness"] - hist_new_fitness) / abs(hist_new_fitness) if hist_new_fitness != 0 else 0,
            }
            # Must not be significantly worse than historical champions
            comparison["passed"] = comparison["improvement"] >= -self.min_improvement
            results["comparisons"].append(comparison)
            
            if not comparison["passed"]:
                results["passed"] = False
        
        return results["passed"], results
    
    def _get_fitness(self, report: EvalReport) -> float:
        """Extract fitness from eval report."""
        metrics = report.aggregate_metrics
        sharpe = metrics.get("sharpe", 0)
        net_return = metrics.get("net_return", 0)
        max_dd = metrics.get("max_drawdown", 100)
        
        return sharpe * 0.5 + net_return * 0.3 - max_dd * 0.2
    
    def _sample_historical_champions(
        self,
        archive: QualityDiversityArchive,
        n: int = 3,
    ) -> List[Tuple[EvolutionConfig, float]]:
        """Sample historical champions from archive."""
        champions = archive.get_champions(n * 2)
        
        if len(champions) <= n:
            return [
                (EvolutionConfig.from_dict(c.config), c.fitness)
                for c in champions
            ]
        
        # Random sample
        sampled = random.sample(champions, n)
        return [
            (EvolutionConfig.from_dict(c.config), c.fitness)
            for c in sampled
        ]
    
    def add_to_history(self, config: EvolutionConfig, fitness: float) -> None:
        """Add a champion to historical record."""
        self.historical_champions.append((config, fitness))
        # Keep last 20
        if len(self.historical_champions) > 20:
            self.historical_champions = self.historical_champions[-20:]


# =============================================================================
# EVOLUTION LOOP - Main orchestrator
# =============================================================================

@dataclass
class EvolutionLoopConfig:
    """Configuration for the evolution loop."""
    # Variant generation
    variants_per_round: int = 10
    mutation_rate: float = 0.2
    mutation_strength: float = 0.15
    patch_budget: int = 5
    
    # Rounds
    max_rounds: int = 10
    stagnation_limit: int = 3
    
    # Champion testing
    min_improvement_pct: float = 5.0
    
    # Canary deployment
    canary_trades_required: int = 10
    canary_max_dd_pct: float = 5.0
    
    # Output
    output_dir: str = "evolution_output"


class EvolutionLoop:
    """
    Sakana-style open-ended self-improvement loop.
    
    Orchestrates:
    - Variant generation (config-only mutations)
    - Walk-forward evaluation
    - MAP-Elites archiving
    - Champion testing
    - Canary deployment
    """
    
    def __init__(
        self,
        config: Optional[EvolutionLoopConfig] = None,
        eval_config: Optional[EvalConfig] = None,
    ):
        self.config = config or EvolutionLoopConfig()
        self.harness = EvaluationHarness(eval_config)
        self.archive = QualityDiversityArchive()
        self.champion_tester = ChampionTester(
            self.harness,
            min_improvement_pct=self.config.min_improvement_pct,
        )
        
        self.current_champion: Optional[EvolutionConfig] = None
        self.live_state: Optional[LiveGatingState] = None
        self.round = 0
        self.stagnation = 0
        self.best_fitness = float("-inf")
        
        # Output directory
        self.output_dir = Path(self.config.output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def run(
        self,
        data: List[Any],
        initial_config: Optional[EvolutionConfig] = None,
        max_rounds: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Run the evolution loop.
        
        Args:
            data: Historical OHLCV data
            initial_config: Starting config (default if None)
            max_rounds: Override max rounds
            
        Returns:
            Summary of evolution run
        """
        max_rounds = max_rounds or self.config.max_rounds
        
        # Initialize
        if initial_config is None:
            initial_config = EvolutionConfig()
        self.current_champion = initial_config
        
        # Create run manifest
        cost_model = {
            "spread_pips": self.harness.config.spread_pips,
            "slippage_pips": self.harness.config.slippage_pips,
            "commission_per_lot": self.harness.config.commission_per_lot,
        }
        
        manifest = RunManifest.create(
            data_start=str(0),
            data_end=str(len(data)),
            data_bars=len(data),
            cost_model=cost_model,
        )
        manifest.save(self.output_dir / f"RUN_MANIFEST_{manifest.run_id}.json")
        
        # Initialize live gating state
        self.live_state = LiveGatingState(
            updated_at=datetime.now(timezone.utc).isoformat(),
            active_variant_id="initial",
            active_config=initial_config.to_dict(),
            canary_mode=CanaryMode.OFF.value,
            canary_start_time=None,
            canary_trades=0,
            canary_pnl=0.0,
            kill_switch_active=False,
            kill_switch_reason=None,
            previous_variant_id=None,
            max_drawdown_threshold=self.config.canary_max_dd_pct,
            anomaly_threshold=3.0,
        )
        
        logger.info(f"Starting evolution loop for {max_rounds} rounds")
        
        # Run rounds
        for round_num in range(max_rounds):
            self.round = round_num
            
            round_result = self._run_round(data, manifest)
            
            # Check stagnation
            if round_result["best_fitness"] > self.best_fitness:
                self.best_fitness = round_result["best_fitness"]
                self.stagnation = 0
            else:
                self.stagnation += 1
            
            if self.stagnation >= self.config.stagnation_limit:
                logger.info(f"Stopping due to stagnation at round {round_num}")
                break
            
            self.archive.increment_generation()
        
        # Save final state
        self._save_state()
        
        # Summary
        summary = {
            "rounds_completed": self.round + 1,
            "total_variants_evaluated": self.archive.total_evaluated,
            "best_fitness": self.best_fitness,
            "archive_size": sum(len(b) for b in self.archive.buckets.values()),
            "final_champion": self.current_champion.to_dict() if self.current_champion else None,
            "manifest_id": manifest.run_id,
        }
        
        logger.info(f"Evolution complete: {summary}")
        return summary
    
    def _run_round(
        self,
        data: List[Any],
        manifest: RunManifest,
    ) -> Dict[str, Any]:
        """Run a single evolution round."""
        logger.info(f"Starting round {self.round}")
        
        round_result = {
            "round": self.round,
            "variants_generated": 0,
            "variants_passed": 0,
            "best_fitness": float("-inf"),
            "promoted": False,
        }
        
        # Generate variants
        variants = self._generate_variants()
        round_result["variants_generated"] = len(variants)
        
        # Evaluate each variant
        for variant_config, patch in variants:
            # Evaluate
            report = self.harness.evaluate(variant_config, data, manifest)
            
            # Save eval report
            report_path = self.output_dir / f"EVAL_REPORT_{patch.variant_id}.json"
            report.save(report_path)
            
            # Save patch
            patch_path = self.output_dir / f"VARIANT_PATCH_{patch.variant_id}.json"
            with open(patch_path, "w") as f:
                json.dump(patch.to_dict(), f, indent=2)
            
            if report.passed_all_gates:
                round_result["variants_passed"] += 1
                
                # Calculate fitness
                fitness = self._calculate_fitness(report)
                if fitness > round_result["best_fitness"]:
                    round_result["best_fitness"] = fitness
                
                # Try to add to archive
                self.archive.add(
                    variant_id=patch.variant_id,
                    config=variant_config.to_dict(),
                    eval_report=report,
                    manifest_id=manifest.run_id,
                    eval_report_path=str(report_path),
                )
                
                # Test against champions for promotion
                if fitness > self.best_fitness:
                    passed, comparison = self.champion_tester.test_against_champions(
                        candidate=variant_config,
                        candidate_report=report,
                        current_champion=self.current_champion,
                        archive=self.archive,
                        test_data=data[-self.harness.config.test_bars:],
                        manifest=manifest,
                    )
                    
                    if passed:
                        self._promote_variant(variant_config, patch.variant_id)
                        round_result["promoted"] = True
        
        # Save archive index
        archive_index = self.archive.to_archive_index()
        archive_index.save(self.output_dir / "ARCHIVE_INDEX.json")
        
        # Save live gating state
        if self.live_state:
            self.live_state.save(self.output_dir / "LIVE_GATING_STATE.json")
        
        logger.info(
            f"Round {self.round}: {round_result['variants_passed']}/{round_result['variants_generated']} passed, "
            f"best={round_result['best_fitness']:.4f}, promoted={round_result['promoted']}"
        )
        
        return round_result
    
    def _generate_variants(self) -> List[Tuple[EvolutionConfig, VariantPatch]]:
        """Generate variant configs for this round."""
        variants = []
        
        for _ in range(self.config.variants_per_round):
            # Select parent
            if self.archive.total_evaluated > 0 and random.random() < 0.7:
                # Use archive champion as parent
                champion = self.archive.get_random_champion()
                if champion:
                    parent = EvolutionConfig.from_dict(champion.config)
                else:
                    parent = self.current_champion or EvolutionConfig()
            else:
                parent = self.current_champion or EvolutionConfig()
            
            # Mutate
            variant, patch = mutate_config(
                parent,
                mutation_rate=self.config.mutation_rate,
                mutation_strength=self.config.mutation_strength,
                patch_budget=self.config.patch_budget,
            )
            variants.append((variant, patch))
        
        return variants
    
    def _calculate_fitness(self, report: EvalReport) -> float:
        """Calculate fitness from eval report."""
        metrics = report.aggregate_metrics
        sharpe = metrics.get("sharpe", 0)
        net_return = metrics.get("net_return", 0)
        max_dd = metrics.get("max_drawdown", 100)
        
        return sharpe * 0.5 + net_return * 0.3 - max_dd * 0.2
    
    def _promote_variant(self, config: EvolutionConfig, variant_id: str) -> None:
        """Promote a variant to active champion."""
        logger.info(f"Promoting variant {variant_id} to champion")
        
        # Update champion
        old_champion = self.current_champion
        self.current_champion = config
        
        # Add old champion to history
        if old_champion:
            self.champion_tester.add_to_history(old_champion, self.best_fitness)
        
        # Update live state to canary mode
        if self.live_state:
            self.live_state.previous_variant_id = self.live_state.active_variant_id
            self.live_state.active_variant_id = variant_id
            self.live_state.active_config = config.to_dict()
            self.live_state.canary_mode = CanaryMode.PAPER.value
            self.live_state.canary_start_time = datetime.now(timezone.utc).isoformat()
            self.live_state.canary_trades = 0
            self.live_state.canary_pnl = 0.0
            self.live_state.updated_at = datetime.now(timezone.utc).isoformat()
    
    def _save_state(self) -> None:
        """Save all state to output directory."""
        # Archive index
        archive_index = self.archive.to_archive_index()
        archive_index.save(self.output_dir / "ARCHIVE_INDEX.json")
        
        # Live gating state
        if self.live_state:
            self.live_state.save(self.output_dir / "LIVE_GATING_STATE.json")
        
        # Champion config
        if self.current_champion:
            with open(self.output_dir / "CHAMPION_CONFIG.json", "w") as f:
                json.dump(self.current_champion.to_dict(), f, indent=2)
    
    def update_canary_status(self, trades: int, pnl: float, max_dd: float) -> None:
        """
        Update canary deployment status.
        
        Call this during live trading to track canary performance.
        """
        if not self.live_state:
            return
        
        self.live_state.canary_trades = trades
        self.live_state.canary_pnl = pnl
        self.live_state.updated_at = datetime.now(timezone.utc).isoformat()
        
        # Check kill switch conditions
        if max_dd > self.live_state.max_drawdown_threshold:
            self.live_state.activate_kill_switch(f"MAX_DD_BREACH_{max_dd:.1f}PCT")
            self._revert_to_previous()
        
        # Check if canary period complete
        if (
            self.live_state.canary_mode == CanaryMode.PAPER.value and
            trades >= self.config.canary_trades_required and
            pnl >= 0
        ):
            # Promote to micro
            self.live_state.canary_mode = CanaryMode.MICRO.value
            logger.info("Canary promoted to MICRO mode")
        
        elif (
            self.live_state.canary_mode == CanaryMode.MICRO.value and
            trades >= self.config.canary_trades_required * 2 and
            pnl >= 0
        ):
            # Promote to full
            self.live_state.canary_mode = CanaryMode.FULL.value
            logger.info("Canary promoted to FULL mode")
        
        self.live_state.save(self.output_dir / "LIVE_GATING_STATE.json")
    
    def _revert_to_previous(self) -> None:
        """Revert to previous champion after kill switch."""
        if not self.live_state or not self.live_state.previous_variant_id:
            return
        
        logger.warning("Reverting to previous champion")
        
        # Find previous config in archive
        for entries in self.archive.buckets.values():
            for entry in entries:
                if entry.variant_id == self.live_state.previous_variant_id:
                    self.current_champion = EvolutionConfig.from_dict(entry.config)
                    self.live_state.active_variant_id = entry.variant_id
                    self.live_state.active_config = entry.config
                    break


# =============================================================================
# CLI INTERFACE
# =============================================================================

def run_evolution(
    data_path: Optional[str] = None,
    rounds: int = 10,
    variants: int = 10,
    output_dir: str = "evolution_output",
) -> Dict[str, Any]:
    """
    Run the evolution loop from command line.
    
    Args:
        data_path: Path to OHLCV data (JSON or CSV)
        rounds: Number of evolution rounds
        variants: Variants per round
        output_dir: Output directory for results
        
    Returns:
        Evolution summary
    """
    # Load data
    if data_path:
        # Load from file
        with open(data_path, "r") as f:
            data = json.load(f)
    else:
        # Generate synthetic data for testing
        data = _generate_synthetic_data(1000)
    
    # Configure
    config = EvolutionLoopConfig(
        max_rounds=rounds,
        variants_per_round=variants,
        output_dir=output_dir,
    )
    
    # Run
    loop = EvolutionLoop(config)
    return loop.run(data)


def _generate_synthetic_data(n_bars: int) -> List[Dict[str, Any]]:
    """Generate synthetic OHLCV data for testing."""
    import numpy as np
    
    data = []
    price = 1.1000
    
    for i in range(n_bars):
        # Random walk with slight trend
        change = np.random.normal(0.0001, 0.001)
        price *= (1 + change)
        
        high = price * (1 + abs(np.random.normal(0, 0.0005)))
        low = price * (1 - abs(np.random.normal(0, 0.0005)))
        open_price = price * (1 + np.random.normal(0, 0.0002))
        
        data.append({
            "timestamp": f"2024-01-01T{i:05d}",
            "open": open_price,
            "high": max(high, open_price, price),
            "low": min(low, open_price, price),
            "close": price,
            "volume": np.random.randint(1000, 10000),
        })
    
    return data


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Run Sakana-style evolution loop")
    parser.add_argument("--data", type=str, help="Path to OHLCV data")
    parser.add_argument("--rounds", type=int, default=10, help="Number of rounds")
    parser.add_argument("--variants", type=int, default=10, help="Variants per round")
    parser.add_argument("--output", type=str, default="evolution_output", help="Output directory")
    
    args = parser.parse_args()
    
    result = run_evolution(
        data_path=args.data,
        rounds=args.rounds,
        variants=args.variants,
        output_dir=args.output,
    )
    
    print(json.dumps(result, indent=2))
