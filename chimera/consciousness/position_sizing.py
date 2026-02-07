"""
Risk-Adjusted Position Sizing Intelligence Module

This module implements institutional-grade position sizing:
1. Kelly Criterion - Optimal bet sizing based on edge
2. Volatility-Adjusted Sizing - Scale position based on ATR
3. Correlation-Aware Sizing - Reduce size when correlated positions exist
4. Drawdown-Based Scaling - Reduce size during drawdowns
5. Risk Parity - Equal risk contribution across positions

This is how the BEST hedge funds and prop firms size their positions -
not fixed lot sizes, but dynamic risk-adjusted sizing.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple, Any
from enum import Enum
import math


class RiskLevel(Enum):
    """Risk level categories"""
    ULTRA_CONSERVATIVE = "ultra_conservative"
    CONSERVATIVE = "conservative"
    MODERATE = "moderate"
    AGGRESSIVE = "aggressive"
    ULTRA_AGGRESSIVE = "ultra_aggressive"


class DrawdownState(Enum):
    """Drawdown state"""
    NONE = "none"
    MINOR = "minor"
    MODERATE = "moderate"
    SEVERE = "severe"
    CRITICAL = "critical"


@dataclass
class PositionSizeResult:
    """Result of position sizing calculation"""
    # Core sizing
    position_size: float  # In lots or units
    position_value: float  # In account currency
    risk_amount: float  # Dollar risk
    risk_percent: float  # Percent of account at risk
    
    # Kelly analysis
    kelly_fraction: float  # Optimal Kelly fraction
    half_kelly: float  # Half Kelly (more conservative)
    quarter_kelly: float  # Quarter Kelly (very conservative)
    recommended_kelly: float  # Recommended Kelly based on confidence
    
    # Adjustments applied
    volatility_adjustment: float  # Multiplier from volatility
    correlation_adjustment: float  # Multiplier from correlation
    drawdown_adjustment: float  # Multiplier from drawdown
    regime_adjustment: float  # Multiplier from market regime
    confidence_adjustment: float  # Multiplier from signal confidence
    
    # Final multiplier
    total_adjustment: float  # Combined adjustment multiplier
    
    # Risk metrics
    max_loss: float  # Maximum potential loss
    expected_profit: float  # Expected profit based on win rate
    risk_reward_ratio: float  # Risk/reward ratio
    
    # Position limits
    max_position_size: float  # Maximum allowed position
    min_position_size: float  # Minimum viable position
    is_within_limits: bool  # Whether size is within limits
    
    # Warnings
    warnings: List[str]
    
    def get_summary(self) -> str:
        return f"""
POSITION SIZING RESULT
======================
Position Size: {self.position_size:.4f} lots
Position Value: ${self.position_value:,.2f}
Risk Amount: ${self.risk_amount:,.2f} ({self.risk_percent:.2%})

Kelly Analysis:
  Full Kelly: {self.kelly_fraction:.2%}
  Half Kelly: {self.half_kelly:.2%}
  Quarter Kelly: {self.quarter_kelly:.2%}
  Recommended: {self.recommended_kelly:.2%}

Adjustments:
  Volatility: {self.volatility_adjustment:.2f}x
  Correlation: {self.correlation_adjustment:.2f}x
  Drawdown: {self.drawdown_adjustment:.2f}x
  Regime: {self.regime_adjustment:.2f}x
  Confidence: {self.confidence_adjustment:.2f}x
  Total: {self.total_adjustment:.2f}x

Risk Metrics:
  Max Loss: ${self.max_loss:,.2f}
  Expected Profit: ${self.expected_profit:,.2f}
  Risk/Reward: {self.risk_reward_ratio:.2f}

Limits:
  Max Size: {self.max_position_size:.4f}
  Min Size: {self.min_position_size:.4f}
  Within Limits: {'YES' if self.is_within_limits else 'NO'}

