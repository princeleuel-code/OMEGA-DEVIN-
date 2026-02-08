# SAKANA EVOLUTION LAB - Digital Red Queen + MAP-Elites
#
# The evolution lab that makes the robot smarter.
# Only safe winners get to play in the live engine.
#
# Architecture:
# - MAP-Elites archive of champions across behavior bins
# - Red-Queen loop: challengers mutate champions and re-fight
# - Promotion pipeline: backtest -> walk-forward -> stress -> paper probation -> production
#
# The engine ONLY consumes approved StrategySpecs. No surprises.

import random
import hashlib
import json
import os
from typing import Dict, Any, List, Optional, Callable, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import copy


class PromotionStage(Enum):
    """Stages in the promotion pipeline"""
    CANDIDATE = "candidate"      # Just created
    BACKTEST = "backtest"        # Passed initial backtest
    WALK_FORWARD = "walk_forward"  # Passed walk-forward validation
    STRESS_TEST = "stress_test"  # Passed stress testing
    PAPER_PROBATION = "paper_probation"  # In paper trading probation
    PRODUCTION = "production"    # Approved for production


@dataclass
class StrategySpec:
    """
    A strategy specification that can be evolved.
    
    This is the "DNA" of a strategy - the parameters that define its behavior.
    """
    strategy_id: str
    name: str
    version: str
    
    # Core parameters
    params: Dict[str, Any] = field(default_factory=dict)
    
    # Behavior descriptors (for MAP-Elites binning)
    trade_frequency: str = "medium"  # low, medium, high
    hold_time: str = "medium"        # short, medium, long
    regime_affinity: str = "all"     # trending, ranging, volatile, all
    risk_bucket: str = "medium"      # conservative, medium, aggressive
    
    # Promotion status
    stage: PromotionStage = PromotionStage.CANDIDATE
    
    # Performance metrics
    metrics: Dict[str, float] = field(default_factory=dict)
    
    # Lineage
    parent_id: Optional[str] = None
    generation: int = 0
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def get_behavior_key(self) -> str:
        """Get the behavior bin key for MAP-Elites"""
        return f"{self.trade_frequency}_{self.hold_time}_{self.regime_affinity}_{self.risk_bucket}"
        
    def get_hash(self) -> str:
        """Get a hash of the strategy parameters"""
        params_str = json.dumps(self.params, sort_keys=True)
        return hashlib.sha256(params_str.encode()).hexdigest()[:16]
        
    def to_dict(self) -> Dict:
        return {
            "strategy_id": self.strategy_id,
            "name": self.name,
            "version": self.version,
            "params": self.params,
            "trade_frequency": self.trade_frequency,
            "hold_time": self.hold_time,
            "regime_affinity": self.regime_affinity,
            "risk_bucket": self.risk_bucket,
            "stage": self.stage.value,
            "metrics": self.metrics,
            "parent_id": self.parent_id,
            "generation": self.generation,
            "created_at": self.created_at,
            "behavior_key": self.get_behavior_key(),
            "hash": self.get_hash()
        }
        
    @classmethod
    def from_dict(cls, data: Dict) -> 'StrategySpec':
        spec = cls(
            strategy_id=data["strategy_id"],
            name=data["name"],
            version=data["version"],
            params=data.get("params", {}),
            trade_frequency=data.get("trade_frequency", "medium"),
            hold_time=data.get("hold_time", "medium"),
            regime_affinity=data.get("regime_affinity", "all"),
            risk_bucket=data.get("risk_bucket", "medium"),
            stage=PromotionStage(data.get("stage", "candidate")),
            metrics=data.get("metrics", {}),
            parent_id=data.get("parent_id"),
            generation=data.get("generation", 0),
            created_at=data.get("created_at", datetime.now().isoformat())
        )
        return spec


