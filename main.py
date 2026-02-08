#!/usr/bin/env python3
# OMEGA-DEVIN // MASTER CONTROL PROGRAM
# Repository: github.com/princeleuel-code/OMEGA-DEVIN-
# The UNMATCHABLE Trading AGI

import time
import sys
import os
import json
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.devin_optimizer import DevinBrain
from core.unified_intelligence import UnifiedIntelligence
from ingestors.market_data import MarketDataFeed
from strategies.liquidity_hunter import LiquidityHunter
from strategies.smc_strategy import SMCStrategy
from strategies.confluence_strategy import ConfluenceStrategy
from execution.trade_executor import TradeExecutor
from execution.risk_manager import RiskManager

# ASCII Art Banner
BANNER = """
░█████╗░███╗░░░███╗███████╗░██████╗░░█████╗░░░░░░░██████╗░███████╗██╗░░░██╗██╗███╗░░██╗
██╔══██╗████╗░████║██╔════╝██╔════╝░██╔══██╗░░░░░░██╔══██╗██╔════╝██║░░░██║██║████╗░██║
██║░░██║██╔████╔██║█████╗░░██║░░██╗░███████║█████╗██║░░██║█████╗░░╚██╗░██╔╝██║██╔██╗██║
██║░░██║██║╚██╔╝██║██╔══╝░░██║░░╚██╗██╔══██║╚════╝██║░░██║██╔══╝░░░╚████╔╝░██║██║╚████║
╚█████╔╝██║░╚═╝░██║███████╗╚██████╔╝██║░░██║░░░░░░██████╔╝███████╗░░╚██╔╝░░██║██║░╚███║
░╚════╝░╚═╝░░░░░╚═╝╚══════╝░╚═════╝░╚═╝░░╚═╝░░░░░░╚═════╝░╚══════╝░░░╚═╝░░░╚═╝╚═╝░░╚══╝

[ SYSTEM: OMEGA-DEVIN ] [ STATUS: ONLINE ] [ MODE: AUTONOMOUS ]
[ 18 INTELLIGENCE MODULES ] [ SELF-OPTIMIZING ] [ FAIL-CLOSED ]
"""

