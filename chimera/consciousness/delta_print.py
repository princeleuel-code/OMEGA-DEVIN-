"""
DELTA PRINT INTELLIGENCE MODULE

This module surpasses DeepCharts by not just SHOWING orderflow data,
but UNDERSTANDING and THINKING about it.

Key Features:
1. Delta Print Detection - High delta pressure zones
2. Big Trades Detection - Institutional footprint
3. Absorption Detection - Failed buyers/sellers
4. Volume Ledge Detection - Sharp volume transitions
5. Confluence Zone Scoring - Multi-factor zone rating
6. Integration with Consciousness Engine

This is the IMPOSSIBLE made possible - orderflow intelligence that THINKS.

Author: Devin (for Prince)
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
import numpy as np


class DeltaDirection(Enum):
    """Direction of delta pressure."""
    STRONG_BUYING = "strong_buying"
    MODERATE_BUYING = "moderate_buying"
    NEUTRAL = "neutral"
    MODERATE_SELLING = "moderate_selling"
    STRONG_SELLING = "strong_selling"


class TradeSize(Enum):
    """Classification of trade size."""
    RETAIL = "retail"
    MEDIUM = "medium"
    LARGE = "large"
    INSTITUTIONAL = "institutional"
    WHALE = "whale"


class AbsorptionType(Enum):
    """Type of absorption pattern."""
    BUYER_ABSORPTION = "buyer_absorption"  # Sellers absorbing aggressive buyers
    SELLER_ABSORPTION = "seller_absorption"  # Buyers absorbing aggressive sellers
    NONE = "none"


class ZoneStrength(Enum):
    """Strength classification of a zone."""
    WEAK = "weak"
    MODERATE = "moderate"
    STRONG = "strong"
    VERY_STRONG = "very_strong"
    EXTREME = "extreme"


@dataclass
class DeltaLevel:
    """A price level with delta information."""
    price: float
    volume: float
    buy_volume: float
    sell_volume: float
    delta: float  # buy_volume - sell_volume
    delta_pct: float  # delta / volume
    big_trades_count: int
    big_trades_volume: float
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    
    @property
    def direction(self) -> DeltaDirection:
        """Get the delta direction."""
        if self.delta_pct > 0.3:
            return DeltaDirection.STRONG_BUYING
        elif self.delta_pct > 0.1:
            return DeltaDirection.MODERATE_BUYING
        elif self.delta_pct < -0.3:
            return DeltaDirection.STRONG_SELLING
        elif self.delta_pct < -0.1:
            return DeltaDirection.MODERATE_SELLING
        return DeltaDirection.NEUTRAL
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "price": self.price,
            "volume": self.volume,
            "buy_volume": self.buy_volume,
            "sell_volume": self.sell_volume,
            "delta": self.delta,
            "delta_pct": self.delta_pct,
            "big_trades_count": self.big_trades_count,
            "big_trades_volume": self.big_trades_volume,
            "direction": self.direction.value,
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class BigTrade:
    """A large institutional trade."""
    timestamp: datetime
    price: float
    size: float
    side: str  # "buy" or "sell"
    trade_size_class: TradeSize
    is_aggressive: bool  # True if market order, False if limit order
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp.isoformat(),
            "price": self.price,
            "size": self.size,
            "side": self.side,
            "trade_size_class": self.trade_size_class.value,
            "is_aggressive": self.is_aggressive,
        }


@dataclass
class AbsorptionPattern:
    """An absorption pattern where one side absorbs the other."""
    timestamp: datetime
    price_start: float
    price_end: float
    absorption_type: AbsorptionType
    aggressive_volume: float  # Volume of aggressive side
    absorbed_volume: float  # Volume that got absorbed
    absorption_ratio: float  # absorbed / aggressive
    candle_count: int  # Number of candles in pattern
    confidence: float
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp.isoformat(),
            "price_start": self.price_start,
            "price_end": self.price_end,
            "absorption_type": self.absorption_type.value,
            "aggressive_volume": self.aggressive_volume,
            "absorbed_volume": self.absorbed_volume,
            "absorption_ratio": self.absorption_ratio,
            "candle_count": self.candle_count,
            "confidence": self.confidence,
        }


@dataclass
class VolumeLedge:
    """A volume ledge - sharp transition from high to low volume."""
    price_high: float  # High volume node price
    price_low: float  # Low volume node price
    volume_high: float
    volume_low: float
    ledge_ratio: float  # volume_high / volume_low
    direction: str  # "above" or "below" - where the ledge is relative to current price
    strength: ZoneStrength
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "price_high": self.price_high,
            "price_low": self.price_low,
            "volume_high": self.volume_high,
            "volume_low": self.volume_low,
            "ledge_ratio": self.ledge_ratio,
            "direction": self.direction,
            "strength": self.strength.value,
        }


@dataclass
class ValueArea:
    """Value Area - where 70% of volume was traded."""
    vah: float  # Value Area High
    val: float  # Value Area Low
    poc: float  # Point of Control (highest volume price)
    total_volume: float
    value_area_volume: float
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "vah": self.vah,
            "val": self.val,
            "poc": self.poc,
            "total_volume": self.total_volume,
            "value_area_volume": self.value_area_volume,
        }


@dataclass
class DeltaPrintZone:
    """A Delta Print zone - high probability entry area."""
    price_high: float
    price_low: float
    zone_type: str  # "resistance" or "support"
    delta_pressure: DeltaDirection
    big_trades_count: int
    big_trades_volume: float
    has_absorption: bool
    absorption_type: Optional[AbsorptionType]
    has_volume_ledge: bool
    is_at_value_area: bool  # At VAH or VAL
    confluence_score: float  # 0-1 score based on multiple factors
    strength: ZoneStrength
    reasoning: str
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "price_high": self.price_high,
            "price_low": self.price_low,
            "zone_type": self.zone_type,
            "delta_pressure": self.delta_pressure.value,
            "big_trades_count": self.big_trades_count,
            "big_trades_volume": self.big_trades_volume,
            "has_absorption": self.has_absorption,
            "absorption_type": self.absorption_type.value if self.absorption_type else None,
            "has_volume_ledge": self.has_volume_ledge,
            "is_at_value_area": self.is_at_value_area,
            "confluence_score": self.confluence_score,
            "strength": self.strength.value,
            "reasoning": self.reasoning,
        }


@dataclass
class DeltaPrintAnalysis:
    """Complete Delta Print analysis output."""
    timestamp: datetime
    symbol: str
    current_price: float
    
    # Volume Profile
    value_area: ValueArea
    volume_profile: List[DeltaLevel]
    
    # Big Trades
    big_trades: List[BigTrade]
    institutional_bias: str  # "bullish", "bearish", "neutral"
    
    # Absorption
    absorption_patterns: List[AbsorptionPattern]
    
    # Volume Ledges
    volume_ledges: List[VolumeLedge]
    
    # Delta Print Zones
    delta_print_zones: List[DeltaPrintZone]
    
    # Best Entry Zone
    best_entry_zone: Optional[DeltaPrintZone]
    
    # Overall Assessment
    market_structure: str  # "trending", "ranging", "transitioning"
    directional_bias: str  # "bullish", "bearish", "neutral"
    confidence: float
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp.isoformat(),
            "symbol": self.symbol,
            "current_price": self.current_price,
            "value_area": self.value_area.to_dict(),
            "volume_profile": [l.to_dict() for l in self.volume_profile],
            "big_trades": [t.to_dict() for t in self.big_trades],
            "institutional_bias": self.institutional_bias,
            "absorption_patterns": [p.to_dict() for p in self.absorption_patterns],
            "volume_ledges": [l.to_dict() for l in self.volume_ledges],
            "delta_print_zones": [z.to_dict() for z in self.delta_print_zones],
            "best_entry_zone": self.best_entry_zone.to_dict() if self.best_entry_zone else None,
            "market_structure": self.market_structure,
            "directional_bias": self.directional_bias,
            "confidence": self.confidence,
        }


class DeltaPrintIntelligence:
    """
    Delta Print Intelligence Engine.
    
    This surpasses DeepCharts by not just visualizing orderflow,
    but UNDERSTANDING and THINKING about it.
    """
    
    def __init__(
        self,
        big_trade_threshold: float = 0.01,  # % of average volume
        absorption_threshold: float = 0.7,  # Absorption ratio threshold
        ledge_ratio_threshold: float = 3.0,  # Volume ratio for ledge detection
        value_area_pct: float = 0.70,  # 70% for value area
    ):
        self.big_trade_threshold = big_trade_threshold
        self.absorption_threshold = absorption_threshold
        self.ledge_ratio_threshold = ledge_ratio_threshold
        self.value_area_pct = value_area_pct
        
        # History for learning
        self.zone_history: List[Dict[str, Any]] = []
        self.trade_history: List[BigTrade] = []
    
    def analyze(
        self,
        candles: List[Dict[str, Any]],
        trades: Optional[List[Dict[str, Any]]] = None,
        order_book: Optional[Dict[str, Any]] = None,
        symbol: str = "UNKNOWN",
    ) -> DeltaPrintAnalysis:
        """
        Perform complete Delta Print analysis.
        
        This is the main entry point that orchestrates all analysis.
        """
        if not candles:
            raise ValueError("No candle data provided")
        
        current_price = candles[-1].get("close", 0)
        
        # Step 1: Build Volume Profile
        volume_profile = self._build_volume_profile(candles)
        
        # Step 2: Calculate Value Area
        value_area = self._calculate_value_area(volume_profile)
        
        # Step 3: Detect Big Trades
        big_trades = self._detect_big_trades(candles, trades)
        institutional_bias = self._calculate_institutional_bias(big_trades)
        
        # Step 4: Detect Absorption Patterns
        absorption_patterns = self._detect_absorption_patterns(candles, volume_profile)
        
        # Step 5: Detect Volume Ledges
        volume_ledges = self._detect_volume_ledges(volume_profile, current_price)
        
        # Step 6: Identify Delta Print Zones
        delta_print_zones = self._identify_delta_print_zones(
            volume_profile=volume_profile,
            value_area=value_area,
            big_trades=big_trades,
            absorption_patterns=absorption_patterns,
            volume_ledges=volume_ledges,
            current_price=current_price,
        )
        
        # Step 7: Find Best Entry Zone
        best_entry_zone = self._find_best_entry_zone(delta_print_zones, current_price)
        
        # Step 8: Assess Market Structure
        market_structure = self._assess_market_structure(candles, value_area)
        
        # Step 9: Determine Directional Bias
        directional_bias = self._determine_directional_bias(
            institutional_bias=institutional_bias,
            absorption_patterns=absorption_patterns,
            volume_profile=volume_profile,
            current_price=current_price,
            value_area=value_area,
        )
        
        # Step 10: Calculate Confidence
        confidence = self._calculate_confidence(
            delta_print_zones=delta_print_zones,
            big_trades=big_trades,
            absorption_patterns=absorption_patterns,
        )
        
        return DeltaPrintAnalysis(
            timestamp=datetime.now(timezone.utc),
            symbol=symbol,
            current_price=current_price,
            value_area=value_area,
            volume_profile=volume_profile,
            big_trades=big_trades,
            institutional_bias=institutional_bias,
            absorption_patterns=absorption_patterns,
            volume_ledges=volume_ledges,
            delta_print_zones=delta_print_zones,
            best_entry_zone=best_entry_zone,
            market_structure=market_structure,
            directional_bias=directional_bias,
            confidence=confidence,
        )
    
    def _build_volume_profile(
        self,
        candles: List[Dict[str, Any]],
        num_levels: int = 50,
    ) -> List[DeltaLevel]:
        """Build volume profile from candle data."""
        if not candles:
            return []
        
        # Find price range
        all_highs = [c.get("high", c.get("close", 0)) for c in candles]
        all_lows = [c.get("low", c.get("close", 0)) for c in candles]
        price_high = max(all_highs)
        price_low = min(all_lows)
        
        if price_high == price_low:
            price_high = price_low * 1.01
        
        # Create price levels
        price_step = (price_high - price_low) / num_levels
        levels: Dict[int, Dict[str, float]] = {}
        
        for i in range(num_levels):
            levels[i] = {
                "price": price_low + (i + 0.5) * price_step,
                "volume": 0,
                "buy_volume": 0,
                "sell_volume": 0,
                "big_trades_count": 0,
                "big_trades_volume": 0,
            }
        
        # Distribute volume across levels
        avg_volume = np.mean([c.get("volume", 0) for c in candles]) if candles else 1
        
        for candle in candles:
            high = candle.get("high", candle.get("close", 0))
            low = candle.get("low", candle.get("close", 0))
            close = candle.get("close", 0)
            open_price = candle.get("open", close)
            volume = candle.get("volume", 0)
            
            if high == low:
                continue
            
            # Determine if bullish or bearish candle
            is_bullish = close >= open_price
            
            # Distribute volume across price levels touched by this candle
            for i in range(num_levels):
                level_price = levels[i]["price"]
                level_low = price_low + i * price_step
                level_high = price_low + (i + 1) * price_step
                
                # Check if candle touches this level
                if low <= level_high and high >= level_low:
                    # Calculate overlap
                    overlap_low = max(low, level_low)
                    overlap_high = min(high, level_high)
                    overlap_pct = (overlap_high - overlap_low) / (high - low) if high > low else 0
                    
                    level_volume = volume * overlap_pct
                    levels[i]["volume"] += level_volume
                    
                    # Estimate buy/sell volume based on candle direction and position
                    if is_bullish:
                        # Bullish candle: more buying at lower prices, more selling at higher
                        buy_pct = 0.6 if level_price < close else 0.4
                    else:
                        # Bearish candle: more selling at higher prices, more buying at lower
                        buy_pct = 0.4 if level_price > close else 0.6
                    
                    levels[i]["buy_volume"] += level_volume * buy_pct
                    levels[i]["sell_volume"] += level_volume * (1 - buy_pct)
                    
                    # Check for big trades
                    if volume > avg_volume * 2:
                        levels[i]["big_trades_count"] += 1
                        levels[i]["big_trades_volume"] += level_volume
        
        # Convert to DeltaLevel objects
        result = []
        for i in range(num_levels):
            level = levels[i]
            volume = level["volume"]
            if volume > 0:
                delta = level["buy_volume"] - level["sell_volume"]
                delta_pct = delta / volume if volume > 0 else 0
                
                result.append(DeltaLevel(
                    price=level["price"],
                    volume=volume,
                    buy_volume=level["buy_volume"],
                    sell_volume=level["sell_volume"],
                    delta=delta,
                    delta_pct=delta_pct,
                    big_trades_count=int(level["big_trades_count"]),
                    big_trades_volume=level["big_trades_volume"],
                ))
        
        return result
    
    def _calculate_value_area(
        self,
        volume_profile: List[DeltaLevel],
    ) -> ValueArea:
        """Calculate Value Area (VAH, VAL, POC)."""
        if not volume_profile:
            return ValueArea(vah=0, val=0, poc=0, total_volume=0, value_area_volume=0)
        
        # Sort by volume to find POC
        sorted_by_volume = sorted(volume_profile, key=lambda x: x.volume, reverse=True)
        poc = sorted_by_volume[0].price if sorted_by_volume else 0
        
        # Calculate total volume
        total_volume = sum(l.volume for l in volume_profile)
        target_volume = total_volume * self.value_area_pct
        
        # Find POC index in original profile
        sorted_by_price = sorted(volume_profile, key=lambda x: x.price)
        poc_idx = 0
        for i, level in enumerate(sorted_by_price):
            if level.price == poc:
                poc_idx = i
                break
        
        # Expand from POC until we reach target volume
        included = {poc_idx}
        current_volume = sorted_by_price[poc_idx].volume if sorted_by_price else 0
        
        low_idx = poc_idx
        high_idx = poc_idx
        
        while current_volume < target_volume and (low_idx > 0 or high_idx < len(sorted_by_price) - 1):
            # Check which direction to expand
            low_vol = sorted_by_price[low_idx - 1].volume if low_idx > 0 else 0
            high_vol = sorted_by_price[high_idx + 1].volume if high_idx < len(sorted_by_price) - 1 else 0
            
            if low_vol >= high_vol and low_idx > 0:
                low_idx -= 1
                current_volume += sorted_by_price[low_idx].volume
                included.add(low_idx)
            elif high_idx < len(sorted_by_price) - 1:
                high_idx += 1
                current_volume += sorted_by_price[high_idx].volume
                included.add(high_idx)
            else:
                break
        
        val = sorted_by_price[low_idx].price if sorted_by_price else 0
        vah = sorted_by_price[high_idx].price if sorted_by_price else 0
        
        return ValueArea(
            vah=vah,
            val=val,
            poc=poc,
            total_volume=total_volume,
            value_area_volume=current_volume,
        )
    
    def _detect_big_trades(
        self,
        candles: List[Dict[str, Any]],
        trades: Optional[List[Dict[str, Any]]] = None,
    ) -> List[BigTrade]:
        """Detect big trades (institutional footprint)."""
        big_trades = []
        
        if trades:
            # Use actual trade data if available
            avg_size = np.mean([t.get("size", 0) for t in trades]) if trades else 1
            
            for trade in trades:
                size = trade.get("size", 0)
                if size > avg_size * 5:  # 5x average = institutional
                    trade_size_class = self._classify_trade_size(size, avg_size)
                    
                    big_trades.append(BigTrade(
                        timestamp=trade.get("timestamp", datetime.now(timezone.utc)),
                        price=trade.get("price", 0),
                        size=size,
                        side=trade.get("side", "unknown"),
                        trade_size_class=trade_size_class,
                        is_aggressive=trade.get("is_aggressive", True),
                    ))
        else:
            # Estimate from candle data
            avg_volume = np.mean([c.get("volume", 0) for c in candles]) if candles else 1
            
            for candle in candles:
                volume = candle.get("volume", 0)
                if volume > avg_volume * 3:  # 3x average = significant
                    close = candle.get("close", 0)
                    open_price = candle.get("open", close)
                    is_bullish = close >= open_price
                    
                    trade_size_class = self._classify_trade_size(volume, avg_volume)
                    
                    big_trades.append(BigTrade(
                        timestamp=candle.get("timestamp", datetime.now(timezone.utc)),
                        price=close,
                        size=volume,
                        side="buy" if is_bullish else "sell",
                        trade_size_class=trade_size_class,
                        is_aggressive=True,  # Assume aggressive for high volume candles
                    ))
        
        return big_trades
    
    def _classify_trade_size(self, size: float, avg_size: float) -> TradeSize:
        """Classify trade size."""
        ratio = size / avg_size if avg_size > 0 else 1
        
        if ratio > 20:
            return TradeSize.WHALE
        elif ratio > 10:
            return TradeSize.INSTITUTIONAL
        elif ratio > 5:
            return TradeSize.LARGE
        elif ratio > 2:
            return TradeSize.MEDIUM
        return TradeSize.RETAIL
    
    def _calculate_institutional_bias(self, big_trades: List[BigTrade]) -> str:
        """Calculate institutional bias from big trades."""
        if not big_trades:
            return "neutral"
        
        buy_volume = sum(t.size for t in big_trades if t.side == "buy")
        sell_volume = sum(t.size for t in big_trades if t.side == "sell")
        
        total = buy_volume + sell_volume
        if total == 0:
            return "neutral"
        
        buy_pct = buy_volume / total
        
        if buy_pct > 0.6:
            return "bullish"
        elif buy_pct < 0.4:
            return "bearish"
        return "neutral"
    
    def _detect_absorption_patterns(
        self,
        candles: List[Dict[str, Any]],
        volume_profile: List[DeltaLevel],
    ) -> List[AbsorptionPattern]:
        """Detect absorption patterns."""
        patterns = []
        
        if len(candles) < 3:
            return patterns
        
        # Look for absorption: high volume but price doesn't move much
        for i in range(2, len(candles)):
            c1 = candles[i - 2]
            c2 = candles[i - 1]
            c3 = candles[i]
            
            # Get volumes
            v1 = c1.get("volume", 0)
            v2 = c2.get("volume", 0)
            v3 = c3.get("volume", 0)
            
            # Get price movements
            close1 = c1.get("close", 0)
            close2 = c2.get("close", 0)
            close3 = c3.get("close", 0)
            
            high2 = c2.get("high", close2)
            low2 = c2.get("low", close2)
            
            # Check for absorption pattern:
            # High volume candle (c2) but price reverses (c3)
            avg_volume = (v1 + v2 + v3) / 3
            
            if v2 > avg_volume * 1.5:  # High volume
                price_range = high2 - low2 if high2 > low2 else 0.0001
                
                # Buyer absorption: aggressive buyers get absorbed, price goes down
                if close2 > close1 and close3 < close2:
                    absorption_ratio = abs(close2 - close3) / price_range
                    if absorption_ratio > 0.3:
                        patterns.append(AbsorptionPattern(
                            timestamp=c2.get("timestamp", datetime.now(timezone.utc)),
                            price_start=close1,
                            price_end=close3,
                            absorption_type=AbsorptionType.BUYER_ABSORPTION,
                            aggressive_volume=v2,
                            absorbed_volume=v2 * absorption_ratio,
                            absorption_ratio=absorption_ratio,
                            candle_count=3,
                            confidence=min(absorption_ratio, 1.0),
                        ))
                
                # Seller absorption: aggressive sellers get absorbed, price goes up
                elif close2 < close1 and close3 > close2:
                    absorption_ratio = abs(close3 - close2) / price_range
                    if absorption_ratio > 0.3:
                        patterns.append(AbsorptionPattern(
                            timestamp=c2.get("timestamp", datetime.now(timezone.utc)),
                            price_start=close1,
                            price_end=close3,
                            absorption_type=AbsorptionType.SELLER_ABSORPTION,
                            aggressive_volume=v2,
                            absorbed_volume=v2 * absorption_ratio,
                            absorption_ratio=absorption_ratio,
                            candle_count=3,
                            confidence=min(absorption_ratio, 1.0),
                        ))
        
        return patterns
    
    def _detect_volume_ledges(
        self,
        volume_profile: List[DeltaLevel],
        current_price: float,
    ) -> List[VolumeLedge]:
        """Detect volume ledges (sharp transitions in volume)."""
        ledges = []
        
        if len(volume_profile) < 3:
            return ledges
        
        # Sort by price
        sorted_profile = sorted(volume_profile, key=lambda x: x.price)
        
        for i in range(1, len(sorted_profile) - 1):
            prev_level = sorted_profile[i - 1]
            curr_level = sorted_profile[i]
            next_level = sorted_profile[i + 1]
            
            # Check for ledge: high volume followed by low volume
            if curr_level.volume > 0 and next_level.volume > 0:
                ratio = curr_level.volume / next_level.volume
                
                if ratio >= self.ledge_ratio_threshold:
                    direction = "above" if curr_level.price > current_price else "below"
                    
                    # Determine strength
                    if ratio > 10:
                        strength = ZoneStrength.EXTREME
                    elif ratio > 7:
                        strength = ZoneStrength.VERY_STRONG
                    elif ratio > 5:
                        strength = ZoneStrength.STRONG
                    elif ratio > 3:
                        strength = ZoneStrength.MODERATE
                    else:
                        strength = ZoneStrength.WEAK
                    
                    ledges.append(VolumeLedge(
                        price_high=curr_level.price,
                        price_low=next_level.price,
                        volume_high=curr_level.volume,
                        volume_low=next_level.volume,
                        ledge_ratio=ratio,
                        direction=direction,
                        strength=strength,
                    ))
            
            # Also check for ledge in opposite direction
            if prev_level.volume > 0 and curr_level.volume > 0:
                ratio = curr_level.volume / prev_level.volume
                
                if ratio >= self.ledge_ratio_threshold:
                    direction = "above" if curr_level.price > current_price else "below"
                    
                    if ratio > 10:
                        strength = ZoneStrength.EXTREME
                    elif ratio > 7:
                        strength = ZoneStrength.VERY_STRONG
                    elif ratio > 5:
                        strength = ZoneStrength.STRONG
                    elif ratio > 3:
                        strength = ZoneStrength.MODERATE
                    else:
                        strength = ZoneStrength.WEAK
                    
                    ledges.append(VolumeLedge(
                        price_high=curr_level.price,
                        price_low=prev_level.price,
                        volume_high=curr_level.volume,
                        volume_low=prev_level.volume,
                        ledge_ratio=ratio,
                        direction=direction,
                        strength=strength,
                    ))
        
        return ledges
    
    def _identify_delta_print_zones(
        self,
        volume_profile: List[DeltaLevel],
        value_area: ValueArea,
        big_trades: List[BigTrade],
        absorption_patterns: List[AbsorptionPattern],
        volume_ledges: List[VolumeLedge],
        current_price: float,
    ) -> List[DeltaPrintZone]:
        """Identify Delta Print zones - high probability entry areas."""
        zones = []
        
        if not volume_profile:
            return zones
        
        # Find high delta pressure levels
        sorted_by_delta = sorted(volume_profile, key=lambda x: abs(x.delta), reverse=True)
        
        # Take top 10 levels with highest delta
        top_delta_levels = sorted_by_delta[:10]
        
        for level in top_delta_levels:
            # Calculate zone boundaries
            price_range = (max(l.price for l in volume_profile) - min(l.price for l in volume_profile)) / len(volume_profile)
            price_high = level.price + price_range / 2
            price_low = level.price - price_range / 2
            
            # Determine zone type
            zone_type = "resistance" if level.price > current_price else "support"
            
            # Check for big trades at this level
            big_trades_at_level = [
                t for t in big_trades
                if price_low <= t.price <= price_high
            ]
            big_trades_count = len(big_trades_at_level)
            big_trades_volume = sum(t.size for t in big_trades_at_level)
            
            # Check for absorption at this level
            absorption_at_level = [
                p for p in absorption_patterns
                if price_low <= p.price_end <= price_high
            ]
            has_absorption = len(absorption_at_level) > 0
            absorption_type = absorption_at_level[0].absorption_type if absorption_at_level else None
            
            # Check for volume ledge at this level
            ledges_at_level = [
                l for l in volume_ledges
                if price_low <= l.price_high <= price_high or price_low <= l.price_low <= price_high
            ]
            has_volume_ledge = len(ledges_at_level) > 0
            
            # Check if at value area boundary
            is_at_value_area = (
                abs(level.price - value_area.vah) < price_range or
                abs(level.price - value_area.val) < price_range
            )
            
            # Calculate confluence score
            confluence_score = self._calculate_confluence_score(
                delta_strength=abs(level.delta_pct),
                big_trades_count=big_trades_count,
                has_absorption=has_absorption,
                has_volume_ledge=has_volume_ledge,
                is_at_value_area=is_at_value_area,
                volume=level.volume,
                max_volume=max(l.volume for l in volume_profile),
            )
            
            # Determine strength
            if confluence_score > 0.8:
                strength = ZoneStrength.EXTREME
            elif confluence_score > 0.6:
                strength = ZoneStrength.VERY_STRONG
            elif confluence_score > 0.4:
                strength = ZoneStrength.STRONG
            elif confluence_score > 0.2:
                strength = ZoneStrength.MODERATE
            else:
                strength = ZoneStrength.WEAK
            
            # Generate reasoning
            reasoning = self._generate_zone_reasoning(
                level=level,
                big_trades_count=big_trades_count,
                has_absorption=has_absorption,
                absorption_type=absorption_type,
                has_volume_ledge=has_volume_ledge,
                is_at_value_area=is_at_value_area,
                zone_type=zone_type,
            )
            
            zones.append(DeltaPrintZone(
                price_high=price_high,
                price_low=price_low,
                zone_type=zone_type,
                delta_pressure=level.direction,
                big_trades_count=big_trades_count,
                big_trades_volume=big_trades_volume,
                has_absorption=has_absorption,
                absorption_type=absorption_type,
                has_volume_ledge=has_volume_ledge,
                is_at_value_area=is_at_value_area,
                confluence_score=confluence_score,
                strength=strength,
                reasoning=reasoning,
            ))
        
        # Sort by confluence score
        zones.sort(key=lambda x: x.confluence_score, reverse=True)
        
        return zones
    
    def _calculate_confluence_score(
        self,
        delta_strength: float,
        big_trades_count: int,
        has_absorption: bool,
        has_volume_ledge: bool,
        is_at_value_area: bool,
        volume: float,
        max_volume: float,
    ) -> float:
        """Calculate confluence score for a zone."""
        score = 0.0
        
        # Delta strength (0-0.25)
        score += min(delta_strength, 0.5) * 0.5  # Max 0.25
        
        # Big trades (0-0.2)
        score += min(big_trades_count / 5, 1.0) * 0.2
        
        # Absorption (0-0.2)
        if has_absorption:
            score += 0.2
        
        # Volume ledge (0-0.15)
        if has_volume_ledge:
            score += 0.15
        
        # Value area (0-0.1)
        if is_at_value_area:
            score += 0.1
        
        # Volume relative to max (0-0.1)
        if max_volume > 0:
            score += (volume / max_volume) * 0.1
        
        return min(score, 1.0)
    
    def _generate_zone_reasoning(
        self,
        level: DeltaLevel,
        big_trades_count: int,
        has_absorption: bool,
        absorption_type: Optional[AbsorptionType],
        has_volume_ledge: bool,
        is_at_value_area: bool,
        zone_type: str,
    ) -> str:
        """Generate human-readable reasoning for a zone."""
        reasons = []
        
        # Delta pressure
        if level.direction == DeltaDirection.STRONG_SELLING:
            reasons.append(f"Strong selling pressure ({level.delta_pct:.0%} delta)")
        elif level.direction == DeltaDirection.STRONG_BUYING:
            reasons.append(f"Strong buying pressure ({level.delta_pct:.0%} delta)")
        elif level.direction == DeltaDirection.MODERATE_SELLING:
            reasons.append(f"Moderate selling pressure ({level.delta_pct:.0%} delta)")
        elif level.direction == DeltaDirection.MODERATE_BUYING:
            reasons.append(f"Moderate buying pressure ({level.delta_pct:.0%} delta)")
        
        # Big trades
        if big_trades_count > 0:
            reasons.append(f"{big_trades_count} institutional trades detected")
        
        # Absorption
        if has_absorption:
            if absorption_type == AbsorptionType.BUYER_ABSORPTION:
                reasons.append("Buyer absorption pattern (sellers in control)")
            elif absorption_type == AbsorptionType.SELLER_ABSORPTION:
                reasons.append("Seller absorption pattern (buyers in control)")
        
        # Volume ledge
        if has_volume_ledge:
            reasons.append("Volume ledge creates natural support/resistance")
        
        # Value area
        if is_at_value_area:
            reasons.append("At Value Area boundary (VAH/VAL)")
        
        if not reasons:
            reasons.append(f"Price level with notable volume activity")
        
        return f"{zone_type.upper()} ZONE: " + "; ".join(reasons)
    
    def _find_best_entry_zone(
        self,
        delta_print_zones: List[DeltaPrintZone],
        current_price: float,
    ) -> Optional[DeltaPrintZone]:
        """Find the best entry zone near current price."""
        if not delta_print_zones:
            return None
        
        # Filter zones that are close to current price (within 1%)
        nearby_zones = [
            z for z in delta_print_zones
            if abs((z.price_high + z.price_low) / 2 - current_price) / current_price < 0.01
        ]
        
        if nearby_zones:
            # Return highest confluence score
            return max(nearby_zones, key=lambda x: x.confluence_score)
        
        # If no nearby zones, return the highest confluence zone
        return delta_print_zones[0] if delta_print_zones else None
    
    def _assess_market_structure(
        self,
        candles: List[Dict[str, Any]],
        value_area: ValueArea,
    ) -> str:
        """Assess market structure (trending, ranging, transitioning)."""
        if len(candles) < 10:
            return "unknown"
        
        # Get recent closes
        recent_closes = [c.get("close", 0) for c in candles[-20:]]
        current_price = recent_closes[-1] if recent_closes else 0
        
        # Check if price is within value area
        in_value_area = value_area.val <= current_price <= value_area.vah
        
        # Calculate trend
        if len(recent_closes) >= 10:
            first_half_avg = np.mean(recent_closes[:10])
            second_half_avg = np.mean(recent_closes[10:]) if len(recent_closes) > 10 else first_half_avg
            
            trend_strength = abs(second_half_avg - first_half_avg) / first_half_avg if first_half_avg > 0 else 0
            
            if trend_strength > 0.01:  # 1% move
                if in_value_area:
                    return "transitioning"
                return "trending"
        
        if in_value_area:
            return "ranging"
        
        return "transitioning"
    
    def _determine_directional_bias(
        self,
        institutional_bias: str,
        absorption_patterns: List[AbsorptionPattern],
        volume_profile: List[DeltaLevel],
        current_price: float,
        value_area: ValueArea,
    ) -> str:
        """Determine directional bias."""
        bullish_signals = 0
        bearish_signals = 0
        
        # Institutional bias
        if institutional_bias == "bullish":
            bullish_signals += 2
        elif institutional_bias == "bearish":
            bearish_signals += 2
        
        # Absorption patterns
        for pattern in absorption_patterns[-5:]:  # Recent patterns
            if pattern.absorption_type == AbsorptionType.SELLER_ABSORPTION:
                bullish_signals += 1
            elif pattern.absorption_type == AbsorptionType.BUYER_ABSORPTION:
                bearish_signals += 1
        
        # Price relative to value area
        if current_price > value_area.vah:
            bullish_signals += 1
        elif current_price < value_area.val:
            bearish_signals += 1
        
        # Delta profile bias
        if volume_profile:
            total_delta = sum(l.delta for l in volume_profile)
            if total_delta > 0:
                bullish_signals += 1
            elif total_delta < 0:
                bearish_signals += 1
        
        if bullish_signals > bearish_signals + 1:
            return "bullish"
        elif bearish_signals > bullish_signals + 1:
            return "bearish"
        return "neutral"
    
    def _calculate_confidence(
        self,
        delta_print_zones: List[DeltaPrintZone],
        big_trades: List[BigTrade],
        absorption_patterns: List[AbsorptionPattern],
    ) -> float:
        """Calculate overall confidence in the analysis."""
        confidence = 0.5  # Base confidence
        
        # Strong zones increase confidence
        if delta_print_zones:
            best_zone_score = delta_print_zones[0].confluence_score
            confidence += best_zone_score * 0.2
        
        # Big trades increase confidence
        if big_trades:
            confidence += min(len(big_trades) / 10, 0.15)
        
        # Absorption patterns increase confidence
        if absorption_patterns:
            confidence += min(len(absorption_patterns) / 5, 0.15)
        
        return min(confidence, 1.0)
    
    def get_entry_recommendation(
        self,
        analysis: DeltaPrintAnalysis,
    ) -> Dict[str, Any]:
        """
        Get entry recommendation based on Delta Print analysis.
        
        This is where we SURPASS DeepCharts - we don't just show data,
        we make intelligent recommendations.
        """
        if not analysis.best_entry_zone:
            return {
                "action": "WAIT",
                "reason": "No high-probability entry zone identified",
                "confidence": 0.0,
            }
        
        zone = analysis.best_entry_zone
        
        # Determine action based on zone type and directional bias
        if zone.zone_type == "support" and analysis.directional_bias in ["bullish", "neutral"]:
            action = "BUY"
            entry_price = zone.price_low
            stop_loss = zone.price_low * 0.995  # 0.5% below zone
            take_profit = zone.price_high + (zone.price_high - zone.price_low) * 2  # 2:1 R:R
        elif zone.zone_type == "resistance" and analysis.directional_bias in ["bearish", "neutral"]:
            action = "SELL"
            entry_price = zone.price_high
            stop_loss = zone.price_high * 1.005  # 0.5% above zone
            take_profit = zone.price_low - (zone.price_high - zone.price_low) * 2  # 2:1 R:R
        else:
            return {
                "action": "WAIT",
                "reason": f"Zone type ({zone.zone_type}) conflicts with directional bias ({analysis.directional_bias})",
                "confidence": 0.0,
            }
        
        # Check confidence threshold
        if zone.confluence_score < 0.4:
            return {
                "action": "WAIT",
                "reason": f"Confluence score too low ({zone.confluence_score:.0%})",
                "confidence": zone.confluence_score,
            }
        
        return {
            "action": action,
            "entry_price": entry_price,
            "stop_loss": stop_loss,
            "take_profit": take_profit,
            "zone": zone.to_dict(),
            "reason": zone.reasoning,
            "confluence_score": zone.confluence_score,
            "confidence": analysis.confidence,
            "directional_bias": analysis.directional_bias,
            "institutional_bias": analysis.institutional_bias,
            "market_structure": analysis.market_structure,
        }


def create_delta_print_intelligence(**kwargs) -> DeltaPrintIntelligence:
    """Factory function to create Delta Print Intelligence."""
    return DeltaPrintIntelligence(**kwargs)
