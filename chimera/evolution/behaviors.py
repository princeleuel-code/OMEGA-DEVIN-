"""
Behavior Descriptors - Characterize strategy behavior for MAP-Elites

Behavior descriptors define the "niche" of a strategy in behavior space.
This allows us to maintain diversity: strategies that behave differently
are kept even if one has slightly lower fitness.
"""

from dataclasses import dataclass
from typing import List, Dict, Any, Tuple
from enum import Enum, auto


class BehaviorDimension(Enum):
    """Dimensions of behavior space"""
    TRADE_FREQUENCY = auto()    # How often it trades
    HOLDING_TIME = auto()       # How long it holds positions
    REGIME_AFFINITY = auto()    # Trend vs range preference
    RISK_PROFILE = auto()       # Conservative vs aggressive
    VOLATILITY_PREF = auto()    # Low vs high volatility preference


@dataclass
class BehaviorDescriptor:
    """
    Multi-dimensional behavior descriptor for a strategy.
    
    Each dimension is discretized into buckets for MAP-Elites grid.
    """
    
    # Trade frequency: trades per day (discretized)
    # 0 = very low (0-1), 1 = low (1-3), 2 = medium (3-5), 3 = high (5+)
    trade_frequency_bucket: int = 1
    
    # Holding time: average bars held
    # 0 = scalp (1-5), 1 = short (5-20), 2 = medium (20-50), 3 = long (50+)
    holding_time_bucket: int = 1
    
    # Regime affinity: trend vs range
    # 0 = strong range, 1 = slight range, 2 = slight trend, 3 = strong trend
    regime_bucket: int = 2
    
    # Risk profile: based on risk per trade and drawdown tolerance
    # 0 = very conservative, 1 = conservative, 2 = moderate, 3 = aggressive
    risk_bucket: int = 1
    
    # Volatility preference
    # 0 = low vol only, 1 = prefers low, 2 = prefers high, 3 = high vol only
    volatility_bucket: int = 1
    
    def to_tuple(self) -> Tuple[int, ...]:
        """Convert to tuple for use as dictionary key"""
        return (
            self.trade_frequency_bucket,
            self.holding_time_bucket,
            self.regime_bucket,
            self.risk_bucket,
            self.volatility_bucket
        )
    
    def to_dict(self) -> Dict[str, int]:
        return {
            "trade_frequency": self.trade_frequency_bucket,
            "holding_time": self.holding_time_bucket,
            "regime": self.regime_bucket,
            "risk": self.risk_bucket,
            "volatility": self.volatility_bucket
        }
    
    @classmethod
    def from_tuple(cls, t: Tuple[int, ...]) -> "BehaviorDescriptor":
        return cls(
            trade_frequency_bucket=t[0],
            holding_time_bucket=t[1],
            regime_bucket=t[2],
            risk_bucket=t[3],
            volatility_bucket=t[4]
        )
    
    def distance(self, other: "BehaviorDescriptor") -> float:
        """Euclidean distance in behavior space"""
        t1 = self.to_tuple()
        t2 = other.to_tuple()
        return sum((a - b) ** 2 for a, b in zip(t1, t2)) ** 0.5


def compute_behavior(
    genome: "StrategyGenome",
    backtest_results: Dict[str, Any]
) -> BehaviorDescriptor:
    """
    Compute behavior descriptor from genome and backtest results.
    
    Args:
        genome: The strategy genome
        backtest_results: Results from backtesting (trades, metrics, etc.)
    
    Returns:
        BehaviorDescriptor characterizing the strategy's behavior
    """
    # Trade frequency bucket
    trades_per_day = backtest_results.get("trades_per_day", 0)
    if trades_per_day < 1:
        freq_bucket = 0
    elif trades_per_day < 3:
        freq_bucket = 1
    elif trades_per_day < 5:
        freq_bucket = 2
    else:
        freq_bucket = 3
    
    # Holding time bucket
    avg_hold = backtest_results.get("avg_holding_bars", genome.hold_bars_min)
    if avg_hold < 5:
        hold_bucket = 0
    elif avg_hold < 20:
        hold_bucket = 1
    elif avg_hold < 50:
        hold_bucket = 2
    else:
        hold_bucket = 3
    
    # Regime bucket (from genome affinity)
    trend_aff = genome.trend_affinity
    if trend_aff < 0.25:
        regime_bucket = 0
    elif trend_aff < 0.5:
        regime_bucket = 1
    elif trend_aff < 0.75:
        regime_bucket = 2
    else:
        regime_bucket = 3
    
    # Risk bucket
    risk_score = (genome.risk_per_trade_pct / 3.0 + genome.max_drawdown_pct / 10.0) / 2
    if risk_score < 0.25:
        risk_bucket = 0
    elif risk_score < 0.5:
        risk_bucket = 1
    elif risk_score < 0.75:
        risk_bucket = 2
    else:
        risk_bucket = 3
    
    # Volatility bucket
    vol_aff = genome.volatility_affinity
    if vol_aff < 0.25:
        vol_bucket = 0
    elif vol_aff < 0.5:
        vol_bucket = 1
    elif vol_aff < 0.75:
        vol_bucket = 2
    else:
        vol_bucket = 3
    
    return BehaviorDescriptor(
        trade_frequency_bucket=freq_bucket,
        holding_time_bucket=hold_bucket,
        regime_bucket=regime_bucket,
        risk_bucket=risk_bucket,
        volatility_bucket=vol_bucket
    )


def get_grid_dimensions() -> Tuple[int, ...]:
    """Get the size of each dimension in the MAP-Elites grid"""
    return (4, 4, 4, 4, 4)  # 4 buckets per dimension = 1024 cells


def get_total_cells() -> int:
    """Get total number of cells in the MAP-Elites grid"""
    dims = get_grid_dimensions()
    total = 1
    for d in dims:
        total *= d
    return total