class OmegaDevin:
    """
    OMEGA-DEVIN: The UNMATCHABLE Trading AGI
    
    Combines:
    - 18 Intelligence Modules
    - Self-Optimizing Brain (Devin)
    - Multiple Trading Strategies
    - Risk Management
    - Trade Execution
    
    All working together as ONE unified system.
    """
    
    def __init__(self, mode: str = "PAPER", symbols: list = None):
        print(BANNER)
        
        self.mode = mode
        self.symbols = symbols or ["EURUSD", "GBPUSD", "USDJPY", "XAUUSD"]
        self.running = False
        self.cycle_count = 0
        
        # Initialize components
        print("\n[OMEGA]: Initializing components...")
        
        # The Brain - Self-Optimizing
        self.brain = DevinBrain()
        print("   [OK] Devin Brain initialized")
        
        # The Intelligence - 18 Modules Combined
        self.intelligence = UnifiedIntelligence()
        print("   [OK] Unified Intelligence initialized (18 modules)")
        
        # The Eyes - Market Data
        self.data_feed = MarketDataFeed(data_source="yfinance")
        print("   [OK] Market Data Feed initialized")
        
        # The Strategies
        self.liquidity_hunter = LiquidityHunter()
        self.smc_strategy = SMCStrategy()
        self.confluence_strategy = ConfluenceStrategy(min_confluence=6, min_confidence=0.70)
        print("   [OK] Strategies initialized (Liquidity Hunter, SMC, Confluence)")
        
        # The Hands - Execution
        self.executor = TradeExecutor(mode=mode)
        print(f"   [OK] Trade Executor initialized ({mode} mode)")
        
        # The Shield - Risk Management
        self.risk_manager = RiskManager()
        print("   [OK] Risk Manager initialized")
        
        print("\n[OMEGA]: All systems operational. Ready to trade.")
    
    def run(self, interval: int = 60):
        """
        Main trading loop
        
        Args:
            interval: Seconds between cycles
        """
        self.running = True
        print(f"\n[OMEGA]: Starting main loop (interval: {interval}s)")
        print("=" * 60)
        
        while self.running:
            try:
                self.cycle_count += 1
                print(f"\n[OMEGA]: === CYCLE {self.cycle_count} === {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                
                # 1. Self-Optimization Check
                print("\n[STEP 1]: Running self-optimization...")
                optimization_result = self.brain.analyze_performance()
                print(f"   Status: {optimization_result.get('status', 'unknown')}")
                
                # 2. Risk Check
                print("\n[STEP 2]: Checking risk status...")
                risk_check = self.risk_manager.can_trade()
                if not risk_check['allowed']:
                    print(f"   BLOCKED: {risk_check['reason']}")
                    print(f"   Sleeping {interval}s...")
                    time.sleep(interval)
                    continue
                print(f"   OK: {risk_check['reason']}")
                
                # 3. Analyze Each Symbol
                for symbol in self.symbols:
                    print(f"\n[STEP 3]: Analyzing {symbol}...")
                    
                    # Fetch market data
                    bars = self.data_feed.fetch_ohlcv(symbol, "1h", 100)
                    if not bars:
                        print(f"   No data for {symbol}")
                        continue
                    
                    current_price = bars[-1]['close']
                    print(f"   Current price: {current_price:.5f}")
                    
                    # Run unified intelligence
                    analysis = self.intelligence.analyze({"bars": bars, "symbol": symbol})
                    print(f"   Direction: {analysis['direction']}")
                    print(f"   Confidence: {analysis['confidence']:.2%}")
                    print(f"   Confluence: {analysis['confluence']}")
                    
                    # Check for high confluence setup
                    confluence_signal = self.confluence_strategy.analyze(bars, analysis)
                    
                    if confluence_signal['signal'] != 'WAIT':
                        print(f"\n   *** HIGH CONFLUENCE SIGNAL: {confluence_signal['signal']} ***")
                        print(f"   Reason: {confluence_signal['reason']}")
                        
                        # Calculate position size
                        trade_setup = analysis.get('trade_setup', {})
                        if trade_setup:
                            position_size = self.risk_manager.calculate_position_size(
                                entry_price=trade_setup.get('entry', current_price),
                                stop_loss=trade_setup.get('stop_loss', current_price * 0.99),
                                symbol=symbol
                            )
                            
                            print(f"   Position size: {position_size['size']} lots")
                            print(f"   Risk: ${position_size['risk_amount']:.2f} ({position_size['risk_percent']:.2%})")
                            
                            # Execute trade (in paper mode)
                            if self.mode == "PAPER" and position_size['size'] > 0:
                                order = self.executor.place_order(
                                    symbol=symbol,
                                    side="BUY" if confluence_signal['signal'] == "LONG" else "SELL",
                                    quantity=position_size['size'],
                                    order_type="MARKET",
                                    stop_loss=trade_setup.get('stop_loss'),
                                    take_profit=trade_setup.get('take_profit_1'),
                                    reason=confluence_signal['reason']
                                )
                                print(f"   Order placed: {order['order_id']}")
                    else:
                        print(f"   No trade: {confluence_signal['reason']}")
                    
                    # Also check liquidity hunter
                    liquidity_signal = self.liquidity_hunter.analyze(bars)
                    if liquidity_signal['signal'] != 'WAIT':
                        print(f"\n   [LIQUIDITY HUNTER]: {liquidity_signal['signal']}")
                        print(f"   {liquidity_signal['reason']}")
                
                # 4. Check open positions
                print("\n[STEP 4]: Checking positions...")
                positions = self.executor.get_all_positions()
                if positions:
                    for symbol, pos in positions.items():
                        print(f"   {symbol}: {pos['quantity']} @ {pos['avg_price']:.5f}")
                else:
                    print("   No open positions")
                
                # 5. Performance summary
                print("\n[STEP 5]: Performance summary...")
                risk_status = self.risk_manager.get_risk_status()
                print(f"   Equity: ${risk_status['current_equity']:.2f}")
                print(f"   Daily PnL: ${risk_status['daily_pnl']:.2f}")
                print(f"   Positions: {risk_status['open_positions']}/{risk_status['max_positions']}")
                
                print(f"\n[OMEGA]: Cycle complete. Sleeping {interval}s...")
                print("=" * 60)
                time.sleep(interval)
                
            except KeyboardInterrupt:
                print("\n[OMEGA]: Keyboard interrupt received. Shutting down...")
                self.stop()
            except Exception as e:
                print(f"\n[OMEGA]: Error in main loop: {e}")
                import traceback
                traceback.print_exc()
                time.sleep(interval)
    
    def stop(self):
        """Stop the trading loop"""
        self.running = False
        print("\n[OMEGA]: Shutdown complete.")
    
    def analyze_symbol(self, symbol: str) -> dict:
        """
        Analyze a single symbol (for manual use)
        
        Args:
            symbol: Trading symbol
            
        Returns:
            Complete analysis
        """
        bars = self.data_feed.fetch_ohlcv(symbol, "1h", 100)
        if not bars:
            return {"error": "No data"}
        
        analysis = self.intelligence.analyze({"bars": bars, "symbol": symbol})
        liquidity = self.liquidity_hunter.analyze(bars)
        smc = self.smc_strategy.analyze(bars)
        confluence = self.confluence_strategy.analyze(bars, analysis)
        
        return {
            "symbol": symbol,
            "current_price": bars[-1]['close'],
            "unified_analysis": analysis,
            "liquidity_hunter": liquidity,
            "smc_analysis": smc,
            "confluence_signal": confluence
        }


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="OMEGA-DEVIN Trading AGI")
    parser.add_argument("--mode", choices=["PAPER", "LIVE"], default="PAPER", help="Trading mode")
    parser.add_argument("--symbols", nargs="+", default=["EURUSD", "GBPUSD"], help="Symbols to trade")
    parser.add_argument("--interval", type=int, default=60, help="Cycle interval in seconds")
    parser.add_argument("--analyze", type=str, help="Analyze a single symbol and exit")
    
    args = parser.parse_args()
    
    # Initialize OMEGA-DEVIN
    omega = OmegaDevin(mode=args.mode, symbols=args.symbols)
    
    if args.analyze:
        # Single analysis mode
        result = omega.analyze_symbol(args.analyze)
        print("\n" + "=" * 60)
        print(f"ANALYSIS FOR {args.analyze}")
        print("=" * 60)
        print(json.dumps(result, indent=2, default=str))
    else:
        # Run main loop
        omega.run(interval=args.interval)


if __name__ == "__main__":
    main()
