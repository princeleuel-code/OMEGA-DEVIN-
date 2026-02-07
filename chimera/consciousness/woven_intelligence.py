"""
WOVEN INTELLIGENCE - TRUE Emergent Understanding

This is NOT a voting system. This is a LAYERED intelligence where each module
INFORMS the next, creating EMERGENT understanding and COHERENT NARRATIVES.

Architecture:
LAYER 1: CONTEXT ESTABLISHMENT
  - Regime Detection: What type of market?
  - Session Analysis: What time? News coming?
  - Cross-Asset: Broader market sentiment?

LAYER 2: STRUCTURE ANALYSIS (informed by Layer 1)
  - SMC: Look for structures appropriate to the regime
  - Fractal Swing: Count swings, check reversal readiness
  - Multi-Profile: Key volume levels

LAYER 3: FLOW ANALYSIS (informed by Layers 1 & 2)
  - Institutional Flow: Are institutions at the SMC levels?
  - VPE: Is volume confirming structure?
  - Manipulation: Are traps being set?

LAYER 4: CONFLUENCE & VALIDATION
  - Does flow CONFIRM structure?
  - Does structure ALIGN with regime?
  - Is there a COHERENT NARRATIVE?

LAYER 5: DECISION
  - All layers align → HIGH CONFIDENCE
  - Layers conflict → NO TRADE
  - Generate NARRATIVE explanation

The key: Each layer INFORMS the next. Context flows through the system.
This creates EMERGENT understanding, not just vote counting.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple, Any
from enum import Enum
import math


# ============================================================================
# CONTEXT OBJECTS - Flow between layers
# ============================================================================

class MarketContext(Enum):
    """Overall market context"""
    STRONG_TREND_UP = "strong_trend_up"
    WEAK_TREND_UP = "weak_trend_up"
    RANGING = "ranging"
    WEAK_TREND_DOWN = "weak_trend_down"
    STRONG_TREND_DOWN = "strong_trend_down"
    VOLATILE_CHAOS = "volatile_chaos"
    ACCUMULATION = "accumulation"
    DISTRIBUTION = "distribution"


class FlowConfirmation(Enum):
    """How well flow confirms structure"""
    STRONG_CONFIRM = "strong_confirm"
    WEAK_CONFIRM = "weak_confirm"
    NEUTRAL = "neutral"
    WEAK_DIVERGE = "weak_diverge"
    STRONG_DIVERGE = "strong_diverge"


class NarrativeStrength(Enum):
    """How coherent is the market narrative"""
    CRYSTAL_CLEAR = "crystal_clear"  # Everything aligns perfectly
    CLEAR = "clear"  # Strong alignment
    MODERATE = "moderate"  # Some alignment
    MURKY = "murky"  # Mixed signals
    CONTRADICTORY = "contradictory"  # Signals fight each other


@dataclass
class Layer1Context:
    """Context from Layer 1 - Market Environment"""
    market_context: MarketContext
    regime_confidence: float
    
    # Session info
    current_session: str  # "asian", "london", "new_york", "overlap"
    session_quality: str  # "prime", "good", "poor", "avoid"
    news_risk: bool
    
    # Cross-asset sentiment
    risk_sentiment: str  # "risk_on", "risk_off", "neutral"
    dxy_bias: str  # "bullish", "bearish", "neutral"
    correlated_assets_agree: bool
    
    # What to look for in Layer 2
    look_for_longs: bool
    look_for_shorts: bool
    expect_reversal: bool
    expect_continuation: bool
    
    # Confidence in context
    context_confidence: float


@dataclass
class Layer2Structure:
    """Structure from Layer 2 - Market Structure"""
    # SMC findings
    has_bullish_ob: bool
    has_bearish_ob: bool
    ob_price: Optional[float]
    ob_strength: float
    
    has_bullish_fvg: bool
    has_bearish_fvg: bool
    fvg_price: Optional[float]
    
    liquidity_above: Optional[float]
    liquidity_below: Optional[float]
    
    # Fractal Swing findings
    swing_count: int
    ready_for_reversal: bool
    swing_direction: str  # "up", "down", "unclear"
    previous_range_broken: bool
    
    # Multi-Profile findings
    poc_price: float
    vah_price: float
    val_price: float
    price_vs_value: str  # "above_value", "at_value", "below_value"
    volume_confluence_price: Optional[float]
    
    # What Layer 2 suggests
    structure_bias: str  # "bullish", "bearish", "neutral"
    structure_confidence: float
    key_level_to_watch: float
    invalidation_level: float


@dataclass
class Layer3Flow:
    """Flow from Layer 3 - Order Flow Analysis"""
    # Institutional Flow
    institutional_activity: str  # "accumulating", "distributing", "neutral"
    smart_money_direction: str  # "buying", "selling", "neutral"
    iceberg_detected: bool
    iceberg_direction: Optional[str]
    
    # VPE findings
    volume_confirms_structure: bool
    signal_candle_detected: bool
    signal_candle_type: Optional[str]  # "bullish_engulfing", "bearish_engulfing", etc.
    volume_at_key_level: bool
    
    # Manipulation findings
    trap_detected: bool
    trap_direction: Optional[str]  # "long_trap", "short_trap"
    absorption_detected: bool
    absorption_direction: Optional[str]
    
    # Flow confirmation
    flow_confirms_structure: FlowConfirmation
    flow_confidence: float


@dataclass
class Layer4Confluence:
    """Confluence from Layer 4 - Validation"""
    # Does everything align?
    context_structure_align: bool
    structure_flow_align: bool
    all_layers_align: bool
    
    # Narrative
    narrative_strength: NarrativeStrength
    narrative_text: str  # Human-readable story
    
    # Confluence score
    confluence_score: float  # -1 to 1
    
    # Conflicts
    conflicts: List[str]
    
    # Validation
    is_valid_setup: bool
    validation_reasons: List[str]


@dataclass
class WovenDecision:
    """Final decision from Layer 5"""
    # Direction
    direction: str  # "LONG", "SHORT", "NO_TRADE"
    confidence: float
    
    # Entry/Exit
    entry_price: float
    stop_loss: float
    take_profit_1: float
    take_profit_2: float
    take_profit_3: float
    
    # The NARRATIVE - why we're taking this trade
    narrative: str
    
    # Layer summaries
    context_summary: str
    structure_summary: str
    flow_summary: str
    confluence_summary: str
    
    # Warnings
    warnings: List[str]
    
    # Invalidation
    invalidation_conditions: List[str]
    
    # Scores
    narrative_strength: NarrativeStrength
    overall_score: float


@dataclass
class WovenAnalysis:
    """Complete Woven Intelligence Analysis"""
    # All layers
    layer1: Layer1Context
    layer2: Layer2Structure
    layer3: Layer3Flow
    layer4: Layer4Confluence
    decision: WovenDecision
    
    # Raw data for debugging
    raw_signals: Dict[str, Any]
    
    def get_full_narrative(self) -> str:
        """Get the complete market narrative"""
        return f"""
