"""
News Loader

Fetches and manages news data from various sources.
Provides a unified interface for news ingestion.

Note: This is a framework implementation. For production use,
you would integrate with actual news APIs (Reuters, Bloomberg, etc.)
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional
import json

logger = logging.getLogger(__name__)


class NewsSource(Enum):
    """Supported news sources."""
    REUTERS = "reuters"
    BLOOMBERG = "bloomberg"
    WSJ = "wsj"
    TWITTER = "twitter"
    REDDIT = "reddit"
    ECONOMIC_CALENDAR = "economic_calendar"
    CUSTOM = "custom"


@dataclass
class NewsItem:
    """A single news item."""
    headline: str
    source: NewsSource
    timestamp: datetime
    url: Optional[str] = None
    body: Optional[str] = None
    symbols: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    importance: str = "normal"  # low, normal, high, critical
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "headline": self.headline,
            "source": self.source.value,
            "timestamp": self.timestamp.isoformat(),
            "url": self.url,
            "body": self.body,
            "symbols": self.symbols,
            "tags": self.tags,
            "importance": self.importance,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "NewsItem":
        return cls(
            headline=data["headline"],
            source=NewsSource(data["source"]),
            timestamp=datetime.fromisoformat(data["timestamp"]),
            url=data.get("url"),
            body=data.get("body"),
            symbols=data.get("symbols", []),
            tags=data.get("tags", []),
            importance=data.get("importance", "normal"),
        )


@dataclass
class EconomicEvent:
    """An economic calendar event."""
    name: str
    timestamp: datetime
    currency: str
    importance: str  # low, medium, high
    actual: Optional[float] = None
    forecast: Optional[float] = None
    previous: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "timestamp": self.timestamp.isoformat(),
            "currency": self.currency,
            "importance": self.importance,
            "actual": self.actual,
            "forecast": self.forecast,
            "previous": self.previous,
        }


class NewsLoader:
    """
    Loads and manages news data.
    
    This is a framework implementation that can be extended
    to integrate with actual news APIs.
    """
    
    # Sample economic events for demonstration
    SAMPLE_EVENTS = [
        ("FOMC Interest Rate Decision", "USD", "high"),
        ("Non-Farm Payrolls", "USD", "high"),
        ("CPI (Consumer Price Index)", "USD", "high"),
        ("GDP Growth Rate", "USD", "medium"),
        ("Unemployment Rate", "USD", "medium"),
        ("ECB Interest Rate Decision", "EUR", "high"),
        ("BOJ Interest Rate Decision", "JPY", "high"),
        ("BOE Interest Rate Decision", "GBP", "high"),
        ("Retail Sales", "USD", "medium"),
        ("PMI Manufacturing", "USD", "medium"),
    ]
    
    def __init__(self, cache_hours: float = 24.0):
        self.cache_hours = cache_hours
        self._news_cache: List[NewsItem] = []
        self._events_cache: List[EconomicEvent] = []
        self._last_fetch: Optional[datetime] = None
        logger.info("NewsLoader initialized")
    
    def add_news(self, item: NewsItem) -> None:
        """Add a news item to the cache."""
        self._news_cache.append(item)
        # Keep cache sorted by timestamp
        self._news_cache.sort(key=lambda x: x.timestamp, reverse=True)
        # Trim old news
        self._trim_cache()
    
    def add_news_batch(self, items: List[NewsItem]) -> None:
        """Add multiple news items."""
        for item in items:
            self._news_cache.append(item)
        self._news_cache.sort(key=lambda x: x.timestamp, reverse=True)
        self._trim_cache()
    
    def _trim_cache(self) -> None:
        """Remove old news from cache."""
        cutoff = datetime.utcnow() - timedelta(hours=self.cache_hours)
        self._news_cache = [n for n in self._news_cache if n.timestamp > cutoff]
    
    def get_recent_news(
        self,
        hours: float = 4.0,
        source: Optional[NewsSource] = None,
        symbols: Optional[List[str]] = None,
        min_importance: str = "normal",
    ) -> List[NewsItem]:
        """
        Get recent news items.
        
        Args:
            hours: How far back to look
            source: Filter by source
            symbols: Filter by symbols (e.g., ["EURUSD", "EUR", "USD"])
            min_importance: Minimum importance level
            
        Returns:
            List of matching news items
        """
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        importance_order = {"low": 0, "normal": 1, "high": 2, "critical": 3}
        min_imp_value = importance_order.get(min_importance, 1)
        
        results = []
        for item in self._news_cache:
            # Time filter
            if item.timestamp < cutoff:
                continue
            
            # Source filter
            if source and item.source != source:
                continue
            
            # Symbol filter
            if symbols:
                if not any(s in item.symbols or s.lower() in item.headline.lower() 
                          for s in symbols):
                    continue
            
            # Importance filter
            item_imp_value = importance_order.get(item.importance, 1)
            if item_imp_value < min_imp_value:
                continue
            
            results.append(item)
        
        return results
    
    def get_upcoming_events(
        self,
        hours_ahead: float = 24.0,
        currencies: Optional[List[str]] = None,
        min_importance: str = "medium",
    ) -> List[EconomicEvent]:
        """
        Get upcoming economic events.
        
        Args:
            hours_ahead: How far ahead to look
            currencies: Filter by currencies
            min_importance: Minimum importance level
            
        Returns:
            List of upcoming events
        """
        now = datetime.utcnow()
        cutoff = now + timedelta(hours=hours_ahead)
        importance_order = {"low": 0, "medium": 1, "high": 2}
        min_imp_value = importance_order.get(min_importance, 1)
        
        results = []
        for event in self._events_cache:
            # Time filter (upcoming only)
            if event.timestamp < now or event.timestamp > cutoff:
                continue
            
            # Currency filter
            if currencies and event.currency not in currencies:
                continue
            
            # Importance filter
            event_imp_value = importance_order.get(event.importance, 1)
            if event_imp_value < min_imp_value:
                continue
            
            results.append(event)
        
        return results
    
    def has_high_impact_event_soon(
        self,
        hours_ahead: float = 1.0,
        currencies: Optional[List[str]] = None,
    ) -> bool:
        """
        Check if there's a high-impact event coming soon.
        
        This is used to trigger the news blackout veto.
        """
        events = self.get_upcoming_events(
            hours_ahead=hours_ahead,
            currencies=currencies,
            min_importance="high",
        )
        return len(events) > 0
    
    def generate_sample_news(self, n_items: int = 10) -> List[NewsItem]:
        """
        Generate sample news items for testing.
        
        In production, this would be replaced with actual API calls.
        """
        import random
        
        headlines = [
            ("Fed signals potential rate cut in coming months", NewsSource.REUTERS, "high", ["USD"]),
            ("EUR/USD breaks above key resistance level", NewsSource.BLOOMBERG, "normal", ["EURUSD", "EUR", "USD"]),
            ("ECB maintains hawkish stance on inflation", NewsSource.REUTERS, "high", ["EUR"]),
            ("US jobs report beats expectations", NewsSource.WSJ, "high", ["USD"]),
            ("Dollar weakens on dovish Fed comments", NewsSource.BLOOMBERG, "normal", ["USD"]),
            ("Risk appetite improves as trade tensions ease", NewsSource.REUTERS, "normal", []),
            ("GBP rallies on positive Brexit developments", NewsSource.BLOOMBERG, "normal", ["GBP", "GBPUSD"]),
            ("Oil prices surge on supply concerns", NewsSource.WSJ, "normal", ["CAD", "USDCAD"]),
            ("Asian markets mixed ahead of key data", NewsSource.REUTERS, "low", ["JPY", "AUD"]),
            ("Inflation data comes in hotter than expected", NewsSource.BLOOMBERG, "high", ["USD"]),
            ("Central bank intervention supports currency", NewsSource.REUTERS, "high", []),
            ("Technical breakout signals trend change", NewsSource.CUSTOM, "normal", []),
            ("Market volatility spikes on geopolitical concerns", NewsSource.WSJ, "high", []),
            ("Retail sales disappoint, raising recession fears", NewsSource.BLOOMBERG, "normal", ["USD"]),
            ("Currency pair tests multi-year lows", NewsSource.REUTERS, "normal", []),
        ]
        
        items = []
        now = datetime.utcnow()
        
        for i in range(min(n_items, len(headlines))):
            headline, source, importance, symbols = random.choice(headlines)
            # Random time in last 4 hours
            timestamp = now - timedelta(hours=random.uniform(0, 4))
            
            items.append(NewsItem(
                headline=headline,
                source=source,
                timestamp=timestamp,
                symbols=symbols,
                importance=importance,
            ))
        
        return items
    
    def generate_sample_events(self, n_events: int = 5) -> List[EconomicEvent]:
        """
        Generate sample economic events for testing.
        """
        import random
        
        events = []
        now = datetime.utcnow()
        
        for i in range(min(n_events, len(self.SAMPLE_EVENTS))):
            name, currency, importance = self.SAMPLE_EVENTS[i]
            # Random time in next 48 hours
            timestamp = now + timedelta(hours=random.uniform(0.5, 48))
            
            events.append(EconomicEvent(
                name=name,
                timestamp=timestamp,
                currency=currency,
                importance=importance,
            ))
        
        return events
    
    def load_sample_data(self) -> None:
        """Load sample news and events for testing."""
        news = self.generate_sample_news(10)
        events = self.generate_sample_events(5)
        
        self.add_news_batch(news)
        self._events_cache = events
        
        logger.info(f"Loaded {len(news)} sample news items and {len(events)} events")
    
    def save_cache(self, path: str) -> None:
        """Save cache to file."""
        data = {
            "news": [n.to_dict() for n in self._news_cache],
            "events": [e.to_dict() for e in self._events_cache],
            "last_fetch": self._last_fetch.isoformat() if self._last_fetch else None,
        }
        with open(path, "w") as f:
            json.dump(data, f, indent=2)
    
    def load_cache(self, path: str) -> None:
        """Load cache from file."""
        with open(path, "r") as f:
            data = json.load(f)
        
        self._news_cache = [NewsItem.from_dict(n) for n in data.get("news", [])]
        self._events_cache = [
            EconomicEvent(
                name=e["name"],
                timestamp=datetime.fromisoformat(e["timestamp"]),
                currency=e["currency"],
                importance=e["importance"],
                actual=e.get("actual"),
                forecast=e.get("forecast"),
                previous=e.get("previous"),
            )
            for e in data.get("events", [])
        ]
        if data.get("last_fetch"):
            self._last_fetch = datetime.fromisoformat(data["last_fetch"])
