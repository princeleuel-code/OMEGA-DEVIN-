"""
Multi-Timeframe (MTF) Confluence Intelligence Module

This module implements institutional-grade multi-timeframe analysis:
1. HTF (Higher Timeframe) for direction/bias
2. LTF (Lower Timeframe) for precise entries
3. Confluence scoring across all timeframes
4. Alignment detection for high-probability setups

The BEST traders use MTF confluence - they don't just look at one chart.
This is how institutions actually trade.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple, Any
from enum import Enum
import math


class TimeframeType(Enum):
    """Standard trading timeframes"""
    M1 = "1m"
    M5 = "5m"
    M15 = "15m"
    M30 = "30m"
    H1 = "1h"
    H4 = "4h"
    D1 = "1d"
    W1 = "1w"


class TrendDirection(Enum):
    """Trend direction"""
    STRONG_BULLISH = "strong_bullish"
    BULLISH = "bullish"
    WEAK_BULLISH = "weak_bullish"
    NEUTRAL = "neutral"
    WEAK_BEARISH = "weak_bearish"
    BEARISH = "bearish"
    STRONG_BEARISH = "strong_bearish"


class AlignmentType(Enum):
    """MTF alignment types"""
    FULL_BULLISH = "full_bullish"  # All timeframes bullish
    PARTIAL_BULLISH = "partial_bullish"  # Most timeframes bullish
    MIXED = "mixed"  # No clear alignment
    PARTIAL_BEARISH = "partial_bearish"  # Most timeframes bearish
    FULL_BEARISH = "full_bearish"  # All timeframes bearish


@dataclass
class TimeframeAnalysis:
    """Analysis for a single timeframe"""
    timeframe: TimeframeType
    trend: TrendDirection
    trend_strength: float  # 0-1
    
    # Structure
    higher_high: bool
    higher_low: bool
    lower_high: bool
    lower_low: bool
    
    # Key levels
    swing_high: float
    swing_low: float
    current_price: float
    
    # Momentum
    momentum_score: float  # -1 to 1
    rsi: float
    
    # Moving averages
    ema_20: float
    ema_50: float
    ema_200: float
    price_vs_ema_20: str  # "above" or "below"
    price_vs_ema_50: str
    price_vs_ema_200: str
    ema_alignment: str  # "bullish", "bearish", or "mixed"
    
    # Volume
    volume_trend: str  # "increasing", "decreasing", "flat"
    relative_volume: float  # Current volume vs average
    
    # Bias
    bias: TrendDirection
    bias_confidence: float
    
    def get_score(self) -> float:
        """Get overall score for this timeframe (-1 to 1)"""
        score = 0.0
        
        # Trend contribution
        trend_scores = {
            TrendDirection.STRONG_BULLISH: 1.0,
            TrendDirection.BULLISH: 0.6,
            TrendDirection.WEAK_BULLISH: 0.3,
            TrendDirection.NEUTRAL: 0.0,
            TrendDirection.WEAK_BEARISH: -0.3,
            TrendDirection.BEARISH: -0.6,
            TrendDirection.STRONG_BEARISH: -1.0
        }
        score += trend_scores.get(self.trend, 0) * 0.4
        
        # Structure contribution
        if self.higher_high and self.higher_low:
            score += 0.2
        elif self.lower_high and self.lower_low:
            score -= 0.2
        
        # EMA alignment contribution
        if self.ema_alignment == "bullish":
            score += 0.2
        elif self.ema_alignment == "bearish":
            score -= 0.2
        
        # Momentum contribution
        score += self.momentum_score * 0.2
        
        return max(-1.0, min(1.0, score))


@dataclass
class MTFConfluence:
    """Multi-timeframe confluence analysis result"""
    timeframe_analyses: Dict[TimeframeType, TimeframeAnalysis]
    alignment: AlignmentType
    alignment_score: float  # 0-1 (how aligned are the timeframes)
    
    # Weighted scores
    htf_score: float  # Higher timeframe score (4H, D1)
    mtf_score: float  # Medium timeframe score (1H, 15M)
    ltf_score: float  # Lower timeframe score (5M, 1M)
    overall_score: float  # Combined weighted score
    
    # Direction
    direction: TrendDirection
    direction_confidence: float
    
    # Key levels from all timeframes
    htf_resistance: float
    htf_support: float
    mtf_resistance: float
    mtf_support: float
    ltf_resistance: float
    ltf_support: float
    
    # Confluence zones (where multiple TF levels overlap)
    confluence_resistance_zones: List[Tuple[float, float, int]]  # (top, bottom, num_timeframes)
    confluence_support_zones: List[Tuple[float, float, int]]
    
    # Trade recommendation
    trade_direction: Optional[str]  # "LONG", "SHORT", or None
    entry_timeframe: Optional[TimeframeType]
    confidence: float
    reasoning: List[str]
    
    def get_summary(self) -> str:
        """Get human-readable summary"""
        return f"""
