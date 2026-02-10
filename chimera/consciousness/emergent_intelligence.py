"""
EMERGENT INTELLIGENCE ENGINE
============================

This is NOT a voting system. This is TRUE REASONING.

The difference:
- Voting: "SMC says SHORT, VPE says SHORT, therefore SHORT" (counting signals)
- Reasoning: "Price broke the bullish OB BECAUSE institutions distributed, 
              WHICH CAUSED trapped longs to panic, WHICH IS CONFIRMED BY 
              the absorption candle, THEREFORE we expect continuation to 1.1800"

Key Components:
1. CAUSAL REASONING CHAINS - Each insight builds on the previous
2. HYPOTHESIS GENERATION - Generate theories and test them
3. NARRATIVE CONSTRUCTION - Build coherent market stories
4. SELF-QUESTIONING - Ask "What would invalidate my thesis?"
5. MULTI-SCALE COHERENCE - All timeframes tell one story

"The market is a story. Your job is to read it." - Prince
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple, Any
from enum import Enum
import json

# Import IcebergType for checking
from chimera.consciousness.institutional_flow_detection import IcebergType


class MarketPhase(Enum):
    """What phase is the market in?"""
    ACCUMULATION = "accumulation"  # Smart money buying quietly
    MARKUP = "markup"  # Price rising after accumulation
    DISTRIBUTION = "distribution"  # Smart money selling quietly
    MARKDOWN = "markdown"  # Price falling after distribution
    RANGING = "ranging"  # No clear phase
    UNKNOWN = "unknown"


class CausalRelation(Enum):
    """Types of causal relationships"""
    CAUSED_BY = "caused_by"  # X was caused by Y
    RESULTED_IN = "resulted_in"  # X resulted in Y
    CONFIRMED_BY = "confirmed_by"  # X is confirmed by Y
    INVALIDATED_BY = "invalidated_by"  # X is invalidated by Y
    IMPLIES = "implies"  # X implies Y
    CONTRADICTS = "contradicts"  # X contradicts Y


class HypothesisStatus(Enum):
    """Status of a hypothesis"""
    PENDING = "pending"  # Not yet tested
    CONFIRMED = "confirmed"  # Evidence supports it
    INVALIDATED = "invalidated"  # Evidence contradicts it
    UNCERTAIN = "uncertain"  # Mixed evidence


class NarrativeClarity(Enum):
    """How clear is the market narrative?"""
    CRYSTAL_CLEAR = "crystal_clear"  # Everything aligns perfectly
    CLEAR = "clear"  # Strong alignment with minor noise
    MODERATE = "moderate"  # Some alignment, some conflict
    MURKY = "murky"  # Conflicting signals
    CHAOS = "chaos"  # No coherent narrative


@dataclass
class CausalLink:
    """A single link in a causal reasoning chain"""
    observation: str  # What we observed
    cause: str  # What caused it
    effect: str  # What it implies
    relation: CausalRelation
    confidence: float  # 0-1
    evidence: List[str]  # Supporting evidence
    
    def to_narrative(self) -> str:
        """Convert to human-readable narrative"""
        if self.relation == CausalRelation.CAUSED_BY:
            return f"{self.observation} was CAUSED BY {self.cause}"
        elif self.relation == CausalRelation.RESULTED_IN:
            return f"{self.observation} RESULTED IN {self.effect}"
        elif self.relation == CausalRelation.CONFIRMED_BY:
            return f"{self.observation} is CONFIRMED BY {self.evidence[0] if self.evidence else 'evidence'}"
        elif self.relation == CausalRelation.IMPLIES:
            return f"{self.observation} IMPLIES {self.effect}"
        elif self.relation == CausalRelation.CONTRADICTS:
            return f"{self.observation} CONTRADICTS {self.effect}"
        return f"{self.observation}"


@dataclass
class CausalChain:
    """A complete causal reasoning chain"""
    links: List[CausalLink]
    conclusion: str
    overall_confidence: float
    
    def to_narrative(self) -> str:
        """Convert entire chain to narrative"""
        if not self.links:
            return "No causal chain established."
        
        parts = []
        for i, link in enumerate(self.links):
            if i == 0:
                parts.append(link.to_narrative())
            else:
                # Connect with "WHICH" for flow
                parts.append(f"WHICH {link.to_narrative().lower()}")
        
        parts.append(f"THEREFORE: {self.conclusion}")
        return " ".join(parts)


@dataclass
class Hypothesis:
    """A market hypothesis to be tested"""
    id: str
    statement: str  # "Smart money is accumulating for a move up"
    confirmation_criteria: List[str]  # What would confirm this
    invalidation_criteria: List[str]  # What would invalidate this
    status: HypothesisStatus
    confidence: float
    evidence_for: List[str]
    evidence_against: List[str]
    created_at_bar: int
    last_updated_bar: int
    
    def evaluate(self, new_evidence: Dict[str, Any]) -> HypothesisStatus:
        """Evaluate hypothesis against new evidence"""
        # Count confirmations and invalidations
        confirmations = 0
        invalidations = 0
        
        for criteria in self.confirmation_criteria:
            if self._check_criteria(criteria, new_evidence):
                confirmations += 1
                self.evidence_for.append(f"Confirmed: {criteria}")
        
        for criteria in self.invalidation_criteria:
            if self._check_criteria(criteria, new_evidence):
                invalidations += 1
                self.evidence_against.append(f"Invalidated: {criteria}")
        
        # Update status
        if invalidations > 0:
            self.status = HypothesisStatus.INVALIDATED
            self.confidence = max(0, self.confidence - 0.3)
        elif confirmations > 0:
            self.status = HypothesisStatus.CONFIRMED
            self.confidence = min(1.0, self.confidence + 0.2)
        else:
            self.status = HypothesisStatus.UNCERTAIN
        
        return self.status
    
    def _check_criteria(self, criteria: str, evidence: Dict[str, Any]) -> bool:
        """Check if criteria is met by evidence"""
        # This is simplified - in production would use more sophisticated matching
        criteria_lower = criteria.lower()
        
        # Check for price breaks
        if "price breaks above" in criteria_lower:
            level = self._extract_level(criteria)
            if level and evidence.get("current_price", 0) > level:
                return True
        
        if "price breaks below" in criteria_lower:
            level = self._extract_level(criteria)
            if level and evidence.get("current_price", 0) < level:
                return True
        
        # Check for absorption
        if "absorption" in criteria_lower:
            if evidence.get("absorption_detected"):
                return True
        
        # Check for volume
        if "high volume" in criteria_lower:
            if evidence.get("volume_spike"):
                return True
        
        return False
    
    def _extract_level(self, criteria: str) -> Optional[float]:
        """Extract price level from criteria string"""
        import re
        match = re.search(r'(\d+\.?\d*)', criteria)
        if match:
            return float(match.group(1))
        return None


@dataclass
class MarketNarrative:
    """A complete market narrative"""
    phase: MarketPhase
    story: str  # Human-readable story
    key_players: List[str]  # Who's doing what (smart money, retail, etc.)
    key_levels: Dict[str, float]  # Important price levels
    expected_move: str  # What we expect to happen
    invalidation: str  # What would invalidate this narrative
    clarity: NarrativeClarity
    confidence: float
    
    def to_full_narrative(self) -> str:
        """Generate complete narrative"""
        return f"""
