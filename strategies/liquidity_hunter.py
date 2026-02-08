# OMEGA-DEVIN // STRATEGY MODULE: LIQUIDITY HUNTER
# The "Turtle Soup" Strategy - Hunt liquidity sweeps

from typing import Dict, List, Any, Optional
from datetime import datetime

class LiquidityHunter:
    """
    LIQUIDITY HUNTER STRATEGY
    
    This strategy hunts for liquidity sweeps - when price takes out
    swing highs/lows and reverses. This is a key institutional trading concept.
    
    The "Turtle Soup" Logic:
    - Look for price breaking recent highs/lows
    - Wait for rejection (close back inside the range)
    - Enter in the opposite direction
    
    This is how institutions trap retail traders.
    """
    
    def __init__(self, lookback: int = 20, min_sweep_pips: float = 5):
        self.lookback = lookback
        self.min_sweep_pips = min_sweep_pips
        self.signals = []
        
    def analyze(self, bars: List[Dict]) -> Dict[str, Any]:
        """
        Analyze price data for liquidity sweep opportunities
        
        Args:
            bars: List of OHLCV dictionaries
            
        Returns:
            Analysis result with signal and details
        """
        if not bars or len(bars) < self.lookback + 5:
            return self._no_signal("Insufficient data")
        
        # Get recent bars for analysis
        recent_bars = bars[-(self.lookback + 5):]
        lookback_bars = recent_bars[:self.lookback]
        current_bars = recent_bars[self.lookback:]
        
        # Find swing highs and lows in lookback period
        recent_high = max(b['high'] for b in lookback_bars)
        recent_low = min(b['low'] for b in lookback_bars)
        
        # Check last few bars for sweeps
        for i, bar in enumerate(current_bars):
            # HIGH SWEEP: Price breaks above recent high then closes below
            sweep_high = bar['high'] > recent_high
            close_below = bar['close'] < recent_high
            
            if sweep_high and close_below:
                sweep_distance = (bar['high'] - recent_high) * 10000  # pips for forex
                
                if sweep_distance >= self.min_sweep_pips:
                    return {
                        "signal": "SHORT",
                        "type": "LIQUIDITY_SWEEP_HIGH",
                        "confidence": min(0.85, 0.6 + (sweep_distance / 20)),
                        "entry": bar['close'],
                        "stop_loss": bar['high'] + (bar['high'] - bar['close']) * 0.5,
                        "take_profit": bar['close'] - (bar['high'] - bar['close']) * 2,
                        "sweep_level": recent_high,
                        "sweep_distance_pips": sweep_distance,
                        "reason": f"Liquidity sweep above {recent_high:.5f}, rejected with {sweep_distance:.1f} pip sweep",
                        "timestamp": datetime.now().isoformat()
                    }
            
            # LOW SWEEP: Price breaks below recent low then closes above
            sweep_low = bar['low'] < recent_low
            close_above = bar['close'] > recent_low
            
            if sweep_low and close_above:
                sweep_distance = (recent_low - bar['low']) * 10000  # pips for forex
                
                if sweep_distance >= self.min_sweep_pips:
                    return {
                        "signal": "LONG",
                        "type": "LIQUIDITY_SWEEP_LOW",
                        "confidence": min(0.85, 0.6 + (sweep_distance / 20)),
                        "entry": bar['close'],
                        "stop_loss": bar['low'] - (bar['close'] - bar['low']) * 0.5,
                        "take_profit": bar['close'] + (bar['close'] - bar['low']) * 2,
                        "sweep_level": recent_low,
                        "sweep_distance_pips": sweep_distance,
                        "reason": f"Liquidity sweep below {recent_low:.5f}, rejected with {sweep_distance:.1f} pip sweep",
                        "timestamp": datetime.now().isoformat()
                    }
        
        return self._no_signal("No liquidity sweep detected")
    
    def _no_signal(self, reason: str) -> Dict[str, Any]:
        """Return no signal result"""
        return {
            "signal": "WAIT",
            "type": "NO_SWEEP",
            "confidence": 0,
            "reason": reason,
            "timestamp": datetime.now().isoformat()
        }
    
    def detect_sweep(self, bars: List[Dict]) -> str:
        """
        Simple sweep detection for compatibility
        
        Returns:
            "SHORT_SIGNAL_DETECTED", "LONG_SIGNAL_DETECTED", or "WAITING_FOR_LIQUIDITY"
        """
        result = self.analyze(bars)
        
        if result["signal"] == "SHORT":
            return "SHORT_SIGNAL_DETECTED"
        elif result["signal"] == "LONG":
            return "LONG_SIGNAL_DETECTED"
        else:
            return "WAITING_FOR_LIQUIDITY"
    
    def find_liquidity_zones(self, bars: List[Dict]) -> Dict[str, Any]:
        """
        Find potential liquidity zones (where stops are likely placed)
        
        Returns:
            Dictionary with liquidity zones above and below current price
        """
        if not bars or len(bars) < 50:
            return {"above": [], "below": []}
        
        # Find swing highs and lows
        swing_highs = []
        swing_lows = []
        
        for i in range(2, len(bars) - 2):
            # Swing high
            if (bars[i]['high'] > bars[i-1]['high'] and 
                bars[i]['high'] > bars[i-2]['high'] and
                bars[i]['high'] > bars[i+1]['high'] and 
                bars[i]['high'] > bars[i+2]['high']):
                swing_highs.append({
                    "price": bars[i]['high'],
                    "index": i,
                    "timestamp": bars[i].get('timestamp', '')
                })
            
            # Swing low
            if (bars[i]['low'] < bars[i-1]['low'] and 
                bars[i]['low'] < bars[i-2]['low'] and
                bars[i]['low'] < bars[i+1]['low'] and 
                bars[i]['low'] < bars[i+2]['low']):
                swing_lows.append({
                    "price": bars[i]['low'],
                    "index": i,
                    "timestamp": bars[i].get('timestamp', '')
                })
        
        current_price = bars[-1]['close']
        
        # Liquidity above = swing highs above current price (buy stops)
        liquidity_above = [sh for sh in swing_highs if sh['price'] > current_price]
        liquidity_above.sort(key=lambda x: x['price'])
        
        # Liquidity below = swing lows below current price (sell stops)
        liquidity_below = [sl for sl in swing_lows if sl['price'] < current_price]
        liquidity_below.sort(key=lambda x: x['price'], reverse=True)
        
        return {
            "above": liquidity_above[:5],  # Top 5 levels above
            "below": liquidity_below[:5],  # Top 5 levels below
            "current_price": current_price,
            "nearest_above": liquidity_above[0] if liquidity_above else None,
            "nearest_below": liquidity_below[0] if liquidity_below else None
        }


