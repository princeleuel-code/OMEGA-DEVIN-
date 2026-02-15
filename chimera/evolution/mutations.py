"""
Mutations - Genetic operators for strategy genomes

Provides mutation and crossover operations to evolve strategies.
"""

import random
from typing import Optional, Tuple
from .genome import StrategyGenome, GenomeConfig


def mutate_genome(
    genome: StrategyGenome,
    mutation_rate: float = 0.2,
    mutation_strength: float = 0.1,
    config: Optional[GenomeConfig] = None
) -> StrategyGenome:
    """
    Mutate a genome by randomly perturbing parameters.
    
    Args:
        genome: The genome to mutate
        mutation_rate: Probability of mutating each parameter (0-1)
        mutation_strength: How much to change values (0-1, as fraction of range)
        config: Bounds for parameters
    
    Returns:
        A new mutated genome
    """
    cfg = config or GenomeConfig()
    child = genome.clone()
    
    def mutate_float(value: float, bounds: Tuple[float, float]) -> float:
        if random.random() > mutation_rate:
            return value
        range_size = bounds[1] - bounds[0]
        delta = random.gauss(0, mutation_strength * range_size)
        new_value = value + delta
        return max(bounds[0], min(bounds[1], new_value))
    
    def mutate_int(value: int, bounds: Tuple[int, int]) -> int:
        if random.random() > mutation_rate:
            return value
        range_size = bounds[1] - bounds[0]
        delta = int(random.gauss(0, mutation_strength * range_size))
        new_value = value + delta
        return max(bounds[0], min(bounds[1], new_value))
    
    def mutate_bool(value: bool) -> bool:
        if random.random() > mutation_rate:
            return value
        return not value
    
    # Mutate each parameter
    child.min_confidence = mutate_float(child.min_confidence, cfg.min_confidence)
    child.atr_multiplier_sl = mutate_float(child.atr_multiplier_sl, cfg.atr_multiplier_sl)
    child.atr_multiplier_tp = mutate_float(child.atr_multiplier_tp, cfg.atr_multiplier_tp)
    child.require_displacement = mutate_bool(child.require_displacement)
    child.require_structure_break = mutate_bool(child.require_structure_break)
    child.min_swing_distance = mutate_int(child.min_swing_distance, cfg.min_swing_distance)
    child.risk_per_trade_pct = mutate_float(child.risk_per_trade_pct, cfg.risk_per_trade_pct)
    child.max_trades_per_day = mutate_int(child.max_trades_per_day, cfg.max_trades_per_day)
    child.max_drawdown_pct = mutate_float(child.max_drawdown_pct, cfg.max_drawdown_pct)
    child.hold_bars_min = mutate_int(child.hold_bars_min, cfg.hold_bars_min)
    child.hold_bars_max = mutate_int(child.hold_bars_max, cfg.hold_bars_max)
    child.min_atr = mutate_float(child.min_atr, cfg.min_atr)
    child.max_spread_atr_ratio = mutate_float(child.max_spread_atr_ratio, cfg.max_spread_atr_ratio)
    child.min_volume_ratio = mutate_float(child.min_volume_ratio, cfg.min_volume_ratio)
    child.use_aether_gate = mutate_bool(child.use_aether_gate)
    child.aether_entropy_max = mutate_float(child.aether_entropy_max, cfg.aether_entropy_max)
    child.aether_coherence_min = mutate_float(child.aether_coherence_min, cfg.aether_coherence_min)
    child.aether_pc_min = mutate_float(child.aether_pc_min, cfg.aether_pc_min)
    child.aether_force_min = mutate_float(child.aether_force_min, cfg.aether_force_min)
    child.aether_block_on_seam = mutate_bool(child.aether_block_on_seam)
    child.aether_seam_force_override = mutate_float(child.aether_seam_force_override, cfg.aether_seam_force_override)
    child.trend_affinity = mutate_float(child.trend_affinity, (0.0, 1.0))
    child.volatility_affinity = mutate_float(child.volatility_affinity, (0.0, 1.0))
    
    # Ensure hold_bars_min <= hold_bars_max
    if child.hold_bars_min > child.hold_bars_max:
        child.hold_bars_min, child.hold_bars_max = child.hold_bars_max, child.hold_bars_min
    
    # Regenerate ID since parameters changed
    child.genome_id = child._generate_id()
    
    return child