MARKET NARRATIVE ({self.clarity.value.upper()})
{'='*60}

PHASE: {self.phase.value.upper()}

STORY:
{self.story}

KEY PLAYERS:
{chr(10).join(f'  - {player}' for player in self.key_players)}

KEY LEVELS:
{chr(10).join(f'  - {name}: {level:.5f}' for name, level in self.key_levels.items())}

EXPECTED MOVE:
{self.expected_move}

INVALIDATION:
{self.invalidation}

CONFIDENCE: {self.confidence*100:.0f}%
"""


@dataclass
class SelfQuestion:
    """A question the system asks itself"""
    question: str
    answer: str
    confidence: float
    implications: List[str]


@dataclass
class EmergentAnalysis:
    """Complete emergent intelligence analysis"""
    # Causal reasoning
    causal_chain: CausalChain
    
    # Hypotheses
    active_hypotheses: List[Hypothesis]
    confirmed_hypotheses: List[Hypothesis]
    invalidated_hypotheses: List[Hypothesis]
    
    # Narrative
    narrative: MarketNarrative
    
    # Self-questioning
    self_questions: List[SelfQuestion]
    
    # Decision
    direction: str  # "LONG", "SHORT", "NO_TRADE"
    confidence: float
    entry_price: float
    stop_loss: float
    take_profit_1: float
    take_profit_2: float
    take_profit_3: float
    
    # Reasoning
    reasoning_chain: str  # Full reasoning in narrative form
    warnings: List[str]
    
    def get_full_analysis(self) -> str:
        """Get complete analysis as narrative"""
        output = []
        
        output.append("=" * 80)
        output.append("EMERGENT INTELLIGENCE ANALYSIS")
        output.append("=" * 80)
        
        # Causal Chain
        output.append("\n" + "-" * 40)
        output.append("CAUSAL REASONING CHAIN")
        output.append("-" * 40)
        output.append(self.causal_chain.to_narrative())
        
        # Narrative
        output.append(self.narrative.to_full_narrative())
        
        # Self-Questions
        output.append("-" * 40)
        output.append("SELF-QUESTIONING")
        output.append("-" * 40)
        for q in self.self_questions:
            output.append(f"Q: {q.question}")
            output.append(f"A: {q.answer}")
            output.append(f"   Confidence: {q.confidence*100:.0f}%")
            output.append("")
        
        # Decision
        output.append("-" * 40)
        output.append("DECISION")
        output.append("-" * 40)
        output.append(f"Direction: {self.direction}")
        output.append(f"Confidence: {self.confidence*100:.0f}%")
        output.append(f"Entry: {self.entry_price:.5f}")
        output.append(f"Stop Loss: {self.stop_loss:.5f}")
        output.append(f"TP1: {self.take_profit_1:.5f}")
        output.append(f"TP2: {self.take_profit_2:.5f}")
        output.append(f"TP3: {self.take_profit_3:.5f}")
        
        if self.warnings:
            output.append("\nWARNINGS:")
            for w in self.warnings:
                output.append(f"  - {w}")
        
        output.append("=" * 80)
        
        return "\n".join(output)


class EmergentIntelligence:
    """
    TRUE EMERGENT INTELLIGENCE ENGINE
    
    This is not a voting system. This is a REASONING system.
    
    It builds causal chains, generates hypotheses, constructs narratives,
    and questions itself before making decisions.
    
    "The difference between a good trader and a great trader is not
    what they see, but how they THINK about what they see." - Prince
    """
    
    def __init__(self):
        """Initialize the Emergent Intelligence Engine"""
        # Import all intelligence modules
        from chimera.consciousness.smc_intelligence import SMCIntelligence
        from chimera.consciousness.fractal_swing_intelligence import FractalSwingIntelligence
        from chimera.consciousness.multi_profile_volume_intelligence import MultiProfileVolumeIntelligence
        from chimera.consciousness.vpe_intelligence import VPEIntelligence
        from chimera.consciousness.manipulation_candle_intelligence import ManipulationCandleIntelligence
        from chimera.consciousness.institutional_flow_detection import InstitutionalFlowDetection
        from chimera.consciousness.cross_asset_correlation import CrossAssetCorrelationIntelligence
        from chimera.consciousness.adaptive_regime import AdaptiveRegimeIntelligence
        from chimera.consciousness.session_trade_management import SessionTradeManagementIntelligence
        
        # Initialize modules
        self.smc = SMCIntelligence()
        self.fractal = FractalSwingIntelligence()
        self.multi_profile = MultiProfileVolumeIntelligence()
        self.vpe = VPEIntelligence()
        self.manipulation = ManipulationCandleIntelligence()
        self.institutional = InstitutionalFlowDetection()
        self.cross_asset = CrossAssetCorrelationIntelligence()
        self.regime = AdaptiveRegimeIntelligence()
        self.session = SessionTradeManagementIntelligence()
        
        # Active hypotheses
        self.hypotheses: List[Hypothesis] = []
        self.hypothesis_counter = 0
    
    def analyze(self, bars: List[Dict[str, Any]]) -> EmergentAnalysis:
        """
        Perform EMERGENT analysis - not voting, but REASONING
        
        This method:
        1. Gathers observations from all modules
        2. Builds causal reasoning chains
        3. Generates and tests hypotheses
        4. Constructs a market narrative
        5. Questions itself
        6. Makes a reasoned decision
        """
        if len(bars) < 50:
            return self._insufficient_data_analysis(bars)
        
        current_price = bars[-1]["close"]
        current_bar = len(bars) - 1
        
        # STEP 1: Gather raw observations from all modules
        observations = self._gather_observations(bars)
        
        # STEP 2: Build causal reasoning chain
        causal_chain = self._build_causal_chain(observations, bars)
        
        # STEP 3: Generate and test hypotheses
        self._generate_hypotheses(observations, current_bar)
        self._test_hypotheses(observations, current_bar)
        
        # STEP 4: Construct market narrative
        narrative = self._construct_narrative(observations, causal_chain)
        
        # STEP 5: Self-questioning
        self_questions = self._self_question(observations, narrative, causal_chain)
        
        # STEP 6: Make reasoned decision
        direction, confidence, entry, sl, tp1, tp2, tp3, warnings = self._make_decision(
            observations, causal_chain, narrative, self_questions, bars
        )
        
        # Build reasoning chain narrative
        reasoning_chain = self._build_reasoning_narrative(
            observations, causal_chain, narrative, self_questions, direction
        )
        
        return EmergentAnalysis(
            causal_chain=causal_chain,
            active_hypotheses=[h for h in self.hypotheses if h.status == HypothesisStatus.PENDING],
            confirmed_hypotheses=[h for h in self.hypotheses if h.status == HypothesisStatus.CONFIRMED],
            invalidated_hypotheses=[h for h in self.hypotheses if h.status == HypothesisStatus.INVALIDATED],
            narrative=narrative,
            self_questions=self_questions,
            direction=direction,
            confidence=confidence,
            entry_price=entry,
            stop_loss=sl,
            take_profit_1=tp1,
            take_profit_2=tp2,
            take_profit_3=tp3,
            reasoning_chain=reasoning_chain,
            warnings=warnings
        )
    
    def _gather_observations(self, bars: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Gather observations from all intelligence modules"""
        observations = {}
        
        # SMC Analysis
        smc_analysis = self.smc.analyze(bars)
        bullish_zones = smc_analysis.get_bullish_zones()
        bearish_zones = smc_analysis.get_bearish_zones()
        observations["smc"] = {
            "bullish_ob": smc_analysis.nearest_demand,
            "bearish_ob": smc_analysis.nearest_supply,
            "liquidity_pools": smc_analysis.liquidity_pools,
            "order_blocks": smc_analysis.order_blocks,
            "bias": smc_analysis.bias.value,
            "bias_strength": smc_analysis.bias_strength,
            "signal": "LONG" if smc_analysis.bias.value == "bullish" else ("SHORT" if smc_analysis.bias.value == "bearish" else "NEUTRAL"),
            "signal_strength": smc_analysis.bias_strength
        }
        
        # Fractal Swing Analysis
        fractal_analysis = self.fractal.analyze(bars)
        swing_highs = [s for s in fractal_analysis.swings if s.is_high]
        swing_lows = [s for s in fractal_analysis.swings if not s.is_high]
        observations["fractal"] = {
            "swing_highs": len(swing_highs),
            "swing_lows": len(swing_lows),
            "swing_count": fractal_analysis.swing_count,
            "swing_direction": fractal_analysis.swing_direction.value,
            "previous_range": fractal_analysis.previous_range,
            "signal": fractal_analysis.signal,
            "signal_strength": fractal_analysis.signal_strength
        }
        
        # Multi-Profile Volume Analysis
        multi_profile = self.multi_profile.analyze(bars)
        observations["volume_profile"] = {
            "poc": multi_profile.session.poc if multi_profile.session else bars[-1]["close"],
            "vah": multi_profile.session.vah if multi_profile.session else bars[-1]["close"] * 1.001,
            "val": multi_profile.session.val if multi_profile.session else bars[-1]["close"] * 0.999,
            "signal": multi_profile.signal,
            "signal_strength": multi_profile.signal_strength
        }
        
        # VPE Analysis
        vpe_analysis = self.vpe.analyze(bars)
        observations["vpe"] = {
            "market_bias": vpe_analysis.market_bias,
            "current_zone": vpe_analysis.current_zone,
            "signal_candles": len(vpe_analysis.signal_candles) if vpe_analysis.signal_candles else 0,
            "trade_setup": vpe_analysis.trade_setup
        }
        
        # Manipulation Analysis
        manipulation = self.manipulation.analyze(bars)
        observations["manipulation"] = {
            "trap_detected": manipulation.trap_detected,
            "trap_direction": manipulation.trap_direction,
            "absorption_zones": len(manipulation.absorption_zones) if manipulation.absorption_zones else 0,
            "delta_direction": manipulation.delta_direction.value,
            "signal": manipulation.signal,
            "signal_strength": manipulation.signal_strength
        }
        
        # Institutional Flow
        institutional = self.institutional.analyze(bars)
        observations["institutional"] = {
            "activity": institutional.current_activity.value,
            "iceberg_detected": institutional.iceberg_detected != IcebergType.NONE if hasattr(institutional, 'iceberg_detected') else False,
            "iceberg_direction": institutional.smart_money_direction,
            "smart_money_direction": institutional.smart_money_direction,
            "signal": institutional.smart_money_direction,
            "signal_strength": institutional.activity_confidence
        }
        
        # Cross-Asset Correlation
        cross_asset = self.cross_asset.analyze("EURUSD", bars)
        observations["cross_asset"] = {
            "risk_sentiment": cross_asset.risk_sentiment.sentiment.value,
            "dxy_impact": cross_asset.dxy_impact.dxy_direction.lower() if cross_asset.dxy_impact else "neutral",
            "signal_strength": cross_asset.signal_strength
        }
        
        # Regime Detection
        regime = self.regime.analyze(bars)
        observations["regime"] = {
            "regime": regime.current_regime.value,
            "confidence": regime.regime_confidence,
            "volatility": regime.volatility_state.value
        }
        
        # Session Analysis
        session = self.session.analyze(bars)
        observations["session"] = {
            "current_session": session.session_info.current_session.value,
            "session_quality": session.session_info.session_quality.value,
            "time_to_close": session.session_info.time_until_next_session
        }
        
        # Current price info
        observations["current_price"] = bars[-1]["close"]
        observations["current_high"] = bars[-1]["high"]
        observations["current_low"] = bars[-1]["low"]
        
        return observations
    
    def _build_causal_chain(self, observations: Dict[str, Any], bars: List[Dict[str, Any]]) -> CausalChain:
        """Build a causal reasoning chain from observations"""
        links = []
        
        # Start with regime context
        regime = observations["regime"]["regime"]
        regime_confidence = observations["regime"]["confidence"]
        
        if regime in ["strong_trend_up", "weak_trend_up"]:
            links.append(CausalLink(
                observation=f"Market is in {regime} regime",
                cause="Sustained buying pressure over multiple sessions",
                effect="Higher probability of continuation moves",
                relation=CausalRelation.IMPLIES,
                confidence=regime_confidence,
                evidence=[f"Regime confidence: {regime_confidence*100:.0f}%"]
            ))
        elif regime in ["strong_trend_down", "weak_trend_down"]:
            links.append(CausalLink(
                observation=f"Market is in {regime} regime",
                cause="Sustained selling pressure over multiple sessions",
                effect="Higher probability of continuation moves",
                relation=CausalRelation.IMPLIES,
                confidence=regime_confidence,
                evidence=[f"Regime confidence: {regime_confidence*100:.0f}%"]
            ))
        
        # Add institutional activity
        inst_activity = observations["institutional"]["activity"]
        smart_money = observations["institutional"]["smart_money_direction"]
        
        if inst_activity == "accumulating":
            links.append(CausalLink(
                observation="Institutional accumulation detected",
                cause="Smart money building positions quietly",
                effect="Expect markup phase to follow",
                relation=CausalRelation.IMPLIES,
                confidence=observations["institutional"]["signal_strength"],
                evidence=[f"Smart money direction: {smart_money}"]
            ))
        elif inst_activity == "distributing":
            links.append(CausalLink(
                observation="Institutional distribution detected",
                cause="Smart money offloading positions",
                effect="Expect markdown phase to follow",
                relation=CausalRelation.IMPLIES,
                confidence=observations["institutional"]["signal_strength"],
                evidence=[f"Smart money direction: {smart_money}"]
            ))
        
        # Add SMC structure
        smc = observations["smc"]
        if smc["bullish_ob"]:
            links.append(CausalLink(
                observation="Bullish order block identified",
                cause="Previous institutional buying created demand zone",
                effect="Price likely to react at this level",
                relation=CausalRelation.CAUSED_BY,
                confidence=smc["signal_strength"],
                evidence=["Order block from previous session"]
            ))
        elif smc["bearish_ob"]:
            links.append(CausalLink(
                observation="Bearish order block identified",
                cause="Previous institutional selling created supply zone",
                effect="Price likely to react at this level",
                relation=CausalRelation.CAUSED_BY,
                confidence=smc["signal_strength"],
                evidence=["Order block from previous session"]
            ))
        
        # Add manipulation/trap detection
        manip = observations["manipulation"]
        if manip["trap_detected"]:
            trap_dir = manip["trap_direction"]
            links.append(CausalLink(
                observation=f"Trap detected: {trap_dir} traders trapped",
                cause="Smart money engineered liquidity grab",
                effect="Expect reversal as trapped traders exit",
                relation=CausalRelation.RESULTED_IN,
                confidence=manip["signal_strength"],
                evidence=[f"Delta direction: {manip['delta_direction']}"]
            ))
        
        # Add volume confirmation
        vpe = observations["vpe"]
        if vpe["signal_candles"] > 0:
            links.append(CausalLink(
                observation=f"{vpe['signal_candles']} signal candle(s) detected",
                cause="High volume reaction at key level",
                effect="Confirms institutional interest at this price",
                relation=CausalRelation.CONFIRMED_BY,
                confidence=0.7,
                evidence=[f"Market bias: {vpe['market_bias']}"]
            ))
        
        # Build conclusion
        conclusion = self._derive_conclusion(observations, links)
        
        # Calculate overall confidence
        if links:
            overall_confidence = sum(l.confidence for l in links) / len(links)
        else:
            overall_confidence = 0.3
        
        return CausalChain(
            links=links,
            conclusion=conclusion,
            overall_confidence=overall_confidence
        )
    
    def _derive_conclusion(self, observations: Dict[str, Any], links: List[CausalLink]) -> str:
        """Derive a conclusion from the causal chain"""
        bullish_evidence = 0
        bearish_evidence = 0
        
        # Count directional evidence
        if observations["smc"]["signal"] == "LONG":
            bullish_evidence += 1
        elif observations["smc"]["signal"] == "SHORT":
            bearish_evidence += 1
        
        if observations["fractal"]["signal"] == "LONG":
            bullish_evidence += 1
        elif observations["fractal"]["signal"] == "SHORT":
            bearish_evidence += 1
        
        if observations["institutional"]["activity"] == "accumulating":
            bullish_evidence += 2
        elif observations["institutional"]["activity"] == "distributing":
            bearish_evidence += 2
        
        if observations["manipulation"]["trap_direction"] == "SHORT":
            bullish_evidence += 1
        elif observations["manipulation"]["trap_direction"] == "LONG":
            bearish_evidence += 1
        
        if observations["vpe"]["market_bias"] == "bullish":
            bullish_evidence += 1
        elif observations["vpe"]["market_bias"] == "bearish":
            bearish_evidence += 1
        
        # Derive conclusion
        if bullish_evidence > bearish_evidence + 2:
            return "Strong bullish setup - expect continuation higher"
        elif bullish_evidence > bearish_evidence:
            return "Moderate bullish bias - look for long entries on pullbacks"
        elif bearish_evidence > bullish_evidence + 2:
            return "Strong bearish setup - expect continuation lower"
        elif bearish_evidence > bullish_evidence:
            return "Moderate bearish bias - look for short entries on rallies"
        else:
            return "Mixed signals - wait for clarity before taking positions"
    
    def _generate_hypotheses(self, observations: Dict[str, Any], current_bar: int):
        """Generate new hypotheses based on observations"""
        current_price = observations["current_price"]
        
        # Hypothesis: Accumulation leading to markup
        if observations["institutional"]["activity"] == "accumulating":
            self.hypothesis_counter += 1
            self.hypotheses.append(Hypothesis(
                id=f"H{self.hypothesis_counter}",
                statement="Smart money is accumulating for a move up",
                confirmation_criteria=[
                    "Price breaks above recent swing high",
                    "Absorption at value area low",
                    "Bullish delta divergence"
                ],
                invalidation_criteria=[
                    f"Price breaks below {current_price * 0.995:.5f}",
                    "Distribution pattern emerges",
                    "Strong bearish absorption"
                ],
                status=HypothesisStatus.PENDING,
                confidence=0.6,
                evidence_for=["Institutional accumulation detected"],
                evidence_against=[],
                created_at_bar=current_bar,
                last_updated_bar=current_bar
            ))
        
        # Hypothesis: Distribution leading to markdown
        if observations["institutional"]["activity"] == "distributing":
            self.hypothesis_counter += 1
            self.hypotheses.append(Hypothesis(
                id=f"H{self.hypothesis_counter}",
                statement="Smart money is distributing for a move down",
                confirmation_criteria=[
                    "Price breaks below recent swing low",
                    "Absorption at value area high",
                    "Bearish delta divergence"
                ],
                invalidation_criteria=[
                    f"Price breaks above {current_price * 1.005:.5f}",
                    "Accumulation pattern emerges",
                    "Strong bullish absorption"
                ],
                status=HypothesisStatus.PENDING,
                confidence=0.6,
                evidence_for=["Institutional distribution detected"],
                evidence_against=[],
                created_at_bar=current_bar,
                last_updated_bar=current_bar
            ))
        
        # Hypothesis: Trap reversal
        if observations["manipulation"]["trap_detected"]:
            trap_dir = observations["manipulation"]["trap_direction"]
            self.hypothesis_counter += 1
            
            if trap_dir == "LONG":
                self.hypotheses.append(Hypothesis(
                    id=f"H{self.hypothesis_counter}",
                    statement="Long trap will lead to bearish reversal",
                    confirmation_criteria=[
                        "Price fails to reclaim trap level",
                        "Bearish follow-through candle",
                        "Increasing selling volume"
                    ],
                    invalidation_criteria=[
                        "Price reclaims trap level with volume",
                        "Bullish absorption appears"
                    ],
                    status=HypothesisStatus.PENDING,
                    confidence=0.65,
                    evidence_for=["Long trap detected"],
                    evidence_against=[],
                    created_at_bar=current_bar,
                    last_updated_bar=current_bar
                ))
            else:
                self.hypotheses.append(Hypothesis(
                    id=f"H{self.hypothesis_counter}",
                    statement="Short trap will lead to bullish reversal",
                    confirmation_criteria=[
                        "Price fails to break trap level",
                        "Bullish follow-through candle",
                        "Increasing buying volume"
                    ],
                    invalidation_criteria=[
                        "Price breaks trap level with volume",
                        "Bearish absorption appears"
                    ],
                    status=HypothesisStatus.PENDING,
                    confidence=0.65,
                    evidence_for=["Short trap detected"],
                    evidence_against=[],
                    created_at_bar=current_bar,
                    last_updated_bar=current_bar
                ))
        
        # Limit active hypotheses
        self.hypotheses = self.hypotheses[-10:]  # Keep last 10
    
    def _test_hypotheses(self, observations: Dict[str, Any], current_bar: int):
        """Test existing hypotheses against new observations"""
        evidence = {
            "current_price": observations["current_price"],
            "absorption_detected": observations["manipulation"]["absorption_zones"] > 0,
            "volume_spike": observations["vpe"]["signal_candles"] > 0,
            "institutional_activity": observations["institutional"]["activity"],
            "delta_direction": observations["manipulation"]["delta_direction"]
        }
        
        for hypothesis in self.hypotheses:
            if hypothesis.status == HypothesisStatus.PENDING:
                hypothesis.evaluate(evidence)
                hypothesis.last_updated_bar = current_bar
    
    def _construct_narrative(self, observations: Dict[str, Any], causal_chain: CausalChain) -> MarketNarrative:
        """Construct a coherent market narrative"""
        # Determine market phase
        inst_activity = observations["institutional"]["activity"]
        regime = observations["regime"]["regime"]
        
        if inst_activity == "accumulating":
            phase = MarketPhase.ACCUMULATION
        elif inst_activity == "distributing":
            phase = MarketPhase.DISTRIBUTION
        elif regime in ["strong_trend_up", "weak_trend_up"]:
            phase = MarketPhase.MARKUP
        elif regime in ["strong_trend_down", "weak_trend_down"]:
            phase = MarketPhase.MARKDOWN
        else:
            phase = MarketPhase.RANGING
        
        # Build story
        story = self._build_story(observations, phase, causal_chain)
        
        # Identify key players
        key_players = []
        if observations["institutional"]["iceberg_detected"]:
            key_players.append(f"Iceberg orders detected ({observations['institutional']['iceberg_direction']})")
        if observations["manipulation"]["trap_detected"]:
            key_players.append(f"Trapped {observations['manipulation']['trap_direction']} traders")
        if inst_activity != "neutral":
            key_players.append(f"Smart money {inst_activity}")
        if not key_players:
            key_players.append("No clear institutional activity")
        
        # Key levels
        key_levels = {
            "POC": observations["volume_profile"]["poc"],
            "VAH": observations["volume_profile"]["vah"],
            "VAL": observations["volume_profile"]["val"],
            "Current": observations["current_price"]
        }
        
        if observations["smc"]["bullish_ob"]:
            key_levels["Bullish OB"] = observations["smc"]["bullish_ob"].bottom
        if observations["smc"]["bearish_ob"]:
            key_levels["Bearish OB"] = observations["smc"]["bearish_ob"].top
        
        # Expected move
        expected_move = self._determine_expected_move(observations, phase)
        
        # Invalidation
        invalidation = self._determine_invalidation(observations, phase)
        
        # Clarity
        clarity = self._assess_clarity(observations, causal_chain)
        
        return MarketNarrative(
            phase=phase,
            story=story,
            key_players=key_players,
            key_levels=key_levels,
            expected_move=expected_move,
            invalidation=invalidation,
            clarity=clarity,
            confidence=causal_chain.overall_confidence
        )
    
    def _build_story(self, observations: Dict[str, Any], phase: MarketPhase, causal_chain: CausalChain) -> str:
        """Build a human-readable market story"""
        session = observations["session"]["current_session"]
        regime = observations["regime"]["regime"]
        inst_activity = observations["institutional"]["activity"]
        
        story_parts = []
        
        # Opening
        story_parts.append(f"During the {session} session, the market is in a {phase.value} phase.")
        
        # Institutional activity
        if inst_activity == "accumulating":
            story_parts.append("Smart money appears to be quietly building long positions.")
        elif inst_activity == "distributing":
            story_parts.append("Smart money appears to be offloading positions to retail.")
        
        # Trap activity
        if observations["manipulation"]["trap_detected"]:
            trap_dir = observations["manipulation"]["trap_direction"]
            story_parts.append(f"A {trap_dir.lower()} trap was detected, suggesting a reversal is likely.")
        
        # Volume profile context
        current_zone = observations["vpe"]["current_zone"]
        story_parts.append(f"Price is currently in the {current_zone} zone of the volume profile.")
        
        # Conclusion from causal chain
        story_parts.append(causal_chain.conclusion)
        
        return " ".join(story_parts)
    
    def _determine_expected_move(self, observations: Dict[str, Any], phase: MarketPhase) -> str:
        """Determine expected market move"""
        current_price = observations["current_price"]
        poc = observations["volume_profile"]["poc"]
        vah = observations["volume_profile"]["vah"]
        val = observations["volume_profile"]["val"]
        
        if phase == MarketPhase.ACCUMULATION:
            return f"Expect markup to begin. Target: {vah:.5f} (VAH), then higher."
        elif phase == MarketPhase.DISTRIBUTION:
            return f"Expect markdown to begin. Target: {val:.5f} (VAL), then lower."
        elif phase == MarketPhase.MARKUP:
            return f"Expect continuation higher. Look for pullbacks to {poc:.5f} (POC) for entries."
        elif phase == MarketPhase.MARKDOWN:
            return f"Expect continuation lower. Look for rallies to {poc:.5f} (POC) for entries."
        else:
            return f"Expect ranging between {val:.5f} and {vah:.5f}. Trade the edges."
    
    def _determine_invalidation(self, observations: Dict[str, Any], phase: MarketPhase) -> str:
        """Determine what would invalidate the current narrative"""
        current_price = observations["current_price"]
        val = observations["volume_profile"]["val"]
        vah = observations["volume_profile"]["vah"]
        
        if phase in [MarketPhase.ACCUMULATION, MarketPhase.MARKUP]:
            return f"Narrative invalidated if price breaks below {val:.5f} with conviction."
        elif phase in [MarketPhase.DISTRIBUTION, MarketPhase.MARKDOWN]:
            return f"Narrative invalidated if price breaks above {vah:.5f} with conviction."
        else:
            return "Narrative invalidated if clear trend emerges with institutional confirmation."
    
    def _assess_clarity(self, observations: Dict[str, Any], causal_chain: CausalChain) -> NarrativeClarity:
        """Assess how clear the market narrative is"""
        # Count aligned signals
        aligned = 0
        conflicting = 0
        
        # Check if signals align
        smc_signal = observations["smc"]["signal"]
        fractal_signal = observations["fractal"]["signal"]
        manip_signal = observations["manipulation"]["signal"]
        vpe_bias = observations["vpe"]["market_bias"]
        
        signals = [smc_signal, fractal_signal, manip_signal]
        bullish_count = sum(1 for s in signals if s == "LONG")
        bearish_count = sum(1 for s in signals if s == "SHORT")
        
        if bullish_count >= 2 or bearish_count >= 2:
            aligned += 1
        else:
            conflicting += 1
        
        # Check institutional alignment
        inst_activity = observations["institutional"]["activity"]
        if inst_activity == "accumulating" and bullish_count > bearish_count:
            aligned += 1
        elif inst_activity == "distributing" and bearish_count > bullish_count:
            aligned += 1
        elif inst_activity != "neutral":
            conflicting += 1
        
        # Assess clarity
        confidence = causal_chain.overall_confidence
        
        if aligned >= 2 and conflicting == 0 and confidence > 0.7:
            return NarrativeClarity.CRYSTAL_CLEAR
        elif aligned >= 1 and conflicting <= 1 and confidence > 0.5:
            return NarrativeClarity.CLEAR
        elif aligned >= 1:
            return NarrativeClarity.MODERATE
        elif conflicting >= 2:
            return NarrativeClarity.CHAOS
        else:
            return NarrativeClarity.MURKY
    
    def _self_question(
        self,
        observations: Dict[str, Any],
        narrative: MarketNarrative,
        causal_chain: CausalChain
    ) -> List[SelfQuestion]:
        """Ask critical questions before making a decision"""
        questions = []
        
        # Question 1: What is my thesis?
        questions.append(SelfQuestion(
            question="What is my thesis?",
            answer=causal_chain.conclusion,
            confidence=causal_chain.overall_confidence,
            implications=["This determines trade direction"]
        ))
        
        # Question 2: What evidence supports it?
        evidence = []
        for link in causal_chain.links:
            evidence.extend(link.evidence)
        questions.append(SelfQuestion(
            question="What evidence supports my thesis?",
            answer="; ".join(evidence) if evidence else "Limited evidence",
            confidence=causal_chain.overall_confidence,
            implications=["More evidence = higher confidence"]
        ))
        
        # Question 3: What would invalidate it?
        questions.append(SelfQuestion(
            question="What would invalidate my thesis?",
            answer=narrative.invalidation,
            confidence=0.8,
            implications=["This is my stop loss logic"]
        ))
        
        # Question 4: Am I seeing what I want to see?
        # Check for confirmation bias
        aligned_signals = 0
        total_signals = 0
        for key in ["smc", "fractal", "manipulation"]:
            if observations[key]["signal"] != "NEUTRAL":
                total_signals += 1
                if narrative.phase in [MarketPhase.ACCUMULATION, MarketPhase.MARKUP]:
                    if observations[key]["signal"] == "LONG":
                        aligned_signals += 1
                elif narrative.phase in [MarketPhase.DISTRIBUTION, MarketPhase.MARKDOWN]:
                    if observations[key]["signal"] == "SHORT":
                        aligned_signals += 1
        
        bias_check = "No" if total_signals > 0 and aligned_signals / total_signals < 0.8 else "Possibly"
        questions.append(SelfQuestion(
            question="Am I seeing what I want to see (confirmation bias)?",
            answer=f"{bias_check} - {aligned_signals}/{total_signals} signals align with narrative",
            confidence=0.7,
            implications=["Be aware of cognitive biases"]
        ))
        
        # Question 5: Is this the right time?
        session_quality = observations["session"]["session_quality"]
        questions.append(SelfQuestion(
            question="Is this the right time to trade?",
            answer=f"Session quality: {session_quality}",
            confidence=0.8 if session_quality in ["excellent", "good"] else 0.4,
            implications=["Poor session = higher risk of false signals"]
        ))
        
        return questions
    
    def _make_decision(
        self,
        observations: Dict[str, Any],
        causal_chain: CausalChain,
        narrative: MarketNarrative,
        self_questions: List[SelfQuestion],
        bars: List[Dict[str, Any]]
    ) -> Tuple[str, float, float, float, float, float, float, List[str]]:
        """Make a reasoned trading decision"""
        warnings = []
        current_price = bars[-1]["close"]
        atr = self._calculate_atr(bars)
        
        # Default values
        direction = "NO_TRADE"
        confidence = 0.0
        entry = current_price
        sl = current_price
        tp1 = current_price
        tp2 = current_price
        tp3 = current_price
        
        # Check narrative clarity
        if narrative.clarity == NarrativeClarity.CHAOS:
            warnings.append("Market narrative is chaotic - no trade")
            return direction, confidence, entry, sl, tp1, tp2, tp3, warnings
        
        if narrative.clarity == NarrativeClarity.MURKY:
            warnings.append("Market narrative is murky - reduced confidence")
        
        # Check session quality
        session_quality = observations["session"]["session_quality"]
        if session_quality in ["poor", "avoid"]:
            warnings.append(f"Session quality is {session_quality} - consider waiting")
        
        # Determine direction based on narrative and causal chain
        if narrative.phase in [MarketPhase.ACCUMULATION, MarketPhase.MARKUP]:
            if narrative.clarity in [NarrativeClarity.CRYSTAL_CLEAR, NarrativeClarity.CLEAR]:
                direction = "LONG"
                confidence = causal_chain.overall_confidence * 0.9
            elif narrative.clarity == NarrativeClarity.MODERATE:
                direction = "LONG"
                confidence = causal_chain.overall_confidence * 0.6
                warnings.append("Moderate clarity - use smaller position")
        
        elif narrative.phase in [MarketPhase.DISTRIBUTION, MarketPhase.MARKDOWN]:
            if narrative.clarity in [NarrativeClarity.CRYSTAL_CLEAR, NarrativeClarity.CLEAR]:
                direction = "SHORT"
                confidence = causal_chain.overall_confidence * 0.9
            elif narrative.clarity == NarrativeClarity.MODERATE:
                direction = "SHORT"
                confidence = causal_chain.overall_confidence * 0.6
                warnings.append("Moderate clarity - use smaller position")
        
        # Calculate levels
        if direction == "LONG":
            entry = current_price
            sl = current_price - atr * 1.5
            tp1 = current_price + atr * 1.0
            tp2 = current_price + atr * 2.0
            tp3 = current_price + atr * 3.0
            
            # Use key levels if available
            if observations["smc"]["bullish_ob"]:
                sl = min(sl, observations["smc"]["bullish_ob"].bottom - atr * 0.5)
            
            tp2 = max(tp2, observations["volume_profile"]["vah"])
        
        elif direction == "SHORT":
            entry = current_price
            sl = current_price + atr * 1.5
            tp1 = current_price - atr * 1.0
            tp2 = current_price - atr * 2.0
            tp3 = current_price - atr * 3.0
            
            # Use key levels if available
            if observations["smc"]["bearish_ob"]:
                sl = max(sl, observations["smc"]["bearish_ob"].top + atr * 0.5)
            
            tp2 = min(tp2, observations["volume_profile"]["val"])
        
        # Final confidence adjustment
        if confidence > 0:
            # Adjust for session quality
            if session_quality == "excellent":
                confidence *= 1.1
            elif session_quality == "poor":
                confidence *= 0.7
            
            # Cap confidence
            confidence = min(0.95, confidence)
        
        return direction, confidence, entry, sl, tp1, tp2, tp3, warnings
    
    def _build_reasoning_narrative(
        self,
        observations: Dict[str, Any],
        causal_chain: CausalChain,
        narrative: MarketNarrative,
        self_questions: List[SelfQuestion],
        direction: str
    ) -> str:
        """Build complete reasoning narrative"""
        parts = []
        
        parts.append("REASONING CHAIN:")
        parts.append("-" * 40)
        
        # Causal chain
        parts.append(causal_chain.to_narrative())
        parts.append("")
        
        # Narrative summary
        parts.append(f"NARRATIVE: {narrative.story}")
        parts.append("")
        
        # Self-questioning summary
        parts.append("SELF-CHECK:")
        for q in self_questions[:3]:  # Top 3 questions
            parts.append(f"  Q: {q.question}")
            parts.append(f"  A: {q.answer}")
        parts.append("")
        
        # Decision
        parts.append(f"DECISION: {direction}")
        if direction != "NO_TRADE":
            parts.append(f"EXPECTED MOVE: {narrative.expected_move}")
            parts.append(f"INVALIDATION: {narrative.invalidation}")
        
        return "\n".join(parts)
    
    def _calculate_atr(self, bars: List[Dict[str, Any]], period: int = 14) -> float:
        """Calculate Average True Range"""
        if len(bars) < period + 1:
            return 0.001
        
        tr_values = []
        for i in range(1, min(len(bars), period + 1)):
            high = bars[-i]["high"]
            low = bars[-i]["low"]
            prev_close = bars[-i-1]["close"]
            
            tr = max(
                high - low,
                abs(high - prev_close),
                abs(low - prev_close)
            )
            tr_values.append(tr)
        
        return sum(tr_values) / len(tr_values) if tr_values else 0.001
    
    def _insufficient_data_analysis(self, bars: List[Dict[str, Any]]) -> EmergentAnalysis:
        """Return analysis when insufficient data"""
        current_price = bars[-1]["close"] if bars else 1.0
        
        return EmergentAnalysis(
            causal_chain=CausalChain(
                links=[],
                conclusion="Insufficient data for analysis",
                overall_confidence=0.0
            ),
            active_hypotheses=[],
            confirmed_hypotheses=[],
            invalidated_hypotheses=[],
            narrative=MarketNarrative(
                phase=MarketPhase.UNKNOWN,
                story="Insufficient data to construct narrative",
                key_players=[],
                key_levels={"Current": current_price},
                expected_move="Wait for more data",
                invalidation="N/A",
                clarity=NarrativeClarity.CHAOS,
                confidence=0.0
            ),
            self_questions=[],
            direction="NO_TRADE",
            confidence=0.0,
            entry_price=current_price,
            stop_loss=current_price,
            take_profit_1=current_price,
            take_profit_2=current_price,
            take_profit_3=current_price,
            reasoning_chain="Insufficient data for reasoning",
            warnings=["Need at least 50 bars for analysis"]
        )


