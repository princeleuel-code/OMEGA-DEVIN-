"""
Smart Money Concepts (SMC) Intelligence Module

This module implements institutional-grade Smart Money Concepts analysis:
1. Order Blocks (OB) - Areas where institutions placed large orders
2. Fair Value Gaps (FVG) - Imbalances in price that tend to get filled
3. Liquidity Pools - Equal highs/lows where stop losses cluster
4. Break of Structure (BOS) - Trend continuation signals
5. Change of Character (CHoCH) - Trend reversal signals
6. Premium/Discount Zones - Fibonacci-based value areas
7. Mitigation Blocks - Order blocks that have been partially filled
8. Breaker Blocks - Failed order blocks that become support/resistance

This is what the BEST institutional traders use - not retail indicators.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple, Any
from enum import Enum
import math


class StructureType(Enum):
    """Market structure types"""
    BULLISH = "bullish"
    BEARISH = "bearish"
    NEUTRAL = "neutral"


class ZoneType(Enum):
    """SMC zone types"""
    ORDER_BLOCK_BULLISH = "order_block_bullish"
    ORDER_BLOCK_BEARISH = "order_block_bearish"
    FVG_BULLISH = "fvg_bullish"
    FVG_BEARISH = "fvg_bearish"
    LIQUIDITY_HIGH = "liquidity_high"
    LIQUIDITY_LOW = "liquidity_low"
    BREAKER_BULLISH = "breaker_bullish"
    BREAKER_BEARISH = "breaker_bearish"
    MITIGATION_BULLISH = "mitigation_bullish"
    MITIGATION_BEARISH = "mitigation_bearish"


class StructureBreak(Enum):
    """Structure break types"""
    BOS_BULLISH = "bos_bullish"  # Break of Structure - continuation
    BOS_BEARISH = "bos_bearish"
    CHOCH_BULLISH = "choch_bullish"  # Change of Character - reversal
    CHOCH_BEARISH = "choch_bearish"


@dataclass
class SwingPoint:
    """Represents a swing high or swing low"""
    index: int
    price: float
    is_high: bool
    strength: int  # Number of bars on each side that confirm this swing
    timestamp: Optional[str] = None
    
    @property
    def type_str(self) -> str:
        return "swing_high" if self.is_high else "swing_low"


@dataclass
class SMCZone:
    """Represents an SMC zone (order block, FVG, liquidity, etc.)"""
    zone_type: ZoneType
    top: float
    bottom: float
    start_index: int
    end_index: Optional[int] = None
    strength: float = 1.0  # 0-1 strength score
    mitigated: bool = False
    mitigation_percent: float = 0.0
    volume: float = 0.0
    touches: int = 0
    
    @property
    def midpoint(self) -> float:
        return (self.top + self.bottom) / 2
    
    @property
    def size(self) -> float:
        return self.top - self.bottom
    
    def contains_price(self, price: float) -> bool:
        return self.bottom <= price <= self.top
    
    def distance_to_price(self, price: float) -> float:
        if price > self.top:
            return price - self.top
        elif price < self.bottom:
            return self.bottom - price
        return 0.0


@dataclass
class StructureBreakEvent:
    """Represents a break of structure or change of character"""
    break_type: StructureBreak
    index: int
    price: float
    broken_level: float
    strength: float = 1.0
    confirmed: bool = False
    
    @property
    def is_bullish(self) -> bool:
        return self.break_type in [StructureBreak.BOS_BULLISH, StructureBreak.CHOCH_BULLISH]
    
    @property
    def is_reversal(self) -> bool:
        return self.break_type in [StructureBreak.CHOCH_BULLISH, StructureBreak.CHOCH_BEARISH]


@dataclass
class SMCAnalysis:
    """Complete SMC analysis result"""
    structure: StructureType
    swing_highs: List[SwingPoint]
    swing_lows: List[SwingPoint]
    order_blocks: List[SMCZone]
    fair_value_gaps: List[SMCZone]
    liquidity_pools: List[SMCZone]
    breaker_blocks: List[SMCZone]
    structure_breaks: List[StructureBreakEvent]
    premium_zone: Tuple[float, float]  # (top, bottom)
    discount_zone: Tuple[float, float]  # (top, bottom)
    equilibrium: float
    bias: StructureType
    bias_strength: float
    nearest_demand: Optional[SMCZone] = None
    nearest_supply: Optional[SMCZone] = None
    active_fvg: Optional[SMCZone] = None
    
    def get_all_zones(self) -> List[SMCZone]:
        """Get all SMC zones combined"""
        return self.order_blocks + self.fair_value_gaps + self.liquidity_pools + self.breaker_blocks
    
    def get_bullish_zones(self) -> List[SMCZone]:
        """Get all bullish zones (demand)"""
        bullish_types = [
            ZoneType.ORDER_BLOCK_BULLISH,
            ZoneType.FVG_BULLISH,
            ZoneType.BREAKER_BULLISH,
            ZoneType.MITIGATION_BULLISH
        ]
        return [z for z in self.get_all_zones() if z.zone_type in bullish_types and not z.mitigated]
    
    def get_bearish_zones(self) -> List[SMCZone]:
        """Get all bearish zones (supply)"""
        bearish_types = [
            ZoneType.ORDER_BLOCK_BEARISH,
            ZoneType.FVG_BEARISH,
            ZoneType.BREAKER_BEARISH,
            ZoneType.MITIGATION_BEARISH
        ]
        return [z for z in self.get_all_zones() if z.zone_type in bearish_types and not z.mitigated]


class SMCIntelligence:
    """
    Smart Money Concepts Intelligence Engine
    
    Implements institutional-grade market structure analysis used by
    the world's best traders. This is NOT retail technical analysis -
    this is how smart money actually trades.
    """
    
    def __init__(
        self,
        swing_strength: int = 3,
        fvg_min_size_atr: float = 0.5,
        ob_lookback: int = 50,
        liquidity_equal_threshold: float = 0.0005,
        structure_confirmation_bars: int = 2
    ):
        """
        Initialize SMC Intelligence
        
        Args:
            swing_strength: Number of bars on each side to confirm swing
            fvg_min_size_atr: Minimum FVG size as multiple of ATR
            ob_lookback: Lookback period for order block detection
            liquidity_equal_threshold: Threshold for equal highs/lows (as % of price)
            structure_confirmation_bars: Bars needed to confirm structure break
        """
        self.swing_strength = swing_strength
        self.fvg_min_size_atr = fvg_min_size_atr
        self.ob_lookback = ob_lookback
        self.liquidity_equal_threshold = liquidity_equal_threshold
        self.structure_confirmation_bars = structure_confirmation_bars
    
    def analyze(self, bars: List[Dict[str, Any]]) -> SMCAnalysis:
        """
        Perform complete SMC analysis on price data
        
        Args:
            bars: List of OHLCV bars with keys: open, high, low, close, volume
            
        Returns:
            SMCAnalysis with all detected patterns and zones
        """
        if len(bars) < self.swing_strength * 2 + 1:
            return self._empty_analysis()
        
        # Step 1: Identify swing points
        swing_highs = self._find_swing_highs(bars)
        swing_lows = self._find_swing_lows(bars)
        
        # Step 2: Determine market structure
        structure, structure_breaks = self._analyze_structure(bars, swing_highs, swing_lows)
        
        # Step 3: Find order blocks
        order_blocks = self._find_order_blocks(bars, swing_highs, swing_lows, structure_breaks)
        
        # Step 4: Find fair value gaps
        atr = self._calculate_atr(bars)
        fair_value_gaps = self._find_fair_value_gaps(bars, atr)
        
        # Step 5: Find liquidity pools
        liquidity_pools = self._find_liquidity_pools(bars, swing_highs, swing_lows)
        
        # Step 6: Find breaker blocks (failed order blocks)
        breaker_blocks = self._find_breaker_blocks(bars, order_blocks)
        
        # Step 7: Calculate premium/discount zones
        premium_zone, discount_zone, equilibrium = self._calculate_premium_discount(bars, swing_highs, swing_lows)
        
        # Step 8: Determine bias
        bias, bias_strength = self._determine_bias(
            bars, structure, structure_breaks, order_blocks, fair_value_gaps
        )
        
        # Step 9: Find nearest zones to current price
        current_price = bars[-1]["close"]
        nearest_demand = self._find_nearest_zone(current_price, order_blocks + fair_value_gaps, bullish=True)
        nearest_supply = self._find_nearest_zone(current_price, order_blocks + fair_value_gaps, bullish=False)
        
        # Step 10: Find active FVG (price is inside)
        active_fvg = self._find_active_fvg(current_price, fair_value_gaps)
        
        # Update zone mitigation status
        self._update_mitigation_status(bars, order_blocks)
        self._update_mitigation_status(bars, fair_value_gaps)
        
        return SMCAnalysis(
            structure=structure,
            swing_highs=swing_highs,
            swing_lows=swing_lows,
            order_blocks=order_blocks,
            fair_value_gaps=fair_value_gaps,
            liquidity_pools=liquidity_pools,
            breaker_blocks=breaker_blocks,
            structure_breaks=structure_breaks,
            premium_zone=premium_zone,
            discount_zone=discount_zone,
            equilibrium=equilibrium,
            bias=bias,
            bias_strength=bias_strength,
            nearest_demand=nearest_demand,
            nearest_supply=nearest_supply,
            active_fvg=active_fvg
        )
    
    def _find_swing_highs(self, bars: List[Dict[str, Any]]) -> List[SwingPoint]:
        """Find all swing highs in the data"""
        swing_highs = []
        n = len(bars)
        
        for i in range(self.swing_strength, n - self.swing_strength):
            high = bars[i]["high"]
            is_swing = True
            
            # Check left side
            for j in range(1, self.swing_strength + 1):
                if bars[i - j]["high"] >= high:
                    is_swing = False
                    break
            
            # Check right side
            if is_swing:
                for j in range(1, self.swing_strength + 1):
                    if bars[i + j]["high"] >= high:
                        is_swing = False
                        break
            
            if is_swing:
                swing_highs.append(SwingPoint(
                    index=i,
                    price=high,
                    is_high=True,
                    strength=self.swing_strength,
                    timestamp=bars[i].get("timestamp")
                ))
        
        return swing_highs
    
    def _find_swing_lows(self, bars: List[Dict[str, Any]]) -> List[SwingPoint]:
        """Find all swing lows in the data"""
        swing_lows = []
        n = len(bars)
        
        for i in range(self.swing_strength, n - self.swing_strength):
            low = bars[i]["low"]
            is_swing = True
            
            # Check left side
            for j in range(1, self.swing_strength + 1):
                if bars[i - j]["low"] <= low:
                    is_swing = False
                    break
            
            # Check right side
            if is_swing:
                for j in range(1, self.swing_strength + 1):
                    if bars[i + j]["low"] <= low:
                        is_swing = False
                        break
            
            if is_swing:
                swing_lows.append(SwingPoint(
                    index=i,
                    price=low,
                    is_high=False,
                    strength=self.swing_strength,
                    timestamp=bars[i].get("timestamp")
                ))
        
        return swing_lows
    
    def _analyze_structure(
        self,
        bars: List[Dict[str, Any]],
        swing_highs: List[SwingPoint],
        swing_lows: List[SwingPoint]
    ) -> Tuple[StructureType, List[StructureBreakEvent]]:
        """Analyze market structure and detect BOS/CHoCH"""
        structure_breaks = []
        
        if len(swing_highs) < 2 or len(swing_lows) < 2:
            return StructureType.NEUTRAL, structure_breaks
        
        # Combine and sort swings by index
        all_swings = sorted(swing_highs + swing_lows, key=lambda x: x.index)
        
        # Track structure
        last_higher_high = None
        last_higher_low = None
        last_lower_high = None
        last_lower_low = None
        
        current_structure = StructureType.NEUTRAL
        
        for i in range(1, len(all_swings)):
            swing = all_swings[i]
            prev_same_type = None
            
            # Find previous swing of same type
            for j in range(i - 1, -1, -1):
                if all_swings[j].is_high == swing.is_high:
                    prev_same_type = all_swings[j]
                    break
            
            if prev_same_type is None:
                continue
            
            if swing.is_high:
                # Analyzing highs
                if swing.price > prev_same_type.price:
                    # Higher high
                    last_higher_high = swing
                    if current_structure == StructureType.BEARISH:
                        # CHoCH - Change of Character (reversal)
                        structure_breaks.append(StructureBreakEvent(
                            break_type=StructureBreak.CHOCH_BULLISH,
                            index=swing.index,
                            price=swing.price,
                            broken_level=prev_same_type.price,
                            strength=0.8,
                            confirmed=True
                        ))
                        current_structure = StructureType.BULLISH
                    elif current_structure == StructureType.BULLISH:
                        # BOS - Break of Structure (continuation)
                        structure_breaks.append(StructureBreakEvent(
                            break_type=StructureBreak.BOS_BULLISH,
                            index=swing.index,
                            price=swing.price,
                            broken_level=prev_same_type.price,
                            strength=0.6,
                            confirmed=True
                        ))
                else:
                    # Lower high
                    last_lower_high = swing
            else:
                # Analyzing lows
                if swing.price < prev_same_type.price:
                    # Lower low
                    last_lower_low = swing
                    if current_structure == StructureType.BULLISH:
                        # CHoCH - Change of Character (reversal)
                        structure_breaks.append(StructureBreakEvent(
                            break_type=StructureBreak.CHOCH_BEARISH,
                            index=swing.index,
                            price=swing.price,
                            broken_level=prev_same_type.price,
                            strength=0.8,
                            confirmed=True
                        ))
                        current_structure = StructureType.BEARISH
                    elif current_structure == StructureType.BEARISH:
                        # BOS - Break of Structure (continuation)
                        structure_breaks.append(StructureBreakEvent(
                            break_type=StructureBreak.BOS_BEARISH,
                            index=swing.index,
                            price=swing.price,
                            broken_level=prev_same_type.price,
                            strength=0.6,
                            confirmed=True
                        ))
                else:
                    # Higher low
                    last_higher_low = swing
        
        # Determine final structure based on recent swings
        if len(swing_highs) >= 2 and len(swing_lows) >= 2:
            recent_highs = swing_highs[-2:]
            recent_lows = swing_lows[-2:]
            
            hh = recent_highs[-1].price > recent_highs[-2].price
            hl = recent_lows[-1].price > recent_lows[-2].price
            lh = recent_highs[-1].price < recent_highs[-2].price
            ll = recent_lows[-1].price < recent_lows[-2].price
            
            if hh and hl:
                current_structure = StructureType.BULLISH
            elif lh and ll:
                current_structure = StructureType.BEARISH
            else:
                current_structure = StructureType.NEUTRAL
        
        return current_structure, structure_breaks
    
    def _find_order_blocks(
        self,
        bars: List[Dict[str, Any]],
        swing_highs: List[SwingPoint],
        swing_lows: List[SwingPoint],
        structure_breaks: List[StructureBreakEvent]
    ) -> List[SMCZone]:
        """
        Find order blocks - areas where institutions placed large orders
        
        Bullish OB: Last bearish candle before a strong bullish move
        Bearish OB: Last bullish candle before a strong bearish move
        """
        order_blocks = []
        n = len(bars)
        
        # Find bullish order blocks (demand zones)
        for swing in swing_lows:
            if swing.index < 1 or swing.index >= n - 3:
                continue
            
            # Look for the last bearish candle before the swing low
            ob_index = None
            for i in range(swing.index, max(0, swing.index - 5), -1):
                if bars[i]["close"] < bars[i]["open"]:  # Bearish candle
                    ob_index = i
                    break
            
            if ob_index is not None:
                # Check if there was a strong move after
                move_strength = 0
                for i in range(swing.index + 1, min(n, swing.index + 5)):
                    move_strength += (bars[i]["close"] - bars[i]["open"]) / (bars[i]["high"] - bars[i]["low"] + 0.0001)
                
                if move_strength > 1.5:  # Strong bullish move
                    ob = SMCZone(
                        zone_type=ZoneType.ORDER_BLOCK_BULLISH,
                        top=bars[ob_index]["open"],
                        bottom=bars[ob_index]["low"],
                        start_index=ob_index,
                        strength=min(1.0, move_strength / 3),
                        volume=bars[ob_index].get("volume", 0)
                    )
                    order_blocks.append(ob)
        
        # Find bearish order blocks (supply zones)
        for swing in swing_highs:
            if swing.index < 1 or swing.index >= n - 3:
                continue
            
            # Look for the last bullish candle before the swing high
            ob_index = None
            for i in range(swing.index, max(0, swing.index - 5), -1):
                if bars[i]["close"] > bars[i]["open"]:  # Bullish candle
                    ob_index = i
                    break
            
            if ob_index is not None:
                # Check if there was a strong move after
                move_strength = 0
                for i in range(swing.index + 1, min(n, swing.index + 5)):
                    move_strength += (bars[i]["open"] - bars[i]["close"]) / (bars[i]["high"] - bars[i]["low"] + 0.0001)
                
                if move_strength > 1.5:  # Strong bearish move
                    ob = SMCZone(
                        zone_type=ZoneType.ORDER_BLOCK_BEARISH,
                        top=bars[ob_index]["high"],
                        bottom=bars[ob_index]["open"],
                        start_index=ob_index,
                        strength=min(1.0, move_strength / 3),
                        volume=bars[ob_index].get("volume", 0)
                    )
                    order_blocks.append(ob)
        
        return order_blocks
    
    def _find_fair_value_gaps(self, bars: List[Dict[str, Any]], atr: float) -> List[SMCZone]:
        """
        Find Fair Value Gaps (FVG) - imbalances in price
        
        Bullish FVG: Gap between candle 1 high and candle 3 low (price moved up fast)
        Bearish FVG: Gap between candle 1 low and candle 3 high (price moved down fast)
        """
        fvgs = []
        min_size = atr * self.fvg_min_size_atr
        
        for i in range(2, len(bars)):
            candle1 = bars[i - 2]
            candle2 = bars[i - 1]
            candle3 = bars[i]
            
            # Bullish FVG: candle 3 low > candle 1 high
            if candle3["low"] > candle1["high"]:
                gap_size = candle3["low"] - candle1["high"]
                if gap_size >= min_size:
                    fvg = SMCZone(
                        zone_type=ZoneType.FVG_BULLISH,
                        top=candle3["low"],
                        bottom=candle1["high"],
                        start_index=i - 1,
                        strength=min(1.0, gap_size / (atr * 2)),
                        volume=candle2.get("volume", 0)
                    )
                    fvgs.append(fvg)
            
            # Bearish FVG: candle 3 high < candle 1 low
            if candle3["high"] < candle1["low"]:
                gap_size = candle1["low"] - candle3["high"]
                if gap_size >= min_size:
                    fvg = SMCZone(
                        zone_type=ZoneType.FVG_BEARISH,
                        top=candle1["low"],
                        bottom=candle3["high"],
                        start_index=i - 1,
                        strength=min(1.0, gap_size / (atr * 2)),
                        volume=candle2.get("volume", 0)
                    )
                    fvgs.append(fvg)
        
        return fvgs
    
    def _find_liquidity_pools(
        self,
        bars: List[Dict[str, Any]],
        swing_highs: List[SwingPoint],
        swing_lows: List[SwingPoint]
    ) -> List[SMCZone]:
        """
        Find liquidity pools - equal highs/lows where stop losses cluster
        
        These are areas where retail traders place their stops, and smart money
        hunts these levels to fill their large orders.
        """
        liquidity_pools = []
        
        # Find equal highs (buy-side liquidity)
        for i in range(len(swing_highs)):
            for j in range(i + 1, len(swing_highs)):
                high1 = swing_highs[i].price
                high2 = swing_highs[j].price
                avg_price = (high1 + high2) / 2
                
                # Check if highs are approximately equal
                if abs(high1 - high2) / avg_price < self.liquidity_equal_threshold:
                    # Count how many times this level was tested
                    touches = 2
                    for k in range(len(swing_highs)):
                        if k != i and k != j:
                            if abs(swing_highs[k].price - avg_price) / avg_price < self.liquidity_equal_threshold:
                                touches += 1
                    
                    pool = SMCZone(
                        zone_type=ZoneType.LIQUIDITY_HIGH,
                        top=max(high1, high2) * 1.001,  # Slightly above
                        bottom=min(high1, high2),
                        start_index=swing_highs[i].index,
                        end_index=swing_highs[j].index,
                        strength=min(1.0, touches / 4),
                        touches=touches
                    )
                    liquidity_pools.append(pool)
        
        # Find equal lows (sell-side liquidity)
        for i in range(len(swing_lows)):
            for j in range(i + 1, len(swing_lows)):
                low1 = swing_lows[i].price
                low2 = swing_lows[j].price
                avg_price = (low1 + low2) / 2
                
                # Check if lows are approximately equal
                if abs(low1 - low2) / avg_price < self.liquidity_equal_threshold:
                    # Count how many times this level was tested
                    touches = 2
                    for k in range(len(swing_lows)):
                        if k != i and k != j:
                            if abs(swing_lows[k].price - avg_price) / avg_price < self.liquidity_equal_threshold:
                                touches += 1
                    
                    pool = SMCZone(
                        zone_type=ZoneType.LIQUIDITY_LOW,
                        top=max(low1, low2),
                        bottom=min(low1, low2) * 0.999,  # Slightly below
                        start_index=swing_lows[i].index,
                        end_index=swing_lows[j].index,
                        strength=min(1.0, touches / 4),
                        touches=touches
                    )
                    liquidity_pools.append(pool)
        
        return liquidity_pools
    
    def _find_breaker_blocks(
        self,
        bars: List[Dict[str, Any]],
        order_blocks: List[SMCZone]
    ) -> List[SMCZone]:
        """
        Find breaker blocks - order blocks that failed and became opposite zones
        
        When a bullish OB fails (price breaks below), it becomes bearish resistance
        When a bearish OB fails (price breaks above), it becomes bullish support
        """
        breaker_blocks = []
        
        for ob in order_blocks:
            if ob.start_index >= len(bars) - 5:
                continue
            
            # Check if order block was broken
            broken = False
            break_index = None
            
            for i in range(ob.start_index + 1, len(bars)):
                if ob.zone_type == ZoneType.ORDER_BLOCK_BULLISH:
                    # Bullish OB broken if price closes below bottom
                    if bars[i]["close"] < ob.bottom:
                        broken = True
                        break_index = i
                        break
                else:
                    # Bearish OB broken if price closes above top
                    if bars[i]["close"] > ob.top:
                        broken = True
                        break_index = i
                        break
            
            if broken and break_index is not None:
                # Create breaker block (opposite type)
                if ob.zone_type == ZoneType.ORDER_BLOCK_BULLISH:
                    breaker = SMCZone(
                        zone_type=ZoneType.BREAKER_BEARISH,
                        top=ob.top,
                        bottom=ob.bottom,
                        start_index=ob.start_index,
                        end_index=break_index,
                        strength=ob.strength * 0.8
                    )
                else:
                    breaker = SMCZone(
                        zone_type=ZoneType.BREAKER_BULLISH,
                        top=ob.top,
                        bottom=ob.bottom,
                        start_index=ob.start_index,
                        end_index=break_index,
                        strength=ob.strength * 0.8
                    )
                breaker_blocks.append(breaker)
        
        return breaker_blocks
    
    def _calculate_premium_discount(
        self,
        bars: List[Dict[str, Any]],
        swing_highs: List[SwingPoint],
        swing_lows: List[SwingPoint]
    ) -> Tuple[Tuple[float, float], Tuple[float, float], float]:
        """
        Calculate premium and discount zones using Fibonacci levels
        
        Premium zone: 0.5 - 1.0 (above equilibrium - expensive)
        Discount zone: 0.0 - 0.5 (below equilibrium - cheap)
        """
        if not swing_highs or not swing_lows:
            current_price = bars[-1]["close"]
            return (current_price, current_price), (current_price, current_price), current_price
        
        # Use recent swing range
        recent_high = max(sh.price for sh in swing_highs[-5:]) if swing_highs else bars[-1]["high"]
        recent_low = min(sl.price for sl in swing_lows[-5:]) if swing_lows else bars[-1]["low"]
        
        range_size = recent_high - recent_low
        equilibrium = recent_low + range_size * 0.5
        
        # Premium zone: 0.5 to 1.0 of range
        premium_zone = (recent_high, equilibrium)
        
        # Discount zone: 0.0 to 0.5 of range
        discount_zone = (equilibrium, recent_low)
        
        return premium_zone, discount_zone, equilibrium
    
    def _determine_bias(
        self,
        bars: List[Dict[str, Any]],
        structure: StructureType,
        structure_breaks: List[StructureBreakEvent],
        order_blocks: List[SMCZone],
        fvgs: List[SMCZone]
    ) -> Tuple[StructureType, float]:
        """
        Determine overall market bias and strength
        
        Combines structure, recent breaks, and zone analysis
        """
        bias_score = 0.0
        
        # Structure contribution (40%)
        if structure == StructureType.BULLISH:
            bias_score += 0.4
        elif structure == StructureType.BEARISH:
            bias_score -= 0.4
        
        # Recent structure breaks contribution (30%)
        recent_breaks = [b for b in structure_breaks if b.index > len(bars) - 20]
        for brk in recent_breaks:
            if brk.is_bullish:
                bias_score += 0.15 * brk.strength
            else:
                bias_score -= 0.15 * brk.strength
        
        # Unmitigated zones contribution (30%)
        bullish_zones = [z for z in order_blocks + fvgs 
                       if z.zone_type in [ZoneType.ORDER_BLOCK_BULLISH, ZoneType.FVG_BULLISH] 
                       and not z.mitigated]
        bearish_zones = [z for z in order_blocks + fvgs 
                        if z.zone_type in [ZoneType.ORDER_BLOCK_BEARISH, ZoneType.FVG_BEARISH] 
                        and not z.mitigated]
        
        zone_diff = len(bullish_zones) - len(bearish_zones)
        bias_score += zone_diff * 0.05
        
        # Clamp bias score
        bias_score = max(-1.0, min(1.0, bias_score))
        
        # Determine bias type
        if bias_score > 0.2:
            bias = StructureType.BULLISH
        elif bias_score < -0.2:
            bias = StructureType.BEARISH
        else:
            bias = StructureType.NEUTRAL
        
        return bias, abs(bias_score)
    
    def _find_nearest_zone(
        self,
        price: float,
        zones: List[SMCZone],
        bullish: bool
    ) -> Optional[SMCZone]:
        """Find the nearest unmitigated zone to current price"""
        target_types = [
            ZoneType.ORDER_BLOCK_BULLISH if bullish else ZoneType.ORDER_BLOCK_BEARISH,
            ZoneType.FVG_BULLISH if bullish else ZoneType.FVG_BEARISH,
            ZoneType.BREAKER_BULLISH if bullish else ZoneType.BREAKER_BEARISH
        ]
        
        relevant_zones = [z for z in zones if z.zone_type in target_types and not z.mitigated]
        
        if not relevant_zones:
            return None
        
        # For bullish zones (demand), find nearest below price
        # For bearish zones (supply), find nearest above price
        if bullish:
            below_zones = [z for z in relevant_zones if z.top < price]
            if not below_zones:
                return None
            return max(below_zones, key=lambda z: z.top)
        else:
            above_zones = [z for z in relevant_zones if z.bottom > price]
            if not above_zones:
                return None
            return min(above_zones, key=lambda z: z.bottom)
    
    def _find_active_fvg(self, price: float, fvgs: List[SMCZone]) -> Optional[SMCZone]:
        """Find FVG that price is currently inside"""
        for fvg in fvgs:
            if fvg.contains_price(price) and not fvg.mitigated:
                return fvg
        return None
    
    def _update_mitigation_status(self, bars: List[Dict[str, Any]], zones: List[SMCZone]):
        """Update mitigation status of zones based on price action"""
        for zone in zones:
            if zone.mitigated:
                continue
            
            # Check if price has entered the zone
            for i in range(zone.start_index + 1, len(bars)):
                bar = bars[i]
                
                # Check if price touched the zone
                if zone.zone_type in [ZoneType.ORDER_BLOCK_BULLISH, ZoneType.FVG_BULLISH]:
                    # Bullish zone - check if price came down to it
                    if bar["low"] <= zone.top:
                        zone.touches += 1
                        # Calculate mitigation percentage
                        penetration = (zone.top - bar["low"]) / zone.size if zone.size > 0 else 0
                        zone.mitigation_percent = max(zone.mitigation_percent, min(1.0, penetration))
                        
                        # Fully mitigated if price closed below bottom
                        if bar["close"] < zone.bottom:
                            zone.mitigated = True
                            zone.mitigation_percent = 1.0
                            break
                else:
                    # Bearish zone - check if price came up to it
                    if bar["high"] >= zone.bottom:
                        zone.touches += 1
                        # Calculate mitigation percentage
                        penetration = (bar["high"] - zone.bottom) / zone.size if zone.size > 0 else 0
                        zone.mitigation_percent = max(zone.mitigation_percent, min(1.0, penetration))
                        
                        # Fully mitigated if price closed above top
                        if bar["close"] > zone.top:
                            zone.mitigated = True
                            zone.mitigation_percent = 1.0
                            break
    
    def _calculate_atr(self, bars: List[Dict[str, Any]], period: int = 14) -> float:
        """Calculate Average True Range"""
        if len(bars) < period + 1:
            return 0.0
        
        tr_values = []
        for i in range(1, len(bars)):
            high = bars[i]["high"]
            low = bars[i]["low"]
            prev_close = bars[i - 1]["close"]
            
            tr = max(
                high - low,
                abs(high - prev_close),
                abs(low - prev_close)
            )
            tr_values.append(tr)
        
        if len(tr_values) < period:
            return sum(tr_values) / len(tr_values) if tr_values else 0.0
        
        return sum(tr_values[-period:]) / period
    
    def _empty_analysis(self) -> SMCAnalysis:
        """Return empty analysis when insufficient data"""
        return SMCAnalysis(
            structure=StructureType.NEUTRAL,
            swing_highs=[],
            swing_lows=[],
            order_blocks=[],
            fair_value_gaps=[],
            liquidity_pools=[],
            breaker_blocks=[],
            structure_breaks=[],
            premium_zone=(0, 0),
            discount_zone=(0, 0),
            equilibrium=0,
            bias=StructureType.NEUTRAL,
            bias_strength=0.0
        )
    
    def get_trade_setup(
        self,
        analysis: SMCAnalysis,
        current_price: float
    ) -> Dict[str, Any]:
        """
        Generate trade setup based on SMC analysis
        
        Returns entry, stop loss, and take profit levels based on
        institutional trading concepts.
        """
        setup = {
            "direction": None,
            "entry": None,
            "stop_loss": None,
            "take_profit_1": None,
            "take_profit_2": None,
            "risk_reward": None,
            "confidence": 0.0,
            "reasoning": []
        }
        
        # Determine direction based on bias and structure
        if analysis.bias == StructureType.BULLISH and analysis.bias_strength > 0.3:
            setup["direction"] = "LONG"
            
            # Entry at nearest demand zone
            if analysis.nearest_demand:
                setup["entry"] = analysis.nearest_demand.top
                setup["stop_loss"] = analysis.nearest_demand.bottom * 0.999
                setup["reasoning"].append(f"Entry at bullish order block/FVG: {analysis.nearest_demand.top:.5f}")
            else:
                setup["entry"] = current_price
                setup["stop_loss"] = analysis.discount_zone[1] * 0.999
                setup["reasoning"].append("Entry at current price (no nearby demand zone)")
            
            # Take profit at supply zones or premium zone
            if analysis.nearest_supply:
                setup["take_profit_1"] = analysis.nearest_supply.bottom
                setup["take_profit_2"] = analysis.nearest_supply.top
            else:
                setup["take_profit_1"] = analysis.premium_zone[1]  # Equilibrium
                setup["take_profit_2"] = analysis.premium_zone[0]  # Premium high
            
            setup["reasoning"].append(f"Structure: BULLISH (strength: {analysis.bias_strength:.2f})")
            
        elif analysis.bias == StructureType.BEARISH and analysis.bias_strength > 0.3:
            setup["direction"] = "SHORT"
            
            # Entry at nearest supply zone
            if analysis.nearest_supply:
                setup["entry"] = analysis.nearest_supply.bottom
                setup["stop_loss"] = analysis.nearest_supply.top * 1.001
                setup["reasoning"].append(f"Entry at bearish order block/FVG: {analysis.nearest_supply.bottom:.5f}")
            else:
                setup["entry"] = current_price
                setup["stop_loss"] = analysis.premium_zone[0] * 1.001
                setup["reasoning"].append("Entry at current price (no nearby supply zone)")
            
            # Take profit at demand zones or discount zone
            if analysis.nearest_demand:
                setup["take_profit_1"] = analysis.nearest_demand.top
                setup["take_profit_2"] = analysis.nearest_demand.bottom
            else:
                setup["take_profit_1"] = analysis.discount_zone[0]  # Equilibrium
                setup["take_profit_2"] = analysis.discount_zone[1]  # Discount low
            
            setup["reasoning"].append(f"Structure: BEARISH (strength: {analysis.bias_strength:.2f})")
        
        # Calculate risk/reward
        if setup["entry"] and setup["stop_loss"] and setup["take_profit_1"]:
            risk = abs(setup["entry"] - setup["stop_loss"])
            reward = abs(setup["take_profit_1"] - setup["entry"])
            setup["risk_reward"] = reward / risk if risk > 0 else 0
        
        # Calculate confidence
        confidence = 0.0
        
        # Structure alignment
        if analysis.bias_strength > 0.5:
            confidence += 0.3
        elif analysis.bias_strength > 0.3:
            confidence += 0.2
        
        # Zone quality
        if setup["direction"] == "LONG" and analysis.nearest_demand:
            confidence += 0.2 * analysis.nearest_demand.strength
        elif setup["direction"] == "SHORT" and analysis.nearest_supply:
            confidence += 0.2 * analysis.nearest_supply.strength
        
        # Recent structure breaks
        recent_breaks = [b for b in analysis.structure_breaks if b.confirmed]
        if recent_breaks:
            last_break = recent_breaks[-1]
            if (setup["direction"] == "LONG" and last_break.is_bullish) or \
               (setup["direction"] == "SHORT" and not last_break.is_bullish):
                confidence += 0.2
        
        # Risk/reward bonus
        if setup["risk_reward"] and setup["risk_reward"] >= 2.0:
            confidence += 0.2
        elif setup["risk_reward"] and setup["risk_reward"] >= 1.5:
            confidence += 0.1
        
        setup["confidence"] = min(1.0, confidence)
        
        return setup


def test_smc_intelligence():
    """Test SMC Intelligence with sample data"""
    import random
    
    # Generate sample trending data
    bars = []
    price = 1.1000
    
    for i in range(200):
        # Add some trend and noise
        trend = 0.0001 if i < 100 else -0.00005
        noise = random.uniform(-0.0005, 0.0005)
        
        open_price = price
        close_price = price + trend + noise
        high_price = max(open_price, close_price) + random.uniform(0, 0.0003)
        low_price = min(open_price, close_price) - random.uniform(0, 0.0003)
        
        bars.append({
            "open": open_price,
            "high": high_price,
            "low": low_price,
            "close": close_price,
            "volume": random.uniform(1000, 5000)
        })
        
        price = close_price
    
    # Run SMC analysis
    smc = SMCIntelligence()
    analysis = smc.analyze(bars)
    
    print("=" * 60)
    print("SMC INTELLIGENCE TEST RESULTS")
    print("=" * 60)
    print(f"\nMarket Structure: {analysis.structure.value}")
    print(f"Bias: {analysis.bias.value} (strength: {analysis.bias_strength:.2f})")
    print(f"\nSwing Highs: {len(analysis.swing_highs)}")
    print(f"Swing Lows: {len(analysis.swing_lows)}")
    print(f"\nOrder Blocks: {len(analysis.order_blocks)}")
    for ob in analysis.order_blocks[:3]:
        print(f"  - {ob.zone_type.value}: {ob.bottom:.5f} - {ob.top:.5f} (strength: {ob.strength:.2f})")
    
    print(f"\nFair Value Gaps: {len(analysis.fair_value_gaps)}")
    for fvg in analysis.fair_value_gaps[:3]:
        print(f"  - {fvg.zone_type.value}: {fvg.bottom:.5f} - {fvg.top:.5f}")
    
    print(f"\nLiquidity Pools: {len(analysis.liquidity_pools)}")
    print(f"Breaker Blocks: {len(analysis.breaker_blocks)}")
    print(f"Structure Breaks: {len(analysis.structure_breaks)}")
    
    print(f"\nPremium Zone: {analysis.premium_zone[1]:.5f} - {analysis.premium_zone[0]:.5f}")
    print(f"Discount Zone: {analysis.discount_zone[1]:.5f} - {analysis.discount_zone[0]:.5f}")
    print(f"Equilibrium: {analysis.equilibrium:.5f}")
    
    # Get trade setup
    current_price = bars[-1]["close"]
    setup = smc.get_trade_setup(analysis, current_price)
    
    print(f"\n{'=' * 60}")
    print("TRADE SETUP")
    print("=" * 60)
    print(f"Direction: {setup['direction']}")
    print(f"Entry: {setup['entry']}")
    print(f"Stop Loss: {setup['stop_loss']}")
    print(f"Take Profit 1: {setup['take_profit_1']}")
    print(f"Take Profit 2: {setup['take_profit_2']}")
    print(f"Risk/Reward: {setup['risk_reward']:.2f}" if setup['risk_reward'] else "Risk/Reward: N/A")
    print(f"Confidence: {setup['confidence']:.1%}")
    print(f"\nReasoning:")
    for reason in setup['reasoning']:
        print(f"  - {reason}")
    
    return analysis, setup


if __name__ == "__main__":
    test_smc_intelligence()
