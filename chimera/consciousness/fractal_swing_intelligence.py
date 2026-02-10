"""
Fractal Swing Intelligence Module

This module implements the key concepts from Dave's Fractal Scalping Strategy:
1. Four Swing Rule - Price should complete 4-6 swings before reversing at a POI
2. Previous Range Entry - Trade pullbacks to 30/50/70% of previous range
3. Rounding Pattern Detection - Cup/inverse cup patterns at tops/bottoms
4. Prominent Wick Detection - Identify wicks that stand out for targeting
5. Sweep Detection - Ensure liquidity sweep before entry
6. 21 EMA Trailing - Dynamic stop loss management
7. Fractal Structure - Same patterns appear on all timeframes

"If you can't see the sweep, you are the sweep" - Dave
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple, Any
from enum import Enum
import math


class SwingDirection(Enum):
    """Swing direction types"""
    UP = "up"
    DOWN = "down"
    NEUTRAL = "neutral"


class RoundingType(Enum):
    """Rounding pattern types"""
    CUP = "cup"  # Bullish rounding bottom
    INVERSE_CUP = "inverse_cup"  # Bearish rounding top
    NONE = "none"


class SweepType(Enum):
    """Liquidity sweep types"""
    SWEEP_HIGH = "sweep_high"  # Swept liquidity above
    SWEEP_LOW = "sweep_low"  # Swept liquidity below
    NO_SWEEP = "no_sweep"


@dataclass
class SwingPoint:
    """Represents a swing high or swing low"""
    index: int
    price: float
    is_high: bool
    strength: int
    timestamp: Optional[str] = None
    
    @property
    def type_str(self) -> str:
        return "swing_high" if self.is_high else "swing_low"


@dataclass
class PreviousRange:
    """Represents a previous price range for pullback entries"""
    high: float
    low: float
    start_index: int
    end_index: int
    
    @property
    def size(self) -> float:
        return self.high - self.low
    
    @property
    def midpoint(self) -> float:
        return (self.high + self.low) / 2
    
    def retracement_level(self, percent: float) -> float:
        """Get retracement level (30%, 50%, 70%)"""
        return self.high - (self.size * percent)
    
    @property
    def level_30(self) -> float:
        return self.retracement_level(0.30)
    
    @property
    def level_50(self) -> float:
        return self.retracement_level(0.50)
    
    @property
    def level_70(self) -> float:
        return self.retracement_level(0.70)


@dataclass
class ProminentWick:
    """Represents a prominent wick that stands out"""
    index: int
    price: float
    is_upper: bool  # True for upper wick, False for lower wick
    wick_size: float
    body_size: float
    prominence_score: float  # How much it stands out (0-1)
    
    @property
    def wick_to_body_ratio(self) -> float:
        return self.wick_size / max(self.body_size, 0.0001)


@dataclass
class LiquiditySweep:
    """Represents a liquidity sweep event"""
    sweep_type: SweepType
    index: int
    sweep_price: float  # Price that was swept
    reversal_price: float  # Price after reversal
    strength: float  # 0-1 strength score
    confirmed: bool


@dataclass
class RoundingPattern:
    """Represents a rounding pattern (cup or inverse cup)"""
    pattern_type: RoundingType
    start_index: int
    end_index: int
    apex_index: int  # Lowest point for cup, highest for inverse cup
    apex_price: float
    strength: float  # 0-1 pattern strength
    confirmed: bool


@dataclass
class FractalSwingAnalysis:
    """Complete Fractal Swing analysis result"""
    # Swing counting
    swing_count: int  # Number of swings to current POI
    swings: List[SwingPoint]
    swing_direction: SwingDirection  # Current swing direction
    ready_for_reversal: bool  # True if 4-6 swings completed
    
    # Previous range
    previous_range: Optional[PreviousRange]
    in_retracement_zone: bool  # True if price is in 30-70% zone
    retracement_level: str  # "30%", "50%", "70%", or "none"
    
    # Prominent wicks
    prominent_wicks: List[ProminentWick]
    nearest_wick_target: Optional[float]  # Nearest prominent wick to target
    
    # Liquidity sweeps
    recent_sweeps: List[LiquiditySweep]
    sweep_confirmed: bool  # True if recent sweep confirms entry
    
    # Rounding patterns
    rounding_pattern: Optional[RoundingPattern]
    
    # 21 EMA
    ema_21: float
    price_above_ema: bool
    ema_slope: str  # "up", "down", "flat"
    
    # Trade signal
    signal: str  # "LONG", "SHORT", "NEUTRAL"
    signal_strength: float  # 0-1
    confidence: float  # 0-1
    reasoning: List[str]
    
    # Entry/Exit
    entry_price: float
    stop_loss: float
    take_profit: float
    trailing_stop: float  # 21 EMA based


class FractalSwingIntelligence:
    """
    Fractal Swing Intelligence Engine
    
    Implements Dave's Fractal Scalping Strategy:
    - Count swings to POI (4-6 swings before reversal)
    - Trade pullbacks to previous range (30/50/70%)
    - Detect rounding patterns at tops/bottoms
    - Identify prominent wicks for targeting
    - Confirm liquidity sweeps before entry
    - Use 21 EMA for trailing stops
    
    "The market is fractal - same patterns on all timeframes"
    """
    
    def __init__(
        self,
        swing_strength: int = 3,
        min_swings_for_reversal: int = 4,
        max_swings_for_reversal: int = 6,
        wick_prominence_threshold: float = 2.0,
        sweep_threshold: float = 0.0003,
        ema_period: int = 21
    ):
        """
        Initialize Fractal Swing Intelligence
        
        Args:
            swing_strength: Bars on each side to confirm swing
            min_swings_for_reversal: Minimum swings before expecting reversal
            max_swings_for_reversal: Maximum swings before reversal
            wick_prominence_threshold: Wick/body ratio to be prominent
            sweep_threshold: Price threshold for sweep detection
            ema_period: EMA period for trailing (default 21)
        """
        self.swing_strength = swing_strength
        self.min_swings = min_swings_for_reversal
        self.max_swings = max_swings_for_reversal
        self.wick_prominence_threshold = wick_prominence_threshold
        self.sweep_threshold = sweep_threshold
        self.ema_period = ema_period
    
    def analyze(self, bars: List[Dict[str, Any]]) -> FractalSwingAnalysis:
        """
        Perform complete Fractal Swing analysis
        
        Args:
            bars: List of OHLCV bars
            
        Returns:
            FractalSwingAnalysis with complete analysis
        """
        if len(bars) < self.swing_strength * 2 + 1:
            return self._empty_analysis()
        
        reasoning = []
        
        # Step 1: Find all swing points
        swings = self._find_all_swings(bars)
        
        # Step 2: Count swings to current POI
        swing_count, swing_direction = self._count_swings_to_poi(swings)
        ready_for_reversal = self.min_swings <= swing_count <= self.max_swings
        
        if ready_for_reversal:
            reasoning.append(f"4-6 swing rule: {swing_count} swings completed - ready for reversal")
        else:
            reasoning.append(f"Swing count: {swing_count} - {'wait for more swings' if swing_count < self.min_swings else 'extended move'}")
        
        # Step 3: Identify previous range
        previous_range = self._find_previous_range(bars, swings)
        in_retracement_zone, retracement_level = self._check_retracement_zone(
            bars[-1]["close"], previous_range
        )
        
        if in_retracement_zone:
            reasoning.append(f"Price in {retracement_level} retracement zone of previous range")
        
        # Step 4: Find prominent wicks
        prominent_wicks = self._find_prominent_wicks(bars)
        nearest_wick_target = self._find_nearest_wick_target(
            bars[-1]["close"], prominent_wicks, swing_direction
        )
        
        if nearest_wick_target:
            reasoning.append(f"Prominent wick target at {nearest_wick_target:.5f}")
        
        # Step 5: Detect liquidity sweeps
        recent_sweeps = self._detect_liquidity_sweeps(bars, swings)
        sweep_confirmed = any(s.confirmed for s in recent_sweeps[-3:]) if recent_sweeps else False
        
        if sweep_confirmed:
            reasoning.append("Liquidity sweep confirmed - 'If you can't see the sweep, you are the sweep'")
        
        # Step 6: Detect rounding patterns
        rounding_pattern = self._detect_rounding_pattern(bars, swings)
        
        if rounding_pattern and rounding_pattern.confirmed:
            reasoning.append(f"Rounding pattern detected: {rounding_pattern.pattern_type.value}")
        
        # Step 7: Calculate 21 EMA
        ema_21 = self._calculate_ema(bars, self.ema_period)
        current_price = bars[-1]["close"]
        price_above_ema = current_price > ema_21
        ema_slope = self._calculate_ema_slope(bars, self.ema_period)
        
        reasoning.append(f"21 EMA: {ema_21:.5f}, Price {'above' if price_above_ema else 'below'}, Slope: {ema_slope}")
        
        # Step 8: Generate trade signal
        signal, signal_strength, confidence = self._generate_signal(
            swing_count=swing_count,
            swing_direction=swing_direction,
            ready_for_reversal=ready_for_reversal,
            in_retracement_zone=in_retracement_zone,
            sweep_confirmed=sweep_confirmed,
            rounding_pattern=rounding_pattern,
            price_above_ema=price_above_ema,
            ema_slope=ema_slope
        )
        
        # Step 9: Calculate entry/exit levels
        entry_price, stop_loss, take_profit, trailing_stop = self._calculate_levels(
            bars=bars,
            signal=signal,
            previous_range=previous_range,
            prominent_wicks=prominent_wicks,
            ema_21=ema_21,
            swings=swings
        )
        
        return FractalSwingAnalysis(
            swing_count=swing_count,
            swings=swings,
            swing_direction=swing_direction,
            ready_for_reversal=ready_for_reversal,
            previous_range=previous_range,
            in_retracement_zone=in_retracement_zone,
            retracement_level=retracement_level,
            prominent_wicks=prominent_wicks,
            nearest_wick_target=nearest_wick_target,
            recent_sweeps=recent_sweeps,
            sweep_confirmed=sweep_confirmed,
            rounding_pattern=rounding_pattern,
            ema_21=ema_21,
            price_above_ema=price_above_ema,
            ema_slope=ema_slope,
            signal=signal,
            signal_strength=signal_strength,
            confidence=confidence,
            reasoning=reasoning,
            entry_price=entry_price,
            stop_loss=stop_loss,
            take_profit=take_profit,
            trailing_stop=trailing_stop
        )
    
    def _find_all_swings(self, bars: List[Dict[str, Any]]) -> List[SwingPoint]:
        """Find all swing highs and lows"""
        swings = []
        n = len(bars)
        
        for i in range(self.swing_strength, n - self.swing_strength):
            # Check for swing high
            high = bars[i]["high"]
            is_swing_high = True
            for j in range(1, self.swing_strength + 1):
                if bars[i - j]["high"] >= high or bars[i + j]["high"] >= high:
                    is_swing_high = False
                    break
            
            if is_swing_high:
                swings.append(SwingPoint(
                    index=i,
                    price=high,
                    is_high=True,
                    strength=self.swing_strength,
                    timestamp=bars[i].get("timestamp")
                ))
            
            # Check for swing low
            low = bars[i]["low"]
            is_swing_low = True
            for j in range(1, self.swing_strength + 1):
                if bars[i - j]["low"] <= low or bars[i + j]["low"] <= low:
                    is_swing_low = False
                    break
            
            if is_swing_low:
                swings.append(SwingPoint(
                    index=i,
                    price=low,
                    is_high=False,
                    strength=self.swing_strength,
                    timestamp=bars[i].get("timestamp")
                ))
        
        # Sort by index
        swings.sort(key=lambda x: x.index)
        return swings
    
    def _count_swings_to_poi(self, swings: List[SwingPoint]) -> Tuple[int, SwingDirection]:
        """
        Count swings leading to current Point of Interest
        
        Returns:
            (swing_count, swing_direction)
        """
        if len(swings) < 2:
            return 0, SwingDirection.NEUTRAL
        
        # Get recent swings (last 20)
        recent_swings = swings[-20:] if len(swings) > 20 else swings
        
        # Determine direction based on recent swing pattern
        highs = [s for s in recent_swings if s.is_high]
        lows = [s for s in recent_swings if not s.is_high]
        
        if len(highs) < 2 or len(lows) < 2:
            return len(recent_swings), SwingDirection.NEUTRAL
        
        # Check for higher highs and higher lows (bullish)
        hh = highs[-1].price > highs[-2].price if len(highs) >= 2 else False
        hl = lows[-1].price > lows[-2].price if len(lows) >= 2 else False
        
        # Check for lower highs and lower lows (bearish)
        lh = highs[-1].price < highs[-2].price if len(highs) >= 2 else False
        ll = lows[-1].price < lows[-2].price if len(lows) >= 2 else False
        
        # Count consecutive swings in the same direction
        swing_count = 0
        if hh and hl:
            # Bullish - count swings from last significant low
            direction = SwingDirection.UP
            for i in range(len(recent_swings) - 1, -1, -1):
                swing_count += 1
                # Stop if we find a break in structure
                if i > 0 and recent_swings[i].is_high and recent_swings[i-1].is_high:
                    if recent_swings[i].price < recent_swings[i-1].price:
                        break
        elif lh and ll:
            # Bearish - count swings from last significant high
            direction = SwingDirection.DOWN
            for i in range(len(recent_swings) - 1, -1, -1):
                swing_count += 1
                # Stop if we find a break in structure
                if i > 0 and not recent_swings[i].is_high and not recent_swings[i-1].is_high:
                    if recent_swings[i].price > recent_swings[i-1].price:
                        break
        else:
            direction = SwingDirection.NEUTRAL
            swing_count = len(recent_swings)
        
        return min(swing_count, 10), direction
    
    def _find_previous_range(
        self,
        bars: List[Dict[str, Any]],
        swings: List[SwingPoint]
    ) -> Optional[PreviousRange]:
        """Find the previous price range for pullback entries"""
        if len(swings) < 4:
            return None
        
        # Get the last completed swing range
        recent_swings = swings[-6:] if len(swings) >= 6 else swings
        
        highs = [s for s in recent_swings if s.is_high]
        lows = [s for s in recent_swings if not s.is_high]
        
        if not highs or not lows:
            return None
        
        # Find the range from the last significant move
        range_high = max(s.price for s in highs)
        range_low = min(s.price for s in lows)
        
        start_index = min(s.index for s in recent_swings)
        end_index = max(s.index for s in recent_swings)
        
        return PreviousRange(
            high=range_high,
            low=range_low,
            start_index=start_index,
            end_index=end_index
        )
    
    def _check_retracement_zone(
        self,
        current_price: float,
        previous_range: Optional[PreviousRange]
    ) -> Tuple[bool, str]:
        """Check if price is in a retracement zone (30%, 50%, 70%)"""
        if not previous_range:
            return False, "none"
        
        # Check each retracement level with tolerance
        tolerance = previous_range.size * 0.05  # 5% tolerance
        
        if abs(current_price - previous_range.level_30) <= tolerance:
            return True, "30%"
        elif abs(current_price - previous_range.level_50) <= tolerance:
            return True, "50%"
        elif abs(current_price - previous_range.level_70) <= tolerance:
            return True, "70%"
        
        # Check if in the general retracement zone (30-70%)
        if previous_range.level_70 <= current_price <= previous_range.level_30:
            # Find closest level
            distances = {
                "30%": abs(current_price - previous_range.level_30),
                "50%": abs(current_price - previous_range.level_50),
                "70%": abs(current_price - previous_range.level_70)
            }
            closest = min(distances, key=distances.get)
            return True, closest
        
        return False, "none"
    
    def _find_prominent_wicks(self, bars: List[Dict[str, Any]]) -> List[ProminentWick]:
        """Find prominent wicks that stand out (targets to the left)"""
        prominent_wicks = []
        
        for i, bar in enumerate(bars):
            body_size = abs(bar["close"] - bar["open"])
            upper_wick = bar["high"] - max(bar["close"], bar["open"])
            lower_wick = min(bar["close"], bar["open"]) - bar["low"]
            
            # Check upper wick
            if body_size > 0 and upper_wick / body_size >= self.wick_prominence_threshold:
                prominence = min(1.0, upper_wick / body_size / 5)
                prominent_wicks.append(ProminentWick(
                    index=i,
                    price=bar["high"],
                    is_upper=True,
                    wick_size=upper_wick,
                    body_size=body_size,
                    prominence_score=prominence
                ))
            
            # Check lower wick
            if body_size > 0 and lower_wick / body_size >= self.wick_prominence_threshold:
                prominence = min(1.0, lower_wick / body_size / 5)
                prominent_wicks.append(ProminentWick(
                    index=i,
                    price=bar["low"],
                    is_upper=False,
                    wick_size=lower_wick,
                    body_size=body_size,
                    prominence_score=prominence
                ))
        
        # Sort by prominence score
        prominent_wicks.sort(key=lambda x: x.prominence_score, reverse=True)
        return prominent_wicks[:10]  # Return top 10
    
    def _find_nearest_wick_target(
        self,
        current_price: float,
        prominent_wicks: List[ProminentWick],
        direction: SwingDirection
    ) -> Optional[float]:
        """Find the nearest prominent wick to target"""
        if not prominent_wicks:
            return None
        
        if direction == SwingDirection.UP:
            # Look for upper wicks above current price
            targets = [w.price for w in prominent_wicks if w.is_upper and w.price > current_price]
        elif direction == SwingDirection.DOWN:
            # Look for lower wicks below current price
            targets = [w.price for w in prominent_wicks if not w.is_upper and w.price < current_price]
        else:
            return None
        
        if not targets:
            return None
        
        # Return nearest target
        return min(targets, key=lambda x: abs(x - current_price))
    
    def _detect_liquidity_sweeps(
        self,
        bars: List[Dict[str, Any]],
        swings: List[SwingPoint]
    ) -> List[LiquiditySweep]:
        """
        Detect liquidity sweeps - price taking out a level then reversing
        
        "If you can't see the sweep, you are the sweep"
        """
        sweeps = []
        
        if len(bars) < 5 or len(swings) < 2:
            return sweeps
        
        # Look for sweeps of recent swing highs/lows
        for i in range(len(bars) - 3, max(0, len(bars) - 20), -1):
            bar = bars[i]
            next_bar = bars[i + 1] if i + 1 < len(bars) else None
            
            if not next_bar:
                continue
            
            # Find swing levels that could have been swept
            for swing in swings:
                if swing.index >= i:
                    continue
                
                # Check for sweep of swing high
                if swing.is_high:
                    if bar["high"] > swing.price and next_bar["close"] < swing.price:
                        # Swept high and reversed
                        sweeps.append(LiquiditySweep(
                            sweep_type=SweepType.SWEEP_HIGH,
                            index=i,
                            sweep_price=swing.price,
                            reversal_price=next_bar["close"],
                            strength=min(1.0, (bar["high"] - swing.price) / (swing.price * self.sweep_threshold)),
                            confirmed=True
                        ))
                
                # Check for sweep of swing low
                else:
                    if bar["low"] < swing.price and next_bar["close"] > swing.price:
                        # Swept low and reversed
                        sweeps.append(LiquiditySweep(
                            sweep_type=SweepType.SWEEP_LOW,
                            index=i,
                            sweep_price=swing.price,
                            reversal_price=next_bar["close"],
                            strength=min(1.0, (swing.price - bar["low"]) / (swing.price * self.sweep_threshold)),
                            confirmed=True
                        ))
        
        return sweeps
    
    def _detect_rounding_pattern(
        self,
        bars: List[Dict[str, Any]],
        swings: List[SwingPoint]
    ) -> Optional[RoundingPattern]:
        """
        Detect rounding patterns (cup or inverse cup)
        
        Cup: Price rounds at bottom before moving up
        Inverse Cup: Price rounds at top before moving down
        """
        if len(bars) < 20:
            return None
        
        # Look at recent price action
        recent_bars = bars[-30:] if len(bars) >= 30 else bars
        
        # Calculate price curve
        closes = [b["close"] for b in recent_bars]
        highs = [b["high"] for b in recent_bars]
        lows = [b["low"] for b in recent_bars]
        
        # Find apex (lowest for cup, highest for inverse cup)
        min_idx = lows.index(min(lows))
        max_idx = highs.index(max(highs))
        
        # Check for cup pattern (rounding bottom)
        if min_idx > 5 and min_idx < len(recent_bars) - 5:
            # Check if prices curve around the low
            left_slope = (closes[min_idx] - closes[0]) / (min_idx + 1)
            right_slope = (closes[-1] - closes[min_idx]) / (len(closes) - min_idx)
            
            if left_slope < 0 and right_slope > 0:
                # Cup pattern detected
                strength = min(1.0, abs(right_slope / left_slope))
                return RoundingPattern(
                    pattern_type=RoundingType.CUP,
                    start_index=len(bars) - len(recent_bars),
                    end_index=len(bars) - 1,
                    apex_index=len(bars) - len(recent_bars) + min_idx,
                    apex_price=lows[min_idx],
                    strength=strength,
                    confirmed=strength > 0.5
                )
        
        # Check for inverse cup pattern (rounding top)
        if max_idx > 5 and max_idx < len(recent_bars) - 5:
            # Check if prices curve around the high
            left_slope = (closes[max_idx] - closes[0]) / (max_idx + 1)
            right_slope = (closes[-1] - closes[max_idx]) / (len(closes) - max_idx)
            
            if left_slope > 0 and right_slope < 0:
                # Inverse cup pattern detected
                strength = min(1.0, abs(right_slope / left_slope))
                return RoundingPattern(
                    pattern_type=RoundingType.INVERSE_CUP,
                    start_index=len(bars) - len(recent_bars),
                    end_index=len(bars) - 1,
                    apex_index=len(bars) - len(recent_bars) + max_idx,
                    apex_price=highs[max_idx],
                    strength=strength,
                    confirmed=strength > 0.5
                )
        
        return None
    
    def _calculate_ema(self, bars: List[Dict[str, Any]], period: int) -> float:
        """Calculate Exponential Moving Average"""
        if len(bars) < period:
            return bars[-1]["close"] if bars else 0
        
        multiplier = 2 / (period + 1)
        ema = sum(b["close"] for b in bars[:period]) / period
        
        for bar in bars[period:]:
            ema = (bar["close"] - ema) * multiplier + ema
        
        return ema
    
    def _calculate_ema_slope(self, bars: List[Dict[str, Any]], period: int) -> str:
        """Calculate EMA slope direction"""
        if len(bars) < period + 5:
            return "flat"
        
        current_ema = self._calculate_ema(bars, period)
        prev_ema = self._calculate_ema(bars[:-5], period)
        
        slope = (current_ema - prev_ema) / prev_ema if prev_ema != 0 else 0
        
        if slope > 0.001:
            return "up"
        elif slope < -0.001:
            return "down"
        return "flat"
    
    def _generate_signal(
        self,
        swing_count: int,
        swing_direction: SwingDirection,
        ready_for_reversal: bool,
        in_retracement_zone: bool,
        sweep_confirmed: bool,
        rounding_pattern: Optional[RoundingPattern],
        price_above_ema: bool,
        ema_slope: str
    ) -> Tuple[str, float, float]:
        """
        Generate trade signal based on all factors
        
        Returns:
            (signal, strength, confidence)
        """
        score = 0.0
        factors = 0
        
        # Factor 1: Swing count (4-6 swings ready for reversal)
        if ready_for_reversal:
            if swing_direction == SwingDirection.UP:
                score -= 0.3  # Ready for bearish reversal
            elif swing_direction == SwingDirection.DOWN:
                score += 0.3  # Ready for bullish reversal
            factors += 1
        
        # Factor 2: Retracement zone
        if in_retracement_zone:
            if swing_direction == SwingDirection.UP:
                score += 0.2  # Pullback in uptrend = bullish
            elif swing_direction == SwingDirection.DOWN:
                score -= 0.2  # Pullback in downtrend = bearish
            factors += 1
        
        # Factor 3: Liquidity sweep confirmed
        if sweep_confirmed:
            # Sweep confirms reversal
            if swing_direction == SwingDirection.UP:
                score -= 0.25  # Swept high = bearish
            elif swing_direction == SwingDirection.DOWN:
                score += 0.25  # Swept low = bullish
            factors += 1
        
        # Factor 4: Rounding pattern
        if rounding_pattern and rounding_pattern.confirmed:
            if rounding_pattern.pattern_type == RoundingType.CUP:
                score += 0.2 * rounding_pattern.strength
            elif rounding_pattern.pattern_type == RoundingType.INVERSE_CUP:
                score -= 0.2 * rounding_pattern.strength
            factors += 1
        
        # Factor 5: EMA alignment
        if ema_slope == "up" and price_above_ema:
            score += 0.15
        elif ema_slope == "down" and not price_above_ema:
            score -= 0.15
        factors += 1
        
        # Determine signal
        if score > 0.3:
            signal = "LONG"
        elif score < -0.3:
            signal = "SHORT"
        else:
            signal = "NEUTRAL"
        
        # Calculate strength and confidence
        strength = min(1.0, abs(score))
        confidence = min(1.0, factors / 5) * strength
        
        return signal, strength, confidence
    
    def _calculate_levels(
        self,
        bars: List[Dict[str, Any]],
        signal: str,
        previous_range: Optional[PreviousRange],
        prominent_wicks: List[ProminentWick],
        ema_21: float,
        swings: List[SwingPoint]
    ) -> Tuple[float, float, float, float]:
        """
        Calculate entry, stop loss, take profit, and trailing stop
        
        Returns:
            (entry_price, stop_loss, take_profit, trailing_stop)
        """
        current_price = bars[-1]["close"]
        
        if signal == "NEUTRAL":
            return current_price, current_price, current_price, ema_21
        
        # Entry at current price or retracement level
        entry_price = current_price
        if previous_range:
            if signal == "LONG":
                # Enter at 50% or 70% retracement
                if current_price > previous_range.level_50:
                    entry_price = previous_range.level_50
                elif current_price > previous_range.level_70:
                    entry_price = previous_range.level_70
            else:
                # Enter at 50% or 30% retracement
                if current_price < previous_range.level_50:
                    entry_price = previous_range.level_50
                elif current_price < previous_range.level_30:
                    entry_price = previous_range.level_30
        
        # Stop loss below/above recent swing
        recent_lows = [s.price for s in swings if not s.is_high][-3:]
        recent_highs = [s.price for s in swings if s.is_high][-3:]
        
        if signal == "LONG":
            stop_loss = min(recent_lows) if recent_lows else current_price * 0.995
            # Take profit at prominent wick or previous range high
            if prominent_wicks:
                upper_wicks = [w.price for w in prominent_wicks if w.is_upper and w.price > current_price]
                take_profit = min(upper_wicks) if upper_wicks else (previous_range.high if previous_range else current_price * 1.01)
            else:
                take_profit = previous_range.high if previous_range else current_price * 1.01
        else:
            stop_loss = max(recent_highs) if recent_highs else current_price * 1.005
            # Take profit at prominent wick or previous range low
            if prominent_wicks:
                lower_wicks = [w.price for w in prominent_wicks if not w.is_upper and w.price < current_price]
                take_profit = max(lower_wicks) if lower_wicks else (previous_range.low if previous_range else current_price * 0.99)
            else:
                take_profit = previous_range.low if previous_range else current_price * 0.99
        
        # Trailing stop at 21 EMA
        trailing_stop = ema_21
        
        return entry_price, stop_loss, take_profit, trailing_stop
    
    def _empty_analysis(self) -> FractalSwingAnalysis:
        """Return empty analysis when insufficient data"""
        return FractalSwingAnalysis(
            swing_count=0,
            swings=[],
            swing_direction=SwingDirection.NEUTRAL,
            ready_for_reversal=False,
            previous_range=None,
            in_retracement_zone=False,
            retracement_level="none",
            prominent_wicks=[],
            nearest_wick_target=None,
            recent_sweeps=[],
            sweep_confirmed=False,
            rounding_pattern=None,
            ema_21=0,
            price_above_ema=False,
            ema_slope="flat",
            signal="NEUTRAL",
            signal_strength=0,
            confidence=0,
            reasoning=["Insufficient data for analysis"],
            entry_price=0,
            stop_loss=0,
            take_profit=0,
            trailing_stop=0
        )


def test_fractal_swing_intelligence():
    """Test the Fractal Swing Intelligence module"""
    # Generate sample data with swings
    import random
    random.seed(42)
    
    bars = []
    price = 1.1000
    
    for i in range(200):
        # Create swinging price action
        if i % 20 < 10:
            price += random.uniform(0.0001, 0.0010)
        else:
            price -= random.uniform(0.0001, 0.0010)
        
        high = price + random.uniform(0.0005, 0.0020)
        low = price - random.uniform(0.0005, 0.0020)
        open_price = price + random.uniform(-0.0005, 0.0005)
        close = price + random.uniform(-0.0005, 0.0005)
        
        bars.append({
            "open": open_price,
            "high": high,
            "low": low,
            "close": close,
            "volume": random.uniform(1000, 5000)
        })
    
    # Run analysis
    intelligence = FractalSwingIntelligence()
    analysis = intelligence.analyze(bars)
    
    print("=" * 60)
    print("FRACTAL SWING INTELLIGENCE TEST")
    print("=" * 60)
    print(f"Swing Count: {analysis.swing_count}")
    print(f"Swing Direction: {analysis.swing_direction.value}")
    print(f"Ready for Reversal: {analysis.ready_for_reversal}")
    print(f"In Retracement Zone: {analysis.in_retracement_zone} ({analysis.retracement_level})")
    print(f"Sweep Confirmed: {analysis.sweep_confirmed}")
    print(f"21 EMA: {analysis.ema_21:.5f}")
    print(f"EMA Slope: {analysis.ema_slope}")
    print(f"Signal: {analysis.signal}")
    print(f"Signal Strength: {analysis.signal_strength:.2%}")
    print(f"Confidence: {analysis.confidence:.2%}")
    print("\nReasoning:")
    for r in analysis.reasoning:
        print(f"  - {r}")
    print(f"\nEntry: {analysis.entry_price:.5f}")
    print(f"Stop Loss: {analysis.stop_loss:.5f}")
    print(f"Take Profit: {analysis.take_profit:.5f}")
    print(f"Trailing Stop (21 EMA): {analysis.trailing_stop:.5f}")
    
    return analysis


if __name__ == "__main__":
    test_fractal_swing_intelligence()
