"""
Multi-Profile Volume Intelligence Module

This module implements the key concepts from the Funded Brothers Volume Profile Mastery:
1. Multiple Volume Profiles - Previous week, previous day, current week, current day, session
2. POC (Point of Control) - Price with most volume, acts as sniper entry
3. Value Area (70%) - VAH and VAL are extremes
4. Institutional Supply/Demand Zones - Where institutions placed orders
5. Profile Shape Analysis - P-shape, b-shape, D-shape patterns
6. Multi-Profile Confluence - When multiple profiles align

"Draw 5 volume profiles to map out institutional supply and demand zones"
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple, Any
from enum import Enum
import math


class ProfileType(Enum):
    """Types of volume profiles"""
    PREVIOUS_WEEK = "previous_week"
    PREVIOUS_DAY = "previous_day"
    CURRENT_WEEK = "current_week"
    CURRENT_DAY = "current_day"
    SESSION = "session"
    CUSTOM = "custom"


class ProfileShape(Enum):
    """Volume profile shapes"""
    P_SHAPE = "p_shape"  # Bullish - volume concentrated at bottom
    B_SHAPE = "b_shape"  # Bearish - volume concentrated at top
    D_SHAPE = "d_shape"  # Balanced - volume in middle
    DOUBLE_DISTRIBUTION = "double_distribution"  # Two POCs
    THIN = "thin"  # Low volume, fast move
    WIDE = "wide"  # High volume, consolidation


class ZoneType(Enum):
    """Institutional zone types"""
    SUPPLY = "supply"  # Institutional selling
    DEMAND = "demand"  # Institutional buying
    BALANCE = "balance"  # Fair value area


@dataclass
class VolumeLevel:
    """Represents a price level with volume"""
    price: float
    volume: float
    buy_volume: float
    sell_volume: float
    delta: float  # buy - sell
    
    @property
    def delta_percent(self) -> float:
        if self.volume == 0:
            return 0
        return self.delta / self.volume


@dataclass
class VolumeProfile:
    """Represents a complete volume profile"""
    profile_type: ProfileType
    start_index: int
    end_index: int
    high: float
    low: float
    poc: float  # Point of Control
    vah: float  # Value Area High
    val: float  # Value Area Low
    total_volume: float
    shape: ProfileShape
    levels: List[VolumeLevel]
    
    @property
    def range_size(self) -> float:
        return self.high - self.low
    
    @property
    def value_area_size(self) -> float:
        return self.vah - self.val
    
    @property
    def poc_position(self) -> float:
        """POC position within range (0 = bottom, 1 = top)"""
        if self.range_size == 0:
            return 0.5
        return (self.poc - self.low) / self.range_size
    
    def is_price_in_value_area(self, price: float) -> bool:
        return self.val <= price <= self.vah
    
    def is_price_above_poc(self, price: float) -> bool:
        return price > self.poc
    
    def distance_to_poc(self, price: float) -> float:
        return abs(price - self.poc)


@dataclass
class InstitutionalZone:
    """Represents an institutional supply/demand zone"""
    zone_type: ZoneType
    top: float
    bottom: float
    volume: float
    strength: float  # 0-1
    profile_source: ProfileType
    touches: int
    
    @property
    def midpoint(self) -> float:
        return (self.top + self.bottom) / 2
    
    @property
    def size(self) -> float:
        return self.top - self.bottom


@dataclass
class ProfileConfluence:
    """Represents confluence between multiple profiles"""
    price_level: float
    profiles_aligned: List[ProfileType]
    confluence_type: str  # "poc", "vah", "val"
    strength: float  # 0-1
    
    @property
    def num_profiles(self) -> int:
        return len(self.profiles_aligned)


@dataclass
class MultiProfileAnalysis:
    """Complete multi-profile volume analysis result"""
    # Individual profiles
    previous_week: Optional[VolumeProfile]
    previous_day: Optional[VolumeProfile]
    current_week: Optional[VolumeProfile]
    current_day: Optional[VolumeProfile]
    session: Optional[VolumeProfile]
    
    # Institutional zones
    supply_zones: List[InstitutionalZone]
    demand_zones: List[InstitutionalZone]
    nearest_supply: Optional[InstitutionalZone]
    nearest_demand: Optional[InstitutionalZone]
    
    # Confluence
    poc_confluences: List[ProfileConfluence]
    vah_confluences: List[ProfileConfluence]
    val_confluences: List[ProfileConfluence]
    strongest_confluence: Optional[ProfileConfluence]
    
    # Current position
    price_vs_profiles: Dict[str, str]  # Profile -> "above_poc", "below_poc", "in_value_area"
    
    # Trade signal
    signal: str  # "LONG", "SHORT", "NEUTRAL"
    signal_strength: float  # 0-1
    confidence: float  # 0-1
    reasoning: List[str]
    
    # Entry/Exit
    entry_price: float
    stop_loss: float
    take_profit_1: float
    take_profit_2: float
    
    # Key levels
    key_poc_levels: List[float]
    key_vah_levels: List[float]
    key_val_levels: List[float]


class MultiProfileVolumeIntelligence:
    """
    Multi-Profile Volume Intelligence Engine
    
    Implements the Funded Brothers Volume Profile Mastery strategy:
    - Draw 5 volume profiles (previous week, previous day, current week, current day, session)
    - Identify POC, VAH, VAL for each profile
    - Find institutional supply/demand zones
    - Detect profile shape (P, b, D)
    - Find confluence between multiple profiles
    
    "The POC acts as a sniper entry - price with most volume"
    """
    
    def __init__(
        self,
        value_area_percent: float = 0.70,
        num_price_levels: int = 50,
        confluence_threshold: float = 0.002,
        zone_strength_threshold: float = 0.5
    ):
        """
        Initialize Multi-Profile Volume Intelligence
        
        Args:
            value_area_percent: Percentage of volume for value area (default 70%)
            num_price_levels: Number of price levels for profile
            confluence_threshold: Price threshold for confluence detection
            zone_strength_threshold: Minimum strength for institutional zones
        """
        self.value_area_percent = value_area_percent
        self.num_price_levels = num_price_levels
        self.confluence_threshold = confluence_threshold
        self.zone_strength_threshold = zone_strength_threshold
    
    def analyze(
        self,
        bars: List[Dict[str, Any]],
        bars_per_day: int = 288,  # 5-min bars per day
        bars_per_week: int = 1440  # 5-min bars per week
    ) -> MultiProfileAnalysis:
        """
        Perform complete multi-profile volume analysis
        
        Args:
            bars: List of OHLCV bars
            bars_per_day: Number of bars in a day
            bars_per_week: Number of bars in a week
            
        Returns:
            MultiProfileAnalysis with complete analysis
        """
        if len(bars) < 50:
            return self._empty_analysis()
        
        reasoning = []
        current_price = bars[-1]["close"]
        
        # Step 1: Build individual profiles
        previous_week = self._build_profile(
            bars, ProfileType.PREVIOUS_WEEK, bars_per_week * 2, bars_per_week
        )
        previous_day = self._build_profile(
            bars, ProfileType.PREVIOUS_DAY, bars_per_day * 2, bars_per_day
        )
        current_week = self._build_profile(
            bars, ProfileType.CURRENT_WEEK, bars_per_week, 0
        )
        current_day = self._build_profile(
            bars, ProfileType.CURRENT_DAY, bars_per_day, 0
        )
        session = self._build_profile(
            bars, ProfileType.SESSION, min(50, len(bars)), 0
        )
        
        profiles = [p for p in [previous_week, previous_day, current_week, current_day, session] if p]
        
        if profiles:
            reasoning.append(f"Built {len(profiles)} volume profiles")
        
        # Step 2: Identify institutional zones
        supply_zones, demand_zones = self._identify_institutional_zones(profiles)
        nearest_supply = self._find_nearest_zone(current_price, supply_zones, above=True)
        nearest_demand = self._find_nearest_zone(current_price, demand_zones, above=False)
        
        if supply_zones:
            reasoning.append(f"Found {len(supply_zones)} supply zones")
        if demand_zones:
            reasoning.append(f"Found {len(demand_zones)} demand zones")
        
        # Step 3: Find confluences
        poc_confluences = self._find_confluences(profiles, "poc")
        vah_confluences = self._find_confluences(profiles, "vah")
        val_confluences = self._find_confluences(profiles, "val")
        
        all_confluences = poc_confluences + vah_confluences + val_confluences
        strongest_confluence = max(all_confluences, key=lambda c: c.strength) if all_confluences else None
        
        if strongest_confluence:
            reasoning.append(f"Strongest confluence: {strongest_confluence.confluence_type} at {strongest_confluence.price_level:.5f} ({strongest_confluence.num_profiles} profiles)")
        
        # Step 4: Analyze price position vs profiles
        price_vs_profiles = self._analyze_price_position(current_price, profiles)
        
        # Step 5: Generate trade signal
        signal, signal_strength, confidence = self._generate_signal(
            current_price=current_price,
            profiles=profiles,
            supply_zones=supply_zones,
            demand_zones=demand_zones,
            confluences=all_confluences,
            price_vs_profiles=price_vs_profiles
        )
        
        # Step 6: Calculate entry/exit levels
        entry_price, stop_loss, tp1, tp2 = self._calculate_levels(
            current_price=current_price,
            signal=signal,
            profiles=profiles,
            supply_zones=supply_zones,
            demand_zones=demand_zones,
            confluences=all_confluences
        )
        
        # Step 7: Compile key levels
        key_poc_levels = [p.poc for p in profiles]
        key_vah_levels = [p.vah for p in profiles]
        key_val_levels = [p.val for p in profiles]
        
        return MultiProfileAnalysis(
            previous_week=previous_week,
            previous_day=previous_day,
            current_week=current_week,
            current_day=current_day,
            session=session,
            supply_zones=supply_zones,
            demand_zones=demand_zones,
            nearest_supply=nearest_supply,
            nearest_demand=nearest_demand,
            poc_confluences=poc_confluences,
            vah_confluences=vah_confluences,
            val_confluences=val_confluences,
            strongest_confluence=strongest_confluence,
            price_vs_profiles=price_vs_profiles,
            signal=signal,
            signal_strength=signal_strength,
            confidence=confidence,
            reasoning=reasoning,
            entry_price=entry_price,
            stop_loss=stop_loss,
            take_profit_1=tp1,
            take_profit_2=tp2,
            key_poc_levels=key_poc_levels,
            key_vah_levels=key_vah_levels,
            key_val_levels=key_val_levels
        )
    
    def _build_profile(
        self,
        bars: List[Dict[str, Any]],
        profile_type: ProfileType,
        lookback: int,
        offset: int
    ) -> Optional[VolumeProfile]:
        """Build a volume profile for a specific period"""
        if len(bars) < lookback + offset:
            # Use available data
            if len(bars) < 20:
                return None
            start_idx = 0
            end_idx = len(bars) - offset if offset > 0 else len(bars)
        else:
            start_idx = len(bars) - lookback - offset
            end_idx = len(bars) - offset if offset > 0 else len(bars)
        
        if start_idx >= end_idx or end_idx <= 0:
            return None
        
        profile_bars = bars[start_idx:end_idx]
        
        if not profile_bars:
            return None
        
        # Calculate range
        high = max(b["high"] for b in profile_bars)
        low = min(b["low"] for b in profile_bars)
        range_size = high - low
        
        if range_size == 0:
            return None
        
        # Build volume levels
        level_size = range_size / self.num_price_levels
        levels: List[VolumeLevel] = []
        
        for i in range(self.num_price_levels):
            level_price = low + (i + 0.5) * level_size
            level_volume = 0
            buy_volume = 0
            sell_volume = 0
            
            for bar in profile_bars:
                # Check if bar touches this level
                if bar["low"] <= level_price <= bar["high"]:
                    bar_volume = bar.get("volume", 0)
                    level_volume += bar_volume
                    
                    # Estimate buy/sell based on close position
                    bar_range = bar["high"] - bar["low"]
                    if bar_range > 0:
                        close_position = (bar["close"] - bar["low"]) / bar_range
                        buy_volume += bar_volume * close_position
                        sell_volume += bar_volume * (1 - close_position)
            
            levels.append(VolumeLevel(
                price=level_price,
                volume=level_volume,
                buy_volume=buy_volume,
                sell_volume=sell_volume,
                delta=buy_volume - sell_volume
            ))
        
        # Find POC (level with highest volume)
        if not levels:
            return None
        
        poc_level = max(levels, key=lambda l: l.volume)
        poc = poc_level.price
        
        # Calculate Value Area (70% of volume)
        total_volume = sum(l.volume for l in levels)
        target_volume = total_volume * self.value_area_percent
        
        # Start from POC and expand outward
        poc_idx = levels.index(poc_level)
        va_volume = poc_level.volume
        lower_idx = poc_idx
        upper_idx = poc_idx
        
        while va_volume < target_volume and (lower_idx > 0 or upper_idx < len(levels) - 1):
            lower_vol = levels[lower_idx - 1].volume if lower_idx > 0 else 0
            upper_vol = levels[upper_idx + 1].volume if upper_idx < len(levels) - 1 else 0
            
            if lower_vol >= upper_vol and lower_idx > 0:
                lower_idx -= 1
                va_volume += lower_vol
            elif upper_idx < len(levels) - 1:
                upper_idx += 1
                va_volume += upper_vol
            else:
                break
        
        val = levels[lower_idx].price
        vah = levels[upper_idx].price
        
        # Determine shape
        shape = self._determine_shape(levels, poc_idx, len(levels))
        
        return VolumeProfile(
            profile_type=profile_type,
            start_index=start_idx,
            end_index=end_idx,
            high=high,
            low=low,
            poc=poc,
            vah=vah,
            val=val,
            total_volume=total_volume,
            shape=shape,
            levels=levels
        )
    
    def _determine_shape(
        self,
        levels: List[VolumeLevel],
        poc_idx: int,
        num_levels: int
    ) -> ProfileShape:
        """Determine the shape of the volume profile"""
        if num_levels == 0:
            return ProfileShape.D_SHAPE
        
        poc_position = poc_idx / num_levels
        
        # Calculate volume distribution
        lower_third = sum(l.volume for l in levels[:num_levels//3])
        middle_third = sum(l.volume for l in levels[num_levels//3:2*num_levels//3])
        upper_third = sum(l.volume for l in levels[2*num_levels//3:])
        
        total = lower_third + middle_third + upper_third
        if total == 0:
            return ProfileShape.D_SHAPE
        
        lower_pct = lower_third / total
        middle_pct = middle_third / total
        upper_pct = upper_third / total
        
        # P-shape: Volume concentrated at bottom (bullish)
        if lower_pct > 0.45 and poc_position < 0.4:
            return ProfileShape.P_SHAPE
        
        # b-shape: Volume concentrated at top (bearish)
        if upper_pct > 0.45 and poc_position > 0.6:
            return ProfileShape.B_SHAPE
        
        # D-shape: Volume in middle (balanced)
        if middle_pct > 0.4:
            return ProfileShape.D_SHAPE
        
        # Check for double distribution
        volumes = [l.volume for l in levels]
        peaks = self._find_peaks(volumes)
        if len(peaks) >= 2:
            return ProfileShape.DOUBLE_DISTRIBUTION
        
        # Thin profile (low volume, fast move)
        avg_volume = total / num_levels
        if avg_volume < total * 0.01:
            return ProfileShape.THIN
        
        return ProfileShape.D_SHAPE
    
    def _find_peaks(self, values: List[float]) -> List[int]:
        """Find peaks in a list of values"""
        peaks = []
        for i in range(1, len(values) - 1):
            if values[i] > values[i-1] and values[i] > values[i+1]:
                peaks.append(i)
        return peaks
    
    def _identify_institutional_zones(
        self,
        profiles: List[VolumeProfile]
    ) -> Tuple[List[InstitutionalZone], List[InstitutionalZone]]:
        """Identify institutional supply and demand zones from profiles"""
        supply_zones = []
        demand_zones = []
        
        for profile in profiles:
            # Supply zone: Above POC with high volume
            if profile.vah > profile.poc:
                supply_zones.append(InstitutionalZone(
                    zone_type=ZoneType.SUPPLY,
                    top=profile.vah,
                    bottom=profile.poc,
                    volume=profile.total_volume * 0.3,
                    strength=0.7 if profile.shape == ProfileShape.B_SHAPE else 0.5,
                    profile_source=profile.profile_type,
                    touches=0
                ))
            
            # Demand zone: Below POC with high volume
            if profile.val < profile.poc:
                demand_zones.append(InstitutionalZone(
                    zone_type=ZoneType.DEMAND,
                    top=profile.poc,
                    bottom=profile.val,
                    volume=profile.total_volume * 0.3,
                    strength=0.7 if profile.shape == ProfileShape.P_SHAPE else 0.5,
                    profile_source=profile.profile_type,
                    touches=0
                ))
            
            # High volume nodes as additional zones
            for level in profile.levels:
                if level.volume > profile.total_volume / self.num_price_levels * 2:
                    if level.delta > 0:
                        # Buyers dominant - demand zone
                        demand_zones.append(InstitutionalZone(
                            zone_type=ZoneType.DEMAND,
                            top=level.price + profile.range_size * 0.02,
                            bottom=level.price - profile.range_size * 0.02,
                            volume=level.volume,
                            strength=min(1.0, level.volume / (profile.total_volume / self.num_price_levels) / 3),
                            profile_source=profile.profile_type,
                            touches=0
                        ))
                    else:
                        # Sellers dominant - supply zone
                        supply_zones.append(InstitutionalZone(
                            zone_type=ZoneType.SUPPLY,
                            top=level.price + profile.range_size * 0.02,
                            bottom=level.price - profile.range_size * 0.02,
                            volume=level.volume,
                            strength=min(1.0, abs(level.delta) / level.volume),
                            profile_source=profile.profile_type,
                            touches=0
                        ))
        
        # Filter by strength
        supply_zones = [z for z in supply_zones if z.strength >= self.zone_strength_threshold]
        demand_zones = [z for z in demand_zones if z.strength >= self.zone_strength_threshold]
        
        return supply_zones, demand_zones
    
    def _find_nearest_zone(
        self,
        current_price: float,
        zones: List[InstitutionalZone],
        above: bool
    ) -> Optional[InstitutionalZone]:
        """Find nearest zone above or below current price"""
        if not zones:
            return None
        
        if above:
            candidates = [z for z in zones if z.bottom > current_price]
            if not candidates:
                return None
            return min(candidates, key=lambda z: z.bottom - current_price)
        else:
            candidates = [z for z in zones if z.top < current_price]
            if not candidates:
                return None
            return max(candidates, key=lambda z: z.top)
    
    def _find_confluences(
        self,
        profiles: List[VolumeProfile],
        level_type: str
    ) -> List[ProfileConfluence]:
        """Find confluences between profiles at specific level type"""
        confluences = []
        
        if len(profiles) < 2:
            return confluences
        
        # Get levels from each profile
        levels = []
        for profile in profiles:
            if level_type == "poc":
                levels.append((profile.poc, profile.profile_type))
            elif level_type == "vah":
                levels.append((profile.vah, profile.profile_type))
            elif level_type == "val":
                levels.append((profile.val, profile.profile_type))
        
        # Find clusters of similar levels
        used = set()
        for i, (level1, type1) in enumerate(levels):
            if i in used:
                continue
            
            cluster = [type1]
            cluster_sum = level1
            
            for j, (level2, type2) in enumerate(levels):
                if j <= i or j in used:
                    continue
                
                # Check if levels are close enough
                if abs(level1 - level2) / level1 < self.confluence_threshold:
                    cluster.append(type2)
                    cluster_sum += level2
                    used.add(j)
            
            if len(cluster) >= 2:
                avg_level = cluster_sum / len(cluster)
                strength = len(cluster) / len(profiles)
                
                confluences.append(ProfileConfluence(
                    price_level=avg_level,
                    profiles_aligned=cluster,
                    confluence_type=level_type,
                    strength=strength
                ))
        
        return confluences
    
    def _analyze_price_position(
        self,
        current_price: float,
        profiles: List[VolumeProfile]
    ) -> Dict[str, str]:
        """Analyze current price position relative to each profile"""
        positions = {}
        
        for profile in profiles:
            name = profile.profile_type.value
            
            if profile.is_price_in_value_area(current_price):
                positions[name] = "in_value_area"
            elif profile.is_price_above_poc(current_price):
                positions[name] = "above_poc"
            else:
                positions[name] = "below_poc"
        
        return positions
    
    def _generate_signal(
        self,
        current_price: float,
        profiles: List[VolumeProfile],
        supply_zones: List[InstitutionalZone],
        demand_zones: List[InstitutionalZone],
        confluences: List[ProfileConfluence],
        price_vs_profiles: Dict[str, str]
    ) -> Tuple[str, float, float]:
        """Generate trade signal based on multi-profile analysis"""
        score = 0.0
        factors = 0
        
        # Factor 1: Price position vs profiles
        above_poc_count = sum(1 for v in price_vs_profiles.values() if v == "above_poc")
        below_poc_count = sum(1 for v in price_vs_profiles.values() if v == "below_poc")
        
        if above_poc_count > below_poc_count:
            score += 0.2  # Bullish
        elif below_poc_count > above_poc_count:
            score -= 0.2  # Bearish
        factors += 1
        
        # Factor 2: Profile shapes
        for profile in profiles:
            if profile.shape == ProfileShape.P_SHAPE:
                score += 0.1  # Bullish
            elif profile.shape == ProfileShape.B_SHAPE:
                score -= 0.1  # Bearish
        factors += 1
        
        # Factor 3: Proximity to supply/demand zones
        if supply_zones:
            nearest_supply = min(supply_zones, key=lambda z: abs(z.midpoint - current_price))
            if current_price > nearest_supply.bottom and current_price < nearest_supply.top:
                score -= 0.25 * nearest_supply.strength  # In supply zone = bearish
        
        if demand_zones:
            nearest_demand = min(demand_zones, key=lambda z: abs(z.midpoint - current_price))
            if current_price > nearest_demand.bottom and current_price < nearest_demand.top:
                score += 0.25 * nearest_demand.strength  # In demand zone = bullish
        factors += 1
        
        # Factor 4: Confluences
        for confluence in confluences:
            distance = abs(confluence.price_level - current_price) / current_price
            if distance < 0.005:  # Within 0.5% of confluence
                if confluence.confluence_type == "val":
                    score += 0.15 * confluence.strength  # Near VAL = bullish
                elif confluence.confluence_type == "vah":
                    score -= 0.15 * confluence.strength  # Near VAH = bearish
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
        confidence = min(1.0, factors / 4) * strength
        
        return signal, strength, confidence
    
    def _calculate_levels(
        self,
        current_price: float,
        signal: str,
        profiles: List[VolumeProfile],
        supply_zones: List[InstitutionalZone],
        demand_zones: List[InstitutionalZone],
        confluences: List[ProfileConfluence]
    ) -> Tuple[float, float, float, float]:
        """Calculate entry, stop loss, and take profit levels"""
        if signal == "NEUTRAL" or not profiles:
            return current_price, current_price, current_price, current_price
        
        # Get key levels from profiles
        pocs = [p.poc for p in profiles]
        vahs = [p.vah for p in profiles]
        vals = [p.val for p in profiles]
        
        if signal == "LONG":
            # Entry at current price or nearest POC below
            entry_price = current_price
            pocs_below = [p for p in pocs if p < current_price]
            if pocs_below:
                entry_price = max(pocs_below)
            
            # Stop loss below nearest VAL
            vals_below = [v for v in vals if v < current_price]
            stop_loss = min(vals_below) if vals_below else current_price * 0.995
            
            # Take profit at nearest VAH
            vahs_above = [v for v in vahs if v > current_price]
            tp1 = min(vahs_above) if vahs_above else current_price * 1.01
            
            # Second take profit at next supply zone
            if supply_zones:
                supplies_above = [z.bottom for z in supply_zones if z.bottom > current_price]
                tp2 = min(supplies_above) if supplies_above else tp1 * 1.01
            else:
                tp2 = tp1 * 1.01
        else:
            # Entry at current price or nearest POC above
            entry_price = current_price
            pocs_above = [p for p in pocs if p > current_price]
            if pocs_above:
                entry_price = min(pocs_above)
            
            # Stop loss above nearest VAH
            vahs_above = [v for v in vahs if v > current_price]
            stop_loss = max(vahs_above) if vahs_above else current_price * 1.005
            
            # Take profit at nearest VAL
            vals_below = [v for v in vals if v < current_price]
            tp1 = max(vals_below) if vals_below else current_price * 0.99
            
            # Second take profit at next demand zone
            if demand_zones:
                demands_below = [z.top for z in demand_zones if z.top < current_price]
                tp2 = max(demands_below) if demands_below else tp1 * 0.99
            else:
                tp2 = tp1 * 0.99
        
        return entry_price, stop_loss, tp1, tp2
    
    def _empty_analysis(self) -> MultiProfileAnalysis:
        """Return empty analysis when insufficient data"""
        return MultiProfileAnalysis(
            previous_week=None,
            previous_day=None,
            current_week=None,
            current_day=None,
            session=None,
            supply_zones=[],
            demand_zones=[],
            nearest_supply=None,
            nearest_demand=None,
            poc_confluences=[],
            vah_confluences=[],
            val_confluences=[],
            strongest_confluence=None,
            price_vs_profiles={},
            signal="NEUTRAL",
            signal_strength=0,
            confidence=0,
            reasoning=["Insufficient data for analysis"],
            entry_price=0,
            stop_loss=0,
            take_profit_1=0,
            take_profit_2=0,
            key_poc_levels=[],
            key_vah_levels=[],
            key_val_levels=[]
        )


def test_multi_profile_volume_intelligence():
    """Test the Multi-Profile Volume Intelligence module"""
    import random
    random.seed(42)
    
    bars = []
    price = 1.1000
    
    for i in range(500):
        # Create trending price action with volume
        if i < 200:
            price += random.uniform(-0.0005, 0.0010)  # Slight uptrend
        elif i < 350:
            price += random.uniform(-0.0008, 0.0005)  # Slight downtrend
        else:
            price += random.uniform(-0.0005, 0.0005)  # Consolidation
        
        high = price + random.uniform(0.0005, 0.0015)
        low = price - random.uniform(0.0005, 0.0015)
        close = price + random.uniform(-0.0008, 0.0008)
        
        # Volume varies with price movement
        volume = random.uniform(1000, 3000)
        if abs(close - price) > 0.0005:
            volume *= 1.5  # Higher volume on bigger moves
        
        bars.append({
            "open": price,
            "high": high,
            "low": low,
            "close": close,
            "volume": volume
        })
        
        price = close
    
    # Run analysis
    intelligence = MultiProfileVolumeIntelligence()
    analysis = intelligence.analyze(bars)
    
    print("=" * 60)
    print("MULTI-PROFILE VOLUME INTELLIGENCE TEST")
    print("=" * 60)
    
    if analysis.session:
        print(f"\nSession Profile:")
        print(f"  POC: {analysis.session.poc:.5f}")
        print(f"  VAH: {analysis.session.vah:.5f}")
        print(f"  VAL: {analysis.session.val:.5f}")
        print(f"  Shape: {analysis.session.shape.value}")
    
    if analysis.current_day:
        print(f"\nCurrent Day Profile:")
        print(f"  POC: {analysis.current_day.poc:.5f}")
        print(f"  VAH: {analysis.current_day.vah:.5f}")
        print(f"  VAL: {analysis.current_day.val:.5f}")
        print(f"  Shape: {analysis.current_day.shape.value}")
    
    print(f"\nSupply Zones: {len(analysis.supply_zones)}")
    print(f"Demand Zones: {len(analysis.demand_zones)}")
    
    if analysis.strongest_confluence:
        print(f"\nStrongest Confluence:")
        print(f"  Level: {analysis.strongest_confluence.price_level:.5f}")
        print(f"  Type: {analysis.strongest_confluence.confluence_type}")
        print(f"  Profiles: {analysis.strongest_confluence.num_profiles}")
    
    print(f"\nSignal: {analysis.signal}")
    print(f"Signal Strength: {analysis.signal_strength:.2%}")
    print(f"Confidence: {analysis.confidence:.2%}")
    
    print("\nReasoning:")
    for r in analysis.reasoning:
        print(f"  - {r}")
    
    print(f"\nEntry: {analysis.entry_price:.5f}")
    print(f"Stop Loss: {analysis.stop_loss:.5f}")
    print(f"Take Profit 1: {analysis.take_profit_1:.5f}")
    print(f"Take Profit 2: {analysis.take_profit_2:.5f}")
    
    return analysis


if __name__ == "__main__":
    test_multi_profile_volume_intelligence()
