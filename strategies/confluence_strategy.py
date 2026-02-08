# OMEGA-DEVIN // STRATEGY MODULE: CONFLUENCE STRATEGY
# Combines ALL intelligence modules for high-probability setups

from typing import Dict, List, Any
from datetime import datetime
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

class ConfluenceStrategy:
    """
    CONFLUENCE STRATEGY
    
    Only takes trades when multiple signals agree.
    This is the EDGE - high confluence = high probability.
    
    Minimum 6 signals must agree for a trade.
    """
    
    def __init__(self, min_confluence: int = 6, min_confidence: float = 0.70):
        self.min_confluence = min_confluence
        self.min_confidence = min_confidence
        
    def analyze(self, bars: List[Dict], unified_analysis: Dict = None) -> Dict[str, Any]:
        """
        Analyze for high confluence setups
        
        Args:
            bars: OHLCV data
            unified_analysis: Optional pre-computed unified analysis
            
        Returns:
            Trade signal if confluence is met
        """
        if not bars or len(bars) < 20:
            return self._no_signal("Insufficient data")
        
        # Get unified analysis if not provided
        if unified_analysis is None:
            try:
                from core.unified_intelligence import UnifiedIntelligence
                intelligence = UnifiedIntelligence()
                unified_analysis = intelligence.analyze({"bars": bars})
            except ImportError:
                # Fallback to basic analysis
                unified_analysis = self._basic_analysis(bars)
        
        # Check confluence
        confluence = unified_analysis.get('confluence', {})
        bullish = confluence.get('bullish', 0)
        bearish = confluence.get('bearish', 0)
        confidence = unified_analysis.get('confidence', 0)
        
        # Determine direction based on confluence
        if bullish >= self.min_confluence and confidence >= self.min_confidence:
            return {
                "signal": "LONG",
                "confidence": confidence,
                "confluence": bullish,
                "trade_setup": unified_analysis.get('trade_setup'),
                "reason": f"HIGH CONFLUENCE LONG: {bullish} bullish signals at {confidence:.0%} confidence",
                "timestamp": datetime.now().isoformat()
            }
        
        if bearish >= self.min_confluence and confidence >= self.min_confidence:
            return {
                "signal": "SHORT",
                "confidence": confidence,
                "confluence": bearish,
                "trade_setup": unified_analysis.get('trade_setup'),
                "reason": f"HIGH CONFLUENCE SHORT: {bearish} bearish signals at {confidence:.0%} confidence",
                "timestamp": datetime.now().isoformat()
            }
        
        return self._no_signal(f"Confluence too low: {max(bullish, bearish)} signals (need {self.min_confluence})")
    
    def _basic_analysis(self, bars: List[Dict]) -> Dict[str, Any]:
        """Basic analysis fallback"""
        bullish = 0
        bearish = 0
        
        # Trend
        if bars[-1]['close'] > bars[-10]['close']:
            bullish += 1
        else:
            bearish += 1
        
        # Last candle
        if bars[-1]['close'] > bars[-1]['open']:
            bullish += 1
        else:
            bearish += 1
        
        # Volume
        avg_vol = sum(b.get('volume', 1000) for b in bars[-10:]) / 10
        if bars[-1].get('volume', 1000) > avg_vol:
            if bars[-1]['close'] > bars[-1]['open']:
                bullish += 1
            else:
                bearish += 1
        
        return {
            'confluence': {'bullish': bullish, 'bearish': bearish, 'neutral': 10 - bullish - bearish},
            'confidence': max(bullish, bearish) / 10
        }
    
    def _no_signal(self, reason: str) -> Dict[str, Any]:
        return {
            "signal": "WAIT",
            "confidence": 0,
            "confluence": 0,
            "reason": reason,
            "timestamp": datetime.now().isoformat()
        }
