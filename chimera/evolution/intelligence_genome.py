"""
INTELLIGENCE GENOME - Full-Stack Evolvable Intelligence Parameters

This module extends the basic StrategyGenome to cover ALL parameters
across the entire intelligence stack:

1. Delta Print Intelligence parameters
2. VPIN/Orderflow parameters
3. HMM Regime Detection parameters
4. Consciousness Engine parameters
5. Fundamental Intelligence parameters
6. Complete Intelligence integration weights

This enables TRUE DRQ-style evolution of the entire system,
not just trading parameters.

Author: Devin (for Prince)
"""

from dataclasses import dataclass, field, asdict
from typing import Dict, Any, Optional, List, Tuple
import hashlib
import json
import random
from datetime import datetime


@dataclass
class IntelligenceGenomeConfig:
    """Bounds and defaults for ALL intelligence parameters"""
    
    # === DELTA PRINT PARAMETERS ===
    big_trade_threshold: Tuple[float, float] = (0.005, 0.05)  # % of avg volume
    absorption_threshold: Tuple[float, float] = (0.5, 0.9)
    ledge_ratio_threshold: Tuple[float, float] = (2.0, 5.0)
    value_area_pct: Tuple[float, float] = (0.60, 0.80)
    
    # === VPIN PARAMETERS ===
    vpin_bucket_volume: Tuple[float, float] = (500.0, 5000.0)
    vpin_window_buckets: Tuple[int, int] = (20, 100)
    vpin_high_threshold: Tuple[float, float] = (0.5, 0.8)  # High informed trading
    vpin_low_threshold: Tuple[float, float] = (0.2, 0.4)   # Low informed trading
    
    # === HMM REGIME PARAMETERS ===
    hmm_learning_rate: Tuple[float, float] = (0.001, 0.1)
    hmm_trend_up_mean: Tuple[float, float] = (0.01, 0.05)
    hmm_trend_down_mean: Tuple[float, float] = (-0.05, -0.01)
    hmm_mean_revert_var: Tuple[float, float] = (0.001, 0.01)
    hmm_high_vol_var: Tuple[float, float] = (0.02, 0.1)
    
    # === CONSCIOUSNESS PARAMETERS ===
    min_confluence_threshold: Tuple[float, float] = (0.3, 0.7)
    min_confidence_threshold: Tuple[float, float] = (0.4, 0.7)
    uncertainty_threshold: Tuple[float, float] = (0.3, 0.6)
    model_agreement_threshold: Tuple[float, float] = (0.2, 0.5)
    
    # === FUNDAMENTAL PARAMETERS ===
    undervalued_threshold: Tuple[float, float] = (0.05, 0.20)
    deeply_undervalued_threshold: Tuple[float, float] = (0.20, 0.50)
    min_current_ratio: Tuple[float, float] = (0.8, 1.5)
    max_debt_to_equity: Tuple[float, float] = (1.0, 3.0)
    min_profit_margin: Tuple[float, float] = (0.02, 0.10)
    
    # === INTEGRATION WEIGHTS ===
    technical_weight: Tuple[float, float] = (0.4, 0.8)
    fundamental_weight: Tuple[float, float] = (0.2, 0.6)
    delta_print_weight: Tuple[float, float] = (0.3, 0.7)
    vpin_weight: Tuple[float, float] = (0.2, 0.5)
    regime_weight: Tuple[float, float] = (0.2, 0.5)
    
    # === SIGNAL GENERATION ===
    confluence_boost: Tuple[float, float] = (0.05, 0.25)
    divergence_penalty: Tuple[float, float] = (0.10, 0.30)
    institutional_grade_threshold: Tuple[float, float] = (0.65, 0.85)
    
    # === RISK PARAMETERS ===
    risk_per_trade_pct: Tuple[float, float] = (0.5, 3.0)
    max_drawdown_pct: Tuple[float, float] = (5.0, 20.0)
    max_trades_per_day: Tuple[int, int] = (1, 20)
    
    # === ENTRY/EXIT PARAMETERS ===
    atr_multiplier_sl: Tuple[float, float] = (1.0, 4.0)
    atr_multiplier_tp: Tuple[float, float] = (1.5, 6.0)
    min_risk_reward: Tuple[float, float] = (1.0, 3.0)