def test_emergent_intelligence():
    """Test the Emergent Intelligence Engine"""
    print("=" * 80)
    print("EMERGENT INTELLIGENCE TEST")
    print("=" * 80)
    
    # Create test data
    import random
    random.seed(42)
    
    base_price = 1.1800
    test_bars = []
    
    for i in range(200):
        # Create trending data with some noise
        trend = 0.0001 * (i // 50)  # Slight uptrend
        noise = random.uniform(-0.0005, 0.0005)
        
        open_price = base_price + trend + noise
        close_price = open_price + random.uniform(-0.0003, 0.0004)
        high = max(open_price, close_price) + random.uniform(0, 0.0003)
        low = min(open_price, close_price) - random.uniform(0, 0.0003)
        
        test_bars.append({
            "timestamp": f"2026-02-07T{10 + i // 12:02d}:{(i * 5) % 60:02d}:00",
            "open": open_price,
            "high": high,
            "low": low,
            "close": close_price,
            "volume": random.uniform(100, 500)
        })
        
        base_price = close_price
    
    # Initialize and run
    engine = EmergentIntelligence()
    analysis = engine.analyze(test_bars)
    
    # Print results
    print(analysis.get_full_analysis())
    
    return analysis


if __name__ == "__main__":
    test_emergent_intelligence()
