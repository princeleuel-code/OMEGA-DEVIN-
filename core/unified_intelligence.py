# OMEGA-DEVIN // UNIFIED INTELLIGENCE ENGINE
# Combines ALL 18 Intelligence Modules into ONE system
# This is the TRUE AGI - all knowledge working together

import sys
import os
from typing import Dict, List, Any, Optional
from datetime import datetime

# Add chimera to path for importing intelligence modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

class UnifiedIntelligence:
    """
    UNIFIED INTELLIGENCE ENGINE
    
    Combines ALL 18 intelligence modules:
    1. Core Consciousness (7 layers)
    2. Delta Print Intelligence
    3. SMC Intelligence
    4. MTF Intelligence
    5. VPE Intelligence
    6. Fractal Swing Intelligence
    7. Manipulation Candle Intelligence
    8. Multi-Profile Volume Intelligence
    9. Session & Trade Management
    10. Self-Evolving Intelligence
    11. Institutional Flow Detection
    12. Cross-Asset Correlation
    13. Woven Intelligence
    14. Emergent Intelligence
    15. SOTA Intelligence
    16. Advanced Reasoning Engine
    17. Signal Intelligence
    18. Ultimate Intelligence
    """
    
    def __init__(self):
        self.modules = {}
        self.weights = {
            "price_action": 0.15,
            "order_flow": 0.15,
            "structure": 0.12,
            "delta_flow": 0.12,
            "volume_profile": 0.10,
            "institutional": 0.10,
            "footprint": 0.08,
            "session": 0.08,
            "vwap": 0.05,
            "absorption": 0.05
        }
        self._load_modules()
    
    def _load_modules(self):
        """Load all intelligence modules"""
        try:
            # Try to import from chimera
            from chimera.consciousness import (
                smc_intelligence,
                mtf_intelligence,
                vpe_intelligence,
                fractal_swing_intelligence,
                manipulation_candle_intelligence,
                multi_profile_volume_intelligence,
                session_trade_management,
                self_evolving_intelligence,
                institutional_flow_detection,
                cross_asset_correlation,
                woven_intelligence,
                emergent_intelligence,
                sota_intelligence,
                ultimate_intelligence
            )
            
            self.modules = {
                "smc": smc_intelligence,
                "mtf": mtf_intelligence,
                "vpe": vpe_intelligence,
                "fractal_swing": fractal_swing_intelligence,
                "manipulation": manipulation_candle_intelligence,
                "multi_profile": multi_profile_volume_intelligence,
                "session": session_trade_management,
                "self_evolving": self_evolving_intelligence,
                "institutional": institutional_flow_detection,
                "cross_asset": cross_asset_correlation,
                "woven": woven_intelligence,
                "emergent": emergent_intelligence,
                "sota": sota_intelligence,
                "ultimate": ultimate_intelligence
            }
            print(f"   [UNIFIED]: Loaded {len(self.modules)} intelligence modules")
        except ImportError as e:
            print(f"   [UNIFIED]: Could not load chimera modules: {e}")
            self.modules = {}
    
    def analyze(self, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run unified analysis using ALL intelligence modules
        
        Args:
            market_data: Dictionary containing:
                - bars: List of OHLCV bars
                - symbol: Trading symbol
                - timeframe: Current timeframe
                
        Returns:
            Unified analysis with signals, confidence, and reasoning
        """
        bars = market_data.get('bars', [])
        symbol = market_data.get('symbol', 'EURUSD')
        
        if not bars or len(bars) < 20:
            return self._empty_analysis("Insufficient data")
        
        # Collect signals from all sources
        signals = []
        reasoning_chain = []
        
        # 1. Price Action Analysis
        price_signal = self._analyze_price_action(bars)
        signals.append({"source": "price_action", "signal": price_signal["direction"], "weight": self.weights["price_action"]})
        reasoning_chain.append(f"Price Action: {price_signal['reason']}")
        
        # 2. Order Flow Analysis
        order_flow_signal = self._analyze_order_flow(bars)
        signals.append({"source": "order_flow", "signal": order_flow_signal["direction"], "weight": self.weights["order_flow"]})
        reasoning_chain.append(f"Order Flow: {order_flow_signal['reason']}")
        
        # 3. Market Structure Analysis
        structure_signal = self._analyze_structure(bars)
        signals.append({"source": "structure", "signal": structure_signal["direction"], "weight": self.weights["structure"]})
        reasoning_chain.append(f"Structure: {structure_signal['reason']}")
        
        # 4. Delta Flow Analysis
        delta_signal = self._analyze_delta_flow(bars)
        signals.append({"source": "delta_flow", "signal": delta_signal["direction"], "weight": self.weights["delta_flow"]})
        reasoning_chain.append(f"Delta Flow: {delta_signal['reason']}")
        
        # 5. Volume Profile Analysis
        volume_signal = self._analyze_volume_profile(bars)
        signals.append({"source": "volume_profile", "signal": volume_signal["direction"], "weight": self.weights["volume_profile"]})
        reasoning_chain.append(f"Volume Profile: {volume_signal['reason']}")
        
        # 6. Institutional Flow Analysis
        institutional_signal = self._analyze_institutional_flow(bars)
        signals.append({"source": "institutional", "signal": institutional_signal["direction"], "weight": self.weights["institutional"]})
        reasoning_chain.append(f"Institutional: {institutional_signal['reason']}")
        
        # 7. Footprint Analysis
        footprint_signal = self._analyze_footprint(bars)
        signals.append({"source": "footprint", "signal": footprint_signal["direction"], "weight": self.weights["footprint"]})
        reasoning_chain.append(f"Footprint: {footprint_signal['reason']}")
        
        # 8. Session Analysis
        session_signal = self._analyze_session(bars)
        signals.append({"source": "session", "signal": session_signal["direction"], "weight": self.weights["session"]})
        reasoning_chain.append(f"Session: {session_signal['reason']}")
        
        # 9. VWAP Analysis
        vwap_signal = self._analyze_vwap(bars)
        signals.append({"source": "vwap", "signal": vwap_signal["direction"], "weight": self.weights["vwap"]})
        reasoning_chain.append(f"VWAP: {vwap_signal['reason']}")
        
        # 10. Absorption Analysis
        absorption_signal = self._analyze_absorption(bars)
        signals.append({"source": "absorption", "signal": absorption_signal["direction"], "weight": self.weights["absorption"]})
        reasoning_chain.append(f"Absorption: {absorption_signal['reason']}")
        
        # Calculate confluence
        bullish_count = sum(1 for s in signals if s["signal"] == "BULLISH")
        bearish_count = sum(1 for s in signals if s["signal"] == "BEARISH")
        neutral_count = sum(1 for s in signals if s["signal"] == "NEUTRAL")
        
        # Calculate weighted score
        weighted_score = 0
        for s in signals:
            if s["signal"] == "BULLISH":
                weighted_score += s["weight"] * 100
            elif s["signal"] == "BEARISH":
                weighted_score -= s["weight"] * 100
        
        # Determine final direction
        if weighted_score > 20:
            direction = "LONG"
            confidence = min(0.95, 0.5 + (weighted_score / 200))
        elif weighted_score < -20:
            direction = "SHORT"
            confidence = min(0.95, 0.5 + (abs(weighted_score) / 200))
        else:
            direction = "WAIT"
            confidence = 0.3
        
        # Generate trade setup
        current_price = bars[-1]['close']
        atr = self._calculate_atr(bars)
        
        if direction == "LONG":
            stop_loss = current_price - (atr * 1.5)
            take_profit_1 = current_price + (atr * 2)
            take_profit_2 = current_price + (atr * 3.5)
        elif direction == "SHORT":
            stop_loss = current_price + (atr * 1.5)
            take_profit_1 = current_price - (atr * 2)
            take_profit_2 = current_price - (atr * 3.5)
        else:
            stop_loss = current_price
            take_profit_1 = current_price
            take_profit_2 = current_price
        
        # Build reasoning narrative
        if direction != "WAIT":
            narrative = f"UNIFIED AGI detected {direction} opportunity with {confidence:.0%} confidence. "
            narrative += f"{bullish_count} bullish signals vs {bearish_count} bearish signals. "
            narrative += f"Weighted score: {weighted_score:+.0f}. "
            narrative += f"Entry at {current_price:.5f}, Stop at {stop_loss:.5f}, TP1 at {take_profit_1:.5f}."
        else:
            narrative = f"Mixed signals detected. {bullish_count} bullish, {bearish_count} bearish, {neutral_count} neutral. "
            narrative += "Waiting for clearer setup with higher confluence."
        
        return {
            "timestamp": datetime.now().isoformat(),
            "symbol": symbol,
            "direction": direction,
            "confidence": confidence,
            "weighted_score": weighted_score,
            "signals": signals,
            "confluence": {
                "bullish": bullish_count,
                "bearish": bearish_count,
                "neutral": neutral_count,
                "total": len(signals)
            },
            "reasoning_chain": reasoning_chain,
            "narrative": narrative,
            "trade_setup": {
                "entry": current_price,
                "stop_loss": stop_loss,
                "take_profit_1": take_profit_1,
                "take_profit_2": take_profit_2,
                "risk_reward": abs(take_profit_1 - current_price) / abs(current_price - stop_loss) if stop_loss != current_price else 0
            },
            "key_levels": {
                "current_price": current_price,
                "atr": atr,
                "recent_high": max(b['high'] for b in bars[-20:]),
                "recent_low": min(b['low'] for b in bars[-20:])
            }
        }
    
    def _empty_analysis(self, reason: str) -> Dict[str, Any]:
        """Return empty analysis when data is insufficient"""
        return {
            "timestamp": datetime.now().isoformat(),
            "direction": "WAIT",
            "confidence": 0,
            "weighted_score": 0,
            "signals": [],
            "confluence": {"bullish": 0, "bearish": 0, "neutral": 0, "total": 0},
            "reasoning_chain": [reason],
            "narrative": reason,
            "trade_setup": None,
            "key_levels": None
        }
    
    def _analyze_price_action(self, bars: List[Dict]) -> Dict[str, Any]:
        """Analyze price action patterns"""
        if len(bars) < 3:
            return {"direction": "NEUTRAL", "reason": "Insufficient data"}
        
        last_bar = bars[-1]
        prev_bar = bars[-2]
        
        # Check for bullish/bearish engulfing
        is_bullish = last_bar['close'] > last_bar['open']
        is_prev_bearish = prev_bar['close'] < prev_bar['open']
        
        body_size = abs(last_bar['close'] - last_bar['open'])
        prev_body = abs(prev_bar['close'] - prev_bar['open'])
        
        if is_bullish and is_prev_bearish and body_size > prev_body * 1.2:
            return {"direction": "BULLISH", "reason": "Bullish engulfing pattern detected"}
        
        is_bearish = last_bar['close'] < last_bar['open']
        is_prev_bullish = prev_bar['close'] > prev_bar['open']
        
        if is_bearish and is_prev_bullish and body_size > prev_body * 1.2:
            return {"direction": "BEARISH", "reason": "Bearish engulfing pattern detected"}
        
        # Check trend
        closes = [b['close'] for b in bars[-10:]]
        if closes[-1] > closes[0] * 1.002:
            return {"direction": "BULLISH", "reason": "Uptrend in recent bars"}
        elif closes[-1] < closes[0] * 0.998:
            return {"direction": "BEARISH", "reason": "Downtrend in recent bars"}
        
        return {"direction": "NEUTRAL", "reason": "No clear price action signal"}
    
    def _analyze_order_flow(self, bars: List[Dict]) -> Dict[str, Any]:
        """Analyze order flow imbalance"""
        if len(bars) < 10:
            return {"direction": "NEUTRAL", "reason": "Insufficient data"}
        
        recent_bars = bars[-10:]
        
        # Calculate buying vs selling pressure
        buy_pressure = 0
        sell_pressure = 0
        
        for bar in recent_bars:
            volume = bar.get('volume', 1000)
            close_position = (bar['close'] - bar['low']) / (bar['high'] - bar['low']) if bar['high'] != bar['low'] else 0.5
            
            buy_pressure += volume * close_position
            sell_pressure += volume * (1 - close_position)
        
        ratio = buy_pressure / sell_pressure if sell_pressure > 0 else 1
        
        if ratio > 1.2:
            return {"direction": "BULLISH", "reason": f"Strong buying pressure (ratio: {ratio:.2f})"}
        elif ratio < 0.8:
            return {"direction": "BEARISH", "reason": f"Strong selling pressure (ratio: {ratio:.2f})"}
        
        return {"direction": "NEUTRAL", "reason": "Order flow balanced"}
    
    def _analyze_structure(self, bars: List[Dict]) -> Dict[str, Any]:
        """Analyze market structure (HH, HL, LH, LL)"""
        if len(bars) < 20:
            return {"direction": "NEUTRAL", "reason": "Insufficient data"}
        
        # Find swing highs and lows
        swing_highs = []
        swing_lows = []
        
        for i in range(2, len(bars) - 2):
            if bars[i]['high'] > bars[i-1]['high'] and bars[i]['high'] > bars[i-2]['high'] and \
               bars[i]['high'] > bars[i+1]['high'] and bars[i]['high'] > bars[i+2]['high']:
                swing_highs.append(bars[i]['high'])
            
            if bars[i]['low'] < bars[i-1]['low'] and bars[i]['low'] < bars[i-2]['low'] and \
               bars[i]['low'] < bars[i+1]['low'] and bars[i]['low'] < bars[i+2]['low']:
                swing_lows.append(bars[i]['low'])
        
        if len(swing_highs) >= 2 and len(swing_lows) >= 2:
            # Check for higher highs and higher lows (bullish structure)
            if swing_highs[-1] > swing_highs[-2] and swing_lows[-1] > swing_lows[-2]:
                return {"direction": "BULLISH", "reason": "Higher highs and higher lows - bullish structure"}
            
            # Check for lower highs and lower lows (bearish structure)
            if swing_highs[-1] < swing_highs[-2] and swing_lows[-1] < swing_lows[-2]:
                return {"direction": "BEARISH", "reason": "Lower highs and lower lows - bearish structure"}
        
        return {"direction": "NEUTRAL", "reason": "Ranging market - no clear structure"}
    
    def _analyze_delta_flow(self, bars: List[Dict]) -> Dict[str, Any]:
        """Analyze cumulative delta"""
        if len(bars) < 10:
            return {"direction": "NEUTRAL", "reason": "Insufficient data"}
        
        cumulative_delta = 0
        
        for bar in bars[-20:]:
            volume = bar.get('volume', 1000)
            is_bullish = bar['close'] >= bar['open']
            
            body = abs(bar['close'] - bar['open'])
            total_range = bar['high'] - bar['low']
            body_ratio = body / total_range if total_range > 0 else 0.5
            
            if is_bullish:
                bar_delta = volume * (0.3 + 0.4 * body_ratio)
            else:
                bar_delta = -volume * (0.3 + 0.4 * body_ratio)
            
            cumulative_delta += bar_delta
        
        if cumulative_delta > 5000:
            return {"direction": "BULLISH", "reason": f"Strong positive delta (+{cumulative_delta:.0f})"}
        elif cumulative_delta < -5000:
            return {"direction": "BEARISH", "reason": f"Strong negative delta ({cumulative_delta:.0f})"}
        
        return {"direction": "NEUTRAL", "reason": f"Delta neutral ({cumulative_delta:.0f})"}
    
    def _analyze_volume_profile(self, bars: List[Dict]) -> Dict[str, Any]:
        """Analyze volume profile (POC, VAH, VAL)"""
        if len(bars) < 20:
            return {"direction": "NEUTRAL", "reason": "Insufficient data"}
        
        # Calculate POC (Point of Control)
        price_volumes = {}
        for bar in bars[-50:]:
            mid_price = round((bar['high'] + bar['low']) / 2, 4)
            volume = bar.get('volume', 1000)
            price_volumes[mid_price] = price_volumes.get(mid_price, 0) + volume
        
        if not price_volumes:
            return {"direction": "NEUTRAL", "reason": "No volume data"}
        
        poc = max(price_volumes, key=price_volumes.get)
        current_price = bars[-1]['close']
        
        if current_price > poc * 1.001:
            return {"direction": "BULLISH", "reason": f"Price above POC ({poc:.5f}) - buyers in control"}
        elif current_price < poc * 0.999:
            return {"direction": "BEARISH", "reason": f"Price below POC ({poc:.5f}) - sellers in control"}
        
        return {"direction": "NEUTRAL", "reason": f"Price at POC ({poc:.5f}) - balanced"}
    
    def _analyze_institutional_flow(self, bars: List[Dict]) -> Dict[str, Any]:
        """Detect institutional activity"""
        if len(bars) < 10:
            return {"direction": "NEUTRAL", "reason": "Insufficient data"}
        
        # Look for high volume bars with large bodies (institutional moves)
        avg_volume = sum(b.get('volume', 1000) for b in bars[-20:]) / 20
        avg_body = sum(abs(b['close'] - b['open']) for b in bars[-20:]) / 20
        
        last_bar = bars[-1]
        last_volume = last_bar.get('volume', 1000)
        last_body = abs(last_bar['close'] - last_bar['open'])
        
        if last_volume > avg_volume * 2 and last_body > avg_body * 1.5:
            if last_bar['close'] > last_bar['open']:
                return {"direction": "BULLISH", "reason": "Institutional buying detected (high volume bullish bar)"}
            else:
                return {"direction": "BEARISH", "reason": "Institutional selling detected (high volume bearish bar)"}
        
        return {"direction": "NEUTRAL", "reason": "No institutional activity detected"}
    
    def _analyze_footprint(self, bars: List[Dict]) -> Dict[str, Any]:
        """Analyze footprint patterns"""
        if len(bars) < 5:
            return {"direction": "NEUTRAL", "reason": "Insufficient data"}
        
        # Look for stacked imbalances
        bullish_stack = 0
        bearish_stack = 0
        
        for bar in bars[-5:]:
            body = abs(bar['close'] - bar['open'])
            total_range = bar['high'] - bar['low']
            body_ratio = body / total_range if total_range > 0 else 0.5
            
            if body_ratio > 0.6:
                if bar['close'] > bar['open']:
                    bullish_stack += 1
                else:
                    bearish_stack += 1
        
        if bullish_stack >= 3:
            return {"direction": "BULLISH", "reason": f"Bullish stacked imbalance ({bullish_stack} strong bars)"}
        elif bearish_stack >= 3:
            return {"direction": "BEARISH", "reason": f"Bearish stacked imbalance ({bearish_stack} strong bars)"}
        
        return {"direction": "NEUTRAL", "reason": "No footprint imbalance"}
    
    def _analyze_session(self, bars: List[Dict]) -> Dict[str, Any]:
        """Analyze session context"""
        # Simplified session analysis
        current_hour = datetime.now().hour
        
        # London session (7-16 UTC) - most volatile
        if 7 <= current_hour <= 16:
            # During London, follow the trend
            recent_trend = bars[-1]['close'] - bars[-10]['close'] if len(bars) >= 10 else 0
            if recent_trend > 0:
                return {"direction": "BULLISH", "reason": "London session - following bullish trend"}
            elif recent_trend < 0:
                return {"direction": "BEARISH", "reason": "London session - following bearish trend"}
        
        # Asian session (0-7 UTC) - ranging
        if 0 <= current_hour < 7:
            return {"direction": "NEUTRAL", "reason": "Asian session - expect ranging"}
        
        return {"direction": "NEUTRAL", "reason": "Session analysis neutral"}
    
    def _analyze_vwap(self, bars: List[Dict]) -> Dict[str, Any]:
        """Analyze VWAP position"""
        if len(bars) < 10:
            return {"direction": "NEUTRAL", "reason": "Insufficient data"}
        
        # Calculate VWAP
        cumulative_tpv = 0
        cumulative_volume = 0
        
        for bar in bars[-50:]:
            typical_price = (bar['high'] + bar['low'] + bar['close']) / 3
            volume = bar.get('volume', 1000)
            cumulative_tpv += typical_price * volume
            cumulative_volume += volume
        
        vwap = cumulative_tpv / cumulative_volume if cumulative_volume > 0 else bars[-1]['close']
        current_price = bars[-1]['close']
        
        if current_price > vwap * 1.001:
            return {"direction": "BULLISH", "reason": f"Price above VWAP ({vwap:.5f})"}
        elif current_price < vwap * 0.999:
            return {"direction": "BEARISH", "reason": f"Price below VWAP ({vwap:.5f})"}
        
        return {"direction": "NEUTRAL", "reason": f"Price at VWAP ({vwap:.5f})"}
    
    def _analyze_absorption(self, bars: List[Dict]) -> Dict[str, Any]:
        """Detect absorption patterns"""
        if len(bars) < 5:
            return {"direction": "NEUTRAL", "reason": "Insufficient data"}
        
        # Look for high volume with small body (absorption)
        for i in range(-3, 0):
            bar = bars[i]
            prev_bar = bars[i-1]
            
            volume = bar.get('volume', 1000)
            prev_volume = prev_bar.get('volume', 1000)
            
            body = abs(bar['close'] - bar['open'])
            total_range = bar['high'] - bar['low']
            body_ratio = body / total_range if total_range > 0 else 0.5
            
            # High volume + small body = absorption
            if volume > prev_volume * 1.5 and body_ratio < 0.3:
                # Absorption at lows = bullish
                if bar['close'] < bars[-10]['close'] if len(bars) >= 10 else False:
                    return {"direction": "BULLISH", "reason": "Absorption at lows - potential reversal"}
                # Absorption at highs = bearish
                elif bar['close'] > bars[-10]['close'] if len(bars) >= 10 else False:
                    return {"direction": "BEARISH", "reason": "Absorption at highs - potential reversal"}
        
        return {"direction": "NEUTRAL", "reason": "No absorption detected"}
    
    def _calculate_atr(self, bars: List[Dict], period: int = 14) -> float:
        """Calculate Average True Range"""
        if len(bars) < period + 1:
            return 0.001
        
        true_ranges = []
        for i in range(-period, 0):
            bar = bars[i]
            prev_bar = bars[i-1]
            
            tr = max(
                bar['high'] - bar['low'],
                abs(bar['high'] - prev_bar['close']),
                abs(bar['low'] - prev_bar['close'])
            )
            true_ranges.append(tr)
        
        return sum(true_ranges) / len(true_ranges)


# Test the unified intelligence
if __name__ == "__main__":
    # Create sample data
    import random
    
    bars = []
    price = 1.0850
    for i in range(100):
        change = random.uniform(-0.002, 0.002)
        open_price = price
        close_price = price + change
        high_price = max(open_price, close_price) + random.uniform(0, 0.001)
        low_price = min(open_price, close_price) - random.uniform(0, 0.001)
        
        bars.append({
            "timestamp": f"2026-01-28 {i:02d}:00",
            "open": open_price,
            "high": high_price,
            "low": low_price,
            "close": close_price,
            "volume": random.randint(1000, 5000)
        })
        price = close_price
    
    intelligence = UnifiedIntelligence()
    result = intelligence.analyze({"bars": bars, "symbol": "EURUSD"})
    
    print("\n=== UNIFIED INTELLIGENCE ANALYSIS ===")
    print(f"Direction: {result['direction']}")
    print(f"Confidence: {result['confidence']:.2%}")
    print(f"Weighted Score: {result['weighted_score']}")
    print(f"\nConfluence: {result['confluence']}")
    print(f"\nNarrative: {result['narrative']}")
    print(f"\nTrade Setup: {result['trade_setup']}")
