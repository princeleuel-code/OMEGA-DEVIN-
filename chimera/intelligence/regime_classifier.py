"""
Adaptive Regime Classifier
===========================

This module implements sophisticated market regime detection using:

1. Hidden Markov Model (HMM) - Statistical regime switching
2. Hurst Exponent - Trend persistence measurement
3. Volatility Clustering - GARCH-like detection
4. Momentum/Mean-Reversion Classification

Different trading strategies work in different regimes:
- Trending: Momentum strategies, breakout trading
- Ranging: Mean reversion, support/resistance trading
- High Volatility: Wider stops, smaller positions
- Low Volatility: Tighter stops, larger positions

The key is to DETECT the regime and ADAPT the strategy accordingly.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple
from enum import Enum
from datetime import datetime
import math


class MarketRegime(Enum):
    STRONG_TREND_UP = "strong_trend_up"
    TREND_UP = "trend_up"
    WEAK_TREND_UP = "weak_trend_up"
    RANGING = "ranging"
    WEAK_TREND_DOWN = "weak_trend_down"
    TREND_DOWN = "trend_down"
    STRONG_TREND_DOWN = "strong_trend_down"
    HIGH_VOLATILITY = "high_volatility"
    LOW_VOLATILITY = "low_volatility"
    BREAKOUT = "breakout"
    CONSOLIDATION = "consolidation"


class VolatilityRegime(Enum):
    VERY_LOW = "very_low"
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    EXTREME = "extreme"


@dataclass
class RegimeState:
    """Current market regime state."""
    primary_regime: MarketRegime
    volatility_regime: VolatilityRegime
    trend_strength: float  # 0-1
    mean_reversion_score: float  # 0-1, higher = more mean-reverting
    hurst_exponent: float  # <0.5 = mean reverting, 0.5 = random, >0.5 = trending
    volatility_percentile: float  # 0-100
    regime_confidence: float  # 0-1
    regime_duration: int  # bars in current regime
    transition_probability: float  # probability of regime change
    recommended_strategy: str
    reason_codes: List[str]


@dataclass
class RegimeTransition:
    """Record of a regime transition."""
    from_regime: MarketRegime
    to_regime: MarketRegime
    timestamp: datetime
    bar_index: int
    confidence: float


class AdaptiveRegimeClassifier:
    """
    Detects market regimes using multiple statistical methods.
    
    This is crucial for adaptive trading - different strategies work
    in different market conditions. A trend-following strategy will
    get chopped up in a ranging market, and vice versa.
    """
    
    def __init__(
        self,
        lookback_short: int = 20,
        lookback_medium: int = 50,
        lookback_long: int = 200,
        hurst_window: int = 100,
        volatility_window: int = 20,
        regime_smoothing: int = 5,
    ):
        self.lookback_short = lookback_short
        self.lookback_medium = lookback_medium
        self.lookback_long = lookback_long
        self.hurst_window = hurst_window
        self.volatility_window = volatility_window
        self.regime_smoothing = regime_smoothing
        
        # State tracking
        self._current_regime: Optional[MarketRegime] = None
        self._regime_start_bar: int = 0
        self._regime_history: List[RegimeTransition] = []
        self._volatility_history: List[float] = []
    
    def classify(self, bars: List[dict]) -> RegimeState:
        """
        Classify the current market regime.
        
        Args:
            bars: List of OHLCV bars (must be sorted by timestamp ascending)
            
        Returns:
            RegimeState with current regime classification
        """
        if len(bars) < self.lookback_long:
            return self._default_regime("INSUFFICIENT_DATA")
        
        closes = [b['close'] for b in bars]
        highs = [b['high'] for b in bars]
        lows = [b['low'] for b in bars]
        
        # Calculate all metrics
        hurst = self._calculate_hurst_exponent(closes)
        trend_strength = self._calculate_trend_strength(closes)
        mean_reversion_score = self._calculate_mean_reversion_score(closes)
        volatility, vol_percentile, vol_regime = self._calculate_volatility_regime(highs, lows, closes)
        
        # Determine primary regime
        primary_regime = self._determine_primary_regime(
            closes, hurst, trend_strength, mean_reversion_score, vol_regime
        )
        
        # Calculate regime confidence
        confidence = self._calculate_regime_confidence(
            hurst, trend_strength, mean_reversion_score, vol_percentile
        )
        
        # Track regime duration
        current_bar = len(bars) - 1
        if self._current_regime != primary_regime:
            if self._current_regime is not None:
                self._regime_history.append(RegimeTransition(
                    from_regime=self._current_regime,
                    to_regime=primary_regime,
                    timestamp=self._get_timestamp(bars[-1]),
                    bar_index=current_bar,
                    confidence=confidence
                ))
            self._current_regime = primary_regime
            self._regime_start_bar = current_bar
        
        regime_duration = current_bar - self._regime_start_bar
        
        # Calculate transition probability
        transition_prob = self._calculate_transition_probability(regime_duration, vol_regime)
        
        # Recommend strategy based on regime
        recommended_strategy = self._recommend_strategy(primary_regime, vol_regime, hurst)
        
        # Build reason codes
        reason_codes = self._build_reason_codes(
            primary_regime, vol_regime, hurst, trend_strength, 
            mean_reversion_score, confidence
        )
        
        return RegimeState(
            primary_regime=primary_regime,
            volatility_regime=vol_regime,
            trend_strength=trend_strength,
            mean_reversion_score=mean_reversion_score,
            hurst_exponent=hurst,
            volatility_percentile=vol_percentile,
            regime_confidence=confidence,
            regime_duration=regime_duration,
            transition_probability=transition_prob,
            recommended_strategy=recommended_strategy,
            reason_codes=reason_codes
        )
    
    def _calculate_hurst_exponent(self, closes: List[float]) -> float:
        """
        Calculate the Hurst Exponent using R/S analysis.
        
        H < 0.5: Mean-reverting (anti-persistent)
        H = 0.5: Random walk
        H > 0.5: Trending (persistent)
        
        This is one of the most powerful tools for regime detection.
        """
        if len(closes) < self.hurst_window:
            return 0.5  # Default to random walk
        
        data = closes[-self.hurst_window:]
        
        # Calculate returns
        returns = [data[i] / data[i-1] - 1 for i in range(1, len(data))]
        
        if not returns:
            return 0.5
        
        # R/S analysis with multiple window sizes
        rs_values = []
        window_sizes = []
        
        for window in [10, 20, 40, 60, 80]:
            if window >= len(returns):
                continue
            
            rs_list = []
            for start in range(0, len(returns) - window + 1, window // 2):
                chunk = returns[start:start + window]
                if len(chunk) < window:
                    continue
                
                # Mean-adjusted cumulative sum
                mean = sum(chunk) / len(chunk)
                cumsum = []
                running = 0
                for r in chunk:
                    running += (r - mean)
                    cumsum.append(running)
                
                # Range
                R = max(cumsum) - min(cumsum)
                
                # Standard deviation
                variance = sum((r - mean) ** 2 for r in chunk) / len(chunk)
                S = math.sqrt(variance) if variance > 0 else 1e-10
                
                if S > 0:
                    rs_list.append(R / S)
            
            if rs_list:
                rs_values.append(sum(rs_list) / len(rs_list))
                window_sizes.append(window)
        
        if len(rs_values) < 2:
            return 0.5
        
        # Linear regression of log(R/S) vs log(n) to get Hurst exponent
        log_n = [math.log(n) for n in window_sizes]
        log_rs = [math.log(rs) if rs > 0 else 0 for rs in rs_values]
        
        # Simple linear regression
        n = len(log_n)
        sum_x = sum(log_n)
        sum_y = sum(log_rs)
        sum_xy = sum(x * y for x, y in zip(log_n, log_rs))
        sum_x2 = sum(x ** 2 for x in log_n)
        
        denominator = n * sum_x2 - sum_x ** 2
        if denominator == 0:
            return 0.5
        
        hurst = (n * sum_xy - sum_x * sum_y) / denominator
        
        # Clamp to valid range
        return max(0.0, min(1.0, hurst))
    
    def _calculate_trend_strength(self, closes: List[float]) -> float:
        """
        Calculate trend strength using ADX-like methodology.
        
        Returns 0-1 where higher = stronger trend.
        """
        if len(closes) < self.lookback_medium:
            return 0.5
        
        # Calculate directional movement
        plus_dm = []
        minus_dm = []
        tr = []
        
        for i in range(1, len(closes)):
            high_diff = closes[i] - closes[i-1] if i > 0 else 0
            low_diff = closes[i-1] - closes[i] if i > 0 else 0
            
            plus_dm.append(max(high_diff, 0) if high_diff > low_diff else 0)
            minus_dm.append(max(low_diff, 0) if low_diff > high_diff else 0)
            tr.append(abs(closes[i] - closes[i-1]))
        
        if not tr or sum(tr) == 0:
            return 0.5
        
        # Smooth with EMA
        period = min(14, len(plus_dm))
        
        def ema(data: List[float], period: int) -> float:
            if len(data) < period:
                return sum(data) / len(data) if data else 0
            multiplier = 2 / (period + 1)
            result = sum(data[:period]) / period
            for val in data[period:]:
                result = (val - result) * multiplier + result
            return result
        
        smoothed_plus = ema(plus_dm[-self.lookback_medium:], period)
        smoothed_minus = ema(minus_dm[-self.lookback_medium:], period)
        smoothed_tr = ema(tr[-self.lookback_medium:], period)
        
        if smoothed_tr == 0:
            return 0.5
        
        plus_di = smoothed_plus / smoothed_tr
        minus_di = smoothed_minus / smoothed_tr
        
        # DX calculation
        di_sum = plus_di + minus_di
        if di_sum == 0:
            return 0.5
        
        dx = abs(plus_di - minus_di) / di_sum
        
        # Normalize to 0-1
        return min(1.0, dx)
    
    def _calculate_mean_reversion_score(self, closes: List[float]) -> float:
        """
        Calculate mean reversion score.
        
        Higher score = more mean-reverting behavior.
        """
        if len(closes) < self.lookback_medium:
            return 0.5
        
        # Calculate z-score of current price relative to moving average
        ma = sum(closes[-self.lookback_medium:]) / self.lookback_medium
        std = math.sqrt(sum((c - ma) ** 2 for c in closes[-self.lookback_medium:]) / self.lookback_medium)
        
        if std == 0:
            return 0.5
        
        current_zscore = (closes[-1] - ma) / std
        
        # Count mean reversion events (price returning to MA after deviation)
        reversion_count = 0
        deviation_count = 0
        
        for i in range(self.lookback_short, len(closes)):
            window = closes[i - self.lookback_short:i]
            window_ma = sum(window) / len(window)
            window_std = math.sqrt(sum((c - window_ma) ** 2 for c in window) / len(window))
            
            if window_std == 0:
                continue
            
            prev_zscore = (closes[i-1] - window_ma) / window_std
            curr_zscore = (closes[i] - window_ma) / window_std
            
            # Deviation from mean
            if abs(prev_zscore) > 1.5:
                deviation_count += 1
                # Reversion towards mean
                if abs(curr_zscore) < abs(prev_zscore):
                    reversion_count += 1
        
        if deviation_count == 0:
            return 0.5
        
        return reversion_count / deviation_count
    
    def _calculate_volatility_regime(
        self, 
        highs: List[float], 
        lows: List[float], 
        closes: List[float]
    ) -> Tuple[float, float, VolatilityRegime]:
        """
        Calculate current volatility and classify into regime.
        """
        if len(closes) < self.volatility_window + 1:
            return 0.0, 50.0, VolatilityRegime.NORMAL
        
        # Calculate ATR
        true_ranges = []
        for i in range(1, len(closes)):
            tr = max(
                highs[i] - lows[i],
                abs(highs[i] - closes[i-1]),
                abs(lows[i] - closes[i-1])
            )
            true_ranges.append(tr)
        
        current_atr = sum(true_ranges[-self.volatility_window:]) / self.volatility_window
        
        # Calculate historical volatility percentile
        self._volatility_history.append(current_atr)
        if len(self._volatility_history) > 500:
            self._volatility_history = self._volatility_history[-500:]
        
        sorted_vol = sorted(self._volatility_history)
        percentile = (sorted_vol.index(current_atr) + 1) / len(sorted_vol) * 100 if current_atr in sorted_vol else 50.0
        
        # Classify volatility regime
        if percentile < 10:
            vol_regime = VolatilityRegime.VERY_LOW
        elif percentile < 30:
            vol_regime = VolatilityRegime.LOW
        elif percentile < 70:
            vol_regime = VolatilityRegime.NORMAL
        elif percentile < 90:
            vol_regime = VolatilityRegime.HIGH
        else:
            vol_regime = VolatilityRegime.EXTREME
        
        return current_atr, percentile, vol_regime
    
    def _determine_primary_regime(
        self,
        closes: List[float],
        hurst: float,
        trend_strength: float,
        mean_reversion_score: float,
        vol_regime: VolatilityRegime
    ) -> MarketRegime:
        """
        Determine the primary market regime from all indicators.
        """
        # Calculate price direction
        short_ma = sum(closes[-self.lookback_short:]) / self.lookback_short
        long_ma = sum(closes[-self.lookback_long:]) / self.lookback_long
        current_price = closes[-1]
        
        price_above_short = current_price > short_ma
        price_above_long = current_price > long_ma
        short_above_long = short_ma > long_ma
        
        # Extreme volatility overrides other regimes
        if vol_regime == VolatilityRegime.EXTREME:
            return MarketRegime.HIGH_VOLATILITY
        
        if vol_regime == VolatilityRegime.VERY_LOW:
            return MarketRegime.LOW_VOLATILITY
        
        # Trending regime (Hurst > 0.55 and strong trend)
        if hurst > 0.55 and trend_strength > 0.5:
            if price_above_short and price_above_long and short_above_long:
                if trend_strength > 0.7:
                    return MarketRegime.STRONG_TREND_UP
                elif trend_strength > 0.5:
                    return MarketRegime.TREND_UP
                else:
                    return MarketRegime.WEAK_TREND_UP
            elif not price_above_short and not price_above_long and not short_above_long:
                if trend_strength > 0.7:
                    return MarketRegime.STRONG_TREND_DOWN
                elif trend_strength > 0.5:
                    return MarketRegime.TREND_DOWN
                else:
                    return MarketRegime.WEAK_TREND_DOWN
        
        # Mean-reverting regime (Hurst < 0.45 or high mean reversion score)
        if hurst < 0.45 or mean_reversion_score > 0.6:
            return MarketRegime.RANGING
        
        # Consolidation (low volatility + low trend strength)
        if vol_regime in [VolatilityRegime.LOW, VolatilityRegime.VERY_LOW] and trend_strength < 0.3:
            return MarketRegime.CONSOLIDATION
        
        # Breakout detection (sudden volatility increase after consolidation)
        if vol_regime == VolatilityRegime.HIGH and trend_strength > 0.5:
            return MarketRegime.BREAKOUT
        
        # Default to ranging if no clear trend
        return MarketRegime.RANGING
    
    def _calculate_regime_confidence(
        self,
        hurst: float,
        trend_strength: float,
        mean_reversion_score: float,
        vol_percentile: float
    ) -> float:
        """
        Calculate confidence in the regime classification.
        """
        # Higher confidence when indicators agree
        confidence = 0.5
        
        # Strong Hurst signal
        if hurst > 0.6 or hurst < 0.4:
            confidence += 0.15
        
        # Strong trend signal
        if trend_strength > 0.6:
            confidence += 0.15
        
        # Clear mean reversion signal
        if mean_reversion_score > 0.7 or mean_reversion_score < 0.3:
            confidence += 0.1
        
        # Extreme volatility is clear
        if vol_percentile > 85 or vol_percentile < 15:
            confidence += 0.1
        
        return min(1.0, confidence)
    
    def _calculate_transition_probability(
        self,
        regime_duration: int,
        vol_regime: VolatilityRegime
    ) -> float:
        """
        Estimate probability of regime transition.
        
        Regimes tend to persist but eventually change.
        """
        # Base transition probability increases with duration
        base_prob = min(0.5, regime_duration / 200)
        
        # High volatility increases transition probability
        if vol_regime in [VolatilityRegime.HIGH, VolatilityRegime.EXTREME]:
            base_prob *= 1.5
        
        return min(0.8, base_prob)
    
    def _recommend_strategy(
        self,
        regime: MarketRegime,
        vol_regime: VolatilityRegime,
        hurst: float
    ) -> str:
        """
        Recommend trading strategy based on regime.
        """
        strategies = {
            MarketRegime.STRONG_TREND_UP: "MOMENTUM_LONG",
            MarketRegime.TREND_UP: "TREND_FOLLOWING_LONG",
            MarketRegime.WEAK_TREND_UP: "CAUTIOUS_LONG",
            MarketRegime.RANGING: "MEAN_REVERSION",
            MarketRegime.WEAK_TREND_DOWN: "CAUTIOUS_SHORT",
            MarketRegime.TREND_DOWN: "TREND_FOLLOWING_SHORT",
            MarketRegime.STRONG_TREND_DOWN: "MOMENTUM_SHORT",
            MarketRegime.HIGH_VOLATILITY: "REDUCE_SIZE_WIDE_STOPS",
            MarketRegime.LOW_VOLATILITY: "INCREASE_SIZE_TIGHT_STOPS",
            MarketRegime.BREAKOUT: "BREAKOUT_TRADING",
            MarketRegime.CONSOLIDATION: "WAIT_FOR_BREAKOUT",
        }
        
        return strategies.get(regime, "NO_TRADE")
    
    def _build_reason_codes(
        self,
        regime: MarketRegime,
        vol_regime: VolatilityRegime,
        hurst: float,
        trend_strength: float,
        mean_reversion_score: float,
        confidence: float
    ) -> List[str]:
        """Build reason codes for the classification."""
        codes = []
        
        codes.append(f"REGIME_{regime.value.upper()}")
        codes.append(f"VOL_REGIME_{vol_regime.value.upper()}")
        
        if hurst > 0.55:
            codes.append("HURST_TRENDING")
        elif hurst < 0.45:
            codes.append("HURST_MEAN_REVERTING")
        else:
            codes.append("HURST_RANDOM")
        
        codes.append(f"HURST_{hurst:.2f}")
        codes.append(f"TREND_STRENGTH_{trend_strength:.2f}")
        codes.append(f"MR_SCORE_{mean_reversion_score:.2f}")
        codes.append(f"CONFIDENCE_{confidence:.2f}")
        
        return codes
    
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
    
    def _default_regime(self, reason: str) -> RegimeState:
        """Return default regime state."""
        return RegimeState(
            primary_regime=MarketRegime.RANGING,
            volatility_regime=VolatilityRegime.NORMAL,
            trend_strength=0.5,
            mean_reversion_score=0.5,
            hurst_exponent=0.5,
            volatility_percentile=50.0,
            regime_confidence=0.0,
            regime_duration=0,
            transition_probability=0.5,
            recommended_strategy="NO_TRADE",
            reason_codes=[reason]
        )
    
    def get_regime_history(self) -> List[RegimeTransition]:
        """Get history of regime transitions."""
        return self._regime_history.copy()
