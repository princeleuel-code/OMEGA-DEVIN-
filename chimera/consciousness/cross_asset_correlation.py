"""
Cross-Asset Correlation Intelligence

This module implements cross-asset correlation analysis - understanding how markets
move together and using that knowledge to predict moves.

Key Capabilities:
1. DXY Impact Analysis - How dollar strength affects forex pairs
2. Bond-Gold Correlation - Yields vs safe haven flows
3. Risk-On/Risk-Off Detection - Market sentiment across assets
4. Intermarket Divergence Signals - When correlations break down
5. Leading Indicator Detection - Which asset moves first

Markets don't move in isolation. Understanding correlations gives you an edge.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple, Any
from enum import Enum
from datetime import datetime, timedelta
import math


class MarketSentiment(Enum):
    """Overall market sentiment"""
    RISK_ON = "risk_on"  # Investors seeking risk
    RISK_OFF = "risk_off"  # Investors seeking safety
    NEUTRAL = "neutral"
    TRANSITIONING = "transitioning"


class CorrelationStrength(Enum):
    """Strength of correlation"""
    STRONG_POSITIVE = "strong_positive"  # > 0.7
    MODERATE_POSITIVE = "moderate_positive"  # 0.3 to 0.7
    WEAK = "weak"  # -0.3 to 0.3
    MODERATE_NEGATIVE = "moderate_negative"  # -0.7 to -0.3
    STRONG_NEGATIVE = "strong_negative"  # < -0.7


class DivergenceType(Enum):
    """Type of intermarket divergence"""
    BULLISH_DIVERGENCE = "bullish_divergence"  # Correlated asset up, this down
    BEARISH_DIVERGENCE = "bearish_divergence"  # Correlated asset down, this up
    CORRELATION_BREAKDOWN = "correlation_breakdown"  # Normal correlation not holding
    NONE = "none"


class AssetClass(Enum):
    """Asset classes"""
    FOREX_MAJOR = "forex_major"
    FOREX_MINOR = "forex_minor"
    FOREX_EXOTIC = "forex_exotic"
    COMMODITY = "commodity"
    INDEX = "index"
    BOND = "bond"
    CRYPTO = "crypto"


@dataclass
class AssetCorrelation:
    """Correlation between two assets"""
    asset1: str
    asset2: str
    correlation: float  # -1 to 1
    strength: CorrelationStrength
    
    # Time-based analysis
    correlation_1h: float
    correlation_4h: float
    correlation_1d: float
    
    # Stability
    is_stable: bool  # Has correlation been consistent?
    stability_score: float  # 0-1
    
    # Current state
    currently_aligned: bool  # Are they moving together as expected?
    divergence: DivergenceType


@dataclass
class DXYImpact:
    """Dollar index impact analysis"""
    dxy_direction: str  # "UP", "DOWN", "FLAT"
    dxy_strength: float  # 0-1
    
    # Impact on pairs
    usd_pairs_impact: Dict[str, str]  # pair -> expected direction
    
    # Current alignment
    pairs_aligned: int
    pairs_diverging: int
    
    # Signal
    signal: str  # "LONG_USD", "SHORT_USD", "NEUTRAL"
    confidence: float


@dataclass
class RiskSentiment:
    """Risk-on/Risk-off sentiment analysis"""
    sentiment: MarketSentiment
    confidence: float
    
    # Indicators
    vix_level: str  # "HIGH", "NORMAL", "LOW"
    gold_flow: str  # "INFLOW", "OUTFLOW", "NEUTRAL"
    jpy_flow: str  # "INFLOW", "OUTFLOW", "NEUTRAL" (safe haven)
    chf_flow: str  # "INFLOW", "OUTFLOW", "NEUTRAL" (safe haven)
    
    # Risk assets
    equities_direction: str
    high_yield_direction: str
    
    # Implications
    favor_risk_currencies: bool  # AUD, NZD, CAD
    favor_safe_havens: bool  # JPY, CHF, USD, Gold


@dataclass
class LeadingIndicator:
    """Asset that leads another"""
    leading_asset: str
    lagging_asset: str
    lead_time_bars: int  # How many bars it leads by
    correlation: float
    confidence: float
    
    # Current signal
    leading_asset_direction: str
    expected_lagging_direction: str
    signal_active: bool


@dataclass
class IntermarketDivergence:
    """Detected intermarket divergence"""
    asset1: str
    asset2: str
    divergence_type: DivergenceType
    
    # Details
    asset1_direction: str
    asset2_direction: str
    expected_relationship: str  # "positive", "negative"
    
    # Significance
    significance: float  # 0-1
    duration_bars: int
    
    # Trading implication
    trade_signal: str  # Which asset to trade
    signal_direction: str
    confidence: float


@dataclass
class CrossAssetAnalysis:
    """Complete cross-asset correlation analysis"""
    # Market sentiment
    risk_sentiment: RiskSentiment
    
    # DXY analysis
    dxy_impact: DXYImpact
    
    # Correlations
    correlations: List[AssetCorrelation]
    strongest_correlation: Optional[AssetCorrelation]
    
    # Leading indicators
    leading_indicators: List[LeadingIndicator]
    active_leads: List[LeadingIndicator]
    
    # Divergences
    divergences: List[IntermarketDivergence]
    significant_divergence: Optional[IntermarketDivergence]
    
    # Signal for target asset
    target_asset: str
    signal: str  # "LONG", "SHORT", "NEUTRAL"
    signal_strength: float
    confidence: float
    
    # Reasoning
    reasoning: List[str]


class CrossAssetCorrelationIntelligence:
    """
    Cross-Asset Correlation Intelligence
    
    Analyzes relationships between markets to generate trading signals.
    
    Key Relationships:
    - DXY vs USD pairs (inverse for EURUSD, GBPUSD; direct for USDJPY)
    - Gold vs USD (typically inverse)
    - Gold vs Real Yields (inverse)
    - Risk currencies (AUD, NZD) vs Risk sentiment
    - Safe havens (JPY, CHF, Gold) vs Risk sentiment
    - Equities vs Risk currencies
    
    This intelligence helps you:
    1. Confirm trades with correlated assets
    2. Spot divergences that signal reversals
    3. Identify leading indicators for your asset
    4. Understand the broader market context
    """
    
    # Known correlations (typical relationships)
    KNOWN_CORRELATIONS = {
        # DXY relationships
        ("DXY", "EURUSD"): -0.95,  # Strong inverse
        ("DXY", "GBPUSD"): -0.85,  # Strong inverse
        ("DXY", "USDJPY"): 0.80,   # Strong positive
        ("DXY", "USDCHF"): 0.85,   # Strong positive
        ("DXY", "AUDUSD"): -0.75,  # Moderate inverse
        ("DXY", "XAUUSD"): -0.70,  # Moderate inverse (Gold)
        
        # Gold relationships
        ("XAUUSD", "USDJPY"): -0.50,  # Both safe havens
        ("XAUUSD", "US10Y"): -0.60,   # Inverse to yields
        
        # Risk currency relationships
        ("AUDUSD", "SPX"): 0.65,   # Risk-on correlation
        ("NZDUSD", "SPX"): 0.60,   # Risk-on correlation
        ("USDJPY", "SPX"): 0.55,   # Risk-on (JPY weakness)
        
        # Forex pair correlations
        ("EURUSD", "GBPUSD"): 0.85,  # Strong positive
        ("AUDUSD", "NZDUSD"): 0.90,  # Very strong positive
        ("EURUSD", "USDCHF"): -0.90, # Strong inverse
    }
    
    # Risk-on currencies
    RISK_ON_CURRENCIES = ["AUD", "NZD", "CAD"]
    
    # Safe haven currencies
    SAFE_HAVEN_CURRENCIES = ["JPY", "CHF", "USD"]
    
    def __init__(self):
        """Initialize Cross-Asset Correlation Intelligence"""
        self.correlation_cache: Dict[Tuple[str, str], float] = {}
        self.price_history: Dict[str, List[float]] = {}
    
    def analyze(
        self,
        target_asset: str,
        target_bars: List[Dict[str, Any]],
        correlated_assets: Optional[Dict[str, List[Dict[str, Any]]]] = None,
        dxy_bars: Optional[List[Dict[str, Any]]] = None,
        gold_bars: Optional[List[Dict[str, Any]]] = None,
        spx_bars: Optional[List[Dict[str, Any]]] = None
    ) -> CrossAssetAnalysis:
        """
        Perform complete cross-asset correlation analysis
        
        Args:
            target_asset: The asset we're analyzing (e.g., "EURUSD")
            target_bars: OHLCV bars for target asset
            correlated_assets: Dict of asset name -> bars for correlated assets
            dxy_bars: Dollar index bars (optional)
            gold_bars: Gold bars (optional)
            spx_bars: S&P 500 bars (optional)
            
        Returns:
            CrossAssetAnalysis with complete correlation analysis
        """
        if len(target_bars) < 20:
            return self._empty_analysis(target_asset)
        
        reasoning = []
        
        # Store price history
        self.price_history[target_asset] = [b["close"] for b in target_bars]
        
        if correlated_assets:
            for asset, bars in correlated_assets.items():
                self.price_history[asset] = [b["close"] for b in bars]
        
        # 1. Analyze DXY impact
        dxy_impact = self._analyze_dxy_impact(target_asset, target_bars, dxy_bars)
        if dxy_impact.signal != "NEUTRAL":
            reasoning.append(f"DXY: {dxy_impact.dxy_direction} -> {dxy_impact.signal} ({dxy_impact.confidence:.0%})")
        
        # 2. Analyze risk sentiment
        risk_sentiment = self._analyze_risk_sentiment(
            target_asset, target_bars, gold_bars, spx_bars, correlated_assets
        )
        reasoning.append(f"Risk Sentiment: {risk_sentiment.sentiment.value} ({risk_sentiment.confidence:.0%})")
        
        # 3. Calculate correlations
        correlations = self._calculate_correlations(target_asset, correlated_assets)
        strongest = max(correlations, key=lambda c: abs(c.correlation)) if correlations else None
        
        if strongest:
            reasoning.append(f"Strongest correlation: {strongest.asset2} ({strongest.correlation:.2f})")
        
        # 4. Detect leading indicators
        leading_indicators = self._detect_leading_indicators(target_asset, correlated_assets)
        active_leads = [l for l in leading_indicators if l.signal_active]
        
        for lead in active_leads:
            reasoning.append(f"Leading indicator: {lead.leading_asset} -> {lead.expected_lagging_direction}")
        
        # 5. Detect divergences
        divergences = self._detect_divergences(target_asset, target_bars, correlations, correlated_assets)
        significant_div = next((d for d in divergences if d.significance > 0.7), None)
        
        if significant_div:
            reasoning.append(f"DIVERGENCE: {significant_div.divergence_type.value} with {significant_div.asset2}")
        
        # 6. Generate signal
        signal, strength, confidence = self._generate_signal(
            target_asset, dxy_impact, risk_sentiment, correlations,
            active_leads, divergences
        )
        
        return CrossAssetAnalysis(
            risk_sentiment=risk_sentiment,
            dxy_impact=dxy_impact,
            correlations=correlations,
            strongest_correlation=strongest,
            leading_indicators=leading_indicators,
            active_leads=active_leads,
            divergences=divergences,
            significant_divergence=significant_div,
            target_asset=target_asset,
            signal=signal,
            signal_strength=strength,
            confidence=confidence,
            reasoning=reasoning
        )
    
    def _analyze_dxy_impact(
        self,
        target_asset: str,
        target_bars: List[Dict[str, Any]],
        dxy_bars: Optional[List[Dict[str, Any]]]
    ) -> DXYImpact:
        """Analyze dollar index impact on target asset"""
        # Determine if target is USD pair
        is_usd_base = target_asset.startswith("USD")
        is_usd_quote = target_asset.endswith("USD") or target_asset in ["EURUSD", "GBPUSD", "AUDUSD", "NZDUSD"]
        
        # Simulate DXY direction if not provided
        if dxy_bars and len(dxy_bars) >= 10:
            dxy_change = (dxy_bars[-1]["close"] - dxy_bars[-10]["close"]) / dxy_bars[-10]["close"]
        else:
            # Infer from USD pairs
            target_change = (target_bars[-1]["close"] - target_bars[-10]["close"]) / target_bars[-10]["close"]
            if is_usd_quote:
                dxy_change = -target_change  # Inverse relationship
            elif is_usd_base:
                dxy_change = target_change  # Direct relationship
            else:
                dxy_change = 0
        
        # Determine DXY direction
        if dxy_change > 0.002:
            dxy_direction = "UP"
            dxy_strength = min(1.0, abs(dxy_change) * 100)
        elif dxy_change < -0.002:
            dxy_direction = "DOWN"
            dxy_strength = min(1.0, abs(dxy_change) * 100)
        else:
            dxy_direction = "FLAT"
            dxy_strength = 0.3
        
        # Calculate expected impact on USD pairs
        usd_pairs_impact = {}
        
        if dxy_direction == "UP":
            usd_pairs_impact = {
                "EURUSD": "DOWN",
                "GBPUSD": "DOWN",
                "AUDUSD": "DOWN",
                "NZDUSD": "DOWN",
                "USDJPY": "UP",
                "USDCHF": "UP",
                "USDCAD": "UP",
                "XAUUSD": "DOWN"
            }
        elif dxy_direction == "DOWN":
            usd_pairs_impact = {
                "EURUSD": "UP",
                "GBPUSD": "UP",
                "AUDUSD": "UP",
                "NZDUSD": "UP",
                "USDJPY": "DOWN",
                "USDCHF": "DOWN",
                "USDCAD": "DOWN",
                "XAUUSD": "UP"
            }
        
        # Check alignment
        pairs_aligned = 0
        pairs_diverging = 0
        
        if target_asset in usd_pairs_impact:
            expected = usd_pairs_impact[target_asset]
            actual_change = (target_bars[-1]["close"] - target_bars[-5]["close"]) / target_bars[-5]["close"]
            actual_direction = "UP" if actual_change > 0 else "DOWN"
            
            if actual_direction == expected:
                pairs_aligned = 1
            else:
                pairs_diverging = 1
        
        # Generate signal
        if dxy_direction == "UP":
            signal = "LONG_USD"
        elif dxy_direction == "DOWN":
            signal = "SHORT_USD"
        else:
            signal = "NEUTRAL"
        
        confidence = dxy_strength * 0.8
        
        return DXYImpact(
            dxy_direction=dxy_direction,
            dxy_strength=dxy_strength,
            usd_pairs_impact=usd_pairs_impact,
            pairs_aligned=pairs_aligned,
            pairs_diverging=pairs_diverging,
            signal=signal,
            confidence=confidence
        )
    
    def _analyze_risk_sentiment(
        self,
        target_asset: str,
        target_bars: List[Dict[str, Any]],
        gold_bars: Optional[List[Dict[str, Any]]],
        spx_bars: Optional[List[Dict[str, Any]]],
        correlated_assets: Optional[Dict[str, List[Dict[str, Any]]]]
    ) -> RiskSentiment:
        """Analyze overall risk sentiment"""
        risk_on_signals = 0
        risk_off_signals = 0
        
        # Analyze gold (safe haven)
        gold_flow = "NEUTRAL"
        if gold_bars and len(gold_bars) >= 10:
            gold_change = (gold_bars[-1]["close"] - gold_bars[-10]["close"]) / gold_bars[-10]["close"]
            if gold_change > 0.005:
                gold_flow = "INFLOW"
                risk_off_signals += 1
            elif gold_change < -0.005:
                gold_flow = "OUTFLOW"
                risk_on_signals += 1
        
        # Analyze equities (risk asset)
        equities_direction = "NEUTRAL"
        if spx_bars and len(spx_bars) >= 10:
            spx_change = (spx_bars[-1]["close"] - spx_bars[-10]["close"]) / spx_bars[-10]["close"]
            if spx_change > 0.005:
                equities_direction = "UP"
                risk_on_signals += 1
            elif spx_change < -0.005:
                equities_direction = "DOWN"
                risk_off_signals += 1
        
        # Analyze JPY (safe haven)
        jpy_flow = "NEUTRAL"
        if correlated_assets and "USDJPY" in correlated_assets:
            jpy_bars = correlated_assets["USDJPY"]
            if len(jpy_bars) >= 10:
                jpy_change = (jpy_bars[-1]["close"] - jpy_bars[-10]["close"]) / jpy_bars[-10]["close"]
                if jpy_change < -0.003:  # USDJPY down = JPY strength = risk off
                    jpy_flow = "INFLOW"
                    risk_off_signals += 1
                elif jpy_change > 0.003:  # USDJPY up = JPY weakness = risk on
                    jpy_flow = "OUTFLOW"
                    risk_on_signals += 1
        
        # Analyze CHF (safe haven)
        chf_flow = "NEUTRAL"
        if correlated_assets and "USDCHF" in correlated_assets:
            chf_bars = correlated_assets["USDCHF"]
            if len(chf_bars) >= 10:
                chf_change = (chf_bars[-1]["close"] - chf_bars[-10]["close"]) / chf_bars[-10]["close"]
                if chf_change < -0.003:  # USDCHF down = CHF strength = risk off
                    chf_flow = "INFLOW"
                    risk_off_signals += 1
                elif chf_change > 0.003:
                    chf_flow = "OUTFLOW"
                    risk_on_signals += 1
        
        # Determine sentiment
        if risk_on_signals > risk_off_signals + 1:
            sentiment = MarketSentiment.RISK_ON
            confidence = min(1.0, (risk_on_signals - risk_off_signals) / 4)
        elif risk_off_signals > risk_on_signals + 1:
            sentiment = MarketSentiment.RISK_OFF
            confidence = min(1.0, (risk_off_signals - risk_on_signals) / 4)
        elif risk_on_signals > 0 and risk_off_signals > 0:
            sentiment = MarketSentiment.TRANSITIONING
            confidence = 0.4
        else:
            sentiment = MarketSentiment.NEUTRAL
            confidence = 0.3
        
        # Determine currency preferences
        favor_risk = sentiment == MarketSentiment.RISK_ON
        favor_safe = sentiment == MarketSentiment.RISK_OFF
        
        return RiskSentiment(
            sentiment=sentiment,
            confidence=confidence,
            vix_level="NORMAL",  # Would need VIX data
            gold_flow=gold_flow,
            jpy_flow=jpy_flow,
            chf_flow=chf_flow,
            equities_direction=equities_direction,
            high_yield_direction="NEUTRAL",
            favor_risk_currencies=favor_risk,
            favor_safe_havens=favor_safe
        )
    
    def _calculate_correlations(
        self,
        target_asset: str,
        correlated_assets: Optional[Dict[str, List[Dict[str, Any]]]]
    ) -> List[AssetCorrelation]:
        """Calculate correlations with other assets"""
        correlations = []
        
        if not correlated_assets:
            # Use known correlations
            for (asset1, asset2), corr in self.KNOWN_CORRELATIONS.items():
                if asset1 == target_asset or asset2 == target_asset:
                    other_asset = asset2 if asset1 == target_asset else asset1
                    
                    strength = self._classify_correlation_strength(corr)
                    
                    correlations.append(AssetCorrelation(
                        asset1=target_asset,
                        asset2=other_asset,
                        correlation=corr if asset1 == target_asset else corr,
                        strength=strength,
                        correlation_1h=corr,
                        correlation_4h=corr,
                        correlation_1d=corr,
                        is_stable=True,
                        stability_score=0.8,
                        currently_aligned=True,
                        divergence=DivergenceType.NONE
                    ))
            return correlations
        
        # Calculate actual correlations
        target_prices = self.price_history.get(target_asset, [])
        
        for asset, bars in correlated_assets.items():
            if len(bars) < 20 or len(target_prices) < 20:
                continue
            
            asset_prices = [b["close"] for b in bars]
            
            # Calculate correlation
            corr = self._pearson_correlation(target_prices[-50:], asset_prices[-50:])
            strength = self._classify_correlation_strength(corr)
            
            # Check if currently aligned
            target_change = (target_prices[-1] - target_prices[-5]) / target_prices[-5]
            asset_change = (asset_prices[-1] - asset_prices[-5]) / asset_prices[-5]
            
            expected_same_direction = corr > 0
            actual_same_direction = (target_change > 0) == (asset_change > 0)
            
            currently_aligned = expected_same_direction == actual_same_direction
            
            # Detect divergence
            if not currently_aligned and abs(corr) > 0.5:
                if target_change < 0 and asset_change > 0 and corr > 0:
                    divergence = DivergenceType.BULLISH_DIVERGENCE
                elif target_change > 0 and asset_change < 0 and corr > 0:
                    divergence = DivergenceType.BEARISH_DIVERGENCE
                else:
                    divergence = DivergenceType.CORRELATION_BREAKDOWN
            else:
                divergence = DivergenceType.NONE
            
            correlations.append(AssetCorrelation(
                asset1=target_asset,
                asset2=asset,
                correlation=corr,
                strength=strength,
                correlation_1h=corr,
                correlation_4h=corr,
                correlation_1d=corr,
                is_stable=True,
                stability_score=0.7,
                currently_aligned=currently_aligned,
                divergence=divergence
            ))
        
        return correlations
    
    def _detect_leading_indicators(
        self,
        target_asset: str,
        correlated_assets: Optional[Dict[str, List[Dict[str, Any]]]]
    ) -> List[LeadingIndicator]:
        """Detect assets that lead the target asset"""
        leading_indicators = []
        
        if not correlated_assets:
            return leading_indicators
        
        target_prices = self.price_history.get(target_asset, [])
        if len(target_prices) < 30:
            return leading_indicators
        
        for asset, bars in correlated_assets.items():
            if len(bars) < 30:
                continue
            
            asset_prices = [b["close"] for b in bars]
            
            # Test different lag periods
            best_lag = 0
            best_corr = 0
            
            for lag in range(1, 6):  # Test 1-5 bar lags
                if len(asset_prices) > lag and len(target_prices) > lag:
                    # Correlate lagged asset with current target
                    lagged_asset = asset_prices[:-lag]
                    current_target = target_prices[lag:]
                    
                    min_len = min(len(lagged_asset), len(current_target))
                    if min_len < 20:
                        continue
                    
                    corr = self._pearson_correlation(
                        lagged_asset[-min_len:],
                        current_target[-min_len:]
                    )
                    
                    if abs(corr) > abs(best_corr):
                        best_corr = corr
                        best_lag = lag
            
            # If significant leading correlation found
            if abs(best_corr) > 0.5 and best_lag > 0:
                # Determine current signal
                asset_change = (asset_prices[-1] - asset_prices[-best_lag]) / asset_prices[-best_lag]
                
                if asset_change > 0.002:
                    leading_direction = "UP"
                    expected_direction = "LONG" if best_corr > 0 else "SHORT"
                elif asset_change < -0.002:
                    leading_direction = "DOWN"
                    expected_direction = "SHORT" if best_corr > 0 else "LONG"
                else:
                    leading_direction = "FLAT"
                    expected_direction = "NEUTRAL"
                
                leading_indicators.append(LeadingIndicator(
                    leading_asset=asset,
                    lagging_asset=target_asset,
                    lead_time_bars=best_lag,
                    correlation=best_corr,
                    confidence=min(1.0, abs(best_corr)),
                    leading_asset_direction=leading_direction,
                    expected_lagging_direction=expected_direction,
                    signal_active=expected_direction != "NEUTRAL"
                ))
        
        return leading_indicators
    
    def _detect_divergences(
        self,
        target_asset: str,
        target_bars: List[Dict[str, Any]],
        correlations: List[AssetCorrelation],
        correlated_assets: Optional[Dict[str, List[Dict[str, Any]]]]
    ) -> List[IntermarketDivergence]:
        """Detect intermarket divergences"""
        divergences = []
        
        for corr in correlations:
            if corr.divergence != DivergenceType.NONE:
                # Calculate significance
                significance = abs(corr.correlation) * (1 - corr.stability_score)
                
                # Determine trade signal
                if corr.divergence == DivergenceType.BULLISH_DIVERGENCE:
                    signal_direction = "LONG"
                elif corr.divergence == DivergenceType.BEARISH_DIVERGENCE:
                    signal_direction = "SHORT"
                else:
                    signal_direction = "NEUTRAL"
                
                divergences.append(IntermarketDivergence(
                    asset1=target_asset,
                    asset2=corr.asset2,
                    divergence_type=corr.divergence,
                    asset1_direction="DOWN" if corr.divergence == DivergenceType.BULLISH_DIVERGENCE else "UP",
                    asset2_direction="UP" if corr.divergence == DivergenceType.BULLISH_DIVERGENCE else "DOWN",
                    expected_relationship="positive" if corr.correlation > 0 else "negative",
                    significance=significance,
                    duration_bars=5,
                    trade_signal=target_asset,
                    signal_direction=signal_direction,
                    confidence=significance
                ))
        
        return divergences
    
    def _generate_signal(
        self,
        target_asset: str,
        dxy_impact: DXYImpact,
        risk_sentiment: RiskSentiment,
        correlations: List[AssetCorrelation],
        active_leads: List[LeadingIndicator],
        divergences: List[IntermarketDivergence]
    ) -> Tuple[str, float, float]:
        """Generate trading signal from cross-asset analysis"""
        long_score = 0.0
        short_score = 0.0
        confidence_factors = []
        
        # DXY impact
        if target_asset in dxy_impact.usd_pairs_impact:
            expected = dxy_impact.usd_pairs_impact[target_asset]
            if expected == "UP":
                long_score += dxy_impact.confidence * 0.3
            elif expected == "DOWN":
                short_score += dxy_impact.confidence * 0.3
            confidence_factors.append(dxy_impact.confidence)
        
        # Risk sentiment
        base_currency = target_asset[:3]
        quote_currency = target_asset[3:6] if len(target_asset) >= 6 else ""
        
        if risk_sentiment.favor_risk_currencies:
            if base_currency in self.RISK_ON_CURRENCIES:
                long_score += risk_sentiment.confidence * 0.25
            if quote_currency in self.RISK_ON_CURRENCIES:
                short_score += risk_sentiment.confidence * 0.25
        
        if risk_sentiment.favor_safe_havens:
            if base_currency in self.SAFE_HAVEN_CURRENCIES:
                long_score += risk_sentiment.confidence * 0.25
            if quote_currency in self.SAFE_HAVEN_CURRENCIES:
                short_score += risk_sentiment.confidence * 0.25
        
        confidence_factors.append(risk_sentiment.confidence)
        
        # Leading indicators
        for lead in active_leads:
            if lead.expected_lagging_direction == "LONG":
                long_score += lead.confidence * 0.2
            elif lead.expected_lagging_direction == "SHORT":
                short_score += lead.confidence * 0.2
            confidence_factors.append(lead.confidence)
        
        # Divergences
        for div in divergences:
            if div.signal_direction == "LONG":
                long_score += div.confidence * 0.25
            elif div.signal_direction == "SHORT":
                short_score += div.confidence * 0.25
            confidence_factors.append(div.confidence)
        
        # Determine signal
        if long_score > short_score + 0.1:
            signal = "LONG"
            strength = min(1.0, long_score)
        elif short_score > long_score + 0.1:
            signal = "SHORT"
            strength = min(1.0, short_score)
        else:
            signal = "NEUTRAL"
            strength = 0.5
        
        # Calculate confidence
        confidence = sum(confidence_factors) / len(confidence_factors) if confidence_factors else 0.5
        
        return signal, strength, confidence
    
    def _pearson_correlation(self, x: List[float], y: List[float]) -> float:
        """Calculate Pearson correlation coefficient"""
        n = min(len(x), len(y))
        if n < 2:
            return 0.0
        
        x = x[-n:]
        y = y[-n:]
        
        mean_x = sum(x) / n
        mean_y = sum(y) / n
        
        numerator = sum((x[i] - mean_x) * (y[i] - mean_y) for i in range(n))
        
        sum_sq_x = sum((xi - mean_x) ** 2 for xi in x)
        sum_sq_y = sum((yi - mean_y) ** 2 for yi in y)
        
        denominator = math.sqrt(sum_sq_x * sum_sq_y)
        
        if denominator == 0:
            return 0.0
        
        return numerator / denominator
    
    def _classify_correlation_strength(self, corr: float) -> CorrelationStrength:
        """Classify correlation strength"""
        if corr > 0.7:
            return CorrelationStrength.STRONG_POSITIVE
        elif corr > 0.3:
            return CorrelationStrength.MODERATE_POSITIVE
        elif corr > -0.3:
            return CorrelationStrength.WEAK
        elif corr > -0.7:
            return CorrelationStrength.MODERATE_NEGATIVE
        else:
            return CorrelationStrength.STRONG_NEGATIVE
    
    def _empty_analysis(self, target_asset: str) -> CrossAssetAnalysis:
        """Return empty analysis when insufficient data"""
        return CrossAssetAnalysis(
            risk_sentiment=RiskSentiment(
                sentiment=MarketSentiment.NEUTRAL,
                confidence=0.0,
                vix_level="NORMAL",
                gold_flow="NEUTRAL",
                jpy_flow="NEUTRAL",
                chf_flow="NEUTRAL",
                equities_direction="NEUTRAL",
                high_yield_direction="NEUTRAL",
                favor_risk_currencies=False,
                favor_safe_havens=False
            ),
            dxy_impact=DXYImpact(
                dxy_direction="FLAT",
                dxy_strength=0.0,
                usd_pairs_impact={},
                pairs_aligned=0,
                pairs_diverging=0,
                signal="NEUTRAL",
                confidence=0.0
            ),
            correlations=[],
            strongest_correlation=None,
            leading_indicators=[],
            active_leads=[],
            divergences=[],
            significant_divergence=None,
            target_asset=target_asset,
            signal="NEUTRAL",
            signal_strength=0.0,
            confidence=0.0,
            reasoning=["Insufficient data for cross-asset analysis"]
        )


def test_cross_asset_correlation():
    """Test the Cross-Asset Correlation Intelligence"""
    print("=" * 80)
    print("CROSS-ASSET CORRELATION INTELLIGENCE TEST")
    print("=" * 80)
    
    # Generate sample data
    import random
    
    def generate_bars(base_price: float, trend: float = 0) -> List[Dict[str, Any]]:
        bars = []
        price = base_price
        for i in range(100):
            change = random.uniform(-0.002, 0.002) + trend
            price = price * (1 + change)
            bars.append({
                "open": price,
                "high": price * (1 + random.uniform(0, 0.001)),
                "low": price * (1 - random.uniform(0, 0.001)),
                "close": price,
                "volume": random.uniform(1000, 5000)
            })
        return bars
    
    # Generate correlated data
    eurusd_bars = generate_bars(1.1000, trend=0.0002)  # Slight uptrend
    gbpusd_bars = generate_bars(1.2700, trend=0.0001)  # Correlated with EURUSD
    usdjpy_bars = generate_bars(150.00, trend=-0.0001)  # Inverse to EURUSD
    gold_bars = generate_bars(2000.00, trend=0.0001)  # Safe haven
    
    # Create analyzer
    analyzer = CrossAssetCorrelationIntelligence()
    
    # Analyze
    analysis = analyzer.analyze(
        target_asset="EURUSD",
        target_bars=eurusd_bars,
        correlated_assets={
            "GBPUSD": gbpusd_bars,
            "USDJPY": usdjpy_bars
        },
        gold_bars=gold_bars
    )
    
    # Print results
    print(f"\nTarget Asset: {analysis.target_asset}")
    print(f"\nRisk Sentiment: {analysis.risk_sentiment.sentiment.value}")
    print(f"  Confidence: {analysis.risk_sentiment.confidence:.0%}")
    print(f"  Gold Flow: {analysis.risk_sentiment.gold_flow}")
    print(f"  JPY Flow: {analysis.risk_sentiment.jpy_flow}")
    
    print(f"\nDXY Impact:")
    print(f"  Direction: {analysis.dxy_impact.dxy_direction}")
    print(f"  Signal: {analysis.dxy_impact.signal}")
    
    print(f"\nCorrelations:")
    for corr in analysis.correlations:
        print(f"  {corr.asset2}: {corr.correlation:.2f} ({corr.strength.value})")
        if corr.divergence != DivergenceType.NONE:
            print(f"    DIVERGENCE: {corr.divergence.value}")
    
    print(f"\nLeading Indicators:")
    for lead in analysis.leading_indicators:
        print(f"  {lead.leading_asset} leads by {lead.lead_time_bars} bars (corr: {lead.correlation:.2f})")
        if lead.signal_active:
            print(f"    ACTIVE: Expecting {lead.expected_lagging_direction}")
    
    print(f"\nSIGNAL: {analysis.signal}")
    print(f"Signal Strength: {analysis.signal_strength:.0%}")
    print(f"Confidence: {analysis.confidence:.0%}")
    
    print("\nREASONING:")
    for reason in analysis.reasoning:
        print(f"  - {reason}")
    
    print("\nTest completed successfully!")


if __name__ == "__main__":
    test_cross_asset_correlation()
