# OMEGA-DEVIN // STRATEGY MODULE: SMC (Smart Money Concepts)
# Institutional trading concepts - BOS, CHoCH, Order Blocks, FVG

from typing import Dict, List, Any, Optional
from datetime import datetime

class SMCStrategy:
    """
    SMART MONEY CONCEPTS STRATEGY
    
    Implements institutional trading concepts:
    1. BOS (Break of Structure) - Trend continuation
    2. CHoCH (Change of Character) - Trend reversal
    3. Order Blocks - Institutional entry zones
    4. FVG (Fair Value Gaps) - Imbalance zones
    5. Liquidity Pools - Where stops are placed
    """
    
    def __init__(self):
        self.swing_lookback = 5
        self.order_block_lookback = 20
        
    def analyze(self, bars: List[Dict]) -> Dict[str, Any]:
        """
        Full SMC analysis
        
        Returns:
            Complete SMC analysis with structure, order blocks, and signals
        """
        if not bars or len(bars) < 30:
            return {"signal": "WAIT", "reason": "Insufficient data"}
        
        # Analyze market structure
        structure = self._analyze_structure(bars)
        
        # Find order blocks
        order_blocks = self._find_order_blocks(bars)
        
        # Find FVGs
        fvgs = self._find_fvgs(bars)
        
        # Detect BOS/CHoCH
        structure_break = self._detect_structure_break(bars)
        
        # Generate signal
        signal = self._generate_signal(bars, structure, order_blocks, fvgs, structure_break)
        
        return {
            "signal": signal["direction"],
            "confidence": signal["confidence"],
            "structure": structure,
            "order_blocks": order_blocks,
            "fvgs": fvgs,
            "structure_break": structure_break,
            "reason": signal["reason"],
            "timestamp": datetime.now().isoformat()
        }
    
    def _analyze_structure(self, bars: List[Dict]) -> Dict[str, Any]:
        """Analyze market structure (swing highs/lows)"""
        swing_highs = []
        swing_lows = []
        
        for i in range(self.swing_lookback, len(bars) - self.swing_lookback):
            # Check for swing high
            is_swing_high = True
            for j in range(1, self.swing_lookback + 1):
                if bars[i]['high'] <= bars[i-j]['high'] or bars[i]['high'] <= bars[i+j]['high']:
                    is_swing_high = False
                    break
            
            if is_swing_high:
                swing_highs.append({
                    "price": bars[i]['high'],
                    "index": i,
                    "timestamp": bars[i].get('timestamp', '')
                })
            
            # Check for swing low
            is_swing_low = True
            for j in range(1, self.swing_lookback + 1):
                if bars[i]['low'] >= bars[i-j]['low'] or bars[i]['low'] >= bars[i+j]['low']:
                    is_swing_low = False
                    break
            
            if is_swing_low:
                swing_lows.append({
                    "price": bars[i]['low'],
                    "index": i,
                    "timestamp": bars[i].get('timestamp', '')
                })
        
        # Determine trend
        trend = "RANGING"
        if len(swing_highs) >= 2 and len(swing_lows) >= 2:
            if swing_highs[-1]['price'] > swing_highs[-2]['price'] and swing_lows[-1]['price'] > swing_lows[-2]['price']:
                trend = "BULLISH"
            elif swing_highs[-1]['price'] < swing_highs[-2]['price'] and swing_lows[-1]['price'] < swing_lows[-2]['price']:
                trend = "BEARISH"
        
        return {
            "trend": trend,
            "swing_highs": swing_highs[-5:],
            "swing_lows": swing_lows[-5:],
            "last_high": swing_highs[-1] if swing_highs else None,
            "last_low": swing_lows[-1] if swing_lows else None
        }
    
    def _find_order_blocks(self, bars: List[Dict]) -> List[Dict]:
        """Find order blocks (last opposite candle before a strong move)"""
        order_blocks = []
        
        for i in range(2, len(bars) - 1):
            # Bullish Order Block: Last bearish candle before strong bullish move
            if bars[i-1]['close'] < bars[i-1]['open']:  # Bearish candle
                # Check for strong bullish move after
                if bars[i]['close'] > bars[i]['open']:  # Bullish candle
                    move_size = bars[i]['close'] - bars[i]['open']
                    prev_range = bars[i-1]['high'] - bars[i-1]['low']
                    
                    if move_size > prev_range * 1.5:  # Strong move
                        order_blocks.append({
                            "type": "BULLISH_OB",
                            "high": bars[i-1]['high'],
                            "low": bars[i-1]['low'],
                            "index": i-1,
                            "timestamp": bars[i-1].get('timestamp', ''),
                            "strength": move_size / prev_range if prev_range > 0 else 1
                        })
            
            # Bearish Order Block: Last bullish candle before strong bearish move
            if bars[i-1]['close'] > bars[i-1]['open']:  # Bullish candle
                # Check for strong bearish move after
                if bars[i]['close'] < bars[i]['open']:  # Bearish candle
                    move_size = bars[i]['open'] - bars[i]['close']
                    prev_range = bars[i-1]['high'] - bars[i-1]['low']
                    
                    if move_size > prev_range * 1.5:  # Strong move
                        order_blocks.append({
                            "type": "BEARISH_OB",
                            "high": bars[i-1]['high'],
                            "low": bars[i-1]['low'],
                            "index": i-1,
                            "timestamp": bars[i-1].get('timestamp', ''),
                            "strength": move_size / prev_range if prev_range > 0 else 1
                        })
        
        return order_blocks[-10:]  # Return last 10 order blocks
    
    def _find_fvgs(self, bars: List[Dict]) -> List[Dict]:
        """Find Fair Value Gaps (imbalance zones)"""
        fvgs = []
        
        for i in range(2, len(bars)):
            # Bullish FVG: Gap between bar[i-2] high and bar[i] low
            if bars[i]['low'] > bars[i-2]['high']:
                fvgs.append({
                    "type": "BULLISH_FVG",
                    "high": bars[i]['low'],
                    "low": bars[i-2]['high'],
                    "index": i-1,
                    "timestamp": bars[i-1].get('timestamp', ''),
                    "size": bars[i]['low'] - bars[i-2]['high']
                })
            
            # Bearish FVG: Gap between bar[i-2] low and bar[i] high
            if bars[i]['high'] < bars[i-2]['low']:
                fvgs.append({
                    "type": "BEARISH_FVG",
                    "high": bars[i-2]['low'],
                    "low": bars[i]['high'],
                    "index": i-1,
                    "timestamp": bars[i-1].get('timestamp', ''),
                    "size": bars[i-2]['low'] - bars[i]['high']
                })
        
        return fvgs[-10:]  # Return last 10 FVGs
    
    def _detect_structure_break(self, bars: List[Dict]) -> Dict[str, Any]:
        """Detect BOS (Break of Structure) or CHoCH (Change of Character)"""
        structure = self._analyze_structure(bars[:-5])  # Analyze without last 5 bars
        
        if not structure['last_high'] or not structure['last_low']:
            return {"type": None, "direction": None}
        
        last_high = structure['last_high']['price']
        last_low = structure['last_low']['price']
        current_price = bars[-1]['close']
        
        # Check for BOS (continuation)
        if structure['trend'] == "BULLISH":
            if current_price > last_high:
                return {
                    "type": "BOS",
                    "direction": "BULLISH",
                    "level": last_high,
                    "reason": f"Break of Structure above {last_high:.5f} - bullish continuation"
                }
        elif structure['trend'] == "BEARISH":
            if current_price < last_low:
                return {
                    "type": "BOS",
                    "direction": "BEARISH",
                    "level": last_low,
                    "reason": f"Break of Structure below {last_low:.5f} - bearish continuation"
                }
        
        # Check for CHoCH (reversal)
        if structure['trend'] == "BULLISH":
            if current_price < last_low:
                return {
                    "type": "CHoCH",
                    "direction": "BEARISH",
                    "level": last_low,
                    "reason": f"Change of Character below {last_low:.5f} - potential reversal to bearish"
                }
        elif structure['trend'] == "BEARISH":
            if current_price > last_high:
                return {
                    "type": "CHoCH",
                    "direction": "BULLISH",
                    "level": last_high,
                    "reason": f"Change of Character above {last_high:.5f} - potential reversal to bullish"
                }
        
        return {"type": None, "direction": None}
    
    def _generate_signal(self, bars: List[Dict], structure: Dict, order_blocks: List[Dict], 
                         fvgs: List[Dict], structure_break: Dict) -> Dict[str, Any]:
        """Generate trading signal based on SMC analysis"""
        current_price = bars[-1]['close']
        
        # Priority 1: Structure break signals
        if structure_break.get('type'):
            direction = "LONG" if structure_break['direction'] == "BULLISH" else "SHORT"
            confidence = 0.75 if structure_break['type'] == "BOS" else 0.65
            return {
                "direction": direction,
                "confidence": confidence,
                "reason": structure_break['reason']
            }
        
        # Priority 2: Price at order block
        for ob in reversed(order_blocks):
            if ob['low'] <= current_price <= ob['high']:
                if ob['type'] == "BULLISH_OB":
                    return {
                        "direction": "LONG",
                        "confidence": 0.70,
                        "reason": f"Price at bullish order block ({ob['low']:.5f} - {ob['high']:.5f})"
                    }
                else:
                    return {
                        "direction": "SHORT",
                        "confidence": 0.70,
                        "reason": f"Price at bearish order block ({ob['low']:.5f} - {ob['high']:.5f})"
                    }
        
        # Priority 3: Price filling FVG
        for fvg in reversed(fvgs):
            if fvg['low'] <= current_price <= fvg['high']:
                if fvg['type'] == "BULLISH_FVG":
                    return {
                        "direction": "LONG",
                        "confidence": 0.60,
                        "reason": f"Price filling bullish FVG ({fvg['low']:.5f} - {fvg['high']:.5f})"
                    }
                else:
                    return {
                        "direction": "SHORT",
                        "confidence": 0.60,
                        "reason": f"Price filling bearish FVG ({fvg['low']:.5f} - {fvg['high']:.5f})"
                    }
        
        # No clear signal
        return {
            "direction": "WAIT",
            "confidence": 0,
            "reason": f"No SMC setup - trend is {structure['trend']}"
        }


# Test
if __name__ == "__main__":
    import random
    
    # Generate test data
    bars = []
    price = 1.0850
    
    for i in range(50):
        change = random.uniform(-0.001, 0.001)
        open_price = price
        close_price = price + change
        high_price = max(open_price, close_price) + random.uniform(0, 0.0005)
        low_price = min(open_price, close_price) - random.uniform(0, 0.0005)
        
        bars.append({
            "timestamp": f"2026-01-28 {i:02d}:00",
            "open": open_price,
            "high": high_price,
            "low": low_price,
            "close": close_price,
            "volume": random.randint(1000, 5000)
        })
        price = close_price
    
    strategy = SMCStrategy()
    result = strategy.analyze(bars)
    
    print("\n=== SMC STRATEGY TEST ===")
    print(f"Signal: {result['signal']}")
    print(f"Confidence: {result['confidence']:.2%}")
    print(f"Structure: {result['structure']['trend']}")
    print(f"Order Blocks: {len(result['order_blocks'])}")
    print(f"FVGs: {len(result['fvgs'])}")
    print(f"Reason: {result['reason']}")
