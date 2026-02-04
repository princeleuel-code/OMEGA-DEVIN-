"""
Strategy Genome - Strategies as evolvable configurations

A genome represents a complete trading strategy as a set of tunable parameters.
This allows strategies to be:
- Mutated (small random changes)
- Crossed over (combine two strategies)
- Archived (exact reproduction via hash)
- Evaluated (deterministic scoring)
"""

from dataclasses import dataclass, field, asdict
from typing import Dict, Any, Optional, List
import hashlib
import json
import random
from datetime import datetime


@dataclass
class GenomeConfig:
    """Bounds and defaults for genome parameters"""
    
    # Entry parameters
    min_confidence: tuple = (0.3, 0.9)  # (min, max) range
    atr_multiplier_sl: tuple = (1.0, 4.0)  # Stop loss ATR multiplier
    atr_multiplier_tp: tuple = (1.5, 6.0)  # Take profit ATR multiplier
    
    # Structure parameters
    require_displacement: tuple = (0, 1)  # Boolean as int
    require_structure_break: tuple = (0, 1)
    min_swing_distance: tuple = (3, 20)  # Bars
    
    # Risk parameters
    risk_per_trade_pct: tuple = (0.5, 3.0)
    max_trades_per_day: tuple = (1, 10)
    max_drawdown_pct: tuple = (2.0, 10.0)
    
    # Timing parameters
    hold_bars_min: tuple = (1, 10)
    hold_bars_max: tuple = (10, 100)
    
    # Filter parameters
    min_atr: tuple = (0.0001, 0.001)
    max_spread_atr_ratio: tuple = (0.1, 0.5)
    min_volume_ratio: tuple = (0.5, 2.0)


@dataclass
class StrategyGenome:
    """
    A complete trading strategy encoded as parameters.
    
    This is the "DNA" of a strategy - everything needed to reproduce
    its behavior exactly.
    """
    
    # Identification
    genome_id: str = ""
    parent_ids: List[str] = field(default_factory=list)
    generation: int = 0
    created_at: str = ""
    
    # Entry parameters
    min_confidence: float = 0.6
    atr_multiplier_sl: float = 2.0
    atr_multiplier_tp: float = 3.0
    
    # Structure parameters
    require_displacement: bool = True
    require_structure_break: bool = False
    min_swing_distance: int = 5
    
    # Risk parameters
    risk_per_trade_pct: float = 1.0
    max_trades_per_day: int = 5
    max_drawdown_pct: float = 5.0
    
    # Timing parameters
    hold_bars_min: int = 2
    hold_bars_max: int = 24
    
    # Filter parameters
    min_atr: float = 0.0003
    max_spread_atr_ratio: float = 0.3
    min_volume_ratio: float = 0.8
    
    # Regime affinity (which regimes this strategy prefers)
    trend_affinity: float = 0.5  # 0 = range, 1 = trend
    volatility_affinity: float = 0.5  # 0 = low vol, 1 = high vol
    
    def __post_init__(self):
        if not self.genome_id:
            self.genome_id = self._generate_id()
        if not self.created_at:
            self.created_at = datetime.utcnow().isoformat()
    
    def _generate_id(self) -> str:
        """Generate unique genome ID based on parameters"""
        params = self.to_dict()
        # Remove metadata for hashing
        for key in ["genome_id", "parent_ids", "generation", "created_at"]:
            params.pop(key, None)
        
        canonical = json.dumps(params, sort_keys=True)
        hash_val = hashlib.sha256(canonical.encode()).hexdigest()[:12]
        return f"genome_{hash_val}"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "StrategyGenome":
        """Create from dictionary"""
        return cls(**d)
    
    def get_hash(self) -> str:
        """Get deterministic hash of strategy parameters"""
        params = self.to_dict()
        for key in ["genome_id", "parent_ids", "generation", "created_at"]:
            params.pop(key, None)
        canonical = json.dumps(params, sort_keys=True)
        return hashlib.sha256(canonical.encode()).hexdigest()
    
    def clone(self) -> "StrategyGenome":
        """Create an exact copy"""
        d = self.to_dict()
        d["genome_id"] = ""  # Will be regenerated
        d["parent_ids"] = [self.genome_id]
        d["generation"] = self.generation + 1
        d["created_at"] = ""
        return StrategyGenome.from_dict(d)
    
    def save(self, path: str):
        """Save genome to JSON file"""
        with open(path, "w") as f:
            json.dump(self.to_dict(), f, indent=2)
    
    @classmethod
    def load(cls, path: str) -> "StrategyGenome":
        """Load genome from JSON file"""
        with open(path, "r") as f:
            return cls.from_dict(json.load(f))


def create_random_genome(config: Optional[GenomeConfig] = None) -> StrategyGenome:
    """Create a random genome within configured bounds"""
    cfg = config or GenomeConfig()
    
    def rand_range(bounds: tuple) -> float:
        return random.uniform(bounds[0], bounds[1])
    
    def rand_int_range(bounds: tuple) -> int:
        return random.randint(int(bounds[0]), int(bounds[1]))
    
    def rand_bool(bounds: tuple) -> bool:
        return random.random() > 0.5
    
    return StrategyGenome(
        min_confidence=rand_range(cfg.min_confidence),
        atr_multiplier_sl=rand_range(cfg.atr_multiplier_sl),
        atr_multiplier_tp=rand_range(cfg.atr_multiplier_tp),
        require_displacement=rand_bool(cfg.require_displacement),
        require_structure_break=rand_bool(cfg.require_structure_break),
        min_swing_distance=rand_int_range(cfg.min_swing_distance),
        risk_per_trade_pct=rand_range(cfg.risk_per_trade_pct),
        max_trades_per_day=rand_int_range(cfg.max_trades_per_day),
        max_drawdown_pct=rand_range(cfg.max_drawdown_pct),
        hold_bars_min=rand_int_range(cfg.hold_bars_min),
        hold_bars_max=rand_int_range(cfg.hold_bars_max),
        min_atr=rand_range(cfg.min_atr),
        max_spread_atr_ratio=rand_range(cfg.max_spread_atr_ratio),
        min_volume_ratio=rand_range(cfg.min_volume_ratio),
        trend_affinity=random.random(),
        volatility_affinity=random.random()
    )


def create_default_genome() -> StrategyGenome:
    """Create a genome with conservative default values"""
    return StrategyGenome(
        min_confidence=0.5,  # Lowered for more trades in backtesting
        atr_multiplier_sl=2.0,
        atr_multiplier_tp=3.0,
        require_displacement=False,  # Disabled for more trades
        require_structure_break=False,
        min_swing_distance=5,
        risk_per_trade_pct=1.0,
        max_trades_per_day=20,  # Increased for backtesting
        max_drawdown_pct=10.0,  # Increased for backtesting
        hold_bars_min=2,
        hold_bars_max=24,
        min_atr=0.0001,  # Lowered for synthetic data
        max_spread_atr_ratio=0.5,
        min_volume_ratio=0.5,  # Lowered for more trades
        trend_affinity=0.5,
        volatility_affinity=0.5
    )