Warnings: {', '.join(self.warnings) if self.warnings else 'None'}
"""


@dataclass
class PortfolioRisk:
    """Portfolio-level risk metrics"""
    total_exposure: float  # Total position value
    total_risk: float  # Total dollar risk
    total_risk_percent: float  # Total risk as percent of account
    
    # Correlation metrics
    average_correlation: float  # Average correlation between positions
    diversification_ratio: float  # 1 = fully diversified, 0 = fully correlated
    
    # Position metrics
    num_positions: int
    largest_position_percent: float
    concentration_risk: float  # Herfindahl index
    
    # Risk limits
    max_total_risk: float
    remaining_risk_budget: float
    can_add_position: bool
    
    def get_summary(self) -> str:
        return f"""
PORTFOLIO RISK
==============
Total Exposure: ${self.total_exposure:,.2f}
Total Risk: ${self.total_risk:,.2f} ({self.total_risk_percent:.2%})

Correlation:
  Average: {self.average_correlation:.2f}
  Diversification: {self.diversification_ratio:.2%}

Positions:
  Count: {self.num_positions}
  Largest: {self.largest_position_percent:.2%}
  Concentration: {self.concentration_risk:.2f}

Risk Budget:
  Max Total Risk: ${self.max_total_risk:,.2f}
  Remaining: ${self.remaining_risk_budget:,.2f}
  Can Add Position: {'YES' if self.can_add_position else 'NO'}
