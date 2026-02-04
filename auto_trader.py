#!/usr/bin/env python3
"""
OMEGA-DEVIN Automated Live Trading
==================================

This script runs automated paper trading with live market data.
It automatically:
1. Fetches real-time prices from yfinance
2. Generates signals using the Breakthrough Intelligence Module
3. Executes paper trades with full risk management
4. Logs all activity and sends status updates
5. Runs continuously until stopped

Usage:
    # Start automated trading
    python3 auto_trader.py
    
    # Start with custom settings
    python3 auto_trader.py --capital 10000 --risk 0.02 --update-interval 60

The script will:
- Run continuously during market hours
- Generate hourly status reports
- Save all trades to paper_trading_logs/
- Automatically stop if kill-switch triggers
"""

import sys
import os
import argparse
import time
import json
import signal
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import threading

sys.path.insert(0, '/home/ubuntu/omega_devin')

# Check for required packages
try:
    import yfinance as yf
    import pandas as pd
    import numpy as np
except ImportError as e:
    print(f"Missing required package: {e}")
    print("Install with: pip install yfinance pandas numpy")
    sys.exit(1)

from chimera.paper_trading.paper_trader import PaperTrader, PaperTradingConfig
from chimera.paper_trading.monitor import TradingMonitor, PerformanceTracker
from chimera.intelligence.breakthrough_engine import BreakthroughEngine, BreakthroughConfig
from chimera.intelligence.confluence_engine import ConfluenceEngine, ConfluenceConfig


