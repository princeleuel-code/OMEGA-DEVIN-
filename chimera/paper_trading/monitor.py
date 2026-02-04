"""
Trading Monitor & Dashboard
============================

This module provides monitoring and visualization for paper trading:

1. TradingMonitor - Real-time monitoring of trading activity
2. PerformanceTracker - Track and analyze performance metrics
3. Dashboard generation for visual reporting
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
import json
import os
import math


@dataclass
class DailyStats:
    """Daily trading statistics."""
    date: str
    trades: int
    wins: int
    losses: int
    pnl: float
    pnl_pct: float
    win_rate: float
    max_drawdown: float
    starting_capital: float
    ending_capital: float


@dataclass
class SymbolStats:
    """Per-symbol trading statistics."""
    symbol: str
    trades: int
    wins: int
    losses: int
    pnl: float
    pnl_pct: float
    win_rate: float
    avg_duration_hours: float
    best_trade: float
    worst_trade: float


class PerformanceTracker:
    """
    Tracks and analyzes trading performance over time.
    """
    
    def __init__(self, initial_capital: float = 10000.0):
        self.initial_capital = initial_capital
        self.trades: List[dict] = []
        self.equity_curve: List[Tuple[datetime, float]] = []
        self.daily_stats: Dict[str, DailyStats] = {}
        self.symbol_stats: Dict[str, SymbolStats] = {}
    
    def add_trade(self, trade: dict):
        """Add a completed trade."""
        self.trades.append(trade)
        self._update_daily_stats(trade)
        self._update_symbol_stats(trade)
    
    def update_equity(self, timestamp: datetime, equity: float):
        """Update equity curve."""
        self.equity_curve.append((timestamp, equity))
    
    def _update_daily_stats(self, trade: dict):
        """Update daily statistics."""
        date_str = trade.get('exit_time', datetime.now()).strftime('%Y-%m-%d') if isinstance(trade.get('exit_time'), datetime) else str(trade.get('exit_time', ''))[:10]
        
        if date_str not in self.daily_stats:
            self.daily_stats[date_str] = DailyStats(
                date=date_str,
                trades=0,
                wins=0,
                losses=0,
                pnl=0.0,
                pnl_pct=0.0,
                win_rate=0.0,
                max_drawdown=0.0,
                starting_capital=self.initial_capital,
                ending_capital=self.initial_capital
            )
        
        stats = self.daily_stats[date_str]
        stats.trades += 1
        
        pnl = trade.get('pnl', 0)
        if pnl > 0:
            stats.wins += 1
        else:
            stats.losses += 1
        
        stats.pnl += pnl
        stats.pnl_pct = (stats.pnl / self.initial_capital) * 100
        stats.win_rate = stats.wins / stats.trades if stats.trades > 0 else 0
        stats.ending_capital = stats.starting_capital + stats.pnl
    
    def _update_symbol_stats(self, trade: dict):
        """Update per-symbol statistics."""
        symbol = trade.get('symbol', 'UNKNOWN')
        
        if symbol not in self.symbol_stats:
            self.symbol_stats[symbol] = SymbolStats(
                symbol=symbol,
                trades=0,
                wins=0,
                losses=0,
                pnl=0.0,
                pnl_pct=0.0,
                win_rate=0.0,
                avg_duration_hours=0.0,
                best_trade=0.0,
                worst_trade=0.0
            )
        
        stats = self.symbol_stats[symbol]
        stats.trades += 1
        
        pnl = trade.get('pnl', 0)
        if pnl > 0:
            stats.wins += 1
        else:
            stats.losses += 1
        
        stats.pnl += pnl
        stats.pnl_pct = (stats.pnl / self.initial_capital) * 100
        stats.win_rate = stats.wins / stats.trades if stats.trades > 0 else 0
        
        # Track best/worst
        if pnl > stats.best_trade:
            stats.best_trade = pnl
        if pnl < stats.worst_trade:
            stats.worst_trade = pnl
        
        # Update average duration
        duration = trade.get('duration_hours', 0)
        stats.avg_duration_hours = (
            (stats.avg_duration_hours * (stats.trades - 1) + duration) / stats.trades
        )
    
    def get_summary(self) -> dict:
        """Get overall performance summary."""
        if not self.trades:
            return {
                "total_trades": 0,
                "total_pnl": 0.0,
                "total_pnl_pct": 0.0,
                "win_rate": 0.0,
                "profit_factor": 0.0,
                "sharpe_ratio": 0.0,
                "max_drawdown": 0.0,
                "avg_trade_duration": 0.0,
                "best_day": None,
                "worst_day": None,
                "best_symbol": None,
                "worst_symbol": None
            }
        
        wins = [t for t in self.trades if t.get('pnl', 0) > 0]
        losses = [t for t in self.trades if t.get('pnl', 0) <= 0]
        
        gross_profit = sum(t.get('pnl', 0) for t in wins)
        gross_loss = abs(sum(t.get('pnl', 0) for t in losses))
        
        total_pnl = sum(t.get('pnl', 0) for t in self.trades)
        
        # Calculate Sharpe
        returns = [t.get('pnl_pct', 0) for t in self.trades]
        avg_return = sum(returns) / len(returns) if returns else 0
        std_return = math.sqrt(sum((r - avg_return) ** 2 for r in returns) / len(returns)) if len(returns) > 1 else 0
        sharpe = (avg_return / std_return) * math.sqrt(252) if std_return > 0 else 0
        
        # Calculate max drawdown from equity curve
        max_dd = 0.0
        if self.equity_curve:
            peak = self.equity_curve[0][1]
            for _, equity in self.equity_curve:
                if equity > peak:
                    peak = equity
                dd = (peak - equity) / peak
                if dd > max_dd:
                    max_dd = dd
        
        # Best/worst day
        best_day = max(self.daily_stats.values(), key=lambda x: x.pnl) if self.daily_stats else None
        worst_day = min(self.daily_stats.values(), key=lambda x: x.pnl) if self.daily_stats else None
        
        # Best/worst symbol
        best_symbol = max(self.symbol_stats.values(), key=lambda x: x.pnl) if self.symbol_stats else None
        worst_symbol = min(self.symbol_stats.values(), key=lambda x: x.pnl) if self.symbol_stats else None
        
        return {
            "total_trades": len(self.trades),
            "winning_trades": len(wins),
            "losing_trades": len(losses),
            "total_pnl": total_pnl,
            "total_pnl_pct": (total_pnl / self.initial_capital) * 100,
            "win_rate": len(wins) / len(self.trades),
            "profit_factor": gross_profit / gross_loss if gross_loss > 0 else 0,
            "sharpe_ratio": sharpe,
            "max_drawdown": max_dd * 100,
            "avg_trade_duration": sum(t.get('duration_hours', 0) for t in self.trades) / len(self.trades),
            "best_day": best_day.date if best_day else None,
            "best_day_pnl": best_day.pnl if best_day else 0,
            "worst_day": worst_day.date if worst_day else None,
            "worst_day_pnl": worst_day.pnl if worst_day else 0,
            "best_symbol": best_symbol.symbol if best_symbol else None,
            "best_symbol_pnl": best_symbol.pnl if best_symbol else 0,
            "worst_symbol": worst_symbol.symbol if worst_symbol else None,
            "worst_symbol_pnl": worst_symbol.pnl if worst_symbol else 0
        }
    
    def export_to_json(self, filepath: str):
        """Export all data to JSON."""
        data = {
            "summary": self.get_summary(),
            "trades": self.trades,
            "daily_stats": {k: vars(v) for k, v in self.daily_stats.items()},
            "symbol_stats": {k: vars(v) for k, v in self.symbol_stats.items()},
            "equity_curve": [(ts.isoformat() if isinstance(ts, datetime) else str(ts), eq) for ts, eq in self.equity_curve]
        }
        
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2, default=str)


class TradingMonitor:
    """
    Real-time monitoring of paper trading activity.
    
    Provides:
    - Live status updates
    - Alert generation
    - Performance tracking
    - Dashboard generation
    """
    
    def __init__(
        self,
        log_dir: str = "/home/ubuntu/omega_devin/paper_trading_logs",
        alert_callback: callable = None
    ):
        self.log_dir = log_dir
        self.alert_callback = alert_callback
        
        self.tracker = PerformanceTracker()
        self._alerts: List[dict] = []
        
        os.makedirs(log_dir, exist_ok=True)
    
    def on_trade_closed(self, trade: dict):
        """Handle trade closed event."""
        self.tracker.add_trade(trade)
        
        # Check for alerts
        pnl = trade.get('pnl', 0)
        if pnl < -100:  # Large loss alert
            self._add_alert("LARGE_LOSS", f"Large loss: ${pnl:.2f} on {trade.get('symbol')}")
        
        # Log trade
        self._log_event("TRADE_CLOSED", trade)
    
    def on_equity_update(self, timestamp: datetime, equity: float):
        """Handle equity update."""
        self.tracker.update_equity(timestamp, equity)
    
    def on_kill_switch(self, reason: str):
        """Handle kill switch activation."""
        self._add_alert("KILL_SWITCH", f"Kill switch activated: {reason}")
        self._log_event("KILL_SWITCH", {"reason": reason})
    
    def _add_alert(self, alert_type: str, message: str):
        """Add an alert."""
        alert = {
            "timestamp": datetime.now().isoformat(),
            "type": alert_type,
            "message": message
        }
        self._alerts.append(alert)
        
        if self.alert_callback:
            self.alert_callback(alert)
        
        # Log alert
        self._log_event("ALERT", alert)
    
    def _log_event(self, event_type: str, data: dict):
        """Log an event."""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "event": event_type,
            "data": data
        }
        
        log_file = os.path.join(self.log_dir, f"monitor_{datetime.now().strftime('%Y%m%d')}.jsonl")
        with open(log_file, 'a') as f:
            f.write(json.dumps(log_entry, default=str) + '\n')
    
    def get_status(self) -> dict:
        """Get current monitoring status."""
        summary = self.tracker.get_summary()
        
        return {
            "timestamp": datetime.now().isoformat(),
            "performance": summary,
            "recent_alerts": self._alerts[-10:],
            "daily_stats": list(self.tracker.daily_stats.values())[-7:],  # Last 7 days
            "symbol_stats": list(self.tracker.symbol_stats.values())
        }
    
    def generate_report(self) -> str:
        """Generate a text report."""
        summary = self.tracker.get_summary()
        
        report = []
        report.append("=" * 60)
        report.append("PAPER TRADING PERFORMANCE REPORT")
        report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("=" * 60)
        report.append("")
        
        report.append("OVERALL PERFORMANCE")
        report.append("-" * 40)
        report.append(f"Total Trades: {summary['total_trades']}")
        report.append(f"Win Rate: {summary['win_rate']:.1%}")
        report.append(f"Total P&L: ${summary['total_pnl']:.2f} ({summary['total_pnl_pct']:+.2f}%)")
        report.append(f"Profit Factor: {summary['profit_factor']:.2f}")
        report.append(f"Sharpe Ratio: {summary['sharpe_ratio']:.2f}")
        report.append(f"Max Drawdown: {summary['max_drawdown']:.2f}%")
        report.append("")
        
        report.append("BY SYMBOL")
        report.append("-" * 40)
        for symbol, stats in self.tracker.symbol_stats.items():
            report.append(f"{symbol}: {stats.trades} trades, {stats.win_rate:.1%} win rate, ${stats.pnl:+.2f}")
        report.append("")
        
        report.append("RECENT ALERTS")
        report.append("-" * 40)
        for alert in self._alerts[-5:]:
            report.append(f"[{alert['type']}] {alert['message']}")
        
        report.append("")
        report.append("=" * 60)
        
        return "\n".join(report)
    
    def save_report(self, filepath: str = None):
        """Save report to file."""
        if filepath is None:
            filepath = os.path.join(self.log_dir, f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt")
        
        report = self.generate_report()
        with open(filepath, 'w') as f:
            f.write(report)
        
        return filepath
    
    def export_data(self, filepath: str = None):
        """Export all tracking data."""
        if filepath is None:
            filepath = os.path.join(self.log_dir, f"data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        
        self.tracker.export_to_json(filepath)
        return filepath


def print_live_status(trader, monitor: TradingMonitor):
    """Print live trading status to console."""
    state = trader.get_state()
    summary = monitor.tracker.get_summary()
    
    print("\033[2J\033[H")  # Clear screen
    print("=" * 60)
    print("OMEGA-DEVIN PAPER TRADING - LIVE STATUS")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    print("")
    
    print(f"Capital: ${state.capital:,.2f}")
    print(f"Equity: ${state.equity:,.2f}")
    print(f"Total P&L: ${state.total_pnl:+,.2f} ({state.total_pnl_pct:+.2f}%)")
    print(f"Daily P&L: ${state.daily_pnl:+,.2f}")
    print("")
    
    print(f"Open Positions: {len(state.open_positions)}")
    for pos in state.open_positions:
        direction = "LONG" if pos.side.value == "buy" else "SHORT"
        print(f"  {pos.symbol} {direction} @ {pos.entry_price:.5f} | P&L: ${pos.unrealized_pnl:+.2f}")
    print("")
    
    print(f"Closed Trades: {summary['total_trades']}")
    print(f"Win Rate: {summary['win_rate']:.1%}")
    print(f"Profit Factor: {summary['profit_factor']:.2f}")
    print("")
    
    if state.kill_switch_active:
        print(f"!!! KILL SWITCH ACTIVE: {state.kill_switch_reason} !!!")
    
    print("=" * 60)
