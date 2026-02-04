#!/usr/bin/env python3
"""
OMEGA-DEVIN Paper Trading Runner
================================

This script runs the paper trading system with the Breakthrough Intelligence Module.

Usage:
    # Run with simulated data (fast replay)
    python3 run_paper_trading.py --mode simulate --speed 100
    
    # Run with live data (real-time)
    python3 run_paper_trading.py --mode live
    
    # Run quick test
    python3 run_paper_trading.py --mode test
"""

import sys
import os
import argparse
import time
from datetime import datetime

sys.path.insert(0, '/home/ubuntu/omega_devin')

from chimera.paper_trading.paper_trader import PaperTrader, PaperTradingConfig
from chimera.paper_trading.live_feed import SimulatedFeed, LiveDataFeed, load_data_for_simulation
from chimera.paper_trading.monitor import TradingMonitor, print_live_status
from chimera.intelligence.breakthrough_engine import BreakthroughEngine, BreakthroughConfig
from chimera.intelligence.multi_timeframe import Timeframe


def run_simulation(speed_multiplier: float = 10.0, max_bars: int = None):
    """Run paper trading with simulated data."""
    print("="*60)
    print("OMEGA-DEVIN PAPER TRADING - SIMULATION MODE")
    print("="*60)
    
    # Load historical data
    print("\nLoading historical data...")
    data = load_data_for_simulation(
        symbols=["EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "XAUUSD"]
    )
    
    if not data:
        print("ERROR: No data loaded!")
        return
    
    # Limit data if specified
    if max_bars:
        for symbol in data:
            data[symbol] = data[symbol][:max_bars]
    
    # Initialize components
    print("\nInitializing trading system...")
    
    trading_config = PaperTradingConfig(
        initial_capital=10000.0,
        max_risk_per_trade=0.02,
        max_daily_loss=0.05,
        max_positions=3,
        slippage_pips=0.5,
        spread_pips=1.0,
        kill_switch_loss_pct=0.05,
        kill_switch_consecutive_losses=5,
    )
    
    trader = PaperTrader(trading_config)
    monitor = TradingMonitor()
    
    breakthrough_config = BreakthroughConfig(
        min_confluence_score=0.45,
        min_risk_reward=1.2,
        max_risk_per_trade=0.02,
    )
    
    engines = {
        symbol: BreakthroughEngine(breakthrough_config)
        for symbol in data.keys()
    }
    
    # Set up callbacks
    def on_trade(trade):
        monitor.on_trade_closed(vars(trade))
    
    def on_kill_switch(reason):
        monitor.on_kill_switch(reason)
        print(f"\n!!! KILL SWITCH ACTIVATED: {reason} !!!")
    
    trader.set_callbacks(on_trade=on_trade, on_kill_switch=on_kill_switch)
    
    # Create simulated feed
    feed = SimulatedFeed(
        data=data,
        speed_multiplier=speed_multiplier,
        bar_interval_seconds=3600  # 1 hour bars
    )
    
    print(f"\nStarting simulation at {speed_multiplier}x speed...")
    print("Press Ctrl+C to stop\n")
    
    # Track progress
    total_bars = min(len(bars) for bars in data.values())
    processed_bars = 0
    last_print = time.time()
    
    try:
        # Process each bar
        while not feed.is_complete():
            # Get current bars and prices
            current_bars = feed.get_current_bars()
            prices = feed.get_latest_prices()
            
            if not prices:
                feed._replay_loop()  # Advance one step
                continue
            
            # Update trader with current prices
            trader.update_prices(prices)
            
            # Generate signals for each symbol
            for symbol in data.keys():
                if symbol in trader.open_positions:
                    continue  # Already have a position
                
                # Get history for analysis
                history = feed.get_history(symbol, lookback=250)
                
                if len(history) < 200:
                    continue
                
                # Analyze with breakthrough engine
                engine = engines[symbol]
                signal = engine.confluence_engine.analyze(
                    bars=history,
                    capital=trader.capital,
                )
                
                # Convert signal to dict for paper trader
                if signal.direction.value != 0:
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
                    trader.process_signal(
                        symbol=symbol,
                        signal=signal_dict,
                        current_price=prices.get(symbol, signal.entry_price)
                    )
            
            # Advance feed
            with feed._lock:
                for symbol in data.keys():
                    idx = feed._current_index[symbol]
                    if idx < len(data[symbol]) - 1:
                        feed._current_index[symbol] += 1
                        new_idx = feed._current_index[symbol]
                        feed._latest_prices[symbol] = data[symbol][new_idx]['close']
            
            processed_bars += 1
            
            # Print status periodically
            if time.time() - last_print > 2.0:
                state = trader.get_state()
                progress = (processed_bars / total_bars) * 100
                print(f"\rProgress: {progress:.1f}% | Capital: ${state.capital:,.2f} | "
                      f"P&L: ${state.total_pnl:+,.2f} | Trades: {len(state.closed_trades)} | "
                      f"Open: {len(state.open_positions)}", end="")
                last_print = time.time()
            
            # Small delay for speed control
            time.sleep(0.001 / speed_multiplier)
    
    except KeyboardInterrupt:
        print("\n\nSimulation stopped by user.")
    
    # Final report
    print("\n\n" + "="*60)
    print("SIMULATION COMPLETE")
    print("="*60)
    
    report = monitor.generate_report()
    print(report)
    
    # Save report
    report_path = monitor.save_report()
    data_path = monitor.export_data()
    
    print(f"\nReport saved to: {report_path}")
    print(f"Data saved to: {data_path}")
    
    return trader, monitor


def run_live():
    """Run paper trading with live data."""
    print("="*60)
    print("OMEGA-DEVIN PAPER TRADING - LIVE MODE")
    print("="*60)
    print("\nNote: Live mode uses yfinance for data.")
    print("For production, use a proper market data provider.")
    print("\nPress Ctrl+C to stop\n")
    
    # Initialize components
    trading_config = PaperTradingConfig(
        initial_capital=10000.0,
        max_risk_per_trade=0.02,
        max_daily_loss=0.05,
        max_positions=3,
    )
    
    trader = PaperTrader(trading_config)
    monitor = TradingMonitor()
    
    breakthrough_config = BreakthroughConfig(
        min_confluence_score=0.45,
        min_risk_reward=1.2,
    )
    
    # Set up callbacks
    def on_trade(trade):
        monitor.on_trade_closed(vars(trade))
        print(f"\nTrade closed: {trade.symbol} | P&L: ${trade.pnl:+.2f}")
    
    def on_kill_switch(reason):
        monitor.on_kill_switch(reason)
        print(f"\n!!! KILL SWITCH ACTIVATED: {reason} !!!")
    
    trader.set_callbacks(on_trade=on_trade, on_kill_switch=on_kill_switch)
    
    # Create live feed
    symbols = ["EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "XAUUSD"]
    feed = LiveDataFeed(symbols=symbols, update_interval=60)
    
    # Price update callback
    def on_price_update(prices):
        trader.update_prices(prices)
        print_live_status(trader, monitor)
    
    feed.subscribe(on_price_update)
    feed.start()
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n\nStopping live trading...")
        feed.stop()
    
    # Final report
    report = monitor.generate_report()
    print(report)
    
    return trader, monitor


def run_test():
    """Run a quick test of the paper trading system."""
    print("="*60)
    print("OMEGA-DEVIN PAPER TRADING - QUICK TEST")
    print("="*60)
    
    # Run simulation with limited data
    trader, monitor = run_simulation(speed_multiplier=1000.0, max_bars=500)
    
    # Verify results
    state = trader.get_state()
    summary = monitor.tracker.get_summary()
    
    print("\n" + "="*60)
    print("TEST RESULTS")
    print("="*60)
    print(f"Trades executed: {summary['total_trades']}")
    print(f"Win rate: {summary['win_rate']:.1%}")
    print(f"Total P&L: ${summary['total_pnl']:+.2f}")
    print(f"Kill switch triggered: {state.kill_switch_active}")
    
    if summary['total_trades'] > 0 and summary['win_rate'] > 0.5:
        print("\nTEST PASSED!")
    else:
        print("\nTEST COMPLETED (review results)")
    
    return trader, monitor


def main():
    parser = argparse.ArgumentParser(description="OMEGA-DEVIN Paper Trading")
    parser.add_argument(
        "--mode",
        choices=["simulate", "live", "test"],
        default="test",
        help="Trading mode"
    )
    parser.add_argument(
        "--speed",
        type=float,
        default=100.0,
        help="Simulation speed multiplier (default: 100)"
    )
    parser.add_argument(
        "--bars",
        type=int,
        default=None,
        help="Maximum bars to process (default: all)"
    )
    
    args = parser.parse_args()
    
    if args.mode == "simulate":
        run_simulation(speed_multiplier=args.speed, max_bars=args.bars)
    elif args.mode == "live":
        run_live()
    elif args.mode == "test":
        run_test()


if __name__ == "__main__":
    main()
