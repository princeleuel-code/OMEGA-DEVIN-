"""
Feature Engine - Compute indicators and market structure

Translates raw OHLCV data into actionable features for the decision engine.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Dict, Any, Tuple
from enum import Enum, auto
import math

from .loader import OHLCV
from ..intelligence.aether_indicator import AetherIndicator


class StructureType(Enum):
    """Market structure types"""
    HH = auto()  # Higher High
    HL = auto()  # Higher Low
    LH = auto()  # Lower High
    LL = auto()  # Lower Low
    EQUAL = auto()  # Equal level


class Trend(Enum):
    """Market trend"""
    BULLISH = auto()
    BEARISH = auto()
    RANGING = auto()
    UNKNOWN = auto()


@dataclass
class SwingPoint:
    """A swing high or low point"""
    index: int
    timestamp: datetime
    price: float
    is_high: bool  # True for swing high, False for swing low
    structure: Optional[StructureType] = None


@dataclass
class MarketStructure:
    """Current market structure state"""
    trend: Trend
    last_swing_high: Optional[SwingPoint] = None
    last_swing_low: Optional[SwingPoint] = None
    structure_break: bool = False  # BOS (Break of Structure)
    change_of_character: bool = False  # CHoCH
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "trend": self.trend.name,
            "last_swing_high": self.last_swing_high.price if self.last_swing_high else None,
            "last_swing_low": self.last_swing_low.price if self.last_swing_low else None,
            "structure_break": self.structure_break,
            "change_of_character": self.change_of_character
        }


@dataclass
class Features:
    """Computed features for a single bar"""
    timestamp: datetime
    
    # Price features
    close: float
    atr: float  # Average True Range
    volatility: float  # Normalized volatility
    
    # Momentum
    momentum: float  # Price change over N bars
    roc: float  # Rate of change
    
    # Volume features
    relative_volume: float  # Volume vs average
    
    # Structure
    structure: MarketStructure
    
    # Displacement (strong move)
    displacement: bool
    displacement_direction: Optional[int] = None  # 1 for up, -1 for down
    
    # AETHER topological/spectral state vector
    aether: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp.isoformat(),
            "close": self.close,
            "atr": self.atr,
            "volatility": self.volatility,
            "momentum": self.momentum,
            "roc": self.roc,
            "relative_volume": self.relative_volume,
            "structure": self.structure.to_dict(),
            "displacement": self.displacement,
            "displacement_direction": self.displacement_direction,
            "aether": self.aether,
        }


class FeatureEngine:
    """
    Compute trading features from OHLCV data.
    
    Features include:
    - ATR (Average True Range)
    - Volatility (normalized)
    - Momentum and ROC
    - Market structure (HH/HL/LH/LL)
    - Displacement detection
    """
    
    def __init__(
        self,
        atr_period: int = 14,
        momentum_period: int = 10,
        volume_period: int = 20,
        swing_lookback: int = 5,
        displacement_threshold: float = 1.5  # ATR multiplier
    ):
        self.atr_period = atr_period
        self.momentum_period = momentum_period
        self.volume_period = volume_period
        self.swing_lookback = swing_lookback
        self.displacement_threshold = displacement_threshold
        
        # State
        self._swing_highs: List[SwingPoint] = []
        self._swing_lows: List[SwingPoint] = []
        self._current_trend = Trend.UNKNOWN
    
    def compute(self, data: List[OHLCV]) -> List[Features]:
        """
        Compute features for all bars in the data.
        """
        if len(data) < max(self.atr_period, self.momentum_period, self.volume_period) + 1:
            return []
        
        features = []
        
        # Pre-compute ATR series
        atr_series = self._compute_atr_series(data)
        
        # Pre-compute volume average
        vol_avg = self._compute_volume_average(data)
        
        # Find swing points
        self._find_swing_points(data)
        
        # Compute AETHER series once for the entire run
        aether_indicator = AetherIndicator()
        aether_series = aether_indicator.compute(data)
        
        # Compute features for each bar (after warmup period)
        warmup = max(self.atr_period, self.momentum_period, self.volume_period)
        
        for i in range(warmup, len(data)):
            bar = data[i]
            
            # ATR
            atr = atr_series[i] if i < len(atr_series) else atr_series[-1]
            
            # Volatility (ATR as % of price)
            volatility = (atr / bar.close) * 100 if bar.close > 0 else 0
            
            # Momentum
            momentum = bar.close - data[i - self.momentum_period].close
            roc = (momentum / data[i - self.momentum_period].close) * 100 if data[i - self.momentum_period].close > 0 else 0
            
            # Relative volume
            avg_vol = vol_avg[i] if i < len(vol_avg) else vol_avg[-1]
            relative_volume = bar.volume / avg_vol if avg_vol > 0 else 1.0
            
            # Market structure
            structure = self._get_structure_at(i, data)
            
            # Displacement detection
            displacement, disp_dir = self._detect_displacement(bar, atr)
            
            feat = Features(
                timestamp=bar.timestamp,
                close=bar.close,
                atr=atr,
                volatility=volatility,
                momentum=momentum,
                roc=roc,
                relative_volume=relative_volume,
                structure=structure,
                displacement=displacement,
                displacement_direction=disp_dir,
                aether=aether_series[i].to_dict() if i < len(aether_series) else None,
            )
            features.append(feat)
        
        return features
    
    def _compute_atr_series(self, data: List[OHLCV]) -> List[float]:
        """Compute ATR for all bars"""
        if len(data) < 2:
            return [0.0]
        
        # True Range series
        tr_series = []
        for i in range(1, len(data)):
            prev_close = data[i-1].close
            curr = data[i]
            tr = max(
                curr.high - curr.low,
                abs(curr.high - prev_close),
                abs(curr.low - prev_close)
            )
            tr_series.append(tr)
        
        # ATR (EMA of TR)
        atr_series = [0.0]  # Placeholder for first bar
        if len(tr_series) >= self.atr_period:
            # Initial SMA
            atr = sum(tr_series[:self.atr_period]) / self.atr_period
            atr_series.append(atr)
            
            # EMA for rest
            multiplier = 2 / (self.atr_period + 1)
            for i in range(self.atr_period, len(tr_series)):
                atr = (tr_series[i] * multiplier) + (atr * (1 - multiplier))
                atr_series.append(atr)
        
        return atr_series
    
    def _compute_volume_average(self, data: List[OHLCV]) -> List[float]:
        """Compute rolling volume average"""
        vol_avg = []
        for i in range(len(data)):
            start = max(0, i - self.volume_period + 1)
            window = [d.volume for d in data[start:i+1]]
            avg = sum(window) / len(window) if window else 1.0
            vol_avg.append(avg)
        return vol_avg
    
    def _find_swing_points(self, data: List[OHLCV]):
        """Find swing highs and lows"""
        self._swing_highs = []
        self._swing_lows = []
        
        lookback = self.swing_lookback
        
        for i in range(lookback, len(data) - lookback):
            bar = data[i]
            
            # Check for swing high
            is_swing_high = all(
                bar.high >= data[j].high 
                for j in range(i - lookback, i + lookback + 1) 
                if j != i
            )
            
            if is_swing_high:
                swing = SwingPoint(
                    index=i,
                    timestamp=bar.timestamp,
                    price=bar.high,
                    is_high=True
                )
                # Determine structure type
                if self._swing_highs:
                    prev = self._swing_highs[-1]
                    if swing.price > prev.price:
                        swing.structure = StructureType.HH
                    elif swing.price < prev.price:
                        swing.structure = StructureType.LH
                    else:
                        swing.structure = StructureType.EQUAL
                self._swing_highs.append(swing)
            
            # Check for swing low
            is_swing_low = all(
                bar.low <= data[j].low 
                for j in range(i - lookback, i + lookback + 1) 
                if j != i
            )
            
            if is_swing_low:
                swing = SwingPoint(
                    index=i,
                    timestamp=bar.timestamp,
                    price=bar.low,
                    is_high=False
                )
                # Determine structure type
                if self._swing_lows:
                    prev = self._swing_lows[-1]
                    if swing.price > prev.price:
                        swing.structure = StructureType.HL
                    elif swing.price < prev.price:
                        swing.structure = StructureType.LL
                    else:
                        swing.structure = StructureType.EQUAL
                self._swing_lows.append(swing)
    
    def _get_structure_at(self, index: int, data: List[OHLCV]) -> MarketStructure:
        """Get market structure at a specific bar index"""
        # Find most recent swing points before this index
        last_high = None
        last_low = None
        
        for sh in reversed(self._swing_highs):
            if sh.index < index:
                last_high = sh
                break
        
        for sl in reversed(self._swing_lows):
            if sl.index < index:
                last_low = sl
                break
        
        # Determine trend
        trend = Trend.UNKNOWN
        structure_break = False
        choch = False
        
        if last_high and last_low:
            # Check recent structure
            recent_highs = [sh for sh in self._swing_highs if sh.index < index][-2:]
            recent_lows = [sl for sl in self._swing_lows if sl.index < index][-2:]
            
            if len(recent_highs) >= 2 and len(recent_lows) >= 2:
                # Bullish: HH + HL
                if (recent_highs[-1].structure == StructureType.HH and 
                    recent_lows[-1].structure == StructureType.HL):
                    trend = Trend.BULLISH
                # Bearish: LH + LL
                elif (recent_highs[-1].structure == StructureType.LH and 
                      recent_lows[-1].structure == StructureType.LL):
                    trend = Trend.BEARISH
                else:
                    trend = Trend.RANGING
                
                # Check for BOS (Break of Structure)
                current_price = data[index].close
                if trend == Trend.BULLISH and last_low:
                    if current_price < last_low.price:
                        structure_break = True
                        choch = True  # Change of character
                elif trend == Trend.BEARISH and last_high:
                    if current_price > last_high.price:
                        structure_break = True
                        choch = True
        
        return MarketStructure(
            trend=trend,
            last_swing_high=last_high,
            last_swing_low=last_low,
            structure_break=structure_break,
            change_of_character=choch
        )
    
    def _detect_displacement(self, bar: OHLCV, atr: float) -> Tuple[bool, Optional[int]]:
        """
        Detect displacement (strong impulsive move).
        
        Displacement = candle body > threshold * ATR
        """
        if atr <= 0:
            return False, None
        
        body = bar.body
        threshold = self.displacement_threshold * atr
        
        if body > threshold:
            direction = 1 if bar.is_bullish else -1
            return True, direction
        
        return False, None
    
    def get_swing_highs(self) -> List[SwingPoint]:
        return self._swing_highs.copy()
    
    def get_swing_lows(self) -> List[SwingPoint]:
        return self._swing_lows.copy()
