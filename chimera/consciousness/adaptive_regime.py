"""
Adaptive Regime Detection Intelligence Module

This module implements institutional-grade market regime detection:
1. Trending (Strong/Weak)
2. Ranging (Tight/Wide)
3. Volatile (Expansion/Contraction)
4. Transitioning (Regime change detection)

Each regime requires different strategy parameters - this is how
the BEST traders adapt to changing market conditions.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple, Any
from enum import Enum
import math


class MarketRegime(Enum):
    """Market regime types"""
    STRONG_TREND_UP = "strong_trend_up"
    WEAK_TREND_UP = "weak_trend_up"
    STRONG_TREND_DOWN = "strong_trend_down"
    WEAK_TREND_DOWN = "weak_trend_down"
    TIGHT_RANGE = "tight_range"
    WIDE_RANGE = "wide_range"
    HIGH_VOLATILITY = "high_volatility"
    LOW_VOLATILITY = "low_volatility"
    TRANSITIONING = "transitioning"
    UNKNOWN = "unknown"


class VolatilityState(Enum):
    """Volatility state"""
    EXPANDING = "expanding"
    CONTRACTING = "contracting"
    STABLE = "stable"


class TrendStrength(Enum):
    """Trend strength levels"""
    VERY_STRONG = "very_strong"
    STRONG = "strong"
    MODERATE = "moderate"
    WEAK = "weak"
    NONE = "none"


@dataclass
class RegimeParameters:
    """Optimal trading parameters for a specific regime"""
    # Position sizing
    position_size_multiplier: float  # 0.5 to 2.0
    max_positions: int
    
    # Entry/Exit
    entry_threshold: float  # Confidence threshold for entry
    exit_threshold: float  # Confidence threshold for exit
    
    # Stop loss
    stop_loss_atr_multiplier: float  # ATR multiplier for stop loss
    trailing_stop_enabled: bool
    trailing_stop_atr: float
    
    # Take profit
    take_profit_rr_ratio: float  # Risk/reward ratio for TP
    partial_take_profit: bool
    partial_tp_percent: float  # Percent to take at TP1
    
    # Filters
    min_volume_ratio: float  # Minimum relative volume
    max_spread_atr: float  # Maximum spread as ATR multiple
    
    # Strategy type
    strategy_type: str  # "trend_following", "mean_reversion", "breakout", "scalp"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "position_size_multiplier": self.position_size_multiplier,
            "max_positions": self.max_positions,
            "entry_threshold": self.entry_threshold,
            "exit_threshold": self.exit_threshold,
            "stop_loss_atr_multiplier": self.stop_loss_atr_multiplier,
            "trailing_stop_enabled": self.trailing_stop_enabled,
            "trailing_stop_atr": self.trailing_stop_atr,
            "take_profit_rr_ratio": self.take_profit_rr_ratio,
            "partial_take_profit": self.partial_take_profit,
            "partial_tp_percent": self.partial_tp_percent,
            "min_volume_ratio": self.min_volume_ratio,
            "max_spread_atr": self.max_spread_atr,
            "strategy_type": self.strategy_type
        }


@dataclass
class RegimeAnalysis:
    """Complete regime analysis result"""
    current_regime: MarketRegime
    regime_confidence: float  # 0-1
    regime_duration: int  # Bars in current regime
    
    # Trend analysis
    trend_direction: str  # "up", "down", "none"
    trend_strength: TrendStrength
    trend_score: float  # -1 to 1
    
    # Volatility analysis
    volatility_state: VolatilityState
    current_atr: float
    atr_percentile: float  # 0-100 (where current ATR falls in historical range)
    volatility_ratio: float  # Current vs average volatility
    
    # Range analysis
    range_high: float
    range_low: float
    range_width_atr: float  # Range width in ATR units
    price_position_in_range: float  # 0-1 (0 = at low, 1 = at high)
    
    # Momentum
    momentum_score: float  # -1 to 1
    momentum_divergence: bool  # Price vs momentum divergence
    
    # Regime change probability
    regime_change_probability: float  # 0-1
    likely_next_regime: Optional[MarketRegime]
    
    # Optimal parameters for current regime
    optimal_parameters: RegimeParameters
    
    # Historical regime performance
    regime_win_rate: float
    regime_avg_trade: float
    
    def get_summary(self) -> str:
        return f"""
