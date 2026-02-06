"""
UNIFIED INTELLIGENCE MODULE - THE BREAKTHROUGH

This module integrates ALL intelligence systems into a single, unified engine:
1. Delta Print Intelligence - Orderflow zones and patterns
2. VPIN - Probability of informed trading
3. Online HMM - Real-time regime detection
4. Consciousness Engine - Decision making with explanation

This is the IMPOSSIBLE made possible - a system that THINKS with
institutional-grade orderflow analysis, regime awareness, and
intelligent decision making.

Author: Devin (for Prince)
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
import numpy as np

from .delta_print import (
    DeltaPrintIntelligence,
    DeltaPrintAnalysis,
    DeltaPrintZone,
    DeltaDirection,
    ZoneStrength,
    create_delta_print_intelligence,
)

try:
    from ..orderflow.vpin import Trade, compute_vpin, build_volume_buckets, vpin_from_buckets
    from ..orderflow.imbalance_bars import build_tick_imbalance_bars, ImbalanceBar
    from ..intelligence.online_hmm import OnlineGaussianHMM
    ORDERFLOW_AVAILABLE = True
except ImportError:
    ORDERFLOW_AVAILABLE = False


class MarketRegimeUnified(Enum):
    """Unified market regime classification."""
    TRENDING_BULLISH = "trending_bullish"
    TRENDING_BEARISH = "trending_bearish"
    MEAN_REVERTING = "mean_reverting"
    HIGH_VOLATILITY = "high_volatility"
    LOW_VOLATILITY = "low_volatility"
    TRANSITIONING = "transitioning"


class InformedTradingLevel(Enum):
    """Level of informed trading activity based on VPIN."""
    VERY_LOW = "very_low"      # VPIN < 0.2
    LOW = "low"                # VPIN 0.2-0.35
    MODERATE = "moderate"      # VPIN 0.35-0.5
    HIGH = "high"              # VPIN 0.5-0.65
    VERY_HIGH = "very_high"    # VPIN > 0.65


class SignalStrength(Enum):
    """Unified signal strength."""
    NO_SIGNAL = "no_signal"
    WEAK = "weak"
    MODERATE = "moderate"
    STRONG = "strong"
    VERY_STRONG = "very_strong"
    EXTREME = "extreme"


@dataclass
class VPINAnalysis:
    """VPIN analysis output."""
    vpin_value: Optional[float]
    informed_trading_level: InformedTradingLevel
    bucket_count: int
    buy_volume_total: float
    sell_volume_total: float
    volume_imbalance: float
    is_reliable: bool  # True if we have enough data
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "vpin_value": self.vpin_value,
            "informed_trading_level": self.informed_trading_level.value,
            "bucket_count": self.bucket_count,
            "buy_volume_total": self.buy_volume_total,
            "sell_volume_total": self.sell_volume_total,
            "volume_imbalance": self.volume_imbalance,
            "is_reliable": self.is_reliable,
        }


@dataclass
class RegimeAnalysis:
    """Online HMM regime analysis output."""
    current_regime: MarketRegimeUnified
    regime_probabilities: Dict[str, float]
    regime_stability: float  # How stable is the current regime (0-1)
    regime_duration: int  # How many bars in current regime
    transition_probability: float  # Probability of regime change
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "current_regime": self.current_regime.value,
            "regime_probabilities": self.regime_probabilities,
            "regime_stability": self.regime_stability,
            "regime_duration": self.regime_duration,
            "transition_probability": self.transition_probability,
        }


@dataclass
class UnifiedSignal:
    """A unified trading signal combining all intelligence."""
    timestamp: datetime
    symbol: str
    current_price: float
    
    # Signal
    direction: str  # "buy", "sell", "wait"
    strength: SignalStrength
    confidence: float  # 0-1
    
    # Entry details (if direction != "wait")
    entry_price: Optional[float]
    stop_loss: Optional[float]
    take_profit: Optional[float]
    risk_reward_ratio: Optional[float]
    
    # Zone information
    zone: Optional[DeltaPrintZone]
    zone_confluence: float
    
    # VPIN information
    vpin_value: Optional[float]
    informed_trading_level: InformedTradingLevel
    vpin_boost: float  # How much VPIN boosted the signal
    
    # Regime information
    regime: MarketRegimeUnified
    regime_alignment: bool  # Does regime support the signal?
    
    # Reasoning
    reasoning: str
    factors: List[str]
    warnings: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp.isoformat(),
            "symbol": self.symbol,
            "current_price": self.current_price,
            "direction": self.direction,
            "strength": self.strength.value,
            "confidence": self.confidence,
            "entry_price": self.entry_price,
            "stop_loss": self.stop_loss,
            "take_profit": self.take_profit,
            "risk_reward_ratio": self.risk_reward_ratio,
            "zone": self.zone.to_dict() if self.zone else None,
            "zone_confluence": self.zone_confluence,
            "vpin_value": self.vpin_value,
            "informed_trading_level": self.informed_trading_level.value,
            "vpin_boost": self.vpin_boost,
            "regime": self.regime.value,
            "regime_alignment": self.regime_alignment,
            "reasoning": self.reasoning,
            "factors": self.factors,
            "warnings": self.warnings,
        }


@dataclass
class UnifiedAnalysis:
    """Complete unified intelligence analysis output."""
    timestamp: datetime
    symbol: str
    current_price: float
    
    # Component analyses
    delta_print: DeltaPrintAnalysis
    vpin_analysis: VPINAnalysis
    regime_analysis: RegimeAnalysis
    
    # Unified signal
    signal: UnifiedSignal
    
    # Overall assessment
    market_quality: float  # 0-1, how tradeable is this market
    institutional_activity: float  # 0-1, level of institutional activity
    overall_confidence: float  # 0-1
    
    # Meta
    analysis_time_ms: float
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp.isoformat(),
            "symbol": self.symbol,
            "current_price": self.current_price,
            "delta_print": self.delta_print.to_dict(),
            "vpin_analysis": self.vpin_analysis.to_dict(),
            "regime_analysis": self.regime_analysis.to_dict(),
            "signal": self.signal.to_dict(),
            "market_quality": self.market_quality,
            "institutional_activity": self.institutional_activity,
            "overall_confidence": self.overall_confidence,
            "analysis_time_ms": self.analysis_time_ms,
        }


class UnifiedIntelligence:
    """
    UNIFIED INTELLIGENCE ENGINE - THE BREAKTHROUGH
    
    This integrates:
    1. Delta Print Intelligence - Orderflow zones and patterns
    2. VPIN - Probability of informed trading
    3. Online HMM - Real-time regime detection
    
    Into a single, unified system that THINKS about markets.
    """
    
    def __init__(
        self,
        # Delta Print parameters
        big_trade_threshold: float = 0.01,
        absorption_threshold: float = 0.7,
        ledge_ratio_threshold: float = 3.0,
        value_area_pct: float = 0.70,
        # VPIN parameters
        vpin_bucket_volume: float = 1000.0,
        vpin_window_buckets: int = 50,
        # HMM parameters
        hmm_learning_rate: float = 0.01,
        # Signal parameters
        min_confluence_threshold: float = 0.40,
        min_confidence_threshold: float = 0.50,
    ):
        # Initialize Delta Print Intelligence
        self.delta_print = DeltaPrintIntelligence(
            big_trade_threshold=big_trade_threshold,
            absorption_threshold=absorption_threshold,
            ledge_ratio_threshold=ledge_ratio_threshold,
            value_area_pct=value_area_pct,
        )
        
        # VPIN parameters
        self.vpin_bucket_volume = vpin_bucket_volume
        self.vpin_window_buckets = vpin_window_buckets
        
        # Initialize Online HMM for regime detection
        # 4 states: trending_up, trending_down, mean_reverting, high_volatility
        if ORDERFLOW_AVAILABLE:
            self.hmm = OnlineGaussianHMM(
                transition=[
                    [0.85, 0.05, 0.05, 0.05],  # trending_up
                    [0.05, 0.85, 0.05, 0.05],  # trending_down
                    [0.10, 0.10, 0.70, 0.10],  # mean_reverting
                    [0.10, 0.10, 0.10, 0.70],  # high_volatility
                ],
                means=[0.02, -0.02, 0.0, 0.0],  # Expected returns
                variances=[0.01, 0.01, 0.005, 0.04],  # Return variances
                learning_rate=hmm_learning_rate,
            )
        else:
            self.hmm = None
        
        # Signal parameters
        self.min_confluence_threshold = min_confluence_threshold
        self.min_confidence_threshold = min_confidence_threshold
        
        # State tracking
        self.regime_history: List[MarketRegimeUnified] = []
        self.vpin_history: List[float] = []
        self.signal_history: List[UnifiedSignal] = []
    
    def analyze(
        self,
        candles: List[Dict[str, Any]],
        trades: Optional[List[Dict[str, Any]]] = None,
        symbol: str = "UNKNOWN",
    ) -> UnifiedAnalysis:
        """
        Perform complete unified intelligence analysis.
        
        This is the main entry point that orchestrates all analysis systems.
        """
        import time
        start_time = time.time()
        
        if not candles:
            raise ValueError("No candle data provided")
        
        current_price = candles[-1].get("close", 0)
        
        # Step 1: Run Delta Print Analysis
        delta_print_analysis = self.delta_print.analyze(
            candles=candles,
            trades=trades,
            symbol=symbol,
        )
        
        # Step 2: Run VPIN Analysis
        vpin_analysis = self._analyze_vpin(candles, trades)
        
        # Step 3: Run Regime Analysis
        regime_analysis = self._analyze_regime(candles)
        
        # Step 4: Generate Unified Signal
        signal = self._generate_unified_signal(
            delta_print=delta_print_analysis,
            vpin=vpin_analysis,
            regime=regime_analysis,
            current_price=current_price,
            symbol=symbol,
        )
        
        # Step 5: Calculate overall metrics
        market_quality = self._calculate_market_quality(
            delta_print=delta_print_analysis,
            vpin=vpin_analysis,
            regime=regime_analysis,
        )
        
        institutional_activity = self._calculate_institutional_activity(
            delta_print=delta_print_analysis,
            vpin=vpin_analysis,
        )
        
        overall_confidence = self._calculate_overall_confidence(
            signal=signal,
            market_quality=market_quality,
            institutional_activity=institutional_activity,
        )
        
        # Track history
        self.regime_history.append(regime_analysis.current_regime)
        if vpin_analysis.vpin_value is not None:
            self.vpin_history.append(vpin_analysis.vpin_value)
        self.signal_history.append(signal)
        
        # Keep history bounded
        max_history = 1000
        if len(self.regime_history) > max_history:
            self.regime_history = self.regime_history[-max_history:]
        if len(self.vpin_history) > max_history:
            self.vpin_history = self.vpin_history[-max_history:]
        if len(self.signal_history) > max_history:
            self.signal_history = self.signal_history[-max_history:]
        
        analysis_time_ms = (time.time() - start_time) * 1000
        
        return UnifiedAnalysis(
            timestamp=datetime.now(timezone.utc),
            symbol=symbol,
            current_price=current_price,
            delta_print=delta_print_analysis,
            vpin_analysis=vpin_analysis,
            regime_analysis=regime_analysis,
            signal=signal,
            market_quality=market_quality,
            institutional_activity=institutional_activity,
            overall_confidence=overall_confidence,
            analysis_time_ms=analysis_time_ms,
        )
    
    def _analyze_vpin(
        self,
        candles: List[Dict[str, Any]],
        trades: Optional[List[Dict[str, Any]]] = None,
    ) -> VPINAnalysis:
        """Analyze VPIN from trade data or estimate from candles."""
        if not ORDERFLOW_AVAILABLE:
            return VPINAnalysis(
                vpin_value=None,
                informed_trading_level=InformedTradingLevel.MODERATE,
                bucket_count=0,
                buy_volume_total=0,
                sell_volume_total=0,
                volume_imbalance=0,
                is_reliable=False,
            )
        
        # Convert candles to synthetic trades if no real trades provided
        if trades:
            trade_list = [
                Trade(
                    price=t.get("price", 0),
                    size=t.get("size", 0),
                    is_buy=t.get("is_buy", t.get("side", "").lower() == "buy"),
                )
                for t in trades
            ]
        else:
            # Estimate trades from candles
            trade_list = self._estimate_trades_from_candles(candles)
        
        if not trade_list:
            return VPINAnalysis(
                vpin_value=None,
                informed_trading_level=InformedTradingLevel.MODERATE,
                bucket_count=0,
                buy_volume_total=0,
                sell_volume_total=0,
                volume_imbalance=0,
                is_reliable=False,
            )
        
        # Build volume buckets
        buckets = build_volume_buckets(trade_list, bucket_volume=self.vpin_bucket_volume)
        
        # Calculate VPIN
        vpin_value = vpin_from_buckets(buckets, window_buckets=min(self.vpin_window_buckets, len(buckets)))
        
        # Calculate totals
        buy_volume = sum(t.size for t in trade_list if t.is_buy)
        sell_volume = sum(t.size for t in trade_list if not t.is_buy)
        total_volume = buy_volume + sell_volume
        volume_imbalance = (buy_volume - sell_volume) / total_volume if total_volume > 0 else 0
        
        # Determine informed trading level
        if vpin_value is None:
            informed_level = InformedTradingLevel.MODERATE
        elif vpin_value < 0.2:
            informed_level = InformedTradingLevel.VERY_LOW
        elif vpin_value < 0.35:
            informed_level = InformedTradingLevel.LOW
        elif vpin_value < 0.5:
            informed_level = InformedTradingLevel.MODERATE
        elif vpin_value < 0.65:
            informed_level = InformedTradingLevel.HIGH
        else:
            informed_level = InformedTradingLevel.VERY_HIGH
        
        return VPINAnalysis(
            vpin_value=vpin_value,
            informed_trading_level=informed_level,
            bucket_count=len(buckets),
            buy_volume_total=buy_volume,
            sell_volume_total=sell_volume,
            volume_imbalance=volume_imbalance,
            is_reliable=len(buckets) >= self.vpin_window_buckets,
        )
    
    def _estimate_trades_from_candles(
        self,
        candles: List[Dict[str, Any]],
    ) -> List["Trade"]:
        """Estimate trades from candle data (synthetic, Tier C)."""
        if not ORDERFLOW_AVAILABLE:
            return []
        
        trades = []
        for candle in candles:
            open_price = candle.get("open", 0)
            close_price = candle.get("close", 0)
            high = candle.get("high", 0)
            low = candle.get("low", 0)
            volume = candle.get("volume", 0)
            
            if volume <= 0:
                continue
            
            # Estimate buy/sell split based on candle direction
            is_bullish = close_price >= open_price
            
            # Create synthetic trades
            # More buys if bullish, more sells if bearish
            buy_pct = 0.6 if is_bullish else 0.4
            buy_volume = volume * buy_pct
            sell_volume = volume * (1 - buy_pct)
            
            # Add buy trades
            if buy_volume > 0:
                trades.append(Trade(
                    price=close_price if is_bullish else open_price,
                    size=buy_volume,
                    is_buy=True,
                ))
            
            # Add sell trades
            if sell_volume > 0:
                trades.append(Trade(
                    price=open_price if is_bullish else close_price,
                    size=sell_volume,
                    is_buy=False,
                ))
        
        return trades
    
    def _analyze_regime(
        self,
        candles: List[Dict[str, Any]],
    ) -> RegimeAnalysis:
        """Analyze market regime using Online HMM."""
        if not self.hmm or len(candles) < 2:
            return RegimeAnalysis(
                current_regime=MarketRegimeUnified.TRANSITIONING,
                regime_probabilities={
                    "trending_bullish": 0.25,
                    "trending_bearish": 0.25,
                    "mean_reverting": 0.25,
                    "high_volatility": 0.25,
                },
                regime_stability=0.5,
                regime_duration=0,
                transition_probability=0.5,
            )
        
        # Calculate returns and update HMM
        returns = []
        for i in range(1, len(candles)):
            prev_close = candles[i-1].get("close", 1)
            curr_close = candles[i].get("close", 1)
            if prev_close > 0:
                ret = (curr_close - prev_close) / prev_close
                returns.append(ret)
                self.hmm.update(ret)
        
        # Get state probabilities
        state_probs = self.hmm.state_probs
        most_likely = self.hmm.most_likely_state()
        
        # Map state to regime
        regime_map = {
            0: MarketRegimeUnified.TRENDING_BULLISH,
            1: MarketRegimeUnified.TRENDING_BEARISH,
            2: MarketRegimeUnified.MEAN_REVERTING,
            3: MarketRegimeUnified.HIGH_VOLATILITY,
        }
        current_regime = regime_map.get(most_likely, MarketRegimeUnified.TRANSITIONING)
        
        # Calculate regime stability
        regime_stability = max(state_probs) if state_probs else 0.5
        
        # Calculate regime duration
        regime_duration = 0
        for past_regime in reversed(self.regime_history):
            if past_regime == current_regime:
                regime_duration += 1
            else:
                break
        
        # Calculate transition probability
        transition_prob = 1.0 - regime_stability
        
        return RegimeAnalysis(
            current_regime=current_regime,
            regime_probabilities={
                "trending_bullish": state_probs[0] if len(state_probs) > 0 else 0.25,
                "trending_bearish": state_probs[1] if len(state_probs) > 1 else 0.25,
                "mean_reverting": state_probs[2] if len(state_probs) > 2 else 0.25,
                "high_volatility": state_probs[3] if len(state_probs) > 3 else 0.25,
            },
            regime_stability=regime_stability,
            regime_duration=regime_duration,
            transition_probability=transition_prob,
        )
    
    def _generate_unified_signal(
        self,
        delta_print: DeltaPrintAnalysis,
        vpin: VPINAnalysis,
        regime: RegimeAnalysis,
        current_price: float,
        symbol: str,
    ) -> UnifiedSignal:
        """Generate unified trading signal from all analyses."""
        factors = []
        warnings = []
        
        # Get best zone from Delta Print
        zone = delta_print.best_entry_zone
        zone_confluence = zone.confluence_score if zone else 0
        
        # Calculate VPIN boost
        vpin_boost = 0.0
        if vpin.vpin_value is not None and vpin.is_reliable:
            if vpin.informed_trading_level == InformedTradingLevel.HIGH:
                vpin_boost = 0.1
                factors.append("High VPIN indicates institutional activity (+10%)")
            elif vpin.informed_trading_level == InformedTradingLevel.VERY_HIGH:
                vpin_boost = 0.2
                factors.append("Very high VPIN indicates strong institutional activity (+20%)")
        
        # Check regime alignment
        regime_alignment = False
        if zone:
            if zone.zone_type == "support":
                regime_alignment = regime.current_regime in [
                    MarketRegimeUnified.TRENDING_BULLISH,
                    MarketRegimeUnified.MEAN_REVERTING,
                ]
                if regime_alignment:
                    factors.append(f"Regime ({regime.current_regime.value}) supports long entry")
                else:
                    warnings.append(f"Regime ({regime.current_regime.value}) conflicts with long entry")
            elif zone.zone_type == "resistance":
                regime_alignment = regime.current_regime in [
                    MarketRegimeUnified.TRENDING_BEARISH,
                    MarketRegimeUnified.MEAN_REVERTING,
                ]
                if regime_alignment:
                    factors.append(f"Regime ({regime.current_regime.value}) supports short entry")
                else:
                    warnings.append(f"Regime ({regime.current_regime.value}) conflicts with short entry")
        
        # Calculate adjusted confluence
        adjusted_confluence = zone_confluence + vpin_boost
        if regime_alignment:
            adjusted_confluence += 0.05
            factors.append("Regime alignment bonus (+5%)")
        
        # Determine signal direction
        direction = "wait"
        entry_price = None
        stop_loss = None
        take_profit = None
        risk_reward = None
        
        if zone and adjusted_confluence >= self.min_confluence_threshold:
            if zone.zone_type == "support":
                direction = "buy"
                entry_price = zone.price_low
                stop_loss = entry_price - (zone.price_high - zone.price_low) * 2
                take_profit = entry_price + (zone.price_high - zone.price_low) * 3
                factors.append(f"Support zone at {zone.price_low:.5f}-{zone.price_high:.5f}")
            elif zone.zone_type == "resistance":
                direction = "sell"
                entry_price = zone.price_high
                stop_loss = entry_price + (zone.price_high - zone.price_low) * 2
                take_profit = entry_price - (zone.price_high - zone.price_low) * 3
                factors.append(f"Resistance zone at {zone.price_low:.5f}-{zone.price_high:.5f}")
            
            if entry_price and stop_loss and take_profit:
                risk = abs(entry_price - stop_loss)
                reward = abs(take_profit - entry_price)
                risk_reward = reward / risk if risk > 0 else 0
        else:
            if not zone:
                warnings.append("No high-probability zone identified")
            elif adjusted_confluence < self.min_confluence_threshold:
                warnings.append(f"Confluence ({adjusted_confluence:.0%}) below threshold ({self.min_confluence_threshold:.0%})")
        
        # Determine signal strength
        if direction == "wait":
            strength = SignalStrength.NO_SIGNAL
        elif adjusted_confluence >= 0.7:
            strength = SignalStrength.EXTREME
        elif adjusted_confluence >= 0.6:
            strength = SignalStrength.VERY_STRONG
        elif adjusted_confluence >= 0.5:
            strength = SignalStrength.STRONG
        elif adjusted_confluence >= 0.4:
            strength = SignalStrength.MODERATE
        else:
            strength = SignalStrength.WEAK
        
        # Calculate confidence
        confidence = adjusted_confluence
        if regime.regime_stability > 0.7:
            confidence += 0.05
            factors.append("Stable regime (+5% confidence)")
        if len(delta_print.big_trades) > 3:
            confidence += 0.05
            factors.append(f"{len(delta_print.big_trades)} big trades detected (+5% confidence)")
        
        confidence = min(confidence, 1.0)
        
        # Generate reasoning
        reasoning = self._generate_reasoning(
            direction=direction,
            zone=zone,
            vpin=vpin,
            regime=regime,
            adjusted_confluence=adjusted_confluence,
        )
        
        return UnifiedSignal(
            timestamp=datetime.now(timezone.utc),
            symbol=symbol,
            current_price=current_price,
            direction=direction,
            strength=strength,
            confidence=confidence,
            entry_price=entry_price,
            stop_loss=stop_loss,
            take_profit=take_profit,
            risk_reward_ratio=risk_reward,
            zone=zone,
            zone_confluence=zone_confluence,
            vpin_value=vpin.vpin_value,
            informed_trading_level=vpin.informed_trading_level,
            vpin_boost=vpin_boost,
            regime=regime.current_regime,
            regime_alignment=regime_alignment,
            reasoning=reasoning,
            factors=factors,
            warnings=warnings,
        )
    
    def _generate_reasoning(
        self,
        direction: str,
        zone: Optional[DeltaPrintZone],
        vpin: VPINAnalysis,
        regime: RegimeAnalysis,
        adjusted_confluence: float,
    ) -> str:
        """Generate human-readable reasoning for the signal."""
        if direction == "wait":
            reasons = []
            if not zone:
                reasons.append("no high-probability zone identified")
            if adjusted_confluence < self.min_confluence_threshold:
                reasons.append(f"confluence ({adjusted_confluence:.0%}) below threshold")
            if regime.regime_stability < 0.5:
                reasons.append("unstable regime")
            return f"WAIT: {', '.join(reasons) if reasons else 'insufficient conditions'}"
        
        zone_type = zone.zone_type.upper() if zone else "UNKNOWN"
        vpin_str = f"VPIN={vpin.vpin_value:.2f}" if vpin.vpin_value else "VPIN=N/A"
        regime_str = regime.current_regime.value.upper()
        
        return (
            f"{direction.upper()}: {zone_type} zone with {adjusted_confluence:.0%} confluence. "
            f"{vpin_str} ({vpin.informed_trading_level.value}). "
            f"Regime: {regime_str} (stability: {regime.regime_stability:.0%})"
        )
    
    def _calculate_market_quality(
        self,
        delta_print: DeltaPrintAnalysis,
        vpin: VPINAnalysis,
        regime: RegimeAnalysis,
    ) -> float:
        """Calculate overall market quality (0-1)."""
        quality = 0.5  # Base
        
        # Better quality if we have clear zones
        if delta_print.delta_print_zones:
            quality += 0.1
        
        # Better quality if regime is stable
        if regime.regime_stability > 0.7:
            quality += 0.1
        
        # Better quality if VPIN is reliable
        if vpin.is_reliable:
            quality += 0.1
        
        # Lower quality if high volatility
        if regime.current_regime == MarketRegimeUnified.HIGH_VOLATILITY:
            quality -= 0.2
        
        # Lower quality if transitioning
        if regime.current_regime == MarketRegimeUnified.TRANSITIONING:
            quality -= 0.1
        
        return max(0, min(1, quality))
    
    def _calculate_institutional_activity(
        self,
        delta_print: DeltaPrintAnalysis,
        vpin: VPINAnalysis,
    ) -> float:
        """Calculate level of institutional activity (0-1)."""
        activity = 0.0
        
        # Big trades indicate institutional activity
        big_trade_count = len(delta_print.big_trades)
        activity += min(big_trade_count * 0.1, 0.4)
        
        # VPIN indicates informed trading
        if vpin.vpin_value is not None:
            activity += vpin.vpin_value * 0.4
        
        # Absorption patterns indicate institutional activity
        absorption_count = len(delta_print.absorption_patterns)
        activity += min(absorption_count * 0.1, 0.2)
        
        return min(1.0, activity)
    
    def _calculate_overall_confidence(
        self,
        signal: UnifiedSignal,
        market_quality: float,
        institutional_activity: float,
    ) -> float:
        """Calculate overall confidence in the analysis."""
        if signal.direction == "wait":
            return 0.0
        
        confidence = signal.confidence
        
        # Adjust for market quality
        confidence *= (0.5 + market_quality * 0.5)
        
        # Boost for institutional activity
        confidence += institutional_activity * 0.1
        
        return min(1.0, confidence)


def create_unified_intelligence(
    min_confluence_threshold: float = 0.40,
    min_confidence_threshold: float = 0.50,
) -> UnifiedIntelligence:
    """Factory function to create a UnifiedIntelligence instance."""
    return UnifiedIntelligence(
        min_confluence_threshold=min_confluence_threshold,
        min_confidence_threshold=min_confidence_threshold,
    )
