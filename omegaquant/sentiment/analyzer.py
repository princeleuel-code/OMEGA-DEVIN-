"""
Sentiment Analyzer

Analyzes text (news headlines, social media posts) to determine market sentiment.
Uses rule-based analysis with optional transformer model integration.

Key Features:
- Financial-specific sentiment lexicon
- Confidence scoring
- Integration with veto cascade via reason codes
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class MarketSentiment(Enum):
    """Market sentiment classification."""
    VERY_BEARISH = -2
    BEARISH = -1
    NEUTRAL = 0
    BULLISH = 1
    VERY_BULLISH = 2


@dataclass
class SentimentConfig:
    """Configuration for sentiment analysis."""
    # Thresholds for sentiment classification
    very_bullish_threshold: float = 0.6
    bullish_threshold: float = 0.2
    bearish_threshold: float = -0.2
    very_bearish_threshold: float = -0.6
    
    # Time decay for news relevance (hours)
    news_decay_hours: float = 4.0
    
    # Minimum confidence to influence trading
    min_confidence: float = 0.5
    
    # Weight for different sources
    source_weights: Dict[str, float] = field(default_factory=lambda: {
        "reuters": 1.0,
        "bloomberg": 1.0,
        "wsj": 0.9,
        "twitter": 0.5,
        "reddit": 0.4,
        "unknown": 0.3,
    })
    
    # Keywords that indicate high-impact news
    high_impact_keywords: List[str] = field(default_factory=lambda: [
        "fed", "fomc", "rate", "inflation", "cpi", "gdp", "employment",
        "nonfarm", "payroll", "central bank", "ecb", "boj", "rba",
        "interest rate", "monetary policy", "quantitative", "tapering",
    ])


@dataclass
class SentimentResult:
    """Result of sentiment analysis."""
    score: float  # -1.0 to 1.0
    sentiment: MarketSentiment
    confidence: float  # 0.0 to 1.0
    is_high_impact: bool
    keywords_found: List[str]
    source: str
    timestamp: datetime
    reason_codes: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "score": self.score,
            "sentiment": self.sentiment.name,
            "confidence": self.confidence,
            "is_high_impact": self.is_high_impact,
            "keywords_found": self.keywords_found,
            "source": self.source,
            "timestamp": self.timestamp.isoformat(),
            "reason_codes": self.reason_codes,
        }


class SentimentAnalyzer:
    """
    Analyzes market sentiment from text data.
    
    Uses a financial-specific lexicon for rule-based sentiment analysis.
    Can be extended to use transformer models (FinBERT, etc.) when available.
    """
    
    # Financial sentiment lexicon (word -> score)
    BULLISH_WORDS = {
        # Strong bullish
        "surge": 0.8, "soar": 0.8, "rally": 0.7, "boom": 0.8, "breakout": 0.7,
        "bullish": 0.9, "optimistic": 0.6, "growth": 0.5, "gain": 0.5, "profit": 0.5,
        "beat": 0.6, "exceed": 0.5, "outperform": 0.6, "upgrade": 0.6, "buy": 0.4,
        "strong": 0.4, "positive": 0.4, "recovery": 0.5, "rebound": 0.6, "upside": 0.5,
        "momentum": 0.4, "expansion": 0.5, "accelerate": 0.5, "improve": 0.4,
        # Moderate bullish
        "rise": 0.3, "increase": 0.3, "up": 0.2, "higher": 0.3, "advance": 0.3,
        "support": 0.2, "stable": 0.2, "steady": 0.2, "confident": 0.3,
    }
    
    BEARISH_WORDS = {
        # Strong bearish
        "crash": -0.9, "plunge": -0.8, "collapse": -0.9, "crisis": -0.8, "panic": -0.8,
        "bearish": -0.9, "pessimistic": -0.6, "recession": -0.7, "loss": -0.5, "deficit": -0.5,
        "miss": -0.6, "disappoint": -0.6, "underperform": -0.6, "downgrade": -0.6, "sell": -0.4,
        "weak": -0.4, "negative": -0.4, "decline": -0.5, "drop": -0.5, "downside": -0.5,
        "slowdown": -0.5, "contraction": -0.5, "decelerate": -0.5, "worsen": -0.5,
        # Moderate bearish
        "fall": -0.3, "decrease": -0.3, "down": -0.2, "lower": -0.3, "retreat": -0.3,
        "resistance": -0.2, "volatile": -0.3, "uncertain": -0.3, "concern": -0.3,
        "risk": -0.2, "warning": -0.4, "caution": -0.3,
    }
    
    # Negation words that flip sentiment
    NEGATION_WORDS = {"not", "no", "never", "neither", "nobody", "nothing", "nowhere",
                      "hardly", "barely", "scarcely", "doesn't", "don't", "didn't",
                      "won't", "wouldn't", "couldn't", "shouldn't", "isn't", "aren't"}
    
    # Intensifiers that amplify sentiment
    INTENSIFIERS = {"very": 1.5, "extremely": 2.0, "highly": 1.5, "significantly": 1.5,
                    "substantially": 1.5, "sharply": 1.5, "dramatically": 1.8,
                    "slightly": 0.5, "marginally": 0.5, "somewhat": 0.7}
    
    def __init__(self, config: Optional[SentimentConfig] = None):
        self.config = config or SentimentConfig()
        self._sentiment_cache: Dict[str, SentimentResult] = {}
        logger.info("SentimentAnalyzer initialized")
    
    def analyze(
        self,
        text: str,
        source: str = "unknown",
        timestamp: Optional[datetime] = None,
    ) -> SentimentResult:
        """
        Analyze sentiment of a text.
        
        Args:
            text: Text to analyze (headline, tweet, etc.)
            source: Source of the text (reuters, twitter, etc.)
            timestamp: When the text was published
            
        Returns:
            SentimentResult with score, classification, and metadata
        """
        timestamp = timestamp or datetime.utcnow()
        
        # Check cache
        cache_key = f"{text}:{source}"
        if cache_key in self._sentiment_cache:
            cached = self._sentiment_cache[cache_key]
            # Return cached if still fresh
            if (datetime.utcnow() - cached.timestamp).total_seconds() < 3600:
                return cached
        
        # Preprocess text
        text_lower = text.lower()
        words = re.findall(r'\b\w+\b', text_lower)
        
        # Calculate sentiment score
        score, keywords_found = self._calculate_score(words)
        
        # Check for high-impact news
        is_high_impact = self._check_high_impact(text_lower)
        
        # Calculate confidence based on keyword coverage and source
        confidence = self._calculate_confidence(words, keywords_found, source)
        
        # Classify sentiment
        sentiment = self._classify_sentiment(score)
        
        # Generate reason codes
        reason_codes = self._generate_reason_codes(sentiment, confidence, is_high_impact)
        
        result = SentimentResult(
            score=score,
            sentiment=sentiment,
            confidence=confidence,
            is_high_impact=is_high_impact,
            keywords_found=keywords_found,
            source=source,
            timestamp=timestamp,
            reason_codes=reason_codes,
        )
        
        # Cache result
        self._sentiment_cache[cache_key] = result
        
        return result
    
    def _calculate_score(self, words: List[str]) -> Tuple[float, List[str]]:
        """Calculate sentiment score from words."""
        total_score = 0.0
        keywords_found = []
        
        i = 0
        while i < len(words):
            word = words[i]
            
            # Check for negation in previous words
            negated = False
            if i > 0 and words[i - 1] in self.NEGATION_WORDS:
                negated = True
            
            # Check for intensifier in previous word
            intensifier = 1.0
            if i > 0 and words[i - 1] in self.INTENSIFIERS:
                intensifier = self.INTENSIFIERS[words[i - 1]]
            
            # Check bullish words
            if word in self.BULLISH_WORDS:
                word_score = self.BULLISH_WORDS[word] * intensifier
                if negated:
                    word_score = -word_score * 0.5  # Negation flips and reduces
                total_score += word_score
                keywords_found.append(word)
            
            # Check bearish words
            elif word in self.BEARISH_WORDS:
                word_score = self.BEARISH_WORDS[word] * intensifier
                if negated:
                    word_score = -word_score * 0.5
                total_score += word_score
                keywords_found.append(word)
            
            i += 1
        
        # Normalize score to [-1, 1]
        if keywords_found:
            score = max(-1.0, min(1.0, total_score / len(keywords_found)))
        else:
            score = 0.0
        
        return score, keywords_found
    
    def _check_high_impact(self, text: str) -> bool:
        """Check if text contains high-impact keywords."""
        for keyword in self.config.high_impact_keywords:
            if keyword in text:
                return True
        return False
    
    def _calculate_confidence(
        self,
        words: List[str],
        keywords_found: List[str],
        source: str,
    ) -> float:
        """Calculate confidence in the sentiment analysis."""
        if not words:
            return 0.0
        
        # Base confidence from keyword coverage
        keyword_ratio = len(keywords_found) / max(len(words), 1)
        base_confidence = min(1.0, keyword_ratio * 5)  # Scale up
        
        # Adjust by source weight
        source_weight = self.config.source_weights.get(source.lower(), 0.3)
        
        # Final confidence
        confidence = base_confidence * source_weight
        
        return min(1.0, max(0.0, confidence))
    
    def _classify_sentiment(self, score: float) -> MarketSentiment:
        """Classify sentiment based on score."""
        if score >= self.config.very_bullish_threshold:
            return MarketSentiment.VERY_BULLISH
        elif score >= self.config.bullish_threshold:
            return MarketSentiment.BULLISH
        elif score <= self.config.very_bearish_threshold:
            return MarketSentiment.VERY_BEARISH
        elif score <= self.config.bearish_threshold:
            return MarketSentiment.BEARISH
        else:
            return MarketSentiment.NEUTRAL
    
    def _generate_reason_codes(
        self,
        sentiment: MarketSentiment,
        confidence: float,
        is_high_impact: bool,
    ) -> List[str]:
        """Generate reason codes for the sentiment result."""
        codes = []
        
        # Sentiment code
        codes.append(f"SENTIMENT_{sentiment.name}")
        
        # Confidence code
        if confidence >= 0.8:
            codes.append("SENTIMENT_HIGH_CONFIDENCE")
        elif confidence >= 0.5:
            codes.append("SENTIMENT_MEDIUM_CONFIDENCE")
        else:
            codes.append("SENTIMENT_LOW_CONFIDENCE")
        
        # High impact code
        if is_high_impact:
            codes.append("SENTIMENT_HIGH_IMPACT_NEWS")
        
        return codes
    
    def analyze_batch(
        self,
        texts: List[Tuple[str, str, Optional[datetime]]],
    ) -> List[SentimentResult]:
        """
        Analyze multiple texts.
        
        Args:
            texts: List of (text, source, timestamp) tuples
            
        Returns:
            List of SentimentResult objects
        """
        return [self.analyze(text, source, ts) for text, source, ts in texts]
    
    def get_aggregate_sentiment(
        self,
        results: List[SentimentResult],
        decay_hours: Optional[float] = None,
    ) -> SentimentResult:
        """
        Aggregate multiple sentiment results into one.
        
        Uses time-weighted averaging with exponential decay.
        
        Args:
            results: List of sentiment results to aggregate
            decay_hours: Hours for half-life decay (default from config)
            
        Returns:
            Aggregated SentimentResult
        """
        if not results:
            return SentimentResult(
                score=0.0,
                sentiment=MarketSentiment.NEUTRAL,
                confidence=0.0,
                is_high_impact=False,
                keywords_found=[],
                source="aggregate",
                timestamp=datetime.utcnow(),
                reason_codes=["SENTIMENT_NO_DATA"],
            )
        
        decay_hours = decay_hours or self.config.news_decay_hours
        now = datetime.utcnow()
        
        weighted_score = 0.0
        total_weight = 0.0
        all_keywords = []
        any_high_impact = False
        
        for result in results:
            # Calculate time decay weight
            age_hours = (now - result.timestamp).total_seconds() / 3600
            time_weight = 0.5 ** (age_hours / decay_hours)
            
            # Combine with confidence
            weight = time_weight * result.confidence
            
            weighted_score += result.score * weight
            total_weight += weight
            all_keywords.extend(result.keywords_found)
            
            if result.is_high_impact:
                any_high_impact = True
        
        # Calculate aggregate score
        if total_weight > 0:
            agg_score = weighted_score / total_weight
            agg_confidence = min(1.0, total_weight / len(results))
        else:
            agg_score = 0.0
            agg_confidence = 0.0
        
        sentiment = self._classify_sentiment(agg_score)
        reason_codes = self._generate_reason_codes(sentiment, agg_confidence, any_high_impact)
        reason_codes.append(f"SENTIMENT_AGGREGATE_N={len(results)}")
        
        return SentimentResult(
            score=agg_score,
            sentiment=sentiment,
            confidence=agg_confidence,
            is_high_impact=any_high_impact,
            keywords_found=list(set(all_keywords)),
            source="aggregate",
            timestamp=now,
            reason_codes=reason_codes,
        )
    
    def should_veto_trade(
        self,
        sentiment: SentimentResult,
        trade_direction: str,  # "long" or "short"
    ) -> Tuple[bool, List[str]]:
        """
        Determine if sentiment should veto a trade.
        
        Args:
            sentiment: Current sentiment result
            trade_direction: Direction of proposed trade
            
        Returns:
            Tuple of (should_veto, reason_codes)
        """
        reason_codes = []
        
        # Low confidence - don't veto but note it
        if sentiment.confidence < self.config.min_confidence:
            reason_codes.append("SENTIMENT_LOW_CONFIDENCE_NO_VETO")
            return False, reason_codes
        
        # High impact news pending - always veto
        if sentiment.is_high_impact:
            reason_codes.append("VETO_HIGH_IMPACT_NEWS")
            return True, reason_codes
        
        # Check sentiment vs trade direction
        if trade_direction == "long":
            if sentiment.sentiment == MarketSentiment.VERY_BEARISH:
                reason_codes.append("VETO_SENTIMENT_VERY_BEARISH")
                return True, reason_codes
            elif sentiment.sentiment == MarketSentiment.BEARISH and sentiment.confidence > 0.7:
                reason_codes.append("VETO_SENTIMENT_BEARISH_HIGH_CONF")
                return True, reason_codes
        
        elif trade_direction == "short":
            if sentiment.sentiment == MarketSentiment.VERY_BULLISH:
                reason_codes.append("VETO_SENTIMENT_VERY_BULLISH")
                return True, reason_codes
            elif sentiment.sentiment == MarketSentiment.BULLISH and sentiment.confidence > 0.7:
                reason_codes.append("VETO_SENTIMENT_BULLISH_HIGH_CONF")
                return True, reason_codes
        
        # No veto
        reason_codes.append("SENTIMENT_ALIGNED")
        return False, reason_codes
    
    def clear_cache(self) -> None:
        """Clear the sentiment cache."""
        self._sentiment_cache.clear()
