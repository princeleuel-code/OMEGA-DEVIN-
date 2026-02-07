"""
Sentiment Analysis Module

NLP-based sentiment analysis for market news and social media.
Provides market mood indicators to influence trading decisions.
"""

from omegaquant.sentiment.analyzer import (
    SentimentAnalyzer,
    SentimentResult,
    SentimentConfig,
    MarketSentiment,
)
from omegaquant.sentiment.news_loader import (
    NewsLoader,
    NewsItem,
    NewsSource,
)

__all__ = [
    "SentimentAnalyzer",
    "SentimentResult", 
    "SentimentConfig",
    "MarketSentiment",
    "NewsLoader",
    "NewsItem",
    "NewsSource",
]