@dataclass
class IntelligenceGenome:
    """
    Complete Intelligence Genome - ALL parameters for the entire system.
    
    This is the "DNA" of the entire intelligence stack - everything needed
    to configure and reproduce the system's behavior exactly.
    """
    
    # === IDENTIFICATION ===
    genome_id: str = ""
    parent_ids: List[str] = field(default_factory=list)
    generation: int = 0
    created_at: str = ""
    fitness: float = 0.0
    
    # === DELTA PRINT PARAMETERS ===
    big_trade_threshold: float = 0.01
    absorption_threshold: float = 0.7
    ledge_ratio_threshold: float = 3.0
    value_area_pct: float = 0.70
    
    # === VPIN PARAMETERS ===
    vpin_bucket_volume: float = 1000.0
    vpin_window_buckets: int = 50
    vpin_high_threshold: float = 0.65
    vpin_low_threshold: float = 0.35
    
    # === HMM REGIME PARAMETERS ===
    hmm_learning_rate: float = 0.01
    hmm_trend_up_mean: float = 0.02
    hmm_trend_down_mean: float = -0.02
    hmm_mean_revert_var: float = 0.005
    hmm_high_vol_var: float = 0.04
    
    # === CONSCIOUSNESS PARAMETERS ===
    min_confluence_threshold: float = 0.40
    min_confidence_threshold: float = 0.50
    uncertainty_threshold: float = 0.50
    model_agreement_threshold: float = 0.30
    
    # === FUNDAMENTAL PARAMETERS ===
    undervalued_threshold: float = 0.10
    deeply_undervalued_threshold: float = 0.30
    min_current_ratio: float = 1.0
    max_debt_to_equity: float = 2.0
    min_profit_margin: float = 0.05
    
    # === INTEGRATION WEIGHTS ===
    technical_weight: float = 0.60
    fundamental_weight: float = 0.40
    delta_print_weight: float = 0.50
    vpin_weight: float = 0.30
    regime_weight: float = 0.30
    
    # === SIGNAL GENERATION ===
    confluence_boost: float = 0.15
    divergence_penalty: float = 0.15
    institutional_grade_threshold: float = 0.75
    
    # === RISK PARAMETERS ===
    risk_per_trade_pct: float = 1.0
    max_drawdown_pct: float = 10.0
    max_trades_per_day: int = 10
    
    # === ENTRY/EXIT PARAMETERS ===
    atr_multiplier_sl: float = 2.0
    atr_multiplier_tp: float = 3.0
    min_risk_reward: float = 1.5
    
    # === REGIME AFFINITY ===
    trend_affinity: float = 0.5
    volatility_affinity: float = 0.5
    
    def __post_init__(self):
        if not self.genome_id:
            self.genome_id = self._generate_id()
        if not self.created_at:
            self.created_at = datetime.utcnow().isoformat()
        self._normalize_weights()
    
    def _generate_id(self) -> str:
        """Generate unique genome ID based on parameters"""
        params = self.to_dict()
        for key in ["genome_id", "parent_ids", "generation", "created_at", "fitness"]:
            params.pop(key, None)
        canonical = json.dumps(params, sort_keys=True)
        hash_val = hashlib.sha256(canonical.encode()).hexdigest()[:12]
        return f"intel_{hash_val}"
    
    def _normalize_weights(self):
        """Ensure integration weights sum to reasonable values"""
        total_tech = self.technical_weight + self.fundamental_weight
        if total_tech > 0:
            self.technical_weight = self.technical_weight / total_tech
            self.fundamental_weight = self.fundamental_weight / total_tech
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "IntelligenceGenome":
        """Create from dictionary"""
        return cls(**d)
    
    def get_hash(self) -> str:
        """Get deterministic hash of parameters"""
        params = self.to_dict()
        for key in ["genome_id", "parent_ids", "generation", "created_at", "fitness"]:
            params.pop(key, None)
        canonical = json.dumps(params, sort_keys=True)
        return hashlib.sha256(canonical.encode()).hexdigest()
    
    def clone(self) -> "IntelligenceGenome":
        """Create an exact copy"""
        d = self.to_dict()
        d["genome_id"] = ""
        d["parent_ids"] = [self.genome_id]
        d["generation"] = self.generation + 1
        d["created_at"] = ""
        d["fitness"] = 0.0
        return IntelligenceGenome.from_dict(d)
    
    def save(self, path: str):
        """Save genome to JSON file"""
        with open(path, "w") as f:
            json.dump(self.to_dict(), f, indent=2)
    
    @classmethod
    def load(cls, path: str) -> "IntelligenceGenome":
        """Load genome from JSON file"""
        with open(path, "r") as f:
            return cls.from_dict(json.load(f))
    
    def get_delta_print_config(self) -> Dict[str, Any]:
        """Get Delta Print Intelligence configuration"""
        return {
            "big_trade_threshold": self.big_trade_threshold,
            "absorption_threshold": self.absorption_threshold,
            "ledge_ratio_threshold": self.ledge_ratio_threshold,
            "value_area_pct": self.value_area_pct,
        }
    
    def get_vpin_config(self) -> Dict[str, Any]:
        """Get VPIN configuration"""
        return {
            "bucket_volume": self.vpin_bucket_volume,
            "window_buckets": self.vpin_window_buckets,
            "high_threshold": self.vpin_high_threshold,
            "low_threshold": self.vpin_low_threshold,
        }
    
    def get_hmm_config(self) -> Dict[str, Any]:
        """Get HMM Regime configuration"""
        return {
            "learning_rate": self.hmm_learning_rate,
            "means": [self.hmm_trend_up_mean, self.hmm_trend_down_mean, 0.0, 0.0],
            "variances": [0.01, 0.01, self.hmm_mean_revert_var, self.hmm_high_vol_var],
        }
    
    def get_consciousness_config(self) -> Dict[str, Any]:
        """Get Consciousness Engine configuration"""
        return {
            "min_confluence_threshold": self.min_confluence_threshold,
            "min_confidence_threshold": self.min_confidence_threshold,
            "uncertainty_threshold": self.uncertainty_threshold,
            "model_agreement_threshold": self.model_agreement_threshold,
        }
    
    def get_fundamental_config(self) -> Dict[str, Any]:
        """Get Fundamental Intelligence configuration"""
        return {
            "undervalued_threshold": self.undervalued_threshold,
            "deeply_undervalued_threshold": self.deeply_undervalued_threshold,
            "min_current_ratio": self.min_current_ratio,
            "max_debt_to_equity": self.max_debt_to_equity,
            "min_profit_margin": self.min_profit_margin,
        }
    
    def get_integration_config(self) -> Dict[str, Any]:
        """Get integration weights configuration"""
        return {
            "technical_weight": self.technical_weight,
            "fundamental_weight": self.fundamental_weight,
            "delta_print_weight": self.delta_print_weight,
            "vpin_weight": self.vpin_weight,
            "regime_weight": self.regime_weight,
            "confluence_boost": self.confluence_boost,
            "divergence_penalty": self.divergence_penalty,
            "institutional_grade_threshold": self.institutional_grade_threshold,
        }
    
    def get_risk_config(self) -> Dict[str, Any]:
        """Get risk management configuration"""
        return {
            "risk_per_trade_pct": self.risk_per_trade_pct,
            "max_drawdown_pct": self.max_drawdown_pct,
            "max_trades_per_day": self.max_trades_per_day,
            "atr_multiplier_sl": self.atr_multiplier_sl,
            "atr_multiplier_tp": self.atr_multiplier_tp,
            "min_risk_reward": self.min_risk_reward,
        }


