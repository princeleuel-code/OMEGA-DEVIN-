"""
Paper Trading Engine
====================

This module implements a complete paper trading system for live simulation
without risking real money. It connects to the Breakthrough Intelligence
Module and executes trades in a simulated environment.

Key Features:
1. Real-time signal generation using the Confluence Engine
2. Simulated order execution with realistic slippage
3. Position tracking and P&L calculation
4. Risk management with automatic stop-loss/take-profit
5. Performance logging and reporting
6. Kill-switch for anomaly detection
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple, Callable
from enum import Enum
from datetime import datetime, timedelta
import json
import os
import threading
import time
import math


class OrderType(Enum):
    MARKET = "market"
    LIMIT = "limit"
    STOP = "stop"


class OrderSide(Enum):
    BUY = "buy"
    SELL = "sell"


class PositionStatus(Enum):
    OPEN = "open"
    CLOSED = "closed"
    PARTIAL = "partial"


@dataclass
class PaperTradingConfig:
    """Configuration for paper trading."""
    initial_capital: float = 10000.0
    max_risk_per_trade: float = 0.02  # 2%
    max_daily_loss: float = 0.05  # 5%
    max_drawdown: float = 0.10  # 10%
    max_positions: int = 5
    slippage_pips: float = 0.5
    spread_pips: float = 1.0
    
    # Kill-switch thresholds
    kill_switch_loss_pct: float = 0.03  # 3% loss triggers kill
    kill_switch_consecutive_losses: int = 5
    kill_switch_anomaly_threshold: float = 3.0  # 3 std devs
    
    # Logging
    log_dir: str = "/home/ubuntu/omega_devin/paper_trading_logs"
    log_trades: bool = True
    log_signals: bool = True
    
    # Assets to trade
    symbols: List[str] = field(default_factory=lambda: ["EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "XAUUSD"])


@dataclass
class PaperPosition:
    """A paper trading position."""
    position_id: str
    symbol: str
    side: OrderSide
    entry_price: float
    entry_time: datetime
    size: float  # Units
    stop_loss: float
    take_profit_1: float
    take_profit_2: float
    take_profit_3: float
    status: PositionStatus = PositionStatus.OPEN
    current_price: float = 0.0
    unrealized_pnl: float = 0.0
    realized_pnl: float = 0.0
    exit_price: Optional[float] = None
    exit_time: Optional[datetime] = None
    exit_reason: str = ""
    partial_exits: List[dict] = field(default_factory=list)
    signal_confidence: float = 0.0
    reason_codes: List[str] = field(default_factory=list)


@dataclass
class PaperTrade:
    """A completed paper trade."""
    trade_id: str
    symbol: str
    side: str
    entry_price: float
    entry_time: datetime
    exit_price: float
    exit_time: datetime
    size: float
    pnl: float
    pnl_pct: float
    exit_reason: str
    duration_hours: float
    signal_confidence: float
    reason_codes: List[str]


@dataclass
class TradingState:
    """Current state of the paper trading system."""
    capital: float
    equity: float
    open_positions: List[PaperPosition]
    closed_trades: List[PaperTrade]
    daily_pnl: float
    total_pnl: float
    total_pnl_pct: float
    max_drawdown: float
    current_drawdown: float
    consecutive_losses: int
    kill_switch_active: bool
    kill_switch_reason: str
    last_update: datetime


class PaperTrader:
    """
    Paper Trading Engine.
    
    This simulates live trading without real money. It uses the
    Breakthrough Intelligence Module to generate signals and
    executes them in a simulated environment.
    """
    
    def __init__(self, config: PaperTradingConfig = None):
        self.config = config or PaperTradingConfig()
        
        # Initialize state
        self.capital = self.config.initial_capital
        self.equity = self.config.initial_capital
        self.peak_equity = self.config.initial_capital
        
        self.open_positions: Dict[str, PaperPosition] = {}
        self.closed_trades: List[PaperTrade] = []
        
        self.daily_pnl = 0.0
        self.total_pnl = 0.0
        self.consecutive_losses = 0
        
        self.kill_switch_active = False
        self.kill_switch_reason = ""
        
        self._position_counter = 0
        self._trade_counter = 0
        
        # Create log directory
        os.makedirs(self.config.log_dir, exist_ok=True)
        
        # Callbacks
        self._on_trade_callback: Optional[Callable] = None
        self._on_signal_callback: Optional[Callable] = None
        self._on_kill_switch_callback: Optional[Callable] = None
        
        # Threading
        self._running = False
        self._lock = threading.Lock()
    
    def get_state(self) -> TradingState:
        """Get current trading state."""
        with self._lock:
            return TradingState(
                capital=self.capital,
                equity=self.equity,
                open_positions=list(self.open_positions.values()),
                closed_trades=self.closed_trades.copy(),
                daily_pnl=self.daily_pnl,
                total_pnl=self.total_pnl,
                total_pnl_pct=(self.total_pnl / self.config.initial_capital) * 100,
                max_drawdown=((self.peak_equity - min(self.equity, self.peak_equity)) / self.peak_equity) * 100,
                current_drawdown=((self.peak_equity - self.equity) / self.peak_equity) * 100 if self.equity < self.peak_equity else 0,
                consecutive_losses=self.consecutive_losses,
                kill_switch_active=self.kill_switch_active,
                kill_switch_reason=self.kill_switch_reason,
                last_update=datetime.now()
            )
    
    def process_signal(
        self,
        symbol: str,
        signal: dict,
        current_price: float,
        timestamp: datetime = None
    ) -> Optional[PaperPosition]:
        """
        Process a trading signal and potentially open a position.
        
        Args:
            symbol: Trading symbol (e.g., "EURUSD")
            signal: Signal from Confluence Engine
            current_price: Current market price
            timestamp: Signal timestamp
            
        Returns:
            PaperPosition if a trade was opened, None otherwise
        """
        timestamp = timestamp or datetime.now()
        
        # Check kill switch
        if self.kill_switch_active:
            self._log_signal(symbol, signal, "BLOCKED_KILL_SWITCH", timestamp)
            return None
        
        # Check if we already have a position in this symbol
        if symbol in self.open_positions:
            self._log_signal(symbol, signal, "BLOCKED_EXISTING_POSITION", timestamp)
            return None
        
        # Check max positions
        if len(self.open_positions) >= self.config.max_positions:
            self._log_signal(symbol, signal, "BLOCKED_MAX_POSITIONS", timestamp)
            return None
        
        # Check daily loss limit
        if self.daily_pnl <= -self.config.max_daily_loss * self.config.initial_capital:
            self._log_signal(symbol, signal, "BLOCKED_DAILY_LOSS_LIMIT", timestamp)
            return None
        
        # Extract signal details
        direction = signal.get('direction', 0)
        if direction == 0:
            self._log_signal(symbol, signal, "NO_DIRECTION", timestamp)
            return None
        
        confidence = signal.get('confidence', 0)
        entry_price = signal.get('entry_price', current_price)
        stop_loss = signal.get('stop_loss', 0)
        tp1 = signal.get('take_profit_1', 0)
        tp2 = signal.get('take_profit_2', 0)
        tp3 = signal.get('take_profit_3', 0)
        position_size = signal.get('position_size', {}).get('units', 0)
        
        if position_size <= 0:
            self._log_signal(symbol, signal, "INVALID_POSITION_SIZE", timestamp)
            return None
        
        # Apply slippage
        if direction == 1:  # Long
            entry_price += self.config.slippage_pips * 0.0001
            entry_price += self.config.spread_pips * 0.0001
        else:  # Short
            entry_price -= self.config.slippage_pips * 0.0001
        
        # Create position
        self._position_counter += 1
        position_id = f"POS_{self._position_counter:06d}"
        
        position = PaperPosition(
            position_id=position_id,
            symbol=symbol,
            side=OrderSide.BUY if direction == 1 else OrderSide.SELL,
            entry_price=entry_price,
            entry_time=timestamp,
            size=position_size,
            stop_loss=stop_loss,
            take_profit_1=tp1,
            take_profit_2=tp2,
            take_profit_3=tp3,
            current_price=current_price,
            signal_confidence=confidence,
            reason_codes=signal.get('reason_codes', [])
        )
        
        with self._lock:
            self.open_positions[symbol] = position
        
        self._log_signal(symbol, signal, "TRADE_OPENED", timestamp)
        self._log_trade_open(position)
        
        if self._on_signal_callback:
            self._on_signal_callback(symbol, signal, "TRADE_OPENED")
        
        return position
    
    def update_prices(self, prices: Dict[str, float], timestamp: datetime = None):
        """
        Update prices and check for exits.
        
        Args:
            prices: Dict of symbol -> current price
            timestamp: Update timestamp
        """
        timestamp = timestamp or datetime.now()
        
        positions_to_close = []
        
        with self._lock:
            for symbol, position in self.open_positions.items():
                if symbol not in prices:
                    continue
                
                current_price = prices[symbol]
                position.current_price = current_price
                
                # Calculate unrealized P&L
                if position.side == OrderSide.BUY:
                    position.unrealized_pnl = (current_price - position.entry_price) * position.size
                else:
                    position.unrealized_pnl = (position.entry_price - current_price) * position.size
                
                # Check exit conditions
                exit_price, exit_reason = self._check_exit_conditions(position, current_price)
                
                if exit_price:
                    positions_to_close.append((symbol, exit_price, exit_reason, timestamp))
        
        # Close positions outside the lock
        for symbol, exit_price, exit_reason, ts in positions_to_close:
            self._close_position(symbol, exit_price, exit_reason, ts)
        
        # Update equity
        self._update_equity()
        
        # Check kill switch conditions
        self._check_kill_switch()
    
    def _check_exit_conditions(
        self,
        position: PaperPosition,
        current_price: float
    ) -> Tuple[Optional[float], str]:
        """Check if position should be exited."""
        
        if position.side == OrderSide.BUY:
            # Long position
            if current_price <= position.stop_loss:
                return position.stop_loss, "STOP_LOSS"
            if current_price >= position.take_profit_3:
                return position.take_profit_3, "TAKE_PROFIT_3"
            if current_price >= position.take_profit_2:
                return position.take_profit_2, "TAKE_PROFIT_2"
            if current_price >= position.take_profit_1:
                return position.take_profit_1, "TAKE_PROFIT_1"
        else:
            # Short position
            if current_price >= position.stop_loss:
                return position.stop_loss, "STOP_LOSS"
            if current_price <= position.take_profit_3:
                return position.take_profit_3, "TAKE_PROFIT_3"
            if current_price <= position.take_profit_2:
                return position.take_profit_2, "TAKE_PROFIT_2"
            if current_price <= position.take_profit_1:
                return position.take_profit_1, "TAKE_PROFIT_1"
        
        return None, ""
    
    def _close_position(
        self,
        symbol: str,
        exit_price: float,
        exit_reason: str,
        timestamp: datetime
    ):
        """Close a position."""
        with self._lock:
            if symbol not in self.open_positions:
                return
            
            position = self.open_positions[symbol]
            
            # Apply slippage on exit
            if position.side == OrderSide.BUY:
                exit_price -= self.config.slippage_pips * 0.0001
            else:
                exit_price += self.config.slippage_pips * 0.0001
            
            # Calculate P&L
            if position.side == OrderSide.BUY:
                pnl = (exit_price - position.entry_price) * position.size
            else:
                pnl = (position.entry_price - exit_price) * position.size
            
            pnl_pct = pnl / self.capital
            
            # Update position
            position.exit_price = exit_price
            position.exit_time = timestamp
            position.exit_reason = exit_reason
            position.realized_pnl = pnl
            position.status = PositionStatus.CLOSED
            
            # Calculate duration
            duration = (timestamp - position.entry_time).total_seconds() / 3600
            
            # Create trade record
            self._trade_counter += 1
            trade = PaperTrade(
                trade_id=f"TRADE_{self._trade_counter:06d}",
                symbol=symbol,
                side=position.side.value,
                entry_price=position.entry_price,
                entry_time=position.entry_time,
                exit_price=exit_price,
                exit_time=timestamp,
                size=position.size,
                pnl=pnl,
                pnl_pct=pnl_pct,
                exit_reason=exit_reason,
                duration_hours=duration,
                signal_confidence=position.signal_confidence,
                reason_codes=position.reason_codes
            )
            
            self.closed_trades.append(trade)
            
            # Update capital and stats
            self.capital += pnl
            self.daily_pnl += pnl
            self.total_pnl += pnl
            
            # Track consecutive losses
            if pnl < 0:
                self.consecutive_losses += 1
            else:
                self.consecutive_losses = 0
            
            # Remove from open positions
            del self.open_positions[symbol]
        
        self._log_trade_close(trade)
        
        if self._on_trade_callback:
            self._on_trade_callback(trade)
    
    def _update_equity(self):
        """Update equity including unrealized P&L."""
        with self._lock:
            unrealized = sum(p.unrealized_pnl for p in self.open_positions.values())
            self.equity = self.capital + unrealized
            
            if self.equity > self.peak_equity:
                self.peak_equity = self.equity
    
    def _check_kill_switch(self):
        """Check if kill switch should be activated."""
        if self.kill_switch_active:
            return
        
        # Check loss threshold
        loss_pct = (self.config.initial_capital - self.equity) / self.config.initial_capital
        if loss_pct >= self.config.kill_switch_loss_pct:
            self._activate_kill_switch(f"LOSS_THRESHOLD_{loss_pct:.2%}")
            return
        
        # Check consecutive losses
        if self.consecutive_losses >= self.config.kill_switch_consecutive_losses:
            self._activate_kill_switch(f"CONSECUTIVE_LOSSES_{self.consecutive_losses}")
            return
        
        # Check max drawdown
        drawdown = (self.peak_equity - self.equity) / self.peak_equity
        if drawdown >= self.config.max_drawdown:
            self._activate_kill_switch(f"MAX_DRAWDOWN_{drawdown:.2%}")
            return
    
    def _activate_kill_switch(self, reason: str):
        """Activate the kill switch."""
        with self._lock:
            self.kill_switch_active = True
            self.kill_switch_reason = reason
        
        # Close all open positions
        for symbol in list(self.open_positions.keys()):
            position = self.open_positions[symbol]
            self._close_position(
                symbol,
                position.current_price,
                f"KILL_SWITCH_{reason}",
                datetime.now()
            )
        
        self._log_kill_switch(reason)
        
        if self._on_kill_switch_callback:
            self._on_kill_switch_callback(reason)
    
    def reset_kill_switch(self):
        """Reset the kill switch (manual override)."""
        with self._lock:
            self.kill_switch_active = False
            self.kill_switch_reason = ""
            self.consecutive_losses = 0
    
    def reset_daily_stats(self):
        """Reset daily statistics (call at start of new trading day)."""
        with self._lock:
            self.daily_pnl = 0.0
    
    def _log_signal(self, symbol: str, signal: dict, action: str, timestamp: datetime):
        """Log a signal."""
        if not self.config.log_signals:
            return
        
        log_entry = {
            "timestamp": timestamp.isoformat(),
            "symbol": symbol,
            "action": action,
            "direction": signal.get('direction', 0),
            "confidence": signal.get('confidence', 0),
            "reason_codes": signal.get('reason_codes', [])[:5]
        }
        
        log_file = os.path.join(self.config.log_dir, f"signals_{timestamp.strftime('%Y%m%d')}.jsonl")
        with open(log_file, 'a') as f:
            f.write(json.dumps(log_entry) + '\n')
    
    def _log_trade_open(self, position: PaperPosition):
        """Log trade open."""
        if not self.config.log_trades:
            return
        
        log_entry = {
            "event": "OPEN",
            "timestamp": position.entry_time.isoformat(),
            "position_id": position.position_id,
            "symbol": position.symbol,
            "side": position.side.value,
            "entry_price": position.entry_price,
            "size": position.size,
            "stop_loss": position.stop_loss,
            "take_profit_1": position.take_profit_1,
            "confidence": position.signal_confidence
        }
        
        log_file = os.path.join(self.config.log_dir, f"trades_{position.entry_time.strftime('%Y%m%d')}.jsonl")
        with open(log_file, 'a') as f:
            f.write(json.dumps(log_entry) + '\n')
    
    def _log_trade_close(self, trade: PaperTrade):
        """Log trade close."""
        if not self.config.log_trades:
            return
        
        log_entry = {
            "event": "CLOSE",
            "timestamp": trade.exit_time.isoformat(),
            "trade_id": trade.trade_id,
            "symbol": trade.symbol,
            "side": trade.side,
            "entry_price": trade.entry_price,
            "exit_price": trade.exit_price,
            "size": trade.size,
            "pnl": trade.pnl,
            "pnl_pct": trade.pnl_pct,
            "exit_reason": trade.exit_reason,
            "duration_hours": trade.duration_hours
        }
        
        log_file = os.path.join(self.config.log_dir, f"trades_{trade.exit_time.strftime('%Y%m%d')}.jsonl")
        with open(log_file, 'a') as f:
            f.write(json.dumps(log_entry) + '\n')
    
    def _log_kill_switch(self, reason: str):
        """Log kill switch activation."""
        log_entry = {
            "event": "KILL_SWITCH",
            "timestamp": datetime.now().isoformat(),
            "reason": reason,
            "capital": self.capital,
            "equity": self.equity,
            "total_pnl": self.total_pnl,
            "consecutive_losses": self.consecutive_losses
        }
        
        log_file = os.path.join(self.config.log_dir, "kill_switch.jsonl")
        with open(log_file, 'a') as f:
            f.write(json.dumps(log_entry) + '\n')
    
    def get_performance_summary(self) -> dict:
        """Get performance summary."""
        if not self.closed_trades:
            return {
                "total_trades": 0,
                "winning_trades": 0,
                "losing_trades": 0,
                "win_rate": 0.0,
                "total_pnl": 0.0,
                "total_pnl_pct": 0.0,
                "profit_factor": 0.0,
                "avg_win": 0.0,
                "avg_loss": 0.0,
                "max_drawdown": 0.0,
                "sharpe_ratio": 0.0
            }
        
        wins = [t for t in self.closed_trades if t.pnl > 0]
        losses = [t for t in self.closed_trades if t.pnl <= 0]
        
        gross_profit = sum(t.pnl for t in wins)
        gross_loss = abs(sum(t.pnl for t in losses))
        
        returns = [t.pnl_pct for t in self.closed_trades]
        avg_return = sum(returns) / len(returns)
        std_return = math.sqrt(sum((r - avg_return) ** 2 for r in returns) / len(returns)) if len(returns) > 1 else 0
        
        return {
            "total_trades": len(self.closed_trades),
            "winning_trades": len(wins),
            "losing_trades": len(losses),
            "win_rate": len(wins) / len(self.closed_trades),
            "total_pnl": self.total_pnl,
            "total_pnl_pct": (self.total_pnl / self.config.initial_capital) * 100,
            "profit_factor": gross_profit / gross_loss if gross_loss > 0 else 0,
            "avg_win": gross_profit / len(wins) if wins else 0,
            "avg_loss": gross_loss / len(losses) if losses else 0,
            "max_drawdown": ((self.peak_equity - min(self.equity, self.peak_equity)) / self.peak_equity) * 100,
            "sharpe_ratio": (avg_return / std_return) * math.sqrt(252) if std_return > 0 else 0,
            "current_capital": self.capital,
            "current_equity": self.equity,
            "open_positions": len(self.open_positions)
        }
    
    def set_callbacks(
        self,
        on_trade: Callable = None,
        on_signal: Callable = None,
        on_kill_switch: Callable = None
    ):
        """Set callback functions."""
        self._on_trade_callback = on_trade
        self._on_signal_callback = on_signal
        self._on_kill_switch_callback = on_kill_switch