================================================================================
                    WOVEN INTELLIGENCE ANALYSIS
================================================================================

MARKET NARRATIVE: {self.decision.narrative_strength.value.upper()}
{self.decision.narrative}

--------------------------------------------------------------------------------
LAYER 1 - CONTEXT
--------------------------------------------------------------------------------
{self.decision.context_summary}

--------------------------------------------------------------------------------
LAYER 2 - STRUCTURE  
--------------------------------------------------------------------------------
{self.decision.structure_summary}

--------------------------------------------------------------------------------
LAYER 3 - FLOW
--------------------------------------------------------------------------------
{self.decision.flow_summary}

--------------------------------------------------------------------------------
LAYER 4 - CONFLUENCE
--------------------------------------------------------------------------------
{self.decision.confluence_summary}

--------------------------------------------------------------------------------
DECISION
--------------------------------------------------------------------------------
Direction: {self.decision.direction}
Confidence: {self.decision.confidence:.1%}
Entry: {self.decision.entry_price:.5f}
Stop Loss: {self.decision.stop_loss:.5f}
TP1: {self.decision.take_profit_1:.5f}
TP2: {self.decision.take_profit_2:.5f}
TP3: {self.decision.take_profit_3:.5f}

Warnings:
{chr(10).join(['  - ' + w for w in self.decision.warnings]) if self.decision.warnings else '  None'}

Invalidation:
{chr(10).join(['  - ' + i for i in self.decision.invalidation_conditions]) if self.decision.invalidation_conditions else '  None'}

