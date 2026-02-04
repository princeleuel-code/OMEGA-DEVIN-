"""
Confluence Engine
=================

This is the BRAIN of the breakthrough trading system.

It combines signals from ALL intelligence modules:
- Multi-Timeframe Analysis
- Smart Money Concepts
- Regime Classification
- Position Sizing

A trade is only taken when MULTIPLE signals align (confluence).
This dramatically improves win rate and reduces false signals.

The key insight: One indicator can be wrong. Multiple indicators
agreeing is much more reliable.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple
from enum import Enum
from datetime import datetime
import math

from .multi_timeframe import MultiTimeframeAnalyzer, MTFConfluence, TrendDirection, Timeframe
from .smart_money import SmartMoneyDetector, SMCAnalysis, BlockType, GapType
from .regime_classifier import AdaptiveRegimeClassifier, RegimeState, MarketRegime, VolatilityRegime
from .position_sizer import IntelligentPositionSizer, PositionSize, TradeStats


class SignalStrength(Enum):
    NONE = 0
    WEAK = 1
    MODERATE = 2
    STRONG = 3
    VERY_STRONG = 4


class TradeDirection(Enum):
    LONG = 1
    SHORT = -1
    NO_TRADE = 0


@dataclass
class ConfluenceSignal:
    """
    The final trading signal with full confluence analysis.
    
    This is what the execution layer uses to make trading decisions.
    """
    direction: TradeDirection
    strength: SignalStrength
    confidence: float  # 0-1
    
    # Entry/Exit levels
    entry_price: float
    stop_loss: float
    take_profit_1: float
    take_profit_2: float
    take_profit_3: float
    
    # Position sizing
    position_size: PositionSize
    
    # Confluence details
    mtf_confluence: MTFConfluence
    smc_analysis: SMCAnalysis
    regime_state: RegimeState
    
    # Scoring breakdown
    mtf_score: float
    smc_score: float
    regime_score: float
    total_score: float
    
    # Risk/Reward
    risk_reward_ratio: float
    expected_value: float
    
    # Audit trail
    reason_codes: List[str]
    veto_reasons: List[str]
    timestamp: datetime


@dataclass
class ConfluenceConfig:
    """Configuration for the confluence engine."""
    min_confluence_score: float = 0.6
    min_risk_reward: float = 1.5
    max_spread_atr_ratio: float = 0.3
    
    # Weights for different signal sources
    mtf_weight: float = 0.35
    smc_weight: float = 0.35
    regime_weight: float = 0.30
    
    # Entry refinement
    use_order_block_entry: bool = True
    use_fvg_entry: bool = True
    
    # Stop loss placement
    sl_atr_multiplier: float = 1.5
    sl_beyond_structure: float = 0.0005  # 5 pips beyond structure
    
    # Take profit levels
    tp1_rr: float = 1.0
    tp2_rr: float = 2.0
    tp3_rr: float = 3.0


class ConfluenceEngine:
    """
    The master intelligence engine that combines all signal sources.
    
    This is where the magic happens. We take signals from:
    1. Multi-Timeframe Analysis (trend direction and strength)
    2. Smart Money Concepts (institutional footprints)
    3. Regime Classification (market conditions)
    
    And combine them into a single, high-confidence trading signal.
    """
    
    def __init__(self, config: ConfluenceConfig = None):
        self.config = config or ConfluenceConfig()
        
        # Initialize all analyzers
        self.mtf_analyzer = MultiTimeframeAnalyzer()
        self.smc_detector = SmartMoneyDetector()
        self.regime_classifier = AdaptiveRegimeClassifier()
        self.position_sizer = IntelligentPositionSizer()
    
    def analyze(
        self,
        bars: List[dict],
        capital: float = 10000.0,
        trade_stats: TradeStats = None,
        base_timeframe: Timeframe = Timeframe.H1,
    ) -> ConfluenceSignal:
        """
        Perform complete confluence analysis.
        
        Args:
            bars: List of OHLCV bars
            capital: Current account capital
            trade_stats: Historical trade statistics for position sizing
            base_timeframe: Timeframe of the input bars
            
        Returns:
            ConfluenceSignal with complete analysis and trading decision
        """
        if len(bars) < 200:
            return self._no_trade_signal("INSUFFICIENT_DATA", bars)
        
        current_price = bars[-1]['close']
        current_atr = self._calculate_atr(bars)
        
        reason_codes = []
        veto_reasons = []
        
        # 1. Multi-Timeframe Analysis
        mtf_confluence = self.mtf_analyzer.analyze(bars, base_timeframe)
        mtf_score = self._score_mtf(mtf_confluence)
        reason_codes.extend(mtf_confluence.reason_codes)
        
        # 2. Smart Money Concepts Analysis
        smc_analysis = self.smc_detector.analyze(bars)
        smc_score = self._score_smc(smc_analysis, current_price)
        reason_codes.extend(smc_analysis.reason_codes)
        
        # 3. Regime Classification
        regime_state = self.regime_classifier.classify(bars)
        regime_score = self._score_regime(regime_state)
        reason_codes.extend(regime_state.reason_codes)
        
        # Calculate total confluence score
        total_score = (
            mtf_score * self.config.mtf_weight +
            smc_score * self.config.smc_weight +
            regime_score * self.config.regime_weight
        )
        
        # Determine trade direction
        direction = self._determine_direction(mtf_confluence, smc_analysis, regime_state)
        
        # Apply veto checks
        vetoed, veto_reasons = self._apply_vetoes(
            direction, total_score, regime_state, current_atr, bars
        )
        
        if vetoed:
            return self._no_trade_signal(
                veto_reasons[0] if veto_reasons else "VETOED",
                bars,
                mtf_confluence=mtf_confluence,
                smc_analysis=smc_analysis,
                regime_state=regime_state,
                veto_reasons=veto_reasons
            )
        
        # Calculate entry, stop loss, and take profit levels
        entry_price, stop_loss, tp1, tp2, tp3 = self._calculate_levels(
            direction, current_price, current_atr, smc_analysis, mtf_confluence
        )
        
        # Calculate risk/reward
        risk = abs(entry_price - stop_loss)
        reward = abs(tp2 - entry_price)  # Use TP2 for R:R calculation
        risk_reward = reward / risk if risk > 0 else 0
        
        # Check minimum R:R
        if risk_reward < self.config.min_risk_reward:
            veto_reasons.append(f"RR_TOO_LOW_{risk_reward:.2f}")
            return self._no_trade_signal(
                "RR_TOO_LOW",
                bars,
                mtf_confluence=mtf_confluence,
                smc_analysis=smc_analysis,
                regime_state=regime_state,
                veto_reasons=veto_reasons
            )
        
        # Calculate position size
        volatility = current_atr / current_price if current_price > 0 else 0.01
        position_size = self.position_sizer.calculate_size(
            capital=capital,
            entry_price=entry_price,
            stop_loss=stop_loss,
            confidence=total_score,
            current_volatility=volatility,
            trade_stats=trade_stats
        )
        
        # Determine signal strength
        strength = self._determine_strength(total_score)
        
        # Calculate expected value
        # EV = (win_rate * avg_win) - (loss_rate * avg_loss)
        # Estimate win rate from confluence score
        estimated_win_rate = 0.4 + (total_score * 0.3)  # 40-70% based on score
        expected_value = (estimated_win_rate * reward) - ((1 - estimated_win_rate) * risk)
        
        reason_codes.append(f"CONFLUENCE_SCORE_{total_score:.2f}")
        reason_codes.append(f"RR_RATIO_{risk_reward:.2f}")
        reason_codes.append(f"DIRECTION_{'LONG' if direction == TradeDirection.LONG else 'SHORT'}")
        
        return ConfluenceSignal(
            direction=direction,
            strength=strength,
            confidence=total_score,
            entry_price=entry_price,
            stop_loss=stop_loss,
            take_profit_1=tp1,
            take_profit_2=tp2,
            take_profit_3=tp3,
            position_size=position_size,
            mtf_confluence=mtf_confluence,
            smc_analysis=smc_analysis,
            regime_state=regime_state,
            mtf_score=mtf_score,
            smc_score=smc_score,
            regime_score=regime_score,
            total_score=total_score,
            risk_reward_ratio=risk_reward,
            expected_value=expected_value,
            reason_codes=reason_codes,
            veto_reasons=veto_reasons,
            timestamp=datetime.now()
        )
    
    def _score_mtf(self, mtf: MTFConfluence) -> float:
        """Score the multi-timeframe confluence (0-1)."""
        if not mtf.entry_valid:
            return 0.0
        
        score = mtf.confluence_score
        
        # Bonus for strong trends
        if mtf.overall_bias in [TrendDirection.STRONG_BULLISH, TrendDirection.STRONG_BEARISH]:
            score *= 1.2
        
        return min(1.0, score)
    
    def _score_smc(self, smc: SMCAnalysis, current_price: float) -> float:
        """Score the Smart Money Concepts analysis (0-1)."""
        score = 0.0
        
        # Bias alignment
        if smc.current_bias != 0:
            score += 0.2
        
        # Near order block
        if smc.nearest_bullish_ob and smc.current_bias > 0:
            distance = abs(current_price - smc.nearest_bullish_ob.high) / current_price
            if distance < 0.005:  # Within 0.5%
                score += 0.3
        
        if smc.nearest_bearish_ob and smc.current_bias < 0:
            distance = abs(current_price - smc.nearest_bearish_ob.low) / current_price
            if distance < 0.005:
                score += 0.3
        
        # Unfilled FVG nearby
        if smc.nearest_unfilled_fvg:
            distance = abs(current_price - smc.nearest_unfilled_fvg.midpoint) / current_price
            if distance < 0.01:  # Within 1%
                score += 0.2
        
        # Recent structure break
        if smc.structure_breaks:
            last_break = smc.structure_breaks[-1]
            if last_break.direction == smc.current_bias:
                score += 0.3
        
        return min(1.0, score)
    
    def _score_regime(self, regime: RegimeState) -> float:
        """Score the regime classification (0-1)."""
        score = regime.regime_confidence
        
        # Bonus for clear trending regimes
        if regime.primary_regime in [
            MarketRegime.STRONG_TREND_UP, 
            MarketRegime.STRONG_TREND_DOWN,
            MarketRegime.TREND_UP,
            MarketRegime.TREND_DOWN
        ]:
            score *= 1.2
        
        # Penalty for high volatility
        if regime.volatility_regime == VolatilityRegime.EXTREME:
            score *= 0.5
        elif regime.volatility_regime == VolatilityRegime.HIGH:
            score *= 0.8
        
        # Penalty for consolidation (wait for breakout)
        if regime.primary_regime == MarketRegime.CONSOLIDATION:
            score *= 0.3
        
        return min(1.0, score)
    
    def _determine_direction(
        self,
        mtf: MTFConfluence,
        smc: SMCAnalysis,
        regime: RegimeState
    ) -> TradeDirection:
        """Determine trade direction from all signals."""
        votes = []
        
        # MTF vote
        if mtf.entry_valid:
            votes.append(mtf.entry_direction)
        
        # SMC vote
        if smc.current_bias != 0:
            votes.append(smc.current_bias)
        
        # Regime vote
        if regime.primary_regime in [MarketRegime.STRONG_TREND_UP, MarketRegime.TREND_UP, MarketRegime.WEAK_TREND_UP]:
            votes.append(1)
        elif regime.primary_regime in [MarketRegime.STRONG_TREND_DOWN, MarketRegime.TREND_DOWN, MarketRegime.WEAK_TREND_DOWN]:
            votes.append(-1)
        
        if not votes:
            return TradeDirection.NO_TRADE
        
        # Majority vote
        avg_vote = sum(votes) / len(votes)
        
        if avg_vote > 0.3:
            return TradeDirection.LONG
        elif avg_vote < -0.3:
            return TradeDirection.SHORT
        else:
            return TradeDirection.NO_TRADE
    
    def _apply_vetoes(
        self,
        direction: TradeDirection,
        score: float,
        regime: RegimeState,
        atr: float,
        bars: List[dict]
    ) -> Tuple[bool, List[str]]:
        """Apply veto checks to filter out bad trades."""
        veto_reasons = []
        
        # No direction = no trade
        if direction == TradeDirection.NO_TRADE:
            veto_reasons.append("NO_DIRECTION")
            return True, veto_reasons
        
        # Minimum confluence score
        if score < self.config.min_confluence_score:
            veto_reasons.append(f"LOW_CONFLUENCE_{score:.2f}")
            return True, veto_reasons
        
        # Extreme volatility veto
        if regime.volatility_regime == VolatilityRegime.EXTREME:
            veto_reasons.append("EXTREME_VOLATILITY")
            return True, veto_reasons
        
        # Consolidation veto (wait for breakout)
        if regime.primary_regime == MarketRegime.CONSOLIDATION:
            veto_reasons.append("CONSOLIDATION_REGIME")
            return True, veto_reasons
        
        # Direction vs regime mismatch
        if direction == TradeDirection.LONG and regime.primary_regime in [
            MarketRegime.STRONG_TREND_DOWN, MarketRegime.TREND_DOWN
        ]:
            veto_reasons.append("LONG_IN_DOWNTREND")
            return True, veto_reasons
        
        if direction == TradeDirection.SHORT and regime.primary_regime in [
            MarketRegime.STRONG_TREND_UP, MarketRegime.TREND_UP
        ]:
            veto_reasons.append("SHORT_IN_UPTREND")
            return True, veto_reasons
        
        return False, veto_reasons
    
    def _calculate_levels(
        self,
        direction: TradeDirection,
        current_price: float,
        atr: float,
        smc: SMCAnalysis,
        mtf: MTFConfluence
    ) -> Tuple[float, float, float, float, float]:
        """Calculate entry, stop loss, and take profit levels."""
        
        if direction == TradeDirection.LONG:
            # Entry at current price or order block
            entry = current_price
            if self.config.use_order_block_entry and smc.nearest_bullish_ob:
                ob = smc.nearest_bullish_ob
                if ob.high < current_price and (current_price - ob.high) / current_price < 0.01:
                    entry = ob.midpoint
            
            # Stop loss below structure
            sl = entry - (atr * self.config.sl_atr_multiplier)
            if smc.nearest_bullish_ob:
                structure_sl = smc.nearest_bullish_ob.low - self.config.sl_beyond_structure
                sl = min(sl, structure_sl)
            
            # Take profits
            risk = entry - sl
            tp1 = entry + (risk * self.config.tp1_rr)
            tp2 = entry + (risk * self.config.tp2_rr)
            tp3 = entry + (risk * self.config.tp3_rr)
            
        else:  # SHORT
            entry = current_price
            if self.config.use_order_block_entry and smc.nearest_bearish_ob:
                ob = smc.nearest_bearish_ob
                if ob.low > current_price and (ob.low - current_price) / current_price < 0.01:
                    entry = ob.midpoint
            
            # Stop loss above structure
            sl = entry + (atr * self.config.sl_atr_multiplier)
            if smc.nearest_bearish_ob:
                structure_sl = smc.nearest_bearish_ob.high + self.config.sl_beyond_structure
                sl = max(sl, structure_sl)
            
            # Take profits
            risk = sl - entry
            tp1 = entry - (risk * self.config.tp1_rr)
            tp2 = entry - (risk * self.config.tp2_rr)
            tp3 = entry - (risk * self.config.tp3_rr)
        
        return entry, sl, tp1, tp2, tp3
    
    def _determine_strength(self, score: float) -> SignalStrength:
        """Determine signal strength from confluence score."""
        if score >= 0.85:
            return SignalStrength.VERY_STRONG
        elif score >= 0.7:
            return SignalStrength.STRONG
        elif score >= 0.55:
            return SignalStrength.MODERATE
        elif score >= 0.4:
            return SignalStrength.WEAK
        else:
            return SignalStrength.NONE
    
    def _calculate_atr(self, bars: List[dict], period: int = 14) -> float:
        """Calculate Average True Range."""
        if len(bars) < period + 1:
            return 0.0
        
        true_ranges = []
        for i in range(1, len(bars)):
            tr = max(
                bars[i]['high'] - bars[i]['low'],
                abs(bars[i]['high'] - bars[i - 1]['close']),
                abs(bars[i]['low'] - bars[i - 1]['close'])
            )
            true_ranges.append(tr)
        
        return sum(true_ranges[-period:]) / period
    
    def _no_trade_signal(
        self,
        reason: str,
        bars: List[dict],
        mtf_confluence: MTFConfluence = None,
        smc_analysis: SMCAnalysis = None,
        regime_state: RegimeState = None,
        veto_reasons: List[str] = None
    ) -> ConfluenceSignal:
        """Return a no-trade signal."""
        current_price = bars[-1]['close'] if bars else 0.0
        
        # Create default objects if not provided
        if mtf_confluence is None:
            mtf_confluence = self.mtf_analyzer.analyze(bars) if len(bars) >= 200 else MTFConfluence(
                overall_bias=TrendDirection.NEUTRAL,
                confluence_score=0.0,
                entry_valid=False,
                entry_direction=0,
                htf_signals=[],
                ltf_signals=[],
                key_levels=[],
                reason_codes=[]
            )
        
        if smc_analysis is None:
            smc_analysis = self.smc_detector.analyze(bars) if len(bars) >= 50 else SMCAnalysis(
                order_blocks=[],
                fair_value_gaps=[],
                liquidity_pools=[],
                structure_breaks=[],
                current_bias=0,
                nearest_bullish_ob=None,
                nearest_bearish_ob=None,
                nearest_unfilled_fvg=None,
                reason_codes=[]
            )
        
        if regime_state is None:
            regime_state = self.regime_classifier.classify(bars) if len(bars) >= 200 else RegimeState(
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
                reason_codes=[]
            )
        
        return ConfluenceSignal(
            direction=TradeDirection.NO_TRADE,
            strength=SignalStrength.NONE,
            confidence=0.0,
            entry_price=current_price,
            stop_loss=current_price,
            take_profit_1=current_price,
            take_profit_2=current_price,
            take_profit_3=current_price,
            position_size=PositionSize(
                units=0.0,
                risk_amount=0.0,
                risk_percent=0.0,
                method_used=None,
                kelly_fraction=0.0,
                volatility_adjustment=1.0,
                confidence_adjustment=1.0,
                max_size_cap=0.1,
                final_size_percent=0.0,
                reason_codes=[reason]
            ),
            mtf_confluence=mtf_confluence,
            smc_analysis=smc_analysis,
            regime_state=regime_state,
            mtf_score=0.0,
            smc_score=0.0,
            regime_score=0.0,
            total_score=0.0,
            risk_reward_ratio=0.0,
            expected_value=0.0,
            reason_codes=[reason],
            veto_reasons=veto_reasons or [reason],
            timestamp=datetime.now()
        )
