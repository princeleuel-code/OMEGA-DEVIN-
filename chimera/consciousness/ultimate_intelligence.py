"""
Ultimate Trading Intelligence Module

This module integrates ALL intelligence systems into one unified engine:
1. Smart Money Concepts (SMC) - Order blocks, FVGs, liquidity pools
2. Multi-Timeframe Confluence (MTF) - 4H/1H/15M/5M alignment
3. Adaptive Regime Detection - Auto-adjust strategy per regime
4. Risk-Adjusted Position Sizing - Kelly Criterion, volatility scaling
5. Delta Print Intelligence - Orderflow analysis
6. Market Consciousness Engine - 7-layer AI reasoning
7. Unified Intelligence - Signal confluence

This is the ULTIMATE system - combining everything the BEST traders use
into one intelligent, adaptive, self-aware trading engine.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple, Any
from enum import Enum
import math

# Import all intelligence modules
from .smc_intelligence import SMCIntelligence, SMCAnalysis, StructureType, ZoneType
from .mtf_intelligence import MTFIntelligence, MTFConfluence, TimeframeType, TrendDirection, AlignmentType
from .adaptive_regime import AdaptiveRegimeIntelligence, RegimeAnalysis, MarketRegime
from .position_sizing import PositionSizingIntelligence, PositionSizeResult, RiskLevel
from .vpe_intelligence import VPEIntelligence, VPEAnalysis, VPShape

# NEW: Import Transcript-based Intelligence Modules (3 Trader YouTube Transcripts)
from .fractal_swing_intelligence import FractalSwingIntelligence, FractalSwingAnalysis, SwingDirection
from .manipulation_candle_intelligence import ManipulationCandleIntelligence, ManipulationAnalysis, ManipulationType
from .multi_profile_volume_intelligence import MultiProfileVolumeIntelligence, MultiProfileAnalysis, ProfileShape


class SignalStrength(Enum):
    """Signal strength levels"""
    ULTRA_STRONG = "ultra_strong"
    STRONG = "strong"
    MODERATE = "moderate"
    WEAK = "weak"
    NO_SIGNAL = "no_signal"


class TradeType(Enum):
    """Trade types"""
    TREND_CONTINUATION = "trend_continuation"
    TREND_REVERSAL = "trend_reversal"
    RANGE_BOUNCE = "range_bounce"
    BREAKOUT = "breakout"
    SCALP = "scalp"
    NO_TRADE = "no_trade"


@dataclass
class IntelligenceSignal:
    """Individual intelligence signal"""
    source: str  # Which intelligence module
    direction: str  # "LONG", "SHORT", or "NEUTRAL"
    strength: float  # 0-1
    confidence: float  # 0-1
    reasoning: str
    weight: float  # Weight in final decision


@dataclass
class TradeSetup:
    """Complete trade setup from Ultimate Intelligence"""
    # Direction
    direction: str  # "LONG", "SHORT", or "NO_TRADE"
    trade_type: TradeType
    
    # Entry/Exit levels
    entry_price: float
    stop_loss: float
    take_profit_1: float
    take_profit_2: float
    take_profit_3: float
    
    # Position sizing
    position_size: float
    risk_amount: float
    risk_percent: float
    risk_reward_ratio: float
    
    # Confidence
    overall_confidence: float
    signal_strength: SignalStrength
    
    # Individual signals
    signals: List[IntelligenceSignal]
    
    # Confluence
    bullish_signals: int
    bearish_signals: int
    neutral_signals: int
    confluence_score: float
    
    # Key levels
    nearest_support: float
    nearest_resistance: float
    key_levels: List[Tuple[float, str]]  # (price, description)
    
    # Reasoning
    reasoning: List[str]
    warnings: List[str]
    
    # Timing
    entry_timing: str  # "immediate", "wait_for_pullback", "wait_for_breakout"
    invalidation_conditions: List[str]
    
    def get_summary(self) -> str:
        signals_str = "\n".join([
            f"  {s.source}: {s.direction} ({s.strength:.0%} strength, {s.confidence:.0%} conf)"
            for s in self.signals
        ])
        
        reasoning_str = "\n".join([f"  - {r}" for r in self.reasoning])
        warnings_str = "\n".join([f"  - {w}" for w in self.warnings]) if self.warnings else "  None"
        
        return f"""
================================================================================
                        ULTIMATE INTELLIGENCE TRADE SETUP
================================================================================

DIRECTION: {self.direction}
Trade Type: {self.trade_type.value}
Signal Strength: {self.signal_strength.value}
Overall Confidence: {self.overall_confidence:.1%}

ENTRY/EXIT LEVELS:
  Entry: {self.entry_price:.5f}
  Stop Loss: {self.stop_loss:.5f}
  Take Profit 1: {self.take_profit_1:.5f}
  Take Profit 2: {self.take_profit_2:.5f}
  Take Profit 3: {self.take_profit_3:.5f}

POSITION SIZING:
  Size: {self.position_size:.4f} lots
  Risk: ${self.risk_amount:.2f} ({self.risk_percent:.2%})
  Risk/Reward: {self.risk_reward_ratio:.2f}

SIGNAL CONFLUENCE:
  Bullish: {self.bullish_signals}
  Bearish: {self.bearish_signals}
  Neutral: {self.neutral_signals}
  Confluence Score: {self.confluence_score:.2f}

INDIVIDUAL SIGNALS:
{signals_str}

