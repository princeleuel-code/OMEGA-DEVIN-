"""
LAYER 4: DECISION - Risk-Aware Actor

The fourth layer of consciousness: DECIDING what to do.

This module makes trading decisions based on:
1. Full probability distribution of outcomes (not just expected value)
2. Risk preferences (Kelly criterion, max drawdown constraints)
3. Uncertainty quantification (refuse to trade when uncertain)
4. Position sizing based on edge and risk

Key innovations:
- Decisions consider the ENTIRE distribution, not just the mean
- Kelly criterion for optimal position sizing
- Explicit "I don't know" state when uncertainty is too high
- Multi-objective optimization (return vs risk vs uncertainty)

This is how professional traders think - not "will it go up?" but
"what's my edge, what's my risk, and how much should I bet?"
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
from enum import Enum
import numpy as np

from .perception import MarketState, MarketRegime, LiquidityCondition
from .prediction import ForecastDistribution, ForecastHorizon


class DecisionType(Enum):
    """Types of trading decisions."""
    LONG = "long"
    SHORT = "short"
    HOLD = "hold"
    CLOSE_LONG = "close_long"
    CLOSE_SHORT = "close_short"
    REDUCE = "reduce"
    WAIT = "wait"           # Waiting for better setup
    REFUSE = "refuse"       # Refusing to trade due to uncertainty


class RefusalReason(Enum):
    """Reasons for refusing to trade."""
    HIGH_UNCERTAINTY = "high_uncertainty"
    LOW_CONFIDENCE = "low_confidence"
    POOR_RISK_REWARD = "poor_risk_reward"
    INSUFFICIENT_DATA = "insufficient_data"
    REGIME_UNCLEAR = "regime_unclear"
    LIQUIDITY_CRISIS = "liquidity_crisis"
    MODEL_DISAGREEMENT = "model_disagreement"
    DRAWDOWN_LIMIT = "drawdown_limit"
    CORRELATION_RISK = "correlation_risk"


@dataclass
class RiskParameters:
    """Risk management parameters."""
    max_position_pct: float = 0.1       # Max position as % of capital
    max_drawdown_pct: float = 0.15      # Max drawdown before stopping
    kelly_fraction: float = 0.25        # Fraction of Kelly to use
    min_risk_reward: float = 1.5        # Minimum risk/reward ratio
    max_correlation: float = 0.7        # Max correlation with existing positions
    min_confidence: float = 0.6         # Minimum confidence to trade
    max_uncertainty: float = 0.4        # Maximum uncertainty to trade
    min_liquidity_score: float = 0.3    # Minimum liquidity to trade
    stop_loss_atr: float = 2.0          # Stop loss in ATR units
    take_profit_atr: float = 3.0        # Take profit in ATR units


@dataclass
class PositionSizing:
    """Position sizing recommendation."""
    size: float                         # Position size (units)
    size_pct: float                     # Size as % of capital
    kelly_optimal: float                # Full Kelly size
    kelly_fraction_used: float          # Fraction of Kelly used
    risk_per_trade: float               # Risk in currency
    risk_pct: float                     # Risk as % of capital
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "size": self.size,
            "size_pct": self.size_pct,
            "kelly_optimal": self.kelly_optimal,
            "kelly_fraction_used": self.kelly_fraction_used,
            "risk_per_trade": self.risk_per_trade,
            "risk_pct": self.risk_pct,
        }


@dataclass
class TradingDecision:
    """
    A complete trading decision with full reasoning.
    
    This is NOT just "buy" or "sell" - it includes:
    - The decision itself
    - Position sizing
    - Entry/exit levels
    - Confidence and uncertainty
    - Full reasoning chain
    - Conditions for invalidation
    """
    # Metadata
    timestamp: datetime
    symbol: str
    
    # The decision
    decision: DecisionType
    direction: int  # 1 = long, -1 = short, 0 = neutral
    
    # Position sizing
    position_sizing: Optional[PositionSizing] = None
    
    # Entry/Exit levels
    entry_price: Optional[float] = None
    stop_loss: Optional[float] = None
    take_profit_1: Optional[float] = None
    take_profit_2: Optional[float] = None
    take_profit_3: Optional[float] = None
    
    # Confidence and uncertainty
    confidence: float = 0.0             # 0-1, how confident in the decision
    uncertainty: float = 1.0            # 0-1, how uncertain about the outcome
    edge: float = 0.0                   # Expected edge (expected return / risk)
    
    # Risk metrics
    expected_return: float = 0.0
    expected_risk: float = 0.0
    risk_reward_ratio: float = 0.0
    probability_of_profit: float = 0.5
    max_loss: float = 0.0
    
    # Reasoning
    reasoning: List[str] = field(default_factory=list)
    supporting_factors: List[str] = field(default_factory=list)
    opposing_factors: List[str] = field(default_factory=list)
    
    # Refusal (if applicable)
    refusal_reason: Optional[RefusalReason] = None
    refusal_explanation: Optional[str] = None
    
    # Invalidation conditions
    invalidation_conditions: List[str] = field(default_factory=list)
    
    # Model inputs (for auditability)
    forecast_used: Optional[Dict[str, Any]] = None
    state_used: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp.isoformat(),
            "symbol": self.symbol,
            "decision": self.decision.value,
            "direction": self.direction,
            "position_sizing": self.position_sizing.to_dict() if self.position_sizing else None,
            "entry_price": self.entry_price,
            "stop_loss": self.stop_loss,
            "take_profit_1": self.take_profit_1,
            "take_profit_2": self.take_profit_2,
            "take_profit_3": self.take_profit_3,
            "confidence": self.confidence,
            "uncertainty": self.uncertainty,
            "edge": self.edge,
            "expected_return": self.expected_return,
            "expected_risk": self.expected_risk,
            "risk_reward_ratio": self.risk_reward_ratio,
            "probability_of_profit": self.probability_of_profit,
            "reasoning": self.reasoning,
            "supporting_factors": self.supporting_factors,
            "opposing_factors": self.opposing_factors,
            "refusal_reason": self.refusal_reason.value if self.refusal_reason else None,
            "refusal_explanation": self.refusal_explanation,
            "invalidation_conditions": self.invalidation_conditions,
        }
    
    def is_actionable(self) -> bool:
        """Check if this decision is actionable (not WAIT or REFUSE)."""
        return self.decision not in [DecisionType.WAIT, DecisionType.REFUSE, DecisionType.HOLD]
    
    def summary(self) -> str:
        """Get a one-line summary of the decision."""
        if self.decision == DecisionType.REFUSE:
            return f"REFUSE: {self.refusal_explanation}"
        elif self.decision == DecisionType.WAIT:
            return f"WAIT: {self.reasoning[0] if self.reasoning else 'No clear setup'}"
        elif self.decision == DecisionType.HOLD:
            return f"HOLD: {self.reasoning[0] if self.reasoning else 'Maintain position'}"
        else:
            size_str = f"{self.position_sizing.size_pct*100:.1f}%" if self.position_sizing else "?"
            return f"{self.decision.value.upper()} {self.symbol} @ {self.entry_price:.5f}, size={size_str}, conf={self.confidence:.0%}"


class RiskAwareActor:
    """
    The decision-making engine that considers full risk profile.
    
    This actor:
    1. Evaluates the forecast distribution
    2. Computes optimal position size using Kelly criterion
    3. Checks risk constraints
    4. Makes a decision with full reasoning
    5. Can REFUSE to trade when uncertain
    """
    
    def __init__(self, risk_params: Optional[RiskParameters] = None):
        self.risk_params = risk_params or RiskParameters()
        
        # Current state
        self.capital = 10000.0
        self.current_positions: Dict[str, float] = {}  # symbol -> size
        self.current_drawdown = 0.0
        self.peak_equity = self.capital
        
        # Decision history
        self.decision_history: List[TradingDecision] = []
        
        # Performance tracking
        self.decisions_made = 0
        self.decisions_refused = 0
        self.profitable_decisions = 0
    
    def decide(
        self,
        state: MarketState,
        forecast: ForecastDistribution,
        current_position: float = 0.0,
    ) -> TradingDecision:
        """
        Make a trading decision based on state and forecast.
        
        This is the core decision function that:
        1. Checks if we should refuse to trade
        2. Determines direction
        3. Computes position size
        4. Sets entry/exit levels
        5. Documents reasoning
        """
        timestamp = datetime.now(timezone.utc)
        symbol = state.symbol
        current_price = state.price
        
        reasoning = []
        supporting = []
        opposing = []
        
        # Step 1: Check refusal conditions
        refusal = self._check_refusal_conditions(state, forecast)
        if refusal:
            reason, explanation = refusal
            self.decisions_refused += 1
            return TradingDecision(
                timestamp=timestamp,
                symbol=symbol,
                decision=DecisionType.REFUSE,
                direction=0,
                confidence=0.0,
                uncertainty=1.0,
                refusal_reason=reason,
                refusal_explanation=explanation,
                reasoning=[explanation],
                forecast_used=forecast.to_dict(),
                state_used=state.to_dict(),
            )
        
        # Step 2: Determine direction
        direction, direction_confidence, direction_reasoning = self._determine_direction(
            state, forecast
        )
        reasoning.extend(direction_reasoning)
        
        if direction == 0:
            # No clear direction
            return TradingDecision(
                timestamp=timestamp,
                symbol=symbol,
                decision=DecisionType.WAIT,
                direction=0,
                confidence=direction_confidence,
                uncertainty=state.state_uncertainty,
                reasoning=["No clear directional edge detected"],
                forecast_used=forecast.to_dict(),
                state_used=state.to_dict(),
            )
        
        # Step 3: Compute expected edge
        edge, edge_reasoning = self._compute_edge(forecast, direction)
        reasoning.extend(edge_reasoning)
        
        if edge < 0:
            opposing.append(f"Negative expected edge: {edge:.2%}")
            return TradingDecision(
                timestamp=timestamp,
                symbol=symbol,
                decision=DecisionType.WAIT,
                direction=0,
                confidence=direction_confidence,
                uncertainty=state.state_uncertainty,
                edge=edge,
                reasoning=["Negative expected edge - waiting for better setup"],
                opposing_factors=opposing,
                forecast_used=forecast.to_dict(),
                state_used=state.to_dict(),
            )
        
        supporting.append(f"Positive expected edge: {edge:.2%}")
        
        # Step 4: Compute position size using Kelly criterion
        position_sizing = self._compute_position_size(
            forecast, direction, current_price, edge
        )
        reasoning.append(f"Kelly-optimal size: {position_sizing.kelly_optimal:.2%}, using {position_sizing.kelly_fraction_used:.0%}")
        
        # Step 5: Compute entry/exit levels
        entry_price = current_price
        stop_loss, take_profits = self._compute_exit_levels(
            state, forecast, direction, entry_price
        )
        
        # Step 6: Compute risk metrics
        risk_reward = self._compute_risk_reward(
            entry_price, stop_loss, take_profits[0] if take_profits else entry_price
        )
        
        if risk_reward < self.risk_params.min_risk_reward:
            opposing.append(f"Poor risk/reward: {risk_reward:.2f}")
            return TradingDecision(
                timestamp=timestamp,
                symbol=symbol,
                decision=DecisionType.WAIT,
                direction=0,
                confidence=direction_confidence,
                uncertainty=state.state_uncertainty,
                risk_reward_ratio=risk_reward,
                reasoning=[f"Risk/reward {risk_reward:.2f} below minimum {self.risk_params.min_risk_reward}"],
                opposing_factors=opposing,
                forecast_used=forecast.to_dict(),
                state_used=state.to_dict(),
            )
        
        supporting.append(f"Good risk/reward: {risk_reward:.2f}")
        
        # Step 7: Check if we need to manage existing position
        if current_position != 0:
            decision_type = self._manage_existing_position(
                current_position, direction, state, forecast
            )
        else:
            decision_type = DecisionType.LONG if direction > 0 else DecisionType.SHORT
        
        # Step 8: Compute final confidence
        confidence = self._compute_final_confidence(
            direction_confidence, forecast.model_agreement, forecast.calibration_score
        )
        
        # Step 9: Document invalidation conditions
        invalidation = self._compute_invalidation_conditions(
            state, forecast, direction, stop_loss
        )
        
        # Step 10: Gather supporting and opposing factors
        supporting.extend(self._gather_supporting_factors(state, forecast, direction))
        opposing.extend(self._gather_opposing_factors(state, forecast, direction))
        
        self.decisions_made += 1
        
        decision = TradingDecision(
            timestamp=timestamp,
            symbol=symbol,
            decision=decision_type,
            direction=direction,
            position_sizing=position_sizing,
            entry_price=entry_price,
            stop_loss=stop_loss,
            take_profit_1=take_profits[0] if len(take_profits) > 0 else None,
            take_profit_2=take_profits[1] if len(take_profits) > 1 else None,
            take_profit_3=take_profits[2] if len(take_profits) > 2 else None,
            confidence=confidence,
            uncertainty=state.state_uncertainty,
            edge=edge,
            expected_return=forecast.expected_return(),
            expected_risk=position_sizing.risk_pct,
            risk_reward_ratio=risk_reward,
            probability_of_profit=forecast.prob_up if direction > 0 else forecast.prob_down,
            max_loss=position_sizing.risk_per_trade,
            reasoning=reasoning,
            supporting_factors=supporting,
            opposing_factors=opposing,
            invalidation_conditions=invalidation,
            forecast_used=forecast.to_dict(),
            state_used=state.to_dict(),
        )
        
        self.decision_history.append(decision)
        
        return decision
    
    def _check_refusal_conditions(
        self,
        state: MarketState,
        forecast: ForecastDistribution,
    ) -> Optional[Tuple[RefusalReason, str]]:
        """Check if we should refuse to trade."""
        
        # High uncertainty
        if state.state_uncertainty > self.risk_params.max_uncertainty:
            return (
                RefusalReason.HIGH_UNCERTAINTY,
                f"State uncertainty {state.state_uncertainty:.0%} exceeds maximum {self.risk_params.max_uncertainty:.0%}"
            )
        
        # Low confidence
        if forecast.calibration_score < self.risk_params.min_confidence:
            return (
                RefusalReason.LOW_CONFIDENCE,
                f"Forecast confidence {forecast.calibration_score:.0%} below minimum {self.risk_params.min_confidence:.0%}"
            )
        
        # Model disagreement
        if forecast.model_agreement < 0.3:
            return (
                RefusalReason.MODEL_DISAGREEMENT,
                f"Models disagree significantly (agreement: {forecast.model_agreement:.0%})"
            )
        
        # Insufficient data
        if state.data_quality < 0.3:
            return (
                RefusalReason.INSUFFICIENT_DATA,
                f"Insufficient data quality ({state.data_quality:.0%})"
            )
        
        # Regime unclear
        if state.regime_confidence < 0.4 and state.primary_regime == MarketRegime.UNKNOWN:
            return (
                RefusalReason.REGIME_UNCLEAR,
                f"Market regime unclear (confidence: {state.regime_confidence:.0%})"
            )
        
        # Liquidity crisis
        if state.liquidity_condition == LiquidityCondition.CRISIS:
            return (
                RefusalReason.LIQUIDITY_CRISIS,
                "Liquidity crisis detected - refusing to trade"
            )
        
        if state.liquidity_score < self.risk_params.min_liquidity_score:
            return (
                RefusalReason.LIQUIDITY_CRISIS,
                f"Liquidity score {state.liquidity_score:.0%} below minimum {self.risk_params.min_liquidity_score:.0%}"
            )
        
        # Drawdown limit
        if self.current_drawdown > self.risk_params.max_drawdown_pct:
            return (
                RefusalReason.DRAWDOWN_LIMIT,
                f"Current drawdown {self.current_drawdown:.0%} exceeds maximum {self.risk_params.max_drawdown_pct:.0%}"
            )
        
        return None
    
    def _determine_direction(
        self,
        state: MarketState,
        forecast: ForecastDistribution,
    ) -> Tuple[int, float, List[str]]:
        """Determine trading direction based on multiple factors."""
        reasoning = []
        
        # Factor 1: Forecast direction
        forecast_direction = 1 if forecast.prob_up > 0.5 else -1 if forecast.prob_down > 0.5 else 0
        forecast_strength = abs(forecast.prob_up - 0.5) * 2
        reasoning.append(f"Forecast: {'bullish' if forecast_direction > 0 else 'bearish' if forecast_direction < 0 else 'neutral'} ({forecast.prob_up:.0%} up)")
        
        # Factor 2: Order flow
        flow_direction = 1 if state.order_flow_score > 0.2 else -1 if state.order_flow_score < -0.2 else 0
        reasoning.append(f"Order flow: {'bullish' if flow_direction > 0 else 'bearish' if flow_direction < 0 else 'neutral'} ({state.order_flow_score:.2f})")
        
        # Factor 3: Regime
        regime_direction = 0
        if state.primary_regime == MarketRegime.TRENDING_BULLISH:
            regime_direction = 1
        elif state.primary_regime == MarketRegime.TRENDING_BEARISH:
            regime_direction = -1
        reasoning.append(f"Regime: {state.primary_regime.value}")
        
        # Factor 4: Multi-timeframe trend
        mtf_direction = 0
        if state.timeframe_states:
            trends = [s.trend_direction for s in state.timeframe_states.values()]
            avg_trend = np.mean(trends) if trends else 0
            mtf_direction = 1 if avg_trend > 0.3 else -1 if avg_trend < -0.3 else 0
            reasoning.append(f"MTF trend: {avg_trend:.2f}")
        
        # Combine factors with weights
        weights = {
            "forecast": 0.4,
            "flow": 0.25,
            "regime": 0.2,
            "mtf": 0.15,
        }
        
        combined_score = (
            weights["forecast"] * forecast_direction * forecast_strength +
            weights["flow"] * flow_direction +
            weights["regime"] * regime_direction * state.regime_confidence +
            weights["mtf"] * mtf_direction
        )
        
        # Determine direction
        if combined_score > 0.2:
            direction = 1
        elif combined_score < -0.2:
            direction = -1
        else:
            direction = 0
        
        # Confidence based on agreement
        agreements = [forecast_direction, flow_direction, regime_direction, mtf_direction]
        non_zero = [a for a in agreements if a != 0]
        if non_zero:
            agreement_rate = sum(1 for a in non_zero if a == direction) / len(non_zero)
        else:
            agreement_rate = 0.5
        
        confidence = agreement_rate * forecast.calibration_score
        
        return direction, confidence, reasoning
    
    def _compute_edge(
        self,
        forecast: ForecastDistribution,
        direction: int,
    ) -> Tuple[float, List[str]]:
        """Compute expected edge from the forecast."""
        reasoning = []
        
        # Expected return in the direction we're trading
        if direction > 0:
            # Long: profit if price goes up
            expected_profit = forecast.quantiles.get(0.75, forecast.mean) - forecast.current_price
            expected_loss = forecast.current_price - forecast.quantiles.get(0.25, forecast.mean)
            prob_profit = forecast.prob_up
        else:
            # Short: profit if price goes down
            expected_profit = forecast.current_price - forecast.quantiles.get(0.25, forecast.mean)
            expected_loss = forecast.quantiles.get(0.75, forecast.mean) - forecast.current_price
            prob_profit = forecast.prob_down
        
        # Expected value
        ev = prob_profit * expected_profit - (1 - prob_profit) * expected_loss
        
        # Edge as percentage of price
        edge = ev / forecast.current_price if forecast.current_price > 0 else 0
        
        reasoning.append(f"Expected profit: {expected_profit:.5f} ({prob_profit:.0%} prob)")
        reasoning.append(f"Expected loss: {expected_loss:.5f} ({1-prob_profit:.0%} prob)")
        reasoning.append(f"Expected edge: {edge:.2%}")
        
        return edge, reasoning
    
    def _compute_position_size(
        self,
        forecast: ForecastDistribution,
        direction: int,
        current_price: float,
        edge: float,
    ) -> PositionSizing:
        """Compute position size using Kelly criterion."""
        # Kelly formula: f* = (p*b - q) / b
        # where p = prob of win, q = prob of loss, b = win/loss ratio
        
        if direction > 0:
            prob_win = forecast.prob_up
            win_amount = forecast.quantiles.get(0.75, forecast.mean) - current_price
            loss_amount = current_price - forecast.quantiles.get(0.25, forecast.mean)
        else:
            prob_win = forecast.prob_down
            win_amount = current_price - forecast.quantiles.get(0.25, forecast.mean)
            loss_amount = forecast.quantiles.get(0.75, forecast.mean) - current_price
        
        prob_loss = 1 - prob_win
        
        if loss_amount <= 0:
            loss_amount = current_price * 0.01  # Default 1% loss
        
        win_loss_ratio = win_amount / loss_amount if loss_amount > 0 else 1
        
        # Kelly fraction
        kelly = (prob_win * win_loss_ratio - prob_loss) / win_loss_ratio if win_loss_ratio > 0 else 0
        kelly = max(0, kelly)  # Can't be negative
        
        # Apply Kelly fraction (use only a fraction of Kelly for safety)
        kelly_fraction = self.risk_params.kelly_fraction
        position_pct = kelly * kelly_fraction
        
        # Apply maximum position constraint
        position_pct = min(position_pct, self.risk_params.max_position_pct)
        
        # Compute actual size
        position_value = self.capital * position_pct
        size = position_value / current_price if current_price > 0 else 0
        
        # Risk per trade
        risk_per_trade = position_value * (loss_amount / current_price)
        risk_pct = risk_per_trade / self.capital if self.capital > 0 else 0
        
        return PositionSizing(
            size=size,
            size_pct=position_pct,
            kelly_optimal=kelly,
            kelly_fraction_used=kelly_fraction,
            risk_per_trade=risk_per_trade,
            risk_pct=risk_pct,
        )
    
    def _compute_exit_levels(
        self,
        state: MarketState,
        forecast: ForecastDistribution,
        direction: int,
        entry_price: float,
    ) -> Tuple[float, List[float]]:
        """Compute stop loss and take profit levels."""
        # Get ATR from state
        atr = 0.0
        if state.timeframe_states:
            # Use volatility as proxy for ATR
            vols = [s.volatility for s in state.timeframe_states.values()]
            avg_vol = np.mean(vols) if vols else 0.01
            atr = entry_price * avg_vol * 10  # Scale volatility to ATR-like value
        
        if atr == 0:
            atr = entry_price * 0.01  # Default 1%
        
        # Stop loss
        stop_distance = atr * self.risk_params.stop_loss_atr
        if direction > 0:
            stop_loss = entry_price - stop_distance
        else:
            stop_loss = entry_price + stop_distance
        
        # Take profits at multiple levels
        tp_distances = [
            atr * self.risk_params.take_profit_atr * 0.5,  # TP1: 50% of target
            atr * self.risk_params.take_profit_atr,        # TP2: Full target
            atr * self.risk_params.take_profit_atr * 1.5,  # TP3: Extended target
        ]
        
        take_profits = []
        for tp_dist in tp_distances:
            if direction > 0:
                take_profits.append(entry_price + tp_dist)
            else:
                take_profits.append(entry_price - tp_dist)
        
        return stop_loss, take_profits
    
    def _compute_risk_reward(
        self,
        entry: float,
        stop: float,
        target: float,
    ) -> float:
        """Compute risk/reward ratio."""
        risk = abs(entry - stop)
        reward = abs(target - entry)
        
        if risk == 0:
            return 0.0
        
        return reward / risk
    
    def _manage_existing_position(
        self,
        current_position: float,
        new_direction: int,
        state: MarketState,
        forecast: ForecastDistribution,
    ) -> DecisionType:
        """Determine how to manage existing position."""
        current_direction = 1 if current_position > 0 else -1 if current_position < 0 else 0
        
        if current_direction == new_direction:
            # Same direction - hold or add
            return DecisionType.HOLD
        elif current_direction == -new_direction:
            # Opposite direction - close
            if current_direction > 0:
                return DecisionType.CLOSE_LONG
            else:
                return DecisionType.CLOSE_SHORT
        else:
            # No position - new trade
            return DecisionType.LONG if new_direction > 0 else DecisionType.SHORT
    
    def _compute_final_confidence(
        self,
        direction_confidence: float,
        model_agreement: float,
        calibration_score: float,
    ) -> float:
        """Compute final confidence score."""
        # Weighted combination
        confidence = (
            0.4 * direction_confidence +
            0.3 * model_agreement +
            0.3 * calibration_score
        )
        
        return min(1.0, max(0.0, confidence))
    
    def _compute_invalidation_conditions(
        self,
        state: MarketState,
        forecast: ForecastDistribution,
        direction: int,
        stop_loss: float,
    ) -> List[str]:
        """Compute conditions that would invalidate this trade."""
        conditions = []
        
        # Price invalidation
        if direction > 0:
            conditions.append(f"Price closes below {stop_loss:.5f}")
        else:
            conditions.append(f"Price closes above {stop_loss:.5f}")
        
        # Regime change
        conditions.append(f"Regime changes from {state.primary_regime.value}")
        
        # Order flow reversal
        if state.order_flow_score > 0.2:
            conditions.append("Order flow turns bearish (< -0.2)")
        elif state.order_flow_score < -0.2:
            conditions.append("Order flow turns bullish (> 0.2)")
        
        # Time invalidation
        conditions.append(f"Setup not triggered within {forecast.horizon.value * 2} bars")
        
        return conditions
    
    def _gather_supporting_factors(
        self,
        state: MarketState,
        forecast: ForecastDistribution,
        direction: int,
    ) -> List[str]:
        """Gather factors supporting the trade."""
        factors = []
        
        # Forecast alignment
        if (direction > 0 and forecast.prob_up > 0.6) or (direction < 0 and forecast.prob_down > 0.6):
            factors.append(f"Strong directional probability ({max(forecast.prob_up, forecast.prob_down):.0%})")
        
        # Order flow alignment
        if (direction > 0 and state.order_flow_score > 0.3) or (direction < 0 and state.order_flow_score < -0.3):
            factors.append(f"Order flow confirms direction ({state.order_flow_score:.2f})")
        
        # Regime alignment
        if direction > 0 and state.primary_regime == MarketRegime.TRENDING_BULLISH:
            factors.append("Bullish regime confirmed")
        elif direction < 0 and state.primary_regime == MarketRegime.TRENDING_BEARISH:
            factors.append("Bearish regime confirmed")
        
        # Good liquidity
        if state.liquidity_score > 0.7:
            factors.append(f"Good liquidity ({state.liquidity_score:.0%})")
        
        # Model agreement
        if forecast.model_agreement > 0.7:
            factors.append(f"Strong model agreement ({forecast.model_agreement:.0%})")
        
        return factors
    
    def _gather_opposing_factors(
        self,
        state: MarketState,
        forecast: ForecastDistribution,
        direction: int,
    ) -> List[str]:
        """Gather factors opposing the trade."""
        factors = []
        
        # Uncertainty
        if state.state_uncertainty > 0.3:
            factors.append(f"Elevated uncertainty ({state.state_uncertainty:.0%})")
        
        # Counter-trend
        if state.timeframe_states:
            trends = [s.trend_direction for s in state.timeframe_states.values()]
            avg_trend = np.mean(trends) if trends else 0
            if (direction > 0 and avg_trend < -0.2) or (direction < 0 and avg_trend > 0.2):
                factors.append(f"Trading against MTF trend ({avg_trend:.2f})")
        
        # Volatility regime
        if state.primary_regime == MarketRegime.HIGH_VOLATILITY:
            factors.append("High volatility regime - increased risk")
        
        # Thin liquidity
        if state.liquidity_score < 0.5:
            factors.append(f"Thin liquidity ({state.liquidity_score:.0%})")
        
        # Model disagreement
        if forecast.model_agreement < 0.5:
            factors.append(f"Model disagreement ({forecast.model_agreement:.0%})")
        
        return factors
    
    def update_equity(self, new_equity: float) -> None:
        """Update equity and drawdown tracking."""
        self.capital = new_equity
        
        if new_equity > self.peak_equity:
            self.peak_equity = new_equity
        
        self.current_drawdown = (self.peak_equity - new_equity) / self.peak_equity
    
    def get_decision_summary(self) -> Dict[str, Any]:
        """Get summary of decision-making performance."""
        return {
            "decisions_made": self.decisions_made,
            "decisions_refused": self.decisions_refused,
            "refusal_rate": self.decisions_refused / max(1, self.decisions_made + self.decisions_refused),
            "current_capital": self.capital,
            "current_drawdown": self.current_drawdown,
            "peak_equity": self.peak_equity,
        }
