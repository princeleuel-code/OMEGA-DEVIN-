"""
LAYER 1: PERCEPTION - Market State Encoder

The first layer of consciousness: PERCEIVING the market.

This module fuses ALL data sources into a unified market state representation:
- Price action (OHLCV at multiple timeframes)
- Order flow (DOM, trades, imbalances)
- Market structure (support/resistance, trends, regimes)
- Volatility regimes
- Liquidity conditions

The output is a dense vector that captures the FULL market state - 
not just what's happening, but the CONTEXT of what's happening.

This is inspired by:
- Temporal Fusion Transformers (Google)
- Attention mechanisms for multi-scale feature fusion
- State-space models for temporal dynamics
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
from enum import Enum
import numpy as np


class MarketRegime(Enum):
    """Hidden market states detected by the perception layer."""
    TRENDING_BULLISH = "trending_bullish"
    TRENDING_BEARISH = "trending_bearish"
    MEAN_REVERTING = "mean_reverting"
    HIGH_VOLATILITY = "high_volatility"
    LOW_VOLATILITY = "low_volatility"
    BREAKOUT = "breakout"
    CONSOLIDATION = "consolidation"
    UNKNOWN = "unknown"


class LiquidityCondition(Enum):
    """Current liquidity state."""
    ABUNDANT = "abundant"      # Deep order book, tight spreads
    NORMAL = "normal"          # Average conditions
    THIN = "thin"              # Shallow book, wide spreads
    CRISIS = "crisis"          # Extreme illiquidity
    UNKNOWN = "unknown"


class OrderFlowState(Enum):
    """Aggregate order flow condition."""
    STRONG_BUYING = "strong_buying"
    MODERATE_BUYING = "moderate_buying"
    BALANCED = "balanced"
    MODERATE_SELLING = "moderate_selling"
    STRONG_SELLING = "strong_selling"
    ABSORPTION = "absorption"      # Large orders being absorbed
    EXHAUSTION = "exhaustion"      # Momentum exhaustion
    UNKNOWN = "unknown"


@dataclass
class TimeframeState:
    """State at a single timeframe."""
    timeframe: str  # "1m", "5m", "15m", "1h", "4h", "1d"
    
    # Price dynamics
    trend_direction: float  # -1 to 1 (bearish to bullish)
    trend_strength: float   # 0 to 1
    momentum: float         # Rate of change
    
    # Volatility
    volatility: float       # Current volatility
    volatility_regime: float  # Relative to historical (z-score)
    
    # Structure
    distance_to_resistance: float  # In ATR units
    distance_to_support: float     # In ATR units
    in_value_area: bool
    
    # Order flow (if available)
    delta: float            # Buy - Sell volume
    cumulative_delta: float
    vwap_deviation: float   # Distance from VWAP in std devs


@dataclass
class MarketState:
    """
    The unified market state representation.
    
    This is the output of the perception layer - a complete snapshot
    of everything the system knows about the current market.
    """
    # Metadata
    timestamp: datetime
    symbol: str
    
    # Current price info
    price: float
    bid: Optional[float] = None
    ask: Optional[float] = None
    spread: Optional[float] = None
    
    # Multi-timeframe states
    timeframe_states: Dict[str, TimeframeState] = field(default_factory=dict)
    
    # Regime detection
    primary_regime: MarketRegime = MarketRegime.UNKNOWN
    regime_confidence: float = 0.0
    regime_probabilities: Dict[MarketRegime, float] = field(default_factory=dict)
    
    # Liquidity
    liquidity_condition: LiquidityCondition = LiquidityCondition.UNKNOWN
    liquidity_score: float = 0.5  # 0 = crisis, 1 = abundant
    
    # Order flow
    order_flow_state: OrderFlowState = OrderFlowState.UNKNOWN
    order_flow_score: float = 0.0  # -1 = strong selling, 1 = strong buying
    
    # Key levels
    nearest_support: Optional[float] = None
    nearest_resistance: Optional[float] = None
    poc: Optional[float] = None  # Point of Control
    vah: Optional[float] = None  # Value Area High
    val: Optional[float] = None  # Value Area Low
    
    # Uncertainty quantification
    state_uncertainty: float = 1.0  # 0 = certain, 1 = maximum uncertainty
    data_quality: float = 0.0      # 0 = no data, 1 = full data
    
    # Raw embedding (for neural network consumption)
    embedding: Optional[np.ndarray] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "timestamp": self.timestamp.isoformat(),
            "symbol": self.symbol,
            "price": self.price,
            "bid": self.bid,
            "ask": self.ask,
            "spread": self.spread,
            "primary_regime": self.primary_regime.value,
            "regime_confidence": self.regime_confidence,
            "liquidity_condition": self.liquidity_condition.value,
            "liquidity_score": self.liquidity_score,
            "order_flow_state": self.order_flow_state.value,
            "order_flow_score": self.order_flow_score,
            "nearest_support": self.nearest_support,
            "nearest_resistance": self.nearest_resistance,
            "poc": self.poc,
            "vah": self.vah,
            "val": self.val,
            "state_uncertainty": self.state_uncertainty,
            "data_quality": self.data_quality,
        }


class MarketStateEncoder:
    """
    The perception engine that encodes raw market data into MarketState.
    
    This is a Temporal Fusion architecture that:
    1. Processes each timeframe independently
    2. Fuses timeframes with attention weights
    3. Detects regimes using Hidden Markov Model
    4. Quantifies uncertainty at every step
    """
    
    # Timeframes to process (in order of importance for attention)
    TIMEFRAMES = ["1m", "5m", "15m", "1h", "4h", "1d"]
    
    # Embedding dimension
    EMBEDDING_DIM = 128
    
    def __init__(self):
        # HMM parameters for regime detection
        self.regime_transition_matrix = self._init_regime_transitions()
        self.regime_emission_params = self._init_regime_emissions()
        self.current_regime_belief = self._init_regime_belief()
        
        # Attention weights for timeframe fusion
        self.timeframe_attention = {tf: 1.0 / len(self.TIMEFRAMES) for tf in self.TIMEFRAMES}
        
        # Historical state for temporal dynamics
        self.state_history: List[MarketState] = []
        self.max_history = 1000
        
        # Calibration for uncertainty
        self.prediction_errors: List[float] = []
        self.calibration_window = 100
    
    def _init_regime_transitions(self) -> Dict[MarketRegime, Dict[MarketRegime, float]]:
        """Initialize regime transition probabilities (HMM)."""
        regimes = list(MarketRegime)
        n = len(regimes)
        
        # Start with uniform transitions, will be learned
        transitions = {}
        for r1 in regimes:
            transitions[r1] = {}
            for r2 in regimes:
                if r1 == r2:
                    transitions[r1][r2] = 0.7  # Regimes tend to persist
                else:
                    transitions[r1][r2] = 0.3 / (n - 1)
        
        return transitions
    
    def _init_regime_emissions(self) -> Dict[MarketRegime, Dict[str, Tuple[float, float]]]:
        """Initialize emission parameters (mean, std) for each regime."""
        return {
            MarketRegime.TRENDING_BULLISH: {
                "trend": (0.7, 0.2),
                "volatility": (0.5, 0.2),
                "momentum": (0.6, 0.2),
            },
            MarketRegime.TRENDING_BEARISH: {
                "trend": (-0.7, 0.2),
                "volatility": (0.5, 0.2),
                "momentum": (-0.6, 0.2),
            },
            MarketRegime.MEAN_REVERTING: {
                "trend": (0.0, 0.3),
                "volatility": (0.3, 0.15),
                "momentum": (0.0, 0.2),
            },
            MarketRegime.HIGH_VOLATILITY: {
                "trend": (0.0, 0.4),
                "volatility": (0.8, 0.15),
                "momentum": (0.0, 0.4),
            },
            MarketRegime.LOW_VOLATILITY: {
                "trend": (0.0, 0.2),
                "volatility": (0.2, 0.1),
                "momentum": (0.0, 0.1),
            },
            MarketRegime.BREAKOUT: {
                "trend": (0.5, 0.3),
                "volatility": (0.7, 0.2),
                "momentum": (0.7, 0.2),
            },
            MarketRegime.CONSOLIDATION: {
                "trend": (0.0, 0.15),
                "volatility": (0.25, 0.1),
                "momentum": (0.0, 0.1),
            },
            MarketRegime.UNKNOWN: {
                "trend": (0.0, 0.5),
                "volatility": (0.5, 0.3),
                "momentum": (0.0, 0.5),
            },
        }
    
    def _init_regime_belief(self) -> Dict[MarketRegime, float]:
        """Initialize uniform belief over regimes."""
        regimes = list(MarketRegime)
        return {r: 1.0 / len(regimes) for r in regimes}
    
    def encode(
        self,
        symbol: str,
        candles: Dict[str, List[Dict[str, Any]]],  # timeframe -> candles
        order_book: Optional[Dict[str, Any]] = None,
        trades: Optional[List[Dict[str, Any]]] = None,
        volume_profile: Optional[Dict[str, Any]] = None,
    ) -> MarketState:
        """
        Encode raw market data into a unified MarketState.
        
        Args:
            symbol: Trading symbol
            candles: Dict mapping timeframe to list of OHLCV candles
            order_book: Current order book snapshot (bids, asks)
            trades: Recent trades
            volume_profile: Volume profile data (POC, VAH, VAL)
        
        Returns:
            MarketState: The unified market state representation
        """
        timestamp = datetime.now(timezone.utc)
        
        # Get current price from most recent candle
        price = self._get_current_price(candles)
        
        # Process each timeframe
        timeframe_states = {}
        for tf in self.TIMEFRAMES:
            if tf in candles and candles[tf]:
                timeframe_states[tf] = self._process_timeframe(tf, candles[tf])
        
        # Fuse timeframes with attention
        fused_features = self._fuse_timeframes(timeframe_states)
        
        # Detect regime using HMM
        regime, regime_conf, regime_probs = self._detect_regime(fused_features)
        
        # Analyze liquidity
        liquidity_cond, liquidity_score = self._analyze_liquidity(order_book)
        
        # Analyze order flow
        flow_state, flow_score = self._analyze_order_flow(trades, order_book)
        
        # Extract key levels
        support, resistance = self._find_key_levels(candles, volume_profile)
        poc = volume_profile.get("poc") if volume_profile else None
        vah = volume_profile.get("vah") if volume_profile else None
        val = volume_profile.get("val") if volume_profile else None
        
        # Get bid/ask from order book
        bid, ask, spread = self._extract_bba(order_book)
        
        # Compute uncertainty
        uncertainty = self._compute_uncertainty(
            timeframe_states, order_book, regime_conf
        )
        
        # Compute data quality
        data_quality = self._compute_data_quality(candles, order_book, trades)
        
        # Generate embedding
        embedding = self._generate_embedding(
            fused_features, regime_probs, liquidity_score, flow_score
        )
        
        state = MarketState(
            timestamp=timestamp,
            symbol=symbol,
            price=price,
            bid=bid,
            ask=ask,
            spread=spread,
            timeframe_states=timeframe_states,
            primary_regime=regime,
            regime_confidence=regime_conf,
            regime_probabilities=regime_probs,
            liquidity_condition=liquidity_cond,
            liquidity_score=liquidity_score,
            order_flow_state=flow_state,
            order_flow_score=flow_score,
            nearest_support=support,
            nearest_resistance=resistance,
            poc=poc,
            vah=vah,
            val=val,
            state_uncertainty=uncertainty,
            data_quality=data_quality,
            embedding=embedding,
        )
        
        # Update history
        self._update_history(state)
        
        return state
    
    def _get_current_price(self, candles: Dict[str, List[Dict[str, Any]]]) -> float:
        """Get current price from most recent candle."""
        for tf in ["1m", "5m", "15m", "1h", "4h", "1d"]:
            if tf in candles and candles[tf]:
                return float(candles[tf][-1].get("close", 0))
        return 0.0
    
    def _process_timeframe(
        self, 
        timeframe: str, 
        candles: List[Dict[str, Any]]
    ) -> TimeframeState:
        """Process a single timeframe into TimeframeState."""
        if not candles:
            return self._empty_timeframe_state(timeframe)
        
        # Extract OHLCV arrays
        closes = np.array([float(c.get("close", 0)) for c in candles])
        highs = np.array([float(c.get("high", 0)) for c in candles])
        lows = np.array([float(c.get("low", 0)) for c in candles])
        volumes = np.array([float(c.get("volume", 0)) for c in candles])
        
        if len(closes) < 2:
            return self._empty_timeframe_state(timeframe)
        
        # Trend detection using linear regression
        trend_direction, trend_strength = self._compute_trend(closes)
        
        # Momentum (rate of change)
        momentum = self._compute_momentum(closes)
        
        # Volatility
        volatility = self._compute_volatility(closes)
        volatility_regime = self._compute_volatility_zscore(volatility, closes)
        
        # ATR for distance calculations
        atr = self._compute_atr(highs, lows, closes)
        
        # Support/Resistance distances
        current_price = closes[-1]
        resistance = self._find_resistance(highs, current_price)
        support = self._find_support(lows, current_price)
        
        dist_to_resistance = (resistance - current_price) / atr if atr > 0 else 0
        dist_to_support = (current_price - support) / atr if atr > 0 else 0
        
        # VWAP calculation
        vwap, vwap_std = self._compute_vwap(closes, volumes)
        vwap_deviation = (current_price - vwap) / vwap_std if vwap_std > 0 else 0
        
        # Delta (simplified - would need tick data for real delta)
        delta = self._estimate_delta(candles)
        cum_delta = self._estimate_cumulative_delta(candles)
        
        return TimeframeState(
            timeframe=timeframe,
            trend_direction=float(np.clip(trend_direction, -1, 1)),
            trend_strength=float(np.clip(trend_strength, 0, 1)),
            momentum=float(np.clip(momentum, -1, 1)),
            volatility=float(volatility),
            volatility_regime=float(np.clip(volatility_regime, -3, 3)),
            distance_to_resistance=float(dist_to_resistance),
            distance_to_support=float(dist_to_support),
            in_value_area=abs(vwap_deviation) < 1.0,
            delta=float(delta),
            cumulative_delta=float(cum_delta),
            vwap_deviation=float(np.clip(vwap_deviation, -3, 3)),
        )
    
    def _empty_timeframe_state(self, timeframe: str) -> TimeframeState:
        """Return empty state when no data available."""
        return TimeframeState(
            timeframe=timeframe,
            trend_direction=0.0,
            trend_strength=0.0,
            momentum=0.0,
            volatility=0.0,
            volatility_regime=0.0,
            distance_to_resistance=0.0,
            distance_to_support=0.0,
            in_value_area=True,
            delta=0.0,
            cumulative_delta=0.0,
            vwap_deviation=0.0,
        )
    
    def _compute_trend(self, closes: np.ndarray) -> Tuple[float, float]:
        """Compute trend direction and strength using linear regression."""
        n = len(closes)
        if n < 2:
            return 0.0, 0.0
        
        x = np.arange(n)
        
        # Linear regression
        x_mean = x.mean()
        y_mean = closes.mean()
        
        numerator = np.sum((x - x_mean) * (closes - y_mean))
        denominator = np.sum((x - x_mean) ** 2)
        
        if denominator == 0:
            return 0.0, 0.0
        
        slope = numerator / denominator
        
        # Normalize slope by price level and time
        normalized_slope = slope * n / y_mean if y_mean != 0 else 0
        
        # R-squared for strength
        y_pred = slope * (x - x_mean) + y_mean
        ss_res = np.sum((closes - y_pred) ** 2)
        ss_tot = np.sum((closes - y_mean) ** 2)
        
        r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0
        
        # Direction: sign of slope, scaled
        direction = np.tanh(normalized_slope * 10)  # Scale and bound
        
        # Strength: R-squared
        strength = max(0, r_squared)
        
        return direction, strength
    
    def _compute_momentum(self, closes: np.ndarray) -> float:
        """Compute momentum as normalized rate of change."""
        if len(closes) < 10:
            return 0.0
        
        # Multiple lookback periods
        roc_5 = (closes[-1] / closes[-5] - 1) if closes[-5] != 0 else 0
        roc_10 = (closes[-1] / closes[-10] - 1) if closes[-10] != 0 else 0
        
        # Weighted average
        momentum = 0.6 * roc_5 + 0.4 * roc_10
        
        # Normalize to [-1, 1]
        return float(np.tanh(momentum * 20))
    
    def _compute_volatility(self, closes: np.ndarray) -> float:
        """Compute volatility as standard deviation of returns."""
        if len(closes) < 2:
            return 0.0
        
        returns = np.diff(closes) / closes[:-1]
        returns = returns[np.isfinite(returns)]
        
        if len(returns) == 0:
            return 0.0
        
        return float(np.std(returns))
    
    def _compute_volatility_zscore(self, current_vol: float, closes: np.ndarray) -> float:
        """Compute volatility z-score relative to historical."""
        if len(closes) < 50:
            return 0.0
        
        # Rolling volatility
        window = 20
        vols = []
        for i in range(window, len(closes)):
            window_closes = closes[i-window:i]
            returns = np.diff(window_closes) / window_closes[:-1]
            returns = returns[np.isfinite(returns)]
            if len(returns) > 0:
                vols.append(np.std(returns))
        
        if not vols:
            return 0.0
        
        vol_mean = np.mean(vols)
        vol_std = np.std(vols)
        
        if vol_std == 0:
            return 0.0
        
        return (current_vol - vol_mean) / vol_std
    
    def _compute_atr(
        self, 
        highs: np.ndarray, 
        lows: np.ndarray, 
        closes: np.ndarray,
        period: int = 14
    ) -> float:
        """Compute Average True Range."""
        if len(closes) < 2:
            return 0.0
        
        tr = np.maximum(
            highs[1:] - lows[1:],
            np.maximum(
                np.abs(highs[1:] - closes[:-1]),
                np.abs(lows[1:] - closes[:-1])
            )
        )
        
        if len(tr) < period:
            return float(np.mean(tr)) if len(tr) > 0 else 0.0
        
        return float(np.mean(tr[-period:]))
    
    def _find_resistance(self, highs: np.ndarray, current_price: float) -> float:
        """Find nearest resistance level above current price."""
        above = highs[highs > current_price]
        if len(above) == 0:
            return current_price * 1.01  # Default 1% above
        return float(np.min(above))
    
    def _find_support(self, lows: np.ndarray, current_price: float) -> float:
        """Find nearest support level below current price."""
        below = lows[lows < current_price]
        if len(below) == 0:
            return current_price * 0.99  # Default 1% below
        return float(np.max(below))
    
    def _compute_vwap(
        self, 
        closes: np.ndarray, 
        volumes: np.ndarray
    ) -> Tuple[float, float]:
        """Compute VWAP and standard deviation."""
        if len(closes) == 0 or np.sum(volumes) == 0:
            return closes[-1] if len(closes) > 0 else 0.0, 1.0
        
        vwap = np.sum(closes * volumes) / np.sum(volumes)
        
        # VWAP standard deviation
        variance = np.sum(volumes * (closes - vwap) ** 2) / np.sum(volumes)
        std = np.sqrt(variance) if variance > 0 else 1.0
        
        return float(vwap), float(std)
    
    def _estimate_delta(self, candles: List[Dict[str, Any]]) -> float:
        """Estimate delta from candle data (approximation)."""
        if not candles:
            return 0.0
        
        # Use close vs open as proxy for buy/sell pressure
        last = candles[-1]
        open_price = float(last.get("open", 0))
        close_price = float(last.get("close", 0))
        volume = float(last.get("volume", 0))
        
        if open_price == 0:
            return 0.0
        
        # Positive delta if close > open (buying pressure)
        direction = 1 if close_price > open_price else -1
        magnitude = abs(close_price - open_price) / open_price
        
        return direction * magnitude * volume
    
    def _estimate_cumulative_delta(self, candles: List[Dict[str, Any]]) -> float:
        """Estimate cumulative delta over recent candles."""
        if not candles:
            return 0.0
        
        cum_delta = 0.0
        for c in candles[-20:]:  # Last 20 candles
            open_price = float(c.get("open", 0))
            close_price = float(c.get("close", 0))
            volume = float(c.get("volume", 0))
            
            if open_price > 0:
                direction = 1 if close_price > open_price else -1
                magnitude = abs(close_price - open_price) / open_price
                cum_delta += direction * magnitude * volume
        
        return cum_delta
    
    def _fuse_timeframes(
        self, 
        timeframe_states: Dict[str, TimeframeState]
    ) -> Dict[str, float]:
        """Fuse multiple timeframes using attention-weighted averaging."""
        if not timeframe_states:
            return {
                "trend": 0.0,
                "momentum": 0.0,
                "volatility": 0.0,
                "volatility_regime": 0.0,
            }
        
        # Compute attention weights based on data quality and timeframe importance
        weights = {}
        total_weight = 0.0
        
        for tf, state in timeframe_states.items():
            # Higher weight for lower timeframes (more recent info)
            tf_importance = self.timeframe_attention.get(tf, 0.1)
            
            # Weight by trend strength (more confident = more weight)
            confidence = state.trend_strength
            
            weight = tf_importance * (0.5 + 0.5 * confidence)
            weights[tf] = weight
            total_weight += weight
        
        # Normalize weights
        if total_weight > 0:
            weights = {tf: w / total_weight for tf, w in weights.items()}
        
        # Fuse features
        fused = {
            "trend": 0.0,
            "momentum": 0.0,
            "volatility": 0.0,
            "volatility_regime": 0.0,
        }
        
        for tf, state in timeframe_states.items():
            w = weights.get(tf, 0)
            fused["trend"] += w * state.trend_direction
            fused["momentum"] += w * state.momentum
            fused["volatility"] += w * state.volatility
            fused["volatility_regime"] += w * state.volatility_regime
        
        return fused
    
    def _detect_regime(
        self, 
        features: Dict[str, float]
    ) -> Tuple[MarketRegime, float, Dict[MarketRegime, float]]:
        """Detect market regime using HMM forward algorithm."""
        # Compute emission probabilities for each regime
        emission_probs = {}
        
        for regime, params in self.regime_emission_params.items():
            prob = 1.0
            for feature_name, (mean, std) in params.items():
                if feature_name in features:
                    value = features[feature_name]
                    # Gaussian emission probability
                    z = (value - mean) / std if std > 0 else 0
                    emission = math.exp(-0.5 * z * z) / (std * math.sqrt(2 * math.pi))
                    prob *= max(emission, 1e-10)
            emission_probs[regime] = prob
        
        # HMM forward step: P(regime | observations) proportional to
        # P(observation | regime) * sum over prev_regime of P(regime | prev_regime) * P(prev_regime)
        new_belief = {}
        for regime in MarketRegime:
            # Transition from all previous regimes
            trans_prob = sum(
                self.regime_transition_matrix[prev][regime] * self.current_regime_belief[prev]
                for prev in MarketRegime
            )
            new_belief[regime] = emission_probs.get(regime, 1e-10) * trans_prob
        
        # Normalize
        total = sum(new_belief.values())
        if total > 0:
            new_belief = {r: p / total for r, p in new_belief.items()}
        
        # Update belief
        self.current_regime_belief = new_belief
        
        # Find most likely regime
        best_regime = max(new_belief, key=new_belief.get)
        confidence = new_belief[best_regime]
        
        return best_regime, confidence, new_belief
    
    def _analyze_liquidity(
        self, 
        order_book: Optional[Dict[str, Any]]
    ) -> Tuple[LiquidityCondition, float]:
        """Analyze current liquidity conditions."""
        if not order_book:
            return LiquidityCondition.UNKNOWN, 0.5
        
        bids = order_book.get("bids", [])
        asks = order_book.get("asks", [])
        
        if not bids or not asks:
            return LiquidityCondition.UNKNOWN, 0.5
        
        # Total depth
        bid_depth = sum(float(b.get("size", 0)) for b in bids[:10])
        ask_depth = sum(float(a.get("size", 0)) for a in asks[:10])
        total_depth = bid_depth + ask_depth
        
        # Spread
        best_bid = float(bids[0].get("price", 0))
        best_ask = float(asks[0].get("price", 0))
        mid = (best_bid + best_ask) / 2 if best_bid > 0 else 1
        spread_pct = (best_ask - best_bid) / mid * 100 if mid > 0 else 0
        
        # Score based on depth and spread
        # Higher depth = better, lower spread = better
        depth_score = min(1.0, total_depth / 1000)  # Normalize
        spread_score = max(0, 1 - spread_pct / 0.5)  # 0.5% spread = 0 score
        
        liquidity_score = 0.6 * depth_score + 0.4 * spread_score
        
        # Classify
        if liquidity_score > 0.8:
            condition = LiquidityCondition.ABUNDANT
        elif liquidity_score > 0.5:
            condition = LiquidityCondition.NORMAL
        elif liquidity_score > 0.2:
            condition = LiquidityCondition.THIN
        else:
            condition = LiquidityCondition.CRISIS
        
        return condition, liquidity_score
    
    def _analyze_order_flow(
        self,
        trades: Optional[List[Dict[str, Any]]],
        order_book: Optional[Dict[str, Any]]
    ) -> Tuple[OrderFlowState, float]:
        """Analyze order flow conditions."""
        if not trades and not order_book:
            return OrderFlowState.UNKNOWN, 0.0
        
        # Analyze recent trades
        buy_volume = 0.0
        sell_volume = 0.0
        
        if trades:
            for t in trades[-100:]:  # Last 100 trades
                size = float(t.get("size", 0))
                side = t.get("side", "").lower()
                if side == "buy":
                    buy_volume += size
                elif side == "sell":
                    sell_volume += size
        
        # Analyze order book imbalance
        book_imbalance = 0.0
        if order_book:
            bids = order_book.get("bids", [])
            asks = order_book.get("asks", [])
            bid_size = sum(float(b.get("size", 0)) for b in bids[:5])
            ask_size = sum(float(a.get("size", 0)) for a in asks[:5])
            total = bid_size + ask_size
            if total > 0:
                book_imbalance = (bid_size - ask_size) / total
        
        # Combine trade flow and book imbalance
        total_volume = buy_volume + sell_volume
        if total_volume > 0:
            trade_imbalance = (buy_volume - sell_volume) / total_volume
        else:
            trade_imbalance = 0.0
        
        # Weighted combination
        flow_score = 0.7 * trade_imbalance + 0.3 * book_imbalance
        
        # Classify
        if flow_score > 0.5:
            state = OrderFlowState.STRONG_BUYING
        elif flow_score > 0.2:
            state = OrderFlowState.MODERATE_BUYING
        elif flow_score > -0.2:
            state = OrderFlowState.BALANCED
        elif flow_score > -0.5:
            state = OrderFlowState.MODERATE_SELLING
        else:
            state = OrderFlowState.STRONG_SELLING
        
        return state, flow_score
    
    def _find_key_levels(
        self,
        candles: Dict[str, List[Dict[str, Any]]],
        volume_profile: Optional[Dict[str, Any]]
    ) -> Tuple[Optional[float], Optional[float]]:
        """Find key support and resistance levels."""
        # Get current price
        price = self._get_current_price(candles)
        if price == 0:
            return None, None
        
        # Collect all highs and lows
        all_highs = []
        all_lows = []
        
        for tf, tf_candles in candles.items():
            for c in tf_candles:
                all_highs.append(float(c.get("high", 0)))
                all_lows.append(float(c.get("low", 0)))
        
        if not all_highs or not all_lows:
            return None, None
        
        # Find nearest support (highest low below price)
        lows_below = [l for l in all_lows if l < price]
        support = max(lows_below) if lows_below else None
        
        # Find nearest resistance (lowest high above price)
        highs_above = [h for h in all_highs if h > price]
        resistance = min(highs_above) if highs_above else None
        
        return support, resistance
    
    def _extract_bba(
        self, 
        order_book: Optional[Dict[str, Any]]
    ) -> Tuple[Optional[float], Optional[float], Optional[float]]:
        """Extract best bid, best ask, and spread."""
        if not order_book:
            return None, None, None
        
        bids = order_book.get("bids", [])
        asks = order_book.get("asks", [])
        
        if not bids or not asks:
            return None, None, None
        
        bid = float(bids[0].get("price", 0))
        ask = float(asks[0].get("price", 0))
        spread = ask - bid if bid > 0 and ask > 0 else None
        
        return bid, ask, spread
    
    def _compute_uncertainty(
        self,
        timeframe_states: Dict[str, TimeframeState],
        order_book: Optional[Dict[str, Any]],
        regime_confidence: float
    ) -> float:
        """Compute overall state uncertainty."""
        uncertainties = []
        
        # Uncertainty from regime detection
        uncertainties.append(1 - regime_confidence)
        
        # Uncertainty from timeframe disagreement
        if timeframe_states:
            trends = [s.trend_direction for s in timeframe_states.values()]
            if trends:
                trend_std = np.std(trends)
                uncertainties.append(min(1.0, trend_std))
        
        # Uncertainty from data availability
        if not order_book:
            uncertainties.append(0.3)  # Missing order book adds uncertainty
        
        if len(timeframe_states) < 3:
            uncertainties.append(0.2)  # Missing timeframes adds uncertainty
        
        # Combine uncertainties
        return float(np.mean(uncertainties)) if uncertainties else 1.0
    
    def _compute_data_quality(
        self,
        candles: Dict[str, List[Dict[str, Any]]],
        order_book: Optional[Dict[str, Any]],
        trades: Optional[List[Dict[str, Any]]]
    ) -> float:
        """Compute data quality score."""
        score = 0.0
        
        # Candle data quality
        for tf in self.TIMEFRAMES:
            if tf in candles and len(candles[tf]) >= 50:
                score += 0.1
        
        # Order book quality
        if order_book:
            bids = order_book.get("bids", [])
            asks = order_book.get("asks", [])
            if len(bids) >= 10 and len(asks) >= 10:
                score += 0.2
        
        # Trade data quality
        if trades and len(trades) >= 50:
            score += 0.2
        
        return min(1.0, score)
    
    def _generate_embedding(
        self,
        fused_features: Dict[str, float],
        regime_probs: Dict[MarketRegime, float],
        liquidity_score: float,
        flow_score: float
    ) -> np.ndarray:
        """Generate dense embedding vector for neural network consumption."""
        embedding = np.zeros(self.EMBEDDING_DIM)
        
        # Fused features (first 10 dims)
        embedding[0] = fused_features.get("trend", 0)
        embedding[1] = fused_features.get("momentum", 0)
        embedding[2] = fused_features.get("volatility", 0)
        embedding[3] = fused_features.get("volatility_regime", 0)
        embedding[4] = liquidity_score
        embedding[5] = flow_score
        
        # Regime probabilities (dims 10-20)
        for i, regime in enumerate(MarketRegime):
            if i < 10:
                embedding[10 + i] = regime_probs.get(regime, 0)
        
        # Rest is reserved for learned features
        
        return embedding
    
    def _update_history(self, state: MarketState) -> None:
        """Update state history."""
        self.state_history.append(state)
        if len(self.state_history) > self.max_history:
            self.state_history = self.state_history[-self.max_history:]
    
    def get_state_history(self, n: int = 100) -> List[MarketState]:
        """Get recent state history."""
        return self.state_history[-n:]