KEY LEVELS:
  Nearest Support: {self.nearest_support:.5f}
  Nearest Resistance: {self.nearest_resistance:.5f}

REASONING:
{reasoning_str}

WARNINGS:
{warnings_str}

ENTRY TIMING: {self.entry_timing}
================================================================================
"""


@dataclass
class UltimateAnalysis:
    """Complete analysis from Ultimate Intelligence"""
    # Sub-analyses
    smc_analysis: Optional[SMCAnalysis]
    mtf_confluence: Optional[MTFConfluence]
    regime_analysis: Optional[RegimeAnalysis]
    
    # Trade setup
    trade_setup: TradeSetup
    
    # Market state
    market_bias: str  # "BULLISH", "BEARISH", "NEUTRAL"
    market_phase: str  # "TRENDING", "RANGING", "TRANSITIONING"
    volatility_state: str  # "HIGH", "NORMAL", "LOW"
    
    # Scores
    overall_score: float  # -1 to 1
    tradability_score: float  # 0 to 1 (how tradable is current market)
    
    # Timing
    best_entry_window: str
    avoid_trading_until: Optional[str]
    
    def should_trade(self) -> bool:
        """Determine if we should take this trade"""
        return (
            self.trade_setup.direction != "NO_TRADE" and
            self.trade_setup.overall_confidence >= 0.5 and
            self.tradability_score >= 0.4 and
            len(self.trade_setup.warnings) < 3
        )


class UltimateIntelligence:
    """
    Ultimate Trading Intelligence Engine
    
    The pinnacle of trading intelligence - combining:
    - Smart Money Concepts (institutional trading)
    - Multi-Timeframe Confluence (professional analysis)
    - Adaptive Regime Detection (market adaptation)
    - Risk-Adjusted Position Sizing (institutional risk management)
    
    This is what the BEST traders in the world wish they had.
    """
    
    # Signal weights for different intelligence sources
    # ALL-KNOWING: Uses BEST parts of ALL systems together
    # Updated with 3 Trader YouTube Transcript Intelligence
    SIGNAL_WEIGHTS = {
        "smc": 0.15,  # Smart Money Concepts - Order blocks, FVGs, liquidity
        "mtf": 0.15,  # Multi-Timeframe - HTF/LTF alignment
        "vpe": 0.15,  # Volume Profile Edge - POC, VAH, VAL, signal candles
        "fractal_swing": 0.12,  # NEW: Fractal Swing - 4-6 swing rule, previous range, rounding
        "manipulation": 0.12,  # NEW: Manipulation Candle - absorption, traps, sweep detection
        "multi_profile": 0.10,  # NEW: Multi-Profile Volume - week/day/session profiles
        "regime": 0.08,  # Regime Detection - Market state adaptation
        "delta": 0.06,  # Delta Print - Orderflow analysis
        "consciousness": 0.04,  # Market Consciousness - AI reasoning
        "fundamental": 0.03  # Fundamental - Financials, valuation
    }
    
    # Minimum confidence thresholds
    MIN_CONFIDENCE_TRADE = 0.5
    MIN_CONFLUENCE_SCORE = 0.4
    MIN_SIGNALS_ALIGNED = 3
    
    def __init__(
        self,
        account_balance: float = 10000,
        risk_level: RiskLevel = RiskLevel.MODERATE,
        base_risk_per_trade: float = 0.02
    ):
        """
        Initialize Ultimate Intelligence
        
        Args:
            account_balance: Trading account balance
            risk_level: Risk tolerance level
            base_risk_per_trade: Base risk per trade as decimal
        """
        # Initialize all intelligence modules - ALL-KNOWING system
        self.smc = SMCIntelligence()
        self.mtf = MTFIntelligence()
        self.vpe = VPEIntelligence()  # Volume Profile Edge - Forest Knight's system
        self.regime = AdaptiveRegimeIntelligence()
        self.position_sizer = PositionSizingIntelligence(
            account_balance=account_balance,
            risk_level=risk_level,
            base_risk_per_trade=base_risk_per_trade
        )
        
        # NEW: Initialize Transcript-based Intelligence Modules (3 Trader YouTube Transcripts)
        self.fractal_swing = FractalSwingIntelligence()  # Dave's 4-6 swing rule, previous range
        self.manipulation = ManipulationCandleIntelligence()  # Funded Brothers manipulation candles
        self.multi_profile = MultiProfileVolumeIntelligence()  # Multi-profile volume analysis
        
        self.account_balance = account_balance
    
    def analyze(
        self,
        bars: List[Dict[str, Any]],
        timeframe_data: Optional[Dict[TimeframeType, List[Dict[str, Any]]]] = None,
        delta_analysis: Optional[Dict[str, Any]] = None,
        consciousness_analysis: Optional[Dict[str, Any]] = None,
        fundamental_analysis: Optional[Dict[str, Any]] = None
    ) -> UltimateAnalysis:
        """
        Perform complete Ultimate Intelligence analysis
        
        Args:
            bars: Primary timeframe OHLCV bars
            timeframe_data: Multi-timeframe data (optional)
            delta_analysis: Delta Print analysis (optional)
            consciousness_analysis: Market Consciousness analysis (optional)
            fundamental_analysis: Fundamental analysis (optional)
            
        Returns:
            UltimateAnalysis with complete trade setup
        """
        signals: List[IntelligenceSignal] = []
        reasoning: List[str] = []
        warnings: List[str] = []
        
        current_price = bars[-1]["close"] if bars else 0
        
        # 1. Smart Money Concepts Analysis
        smc_analysis = None
        if len(bars) >= 50:
            smc_analysis = self.smc.analyze(bars)
            smc_signal = self._process_smc_signal(smc_analysis)
            signals.append(smc_signal)
            reasoning.append(f"SMC: {smc_analysis.bias.value} bias with {smc_analysis.bias_strength:.0%} strength")
        
        # 2. Multi-Timeframe Confluence
        mtf_confluence = None
        if timeframe_data and len(timeframe_data) >= 2:
            mtf_confluence = self.mtf.analyze(timeframe_data)
            mtf_signal = self._process_mtf_signal(mtf_confluence)
            signals.append(mtf_signal)
            reasoning.append(f"MTF: {mtf_confluence.alignment.value} alignment ({mtf_confluence.alignment_score:.0%})")
        
        # 3. Volume Profile Edge Analysis (Forest Knight's system)
        vpe_analysis = None
        if len(bars) >= 50:
            vpe_analysis = self.vpe.analyze(bars)
            vpe_signal = self._process_vpe_signal(vpe_analysis)
            signals.append(vpe_signal)
            reasoning.append(f"VPE: {vpe_analysis.market_bias} bias, VP shape: {vpe_analysis.session_vp.shape.value}")
        
        # 4. Regime Analysis
        regime_analysis = None
        if len(bars) >= 200:
            regime_analysis = self.regime.analyze(bars)
            regime_signal = self._process_regime_signal(regime_analysis)
            signals.append(regime_signal)
            reasoning.append(f"Regime: {regime_analysis.current_regime.value} ({regime_analysis.regime_confidence:.0%})")
        
        # 5. NEW: Fractal Swing Intelligence (Dave's 4-6 swing rule)
        fractal_analysis = None
        if len(bars) >= 50:
            fractal_analysis = self.fractal_swing.analyze(bars)
            fractal_signal = self._process_fractal_swing_signal(fractal_analysis)
            signals.append(fractal_signal)
            reasoning.append(f"Fractal Swing: {fractal_analysis.signal} ({fractal_analysis.swing_count} swings, {'ready for reversal' if fractal_analysis.ready_for_reversal else 'not ready'})")
        
        # 6. NEW: Manipulation Candle Intelligence (Funded Brothers)
        manipulation_analysis = None
        if len(bars) >= 20:
            manipulation_analysis = self.manipulation.analyze(bars)
            manipulation_signal = self._process_manipulation_signal(manipulation_analysis)
            signals.append(manipulation_signal)
            if manipulation_analysis.trap_detected:
                reasoning.append(f"Manipulation: {manipulation_analysis.signal} (TRAP DETECTED: {manipulation_analysis.trap_direction} traders trapped)")
            else:
                reasoning.append(f"Manipulation: {manipulation_analysis.signal} ({manipulation_analysis.delta_direction.value})")
        
        # 7. NEW: Multi-Profile Volume Intelligence
        multi_profile_analysis = None
        if len(bars) >= 50:
            multi_profile_analysis = self.multi_profile.analyze(bars)
            multi_profile_signal = self._process_multi_profile_signal(multi_profile_analysis)
            signals.append(multi_profile_signal)
            if multi_profile_analysis.strongest_confluence:
                reasoning.append(f"Multi-Profile: {multi_profile_analysis.signal} (confluence at {multi_profile_analysis.strongest_confluence.price_level:.5f})")
            else:
                reasoning.append(f"Multi-Profile: {multi_profile_analysis.signal}")
        
        # 8. Delta Print Analysis (if provided)
        if delta_analysis:
            delta_signal = self._process_delta_signal(delta_analysis)
            signals.append(delta_signal)
            reasoning.append(f"Delta: {delta_analysis.get('bias', 'neutral')} pressure")
        
        # 7. Market Consciousness Analysis (if provided)
        if consciousness_analysis:
            consciousness_signal = self._process_consciousness_signal(consciousness_analysis)
            signals.append(consciousness_signal)
            reasoning.append(f"Consciousness: {consciousness_analysis.get('signal', 'neutral')}")
        
        # 8. Fundamental Analysis (if provided)
        if fundamental_analysis:
            fundamental_signal = self._process_fundamental_signal(fundamental_analysis)
            signals.append(fundamental_signal)
            reasoning.append(f"Fundamental: {fundamental_analysis.get('bias', 'neutral')}")
        
        # Calculate confluence
        bullish_signals = sum(1 for s in signals if s.direction == "LONG")
        bearish_signals = sum(1 for s in signals if s.direction == "SHORT")
        neutral_signals = sum(1 for s in signals if s.direction == "NEUTRAL")
        
        # Weighted confluence score
        confluence_score = self._calculate_confluence_score(signals)
        
        # Determine direction
        direction, overall_confidence = self._determine_direction(
            signals, confluence_score, bullish_signals, bearish_signals
        )
        
        # Determine trade type
        trade_type = self._determine_trade_type(
            smc_analysis, mtf_confluence, regime_analysis, direction
        )
        
        # Calculate entry/exit levels
        entry_price, stop_loss, tp1, tp2, tp3 = self._calculate_levels(
            bars, smc_analysis, mtf_confluence, regime_analysis, direction
        )
        
        # Calculate position size
        position_result = None
        if direction != "NO_TRADE" and entry_price > 0 and stop_loss > 0:
            win_rate = 0.55 if overall_confidence > 0.6 else 0.50
            regime_multiplier = regime_analysis.optimal_parameters.position_size_multiplier if regime_analysis else 1.0
            
            position_result = self.position_sizer.calculate_position_size(
                entry_price=entry_price,
                stop_loss=stop_loss,
                take_profit=tp1,
                win_rate=win_rate,
                signal_confidence=overall_confidence,
                current_atr=regime_analysis.current_atr if regime_analysis else 0,
                average_atr=regime_analysis.current_atr if regime_analysis else 0,
                existing_correlation=0.0,
                regime_multiplier=regime_multiplier
            )
        
        # Determine signal strength
        signal_strength = self._determine_signal_strength(
            overall_confidence, confluence_score, bullish_signals + bearish_signals
        )
        
        # Get key levels
        nearest_support, nearest_resistance, key_levels = self._get_key_levels(
            current_price, smc_analysis, mtf_confluence
        )
        
        # Determine entry timing
        entry_timing = self._determine_entry_timing(
            current_price, entry_price, direction, smc_analysis
        )
        
        # Generate warnings
        warnings = self._generate_warnings(
            signals, regime_analysis, overall_confidence, confluence_score
        )
        
        # Invalidation conditions
        invalidation_conditions = self._get_invalidation_conditions(
            direction, stop_loss, smc_analysis
        )
        
        # Create trade setup
        trade_setup = TradeSetup(
            direction=direction,
            trade_type=trade_type,
            entry_price=entry_price,
            stop_loss=stop_loss,
            take_profit_1=tp1,
            take_profit_2=tp2,
            take_profit_3=tp3,
            position_size=position_result.position_size if position_result else 0,
            risk_amount=position_result.risk_amount if position_result else 0,
            risk_percent=position_result.risk_percent if position_result else 0,
            risk_reward_ratio=position_result.risk_reward_ratio if position_result else 0,
            overall_confidence=overall_confidence,
            signal_strength=signal_strength,
            signals=signals,
            bullish_signals=bullish_signals,
            bearish_signals=bearish_signals,
            neutral_signals=neutral_signals,
            confluence_score=confluence_score,
            nearest_support=nearest_support,
            nearest_resistance=nearest_resistance,
            key_levels=key_levels,
            reasoning=reasoning,
            warnings=warnings,
            entry_timing=entry_timing,
            invalidation_conditions=invalidation_conditions
        )
        
        # Determine market state
        market_bias = "BULLISH" if confluence_score > 0.2 else ("BEARISH" if confluence_score < -0.2 else "NEUTRAL")
        market_phase = regime_analysis.current_regime.value if regime_analysis else "unknown"
        volatility_state = regime_analysis.volatility_state.value if regime_analysis else "normal"
        
        # Calculate tradability score
        tradability_score = self._calculate_tradability_score(
            overall_confidence, confluence_score, regime_analysis, len(warnings)
        )
        
        return UltimateAnalysis(
            smc_analysis=smc_analysis,
            mtf_confluence=mtf_confluence,
            regime_analysis=regime_analysis,
            trade_setup=trade_setup,
            market_bias=market_bias,
            market_phase=market_phase,
            volatility_state=volatility_state,
            overall_score=confluence_score,
            tradability_score=tradability_score,
            best_entry_window="Now" if entry_timing == "immediate" else "Wait for setup",
            avoid_trading_until=None
        )
    
    def _process_smc_signal(self, analysis: SMCAnalysis) -> IntelligenceSignal:
        """Process SMC analysis into signal"""
        if analysis.bias == StructureType.BULLISH:
            direction = "LONG"
        elif analysis.bias == StructureType.BEARISH:
            direction = "SHORT"
        else:
            direction = "NEUTRAL"
        
        return IntelligenceSignal(
            source="smc",
            direction=direction,
            strength=analysis.bias_strength,
            confidence=analysis.bias_strength,
            reasoning=f"Structure: {analysis.structure.value}, OBs: {len(analysis.order_blocks)}, FVGs: {len(analysis.fair_value_gaps)}",
            weight=self.SIGNAL_WEIGHTS["smc"]
        )
    
    def _process_mtf_signal(self, confluence: MTFConfluence) -> IntelligenceSignal:
        """Process MTF confluence into signal"""
        if confluence.trade_direction == "LONG":
            direction = "LONG"
        elif confluence.trade_direction == "SHORT":
            direction = "SHORT"
        else:
            direction = "NEUTRAL"
        
        return IntelligenceSignal(
            source="mtf",
            direction=direction,
            strength=confluence.alignment_score,
            confidence=confluence.confidence,
            reasoning=f"Alignment: {confluence.alignment.value}, HTF: {confluence.htf_score:+.2f}",
            weight=self.SIGNAL_WEIGHTS["mtf"]
        )
    
    def _process_vpe_signal(self, analysis: VPEAnalysis) -> IntelligenceSignal:
        """Process VPE (Volume Profile Edge) analysis into signal - Forest Knight's system"""
        # Determine direction from market bias and trade setup
        if analysis.market_bias == "bullish":
            direction = "LONG"
        elif analysis.market_bias == "bearish":
            direction = "SHORT"
        else:
            # Check trade setup for direction
            if analysis.trade_setup and analysis.trade_setup.direction.lower() == "long":
                direction = "LONG"
            elif analysis.trade_setup and analysis.trade_setup.direction.lower() == "short":
                direction = "SHORT"
            else:
                direction = "NEUTRAL"
        
        # Calculate strength from VP shape and signal candles
        strength = 0.5
        
        # VP shape bias
        if analysis.session_vp.shape == VPShape.P_SHAPED:
            strength += 0.15 if direction == "LONG" else -0.1
        elif analysis.session_vp.shape == VPShape.B_SHAPED:
            strength += 0.15 if direction == "SHORT" else -0.1
        
        # Signal candles at key levels boost strength
        strong_signals = sum(1 for sc in analysis.signal_candles if sc.at_key_level and sc.volume_ratio > 1.5)
        strength += min(0.2, strong_signals * 0.05)
        
        # Trade setup confidence
        if analysis.trade_setup:
            strength = max(strength, analysis.trade_setup.confidence)
        
        strength = max(0.1, min(1.0, strength))
        
        # Build reasoning
        reasoning_parts = [
            f"VP shape: {analysis.session_vp.shape.value}",
            f"POC: {analysis.session_vp.poc:.5f}",
            f"Zone: {analysis.current_zone}",
        ]
        if analysis.trade_setup:
            reasoning_parts.append(f"Setup: {analysis.trade_setup.setup_type}")
        
        return IntelligenceSignal(
            source="vpe",
            direction=direction,
            strength=strength,
            confidence=strength,
            reasoning=", ".join(reasoning_parts),
            weight=self.SIGNAL_WEIGHTS["vpe"]
        )
    
    def _process_regime_signal(self, analysis: RegimeAnalysis) -> IntelligenceSignal:
        """Process regime analysis into signal"""
        if analysis.trend_direction == "up":
            direction = "LONG"
        elif analysis.trend_direction == "down":
            direction = "SHORT"
        else:
            direction = "NEUTRAL"
        
        return IntelligenceSignal(
            source="regime",
            direction=direction,
            strength=analysis.regime_confidence,
            confidence=analysis.regime_confidence,
            reasoning=f"Regime: {analysis.current_regime.value}, Trend: {analysis.trend_strength.value}",
            weight=self.SIGNAL_WEIGHTS["regime"]
        )
    
    def _process_delta_signal(self, analysis: Dict[str, Any]) -> IntelligenceSignal:
        """Process delta analysis into signal"""
        bias = analysis.get("bias", "neutral")
        strength = analysis.get("strength", 0.5)
        
        if bias == "bullish":
            direction = "LONG"
        elif bias == "bearish":
            direction = "SHORT"
        else:
            direction = "NEUTRAL"
        
        return IntelligenceSignal(
            source="delta",
            direction=direction,
            strength=strength,
            confidence=strength,
            reasoning=f"Delta bias: {bias}",
            weight=self.SIGNAL_WEIGHTS["delta"]
        )
    
    def _process_consciousness_signal(self, analysis: Dict[str, Any]) -> IntelligenceSignal:
        """Process consciousness analysis into signal"""
        signal = analysis.get("signal", "WAIT")
        confidence = analysis.get("confidence", 0.5)
        
        if signal in ["BUY", "STRONG_BUY"]:
            direction = "LONG"
        elif signal in ["SELL", "STRONG_SELL"]:
            direction = "SHORT"
        else:
            direction = "NEUTRAL"
        
        return IntelligenceSignal(
            source="consciousness",
            direction=direction,
            strength=confidence,
            confidence=confidence,
            reasoning=f"Consciousness signal: {signal}",
            weight=self.SIGNAL_WEIGHTS["consciousness"]
        )
    
    def _process_fundamental_signal(self, analysis: Dict[str, Any]) -> IntelligenceSignal:
        """Process fundamental analysis into signal"""
        bias = analysis.get("bias", "neutral")
        strength = analysis.get("strength", 0.5)
        
        if bias == "bullish":
            direction = "LONG"
        elif bias == "bearish":
            direction = "SHORT"
        else:
            direction = "NEUTRAL"
        
        return IntelligenceSignal(
            source="fundamental",
            direction=direction,
            strength=strength,
            confidence=strength,
            reasoning=f"Fundamental bias: {bias}",
            weight=self.SIGNAL_WEIGHTS["fundamental"]
        )
    
    def _process_fractal_swing_signal(self, analysis: FractalSwingAnalysis) -> IntelligenceSignal:
        """
        Process Fractal Swing analysis into signal
        
        Based on Dave's 4-6 swing rule:
        - Count swings to POI (4-6 swings before reversal)
        - Trade pullbacks to previous range (30/50/70%)
        - Confirm liquidity sweeps before entry
        """
        direction = analysis.signal
        
        # Boost strength if ready for reversal and sweep confirmed
        strength = analysis.signal_strength
        if analysis.ready_for_reversal:
            strength = min(1.0, strength * 1.2)
        if analysis.sweep_confirmed:
            strength = min(1.0, strength * 1.15)
        if analysis.in_retracement_zone:
            strength = min(1.0, strength * 1.1)
        
        reasoning_parts = [f"{analysis.swing_count} swings"]
        if analysis.ready_for_reversal:
            reasoning_parts.append("ready for reversal")
        if analysis.sweep_confirmed:
            reasoning_parts.append("sweep confirmed")
        if analysis.in_retracement_zone:
            reasoning_parts.append(f"in {analysis.retracement_level} zone")
        
        return IntelligenceSignal(
            source="fractal_swing",
            direction=direction,
            strength=strength,
            confidence=analysis.confidence,
            reasoning=f"Fractal: {', '.join(reasoning_parts)}",
            weight=self.SIGNAL_WEIGHTS["fractal_swing"]
        )
    
    def _process_manipulation_signal(self, analysis: ManipulationAnalysis) -> IntelligenceSignal:
        """
        Process Manipulation Candle analysis into signal
        
        Based on Funded Brothers strategy:
        - Detect manipulation candles that trap traders
        - Trade AGAINST trapped traders
        - Use absorption zones for tighter stops
        """
        direction = analysis.signal
        strength = analysis.signal_strength
        
        # Boost strength if trap detected (high confidence signal)
        if analysis.trap_detected:
            strength = min(1.0, strength * 1.25)
        
        # Boost if recent manipulation candle
        if analysis.recent_manipulation:
            strength = min(1.0, strength * 1.1)
        
        reasoning_parts = [analysis.delta_direction.value]
        if analysis.trap_detected:
            reasoning_parts.append(f"{analysis.trap_direction} trapped")
        if analysis.recent_manipulation:
            reasoning_parts.append(analysis.recent_manipulation.manipulation_type.value)
        
        return IntelligenceSignal(
            source="manipulation",
            direction=direction,
            strength=strength,
            confidence=analysis.confidence,
            reasoning=f"Manipulation: {', '.join(reasoning_parts)}",
            weight=self.SIGNAL_WEIGHTS["manipulation"]
        )
    
    def _process_multi_profile_signal(self, analysis: MultiProfileAnalysis) -> IntelligenceSignal:
        """
        Process Multi-Profile Volume analysis into signal
        
        Based on Funded Brothers strategy:
        - Use 5 volume profiles (previous week, day, current week, day, session)
        - Find POC, VAH, VAL confluences
        - Identify institutional supply/demand zones
        """
        direction = analysis.signal
        strength = analysis.signal_strength
        
        # Boost strength if strong confluence
        if analysis.strongest_confluence and analysis.strongest_confluence.num_profiles >= 3:
            strength = min(1.0, strength * 1.2)
        
        # Boost if near institutional zone
        if analysis.nearest_demand or analysis.nearest_supply:
            strength = min(1.0, strength * 1.1)
        
        reasoning_parts = []
        if analysis.strongest_confluence:
            reasoning_parts.append(f"{analysis.strongest_confluence.num_profiles}-profile confluence")
        if analysis.session and analysis.session.shape:
            reasoning_parts.append(f"session {analysis.session.shape.value}")
        
        return IntelligenceSignal(
            source="multi_profile",
            direction=direction,
            strength=strength,
            confidence=analysis.confidence,
            reasoning=f"Multi-Profile: {', '.join(reasoning_parts) if reasoning_parts else 'analyzing'}",
            weight=self.SIGNAL_WEIGHTS["multi_profile"]
        )
    
    def _calculate_confluence_score(self, signals: List[IntelligenceSignal]) -> float:
        """Calculate weighted confluence score"""
        if not signals:
            return 0.0
        
        total_weight = sum(s.weight for s in signals)
        if total_weight == 0:
            return 0.0
        
        weighted_score = 0.0
        for signal in signals:
            if signal.direction == "LONG":
                weighted_score += signal.strength * signal.weight
            elif signal.direction == "SHORT":
                weighted_score -= signal.strength * signal.weight
        
        return weighted_score / total_weight
    
    def _determine_direction(
        self,
        signals: List[IntelligenceSignal],
        confluence_score: float,
        bullish_count: int,
        bearish_count: int
    ) -> Tuple[str, float]:
        """Determine trade direction and confidence"""
        if not signals:
            return "NO_TRADE", 0.0
        
        # Need minimum alignment
        total_signals = len(signals)
        if total_signals < 2:
            return "NO_TRADE", 0.0
        
        # Calculate confidence
        avg_confidence = sum(s.confidence * s.weight for s in signals) / sum(s.weight for s in signals)
        
        # Determine direction
        if confluence_score > 0.2 and bullish_count >= self.MIN_SIGNALS_ALIGNED:
            direction = "LONG"
            confidence = min(1.0, avg_confidence * (1 + confluence_score))
        elif confluence_score < -0.2 and bearish_count >= self.MIN_SIGNALS_ALIGNED:
            direction = "SHORT"
            confidence = min(1.0, avg_confidence * (1 + abs(confluence_score)))
        else:
            direction = "NO_TRADE"
            confidence = 0.0
        
        # Minimum confidence check
        if confidence < self.MIN_CONFIDENCE_TRADE:
            direction = "NO_TRADE"
            confidence = 0.0
        
        return direction, confidence
    
    def _determine_trade_type(
        self,
        smc: Optional[SMCAnalysis],
        mtf: Optional[MTFConfluence],
        regime: Optional[RegimeAnalysis],
        direction: str
    ) -> TradeType:
        """Determine the type of trade setup"""
        if direction == "NO_TRADE":
            return TradeType.NO_TRADE
        
        if regime:
            if regime.current_regime in [MarketRegime.STRONG_TREND_UP, MarketRegime.STRONG_TREND_DOWN]:
                return TradeType.TREND_CONTINUATION
            elif regime.current_regime in [MarketRegime.TIGHT_RANGE, MarketRegime.WIDE_RANGE]:
                return TradeType.RANGE_BOUNCE
            elif regime.current_regime == MarketRegime.HIGH_VOLATILITY:
                return TradeType.BREAKOUT
            elif regime.current_regime == MarketRegime.LOW_VOLATILITY:
                return TradeType.SCALP
            elif regime.current_regime == MarketRegime.TRANSITIONING:
                return TradeType.TREND_REVERSAL
        
        return TradeType.TREND_CONTINUATION
    
    def _calculate_levels(
        self,
        bars: List[Dict[str, Any]],
        smc: Optional[SMCAnalysis],
        mtf: Optional[MTFConfluence],
        regime: Optional[RegimeAnalysis],
        direction: str
    ) -> Tuple[float, float, float, float, float]:
        """Calculate entry, stop loss, and take profit levels"""
        if not bars or direction == "NO_TRADE":
            return 0, 0, 0, 0, 0
        
        current_price = bars[-1]["close"]
        atr = regime.current_atr if regime else self._calculate_atr(bars)
        
        if direction == "LONG":
            # Entry at current price or nearest demand zone
            if smc and smc.nearest_demand:
                entry = smc.nearest_demand.top
            else:
                entry = current_price
            
            # Stop loss below demand zone or ATR-based
            if smc and smc.nearest_demand:
                stop_loss = smc.nearest_demand.bottom - atr * 0.5
            else:
                stop_loss = entry - atr * 2
            
            # Take profits at supply zones or ATR-based
            risk = entry - stop_loss
            tp1 = entry + risk * 1.5
            tp2 = entry + risk * 2.5
            tp3 = entry + risk * 4.0
            
            if smc and smc.nearest_supply:
                tp1 = min(tp1, smc.nearest_supply.bottom)
            
        else:  # SHORT
            # Entry at current price or nearest supply zone
            if smc and smc.nearest_supply:
                entry = smc.nearest_supply.bottom
            else:
                entry = current_price
            
            # Stop loss above supply zone or ATR-based
            if smc and smc.nearest_supply:
                stop_loss = smc.nearest_supply.top + atr * 0.5
            else:
                stop_loss = entry + atr * 2
            
            # Take profits at demand zones or ATR-based
            risk = stop_loss - entry
            tp1 = entry - risk * 1.5
            tp2 = entry - risk * 2.5
            tp3 = entry - risk * 4.0
            
            if smc and smc.nearest_demand:
                tp1 = max(tp1, smc.nearest_demand.top)
        
        return entry, stop_loss, tp1, tp2, tp3
    
    def _calculate_atr(self, bars: List[Dict[str, Any]], period: int = 14) -> float:
        """Calculate ATR"""
        if len(bars) < period + 1:
            return 0.0
        
        tr_values = []
        for i in range(1, len(bars)):
            high = bars[i]["high"]
            low = bars[i]["low"]
            prev_close = bars[i - 1]["close"]
            
            tr = max(high - low, abs(high - prev_close), abs(low - prev_close))
            tr_values.append(tr)
        
        return sum(tr_values[-period:]) / period
    
    def _determine_signal_strength(
        self,
        confidence: float,
        confluence_score: float,
        aligned_signals: int
    ) -> SignalStrength:
        """Determine overall signal strength"""
        score = confidence * 0.4 + abs(confluence_score) * 0.3 + (aligned_signals / 6) * 0.3
        
        if score >= 0.8:
            return SignalStrength.ULTRA_STRONG
        elif score >= 0.6:
            return SignalStrength.STRONG
        elif score >= 0.4:
            return SignalStrength.MODERATE
        elif score >= 0.2:
            return SignalStrength.WEAK
        else:
            return SignalStrength.NO_SIGNAL
    
    def _get_key_levels(
        self,
        current_price: float,
        smc: Optional[SMCAnalysis],
        mtf: Optional[MTFConfluence]
    ) -> Tuple[float, float, List[Tuple[float, str]]]:
        """Get key support/resistance levels"""
        key_levels = []
        
        nearest_support = current_price * 0.99
        nearest_resistance = current_price * 1.01
        
        if smc:
            # Add SMC levels
            if smc.nearest_demand:
                nearest_support = smc.nearest_demand.top
                key_levels.append((smc.nearest_demand.top, "Demand Zone"))
            
            if smc.nearest_supply:
                nearest_resistance = smc.nearest_supply.bottom
                key_levels.append((smc.nearest_supply.bottom, "Supply Zone"))
            
            # Add equilibrium
            key_levels.append((smc.equilibrium, "Equilibrium"))
            
            # Add premium/discount
            key_levels.append((smc.premium_zone[1], "Premium Zone"))
            key_levels.append((smc.discount_zone[0], "Discount Zone"))
        
        if mtf:
            # Add MTF levels
            if mtf.htf_support > 0:
                key_levels.append((mtf.htf_support, "HTF Support"))
            if mtf.htf_resistance > 0:
                key_levels.append((mtf.htf_resistance, "HTF Resistance"))
        
        # Sort by distance from current price
        key_levels.sort(key=lambda x: abs(x[0] - current_price))
        
        return nearest_support, nearest_resistance, key_levels[:10]
    
    def _determine_entry_timing(
        self,
        current_price: float,
        entry_price: float,
        direction: str,
        smc: Optional[SMCAnalysis]
    ) -> str:
        """Determine optimal entry timing"""
        if direction == "NO_TRADE":
            return "no_trade"
        
        price_diff_percent = abs(current_price - entry_price) / current_price
        
        if price_diff_percent < 0.001:  # Within 0.1%
            return "immediate"
        elif direction == "LONG" and current_price > entry_price:
            return "wait_for_pullback"
        elif direction == "SHORT" and current_price < entry_price:
            return "wait_for_pullback"
        else:
            return "wait_for_breakout"
    
    def _generate_warnings(
        self,
        signals: List[IntelligenceSignal],
        regime: Optional[RegimeAnalysis],
        confidence: float,
        confluence_score: float
    ) -> List[str]:
        """Generate warnings for the trade setup"""
        warnings = []
        
        # Low confidence warning
        if confidence < 0.6:
            warnings.append(f"Low confidence ({confidence:.0%}) - consider smaller position")
        
        # Mixed signals warning
        if abs(confluence_score) < 0.3:
            warnings.append("Mixed signals - confluence is weak")
        
        # Regime warnings
        if regime:
            if regime.current_regime == MarketRegime.HIGH_VOLATILITY:
                warnings.append("High volatility regime - use wider stops")
            
            if regime.regime_change_probability > 0.5:
                warnings.append(f"Regime change likely ({regime.regime_change_probability:.0%})")
            
            if regime.momentum_divergence:
                warnings.append("Momentum divergence detected - potential reversal")
        
        # Signal disagreement warning
        long_signals = sum(1 for s in signals if s.direction == "LONG")
        short_signals = sum(1 for s in signals if s.direction == "SHORT")
        
        if long_signals > 0 and short_signals > 0:
            warnings.append(f"Conflicting signals: {long_signals} bullish vs {short_signals} bearish")
        
        return warnings
    
    def _get_invalidation_conditions(
        self,
        direction: str,
        stop_loss: float,
        smc: Optional[SMCAnalysis]
    ) -> List[str]:
        """Get conditions that would invalidate the trade"""
        conditions = []
        
        if direction == "NO_TRADE":
            return conditions
        
        conditions.append(f"Price reaches stop loss at {stop_loss:.5f}")
        
        if smc:
            if direction == "LONG":
                conditions.append("Break below nearest demand zone")
                if smc.structure == StructureType.BULLISH:
                    conditions.append("Structure turns bearish (lower low)")
            else:
                conditions.append("Break above nearest supply zone")
                if smc.structure == StructureType.BEARISH:
                    conditions.append("Structure turns bullish (higher high)")
        
        return conditions
    
    def _calculate_tradability_score(
        self,
        confidence: float,
        confluence_score: float,
        regime: Optional[RegimeAnalysis],
        num_warnings: int
    ) -> float:
        """Calculate how tradable the current market is"""
        score = 0.0
        
        # Confidence contribution
        score += confidence * 0.3
        
        # Confluence contribution
        score += abs(confluence_score) * 0.3
        
        # Regime contribution
        if regime:
            if regime.current_regime in [MarketRegime.STRONG_TREND_UP, MarketRegime.STRONG_TREND_DOWN]:
                score += 0.2
            elif regime.current_regime in [MarketRegime.TIGHT_RANGE, MarketRegime.WIDE_RANGE]:
                score += 0.1
            elif regime.current_regime == MarketRegime.HIGH_VOLATILITY:
                score += 0.05
            elif regime.current_regime == MarketRegime.TRANSITIONING:
                score += 0.0
        else:
            score += 0.1
        
        # Warning penalty
        score -= num_warnings * 0.05
        
        return max(0.0, min(1.0, score))
    
    def update_account(self, new_balance: float):
        """Update account balance"""
        self.account_balance = new_balance
        self.position_sizer.update_account(new_balance)


