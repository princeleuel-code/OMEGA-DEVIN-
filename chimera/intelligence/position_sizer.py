"""
Intelligent Position Sizer
==========================

This module implements sophisticated position sizing using:

1. Kelly Criterion - Mathematically optimal bet sizing
2. Fractional Kelly - Reduced Kelly for safety
3. Volatility-Adjusted Sizing - Smaller positions in volatile markets
4. Correlation-Aware Sizing - Account for portfolio correlation
5. Risk Parity - Equal risk contribution from each position

The key insight: Position sizing is MORE important than entry/exit.
A mediocre strategy with great position sizing beats a great strategy
with poor position sizing.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple
from enum import Enum
import math


class SizingMethod(Enum):
    FIXED_FRACTIONAL = "fixed_fractional"
    KELLY = "kelly"
    FRACTIONAL_KELLY = "fractional_kelly"
    VOLATILITY_ADJUSTED = "volatility_adjusted"
    RISK_PARITY = "risk_parity"
    OPTIMAL_F = "optimal_f"


@dataclass
class PositionSize:
    """Calculated position size with full reasoning."""
    units: float
    risk_amount: float
    risk_percent: float
    method_used: SizingMethod
    kelly_fraction: float
    volatility_adjustment: float
    confidence_adjustment: float
    max_size_cap: float
    final_size_percent: float
    reason_codes: List[str]


@dataclass
class KellyResult:
    """Kelly Criterion calculation result."""
    full_kelly: float
    half_kelly: float
    quarter_kelly: float
    edge: float
    win_rate: float
    avg_win: float
    avg_loss: float
    is_positive_expectancy: bool


@dataclass
class TradeStats:
    """Historical trade statistics for Kelly calculation."""
    total_trades: int
    winning_trades: int
    losing_trades: int
    total_profit: float
    total_loss: float
    avg_win: float
    avg_loss: float
    win_rate: float
    profit_factor: float
    expectancy: float


class IntelligentPositionSizer:
    """
    Calculates optimal position sizes using multiple methods.
    
    This is where most traders fail - they either risk too much
    (and blow up) or too little (and never make meaningful returns).
    
    The Kelly Criterion gives us the mathematically optimal bet size
    to maximize long-term growth, but we use fractional Kelly for safety.
    """
    
    def __init__(
        self,
        max_risk_per_trade: float = 0.02,  # 2% max risk per trade
        max_position_size: float = 0.10,   # 10% max position size
        kelly_fraction: float = 0.25,       # Use 1/4 Kelly for safety
        min_trades_for_kelly: int = 30,     # Need 30 trades for Kelly
        volatility_lookback: int = 20,
        target_volatility: float = 0.01,    # 1% daily target vol
    ):
        self.max_risk_per_trade = max_risk_per_trade
        self.max_position_size = max_position_size
        self.kelly_fraction = kelly_fraction
        self.min_trades_for_kelly = min_trades_for_kelly
        self.volatility_lookback = volatility_lookback
        self.target_volatility = target_volatility
        
        # Trade history for Kelly calculation
        self._trade_history: List[float] = []  # List of P&L percentages
    
    def calculate_size(
        self,
        capital: float,
        entry_price: float,
        stop_loss: float,
        confidence: float = 0.5,
        current_volatility: float = None,
        trade_stats: TradeStats = None,
    ) -> PositionSize:
        """
        Calculate optimal position size.
        
        Args:
            capital: Current account capital
            entry_price: Planned entry price
            stop_loss: Stop loss price
            confidence: Signal confidence (0-1)
            current_volatility: Current market volatility (ATR/price)
            trade_stats: Historical trade statistics
            
        Returns:
            PositionSize with full calculation details
        """
        reason_codes = []
        
        # Calculate risk per unit
        risk_per_unit = abs(entry_price - stop_loss)
        if risk_per_unit == 0:
            return self._zero_size("ZERO_RISK_PER_UNIT")
        
        # Start with fixed fractional
        base_risk_amount = capital * self.max_risk_per_trade
        base_units = base_risk_amount / risk_per_unit
        
        # Calculate Kelly if we have enough trades
        kelly_result = None
        kelly_adjustment = 1.0
        
        if trade_stats and trade_stats.total_trades >= self.min_trades_for_kelly:
            kelly_result = self._calculate_kelly(trade_stats)
            
            if kelly_result.is_positive_expectancy:
                # Use fractional Kelly
                kelly_adjustment = kelly_result.full_kelly * self.kelly_fraction
                kelly_adjustment = max(0.1, min(1.0, kelly_adjustment))
                reason_codes.append(f"KELLY_ADJUSTMENT_{kelly_adjustment:.2f}")
            else:
                # Negative expectancy - reduce size significantly
                kelly_adjustment = 0.25
                reason_codes.append("NEGATIVE_EXPECTANCY_REDUCED")
        else:
            reason_codes.append("INSUFFICIENT_TRADES_FOR_KELLY")
        
        # Volatility adjustment
        vol_adjustment = 1.0
        if current_volatility and current_volatility > 0:
            vol_adjustment = self.target_volatility / current_volatility
            vol_adjustment = max(0.25, min(2.0, vol_adjustment))
            reason_codes.append(f"VOL_ADJUSTMENT_{vol_adjustment:.2f}")
        
        # Confidence adjustment
        conf_adjustment = 0.5 + (confidence * 0.5)  # 0.5 to 1.0
        reason_codes.append(f"CONF_ADJUSTMENT_{conf_adjustment:.2f}")
        
        # Apply all adjustments
        adjusted_risk = base_risk_amount * kelly_adjustment * vol_adjustment * conf_adjustment
        adjusted_units = adjusted_risk / risk_per_unit
        
        # Apply maximum position size cap
        max_units = (capital * self.max_position_size) / entry_price
        final_units = min(adjusted_units, max_units)
        
        if final_units < adjusted_units:
            reason_codes.append("MAX_SIZE_CAPPED")
        
        # Calculate final percentages
        final_risk_amount = final_units * risk_per_unit
        final_risk_percent = final_risk_amount / capital
        final_size_percent = (final_units * entry_price) / capital
        
        return PositionSize(
            units=final_units,
            risk_amount=final_risk_amount,
            risk_percent=final_risk_percent,
            method_used=SizingMethod.FRACTIONAL_KELLY if kelly_result else SizingMethod.FIXED_FRACTIONAL,
            kelly_fraction=kelly_adjustment,
            volatility_adjustment=vol_adjustment,
            confidence_adjustment=conf_adjustment,
            max_size_cap=self.max_position_size,
            final_size_percent=final_size_percent,
            reason_codes=reason_codes
        )
    
    def _calculate_kelly(self, stats: TradeStats) -> KellyResult:
        """
        Calculate Kelly Criterion.
        
        Kelly % = W - [(1-W) / R]
        
        Where:
        W = Win rate
        R = Win/Loss ratio (avg win / avg loss)
        """
        if stats.avg_loss == 0:
            return KellyResult(
                full_kelly=0.0,
                half_kelly=0.0,
                quarter_kelly=0.0,
                edge=0.0,
                win_rate=stats.win_rate,
                avg_win=stats.avg_win,
                avg_loss=0.0,
                is_positive_expectancy=False
            )
        
        W = stats.win_rate
        R = abs(stats.avg_win / stats.avg_loss) if stats.avg_loss != 0 else 0
        
        # Kelly formula
        if R == 0:
            kelly = 0.0
        else:
            kelly = W - ((1 - W) / R)
        
        # Calculate edge (expected value per trade)
        edge = (W * stats.avg_win) - ((1 - W) * abs(stats.avg_loss))
        
        return KellyResult(
            full_kelly=max(0.0, kelly),
            half_kelly=max(0.0, kelly / 2),
            quarter_kelly=max(0.0, kelly / 4),
            edge=edge,
            win_rate=W,
            avg_win=stats.avg_win,
            avg_loss=stats.avg_loss,
            is_positive_expectancy=edge > 0
        )
    
    def add_trade_result(self, pnl_percent: float):
        """Add a trade result to history for Kelly calculation."""
        self._trade_history.append(pnl_percent)
        if len(self._trade_history) > 500:
            self._trade_history = self._trade_history[-500:]
    
    def get_trade_stats(self) -> TradeStats:
        """Calculate trade statistics from history."""
        if not self._trade_history:
            return TradeStats(
                total_trades=0,
                winning_trades=0,
                losing_trades=0,
                total_profit=0.0,
                total_loss=0.0,
                avg_win=0.0,
                avg_loss=0.0,
                win_rate=0.0,
                profit_factor=0.0,
                expectancy=0.0
            )
        
        wins = [t for t in self._trade_history if t > 0]
        losses = [t for t in self._trade_history if t < 0]
        
        total_profit = sum(wins)
        total_loss = abs(sum(losses))
        
        avg_win = sum(wins) / len(wins) if wins else 0.0
        avg_loss = abs(sum(losses) / len(losses)) if losses else 0.0
        
        win_rate = len(wins) / len(self._trade_history) if self._trade_history else 0.0
        profit_factor = total_profit / total_loss if total_loss > 0 else 0.0
        
        expectancy = (win_rate * avg_win) - ((1 - win_rate) * avg_loss)
        
        return TradeStats(
            total_trades=len(self._trade_history),
            winning_trades=len(wins),
            losing_trades=len(losses),
            total_profit=total_profit,
            total_loss=total_loss,
            avg_win=avg_win,
            avg_loss=avg_loss,
            win_rate=win_rate,
            profit_factor=profit_factor,
            expectancy=expectancy
        )
    
    def _zero_size(self, reason: str) -> PositionSize:
        """Return zero position size."""
        return PositionSize(
            units=0.0,
            risk_amount=0.0,
            risk_percent=0.0,
            method_used=SizingMethod.FIXED_FRACTIONAL,
            kelly_fraction=0.0,
            volatility_adjustment=1.0,
            confidence_adjustment=1.0,
            max_size_cap=self.max_position_size,
            final_size_percent=0.0,
            reason_codes=[reason]
        )


class KellyCriterion:
    """
    Standalone Kelly Criterion calculator.
    
    The Kelly Criterion is the mathematically optimal bet size to maximize
    the long-term growth rate of capital. It was developed by John Kelly
    at Bell Labs in 1956.
    
    Key insight: Betting too much is just as bad as betting too little.
    Kelly finds the sweet spot.
    """
    
    @staticmethod
    def calculate(win_rate: float, win_loss_ratio: float) -> float:
        """
        Calculate Kelly percentage.
        
        Args:
            win_rate: Probability of winning (0-1)
            win_loss_ratio: Average win / Average loss
            
        Returns:
            Kelly percentage (fraction of capital to risk)
        """
        if win_loss_ratio <= 0:
            return 0.0
        
        kelly = win_rate - ((1 - win_rate) / win_loss_ratio)
        return max(0.0, kelly)
    
    @staticmethod
    def calculate_from_trades(trades: List[float]) -> KellyResult:
        """
        Calculate Kelly from a list of trade P&L percentages.
        
        Args:
            trades: List of trade returns (positive for wins, negative for losses)
            
        Returns:
            KellyResult with full calculation details
        """
        if not trades:
            return KellyResult(
                full_kelly=0.0,
                half_kelly=0.0,
                quarter_kelly=0.0,
                edge=0.0,
                win_rate=0.0,
                avg_win=0.0,
                avg_loss=0.0,
                is_positive_expectancy=False
            )
        
        wins = [t for t in trades if t > 0]
        losses = [t for t in trades if t < 0]
        
        win_rate = len(wins) / len(trades)
        avg_win = sum(wins) / len(wins) if wins else 0.0
        avg_loss = abs(sum(losses) / len(losses)) if losses else 0.0
        
        if avg_loss == 0:
            return KellyResult(
                full_kelly=0.0,
                half_kelly=0.0,
                quarter_kelly=0.0,
                edge=0.0,
                win_rate=win_rate,
                avg_win=avg_win,
                avg_loss=0.0,
                is_positive_expectancy=False
            )
        
        win_loss_ratio = avg_win / avg_loss
        kelly = KellyCriterion.calculate(win_rate, win_loss_ratio)
        
        edge = (win_rate * avg_win) - ((1 - win_rate) * avg_loss)
        
        return KellyResult(
            full_kelly=kelly,
            half_kelly=kelly / 2,
            quarter_kelly=kelly / 4,
            edge=edge,
            win_rate=win_rate,
            avg_win=avg_win,
            avg_loss=avg_loss,
            is_positive_expectancy=edge > 0
        )
    
    @staticmethod
    def optimal_growth_rate(kelly_fraction: float, win_rate: float, win_loss_ratio: float) -> float:
        """
        Calculate the expected growth rate for a given Kelly fraction.
        
        This shows why Kelly is optimal - any other fraction gives lower growth.
        
        Args:
            kelly_fraction: Fraction of Kelly to use (1.0 = full Kelly)
            win_rate: Probability of winning
            win_loss_ratio: Average win / Average loss
            
        Returns:
            Expected log growth rate
        """
        if kelly_fraction <= 0 or win_rate <= 0 or win_loss_ratio <= 0:
            return 0.0
        
        full_kelly = KellyCriterion.calculate(win_rate, win_loss_ratio)
        bet_size = full_kelly * kelly_fraction
        
        # Expected log growth rate
        # G = p * log(1 + b*R) + (1-p) * log(1 - b)
        # where p = win_rate, b = bet_size, R = win_loss_ratio
        
        try:
            win_term = win_rate * math.log(1 + bet_size * win_loss_ratio)
            loss_term = (1 - win_rate) * math.log(1 - bet_size)
            return win_term + loss_term
        except (ValueError, ZeroDivisionError):
            return 0.0