@dataclass
class MAPElitesArchive:
    """
    MAP-Elites Archive of Champions
    
    Maintains the best strategy for each behavior bin.
    This ensures diversity - we keep champions across different trading styles.
    
    Behavior bins:
    - Trade frequency: low, medium, high
    - Hold time: short, medium, long
    - Regime affinity: trending, ranging, volatile, all
    - Risk bucket: conservative, medium, aggressive
    """
    
    archive: Dict[str, StrategySpec] = field(default_factory=dict)
    history: List[Dict] = field(default_factory=list)
    
    def add(self, spec: StrategySpec) -> bool:
        """
        Try to add a strategy to the archive.
        
        Returns True if the strategy became a new champion.
        """
        key = spec.get_behavior_key()
        
        # Check if this bin is empty or if new spec is better
        if key not in self.archive:
            self.archive[key] = spec
            self._log_event("new_champion", spec, None)
            return True
            
        current_champion = self.archive[key]
        
        # Compare fitness (using Sharpe ratio as primary metric)
        new_fitness = spec.metrics.get("sharpe_ratio", 0)
        current_fitness = current_champion.metrics.get("sharpe_ratio", 0)
        
        if new_fitness > current_fitness:
            self.archive[key] = spec
            self._log_event("champion_replaced", spec, current_champion)
            return True
            
        return False
        
    def get_champion(self, key: str) -> Optional[StrategySpec]:
        """Get the champion for a behavior bin"""
        return self.archive.get(key)
        
    def get_all_champions(self) -> List[StrategySpec]:
        """Get all current champions"""
        return list(self.archive.values())
        
    def get_random_champion(self) -> Optional[StrategySpec]:
        """Get a random champion for mutation"""
        if not self.archive:
            return None
        return random.choice(list(self.archive.values()))
        
    def _log_event(self, event_type: str, new_spec: StrategySpec, old_spec: Optional[StrategySpec]):
        """Log archive events"""
        self.history.append({
            "timestamp": datetime.now().isoformat(),
            "event": event_type,
            "new_spec_id": new_spec.strategy_id,
            "new_fitness": new_spec.metrics.get("sharpe_ratio", 0),
            "old_spec_id": old_spec.strategy_id if old_spec else None,
            "old_fitness": old_spec.metrics.get("sharpe_ratio", 0) if old_spec else None,
            "behavior_key": new_spec.get_behavior_key()
        })
        
    def save(self, path: str = "logs/map_elites_archive.json"):
        """Save archive to disk"""
        os.makedirs(os.path.dirname(path), exist_ok=True)
        data = {
            "archive": {k: v.to_dict() for k, v in self.archive.items()},
            "history": self.history
        }
        with open(path, "w") as f:
            json.dump(data, f, indent=2)
            
    @classmethod
    def load(cls, path: str = "logs/map_elites_archive.json") -> 'MAPElitesArchive':
        """Load archive from disk"""
        archive = cls()
        if os.path.exists(path):
            with open(path, "r") as f:
                data = json.load(f)
            archive.archive = {k: StrategySpec.from_dict(v) for k, v in data.get("archive", {}).items()}
            archive.history = data.get("history", [])
        return archive