REGIME ANALYSIS
===============
Current Regime: {self.current_regime.value}
Confidence: {self.regime_confidence:.1%}
Duration: {self.regime_duration} bars

Trend: {self.trend_direction} ({self.trend_strength.value})
Trend Score: {self.trend_score:+.2f}

Volatility: {self.volatility_state.value}
ATR Percentile: {self.atr_percentile:.0f}%
Volatility Ratio: {self.volatility_ratio:.2f}x

Range: {self.range_low:.5f} - {self.range_high:.5f}
Range Width: {self.range_width_atr:.1f} ATR
Price Position: {self.price_position_in_range:.1%}

Momentum: {self.momentum_score:+.2f}
Divergence: {'YES' if self.momentum_divergence else 'NO'}

Regime Change Probability: {self.regime_change_probability:.1%}
Likely Next Regime: {self.likely_next_regime.value if self.likely_next_regime else 'N/A'}

Strategy: {self.optimal_parameters.strategy_type}
Position Size: {self.optimal_parameters.position_size_multiplier:.1f}x
"""


class AdaptiveRegimeIntelligence:
    """
    Adaptive Regime Detection Intelligence Engine
    
    Detects market regimes and automatically adjusts trading parameters
    for optimal performance in each regime. This is how institutional
    traders adapt to changing market conditions.
    """
    
    # Default parameters for each regime
    REGIME_PARAMETERS = {
        MarketRegime.STRONG_TREND_UP: RegimeParameters(
            position_size_multiplier=1.5,
            max_positions=3,
            entry_threshold=0.5,
            exit_threshold=0.3,
            stop_loss_atr_multiplier=2.0,
            trailing_stop_enabled=True,
            trailing_stop_atr=1.5,
            take_profit_rr_ratio=3.0,
            partial_take_profit=True,
            partial_tp_percent=0.5,
            min_volume_ratio=0.8,
            max_spread_atr=0.3,
            strategy_type="trend_following"
        ),
        MarketRegime.WEAK_TREND_UP: RegimeParameters(
            position_size_multiplier=1.0,
            max_positions=2,
            entry_threshold=0.6,
            exit_threshold=0.4,
            stop_loss_atr_multiplier=1.5,
            trailing_stop_enabled=True,
            trailing_stop_atr=1.0,
            take_profit_rr_ratio=2.0,
            partial_take_profit=True,
            partial_tp_percent=0.5,
            min_volume_ratio=1.0,
            max_spread_atr=0.25,
            strategy_type="trend_following"
        ),
        MarketRegime.STRONG_TREND_DOWN: RegimeParameters(
            position_size_multiplier=1.5,
            max_positions=3,
            entry_threshold=0.5,
            exit_threshold=0.3,
            stop_loss_atr_multiplier=2.0,
            trailing_stop_enabled=True,
            trailing_stop_atr=1.5,
            take_profit_rr_ratio=3.0,
            partial_take_profit=True,
            partial_tp_percent=0.5,
            min_volume_ratio=0.8,
            max_spread_atr=0.3,
            strategy_type="trend_following"
        ),
        MarketRegime.WEAK_TREND_DOWN: RegimeParameters(
            position_size_multiplier=1.0,
            max_positions=2,
            entry_threshold=0.6,
            exit_threshold=0.4,
            stop_loss_atr_multiplier=1.5,
            trailing_stop_enabled=True,
            trailing_stop_atr=1.0,
            take_profit_rr_ratio=2.0,
            partial_take_profit=True,
            partial_tp_percent=0.5,
            min_volume_ratio=1.0,
            max_spread_atr=0.25,
            strategy_type="trend_following"
        ),
        MarketRegime.TIGHT_RANGE: RegimeParameters(
            position_size_multiplier=0.75,
            max_positions=2,
            entry_threshold=0.7,
            exit_threshold=0.5,
            stop_loss_atr_multiplier=1.0,
            trailing_stop_enabled=False,
            trailing_stop_atr=0.0,
            take_profit_rr_ratio=1.5,
            partial_take_profit=False,
            partial_tp_percent=0.0,
            min_volume_ratio=1.2,
            max_spread_atr=0.2,
            strategy_type="mean_reversion"
        ),
        MarketRegime.WIDE_RANGE: RegimeParameters(
            position_size_multiplier=1.0,
            max_positions=2,
            entry_threshold=0.6,
            exit_threshold=0.4,
            stop_loss_atr_multiplier=1.5,
            trailing_stop_enabled=False,
            trailing_stop_atr=0.0,
            take_profit_rr_ratio=2.0,
            partial_take_profit=True,
            partial_tp_percent=0.5,
            min_volume_ratio=1.0,
            max_spread_atr=0.25,
            strategy_type="mean_reversion"
        ),
        MarketRegime.HIGH_VOLATILITY: RegimeParameters(
            position_size_multiplier=0.5,
            max_positions=1,
            entry_threshold=0.8,
            exit_threshold=0.6,
            stop_loss_atr_multiplier=2.5,
            trailing_stop_enabled=True,
            trailing_stop_atr=2.0,
            take_profit_rr_ratio=2.5,
            partial_take_profit=True,
            partial_tp_percent=0.7,
            min_volume_ratio=1.5,
            max_spread_atr=0.5,
            strategy_type="breakout"
        ),
        MarketRegime.LOW_VOLATILITY: RegimeParameters(
            position_size_multiplier=1.25,
            max_positions=3,
            entry_threshold=0.5,
            exit_threshold=0.3,
            stop_loss_atr_multiplier=1.0,
            trailing_stop_enabled=False,
            trailing_stop_atr=0.0,
            take_profit_rr_ratio=1.5,
            partial_take_profit=False,
            partial_tp_percent=0.0,
            min_volume_ratio=0.8,
            max_spread_atr=0.15,
            strategy_type="scalp"
        ),
        MarketRegime.TRANSITIONING: RegimeParameters(
            position_size_multiplier=0.5,
            max_positions=1,
            entry_threshold=0.85,
            exit_threshold=0.7,
            stop_loss_atr_multiplier=2.0,
            trailing_stop_enabled=True,
            trailing_stop_atr=1.5,
            take_profit_rr_ratio=2.0,
            partial_take_profit=True,
            partial_tp_percent=0.7,
            min_volume_ratio=1.2,
            max_spread_atr=0.3,
            strategy_type="breakout"
        ),
        MarketRegime.UNKNOWN: RegimeParameters(
            position_size_multiplier=0.25,
            max_positions=1,
            entry_threshold=0.9,
            exit_threshold=0.8,
            stop_loss_atr_multiplier=2.0,
            trailing_stop_enabled=True,
            trailing_stop_atr=1.5,
            take_profit_rr_ratio=2.0,
            partial_take_profit=True,
            partial_tp_percent=0.8,
            min_volume_ratio=1.5,
            max_spread_atr=0.2,
            strategy_type="breakout"
        )
    }
    
    def __init__(
        self,
        atr_period: int = 14,
        trend_ema_fast: int = 20,
        trend_ema_slow: int = 50,
        trend_ema_very_slow: int = 200,
        adx_period: int = 14,
        rsi_period: int = 14,
        range_lookback: int = 50,
        volatility_lookback: int = 100,
        regime_min_duration: int = 10
    ):
        """
        Initialize Adaptive Regime Intelligence
        
        Args:
            atr_period: ATR calculation period
            trend_ema_fast: Fast EMA period for trend
            trend_ema_slow: Slow EMA period for trend
            trend_ema_very_slow: Very slow EMA period for trend
            adx_period: ADX calculation period
            rsi_period: RSI calculation period
            range_lookback: Lookback for range detection
            volatility_lookback: Lookback for volatility analysis
            regime_min_duration: Minimum bars before regime change
        """
        self.atr_period = atr_period
        self.trend_ema_fast = trend_ema_fast
        self.trend_ema_slow = trend_ema_slow
        self.trend_ema_very_slow = trend_ema_very_slow
        self.adx_period = adx_period
        self.rsi_period = rsi_period
        self.range_lookback = range_lookback
        self.volatility_lookback = volatility_lookback
        self.regime_min_duration = regime_min_duration
        
        # Regime history for tracking
        self.regime_history: List[Tuple[MarketRegime, int]] = []
        self.current_regime_start: int = 0
    
    def analyze(self, bars: List[Dict[str, Any]]) -> RegimeAnalysis:
        """
        Perform complete regime analysis
        
        Args:
            bars: List of OHLCV bars
            
        Returns:
            RegimeAnalysis with complete regime detection
        """
        if len(bars) < max(self.volatility_lookback, self.trend_ema_very_slow) + 10:
            return self._empty_analysis()
        
        # Calculate indicators
        atr = self._calculate_atr(bars)
        atr_history = self._calculate_atr_history(bars)
        ema_fast = self._calculate_ema(bars, self.trend_ema_fast)
        ema_slow = self._calculate_ema(bars, self.trend_ema_slow)
        ema_very_slow = self._calculate_ema(bars, self.trend_ema_very_slow)
        adx = self._calculate_adx(bars)
        rsi = self._calculate_rsi(bars)
        
        # Analyze trend
        trend_direction, trend_strength, trend_score = self._analyze_trend(
            bars, ema_fast, ema_slow, ema_very_slow, adx
        )
        
        # Analyze volatility
        volatility_state, atr_percentile, volatility_ratio = self._analyze_volatility(
            atr, atr_history
        )
        
        # Analyze range
        range_high, range_low, range_width_atr, price_position = self._analyze_range(
            bars, atr
        )
        
        # Calculate momentum
        momentum_score, momentum_divergence = self._analyze_momentum(bars, rsi)
        
        # Determine regime
        current_regime, regime_confidence = self._determine_regime(
            trend_direction, trend_strength, trend_score,
            volatility_state, volatility_ratio, atr_percentile,
            range_width_atr, adx
        )
        
        # Calculate regime duration
        regime_duration = self._calculate_regime_duration(current_regime, len(bars))
        
        # Predict regime change
        regime_change_prob, likely_next_regime = self._predict_regime_change(
            current_regime, regime_duration, volatility_state, momentum_divergence
        )
        
        # Get optimal parameters
        optimal_parameters = self.REGIME_PARAMETERS.get(
            current_regime, self.REGIME_PARAMETERS[MarketRegime.UNKNOWN]
        )
        
        # Calculate regime performance (placeholder - would use historical data)
        regime_win_rate = 0.55 if current_regime in [
            MarketRegime.STRONG_TREND_UP, MarketRegime.STRONG_TREND_DOWN
        ] else 0.50
        regime_avg_trade = 0.5 if current_regime in [
            MarketRegime.STRONG_TREND_UP, MarketRegime.STRONG_TREND_DOWN
        ] else 0.25
        
        return RegimeAnalysis(
            current_regime=current_regime,
            regime_confidence=regime_confidence,
            regime_duration=regime_duration,
            trend_direction=trend_direction,
            trend_strength=trend_strength,
            trend_score=trend_score,
            volatility_state=volatility_state,
            current_atr=atr,
            atr_percentile=atr_percentile,
            volatility_ratio=volatility_ratio,
            range_high=range_high,
            range_low=range_low,
            range_width_atr=range_width_atr,
            price_position_in_range=price_position,
            momentum_score=momentum_score,
            momentum_divergence=momentum_divergence,
            regime_change_probability=regime_change_prob,
            likely_next_regime=likely_next_regime,
            optimal_parameters=optimal_parameters,
            regime_win_rate=regime_win_rate,
            regime_avg_trade=regime_avg_trade
        )
    
    def _calculate_atr(self, bars: List[Dict[str, Any]]) -> float:
        """Calculate current ATR"""
        if len(bars) < self.atr_period + 1:
            return 0.0
        
        tr_values = []
        for i in range(1, len(bars)):
            high = bars[i]["high"]
            low = bars[i]["low"]
            prev_close = bars[i - 1]["close"]
            
            tr = max(
                high - low,
                abs(high - prev_close),
                abs(low - prev_close)
            )
            tr_values.append(tr)
        
        return sum(tr_values[-self.atr_period:]) / self.atr_period
    
    def _calculate_atr_history(self, bars: List[Dict[str, Any]]) -> List[float]:
        """Calculate ATR history for volatility analysis"""
        atr_history = []
        
        for i in range(self.atr_period + 1, len(bars)):
            tr_values = []
            for j in range(i - self.atr_period, i):
                high = bars[j]["high"]
                low = bars[j]["low"]
                prev_close = bars[j - 1]["close"]
                
                tr = max(
                    high - low,
                    abs(high - prev_close),
                    abs(low - prev_close)
                )
                tr_values.append(tr)
            
            atr_history.append(sum(tr_values) / self.atr_period)
        
        return atr_history
    
    def _calculate_ema(self, bars: List[Dict[str, Any]], period: int) -> float:
        """Calculate EMA"""
        if len(bars) < period:
            return bars[-1]["close"]
        
        multiplier = 2 / (period + 1)
        ema = sum(b["close"] for b in bars[:period]) / period
        
        for i in range(period, len(bars)):
            ema = (bars[i]["close"] - ema) * multiplier + ema
        
        return ema
    
    def _calculate_adx(self, bars: List[Dict[str, Any]]) -> float:
        """Calculate ADX (Average Directional Index)"""
        if len(bars) < self.adx_period * 2:
            return 25.0  # Default neutral value
        
        # Calculate +DM and -DM
        plus_dm = []
        minus_dm = []
        tr_values = []
        
        for i in range(1, len(bars)):
            high = bars[i]["high"]
            low = bars[i]["low"]
            prev_high = bars[i - 1]["high"]
            prev_low = bars[i - 1]["low"]
            prev_close = bars[i - 1]["close"]
            
            # True Range
            tr = max(high - low, abs(high - prev_close), abs(low - prev_close))
            tr_values.append(tr)
            
            # Directional Movement
            up_move = high - prev_high
            down_move = prev_low - low
            
            if up_move > down_move and up_move > 0:
                plus_dm.append(up_move)
            else:
                plus_dm.append(0)
            
            if down_move > up_move and down_move > 0:
                minus_dm.append(down_move)
            else:
                minus_dm.append(0)
        
        # Smooth values
        period = self.adx_period
        
        if len(tr_values) < period:
            return 25.0
        
        atr = sum(tr_values[-period:]) / period
        plus_di = (sum(plus_dm[-period:]) / period) / atr * 100 if atr > 0 else 0
        minus_di = (sum(minus_dm[-period:]) / period) / atr * 100 if atr > 0 else 0
        
        # Calculate DX
        di_sum = plus_di + minus_di
        if di_sum == 0:
            return 25.0
        
        dx = abs(plus_di - minus_di) / di_sum * 100
        
        return dx
    
    def _calculate_rsi(self, bars: List[Dict[str, Any]]) -> float:
        """Calculate RSI"""
        if len(bars) < self.rsi_period + 1:
            return 50.0
        
        gains = []
        losses = []
        
        for i in range(1, len(bars)):
            change = bars[i]["close"] - bars[i - 1]["close"]
            if change > 0:
                gains.append(change)
                losses.append(0)
            else:
                gains.append(0)
                losses.append(abs(change))
        
        avg_gain = sum(gains[-self.rsi_period:]) / self.rsi_period
        avg_loss = sum(losses[-self.rsi_period:]) / self.rsi_period
        
        if avg_loss == 0:
            return 100.0
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi
    
    def _analyze_trend(
        self,
        bars: List[Dict[str, Any]],
        ema_fast: float,
        ema_slow: float,
        ema_very_slow: float,
        adx: float
    ) -> Tuple[str, TrendStrength, float]:
        """Analyze trend direction and strength"""
        current_price = bars[-1]["close"]
        
        # Determine direction
        if ema_fast > ema_slow > ema_very_slow and current_price > ema_fast:
            direction = "up"
        elif ema_fast < ema_slow < ema_very_slow and current_price < ema_fast:
            direction = "down"
        else:
            direction = "none"
        
        # Determine strength based on ADX
        if adx >= 40:
            strength = TrendStrength.VERY_STRONG
        elif adx >= 30:
            strength = TrendStrength.STRONG
        elif adx >= 20:
            strength = TrendStrength.MODERATE
        elif adx >= 15:
            strength = TrendStrength.WEAK
        else:
            strength = TrendStrength.NONE
        
        # Calculate trend score (-1 to 1)
        if direction == "up":
            score = min(1.0, adx / 50)
        elif direction == "down":
            score = -min(1.0, adx / 50)
        else:
            score = 0.0
        
        return direction, strength, score
    
    def _analyze_volatility(
        self,
        current_atr: float,
        atr_history: List[float]
    ) -> Tuple[VolatilityState, float, float]:
        """Analyze volatility state"""
        if not atr_history:
            return VolatilityState.STABLE, 50.0, 1.0
        
        # Calculate percentile
        sorted_atr = sorted(atr_history)
        percentile_idx = 0
        for i, atr in enumerate(sorted_atr):
            if current_atr <= atr:
                percentile_idx = i
                break
        else:
            percentile_idx = len(sorted_atr)
        
        atr_percentile = (percentile_idx / len(sorted_atr)) * 100
        
        # Calculate ratio vs average
        avg_atr = sum(atr_history) / len(atr_history)
        volatility_ratio = current_atr / avg_atr if avg_atr > 0 else 1.0
        
        # Determine state
        recent_atr = atr_history[-10:] if len(atr_history) >= 10 else atr_history
        older_atr = atr_history[-20:-10] if len(atr_history) >= 20 else atr_history[:len(atr_history)//2]
        
        recent_avg = sum(recent_atr) / len(recent_atr) if recent_atr else current_atr
        older_avg = sum(older_atr) / len(older_atr) if older_atr else current_atr
        
        if recent_avg > older_avg * 1.2:
            state = VolatilityState.EXPANDING
        elif recent_avg < older_avg * 0.8:
            state = VolatilityState.CONTRACTING
        else:
            state = VolatilityState.STABLE
        
        return state, atr_percentile, volatility_ratio
    
    def _analyze_range(
        self,
        bars: List[Dict[str, Any]],
        atr: float
    ) -> Tuple[float, float, float, float]:
        """Analyze price range"""
        lookback = min(self.range_lookback, len(bars))
        recent_bars = bars[-lookback:]
        
        range_high = max(b["high"] for b in recent_bars)
        range_low = min(b["low"] for b in recent_bars)
        
        range_width = range_high - range_low
        range_width_atr = range_width / atr if atr > 0 else 0
        
        current_price = bars[-1]["close"]
        price_position = (current_price - range_low) / range_width if range_width > 0 else 0.5
        
        return range_high, range_low, range_width_atr, price_position
    
    def _analyze_momentum(
        self,
        bars: List[Dict[str, Any]],
        rsi: float
    ) -> Tuple[float, bool]:
        """Analyze momentum and detect divergence"""
        if len(bars) < 20:
            return 0.0, False
        
        # Calculate momentum score
        roc_10 = (bars[-1]["close"] - bars[-10]["close"]) / bars[-10]["close"]
        roc_20 = (bars[-1]["close"] - bars[-20]["close"]) / bars[-20]["close"]
        
        rsi_momentum = (rsi - 50) / 50
        
        momentum_score = (roc_10 * 100 * 0.4) + (roc_20 * 100 * 0.3) + (rsi_momentum * 0.3)
        momentum_score = max(-1.0, min(1.0, momentum_score))
        
        # Detect divergence
        # Price making higher highs but RSI making lower highs = bearish divergence
        # Price making lower lows but RSI making higher lows = bullish divergence
        divergence = False
        
        if len(bars) >= 30:
            price_trend = bars[-1]["close"] - bars[-20]["close"]
            
            # Simple divergence check
            if price_trend > 0 and rsi < 50:
                divergence = True  # Bearish divergence
            elif price_trend < 0 and rsi > 50:
                divergence = True  # Bullish divergence
        
        return momentum_score, divergence
    
    def _determine_regime(
        self,
        trend_direction: str,
        trend_strength: TrendStrength,
        trend_score: float,
        volatility_state: VolatilityState,
        volatility_ratio: float,
        atr_percentile: float,
        range_width_atr: float,
        adx: float
    ) -> Tuple[MarketRegime, float]:
        """Determine current market regime"""
        confidence = 0.0
        
        # High volatility regime
        if volatility_ratio > 1.5 or atr_percentile > 80:
            return MarketRegime.HIGH_VOLATILITY, min(1.0, volatility_ratio / 2)
        
        # Low volatility regime
        if volatility_ratio < 0.6 or atr_percentile < 20:
            return MarketRegime.LOW_VOLATILITY, min(1.0, 1 - volatility_ratio)
        
        # Strong trend regimes
        if trend_strength in [TrendStrength.VERY_STRONG, TrendStrength.STRONG]:
            if trend_direction == "up":
                confidence = min(1.0, adx / 40)
                return MarketRegime.STRONG_TREND_UP, confidence
            elif trend_direction == "down":
                confidence = min(1.0, adx / 40)
                return MarketRegime.STRONG_TREND_DOWN, confidence
        
        # Weak trend regimes
        if trend_strength == TrendStrength.MODERATE:
            if trend_direction == "up":
                confidence = min(1.0, adx / 30)
                return MarketRegime.WEAK_TREND_UP, confidence
            elif trend_direction == "down":
                confidence = min(1.0, adx / 30)
                return MarketRegime.WEAK_TREND_DOWN, confidence
        
        # Range regimes
        if trend_strength in [TrendStrength.WEAK, TrendStrength.NONE]:
            if range_width_atr < 3:
                confidence = min(1.0, (3 - range_width_atr) / 2)
                return MarketRegime.TIGHT_RANGE, confidence
            else:
                confidence = min(1.0, range_width_atr / 6)
                return MarketRegime.WIDE_RANGE, confidence
        
        # Transitioning
        if volatility_state == VolatilityState.EXPANDING:
            return MarketRegime.TRANSITIONING, 0.6
        
        return MarketRegime.UNKNOWN, 0.3
    
    def _calculate_regime_duration(
        self,
        current_regime: MarketRegime,
        current_bar: int
    ) -> int:
        """Calculate how long we've been in current regime"""
        if not self.regime_history:
            self.regime_history.append((current_regime, current_bar))
            self.current_regime_start = current_bar
            return 1
        
        last_regime, last_bar = self.regime_history[-1]
        
        if last_regime == current_regime:
            return current_bar - self.current_regime_start
        else:
            # Regime changed
            self.regime_history.append((current_regime, current_bar))
            self.current_regime_start = current_bar
            return 1
    
    def _predict_regime_change(
        self,
        current_regime: MarketRegime,
        regime_duration: int,
        volatility_state: VolatilityState,
        momentum_divergence: bool
    ) -> Tuple[float, Optional[MarketRegime]]:
        """Predict probability of regime change"""
        base_prob = 0.1
        
        # Longer duration increases change probability
        duration_factor = min(0.3, regime_duration / 100)
        
        # Volatility expansion often precedes regime change
        if volatility_state == VolatilityState.EXPANDING:
            base_prob += 0.2
        
        # Momentum divergence often precedes regime change
        if momentum_divergence:
            base_prob += 0.15
        
        change_prob = min(0.8, base_prob + duration_factor)
        
        # Predict likely next regime
        likely_next = None
        
        if current_regime in [MarketRegime.STRONG_TREND_UP, MarketRegime.WEAK_TREND_UP]:
            if momentum_divergence:
                likely_next = MarketRegime.TRANSITIONING
            else:
                likely_next = MarketRegime.WIDE_RANGE
        elif current_regime in [MarketRegime.STRONG_TREND_DOWN, MarketRegime.WEAK_TREND_DOWN]:
            if momentum_divergence:
                likely_next = MarketRegime.TRANSITIONING
            else:
                likely_next = MarketRegime.WIDE_RANGE
        elif current_regime in [MarketRegime.TIGHT_RANGE, MarketRegime.WIDE_RANGE]:
            if volatility_state == VolatilityState.EXPANDING:
                likely_next = MarketRegime.HIGH_VOLATILITY
            else:
                likely_next = MarketRegime.TRANSITIONING
        elif current_regime == MarketRegime.HIGH_VOLATILITY:
            likely_next = MarketRegime.TRANSITIONING
        elif current_regime == MarketRegime.LOW_VOLATILITY:
            likely_next = MarketRegime.TIGHT_RANGE
        
        return change_prob, likely_next
    
    def _empty_analysis(self) -> RegimeAnalysis:
        """Return empty analysis when insufficient data"""
        return RegimeAnalysis(
            current_regime=MarketRegime.UNKNOWN,
            regime_confidence=0.0,
            regime_duration=0,
            trend_direction="none",
            trend_strength=TrendStrength.NONE,
            trend_score=0.0,
            volatility_state=VolatilityState.STABLE,
            current_atr=0.0,
            atr_percentile=50.0,
            volatility_ratio=1.0,
            range_high=0.0,
            range_low=0.0,
            range_width_atr=0.0,
            price_position_in_range=0.5,
            momentum_score=0.0,
            momentum_divergence=False,
            regime_change_probability=0.0,
            likely_next_regime=None,
            optimal_parameters=self.REGIME_PARAMETERS[MarketRegime.UNKNOWN],
            regime_win_rate=0.5,
            regime_avg_trade=0.0
        )