def create_random_intelligence_genome(
    config: Optional[IntelligenceGenomeConfig] = None
) -> IntelligenceGenome:
    """Create a random intelligence genome within configured bounds"""
    cfg = config or IntelligenceGenomeConfig()
    
    def rand_range(bounds: Tuple[float, float]) -> float:
        return random.uniform(bounds[0], bounds[1])
    
    def rand_int_range(bounds: Tuple[int, int]) -> int:
        return random.randint(bounds[0], bounds[1])
    
    return IntelligenceGenome(
        # Delta Print
        big_trade_threshold=rand_range(cfg.big_trade_threshold),
        absorption_threshold=rand_range(cfg.absorption_threshold),
        ledge_ratio_threshold=rand_range(cfg.ledge_ratio_threshold),
        value_area_pct=rand_range(cfg.value_area_pct),
        # VPIN
        vpin_bucket_volume=rand_range(cfg.vpin_bucket_volume),
        vpin_window_buckets=rand_int_range(cfg.vpin_window_buckets),
        vpin_high_threshold=rand_range(cfg.vpin_high_threshold),
        vpin_low_threshold=rand_range(cfg.vpin_low_threshold),
        # HMM
        hmm_learning_rate=rand_range(cfg.hmm_learning_rate),
        hmm_trend_up_mean=rand_range(cfg.hmm_trend_up_mean),
        hmm_trend_down_mean=rand_range(cfg.hmm_trend_down_mean),
        hmm_mean_revert_var=rand_range(cfg.hmm_mean_revert_var),
        hmm_high_vol_var=rand_range(cfg.hmm_high_vol_var),
        # Consciousness
        min_confluence_threshold=rand_range(cfg.min_confluence_threshold),
        min_confidence_threshold=rand_range(cfg.min_confidence_threshold),
        uncertainty_threshold=rand_range(cfg.uncertainty_threshold),
        model_agreement_threshold=rand_range(cfg.model_agreement_threshold),
        # Fundamental
        undervalued_threshold=rand_range(cfg.undervalued_threshold),
        deeply_undervalued_threshold=rand_range(cfg.deeply_undervalued_threshold),
        min_current_ratio=rand_range(cfg.min_current_ratio),
        max_debt_to_equity=rand_range(cfg.max_debt_to_equity),
        min_profit_margin=rand_range(cfg.min_profit_margin),
        # Integration
        technical_weight=rand_range(cfg.technical_weight),
        fundamental_weight=rand_range(cfg.fundamental_weight),
        delta_print_weight=rand_range(cfg.delta_print_weight),
        vpin_weight=rand_range(cfg.vpin_weight),
        regime_weight=rand_range(cfg.regime_weight),
        # Signal
        confluence_boost=rand_range(cfg.confluence_boost),
        divergence_penalty=rand_range(cfg.divergence_penalty),
        institutional_grade_threshold=rand_range(cfg.institutional_grade_threshold),
        # Risk
        risk_per_trade_pct=rand_range(cfg.risk_per_trade_pct),
        max_drawdown_pct=rand_range(cfg.max_drawdown_pct),
        max_trades_per_day=rand_int_range(cfg.max_trades_per_day),
        # Entry/Exit
        atr_multiplier_sl=rand_range(cfg.atr_multiplier_sl),
        atr_multiplier_tp=rand_range(cfg.atr_multiplier_tp),
        min_risk_reward=rand_range(cfg.min_risk_reward),
        # Affinity
        trend_affinity=random.random(),
        volatility_affinity=random.random(),
    )


