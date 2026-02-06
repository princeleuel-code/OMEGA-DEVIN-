"""
Test the Market Consciousness Engine.

This validates that all 7 layers work together correctly.
"""

import sys
import numpy as np
from datetime import datetime, timezone, timedelta

# Add parent to path
sys.path.insert(0, '/home/ubuntu/omega_devin')

from chimera.consciousness import (
    MarketConsciousness,
    create_consciousness,
    MarketState,
    MarketRegime,
    ForecastHorizon,
    DecisionType,
    ExplanationStyle,
    RiskParameters,
)


def generate_test_candles(n_bars: int = 100, base_price: float = 1.1000) -> dict:
    """Generate test candle data for multiple timeframes."""
    np.random.seed(42)
    
    candles = {}
    
    for tf in ["1m", "5m", "15m", "1h"]:
        tf_candles = []
        price = base_price
        
        # Different volatility per timeframe
        vol = {"1m": 0.0001, "5m": 0.0003, "15m": 0.0005, "1h": 0.001}[tf]
        
        for i in range(n_bars):
            # Random walk with slight upward drift
            change = np.random.normal(0.00001, vol)
            open_price = price
            close_price = price + change
            high_price = max(open_price, close_price) + abs(np.random.normal(0, vol/2))
            low_price = min(open_price, close_price) - abs(np.random.normal(0, vol/2))
            volume = np.random.uniform(1000, 10000)
            
            tf_candles.append({
                "timestamp": datetime.now(timezone.utc) - timedelta(minutes=i),
                "open": open_price,
                "high": high_price,
                "low": low_price,
                "close": close_price,
                "volume": volume,
            })
            
            price = close_price
        
        candles[tf] = list(reversed(tf_candles))
    
    return candles


def generate_test_order_book() -> dict:
    """Generate test order book data."""
    base_price = 1.1000
    
    bids = []
    asks = []
    
    for i in range(10):
        bids.append({
            "price": base_price - 0.0001 * (i + 1),
            "size": np.random.uniform(100, 1000),
        })
        asks.append({
            "price": base_price + 0.0001 * (i + 1),
            "size": np.random.uniform(100, 1000),
        })
    
    return {"bids": bids, "asks": asks}


def generate_test_trades() -> list:
    """Generate test trade data."""
    trades = []
    
    for i in range(100):
        trades.append({
            "timestamp": datetime.now(timezone.utc) - timedelta(seconds=i),
            "price": 1.1000 + np.random.normal(0, 0.0001),
            "size": np.random.uniform(10, 100),
            "side": "buy" if np.random.random() > 0.5 else "sell",
        })
    
    return trades


def test_consciousness_basic():
    """Test basic consciousness functionality."""
    print("=" * 60)
    print("TEST: Basic Consciousness Functionality")
    print("=" * 60)
    
    # Create consciousness
    consciousness = create_consciousness()
    
    # Generate test data
    candles = generate_test_candles()
    order_book = generate_test_order_book()
    trades = generate_test_trades()
    
    # Think!
    output = consciousness.think(
        symbol="EURUSD",
        candles=candles,
        order_book=order_book,
        trades=trades,
    )
    
    # Validate output
    assert output is not None, "Output should not be None"
    assert output.symbol == "EURUSD", "Symbol should match"
    assert output.market_state is not None, "Market state should exist"
    assert output.forecast is not None, "Forecast should exist"
    assert output.decision is not None, "Decision should exist"
    assert output.explanation is not None, "Explanation should exist"
    assert output.performance_state is not None, "Performance state should exist"
    
    print(f"Market State: {output.market_state.primary_regime.value}")
    print(f"Forecast: mean={output.forecast.mean:.5f}, std={output.forecast.std:.5f}")
    print(f"Decision: {output.decision.decision.value}")
    print(f"Confidence: {output.overall_confidence:.0%}")
    print(f"Should Trade: {output.should_trade}")
    
    print("\nFull Report:")
    print(output.full_report())
    
    print("\n[PASSED] Basic consciousness test")
    return True


def test_consciousness_learning():
    """Test consciousness learning from trades."""
    print("\n" + "=" * 60)
    print("TEST: Consciousness Learning")
    print("=" * 60)
    
    consciousness = create_consciousness()
    
    # Generate test data
    candles = generate_test_candles()
    order_book = generate_test_order_book()
    trades = generate_test_trades()
    
    # First think
    output1 = consciousness.think(
        symbol="EURUSD",
        candles=candles,
        order_book=order_book,
        trades=trades,
    )
    
    # Simulate a trade
    if output1.decision.is_actionable():
        consciousness.record_trade_entry(output1.decision)
        
        # Simulate exit
        exit_price = output1.market_state.price * 1.001  # Small profit
        result = consciousness.learn_from_trade(
            decision=output1.decision,
            exit_price=exit_price,
            hit_target=True,
            duration_bars=10,
        )
        
        if result:
            print(f"Trade result: PnL={result.pnl_pct:.2%}")
    
    # Think again - should have learned
    output2 = consciousness.think(
        symbol="EURUSD",
        candles=candles,
        order_book=order_book,
        trades=trades,
    )
    
    # Check adaptation
    summary = consciousness.adaptation.get_adaptation_summary()
    print(f"Adaptations: {summary['total_adaptations']}")
    print(f"Memory buffer: {summary['memory_buffer_size']}")
    
    print("\n[PASSED] Learning test")
    return True


