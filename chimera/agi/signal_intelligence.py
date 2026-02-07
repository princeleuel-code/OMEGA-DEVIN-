"""
SIGNAL INTELLIGENCE ENGINE
===========================
Advanced signal generation for the TRUE Trading AGI.

This module implements:
1. Multi-source signal fusion
2. Confidence-weighted signal aggregation
3. Dynamic signal filtering
4. Real-time signal adaptation

This is what makes the AGI generate ACTIONABLE signals.
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import numpy as np
from collections import deque


class SignalType(Enum):
    """Types of trading signals"""
    ENTRY_LONG = "entry_long"
    ENTRY_SHORT = "entry_short"
    EXIT_LONG = "exit_long"
    EXIT_SHORT = "exit_short"
    SCALE_IN = "scale_in"
    SCALE_OUT = "scale_out"
    STOP_ADJUST = "stop_adjust"
    TAKE_PROFIT = "take_profit"
    WAIT = "wait"


class SignalSource(Enum):
    """Sources of signals"""
    PRICE_ACTION = "price_action"
    VOLUME_PROFILE = "volume_profile"
    ORDER_FLOW = "order_flow"
    MARKET_STRUCTURE = "market_structure"
    MOMENTUM = "momentum"
    VOLATILITY = "volatility"
    CORRELATION = "correlation"
    SENTIMENT = "sentiment"
    PATTERN = "pattern"
    INSTITUTIONAL = "institutional"


@dataclass
class Signal:
    """A trading signal"""
    id: str
    type: SignalType
    source: SignalSource
    direction: str  # LONG, SHORT, NEUTRAL
    strength: float  # 0-1
    confidence: float  # 0-1
    price: float
    timestamp: datetime
    expiry: datetime
    metadata: Dict = field(default_factory=dict)
    
    def is_valid(self) -> bool:
        """Check if signal is still valid"""
        return datetime.now() < self.expiry
    
    def weighted_score(self) -> float:
        """Get weighted score combining strength and confidence"""
        return self.strength * self.confidence


@dataclass
class SignalCluster:
    """A cluster of related signals"""
    signals: List[Signal]
    direction: str
    combined_strength: float
    combined_confidence: float
    sources: List[SignalSource]
    timestamp: datetime
    
    def get_consensus(self) -> Tuple[str, float]:
        """Get consensus direction and confidence"""
        if not self.signals:
            return "NEUTRAL", 0.0
        
        long_score = sum(s.weighted_score() for s in self.signals if s.direction == "LONG")
        short_score = sum(s.weighted_score() for s in self.signals if s.direction == "SHORT")
        
        total = long_score + short_score
        if total == 0:
            return "NEUTRAL", 0.0
        
        if long_score > short_score:
            return "LONG", long_score / total
        elif short_score > long_score:
            return "SHORT", short_score / total
        else:
            return "NEUTRAL", 0.5


class PriceActionAnalyzer:
    """Analyze price action for signals"""
    
    def analyze(self, candles: List[Dict]) -> List[Signal]:
        """Analyze price action and generate signals"""
        signals = []
        
        if len(candles) < 3:
            return signals
        
        # Get recent candles
        current = candles[-1]
        prev = candles[-2]
        prev2 = candles[-3]
        
        price = current.get("close", 0)
        
        # Bullish engulfing
        if (prev.get("close", 0) < prev.get("open", 0) and
            current.get("close", 0) > current.get("open", 0) and
            current.get("close", 0) > prev.get("open", 0) and
            current.get("open", 0) < prev.get("close", 0)):
            
            signals.append(Signal(
                id=f"pa_bullish_engulf_{datetime.now().strftime('%H%M%S')}",
                type=SignalType.ENTRY_LONG,
                source=SignalSource.PRICE_ACTION,
                direction="LONG",
                strength=0.7,
                confidence=0.65,
                price=price,
                timestamp=datetime.now(),
                expiry=datetime.now() + timedelta(minutes=30),
                metadata={"pattern": "bullish_engulfing"}
            ))
        
        # Bearish engulfing
        if (prev.get("close", 0) > prev.get("open", 0) and
            current.get("close", 0) < current.get("open", 0) and
            current.get("close", 0) < prev.get("open", 0) and
            current.get("open", 0) > prev.get("close", 0)):
            
            signals.append(Signal(
                id=f"pa_bearish_engulf_{datetime.now().strftime('%H%M%S')}",
                type=SignalType.ENTRY_SHORT,
                source=SignalSource.PRICE_ACTION,
                direction="SHORT",
                strength=0.7,
                confidence=0.65,
                price=price,
                timestamp=datetime.now(),
                expiry=datetime.now() + timedelta(minutes=30),
                metadata={"pattern": "bearish_engulfing"}
            ))
        
        # Pin bar / hammer
        body = abs(current.get("close", 0) - current.get("open", 0))
        upper_wick = current.get("high", 0) - max(current.get("close", 0), current.get("open", 0))
        lower_wick = min(current.get("close", 0), current.get("open", 0)) - current.get("low", 0)
        
        if lower_wick > body * 2 and upper_wick < body * 0.5:
            # Bullish pin bar
            signals.append(Signal(
                id=f"pa_pin_bull_{datetime.now().strftime('%H%M%S')}",
                type=SignalType.ENTRY_LONG,
                source=SignalSource.PRICE_ACTION,
                direction="LONG",
                strength=0.6,
                confidence=0.6,
                price=price,
                timestamp=datetime.now(),
                expiry=datetime.now() + timedelta(minutes=30),
                metadata={"pattern": "bullish_pin_bar"}
            ))
        
        if upper_wick > body * 2 and lower_wick < body * 0.5:
            # Bearish pin bar
            signals.append(Signal(
                id=f"pa_pin_bear_{datetime.now().strftime('%H%M%S')}",
                type=SignalType.ENTRY_SHORT,
                source=SignalSource.PRICE_ACTION,
                direction="SHORT",
                strength=0.6,
                confidence=0.6,
                price=price,
                timestamp=datetime.now(),
                expiry=datetime.now() + timedelta(minutes=30),
                metadata={"pattern": "bearish_pin_bar"}
            ))
        
        # Three white soldiers
        if (len(candles) >= 3 and
            all(candles[i].get("close", 0) > candles[i].get("open", 0) for i in range(-3, 0)) and
            all(candles[i].get("close", 0) > candles[i-1].get("close", 0) for i in range(-2, 0))):
            
            signals.append(Signal(
                id=f"pa_3ws_{datetime.now().strftime('%H%M%S')}",
                type=SignalType.ENTRY_LONG,
                source=SignalSource.PRICE_ACTION,
                direction="LONG",
                strength=0.75,
                confidence=0.7,
                price=price,
                timestamp=datetime.now(),
                expiry=datetime.now() + timedelta(minutes=30),
                metadata={"pattern": "three_white_soldiers"}
            ))
        
        # Three black crows
        if (len(candles) >= 3 and
            all(candles[i].get("close", 0) < candles[i].get("open", 0) for i in range(-3, 0)) and
            all(candles[i].get("close", 0) < candles[i-1].get("close", 0) for i in range(-2, 0))):
            
            signals.append(Signal(
                id=f"pa_3bc_{datetime.now().strftime('%H%M%S')}",
                type=SignalType.ENTRY_SHORT,
                source=SignalSource.PRICE_ACTION,
                direction="SHORT",
                strength=0.75,
                confidence=0.7,
                price=price,
                timestamp=datetime.now(),
                expiry=datetime.now() + timedelta(minutes=30),
                metadata={"pattern": "three_black_crows"}
            ))
        
        return signals


class OrderFlowAnalyzer:
    """Analyze order flow for signals"""
    
    def analyze(self, data: Dict) -> List[Signal]:
        """Analyze order flow and generate signals"""
        signals = []
        
        delta = data.get("delta", 0)
        cumulative_delta = data.get("cumulative_delta", 0)
        volume = data.get("volume", 0)
        price = data.get("price", 0)
        
        # Strong positive delta
        if delta > 1000:
            strength = min(delta / 2000, 1.0)
            signals.append(Signal(
                id=f"of_pos_delta_{datetime.now().strftime('%H%M%S')}",
                type=SignalType.ENTRY_LONG,
                source=SignalSource.ORDER_FLOW,
                direction="LONG",
                strength=strength,
                confidence=0.7,
                price=price,
                timestamp=datetime.now(),
                expiry=datetime.now() + timedelta(minutes=15),
                metadata={"delta": delta, "type": "positive_delta"}
            ))
        
        # Strong negative delta
        if delta < -1000:
            strength = min(abs(delta) / 2000, 1.0)
            signals.append(Signal(
                id=f"of_neg_delta_{datetime.now().strftime('%H%M%S')}",
                type=SignalType.ENTRY_SHORT,
                source=SignalSource.ORDER_FLOW,
                direction="SHORT",
                strength=strength,
                confidence=0.7,
                price=price,
                timestamp=datetime.now(),
                expiry=datetime.now() + timedelta(minutes=15),
                metadata={"delta": delta, "type": "negative_delta"}
            ))
        
        # Delta divergence (price up, delta down)
        candles = data.get("candles", [])
        if len(candles) >= 2:
            price_change = candles[-1].get("close", 0) - candles[-2].get("close", 0)
            
            if price_change > 0 and delta < -500:
                signals.append(Signal(
                    id=f"of_div_bear_{datetime.now().strftime('%H%M%S')}",
                    type=SignalType.ENTRY_SHORT,
                    source=SignalSource.ORDER_FLOW,
                    direction="SHORT",
                    strength=0.65,
                    confidence=0.6,
                    price=price,
                    timestamp=datetime.now(),
                    expiry=datetime.now() + timedelta(minutes=20),
                    metadata={"type": "bearish_divergence", "price_change": price_change, "delta": delta}
                ))
            
            if price_change < 0 and delta > 500:
                signals.append(Signal(
                    id=f"of_div_bull_{datetime.now().strftime('%H%M%S')}",
                    type=SignalType.ENTRY_LONG,
                    source=SignalSource.ORDER_FLOW,
                    direction="LONG",
                    strength=0.65,
                    confidence=0.6,
                    price=price,
                    timestamp=datetime.now(),
                    expiry=datetime.now() + timedelta(minutes=20),
                    metadata={"type": "bullish_divergence", "price_change": price_change, "delta": delta}
                ))
        
        # Absorption detection
        if volume > data.get("avg_volume", volume) * 2 and abs(delta) < volume * 0.1:
            # High volume but balanced delta = absorption
            signals.append(Signal(
                id=f"of_absorb_{datetime.now().strftime('%H%M%S')}",
                type=SignalType.WAIT,
                source=SignalSource.ORDER_FLOW,
                direction="NEUTRAL",
                strength=0.8,
                confidence=0.75,
                price=price,
                timestamp=datetime.now(),
                expiry=datetime.now() + timedelta(minutes=10),
                metadata={"type": "absorption", "volume": volume, "delta": delta}
            ))
        
        return signals


class MarketStructureAnalyzer:
    """Analyze market structure for signals"""
    
    def __init__(self):
        self.swing_highs: List[float] = []
        self.swing_lows: List[float] = []
    
    def analyze(self, candles: List[Dict]) -> List[Signal]:
        """Analyze market structure and generate signals"""
        signals = []
        
        if len(candles) < 10:
            return signals
        
        price = candles[-1].get("close", 0)
        
        # Find swing points
        self._update_swing_points(candles)
        
        # Break of structure (BOS)
        if self.swing_highs and price > max(self.swing_highs[-3:] if len(self.swing_highs) >= 3 else self.swing_highs):
            signals.append(Signal(
                id=f"ms_bos_bull_{datetime.now().strftime('%H%M%S')}",
                type=SignalType.ENTRY_LONG,
                source=SignalSource.MARKET_STRUCTURE,
                direction="LONG",
                strength=0.8,
                confidence=0.75,
                price=price,
                timestamp=datetime.now(),
                expiry=datetime.now() + timedelta(minutes=60),
                metadata={"type": "bullish_bos", "broken_high": max(self.swing_highs[-3:])}
            ))
        
        if self.swing_lows and price < min(self.swing_lows[-3:] if len(self.swing_lows) >= 3 else self.swing_lows):
            signals.append(Signal(
                id=f"ms_bos_bear_{datetime.now().strftime('%H%M%S')}",
                type=SignalType.ENTRY_SHORT,
                source=SignalSource.MARKET_STRUCTURE,
                direction="SHORT",
                strength=0.8,
                confidence=0.75,
                price=price,
                timestamp=datetime.now(),
                expiry=datetime.now() + timedelta(minutes=60),
                metadata={"type": "bearish_bos", "broken_low": min(self.swing_lows[-3:])}
            ))
        
        # Higher highs and higher lows (uptrend)
        if len(self.swing_highs) >= 2 and len(self.swing_lows) >= 2:
            if (self.swing_highs[-1] > self.swing_highs[-2] and 
                self.swing_lows[-1] > self.swing_lows[-2]):
                signals.append(Signal(
                    id=f"ms_uptrend_{datetime.now().strftime('%H%M%S')}",
                    type=SignalType.ENTRY_LONG,
                    source=SignalSource.MARKET_STRUCTURE,
                    direction="LONG",
                    strength=0.7,
                    confidence=0.7,
                    price=price,
                    timestamp=datetime.now(),
                    expiry=datetime.now() + timedelta(minutes=60),
                    metadata={"type": "uptrend_structure"}
                ))
            
            # Lower highs and lower lows (downtrend)
            if (self.swing_highs[-1] < self.swing_highs[-2] and 
                self.swing_lows[-1] < self.swing_lows[-2]):
                signals.append(Signal(
                    id=f"ms_downtrend_{datetime.now().strftime('%H%M%S')}",
                    type=SignalType.ENTRY_SHORT,
                    source=SignalSource.MARKET_STRUCTURE,
                    direction="SHORT",
                    strength=0.7,
                    confidence=0.7,
                    price=price,
                    timestamp=datetime.now(),
                    expiry=datetime.now() + timedelta(minutes=60),
                    metadata={"type": "downtrend_structure"}
                ))
        
        return signals
    
    def _update_swing_points(self, candles: List[Dict]):
        """Update swing high and low points"""
        if len(candles) < 5:
            return
        
        # Simple swing point detection
        for i in range(2, len(candles) - 2):
            high = candles[i].get("high", 0)
            low = candles[i].get("low", 0)
            
            # Swing high
            if (high > candles[i-1].get("high", 0) and 
                high > candles[i-2].get("high", 0) and
                high > candles[i+1].get("high", 0) and 
                high > candles[i+2].get("high", 0)):
                if high not in self.swing_highs:
                    self.swing_highs.append(high)
            
            # Swing low
            if (low < candles[i-1].get("low", float('inf')) and 
                low < candles[i-2].get("low", float('inf')) and
                low < candles[i+1].get("low", float('inf')) and 
                low < candles[i+2].get("low", float('inf'))):
                if low not in self.swing_lows:
                    self.swing_lows.append(low)
        
        # Keep only recent swing points
        self.swing_highs = self.swing_highs[-10:]
        self.swing_lows = self.swing_lows[-10:]


class MomentumAnalyzer:
    """Analyze momentum for signals"""
    
    def analyze(self, candles: List[Dict]) -> List[Signal]:
        """Analyze momentum and generate signals"""
        signals = []
        
        if len(candles) < 14:
            return signals
        
        price = candles[-1].get("close", 0)
        
        # Calculate RSI
        rsi = self._calculate_rsi(candles)
        
        # Oversold
        if rsi < 30:
            signals.append(Signal(
                id=f"mom_oversold_{datetime.now().strftime('%H%M%S')}",
                type=SignalType.ENTRY_LONG,
                source=SignalSource.MOMENTUM,
                direction="LONG",
                strength=0.6 + (30 - rsi) / 100,
                confidence=0.6,
                price=price,
                timestamp=datetime.now(),
                expiry=datetime.now() + timedelta(minutes=30),
                metadata={"rsi": rsi, "type": "oversold"}
            ))
        
        # Overbought
        if rsi > 70:
            signals.append(Signal(
                id=f"mom_overbought_{datetime.now().strftime('%H%M%S')}",
                type=SignalType.ENTRY_SHORT,
                source=SignalSource.MOMENTUM,
                direction="SHORT",
                strength=0.6 + (rsi - 70) / 100,
                confidence=0.6,
                price=price,
                timestamp=datetime.now(),
                expiry=datetime.now() + timedelta(minutes=30),
                metadata={"rsi": rsi, "type": "overbought"}
            ))
        
        # Strong momentum
        closes = [c.get("close", 0) for c in candles[-5:]]
        momentum = (closes[-1] - closes[0]) / closes[0] if closes[0] > 0 else 0
        
        if momentum > 0.005:  # 0.5% move
            signals.append(Signal(
                id=f"mom_strong_bull_{datetime.now().strftime('%H%M%S')}",
                type=SignalType.ENTRY_LONG,
                source=SignalSource.MOMENTUM,
                direction="LONG",
                strength=min(momentum * 100, 1.0),
                confidence=0.65,
                price=price,
                timestamp=datetime.now(),
                expiry=datetime.now() + timedelta(minutes=15),
                metadata={"momentum": momentum, "type": "strong_bullish"}
            ))
        
        if momentum < -0.005:
            signals.append(Signal(
                id=f"mom_strong_bear_{datetime.now().strftime('%H%M%S')}",
                type=SignalType.ENTRY_SHORT,
                source=SignalSource.MOMENTUM,
                direction="SHORT",
                strength=min(abs(momentum) * 100, 1.0),
                confidence=0.65,
                price=price,
                timestamp=datetime.now(),
                expiry=datetime.now() + timedelta(minutes=15),
                metadata={"momentum": momentum, "type": "strong_bearish"}
            ))
        
        return signals
    
    def _calculate_rsi(self, candles: List[Dict], period: int = 14) -> float:
        """Calculate RSI"""
        if len(candles) < period + 1:
            return 50.0
        
        closes = [c.get("close", 0) for c in candles[-(period+1):]]
        deltas = [closes[i] - closes[i-1] for i in range(1, len(closes))]
        
        gains = [d if d > 0 else 0 for d in deltas]
        losses = [-d if d < 0 else 0 for d in deltas]
        
        avg_gain = sum(gains) / period
        avg_loss = sum(losses) / period
        
        if avg_loss == 0:
            return 100.0
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi


class SignalIntelligence:
    """
    The complete signal intelligence engine.
    
    Combines multiple analyzers and fuses their signals
    into actionable trading decisions.
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {
            "min_confluence": 2,
            "min_confidence": 0.6,
            "signal_expiry_minutes": 30
        }
        
        # Analyzers
        self.price_action = PriceActionAnalyzer()
        self.order_flow = OrderFlowAnalyzer()
        self.market_structure = MarketStructureAnalyzer()
        self.momentum = MomentumAnalyzer()
        
        # Signal history
        self.signal_history: deque = deque(maxlen=1000)
        self.active_signals: List[Signal] = []
    
    def analyze(self, market_data: Dict) -> Dict:
        """
        Analyze market data and generate signals.
        
        This is the main entry point for signal generation.
        """
        all_signals = []
        
        # Get candles
        candles = market_data.get("candles", [])
        
        # Run all analyzers
        all_signals.extend(self.price_action.analyze(candles))
        all_signals.extend(self.order_flow.analyze(market_data))
        all_signals.extend(self.market_structure.analyze(candles))
        all_signals.extend(self.momentum.analyze(candles))
        
        # Filter valid signals
        valid_signals = [s for s in all_signals if s.is_valid()]
        
        # Cluster signals by direction
        long_signals = [s for s in valid_signals if s.direction == "LONG"]
        short_signals = [s for s in valid_signals if s.direction == "SHORT"]
        neutral_signals = [s for s in valid_signals if s.direction == "NEUTRAL"]
        
        # Create clusters
        long_cluster = self._create_cluster(long_signals, "LONG")
        short_cluster = self._create_cluster(short_signals, "SHORT")
        
        # Determine final signal
        final_signal = self._determine_final_signal(long_cluster, short_cluster, neutral_signals)
        
        # Update history
        for signal in valid_signals:
            self.signal_history.append(signal)
        
        self.active_signals = valid_signals
        
        return {
            "final_signal": final_signal,
            "long_cluster": long_cluster,
            "short_cluster": short_cluster,
            "all_signals": len(valid_signals),
            "long_signals": len(long_signals),
            "short_signals": len(short_signals),
            "neutral_signals": len(neutral_signals),
            "sources_active": list(set(s.source.value for s in valid_signals))
        }
    
    def _create_cluster(self, signals: List[Signal], direction: str) -> Optional[SignalCluster]:
        """Create a signal cluster"""
        if not signals:
            return None
        
        combined_strength = sum(s.strength for s in signals) / len(signals)
        combined_confidence = sum(s.confidence for s in signals) / len(signals)
        sources = list(set(s.source for s in signals))
        
        return SignalCluster(
            signals=signals,
            direction=direction,
            combined_strength=combined_strength,
            combined_confidence=combined_confidence,
            sources=sources,
            timestamp=datetime.now()
        )
    
    def _determine_final_signal(
        self,
        long_cluster: Optional[SignalCluster],
        short_cluster: Optional[SignalCluster],
        neutral_signals: List[Signal]
    ) -> Dict:
        """Determine the final trading signal"""
        # Check for absorption (wait signal)
        if any(s.metadata.get("type") == "absorption" for s in neutral_signals):
            return {
                "direction": "WAIT",
                "confidence": 0.8,
                "reason": "Absorption detected - waiting for resolution",
                "type": SignalType.WAIT.value
            }
        
        # Compare clusters
        long_score = 0
        short_score = 0
        
        if long_cluster:
            long_score = (long_cluster.combined_strength * long_cluster.combined_confidence * 
                         len(long_cluster.signals))
        
        if short_cluster:
            short_score = (short_cluster.combined_strength * short_cluster.combined_confidence * 
                          len(short_cluster.signals))
        
        # Check confluence
        min_confluence = self.config["min_confluence"]
        min_confidence = self.config["min_confidence"]
        
        if long_score > short_score and long_cluster:
            if (len(long_cluster.signals) >= min_confluence and 
                long_cluster.combined_confidence >= min_confidence):
                return {
                    "direction": "LONG",
                    "confidence": long_cluster.combined_confidence,
                    "strength": long_cluster.combined_strength,
                    "confluence": len(long_cluster.signals),
                    "sources": [s.value for s in long_cluster.sources],
                    "reason": f"Bullish confluence from {len(long_cluster.signals)} signals",
                    "type": SignalType.ENTRY_LONG.value
                }
        
        if short_score > long_score and short_cluster:
            if (len(short_cluster.signals) >= min_confluence and 
                short_cluster.combined_confidence >= min_confidence):
                return {
                    "direction": "SHORT",
                    "confidence": short_cluster.combined_confidence,
                    "strength": short_cluster.combined_strength,
                    "confluence": len(short_cluster.signals),
                    "sources": [s.value for s in short_cluster.sources],
                    "reason": f"Bearish confluence from {len(short_cluster.signals)} signals",
                    "type": SignalType.ENTRY_SHORT.value
                }
        
        # No clear signal
        return {
            "direction": "NEUTRAL",
            "confidence": 0.5,
            "reason": "Insufficient confluence for trade",
            "type": SignalType.WAIT.value
        }
    
    def get_stats(self) -> Dict:
        """Get signal statistics"""
        return {
            "total_signals_generated": len(self.signal_history),
            "active_signals": len(self.active_signals),
            "signal_sources": list(set(s.source.value for s in self.active_signals))
        }


# Factory function
def create_signal_intelligence(config: Optional[Dict] = None) -> SignalIntelligence:
    """Create a signal intelligence engine"""
    return SignalIntelligence(config)