MTF CONFLUENCE ANALYSIS
=======================
Alignment: {self.alignment.value} ({self.alignment_score:.1%})
Direction: {self.direction.value} ({self.direction_confidence:.1%})

HTF Score: {self.htf_score:+.2f}
MTF Score: {self.mtf_score:+.2f}
LTF Score: {self.ltf_score:+.2f}
Overall: {self.overall_score:+.2f}

Trade: {self.trade_direction or 'NO TRADE'}
Confidence: {self.confidence:.1%}

Reasoning:
{chr(10).join('- ' + r for r in self.reasoning)}
"""


class MTFIntelligence:
    """
    Multi-Timeframe Confluence Intelligence Engine
    
    Analyzes multiple timeframes to find high-probability setups
    where all timeframes align. This is how institutional traders
    actually make decisions - not by looking at a single chart.
    """
    
    # Timeframe weights for scoring
    TIMEFRAME_WEIGHTS = {
        TimeframeType.W1: 0.15,
        TimeframeType.D1: 0.20,
        TimeframeType.H4: 0.20,
        TimeframeType.H1: 0.15,
        TimeframeType.M30: 0.10,
        TimeframeType.M15: 0.10,
        TimeframeType.M5: 0.05,
        TimeframeType.M1: 0.05
    }
    
    # Timeframe categories
    HTF_TIMEFRAMES = [TimeframeType.W1, TimeframeType.D1, TimeframeType.H4]
    MTF_TIMEFRAMES = [TimeframeType.H1, TimeframeType.M30, TimeframeType.M15]
    LTF_TIMEFRAMES = [TimeframeType.M5, TimeframeType.M1]
    
    def __init__(
        self,
        swing_lookback: int = 20,
        ema_periods: Tuple[int, int, int] = (20, 50, 200),
        rsi_period: int = 14,
        volume_ma_period: int = 20,
        confluence_zone_tolerance: float = 0.002  # 0.2% tolerance for level overlap
    ):
        """
        Initialize MTF Intelligence
        
        Args:
            swing_lookback: Bars to look back for swing detection
            ema_periods: EMA periods (fast, medium, slow)
            rsi_period: RSI calculation period
            volume_ma_period: Volume moving average period
            confluence_zone_tolerance: Tolerance for level confluence detection
        """
        self.swing_lookback = swing_lookback
        self.ema_periods = ema_periods
        self.rsi_period = rsi_period
        self.volume_ma_period = volume_ma_period
        self.confluence_zone_tolerance = confluence_zone_tolerance
    
    def analyze(
        self,
        timeframe_data: Dict[TimeframeType, List[Dict[str, Any]]]
    ) -> MTFConfluence:
        """
        Perform multi-timeframe confluence analysis
        
        Args:
            timeframe_data: Dictionary mapping timeframes to their bar data
            
        Returns:
            MTFConfluence with complete analysis
        """
        # Analyze each timeframe
        timeframe_analyses = {}
        for tf, bars in timeframe_data.items():
            if len(bars) >= max(self.ema_periods) + 10:
                analysis = self._analyze_timeframe(tf, bars)
                timeframe_analyses[tf] = analysis
        
        if not timeframe_analyses:
            return self._empty_confluence()
        
        # Calculate category scores
        htf_score = self._calculate_category_score(timeframe_analyses, self.HTF_TIMEFRAMES)
        mtf_score = self._calculate_category_score(timeframe_analyses, self.MTF_TIMEFRAMES)
        ltf_score = self._calculate_category_score(timeframe_analyses, self.LTF_TIMEFRAMES)
        
        # Calculate overall weighted score
        overall_score = self._calculate_overall_score(timeframe_analyses)
        
        # Determine alignment
        alignment, alignment_score = self._determine_alignment(timeframe_analyses)
        
        # Determine direction
        direction, direction_confidence = self._determine_direction(
            overall_score, alignment, alignment_score
        )
        
        # Extract key levels
        htf_resistance, htf_support = self._get_category_levels(timeframe_analyses, self.HTF_TIMEFRAMES)
        mtf_resistance, mtf_support = self._get_category_levels(timeframe_analyses, self.MTF_TIMEFRAMES)
        ltf_resistance, ltf_support = self._get_category_levels(timeframe_analyses, self.LTF_TIMEFRAMES)
        
        # Find confluence zones
        all_resistances = self._collect_levels(timeframe_analyses, is_resistance=True)
        all_supports = self._collect_levels(timeframe_analyses, is_resistance=False)
        
        confluence_resistance_zones = self._find_confluence_zones(all_resistances)
        confluence_support_zones = self._find_confluence_zones(all_supports)
        
        # Generate trade recommendation
        trade_direction, entry_timeframe, confidence, reasoning = self._generate_recommendation(
            timeframe_analyses, alignment, alignment_score, direction, direction_confidence,
            htf_score, mtf_score, ltf_score
        )
        
        return MTFConfluence(
            timeframe_analyses=timeframe_analyses,
            alignment=alignment,
            alignment_score=alignment_score,
            htf_score=htf_score,
            mtf_score=mtf_score,
            ltf_score=ltf_score,
            overall_score=overall_score,
            direction=direction,
            direction_confidence=direction_confidence,
            htf_resistance=htf_resistance,
            htf_support=htf_support,
            mtf_resistance=mtf_resistance,
            mtf_support=mtf_support,
            ltf_resistance=ltf_resistance,
            ltf_support=ltf_support,
            confluence_resistance_zones=confluence_resistance_zones,
            confluence_support_zones=confluence_support_zones,
            trade_direction=trade_direction,
            entry_timeframe=entry_timeframe,
            confidence=confidence,
            reasoning=reasoning
        )
    
    def _analyze_timeframe(
        self,
        timeframe: TimeframeType,
        bars: List[Dict[str, Any]]
    ) -> TimeframeAnalysis:
        """Analyze a single timeframe"""
        current_price = bars[-1]["close"]
        
        # Calculate EMAs
        ema_20 = self._calculate_ema(bars, self.ema_periods[0])
        ema_50 = self._calculate_ema(bars, self.ema_periods[1])
        ema_200 = self._calculate_ema(bars, self.ema_periods[2])
        
        # Price vs EMAs
        price_vs_ema_20 = "above" if current_price > ema_20 else "below"
        price_vs_ema_50 = "above" if current_price > ema_50 else "below"
        price_vs_ema_200 = "above" if current_price > ema_200 else "below"
        
        # EMA alignment
        if ema_20 > ema_50 > ema_200:
            ema_alignment = "bullish"
        elif ema_20 < ema_50 < ema_200:
            ema_alignment = "bearish"
        else:
            ema_alignment = "mixed"
        
        # Find swing points
        swing_high, swing_low = self._find_swing_levels(bars)
        
        # Detect structure
        higher_high, higher_low, lower_high, lower_low = self._detect_structure(bars)
        
        # Calculate RSI
        rsi = self._calculate_rsi(bars)
        
        # Calculate momentum
        momentum_score = self._calculate_momentum(bars, rsi)
        
        # Analyze volume
        volume_trend, relative_volume = self._analyze_volume(bars)
        
        # Determine trend
        trend, trend_strength = self._determine_trend(
            bars, ema_alignment, higher_high, higher_low, lower_high, lower_low, momentum_score
        )
        
        # Determine bias
        bias, bias_confidence = self._determine_tf_bias(
            trend, trend_strength, price_vs_ema_200, momentum_score
        )
        
        return TimeframeAnalysis(
            timeframe=timeframe,
            trend=trend,
            trend_strength=trend_strength,
            higher_high=higher_high,
            higher_low=higher_low,
            lower_high=lower_high,
            lower_low=lower_low,
            swing_high=swing_high,
            swing_low=swing_low,
            current_price=current_price,
            momentum_score=momentum_score,
            rsi=rsi,
            ema_20=ema_20,
            ema_50=ema_50,
            ema_200=ema_200,
            price_vs_ema_20=price_vs_ema_20,
            price_vs_ema_50=price_vs_ema_50,
            price_vs_ema_200=price_vs_ema_200,
            ema_alignment=ema_alignment,
            volume_trend=volume_trend,
            relative_volume=relative_volume,
            bias=bias,
            bias_confidence=bias_confidence
        )
    
    def _calculate_ema(self, bars: List[Dict[str, Any]], period: int) -> float:
        """Calculate Exponential Moving Average"""
        if len(bars) < period:
            return bars[-1]["close"]
        
        multiplier = 2 / (period + 1)
        ema = sum(b["close"] for b in bars[:period]) / period
        
        for i in range(period, len(bars)):
            ema = (bars[i]["close"] - ema) * multiplier + ema
        
        return ema
    
    def _find_swing_levels(self, bars: List[Dict[str, Any]]) -> Tuple[float, float]:
        """Find recent swing high and low"""
        lookback = min(self.swing_lookback, len(bars))
        recent_bars = bars[-lookback:]
        
        swing_high = max(b["high"] for b in recent_bars)
        swing_low = min(b["low"] for b in recent_bars)
        
        return swing_high, swing_low
    
    def _detect_structure(
        self,
        bars: List[Dict[str, Any]]
    ) -> Tuple[bool, bool, bool, bool]:
        """Detect market structure (HH, HL, LH, LL)"""
        if len(bars) < 40:
            return False, False, False, False
        
        # Find swing points in recent data
        swing_highs = []
        swing_lows = []
        
        for i in range(5, len(bars) - 5):
            # Check for swing high
            if all(bars[i]["high"] > bars[i-j]["high"] for j in range(1, 4)) and \
               all(bars[i]["high"] > bars[i+j]["high"] for j in range(1, 4)):
                swing_highs.append((i, bars[i]["high"]))
            
            # Check for swing low
            if all(bars[i]["low"] < bars[i-j]["low"] for j in range(1, 4)) and \
               all(bars[i]["low"] < bars[i+j]["low"] for j in range(1, 4)):
                swing_lows.append((i, bars[i]["low"]))
        
        higher_high = False
        higher_low = False
        lower_high = False
        lower_low = False
        
        if len(swing_highs) >= 2:
            higher_high = swing_highs[-1][1] > swing_highs[-2][1]
            lower_high = swing_highs[-1][1] < swing_highs[-2][1]
        
        if len(swing_lows) >= 2:
            higher_low = swing_lows[-1][1] > swing_lows[-2][1]
            lower_low = swing_lows[-1][1] < swing_lows[-2][1]
        
        return higher_high, higher_low, lower_high, lower_low
    
    def _calculate_rsi(self, bars: List[Dict[str, Any]]) -> float:
        """Calculate RSI"""
        if len(bars) < self.rsi_period + 1:
            return 50.0
        
        gains = []
        losses = []
        
        for i in range(1, len(bars)):
            change = bars[i]["close"] - bars[i-1]["close"]
            if change > 0:
                gains.append(change)
                losses.append(0)
            else:
                gains.append(0)
                losses.append(abs(change))
        
        if len(gains) < self.rsi_period:
            return 50.0
        
        avg_gain = sum(gains[-self.rsi_period:]) / self.rsi_period
        avg_loss = sum(losses[-self.rsi_period:]) / self.rsi_period
        
        if avg_loss == 0:
            return 100.0
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi
    
    def _calculate_momentum(self, bars: List[Dict[str, Any]], rsi: float) -> float:
        """Calculate momentum score (-1 to 1)"""
        if len(bars) < 20:
            return 0.0
        
        # Price momentum (rate of change)
        roc_10 = (bars[-1]["close"] - bars[-10]["close"]) / bars[-10]["close"]
        roc_20 = (bars[-1]["close"] - bars[-20]["close"]) / bars[-20]["close"]
        
        # RSI momentum
        rsi_momentum = (rsi - 50) / 50  # -1 to 1
        
        # Combine
        momentum = (roc_10 * 100 * 0.4) + (roc_20 * 100 * 0.3) + (rsi_momentum * 0.3)
        
        return max(-1.0, min(1.0, momentum))
    
    def _analyze_volume(self, bars: List[Dict[str, Any]]) -> Tuple[str, float]:
        """Analyze volume trend and relative volume"""
        if len(bars) < self.volume_ma_period + 5:
            return "flat", 1.0
        
        # Calculate volume MA
        vol_ma = sum(b.get("volume", 0) for b in bars[-self.volume_ma_period:]) / self.volume_ma_period
        
        # Current volume vs MA
        current_vol = bars[-1].get("volume", 0)
        relative_volume = current_vol / vol_ma if vol_ma > 0 else 1.0
        
        # Volume trend (compare recent vs older)
        recent_vol = sum(b.get("volume", 0) for b in bars[-5:]) / 5
        older_vol = sum(b.get("volume", 0) for b in bars[-10:-5]) / 5
        
        if recent_vol > older_vol * 1.2:
            volume_trend = "increasing"
        elif recent_vol < older_vol * 0.8:
            volume_trend = "decreasing"
        else:
            volume_trend = "flat"
        
        return volume_trend, relative_volume
    
    def _determine_trend(
        self,
        bars: List[Dict[str, Any]],
        ema_alignment: str,
        higher_high: bool,
        higher_low: bool,
        lower_high: bool,
        lower_low: bool,
        momentum_score: float
    ) -> Tuple[TrendDirection, float]:
        """Determine trend direction and strength"""
        score = 0.0
        
        # EMA alignment
        if ema_alignment == "bullish":
            score += 0.3
        elif ema_alignment == "bearish":
            score -= 0.3
        
        # Structure
        if higher_high and higher_low:
            score += 0.3
        elif lower_high and lower_low:
            score -= 0.3
        elif higher_high or higher_low:
            score += 0.15
        elif lower_high or lower_low:
            score -= 0.15
        
        # Momentum
        score += momentum_score * 0.4
        
        # Determine trend
        if score > 0.6:
            trend = TrendDirection.STRONG_BULLISH
        elif score > 0.3:
            trend = TrendDirection.BULLISH
        elif score > 0.1:
            trend = TrendDirection.WEAK_BULLISH
        elif score > -0.1:
            trend = TrendDirection.NEUTRAL
        elif score > -0.3:
            trend = TrendDirection.WEAK_BEARISH
        elif score > -0.6:
            trend = TrendDirection.BEARISH
        else:
            trend = TrendDirection.STRONG_BEARISH
        
        strength = abs(score)
        
        return trend, strength
    
    def _determine_tf_bias(
        self,
        trend: TrendDirection,
        trend_strength: float,
        price_vs_ema_200: str,
        momentum_score: float
    ) -> Tuple[TrendDirection, float]:
        """Determine timeframe bias"""
        # Start with trend
        bias = trend
        confidence = trend_strength
        
        # Adjust based on price vs 200 EMA
        if price_vs_ema_200 == "above":
            if trend in [TrendDirection.WEAK_BEARISH, TrendDirection.NEUTRAL]:
                bias = TrendDirection.WEAK_BULLISH
                confidence *= 0.8
        else:
            if trend in [TrendDirection.WEAK_BULLISH, TrendDirection.NEUTRAL]:
                bias = TrendDirection.WEAK_BEARISH
                confidence *= 0.8
        
        return bias, confidence
    
    def _calculate_category_score(
        self,
        analyses: Dict[TimeframeType, TimeframeAnalysis],
        category_timeframes: List[TimeframeType]
    ) -> float:
        """Calculate average score for a category of timeframes"""
        scores = []
        for tf in category_timeframes:
            if tf in analyses:
                scores.append(analyses[tf].get_score())
        
        return sum(scores) / len(scores) if scores else 0.0
    
    def _calculate_overall_score(
        self,
        analyses: Dict[TimeframeType, TimeframeAnalysis]
    ) -> float:
        """Calculate weighted overall score"""
        total_weight = 0.0
        weighted_score = 0.0
        
        for tf, analysis in analyses.items():
            weight = self.TIMEFRAME_WEIGHTS.get(tf, 0.1)
            weighted_score += analysis.get_score() * weight
            total_weight += weight
        
        return weighted_score / total_weight if total_weight > 0 else 0.0
    
    def _determine_alignment(
        self,
        analyses: Dict[TimeframeType, TimeframeAnalysis]
    ) -> Tuple[AlignmentType, float]:
        """Determine how aligned the timeframes are"""
        bullish_count = 0
        bearish_count = 0
        total = len(analyses)
        
        for analysis in analyses.values():
            score = analysis.get_score()
            if score > 0.2:
                bullish_count += 1
            elif score < -0.2:
                bearish_count += 1
        
        if total == 0:
            return AlignmentType.MIXED, 0.0
        
        bullish_ratio = bullish_count / total
        bearish_ratio = bearish_count / total
        
        if bullish_ratio >= 0.8:
            return AlignmentType.FULL_BULLISH, bullish_ratio
        elif bullish_ratio >= 0.6:
            return AlignmentType.PARTIAL_BULLISH, bullish_ratio
        elif bearish_ratio >= 0.8:
            return AlignmentType.FULL_BEARISH, bearish_ratio
        elif bearish_ratio >= 0.6:
            return AlignmentType.PARTIAL_BEARISH, bearish_ratio
        else:
            return AlignmentType.MIXED, max(bullish_ratio, bearish_ratio)
    
    def _determine_direction(
        self,
        overall_score: float,
        alignment: AlignmentType,
        alignment_score: float
    ) -> Tuple[TrendDirection, float]:
        """Determine overall direction and confidence"""
        # Base direction on overall score
        if overall_score > 0.5:
            direction = TrendDirection.STRONG_BULLISH
        elif overall_score > 0.25:
            direction = TrendDirection.BULLISH
        elif overall_score > 0.1:
            direction = TrendDirection.WEAK_BULLISH
        elif overall_score > -0.1:
            direction = TrendDirection.NEUTRAL
        elif overall_score > -0.25:
            direction = TrendDirection.WEAK_BEARISH
        elif overall_score > -0.5:
            direction = TrendDirection.BEARISH
        else:
            direction = TrendDirection.STRONG_BEARISH
        
        # Confidence based on alignment
        confidence = alignment_score * abs(overall_score)
        
        return direction, confidence
    
    def _get_category_levels(
        self,
        analyses: Dict[TimeframeType, TimeframeAnalysis],
        category_timeframes: List[TimeframeType]
    ) -> Tuple[float, float]:
        """Get resistance and support levels for a category"""
        resistances = []
        supports = []
        
        for tf in category_timeframes:
            if tf in analyses:
                resistances.append(analyses[tf].swing_high)
                supports.append(analyses[tf].swing_low)
        
        if not resistances:
            return 0.0, 0.0
        
        return max(resistances), min(supports)
    
    def _collect_levels(
        self,
        analyses: Dict[TimeframeType, TimeframeAnalysis],
        is_resistance: bool
    ) -> List[Tuple[float, TimeframeType]]:
        """Collect all levels from all timeframes"""
        levels = []
        for tf, analysis in analyses.items():
            if is_resistance:
                levels.append((analysis.swing_high, tf))
            else:
                levels.append((analysis.swing_low, tf))
        return levels
    
    def _find_confluence_zones(
        self,
        levels: List[Tuple[float, TimeframeType]]
    ) -> List[Tuple[float, float, int]]:
        """Find zones where multiple timeframe levels overlap"""
        if not levels:
            return []
        
        # Sort by price
        sorted_levels = sorted(levels, key=lambda x: x[0])
        
        confluence_zones = []
        used = set()
        
        for i, (price1, tf1) in enumerate(sorted_levels):
            if i in used:
                continue
            
            # Find overlapping levels
            zone_levels = [(price1, tf1)]
            zone_tfs = {tf1}
            
            for j, (price2, tf2) in enumerate(sorted_levels):
                if j <= i or j in used:
                    continue
                
                # Check if within tolerance
                if abs(price2 - price1) / price1 <= self.confluence_zone_tolerance:
                    zone_levels.append((price2, tf2))
                    zone_tfs.add(tf2)
                    used.add(j)
            
            if len(zone_tfs) >= 2:  # At least 2 timeframes
                prices = [p for p, _ in zone_levels]
                confluence_zones.append((max(prices), min(prices), len(zone_tfs)))
                used.add(i)
        
        return confluence_zones
    
    def _generate_recommendation(
        self,
        analyses: Dict[TimeframeType, TimeframeAnalysis],
        alignment: AlignmentType,
        alignment_score: float,
        direction: TrendDirection,
        direction_confidence: float,
        htf_score: float,
        mtf_score: float,
        ltf_score: float
    ) -> Tuple[Optional[str], Optional[TimeframeType], float, List[str]]:
        """Generate trade recommendation"""
        reasoning = []
        confidence = 0.0
        trade_direction = None
        entry_timeframe = None
        
        # Check alignment
        if alignment in [AlignmentType.FULL_BULLISH, AlignmentType.PARTIAL_BULLISH]:
            trade_direction = "LONG"
            reasoning.append(f"MTF alignment is {alignment.value} ({alignment_score:.1%})")
            confidence += 0.3 * alignment_score
        elif alignment in [AlignmentType.FULL_BEARISH, AlignmentType.PARTIAL_BEARISH]:
            trade_direction = "SHORT"
            reasoning.append(f"MTF alignment is {alignment.value} ({alignment_score:.1%})")
            confidence += 0.3 * alignment_score
        else:
            reasoning.append("MTF alignment is mixed - no clear direction")
            return None, None, 0.0, reasoning
        
        # Check HTF direction
        if trade_direction == "LONG" and htf_score > 0:
            reasoning.append(f"HTF (4H/D1) confirms bullish bias ({htf_score:+.2f})")
            confidence += 0.25
        elif trade_direction == "SHORT" and htf_score < 0:
            reasoning.append(f"HTF (4H/D1) confirms bearish bias ({htf_score:+.2f})")
            confidence += 0.25
        else:
            reasoning.append(f"HTF does not confirm direction ({htf_score:+.2f})")
            confidence -= 0.1
        
        # Check MTF direction
        if (trade_direction == "LONG" and mtf_score > 0) or \
           (trade_direction == "SHORT" and mtf_score < 0):
            reasoning.append(f"MTF (1H/15M) aligns with direction ({mtf_score:+.2f})")
            confidence += 0.2
        else:
            reasoning.append(f"MTF shows divergence ({mtf_score:+.2f})")
            confidence -= 0.05
        
        # Check LTF for entry timing
        if (trade_direction == "LONG" and ltf_score > 0) or \
           (trade_direction == "SHORT" and ltf_score < 0):
            reasoning.append(f"LTF (5M/1M) ready for entry ({ltf_score:+.2f})")
            confidence += 0.15
            # Determine entry timeframe
            if TimeframeType.M5 in analyses:
                entry_timeframe = TimeframeType.M5
            elif TimeframeType.M15 in analyses:
                entry_timeframe = TimeframeType.M15
        else:
            reasoning.append(f"LTF not yet aligned - wait for pullback ({ltf_score:+.2f})")
            confidence -= 0.05
        
        # Direction confidence bonus
        confidence += direction_confidence * 0.1
        
        # Clamp confidence
        confidence = max(0.0, min(1.0, confidence))
        
        # Minimum confidence threshold
        if confidence < 0.4:
            reasoning.append(f"Confidence too low ({confidence:.1%}) - no trade")
            return None, None, confidence, reasoning
        
        return trade_direction, entry_timeframe, confidence, reasoning
    
    def _empty_confluence(self) -> MTFConfluence:
        """Return empty confluence when insufficient data"""
        return MTFConfluence(
            timeframe_analyses={},
            alignment=AlignmentType.MIXED,
            alignment_score=0.0,
            htf_score=0.0,
            mtf_score=0.0,
            ltf_score=0.0,
            overall_score=0.0,
            direction=TrendDirection.NEUTRAL,
            direction_confidence=0.0,
            htf_resistance=0.0,
            htf_support=0.0,
            mtf_resistance=0.0,
            mtf_support=0.0,
            ltf_resistance=0.0,
            ltf_support=0.0,
            confluence_resistance_zones=[],
            confluence_support_zones=[],
            trade_direction=None,
            entry_timeframe=None,
            confidence=0.0,
            reasoning=["Insufficient data for MTF analysis"]
        )
    
    def resample_bars(
        self,
        bars_1m: List[Dict[str, Any]],
        target_timeframe: TimeframeType
    ) -> List[Dict[str, Any]]:
        """
        Resample 1-minute bars to higher timeframe
        
        Args:
            bars_1m: List of 1-minute OHLCV bars
            target_timeframe: Target timeframe to resample to
            
        Returns:
            Resampled bars
        """
        # Minutes per bar for each timeframe
        minutes_map = {
            TimeframeType.M1: 1,
            TimeframeType.M5: 5,
            TimeframeType.M15: 15,
            TimeframeType.M30: 30,
            TimeframeType.H1: 60,
            TimeframeType.H4: 240,
            TimeframeType.D1: 1440,
            TimeframeType.W1: 10080
        }
        
        minutes = minutes_map.get(target_timeframe, 1)
        
        if minutes == 1:
            return bars_1m
        
        resampled = []
        
        for i in range(0, len(bars_1m), minutes):
            chunk = bars_1m[i:i + minutes]
            if not chunk:
                continue
            
            resampled_bar = {
                "open": chunk[0]["open"],
                "high": max(b["high"] for b in chunk),
                "low": min(b["low"] for b in chunk),
                "close": chunk[-1]["close"],
                "volume": sum(b.get("volume", 0) for b in chunk),
                "timestamp": chunk[0].get("timestamp")
            }
            resampled.append(resampled_bar)
        
        return resampled


def test_mtf_intelligence():
    """Test MTF Intelligence with sample data"""
    import random
    
    # Generate sample 1-minute data
    bars_1m = []
    price = 1.1000
    
    for i in range(5000):  # ~3.5 days of 1-minute data
        # Add trend and noise
        trend = 0.00001 if i < 2500 else -0.000005
        noise = random.uniform(-0.0002, 0.0002)
        
        open_price = price
        close_price = price + trend + noise
        high_price = max(open_price, close_price) + random.uniform(0, 0.0001)
        low_price = min(open_price, close_price) - random.uniform(0, 0.0001)
        
        bars_1m.append({
            "open": open_price,
            "high": high_price,
            "low": low_price,
            "close": close_price,
            "volume": random.uniform(1000, 5000)
        })
        
        price = close_price
    
    # Create MTF Intelligence
    mtf = MTFIntelligence()
    
    # Resample to different timeframes
    timeframe_data = {
        TimeframeType.M1: bars_1m[-500:],
        TimeframeType.M5: mtf.resample_bars(bars_1m, TimeframeType.M5)[-300:],
        TimeframeType.M15: mtf.resample_bars(bars_1m, TimeframeType.M15)[-300:],
        TimeframeType.H1: mtf.resample_bars(bars_1m, TimeframeType.H1)[-300:],
        TimeframeType.H4: mtf.resample_bars(bars_1m, TimeframeType.H4)[-300:]
    }
    
    # Run analysis
    confluence = mtf.analyze(timeframe_data)
    
    print("=" * 60)
    print("MTF INTELLIGENCE TEST RESULTS")
    print("=" * 60)
    print(confluence.get_summary())
    
    print("\nTimeframe Details:")
    for tf, analysis in confluence.timeframe_analyses.items():
        print(f"\n{tf.value}:")
        print(f"  Trend: {analysis.trend.value} (strength: {analysis.trend_strength:.2f})")
        print(f"  EMA Alignment: {analysis.ema_alignment}")
        print(f"  Structure: HH={analysis.higher_high}, HL={analysis.higher_low}, LH={analysis.lower_high}, LL={analysis.lower_low}")
        print(f"  RSI: {analysis.rsi:.1f}")
        print(f"  Score: {analysis.get_score():+.2f}")
    
    print(f"\nConfluence Resistance Zones: {len(confluence.confluence_resistance_zones)}")
    for zone in confluence.confluence_resistance_zones:
        print(f"  {zone[1]:.5f} - {zone[0]:.5f} ({zone[2]} timeframes)")
    
    print(f"\nConfluence Support Zones: {len(confluence.confluence_support_zones)}")
    for zone in confluence.confluence_support_zones:
        print(f"  {zone[1]:.5f} - {zone[0]:.5f} ({zone[2]} timeframes)")
    
    return confluence


if __name__ == "__main__":
    test_mtf_intelligence()
