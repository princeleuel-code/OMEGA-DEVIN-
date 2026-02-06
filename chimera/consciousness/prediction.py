"""
LAYER 3: PREDICTION - Probabilistic Forecaster

The third layer of consciousness: PREDICTING the future.

This module doesn't just predict a single price - it predicts a DISTRIBUTION
of possible futures with explicit uncertainty quantification.

Key innovations:
1. Ensemble of models for robust predictions
2. Conformal prediction for calibrated uncertainty
3. Regime-conditional forecasting
4. Multi-horizon predictions (1 bar, 5 bars, 20 bars)

The output is NOT "price will be X" but rather:
"There's a 70% chance price will be between X and Y,
 with the most likely outcome being Z,
 but there's a 10% chance of an extreme move to W"

This is how professional quants think about markets.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
from enum import Enum
import numpy as np
from collections import deque

from .perception import MarketState, MarketRegime
from .understanding import CausalWorldModel, CausalQuery


class ForecastHorizon(Enum):
    """Prediction horizons."""
    IMMEDIATE = 1      # 1 bar
    SHORT = 5          # 5 bars
    MEDIUM = 20        # 20 bars
    LONG = 100         # 100 bars


@dataclass
class ForecastDistribution:
    """
    A probability distribution over future prices.
    
    This is NOT a point prediction - it's a full distribution
    that captures uncertainty about the future.
    """
    # Metadata
    timestamp: datetime
    symbol: str
    horizon: ForecastHorizon
    current_price: float
    
    # Distribution parameters
    mean: float                    # Expected value
    std: float                     # Standard deviation
    skew: float                    # Skewness (asymmetry)
    kurtosis: float                # Kurtosis (tail thickness)
    
    # Quantiles for non-parametric representation
    quantiles: Dict[float, float] = field(default_factory=dict)  # {0.05: price, 0.25: price, ...}
    
    # Confidence intervals
    ci_50: Tuple[float, float] = (0.0, 0.0)  # 50% CI
    ci_80: Tuple[float, float] = (0.0, 0.0)  # 80% CI
    ci_95: Tuple[float, float] = (0.0, 0.0)  # 95% CI
    
    # Tail risk
    var_95: float = 0.0           # Value at Risk (95%)
    cvar_95: float = 0.0          # Conditional VaR (Expected Shortfall)
    
    # Directional probabilities
    prob_up: float = 0.5          # P(price goes up)
    prob_down: float = 0.5        # P(price goes down)
    prob_big_move: float = 0.0    # P(|return| > 2 std)
    
    # Regime-conditional forecasts
    regime_forecasts: Dict[MarketRegime, float] = field(default_factory=dict)
    
    # Calibration score (how well-calibrated is this forecast?)
    calibration_score: float = 0.5
    
    # Model agreement (do different models agree?)
    model_agreement: float = 0.5
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp.isoformat(),
            "symbol": self.symbol,
            "horizon": self.horizon.value,
            "current_price": self.current_price,
            "mean": self.mean,
            "std": self.std,
            "skew": self.skew,
            "kurtosis": self.kurtosis,
            "quantiles": self.quantiles,
            "ci_50": self.ci_50,
            "ci_80": self.ci_80,
            "ci_95": self.ci_95,
            "var_95": self.var_95,
            "cvar_95": self.cvar_95,
            "prob_up": self.prob_up,
            "prob_down": self.prob_down,
            "prob_big_move": self.prob_big_move,
            "calibration_score": self.calibration_score,
            "model_agreement": self.model_agreement,
        }
    
    def expected_return(self) -> float:
        """Expected return as percentage."""
        if self.current_price == 0:
            return 0.0
        return (self.mean - self.current_price) / self.current_price * 100
    
    def risk_reward_ratio(self) -> float:
        """Risk-reward ratio based on distribution."""
        upside = self.quantiles.get(0.75, self.mean) - self.current_price
        downside = self.current_price - self.quantiles.get(0.25, self.mean)
        
        if downside <= 0:
            return float('inf') if upside > 0 else 0.0
        
        return upside / downside


@dataclass
class ForecastEnsemble:
    """Ensemble of forecasts from different models."""
    forecasts: List[ForecastDistribution]
    weights: List[float]
    combined: Optional[ForecastDistribution] = None
    
    def combine(self) -> ForecastDistribution:
        """Combine forecasts using weighted averaging."""
        if not self.forecasts:
            raise ValueError("No forecasts to combine")
        
        if len(self.weights) != len(self.forecasts):
            self.weights = [1.0 / len(self.forecasts)] * len(self.forecasts)
        
        # Normalize weights
        total_weight = sum(self.weights)
        weights = [w / total_weight for w in self.weights]
        
        # Weighted average of parameters
        mean = sum(w * f.mean for w, f in zip(weights, self.forecasts))
        
        # Variance of mixture (includes both within and between variance)
        var_within = sum(w * f.std**2 for w, f in zip(weights, self.forecasts))
        var_between = sum(w * (f.mean - mean)**2 for w, f in zip(weights, self.forecasts))
        std = math.sqrt(var_within + var_between)
        
        # Weighted average of other parameters
        skew = sum(w * f.skew for w, f in zip(weights, self.forecasts))
        kurtosis = sum(w * f.kurtosis for w, f in zip(weights, self.forecasts))
        prob_up = sum(w * f.prob_up for w, f in zip(weights, self.forecasts))
        prob_down = sum(w * f.prob_down for w, f in zip(weights, self.forecasts))
        
        # Combine quantiles
        quantiles = {}
        for q in [0.05, 0.10, 0.25, 0.50, 0.75, 0.90, 0.95]:
            quantiles[q] = sum(
                w * f.quantiles.get(q, f.mean) 
                for w, f in zip(weights, self.forecasts)
            )
        
        # Model agreement (inverse of coefficient of variation of means)
        if mean != 0:
            cv = np.std([f.mean for f in self.forecasts]) / abs(mean)
            model_agreement = max(0, 1 - cv)
        else:
            model_agreement = 0.5
        
        base = self.forecasts[0]
        self.combined = ForecastDistribution(
            timestamp=base.timestamp,
            symbol=base.symbol,
            horizon=base.horizon,
            current_price=base.current_price,
            mean=mean,
            std=std,
            skew=skew,
            kurtosis=kurtosis,
            quantiles=quantiles,
            ci_50=(quantiles.get(0.25, mean - std), quantiles.get(0.75, mean + std)),
            ci_80=(quantiles.get(0.10, mean - 1.28*std), quantiles.get(0.90, mean + 1.28*std)),
            ci_95=(quantiles.get(0.05, mean - 1.96*std), quantiles.get(0.95, mean + 1.96*std)),
            var_95=base.current_price - quantiles.get(0.05, mean - 1.96*std),
            cvar_95=sum(w * f.cvar_95 for w, f in zip(weights, self.forecasts)),
            prob_up=prob_up,
            prob_down=prob_down,
            prob_big_move=sum(w * f.prob_big_move for w, f in zip(weights, self.forecasts)),
            calibration_score=sum(w * f.calibration_score for w, f in zip(weights, self.forecasts)),
            model_agreement=model_agreement,
        )
        
        return self.combined


class BaseForecaster:
    """Base class for forecasting models."""
    
    def __init__(self, name: str):
        self.name = name
        self.prediction_history: List[Tuple[ForecastDistribution, float]] = []  # (forecast, actual)
        self.calibration_errors: deque = deque(maxlen=100)
    
    def forecast(
        self,
        state: MarketState,
        horizon: ForecastHorizon,
    ) -> ForecastDistribution:
        """Generate forecast. Override in subclasses."""
        raise NotImplementedError
    
    def update_calibration(self, forecast: ForecastDistribution, actual: float) -> None:
        """Update calibration based on realized outcome."""
        self.prediction_history.append((forecast, actual))
        
        # Check if actual was within confidence intervals
        in_50 = forecast.ci_50[0] <= actual <= forecast.ci_50[1]
        in_80 = forecast.ci_80[0] <= actual <= forecast.ci_80[1]
        in_95 = forecast.ci_95[0] <= actual <= forecast.ci_95[1]
        
        # Calibration error: should be 50% in 50% CI, 80% in 80% CI, etc.
        self.calibration_errors.append({
            "in_50": in_50,
            "in_80": in_80,
            "in_95": in_95,
            "error": actual - forecast.mean,
        })
    
    def get_calibration_score(self) -> float:
        """Compute calibration score based on historical accuracy."""
        if len(self.calibration_errors) < 10:
            return 0.5  # Not enough data
        
        # Check if coverage matches expected
        in_50_rate = sum(1 for e in self.calibration_errors if e["in_50"]) / len(self.calibration_errors)
        in_80_rate = sum(1 for e in self.calibration_errors if e["in_80"]) / len(self.calibration_errors)
        in_95_rate = sum(1 for e in self.calibration_errors if e["in_95"]) / len(self.calibration_errors)
        
        # Calibration error (lower is better)
        cal_error = (
            abs(in_50_rate - 0.50) +
            abs(in_80_rate - 0.80) +
            abs(in_95_rate - 0.95)
        ) / 3
        
        return max(0, 1 - cal_error * 2)


class MomentumForecaster(BaseForecaster):
    """Forecaster based on momentum and trend following."""
    
    def __init__(self):
        super().__init__("momentum")
    
    def forecast(
        self,
        state: MarketState,
        horizon: ForecastHorizon,
    ) -> ForecastDistribution:
        """Forecast based on momentum continuation."""
        current_price = state.price
        
        # Get momentum from state
        momentum = 0.0
        trend = 0.0
        volatility = 0.01
        
        if state.timeframe_states:
            momentums = [s.momentum for s in state.timeframe_states.values()]
            trends = [s.trend_direction for s in state.timeframe_states.values()]
            vols = [s.volatility for s in state.timeframe_states.values()]
            
            momentum = np.mean(momentums) if momentums else 0.0
            trend = np.mean(trends) if trends else 0.0
            volatility = np.mean(vols) if vols else 0.01
        
        # Scale by horizon
        horizon_scale = math.sqrt(horizon.value)
        
        # Expected return based on momentum
        expected_return = momentum * 0.01 * horizon.value  # 1% per unit momentum per bar
        
        # Adjust for trend strength
        expected_return *= (1 + abs(trend) * 0.5)
        
        # Mean prediction
        mean = current_price * (1 + expected_return)
        
        # Standard deviation scales with sqrt(time)
        std = current_price * volatility * horizon_scale
        
        # Skew based on trend direction
        skew = trend * 0.5
        
        # Higher kurtosis in volatile regimes
        kurtosis = 3.0 + volatility * 10
        
        # Directional probabilities
        if std > 0:
            z = (current_price - mean) / std
            prob_up = 0.5 + 0.5 * math.erf(-z / math.sqrt(2))
        else:
            prob_up = 0.5 if momentum >= 0 else 0.5
        
        prob_down = 1 - prob_up
        
        # Quantiles (assuming approximately normal)
        quantiles = {
            0.05: mean - 1.645 * std,
            0.10: mean - 1.28 * std,
            0.25: mean - 0.675 * std,
            0.50: mean,
            0.75: mean + 0.675 * std,
            0.90: mean + 1.28 * std,
            0.95: mean + 1.645 * std,
        }
        
        return ForecastDistribution(
            timestamp=datetime.now(timezone.utc),
            symbol=state.symbol,
            horizon=horizon,
            current_price=current_price,
            mean=mean,
            std=std,
            skew=skew,
            kurtosis=kurtosis,
            quantiles=quantiles,
            ci_50=(quantiles[0.25], quantiles[0.75]),
            ci_80=(quantiles[0.10], quantiles[0.90]),
            ci_95=(quantiles[0.05], quantiles[0.95]),
            var_95=current_price - quantiles[0.05],
            cvar_95=current_price - (mean - 2.06 * std),  # Expected shortfall
            prob_up=prob_up,
            prob_down=prob_down,
            prob_big_move=2 * (1 - 0.5 * (1 + math.erf(2 / math.sqrt(2)))),  # P(|z| > 2)
            calibration_score=self.get_calibration_score(),
            model_agreement=1.0,  # Single model
        )


class MeanReversionForecaster(BaseForecaster):
    """Forecaster based on mean reversion."""
    
    def __init__(self):
        super().__init__("mean_reversion")
        self.mean_price: Dict[str, float] = {}
        self.price_history: Dict[str, deque] = {}
    
    def forecast(
        self,
        state: MarketState,
        horizon: ForecastHorizon,
    ) -> ForecastDistribution:
        """Forecast based on mean reversion."""
        current_price = state.price
        symbol = state.symbol
        
        # Update price history
        if symbol not in self.price_history:
            self.price_history[symbol] = deque(maxlen=500)
        self.price_history[symbol].append(current_price)
        
        # Compute mean
        if len(self.price_history[symbol]) > 20:
            self.mean_price[symbol] = np.mean(list(self.price_history[symbol]))
        else:
            self.mean_price[symbol] = current_price
        
        mean_price = self.mean_price[symbol]
        
        # Get volatility from state
        volatility = 0.01
        if state.timeframe_states:
            vols = [s.volatility for s in state.timeframe_states.values()]
            volatility = np.mean(vols) if vols else 0.01
        
        # Mean reversion speed (half-life in bars)
        half_life = 20
        reversion_speed = 1 - math.exp(-math.log(2) / half_life * horizon.value)
        
        # Expected price reverts toward mean
        expected_price = current_price + reversion_speed * (mean_price - current_price)
        
        # Standard deviation
        horizon_scale = math.sqrt(horizon.value)
        std = current_price * volatility * horizon_scale
        
        # Mean reversion implies negative skew when above mean, positive when below
        deviation = (current_price - mean_price) / mean_price if mean_price != 0 else 0
        skew = -deviation * 2
        
        # Quantiles
        quantiles = {
            0.05: expected_price - 1.645 * std,
            0.10: expected_price - 1.28 * std,
            0.25: expected_price - 0.675 * std,
            0.50: expected_price,
            0.75: expected_price + 0.675 * std,
            0.90: expected_price + 1.28 * std,
            0.95: expected_price + 1.645 * std,
        }
        
        # Directional probabilities
        if expected_price > current_price:
            prob_up = 0.5 + 0.3 * reversion_speed
        else:
            prob_up = 0.5 - 0.3 * reversion_speed
        
        return ForecastDistribution(
            timestamp=datetime.now(timezone.utc),
            symbol=state.symbol,
            horizon=horizon,
            current_price=current_price,
            mean=expected_price,
            std=std,
            skew=skew,
            kurtosis=3.0,
            quantiles=quantiles,
            ci_50=(quantiles[0.25], quantiles[0.75]),
            ci_80=(quantiles[0.10], quantiles[0.90]),
            ci_95=(quantiles[0.05], quantiles[0.95]),
            var_95=current_price - quantiles[0.05],
            cvar_95=current_price - (expected_price - 2.06 * std),
            prob_up=prob_up,
            prob_down=1 - prob_up,
            prob_big_move=0.05,
            calibration_score=self.get_calibration_score(),
            model_agreement=1.0,
        )


class CausalForecaster(BaseForecaster):
    """Forecaster based on causal world model."""
    
    def __init__(self, world_model: CausalWorldModel):
        super().__init__("causal")
        self.world_model = world_model
    
    def forecast(
        self,
        state: MarketState,
        horizon: ForecastHorizon,
    ) -> ForecastDistribution:
        """Forecast using causal inference."""
        current_price = state.price
        
        # Query the causal model for price return prediction
        conditions = {
            "order_flow": state.order_flow_score,
            "momentum": state.timeframe_states.get("1m", type("", (), {"momentum": 0})()).momentum if state.timeframe_states else 0,
            "volatility": state.timeframe_states.get("1m", type("", (), {"volatility": 0.01})()).volatility if state.timeframe_states else 0.01,
            "trend": state.timeframe_states.get("1h", type("", (), {"trend_direction": 0})()).trend_direction if state.timeframe_states else 0,
        }
        
        query = CausalQuery(
            query_type="predict",
            target="price_return",
            conditions=conditions,
        )
        
        answer = self.world_model.query(query)
        
        # Convert predicted return to price
        predicted_return = answer.prediction * horizon.value * 0.001  # Scale by horizon
        expected_price = current_price * (1 + predicted_return)
        
        # Uncertainty from causal model
        base_uncertainty = answer.uncertainty
        
        # Get volatility
        volatility = conditions.get("volatility", 0.01)
        horizon_scale = math.sqrt(horizon.value)
        std = current_price * volatility * horizon_scale * (1 + base_uncertainty)
        
        # Quantiles
        quantiles = {
            0.05: expected_price - 1.645 * std,
            0.10: expected_price - 1.28 * std,
            0.25: expected_price - 0.675 * std,
            0.50: expected_price,
            0.75: expected_price + 0.675 * std,
            0.90: expected_price + 1.28 * std,
            0.95: expected_price + 1.645 * std,
        }
        
        # Directional probability from causal prediction
        prob_up = 0.5 + 0.4 * np.tanh(predicted_return * 100)
        
        return ForecastDistribution(
            timestamp=datetime.now(timezone.utc),
            symbol=state.symbol,
            horizon=horizon,
            current_price=current_price,
            mean=expected_price,
            std=std,
            skew=0.0,
            kurtosis=3.0,
            quantiles=quantiles,
            ci_50=(quantiles[0.25], quantiles[0.75]),
            ci_80=(quantiles[0.10], quantiles[0.90]),
            ci_95=(quantiles[0.05], quantiles[0.95]),
            var_95=current_price - quantiles[0.05],
            cvar_95=current_price - (expected_price - 2.06 * std),
            prob_up=prob_up,
            prob_down=1 - prob_up,
            prob_big_move=0.05 * (1 + base_uncertainty),
            calibration_score=self.get_calibration_score() * answer.confidence,
            model_agreement=answer.confidence,
        )


class RegimeConditionalForecaster(BaseForecaster):
    """Forecaster that conditions on detected regime."""
    
    def __init__(self):
        super().__init__("regime_conditional")
        
        # Regime-specific parameters (learned from data)
        self.regime_params = {
            MarketRegime.TRENDING_BULLISH: {"drift": 0.001, "vol_mult": 1.0},
            MarketRegime.TRENDING_BEARISH: {"drift": -0.001, "vol_mult": 1.0},
            MarketRegime.MEAN_REVERTING: {"drift": 0.0, "vol_mult": 0.8},
            MarketRegime.HIGH_VOLATILITY: {"drift": 0.0, "vol_mult": 2.0},
            MarketRegime.LOW_VOLATILITY: {"drift": 0.0, "vol_mult": 0.5},
            MarketRegime.BREAKOUT: {"drift": 0.002, "vol_mult": 1.5},
            MarketRegime.CONSOLIDATION: {"drift": 0.0, "vol_mult": 0.6},
            MarketRegime.UNKNOWN: {"drift": 0.0, "vol_mult": 1.0},
        }
    
    def forecast(
        self,
        state: MarketState,
        horizon: ForecastHorizon,
    ) -> ForecastDistribution:
        """Forecast conditioned on current regime."""
        current_price = state.price
        regime = state.primary_regime
        regime_conf = state.regime_confidence
        
        # Get regime parameters
        params = self.regime_params.get(regime, self.regime_params[MarketRegime.UNKNOWN])
        drift = params["drift"]
        vol_mult = params["vol_mult"]
        
        # Base volatility from state
        volatility = 0.01
        if state.timeframe_states:
            vols = [s.volatility for s in state.timeframe_states.values()]
            volatility = np.mean(vols) if vols else 0.01
        
        # Adjust for regime
        adjusted_vol = volatility * vol_mult
        
        # Expected price
        horizon_scale = horizon.value
        expected_return = drift * horizon_scale
        expected_price = current_price * (1 + expected_return)
        
        # Standard deviation
        std = current_price * adjusted_vol * math.sqrt(horizon_scale)
        
        # Regime-specific skew
        if regime in [MarketRegime.TRENDING_BULLISH, MarketRegime.BREAKOUT]:
            skew = 0.3
        elif regime in [MarketRegime.TRENDING_BEARISH]:
            skew = -0.3
        else:
            skew = 0.0
        
        # Quantiles
        quantiles = {
            0.05: expected_price - 1.645 * std,
            0.10: expected_price - 1.28 * std,
            0.25: expected_price - 0.675 * std,
            0.50: expected_price,
            0.75: expected_price + 0.675 * std,
            0.90: expected_price + 1.28 * std,
            0.95: expected_price + 1.645 * std,
        }
        
        # Directional probability
        if drift > 0:
            prob_up = 0.5 + 0.3 * regime_conf
        elif drift < 0:
            prob_up = 0.5 - 0.3 * regime_conf
        else:
            prob_up = 0.5
        
        # Regime-conditional forecasts
        regime_forecasts = {}
        for r, p in self.regime_params.items():
            r_return = p["drift"] * horizon_scale
            regime_forecasts[r] = current_price * (1 + r_return)
        
        return ForecastDistribution(
            timestamp=datetime.now(timezone.utc),
            symbol=state.symbol,
            horizon=horizon,
            current_price=current_price,
            mean=expected_price,
            std=std,
            skew=skew,
            kurtosis=3.0 + vol_mult,
            quantiles=quantiles,
            ci_50=(quantiles[0.25], quantiles[0.75]),
            ci_80=(quantiles[0.10], quantiles[0.90]),
            ci_95=(quantiles[0.05], quantiles[0.95]),
            var_95=current_price - quantiles[0.05],
            cvar_95=current_price - (expected_price - 2.06 * std),
            prob_up=prob_up,
            prob_down=1 - prob_up,
            prob_big_move=0.05 * vol_mult,
            calibration_score=self.get_calibration_score() * regime_conf,
            model_agreement=regime_conf,
            regime_forecasts=regime_forecasts,
        )


class ProbabilisticForecaster:
    """
    The main forecasting engine that combines multiple models.
    
    This is an ensemble forecaster that:
    1. Runs multiple forecasting models
    2. Weights them based on recent performance
    3. Combines into a single probabilistic forecast
    4. Maintains calibration through conformal prediction
    """
    
    def __init__(self, world_model: Optional[CausalWorldModel] = None):
        # Initialize forecasters
        self.forecasters: List[BaseForecaster] = [
            MomentumForecaster(),
            MeanReversionForecaster(),
            RegimeConditionalForecaster(),
        ]
        
        if world_model:
            self.forecasters.append(CausalForecaster(world_model))
        
        # Forecaster weights (updated based on performance)
        self.weights = [1.0 / len(self.forecasters)] * len(self.forecasters)
        
        # Conformal prediction calibration
        self.conformity_scores: deque = deque(maxlen=500)
        
        # Forecast history for calibration
        self.forecast_history: List[Tuple[ForecastDistribution, Optional[float]]] = []
    
    def forecast(
        self,
        state: MarketState,
        horizon: ForecastHorizon = ForecastHorizon.SHORT,
    ) -> ForecastDistribution:
        """Generate probabilistic forecast."""
        # Get forecasts from all models
        forecasts = []
        for forecaster in self.forecasters:
            try:
                f = forecaster.forecast(state, horizon)
                forecasts.append(f)
            except Exception:
                pass
        
        if not forecasts:
            # Fallback to simple forecast
            return self._fallback_forecast(state, horizon)
        
        # Create ensemble
        ensemble = ForecastEnsemble(
            forecasts=forecasts,
            weights=self.weights[:len(forecasts)],
        )
        
        # Combine forecasts
        combined = ensemble.combine()
        
        # Apply conformal calibration
        calibrated = self._conformal_calibrate(combined)
        
        # Store for later calibration update
        self.forecast_history.append((calibrated, None))
        
        return calibrated
    
    def _fallback_forecast(
        self,
        state: MarketState,
        horizon: ForecastHorizon,
    ) -> ForecastDistribution:
        """Simple fallback forecast when models fail."""
        current_price = state.price
        std = current_price * 0.01 * math.sqrt(horizon.value)
        
        return ForecastDistribution(
            timestamp=datetime.now(timezone.utc),
            symbol=state.symbol,
            horizon=horizon,
            current_price=current_price,
            mean=current_price,
            std=std,
            skew=0.0,
            kurtosis=3.0,
            quantiles={
                0.05: current_price - 1.645 * std,
                0.50: current_price,
                0.95: current_price + 1.645 * std,
            },
            ci_50=(current_price - 0.675 * std, current_price + 0.675 * std),
            ci_80=(current_price - 1.28 * std, current_price + 1.28 * std),
            ci_95=(current_price - 1.645 * std, current_price + 1.645 * std),
            prob_up=0.5,
            prob_down=0.5,
            calibration_score=0.3,
            model_agreement=0.0,
        )
    
    def _conformal_calibrate(
        self,
        forecast: ForecastDistribution,
    ) -> ForecastDistribution:
        """Apply conformal prediction to calibrate uncertainty."""
        if len(self.conformity_scores) < 20:
            return forecast  # Not enough data for calibration
        
        # Compute calibration factor from historical conformity scores
        scores = list(self.conformity_scores)
        
        # Adjust confidence intervals based on historical coverage
        # If we've been under-covering, widen intervals
        coverage_95 = sum(1 for s in scores if s <= 1.645) / len(scores)
        
        if coverage_95 < 0.90:
            # Under-covering, widen intervals
            scale = 1.0 + (0.95 - coverage_95)
        elif coverage_95 > 0.98:
            # Over-covering, narrow intervals
            scale = 1.0 - (coverage_95 - 0.95) * 0.5
        else:
            scale = 1.0
        
        # Apply scaling to standard deviation
        new_std = forecast.std * scale
        
        # Recompute quantiles
        mean = forecast.mean
        quantiles = {
            0.05: mean - 1.645 * new_std,
            0.10: mean - 1.28 * new_std,
            0.25: mean - 0.675 * new_std,
            0.50: mean,
            0.75: mean + 0.675 * new_std,
            0.90: mean + 1.28 * new_std,
            0.95: mean + 1.645 * new_std,
        }
        
        # Update forecast with calibrated values
        forecast.std = new_std
        forecast.quantiles = quantiles
        forecast.ci_50 = (quantiles[0.25], quantiles[0.75])
        forecast.ci_80 = (quantiles[0.10], quantiles[0.90])
        forecast.ci_95 = (quantiles[0.05], quantiles[0.95])
        forecast.var_95 = forecast.current_price - quantiles[0.05]
        
        return forecast
    
    def update(self, actual_price: float) -> None:
        """Update forecaster with realized price."""
        if not self.forecast_history:
            return
        
        # Get most recent forecast
        forecast, _ = self.forecast_history[-1]
        self.forecast_history[-1] = (forecast, actual_price)
        
        # Compute conformity score
        if forecast.std > 0:
            z_score = abs(actual_price - forecast.mean) / forecast.std
            self.conformity_scores.append(z_score)
        
        # Update individual forecaster calibration
        for forecaster in self.forecasters:
            forecaster.update_calibration(forecast, actual_price)
        
        # Update weights based on recent performance
        self._update_weights()
    
    def _update_weights(self) -> None:
        """Update forecaster weights based on recent performance."""
        if len(self.forecast_history) < 20:
            return
        
        # Compute recent accuracy for each forecaster
        accuracies = []
        for forecaster in self.forecasters:
            cal_score = forecaster.get_calibration_score()
            accuracies.append(cal_score)
        
        # Softmax weighting
        if sum(accuracies) > 0:
            exp_acc = [math.exp(a * 2) for a in accuracies]
            total = sum(exp_acc)
            self.weights = [e / total for e in exp_acc]
    
    def get_forecast_summary(self) -> Dict[str, Any]:
        """Get summary of forecaster state."""
        return {
            "num_forecasters": len(self.forecasters),
            "forecaster_names": [f.name for f in self.forecasters],
            "weights": self.weights,
            "calibration_scores": [f.get_calibration_score() for f in self.forecasters],
            "conformity_scores_count": len(self.conformity_scores),
            "forecast_history_count": len(self.forecast_history),
        }
