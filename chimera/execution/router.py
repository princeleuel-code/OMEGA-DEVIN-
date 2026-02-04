"""
Router - Signal routing and trade proposal

The Router proposes actions (LONG/SHORT/WAIT) based on features and genome.
It does NOT execute trades - that's the job of the execution daemon.
"""

from dataclasses import dataclass
from typing import Optional, Dict, Any
from enum import Enum, auto

from ..data.features import Features, Trend, MarketStructure
from ..evolution.genome import StrategyGenome
from ..core.decision_engine import Signal, Action, create_wait_signal, create_trade_signal
from ..core.reason_codes import ReasonCode


class SetupType(Enum):
    """Types of trading setups"""
    TREND_CONTINUATION = auto()
    TREND_REVERSAL = auto()
    RANGE_BOUNCE = auto()
    BREAKOUT = auto()
    NONE = auto()


@dataclass
class RouterConfig:
    """Configuration for the router"""
    # Minimum requirements
    min_atr_threshold: float = 0.0001
    min_volume_ratio: float = 0.5
    
    # Confidence adjustments
    displacement_bonus: float = 0.15
    trend_alignment_bonus: float = 0.15
    volume_bonus: float = 0.10
    structure_break_bonus: float = 0.20
    
    # Setup detection
    enable_trend_continuation: bool = True
    enable_trend_reversal: bool = True
    enable_range_bounce: bool = False
    enable_breakout: bool = True


