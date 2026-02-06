"""
LAYER 5: EXPLANATION - Natural Language Generator

The fifth layer of consciousness: EXPLAINING decisions.

This module generates human-readable explanations for every decision:
- WHY the system made this decision
- WHAT evidence supports it
- WHAT could invalidate it
- HOW confident the system is

This is NOT just logging - this is TRUE EXPLAINABILITY.

The explanations are:
1. Causal - explain the chain of reasoning
2. Evidential - cite specific data points
3. Counterfactual - explain what would change the decision
4. Calibrated - express appropriate uncertainty

This is what separates a black box from a trusted advisor.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
from enum import Enum

from .perception import MarketState, MarketRegime, OrderFlowState, LiquidityCondition
from .prediction import ForecastDistribution, ForecastHorizon
from .decision import TradingDecision, DecisionType, RefusalReason


class ExplanationStyle(Enum):
    """Different styles of explanation."""
    TECHNICAL = "technical"       # For quants and developers
    TRADER = "trader"             # For experienced traders
    SIMPLE = "simple"             # For non-technical users
    AUDIT = "audit"               # For compliance and review


class ConfidenceLevel(Enum):
    """Human-readable confidence levels."""
    VERY_HIGH = "very high"
    HIGH = "high"
    MODERATE = "moderate"
    LOW = "low"
    VERY_LOW = "very low"


@dataclass
class EvidenceItem:
    """A piece of evidence supporting a claim."""
    claim: str
    evidence_type: str  # "data", "pattern", "model", "historical"
    value: Any
    confidence: float
    source: str
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "claim": self.claim,
            "evidence_type": self.evidence_type,
            "value": str(self.value),
            "confidence": self.confidence,
            "source": self.source,
        }


@dataclass
class ReasoningStep:
    """A step in the reasoning chain."""
    step_number: int
    description: str
    inputs: List[str]
    output: str
    confidence: float
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "step": self.step_number,
            "description": self.description,
            "inputs": self.inputs,
            "output": self.output,
            "confidence": self.confidence,
        }


@dataclass
class DecisionExplanation:
    """
    A complete explanation of a trading decision.
    
    This includes:
    - Summary (one-line)
    - Detailed reasoning chain
    - Evidence for each claim
    - Counterfactuals (what would change the decision)
    - Confidence assessment
    - Risk warnings
    """
    # Metadata
    timestamp: datetime
    decision: TradingDecision
    style: ExplanationStyle
    
    # Summary
    summary: str
    headline: str
    
    # Reasoning
    reasoning_chain: List[ReasoningStep] = field(default_factory=list)
    evidence: List[EvidenceItem] = field(default_factory=list)
    
    # Counterfactuals
    counterfactuals: List[str] = field(default_factory=list)
    
    # Confidence
    confidence_level: ConfidenceLevel = ConfidenceLevel.MODERATE
    confidence_explanation: str = ""
    
    # Warnings
    warnings: List[str] = field(default_factory=list)
    risk_factors: List[str] = field(default_factory=list)
    
    # Full narrative
    narrative: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp.isoformat(),
            "style": self.style.value,
            "summary": self.summary,
            "headline": self.headline,
            "reasoning_chain": [r.to_dict() for r in self.reasoning_chain],
            "evidence": [e.to_dict() for e in self.evidence],
            "counterfactuals": self.counterfactuals,
            "confidence_level": self.confidence_level.value,
            "confidence_explanation": self.confidence_explanation,
            "warnings": self.warnings,
            "risk_factors": self.risk_factors,
            "narrative": self.narrative,
        }


class ExplanationGenerator:
    """
    Generates human-readable explanations for trading decisions.
    
    This is the "voice" of the consciousness - translating internal
    states and decisions into language that humans can understand.
    """
    
    def __init__(self, default_style: ExplanationStyle = ExplanationStyle.TRADER):
        self.default_style = default_style
        
        # Templates for different explanation components
        self.templates = self._init_templates()
    
    def _init_templates(self) -> Dict[str, Dict[str, str]]:
        """Initialize explanation templates for different styles."""
        return {
            ExplanationStyle.TECHNICAL: {
                "long_entry": "Initiating LONG position based on {factors}. Kelly fraction: {kelly:.1%}, expected edge: {edge:.2%}.",
                "short_entry": "Initiating SHORT position based on {factors}. Kelly fraction: {kelly:.1%}, expected edge: {edge:.2%}.",
                "hold": "Maintaining current position. No significant change in {factors}.",
                "refuse": "REFUSING to trade. Reason: {reason}. {details}",
                "wait": "WAITING for better setup. Current conditions: {conditions}.",
            },
            ExplanationStyle.TRADER: {
                "long_entry": "Going LONG on {symbol}. {factors}. Risk/reward: {rr:.1f}:1.",
                "short_entry": "Going SHORT on {symbol}. {factors}. Risk/reward: {rr:.1f}:1.",
                "hold": "Holding {symbol}. {factors}.",
                "refuse": "NOT TRADING {symbol}. {reason}.",
                "wait": "Waiting on {symbol}. {conditions}.",
            },
            ExplanationStyle.SIMPLE: {
                "long_entry": "Buying {symbol} because {factors}.",
                "short_entry": "Selling {symbol} because {factors}.",
                "hold": "Keeping {symbol} position.",
                "refuse": "Not trading right now because {reason}.",
                "wait": "Waiting for a better opportunity.",
            },
            ExplanationStyle.AUDIT: {
                "long_entry": "[{timestamp}] LONG {symbol} @ {price}. Factors: {factors}. Size: {size}. Stop: {stop}. Targets: {targets}. Confidence: {confidence:.0%}. Edge: {edge:.2%}.",
                "short_entry": "[{timestamp}] SHORT {symbol} @ {price}. Factors: {factors}. Size: {size}. Stop: {stop}. Targets: {targets}. Confidence: {confidence:.0%}. Edge: {edge:.2%}.",
                "hold": "[{timestamp}] HOLD {symbol}. Reason: {factors}.",
                "refuse": "[{timestamp}] REFUSE {symbol}. Reason: {reason}. Details: {details}.",
                "wait": "[{timestamp}] WAIT {symbol}. Conditions: {conditions}.",
            },
        }
    
    def explain(
        self,
        decision: TradingDecision,
        state: MarketState,
        forecast: ForecastDistribution,
        style: Optional[ExplanationStyle] = None,
    ) -> DecisionExplanation:
        """Generate a complete explanation for a trading decision."""
        style = style or self.default_style
        timestamp = datetime.now(timezone.utc)
        
        # Generate components
        summary = self._generate_summary(decision, state, style)
        headline = self._generate_headline(decision, state)
        reasoning_chain = self._generate_reasoning_chain(decision, state, forecast)
        evidence = self._gather_evidence(decision, state, forecast)
        counterfactuals = self._generate_counterfactuals(decision, state, forecast)
        confidence_level, confidence_explanation = self._assess_confidence(decision, forecast)
        warnings = self._generate_warnings(decision, state, forecast)
        risk_factors = self._identify_risk_factors(decision, state, forecast)
        narrative = self._generate_narrative(
            decision, state, forecast, style,
            reasoning_chain, evidence, counterfactuals
        )
        
        return DecisionExplanation(
            timestamp=timestamp,
            decision=decision,
            style=style,
            summary=summary,
            headline=headline,
            reasoning_chain=reasoning_chain,
            evidence=evidence,
            counterfactuals=counterfactuals,
            confidence_level=confidence_level,
            confidence_explanation=confidence_explanation,
            warnings=warnings,
            risk_factors=risk_factors,
            narrative=narrative,
        )
    
    def _generate_summary(
        self,
        decision: TradingDecision,
        state: MarketState,
        style: ExplanationStyle,
    ) -> str:
        """Generate a one-line summary."""
        templates = self.templates[style]
        
        # Determine template key
        if decision.decision == DecisionType.REFUSE:
            template_key = "refuse"
        elif decision.decision == DecisionType.WAIT:
            template_key = "wait"
        elif decision.decision == DecisionType.HOLD:
            template_key = "hold"
        elif decision.decision in [DecisionType.LONG]:
            template_key = "long_entry"
        elif decision.decision in [DecisionType.SHORT]:
            template_key = "short_entry"
        else:
            template_key = "hold"
        
        template = templates[template_key]
        
        # Format template
        factors = ", ".join(decision.supporting_factors[:3]) if decision.supporting_factors else "multiple factors"
        
        return template.format(
            symbol=decision.symbol,
            factors=factors,
            kelly=decision.position_sizing.kelly_fraction_used if decision.position_sizing else 0,
            edge=decision.edge,
            rr=decision.risk_reward_ratio,
            reason=decision.refusal_explanation or "uncertainty",
            details=decision.reasoning[0] if decision.reasoning else "",
            conditions=", ".join(decision.reasoning[:2]) if decision.reasoning else "unclear",
            timestamp=decision.timestamp.strftime("%Y-%m-%d %H:%M"),
            price=decision.entry_price or state.price,
            size=f"{decision.position_sizing.size_pct*100:.1f}%" if decision.position_sizing else "N/A",
            stop=decision.stop_loss or "N/A",
            targets=f"{decision.take_profit_1}, {decision.take_profit_2}" if decision.take_profit_1 else "N/A",
            confidence=decision.confidence,
        )
    
    def _generate_headline(
        self,
        decision: TradingDecision,
        state: MarketState,
    ) -> str:
        """Generate a headline for the decision."""
        if decision.decision == DecisionType.REFUSE:
            return f"REFUSING TO TRADE: {decision.refusal_reason.value if decision.refusal_reason else 'uncertainty'}"
        elif decision.decision == DecisionType.WAIT:
            return f"WAITING: No clear edge on {decision.symbol}"
        elif decision.decision == DecisionType.HOLD:
            return f"HOLDING: Maintaining {decision.symbol} position"
        elif decision.decision == DecisionType.LONG:
            return f"LONG {decision.symbol}: {decision.confidence:.0%} confidence"
        elif decision.decision == DecisionType.SHORT:
            return f"SHORT {decision.symbol}: {decision.confidence:.0%} confidence"
        else:
            return f"{decision.decision.value.upper()} {decision.symbol}"
    
    def _generate_reasoning_chain(
        self,
        decision: TradingDecision,
        state: MarketState,
        forecast: ForecastDistribution,
    ) -> List[ReasoningStep]:
        """Generate the chain of reasoning that led to the decision."""
        steps = []
        step_num = 1
        
        # Step 1: Market State Assessment
        steps.append(ReasoningStep(
            step_number=step_num,
            description="Assessed current market state",
            inputs=[
                f"Price: {state.price:.5f}",
                f"Regime: {state.primary_regime.value}",
                f"Order flow: {state.order_flow_score:.2f}",
            ],
            output=f"Market is in {state.primary_regime.value} regime with {state.regime_confidence:.0%} confidence",
            confidence=state.regime_confidence,
        ))
        step_num += 1
        
        # Step 2: Forecast Generation
        steps.append(ReasoningStep(
            step_number=step_num,
            description="Generated probabilistic forecast",
            inputs=[
                f"Current price: {forecast.current_price:.5f}",
                f"Horizon: {forecast.horizon.value} bars",
            ],
            output=f"Expected price: {forecast.mean:.5f} (std: {forecast.std:.5f}), P(up)={forecast.prob_up:.0%}",
            confidence=forecast.calibration_score,
        ))
        step_num += 1
        
        # Step 3: Direction Determination
        direction_str = "LONG" if decision.direction > 0 else "SHORT" if decision.direction < 0 else "NEUTRAL"
        steps.append(ReasoningStep(
            step_number=step_num,
            description="Determined trading direction",
            inputs=decision.reasoning[:3] if decision.reasoning else ["Multiple factors"],
            output=f"Direction: {direction_str}",
            confidence=decision.confidence,
        ))
        step_num += 1
        
        # Step 4: Risk Assessment
        if decision.position_sizing:
            steps.append(ReasoningStep(
                step_number=step_num,
                description="Computed position size and risk",
                inputs=[
                    f"Kelly optimal: {decision.position_sizing.kelly_optimal:.1%}",
                    f"Risk/reward: {decision.risk_reward_ratio:.2f}",
                ],
                output=f"Position size: {decision.position_sizing.size_pct:.1%}, Risk: {decision.position_sizing.risk_pct:.1%}",
                confidence=0.9,
            ))
            step_num += 1
        
        # Step 5: Final Decision
        steps.append(ReasoningStep(
            step_number=step_num,
            description="Made final decision",
            inputs=[
                f"Edge: {decision.edge:.2%}",
                f"Confidence: {decision.confidence:.0%}",
                f"Uncertainty: {decision.uncertainty:.0%}",
            ],
            output=f"Decision: {decision.decision.value.upper()}",
            confidence=decision.confidence,
        ))
        
        return steps
    
    def _gather_evidence(
        self,
        decision: TradingDecision,
        state: MarketState,
        forecast: ForecastDistribution,
    ) -> List[EvidenceItem]:
        """Gather evidence supporting the decision."""
        evidence = []
        
        # Evidence from market state
        evidence.append(EvidenceItem(
            claim=f"Market is in {state.primary_regime.value} regime",
            evidence_type="model",
            value=state.regime_confidence,
            confidence=state.regime_confidence,
            source="HMM Regime Detector",
        ))
        
        # Evidence from order flow
        if state.order_flow_score != 0:
            flow_direction = "bullish" if state.order_flow_score > 0 else "bearish"
            evidence.append(EvidenceItem(
                claim=f"Order flow is {flow_direction}",
                evidence_type="data",
                value=state.order_flow_score,
                confidence=min(1.0, abs(state.order_flow_score) * 2),
                source="Order Flow Analyzer",
            ))
        
        # Evidence from forecast
        evidence.append(EvidenceItem(
            claim=f"Probability of price increase is {forecast.prob_up:.0%}",
            evidence_type="model",
            value=forecast.prob_up,
            confidence=forecast.calibration_score,
            source="Probabilistic Forecaster",
        ))
        
        # Evidence from multi-timeframe
        if state.timeframe_states:
            trends = [s.trend_direction for s in state.timeframe_states.values()]
            avg_trend = sum(trends) / len(trends) if trends else 0
            trend_direction = "bullish" if avg_trend > 0.2 else "bearish" if avg_trend < -0.2 else "neutral"
            evidence.append(EvidenceItem(
                claim=f"Multi-timeframe trend is {trend_direction}",
                evidence_type="data",
                value=avg_trend,
                confidence=min(1.0, abs(avg_trend)),
                source="Multi-Timeframe Analyzer",
            ))
        
        # Evidence from liquidity
        evidence.append(EvidenceItem(
            claim=f"Liquidity is {state.liquidity_condition.value}",
            evidence_type="data",
            value=state.liquidity_score,
            confidence=0.8,
            source="Liquidity Monitor",
        ))
        
        return evidence
    
    def _generate_counterfactuals(
        self,
        decision: TradingDecision,
        state: MarketState,
        forecast: ForecastDistribution,
    ) -> List[str]:
        """Generate counterfactual statements (what would change the decision)."""
        counterfactuals = []
        
        if decision.decision in [DecisionType.LONG, DecisionType.SHORT]:
            # What would make us not take this trade?
            counterfactuals.append(
                f"Would NOT trade if uncertainty exceeded {0.4:.0%} (currently {state.state_uncertainty:.0%})"
            )
            counterfactuals.append(
                f"Would NOT trade if risk/reward fell below 1.5 (currently {decision.risk_reward_ratio:.1f})"
            )
            counterfactuals.append(
                f"Would REVERSE if order flow flipped to {-state.order_flow_score:.2f}"
            )
            
        elif decision.decision == DecisionType.REFUSE:
            # What would make us trade?
            if decision.refusal_reason == RefusalReason.HIGH_UNCERTAINTY:
                counterfactuals.append(
                    f"Would TRADE if uncertainty dropped below 0.4 (currently {state.state_uncertainty:.0%})"
                )
            elif decision.refusal_reason == RefusalReason.LOW_CONFIDENCE:
                counterfactuals.append(
                    f"Would TRADE if confidence exceeded 0.6 (currently {forecast.calibration_score:.0%})"
                )
            elif decision.refusal_reason == RefusalReason.MODEL_DISAGREEMENT:
                counterfactuals.append(
                    f"Would TRADE if model agreement exceeded 0.5 (currently {forecast.model_agreement:.0%})"
                )
        
        elif decision.decision == DecisionType.WAIT:
            # What would trigger a trade?
            counterfactuals.append(
                f"Would go LONG if P(up) exceeded 60% (currently {forecast.prob_up:.0%})"
            )
            counterfactuals.append(
                f"Would go SHORT if P(down) exceeded 60% (currently {forecast.prob_down:.0%})"
            )
        
        return counterfactuals
    
    def _assess_confidence(
        self,
        decision: TradingDecision,
        forecast: ForecastDistribution,
    ) -> Tuple[ConfidenceLevel, str]:
        """Assess and explain confidence level."""
        conf = decision.confidence
        
        if conf >= 0.8:
            level = ConfidenceLevel.VERY_HIGH
            explanation = "Multiple strong signals align. Models agree. Historical accuracy is high."
        elif conf >= 0.65:
            level = ConfidenceLevel.HIGH
            explanation = "Good signal alignment with minor disagreements. Reasonable historical accuracy."
        elif conf >= 0.5:
            level = ConfidenceLevel.MODERATE
            explanation = "Mixed signals. Some model disagreement. Proceed with caution."
        elif conf >= 0.35:
            level = ConfidenceLevel.LOW
            explanation = "Weak signals. Significant uncertainty. Consider reducing size."
        else:
            level = ConfidenceLevel.VERY_LOW
            explanation = "Very weak signals. High uncertainty. Trading not recommended."
        
        return level, explanation
    
    def _generate_warnings(
        self,
        decision: TradingDecision,
        state: MarketState,
        forecast: ForecastDistribution,
    ) -> List[str]:
        """Generate warnings about the decision."""
        warnings = []
        
        # Uncertainty warning
        if state.state_uncertainty > 0.3:
            warnings.append(f"ELEVATED UNCERTAINTY: State uncertainty is {state.state_uncertainty:.0%}")
        
        # Liquidity warning
        if state.liquidity_condition in [LiquidityCondition.THIN, LiquidityCondition.CRISIS]:
            warnings.append(f"LIQUIDITY WARNING: {state.liquidity_condition.value} liquidity conditions")
        
        # Model disagreement warning
        if forecast.model_agreement < 0.5:
            warnings.append(f"MODEL DISAGREEMENT: Models only {forecast.model_agreement:.0%} aligned")
        
        # Volatility warning
        if state.primary_regime == MarketRegime.HIGH_VOLATILITY:
            warnings.append("HIGH VOLATILITY: Increased risk of large adverse moves")
        
        # Counter-trend warning
        if decision.opposing_factors:
            for factor in decision.opposing_factors[:2]:
                warnings.append(f"CAUTION: {factor}")
        
        return warnings
    
    def _identify_risk_factors(
        self,
        decision: TradingDecision,
        state: MarketState,
        forecast: ForecastDistribution,
    ) -> List[str]:
        """Identify key risk factors."""
        risks = []
        
        # Market risk
        risks.append(f"Market risk: {forecast.std / forecast.current_price * 100:.1f}% expected volatility")
        
        # Tail risk
        if forecast.prob_big_move > 0.1:
            risks.append(f"Tail risk: {forecast.prob_big_move:.0%} chance of >2 std move")
        
        # Regime change risk
        if state.regime_confidence < 0.7:
            risks.append(f"Regime risk: Only {state.regime_confidence:.0%} confident in current regime")
        
        # Liquidity risk
        if state.liquidity_score < 0.5:
            risks.append(f"Liquidity risk: Score only {state.liquidity_score:.0%}")
        
        # Model risk
        if forecast.calibration_score < 0.6:
            risks.append(f"Model risk: Calibration score only {forecast.calibration_score:.0%}")
        
        return risks
    
    def _generate_narrative(
        self,
        decision: TradingDecision,
        state: MarketState,
        forecast: ForecastDistribution,
        style: ExplanationStyle,
        reasoning_chain: List[ReasoningStep],
        evidence: List[EvidenceItem],
        counterfactuals: List[str],
    ) -> str:
        """Generate a full narrative explanation."""
        paragraphs = []
        
        # Opening
        if decision.decision == DecisionType.REFUSE:
            paragraphs.append(
                f"After analyzing {decision.symbol}, I am REFUSING to trade. "
                f"The reason is {decision.refusal_reason.value if decision.refusal_reason else 'uncertainty'}. "
                f"{decision.refusal_explanation or ''}"
            )
        elif decision.decision == DecisionType.WAIT:
            paragraphs.append(
                f"I am WAITING on {decision.symbol}. "
                f"While there are some signals, they are not strong enough to justify a trade. "
                f"The current setup does not meet my criteria for entry."
            )
        else:
            direction = "LONG" if decision.direction > 0 else "SHORT"
            paragraphs.append(
                f"I am going {direction} on {decision.symbol} at {decision.entry_price:.5f}. "
                f"My confidence in this trade is {decision.confidence:.0%}."
            )
        
        # Reasoning
        if reasoning_chain:
            reasoning_text = "My reasoning: "
            for step in reasoning_chain:
                reasoning_text += f"{step.description} -> {step.output}. "
            paragraphs.append(reasoning_text)
        
        # Evidence
        if evidence and style != ExplanationStyle.SIMPLE:
            evidence_text = "Supporting evidence: "
            for e in evidence[:3]:
                evidence_text += f"{e.claim} ({e.confidence:.0%} confidence). "
            paragraphs.append(evidence_text)
        
        # Risk management
        if decision.position_sizing and decision.is_actionable():
            paragraphs.append(
                f"Position size: {decision.position_sizing.size_pct*100:.1f}% of capital. "
                f"Stop loss at {decision.stop_loss:.5f}. "
                f"First target at {decision.take_profit_1:.5f}. "
                f"Risk/reward ratio: {decision.risk_reward_ratio:.1f}:1."
            )
        
        # Counterfactuals
        if counterfactuals and style in [ExplanationStyle.TECHNICAL, ExplanationStyle.AUDIT]:
            cf_text = "What would change this decision: "
            cf_text += "; ".join(counterfactuals[:2])
            paragraphs.append(cf_text)
        
        # Closing
        if decision.invalidation_conditions:
            paragraphs.append(
                f"This trade is invalidated if: {decision.invalidation_conditions[0]}"
            )
        
        return "\n\n".join(paragraphs)
    
    def explain_refusal(
        self,
        reason: RefusalReason,
        details: Dict[str, Any],
    ) -> str:
        """Generate a specific explanation for why we refused to trade."""
        explanations = {
            RefusalReason.HIGH_UNCERTAINTY: (
                f"I am refusing to trade because the market state is too uncertain. "
                f"Current uncertainty is {details.get('uncertainty', 'unknown')}, "
                f"which exceeds my maximum threshold. "
                f"When I don't understand what's happening, I don't trade."
            ),
            RefusalReason.LOW_CONFIDENCE: (
                f"I am refusing to trade because my confidence in the forecast is too low. "
                f"Current confidence is {details.get('confidence', 'unknown')}, "
                f"which is below my minimum threshold. "
                f"I only trade when I have sufficient conviction."
            ),
            RefusalReason.MODEL_DISAGREEMENT: (
                f"I am refusing to trade because my models disagree significantly. "
                f"Model agreement is only {details.get('agreement', 'unknown')}. "
                f"When my models can't agree, I step aside."
            ),
            RefusalReason.INSUFFICIENT_DATA: (
                f"I am refusing to trade because I don't have enough data. "
                f"Data quality score is {details.get('data_quality', 'unknown')}. "
                f"I need more information before making a decision."
            ),
            RefusalReason.REGIME_UNCLEAR: (
                f"I am refusing to trade because the market regime is unclear. "
                f"Regime confidence is only {details.get('regime_confidence', 'unknown')}. "
                f"I need to understand the market environment before trading."
            ),
            RefusalReason.LIQUIDITY_CRISIS: (
                f"I am refusing to trade because of poor liquidity conditions. "
                f"Liquidity score is {details.get('liquidity', 'unknown')}. "
                f"Trading in illiquid conditions is too risky."
            ),
            RefusalReason.DRAWDOWN_LIMIT: (
                f"I am refusing to trade because I've hit my drawdown limit. "
                f"Current drawdown is {details.get('drawdown', 'unknown')}. "
                f"I need to protect capital before taking new risks."
            ),
            RefusalReason.POOR_RISK_REWARD: (
                f"I am refusing to trade because the risk/reward is unfavorable. "
                f"Current R:R is {details.get('risk_reward', 'unknown')}. "
                f"I only take trades with favorable risk/reward."
            ),
            RefusalReason.CORRELATION_RISK: (
                f"I am refusing to trade because of correlation risk. "
                f"This trade would be too correlated with existing positions. "
                f"I need to maintain portfolio diversification."
            ),
        }
        
        return explanations.get(
            reason,
            f"I am refusing to trade due to {reason.value}. Details: {details}"
        )