def test_adaptive_regime():
    """Test Adaptive Regime Intelligence"""
    import random
    
    # Generate sample data with different regimes
    bars = []
    price = 1.1000
    
    # Trending phase
    for i in range(100):
        trend = 0.0002
        noise = random.uniform(-0.0003, 0.0003)
        
        open_price = price
        close_price = price + trend + noise
        high_price = max(open_price, close_price) + random.uniform(0, 0.0002)
        low_price = min(open_price, close_price) - random.uniform(0, 0.0002)
        
        bars.append({
            "open": open_price,
            "high": high_price,
            "low": low_price,
            "close": close_price,
            "volume": random.uniform(1000, 5000)
        })
        price = close_price
    
    # Ranging phase
    range_center = price
    for i in range(100):
        noise = random.uniform(-0.0005, 0.0005)
        
        open_price = price
        close_price = range_center + noise
        high_price = max(open_price, close_price) + random.uniform(0, 0.0002)
        low_price = min(open_price, close_price) - random.uniform(0, 0.0002)
        
        bars.append({
            "open": open_price,
            "high": high_price,
            "low": low_price,
            "close": close_price,
            "volume": random.uniform(1000, 5000)
        })
        price = close_price
    
    # High volatility phase
    for i in range(50):
        noise = random.uniform(-0.002, 0.002)
        
        open_price = price
        close_price = price + noise
        high_price = max(open_price, close_price) + random.uniform(0, 0.001)
        low_price = min(open_price, close_price) - random.uniform(0, 0.001)
        
        bars.append({
            "open": open_price,
            "high": high_price,
            "low": low_price,
            "close": close_price,
            "volume": random.uniform(2000, 8000)
        })
        price = close_price
    
    # Run analysis
    regime = AdaptiveRegimeIntelligence()
    analysis = regime.analyze(bars)
    
    print("=" * 60)
    print("ADAPTIVE REGIME INTELLIGENCE TEST")
    print("=" * 60)
    print(analysis.get_summary())
    
    print("\nOptimal Parameters:")
    for key, value in analysis.optimal_parameters.to_dict().items():
        print(f"  {key}: {value}")
    
    return analysis


if __name__ == "__main__":
    test_adaptive_regime()