class Router:
    """
    Route market conditions to trading signals.
    
    The Router analyzes features and genome parameters to propose
    trading actions. It implements the "Ethiopian Method" of
    structure-based trading.
    """
    
    def __init__(self, config: Optional[RouterConfig] = None):
        self.config = config or RouterConfig()
    
    def generate_signal(
        self,
        features: Features,
        genome: StrategyGenome
    ) -> Signal:
        """
        Generate a trading signal from features and genome.
        
        Returns a Signal with action, confidence, and levels.
        """
        # Pre-checks
        if not self._passes_prechecks(features, genome):
            return create_wait_signal("Failed prechecks")
        
        # Detect setup type
        setup_type, direction = self._detect_setup(features, genome)
        
        if setup_type == SetupType.NONE:
            return create_wait_signal("No valid setup detected")
        
        # Calculate confidence
        confidence = self._calculate_confidence(features, genome, setup_type)
        
        if confidence < genome.min_confidence:
            return create_wait_signal(
                f"Confidence {confidence:.2f} below threshold {genome.min_confidence:.2f}"
            )
        
        # Calculate entry, stop loss, take profit
        entry, stop_loss, take_profit = self._calculate_levels(
            features, genome, direction
        )
        
        # Create signal
        action = Action.LONG if direction == 1 else Action.SHORT
        
        return create_trade_signal(
            action=action,
            confidence=confidence,
            entry=entry,
            stop_loss=stop_loss,
            take_profit=take_profit,
            size=genome.risk_per_trade_pct / 100,
            reason=f"{setup_type.name} setup with {confidence:.0%} confidence"
        )
    
    def _passes_prechecks(self, features: Features, genome: StrategyGenome) -> bool:
        """Check if basic requirements are met"""
        # ATR check
        if features.atr < genome.min_atr:
            return False
        
        # Volume check
        if features.relative_volume < genome.min_volume_ratio:
            return False
        
        # Displacement check (if required)
        if genome.require_displacement and not features.displacement:
            return False
        
        return True
    
    def _detect_setup(
        self,
        features: Features,
        genome: StrategyGenome
    ) -> tuple[SetupType, int]:
        """
        Detect the type of setup and direction.
        
        Returns (SetupType, direction) where direction is 1 for long, -1 for short.
        """
        structure = features.structure
        
        # Trend continuation
        if self.config.enable_trend_continuation:
            if structure.trend == Trend.BULLISH:
                # Look for pullback to structure
                if features.displacement and features.displacement_direction == 1:
                    return SetupType.TREND_CONTINUATION, 1
            
            elif structure.trend == Trend.BEARISH:
                if features.displacement and features.displacement_direction == -1:
                    return SetupType.TREND_CONTINUATION, -1
        
        # Trend reversal (Change of Character)
        if self.config.enable_trend_reversal:
            if structure.change_of_character:
                if features.displacement_direction == 1:
                    return SetupType.TREND_REVERSAL, 1
                elif features.displacement_direction == -1:
                    return SetupType.TREND_REVERSAL, -1
        
        # Breakout (Break of Structure)
        if self.config.enable_breakout:
            if structure.structure_break and genome.require_structure_break:
                if features.displacement_direction == 1:
                    return SetupType.BREAKOUT, 1
                elif features.displacement_direction == -1:
                    return SetupType.BREAKOUT, -1
        
        # Range bounce
        if self.config.enable_range_bounce:
            if structure.trend == Trend.RANGING:
                # Check if at range extremes
                if structure.last_swing_low and structure.last_swing_high:
                    range_size = structure.last_swing_high.price - structure.last_swing_low.price
                    if range_size > 0:
                        position_in_range = (
                            (features.close - structure.last_swing_low.price) / range_size
                        )
                        
                        # Near bottom of range
                        if position_in_range < 0.2 and features.displacement_direction == 1:
                            return SetupType.RANGE_BOUNCE, 1
                        
                        # Near top of range
                        if position_in_range > 0.8 and features.displacement_direction == -1:
                            return SetupType.RANGE_BOUNCE, -1
        
        return SetupType.NONE, 0
    
    def _calculate_confidence(
        self,
        features: Features,
        genome: StrategyGenome,
        setup_type: SetupType
    ) -> float:
        """Calculate confidence score for the setup"""
        confidence = 0.5  # Base confidence
        
        # Displacement bonus
        if features.displacement:
            confidence += self.config.displacement_bonus
        
        # Trend alignment bonus
        structure = features.structure
        if setup_type == SetupType.TREND_CONTINUATION:
            confidence += self.config.trend_alignment_bonus
        
        # Volume bonus
        if features.relative_volume > 1.5:
            confidence += self.config.volume_bonus
        elif features.relative_volume > 1.2:
            confidence += self.config.volume_bonus / 2
        
        # Structure break bonus
        if structure.structure_break or structure.change_of_character:
            confidence += self.config.structure_break_bonus
        
        # Regime affinity adjustment
        is_trending = structure.trend in (Trend.BULLISH, Trend.BEARISH)
        if is_trending:
            # Boost if genome prefers trends
            confidence += (genome.trend_affinity - 0.5) * 0.1
        else:
            # Boost if genome prefers ranges
            confidence += (0.5 - genome.trend_affinity) * 0.1
        
        # Volatility affinity adjustment
        high_vol = features.volatility > 0.5  # Normalized volatility
        if high_vol:
            confidence += (genome.volatility_affinity - 0.5) * 0.1
        else:
            confidence += (0.5 - genome.volatility_affinity) * 0.1
        
        return min(1.0, max(0.0, confidence))
    
    def _calculate_levels(
        self,
        features: Features,
        genome: StrategyGenome,
        direction: int
    ) -> tuple[float, float, float]:
        """
        Calculate entry, stop loss, and take profit levels.
        
        Returns (entry, stop_loss, take_profit)
        """
        entry = features.close
        atr = features.atr
        
        if direction == 1:  # Long
            stop_loss = entry - atr * genome.atr_multiplier_sl
            take_profit = entry + atr * genome.atr_multiplier_tp
            
            # Use structure levels if available
            structure = features.structure
            if structure.last_swing_low:
                # Place stop below recent swing low
                structure_stop = structure.last_swing_low.price - atr * 0.5
                # Use the tighter of the two
                stop_loss = max(stop_loss, structure_stop)
        
        else:  # Short
            stop_loss = entry + atr * genome.atr_multiplier_sl
            take_profit = entry - atr * genome.atr_multiplier_tp
            
            structure = features.structure
            if structure.last_swing_high:
                structure_stop = structure.last_swing_high.price + atr * 0.5
                stop_loss = min(stop_loss, structure_stop)
        
        return entry, stop_loss, take_profit
    
    def analyze_setup(
        self,
        features: Features,
        genome: StrategyGenome
    ) -> Dict[str, Any]:
        """
        Analyze a potential setup without generating a signal.
        
        Useful for debugging and understanding why trades are/aren't taken.
        """
        analysis = {
            "timestamp": features.timestamp.isoformat(),
            "close": features.close,
            "atr": features.atr,
            "volatility": features.volatility,
            "relative_volume": features.relative_volume,
            "structure": features.structure.to_dict(),
            "displacement": features.displacement,
            "displacement_direction": features.displacement_direction
        }
        
        # Check prechecks
        analysis["passes_prechecks"] = self._passes_prechecks(features, genome)
        analysis["precheck_details"] = {
            "atr_ok": features.atr >= genome.min_atr,
            "volume_ok": features.relative_volume >= genome.min_volume_ratio,
            "displacement_ok": not genome.require_displacement or features.displacement
        }
        
        # Detect setup
        setup_type, direction = self._detect_setup(features, genome)
        analysis["setup_type"] = setup_type.name
        analysis["direction"] = direction
        
        # Calculate confidence
        if setup_type != SetupType.NONE:
            confidence = self._calculate_confidence(features, genome, setup_type)
            analysis["confidence"] = confidence
            analysis["confidence_threshold"] = genome.min_confidence
            analysis["would_trade"] = confidence >= genome.min_confidence
        else:
            analysis["would_trade"] = False
        
        return analysis