def crossover_genomes(
    parent1: StrategyGenome,
    parent2: StrategyGenome,
    crossover_rate: float = 0.5
) -> Tuple[StrategyGenome, StrategyGenome]:
    """
    Create two children by crossing over two parent genomes.
    
    Uses uniform crossover: each parameter is randomly taken from either parent.
    
    Args:
        parent1: First parent genome
        parent2: Second parent genome
        crossover_rate: Probability of taking from parent2 vs parent1
    
    Returns:
        Tuple of two child genomes
    """
    child1 = parent1.clone()
    child2 = parent2.clone()
    
    # Track both parents
    child1.parent_ids = [parent1.genome_id, parent2.genome_id]
    child2.parent_ids = [parent1.genome_id, parent2.genome_id]
    
    # List of parameter names to crossover
    params = [
        "min_confidence", "atr_multiplier_sl", "atr_multiplier_tp",
        "require_displacement", "require_structure_break", "min_swing_distance",
        "risk_per_trade_pct", "max_trades_per_day", "max_drawdown_pct",
        "hold_bars_min", "hold_bars_max", "min_atr", "max_spread_atr_ratio",
        "min_volume_ratio", "use_aether_gate", "aether_entropy_max",
        "aether_coherence_min", "aether_pc_min", "aether_force_min",
        "aether_block_on_seam", "aether_seam_force_override",
        "trend_affinity", "volatility_affinity"
    ]
    
    for param in params:
        if random.random() < crossover_rate:
            # Swap values between children
            val1 = getattr(child1, param)
            val2 = getattr(child2, param)
            setattr(child1, param, val2)
            setattr(child2, param, val1)
    
    # Ensure constraints
    for child in [child1, child2]:
        if child.hold_bars_min > child.hold_bars_max:
            child.hold_bars_min, child.hold_bars_max = child.hold_bars_max, child.hold_bars_min
        child.genome_id = child._generate_id()
    
    return child1, child2


def blend_genomes(
    parent1: StrategyGenome,
    parent2: StrategyGenome,
    blend_ratio: float = 0.5
) -> StrategyGenome:
    """
    Create a child by blending two parents' parameters.
    
    Numeric parameters are interpolated, booleans are randomly chosen.
    
    Args:
        parent1: First parent genome
        parent2: Second parent genome
        blend_ratio: How much of parent2 to use (0 = all parent1, 1 = all parent2)
    
    Returns:
        Blended child genome
    """
    child = parent1.clone()
    child.parent_ids = [parent1.genome_id, parent2.genome_id]
    
    def blend_float(v1: float, v2: float) -> float:
        return v1 * (1 - blend_ratio) + v2 * blend_ratio
    
    def blend_int(v1: int, v2: int) -> int:
        return int(round(v1 * (1 - blend_ratio) + v2 * blend_ratio))
    
    def blend_bool(v1: bool, v2: bool) -> bool:
        if v1 == v2:
            return v1
        return random.random() < blend_ratio
    
    child.min_confidence = blend_float(parent1.min_confidence, parent2.min_confidence)
    child.atr_multiplier_sl = blend_float(parent1.atr_multiplier_sl, parent2.atr_multiplier_sl)
    child.atr_multiplier_tp = blend_float(parent1.atr_multiplier_tp, parent2.atr_multiplier_tp)
    child.require_displacement = blend_bool(parent1.require_displacement, parent2.require_displacement)
    child.require_structure_break = blend_bool(parent1.require_structure_break, parent2.require_structure_break)
    child.min_swing_distance = blend_int(parent1.min_swing_distance, parent2.min_swing_distance)
    child.risk_per_trade_pct = blend_float(parent1.risk_per_trade_pct, parent2.risk_per_trade_pct)
    child.max_trades_per_day = blend_int(parent1.max_trades_per_day, parent2.max_trades_per_day)
    child.max_drawdown_pct = blend_float(parent1.max_drawdown_pct, parent2.max_drawdown_pct)
    child.hold_bars_min = blend_int(parent1.hold_bars_min, parent2.hold_bars_min)
    child.hold_bars_max = blend_int(parent1.hold_bars_max, parent2.hold_bars_max)
    child.min_atr = blend_float(parent1.min_atr, parent2.min_atr)
    child.max_spread_atr_ratio = blend_float(parent1.max_spread_atr_ratio, parent2.max_spread_atr_ratio)
    child.min_volume_ratio = blend_float(parent1.min_volume_ratio, parent2.min_volume_ratio)
    child.use_aether_gate = blend_bool(parent1.use_aether_gate, parent2.use_aether_gate)
    child.aether_entropy_max = blend_float(parent1.aether_entropy_max, parent2.aether_entropy_max)
    child.aether_coherence_min = blend_float(parent1.aether_coherence_min, parent2.aether_coherence_min)
    child.aether_pc_min = blend_float(parent1.aether_pc_min, parent2.aether_pc_min)
    child.aether_force_min = blend_float(parent1.aether_force_min, parent2.aether_force_min)
    child.aether_block_on_seam = blend_bool(parent1.aether_block_on_seam, parent2.aether_block_on_seam)
    child.aether_seam_force_override = blend_float(parent1.aether_seam_force_override, parent2.aether_seam_force_override)
    child.trend_affinity = blend_float(parent1.trend_affinity, parent2.trend_affinity)
    child.volatility_affinity = blend_float(parent1.volatility_affinity, parent2.volatility_affinity)
    
    if child.hold_bars_min > child.hold_bars_max:
        child.hold_bars_min, child.hold_bars_max = child.hold_bars_max, child.hold_bars_min
    
    child.genome_id = child._generate_id()
    return child
