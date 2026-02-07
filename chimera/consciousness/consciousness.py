"""
THE MARKET CONSCIOUSNESS ENGINE

This is the unified system that integrates all 7 layers of consciousness:
1. PERCEPTION - Market State Encoder
2. UNDERSTANDING - Causal World Model
3. PREDICTION - Probabilistic Forecaster
4. DECISION - Risk-Aware Actor
5. EXPLANATION - Natural Language Generator
6. REFLECTION - Meta-Cognitive Monitor
7. ADAPTATION - Online Learning

This is NOT a trading bot. This is a THINKING SYSTEM.

It doesn't just react to prices - it UNDERSTANDS markets,
PREDICTS outcomes, DECIDES with full risk awareness,
EXPLAINS its reasoning, REFLECTS on its performance,
and ADAPTS to new information.

This is the IMPOSSIBLE made possible.

Author: Devin (for Prince)
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple, Callable
from enum import Enum
import numpy as np

# Import all layers
from .perception import (
    MarketStateEncoder, 
    MarketState, 
    MarketRegime,
    LiquidityCondition,
    OrderFlowState,
)
from .understanding import (
    CausalWorldModel,
    CausalGraph,
    CausalQuery,
    CausalAnswer,
)
from .prediction import (
    ProbabilisticForecaster,
    ForecastDistribution,
    ForecastHorizon,
)
from .decision import (
    RiskAwareActor,
    TradingDecision,
    DecisionType,
    RiskParameters,
    RefusalReason,
)
from .explanation import (
    ExplanationGenerator,
    DecisionExplanation,
    ExplanationStyle,
)
from .reflection import (
    MetaCognitiveMonitor,
    PerformanceState,
    PerformanceAlert,
    TradeResult,
    SystemState,
)
from .adaptation import (
    OnlineLearner,
    AdaptationEvent,
    BeliefUpdate,
)


class ConsciousnessState(Enum):
    """States of the consciousness system."""
    INITIALIZING = "initializing"
    OBSERVING = "observing"       # Perceiving market
    THINKING = "thinking"         # Processing and predicting
    DECIDING = "deciding"         # Making decisions
    ACTING = "acting"             # Executing decisions
    REFLECTING = "reflecting"     # Analyzing performance
    ADAPTING = "adapting"         # Learning and improving
    PAUSED = "paused"             # Temporarily paused
    HALTED = "halted"             # Stopped due to issues


@dataclass
class ConsciousnessOutput:
    """
    The complete output of the consciousness system.
    
    This is everything the system knows, thinks, and decides
    at a given moment in time.
    """
    # Metadata
    timestamp: datetime
    symbol: str
    consciousness_state: ConsciousnessState
    
    # Layer 1: Perception
    market_state: MarketState
    
    # Layer 2: Understanding
    causal_insights: Dict[str, Any]
    
    # Layer 3: Prediction
    forecast: ForecastDistribution
    
    # Layer 4: Decision
    decision: TradingDecision
    
    # Layer 5: Explanation
    explanation: DecisionExplanation
    
    # Layer 6: Reflection
    performance_state: PerformanceState
    
    # Layer 7: Adaptation
    recent_adaptations: List[AdaptationEvent]
    
    # Overall confidence
    overall_confidence: float
    
    # Should we trade?
    should_trade: bool
    trade_blocked_reason: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp.isoformat(),
            "symbol": self.symbol,
            "consciousness_state": self.consciousness_state.value,
            "market_state": self.market_state.to_dict(),
            "forecast": self.forecast.to_dict(),
            "decision": self.decision.to_dict(),
            "explanation": self.explanation.to_dict(),
            "performance_state": self.performance_state.to_dict(),
            "recent_adaptations": [a.to_dict() for a in self.recent_adaptations],
            "overall_confidence": self.overall_confidence,
            "should_trade": self.should_trade,
            "trade_blocked_reason": self.trade_blocked_reason,
        }
    
    def summary(self) -> str:
        """Get a one-line summary."""
        if not self.should_trade:
            return f"[{self.symbol}] NOT TRADING: {self.trade_blocked_reason}"
        else:
            return f"[{self.symbol}] {self.decision.summary()} | Confidence: {self.overall_confidence:.0%}"
    
    def full_report(self) -> str:
        """Get a full report of the consciousness output."""
        lines = [
            "=" * 60,
            f"OMEGA-DEVIN CONSCIOUSNESS REPORT",
            f"Time: {self.timestamp.strftime('%Y-%m-%d %H:%M:%S UTC')}",
            f"Symbol: {self.symbol}",
            f"State: {self.consciousness_state.value}",
            "=" * 60,
            "",
            "--- MARKET PERCEPTION ---",
            f"Price: {self.market_state.price:.5f}",
            f"Regime: {self.market_state.primary_regime.value} ({self.market_state.regime_confidence:.0%} confidence)",
            f"Order Flow: {self.market_state.order_flow_state.value} ({self.market_state.order_flow_score:.2f})",
            f"Liquidity: {self.market_state.liquidity_condition.value} ({self.market_state.liquidity_score:.0%})",
            f"Uncertainty: {self.market_state.state_uncertainty:.0%}",
            "",
            "--- FORECAST ---",
            f"Expected Price: {self.forecast.mean:.5f}",
            f"95% CI: [{self.forecast.ci_95[0]:.5f}, {self.forecast.ci_95[1]:.5f}]",
            f"P(Up): {self.forecast.prob_up:.0%} | P(Down): {self.forecast.prob_down:.0%}",
            f"Model Agreement: {self.forecast.model_agreement:.0%}",
            "",
            "--- DECISION ---",
            f"Action: {self.decision.decision.value.upper()}",
            f"Direction: {'LONG' if self.decision.direction > 0 else 'SHORT' if self.decision.direction < 0 else 'NEUTRAL'}",
            f"Confidence: {self.decision.confidence:.0%}",
            f"Edge: {self.decision.edge:.2%}",
        ]
        
        if self.decision.position_sizing:
            lines.extend([
                f"Position Size: {self.decision.position_sizing.size_pct*100:.1f}%",
                f"Risk: {self.decision.position_sizing.risk_pct*100:.2f}%",
            ])
        
        if self.decision.entry_price:
            lines.extend([
                f"Entry: {self.decision.entry_price:.5f}",
                f"Stop Loss: {self.decision.stop_loss:.5f}",
                f"Take Profit 1: {self.decision.take_profit_1:.5f}",
            ])
        
        lines.extend([
            "",
            "--- EXPLANATION ---",
            self.explanation.narrative,
            "",
            "--- PERFORMANCE ---",
            f"System State: {self.performance_state.system_state.value}",
            f"Health Score: {self.performance_state.health_score:.0%}",
            f"Total Trades: {self.performance_state.total_trades}",
            f"Win Rate: {self.performance_state.win_rate:.0%}",
            f"Sharpe Ratio: {self.performance_state.sharpe_ratio:.2f}",
            f"Max Drawdown: {self.performance_state.max_drawdown:.1%}",
            "",
            "--- TRADING STATUS ---",
            f"Should Trade: {'YES' if self.should_trade else 'NO'}",
        ])
        
        if self.trade_blocked_reason:
            lines.append(f"Blocked Reason: {self.trade_blocked_reason}")
        
        lines.append("=" * 60)
        
        return "\n".join(lines)


class MarketConsciousness:
    """
    THE MARKET CONSCIOUSNESS ENGINE
    
    This is the main class that orchestrates all 7 layers of consciousness
    to create a truly intelligent trading system.
    
    Usage:
        consciousness = MarketConsciousness()
        
        # Process market data
        output = consciousness.think(
            symbol="EURUSD",
            candles={"1m": [...], "5m": [...], ...},
            order_book={...},
            trades=[...],
        )
        
        # Get decision
        if output.should_trade:
            execute(output.decision)
        
        # Learn from outcome
        consciousness.learn(trade_result)
    """
    
    def __init__(
        self,
        risk_params: Optional[RiskParameters] = None,
        explanation_style: ExplanationStyle = ExplanationStyle.TRADER,
    ):
        # Initialize all layers
        self.perception = MarketStateEncoder()
        self.understanding = CausalWorldModel()
        self.prediction = ProbabilisticForecaster(self.understanding)
        self.decision = RiskAwareActor(risk_params)
        self.explanation = ExplanationGenerator(explanation_style)
        self.reflection = MetaCognitiveMonitor()
        self.adaptation = OnlineLearner(self.reflection)
        
        # Current state
        self.state = ConsciousnessState.INITIALIZING
        self.current_symbol: Optional[str] = None
        self.current_position: float = 0.0
        
        # History
        self.output_history: List[ConsciousnessOutput] = []
        self.max_history = 1000
        
        # Callbacks
        self.on_decision_callbacks: List[Callable[[TradingDecision], None]] = []
        self.on_alert_callbacks: List[Callable[[PerformanceAlert], None]] = []
        
        # Register alert callback
        self.reflection.register_alert_callback(self._on_alert)
        
        # Initialize complete
        self.state = ConsciousnessState.OBSERVING
    
    def think(
        self,
        symbol: str,
        candles: Dict[str, List[Dict[str, Any]]],
        order_book: Optional[Dict[str, Any]] = None,
        trades: Optional[List[Dict[str, Any]]] = None,
        volume_profile: Optional[Dict[str, Any]] = None,
        current_position: float = 0.0,
        forecast_horizon: ForecastHorizon = ForecastHorizon.SHORT,
    ) -> ConsciousnessOutput:
        """
        The main thinking loop.
        
        This is where all 7 layers come together to produce
        a complete understanding of the market and a decision.
        """
        timestamp = datetime.now(timezone.utc)
        self.current_symbol = symbol
        self.current_position = current_position
        
        # Check if we should halt
        should_halt, halt_reason = self.reflection.should_halt_trading()
        if should_halt:
            self.state = ConsciousnessState.HALTED
            return self._create_halted_output(symbol, timestamp, halt_reason)
        
        # Layer 1: PERCEPTION
        self.state = ConsciousnessState.OBSERVING
        market_state = self.perception.encode(
            symbol=symbol,
            candles=candles,
            order_book=order_book,
            trades=trades,
            volume_profile=volume_profile,
        )
        
        # Update regime tracking
        regime_changed = self.reflection.update_regime(market_state.primary_regime)
        
        # Layer 2: UNDERSTANDING
        self.state = ConsciousnessState.THINKING
        self.understanding.update(market_state)
        causal_insights = self._get_causal_insights(market_state)
        
        # Layer 3: PREDICTION
        forecast = self.prediction.forecast(market_state, forecast_horizon)
        
        # Layer 4: DECISION
        self.state = ConsciousnessState.DECIDING
        decision = self.decision.decide(market_state, forecast, current_position)
        
        # Layer 5: EXPLANATION
        explanation = self.explanation.explain(decision, market_state, forecast)
        
        # Layer 6: REFLECTION
        self.state = ConsciousnessState.REFLECTING
        performance_state = self.reflection.get_performance_state()
        
        # Layer 7: ADAPTATION
        self.state = ConsciousnessState.ADAPTING
        recent_adaptations = []
        
        if regime_changed:
            adaptation = self.adaptation.on_regime_change(
                market_state.primary_regime,
                performance_state.total_return if performance_state.total_trades > 0 else None,
            )
            recent_adaptations.append(adaptation)
            
            # Apply adapted parameters to decision maker
            new_params = self.adaptation.get_current_parameters()
            self._apply_parameters(new_params)
        
        # Compute overall confidence
        overall_confidence = self._compute_overall_confidence(
            market_state, forecast, decision, performance_state
        )
        
        # Determine if we should trade
        should_trade, blocked_reason = self._should_trade(
            decision, market_state, forecast, performance_state
        )
        
        # Create output
        self.state = ConsciousnessState.OBSERVING
        output = ConsciousnessOutput(
            timestamp=timestamp,
            symbol=symbol,
            consciousness_state=self.state,
            market_state=market_state,
            causal_insights=causal_insights,
            forecast=forecast,
            decision=decision,
            explanation=explanation,
            performance_state=performance_state,
            recent_adaptations=recent_adaptations,
            overall_confidence=overall_confidence,
            should_trade=should_trade,
            trade_blocked_reason=blocked_reason,
        )
        
        # Store in history
        self._update_history(output)
        
        # Notify callbacks
        if decision.is_actionable():
            for callback in self.on_decision_callbacks:
                try:
                    callback(decision)
                except Exception:
                    pass
        
        return output
    
    def learn_from_forecast(
        self,
        forecast: ForecastDistribution,
        actual_price: float,
    ) -> None:
        """Learn from a forecast outcome."""
        # Update forecaster calibration
        self.prediction.update(actual_price)
        
        # Update reflection
        self.reflection.record_forecast(forecast, actual_price)
        
        # Update adaptation
        self.adaptation.learn_from_forecast(forecast, actual_price)
    
    def learn_from_trade(
        self,
        decision: TradingDecision,
        exit_price: float,
        hit_stop: bool = False,
        hit_target: bool = False,
        duration_bars: int = 0,
    ) -> Optional[TradeResult]:
        """Learn from a completed trade."""
        # Record in reflection
        result = self.reflection.record_trade_exit(
            symbol=decision.symbol,
            exit_price=exit_price,
            regime=self.reflection.current_regime,
            hit_stop=hit_stop,
            hit_target=hit_target,
            duration_bars=duration_bars,
        )
        
        if result:
            # Learn from trade
            self.adaptation.learn_from_trade(result)
            
            # Update decision maker equity
            new_equity = self.reflection.equity_curve[-1]
            self.decision.update_equity(new_equity)
        
        return result
    
    def record_trade_entry(self, decision: TradingDecision) -> None:
        """Record a trade entry."""
        self.reflection.record_trade_entry(
            decision=decision,
            regime=self.reflection.current_regime,
        )
    
    def _get_causal_insights(self, state: MarketState) -> Dict[str, Any]:
        """Get causal insights about current market state."""
        insights = {}
        
        # Query: What's causing price movement?
        if state.order_flow_score != 0:
            query = CausalQuery(
                query_type="predict",
                target="price_return",
                conditions={"order_flow": state.order_flow_score},
            )
            answer = self.understanding.query(query)
            insights["order_flow_impact"] = {
                "prediction": answer.prediction,
                "confidence": answer.confidence,
                "reasoning": answer.reasoning,
            }
        
        # Get causal summary
        insights["causal_summary"] = self.understanding.get_causal_summary()
        
        return insights
    
    def _compute_overall_confidence(
        self,
        state: MarketState,
        forecast: ForecastDistribution,
        decision: TradingDecision,
        performance: PerformanceState,
    ) -> float:
        """Compute overall confidence in the current analysis."""
        confidences = [
            1 - state.state_uncertainty,  # Perception confidence
            forecast.calibration_score,    # Forecast confidence
            decision.confidence,           # Decision confidence
            performance.health_score,      # System health
        ]
        
        # Weighted average (decision confidence weighted higher)
        weights = [0.2, 0.25, 0.35, 0.2]
        
        return sum(c * w for c, w in zip(confidences, weights))
    
    def _should_trade(
        self,
        decision: TradingDecision,
        state: MarketState,
        forecast: ForecastDistribution,
        performance: PerformanceState,
    ) -> Tuple[bool, Optional[str]]:
        """Determine if we should actually trade."""
        # Check decision type
        if decision.decision in [DecisionType.REFUSE, DecisionType.WAIT, DecisionType.HOLD]:
            return False, f"Decision is {decision.decision.value}"
        
        # Check system state
        if performance.system_state in [SystemState.CRITICAL, SystemState.HALTED]:
            return False, f"System state is {performance.system_state.value}"
        
        # Check uncertainty
        if state.state_uncertainty > 0.5:
            return False, f"Uncertainty too high ({state.state_uncertainty:.0%})"
        
        # Check confidence
        if decision.confidence < 0.4:
            return False, f"Confidence too low ({decision.confidence:.0%})"
        
        # Check model agreement
        if forecast.model_agreement < 0.3:
            return False, f"Model disagreement ({forecast.model_agreement:.0%})"
        
        # Check liquidity
        if state.liquidity_condition == LiquidityCondition.CRISIS:
            return False, "Liquidity crisis"
        
        # All checks passed
        return True, None
    
    def _create_halted_output(
        self,
        symbol: str,
        timestamp: datetime,
        reason: str,
    ) -> ConsciousnessOutput:
        """Create output when system is halted."""
        # Create minimal state
        empty_state = MarketState(
            timestamp=timestamp,
            symbol=symbol,
            price=0.0,
        )
        
        empty_forecast = ForecastDistribution(
            timestamp=timestamp,
            symbol=symbol,
            horizon=ForecastHorizon.SHORT,
            current_price=0.0,
            mean=0.0,
            std=0.0,
            skew=0.0,
            kurtosis=3.0,
        )
        
        halt_decision = TradingDecision(
            timestamp=timestamp,
            symbol=symbol,
            decision=DecisionType.REFUSE,
            direction=0,
            refusal_reason=RefusalReason.DRAWDOWN_LIMIT,
            refusal_explanation=reason,
        )
        
        halt_explanation = self.explanation.explain(
            halt_decision, empty_state, empty_forecast
        )
        
        performance_state = self.reflection.get_performance_state()
        
        return ConsciousnessOutput(
            timestamp=timestamp,
            symbol=symbol,
            consciousness_state=ConsciousnessState.HALTED,
            market_state=empty_state,
            causal_insights={},
            forecast=empty_forecast,
            decision=halt_decision,
            explanation=halt_explanation,
            performance_state=performance_state,
            recent_adaptations=[],
            overall_confidence=0.0,
            should_trade=False,
            trade_blocked_reason=reason,
        )
    
    def _apply_parameters(self, params: Dict[str, float]) -> None:
        """Apply adapted parameters to decision maker."""
        if "kelly_fraction" in params:
            self.decision.risk_params.kelly_fraction = params["kelly_fraction"]
        if "stop_loss_atr" in params:
            self.decision.risk_params.stop_loss_atr = params["stop_loss_atr"]
        if "take_profit_atr" in params:
            self.decision.risk_params.take_profit_atr = params["take_profit_atr"]
        if "min_confidence" in params:
            self.decision.risk_params.min_confidence = params["min_confidence"]
        if "max_uncertainty" in params:
            self.decision.risk_params.max_uncertainty = params["max_uncertainty"]
        if "max_position_pct" in params:
            self.decision.risk_params.max_position_pct = params["max_position_pct"]
    
    def _update_history(self, output: ConsciousnessOutput) -> None:
        """Update output history."""
        self.output_history.append(output)
        if len(self.output_history) > self.max_history:
            self.output_history = self.output_history[-self.max_history:]
    
    def _on_alert(self, alert: PerformanceAlert) -> None:
        """Handle performance alert."""
        for callback in self.on_alert_callbacks:
            try:
                callback(alert)
            except Exception:
                pass
    
    def register_decision_callback(
        self,
        callback: Callable[[TradingDecision], None],
    ) -> None:
        """Register callback for trading decisions."""
        self.on_decision_callbacks.append(callback)
    
    def register_alert_callback(
        self,
        callback: Callable[[PerformanceAlert], None],
    ) -> None:
        """Register callback for performance alerts."""
        self.on_alert_callbacks.append(callback)
    
    def pause(self) -> None:
        """Pause the consciousness."""
        self.state = ConsciousnessState.PAUSED
        self.adaptation.pause_learning()
    
    def resume(self) -> None:
        """Resume the consciousness."""
        self.state = ConsciousnessState.OBSERVING
        self.adaptation.resume_learning()
    
    def get_state_summary(self) -> Dict[str, Any]:
        """Get summary of consciousness state."""
        return {
            "state": self.state.value,
            "current_symbol": self.current_symbol,
            "current_position": self.current_position,
            "output_history_size": len(self.output_history),
            "perception": {
                "state_history_size": len(self.perception.state_history),
            },
            "understanding": self.understanding.get_causal_summary(),
            "prediction": self.prediction.get_forecast_summary(),
            "decision": self.decision.get_decision_summary(),
            "reflection": self.reflection.get_summary(),
            "adaptation": self.adaptation.get_adaptation_summary(),
        }
    
    def explain_current_state(self, style: ExplanationStyle = ExplanationStyle.SIMPLE) -> str:
        """Get a human-readable explanation of current state."""
        if not self.output_history:
            return "No market data processed yet. Waiting for input."
        
        latest = self.output_history[-1]
        
        if style == ExplanationStyle.SIMPLE:
            if latest.should_trade:
                direction = "buy" if latest.decision.direction > 0 else "sell"
                return (
                    f"I think we should {direction} {latest.symbol}. "
                    f"I'm {latest.overall_confidence:.0%} confident. "
                    f"{latest.explanation.summary}"
                )
            else:
                return (
                    f"I don't think we should trade {latest.symbol} right now. "
                    f"Reason: {latest.trade_blocked_reason}"
                )
        else:
            return latest.full_report()
    
    def ask(self, question: str) -> str:
        """
        Ask the consciousness a question about the market.
        
        This is a simple Q&A interface for interacting with the system.
        """
        question_lower = question.lower()
        
        if not self.output_history:
            return "I haven't analyzed any market data yet. Please provide market data first."
        
        latest = self.output_history[-1]
        
        # Handle common questions
        if "should" in question_lower and "trade" in question_lower:
            if latest.should_trade:
                return (
                    f"Yes, I recommend trading {latest.symbol}. "
                    f"Direction: {'LONG' if latest.decision.direction > 0 else 'SHORT'}. "
                    f"Confidence: {latest.overall_confidence:.0%}. "
                    f"Reason: {latest.explanation.summary}"
                )
            else:
                return f"No, I don't recommend trading right now. Reason: {latest.trade_blocked_reason}"
        
        elif "confidence" in question_lower:
            return (
                f"My overall confidence is {latest.overall_confidence:.0%}. "
                f"This is based on: "
                f"Market clarity ({1-latest.market_state.state_uncertainty:.0%}), "
                f"Forecast quality ({latest.forecast.calibration_score:.0%}), "
                f"Decision confidence ({latest.decision.confidence:.0%}), "
                f"System health ({latest.performance_state.health_score:.0%})."
            )
        
        elif "regime" in question_lower:
            return (
                f"The current market regime is {latest.market_state.primary_regime.value} "
                f"with {latest.market_state.regime_confidence:.0%} confidence."
            )
        
        elif "forecast" in question_lower or "predict" in question_lower:
            return (
                f"My forecast for {latest.symbol}: "
                f"Expected price: {latest.forecast.mean:.5f}. "
                f"95% confidence interval: [{latest.forecast.ci_95[0]:.5f}, {latest.forecast.ci_95[1]:.5f}]. "
                f"Probability of going up: {latest.forecast.prob_up:.0%}."
            )
        
        elif "performance" in question_lower or "how" in question_lower and "doing" in question_lower:
            perf = latest.performance_state
            return (
                f"System performance: "
                f"Total trades: {perf.total_trades}. "
                f"Win rate: {perf.win_rate:.0%}. "
                f"Sharpe ratio: {perf.sharpe_ratio:.2f}. "
                f"Max drawdown: {perf.max_drawdown:.1%}. "
                f"System health: {perf.health_score:.0%}."
            )
        
        elif "why" in question_lower:
            return latest.explanation.narrative
        
        elif "risk" in question_lower:
            if latest.decision.position_sizing:
                return (
                    f"Risk assessment: "
                    f"Position size: {latest.decision.position_sizing.size_pct*100:.1f}% of capital. "
                    f"Risk per trade: {latest.decision.position_sizing.risk_pct*100:.2f}%. "
                    f"Stop loss: {latest.decision.stop_loss:.5f}. "
                    f"Risk/reward ratio: {latest.decision.risk_reward_ratio:.1f}:1."
                )
            else:
                return "No position sizing calculated for current decision."
        
        else:
            return (
                f"I'm not sure how to answer that specific question. "
                f"Here's what I know: {latest.explanation.summary}"
            )


# Convenience function for quick usage
def create_consciousness(
    risk_params: Optional[RiskParameters] = None,
    explanation_style: ExplanationStyle = ExplanationStyle.TRADER,
) -> MarketConsciousness:
    """Create a new Market Consciousness instance."""
    return MarketConsciousness(
        risk_params=risk_params,
        explanation_style=explanation_style,
    )