================================================================================
"""


class WovenIntelligence:
    """
    WOVEN INTELLIGENCE ENGINE
    
    True emergent understanding through layered analysis where each layer
    INFORMS the next, creating coherent market narratives instead of
    simple vote counting.
    
    This is what separates amateur systems from institutional-grade intelligence.
    """
    
    def __init__(self, account_balance: float = 10000):
        """Initialize Woven Intelligence"""
        self.account_balance = account_balance
        
        # Import intelligence modules
        from .smc_intelligence import SMCIntelligence
        from .mtf_intelligence import MTFIntelligence
        from .adaptive_regime import AdaptiveRegimeIntelligence
        from .vpe_intelligence import VPEIntelligence
        from .fractal_swing_intelligence import FractalSwingIntelligence
        from .manipulation_candle_intelligence import ManipulationCandleIntelligence
        from .multi_profile_volume_intelligence import MultiProfileVolumeIntelligence
        from .session_trade_management import SessionTradeManagementIntelligence
        from .institutional_flow_detection import InstitutionalFlowDetection
        from .cross_asset_correlation import CrossAssetCorrelationIntelligence
        
        # Initialize all modules
        self.smc = SMCIntelligence()
        self.mtf = MTFIntelligence()
        self.regime = AdaptiveRegimeIntelligence()
        self.vpe = VPEIntelligence()
        self.fractal_swing = FractalSwingIntelligence()
        self.manipulation = ManipulationCandleIntelligence()
        self.multi_profile = MultiProfileVolumeIntelligence()
        self.session_mgmt = SessionTradeManagementIntelligence(
            account_balance=account_balance,
            risk_per_trade=0.02,
            max_daily_trades=2
        )
        self.institutional_flow = InstitutionalFlowDetection()
        self.cross_asset = CrossAssetCorrelationIntelligence()
    
    def analyze(self, bars: List[Dict[str, Any]], symbol: str = "EURUSD") -> WovenAnalysis:
        """
        Perform WOVEN analysis - layered intelligence with context flow
        
        Args:
            bars: OHLCV bars
            symbol: Trading symbol
            
        Returns:
            WovenAnalysis with complete narrative
        """
        if len(bars) < 50:
            return self._create_insufficient_data_analysis(bars)
        
        current_price = bars[-1]["close"]
        raw_signals = {}
        
        # ====================================================================
        # LAYER 1: CONTEXT ESTABLISHMENT
        # ====================================================================
        layer1 = self._analyze_layer1_context(bars, symbol, raw_signals)
        
        # ====================================================================
        # LAYER 2: STRUCTURE ANALYSIS (informed by Layer 1)
        # ====================================================================
        layer2 = self._analyze_layer2_structure(bars, layer1, raw_signals)
        
        # ====================================================================
        # LAYER 3: FLOW ANALYSIS (informed by Layers 1 & 2)
        # ====================================================================
        layer3 = self._analyze_layer3_flow(bars, layer1, layer2, raw_signals)
        
        # ====================================================================
        # LAYER 4: CONFLUENCE & VALIDATION
        # ====================================================================
        layer4 = self._analyze_layer4_confluence(layer1, layer2, layer3)
        
        # ====================================================================
        # LAYER 5: DECISION
        # ====================================================================
        decision = self._make_decision(bars, layer1, layer2, layer3, layer4)
        
        return WovenAnalysis(
            layer1=layer1,
            layer2=layer2,
            layer3=layer3,
            layer4=layer4,
            decision=decision,
            raw_signals=raw_signals
        )
    
    def _analyze_layer1_context(
        self, 
        bars: List[Dict[str, Any]], 
        symbol: str,
        raw_signals: Dict[str, Any]
    ) -> Layer1Context:
        """
        LAYER 1: Establish market context
        
        This layer determines:
        - What type of market are we in?
        - What session is it?
        - What's the broader sentiment?
        - What should we be looking for?
        """
        # Regime Analysis
        regime_analysis = None
        market_context = MarketContext.RANGING
        regime_confidence = 0.5
        
        if len(bars) >= 200:
            regime_analysis = self.regime.analyze(bars)
            raw_signals["regime"] = regime_analysis
            
            # Map regime to context
            regime_map = {
                "trending_bullish": MarketContext.STRONG_TREND_UP,
                "trending_bearish": MarketContext.STRONG_TREND_DOWN,
                "ranging": MarketContext.RANGING,
                "volatile": MarketContext.VOLATILE_CHAOS,
                "accumulation": MarketContext.ACCUMULATION,
                "distribution": MarketContext.DISTRIBUTION
            }
            regime_str = regime_analysis.current_regime.value.lower()
            market_context = regime_map.get(regime_str, MarketContext.RANGING)
            regime_confidence = regime_analysis.regime_confidence
        
        # Session Analysis
        session_analysis = None
        current_session = "unknown"
        session_quality = "poor"
        news_risk = False
        
        if len(bars) >= 10:
            session_analysis = self.session_mgmt.analyze(bars)
            raw_signals["session"] = session_analysis
            current_session = session_analysis.session_info.current_session.value
            session_quality = session_analysis.session_info.session_quality.value
            news_risk = session_analysis.news_warning
        
        # Cross-Asset Analysis
        cross_asset_analysis = None
        risk_sentiment = "neutral"
        dxy_bias = "neutral"
        correlated_agree = True
        
        if len(bars) >= 20:
            cross_asset_analysis = self.cross_asset.analyze(
                target_asset=symbol,
                target_bars=bars
            )
            raw_signals["cross_asset"] = cross_asset_analysis
            risk_sentiment = cross_asset_analysis.risk_sentiment.sentiment.value
            dxy_bias = cross_asset_analysis.dxy_impact.dxy_direction.lower()
            correlated_agree = cross_asset_analysis.signal_strength > 0.5
        
        # Determine what to look for based on context
        look_for_longs = market_context in [
            MarketContext.STRONG_TREND_UP, 
            MarketContext.WEAK_TREND_UP,
            MarketContext.ACCUMULATION
        ]
        look_for_shorts = market_context in [
            MarketContext.STRONG_TREND_DOWN,
            MarketContext.WEAK_TREND_DOWN,
            MarketContext.DISTRIBUTION
        ]
        expect_reversal = market_context in [
            MarketContext.ACCUMULATION,
            MarketContext.DISTRIBUTION
        ]
        expect_continuation = market_context in [
            MarketContext.STRONG_TREND_UP,
            MarketContext.STRONG_TREND_DOWN
        ]
        
        # In ranging market, look for both
        if market_context == MarketContext.RANGING:
            look_for_longs = True
            look_for_shorts = True
        
        # Calculate context confidence
        context_confidence = regime_confidence * 0.5
        if session_quality in ["prime", "good"]:
            context_confidence += 0.25
        if correlated_agree:
            context_confidence += 0.25
        
        return Layer1Context(
            market_context=market_context,
            regime_confidence=regime_confidence,
            current_session=current_session,
            session_quality=session_quality,
            news_risk=news_risk,
            risk_sentiment=risk_sentiment,
            dxy_bias=dxy_bias,
            correlated_assets_agree=correlated_agree,
            look_for_longs=look_for_longs,
            look_for_shorts=look_for_shorts,
            expect_reversal=expect_reversal,
            expect_continuation=expect_continuation,
            context_confidence=context_confidence
        )
    
    def _analyze_layer2_structure(
        self,
        bars: List[Dict[str, Any]],
        context: Layer1Context,
        raw_signals: Dict[str, Any]
    ) -> Layer2Structure:
        """
        LAYER 2: Analyze market structure (INFORMED by Layer 1)
        
        Based on the context, we look for specific structures:
        - In uptrend: Look for bullish order blocks, bullish FVGs
        - In downtrend: Look for bearish order blocks, bearish FVGs
        - In range: Look for range boundaries
        """
        current_price = bars[-1]["close"]
        
        # SMC Analysis - look for structures based on context
        smc_analysis = self.smc.analyze(bars)
        raw_signals["smc"] = smc_analysis
        
        # Extract relevant structures based on context
        has_bullish_ob = False
        has_bearish_ob = False
        ob_price = None
        ob_strength = 0.0
        
        for ob in smc_analysis.order_blocks:
            if ob.zone_type.value == "demand" and context.look_for_longs:
                has_bullish_ob = True
                ob_price = ob.price_level
                ob_strength = max(ob_strength, ob.strength)
            elif ob.zone_type.value == "supply" and context.look_for_shorts:
                has_bearish_ob = True
                ob_price = ob.price_level
                ob_strength = max(ob_strength, ob.strength)
        
        # FVG analysis
        has_bullish_fvg = False
        has_bearish_fvg = False
        fvg_price = None
        
        for fvg in smc_analysis.fair_value_gaps:
            if fvg.zone_type.value == "demand" and context.look_for_longs:
                has_bullish_fvg = True
                fvg_price = fvg.price_level
            elif fvg.zone_type.value == "supply" and context.look_for_shorts:
                has_bearish_fvg = True
                fvg_price = fvg.price_level
        
        # Liquidity levels
        liquidity_above = None
        liquidity_below = None
        for liq in smc_analysis.liquidity_pools:
            liq_price = liq.midpoint  # Use midpoint of the zone
            if liq_price > current_price:
                if liquidity_above is None or liq_price < liquidity_above:
                    liquidity_above = liq_price
            else:
                if liquidity_below is None or liq_price > liquidity_below:
                    liquidity_below = liq_price
        
        # Fractal Swing Analysis
        fractal_analysis = self.fractal_swing.analyze(bars)
        raw_signals["fractal_swing"] = fractal_analysis
        
        swing_count = fractal_analysis.swing_count
        ready_for_reversal = fractal_analysis.ready_for_reversal
        swing_direction = fractal_analysis.swing_direction.value if fractal_analysis.swing_direction else "unclear"
        # Check if price has broken previous range
        previous_range_broken = False
        if fractal_analysis.previous_range:
            pr = fractal_analysis.previous_range
            previous_range_broken = current_price > pr.high or current_price < pr.low
        
        # Multi-Profile Analysis
        multi_profile_analysis = self.multi_profile.analyze(bars)
        raw_signals["multi_profile"] = multi_profile_analysis
        
        poc_price = multi_profile_analysis.session.poc if multi_profile_analysis.session else current_price
        vah_price = multi_profile_analysis.session.vah if multi_profile_analysis.session else current_price * 1.001
        val_price = multi_profile_analysis.session.val if multi_profile_analysis.session else current_price * 0.999
        
        # Price vs value
        if current_price > vah_price:
            price_vs_value = "above_value"
        elif current_price < val_price:
            price_vs_value = "below_value"
        else:
            price_vs_value = "at_value"
        
        volume_confluence_price = None
        if multi_profile_analysis.strongest_confluence:
            volume_confluence_price = multi_profile_analysis.strongest_confluence.price_level
        
        # Determine structure bias based on findings
        bullish_points = 0
        bearish_points = 0
        
        if has_bullish_ob:
            bullish_points += 2
        if has_bearish_ob:
            bearish_points += 2
        if has_bullish_fvg:
            bullish_points += 1
        if has_bearish_fvg:
            bearish_points += 1
        if swing_direction == "up":
            bullish_points += 1
        elif swing_direction == "down":
            bearish_points += 1
        if price_vs_value == "above_value":
            bullish_points += 1
        elif price_vs_value == "below_value":
            bearish_points += 1
        
        if bullish_points > bearish_points + 1:
            structure_bias = "bullish"
        elif bearish_points > bullish_points + 1:
            structure_bias = "bearish"
        else:
            structure_bias = "neutral"
        
        # Structure confidence
        structure_confidence = min(1.0, (bullish_points + bearish_points) / 6)
        
        # Key level to watch
        if structure_bias == "bullish" and ob_price:
            key_level = ob_price
        elif structure_bias == "bearish" and ob_price:
            key_level = ob_price
        elif volume_confluence_price:
            key_level = volume_confluence_price
        else:
            key_level = poc_price
        
        # Invalidation level
        if structure_bias == "bullish":
            invalidation = liquidity_below if liquidity_below else val_price
        elif structure_bias == "bearish":
            invalidation = liquidity_above if liquidity_above else vah_price
        else:
            invalidation = poc_price
        
        return Layer2Structure(
            has_bullish_ob=has_bullish_ob,
            has_bearish_ob=has_bearish_ob,
            ob_price=ob_price,
            ob_strength=ob_strength,
            has_bullish_fvg=has_bullish_fvg,
            has_bearish_fvg=has_bearish_fvg,
            fvg_price=fvg_price,
            liquidity_above=liquidity_above,
            liquidity_below=liquidity_below,
            swing_count=swing_count,
            ready_for_reversal=ready_for_reversal,
            swing_direction=swing_direction,
            previous_range_broken=previous_range_broken,
            poc_price=poc_price,
            vah_price=vah_price,
            val_price=val_price,
            price_vs_value=price_vs_value,
            volume_confluence_price=volume_confluence_price,
            structure_bias=structure_bias,
            structure_confidence=structure_confidence,
            key_level_to_watch=key_level,
            invalidation_level=invalidation
        )
    
    def _analyze_layer3_flow(
        self,
        bars: List[Dict[str, Any]],
        context: Layer1Context,
        structure: Layer2Structure,
        raw_signals: Dict[str, Any]
    ) -> Layer3Flow:
        """
        LAYER 3: Analyze order flow (INFORMED by Layers 1 & 2)
        
        Now we check if the FLOW confirms the STRUCTURE:
        - Are institutions buying at the bullish order block?
        - Is volume confirming the structure?
        - Are there manipulation traps?
        """
        # Institutional Flow Analysis
        institutional_analysis = self.institutional_flow.analyze(bars)
        raw_signals["institutional_flow"] = institutional_analysis
        
        institutional_activity = institutional_analysis.current_activity.value
        smart_money_direction = institutional_analysis.smart_money_direction
        iceberg_detected = institutional_analysis.iceberg_detected.value != "none"
        iceberg_direction = institutional_analysis.iceberg_detected.value if iceberg_detected else None
        
        # VPE Analysis - check volume at structure levels
        vpe_analysis = self.vpe.analyze(bars)
        raw_signals["vpe"] = vpe_analysis
        
        # Check if volume confirms structure
        volume_confirms = False
        if structure.structure_bias == "bullish" and vpe_analysis.market_bias == "bullish":
            volume_confirms = True
        elif structure.structure_bias == "bearish" and vpe_analysis.market_bias == "bearish":
            volume_confirms = True
        
        signal_candle_detected = len(vpe_analysis.signal_candles) > 0 if vpe_analysis.signal_candles else False
        signal_candle_type = vpe_analysis.signal_candles[0].pattern.value if signal_candle_detected else None
        
        # Check if there's volume at the key level
        volume_at_key_level = False
        if structure.key_level_to_watch:
            current_price = bars[-1]["close"]
            # If price is near key level and volume is high
            if abs(current_price - structure.key_level_to_watch) / current_price < 0.002:
                if vpe_analysis.volume_strength > 0.6:
                    volume_at_key_level = True
        
        # Manipulation Analysis
        manipulation_analysis = self.manipulation.analyze(bars)
        raw_signals["manipulation"] = manipulation_analysis
        
        trap_detected = manipulation_analysis.trap_detected
        trap_direction = manipulation_analysis.trap_direction if trap_detected else None
        absorption_detected = len(manipulation_analysis.absorption_zones) > 0 if manipulation_analysis.absorption_zones else False
        absorption_direction = manipulation_analysis.absorption_zones[0].absorption_type if absorption_detected else None
        
        # Determine flow confirmation
        flow_confirms_structure = FlowConfirmation.NEUTRAL
        
        # Check alignment
        structure_bullish = structure.structure_bias == "bullish"
        structure_bearish = structure.structure_bias == "bearish"
        
        flow_bullish = (
            smart_money_direction == "buying" or
            institutional_activity == "accumulating" or
            (trap_detected and trap_direction == "short_trap") or
            (absorption_detected and absorption_direction == "bullish")
        )
        flow_bearish = (
            smart_money_direction == "selling" or
            institutional_activity == "distributing" or
            (trap_detected and trap_direction == "long_trap") or
            (absorption_detected and absorption_direction == "bearish")
        )
        
        if structure_bullish and flow_bullish and volume_confirms:
            flow_confirms_structure = FlowConfirmation.STRONG_CONFIRM
        elif structure_bullish and flow_bullish:
            flow_confirms_structure = FlowConfirmation.WEAK_CONFIRM
        elif structure_bearish and flow_bearish and volume_confirms:
            flow_confirms_structure = FlowConfirmation.STRONG_CONFIRM
        elif structure_bearish and flow_bearish:
            flow_confirms_structure = FlowConfirmation.WEAK_CONFIRM
        elif structure_bullish and flow_bearish:
            flow_confirms_structure = FlowConfirmation.STRONG_DIVERGE
        elif structure_bearish and flow_bullish:
            flow_confirms_structure = FlowConfirmation.STRONG_DIVERGE
        
        # Flow confidence
        flow_confidence = 0.5
        if flow_confirms_structure in [FlowConfirmation.STRONG_CONFIRM, FlowConfirmation.STRONG_DIVERGE]:
            flow_confidence = 0.8
        elif flow_confirms_structure in [FlowConfirmation.WEAK_CONFIRM, FlowConfirmation.WEAK_DIVERGE]:
            flow_confidence = 0.6
        
        return Layer3Flow(
            institutional_activity=institutional_activity,
            smart_money_direction=smart_money_direction,
            iceberg_detected=iceberg_detected,
            iceberg_direction=iceberg_direction,
            volume_confirms_structure=volume_confirms,
            signal_candle_detected=signal_candle_detected,
            signal_candle_type=signal_candle_type,
            volume_at_key_level=volume_at_key_level,
            trap_detected=trap_detected,
            trap_direction=trap_direction,
            absorption_detected=absorption_detected,
            absorption_direction=absorption_direction,
            flow_confirms_structure=flow_confirms_structure,
            flow_confidence=flow_confidence
        )
    
    def _analyze_layer4_confluence(
        self,
        context: Layer1Context,
        structure: Layer2Structure,
        flow: Layer3Flow
    ) -> Layer4Confluence:
        """
        LAYER 4: Validate confluence across all layers
        
        Check if:
        - Context aligns with structure
        - Structure aligns with flow
        - Everything tells a coherent story
        """
        conflicts = []
        validation_reasons = []
        
        # Check context-structure alignment
        context_structure_align = False
        if context.look_for_longs and structure.structure_bias == "bullish":
            context_structure_align = True
            validation_reasons.append("Context supports bullish structure")
        elif context.look_for_shorts and structure.structure_bias == "bearish":
            context_structure_align = True
            validation_reasons.append("Context supports bearish structure")
        elif structure.structure_bias == "neutral":
            context_structure_align = True
            validation_reasons.append("Neutral structure - waiting for clarity")
        else:
            conflicts.append(f"Context ({context.market_context.value}) conflicts with structure ({structure.structure_bias})")
        
        # Check structure-flow alignment
        structure_flow_align = flow.flow_confirms_structure in [
            FlowConfirmation.STRONG_CONFIRM,
            FlowConfirmation.WEAK_CONFIRM
        ]
        
        if structure_flow_align:
            validation_reasons.append(f"Flow confirms structure ({flow.flow_confirms_structure.value})")
        else:
            conflicts.append(f"Flow diverges from structure ({flow.flow_confirms_structure.value})")
        
        # All layers align?
        all_layers_align = context_structure_align and structure_flow_align
        
        # Determine narrative strength
        if all_layers_align and flow.flow_confirms_structure == FlowConfirmation.STRONG_CONFIRM:
            narrative_strength = NarrativeStrength.CRYSTAL_CLEAR
        elif all_layers_align:
            narrative_strength = NarrativeStrength.CLEAR
        elif context_structure_align or structure_flow_align:
            narrative_strength = NarrativeStrength.MODERATE
        elif len(conflicts) == 1:
            narrative_strength = NarrativeStrength.MURKY
        else:
            narrative_strength = NarrativeStrength.CONTRADICTORY
        
        # Build narrative text
        narrative_text = self._build_narrative(context, structure, flow, narrative_strength)
        
        # Calculate confluence score
        confluence_score = 0.0
        
        # Context contribution
        if context.market_context in [MarketContext.STRONG_TREND_UP, MarketContext.STRONG_TREND_DOWN]:
            confluence_score += 0.3 if context_structure_align else -0.2
        elif context.market_context in [MarketContext.ACCUMULATION, MarketContext.DISTRIBUTION]:
            confluence_score += 0.2 if context_structure_align else -0.1
        
        # Structure contribution
        if structure.structure_bias != "neutral":
            confluence_score += 0.3 * structure.structure_confidence
        
        # Flow contribution
        if flow.flow_confirms_structure == FlowConfirmation.STRONG_CONFIRM:
            confluence_score += 0.4
        elif flow.flow_confirms_structure == FlowConfirmation.WEAK_CONFIRM:
            confluence_score += 0.2
        elif flow.flow_confirms_structure == FlowConfirmation.STRONG_DIVERGE:
            confluence_score -= 0.3
        elif flow.flow_confirms_structure == FlowConfirmation.WEAK_DIVERGE:
            confluence_score -= 0.1
        
        # Clamp to [-1, 1]
        confluence_score = max(-1.0, min(1.0, confluence_score))
        
        # Is this a valid setup?
        is_valid = (
            narrative_strength in [NarrativeStrength.CRYSTAL_CLEAR, NarrativeStrength.CLEAR] and
            len(conflicts) == 0 and
            confluence_score > 0.3
        )
        
        return Layer4Confluence(
            context_structure_align=context_structure_align,
            structure_flow_align=structure_flow_align,
            all_layers_align=all_layers_align,
            narrative_strength=narrative_strength,
            narrative_text=narrative_text,
            confluence_score=confluence_score,
            conflicts=conflicts,
            is_valid_setup=is_valid,
            validation_reasons=validation_reasons
        )
    
    def _build_narrative(
        self,
        context: Layer1Context,
        structure: Layer2Structure,
        flow: Layer3Flow,
        strength: NarrativeStrength
    ) -> str:
        """Build a human-readable market narrative"""
        
        # Context narrative
        context_story = f"The market is in a {context.market_context.value.replace('_', ' ')} phase"
        if context.current_session != "unknown":
            context_story += f" during the {context.current_session} session"
        if context.risk_sentiment != "neutral":
            context_story += f" with {context.risk_sentiment.replace('_', ' ')} sentiment"
        context_story += "."
        
        # Structure narrative
        if structure.structure_bias == "bullish":
            structure_story = "Structure is bullish"
            if structure.has_bullish_ob:
                structure_story += f" with a demand order block at {structure.ob_price:.5f}"
            if structure.ready_for_reversal:
                structure_story += ", and the market has completed enough swings for a potential reversal"
        elif structure.structure_bias == "bearish":
            structure_story = "Structure is bearish"
            if structure.has_bearish_ob:
                structure_story += f" with a supply order block at {structure.ob_price:.5f}"
            if structure.ready_for_reversal:
                structure_story += ", and the market has completed enough swings for a potential reversal"
        else:
            structure_story = "Structure is unclear - no dominant bias"
        structure_story += "."
        
        # Flow narrative
        if flow.flow_confirms_structure == FlowConfirmation.STRONG_CONFIRM:
            flow_story = "Order flow STRONGLY confirms the structure"
            if flow.smart_money_direction != "neutral":
                flow_story += f" - smart money is {flow.smart_money_direction}"
            if flow.trap_detected:
                flow_story += f", with a {flow.trap_direction} trap detected"
        elif flow.flow_confirms_structure == FlowConfirmation.WEAK_CONFIRM:
            flow_story = "Order flow weakly confirms the structure"
        elif flow.flow_confirms_structure == FlowConfirmation.STRONG_DIVERGE:
            flow_story = "WARNING: Order flow DIVERGES from structure - potential trap or reversal"
        elif flow.flow_confirms_structure == FlowConfirmation.WEAK_DIVERGE:
            flow_story = "Order flow shows some divergence from structure"
        else:
            flow_story = "Order flow is neutral"
        flow_story += "."
        
        # Conclusion
        if strength == NarrativeStrength.CRYSTAL_CLEAR:
            conclusion = "CONCLUSION: All signals align perfectly. High-confidence setup."
        elif strength == NarrativeStrength.CLEAR:
            conclusion = "CONCLUSION: Signals align well. Good setup with manageable risk."
        elif strength == NarrativeStrength.MODERATE:
            conclusion = "CONCLUSION: Mixed signals. Proceed with caution or wait for clarity."
        elif strength == NarrativeStrength.MURKY:
            conclusion = "CONCLUSION: Conflicting signals. Best to stay out."
        else:
            conclusion = "CONCLUSION: Signals contradict each other. NO TRADE."
        
        return f"{context_story} {structure_story} {flow_story} {conclusion}"
    
    def _make_decision(
        self,
        bars: List[Dict[str, Any]],
        context: Layer1Context,
        structure: Layer2Structure,
        flow: Layer3Flow,
        confluence: Layer4Confluence
    ) -> WovenDecision:
        """
        LAYER 5: Make the final trading decision
        
        Based on all layers, decide:
        - Direction (LONG/SHORT/NO_TRADE)
        - Entry/Exit levels
        - Confidence
        """
        current_price = bars[-1]["close"]
        atr = self._calculate_atr(bars)
        
        warnings = []
        invalidation_conditions = []
        
        # Determine direction
        direction = "NO_TRADE"
        confidence = 0.0
        
        if confluence.is_valid_setup:
            if structure.structure_bias == "bullish" and context.look_for_longs:
                direction = "LONG"
                confidence = confluence.confluence_score * context.context_confidence
            elif structure.structure_bias == "bearish" and context.look_for_shorts:
                direction = "SHORT"
                confidence = abs(confluence.confluence_score) * context.context_confidence
        
        # Even if not "valid", we might have a moderate setup
        if direction == "NO_TRADE" and confluence.narrative_strength == NarrativeStrength.MODERATE:
            if structure.structure_bias == "bullish" and flow.flow_confirms_structure in [FlowConfirmation.WEAK_CONFIRM, FlowConfirmation.STRONG_CONFIRM]:
                direction = "LONG"
                confidence = 0.4  # Lower confidence for moderate setups
                warnings.append("Moderate setup - reduced position size recommended")
            elif structure.structure_bias == "bearish" and flow.flow_confirms_structure in [FlowConfirmation.WEAK_CONFIRM, FlowConfirmation.STRONG_CONFIRM]:
                direction = "SHORT"
                confidence = 0.4
                warnings.append("Moderate setup - reduced position size recommended")
        
        # Calculate levels
        if direction == "LONG":
            entry_price = current_price
            stop_loss = structure.invalidation_level if structure.invalidation_level < current_price else current_price - 2 * atr
            risk = entry_price - stop_loss
            take_profit_1 = entry_price + risk * 1.5
            take_profit_2 = entry_price + risk * 2.5
            take_profit_3 = entry_price + risk * 4.0
            
            if structure.liquidity_above:
                invalidation_conditions.append(f"Price closes below {stop_loss:.5f}")
            invalidation_conditions.append("Structure breaks bearish")
            
        elif direction == "SHORT":
            entry_price = current_price
            stop_loss = structure.invalidation_level if structure.invalidation_level > current_price else current_price + 2 * atr
            risk = stop_loss - entry_price
            take_profit_1 = entry_price - risk * 1.5
            take_profit_2 = entry_price - risk * 2.5
            take_profit_3 = entry_price - risk * 4.0
            
            if structure.liquidity_below:
                invalidation_conditions.append(f"Price closes above {stop_loss:.5f}")
            invalidation_conditions.append("Structure breaks bullish")
            
        else:
            entry_price = current_price
            stop_loss = current_price
            take_profit_1 = current_price
            take_profit_2 = current_price
            take_profit_3 = current_price
        
        # Add warnings based on context
        if context.news_risk:
            warnings.append("High-impact news approaching")
        if context.session_quality in ["poor", "avoid"]:
            warnings.append(f"Poor session quality: {context.current_session}")
        if not context.correlated_assets_agree:
            warnings.append("Correlated assets diverging")
        if flow.iceberg_detected:
            warnings.append(f"Iceberg order detected: {flow.iceberg_direction}")
        
        # Add conflicts as warnings
        for conflict in confluence.conflicts:
            warnings.append(conflict)
        
        # Build summaries
        context_summary = f"Market: {context.market_context.value}, Session: {context.current_session} ({context.session_quality}), Sentiment: {context.risk_sentiment}"
        structure_summary = f"Bias: {structure.structure_bias}, OB: {'Yes' if structure.has_bullish_ob or structure.has_bearish_ob else 'No'}, Swings: {structure.swing_count}, Ready for reversal: {structure.ready_for_reversal}"
        flow_summary = f"Institutional: {flow.institutional_activity}, Smart Money: {flow.smart_money_direction}, Flow confirms: {flow.flow_confirms_structure.value}"
        confluence_summary = f"Narrative: {confluence.narrative_strength.value}, Confluence: {confluence.confluence_score:.2f}, Valid: {confluence.is_valid_setup}"
        
        # Overall score
        overall_score = confluence.confluence_score * confidence
        
        return WovenDecision(
            direction=direction,
            confidence=confidence,
            entry_price=entry_price,
            stop_loss=stop_loss,
            take_profit_1=take_profit_1,
            take_profit_2=take_profit_2,
            take_profit_3=take_profit_3,
            narrative=confluence.narrative_text,
            context_summary=context_summary,
            structure_summary=structure_summary,
            flow_summary=flow_summary,
            confluence_summary=confluence_summary,
            warnings=warnings,
            invalidation_conditions=invalidation_conditions,
            narrative_strength=confluence.narrative_strength,
            overall_score=overall_score
        )
    
    def _calculate_atr(self, bars: List[Dict[str, Any]], period: int = 14) -> float:
        """Calculate Average True Range"""
        if len(bars) < period + 1:
            return 0.001
        
        true_ranges = []
        for i in range(1, min(len(bars), period + 1)):
            high = bars[-i]["high"]
            low = bars[-i]["low"]
            prev_close = bars[-i-1]["close"]
            
            tr = max(
                high - low,
                abs(high - prev_close),
                abs(low - prev_close)
            )
            true_ranges.append(tr)
        
        return sum(true_ranges) / len(true_ranges) if true_ranges else 0.001
    
    def _create_insufficient_data_analysis(self, bars: List[Dict[str, Any]]) -> WovenAnalysis:
        """Create analysis when there's insufficient data"""
        current_price = bars[-1]["close"] if bars else 0
        
        layer1 = Layer1Context(
            market_context=MarketContext.RANGING,
            regime_confidence=0.0,
            current_session="unknown",
            session_quality="poor",
            news_risk=False,
            risk_sentiment="neutral",
            dxy_bias="neutral",
            correlated_assets_agree=False,
            look_for_longs=False,
            look_for_shorts=False,
            expect_reversal=False,
            expect_continuation=False,
            context_confidence=0.0
        )
        
        layer2 = Layer2Structure(
            has_bullish_ob=False,
            has_bearish_ob=False,
            ob_price=None,
            ob_strength=0.0,
            has_bullish_fvg=False,
            has_bearish_fvg=False,
            fvg_price=None,
            liquidity_above=None,
            liquidity_below=None,
            swing_count=0,
            ready_for_reversal=False,
            swing_direction="unclear",
            previous_range_broken=False,
            poc_price=current_price,
            vah_price=current_price,
            val_price=current_price,
            price_vs_value="at_value",
            volume_confluence_price=None,
            structure_bias="neutral",
            structure_confidence=0.0,
            key_level_to_watch=current_price,
            invalidation_level=current_price
        )
        
        layer3 = Layer3Flow(
            institutional_activity="neutral",
            smart_money_direction="neutral",
            iceberg_detected=False,
            iceberg_direction=None,
            volume_confirms_structure=False,
            signal_candle_detected=False,
            signal_candle_type=None,
            volume_at_key_level=False,
            trap_detected=False,
            trap_direction=None,
            absorption_detected=False,
            absorption_direction=None,
            flow_confirms_structure=FlowConfirmation.NEUTRAL,
            flow_confidence=0.0
        )
        
        layer4 = Layer4Confluence(
            context_structure_align=False,
            structure_flow_align=False,
            all_layers_align=False,
            narrative_strength=NarrativeStrength.CONTRADICTORY,
            narrative_text="Insufficient data for analysis.",
            confluence_score=0.0,
            conflicts=["Insufficient data"],
            is_valid_setup=False,
            validation_reasons=[]
        )
        
        decision = WovenDecision(
            direction="NO_TRADE",
            confidence=0.0,
            entry_price=current_price,
            stop_loss=current_price,
            take_profit_1=current_price,
            take_profit_2=current_price,
            take_profit_3=current_price,
            narrative="Insufficient data for analysis. Need at least 50 bars.",
            context_summary="Insufficient data",
            structure_summary="Insufficient data",
            flow_summary="Insufficient data",
            confluence_summary="Insufficient data",
            warnings=["Insufficient data for analysis"],
            invalidation_conditions=[],
            narrative_strength=NarrativeStrength.CONTRADICTORY,
            overall_score=0.0
        )
        
        return WovenAnalysis(
            layer1=layer1,
            layer2=layer2,
            layer3=layer3,
            layer4=layer4,
            decision=decision,
            raw_signals={}
        )


def test_woven_intelligence():
    """Test the Woven Intelligence system"""
    import json
    
    # Load test data
    with open("/home/ubuntu/omega_devin/data/replay_data.json", "r") as f:
        bars = json.load(f)
    
    print("=" * 80)
    print("WOVEN INTELLIGENCE TEST")
    print("=" * 80)
    
    # Initialize
    woven = WovenIntelligence(account_balance=10000)
    
    # Analyze with 200 bars
    test_bars = bars[:200]
    analysis = woven.analyze(test_bars)
    
    # Print full narrative
    print(analysis.get_full_narrative())
    
    return analysis


if __name__ == "__main__":
    test_woven_intelligence()
