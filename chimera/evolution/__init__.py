"""
Evolution layer - Strategy genomes and DRQ adaptation

This module provides:
1. Basic strategy evolution (StrategyGenome, DRQLoop)
2. Full-stack intelligence evolution (IntelligenceGenome, IntelligenceEvolutionEngine)

The IntelligenceEvolutionEngine is the key to QUADRUPLING intelligence through
automated self-improvement using DRQ principles.
"""

from .genome import StrategyGenome, GenomeConfig, create_random_genome, create_default_genome
from .mutations import mutate_genome, crossover_genomes, blend_genomes
from .behaviors import BehaviorDescriptor, compute_behavior
from .map_elites import MAPElitesArchive
from .drq_loop import DRQLoop, DRQConfig, Scenario, EvaluationResult

from .intelligence_genome import (
    IntelligenceGenome,
    IntelligenceGenomeConfig,
    create_random_intelligence_genome,
    create_default_intelligence_genome,
    mutate_intelligence_genome,
    crossover_intelligence_genomes,
    blend_intelligence_genomes,
)
from .intelligence_evolution import (
    IntelligenceEvolutionEngine,
    IntelligenceEvolutionConfig,
    AdversarialScenario,
    ADVERSARIAL_SCENARIOS,
    FitnessMetrics,
    IntelligenceBehavior,
    compute_intelligence_behavior,
)

__all__ = [
    # Basic evolution
    "StrategyGenome",
    "GenomeConfig",
    "create_random_genome",
    "create_default_genome",
    "mutate_genome",
    "crossover_genomes",
    "blend_genomes",
    "BehaviorDescriptor",
    "compute_behavior",
    "MAPElitesArchive",
    "DRQLoop",
    "DRQConfig",
    "Scenario",
    "EvaluationResult",
    # Intelligence evolution (QUADRUPLE INTELLIGENCE)
    "IntelligenceGenome",
    "IntelligenceGenomeConfig",
    "create_random_intelligence_genome",
    "create_default_intelligence_genome",
    "mutate_intelligence_genome",
    "crossover_intelligence_genomes",
    "blend_intelligence_genomes",
    "IntelligenceEvolutionEngine",
    "IntelligenceEvolutionConfig",
    "AdversarialScenario",
    "ADVERSARIAL_SCENARIOS",
    "FitnessMetrics",
    "IntelligenceBehavior",
    "compute_intelligence_behavior",
]