"""


class PositionSizingIntelligence:
    """
    Risk-Adjusted Position Sizing Intelligence Engine
    
    Implements institutional-grade position sizing that adapts to:
    - Market volatility
    - Portfolio correlation
    - Account drawdown
    - Market regime
    - Signal confidence
    
    This is how professional traders actually size positions.
    """
    
    # Risk level parameters
    RISK_PARAMS = {
        RiskLevel.ULTRA_CONSERVATIVE: {
            "max_risk_per_trade": 0.005,  # 0.5%
            "max_total_risk": 0.02,  # 2%
            "kelly_fraction": 0.25,  # Quarter Kelly
            "max_positions": 3,
            "max_correlation": 0.3
        },
        RiskLevel.CONSERVATIVE: {
            "max_risk_per_trade": 0.01,  # 1%
            "max_total_risk": 0.04,  # 4%
            "kelly_fraction": 0.33,  # Third Kelly
            "max_positions": 4,
            "max_correlation": 0.4
        },
        RiskLevel.MODERATE: {
            "max_risk_per_trade": 0.02,  # 2%
            "max_total_risk": 0.06,  # 6%
            "kelly_fraction": 0.5,  # Half Kelly
            "max_positions": 5,
            "max_correlation": 0.5
        },
        RiskLevel.AGGRESSIVE: {
            "max_risk_per_trade": 0.03,  # 3%
            "max_total_risk": 0.10,  # 10%
            "kelly_fraction": 0.75,  # Three-quarter Kelly
            "max_positions": 6,
            "max_correlation": 0.6
        },
        RiskLevel.ULTRA_AGGRESSIVE: {
            "max_risk_per_trade": 0.05,  # 5%
            "max_total_risk": 0.15,  # 15%
            "kelly_fraction": 1.0,  # Full Kelly
            "max_positions": 8,
            "max_correlation": 0.7
        }
    }
    
    # Drawdown scaling
    DRAWDOWN_SCALING = {
        DrawdownState.NONE: 1.0,
        DrawdownState.MINOR: 0.8,
        DrawdownState.MODERATE: 0.6,
        DrawdownState.SEVERE: 0.4,
        DrawdownState.CRITICAL: 0.2
    }
    
    def __init__(
        self,
        account_balance: float,
        risk_level: RiskLevel = RiskLevel.MODERATE,
        base_risk_per_trade: float = 0.01,  # 1% default
        use_kelly: bool = True,
        use_volatility_adjustment: bool = True,
        use_correlation_adjustment: bool = True,
        use_drawdown_adjustment: bool = True,
        min_position_size: float = 0.01,  # Minimum lot size
        max_position_size: float = 10.0,  # Maximum lot size
        lot_size: float = 100000  # Standard lot size
    ):
        """
        Initialize Position Sizing Intelligence
        
        Args:
            account_balance: Current account balance
            risk_level: Risk tolerance level
            base_risk_per_trade: Base risk per trade as decimal
            use_kelly: Whether to use Kelly Criterion
            use_volatility_adjustment: Whether to adjust for volatility
            use_correlation_adjustment: Whether to adjust for correlation
            use_drawdown_adjustment: Whether to adjust for drawdown
            min_position_size: Minimum position size in lots
            max_position_size: Maximum position size in lots
            lot_size: Standard lot size (100000 for forex)
        """
        self.account_balance = account_balance
        self.risk_level = risk_level
        self.base_risk_per_trade = base_risk_per_trade
        self.use_kelly = use_kelly
        self.use_volatility_adjustment = use_volatility_adjustment
        self.use_correlation_adjustment = use_correlation_adjustment
        self.use_drawdown_adjustment = use_drawdown_adjustment
        self.min_position_size = min_position_size
        self.max_position_size = max_position_size
        self.lot_size = lot_size
        
        # Get risk parameters for level
        self.risk_params = self.RISK_PARAMS[risk_level]
        
        # Portfolio tracking
        self.open_positions: List[Dict[str, Any]] = []
        self.peak_balance: float = account_balance
        self.current_drawdown: float = 0.0
    
    def calculate_position_size(
        self,
        entry_price: float,
        stop_loss: float,
        take_profit: float,
        win_rate: float = 0.5,
        signal_confidence: float = 0.5,
        current_atr: float = 0.0,
        average_atr: float = 0.0,
        existing_correlation: float = 0.0,
        regime_multiplier: float = 1.0
    ) -> PositionSizeResult:
        """
        Calculate optimal position size
        
        Args:
            entry_price: Entry price
            stop_loss: Stop loss price
            take_profit: Take profit price
            win_rate: Historical win rate (0-1)
            signal_confidence: Confidence in current signal (0-1)
            current_atr: Current ATR
            average_atr: Average ATR for volatility comparison
            existing_correlation: Correlation with existing positions
            regime_multiplier: Multiplier from regime analysis
            
        Returns:
            PositionSizeResult with complete sizing analysis
        """
        warnings = []
        
        # Calculate risk per unit
        risk_per_unit = abs(entry_price - stop_loss)
        reward_per_unit = abs(take_profit - entry_price)
        
        if risk_per_unit == 0:
            warnings.append("Invalid stop loss - same as entry")
            risk_per_unit = entry_price * 0.01  # Default 1% stop
        
        # Calculate risk/reward ratio
        risk_reward_ratio = reward_per_unit / risk_per_unit if risk_per_unit > 0 else 0
        
        # Calculate Kelly Criterion
        kelly_fraction, half_kelly, quarter_kelly = self._calculate_kelly(
            win_rate, risk_reward_ratio
        )
        
        # Determine recommended Kelly based on confidence
        if signal_confidence >= 0.8:
            recommended_kelly = half_kelly
        elif signal_confidence >= 0.6:
            recommended_kelly = quarter_kelly
        else:
            recommended_kelly = quarter_kelly * 0.5
        
        # Calculate base risk amount
        max_risk = self.risk_params["max_risk_per_trade"]
        base_risk_amount = self.account_balance * min(self.base_risk_per_trade, max_risk)
        
        # Apply Kelly if enabled
        if self.use_kelly:
            kelly_risk = self.account_balance * recommended_kelly
            base_risk_amount = min(base_risk_amount, kelly_risk)
        
        # Calculate adjustments
        volatility_adjustment = self._calculate_volatility_adjustment(
            current_atr, average_atr
        ) if self.use_volatility_adjustment else 1.0
        
        correlation_adjustment = self._calculate_correlation_adjustment(
            existing_correlation
        ) if self.use_correlation_adjustment else 1.0
        
        drawdown_adjustment = self._calculate_drawdown_adjustment(
        ) if self.use_drawdown_adjustment else 1.0
        
        confidence_adjustment = self._calculate_confidence_adjustment(signal_confidence)
        
        # Total adjustment
        total_adjustment = (
            volatility_adjustment *
            correlation_adjustment *
            drawdown_adjustment *
            regime_multiplier *
            confidence_adjustment
        )
        
        # Apply adjustments to risk amount
        adjusted_risk_amount = base_risk_amount * total_adjustment
        
        # Calculate position size
        position_size_units = adjusted_risk_amount / risk_per_unit
        position_size_lots = position_size_units / self.lot_size
        
        # Apply position limits
        position_size_lots = max(self.min_position_size, 
                                 min(self.max_position_size, position_size_lots))
        
        # Recalculate actual values
        actual_position_units = position_size_lots * self.lot_size
        actual_risk_amount = actual_position_units * risk_per_unit
        actual_risk_percent = actual_risk_amount / self.account_balance
        
        # Check if within limits
        is_within_limits = (
            position_size_lots >= self.min_position_size and
            position_size_lots <= self.max_position_size and
            actual_risk_percent <= max_risk
        )
        
        if not is_within_limits:
            warnings.append(f"Position size adjusted to fit limits")
        
        # Calculate expected profit
        expected_profit = (
            win_rate * reward_per_unit * actual_position_units -
            (1 - win_rate) * risk_per_unit * actual_position_units
        )
        
        # Calculate max loss
        max_loss = actual_risk_amount
        
        # Position value
        position_value = actual_position_units * entry_price
        
        return PositionSizeResult(
            position_size=position_size_lots,
            position_value=position_value,
            risk_amount=actual_risk_amount,
            risk_percent=actual_risk_percent,
            kelly_fraction=kelly_fraction,
            half_kelly=half_kelly,
            quarter_kelly=quarter_kelly,
            recommended_kelly=recommended_kelly,
            volatility_adjustment=volatility_adjustment,
            correlation_adjustment=correlation_adjustment,
            drawdown_adjustment=drawdown_adjustment,
            regime_adjustment=regime_multiplier,
            confidence_adjustment=confidence_adjustment,
            total_adjustment=total_adjustment,
            max_loss=max_loss,
            expected_profit=expected_profit,
            risk_reward_ratio=risk_reward_ratio,
            max_position_size=self.max_position_size,
            min_position_size=self.min_position_size,
            is_within_limits=is_within_limits,
            warnings=warnings
        )
    
    def _calculate_kelly(
        self,
        win_rate: float,
        risk_reward_ratio: float
    ) -> Tuple[float, float, float]:
        """
        Calculate Kelly Criterion
        
        Kelly = W - (1-W)/R
        Where:
            W = Win rate
            R = Risk/Reward ratio
        """
        if risk_reward_ratio <= 0:
            return 0.0, 0.0, 0.0
        
        # Kelly formula
        kelly = win_rate - ((1 - win_rate) / risk_reward_ratio)
        
        # Clamp to reasonable range
        kelly = max(0.0, min(0.25, kelly))  # Cap at 25%
        
        half_kelly = kelly * 0.5
        quarter_kelly = kelly * 0.25
        
        return kelly, half_kelly, quarter_kelly
    
    def _calculate_volatility_adjustment(
        self,
        current_atr: float,
        average_atr: float
    ) -> float:
        """
        Calculate volatility adjustment
        
        Higher volatility = smaller position
        Lower volatility = larger position (up to a limit)
        """
        if average_atr <= 0 or current_atr <= 0:
            return 1.0
        
        volatility_ratio = current_atr / average_atr
        
        # Inverse relationship with limits
        if volatility_ratio > 1.5:
            # High volatility - reduce size
            adjustment = 1.0 / volatility_ratio
        elif volatility_ratio < 0.7:
            # Low volatility - increase size (limited)
            adjustment = min(1.3, 1.0 / volatility_ratio)
        else:
            adjustment = 1.0
        
        return max(0.3, min(1.5, adjustment))
    
    def _calculate_correlation_adjustment(
        self,
        existing_correlation: float
    ) -> float:
        """
        Calculate correlation adjustment
        
        Higher correlation with existing positions = smaller position
        """
        max_correlation = self.risk_params["max_correlation"]
        
        if existing_correlation >= max_correlation:
            # Too correlated - significantly reduce
            return 0.3
        elif existing_correlation > 0.5:
            # Moderately correlated - reduce
            return 1.0 - (existing_correlation - 0.5)
        else:
            # Low correlation - no reduction
            return 1.0
    
    def _calculate_drawdown_adjustment(self) -> float:
        """
        Calculate drawdown adjustment
        
        Larger drawdown = smaller position
        """
        drawdown_state = self._get_drawdown_state()
        return self.DRAWDOWN_SCALING[drawdown_state]
    
    def _calculate_confidence_adjustment(self, confidence: float) -> float:
        """
        Calculate confidence adjustment
        
        Higher confidence = larger position
        Lower confidence = smaller position
        """
        # Scale from 0.5 to 1.5 based on confidence
        return 0.5 + confidence
    
    def _get_drawdown_state(self) -> DrawdownState:
        """Get current drawdown state"""
        if self.current_drawdown <= 0.02:
            return DrawdownState.NONE
        elif self.current_drawdown <= 0.05:
            return DrawdownState.MINOR
        elif self.current_drawdown <= 0.10:
            return DrawdownState.MODERATE
        elif self.current_drawdown <= 0.20:
            return DrawdownState.SEVERE
        else:
            return DrawdownState.CRITICAL
    
    def update_account(
        self,
        new_balance: float,
        positions: Optional[List[Dict[str, Any]]] = None
    ):
        """
        Update account balance and positions
        
        Args:
            new_balance: New account balance
            positions: List of open positions
        """
        self.account_balance = new_balance
        
        # Update peak and drawdown
        if new_balance > self.peak_balance:
            self.peak_balance = new_balance
            self.current_drawdown = 0.0
        else:
            self.current_drawdown = (self.peak_balance - new_balance) / self.peak_balance
        
        if positions is not None:
            self.open_positions = positions
    
    def calculate_portfolio_risk(self) -> PortfolioRisk:
        """Calculate portfolio-level risk metrics"""
        if not self.open_positions:
            return PortfolioRisk(
                total_exposure=0.0,
                total_risk=0.0,
                total_risk_percent=0.0,
                average_correlation=0.0,
                diversification_ratio=1.0,
                num_positions=0,
                largest_position_percent=0.0,
                concentration_risk=0.0,
                max_total_risk=self.account_balance * self.risk_params["max_total_risk"],
                remaining_risk_budget=self.account_balance * self.risk_params["max_total_risk"],
                can_add_position=True
            )
        
        # Calculate totals
        total_exposure = sum(p.get("value", 0) for p in self.open_positions)
        total_risk = sum(p.get("risk", 0) for p in self.open_positions)
        total_risk_percent = total_risk / self.account_balance if self.account_balance > 0 else 0
        
        # Calculate concentration
        position_weights = [p.get("value", 0) / total_exposure for p in self.open_positions] if total_exposure > 0 else []
        largest_position_percent = max(position_weights) if position_weights else 0
        concentration_risk = sum(w ** 2 for w in position_weights)  # Herfindahl index
        
        # Placeholder for correlation (would need actual correlation matrix)
        average_correlation = 0.3  # Assume moderate correlation
        diversification_ratio = 1.0 - average_correlation
        
        # Risk budget
        max_total_risk = self.account_balance * self.risk_params["max_total_risk"]
        remaining_risk_budget = max_total_risk - total_risk
        
        # Can add position?
        can_add_position = (
            len(self.open_positions) < self.risk_params["max_positions"] and
            remaining_risk_budget > self.account_balance * 0.005  # At least 0.5% risk budget
        )
        
        return PortfolioRisk(
            total_exposure=total_exposure,
            total_risk=total_risk,
            total_risk_percent=total_risk_percent,
            average_correlation=average_correlation,
            diversification_ratio=diversification_ratio,
            num_positions=len(self.open_positions),
            largest_position_percent=largest_position_percent,
            concentration_risk=concentration_risk,
            max_total_risk=max_total_risk,
            remaining_risk_budget=remaining_risk_budget,
            can_add_position=can_add_position
        )
    
    def calculate_risk_parity_sizes(
        self,
        instruments: List[Dict[str, Any]]
    ) -> Dict[str, float]:
        """
        Calculate risk parity position sizes
        
        Each position contributes equal risk to the portfolio
        
        Args:
            instruments: List of instruments with volatility info
            
        Returns:
            Dictionary mapping instrument to position size
        """
        if not instruments:
            return {}
        
        # Calculate total risk budget
        total_risk_budget = self.account_balance * self.risk_params["max_total_risk"]
        risk_per_position = total_risk_budget / len(instruments)
        
        sizes = {}
        for inst in instruments:
            symbol = inst.get("symbol", "UNKNOWN")
            atr = inst.get("atr", 0)
            price = inst.get("price", 0)
            
            if atr <= 0 or price <= 0:
                sizes[symbol] = self.min_position_size
                continue
            
            # Risk per unit = ATR (approximate stop loss distance)
            risk_per_unit = atr
            
            # Position size to achieve target risk
            position_units = risk_per_position / risk_per_unit
            position_lots = position_units / self.lot_size
            
            # Apply limits
            position_lots = max(self.min_position_size, 
                               min(self.max_position_size, position_lots))
            
            sizes[symbol] = position_lots
        
        return sizes
    
    def get_max_position_for_risk(
        self,
        entry_price: float,
        stop_loss: float,
        max_risk_percent: Optional[float] = None
    ) -> float:
        """
        Calculate maximum position size for a given risk percentage
        
        Args:
            entry_price: Entry price
            stop_loss: Stop loss price
            max_risk_percent: Maximum risk as decimal (default: use risk level setting)
            
        Returns:
            Maximum position size in lots
        """
        if max_risk_percent is None:
            max_risk_percent = self.risk_params["max_risk_per_trade"]
        
        risk_per_unit = abs(entry_price - stop_loss)
        if risk_per_unit == 0:
            return self.min_position_size
        
        max_risk_amount = self.account_balance * max_risk_percent
        max_position_units = max_risk_amount / risk_per_unit
        max_position_lots = max_position_units / self.lot_size
        
        return min(self.max_position_size, max_position_lots)


def test_position_sizing():
    """Test Position Sizing Intelligence"""
    
    # Create position sizer
    sizer = PositionSizingIntelligence(
        account_balance=10000,
        risk_level=RiskLevel.MODERATE,
        base_risk_per_trade=0.02
    )
    
    # Test position sizing
    result = sizer.calculate_position_size(
        entry_price=1.1000,
        stop_loss=1.0950,
        take_profit=1.1100,
        win_rate=0.55,
        signal_confidence=0.7,
        current_atr=0.0050,
        average_atr=0.0045,
        existing_correlation=0.2,
        regime_multiplier=1.0
    )
    
    print("=" * 60)
    print("POSITION SIZING INTELLIGENCE TEST")
    print("=" * 60)
    print(result.get_summary())
    
    # Test portfolio risk
    sizer.open_positions = [
        {"symbol": "EURUSD", "value": 5000, "risk": 100},
        {"symbol": "GBPUSD", "value": 3000, "risk": 60}
    ]
    
    portfolio_risk = sizer.calculate_portfolio_risk()
    print(portfolio_risk.get_summary())
    
    # Test risk parity
    instruments = [
        {"symbol": "EURUSD", "atr": 0.0050, "price": 1.1000},
        {"symbol": "GBPUSD", "atr": 0.0060, "price": 1.2700},
        {"symbol": "USDJPY", "atr": 0.50, "price": 150.00}
    ]
    
    parity_sizes = sizer.calculate_risk_parity_sizes(instruments)
    print("\nRisk Parity Sizes:")
    for symbol, size in parity_sizes.items():
        print(f"  {symbol}: {size:.4f} lots")
    
    return result, portfolio_risk


if __name__ == "__main__":
    test_position_sizing()
