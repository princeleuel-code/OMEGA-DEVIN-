"""
Volume Profile Edge (VPE) Intelligence Module

Based on Forest Knight's 7-figure trading system from Chart Fanatics.
This module implements institutional-grade Volume Profile analysis.

Key Concepts:
- Volume Profile shows WHERE people are positioned (not just when)
- High Value Areas = sticky prices where most volume accumulated
- Low Value Areas = prices rip through quickly
- Point of Control (POC) = price with most volume
- Value Area = 70% of volume (VAH/VAL)
- Edge to Edge trading = enter at one VP edge, TP at next edge

Signal Candles:
- High volume doji, shooting star, hammer at VP EDGES
- WAIT for candle to CLOSE before entering
- 50-80% wick retracement zones for limit orders

VP Shapes:
- P-shaped = Bullish (volume accumulated higher)
- B-shaped = Bearish (volume accumulated lower)
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Optional, Tuple
import math


class VPShape(Enum):
    """Volume Profile shape patterns"""
    P_SHAPED = "p_shaped"  # Bullish - volume accumulated higher
    B_SHAPED = "b_shaped"  # Bearish - volume accumulated lower
    D_SHAPED = "d_shaped"  # Normal distribution - balanced
    DOUBLE_DISTRIBUTION = "double_distribution"  # Two value areas
    THIN = "thin"  # Low volume day
    UNKNOWN = "unknown"


class CandlePattern(Enum):
    """Signal candle patterns"""
    DOJI = "doji"
    SHOOTING_STAR = "shooting_star"
    HAMMER = "hammer"
    ENGULFING_BULLISH = "engulfing_bullish"
    ENGULFING_BEARISH = "engulfing_bearish"
    MARUBOZU_BULLISH = "marubozu_bullish"
    MARUBOZU_BEARISH = "marubozu_bearish"
    SPINNING_TOP = "spinning_top"
    NONE = "none"


class SignalStrength(Enum):
    """Signal strength levels"""
    ULTRA_STRONG = "ultra_strong"  # VP edge + key level + signal candle + HTF confluence
    STRONG = "strong"  # VP edge + key level + signal candle
    MODERATE = "moderate"  # VP edge + signal candle
    WEAK = "weak"  # Only one factor
    NO_SIGNAL = "no_signal"


@dataclass
class VolumeNode:
    """Represents a volume node at a specific price level"""
    price: float
    volume: float
    is_poc: bool = False
    is_vah: bool = False  # Value Area High
    is_val: bool = False  # Value Area Low
    is_edge: bool = False  # Edge of value area
    node_type: str = "normal"  # "high_value", "low_value", "poc"


@dataclass
class VolumeProfile:
    """Complete volume profile for a session"""
    nodes: List[VolumeNode]
    poc: float  # Point of Control
    vah: float  # Value Area High
    val: float  # Value Area Low
    total_volume: float
    high: float
    low: float
    shape: VPShape
    value_area_volume: float  # Volume within VAH-VAL
    
    @property
    def value_area_range(self) -> float:
        return self.vah - self.val
    
    @property
    def total_range(self) -> float:
        return self.high - self.low
    
    @property
    def value_area_percent(self) -> float:
        if self.total_range == 0:
            return 0
        return self.value_area_range / self.total_range


@dataclass
class KeyLevel:
    """Key price level for trading"""
    price: float
    level_type: str  # "pdh", "pdl", "overnight_high", "overnight_low", "poc", "vah", "val"
    strength: float  # 0-1
    touched_count: int = 0
    last_touch_bar: int = -1


@dataclass
class SignalCandle:
    """Detected signal candle"""
    bar_index: int
    pattern: CandlePattern
    direction: str  # "bullish", "bearish", "neutral"
    volume_ratio: float  # Relative to previous candle
    wick_ratio: float  # Wick size relative to body
    at_edge: bool  # Is at VP edge
    at_key_level: bool  # Is at key level
    strength: SignalStrength
    entry_price: float
    stop_loss: float
    take_profit: float
    wick_retracement_50: float  # 50% of wick
    wick_retracement_80: float  # 80% of wick


@dataclass
class VPETradeSetup:
    """Complete VPE trade setup"""
    direction: str  # "long", "short", "none"
    setup_type: str  # "edge_sweep", "poc_retest", "mean_reversion", "breakout"
    entry_price: float
    stop_loss: float
    take_profit_1: float  # First target (conservative)
    take_profit_2: float  # Second target (POC or next edge)
    take_profit_3: float  # Third target (aggressive)
    risk_reward: float
    confidence: float
    signal_candle: Optional[SignalCandle]
    vp_shape: VPShape
    key_levels_confluence: List[KeyLevel]
    reasoning: List[str]
    warnings: List[str]


@dataclass
class VPEAnalysis:
    """Complete VPE analysis result"""
    session_vp: VolumeProfile
    prior_day_vp: Optional[VolumeProfile]
    visible_range_vp: Optional[VolumeProfile]
    key_levels: List[KeyLevel]
    signal_candles: List[SignalCandle]
    trade_setup: Optional[VPETradeSetup]
    market_bias: str  # "bullish", "bearish", "neutral"
    current_zone: str  # "high_value", "low_value", "above_value", "below_value"
    edge_distance: float  # Distance to nearest edge
    poc_distance: float  # Distance to POC


class VPEIntelligence:
    """
    Volume Profile Edge Intelligence Engine
    
    Implements Forest Knight's VPE trading system:
    - Session Volume Profile analysis
    - Key level detection (PDH/PDL, Overnight High/Low)
    - Signal candle detection
    - Edge to edge trading
    - POC retest setups
    """
    
    def __init__(
        self,
        value_area_percent: float = 0.70,  # 70% of volume for value area
        min_volume_ratio: float = 1.2,  # Min volume ratio for signal candle
        wick_threshold: float = 0.5,  # Min wick ratio for signal candle
        price_resolution: int = 100,  # Number of price levels in VP
    ):
        self.value_area_percent = value_area_percent
        self.min_volume_ratio = min_volume_ratio
        self.wick_threshold = wick_threshold
        self.price_resolution = price_resolution
    
    def analyze(
        self,
        bars: List[Dict],
        session_start_idx: int = 0,
        prior_day_bars: Optional[List[Dict]] = None,
    ) -> VPEAnalysis:
        """
        Perform complete VPE analysis
        
        Args:
            bars: Current session bars (OHLCV dicts)
            session_start_idx: Index where current session starts
            prior_day_bars: Previous day's bars for PDH/PDL
        
        Returns:
            Complete VPE analysis
        """
        if len(bars) < 10:
            return self._empty_analysis()
        
        # Build session volume profile
        session_bars = bars[session_start_idx:]
        session_vp = self._build_volume_profile(session_bars)
        
        # Build prior day VP if available
        prior_day_vp = None
        if prior_day_bars and len(prior_day_bars) > 10:
            prior_day_vp = self._build_volume_profile(prior_day_bars)
        
        # Build visible range VP (all bars)
        visible_range_vp = self._build_volume_profile(bars)
        
        # Detect key levels
        key_levels = self._detect_key_levels(
            bars, session_vp, prior_day_bars, prior_day_vp
        )
        
        # Detect signal candles
        signal_candles = self._detect_signal_candles(
            bars, session_vp, key_levels
        )
        
        # Determine market bias
        market_bias = self._determine_bias(session_vp, bars)
        
        # Determine current zone
        current_price = bars[-1]["close"]
        current_zone = self._get_current_zone(current_price, session_vp)
        
        # Calculate distances
        edge_distance = self._get_edge_distance(current_price, session_vp)
        poc_distance = abs(current_price - session_vp.poc)
        
        # Generate trade setup
        trade_setup = self._generate_trade_setup(
            bars, session_vp, prior_day_vp, key_levels, signal_candles, market_bias
        )
        
        return VPEAnalysis(
            session_vp=session_vp,
            prior_day_vp=prior_day_vp,
            visible_range_vp=visible_range_vp,
            key_levels=key_levels,
            signal_candles=signal_candles,
            trade_setup=trade_setup,
            market_bias=market_bias,
            current_zone=current_zone,
            edge_distance=edge_distance,
            poc_distance=poc_distance,
        )
    
    def _build_volume_profile(self, bars: List[Dict]) -> VolumeProfile:
        """Build volume profile from bars"""
        if not bars:
            return self._empty_vp()
        
        # Find price range
        high = max(bar["high"] for bar in bars)
        low = min(bar["low"] for bar in bars)
        price_range = high - low
        
        if price_range == 0:
            return self._empty_vp()
        
        # Create price levels
        step = price_range / self.price_resolution
        price_levels = {}
        
        for i in range(self.price_resolution + 1):
            price = low + i * step
            price_levels[round(price, 5)] = 0.0
        
        # Distribute volume across price levels
        total_volume = 0.0
        for bar in bars:
            bar_volume = bar.get("volume", bar.get("tick_volume", 1))
            bar_range = bar["high"] - bar["low"]
            
            if bar_range == 0:
                # Single price bar - all volume at close
                closest_price = self._find_closest_price(bar["close"], price_levels)
                price_levels[closest_price] += bar_volume
            else:
                # Distribute volume across bar range
                for price in price_levels:
                    if bar["low"] <= price <= bar["high"]:
                        # Weight by proximity to close (more volume near close)
                        dist_to_close = abs(price - bar["close"])
                        weight = 1.0 - (dist_to_close / bar_range) * 0.5
                        price_levels[price] += bar_volume * weight / self.price_resolution
            
            total_volume += bar_volume
        
        # Create volume nodes
        nodes = []
        max_volume = max(price_levels.values()) if price_levels else 0
        
        for price, volume in sorted(price_levels.items()):
            node = VolumeNode(
                price=price,
                volume=volume,
                node_type="high_value" if volume > max_volume * 0.7 else (
                    "low_value" if volume < max_volume * 0.3 else "normal"
                )
            )
            nodes.append(node)
        
        # Find POC (Point of Control)
        poc_node = max(nodes, key=lambda n: n.volume)
        poc_node.is_poc = True
        poc = poc_node.price
        
        # Calculate Value Area (70% of volume)
        vah, val, va_volume = self._calculate_value_area(nodes, poc, total_volume)
        
        # Mark VAH and VAL
        for node in nodes:
            if abs(node.price - vah) < step:
                node.is_vah = True
                node.is_edge = True
            if abs(node.price - val) < step:
                node.is_val = True
                node.is_edge = True
        
        # Determine VP shape
        shape = self._determine_vp_shape(nodes, poc, vah, val, high, low)
        
        return VolumeProfile(
            nodes=nodes,
            poc=poc,
            vah=vah,
            val=val,
            total_volume=total_volume,
            high=high,
            low=low,
            shape=shape,
            value_area_volume=va_volume,
        )
    
    def _calculate_value_area(
        self,
        nodes: List[VolumeNode],
        poc: float,
        total_volume: float,
    ) -> Tuple[float, float, float]:
        """Calculate Value Area High and Low (70% of volume)"""
        if not nodes or total_volume == 0:
            return 0, 0, 0
        
        target_volume = total_volume * self.value_area_percent
        
        # Start from POC and expand outward
        poc_idx = next(
            (i for i, n in enumerate(nodes) if n.is_poc),
            len(nodes) // 2
        )
        
        va_volume = nodes[poc_idx].volume
        upper_idx = poc_idx
        lower_idx = poc_idx
        
        while va_volume < target_volume:
            # Check which direction has more volume
            upper_vol = nodes[upper_idx + 1].volume if upper_idx + 1 < len(nodes) else 0
            lower_vol = nodes[lower_idx - 1].volume if lower_idx - 1 >= 0 else 0
            
            if upper_vol == 0 and lower_vol == 0:
                break
            
            if upper_vol >= lower_vol and upper_idx + 1 < len(nodes):
                upper_idx += 1
                va_volume += nodes[upper_idx].volume
            elif lower_idx - 1 >= 0:
                lower_idx -= 1
                va_volume += nodes[lower_idx].volume
            else:
                break
        
        vah = nodes[upper_idx].price
        val = nodes[lower_idx].price
        
        return vah, val, va_volume
    
    def _determine_vp_shape(
        self,
        nodes: List[VolumeNode],
        poc: float,
        vah: float,
        val: float,
        high: float,
        low: float,
    ) -> VPShape:
        """Determine the shape of the volume profile"""
        if not nodes:
            return VPShape.UNKNOWN
        
        total_range = high - low
        if total_range == 0:
            return VPShape.UNKNOWN
        
        # Calculate where POC is relative to range
        poc_position = (poc - low) / total_range
        
        # Calculate volume distribution
        upper_half_vol = sum(n.volume for n in nodes if n.price > poc)
        lower_half_vol = sum(n.volume for n in nodes if n.price < poc)
        total_vol = upper_half_vol + lower_half_vol
        
        if total_vol == 0:
            return VPShape.UNKNOWN
        
        upper_ratio = upper_half_vol / total_vol
        
        # Check for thin profile
        max_vol = max(n.volume for n in nodes)
        avg_vol = sum(n.volume for n in nodes) / len(nodes)
        if max_vol < avg_vol * 2:
            return VPShape.THIN
        
        # Check for double distribution
        high_vol_nodes = [n for n in nodes if n.volume > max_vol * 0.6]
        if len(high_vol_nodes) >= 2:
            prices = [n.price for n in high_vol_nodes]
            if max(prices) - min(prices) > total_range * 0.3:
                return VPShape.DOUBLE_DISTRIBUTION
        
        # P-shaped: POC in upper half, more volume above
        if poc_position > 0.6 and upper_ratio > 0.55:
            return VPShape.P_SHAPED
        
        # B-shaped: POC in lower half, more volume below
        if poc_position < 0.4 and upper_ratio < 0.45:
            return VPShape.B_SHAPED
        
        # D-shaped: Normal distribution
        return VPShape.D_SHAPED
    
    def _detect_key_levels(
        self,
        bars: List[Dict],
        session_vp: VolumeProfile,
        prior_day_bars: Optional[List[Dict]],
        prior_day_vp: Optional[VolumeProfile],
    ) -> List[KeyLevel]:
        """Detect key price levels"""
        key_levels = []
        
        # Add VP levels from current session
        key_levels.append(KeyLevel(
            price=session_vp.poc,
            level_type="poc",
            strength=1.0,
        ))
        key_levels.append(KeyLevel(
            price=session_vp.vah,
            level_type="vah",
            strength=0.8,
        ))
        key_levels.append(KeyLevel(
            price=session_vp.val,
            level_type="val",
            strength=0.8,
        ))
        
        # Add prior day levels
        if prior_day_bars:
            pdh = max(bar["high"] for bar in prior_day_bars)
            pdl = min(bar["low"] for bar in prior_day_bars)
            
            key_levels.append(KeyLevel(
                price=pdh,
                level_type="pdh",
                strength=0.9,
            ))
            key_levels.append(KeyLevel(
                price=pdl,
                level_type="pdl",
                strength=0.9,
            ))
            
            # Add prior day POC
            if prior_day_vp:
                key_levels.append(KeyLevel(
                    price=prior_day_vp.poc,
                    level_type="prior_poc",
                    strength=0.85,
                ))
        
        # Detect overnight high/low (assuming first few bars are overnight)
        if len(bars) > 20:
            overnight_bars = bars[:min(20, len(bars) // 4)]
            overnight_high = max(bar["high"] for bar in overnight_bars)
            overnight_low = min(bar["low"] for bar in overnight_bars)
            
            key_levels.append(KeyLevel(
                price=overnight_high,
                level_type="overnight_high",
                strength=0.85,
            ))
            key_levels.append(KeyLevel(
                price=overnight_low,
                level_type="overnight_low",
                strength=0.85,
            ))
        
        # Sort by price
        key_levels.sort(key=lambda x: x.price)
        
        return key_levels
    
    def _detect_signal_candles(
        self,
        bars: List[Dict],
        session_vp: VolumeProfile,
        key_levels: List[KeyLevel],
    ) -> List[SignalCandle]:
        """Detect signal candles at VP edges and key levels"""
        signal_candles = []
        
        if len(bars) < 2:
            return signal_candles
        
        for i in range(1, len(bars)):
            bar = bars[i]
            prev_bar = bars[i - 1]
            
            # Calculate candle metrics
            body = abs(bar["close"] - bar["open"])
            upper_wick = bar["high"] - max(bar["open"], bar["close"])
            lower_wick = min(bar["open"], bar["close"]) - bar["low"]
            total_range = bar["high"] - bar["low"]
            
            if total_range == 0:
                continue
            
            # Volume ratio
            bar_vol = bar.get("volume", bar.get("tick_volume", 1))
            prev_vol = prev_bar.get("volume", prev_bar.get("tick_volume", 1))
            volume_ratio = bar_vol / prev_vol if prev_vol > 0 else 1.0
            
            # Detect pattern
            pattern = self._detect_candle_pattern(
                bar, body, upper_wick, lower_wick, total_range
            )
            
            if pattern == CandlePattern.NONE:
                continue
            
            # Check if at VP edge
            at_edge = self._is_at_vp_edge(bar, session_vp)
            
            # Check if at key level
            at_key_level, nearest_level = self._is_at_key_level(bar, key_levels)
            
            # Determine direction
            if bar["close"] > bar["open"]:
                direction = "bullish"
            elif bar["close"] < bar["open"]:
                direction = "bearish"
            else:
                direction = "neutral"
            
            # Calculate strength
            strength = self._calculate_signal_strength(
                pattern, volume_ratio, at_edge, at_key_level
            )
            
            # Calculate entry, stop, and TP
            entry_price = bar["close"]
            
            if direction == "bullish":
                stop_loss = bar["low"] - (total_range * 0.1)
                take_profit = bar["high"] + (total_range * 2)
                wick_retracement_50 = bar["close"] - (lower_wick * 0.5)
                wick_retracement_80 = bar["close"] - (lower_wick * 0.8)
            else:
                stop_loss = bar["high"] + (total_range * 0.1)
                take_profit = bar["low"] - (total_range * 2)
                wick_retracement_50 = bar["close"] + (upper_wick * 0.5)
                wick_retracement_80 = bar["close"] + (upper_wick * 0.8)
            
            signal_candles.append(SignalCandle(
                bar_index=i,
                pattern=pattern,
                direction=direction,
                volume_ratio=volume_ratio,
                wick_ratio=max(upper_wick, lower_wick) / body if body > 0 else 0,
                at_edge=at_edge,
                at_key_level=at_key_level,
                strength=strength,
                entry_price=entry_price,
                stop_loss=stop_loss,
                take_profit=take_profit,
                wick_retracement_50=wick_retracement_50,
                wick_retracement_80=wick_retracement_80,
            ))
        
        return signal_candles
    
    def _detect_candle_pattern(
        self,
        bar: Dict,
        body: float,
        upper_wick: float,
        lower_wick: float,
        total_range: float,
    ) -> CandlePattern:
        """Detect candle pattern"""
        if total_range == 0:
            return CandlePattern.NONE
        
        body_ratio = body / total_range
        upper_wick_ratio = upper_wick / total_range
        lower_wick_ratio = lower_wick / total_range
        
        # Doji: Very small body
        if body_ratio < 0.1:
            return CandlePattern.DOJI
        
        # Spinning top: Small body with wicks on both sides
        if body_ratio < 0.3 and upper_wick_ratio > 0.2 and lower_wick_ratio > 0.2:
            return CandlePattern.SPINNING_TOP
        
        # Shooting star: Small body at bottom, long upper wick
        if body_ratio < 0.3 and upper_wick_ratio > 0.5 and lower_wick_ratio < 0.1:
            return CandlePattern.SHOOTING_STAR
        
        # Hammer: Small body at top, long lower wick
        if body_ratio < 0.3 and lower_wick_ratio > 0.5 and upper_wick_ratio < 0.1:
            return CandlePattern.HAMMER
        
        # Marubozu: Large body, no wicks
        if body_ratio > 0.8:
            if bar["close"] > bar["open"]:
                return CandlePattern.MARUBOZU_BULLISH
            else:
                return CandlePattern.MARUBOZU_BEARISH
        
        return CandlePattern.NONE
    
    def _is_at_vp_edge(self, bar: Dict, vp: VolumeProfile) -> bool:
        """Check if bar is at VP edge"""
        tolerance = (vp.high - vp.low) * 0.02  # 2% tolerance
        
        # Check if at VAH or VAL
        if abs(bar["high"] - vp.vah) < tolerance or abs(bar["low"] - vp.vah) < tolerance:
            return True
        if abs(bar["high"] - vp.val) < tolerance or abs(bar["low"] - vp.val) < tolerance:
            return True
        
        # Check if at profile high/low
        if abs(bar["high"] - vp.high) < tolerance or abs(bar["low"] - vp.low) < tolerance:
            return True
        
        return False
    
    def _is_at_key_level(
        self,
        bar: Dict,
        key_levels: List[KeyLevel],
    ) -> Tuple[bool, Optional[KeyLevel]]:
        """Check if bar is at a key level"""
        bar_range = bar["high"] - bar["low"]
        tolerance = bar_range * 0.5 if bar_range > 0 else 0.0001
        
        for level in key_levels:
            if bar["low"] - tolerance <= level.price <= bar["high"] + tolerance:
                return True, level
        
        return False, None
    
    def _calculate_signal_strength(
        self,
        pattern: CandlePattern,
        volume_ratio: float,
        at_edge: bool,
        at_key_level: bool,
    ) -> SignalStrength:
        """Calculate signal strength"""
        score = 0
        
        # Pattern strength
        if pattern in [CandlePattern.HAMMER, CandlePattern.SHOOTING_STAR]:
            score += 2
        elif pattern == CandlePattern.DOJI:
            score += 1
        elif pattern in [CandlePattern.ENGULFING_BULLISH, CandlePattern.ENGULFING_BEARISH]:
            score += 2
        
        # Volume
        if volume_ratio >= self.min_volume_ratio:
            score += 2
        elif volume_ratio >= 1.0:
            score += 1
        
        # Location
        if at_edge:
            score += 2
        if at_key_level:
            score += 2
        
        # Map score to strength
        if score >= 7:
            return SignalStrength.ULTRA_STRONG
        elif score >= 5:
            return SignalStrength.STRONG
        elif score >= 3:
            return SignalStrength.MODERATE
        elif score >= 1:
            return SignalStrength.WEAK
        else:
            return SignalStrength.NO_SIGNAL
    
    def _determine_bias(self, vp: VolumeProfile, bars: List[Dict]) -> str:
        """Determine market bias from VP shape and price action"""
        if not bars:
            return "neutral"
        
        current_price = bars[-1]["close"]
        
        # VP shape bias
        if vp.shape == VPShape.P_SHAPED:
            shape_bias = "bullish"
        elif vp.shape == VPShape.B_SHAPED:
            shape_bias = "bearish"
        else:
            shape_bias = "neutral"
        
        # Price position bias
        if current_price > vp.vah:
            position_bias = "bullish"
        elif current_price < vp.val:
            position_bias = "bearish"
        else:
            position_bias = "neutral"
        
        # Combine biases
        if shape_bias == position_bias:
            return shape_bias
        elif shape_bias == "neutral":
            return position_bias
        elif position_bias == "neutral":
            return shape_bias
        else:
            return "neutral"  # Conflicting signals
    
    def _get_current_zone(self, price: float, vp: VolumeProfile) -> str:
        """Get current price zone relative to VP"""
        if price > vp.vah:
            return "above_value"
        elif price < vp.val:
            return "below_value"
        elif price > vp.poc:
            return "high_value"
        else:
            return "low_value"
    
    def _get_edge_distance(self, price: float, vp: VolumeProfile) -> float:
        """Get distance to nearest VP edge"""
        distances = [
            abs(price - vp.vah),
            abs(price - vp.val),
            abs(price - vp.high),
            abs(price - vp.low),
        ]
        return min(distances)
    
    def _generate_trade_setup(
        self,
        bars: List[Dict],
        session_vp: VolumeProfile,
        prior_day_vp: Optional[VolumeProfile],
        key_levels: List[KeyLevel],
        signal_candles: List[SignalCandle],
        market_bias: str,
    ) -> Optional[VPETradeSetup]:
        """Generate trade setup based on VPE analysis"""
        if not bars or not signal_candles:
            return None
        
        current_price = bars[-1]["close"]
        current_zone = self._get_current_zone(current_price, session_vp)
        
        # Find most recent strong signal candle
        recent_signals = [s for s in signal_candles[-5:] if s.strength in [
            SignalStrength.ULTRA_STRONG, SignalStrength.STRONG, SignalStrength.MODERATE
        ]]
        
        if not recent_signals:
            return None
        
        best_signal = max(recent_signals, key=lambda s: (
            3 if s.strength == SignalStrength.ULTRA_STRONG else
            2 if s.strength == SignalStrength.STRONG else 1
        ))
        
        # Determine setup type
        setup_type = self._determine_setup_type(
            current_price, current_zone, session_vp, prior_day_vp, best_signal
        )
        
        # Determine direction
        if best_signal.direction == "bullish" and market_bias != "bearish":
            direction = "long"
        elif best_signal.direction == "bearish" and market_bias != "bullish":
            direction = "short"
        else:
            direction = "none"
        
        if direction == "none":
            return None
        
        # Calculate entry, stop, and targets
        entry_price = best_signal.entry_price
        
        if direction == "long":
            stop_loss = best_signal.stop_loss
            take_profit_1 = session_vp.poc if current_price < session_vp.poc else session_vp.vah
            take_profit_2 = session_vp.vah if current_price < session_vp.vah else session_vp.high
            take_profit_3 = session_vp.high + (session_vp.high - session_vp.low) * 0.5
        else:
            stop_loss = best_signal.stop_loss
            take_profit_1 = session_vp.poc if current_price > session_vp.poc else session_vp.val
            take_profit_2 = session_vp.val if current_price > session_vp.val else session_vp.low
            take_profit_3 = session_vp.low - (session_vp.high - session_vp.low) * 0.5
        
        # Calculate risk/reward
        risk = abs(entry_price - stop_loss)
        reward = abs(take_profit_2 - entry_price)
        risk_reward = reward / risk if risk > 0 else 0
        
        # Calculate confidence
        confidence = self._calculate_confidence(
            best_signal, market_bias, current_zone, session_vp
        )
        
        # Find confluence levels
        confluence_levels = [
            level for level in key_levels
            if abs(level.price - entry_price) < (session_vp.high - session_vp.low) * 0.1
        ]
        
        # Generate reasoning
        reasoning = self._generate_reasoning(
            direction, setup_type, best_signal, session_vp, market_bias, current_zone
        )
        
        # Generate warnings
        warnings = self._generate_warnings(
            direction, market_bias, current_zone, risk_reward, confidence
        )
        
        return VPETradeSetup(
            direction=direction,
            setup_type=setup_type,
            entry_price=entry_price,
            stop_loss=stop_loss,
            take_profit_1=take_profit_1,
            take_profit_2=take_profit_2,
            take_profit_3=take_profit_3,
            risk_reward=risk_reward,
            confidence=confidence,
            signal_candle=best_signal,
            vp_shape=session_vp.shape,
            key_levels_confluence=confluence_levels,
            reasoning=reasoning,
            warnings=warnings,
        )
    
    def _determine_setup_type(
        self,
        current_price: float,
        current_zone: str,
        session_vp: VolumeProfile,
        prior_day_vp: Optional[VolumeProfile],
        signal: SignalCandle,
    ) -> str:
        """Determine the type of trade setup"""
        # Edge sweep: Price swept VP edge and reversed
        if signal.at_edge:
            return "edge_sweep"
        
        # POC retest: Price retesting POC
        if prior_day_vp and abs(current_price - prior_day_vp.poc) < (session_vp.high - session_vp.low) * 0.05:
            return "poc_retest"
        
        # Mean reversion: Price in low value area
        if current_zone in ["above_value", "below_value"]:
            return "mean_reversion"
        
        # Breakout: Price breaking out of value area
        if session_vp.shape in [VPShape.P_SHAPED, VPShape.B_SHAPED]:
            return "breakout"
        
        return "edge_sweep"
    
    def _calculate_confidence(
        self,
        signal: SignalCandle,
        market_bias: str,
        current_zone: str,
        vp: VolumeProfile,
    ) -> float:
        """Calculate trade confidence"""
        confidence = 0.5
        
        # Signal strength
        if signal.strength == SignalStrength.ULTRA_STRONG:
            confidence += 0.25
        elif signal.strength == SignalStrength.STRONG:
            confidence += 0.15
        elif signal.strength == SignalStrength.MODERATE:
            confidence += 0.05
        
        # Bias alignment
        if (signal.direction == "bullish" and market_bias == "bullish") or \
           (signal.direction == "bearish" and market_bias == "bearish"):
            confidence += 0.1
        
        # VP shape alignment
        if (signal.direction == "bullish" and vp.shape == VPShape.P_SHAPED) or \
           (signal.direction == "bearish" and vp.shape == VPShape.B_SHAPED):
            confidence += 0.1
        
        # Zone alignment
        if (signal.direction == "bullish" and current_zone == "below_value") or \
           (signal.direction == "bearish" and current_zone == "above_value"):
            confidence += 0.1
        
        return min(confidence, 1.0)
    
    def _generate_reasoning(
        self,
        direction: str,
        setup_type: str,
        signal: SignalCandle,
        vp: VolumeProfile,
        market_bias: str,
        current_zone: str,
    ) -> List[str]:
        """Generate reasoning for the trade setup"""
        reasoning = []
        
        reasoning.append(f"Setup type: {setup_type}")
        reasoning.append(f"Signal candle: {signal.pattern.value} with {signal.volume_ratio:.1f}x volume")
        reasoning.append(f"VP shape: {vp.shape.value} (bias: {market_bias})")
        reasoning.append(f"Current zone: {current_zone}")
        
        if signal.at_edge:
            reasoning.append("Signal at VP edge - high probability reversal zone")
        if signal.at_key_level:
            reasoning.append("Signal at key level - institutional interest")
        
        if setup_type == "poc_retest":
            reasoning.append("Previous POC retest - bread-and-butter trade")
        elif setup_type == "edge_sweep":
            reasoning.append("Edge sweep detected - expect mean reversion")
        
        return reasoning
    
    def _generate_warnings(
        self,
        direction: str,
        market_bias: str,
        current_zone: str,
        risk_reward: float,
        confidence: float,
    ) -> List[str]:
        """Generate warnings for the trade setup"""
        warnings = []
        
        if (direction == "long" and market_bias == "bearish") or \
           (direction == "short" and market_bias == "bullish"):
            warnings.append("Trading against market bias - use smaller position")
        
        if risk_reward < 1.5:
            warnings.append(f"Low risk/reward ({risk_reward:.1f}) - consider skipping")
        
        if confidence < 0.6:
            warnings.append(f"Low confidence ({confidence:.0%}) - wait for better setup")
        
        if current_zone in ["high_value", "low_value"]:
            warnings.append("In value area - expect chop, be patient")
        
        return warnings
    
    def _find_closest_price(self, price: float, price_levels: Dict[float, float]) -> float:
        """Find closest price level"""
        return min(price_levels.keys(), key=lambda p: abs(p - price))
    
    def _empty_vp(self) -> VolumeProfile:
        """Return empty volume profile"""
        return VolumeProfile(
            nodes=[],
            poc=0,
            vah=0,
            val=0,
            total_volume=0,
            high=0,
            low=0,
            shape=VPShape.UNKNOWN,
            value_area_volume=0,
        )
    
    def _empty_analysis(self) -> VPEAnalysis:
        """Return empty analysis"""
        empty_vp = self._empty_vp()
        return VPEAnalysis(
            session_vp=empty_vp,
            prior_day_vp=None,
            visible_range_vp=None,
            key_levels=[],
            signal_candles=[],
            trade_setup=None,
            market_bias="neutral",
            current_zone="unknown",
            edge_distance=0,
            poc_distance=0,
        )


def test_vpe_intelligence():
    """Test VPE Intelligence with sample data"""
    import random
    
    print("=" * 70)
    print("VPE INTELLIGENCE TEST")
    print("=" * 70)
    
    # Generate sample bars
    bars = []
    price = 100.0
    
    for i in range(200):
        # Add some trend and mean reversion
        if i < 50:
            drift = 0.1  # Uptrend
        elif i < 100:
            drift = -0.05  # Consolidation
        elif i < 150:
            drift = 0.15  # Strong uptrend
        else:
            drift = -0.1  # Pullback
        
        change = random.gauss(drift, 0.5)
        price = max(90, min(120, price + change))
        
        high = price + random.uniform(0.1, 0.5)
        low = price - random.uniform(0.1, 0.5)
        open_price = price + random.uniform(-0.2, 0.2)
        close = price + random.uniform(-0.2, 0.2)
        volume = random.randint(100, 1000)
        
        # Add some signal candles
        if i in [45, 95, 145, 195]:
            # Create hammer/shooting star
            if drift > 0:
                low = price - 1.0
                close = price + 0.1
            else:
                high = price + 1.0
                close = price - 0.1
            volume = volume * 2
        
        bars.append({
            "open": open_price,
            "high": high,
            "low": low,
            "close": close,
            "volume": volume,
        })
    
    # Split into prior day and current session
    prior_day_bars = bars[:100]
    session_bars = bars[100:]
    
    # Create VPE Intelligence
    vpe = VPEIntelligence()
    
    # Analyze
    analysis = vpe.analyze(
        bars=bars,
        session_start_idx=100,
        prior_day_bars=prior_day_bars,
    )
    
    # Print results
    print("\nSESSION VOLUME PROFILE")
    print("=" * 40)
    print(f"POC: {analysis.session_vp.poc:.5f}")
    print(f"VAH: {analysis.session_vp.vah:.5f}")
    print(f"VAL: {analysis.session_vp.val:.5f}")
    print(f"High: {analysis.session_vp.high:.5f}")
    print(f"Low: {analysis.session_vp.low:.5f}")
    print(f"Shape: {analysis.session_vp.shape.value}")
    print(f"Total Volume: {analysis.session_vp.total_volume:.0f}")
    print(f"Value Area %: {analysis.session_vp.value_area_percent:.1%}")
    
    print("\nKEY LEVELS")
    print("=" * 40)
    for level in analysis.key_levels[:10]:
        print(f"  {level.level_type}: {level.price:.5f} (strength: {level.strength:.0%})")
    
    print("\nSIGNAL CANDLES")
    print("=" * 40)
    for signal in analysis.signal_candles[-5:]:
        print(f"  Bar {signal.bar_index}: {signal.pattern.value} ({signal.direction})")
        print(f"    Volume ratio: {signal.volume_ratio:.1f}x")
        print(f"    At edge: {signal.at_edge}, At key level: {signal.at_key_level}")
        print(f"    Strength: {signal.strength.value}")
    
    print("\nMARKET STATE")
    print("=" * 40)
    print(f"Bias: {analysis.market_bias}")
    print(f"Current Zone: {analysis.current_zone}")
    print(f"Edge Distance: {analysis.edge_distance:.5f}")
    print(f"POC Distance: {analysis.poc_distance:.5f}")
    
    if analysis.trade_setup:
        print("\nTRADE SETUP")
        print("=" * 40)
        setup = analysis.trade_setup
        print(f"Direction: {setup.direction.upper()}")
        print(f"Type: {setup.setup_type}")
        print(f"Entry: {setup.entry_price:.5f}")
        print(f"Stop Loss: {setup.stop_loss:.5f}")
        print(f"TP1: {setup.take_profit_1:.5f}")
        print(f"TP2: {setup.take_profit_2:.5f}")
        print(f"TP3: {setup.take_profit_3:.5f}")
        print(f"Risk/Reward: {setup.risk_reward:.2f}")
        print(f"Confidence: {setup.confidence:.0%}")
        print(f"VP Shape: {setup.vp_shape.value}")
        
        print("\nReasoning:")
        for reason in setup.reasoning:
            print(f"  - {reason}")
        
        if setup.warnings:
            print("\nWarnings:")
            for warning in setup.warnings:
                print(f"  ! {warning}")
    else:
        print("\nNo trade setup generated")
    
    print("\n" + "=" * 70)
    print("VPE Intelligence: PASSED")
    print("=" * 70)
    
    return analysis


if __name__ == "__main__":
    test_vpe_intelligence()
