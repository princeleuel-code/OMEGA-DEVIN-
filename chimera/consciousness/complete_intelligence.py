"""
COMPLETE INTELLIGENCE MODULE - THE ULTIMATE INTEGRATION

This module combines ALL intelligence systems into a single, comprehensive engine:
1. Technical Intelligence (Delta Print, VPIN, HMM regimes)
2. Fundamental Intelligence (Financials, Valuation, Earnings)
3. Unified Signal Generation (Technical + Fundamental confluence)

This is what institutional traders do - they don't just look at charts OR fundamentals,
they look at BOTH. This module provides TRUE institutional-grade intelligence.

The key insight: 
- WHY to trade (fundamentals - is it worth buying?)
- WHEN to trade (technicals - is now the right entry?)

Author: Devin (for Prince)
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

from .unified_intelligence import (
    UnifiedIntelligence,
    UnifiedAnalysis,
    UnifiedSignal,
    SignalStrength,
    MarketRegimeUnified,
    create_unified_intelligence,
)
from .fundamental_intelligence import (
    FundamentalIntelligence,
    FundamentalAnalysis,
    FundamentalHealth,
    ValuationStatus,
    create_fundamental_intelligence,
)


class CompleteSignalStrength(Enum):
    """Complete signal strength combining technical and fundamental."""
    NO_SIGNAL = "no_signal"
    WEAK = "weak"
    MODERATE = "moderate"
    STRONG = "strong"
    VERY_STRONG = "very_strong"
    EXTREME = "extreme"
    INSTITUTIONAL_GRADE = "institutional_grade"  # Both technical AND fundamental align


class ConfluenceType(Enum):
    """Type of confluence between technical and fundamental."""
    FULL_CONFLUENCE = "full_confluence"      # Both strongly agree
    PARTIAL_CONFLUENCE = "partial_confluence"  # Both agree but one is weak
    NEUTRAL = "neutral"                       # Mixed signals
    DIVERGENCE = "divergence"                 # Technical and fundamental disagree
    STRONG_DIVERGENCE = "strong_divergence"   # Strong disagreement


@dataclass
class CompleteSignal:
    """A complete trading signal combining technical and fundamental analysis."""
    timestamp: datetime
    symbol: str
    current_price: float
    
    # Direction and strength
    direction: str  # "buy", "sell", "wait"
    strength: CompleteSignalStrength
    confidence: float  # 0-1
    
    # Entry details
    entry_price: Optional[float]
    stop_loss: Optional[float]
    take_profit: Optional[float]
    risk_reward_ratio: Optional[float]
    
    # Technical component
    technical_direction: str
    technical_confidence: float
    technical_reasoning: str
    
    # Fundamental component
    fundamental_bias: str
    fundamental_confidence: float
    fundamental_reasoning: str
    
    # Confluence
    confluence_type: ConfluenceType
    confluence_score: float  # 0-1
    
    # Combined reasoning
    reasoning: str
    factors: List[str]
    warnings: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp.isoformat(),
            "symbol": self.symbol,
            "current_price": self.current_price,
            "direction": self.direction,
            "strength": self.strength.value,
            "confidence": self.confidence,
            "entry_price": self.entry_price,
            "stop_loss": self.stop_loss,
            "take_profit": self.take_profit,
            "risk_reward_ratio": self.risk_reward_ratio,
            "technical_direction": self.technical_direction,
            "technical_confidence": self.technical_confidence,
            "technical_reasoning": self.technical_reasoning,
            "fundamental_bias": self.fundamental_bias,
            "fundamental_confidence": self.fundamental_confidence,
            "fundamental_reasoning": self.fundamental_reasoning,
            "confluence_type": self.confluence_type.value,
            "confluence_score": self.confluence_score,
            "reasoning": self.reasoning,
            "factors": self.factors,
            "warnings": self.warnings,
        }


@dataclass
class CompleteAnalysis:
    """Complete analysis output combining all intelligence systems."""
    timestamp: datetime
    symbol: str
    company_name: str
    current_price: float
    
    # Component analyses
    technical: UnifiedAnalysis
    fundamental: FundamentalAnalysis
    
    # Complete signal
    signal: CompleteSignal
    
    # Overall assessment
    market_quality: float  # 0-1
    institutional_activity: float  # 0-1
    overall_confidence: float  # 0-1
    
    # Meta
    analysis_time_ms: float
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp.isoformat(),
            "symbol": self.symbol,
            "company_name": self.company_name,
            "current_price": self.current_price,
            "technical": self.technical.to_dict(),
            "fundamental": self.fundamental.to_dict(),
            "signal": self.signal.to_dict(),
            "market_quality": self.market_quality,
            "institutional_activity": self.institutional_activity,
            "overall_confidence": self.overall_confidence,
            "analysis_time_ms": self.analysis_time_ms,
        }


class CompleteIntelligence:
    """
    COMPLETE INTELLIGENCE ENGINE - THE ULTIMATE INTEGRATION
    
    Combines:
    1. Technical Intelligence (Delta Print, VPIN, HMM regimes)
    2. Fundamental Intelligence (Financials, Valuation, Earnings)
    
    Into a single, institutional-grade trading system.
    """
    
    def __init__(
        self,
        # Technical parameters
        min_technical_confluence: float = 0.40,
        # Fundamental parameters
        min_fundamental_confidence: float = 0.50,
        # Combined parameters
        min_combined_confidence: float = 0.55,
        technical_weight: float = 0.6,  # 60% technical, 40% fundamental
        fundamental_weight: float = 0.4,
    ):
        # Initialize component engines
        self.technical = create_unified_intelligence(
            min_confluence_threshold=min_technical_confluence,
        )
        self.fundamental = create_fundamental_intelligence()
        
        # Parameters
        self.min_combined_confidence = min_combined_confidence
        self.technical_weight = technical_weight
        self.fundamental_weight = fundamental_weight
    
    def analyze(
        self,
        symbol: str,
        candles: List[Dict[str, Any]],
        trades: Optional[List[Dict[str, Any]]] = None,
    ) -> CompleteAnalysis:
        """
        Perform complete analysis combining technical and fundamental.
        
        This is the main entry point for institutional-grade analysis.
        """
        import time
        start_time = time.time()
        
        # Run technical analysis
        technical_analysis = self.technical.analyze(
            candles=candles,
            trades=trades,
            symbol=symbol,
        )
        
        # Run fundamental analysis
        fundamental_analysis = self.fundamental.analyze(symbol)
        
        # Generate complete signal
        signal = self._generate_complete_signal(
            technical=technical_analysis,
            fundamental=fundamental_analysis,
            symbol=symbol,
        )
        
        # Calculate overall metrics
        market_quality = self._calculate_market_quality(
            technical=technical_analysis,
            fundamental=fundamental_analysis,
        )
        
        institutional_activity = self._calculate_institutional_activity(
            technical=technical_analysis,
            fundamental=fundamental_analysis,
        )
        
        overall_confidence = self._calculate_overall_confidence(
            signal=signal,
            market_quality=market_quality,
        )
        
        analysis_time_ms = (time.time() - start_time) * 1000
        
        return CompleteAnalysis(
            timestamp=datetime.now(timezone.utc),
            symbol=symbol,
            company_name=fundamental_analysis.company_name,
            current_price=technical_analysis.current_price,
            technical=technical_analysis,
            fundamental=fundamental_analysis,
            signal=signal,
            market_quality=market_quality,
            institutional_activity=institutional_activity,
            overall_confidence=overall_confidence,
            analysis_time_ms=analysis_time_ms,
        )
    
    def _generate_complete_signal(
        self,
        technical: UnifiedAnalysis,
        fundamental: FundamentalAnalysis,
        symbol: str,
    ) -> CompleteSignal:
        """Generate complete signal combining technical and fundamental."""
        factors = []
        warnings = []
        
        # Get technical signal
        tech_signal = technical.signal
        tech_direction = tech_signal.direction
        tech_confidence = tech_signal.confidence
        
        # Get fundamental signal
        fund_bias = fundamental.fundamental_bias
        fund_confidence = fundamental.fundamental_confidence
        
        # Determine confluence
        confluence_type, confluence_score = self._calculate_confluence(
            tech_direction=tech_direction,
            tech_confidence=tech_confidence,
            fund_bias=fund_bias,
            fund_confidence=fund_confidence,
        )
        
        # Add confluence factors
        if confluence_type == ConfluenceType.FULL_CONFLUENCE:
            factors.append("FULL CONFLUENCE: Technical and fundamental strongly agree")
        elif confluence_type == ConfluenceType.PARTIAL_CONFLUENCE:
            factors.append("Partial confluence: Technical and fundamental agree")
        elif confluence_type == ConfluenceType.DIVERGENCE:
            warnings.append("DIVERGENCE: Technical and fundamental disagree")
        elif confluence_type == ConfluenceType.STRONG_DIVERGENCE:
            warnings.append("STRONG DIVERGENCE: Technical and fundamental strongly disagree")
        
        # Determine combined direction
        direction = "wait"
        entry_price = None
        stop_loss = None
        take_profit = None
        risk_reward = None
        
        if confluence_type in [ConfluenceType.FULL_CONFLUENCE, ConfluenceType.PARTIAL_CONFLUENCE]:
            # Both agree - use technical entry
            direction = tech_direction
            entry_price = tech_signal.entry_price
            stop_loss = tech_signal.stop_loss
            take_profit = tech_signal.take_profit
            risk_reward = tech_signal.risk_reward_ratio
            
            if direction == "buy":
                factors.append(f"Technical BUY at ${entry_price:.2f}" if entry_price else "Technical BUY signal")
                factors.append(f"Fundamental BULLISH: {fundamental.reasoning}")
            elif direction == "sell":
                factors.append(f"Technical SELL at ${entry_price:.2f}" if entry_price else "Technical SELL signal")
                factors.append(f"Fundamental BEARISH: {fundamental.reasoning}")
        elif tech_direction != "wait" and confluence_type == ConfluenceType.NEUTRAL:
            # Technical has signal but fundamental is neutral - proceed with caution
            direction = tech_direction
            entry_price = tech_signal.entry_price
            stop_loss = tech_signal.stop_loss
            take_profit = tech_signal.take_profit
            risk_reward = tech_signal.risk_reward_ratio
            warnings.append("Fundamental analysis is neutral - proceed with caution")
        else:
            # Divergence or no signal - wait
            if confluence_type in [ConfluenceType.DIVERGENCE, ConfluenceType.STRONG_DIVERGENCE]:
                warnings.append(f"Technical says {tech_direction.upper()}, Fundamental says {fund_bias.upper()}")
            if tech_direction == "wait":
                warnings.append("No technical entry signal")
        
        # Calculate combined confidence
        if direction != "wait":
            combined_confidence = (
                tech_confidence * self.technical_weight +
                fund_confidence * self.fundamental_weight
            )
            # Boost for full confluence
            if confluence_type == ConfluenceType.FULL_CONFLUENCE:
                combined_confidence = min(1.0, combined_confidence + 0.15)
                factors.append("Confluence boost: +15% confidence")
            # Penalty for divergence
            elif confluence_type == ConfluenceType.DIVERGENCE:
                combined_confidence = max(0.3, combined_confidence - 0.15)
                warnings.append("Divergence penalty: -15% confidence")
            elif confluence_type == ConfluenceType.STRONG_DIVERGENCE:
                combined_confidence = max(0.2, combined_confidence - 0.25)
                warnings.append("Strong divergence penalty: -25% confidence")
        else:
            combined_confidence = 0.0
        
        # Determine signal strength
        strength = self._determine_strength(
            direction=direction,
            confidence=combined_confidence,
            confluence_type=confluence_type,
        )
        
        # Generate reasoning
        reasoning = self._generate_reasoning(
            direction=direction,
            tech_direction=tech_direction,
            fund_bias=fund_bias,
            confluence_type=confluence_type,
            combined_confidence=combined_confidence,
        )
        
        return CompleteSignal(
            timestamp=datetime.now(timezone.utc),
            symbol=symbol,
            current_price=technical.current_price,
            direction=direction,
            strength=strength,
            confidence=combined_confidence,
            entry_price=entry_price,
            stop_loss=stop_loss,
            take_profit=take_profit,
            risk_reward_ratio=risk_reward,
            technical_direction=tech_direction,
            technical_confidence=tech_confidence,
            technical_reasoning=tech_signal.reasoning,
            fundamental_bias=fund_bias,
            fundamental_confidence=fund_confidence,
            fundamental_reasoning=fundamental.reasoning,
            confluence_type=confluence_type,
            confluence_score=confluence_score,
            reasoning=reasoning,
            factors=factors,
            warnings=warnings,
        )
    
    def _calculate_confluence(
        self,
        tech_direction: str,
        tech_confidence: float,
        fund_bias: str,
        fund_confidence: float,
    ) -> Tuple[ConfluenceType, float]:
        """Calculate confluence between technical and fundamental."""
        # Map directions to numeric
        tech_score = 0
        if tech_direction == "buy":
            tech_score = tech_confidence
        elif tech_direction == "sell":
            tech_score = -tech_confidence
        
        fund_score = 0
        if fund_bias == "bullish":
            fund_score = fund_confidence
        elif fund_bias == "bearish":
            fund_score = -fund_confidence
        
        # Calculate agreement
        if tech_score == 0 or fund_score == 0:
            return ConfluenceType.NEUTRAL, 0.5
        
        # Same direction
        if (tech_score > 0 and fund_score > 0) or (tech_score < 0 and fund_score < 0):
            avg_confidence = (abs(tech_score) + abs(fund_score)) / 2
            if avg_confidence > 0.6:
                return ConfluenceType.FULL_CONFLUENCE, avg_confidence
            else:
                return ConfluenceType.PARTIAL_CONFLUENCE, avg_confidence
        
        # Opposite directions
        else:
            avg_confidence = (abs(tech_score) + abs(fund_score)) / 2
            if avg_confidence > 0.6:
                return ConfluenceType.STRONG_DIVERGENCE, 1 - avg_confidence
            else:
                return ConfluenceType.DIVERGENCE, 0.5 - avg_confidence * 0.3
    
    def _determine_strength(
        self,
        direction: str,
        confidence: float,
        confluence_type: ConfluenceType,
    ) -> CompleteSignalStrength:
        """Determine signal strength."""
        if direction == "wait":
            return CompleteSignalStrength.NO_SIGNAL
        
        # Institutional grade requires full confluence and high confidence
        if confluence_type == ConfluenceType.FULL_CONFLUENCE and confidence >= 0.75:
            return CompleteSignalStrength.INSTITUTIONAL_GRADE
        
        if confidence >= 0.80:
            return CompleteSignalStrength.EXTREME
        elif confidence >= 0.70:
            return CompleteSignalStrength.VERY_STRONG
        elif confidence >= 0.60:
            return CompleteSignalStrength.STRONG
        elif confidence >= 0.50:
            return CompleteSignalStrength.MODERATE
        else:
            return CompleteSignalStrength.WEAK
    
    def _generate_reasoning(
        self,
        direction: str,
        tech_direction: str,
        fund_bias: str,
        confluence_type: ConfluenceType,
        combined_confidence: float,
    ) -> str:
        """Generate human-readable reasoning."""
        if direction == "wait":
            if confluence_type in [ConfluenceType.DIVERGENCE, ConfluenceType.STRONG_DIVERGENCE]:
                return f"WAIT: Technical ({tech_direction}) and Fundamental ({fund_bias}) diverge"
            return "WAIT: No clear entry signal"
        
        confluence_str = confluence_type.value.replace("_", " ").upper()
        return (
            f"{direction.upper()}: {confluence_str} - "
            f"Technical {tech_direction.upper()} + Fundamental {fund_bias.upper()} = "
            f"{combined_confidence:.0%} confidence"
        )
    
    def _calculate_market_quality(
        self,
        technical: UnifiedAnalysis,
        fundamental: FundamentalAnalysis,
    ) -> float:
        """Calculate overall market quality."""
        tech_quality = technical.market_quality
        
        # Fundamental quality based on data quality and health
        fund_quality = 0.5
        if fundamental.data_quality == "high":
            fund_quality += 0.2
        elif fundamental.data_quality == "low":
            fund_quality -= 0.2
        
        if fundamental.health_score.overall_health == FundamentalHealth.EXCELLENT:
            fund_quality += 0.2
        elif fundamental.health_score.overall_health == FundamentalHealth.CRITICAL:
            fund_quality -= 0.2
        
        return (tech_quality + fund_quality) / 2
    
    def _calculate_institutional_activity(
        self,
        technical: UnifiedAnalysis,
        fundamental: FundamentalAnalysis,
    ) -> float:
        """Calculate institutional activity level."""
        tech_activity = technical.institutional_activity
        
        # Fundamental institutional signals
        fund_activity = 0.0
        
        # Insider buying is institutional activity
        insider = fundamental.insider_activity
        if insider.insider_signal.value in ["strong_buying", "buying"]:
            fund_activity += 0.3
        elif insider.insider_signal.value in ["strong_selling", "selling"]:
            fund_activity += 0.2  # Selling is also activity
        
        # Large market cap = more institutional coverage
        if fundamental.valuation.market_cap > 100e9:  # >$100B
            fund_activity += 0.2
        elif fundamental.valuation.market_cap > 10e9:  # >$10B
            fund_activity += 0.1
        
        return (tech_activity + fund_activity) / 2
    
    def _calculate_overall_confidence(
        self,
        signal: CompleteSignal,
        market_quality: float,
    ) -> float:
        """Calculate overall confidence."""
        if signal.direction == "wait":
            return 0.0
        
        confidence = signal.confidence
        
        # Adjust for market quality
        confidence *= (0.7 + market_quality * 0.3)
        
        return min(1.0, confidence)


def create_complete_intelligence(
    technical_weight: float = 0.6,
    fundamental_weight: float = 0.4,
) -> CompleteIntelligence:
    """Factory function to create a CompleteIntelligence instance."""
    return CompleteIntelligence(
        technical_weight=technical_weight,
        fundamental_weight=fundamental_weight,
    )
