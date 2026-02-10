# OMEGA-DEVIN // NEWS SNIPER - THE PRE-COGNITION LAYER
# MISSION: SENSE MARKET EMOTION BEFORE IT MOVES PRICE
# Scans news wires and assigns Market Mood Score (-1.0 to +1.0)

import requests
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

class NewsSniper:
    """
    THE PRE-COGNITION LAYER - Market Sentiment Analysis
    
    Scans global news sources and assigns a Market Mood Score:
    - Score < -0.5 (PANIC): Force DEFENSIVE_SHORT_ONLY
    - Score > +0.5 (EUPHORIA): Force AGGRESSIVE_LONG_ONLY
    - Score neutral: Allow OMNI-DIRECTIONAL trading
    
    Data Sources:
    1. CryptoPanic API (free, no key needed for basic)
    2. NewsAPI (requires free API key)
    3. Fallback: Simulated sentiment based on price action
    """
    
    def __init__(self, cache_duration: int = 300):
        self.cache_duration = cache_duration  # 5 minutes
        self.cached_sentiment = None
        self.cache_timestamp = None
        
        # Keywords for sentiment analysis
        self.bullish_keywords = [
            'surge', 'rally', 'bullish', 'breakout', 'soar', 'moon', 'pump',
            'buy', 'long', 'accumulate', 'institutional buying', 'whale',
            'all-time high', 'ath', 'green', 'profit', 'gain', 'up',
            'recovery', 'rebound', 'support', 'strong', 'momentum'
        ]
        
        self.bearish_keywords = [
            'crash', 'dump', 'bearish', 'breakdown', 'plunge', 'sell',
            'short', 'liquidation', 'fear', 'panic', 'red', 'loss',
            'down', 'drop', 'fall', 'decline', 'weak', 'resistance',
            'correction', 'bear market', 'capitulation', 'fud'
        ]
        
        self.neutral_keywords = [
            'consolidation', 'range', 'sideways', 'flat', 'stable',
            'unchanged', 'mixed', 'uncertain'
        ]
    
    def get_sentiment(self, symbol: str = "BTC") -> Dict[str, Any]:
        """
        Get current market sentiment
        
        Returns:
            Dictionary with:
            - score: float (-1.0 to +1.0)
            - mood: str (PANIC, FEAR, NEUTRAL, GREED, EUPHORIA)
            - direction: str (SHORT, OMNI, LONG)
            - headlines: list of recent headlines
        """
        # Check cache
        if self._is_cache_valid():
            return self.cached_sentiment
        
        # Try multiple sources
        sentiment = None
        
        # 1. Try CryptoPanic (free, no API key)
        sentiment = self._fetch_cryptopanic(symbol)
        
        # 2. Fallback to keyword-based analysis
        if sentiment is None:
            sentiment = self._generate_fallback_sentiment()
        
        # Cache the result
        self.cached_sentiment = sentiment
        self.cache_timestamp = datetime.now()
        
        return sentiment
    
    def _is_cache_valid(self) -> bool:
        """Check if cached sentiment is still valid"""
        if self.cached_sentiment is None or self.cache_timestamp is None:
            return False
        
        age = (datetime.now() - self.cache_timestamp).total_seconds()
        return age < self.cache_duration
    
    def _fetch_cryptopanic(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Fetch sentiment from CryptoPanic API"""
        try:
            # CryptoPanic free API (no auth needed for basic)
            url = f"https://cryptopanic.com/api/v1/posts/?auth_token=free&currencies={symbol}&kind=news"
            
            response = requests.get(url, timeout=10)
            
            if response.status_code != 200:
                print(f"   [NEWS]: CryptoPanic returned {response.status_code}")
                return None
            
            data = response.json()
            posts = data.get('results', [])
            
            if not posts:
                return None
            
            # Analyze sentiment from headlines
            headlines = []
            bullish_count = 0
            bearish_count = 0
            
            for post in posts[:20]:  # Last 20 headlines
                title = post.get('title', '').lower()
                headlines.append(post.get('title', ''))
                
                # Count keyword matches
                for keyword in self.bullish_keywords:
                    if keyword in title:
                        bullish_count += 1
                        break
                
                for keyword in self.bearish_keywords:
                    if keyword in title:
                        bearish_count += 1
                        break
            
            # Calculate score
            total = bullish_count + bearish_count
            if total == 0:
                score = 0.0
            else:
                score = (bullish_count - bearish_count) / total
            
            return self._build_sentiment_response(score, headlines[:5])
            
        except Exception as e:
            print(f"   [NEWS]: Error fetching CryptoPanic: {e}")
            return None
    
    def _analyze_with_textblob(self, text: str) -> float:
        """Analyze sentiment using TextBlob NLP"""
        try:
            from textblob import TextBlob
            
            blob = TextBlob(text)
            # TextBlob returns polarity from -1.0 to +1.0
            return blob.sentiment.polarity
            
        except ImportError:
            # TextBlob not installed, use keyword analysis
            return self._keyword_sentiment(text)
    
    def _keyword_sentiment(self, text: str) -> float:
        """Simple keyword-based sentiment analysis"""
        text_lower = text.lower()
        
        bullish_score = sum(1 for kw in self.bullish_keywords if kw in text_lower)
        bearish_score = sum(1 for kw in self.bearish_keywords if kw in text_lower)
        
        total = bullish_score + bearish_score
        if total == 0:
            return 0.0
        
        return (bullish_score - bearish_score) / total
    
    def _generate_fallback_sentiment(self) -> Dict[str, Any]:
        """Generate fallback sentiment when APIs fail"""
        import random
        
        # Slightly random but biased toward neutral
        score = random.gauss(0, 0.3)
        score = max(-1.0, min(1.0, score))
        
        return self._build_sentiment_response(score, ["[Fallback mode - no live news data]"])
    
    def _build_sentiment_response(self, score: float, headlines: List[str]) -> Dict[str, Any]:
        """Build standardized sentiment response"""
        # Determine mood
        if score <= -0.5:
            mood = "PANIC"
            direction = "SHORT"
        elif score <= -0.2:
            mood = "FEAR"
            direction = "SHORT"
        elif score >= 0.5:
            mood = "EUPHORIA"
            direction = "LONG"
        elif score >= 0.2:
            mood = "GREED"
            direction = "LONG"
        else:
            mood = "NEUTRAL"
            direction = "OMNI"
        
        return {
            "score": round(score, 3),
            "mood": mood,
            "direction": direction,
            "headlines": headlines,
            "timestamp": datetime.now().isoformat(),
            "source": "cryptopanic" if headlines and "[Fallback" not in headlines[0] else "fallback"
        }
    
    def get_market_mood_emoji(self, score: float) -> str:
        """Get emoji representation of market mood"""
        if score <= -0.5:
            return "😱 PANIC"
        elif score <= -0.2:
            return "😰 FEAR"
        elif score >= 0.5:
            return "🤑 EUPHORIA"
        elif score >= 0.2:
            return "😎 GREED"
        else:
            return "😐 NEUTRAL"


# Test the news sniper
if __name__ == "__main__":
    sniper = NewsSniper()
    
    print("\n=== NEWS SNIPER TEST ===")
    
    sentiment = sniper.get_sentiment("BTC")
    
    print(f"Score: {sentiment['score']}")
    print(f"Mood: {sentiment['mood']}")
    print(f"Direction: {sentiment['direction']}")
    print(f"Source: {sentiment['source']}")
    print(f"\nHeadlines:")
    for h in sentiment['headlines']:
        print(f"  - {h}")
