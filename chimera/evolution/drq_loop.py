"""
DRQ Loop - Digital Red Queen adaptation

Inspired by Sakana AI's Digital Red Queen concept:
The objective moves, so the system must keep adapting.

"Opponents" are market regimes and adversarial stressors.
Strategies must survive against increasingly difficult scenarios.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Callable, Tuple
from pathlib import Path
import logging
import random

from .genome import StrategyGenome, create_random_genome, create_default_genome
from .mutations import mutate_genome, crossover_genomes, blend_genomes
from .behaviors import BehaviorDescriptor, compute_behavior
from .map_elites import MAPElitesArchive


logger = logging.getLogger(__name__)


@dataclass
class Scenario:
    """
    An adversarial scenario to test strategies against.
    
    Scenarios represent different market conditions that strategies
    must survive.
    """
    name: str
    description: str
    
    # Data generation parameters
    trend: float = 0.0          # Trend strength
    volatility: float = 0.0002  # Base volatility
    spread_multiplier: float = 1.0
    gap_probability: float = 0.0
    
    # Stress parameters
    volatility_spike_prob: float = 0.0
    volatility_spike_mult: float = 3.0
    
    # Weight in fitness calculation
    weight: float = 1.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "trend": self.trend,
            "volatility": self.volatility,
            "spread_multiplier": self.spread_multiplier,
            "gap_probability": self.gap_probability,
            "volatility_spike_prob": self.volatility_spike_prob,
            "weight": self.weight
        }


# Default adversarial scenarios
DEFAULT_SCENARIOS = [
    Scenario(
        name="trending_up",
        description="Strong uptrend with normal volatility",
        trend=0.0001,
        volatility=0.00015,
        weight=1.0
    ),
    Scenario(
        name="trending_down",
        description="Strong downtrend with normal volatility",
        trend=-0.0001,
        volatility=0.00015,
        weight=1.0
    ),
    Scenario(
        name="ranging",
        description="Sideways market with low volatility",
        trend=0.0,
        volatility=0.0001,
        weight=1.0
    ),
    Scenario(
        name="choppy",
        description="Choppy market with high volatility",
        trend=0.0,
        volatility=0.0003,
        weight=1.0
    ),
    Scenario(
        name="volatility_spike",
        description="Normal market with sudden volatility spikes",
        trend=0.0,
        volatility=0.00015,
        volatility_spike_prob=0.1,
        volatility_spike_mult=3.0,
        weight=1.5
    ),
    Scenario(
        name="wide_spread",
        description="Normal market with wide spreads",
        trend=0.0,
        volatility=0.00015,
        spread_multiplier=2.0,
        weight=1.0
    ),
    Scenario(
        name="gap_risk",
        description="Market with occasional gaps",
        trend=0.0,
        volatility=0.00015,
        gap_probability=0.05,
        weight=1.5
    ),
    Scenario(
        name="trend_reversal",
        description="Trend that reverses mid-period",
        trend=0.00005,  # Will be modified during generation
        volatility=0.0002,
        weight=2.0
    ),
]


@dataclass
class EvaluationResult:
    """Result of evaluating a genome on a scenario"""
    genome_id: str
    scenario_name: str
    fitness: float
    metrics: Dict[str, Any]
    passed_risk_gates: bool
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "genome_id": self.genome_id,
            "scenario": self.scenario_name,
            "fitness": self.fitness,
            "metrics": self.metrics,
            "passed_risk_gates": self.passed_risk_gates
        }


@dataclass
class DRQConfig:
    """Configuration for DRQ loop"""
    # Population
    initial_population_size: int = 20
    children_per_generation: int = 10
    
    # Selection
    tournament_size: int = 3
    elite_count: int = 2
    
    # Mutation
    mutation_rate: float = 0.2
    mutation_strength: float = 0.15
    crossover_rate: float = 0.3
    
    # Risk gates
    min_sharpe_ratio: float = 0.5
    max_drawdown_pct: float = 15.0
    min_win_rate: float = 0.35
    
    # Stopping
    max_generations: int = 50
    stagnation_limit: int = 10  # Stop if no improvement for N generations


class DRQLoop:
    """
    Digital Red Queen evolutionary loop.
    
    Evolves strategies against adversarial scenarios, keeping
    diverse survivors in a MAP-Elites archive.
    """
    
    def __init__(
        self,
        evaluator: Callable[[StrategyGenome, Scenario], EvaluationResult],
        config: Optional[DRQConfig] = None,
        scenarios: Optional[List[Scenario]] = None
    ):
        """
        Args:
            evaluator: Function that evaluates a genome on a scenario
            config: DRQ configuration
            scenarios: List of adversarial scenarios
        """
        self.evaluator = evaluator
        self.config = config or DRQConfig()
        self.scenarios = scenarios or DEFAULT_SCENARIOS
        
        self.archive = MAPElitesArchive()
        self._best_fitness = float("-inf")
        self._stagnation_counter = 0
        self._history: List[Dict[str, Any]] = []
    
    def initialize_population(self) -> List[StrategyGenome]:
        """Create initial population"""
        population = []
        
        # Add default genome
        population.append(create_default_genome())
        
        # Add random genomes
        for _ in range(self.config.initial_population_size - 1):
            population.append(create_random_genome())
        
        logger.info(f"Initialized population with {len(population)} genomes")
        return population
    
    def evaluate_genome(self, genome: StrategyGenome) -> Tuple[float, BehaviorDescriptor, Dict[str, Any]]:
        """
        Evaluate a genome across all scenarios.
        
        Returns:
            - Combined fitness score
            - Behavior descriptor
            - Detailed metrics
        """
        results = []
        all_metrics = {}
        
        for scenario in self.scenarios:
            result = self.evaluator(genome, scenario)
            results.append(result)
            all_metrics[scenario.name] = result.metrics
        
        # Check risk gates
        passed_gates = all(r.passed_risk_gates for r in results)
        
        # Compute weighted fitness
        if not passed_gates:
            # Penalty for failing risk gates
            fitness = -1.0
        else:
            total_weight = sum(s.weight for s in self.scenarios)
            fitness = sum(
                r.fitness * s.weight 
                for r, s in zip(results, self.scenarios)
            ) / total_weight
        
        # Compute behavior from average metrics
        avg_metrics = {
            "trades_per_day": sum(
                m.get("trades_per_day", 0) for m in all_metrics.values()
            ) / len(all_metrics),
            "avg_holding_bars": sum(
                m.get("avg_holding_bars", 10) for m in all_metrics.values()
            ) / len(all_metrics)
        }
        behavior = compute_behavior(genome, avg_metrics)
        
        return fitness, behavior, all_metrics
    
    def select_parent(self) -> StrategyGenome:
        """Select a parent using tournament selection"""
        if self.archive.size == 0:
            return create_random_genome()
        
        # Tournament selection from archive
        candidates = []
        for _ in range(self.config.tournament_size):
            entry = self.archive.get_random()
            if entry:
                candidates.append(entry)
        
        if not candidates:
            return create_random_genome()
        
        # Return best from tournament
        best = max(candidates, key=lambda e: e.fitness)
        return best.genome.clone()
    
    def create_offspring(self) -> List[StrategyGenome]:
        """Create offspring for next generation"""
        offspring = []
        
        for _ in range(self.config.children_per_generation):
            if random.random() < self.config.crossover_rate and self.archive.size >= 2:
                # Crossover
                parent1 = self.select_parent()
                parent2 = self.select_parent()
                child1, child2 = crossover_genomes(parent1, parent2)
                offspring.append(child1)
            else:
                # Mutation
                parent = self.select_parent()
                child = mutate_genome(
                    parent,
                    mutation_rate=self.config.mutation_rate,
                    mutation_strength=self.config.mutation_strength
                )
                offspring.append(child)
        
        return offspring
    
    def run_generation(self, population: List[StrategyGenome]) -> Dict[str, Any]:
        """Run one generation of evolution"""
        gen_stats = {
            "generation": self.archive.generation,
            "population_size": len(population),
            "evaluations": 0,
            "archive_additions": 0,
            "best_fitness": float("-inf")
        }
        
        for genome in population:
            fitness, behavior, metrics = self.evaluate_genome(genome)
            gen_stats["evaluations"] += 1
            
            if fitness > gen_stats["best_fitness"]:
                gen_stats["best_fitness"] = fitness
            
            # Try to add to archive
            if self.archive.add(genome, behavior, fitness):
                gen_stats["archive_additions"] += 1
        
        # Check for improvement
        if gen_stats["best_fitness"] > self._best_fitness:
            self._best_fitness = gen_stats["best_fitness"]
            self._stagnation_counter = 0
        else:
            self._stagnation_counter += 1
        
        gen_stats["stagnation"] = self._stagnation_counter
        gen_stats["archive_size"] = self.archive.size
        gen_stats["archive_coverage"] = self.archive.coverage
        
        self._history.append(gen_stats)
        self.archive.increment_generation()
        
        logger.info(
            f"Gen {gen_stats['generation']}: "
            f"best={gen_stats['best_fitness']:.4f}, "
            f"archive={gen_stats['archive_size']}, "
            f"stagnation={gen_stats['stagnation']}"
        )
        
        return gen_stats
    
    def run(self, max_generations: Optional[int] = None) -> Dict[str, Any]:
        """
        Run the full DRQ evolution loop.
        
        Returns:
            Summary of the evolution run
        """
        max_gen = max_generations or self.config.max_generations
        
        logger.info(f"Starting DRQ loop for {max_gen} generations")
        
        # Initialize
        population = self.initialize_population()
        
        # Run generations
        for gen in range(max_gen):
            stats = self.run_generation(population)
            
            # Check stopping conditions
            if self._stagnation_counter >= self.config.stagnation_limit:
                logger.info(f"Stopping due to stagnation at generation {gen}")
                break
            
            # Create next generation
            population = self.create_offspring()
        
        # Final summary
        summary = {
            "generations_run": self.archive.generation,
            "final_archive_size": self.archive.size,
            "final_coverage": self.archive.coverage,
            "best_fitness": self._best_fitness,
            "total_evaluations": sum(h["evaluations"] for h in self._history),
            "archive_stats": self.archive.get_statistics()
        }
        
        logger.info(f"DRQ loop complete: {summary}")
        return summary
    
    def get_champions(self, n: int = 5) -> List[StrategyGenome]:
        """Get the top N strategies from the archive"""
        best = self.archive.get_best(n)
        return [e.genome for e in best]
    
    def save_state(self, output_dir: Path):
        """Save the current state of the DRQ loop"""
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Save archive
        self.archive.save(output_dir / "archive.json")
        
        # Save history
        import json
        with open(output_dir / "history.json", "w") as f:
            json.dump(self._history, f, indent=2)
        
        # Save champions
        champions_dir = output_dir / "champions"
        champions_dir.mkdir(exist_ok=True)
        for i, genome in enumerate(self.get_champions(10)):
            genome.save(str(champions_dir / f"champion_{i}.json"))
        
        logger.info(f"Saved DRQ state to {output_dir}")
    
    def load_state(self, input_dir: Path):
        """Load state from a previous run"""
        self.archive.load(input_dir / "archive.json")
        
        import json
        with open(input_dir / "history.json", "r") as f:
            self._history = json.load(f)
        
        if self._history:
            self._best_fitness = max(h["best_fitness"] for h in self._history)
        
        logger.info(f"Loaded DRQ state from {input_dir}")


# Type hint for the evaluate function already imported above
