"""
Manipulation Candle Intelligence Module

This module implements the key concepts from the Funded Brothers Volume Profile Mastery:
1. Manipulation Candle Detection - 5-min candles that trap traders
2. Absorption Pattern Detection - High volume but price doesn't follow through
3. Delta Analysis - Buyer vs seller pressure at key levels
4. Trap Detection - Identify where traders get trapped
5. Session Profile Analysis - NY, London, Asia session behavior
6. Tighter Stop Loss Placement - Use absorption areas for stops

"The core strategy involves identifying 'manipulation candles' where aggressive 
buyers or sellers are trapped" - Funded Brothers
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple, Any
from enum import Enum
import math


class ManipulationType(Enum):
    """Types of manipulation candles"""
    BULL_TRAP = "bull_trap"  # Trapped buyers
    BEAR_TRAP = "bear_trap"  # Trapped sellers
    ABSORPTION_BULLISH = "absorption_bullish"  # Sellers absorbed by buyers
    ABSORPTION_BEARISH = "absorption_bearish"  # Buyers absorbed by sellers
    STOP_HUNT_HIGH = "stop_hunt_high"  # Stop hunt above
    STOP_HUNT_LOW = "stop_hunt_low"  # Stop hunt below
    NONE = "none"


class SessionType(Enum):
    """Trading session types"""
    ASIA = "asia"  # 00:00 - 08:00 UTC
    LONDON = "london"  # 08:00 - 16:00 UTC
    NEW_YORK = "new_york"  # 13:00 - 21:00 UTC
    OVERLAP = "overlap"  # London/NY overlap 13:00 - 16:00 UTC
    OFF_HOURS = "off_hours"


class DeltaDirection(Enum):
    """Delta (buyer vs seller) direction"""
    STRONG_BUYERS = "strong_buyers"
    BUYERS = "buyers"
    NEUTRAL = "neutral"
    SELLERS = "sellers"
    STRONG_SELLERS = "strong_sellers"


@dataclass
class ManipulationCandle:
    """Represents a manipulation candle that traps traders"""
    index: int
    manipulation_type: ManipulationType
    open_price: float
    high: float
    low: float
    close: float
    volume: float
    trapped_direction: str  # "LONG" or "SHORT"
    trap_strength: float  # 0-1
    absorption_volume: float  # Volume absorbed
    reversal_confirmed: bool
    
    @property
    def body_size(self) -> float:
        return abs(self.close - self.open_price)
    
    @property
    def upper_wick(self) -> float:
        return self.high - max(self.close, self.open_price)
    
    @property
    def lower_wick(self) -> float:
        return min(self.close, self.open_price) - self.low
    
    @property
    def is_bullish(self) -> bool:
        return self.close > self.open_price


@dataclass
class AbsorptionZone:
    """Represents an absorption zone where one side absorbed the other"""
    index: int
    top: float
    bottom: float
    absorption_type: str  # "bullish" or "bearish"
    volume: float
    delta: float  # Positive = buyers, Negative = sellers
    strength: float  # 0-1
    
    @property
    def midpoint(self) -> float:
        return (self.top + self.bottom) / 2
    
    @property
    def size(self) -> float:
        return self.top - self.bottom


@dataclass
class DeltaAnalysis:
    """Delta analysis for a bar or zone"""
    index: int
    total_volume: float
    buy_volume: float
    sell_volume: float
    delta: float  # buy_volume - sell_volume
    cumulative_delta: float
    delta_direction: DeltaDirection
    
    @property
    def delta_percent(self) -> float:
        if self.total_volume == 0:
            return 0
        return self.delta / self.total_volume


@dataclass
class SessionProfile:
    """Volume profile for a trading session"""
    session_type: SessionType
    start_index: int
    end_index: int
    high: float
    low: float
    poc: float  # Point of Control
    vah: float  # Value Area High
    val: float  # Value Area Low
    total_volume: float
    manipulation_candles: List[ManipulationCandle]
    
    @property
    def range_size(self) -> float:
        return self.high - self.low


@dataclass
class ManipulationAnalysis:
    """Complete manipulation candle analysis result"""
    # Manipulation candles
    manipulation_candles: List[ManipulationCandle]
    recent_manipulation: Optional[ManipulationCandle]
    
    # Absorption zones
    absorption_zones: List[AbsorptionZone]
    nearest_absorption: Optional[AbsorptionZone]
    
    # Delta analysis
    delta_analysis: List[DeltaAnalysis]
    cumulative_delta: float
    delta_direction: DeltaDirection
    
    # Session profile
    current_session: SessionType
    session_profile: Optional[SessionProfile]
    
    # Trade signal
    signal: str  # "LONG", "SHORT", "NEUTRAL"
    signal_strength: float  # 0-1
    confidence: float  # 0-1
    reasoning: List[str]
    
    # Entry/Exit based on manipulation
    entry_price: float
    stop_loss: float  # Tighter stop using absorption
    take_profit: float
    
    # Trap status
    trap_detected: bool
    trap_direction: str  # Direction of trapped traders


class ManipulationCandleIntelligence:
    """
    Manipulation Candle Intelligence Engine
    
    Implements the Funded Brothers Volume Profile Mastery strategy:
    - Detect manipulation candles that trap traders
    - Identify absorption patterns (high volume, no follow-through)
    - Analyze delta (buyer vs seller pressure)
    - Use session profiles for context
    - Place tighter stops using absorption zones
    
    "Enter on manipulation candle close - when the trap is confirmed"
    """
    
    def __init__(
        self,
        absorption_threshold: float = 0.7,
        manipulation_wick_ratio: float = 2.0,
        delta_threshold: float = 0.3,
        volume_spike_threshold: float = 1.5
    ):
        """
        Initialize Manipulation Candle Intelligence
        
        Args:
            absorption_threshold: Volume ratio for absorption detection
            manipulation_wick_ratio: Wick/body ratio for manipulation candle
            delta_threshold: Delta threshold for direction determination
            volume_spike_threshold: Volume spike multiplier for detection
        """
        self.absorption_threshold = absorption_threshold
        self.manipulation_wick_ratio = manipulation_wick_ratio
        self.delta_threshold = delta_threshold
        self.volume_spike_threshold = volume_spike_threshold
    
    def analyze(self, bars: List[Dict[str, Any]]) -> ManipulationAnalysis:
        """
        Perform complete manipulation candle analysis
        
        Args:
            bars: List of OHLCV bars
            
        Returns:
            ManipulationAnalysis with complete analysis
        """
        if len(bars) < 20:
            return self._empty_analysis()
        
        reasoning = []
        
        # Step 1: Calculate average volume for reference
        avg_volume = sum(b.get("volume", 0) for b in bars) / len(bars)
        
        # Step 2: Detect manipulation candles
        manipulation_candles = self._detect_manipulation_candles(bars, avg_volume)
        recent_manipulation = manipulation_candles[-1] if manipulation_candles else None
        
        if recent_manipulation:
            reasoning.append(f"Manipulation candle detected: {recent_manipulation.manipulation_type.value}")
        
        # Step 3: Detect absorption zones
        absorption_zones = self._detect_absorption_zones(bars, avg_volume)
        nearest_absorption = self._find_nearest_absorption(bars[-1]["close"], absorption_zones)
        
        if nearest_absorption:
            reasoning.append(f"Absorption zone at {nearest_absorption.midpoint:.5f} ({nearest_absorption.absorption_type})")
        
        # Step 4: Perform delta analysis
        delta_analysis = self._analyze_delta(bars)
        cumulative_delta = delta_analysis[-1].cumulative_delta if delta_analysis else 0
        delta_direction = self._determine_delta_direction(cumulative_delta, avg_volume)
        
        reasoning.append(f"Delta direction: {delta_direction.value}, Cumulative: {cumulative_delta:.0f}")
        
        # Step 5: Determine current session
        current_session = self._determine_session(bars[-1])
        
        # Step 6: Build session profile
        session_profile = self._build_session_profile(bars, current_session, manipulation_candles)
        
        if session_profile:
            reasoning.append(f"Session: {current_session.value}, POC: {session_profile.poc:.5f}")
        
        # Step 7: Detect traps
        trap_detected, trap_direction = self._detect_trap(
            bars, manipulation_candles, delta_direction
        )
        
        if trap_detected:
            reasoning.append(f"Trap detected: {trap_direction} traders trapped")
        
        # Step 8: Generate trade signal
        signal, signal_strength, confidence = self._generate_signal(
            manipulation_candles=manipulation_candles,
            absorption_zones=absorption_zones,
            delta_direction=delta_direction,
            trap_detected=trap_detected,
            trap_direction=trap_direction,
            session_profile=session_profile
        )
        
        # Step 9: Calculate entry/exit levels with tighter stops
        entry_price, stop_loss, take_profit = self._calculate_levels(
            bars=bars,
            signal=signal,
            manipulation_candles=manipulation_candles,
            absorption_zones=absorption_zones,
            session_profile=session_profile
        )
        
        return ManipulationAnalysis(
            manipulation_candles=manipulation_candles,
            recent_manipulation=recent_manipulation,
            absorption_zones=absorption_zones,
            nearest_absorption=nearest_absorption,
            delta_analysis=delta_analysis,
            cumulative_delta=cumulative_delta,
            delta_direction=delta_direction,
            current_session=current_session,
            session_profile=session_profile,
            signal=signal,
            signal_strength=signal_strength,
            confidence=confidence,
            reasoning=reasoning,
            entry_price=entry_price,
            stop_loss=stop_loss,
            take_profit=take_profit,
            trap_detected=trap_detected,
            trap_direction=trap_direction
        )
    
    def _detect_manipulation_candles(
        self,
        bars: List[Dict[str, Any]],
        avg_volume: float
    ) -> List[ManipulationCandle]:
        """
        Detect manipulation candles that trap traders
        
        Characteristics:
        - Large wick relative to body
        - High volume
        - Price reverses after
        """
        manipulation_candles = []
        
        for i in range(1, len(bars) - 1):
            bar = bars[i]
            prev_bar = bars[i - 1]
            next_bar = bars[i + 1]
            
            body_size = abs(bar["close"] - bar["open"])
            upper_wick = bar["high"] - max(bar["close"], bar["open"])
            lower_wick = min(bar["close"], bar["open"]) - bar["low"]
            volume = bar.get("volume", 0)
            
            # Skip if body is too small
            if body_size < 0.00001:
                continue
            
            manipulation_type = ManipulationType.NONE
            trapped_direction = "NEUTRAL"
            trap_strength = 0.0
            
            # Check for bull trap (large upper wick, price reverses down)
            if upper_wick / body_size >= self.manipulation_wick_ratio:
                if next_bar["close"] < bar["close"]:
                    manipulation_type = ManipulationType.BULL_TRAP
                    trapped_direction = "LONG"
                    trap_strength = min(1.0, upper_wick / body_size / 5)
            
            # Check for bear trap (large lower wick, price reverses up)
            if lower_wick / body_size >= self.manipulation_wick_ratio:
                if next_bar["close"] > bar["close"]:
                    manipulation_type = ManipulationType.BEAR_TRAP
                    trapped_direction = "SHORT"
                    trap_strength = min(1.0, lower_wick / body_size / 5)
            
            # Check for absorption (high volume but small body)
            if volume > avg_volume * self.volume_spike_threshold:
                if body_size < (bar["high"] - bar["low"]) * 0.3:
                    if bar["close"] > bar["open"]:
                        manipulation_type = ManipulationType.ABSORPTION_BULLISH
                        trapped_direction = "SHORT"
                    else:
                        manipulation_type = ManipulationType.ABSORPTION_BEARISH
                        trapped_direction = "LONG"
                    trap_strength = min(1.0, volume / avg_volume / 3)
            
            # Check for stop hunt
            if bar["high"] > prev_bar["high"] and bar["close"] < prev_bar["high"]:
                if next_bar["close"] < bar["low"]:
                    manipulation_type = ManipulationType.STOP_HUNT_HIGH
                    trapped_direction = "LONG"
                    trap_strength = 0.8
            
            if bar["low"] < prev_bar["low"] and bar["close"] > prev_bar["low"]:
                if next_bar["close"] > bar["high"]:
                    manipulation_type = ManipulationType.STOP_HUNT_LOW
                    trapped_direction = "SHORT"
                    trap_strength = 0.8
            
            if manipulation_type != ManipulationType.NONE:
                manipulation_candles.append(ManipulationCandle(
                    index=i,
                    manipulation_type=manipulation_type,
                    open_price=bar["open"],
                    high=bar["high"],
                    low=bar["low"],
                    close=bar["close"],
                    volume=volume,
                    trapped_direction=trapped_direction,
                    trap_strength=trap_strength,
                    absorption_volume=volume if "absorption" in manipulation_type.value else 0,
                    reversal_confirmed=True
                ))
        
        return manipulation_candles
    
    def _detect_absorption_zones(
        self,
        bars: List[Dict[str, Any]],
        avg_volume: float
    ) -> List[AbsorptionZone]:
        """
        Detect absorption zones where one side absorbed the other
        
        Absorption = High volume but price doesn't follow through
        """
        absorption_zones = []
        
        for i in range(2, len(bars) - 1):
            bar = bars[i]
            prev_bar = bars[i - 1]
            next_bar = bars[i + 1]
            
            volume = bar.get("volume", 0)
            body_size = abs(bar["close"] - bar["open"])
            range_size = bar["high"] - bar["low"]
            
            # High volume with small body = absorption
            if volume > avg_volume * self.volume_spike_threshold:
                if body_size < range_size * 0.3:
                    # Determine absorption type based on next bar
                    if next_bar["close"] > bar["close"]:
                        absorption_type = "bullish"
                        delta = volume * 0.6  # Estimate buyers won
                    else:
                        absorption_type = "bearish"
                        delta = -volume * 0.6  # Estimate sellers won
                    
                    strength = min(1.0, volume / avg_volume / 2)
                    
                    absorption_zones.append(AbsorptionZone(
                        index=i,
                        top=bar["high"],
                        bottom=bar["low"],
                        absorption_type=absorption_type,
                        volume=volume,
                        delta=delta,
                        strength=strength
                    ))
        
        return absorption_zones
    
    def _analyze_delta(self, bars: List[Dict[str, Any]]) -> List[DeltaAnalysis]:
        """
        Analyze delta (buyer vs seller pressure) for each bar
        
        Uses price action to estimate delta:
        - Close near high = buyers dominant
        - Close near low = sellers dominant
        """
        delta_analysis = []
        cumulative_delta = 0
        
        for i, bar in enumerate(bars):
            volume = bar.get("volume", 0)
            range_size = bar["high"] - bar["low"]
            
            if range_size == 0:
                buy_volume = volume / 2
                sell_volume = volume / 2
            else:
                # Estimate buy/sell volume based on close position
                close_position = (bar["close"] - bar["low"]) / range_size
                buy_volume = volume * close_position
                sell_volume = volume * (1 - close_position)
            
            delta = buy_volume - sell_volume
            cumulative_delta += delta
            
            # Determine direction
            if delta > volume * self.delta_threshold:
                direction = DeltaDirection.STRONG_BUYERS
            elif delta > volume * 0.1:
                direction = DeltaDirection.BUYERS
            elif delta < -volume * self.delta_threshold:
                direction = DeltaDirection.STRONG_SELLERS
            elif delta < -volume * 0.1:
                direction = DeltaDirection.SELLERS
            else:
                direction = DeltaDirection.NEUTRAL
            
            delta_analysis.append(DeltaAnalysis(
                index=i,
                total_volume=volume,
                buy_volume=buy_volume,
                sell_volume=sell_volume,
                delta=delta,
                cumulative_delta=cumulative_delta,
                delta_direction=direction
            ))
        
        return delta_analysis
    
    def _determine_delta_direction(
        self,
        cumulative_delta: float,
        avg_volume: float
    ) -> DeltaDirection:
        """Determine overall delta direction"""
        threshold = avg_volume * 5
        
        if cumulative_delta > threshold:
            return DeltaDirection.STRONG_BUYERS
        elif cumulative_delta > threshold * 0.3:
            return DeltaDirection.BUYERS
        elif cumulative_delta < -threshold:
            return DeltaDirection.STRONG_SELLERS
        elif cumulative_delta < -threshold * 0.3:
            return DeltaDirection.SELLERS
        return DeltaDirection.NEUTRAL
    
    def _determine_session(self, bar: Dict[str, Any]) -> SessionType:
        """Determine current trading session based on timestamp"""
        timestamp = bar.get("timestamp", "")
        
        # If no timestamp, assume NY session (most active)
        if not timestamp:
            return SessionType.NEW_YORK
        
        try:
            # Extract hour from timestamp
            if "T" in timestamp:
                hour = int(timestamp.split("T")[1][:2])
            else:
                hour = 14  # Default to NY session
            
            # Determine session
            if 0 <= hour < 8:
                return SessionType.ASIA
            elif 8 <= hour < 13:
                return SessionType.LONDON
            elif 13 <= hour < 16:
                return SessionType.OVERLAP
            elif 16 <= hour < 21:
                return SessionType.NEW_YORK
            else:
                return SessionType.OFF_HOURS
        except (ValueError, IndexError):
            return SessionType.NEW_YORK
    
    def _build_session_profile(
        self,
        bars: List[Dict[str, Any]],
        session: SessionType,
        manipulation_candles: List[ManipulationCandle]
    ) -> Optional[SessionProfile]:
        """Build volume profile for current session"""
        if len(bars) < 10:
            return None
        
        # Use last 50 bars for session profile
        session_bars = bars[-50:] if len(bars) >= 50 else bars
        
        highs = [b["high"] for b in session_bars]
        lows = [b["low"] for b in session_bars]
        volumes = [b.get("volume", 0) for b in session_bars]
        
        session_high = max(highs)
        session_low = min(lows)
        total_volume = sum(volumes)
        
        # Calculate POC (Point of Control) - price with most volume
        # Simplified: use volume-weighted average price
        vwap_sum = sum(
            b.get("volume", 0) * (b["high"] + b["low"] + b["close"]) / 3
            for b in session_bars
        )
        poc = vwap_sum / total_volume if total_volume > 0 else (session_high + session_low) / 2
        
        # Calculate Value Area (70% of volume)
        range_size = session_high - session_low
        vah = poc + range_size * 0.35
        val = poc - range_size * 0.35
        
        # Get manipulation candles in this session
        session_manipulation = [
            mc for mc in manipulation_candles
            if mc.index >= len(bars) - len(session_bars)
        ]
        
        return SessionProfile(
            session_type=session,
            start_index=len(bars) - len(session_bars),
            end_index=len(bars) - 1,
            high=session_high,
            low=session_low,
            poc=poc,
            vah=vah,
            val=val,
            total_volume=total_volume,
            manipulation_candles=session_manipulation
        )
    
    def _find_nearest_absorption(
        self,
        current_price: float,
        absorption_zones: List[AbsorptionZone]
    ) -> Optional[AbsorptionZone]:
        """Find nearest absorption zone to current price"""
        if not absorption_zones:
            return None
        
        # Sort by distance to current price
        sorted_zones = sorted(
            absorption_zones,
            key=lambda z: abs(z.midpoint - current_price)
        )
        
        return sorted_zones[0]
    
    def _detect_trap(
        self,
        bars: List[Dict[str, Any]],
        manipulation_candles: List[ManipulationCandle],
        delta_direction: DeltaDirection
    ) -> Tuple[bool, str]:
        """Detect if traders are currently trapped"""
        if not manipulation_candles:
            return False, "NEUTRAL"
        
        # Check recent manipulation candles
        recent = manipulation_candles[-3:] if len(manipulation_candles) >= 3 else manipulation_candles
        
        # Count trapped directions
        long_traps = sum(1 for mc in recent if mc.trapped_direction == "LONG")
        short_traps = sum(1 for mc in recent if mc.trapped_direction == "SHORT")
        
        if long_traps > short_traps:
            return True, "LONG"
        elif short_traps > long_traps:
            return True, "SHORT"
        
        return False, "NEUTRAL"
    
    def _generate_signal(
        self,
        manipulation_candles: List[ManipulationCandle],
        absorption_zones: List[AbsorptionZone],
        delta_direction: DeltaDirection,
        trap_detected: bool,
        trap_direction: str,
        session_profile: Optional[SessionProfile]
    ) -> Tuple[str, float, float]:
        """
        Generate trade signal based on manipulation analysis
        
        Key insight: Trade AGAINST the trapped traders
        """
        score = 0.0
        factors = 0
        
        # Factor 1: Manipulation candles (trade against trapped traders)
        if manipulation_candles:
            recent = manipulation_candles[-1]
            if recent.trapped_direction == "LONG":
                score -= 0.3 * recent.trap_strength  # Go SHORT
            elif recent.trapped_direction == "SHORT":
                score += 0.3 * recent.trap_strength  # Go LONG
            factors += 1
        
        # Factor 2: Absorption zones
        if absorption_zones:
            recent = absorption_zones[-1]
            if recent.absorption_type == "bullish":
                score += 0.25 * recent.strength
            else:
                score -= 0.25 * recent.strength
            factors += 1
        
        # Factor 3: Delta direction
        if delta_direction == DeltaDirection.STRONG_BUYERS:
            score += 0.2
        elif delta_direction == DeltaDirection.BUYERS:
            score += 0.1
        elif delta_direction == DeltaDirection.STRONG_SELLERS:
            score -= 0.2
        elif delta_direction == DeltaDirection.SELLERS:
            score -= 0.1
        factors += 1
        
        # Factor 4: Trap detection (trade against trapped traders)
        if trap_detected:
            if trap_direction == "LONG":
                score -= 0.25  # Go SHORT
            elif trap_direction == "SHORT":
                score += 0.25  # Go LONG
            factors += 1
        
        # Factor 5: Session context
        if session_profile:
            if session_profile.session_type in [SessionType.NEW_YORK, SessionType.OVERLAP]:
                # More reliable signals during active sessions
                score *= 1.1
            factors += 1
        
        # Determine signal
        if score > 0.25:
            signal = "LONG"
        elif score < -0.25:
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
        manipulation_candles: List[ManipulationCandle],
        absorption_zones: List[AbsorptionZone],
        session_profile: Optional[SessionProfile]
    ) -> Tuple[float, float, float]:
        """
        Calculate entry, stop loss, and take profit
        
        Key insight: Use absorption zones for TIGHTER stops
        """
        current_price = bars[-1]["close"]
        
        if signal == "NEUTRAL":
            return current_price, current_price, current_price
        
        # Entry at current price or manipulation candle close
        entry_price = current_price
        if manipulation_candles:
            recent = manipulation_candles[-1]
            entry_price = recent.close
        
        # Stop loss using absorption zone (TIGHTER stops)
        if signal == "LONG":
            # Stop below nearest bearish absorption or session low
            if absorption_zones:
                bearish_zones = [z for z in absorption_zones if z.absorption_type == "bearish"]
                if bearish_zones:
                    stop_loss = min(z.bottom for z in bearish_zones[-3:])
                else:
                    stop_loss = session_profile.val if session_profile else current_price * 0.995
            else:
                stop_loss = session_profile.val if session_profile else current_price * 0.995
            
            # Take profit at session high or VAH
            take_profit = session_profile.vah if session_profile else current_price * 1.01
        else:
            # Stop above nearest bullish absorption or session high
            if absorption_zones:
                bullish_zones = [z for z in absorption_zones if z.absorption_type == "bullish"]
                if bullish_zones:
                    stop_loss = max(z.top for z in bullish_zones[-3:])
                else:
                    stop_loss = session_profile.vah if session_profile else current_price * 1.005
            else:
                stop_loss = session_profile.vah if session_profile else current_price * 1.005
            
            # Take profit at session low or VAL
            take_profit = session_profile.val if session_profile else current_price * 0.99
        
        return entry_price, stop_loss, take_profit
    
    def _empty_analysis(self) -> ManipulationAnalysis:
        """Return empty analysis when insufficient data"""
        return ManipulationAnalysis(
            manipulation_candles=[],
            recent_manipulation=None,
            absorption_zones=[],
            nearest_absorption=None,
            delta_analysis=[],
            cumulative_delta=0,
            delta_direction=DeltaDirection.NEUTRAL,
            current_session=SessionType.OFF_HOURS,
            session_profile=None,
            signal="NEUTRAL",
            signal_strength=0,
            confidence=0,
            reasoning=["Insufficient data for analysis"],
            entry_price=0,
            stop_loss=0,
            take_profit=0,
            trap_detected=False,
            trap_direction="NEUTRAL"
        )


def test_manipulation_candle_intelligence():
    """Test the Manipulation Candle Intelligence module"""
    import random
    random.seed(42)
    
    bars = []
    price = 1.1000
    
    for i in range(100):
        # Create price action with manipulation patterns
        if i % 15 == 0:
            # Create manipulation candle (large wick)
            high = price + random.uniform(0.0020, 0.0040)
            low = price - random.uniform(0.0005, 0.0010)
            close = price + random.uniform(-0.0005, 0.0005)
            volume = random.uniform(5000, 10000)  # High volume
        else:
            high = price + random.uniform(0.0005, 0.0015)
            low = price - random.uniform(0.0005, 0.0015)
            close = price + random.uniform(-0.0008, 0.0008)
            volume = random.uniform(1000, 3000)
        
        bars.append({
            "open": price,
            "high": high,
            "low": low,
            "close": close,
            "volume": volume,
            "timestamp": f"2024-01-{i//24+1:02d}T{i%24:02d}:00:00Z"
        })
        
        price = close
    
    # Run analysis
    intelligence = ManipulationCandleIntelligence()
    analysis = intelligence.analyze(bars)
    
    print("=" * 60)
    print("MANIPULATION CANDLE INTELLIGENCE TEST")
    print("=" * 60)
    print(f"Manipulation Candles Found: {len(analysis.manipulation_candles)}")
    print(f"Absorption Zones Found: {len(analysis.absorption_zones)}")
    print(f"Cumulative Delta: {analysis.cumulative_delta:.0f}")
    print(f"Delta Direction: {analysis.delta_direction.value}")
    print(f"Current Session: {analysis.current_session.value}")
    print(f"Trap Detected: {analysis.trap_detected} ({analysis.trap_direction})")
    print(f"Signal: {analysis.signal}")
    print(f"Signal Strength: {analysis.signal_strength:.2%}")
    print(f"Confidence: {analysis.confidence:.2%}")
    print("\nReasoning:")
    for r in analysis.reasoning:
        print(f"  - {r}")
    print(f"\nEntry: {analysis.entry_price:.5f}")
    print(f"Stop Loss: {analysis.stop_loss:.5f}")
    print(f"Take Profit: {analysis.take_profit:.5f}")
    
    return analysis


if __name__ == "__main__":
    test_manipulation_candle_intelligence()