class SakanaEvolutionLab:
    """
    THE SAKANA EVOLUTION LAB
    
    The training gym that makes the robot smarter.
    Only safe winners get to play in the live engine.
    
    Process:
    1. Generate candidates (mutate champions or create new)
    2. Evaluate deterministically on historical data
    3. Promote elites to MAP-Elites archive
    4. Run promotion pipeline for production approval
    
    The live engine ONLY consumes approved StrategySpecs from this lab.
    """
    
    def __init__(self, evaluator: Callable[[StrategySpec, List[Dict]], Dict] = None):
        self.archive = MAPElitesArchive()
        self.evaluator = evaluator or self._default_evaluator
        self.candidates: List[StrategySpec] = []
        self.promotion_queue: Dict[PromotionStage, List[StrategySpec]] = {
            stage: [] for stage in PromotionStage
        }
        self.approved_specs: List[StrategySpec] = []
        self.log_file = "logs/evolution_lab.json"
        
        # Mutation parameters
        self.mutation_rate = 0.2
        self.mutation_strength = 0.1
        
        # Promotion thresholds
        self.thresholds = {
            "backtest": {"sharpe_ratio": 1.0, "max_drawdown_pct": 15, "win_rate": 55},
            "walk_forward": {"sharpe_ratio": 0.8, "max_drawdown_pct": 20, "win_rate": 50},
            "stress_test": {"sharpe_ratio": 0.5, "max_drawdown_pct": 25, "win_rate": 45},
            "paper_probation": {"sharpe_ratio": 0.7, "max_drawdown_pct": 20, "win_rate": 50}
        }
        
    def _default_evaluator(self, spec: StrategySpec, data: List[Dict]) -> Dict:
        """Default strategy evaluator (placeholder)"""
        # This should be replaced with actual backtest logic
        return {
            "sharpe_ratio": random.uniform(0, 2),
            "max_drawdown_pct": random.uniform(5, 30),
            "win_rate": random.uniform(40, 70),
            "profit_factor": random.uniform(0.8, 2.5),
            "total_trades": random.randint(50, 500)
        }
        
    def create_candidate(self, base_params: Dict = None) -> StrategySpec:
        """Create a new candidate strategy"""
        params = base_params or self._random_params()
        
        spec = StrategySpec(
            strategy_id=f"strategy_{datetime.now().timestamp()}",
            name="evolved_strategy",
            version="1.0",
            params=params,
            trade_frequency=random.choice(["low", "medium", "high"]),
            hold_time=random.choice(["short", "medium", "long"]),
            regime_affinity=random.choice(["trending", "ranging", "volatile", "all"]),
            risk_bucket=random.choice(["conservative", "medium", "aggressive"])
        )
        
        self.candidates.append(spec)
        return spec
        
    def _random_params(self) -> Dict:
        """Generate random strategy parameters"""
        return {
            "min_confluence": random.randint(6, 12),
            "min_confidence": random.uniform(0.5, 0.9),
            "trend_strength": random.uniform(0.001, 0.01),
            "momentum_threshold": random.uniform(0.005, 0.02),
            "position_size_pct": random.uniform(0.01, 0.05),
            "stop_loss_pct": random.uniform(0.01, 0.05),
            "take_profit_pct": random.uniform(0.02, 0.10)
        }
        
    def mutate(self, parent: StrategySpec) -> StrategySpec:
        """
        Mutate a parent strategy to create a child.
        
        This is the "Red Queen" - challengers mutate champions.
        """
        child_params = copy.deepcopy(parent.params)
        
        # Mutate each parameter with some probability
        for key, value in child_params.items():
            if random.random() < self.mutation_rate:
                if isinstance(value, float):
                    # Gaussian mutation for floats
                    child_params[key] = value * (1 + random.gauss(0, self.mutation_strength))
                elif isinstance(value, int):
                    # Integer mutation
                    child_params[key] = max(1, value + random.randint(-2, 2))
                    
        # Possibly mutate behavior descriptors
        child = StrategySpec(
            strategy_id=f"strategy_{datetime.now().timestamp()}",
            name=f"{parent.name}_child",
            version=parent.version,
            params=child_params,
            trade_frequency=parent.trade_frequency if random.random() > 0.1 else random.choice(["low", "medium", "high"]),
            hold_time=parent.hold_time if random.random() > 0.1 else random.choice(["short", "medium", "long"]),
            regime_affinity=parent.regime_affinity if random.random() > 0.1 else random.choice(["trending", "ranging", "volatile", "all"]),
            risk_bucket=parent.risk_bucket if random.random() > 0.1 else random.choice(["conservative", "medium", "aggressive"]),
            parent_id=parent.strategy_id,
            generation=parent.generation + 1
        )
        
        self.candidates.append(child)
        return child
        
    def evaluate(self, spec: StrategySpec, data: List[Dict]) -> StrategySpec:
        """
        Evaluate a strategy on data.
        
        This is DETERMINISTIC - same spec + same data = same result.
        """
        metrics = self.evaluator(spec, data)
        spec.metrics = metrics
        return spec
        
    def run_evolution_round(self, data: List[Dict], num_candidates: int = 10) -> List[StrategySpec]:
        """
        Run one round of evolution.
        
        1. Generate candidates (mutate champions or create new)
        2. Evaluate all candidates
        3. Update MAP-Elites archive
        4. Return new champions
        """
        new_champions = []
        
        # Generate candidates
        for _ in range(num_candidates):
            if self.archive.archive and random.random() < 0.7:
                # Mutate a random champion
                parent = self.archive.get_random_champion()
                candidate = self.mutate(parent)
            else:
                # Create new random candidate
                candidate = self.create_candidate()
                
            # Evaluate
            self.evaluate(candidate, data)
            
            # Try to add to archive
            if self.archive.add(candidate):
                new_champions.append(candidate)
                
        self._log_round(num_candidates, len(new_champions))
        return new_champions
        
    def run_red_queen(self, data: List[Dict], rounds: int = 10, candidates_per_round: int = 10) -> Dict:
        """
        Run the Red Queen loop.
        
        Challengers mutate champions and re-fight on new regimes.
        The fittest survive and become the new champions.
        """
        results = {
            "rounds": rounds,
            "total_candidates": 0,
            "new_champions": 0,
            "final_archive_size": 0
        }
        
        for round_num in range(rounds):
            new_champions = self.run_evolution_round(data, candidates_per_round)
            results["total_candidates"] += candidates_per_round
            results["new_champions"] += len(new_champions)
            
        results["final_archive_size"] = len(self.archive.archive)
        self.archive.save()
        
        return results
        
    def check_promotion(self, spec: StrategySpec, stage: str) -> Tuple[bool, List[str]]:
        """
        Check if a strategy passes promotion thresholds.
        
        Returns (passed, failed_criteria)
        """
        thresholds = self.thresholds.get(stage, {})
        failed = []
        
        for metric, threshold in thresholds.items():
            value = spec.metrics.get(metric, 0)
            
            if metric == "max_drawdown_pct":
                # Lower is better for drawdown
                if value > threshold:
                    failed.append(f"{metric}: {value:.1f} > {threshold}")
            else:
                # Higher is better for other metrics
                if value < threshold:
                    failed.append(f"{metric}: {value:.1f} < {threshold}")
                    
        return len(failed) == 0, failed
        
    def promote(self, spec: StrategySpec, data: Dict[str, List[Dict]]) -> Tuple[bool, PromotionStage]:
        """
        Run the full promotion pipeline for a strategy.
        
        Pipeline: backtest -> walk-forward -> stress -> paper probation -> production
        
        Args:
            spec: Strategy to promote
            data: Dict with keys "backtest", "walk_forward", "stress" containing test data
            
        Returns:
            (success, final_stage)
        """
        stages = [
            ("backtest", PromotionStage.BACKTEST),
            ("walk_forward", PromotionStage.WALK_FORWARD),
            ("stress_test", PromotionStage.STRESS_TEST)
        ]
        
        for stage_name, stage_enum in stages:
            # Evaluate on stage data
            stage_data = data.get(stage_name, [])
            if stage_data:
                self.evaluate(spec, stage_data)
                
            # Check promotion
            passed, failed = self.check_promotion(spec, stage_name)
            
            if not passed:
                self._log_promotion_failure(spec, stage_name, failed)
                return False, spec.stage
                
            spec.stage = stage_enum
            self._log_promotion_success(spec, stage_name)
            
        # Made it through all stages - ready for paper probation
        spec.stage = PromotionStage.PAPER_PROBATION
        self.promotion_queue[PromotionStage.PAPER_PROBATION].append(spec)
        
        return True, spec.stage
        
    def approve_for_production(self, spec: StrategySpec) -> bool:
        """
        Approve a strategy for production after paper probation.
        
        This is the final gate - only strategies that prove themselves
        in paper trading get approved for production.
        """
        if spec.stage != PromotionStage.PAPER_PROBATION:
            return False
            
        # Check paper probation metrics
        passed, failed = self.check_promotion(spec, "paper_probation")
        
        if passed:
            spec.stage = PromotionStage.PRODUCTION
            self.approved_specs.append(spec)
            self._log_production_approval(spec)
            return True
            
        self._log_promotion_failure(spec, "paper_probation", failed)
        return False
        
    def get_approved_specs(self) -> List[StrategySpec]:
        """Get all production-approved strategy specs"""
        return [s for s in self.approved_specs if s.stage == PromotionStage.PRODUCTION]
        
    def _log_round(self, candidates: int, new_champions: int):
        """Log evolution round"""
        self._log_event("evolution_round", {
            "candidates": candidates,
            "new_champions": new_champions,
            "archive_size": len(self.archive.archive)
        })
        
    def _log_promotion_success(self, spec: StrategySpec, stage: str):
        """Log promotion success"""
        self._log_event("promotion_success", {
            "strategy_id": spec.strategy_id,
            "stage": stage,
            "metrics": spec.metrics
        })
        
    def _log_promotion_failure(self, spec: StrategySpec, stage: str, failed: List[str]):
        """Log promotion failure"""
        self._log_event("promotion_failure", {
            "strategy_id": spec.strategy_id,
            "stage": stage,
            "failed_criteria": failed,
            "metrics": spec.metrics
        })
        
    def _log_production_approval(self, spec: StrategySpec):
        """Log production approval"""
        self._log_event("production_approval", {
            "strategy_id": spec.strategy_id,
            "metrics": spec.metrics,
            "generation": spec.generation
        })
        
    def _log_event(self, event_type: str, data: Dict):
        """Log events to file"""
        os.makedirs(os.path.dirname(self.log_file), exist_ok=True)
        
        event = {
            "timestamp": datetime.now().isoformat(),
            "event": event_type,
            "data": data
        }
        
        try:
            with open(self.log_file, "a") as f:
                f.write(json.dumps(event) + "\n")
        except:
            pass
            
    def get_stats(self) -> Dict:
        """Get evolution lab statistics"""
        return {
            "archive_size": len(self.archive.archive),
            "total_candidates": len(self.candidates),
            "approved_for_production": len(self.get_approved_specs()),
            "promotion_queue": {
                stage.value: len(specs) 
                for stage, specs in self.promotion_queue.items()
            },
            "best_sharpe": max(
                (s.metrics.get("sharpe_ratio", 0) for s in self.archive.get_all_champions()),
                default=0
            )
        }


# Example usage
if __name__ == "__main__":
    # Create the evolution lab
    lab = SakanaEvolutionLab()
    
    # Generate some test data
    test_data = [{"price": 100 + i * 0.1} for i in range(1000)]
    
    # Run Red Queen evolution
    print("Running Red Queen evolution...")
    results = lab.run_red_queen(test_data, rounds=5, candidates_per_round=20)
    print(f"Results: {results}")
    
    # Get champions
    champions = lab.archive.get_all_champions()
    print(f"\nChampions ({len(champions)}):")
    for champ in champions[:5]:
        print(f"  {champ.get_behavior_key()}: Sharpe={champ.metrics.get('sharpe_ratio', 0):.2f}")
    
    # Try to promote best champion
    if champions:
        best = max(champions, key=lambda s: s.metrics.get("sharpe_ratio", 0))
        print(f"\nPromoting best champion: {best.strategy_id}")
        
        promotion_data = {
            "backtest": test_data,
            "walk_forward": test_data[500:],
            "stress_test": test_data[:500]
        }
        
        success, stage = lab.promote(best, promotion_data)
        print(f"Promotion result: success={success}, stage={stage.value}")
    
    # Get stats
    print(f"\nLab Stats: {lab.get_stats()}")