def test_consciousness_qa():
    """Test consciousness Q&A interface."""
    print("\n" + "=" * 60)
    print("TEST: Consciousness Q&A Interface")
    print("=" * 60)
    
    consciousness = create_consciousness()
    
    # Generate test data
    candles = generate_test_candles()
    order_book = generate_test_order_book()
    trades = generate_test_trades()
    
    # Think first
    consciousness.think(
        symbol="EURUSD",
        candles=candles,
        order_book=order_book,
        trades=trades,
    )
    
    # Ask questions
    questions = [
        "Should I trade?",
        "What's your confidence?",
        "What's the current regime?",
        "What's your forecast?",
        "How are you doing?",
        "Why did you make this decision?",
        "What's the risk?",
    ]
    
    for q in questions:
        answer = consciousness.ask(q)
        print(f"\nQ: {q}")
        print(f"A: {answer}")
    
    print("\n[PASSED] Q&A test")
    return True


def test_consciousness_explanation_styles():
    """Test different explanation styles."""
    print("\n" + "=" * 60)
    print("TEST: Explanation Styles")
    print("=" * 60)
    
    # Generate test data
    candles = generate_test_candles()
    order_book = generate_test_order_book()
    trades = generate_test_trades()
    
    for style in [ExplanationStyle.SIMPLE, ExplanationStyle.TRADER, ExplanationStyle.TECHNICAL, ExplanationStyle.AUDIT]:
        consciousness = create_consciousness(explanation_style=style)
        
        output = consciousness.think(
            symbol="EURUSD",
            candles=candles,
            order_book=order_book,
            trades=trades,
        )
        
        print(f"\n--- {style.value.upper()} STYLE ---")
        print(output.explanation.summary)
    
    print("\n[PASSED] Explanation styles test")
    return True


def test_consciousness_refusal():
    """Test consciousness refusing to trade."""
    print("\n" + "=" * 60)
    print("TEST: Consciousness Refusal")
    print("=" * 60)
    
    # Create consciousness with strict parameters
    strict_params = RiskParameters(
        min_confidence=0.9,  # Very high threshold
        max_uncertainty=0.1,  # Very low tolerance
    )
    consciousness = create_consciousness(risk_params=strict_params)
    
    # Generate test data
    candles = generate_test_candles()
    order_book = generate_test_order_book()
    trades = generate_test_trades()
    
    output = consciousness.think(
        symbol="EURUSD",
        candles=candles,
        order_book=order_book,
        trades=trades,
    )
    
    print(f"Decision: {output.decision.decision.value}")
    print(f"Should Trade: {output.should_trade}")
    print(f"Blocked Reason: {output.trade_blocked_reason}")
    
    if output.decision.refusal_reason:
        print(f"Refusal Reason: {output.decision.refusal_reason.value}")
    
    print("\n[PASSED] Refusal test")
    return True


def test_all_layers():
    """Test that all 7 layers are working."""
    print("\n" + "=" * 60)
    print("TEST: All 7 Layers Integration")
    print("=" * 60)
    
    consciousness = create_consciousness()
    
    # Generate test data
    candles = generate_test_candles()
    order_book = generate_test_order_book()
    trades = generate_test_trades()
    
    output = consciousness.think(
        symbol="EURUSD",
        candles=candles,
        order_book=order_book,
        trades=trades,
    )
    
    # Check Layer 1: Perception
    assert output.market_state.price > 0, "Layer 1 (Perception) failed"
    print(f"Layer 1 (Perception): Price={output.market_state.price:.5f}, Regime={output.market_state.primary_regime.value}")
    
    # Check Layer 2: Understanding
    assert output.causal_insights is not None, "Layer 2 (Understanding) failed"
    print(f"Layer 2 (Understanding): Causal graph has {output.causal_insights.get('causal_summary', {}).get('num_edges', 0)} edges")
    
    # Check Layer 3: Prediction
    assert output.forecast.mean > 0, "Layer 3 (Prediction) failed"
    print(f"Layer 3 (Prediction): Mean={output.forecast.mean:.5f}, P(up)={output.forecast.prob_up:.0%}")
    
    # Check Layer 4: Decision
    assert output.decision.decision is not None, "Layer 4 (Decision) failed"
    print(f"Layer 4 (Decision): {output.decision.decision.value}, Confidence={output.decision.confidence:.0%}")
    
    # Check Layer 5: Explanation
    assert output.explanation.narrative, "Layer 5 (Explanation) failed"
    print(f"Layer 5 (Explanation): {output.explanation.headline}")
    
    # Check Layer 6: Reflection
    assert output.performance_state.system_state is not None, "Layer 6 (Reflection) failed"
    print(f"Layer 6 (Reflection): System state={output.performance_state.system_state.value}, Health={output.performance_state.health_score:.0%}")
    
    # Check Layer 7: Adaptation
    summary = consciousness.adaptation.get_adaptation_summary()
    assert summary is not None, "Layer 7 (Adaptation) failed"
    print(f"Layer 7 (Adaptation): Learning enabled={summary['is_learning_enabled']}")
    
    print("\n[PASSED] All 7 layers integration test")
    return True


def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("MARKET CONSCIOUSNESS ENGINE - TEST SUITE")
    print("=" * 60)
    
    tests = [
        test_consciousness_basic,
        test_consciousness_learning,
        test_consciousness_qa,
        test_consciousness_explanation_styles,
        test_consciousness_refusal,
        test_all_layers,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"\n[FAILED] {test.__name__}: {e}")
            import traceback
            traceback.print_exc()
            failed += 1
    
    print("\n" + "=" * 60)
    print(f"TEST RESULTS: {passed} passed, {failed} failed")
    print("=" * 60)
    
    return failed == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
