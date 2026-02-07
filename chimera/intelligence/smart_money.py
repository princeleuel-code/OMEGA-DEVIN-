"""
Smart Money Concepts (SMC) Detector
===================================

This module implements institutional trading concepts used by professional traders:

1. Order Blocks - Zones where institutions placed large orders
2. Fair Value Gaps (FVG) - Imbalances in price that tend to get filled
3. Liquidity Pools - Areas where stop losses cluster (targets for stop hunts)
4. Break of Structure (BOS) - Trend continuation confirmation
5. Change of Character (CHoCH) - Trend reversal signal

These concepts help identify where "smart money" (institutions) are likely to act.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple
from enum import Enum
from datetime import datetime
import math


class BlockType(Enum):
    BULLISH_OB = "bullish_order_block"
    BEARISH_OB = "bearish_order_block"


class GapType(Enum):
    BULLISH_FVG = "bullish_fvg"
    BEARISH_FVG = "bearish_fvg"


class StructureType(Enum):
    BREAK_OF_STRUCTURE = "bos"
    CHANGE_OF_CHARACTER = "choch"


@dataclass
class OrderBlock:
    """
    Order Block: The last opposing candle before a strong move.
    
    Bullish OB: Last bearish candle before a strong bullish move
    Bearish OB: Last bullish candle before a strong bearish move
    
    These zones often act as support/resistance where price returns to.
    """
    block_type: BlockType
    high: float
    low: float
    midpoint: float
    strength: float  # 0-1, based on the move that followed
    timestamp: datetime
    bar_index: int
    mitigated: bool = False  # True if price has returned to this zone
    touches: int = 0
    
    @property
    def zone_size(self) -> float:
        return self.high - self.low


@dataclass
class FairValueGap:
    """
    Fair Value Gap: A 3-candle pattern where there's a gap between candle 1 and 3.
    
    Bullish FVG: Gap between candle 1 high and candle 3 low (price moved up fast)
    Bearish FVG: Gap between candle 1 low and candle 3 high (price moved down fast)
    
    Price tends to return to fill these gaps.
    """
    gap_type: GapType
    high: float
    low: float
    midpoint: float
    size: float
    timestamp: datetime
    bar_index: int
    filled: bool = False
    fill_percentage: float = 0.0


@dataclass
class LiquidityPool:
    """
    Liquidity Pool: Areas where stop losses likely cluster.
    
    - Equal highs/lows (obvious stop loss placement)
    - Round numbers
    - Previous day/week high/low
    
    Institutions often push price to these levels to trigger stops before reversing.
    """
    level: float
    pool_type: str  # "equal_highs", "equal_lows", "round_number", "swing_high", "swing_low"
    strength: float  # 0-1, based on how many times tested
    timestamp: datetime
    bar_index: int
    swept: bool = False  # True if price has taken this liquidity


@dataclass
class StructureBreak:
    """
    Break of Structure (BOS) or Change of Character (CHoCH).
    
    BOS: Price breaks a swing high/low in the direction of the trend (continuation)
    CHoCH: Price breaks a swing high/low against the trend (reversal signal)
    """
    structure_type: StructureType
    direction: int  # 1 = bullish, -1 = bearish
    level: float
    timestamp: datetime
    bar_index: int
    confirmed: bool = True


@dataclass
class SMCAnalysis:
    """Complete Smart Money Concepts analysis."""
    order_blocks: List[OrderBlock]
    fair_value_gaps: List[FairValueGap]
    liquidity_pools: List[LiquidityPool]
    structure_breaks: List[StructureBreak]
    current_bias: int  # 1 = bullish, -1 = bearish, 0 = neutral
    nearest_bullish_ob: Optional[OrderBlock]
    nearest_bearish_ob: Optional[OrderBlock]
    nearest_unfilled_fvg: Optional[FairValueGap]
    reason_codes: List[str]


class SmartMoneyDetector:
    """
    Detects Smart Money Concepts in price action.
    
    This is what separates retail traders from professionals.
    Institutions leave footprints in the market - this detector finds them.
    """
    
    def __init__(
        self,
        ob_lookback: int = 50,
        fvg_min_size_atr: float = 0.5,
        liquidity_tolerance: float = 0.0002,  # 2 pips for FX
        structure_lookback: int = 20,
    ):
        self.ob_lookback = ob_lookback
        self.fvg_min_size_atr = fvg_min_size_atr
        self.liquidity_tolerance = liquidity_tolerance
        self.structure_lookback = structure_lookback
    
    def analyze(self, bars: List[dict]) -> SMCAnalysis:
        """
        Perform complete Smart Money Concepts analysis.
        
        Args:
            bars: List of OHLCV bars (must be sorted by timestamp ascending)
            
        Returns:
            SMCAnalysis with all detected patterns
        """
        if len(bars) < self.ob_lookback:
            return self._empty_analysis()
        
        current_price = bars[-1]['close']
        
        # Detect all patterns
        order_blocks = self._detect_order_blocks(bars)
        fair_value_gaps = self._detect_fair_value_gaps(bars)
        liquidity_pools = self._detect_liquidity_pools(bars)
        structure_breaks = self._detect_structure_breaks(bars)
        
        # Update mitigation/fill status
        order_blocks = self._update_ob_mitigation(order_blocks, bars)
        fair_value_gaps = self._update_fvg_fills(fair_value_gaps, bars)
        liquidity_pools = self._update_liquidity_sweeps(liquidity_pools, bars)
        
        # Determine current bias from structure
        current_bias = self._determine_bias(structure_breaks)
        
        # Find nearest relevant levels
        nearest_bullish_ob = self._find_nearest_ob(order_blocks, current_price, BlockType.BULLISH_OB)
        nearest_bearish_ob = self._find_nearest_ob(order_blocks, current_price, BlockType.BEARISH_OB)
        nearest_unfilled_fvg = self._find_nearest_unfilled_fvg(fair_value_gaps, current_price)
        
        # Build reason codes
        reason_codes = self._build_reason_codes(
            order_blocks, fair_value_gaps, liquidity_pools, 
            structure_breaks, current_price, current_bias
        )
        
        return SMCAnalysis(
            order_blocks=order_blocks,
            fair_value_gaps=fair_value_gaps,
            liquidity_pools=liquidity_pools,
            structure_breaks=structure_breaks,
            current_bias=current_bias,
            nearest_bullish_ob=nearest_bullish_ob,
            nearest_bearish_ob=nearest_bearish_ob,
            nearest_unfilled_fvg=nearest_unfilled_fvg,
            reason_codes=reason_codes
        )
    
    def _detect_order_blocks(self, bars: List[dict]) -> List[OrderBlock]:
        """
        Detect Order Blocks.
        
        Bullish OB: Last bearish candle before a strong bullish move
        Bearish OB: Last bullish candle before a strong bearish move
        """
        order_blocks = []
        
        # Calculate ATR for move strength
        atr = self._calculate_atr(bars)
        if atr == 0:
            return order_blocks
        
        for i in range(2, len(bars) - 1):
            current = bars[i]
            prev = bars[i - 1]
            next_bar = bars[i + 1]
            
            current_body = current['close'] - current['open']
            next_body = next_bar['close'] - next_bar['open']
            
            # Bullish Order Block: bearish candle followed by strong bullish move
            if current_body < 0 and next_body > 0:
                move_size = next_bar['close'] - current['low']
                if move_size > atr * 1.5:  # Strong move
                    strength = min(1.0, move_size / (atr * 3))
                    ob = OrderBlock(
                        block_type=BlockType.BULLISH_OB,
                        high=current['high'],
                        low=current['low'],
                        midpoint=(current['high'] + current['low']) / 2,
                        strength=strength,
                        timestamp=self._get_timestamp(current),
                        bar_index=i
                    )
                    order_blocks.append(ob)
            
            # Bearish Order Block: bullish candle followed by strong bearish move
            if current_body > 0 and next_body < 0:
                move_size = current['high'] - next_bar['close']
                if move_size > atr * 1.5:  # Strong move
                    strength = min(1.0, move_size / (atr * 3))
                    ob = OrderBlock(
                        block_type=BlockType.BEARISH_OB,
                        high=current['high'],
                        low=current['low'],
                        midpoint=(current['high'] + current['low']) / 2,
                        strength=strength,
                        timestamp=self._get_timestamp(current),
                        bar_index=i
                    )
                    order_blocks.append(ob)
        
        # Keep only recent and strong order blocks
        order_blocks = [ob for ob in order_blocks if ob.strength > 0.3]
        order_blocks = order_blocks[-self.ob_lookback:]
        
        return order_blocks
    
    def _detect_fair_value_gaps(self, bars: List[dict]) -> List[FairValueGap]:
        """
        Detect Fair Value Gaps (FVG).
        
        3-candle pattern where there's a gap between candle 1 and candle 3.
        """
        fvgs = []
        
        atr = self._calculate_atr(bars)
        min_gap_size = atr * self.fvg_min_size_atr
        
        for i in range(2, len(bars)):
            candle1 = bars[i - 2]
            candle3 = bars[i]
            
            # Bullish FVG: candle 1 high < candle 3 low
            if candle1['high'] < candle3['low']:
                gap_size = candle3['low'] - candle1['high']
                if gap_size >= min_gap_size:
                    fvg = FairValueGap(
                        gap_type=GapType.BULLISH_FVG,
                        high=candle3['low'],
                        low=candle1['high'],
                        midpoint=(candle3['low'] + candle1['high']) / 2,
                        size=gap_size,
                        timestamp=self._get_timestamp(candle3),
                        bar_index=i
                    )
                    fvgs.append(fvg)
            
            # Bearish FVG: candle 1 low > candle 3 high
            if candle1['low'] > candle3['high']:
                gap_size = candle1['low'] - candle3['high']
                if gap_size >= min_gap_size:
                    fvg = FairValueGap(
                        gap_type=GapType.BEARISH_FVG,
                        high=candle1['low'],
                        low=candle3['high'],
                        midpoint=(candle1['low'] + candle3['high']) / 2,
                        size=gap_size,
                        timestamp=self._get_timestamp(candle3),
                        bar_index=i
                    )
                    fvgs.append(fvg)
        
        return fvgs[-50:]  # Keep last 50 FVGs
    
    def _detect_liquidity_pools(self, bars: List[dict]) -> List[LiquidityPool]:
        """
        Detect Liquidity Pools.
        
        - Equal highs/lows (obvious stop placement)
        - Swing highs/lows
        """
        pools = []
        
        highs = [b['high'] for b in bars]
        lows = [b['low'] for b in bars]
        
        # Find swing highs and lows
        for i in range(self.structure_lookback, len(bars) - self.structure_lookback):
            # Swing high
            if highs[i] == max(highs[i - self.structure_lookback:i + self.structure_lookback + 1]):
                pool = LiquidityPool(
                    level=highs[i],
                    pool_type="swing_high",
                    strength=0.7,
                    timestamp=self._get_timestamp(bars[i]),
                    bar_index=i
                )
                pools.append(pool)
            
            # Swing low
            if lows[i] == min(lows[i - self.structure_lookback:i + self.structure_lookback + 1]):
                pool = LiquidityPool(
                    level=lows[i],
                    pool_type="swing_low",
                    strength=0.7,
                    timestamp=self._get_timestamp(bars[i]),
                    bar_index=i
                )
                pools.append(pool)
        
        # Find equal highs/lows (within tolerance)
        for i in range(len(bars) - 1):
            for j in range(i + 1, min(i + 20, len(bars))):
                # Equal highs
                if abs(highs[i] - highs[j]) / highs[i] < self.liquidity_tolerance:
                    avg_level = (highs[i] + highs[j]) / 2
                    pool = LiquidityPool(
                        level=avg_level,
                        pool_type="equal_highs",
                        strength=0.9,
                        timestamp=self._get_timestamp(bars[j]),
                        bar_index=j
                    )
                    pools.append(pool)
                
                # Equal lows
                if abs(lows[i] - lows[j]) / lows[i] < self.liquidity_tolerance:
                    avg_level = (lows[i] + lows[j]) / 2
                    pool = LiquidityPool(
                        level=avg_level,
                        pool_type="equal_lows",
                        strength=0.9,
                        timestamp=self._get_timestamp(bars[j]),
                        bar_index=j
                    )
                    pools.append(pool)
        
        # Deduplicate pools at similar levels
        pools = self._deduplicate_pools(pools)
        
        return pools[-30:]  # Keep last 30 pools
    
    def _detect_structure_breaks(self, bars: List[dict]) -> List[StructureBreak]:
        """
        Detect Break of Structure (BOS) and Change of Character (CHoCH).
        """
        breaks = []
        
        highs = [b['high'] for b in bars]
        lows = [b['low'] for b in bars]
        
        # Find swing points
        swing_highs = []
        swing_lows = []
        lookback = 5
        
        for i in range(lookback, len(bars) - lookback):
            if highs[i] == max(highs[i - lookback:i + lookback + 1]):
                swing_highs.append((i, highs[i]))
            if lows[i] == min(lows[i - lookback:i + lookback + 1]):
                swing_lows.append((i, lows[i]))
        
        # Detect structure breaks
        current_trend = 0  # 0 = unknown, 1 = bullish, -1 = bearish
        
        for i in range(len(bars)):
            current_high = highs[i]
            current_low = lows[i]
            
            # Check if we broke a recent swing high
            recent_swing_highs = [(idx, level) for idx, level in swing_highs if idx < i and i - idx < 50]
            for idx, level in recent_swing_highs:
                if current_high > level:
                    # Bullish break
                    if current_trend == -1:
                        # CHoCH - trend reversal
                        breaks.append(StructureBreak(
                            structure_type=StructureType.CHANGE_OF_CHARACTER,
                            direction=1,
                            level=level,
                            timestamp=self._get_timestamp(bars[i]),
                            bar_index=i
                        ))
                    else:
                        # BOS - trend continuation
                        breaks.append(StructureBreak(
                            structure_type=StructureType.BREAK_OF_STRUCTURE,
                            direction=1,
                            level=level,
                            timestamp=self._get_timestamp(bars[i]),
                            bar_index=i
                        ))
                    current_trend = 1
                    break
            
            # Check if we broke a recent swing low
            recent_swing_lows = [(idx, level) for idx, level in swing_lows if idx < i and i - idx < 50]
            for idx, level in recent_swing_lows:
                if current_low < level:
                    # Bearish break
                    if current_trend == 1:
                        # CHoCH - trend reversal
                        breaks.append(StructureBreak(
                            structure_type=StructureType.CHANGE_OF_CHARACTER,
                            direction=-1,
                            level=level,
                            timestamp=self._get_timestamp(bars[i]),
                            bar_index=i
                        ))
                    else:
                        # BOS - trend continuation
                        breaks.append(StructureBreak(
                            structure_type=StructureType.BREAK_OF_STRUCTURE,
                            direction=-1,
                            level=level,
                            timestamp=self._get_timestamp(bars[i]),
                            bar_index=i
                        ))
                    current_trend = -1
                    break
        
        return breaks[-20:]  # Keep last 20 structure breaks
    
    def _update_ob_mitigation(self, order_blocks: List[OrderBlock], bars: List[dict]) -> List[OrderBlock]:
        """Update order blocks to mark if they've been mitigated (price returned to zone)."""
        for ob in order_blocks:
            for i in range(ob.bar_index + 1, len(bars)):
                bar = bars[i]
                # Check if price entered the OB zone
                if bar['low'] <= ob.high and bar['high'] >= ob.low:
                    ob.touches += 1
                    if ob.touches >= 2:
                        ob.mitigated = True
        return order_blocks
    
    def _update_fvg_fills(self, fvgs: List[FairValueGap], bars: List[dict]) -> List[FairValueGap]:
        """Update FVGs to mark fill percentage."""
        for fvg in fvgs:
            for i in range(fvg.bar_index + 1, len(bars)):
                bar = bars[i]
                
                if fvg.gap_type == GapType.BULLISH_FVG:
                    # Price needs to come down to fill
                    if bar['low'] <= fvg.midpoint:
                        fvg.fill_percentage = min(1.0, (fvg.high - bar['low']) / fvg.size)
                        if bar['low'] <= fvg.low:
                            fvg.filled = True
                
                elif fvg.gap_type == GapType.BEARISH_FVG:
                    # Price needs to come up to fill
                    if bar['high'] >= fvg.midpoint:
                        fvg.fill_percentage = min(1.0, (bar['high'] - fvg.low) / fvg.size)
                        if bar['high'] >= fvg.high:
                            fvg.filled = True
        
        return fvgs
    
    def _update_liquidity_sweeps(self, pools: List[LiquidityPool], bars: List[dict]) -> List[LiquidityPool]:
        """Update liquidity pools to mark if they've been swept."""
        for pool in pools:
            for i in range(pool.bar_index + 1, len(bars)):
                bar = bars[i]
                
                if pool.pool_type in ["swing_high", "equal_highs"]:
                    if bar['high'] > pool.level:
                        pool.swept = True
                        break
                elif pool.pool_type in ["swing_low", "equal_lows"]:
                    if bar['low'] < pool.level:
                        pool.swept = True
                        break
        
        return pools
    
    def _determine_bias(self, structure_breaks: List[StructureBreak]) -> int:
        """Determine current market bias from recent structure breaks."""
        if not structure_breaks:
            return 0
        
        # Look at last 5 structure breaks
        recent = structure_breaks[-5:]
        
        bullish_count = sum(1 for sb in recent if sb.direction > 0)
        bearish_count = sum(1 for sb in recent if sb.direction < 0)
        
        # Check for CHoCH (most recent)
        last_break = structure_breaks[-1]
        if last_break.structure_type == StructureType.CHANGE_OF_CHARACTER:
            return last_break.direction
        
        if bullish_count > bearish_count:
            return 1
        elif bearish_count > bullish_count:
            return -1
        return 0
    
    def _find_nearest_ob(
        self, 
        order_blocks: List[OrderBlock], 
        current_price: float, 
        block_type: BlockType
    ) -> Optional[OrderBlock]:
        """Find the nearest unmitigated order block of the given type."""
        relevant_obs = [
            ob for ob in order_blocks 
            if ob.block_type == block_type and not ob.mitigated
        ]
        
        if not relevant_obs:
            return None
        
        if block_type == BlockType.BULLISH_OB:
            # Find nearest OB below current price
            below = [ob for ob in relevant_obs if ob.high < current_price]
            if below:
                return max(below, key=lambda ob: ob.high)
        else:
            # Find nearest OB above current price
            above = [ob for ob in relevant_obs if ob.low > current_price]
            if above:
                return min(above, key=lambda ob: ob.low)
        
        return None
    
    def _find_nearest_unfilled_fvg(
        self, 
        fvgs: List[FairValueGap], 
        current_price: float
    ) -> Optional[FairValueGap]:
        """Find the nearest unfilled FVG."""
        unfilled = [fvg for fvg in fvgs if not fvg.filled]
        
        if not unfilled:
            return None
        
        # Find closest to current price
        return min(unfilled, key=lambda fvg: abs(fvg.midpoint - current_price))
    
    def _deduplicate_pools(self, pools: List[LiquidityPool]) -> List[LiquidityPool]:
        """Remove duplicate liquidity pools at similar levels."""
        if not pools:
            return pools
        
        pools = sorted(pools, key=lambda p: p.level)
        deduplicated = [pools[0]]
        
        for pool in pools[1:]:
            last = deduplicated[-1]
            if abs(pool.level - last.level) / last.level > self.liquidity_tolerance * 2:
                deduplicated.append(pool)
            elif pool.strength > last.strength:
                deduplicated[-1] = pool
        
        return deduplicated
    
    def _build_reason_codes(
        self,
        order_blocks: List[OrderBlock],
        fvgs: List[FairValueGap],
        pools: List[LiquidityPool],
        structure_breaks: List[StructureBreak],
        current_price: float,
        current_bias: int
    ) -> List[str]:
        """Build reason codes for the analysis."""
        codes = []
        
        # Bias
        if current_bias > 0:
            codes.append("SMC_BULLISH_BIAS")
        elif current_bias < 0:
            codes.append("SMC_BEARISH_BIAS")
        else:
            codes.append("SMC_NEUTRAL_BIAS")
        
        # Order blocks
        unmitigated_bullish = [ob for ob in order_blocks if ob.block_type == BlockType.BULLISH_OB and not ob.mitigated]
        unmitigated_bearish = [ob for ob in order_blocks if ob.block_type == BlockType.BEARISH_OB and not ob.mitigated]
        
        if unmitigated_bullish:
            codes.append(f"SMC_BULLISH_OB_COUNT_{len(unmitigated_bullish)}")
        if unmitigated_bearish:
            codes.append(f"SMC_BEARISH_OB_COUNT_{len(unmitigated_bearish)}")
        
        # FVGs
        unfilled_bullish = [fvg for fvg in fvgs if fvg.gap_type == GapType.BULLISH_FVG and not fvg.filled]
        unfilled_bearish = [fvg for fvg in fvgs if fvg.gap_type == GapType.BEARISH_FVG and not fvg.filled]
        
        if unfilled_bullish:
            codes.append(f"SMC_BULLISH_FVG_COUNT_{len(unfilled_bullish)}")
        if unfilled_bearish:
            codes.append(f"SMC_BEARISH_FVG_COUNT_{len(unfilled_bearish)}")
        
        # Recent structure breaks
        if structure_breaks:
            last = structure_breaks[-1]
            if last.structure_type == StructureType.CHANGE_OF_CHARACTER:
                codes.append(f"SMC_CHOCH_{'BULLISH' if last.direction > 0 else 'BEARISH'}")
            else:
                codes.append(f"SMC_BOS_{'BULLISH' if last.direction > 0 else 'BEARISH'}")
        
        # Liquidity
        unswept_above = [p for p in pools if not p.swept and p.level > current_price]
        unswept_below = [p for p in pools if not p.swept and p.level < current_price]
        
        if unswept_above:
            codes.append(f"SMC_LIQUIDITY_ABOVE_{len(unswept_above)}")
        if unswept_below:
            codes.append(f"SMC_LIQUIDITY_BELOW_{len(unswept_below)}")
        
        return codes
    
    def _calculate_atr(self, bars: List[dict], period: int = 14) -> float:
        """Calculate Average True Range."""
        if len(bars) < period + 1:
            return 0.0
        
        true_ranges = []
        for i in range(1, len(bars)):
            tr = max(
                bars[i]['high'] - bars[i]['low'],
                abs(bars[i]['high'] - bars[i - 1]['close']),
                abs(bars[i]['low'] - bars[i - 1]['close'])
            )
            true_ranges.append(tr)
        
        return sum(true_ranges[-period:]) / period
    
    def _get_timestamp(self, bar: dict) -> datetime:
        """Extract timestamp from bar."""
        ts = bar.get('timestamp', '')
        if isinstance(ts, datetime):
            return ts
        if isinstance(ts, str):
            try:
                return datetime.fromisoformat(ts.replace('+00:00', '').replace('Z', ''))
            except:
                pass
        return datetime.now()
    
    def _empty_analysis(self) -> SMCAnalysis:
        """Return empty analysis."""
        return SMCAnalysis(
            order_blocks=[],
            fair_value_gaps=[],
            liquidity_pools=[],
            structure_breaks=[],
            current_bias=0,
            nearest_bullish_ob=None,
            nearest_bearish_ob=None,
            nearest_unfilled_fvg=None,
            reason_codes=["SMC_INSUFFICIENT_DATA"]
        )
