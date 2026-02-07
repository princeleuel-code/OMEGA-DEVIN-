"""
Institutional Flow Detection Intelligence

This module implements the ability to detect INSTITUTIONAL FLOW - the holy grail of trading.

Key Capabilities:
1. Large Order Detection - Identify big players from price action
2. Accumulation/Distribution Phase Detection - Know BEFORE the move happens
3. Smart Money vs Retail Flow Separation - Filter out the noise
4. Institutional Entry/Exit Zone Prediction - Trade with the big boys

This is what separates retail traders from institutional traders.
The ability to see what smart money is doing BEFORE the move.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple, Any
from enum import Enum
from datetime import datetime, timedelta
import math


class InstitutionalActivity(Enum):
    """Types of institutional activity"""
    ACCUMULATION = "accumulation"  # Smart money buying
    DISTRIBUTION = "distribution"  # Smart money selling
    MARKUP = "markup"  # Price moving up after accumulation
    MARKDOWN = "markdown"  # Price moving down after distribution
    NEUTRAL = "neutral"  # No clear institutional activity


class OrderFlowType(Enum):
    """Types of order flow"""
    SMART_MONEY_BUY = "smart_money_buy"
    SMART_MONEY_SELL = "smart_money_sell"
    RETAIL_BUY = "retail_buy"
    RETAIL_SELL = "retail_sell"
    MIXED = "mixed"


class LiquidityType(Enum):
    """Types of liquidity"""
    BUY_SIDE = "buy_side"  # Stop losses above price
    SELL_SIDE = "sell_side"  # Stop losses below price
    BOTH = "both"


class IcebergType(Enum):
    """Iceberg order detection"""
    BUYING_ICEBERG = "buying_iceberg"  # Hidden buy orders
    SELLING_ICEBERG = "selling_iceberg"  # Hidden sell orders
    NONE = "none"


@dataclass
class LargeOrderSignature:
    """Signature of a large institutional order"""
    timestamp: datetime
    price_level: float
    estimated_size: float  # Relative size (1.0 = normal, 2.0 = 2x normal)
    direction: str  # "BUY" or "SELL"
    confidence: float
    
    # Detection method
    detection_method: str  # "volume_spike", "price_rejection", "absorption", "sweep"
    
    # Impact
    price_impact: float  # How much price moved
    volume_ratio: float  # Volume vs average
    
    # Context
    at_key_level: bool
    level_type: str  # "support", "resistance", "poc", "vah", "val"


@dataclass
class AccumulationDistributionPhase:
    """Detected accumulation or distribution phase"""
    phase_type: InstitutionalActivity
    start_time: datetime
    end_time: Optional[datetime]
    price_range: Tuple[float, float]  # (low, high)
    
    # Phase characteristics
    volume_profile: str  # "increasing", "decreasing", "steady"
    price_action: str  # "ranging", "slight_up", "slight_down"
    
    # Wyckoff events detected
    spring_detected: bool  # False breakout down (accumulation)
    upthrust_detected: bool  # False breakout up (distribution)
    test_detected: bool  # Test of supply/demand
    
    # Confidence
    confidence: float
    reasoning: List[str]


@dataclass
class SmartMoneyZone:
    """Zone where smart money is active"""
    zone_type: str  # "entry", "exit", "accumulation", "distribution"
    price_low: float
    price_high: float
    
    # Activity
    institutional_activity: InstitutionalActivity
    estimated_position_size: float  # Relative
    
    # Timing
    first_detected: datetime
    last_activity: datetime
    activity_count: int
    
    # Strength
    strength: float  # 0-1
    times_tested: int
    held: bool  # Did price hold at this zone?


@dataclass
class LiquidityPool:
    """Detected liquidity pool (stop losses)"""
    liquidity_type: LiquidityType
    price_level: float
    estimated_size: float  # Relative
    
    # Detection
    detection_method: str  # "swing_high", "swing_low", "round_number", "previous_day"
    
    # Status
    swept: bool
    sweep_time: Optional[datetime]
    
    # Prediction
    likely_target: bool  # Is this likely to be targeted?
    distance_from_current: float


@dataclass
class InstitutionalFlowAnalysis:
    """Complete institutional flow analysis"""
    # Current activity
    current_activity: InstitutionalActivity
    activity_confidence: float
    
    # Large orders detected
    large_orders: List[LargeOrderSignature]
    recent_large_order: Optional[LargeOrderSignature]
    
    # Accumulation/Distribution
    current_phase: Optional[AccumulationDistributionPhase]
    phase_progress: float  # 0-1, how far into the phase
    
    # Smart money zones
    smart_money_zones: List[SmartMoneyZone]
    nearest_entry_zone: Optional[SmartMoneyZone]
    nearest_exit_zone: Optional[SmartMoneyZone]
    
    # Liquidity
    liquidity_pools: List[LiquidityPool]
    likely_liquidity_target: Optional[LiquidityPool]
    
    # Order flow classification
    current_flow_type: OrderFlowType
    smart_money_direction: str  # "LONG", "SHORT", "NEUTRAL"
    retail_direction: str  # Often opposite of smart money
    
    # Iceberg detection
    iceberg_detected: IcebergType
    
    # Signal
    signal: str  # "LONG", "SHORT", "NEUTRAL"
    signal_strength: float
    confidence: float
    
    # Reasoning
    reasoning: List[str]
    
    # Divergences (for intermarket analysis) - optional with defaults
    divergences: List[Any] = field(default_factory=list)
    significant_divergence: Optional[Any] = None


class InstitutionalFlowDetection:
    """
    Institutional Flow Detection Intelligence
    
    Detects what smart money is doing by analyzing:
    1. Volume patterns - Large orders leave footprints
    2. Price action - Institutional activity creates specific patterns
    3. Liquidity - Smart money hunts liquidity
    4. Absorption - When large orders absorb selling/buying pressure
    5. Wyckoff phases - Accumulation and distribution patterns
    
    This is the edge that separates profitable traders from the rest.
    """
    
    # Volume thresholds
    LARGE_ORDER_VOLUME_RATIO = 2.0  # 2x average volume
    ICEBERG_DETECTION_THRESHOLD = 1.5  # Consistent above-average volume
    
    # Price action thresholds
    ABSORPTION_THRESHOLD = 0.3  # Price moves less than 30% of expected
    SWEEP_THRESHOLD = 0.002  # 0.2% beyond level then reversal
    
    # Phase detection
    MIN_PHASE_BARS = 10  # Minimum bars for phase detection
    ACCUMULATION_VOLUME_INCREASE = 1.2  # 20% volume increase
    
    def __init__(self):
        """Initialize Institutional Flow Detection"""
        self.detected_zones: List[SmartMoneyZone] = []
        self.detected_phases: List[AccumulationDistributionPhase] = []
        self.large_order_history: List[LargeOrderSignature] = []
    
    def analyze(
        self,
        bars: List[Dict[str, Any]],
        volume_profile: Optional[Dict[str, Any]] = None,
        delta_data: Optional[List[float]] = None
    ) -> InstitutionalFlowAnalysis:
        """
        Perform complete institutional flow analysis
        
        Args:
            bars: OHLCV bars
            volume_profile: Volume profile data (POC, VAH, VAL)
            delta_data: Delta (buy volume - sell volume) per bar
            
        Returns:
            InstitutionalFlowAnalysis with complete detection results
        """
        if len(bars) < 20:
            return self._empty_analysis()
        
        reasoning = []
        
        # 1. Detect large orders
        large_orders = self._detect_large_orders(bars, volume_profile)
        recent_large_order = large_orders[-1] if large_orders else None
        
        if recent_large_order:
            reasoning.append(f"Large {recent_large_order.direction} order detected at {recent_large_order.price_level:.5f}")
        
        # 2. Detect accumulation/distribution phase
        current_phase = self._detect_phase(bars)
        phase_progress = 0.0
        
        if current_phase:
            reasoning.append(f"{current_phase.phase_type.value.upper()} phase detected ({current_phase.confidence:.0%} confidence)")
            # Calculate progress
            if current_phase.end_time:
                total_duration = (current_phase.end_time - current_phase.start_time).total_seconds()
                elapsed = (datetime.utcnow() - current_phase.start_time).total_seconds()
                phase_progress = min(1.0, elapsed / total_duration) if total_duration > 0 else 0.5
        
        # 3. Detect smart money zones
        smart_money_zones = self._detect_smart_money_zones(bars, large_orders)
        current_price = bars[-1]["close"]
        
        # Find nearest zones
        nearest_entry = None
        nearest_exit = None
        for zone in smart_money_zones:
            if zone.zone_type == "entry":
                if nearest_entry is None or abs(zone.price_low - current_price) < abs(nearest_entry.price_low - current_price):
                    nearest_entry = zone
            elif zone.zone_type == "exit":
                if nearest_exit is None or abs(zone.price_high - current_price) < abs(nearest_exit.price_high - current_price):
                    nearest_exit = zone
        
        if nearest_entry:
            reasoning.append(f"Smart money entry zone at {nearest_entry.price_low:.5f}-{nearest_entry.price_high:.5f}")
        
        # 4. Detect liquidity pools
        liquidity_pools = self._detect_liquidity_pools(bars)
        likely_target = None
        
        for pool in liquidity_pools:
            if pool.likely_target and not pool.swept:
                likely_target = pool
                reasoning.append(f"Liquidity pool at {pool.price_level:.5f} likely to be targeted")
                break
        
        # 5. Classify order flow
        flow_type, smart_direction, retail_direction = self._classify_order_flow(
            bars, delta_data, large_orders
        )
        
        reasoning.append(f"Order flow: {flow_type.value} (Smart: {smart_direction}, Retail: {retail_direction})")
        
        # 6. Detect iceberg orders
        iceberg = self._detect_iceberg(bars, delta_data)
        
        if iceberg != IcebergType.NONE:
            reasoning.append(f"Iceberg order detected: {iceberg.value}")
        
        # 7. Determine current institutional activity
        current_activity = self._determine_activity(
            current_phase, large_orders, flow_type, smart_direction
        )
        
        # 8. Generate signal
        signal, signal_strength, confidence = self._generate_signal(
            current_activity, smart_direction, current_phase, large_orders, liquidity_pools
        )
        
        return InstitutionalFlowAnalysis(
            current_activity=current_activity,
            activity_confidence=confidence,
            large_orders=large_orders,
            recent_large_order=recent_large_order,
            current_phase=current_phase,
            phase_progress=phase_progress,
            smart_money_zones=smart_money_zones,
            nearest_entry_zone=nearest_entry,
            nearest_exit_zone=nearest_exit,
            liquidity_pools=liquidity_pools,
            likely_liquidity_target=likely_target,
            current_flow_type=flow_type,
            smart_money_direction=smart_direction,
            retail_direction=retail_direction,
            iceberg_detected=iceberg,
            signal=signal,
            signal_strength=signal_strength,
            confidence=confidence,
            reasoning=reasoning
        )
    
    def _detect_large_orders(
        self,
        bars: List[Dict[str, Any]],
        volume_profile: Optional[Dict[str, Any]]
    ) -> List[LargeOrderSignature]:
        """Detect large institutional orders from price/volume action"""
        large_orders = []
        
        # Calculate average volume
        volumes = [b.get("volume", 0) for b in bars]
        avg_volume = sum(volumes) / len(volumes) if volumes else 1
        
        for i in range(5, len(bars)):
            bar = bars[i]
            volume = bar.get("volume", 0)
            
            # Check for volume spike
            if volume > avg_volume * self.LARGE_ORDER_VOLUME_RATIO:
                # Determine direction from price action
                open_price = bar["open"]
                close_price = bar["close"]
                high = bar["high"]
                low = bar["low"]
                
                # Calculate body and wicks
                body = abs(close_price - open_price)
                upper_wick = high - max(open_price, close_price)
                lower_wick = min(open_price, close_price) - low
                total_range = high - low
                
                if total_range == 0:
                    continue
                
                # Determine direction
                if close_price > open_price:
                    direction = "BUY"
                    # Check for absorption (large volume but small body)
                    if body / total_range < self.ABSORPTION_THRESHOLD:
                        detection_method = "absorption"
                    else:
                        detection_method = "volume_spike"
                else:
                    direction = "SELL"
                    if body / total_range < self.ABSORPTION_THRESHOLD:
                        detection_method = "absorption"
                    else:
                        detection_method = "volume_spike"
                
                # Check if at key level
                at_key_level = False
                level_type = "none"
                
                if volume_profile:
                    poc = volume_profile.get("poc", 0)
                    vah = volume_profile.get("vah", 0)
                    val = volume_profile.get("val", 0)
                    
                    price_tolerance = total_range * 2
                    
                    if abs(close_price - poc) < price_tolerance:
                        at_key_level = True
                        level_type = "poc"
                    elif abs(close_price - vah) < price_tolerance:
                        at_key_level = True
                        level_type = "vah"
                    elif abs(close_price - val) < price_tolerance:
                        at_key_level = True
                        level_type = "val"
                
                large_orders.append(LargeOrderSignature(
                    timestamp=datetime.utcnow(),
                    price_level=close_price,
                    estimated_size=volume / avg_volume,
                    direction=direction,
                    confidence=min(1.0, (volume / avg_volume) / 3),
                    detection_method=detection_method,
                    price_impact=body,
                    volume_ratio=volume / avg_volume,
                    at_key_level=at_key_level,
                    level_type=level_type
                ))
        
        return large_orders
    
    def _detect_phase(self, bars: List[Dict[str, Any]]) -> Optional[AccumulationDistributionPhase]:
        """Detect accumulation or distribution phase using Wyckoff methodology"""
        if len(bars) < self.MIN_PHASE_BARS:
            return None
        
        # Analyze recent price action
        recent_bars = bars[-30:]
        
        # Calculate price range
        highs = [b["high"] for b in recent_bars]
        lows = [b["low"] for b in recent_bars]
        closes = [b["close"] for b in recent_bars]
        volumes = [b.get("volume", 0) for b in recent_bars]
        
        price_high = max(highs)
        price_low = min(lows)
        price_range = price_high - price_low
        
        if price_range == 0:
            return None
        
        # Check for ranging market (prerequisite for accumulation/distribution)
        avg_close = sum(closes) / len(closes)
        price_deviation = sum(abs(c - avg_close) for c in closes) / len(closes)
        is_ranging = price_deviation / avg_close < 0.01  # Less than 1% deviation
        
        if not is_ranging:
            return None
        
        # Analyze volume trend
        first_half_vol = sum(volumes[:len(volumes)//2])
        second_half_vol = sum(volumes[len(volumes)//2:])
        
        if second_half_vol > first_half_vol * self.ACCUMULATION_VOLUME_INCREASE:
            volume_profile = "increasing"
        elif second_half_vol < first_half_vol * 0.8:
            volume_profile = "decreasing"
        else:
            volume_profile = "steady"
        
        # Analyze price trend within range
        first_half_close = sum(closes[:len(closes)//2]) / (len(closes)//2)
        second_half_close = sum(closes[len(closes)//2:]) / (len(closes) - len(closes)//2)
        
        if second_half_close > first_half_close * 1.002:
            price_action = "slight_up"
        elif second_half_close < first_half_close * 0.998:
            price_action = "slight_down"
        else:
            price_action = "ranging"
        
        # Detect Wyckoff events
        spring_detected = False
        upthrust_detected = False
        test_detected = False
        
        # Check for spring (false breakout below support)
        for i in range(len(recent_bars) - 5, len(recent_bars)):
            if recent_bars[i]["low"] < price_low * 0.999:  # Broke below
                if recent_bars[i]["close"] > price_low:  # Closed back above
                    spring_detected = True
                    break
        
        # Check for upthrust (false breakout above resistance)
        for i in range(len(recent_bars) - 5, len(recent_bars)):
            if recent_bars[i]["high"] > price_high * 1.001:  # Broke above
                if recent_bars[i]["close"] < price_high:  # Closed back below
                    upthrust_detected = True
                    break
        
        # Determine phase type
        reasoning = []
        
        if spring_detected and volume_profile == "increasing" and price_action in ["slight_up", "ranging"]:
            phase_type = InstitutionalActivity.ACCUMULATION
            confidence = 0.8
            reasoning.append("Spring detected with increasing volume - ACCUMULATION")
        elif upthrust_detected and volume_profile == "increasing" and price_action in ["slight_down", "ranging"]:
            phase_type = InstitutionalActivity.DISTRIBUTION
            confidence = 0.8
            reasoning.append("Upthrust detected with increasing volume - DISTRIBUTION")
        elif volume_profile == "increasing" and price_action == "slight_up":
            phase_type = InstitutionalActivity.ACCUMULATION
            confidence = 0.6
            reasoning.append("Increasing volume with slight upward bias - possible ACCUMULATION")
        elif volume_profile == "increasing" and price_action == "slight_down":
            phase_type = InstitutionalActivity.DISTRIBUTION
            confidence = 0.6
            reasoning.append("Increasing volume with slight downward bias - possible DISTRIBUTION")
        else:
            return None
        
        return AccumulationDistributionPhase(
            phase_type=phase_type,
            start_time=datetime.utcnow() - timedelta(minutes=len(recent_bars)),
            end_time=None,
            price_range=(price_low, price_high),
            volume_profile=volume_profile,
            price_action=price_action,
            spring_detected=spring_detected,
            upthrust_detected=upthrust_detected,
            test_detected=test_detected,
            confidence=confidence,
            reasoning=reasoning
        )
    
    def _detect_smart_money_zones(
        self,
        bars: List[Dict[str, Any]],
        large_orders: List[LargeOrderSignature]
    ) -> List[SmartMoneyZone]:
        """Detect zones where smart money is active"""
        zones = []
        
        # Group large orders by price level
        price_clusters: Dict[float, List[LargeOrderSignature]] = {}
        
        for order in large_orders:
            # Round to nearest price level
            price_key = round(order.price_level, 4)
            
            # Find existing cluster within tolerance
            found_cluster = False
            for existing_key in price_clusters.keys():
                if abs(existing_key - price_key) < 0.0005:  # 5 pip tolerance
                    price_clusters[existing_key].append(order)
                    found_cluster = True
                    break
            
            if not found_cluster:
                price_clusters[price_key] = [order]
        
        # Create zones from clusters
        for price_level, orders in price_clusters.items():
            if len(orders) < 2:
                continue
            
            # Determine zone type based on order directions
            buy_orders = sum(1 for o in orders if o.direction == "BUY")
            sell_orders = sum(1 for o in orders if o.direction == "SELL")
            
            if buy_orders > sell_orders:
                zone_type = "entry"
                activity = InstitutionalActivity.ACCUMULATION
            else:
                zone_type = "exit"
                activity = InstitutionalActivity.DISTRIBUTION
            
            # Calculate zone boundaries
            prices = [o.price_level for o in orders]
            zone_low = min(prices) * 0.9995
            zone_high = max(prices) * 1.0005
            
            # Calculate strength
            total_size = sum(o.estimated_size for o in orders)
            strength = min(1.0, total_size / 10)
            
            zones.append(SmartMoneyZone(
                zone_type=zone_type,
                price_low=zone_low,
                price_high=zone_high,
                institutional_activity=activity,
                estimated_position_size=total_size,
                first_detected=orders[0].timestamp,
                last_activity=orders[-1].timestamp,
                activity_count=len(orders),
                strength=strength,
                times_tested=len(orders),
                held=True
            ))
        
        return zones
    
    def _detect_liquidity_pools(self, bars: List[Dict[str, Any]]) -> List[LiquidityPool]:
        """Detect liquidity pools (stop loss clusters)"""
        pools = []
        current_price = bars[-1]["close"]
        
        # Find swing highs and lows
        for i in range(2, len(bars) - 2):
            # Swing high (liquidity above)
            if bars[i]["high"] > bars[i-1]["high"] and bars[i]["high"] > bars[i-2]["high"]:
                if bars[i]["high"] > bars[i+1]["high"] and bars[i]["high"] > bars[i+2]["high"]:
                    level = bars[i]["high"]
                    distance = (level - current_price) / current_price
                    
                    pools.append(LiquidityPool(
                        liquidity_type=LiquidityType.BUY_SIDE,
                        price_level=level,
                        estimated_size=1.0,
                        detection_method="swing_high",
                        swept=current_price > level,
                        sweep_time=None,
                        likely_target=distance > 0 and distance < 0.01,  # Within 1%
                        distance_from_current=distance
                    ))
            
            # Swing low (liquidity below)
            if bars[i]["low"] < bars[i-1]["low"] and bars[i]["low"] < bars[i-2]["low"]:
                if bars[i]["low"] < bars[i+1]["low"] and bars[i]["low"] < bars[i+2]["low"]:
                    level = bars[i]["low"]
                    distance = (current_price - level) / current_price
                    
                    pools.append(LiquidityPool(
                        liquidity_type=LiquidityType.SELL_SIDE,
                        price_level=level,
                        estimated_size=1.0,
                        detection_method="swing_low",
                        swept=current_price < level,
                        sweep_time=None,
                        likely_target=distance > 0 and distance < 0.01,  # Within 1%
                        distance_from_current=distance
                    ))
        
        # Sort by distance
        pools.sort(key=lambda p: abs(p.distance_from_current))
        
        return pools[:10]  # Return top 10 nearest
    
    def _classify_order_flow(
        self,
        bars: List[Dict[str, Any]],
        delta_data: Optional[List[float]],
        large_orders: List[LargeOrderSignature]
    ) -> Tuple[OrderFlowType, str, str]:
        """Classify order flow as smart money or retail"""
        # Analyze large orders (smart money)
        smart_buys = sum(1 for o in large_orders if o.direction == "BUY")
        smart_sells = sum(1 for o in large_orders if o.direction == "SELL")
        
        if smart_buys > smart_sells * 1.5:
            smart_direction = "LONG"
        elif smart_sells > smart_buys * 1.5:
            smart_direction = "SHORT"
        else:
            smart_direction = "NEUTRAL"
        
        # Analyze price action (often retail follows price)
        recent_bars = bars[-10:]
        price_change = (recent_bars[-1]["close"] - recent_bars[0]["close"]) / recent_bars[0]["close"]
        
        if price_change > 0.002:
            retail_direction = "LONG"
        elif price_change < -0.002:
            retail_direction = "SHORT"
        else:
            retail_direction = "NEUTRAL"
        
        # Determine flow type
        if smart_direction == "LONG" and retail_direction == "SHORT":
            flow_type = OrderFlowType.SMART_MONEY_BUY
        elif smart_direction == "SHORT" and retail_direction == "LONG":
            flow_type = OrderFlowType.SMART_MONEY_SELL
        elif smart_direction == retail_direction:
            if smart_direction == "LONG":
                flow_type = OrderFlowType.RETAIL_BUY
            elif smart_direction == "SHORT":
                flow_type = OrderFlowType.RETAIL_SELL
            else:
                flow_type = OrderFlowType.MIXED
        else:
            flow_type = OrderFlowType.MIXED
        
        return flow_type, smart_direction, retail_direction
    
    def _detect_iceberg(
        self,
        bars: List[Dict[str, Any]],
        delta_data: Optional[List[float]]
    ) -> IcebergType:
        """Detect iceberg orders (hidden large orders)"""
        if len(bars) < 10:
            return IcebergType.NONE
        
        recent_bars = bars[-10:]
        
        # Check for consistent above-average volume with small price movement
        volumes = [b.get("volume", 0) for b in recent_bars]
        avg_volume = sum(volumes) / len(volumes)
        
        # Count bars with above-average volume
        high_vol_bars = sum(1 for v in volumes if v > avg_volume * self.ICEBERG_DETECTION_THRESHOLD)
        
        if high_vol_bars < 5:
            return IcebergType.NONE
        
        # Check price movement
        price_change = abs(recent_bars[-1]["close"] - recent_bars[0]["close"])
        expected_change = sum(b["high"] - b["low"] for b in recent_bars) / len(recent_bars) * 5
        
        if price_change < expected_change * 0.3:  # Price moved less than expected
            # Determine direction from delta or price bias
            if delta_data and len(delta_data) >= 10:
                recent_delta = sum(delta_data[-10:])
                if recent_delta > 0:
                    return IcebergType.BUYING_ICEBERG
                else:
                    return IcebergType.SELLING_ICEBERG
            else:
                # Use price bias
                if recent_bars[-1]["close"] > recent_bars[0]["close"]:
                    return IcebergType.BUYING_ICEBERG
                else:
                    return IcebergType.SELLING_ICEBERG
        
        return IcebergType.NONE
    
    def _determine_activity(
        self,
        phase: Optional[AccumulationDistributionPhase],
        large_orders: List[LargeOrderSignature],
        flow_type: OrderFlowType,
        smart_direction: str
    ) -> InstitutionalActivity:
        """Determine current institutional activity"""
        # Phase takes priority
        if phase:
            return phase.phase_type
        
        # Check large orders
        if large_orders:
            recent_orders = large_orders[-5:]
            buy_count = sum(1 for o in recent_orders if o.direction == "BUY")
            sell_count = sum(1 for o in recent_orders if o.direction == "SELL")
            
            if buy_count > sell_count * 2:
                return InstitutionalActivity.ACCUMULATION
            elif sell_count > buy_count * 2:
                return InstitutionalActivity.DISTRIBUTION
        
        # Check flow type
        if flow_type == OrderFlowType.SMART_MONEY_BUY:
            return InstitutionalActivity.ACCUMULATION
        elif flow_type == OrderFlowType.SMART_MONEY_SELL:
            return InstitutionalActivity.DISTRIBUTION
        
        return InstitutionalActivity.NEUTRAL
    
    def _generate_signal(
        self,
        activity: InstitutionalActivity,
        smart_direction: str,
        phase: Optional[AccumulationDistributionPhase],
        large_orders: List[LargeOrderSignature],
        liquidity_pools: List[LiquidityPool]
    ) -> Tuple[str, float, float]:
        """Generate trading signal based on institutional flow"""
        signal = "NEUTRAL"
        strength = 0.5
        confidence = 0.5
        
        # Activity-based signal
        if activity == InstitutionalActivity.ACCUMULATION:
            signal = "LONG"
            strength = 0.7
            confidence = 0.6
        elif activity == InstitutionalActivity.DISTRIBUTION:
            signal = "SHORT"
            strength = 0.7
            confidence = 0.6
        elif activity == InstitutionalActivity.MARKUP:
            signal = "LONG"
            strength = 0.8
            confidence = 0.7
        elif activity == InstitutionalActivity.MARKDOWN:
            signal = "SHORT"
            strength = 0.8
            confidence = 0.7
        
        # Boost confidence if phase detected
        if phase:
            confidence = min(1.0, confidence + 0.1)
            if phase.spring_detected or phase.upthrust_detected:
                confidence = min(1.0, confidence + 0.1)
        
        # Boost if recent large orders align
        if large_orders:
            recent = large_orders[-3:]
            aligned = sum(1 for o in recent if 
                         (o.direction == "BUY" and signal == "LONG") or
                         (o.direction == "SELL" and signal == "SHORT"))
            if aligned >= 2:
                strength = min(1.0, strength + 0.1)
                confidence = min(1.0, confidence + 0.1)
        
        # Check liquidity targets
        for pool in liquidity_pools:
            if pool.likely_target and not pool.swept:
                if pool.liquidity_type == LiquidityType.BUY_SIDE and signal == "LONG":
                    strength = min(1.0, strength + 0.05)
                elif pool.liquidity_type == LiquidityType.SELL_SIDE and signal == "SHORT":
                    strength = min(1.0, strength + 0.05)
        
        return signal, strength, confidence
    
    def _empty_analysis(self) -> InstitutionalFlowAnalysis:
        """Return empty analysis when insufficient data"""
        return InstitutionalFlowAnalysis(
            current_activity=InstitutionalActivity.NEUTRAL,
            activity_confidence=0.0,
            large_orders=[],
            recent_large_order=None,
            current_phase=None,
            phase_progress=0.0,
            smart_money_zones=[],
            nearest_entry_zone=None,
            nearest_exit_zone=None,
            liquidity_pools=[],
            likely_liquidity_target=None,
            current_flow_type=OrderFlowType.MIXED,
            smart_money_direction="NEUTRAL",
            retail_direction="NEUTRAL",
            iceberg_detected=IcebergType.NONE,
            signal="NEUTRAL",
            signal_strength=0.0,
            confidence=0.0,
            reasoning=["Insufficient data for analysis"]
        )


def test_institutional_flow_detection():
    """Test the Institutional Flow Detection"""
    print("=" * 80)
    print("INSTITUTIONAL FLOW DETECTION TEST")
    print("=" * 80)
    
    # Generate sample data
    import random
    
    bars = []
    base_price = 1.1000
    
    for i in range(100):
        # Simulate accumulation phase with occasional volume spikes
        open_price = base_price + random.uniform(-0.001, 0.001)
        
        # Add some large volume bars (institutional activity)
        if i % 15 == 0:
            volume = random.uniform(2000, 5000)  # Large volume
            # Price absorption - large volume but small move
            close_price = open_price + random.uniform(-0.0002, 0.0005)
        else:
            volume = random.uniform(500, 1500)  # Normal volume
            close_price = open_price + random.uniform(-0.001, 0.001)
        
        high = max(open_price, close_price) + random.uniform(0, 0.0005)
        low = min(open_price, close_price) - random.uniform(0, 0.0005)
        
        bars.append({
            "open": open_price,
            "high": high,
            "low": low,
            "close": close_price,
            "volume": volume
        })
        
        base_price = close_price
    
    # Create detector
    detector = InstitutionalFlowDetection()
    
    # Analyze
    analysis = detector.analyze(bars)
    
    # Print results
    print(f"\nCurrent Activity: {analysis.current_activity.value}")
    print(f"Activity Confidence: {analysis.activity_confidence:.0%}")
    print(f"\nSmart Money Direction: {analysis.smart_money_direction}")
    print(f"Retail Direction: {analysis.retail_direction}")
    print(f"Order Flow Type: {analysis.current_flow_type.value}")
    
    print(f"\nLarge Orders Detected: {len(analysis.large_orders)}")
    if analysis.recent_large_order:
        print(f"  Recent: {analysis.recent_large_order.direction} at {analysis.recent_large_order.price_level:.5f}")
    
    if analysis.current_phase:
        print(f"\nPhase: {analysis.current_phase.phase_type.value}")
        print(f"  Spring: {analysis.current_phase.spring_detected}")
        print(f"  Upthrust: {analysis.current_phase.upthrust_detected}")
    
    print(f"\nSmart Money Zones: {len(analysis.smart_money_zones)}")
    for zone in analysis.smart_money_zones[:3]:
        print(f"  {zone.zone_type}: {zone.price_low:.5f}-{zone.price_high:.5f} (strength: {zone.strength:.0%})")
    
    print(f"\nLiquidity Pools: {len(analysis.liquidity_pools)}")
    for pool in analysis.liquidity_pools[:3]:
        print(f"  {pool.liquidity_type.value} at {pool.price_level:.5f} (target: {pool.likely_target})")
    
    print(f"\nIceberg Detected: {analysis.iceberg_detected.value}")
    
    print(f"\nSIGNAL: {analysis.signal}")
    print(f"Signal Strength: {analysis.signal_strength:.0%}")
    print(f"Confidence: {analysis.confidence:.0%}")
    
    print("\nREASONING:")
    for reason in analysis.reasoning:
        print(f"  - {reason}")
    
    print("\nTest completed successfully!")


if __name__ == "__main__":
    test_institutional_flow_detection()