def create_default_intelligence_genome() -> IntelligenceGenome:
    """Create a genome with conservative default values"""
    return IntelligenceGenome()


def mutate_intelligence_genome(
    genome: IntelligenceGenome,
    mutation_rate: float = 0.15,
    mutation_strength: float = 0.10,
    config: Optional[IntelligenceGenomeConfig] = None
) -> IntelligenceGenome:
    """
    Mutate an intelligence genome by randomly perturbing parameters.
    
    Args:
        genome: The genome to mutate
        mutation_rate: Probability of mutating each parameter (0-1)
        mutation_strength: How much to change values (0-1, as fraction of range)
        config: Bounds for parameters
    
    Returns:
        A new mutated genome
    """
    cfg = config or IntelligenceGenomeConfig()
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
    
    # Mutate Delta Print parameters
    child.big_trade_threshold = mutate_float(child.big_trade_threshold, cfg.big_trade_threshold)
    child.absorption_threshold = mutate_float(child.absorption_threshold, cfg.absorption_threshold)
    child.ledge_ratio_threshold = mutate_float(child.ledge_ratio_threshold, cfg.ledge_ratio_threshold)
    child.value_area_pct = mutate_float(child.value_area_pct, cfg.value_area_pct)
    
    # Mutate VPIN parameters
    child.vpin_bucket_volume = mutate_float(child.vpin_bucket_volume, cfg.vpin_bucket_volume)
    child.vpin_window_buckets = mutate_int(child.vpin_window_buckets, cfg.vpin_window_buckets)
    child.vpin_high_threshold = mutate_float(child.vpin_high_threshold, cfg.vpin_high_threshold)
    child.vpin_low_threshold = mutate_float(child.vpin_low_threshold, cfg.vpin_low_threshold)
    
    # Mutate HMM parameters
    child.hmm_learning_rate = mutate_float(child.hmm_learning_rate, cfg.hmm_learning_rate)
    child.hmm_trend_up_mean = mutate_float(child.hmm_trend_up_mean, cfg.hmm_trend_up_mean)
    child.hmm_trend_down_mean = mutate_float(child.hmm_trend_down_mean, cfg.hmm_trend_down_mean)
    child.hmm_mean_revert_var = mutate_float(child.hmm_mean_revert_var, cfg.hmm_mean_revert_var)
    child.hmm_high_vol_var = mutate_float(child.hmm_high_vol_var, cfg.hmm_high_vol_var)
    
    # Mutate Consciousness parameters
    child.min_confluence_threshold = mutate_float(child.min_confluence_threshold, cfg.min_confluence_threshold)
    child.min_confidence_threshold = mutate_float(child.min_confidence_threshold, cfg.min_confidence_threshold)
    child.uncertainty_threshold = mutate_float(child.uncertainty_threshold, cfg.uncertainty_threshold)
    child.model_agreement_threshold = mutate_float(child.model_agreement_threshold, cfg.model_agreement_threshold)
    
    # Mutate Fundamental parameters
    child.undervalued_threshold = mutate_float(child.undervalued_threshold, cfg.undervalued_threshold)
    child.deeply_undervalued_threshold = mutate_float(child.deeply_undervalued_threshold, cfg.deeply_undervalued_threshold)
    child.min_current_ratio = mutate_float(child.min_current_ratio, cfg.min_current_ratio)
    child.max_debt_to_equity = mutate_float(child.max_debt_to_equity, cfg.max_debt_to_equity)
    child.min_profit_margin = mutate_float(child.min_profit_margin, cfg.min_profit_margin)
    
    # Mutate Integration weights
    child.technical_weight = mutate_float(child.technical_weight, cfg.technical_weight)
    child.fundamental_weight = mutate_float(child.fundamental_weight, cfg.fundamental_weight)
    child.delta_print_weight = mutate_float(child.delta_print_weight, cfg.delta_print_weight)
    child.vpin_weight = mutate_float(child.vpin_weight, cfg.vpin_weight)
    child.regime_weight = mutate_float(child.regime_weight, cfg.regime_weight)
    
    # Mutate Signal parameters
    child.confluence_boost = mutate_float(child.confluence_boost, cfg.confluence_boost)
    child.divergence_penalty = mutate_float(child.divergence_penalty, cfg.divergence_penalty)
    child.institutional_grade_threshold = mutate_float(child.institutional_grade_threshold, cfg.institutional_grade_threshold)
    
    # Mutate Risk parameters
    child.risk_per_trade_pct = mutate_float(child.risk_per_trade_pct, cfg.risk_per_trade_pct)
    child.max_drawdown_pct = mutate_float(child.max_drawdown_pct, cfg.max_drawdown_pct)
    child.max_trades_per_day = mutate_int(child.max_trades_per_day, cfg.max_trades_per_day)
    
    # Mutate Entry/Exit parameters
    child.atr_multiplier_sl = mutate_float(child.atr_multiplier_sl, cfg.atr_multiplier_sl)
    child.atr_multiplier_tp = mutate_float(child.atr_multiplier_tp, cfg.atr_multiplier_tp)
    child.min_risk_reward = mutate_float(child.min_risk_reward, cfg.min_risk_reward)
    
    # Mutate Affinity
    child.trend_affinity = mutate_float(child.trend_affinity, (0.0, 1.0))
    child.volatility_affinity = mutate_float(child.volatility_affinity, (0.0, 1.0))
    
    # Ensure constraints
    if child.vpin_low_threshold > child.vpin_high_threshold:
        child.vpin_low_threshold, child.vpin_high_threshold = child.vpin_high_threshold, child.vpin_low_threshold
    
    if child.undervalued_threshold > child.deeply_undervalued_threshold:
        child.undervalued_threshold, child.deeply_undervalued_threshold = child.deeply_undervalued_threshold, child.undervalued_threshold
    
    # Regenerate ID
    child.genome_id = child._generate_id()
    child._normalize_weights()
    
    return child


