"""
INTELLIGENCE EVOLUTION ENGINE - Full-Stack DRQ Evolution

This module implements the complete DRQ-style evolution engine that
evolves the ENTIRE intelligence stack, not just trading parameters.

Key Features:
1. Full-stack parameter evolution (Delta Print, VPIN, HMM, Consciousness, Fundamental)
2. Sophisticated adversarial market scenarios
3. Multi-objective fitness evaluation
4. MAP-Elites diversity maintenance
5. Meta-evolution of evolution parameters

This is the key to QUADRUPLING our intelligence through automated self-improvement.

Author: Devin (for Prince)
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Callable, Tuple
from pathlib import Path
import logging
import random
import json
import math
from datetime import datetime

from .intelligence_genome import (
    IntelligenceGenome,
    IntelligenceGenomeConfig,
    create_random_intelligence_genome,
    create_default_intelligence_genome,
    mutate_intelligence_genome,
    crossover_intelligence_genomes,
    blend_intelligence_genomes,
)
from .behaviors import BehaviorDescriptor, compute_behavior
from .map_elites import MAPElitesArchive, ArchiveEntry


logger = logging.getLogger(__name__)


@dataclass
class AdversarialScenario:
    """
    Sophisticated adversarial market scenario.
    
    These scenarios represent challenging market conditions that
    strategies must survive to prove robustness.
    """
    name: str
    description: str
    
    # Market regime
    regime: str  # "trending_up", "trending_down", "ranging", "volatile", "crisis"
    
    # Price dynamics
    trend_strength: float = 0.0  # -1 to 1
    volatility_base: float = 0.0002
    volatility_spikes: bool = False
    spike_probability: float = 0.0
    spike_magnitude: float = 3.0
    
    # Microstructure
    spread_multiplier: float = 1.0
    gap_probability: float = 0.0
    gap_magnitude: float = 0.01
    
    # Liquidity
    liquidity_factor: float = 1.0  # 1 = normal, <1 = thin, >1 = deep
    
    # Duration and weight
    duration_bars: int = 500
    weight: float = 1.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "regime": self.regime,
            "trend_strength": self.trend_strength,
            "volatility_base": self.volatility_base,
            "volatility_spikes": self.volatility_spikes,
            "spike_probability": self.spike_probability,
            "spike_magnitude": self.spike_magnitude,
            "spread_multiplier": self.spread_multiplier,
            "gap_probability": self.gap_probability,
            "gap_magnitude": self.gap_magnitude,
            "liquidity_factor": self.liquidity_factor,
            "duration_bars": self.duration_bars,
            "weight": self.weight,
        }


# Comprehensive adversarial scenarios
ADVERSARIAL_SCENARIOS = [
    # Normal market conditions
    AdversarialScenario(
        name="normal_trending_up",
        description="Normal uptrend with moderate volatility",
        regime="trending_up",
        trend_strength=0.3,
        volatility_base=0.0002,
        weight=1.0,
    ),
    AdversarialScenario(
        name="normal_trending_down",
        description="Normal downtrend with moderate volatility",
        regime="trending_down",
        trend_strength=-0.3,
        volatility_base=0.0002,
        weight=1.0,
    ),
    AdversarialScenario(
        name="normal_ranging",
        description="Sideways market with low volatility",
        regime="ranging",
        trend_strength=0.0,
        volatility_base=0.00015,
        weight=1.0,
    ),
    
    # Challenging conditions
    AdversarialScenario(
        name="high_volatility",
        description="High volatility market with frequent spikes",
        regime="volatile",
        trend_strength=0.0,
        volatility_base=0.0004,
        volatility_spikes=True,
        spike_probability=0.05,
        spike_magnitude=2.5,
        weight=1.5,
    ),
    AdversarialScenario(
        name="choppy_market",
        description="Choppy market with false breakouts",
        regime="ranging",
        trend_strength=0.0,
        volatility_base=0.0003,
        weight=1.5,
    ),
    AdversarialScenario(
        name="wide_spreads",
        description="Market with wide spreads (illiquid)",
        regime="ranging",
        spread_multiplier=2.5,
        liquidity_factor=0.5,
        weight=1.5,
    ),
    
    # Stress scenarios
    AdversarialScenario(
        name="flash_crash",
        description="Sudden market crash with gaps",
        regime="crisis",
        trend_strength=-0.8,
        volatility_base=0.001,
        volatility_spikes=True,
        spike_probability=0.2,
        spike_magnitude=5.0,
        gap_probability=0.1,
        gap_magnitude=0.02,
        liquidity_factor=0.3,
        weight=2.0,
    ),
    AdversarialScenario(
        name="trend_reversal",
        description="Strong trend that suddenly reverses",
        regime="volatile",
        trend_strength=0.5,  # Will be reversed mid-scenario
        volatility_base=0.0003,
        weight=2.0,
    ),
    AdversarialScenario(
        name="liquidity_crisis",
        description="Severe liquidity crisis with gaps",
        regime="crisis",
        volatility_base=0.0005,
        spread_multiplier=4.0,
        gap_probability=0.15,
        gap_magnitude=0.03,
        liquidity_factor=0.2,
        weight=2.0,
    ),
    AdversarialScenario(
        name="news_event",
        description="Major news event with instant volatility spike",
        regime="volatile",
        volatility_base=0.0002,
        volatility_spikes=True,
        spike_probability=0.3,
        spike_magnitude=4.0,
        gap_probability=0.2,
        gap_magnitude=0.015,
        weight=1.5,
    ),
    
    # Extended scenarios
    AdversarialScenario(
        name="extended_drawdown",
        description="Long period of adverse conditions",
        regime="trending_down",
        trend_strength=-0.2,
        volatility_base=0.00025,
        duration_bars=1000,
        weight=1.5,
    ),
    AdversarialScenario(
        name="whipsaw",
        description="Rapid direction changes (whipsaw)",
        regime="volatile",
        trend_strength=0.0,
        volatility_base=0.0004,
        weight=2.0,
    ),
]


@dataclass
class FitnessMetrics:
    """Multi-objective fitness metrics"""
    sharpe_ratio: float = 0.0
    sortino_ratio: float = 0.0
    max_drawdown_pct: float = 0.0
    win_rate: float = 0.0
    profit_factor: float = 0.0
    total_return_pct: float = 0.0
    avg_trade_pnl: float = 0.0
    total_trades: int = 0
    
    # Risk-adjusted metrics
    calmar_ratio: float = 0.0  # Return / Max Drawdown
    recovery_factor: float = 0.0  # Total Return / Max Drawdown
    
    # Consistency metrics
    win_streak_max: int = 0
    loss_streak_max: int = 0
    monthly_consistency: float = 0.0  # % of profitable months
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "sharpe_ratio": self.sharpe_ratio,
            "sortino_ratio": self.sortino_ratio,
            "max_drawdown_pct": self.max_drawdown_pct,
            "win_rate": self.win_rate,
            "profit_factor": self.profit_factor,
            "total_return_pct": self.total_return_pct,
            "avg_trade_pnl": self.avg_trade_pnl,
            "total_trades": self.total_trades,
            "calmar_ratio": self.calmar_ratio,
            "recovery_factor": self.recovery_factor,
            "win_streak_max": self.win_streak_max,
            "loss_streak_max": self.loss_streak_max,
            "monthly_consistency": self.monthly_consistency,
        }


@dataclass
class EvaluationResult:
    """Result of evaluating a genome on a scenario"""
    genome_id: str
    scenario_name: str
    fitness: float
    metrics: FitnessMetrics
    passed_risk_gates: bool
    risk_gate_failures: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "genome_id": self.genome_id,
            "scenario": self.scenario_name,
            "fitness": self.fitness,
            "metrics": self.metrics.to_dict(),
            "passed_risk_gates": self.passed_risk_gates,
            "risk_gate_failures": self.risk_gate_failures,
        }


@dataclass
class IntelligenceEvolutionConfig:
    """Configuration for Intelligence Evolution Engine"""
    
    # Population
    initial_population_size: int = 30
    children_per_generation: int = 15
    
    # Selection
    tournament_size: int = 4
    elite_count: int = 3
    
    # Mutation
    mutation_rate: float = 0.15
    mutation_strength: float = 0.10
    crossover_rate: float = 0.35
    blend_rate: float = 0.15
    
    # Risk gates
    min_sharpe_ratio: float = 0.3
    max_drawdown_pct: float = 20.0
    min_win_rate: float = 0.30
    min_profit_factor: float = 1.0
    min_trades: int = 20
    
    # Fitness weights (multi-objective)
    sharpe_weight: float = 0.30
    sortino_weight: float = 0.15
    return_weight: float = 0.20
    drawdown_weight: float = 0.15
    consistency_weight: float = 0.10
    profit_factor_weight: float = 0.10
    
    # Stopping
    max_generations: int = 100
    stagnation_limit: int = 15
    target_fitness: float = 2.0  # Stop if achieved
    
    # Meta-evolution
    enable_meta_evolution: bool = True
    meta_evolution_interval: int = 10  # Generations between meta-evolution
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "initial_population_size": self.initial_population_size,
            "children_per_generation": self.children_per_generation,
            "tournament_size": self.tournament_size,
            "elite_count": self.elite_count,
            "mutation_rate": self.mutation_rate,
            "mutation_strength": self.mutation_strength,
            "crossover_rate": self.crossover_rate,
            "blend_rate": self.blend_rate,
            "min_sharpe_ratio": self.min_sharpe_ratio,
            "max_drawdown_pct": self.max_drawdown_pct,
            "min_win_rate": self.min_win_rate,
            "min_profit_factor": self.min_profit_factor,
            "min_trades": self.min_trades,
            "max_generations": self.max_generations,
            "stagnation_limit": self.stagnation_limit,
            "target_fitness": self.target_fitness,
            "enable_meta_evolution": self.enable_meta_evolution,
        }


@dataclass
class IntelligenceBehavior:
    """
    Extended behavior descriptor for intelligence genomes.
    
    Captures more dimensions than basic strategy behavior.
    """
    # Trading behavior
    trade_frequency_bucket: int = 1
    holding_time_bucket: int = 1
    risk_bucket: int = 1
    
    # Intelligence behavior
    technical_bias_bucket: int = 2  # 0=fundamental, 3=technical
    confluence_strictness_bucket: int = 1  # 0=loose, 3=strict
    regime_sensitivity_bucket: int = 1  # 0=ignore regime, 3=regime-dependent
    
    def to_tuple(self) -> Tuple[int, ...]:
        return (
            self.trade_frequency_bucket,
            self.holding_time_bucket,
            self.risk_bucket,
            self.technical_bias_bucket,
            self.confluence_strictness_bucket,
            self.regime_sensitivity_bucket,
        )
    
    def to_dict(self) -> Dict[str, int]:
        return {
            "trade_frequency": self.trade_frequency_bucket,
            "holding_time": self.holding_time_bucket,
            "risk": self.risk_bucket,
            "technical_bias": self.technical_bias_bucket,
            "confluence_strictness": self.confluence_strictness_bucket,
            "regime_sensitivity": self.regime_sensitivity_bucket,
        }


def compute_intelligence_behavior(
    genome: IntelligenceGenome,
    metrics: FitnessMetrics
) -> IntelligenceBehavior:
    """Compute behavior descriptor from genome and metrics"""
    
    # Trade frequency
    trades_per_day = metrics.total_trades / max(1, 252)  # Assume 252 trading days
    if trades_per_day < 0.5:
        freq_bucket = 0
    elif trades_per_day < 2:
        freq_bucket = 1
    elif trades_per_day < 5:
        freq_bucket = 2
    else:
        freq_bucket = 3
    
    # Risk bucket
    risk_score = (genome.risk_per_trade_pct / 3.0 + genome.max_drawdown_pct / 20.0) / 2
    if risk_score < 0.25:
        risk_bucket = 0
    elif risk_score < 0.5:
        risk_bucket = 1
    elif risk_score < 0.75:
        risk_bucket = 2
    else:
        risk_bucket = 3
    
    # Technical bias
    tech_bias = genome.technical_weight / (genome.technical_weight + genome.fundamental_weight + 0.001)
    if tech_bias < 0.4:
        tech_bucket = 0
    elif tech_bias < 0.55:
        tech_bucket = 1
    elif tech_bias < 0.7:
        tech_bucket = 2
    else:
        tech_bucket = 3
    
    # Confluence strictness
    conf_score = genome.min_confluence_threshold
    if conf_score < 0.4:
        conf_bucket = 0
    elif conf_score < 0.5:
        conf_bucket = 1
    elif conf_score < 0.6:
        conf_bucket = 2
    else:
        conf_bucket = 3
    
    # Regime sensitivity
    regime_score = genome.regime_weight
    if regime_score < 0.25:
        regime_bucket = 0
    elif regime_score < 0.35:
        regime_bucket = 1
    elif regime_score < 0.45:
        regime_bucket = 2
    else:
        regime_bucket = 3
    
    return IntelligenceBehavior(
        trade_frequency_bucket=freq_bucket,
        holding_time_bucket=1,  # Default, would need actual holding time data
        risk_bucket=risk_bucket,
        technical_bias_bucket=tech_bucket,
        confluence_strictness_bucket=conf_bucket,
        regime_sensitivity_bucket=regime_bucket,
    )


class IntelligenceEvolutionEngine:
    """
    Full-Stack Intelligence Evolution Engine.
    
    This is the core of the QUADRUPLE INTELLIGENCE system.
    It evolves the entire intelligence stack using DRQ principles.
    """
    
    def __init__(
        self,
        evaluator: Callable[[IntelligenceGenome, AdversarialScenario], EvaluationResult],
        config: Optional[IntelligenceEvolutionConfig] = None,
        scenarios: Optional[List[AdversarialScenario]] = None,
    ):
        """
        Args:
            evaluator: Function that evaluates a genome on a scenario
            config: Evolution configuration
            scenarios: List of adversarial scenarios
        """
        self.evaluator = evaluator
        self.config = config or IntelligenceEvolutionConfig()
        self.scenarios = scenarios or ADVERSARIAL_SCENARIOS
        
        # Archive for diversity
        self._archive: Dict[Tuple[int, ...], Tuple[IntelligenceGenome, float]] = {}
        
        # Evolution state
        self._generation = 0
        self._best_fitness = float("-inf")
        self._best_genome: Optional[IntelligenceGenome] = None
        self._stagnation_counter = 0
        
        # History
        self._history: List[Dict[str, Any]] = []
        self._fitness_history: List[float] = []
        
        # Meta-evolution state
        self._meta_mutation_rate = self.config.mutation_rate
        self._meta_mutation_strength = self.config.mutation_strength
    
    def initialize_population(self) -> List[IntelligenceGenome]:
        """Create initial population with diversity"""
        population = []
        
        # Add default genome
        population.append(create_default_intelligence_genome())
        
        # Add random genomes
        for _ in range(self.config.initial_population_size - 1):
            population.append(create_random_intelligence_genome())
        
        logger.info(f"Initialized population with {len(population)} genomes")
        return population
    
    def calculate_fitness(self, metrics: FitnessMetrics) -> float:
        """
        Calculate multi-objective fitness score.
        
        Higher is better.
        """
        cfg = self.config
        
        # Normalize metrics
        sharpe_norm = max(0, min(3, metrics.sharpe_ratio)) / 3.0
        sortino_norm = max(0, min(4, metrics.sortino_ratio)) / 4.0
        return_norm = max(0, min(100, metrics.total_return_pct)) / 100.0
        drawdown_norm = 1.0 - min(1, metrics.max_drawdown_pct / 30.0)  # Lower is better
        consistency_norm = metrics.monthly_consistency
        pf_norm = max(0, min(3, metrics.profit_factor)) / 3.0
        
        # Weighted sum
        fitness = (
            cfg.sharpe_weight * sharpe_norm +
            cfg.sortino_weight * sortino_norm +
            cfg.return_weight * return_norm +
            cfg.drawdown_weight * drawdown_norm +
            cfg.consistency_weight * consistency_norm +
            cfg.profit_factor_weight * pf_norm
        )
        
        return fitness
    
    def check_risk_gates(self, metrics: FitnessMetrics) -> Tuple[bool, List[str]]:
        """Check if metrics pass risk gates"""
        failures = []
        cfg = self.config
        
        if metrics.sharpe_ratio < cfg.min_sharpe_ratio:
            failures.append(f"Sharpe {metrics.sharpe_ratio:.2f} < {cfg.min_sharpe_ratio}")
        
        if metrics.max_drawdown_pct > cfg.max_drawdown_pct:
            failures.append(f"Drawdown {metrics.max_drawdown_pct:.1f}% > {cfg.max_drawdown_pct}%")
        
        if metrics.win_rate < cfg.min_win_rate:
            failures.append(f"Win rate {metrics.win_rate:.1%} < {cfg.min_win_rate:.1%}")
        
        if metrics.profit_factor < cfg.min_profit_factor:
            failures.append(f"Profit factor {metrics.profit_factor:.2f} < {cfg.min_profit_factor}")
        
        if metrics.total_trades < cfg.min_trades:
            failures.append(f"Trades {metrics.total_trades} < {cfg.min_trades}")
        
        return len(failures) == 0, failures
    
    def evaluate_genome(
        self,
        genome: IntelligenceGenome
    ) -> Tuple[float, IntelligenceBehavior, Dict[str, Any]]:
        """
        Evaluate a genome across all scenarios.
        
        Returns:
            - Combined fitness score
            - Behavior descriptor
            - Detailed metrics per scenario
        """
        results = []
        all_metrics = {}
        
        for scenario in self.scenarios:
            result = self.evaluator(genome, scenario)
            results.append(result)
            all_metrics[scenario.name] = result.metrics.to_dict()
        
        # Aggregate metrics
        total_weight = sum(s.weight for s in self.scenarios)
        
        # Weighted average of fitness
        weighted_fitness = sum(
            r.fitness * s.weight
            for r, s in zip(results, self.scenarios)
        ) / total_weight
        
        # Check if any scenario failed risk gates
        all_passed = all(r.passed_risk_gates for r in results)
        
        # Penalty for failing risk gates
        if not all_passed:
            weighted_fitness *= 0.5
        
        # Compute average metrics for behavior
        avg_metrics = FitnessMetrics(
            sharpe_ratio=sum(r.metrics.sharpe_ratio for r in results) / len(results),
            total_trades=sum(r.metrics.total_trades for r in results),
            win_rate=sum(r.metrics.win_rate for r in results) / len(results),
            max_drawdown_pct=max(r.metrics.max_drawdown_pct for r in results),
            profit_factor=sum(r.metrics.profit_factor for r in results) / len(results),
            monthly_consistency=sum(r.metrics.monthly_consistency for r in results) / len(results),
        )
        
        behavior = compute_intelligence_behavior(genome, avg_metrics)
        
        return weighted_fitness, behavior, all_metrics
    
    def add_to_archive(
        self,
        genome: IntelligenceGenome,
        behavior: IntelligenceBehavior,
        fitness: float
    ) -> bool:
        """Try to add genome to archive"""
        key = behavior.to_tuple()
        
        if key not in self._archive or fitness > self._archive[key][1]:
            self._archive[key] = (genome, fitness)
            return True
        return False
    
    def select_parent(self) -> IntelligenceGenome:
        """Select a parent using tournament selection from archive"""
        if not self._archive:
            return create_random_intelligence_genome()
        
        # Tournament selection
        candidates = []
        archive_list = list(self._archive.values())
        
        for _ in range(self.config.tournament_size):
            genome, fitness = random.choice(archive_list)
            candidates.append((genome, fitness))
        
        # Return best from tournament
        best = max(candidates, key=lambda x: x[1])
        return best[0].clone()
    
    def create_offspring(self) -> List[IntelligenceGenome]:
        """Create offspring for next generation"""
        offspring = []
        
        for _ in range(self.config.children_per_generation):
            r = random.random()
            
            if r < self.config.crossover_rate and len(self._archive) >= 2:
                # Crossover
                parent1 = self.select_parent()
                parent2 = self.select_parent()
                child1, child2 = crossover_intelligence_genomes(parent1, parent2)
                offspring.append(child1)
            elif r < self.config.crossover_rate + self.config.blend_rate and len(self._archive) >= 2:
                # Blend
                parent1 = self.select_parent()
                parent2 = self.select_parent()
                child = blend_intelligence_genomes(parent1, parent2, random.random())
                offspring.append(child)
            else:
                # Mutation
                parent = self.select_parent()
                child = mutate_intelligence_genome(
                    parent,
                    mutation_rate=self._meta_mutation_rate,
                    mutation_strength=self._meta_mutation_strength,
                )
                offspring.append(child)
        
        return offspring
    
    def meta_evolve(self):
        """
        Meta-evolution: Adjust evolution parameters based on progress.
        
        This is the "evolution of evolution" - adapting mutation rates
        and other parameters based on how well evolution is progressing.
        """
        if not self.config.enable_meta_evolution:
            return
        
        # If stagnating, increase mutation
        if self._stagnation_counter > 5:
            self._meta_mutation_rate = min(0.4, self._meta_mutation_rate * 1.2)
            self._meta_mutation_strength = min(0.3, self._meta_mutation_strength * 1.1)
            logger.info(
                f"Meta-evolution: Increasing mutation rate to {self._meta_mutation_rate:.3f}, "
                f"strength to {self._meta_mutation_strength:.3f}"
            )
        # If improving, decrease mutation for fine-tuning
        elif self._stagnation_counter == 0:
            self._meta_mutation_rate = max(0.05, self._meta_mutation_rate * 0.95)
            self._meta_mutation_strength = max(0.03, self._meta_mutation_strength * 0.95)
            logger.info(
                f"Meta-evolution: Decreasing mutation rate to {self._meta_mutation_rate:.3f}, "
                f"strength to {self._meta_mutation_strength:.3f}"
            )
    
    def run_generation(self, population: List[IntelligenceGenome]) -> Dict[str, Any]:
        """Run one generation of evolution"""
        gen_stats = {
            "generation": self._generation,
            "population_size": len(population),
            "evaluations": 0,
            "archive_additions": 0,
            "best_fitness": float("-inf"),
            "avg_fitness": 0.0,
        }
        
        fitnesses = []
        
        for genome in population:
            fitness, behavior, metrics = self.evaluate_genome(genome)
            gen_stats["evaluations"] += 1
            fitnesses.append(fitness)
            
            if fitness > gen_stats["best_fitness"]:
                gen_stats["best_fitness"] = fitness
            
            # Try to add to archive
            if self.add_to_archive(genome, behavior, fitness):
                gen_stats["archive_additions"] += 1
            
            # Track best overall
            if fitness > self._best_fitness:
                self._best_fitness = fitness
                self._best_genome = genome.clone()
                self._best_genome.fitness = fitness
                self._stagnation_counter = 0
            
        # Check for stagnation
        if gen_stats["best_fitness"] <= self._best_fitness:
            self._stagnation_counter += 1
        
        gen_stats["avg_fitness"] = sum(fitnesses) / len(fitnesses) if fitnesses else 0
        gen_stats["stagnation"] = self._stagnation_counter
        gen_stats["archive_size"] = len(self._archive)
        gen_stats["mutation_rate"] = self._meta_mutation_rate
        gen_stats["mutation_strength"] = self._meta_mutation_strength
        
        self._history.append(gen_stats)
        self._fitness_history.append(gen_stats["best_fitness"])
        self._generation += 1
        
        logger.info(
            f"Gen {gen_stats['generation']}: "
            f"best={gen_stats['best_fitness']:.4f}, "
            f"avg={gen_stats['avg_fitness']:.4f}, "
            f"archive={gen_stats['archive_size']}, "
            f"stagnation={gen_stats['stagnation']}"
        )
        
        return gen_stats
    
    def run(self, max_generations: Optional[int] = None) -> Dict[str, Any]:
        """
        Run the full Intelligence Evolution loop.
        
        Returns:
            Summary of the evolution run
        """
        max_gen = max_generations or self.config.max_generations
        
        logger.info(f"Starting Intelligence Evolution for {max_gen} generations")
        logger.info(f"Scenarios: {[s.name for s in self.scenarios]}")
        
        # Initialize
        population = self.initialize_population()
        
        # Run generations
        for gen in range(max_gen):
            stats = self.run_generation(population)
            
            # Check stopping conditions
            if self._stagnation_counter >= self.config.stagnation_limit:
                logger.info(f"Stopping due to stagnation at generation {gen}")
                break
            
            if self._best_fitness >= self.config.target_fitness:
                logger.info(f"Stopping: Target fitness {self.config.target_fitness} achieved")
                break
            
            # Meta-evolution
            if gen > 0 and gen % self.config.meta_evolution_interval == 0:
                self.meta_evolve()
            
            # Create next generation
            population = self.create_offspring()
        
        # Final summary
        summary = {
            "generations_run": self._generation,
            "final_archive_size": len(self._archive),
            "best_fitness": self._best_fitness,
            "best_genome_id": self._best_genome.genome_id if self._best_genome else None,
            "total_evaluations": sum(h["evaluations"] for h in self._history),
            "final_mutation_rate": self._meta_mutation_rate,
            "final_mutation_strength": self._meta_mutation_strength,
            "fitness_history": self._fitness_history,
        }
        
        logger.info(f"Intelligence Evolution complete: {summary}")
        return summary
    
    def get_champions(self, n: int = 5) -> List[IntelligenceGenome]:
        """Get the top N genomes from the archive"""
        sorted_archive = sorted(
            self._archive.values(),
            key=lambda x: x[1],
            reverse=True
        )
        return [genome for genome, _ in sorted_archive[:n]]
    
    def get_best_genome(self) -> Optional[IntelligenceGenome]:
        """Get the best genome found"""
        return self._best_genome
    
    def save_state(self, output_dir: Path):
        """Save the current state of evolution"""
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Save best genome
        if self._best_genome:
            self._best_genome.save(str(output_dir / "best_genome.json"))
        
        # Save archive
        archive_data = {
            str(k): {"genome": g.to_dict(), "fitness": f}
            for k, (g, f) in self._archive.items()
        }
        with open(output_dir / "archive.json", "w") as f:
            json.dump(archive_data, f, indent=2)
        
        # Save history
        with open(output_dir / "history.json", "w") as f:
            json.dump(self._history, f, indent=2)
        
        # Save config
        with open(output_dir / "config.json", "w") as f:
            json.dump(self.config.to_dict(), f, indent=2)
        
        # Save champions
        champions_dir = output_dir / "champions"
        champions_dir.mkdir(exist_ok=True)
        for i, genome in enumerate(self.get_champions(10)):
            genome.save(str(champions_dir / f"champion_{i}.json"))
        
        logger.info(f"Saved evolution state to {output_dir}")
    
    def load_state(self, input_dir: Path):
        """Load state from a previous run"""
        # Load best genome
        best_path = input_dir / "best_genome.json"
        if best_path.exists():
            self._best_genome = IntelligenceGenome.load(str(best_path))
            self._best_fitness = self._best_genome.fitness
        
        # Load archive
        archive_path = input_dir / "archive.json"
        if archive_path.exists():
            with open(archive_path, "r") as f:
                archive_data = json.load(f)
            self._archive = {}
            for k_str, v in archive_data.items():
                k = tuple(int(x) for x in k_str.strip("()").split(",") if x.strip())
                genome = IntelligenceGenome.from_dict(v["genome"])
                self._archive[k] = (genome, v["fitness"])
        
        # Load history
        history_path = input_dir / "history.json"
        if history_path.exists():
            with open(history_path, "r") as f:
                self._history = json.load(f)
            if self._history:
                self._generation = self._history[-1]["generation"] + 1
                self._fitness_history = [h["best_fitness"] for h in self._history]
        
        logger.info(f"Loaded evolution state from {input_dir}")


def create_dummy_evaluator() -> Callable[[IntelligenceGenome, AdversarialScenario], EvaluationResult]:
    """
    Create a dummy evaluator for testing.
    
    In production, this would be replaced with actual backtesting.
    """
    def evaluate(genome: IntelligenceGenome, scenario: AdversarialScenario) -> EvaluationResult:
        # Simulate evaluation with random metrics
        metrics = FitnessMetrics(
            sharpe_ratio=random.gauss(1.0, 0.5),
            sortino_ratio=random.gauss(1.2, 0.6),
            max_drawdown_pct=random.uniform(5, 20),
            win_rate=random.uniform(0.35, 0.65),
            profit_factor=random.uniform(0.8, 2.0),
            total_return_pct=random.uniform(-10, 50),
            avg_trade_pnl=random.uniform(-0.5, 1.0),
            total_trades=random.randint(20, 200),
            monthly_consistency=random.uniform(0.4, 0.8),
        )
        
        # Calculate fitness
        fitness = (
            0.3 * max(0, metrics.sharpe_ratio) / 2.0 +
            0.2 * max(0, metrics.total_return_pct) / 50.0 +
            0.2 * (1 - metrics.max_drawdown_pct / 30.0) +
            0.15 * metrics.win_rate +
            0.15 * min(1, metrics.profit_factor / 2.0)
        )
        
        # Check risk gates
        passed = (
            metrics.sharpe_ratio > 0.3 and
            metrics.max_drawdown_pct < 20 and
            metrics.win_rate > 0.30 and
            metrics.total_trades > 20
        )
        
        return EvaluationResult(
            genome_id=genome.genome_id,
            scenario_name=scenario.name,
            fitness=fitness,
            metrics=metrics,
            passed_risk_gates=passed,
        )
    
    return evaluate
