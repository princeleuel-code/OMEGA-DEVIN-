#!/usr/bin/env python3
"""
OMEGA-DEVIN Live Simulation Replay

Replays historical data as if it's happening in real-time,
running the 14-source LIVING Intelligence system on each bar.
"""

import json
import time
from datetime import datetime
from typing import List, Dict, Any

from chimera.consciousness.ultimate_intelligence import UltimateIntelligence
from chimera.consciousness.institutional_flow_detection import InstitutionalFlowDetection
from chimera.consciousness.cross_asset_correlation import CrossAssetCorrelationIntelligence


def load_replay_data(filepath: str) -> List[Dict[str, Any]]:
    """Load historical data for replay"""
    with open(filepath, 'r') as f:
        return json.load(f)


def run_live_simulation(
    data_path: str = "/home/ubuntu/omega_devin/data/replay_data.json",
    delay_seconds: float = 2.0,
    max_bars: int = 50
):
    """
    Run live simulation replaying historical data
    
    Args:
        data_path: Path to replay data JSON
        delay_seconds: Delay between bars (simulates real-time)
        max_bars: Maximum bars to process
    """
    print("=" * 80)
    print("OMEGA-DEVIN LIVE SIMULATION")
    print("14 Intelligence Sources - Real-Time Analysis")
    print("=" * 80)
    print()
    
    # Load data
    all_data = load_replay_data(data_path)
    print(f"Loaded {len(all_data)} bars for replay")
    print(f"Processing {min(max_bars, len(all_data))} bars with {delay_seconds}s delay")
    print()
    
    # Initialize intelligence systems
    ultimate = UltimateIntelligence(account_balance=10000)
    inst_flow = InstitutionalFlowDetection()
    cross_asset = CrossAssetCorrelationIntelligence()
    
    # Track signals
    signals_history = []
    trades = []
    
    # Process bars
    bars_processed = []
    
    for i, bar in enumerate(all_data[:max_bars]):
        # Convert to expected format
        bar_data = {
            'open': bar['open'],
            'high': bar['high'],
            'low': bar['low'],
            'close': bar['close'],
            'volume': bar['volume']
        }
        bars_processed.append(bar_data)
        
        # Need at least 50 bars for full analysis
        if len(bars_processed) < 50:
            print(f"[{i+1:3d}] Warming up... ({len(bars_processed)}/50 bars)")
            time.sleep(0.1)
            continue
        
        # Current time (simulated)
        sim_time = datetime.now().strftime("%H:%M:%S")
        
        print(f"\n{'='*80}")
        print(f"[{sim_time}] BAR {i+1} | Price: {bar['close']:.5f}")
        print(f"{'='*80}")
        
        # Run Ultimate Intelligence analysis
        try:
            analysis = ultimate.analyze(bars_processed)
            setup = analysis.trade_setup
            
            # Display results
            print(f"\nDIRECTION: {setup.direction}")
            print(f"Confidence: {setup.overall_confidence:.1%}")
            print(f"Signal Strength: {setup.signal_strength.value}")
            print(f"Confluence Score: {setup.confluence_score:.2f}")
            
            print(f"\nSIGNAL BREAKDOWN:")
            print(f"  Bullish: {setup.bullish_signals}")
            print(f"  Bearish: {setup.bearish_signals}")
            print(f"  Neutral: {setup.neutral_signals}")
            
            print(f"\nINDIVIDUAL SIGNALS:")
            for sig in setup.signals[:8]:  # Show top 8
                direction_icon = "+" if sig.direction == "LONG" else "-" if sig.direction == "SHORT" else "="
                print(f"  [{direction_icon}] {sig.source}: {sig.direction} ({sig.strength:.0%})")
            
            # Check for trade signal
            if setup.direction != "NO_TRADE" and setup.overall_confidence >= 0.5:
                print(f"\n*** TRADE SIGNAL: {setup.direction} ***")
                print(f"    Entry: {setup.entry_price:.5f}")
                print(f"    Stop Loss: {setup.stop_loss:.5f}")
                print(f"    Take Profit: {setup.take_profit_1:.5f}")
                trades.append({
                    'bar': i+1,
                    'direction': setup.direction,
                    'confidence': setup.overall_confidence,
                    'entry': setup.entry_price
                })
            
            # Show reasoning
            if setup.reasoning:
                print(f"\nREASONING:")
                for r in setup.reasoning[:5]:
                    print(f"  - {r}")
            
            # Show warnings
            if setup.warnings:
                print(f"\nWARNINGS:")
                for w in setup.warnings[:3]:
                    print(f"  ! {w}")
            
            signals_history.append({
                'bar': i+1,
                'price': bar['close'],
                'direction': setup.direction,
                'confidence': setup.overall_confidence,
                'bullish': setup.bullish_signals,
                'bearish': setup.bearish_signals
            })
            
        except Exception as e:
            print(f"Analysis error: {e}")
        
        # Delay to simulate real-time
        time.sleep(delay_seconds)
    
    # Summary
    print("\n" + "=" * 80)
    print("SIMULATION COMPLETE")
    print("=" * 80)
    print(f"\nBars Processed: {len(bars_processed)}")
    print(f"Trade Signals Generated: {len(trades)}")
    
    if trades:
        print("\nTRADE SIGNALS:")
        for t in trades:
            print(f"  Bar {t['bar']}: {t['direction']} @ {t['entry']:.5f} ({t['confidence']:.1%} conf)")
    
    # Signal distribution
    if signals_history:
        longs = sum(1 for s in signals_history if s['direction'] == 'LONG')
        shorts = sum(1 for s in signals_history if s['direction'] == 'SHORT')
        no_trade = sum(1 for s in signals_history if s['direction'] == 'NO_TRADE')
        print(f"\nSignal Distribution:")
        print(f"  LONG: {longs}")
        print(f"  SHORT: {shorts}")
        print(f"  NO_TRADE: {no_trade}")


if __name__ == "__main__":
    import sys
    
    delay = float(sys.argv[1]) if len(sys.argv) > 1 else 1.0
    max_bars = int(sys.argv[2]) if len(sys.argv) > 2 else 30
    
    run_live_simulation(delay_seconds=delay, max_bars=max_bars)