class AutomatedTrader:
    """
    Automated paper trading system that runs continuously.
    """
    
    def __init__(
        self,
        initial_capital: float = 10000.0,
        max_risk_per_trade: float = 0.02,
        update_interval: int = 60,  # seconds
        symbols: List[str] = None,
    ):
        self.initial_capital = initial_capital
        self.max_risk_per_trade = max_risk_per_trade
        self.update_interval = update_interval
        self.symbols = symbols or ["EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "XAUUSD"]
        
        # Symbol mapping for yfinance
        self.yf_symbols = {
            "EURUSD": "EURUSD=X",
            "GBPUSD": "GBPUSD=X",
            "USDJPY": "USDJPY=X",
            "AUDUSD": "AUDUSD=X",
            "XAUUSD": "GC=F",
        }
        
        # Initialize components
        self._init_trading_system()
        
        # State
        self.running = False
        self.start_time = None
        self.last_status_time = None
        self.price_history: Dict[str, List[dict]] = {s: [] for s in self.symbols}
        
        # Logging
        self.log_dir = "/home/ubuntu/omega_devin/paper_trading_logs"
        os.makedirs(self.log_dir, exist_ok=True)
        
        # Signal handling
        signal.signal(signal.SIGINT, self._handle_shutdown)
        signal.signal(signal.SIGTERM, self._handle_shutdown)
    
    def _init_trading_system(self):
        """Initialize all trading components."""
        # Paper trader config
        trading_config = PaperTradingConfig(
            initial_capital=self.initial_capital,
            max_risk_per_trade=self.max_risk_per_trade,
            max_daily_loss=0.05,
            max_positions=3,
            slippage_pips=0.5,
            spread_pips=1.5,  # Slightly higher for live
            kill_switch_loss_pct=0.03,
            kill_switch_consecutive_losses=5,
            symbols=self.symbols,
        )
        
        self.trader = PaperTrader(trading_config)
        self.monitor = TradingMonitor(log_dir=self.log_dir)
        
        # Breakthrough engine config
        breakthrough_config = BreakthroughConfig(
            min_confluence_score=0.50,  # Slightly higher for live
            min_risk_reward=1.5,
            max_risk_per_trade=self.max_risk_per_trade,
        )
        
        # One engine per symbol
        self.engines = {
            symbol: BreakthroughEngine(breakthrough_config)
            for symbol in self.symbols
        }
        
        # Set up callbacks
        self.trader.set_callbacks(
            on_trade=self._on_trade_closed,
            on_signal=self._on_signal,
            on_kill_switch=self._on_kill_switch,
        )
    
    def _on_trade_closed(self, trade):
        """Handle trade closed event."""
        self.monitor.on_trade_closed(vars(trade))
        self._log(f"TRADE CLOSED: {trade.symbol} | P&L: ${trade.pnl:+.2f} | Reason: {trade.exit_reason}")
    
    def _on_signal(self, symbol, signal, action):
        """Handle signal event."""
        self._log(f"SIGNAL: {symbol} | Action: {action} | Confidence: {signal.get('confidence', 0):.2f}")
    
    def _on_kill_switch(self, reason):
        """Handle kill switch activation."""
        self.monitor.on_kill_switch(reason)
        self._log(f"!!! KILL SWITCH ACTIVATED: {reason} !!!")
        self._send_alert(f"KILL SWITCH: {reason}")
    
    def _log(self, message: str):
        """Log a message with timestamp."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_line = f"[{timestamp}] {message}"
        print(log_line)
        
        # Also write to log file
        log_file = os.path.join(self.log_dir, f"auto_trader_{datetime.now().strftime('%Y%m%d')}.log")
        with open(log_file, 'a') as f:
            f.write(log_line + '\n')
    
    def _send_alert(self, message: str):
        """Send an alert (placeholder for email/SMS/webhook)."""
        alert_file = os.path.join(self.log_dir, "alerts.jsonl")
        alert = {
            "timestamp": datetime.now().isoformat(),
            "message": message
        }
        with open(alert_file, 'a') as f:
            f.write(json.dumps(alert) + '\n')
    
    def fetch_prices(self) -> Dict[str, float]:
        """Fetch current prices from yfinance."""
        prices = {}
        
        for symbol in self.symbols:
            yf_symbol = self.yf_symbols.get(symbol, f"{symbol}=X")
            
            try:
                ticker = yf.Ticker(yf_symbol)
                hist = ticker.history(period="1d", interval="1m")
                
                if len(hist) > 0:
                    prices[symbol] = float(hist['Close'].iloc[-1])
            except Exception as e:
                self._log(f"Error fetching {symbol}: {e}")
        
        return prices
    
    def fetch_hourly_history(self, symbol: str, lookback_days: int = 30) -> List[dict]:
        """Fetch hourly historical data for analysis."""
        yf_symbol = self.yf_symbols.get(symbol, f"{symbol}=X")
        
        try:
            ticker = yf.Ticker(yf_symbol)
            hist = ticker.history(period=f"{lookback_days}d", interval="1h")
            
            if len(hist) == 0:
                return []
            
            bars = []
            for idx, row in hist.iterrows():
                bar = {
                    'timestamp': idx.isoformat(),
                    'open': float(row['Open']),
                    'high': float(row['High']),
                    'low': float(row['Low']),
                    'close': float(row['Close']),
                    'volume': float(row['Volume']) if row['Volume'] > 0 else 1000.0
                }
                bars.append(bar)
            
            return bars
        
        except Exception as e:
            self._log(f"Error fetching history for {symbol}: {e}")
            return []
    
    def analyze_and_trade(self, symbol: str, prices: Dict[str, float]):
        """Analyze a symbol and potentially open a trade."""
        if symbol in self.trader.open_positions:
            return  # Already have a position
        
        if self.trader.kill_switch_active:
            return  # Kill switch is active
        
        # Fetch historical data for analysis
        history = self.fetch_hourly_history(symbol, lookback_days=30)
        
        if len(history) < 200:
            self._log(f"{symbol}: Insufficient history ({len(history)} bars)")
            return
        
        # Analyze with breakthrough engine
        engine = self.engines[symbol]
        signal = engine.confluence_engine.analyze(
            bars=history,
            capital=self.trader.capital,
        )
        
        # Check if we have a valid signal
        if signal.direction.value == 0:
            return  # No trade signal
        
        if signal.strength.value < 2:  # Less than MODERATE
            return  # Signal too weak
        
        # Convert signal to dict for paper trader
        signal_dict = {
            'direction': signal.direction.value,
            'confidence': signal.confidence,
            'entry_price': signal.entry_price,
            'stop_loss': signal.stop_loss,
            'take_profit_1': signal.take_profit_1,
            'take_profit_2': signal.take_profit_2,
            'take_profit_3': signal.take_profit_3,
            'position_size': {
                'units': signal.position_size.units
            },
            'reason_codes': signal.reason_codes
        }
        
        # Process signal
        current_price = prices.get(symbol, signal.entry_price)
        position = self.trader.process_signal(
            symbol=symbol,
            signal=signal_dict,
            current_price=current_price
        )
        
        if position:
            direction = "LONG" if position.side.value == "buy" else "SHORT"
            self._log(f"TRADE OPENED: {symbol} {direction} @ {position.entry_price:.5f} | "
                     f"SL: {position.stop_loss:.5f} | TP1: {position.take_profit_1:.5f} | "
                     f"Confidence: {signal.confidence:.2f}")
    
    def print_status(self):
        """Print current trading status."""
        state = self.trader.get_state()
        summary = self.monitor.tracker.get_summary()
        
        print("\n" + "="*60)
        print(f"OMEGA-DEVIN AUTO TRADER - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*60)
        print(f"Capital: ${state.capital:,.2f} | Equity: ${state.equity:,.2f}")
        print(f"Total P&L: ${state.total_pnl:+,.2f} ({state.total_pnl_pct:+.2f}%)")
        print(f"Daily P&L: ${state.daily_pnl:+,.2f}")
        print(f"Trades: {summary['total_trades']} | Win Rate: {summary['win_rate']:.1%}")
        print(f"Open Positions: {len(state.open_positions)}")
        
        for pos in state.open_positions:
            direction = "LONG" if pos.side.value == "buy" else "SHORT"
            print(f"  {pos.symbol} {direction} @ {pos.entry_price:.5f} | "
                  f"Current: {pos.current_price:.5f} | P&L: ${pos.unrealized_pnl:+.2f}")
        
        if state.kill_switch_active:
            print(f"\n!!! KILL SWITCH ACTIVE: {state.kill_switch_reason} !!!")
        
        print("="*60 + "\n")
    
    def run(self):
        """Run the automated trading loop."""
        self.running = True
        self.start_time = datetime.now()
        self.last_status_time = datetime.now()
        
        self._log("="*60)
        self._log("OMEGA-DEVIN AUTOMATED TRADING STARTED")
        self._log(f"Capital: ${self.initial_capital:,.2f}")
        self._log(f"Symbols: {', '.join(self.symbols)}")
        self._log(f"Update Interval: {self.update_interval}s")
        self._log("="*60)
        
        iteration = 0
        
        while self.running:
            try:
                iteration += 1
                
                # Fetch current prices
                prices = self.fetch_prices()
                
                if not prices:
                    self._log("No prices available, waiting...")
                    time.sleep(self.update_interval)
                    continue
                
                # Update trader with current prices
                self.trader.update_prices(prices)
                
                # Analyze each symbol for potential trades
                for symbol in self.symbols:
                    if symbol in prices:
                        self.analyze_and_trade(symbol, prices)
                
                # Print status every 5 minutes
                if (datetime.now() - self.last_status_time).seconds >= 300:
                    self.print_status()
                    self.last_status_time = datetime.now()
                
                # Check if kill switch triggered
                if self.trader.kill_switch_active:
                    self._log("Kill switch active, stopping trading...")
                    self.running = False
                    break
                
                # Wait for next update
                time.sleep(self.update_interval)
                
            except Exception as e:
                self._log(f"Error in trading loop: {e}")
                time.sleep(self.update_interval)
        
        # Final report
        self._generate_final_report()
    
    def _generate_final_report(self):
        """Generate final trading report."""
        self._log("\n" + "="*60)
        self._log("TRADING SESSION ENDED")
        self._log("="*60)
        
        report = self.monitor.generate_report()
        print(report)
        
        # Save report
        report_path = self.monitor.save_report()
        data_path = self.monitor.export_data()
        
        self._log(f"Report saved to: {report_path}")
        self._log(f"Data saved to: {data_path}")
    
    def _handle_shutdown(self, signum, frame):
        """Handle shutdown signal."""
        self._log("\nShutdown signal received...")
        self.running = False


def main():
    parser = argparse.ArgumentParser(description="OMEGA-DEVIN Automated Paper Trading")
    parser.add_argument("--capital", type=float, default=10000.0, help="Initial capital")
    parser.add_argument("--risk", type=float, default=0.02, help="Max risk per trade (0.02 = 2%)")
    parser.add_argument("--update-interval", type=int, default=60, help="Price update interval in seconds")
    parser.add_argument("--symbols", type=str, default="EURUSD,GBPUSD,USDJPY,AUDUSD,XAUUSD",
                       help="Comma-separated list of symbols to trade")
    
    args = parser.parse_args()
    
    symbols = [s.strip() for s in args.symbols.split(",")]
    
    trader = AutomatedTrader(
        initial_capital=args.capital,
        max_risk_per_trade=args.risk,
        update_interval=args.update_interval,
        symbols=symbols,
    )
    
    trader.run()


if __name__ == "__main__":
    main()