def crossover_intelligence_genomes(
    parent1: IntelligenceGenome,
    parent2: IntelligenceGenome,
    crossover_rate: float = 0.5
) -> Tuple[IntelligenceGenome, IntelligenceGenome]:
    """
    Create two children by crossing over two parent genomes.
    
    Uses uniform crossover: each parameter is randomly taken from either parent.
    """
    child1 = parent1.clone()
    child2 = parent2.clone()
    
    child1.parent_ids = [parent1.genome_id, parent2.genome_id]
    child2.parent_ids = [parent1.genome_id, parent2.genome_id]
    
    # All parameter names to crossover
    params = [
        # Delta Print
        "big_trade_threshold", "absorption_threshold", "ledge_ratio_threshold", "value_area_pct",
        # VPIN
        "vpin_bucket_volume", "vpin_window_buckets", "vpin_high_threshold", "vpin_low_threshold",
        # HMM
        "hmm_learning_rate", "hmm_trend_up_mean", "hmm_trend_down_mean", "hmm_mean_revert_var", "hmm_high_vol_var",
        # Consciousness
        "min_confluence_threshold", "min_confidence_threshold", "uncertainty_threshold", "model_agreement_threshold",
        # Fundamental
        "undervalued_threshold", "deeply_undervalued_threshold", "min_current_ratio", "max_debt_to_equity", "min_profit_margin",
        # Integration
        "technical_weight", "fundamental_weight", "delta_print_weight", "vpin_weight", "regime_weight",
        # Signal
        "confluence_boost", "divergence_penalty", "institutional_grade_threshold",
        # Risk
        "risk_per_trade_pct", "max_drawdown_pct", "max_trades_per_day",
        # Entry/Exit
        "atr_multiplier_sl", "atr_multiplier_tp", "min_risk_reward",
        # Affinity
        "trend_affinity", "volatility_affinity",
    ]
    
    for param in params:
        if random.random() < crossover_rate:
            val1 = getattr(child1, param)
            val2 = getattr(child2, param)
            setattr(child1, param, val2)
            setattr(child2, param, val1)
    
    # Ensure constraints and regenerate IDs
    for child in [child1, child2]:
        if child.vpin_low_threshold > child.vpin_high_threshold:
            child.vpin_low_threshold, child.vpin_high_threshold = child.vpin_high_threshold, child.vpin_low_threshold
        if child.undervalued_threshold > child.deeply_undervalued_threshold:
            child.undervalued_threshold, child.deeply_undervalued_threshold = child.deeply_undervalued_threshold, child.undervalued_threshold
        child.genome_id = child._generate_id()
        child._normalize_weights()
    
    return child1, child2