def test_ultimate_intelligence():
    """Test Ultimate Intelligence"""
    import random
    
    # Generate sample data
    bars = []
    price = 1.1000
    
    for i in range(300):
        trend = 0.0001 if i < 150 else -0.00005
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
    
    # Create Ultimate Intelligence
    ultimate = UltimateIntelligence(
        account_balance=10000,
        risk_level=RiskLevel.MODERATE
    )
    
    # Create MTF data
    mtf = MTFIntelligence()
    timeframe_data = {
        TimeframeType.M15: bars[-200:],
        TimeframeType.H1: mtf.resample_bars(bars, TimeframeType.H1)[-100:],
        TimeframeType.H4: mtf.resample_bars(bars, TimeframeType.H4)[-50:]
    }
    
    # Run analysis
    analysis = ultimate.analyze(
        bars=bars,
        timeframe_data=timeframe_data,
        delta_analysis={"bias": "bullish", "strength": 0.6},
        consciousness_analysis={"signal": "BUY", "confidence": 0.65}
    )
    
    print("=" * 80)
    print("ULTIMATE INTELLIGENCE TEST")
    print("=" * 80)
    print(analysis.trade_setup.get_summary())
    
    print(f"\nMarket State:")
    print(f"  Bias: {analysis.market_bias}")
    print(f"  Phase: {analysis.market_phase}")
    print(f"  Volatility: {analysis.volatility_state}")
    print(f"  Tradability: {analysis.tradability_score:.1%}")
    print(f"  Should Trade: {'YES' if analysis.should_trade() else 'NO'}")
    
    return analysis


if __name__ == "__main__":
    test_ultimate_intelligence()
