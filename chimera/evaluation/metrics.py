"""
Metrics - Performance measurement for trading strategies

Provides comprehensive metrics for evaluating strategy performance.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime
import math


# Anti-fraud guardrails for risk-adjusted metrics. Sharpe/Sortino can explode on
# tiny-N (e.g., 1-2 non-zero returns) and should not be treated as signal.
_MIN_NONZERO_RETURNS_FOR_RATIOS = 5
_RATIO_CAP_ABS = 10.0


@dataclass
class Trade:
    """Record of a single trade"""
    entry_time: datetime
    exit_time: datetime
    direction: int  # 1 for long, -1 for short
    entry_price: float
    exit_price: float
    size: float
    pnl: float
    pnl_pct: float
    bars_held: int
    exit_reason: str
    
    @property
    def is_winner(self) -> bool:
        return self.pnl > 0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "entry_time": self.entry_time.isoformat(),
            "exit_time": self.exit_time.isoformat(),
            "direction": "LONG" if self.direction == 1 else "SHORT",
            "entry_price": self.entry_price,
            "exit_price": self.exit_price,
            "size": self.size,
            "pnl": self.pnl,
            "pnl_pct": self.pnl_pct,
            "bars_held": self.bars_held,
            "exit_reason": self.exit_reason,
            "is_winner": self.is_winner
        }


@dataclass
class TradeMetrics:
    """Metrics computed from a list of trades"""
    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    
    win_rate: float = 0.0
    
    total_pnl: float = 0.0
    avg_pnl: float = 0.0
    avg_winner: float = 0.0
    avg_loser: float = 0.0
    
    largest_winner: float = 0.0
    largest_loser: float = 0.0
    
    profit_factor: float = 0.0
    expectancy: float = 0.0
    
    avg_bars_held: float = 0.0
    avg_bars_winner: float = 0.0
    avg_bars_loser: float = 0.0
    
    long_trades: int = 0
    short_trades: int = 0
    long_win_rate: float = 0.0
    short_win_rate: float = 0.0
    
    @classmethod
    def from_trades(cls, trades: List[Trade]) -> "TradeMetrics":
        """Compute metrics from a list of trades"""
        if not trades:
            return cls()
        
        metrics = cls()
        metrics.total_trades = len(trades)
        
        winners = [t for t in trades if t.is_winner]
        losers = [t for t in trades if not t.is_winner]
        
        metrics.winning_trades = len(winners)
        metrics.losing_trades = len(losers)
        metrics.win_rate = len(winners) / len(trades) if trades else 0
        
        # P&L metrics
        metrics.total_pnl = sum(t.pnl for t in trades)
        metrics.avg_pnl = metrics.total_pnl / len(trades)
        
        if winners:
            metrics.avg_winner = sum(t.pnl for t in winners) / len(winners)
            metrics.largest_winner = max(t.pnl for t in winners)
        
        if losers:
            metrics.avg_loser = sum(t.pnl for t in losers) / len(losers)
            metrics.largest_loser = min(t.pnl for t in losers)
        
        # Profit factor
        gross_profit = sum(t.pnl for t in winners) if winners else 0
        gross_loss = abs(sum(t.pnl for t in losers)) if losers else 0
        metrics.profit_factor = gross_profit / gross_loss if gross_loss > 0 else float('inf')
        
        # Expectancy
        if metrics.win_rate > 0 and metrics.avg_loser != 0:
            metrics.expectancy = (
                metrics.win_rate * metrics.avg_winner + 
                (1 - metrics.win_rate) * metrics.avg_loser
            )
        
        # Holding time
        metrics.avg_bars_held = sum(t.bars_held for t in trades) / len(trades)
        if winners:
            metrics.avg_bars_winner = sum(t.bars_held for t in winners) / len(winners)
        if losers:
            metrics.avg_bars_loser = sum(t.bars_held for t in losers) / len(losers)
        
        # Direction breakdown
        longs = [t for t in trades if t.direction == 1]
        shorts = [t for t in trades if t.direction == -1]
        
        metrics.long_trades = len(longs)
        metrics.short_trades = len(shorts)
        
        if longs:
            metrics.long_win_rate = len([t for t in longs if t.is_winner]) / len(longs)
        if shorts:
            metrics.short_win_rate = len([t for t in shorts if t.is_winner]) / len(shorts)
        
        return metrics
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_trades": self.total_trades,
            "winning_trades": self.winning_trades,
            "losing_trades": self.losing_trades,
            "win_rate": round(self.win_rate, 4),
            "total_pnl": round(self.total_pnl, 2),
            "avg_pnl": round(self.avg_pnl, 2),
            "avg_winner": round(self.avg_winner, 2),
            "avg_loser": round(self.avg_loser, 2),
            "largest_winner": round(self.largest_winner, 2),
            "largest_loser": round(self.largest_loser, 2),
            "profit_factor": round(self.profit_factor, 2),
            "expectancy": round(self.expectancy, 2),
            "avg_bars_held": round(self.avg_bars_held, 1),
            "long_trades": self.long_trades,
            "short_trades": self.short_trades,
            "long_win_rate": round(self.long_win_rate, 4),
            "short_win_rate": round(self.short_win_rate, 4)
        }


@dataclass
class PerformanceMetrics:
    """Overall performance metrics including equity curve analysis"""
    
    # Returns
    total_return: float = 0.0
    total_return_pct: float = 0.0
    annualized_return: float = 0.0
    
    # Risk metrics
    max_drawdown: float = 0.0
    max_drawdown_pct: float = 0.0
    max_drawdown_duration: int = 0  # bars
    
    # Risk-adjusted returns
    sharpe_ratio: float = 0.0
    sortino_ratio: float = 0.0
    calmar_ratio: float = 0.0
    
    # Volatility
    volatility: float = 0.0
    downside_volatility: float = 0.0
    
    # Activity
    total_bars: int = 0
    bars_in_market: int = 0
    time_in_market_pct: float = 0.0
    trades_per_day: float = 0.0
    
    # No-trade analysis
    no_trade_decisions: int = 0
    no_trade_rate: float = 0.0
    
    @classmethod
    def from_equity_curve(
        cls,
        equity: List[float],
        trades: List[Trade],
        initial_capital: float = 10000.0,
        bars_per_day: float = 24.0,  # For hourly bars
        risk_free_rate: float = 0.02  # Annual
    ) -> "PerformanceMetrics":
        """Compute performance metrics from equity curve"""
        if not equity or len(equity) < 2:
            return cls()
        
        metrics = cls()
        
        # Basic returns
        metrics.total_return = equity[-1] - initial_capital
        metrics.total_return_pct = (equity[-1] / initial_capital - 1) * 100
        
        # Annualized return
        total_bars = len(equity)
        years = total_bars / (bars_per_day * 252)  # Trading days per year
        if years > 0:
            metrics.annualized_return = (
                (equity[-1] / initial_capital) ** (1 / years) - 1
            ) * 100
        
        # Drawdown analysis
        peak = equity[0]
        max_dd = 0
        max_dd_pct = 0
        dd_start = 0
        max_dd_duration = 0
        current_dd_duration = 0
        
        for i, eq in enumerate(equity):
            if eq > peak:
                peak = eq
                current_dd_duration = 0
            else:
                dd = peak - eq
                dd_pct = dd / peak * 100
                current_dd_duration += 1
                
                if dd > max_dd:
                    max_dd = dd
                    max_dd_pct = dd_pct
                
                if current_dd_duration > max_dd_duration:
                    max_dd_duration = current_dd_duration
        
        metrics.max_drawdown = max_dd
        metrics.max_drawdown_pct = max_dd_pct
        metrics.max_drawdown_duration = max_dd_duration
        
        # Returns series for volatility calculation
        returns = []
        for i in range(1, len(equity)):
            ret = (equity[i] - equity[i-1]) / equity[i-1]
            returns.append(ret)
        
        if returns:
            # Volatility (annualized)
            mean_ret = sum(returns) / len(returns)
            variance = sum((r - mean_ret) ** 2 for r in returns) / len(returns)
            metrics.volatility = math.sqrt(variance) * math.sqrt(bars_per_day * 252) * 100
            
            # Downside volatility
            negative_returns = [r for r in returns if r < 0]
            if negative_returns:
                down_var = sum(r ** 2 for r in negative_returns) / len(negative_returns)
                metrics.downside_volatility = math.sqrt(down_var) * math.sqrt(bars_per_day * 252) * 100
            
            # Sharpe ratio
            excess_return = metrics.annualized_return - risk_free_rate * 100
            nonzero_returns = [r for r in returns if abs(r) > 1e-12]
            if len(nonzero_returns) >= _MIN_NONZERO_RETURNS_FOR_RATIOS and metrics.volatility > 0:
                metrics.sharpe_ratio = excess_return / metrics.volatility
                metrics.sharpe_ratio = max(-_RATIO_CAP_ABS, min(_RATIO_CAP_ABS, metrics.sharpe_ratio))
            
            # Sortino ratio
            if len(nonzero_returns) >= _MIN_NONZERO_RETURNS_FOR_RATIOS and metrics.downside_volatility > 0:
                metrics.sortino_ratio = excess_return / metrics.downside_volatility
                metrics.sortino_ratio = max(-_RATIO_CAP_ABS, min(_RATIO_CAP_ABS, metrics.sortino_ratio))
            
            # Calmar ratio
            if metrics.max_drawdown_pct > 0:
                metrics.calmar_ratio = metrics.annualized_return / metrics.max_drawdown_pct
        
        # Activity metrics
        metrics.total_bars = total_bars
        if trades:
            metrics.bars_in_market = sum(t.bars_held for t in trades)
            metrics.time_in_market_pct = metrics.bars_in_market / total_bars * 100
            
            days = total_bars / bars_per_day
            metrics.trades_per_day = len(trades) / days if days > 0 else 0
        
        return metrics
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_return": round(self.total_return, 2),
            "total_return_pct": round(self.total_return_pct, 2),
            "annualized_return": round(self.annualized_return, 2),
            "max_drawdown": round(self.max_drawdown, 2),
            "max_drawdown_pct": round(self.max_drawdown_pct, 2),
            "max_drawdown_duration": self.max_drawdown_duration,
            "sharpe_ratio": round(self.sharpe_ratio, 3),
            "sortino_ratio": round(self.sortino_ratio, 3),
            "calmar_ratio": round(self.calmar_ratio, 3),
            "volatility": round(self.volatility, 2),
            "downside_volatility": round(self.downside_volatility, 2),
            "total_bars": self.total_bars,
            "bars_in_market": self.bars_in_market,
            "time_in_market_pct": round(self.time_in_market_pct, 2),
            "trades_per_day": round(self.trades_per_day, 2),
            "no_trade_decisions": self.no_trade_decisions,
            "no_trade_rate": round(self.no_trade_rate, 4)
        }
