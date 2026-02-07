"""
Multi-Timeframe Analysis Engine
===============================

Professional institutional traders use multiple timeframes to confirm signals.
This module implements a sophisticated multi-timeframe confluence system.

Higher Timeframe (HTF) - Sets the bias (trend direction)
Lower Timeframe (LTF) - Provides precise entry points

A signal is only valid when HTF and LTF agree.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple
from enum import Enum
from datetime import datetime, timedelta
import math


class Timeframe(Enum):
    M1 = 1
    M5 = 5
    M15 = 15
    M30 = 30
    H1 = 60
    H4 = 240
    D1 = 1440
    W1 = 10080


class TrendDirection(Enum):
    STRONG_BULLISH = 2
    BULLISH = 1
    NEUTRAL = 0
    BEARISH = -1
    STRONG_BEARISH = -2


@dataclass
class TimeframeSignal:
    timeframe: Timeframe
    trend: TrendDirection
    strength: float  # 0-1
    key_levels: List[float]
    support: float
    resistance: float
    momentum: float  # -1 to 1
    volatility: float
    timestamp: datetime
    reason_codes: List[str] = field(default_factory=list)


@dataclass
class MTFConfluence:
    overall_bias: TrendDirection
    confluence_score: float  # 0-1, higher = stronger agreement
    entry_valid: bool
    entry_direction: int  # 1 = long, -1 = short, 0 = no trade
    htf_signals: List[TimeframeSignal]
    ltf_signals: List[TimeframeSignal]
    key_levels: List[float]
    reason_codes: List[str]


class MultiTimeframeAnalyzer:
    """
    Analyzes price action across multiple timeframes to find high-probability setups.
    
    The key insight: A signal on a lower timeframe is only valid if it aligns
    with the higher timeframe trend. This dramatically improves win rate.
    """
    
    def __init__(
        self,
        htf_timeframes: List[Timeframe] = None,
        ltf_timeframes: List[Timeframe] = None,
        ema_periods: List[int] = None,
        atr_period: int = 14,
        structure_lookback: int = 50,
    ):
        self.htf_timeframes = htf_timeframes or [Timeframe.D1, Timeframe.H4]
        self.ltf_timeframes = ltf_timeframes or [Timeframe.H1, Timeframe.M15]
        self.ema_periods = ema_periods or [20, 50, 200]
        self.atr_period = atr_period
        self.structure_lookback = structure_lookback
        
        # Cache for resampled data
        self._cache: Dict[Timeframe, List[dict]] = {}
    
    def analyze(self, bars: List[dict], base_timeframe: Timeframe = Timeframe.H1) -> MTFConfluence:
        """
        Analyze price action across multiple timeframes.
        
        Args:
            bars: List of OHLCV bars (must be sorted by timestamp ascending)
            base_timeframe: The timeframe of the input bars
            
        Returns:
            MTFConfluence object with overall bias and entry signals
        """
        if len(bars) < self.structure_lookback * 2:
            return self._no_signal("INSUFFICIENT_DATA")
        
        # Resample to different timeframes
        resampled = self._resample_all(bars, base_timeframe)
        
        # Analyze each timeframe
        htf_signals = []
        for tf in self.htf_timeframes:
            if tf in resampled and len(resampled[tf]) >= self.structure_lookback:
                signal = self._analyze_timeframe(resampled[tf], tf)
                htf_signals.append(signal)
        
        ltf_signals = []
        for tf in self.ltf_timeframes:
            if tf in resampled and len(resampled[tf]) >= self.structure_lookback:
                signal = self._analyze_timeframe(resampled[tf], tf)
                ltf_signals.append(signal)
        
        # Also analyze the base timeframe
        base_signal = self._analyze_timeframe(bars, base_timeframe)
        ltf_signals.append(base_signal)
        
        # Calculate confluence
        return self._calculate_confluence(htf_signals, ltf_signals)
    
    def _resample_all(self, bars: List[dict], base_tf: Timeframe) -> Dict[Timeframe, List[dict]]:
        """Resample bars to all required timeframes."""
        result = {base_tf: bars}
        
        base_minutes = base_tf.value
        
        for tf in self.htf_timeframes + self.ltf_timeframes:
            if tf.value > base_minutes:
                # Need to aggregate up
                result[tf] = self._resample_up(bars, base_minutes, tf.value)
            elif tf.value < base_minutes:
                # Can't resample down without more data
                pass
            else:
                result[tf] = bars
        
        return result
    
    def _resample_up(self, bars: List[dict], from_minutes: int, to_minutes: int) -> List[dict]:
        """Aggregate bars from lower to higher timeframe."""
        if not bars:
            return []
        
        ratio = to_minutes // from_minutes
        if ratio <= 1:
            return bars
        
        resampled = []
        i = 0
        
        while i < len(bars):
            chunk = bars[i:i + ratio]
            if not chunk:
                break
            
            agg_bar = {
                'timestamp': chunk[0].get('timestamp', ''),
                'open': chunk[0]['open'],
                'high': max(b['high'] for b in chunk),
                'low': min(b['low'] for b in chunk),
                'close': chunk[-1]['close'],
                'volume': sum(b.get('volume', 0) for b in chunk),
            }
            resampled.append(agg_bar)
            i += ratio
        
        return resampled
    
    def _analyze_timeframe(self, bars: List[dict], tf: Timeframe) -> TimeframeSignal:
        """Analyze a single timeframe for trend, momentum, and key levels."""
        if len(bars) < self.structure_lookback:
            return TimeframeSignal(
                timeframe=tf,
                trend=TrendDirection.NEUTRAL,
                strength=0.0,
                key_levels=[],
                support=0.0,
                resistance=0.0,
                momentum=0.0,
                volatility=0.0,
                timestamp=datetime.now(),
                reason_codes=["INSUFFICIENT_BARS"]
            )
        
        closes = [b['close'] for b in bars]
        highs = [b['high'] for b in bars]
        lows = [b['low'] for b in bars]
        
        # Calculate EMAs
        emas = {}
        for period in self.ema_periods:
            if len(closes) >= period:
                emas[period] = self._ema(closes, period)
        
        # Determine trend from EMA alignment
        trend, trend_strength = self._determine_trend(closes, emas)
        
        # Calculate momentum (rate of change)
        momentum = self._calculate_momentum(closes)
        
        # Calculate volatility (ATR)
        volatility = self._calculate_atr(highs, lows, closes)
        
        # Find key levels (support/resistance)
        support, resistance, key_levels = self._find_key_levels(highs, lows, closes)
        
        # Build reason codes
        reason_codes = []
        if trend in [TrendDirection.STRONG_BULLISH, TrendDirection.BULLISH]:
            reason_codes.append(f"MTF_{tf.name}_BULLISH")
        elif trend in [TrendDirection.STRONG_BEARISH, TrendDirection.BEARISH]:
            reason_codes.append(f"MTF_{tf.name}_BEARISH")
        else:
            reason_codes.append(f"MTF_{tf.name}_NEUTRAL")
        
        if trend_strength > 0.7:
            reason_codes.append(f"MTF_{tf.name}_STRONG_TREND")
        
        return TimeframeSignal(
            timeframe=tf,
            trend=trend,
            strength=trend_strength,
            key_levels=key_levels,
            support=support,
            resistance=resistance,
            momentum=momentum,
            volatility=volatility,
            timestamp=datetime.now(),
            reason_codes=reason_codes
        )
    
    def _determine_trend(self, closes: List[float], emas: Dict[int, float]) -> Tuple[TrendDirection, float]:
        """
        Determine trend direction and strength from EMA alignment.
        
        Strong trend: Price > EMA20 > EMA50 > EMA200 (bullish) or reverse (bearish)
        """
        if not emas:
            return TrendDirection.NEUTRAL, 0.0
        
        current_price = closes[-1]
        sorted_periods = sorted(emas.keys())
        
        # Check EMA alignment
        bullish_score = 0
        bearish_score = 0
        total_checks = 0
        
        # Price vs EMAs
        for period in sorted_periods:
            total_checks += 1
            if current_price > emas[period]:
                bullish_score += 1
            else:
                bearish_score += 1
        
        # EMA vs EMA (shorter should be above longer for bullish)
        for i in range(len(sorted_periods) - 1):
            shorter = sorted_periods[i]
            longer = sorted_periods[i + 1]
            total_checks += 1
            if emas[shorter] > emas[longer]:
                bullish_score += 1
            else:
                bearish_score += 1
        
        # Calculate strength
        if total_checks == 0:
            return TrendDirection.NEUTRAL, 0.0
        
        bullish_pct = bullish_score / total_checks
        bearish_pct = bearish_score / total_checks
        
        if bullish_pct >= 0.9:
            return TrendDirection.STRONG_BULLISH, bullish_pct
        elif bullish_pct >= 0.6:
            return TrendDirection.BULLISH, bullish_pct
        elif bearish_pct >= 0.9:
            return TrendDirection.STRONG_BEARISH, bearish_pct
        elif bearish_pct >= 0.6:
            return TrendDirection.BEARISH, bearish_pct
        else:
            return TrendDirection.NEUTRAL, max(bullish_pct, bearish_pct)
    
    def _calculate_momentum(self, closes: List[float], period: int = 14) -> float:
        """Calculate momentum as rate of change normalized to -1 to 1."""
        if len(closes) < period + 1:
            return 0.0
        
        current = closes[-1]
        past = closes[-period - 1]
        
        if past == 0:
            return 0.0
        
        roc = (current - past) / past
        
        # Normalize to -1 to 1 (assuming max 10% move in period)
        normalized = max(-1.0, min(1.0, roc / 0.10))
        return normalized
    
    def _calculate_atr(self, highs: List[float], lows: List[float], closes: List[float]) -> float:
        """Calculate Average True Range."""
        if len(highs) < self.atr_period + 1:
            return 0.0
        
        true_ranges = []
        for i in range(1, len(highs)):
            tr = max(
                highs[i] - lows[i],
                abs(highs[i] - closes[i - 1]),
                abs(lows[i] - closes[i - 1])
            )
            true_ranges.append(tr)
        
        if len(true_ranges) < self.atr_period:
            return sum(true_ranges) / len(true_ranges) if true_ranges else 0.0
        
        return sum(true_ranges[-self.atr_period:]) / self.atr_period
    
    def _find_key_levels(
        self, 
        highs: List[float], 
        lows: List[float], 
        closes: List[float]
    ) -> Tuple[float, float, List[float]]:
        """Find support, resistance, and key price levels."""
        if len(highs) < 10:
            return 0.0, 0.0, []
        
        current_price = closes[-1]
        
        # Find swing highs and lows
        swing_highs = []
        swing_lows = []
        lookback = 5
        
        for i in range(lookback, len(highs) - lookback):
            # Swing high: higher than surrounding bars
            if highs[i] == max(highs[i - lookback:i + lookback + 1]):
                swing_highs.append(highs[i])
            
            # Swing low: lower than surrounding bars
            if lows[i] == min(lows[i - lookback:i + lookback + 1]):
                swing_lows.append(lows[i])
        
        # Find nearest support (highest swing low below current price)
        supports_below = [s for s in swing_lows if s < current_price]
        support = max(supports_below) if supports_below else min(lows[-20:])
        
        # Find nearest resistance (lowest swing high above current price)
        resistances_above = [r for r in swing_highs if r > current_price]
        resistance = min(resistances_above) if resistances_above else max(highs[-20:])
        
        # Combine and sort key levels
        key_levels = sorted(set(swing_highs + swing_lows))
        
        # Filter to levels within 5% of current price
        key_levels = [l for l in key_levels if abs(l - current_price) / current_price < 0.05]
        
        return support, resistance, key_levels
    
    def _ema(self, data: List[float], period: int) -> float:
        """Calculate Exponential Moving Average."""
        if len(data) < period:
            return sum(data) / len(data) if data else 0.0
        
        multiplier = 2 / (period + 1)
        ema = sum(data[:period]) / period  # SMA for first period
        
        for price in data[period:]:
            ema = (price - ema) * multiplier + ema
        
        return ema
    
    def _calculate_confluence(
        self, 
        htf_signals: List[TimeframeSignal], 
        ltf_signals: List[TimeframeSignal]
    ) -> MTFConfluence:
        """Calculate overall confluence from all timeframe signals."""
        if not htf_signals and not ltf_signals:
            return self._no_signal("NO_SIGNALS")
        
        reason_codes = []
        
        # Calculate HTF bias
        htf_bullish = sum(1 for s in htf_signals if s.trend.value > 0)
        htf_bearish = sum(1 for s in htf_signals if s.trend.value < 0)
        htf_total = len(htf_signals)
        
        if htf_total == 0:
            htf_bias = TrendDirection.NEUTRAL
        elif htf_bullish > htf_bearish:
            htf_bias = TrendDirection.BULLISH if htf_bullish < htf_total else TrendDirection.STRONG_BULLISH
        elif htf_bearish > htf_bullish:
            htf_bias = TrendDirection.BEARISH if htf_bearish < htf_total else TrendDirection.STRONG_BEARISH
        else:
            htf_bias = TrendDirection.NEUTRAL
        
        # Calculate LTF signal
        ltf_bullish = sum(1 for s in ltf_signals if s.trend.value > 0)
        ltf_bearish = sum(1 for s in ltf_signals if s.trend.value < 0)
        ltf_total = len(ltf_signals)
        
        if ltf_total == 0:
            ltf_direction = 0
        elif ltf_bullish > ltf_bearish:
            ltf_direction = 1
        elif ltf_bearish > ltf_bullish:
            ltf_direction = -1
        else:
            ltf_direction = 0
        
        # Check confluence: HTF and LTF must agree
        entry_valid = False
        entry_direction = 0
        confluence_score = 0.0
        
        if htf_bias.value > 0 and ltf_direction > 0:
            # Bullish confluence
            entry_valid = True
            entry_direction = 1
            confluence_score = (htf_bullish / max(htf_total, 1) + ltf_bullish / max(ltf_total, 1)) / 2
            reason_codes.append("MTF_BULLISH_CONFLUENCE")
        elif htf_bias.value < 0 and ltf_direction < 0:
            # Bearish confluence
            entry_valid = True
            entry_direction = -1
            confluence_score = (htf_bearish / max(htf_total, 1) + ltf_bearish / max(ltf_total, 1)) / 2
            reason_codes.append("MTF_BEARISH_CONFLUENCE")
        else:
            # No confluence
            reason_codes.append("MTF_NO_CONFLUENCE")
            if htf_bias.value > 0 and ltf_direction < 0:
                reason_codes.append("MTF_HTF_BULL_LTF_BEAR")
            elif htf_bias.value < 0 and ltf_direction > 0:
                reason_codes.append("MTF_HTF_BEAR_LTF_BULL")
        
        # Boost confluence score if trends are strong
        avg_htf_strength = sum(s.strength for s in htf_signals) / max(len(htf_signals), 1)
        avg_ltf_strength = sum(s.strength for s in ltf_signals) / max(len(ltf_signals), 1)
        
        if avg_htf_strength > 0.7:
            confluence_score *= 1.2
            reason_codes.append("MTF_STRONG_HTF_TREND")
        if avg_ltf_strength > 0.7:
            confluence_score *= 1.1
            reason_codes.append("MTF_STRONG_LTF_TREND")
        
        confluence_score = min(1.0, confluence_score)
        
        # Collect key levels from all timeframes
        all_key_levels = []
        for s in htf_signals + ltf_signals:
            all_key_levels.extend(s.key_levels)
        
        # Collect all reason codes
        for s in htf_signals + ltf_signals:
            reason_codes.extend(s.reason_codes)
        
        return MTFConfluence(
            overall_bias=htf_bias,
            confluence_score=confluence_score,
            entry_valid=entry_valid,
            entry_direction=entry_direction,
            htf_signals=htf_signals,
            ltf_signals=ltf_signals,
            key_levels=sorted(set(all_key_levels)),
            reason_codes=reason_codes
        )
    
    def _no_signal(self, reason: str) -> MTFConfluence:
        """Return a no-signal confluence object."""
        return MTFConfluence(
            overall_bias=TrendDirection.NEUTRAL,
            confluence_score=0.0,
            entry_valid=False,
            entry_direction=0,
            htf_signals=[],
            ltf_signals=[],
            key_levels=[],
            reason_codes=[reason]
        )