def blend_intelligence_genomes(
    parent1: IntelligenceGenome,
    parent2: IntelligenceGenome,
    blend_ratio: float = 0.5
) -> IntelligenceGenome:
    """
    Create a child by blending two parents' parameters.
    
    Numeric parameters are interpolated.
    """
    child = parent1.clone()
    child.parent_ids = [parent1.genome_id, parent2.genome_id]
    
    def blend_float(v1: float, v2: float) -> float:
        return v1 * (1 - blend_ratio) + v2 * blend_ratio
    
    def blend_int(v1: int, v2: int) -> int:
        return int(round(v1 * (1 - blend_ratio) + v2 * blend_ratio))
    
    # Blend all parameters
    child.big_trade_threshold = blend_float(parent1.big_trade_threshold, parent2.big_trade_threshold)
    child.absorption_threshold = blend_float(parent1.absorption_threshold, parent2.absorption_threshold)
    child.ledge_ratio_threshold = blend_float(parent1.ledge_ratio_threshold, parent2.ledge_ratio_threshold)
    child.value_area_pct = blend_float(parent1.value_area_pct, parent2.value_area_pct)
    
    child.vpin_bucket_volume = blend_float(parent1.vpin_bucket_volume, parent2.vpin_bucket_volume)
    child.vpin_window_buckets = blend_int(parent1.vpin_window_buckets, parent2.vpin_window_buckets)
    child.vpin_high_threshold = blend_float(parent1.vpin_high_threshold, parent2.vpin_high_threshold)
    child.vpin_low_threshold = blend_float(parent1.vpin_low_threshold, parent2.vpin_low_threshold)
    
    child.hmm_learning_rate = blend_float(parent1.hmm_learning_rate, parent2.hmm_learning_rate)
    child.hmm_trend_up_mean = blend_float(parent1.hmm_trend_up_mean, parent2.hmm_trend_up_mean)
    child.hmm_trend_down_mean = blend_float(parent1.hmm_trend_down_mean, parent2.hmm_trend_down_mean)
    child.hmm_mean_revert_var = blend_float(parent1.hmm_mean_revert_var, parent2.hmm_mean_revert_var)
    child.hmm_high_vol_var = blend_float(parent1.hmm_high_vol_var, parent2.hmm_high_vol_var)
    
    child.min_confluence_threshold = blend_float(parent1.min_confluence_threshold, parent2.min_confluence_threshold)
    child.min_confidence_threshold = blend_float(parent1.min_confidence_threshold, parent2.min_confidence_threshold)
    child.uncertainty_threshold = blend_float(parent1.uncertainty_threshold, parent2.uncertainty_threshold)
    child.model_agreement_threshold = blend_float(parent1.model_agreement_threshold, parent2.model_agreement_threshold)
    
    child.undervalued_threshold = blend_float(parent1.undervalued_threshold, parent2.undervalued_threshold)
    child.deeply_undervalued_threshold = blend_float(parent1.deeply_undervalued_threshold, parent2.deeply_undervalued_threshold)
    child.min_current_ratio = blend_float(parent1.min_current_ratio, parent2.min_current_ratio)
    child.max_debt_to_equity = blend_float(parent1.max_debt_to_equity, parent2.max_debt_to_equity)
    child.min_profit_margin = blend_float(parent1.min_profit_margin, parent2.min_profit_margin)
    
    child.technical_weight = blend_float(parent1.technical_weight, parent2.technical_weight)
    child.fundamental_weight = blend_float(parent1.fundamental_weight, parent2.fundamental_weight)
    child.delta_print_weight = blend_float(parent1.delta_print_weight, parent2.delta_print_weight)
    child.vpin_weight = blend_float(parent1.vpin_weight, parent2.vpin_weight)
    child.regime_weight = blend_float(parent1.regime_weight, parent2.regime_weight)
    
    child.confluence_boost = blend_float(parent1.confluence_boost, parent2.confluence_boost)
    child.divergence_penalty = blend_float(parent1.divergence_penalty, parent2.divergence_penalty)
    child.institutional_grade_threshold = blend_float(parent1.institutional_grade_threshold, parent2.institutional_grade_threshold)
    
    child.risk_per_trade_pct = blend_float(parent1.risk_per_trade_pct, parent2.risk_per_trade_pct)
    child.max_drawdown_pct = blend_float(parent1.max_drawdown_pct, parent2.max_drawdown_pct)
    child.max_trades_per_day = blend_int(parent1.max_trades_per_day, parent2.max_trades_per_day)
    
    child.atr_multiplier_sl = blend_float(parent1.atr_multiplier_sl, parent2.atr_multiplier_sl)
    child.atr_multiplier_tp = blend_float(parent1.atr_multiplier_tp, parent2.atr_multiplier_tp)
    child.min_risk_reward = blend_float(parent1.min_risk_reward, parent2.min_risk_reward)
    
    child.trend_affinity = blend_float(parent1.trend_affinity, parent2.trend_affinity)
    child.volatility_affinity = blend_float(parent1.volatility_affinity, parent2.volatility_affinity)
    
    # Ensure constraints
    if child.vpin_low_threshold > child.vpin_high_threshold:
        child.vpin_low_threshold, child.vpin_high_threshold = child.vpin_high_threshold, child.vpin_low_threshold
    if child.undervalued_threshold > child.deeply_undervalued_threshold:
        child.undervalued_threshold, child.deeply_undervalued_threshold = child.deeply_undervalued_threshold, child.undervalued_threshold
    
    child.genome_id = child._generate_id()
    child._normalize_weights()
    
    return child