# Test the strategy
if __name__ == "__main__":
    import random
    
    # Generate test data with a liquidity sweep
    bars = []
    price = 1.0850
    
    # Build up to a high
    for i in range(20):
        change = random.uniform(-0.0005, 0.001)  # Slight upward bias
        open_price = price
        close_price = price + change
        high_price = max(open_price, close_price) + random.uniform(0, 0.0003)
        low_price = min(open_price, close_price) - random.uniform(0, 0.0003)
        
        bars.append({
            "timestamp": f"2026-01-28 {i:02d}:00",
            "open": open_price,
            "high": high_price,
            "low": low_price,
            "close": close_price,
            "volume": random.randint(1000, 5000)
        })
        price = close_price
    
    # Create a liquidity sweep (break high then close below)
    recent_high = max(b['high'] for b in bars[-20:])
    sweep_bar = {
        "timestamp": "2026-01-28 20:00",
        "open": price,
        "high": recent_high + 0.0015,  # Break above
        "low": price - 0.0005,
        "close": recent_high - 0.0005,  # Close below
        "volume": 5000
    }
    bars.append(sweep_bar)
    
    # Test the strategy
    hunter = LiquidityHunter()
    result = hunter.analyze(bars)
    
    print("\n=== LIQUIDITY HUNTER TEST ===")
    print(f"Signal: {result['signal']}")
    print(f"Type: {result['type']}")
    print(f"Confidence: {result.get('confidence', 0):.2%}")
    print(f"Reason: {result['reason']}")
    
    if result['signal'] != 'WAIT':
        print(f"\nTrade Setup:")
        print(f"  Entry: {result['entry']:.5f}")
        print(f"  Stop Loss: {result['stop_loss']:.5f}")
        print(f"  Take Profit: {result['take_profit']:.5f}")
    
    # Test liquidity zones
    zones = hunter.find_liquidity_zones(bars)
    print(f"\nLiquidity Zones:")
    print(f"  Above: {len(zones['above'])} levels")
    print(f"  Below: {len(zones['below'])} levels")
