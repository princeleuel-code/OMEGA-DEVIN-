"""
Real DOM Implementation - Binance L2 Order Book
================================================
Connects to Binance websocket for REAL order book data.
This is TIER A data - can affect trading decisions.

Config switch: REAL_DOM=true fails closed if feed not connected.
"""

import asyncio
import json
from datetime import datetime
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum
import os
import logging

try:
    import websockets  # type: ignore
except Exception:  # pragma: no cover
    websockets = None

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DOMConnectionState(Enum):
    DISCONNECTED = "DISCONNECTED"
    CONNECTING = "CONNECTING"
    CONNECTED = "CONNECTED"
    ERROR = "ERROR"


@dataclass
class DOMLevel:
    """A single price level in the order book"""
    price: float
    size: float
    is_bid: bool
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "price": self.price,
            "size": self.size,
            "is_bid": self.is_bid,
            "timestamp": self.timestamp.isoformat()
        }


@dataclass
class RealDOMSnapshot:
    """
    Real DOM snapshot from live feed.
    This is TIER A data - can affect decisions.
    """
    symbol: str
    exchange: str
    timestamp: datetime
    bids: List[DOMLevel]
    asks: List[DOMLevel]
    spread: float
    mid_price: float
    book_imbalance: float  # (bid_size - ask_size) / (bid_size + ask_size)
    total_bid_size: float
    total_ask_size: float
    liquidity_walls: List[DOMLevel]
    is_real: bool = True  # Always True for this class
    provenance_tier: str = "REAL"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "symbol": self.symbol,
            "exchange": self.exchange,
            "timestamp": self.timestamp.isoformat(),
            "bids": [b.to_dict() for b in self.bids],
            "asks": [a.to_dict() for a in self.asks],
            "spread": self.spread,
            "mid_price": self.mid_price,
            "book_imbalance": self.book_imbalance,
            "total_bid_size": self.total_bid_size,
            "total_ask_size": self.total_ask_size,
            "liquidity_walls": [l.to_dict() for l in self.liquidity_walls],
            "is_real": self.is_real,
            "provenance_tier": self.provenance_tier,
            "watermark": None  # No watermark for real data
        }


class BinanceL2Feed:
    """
    Binance L2 Order Book WebSocket Feed.
    Provides REAL DOM data (Tier A).
    """
    
    WEBSOCKET_URL = "wss://stream.binance.com:9443/ws"
    
    def __init__(self, symbol: str = "btcusdt", depth: int = 20):
        self.symbol = symbol.lower()
        self.depth = depth
        self.state = DOMConnectionState.DISCONNECTED
        self.websocket = None
        self.latest_snapshot: Optional[RealDOMSnapshot] = None
        self.callbacks: List[Callable[[RealDOMSnapshot], None]] = []
        self.running = False
        self.reconnect_delay = 5
        self.last_update_id = 0
        
        # Recorded replay data
        self.replay_data: List[Dict[str, Any]] = []
        self.is_replay_mode = False
    
    def get_stream_name(self) -> str:
        """Get the Binance stream name for depth"""
        return f"{self.symbol}@depth{self.depth}@100ms"
    
    async def connect(self) -> bool:
        """Connect to Binance websocket"""
        if websockets is None:
            self.state = DOMConnectionState.ERROR
            logger.error("websockets dependency missing; cannot connect real DOM feed")
            return False
        if self.state == DOMConnectionState.CONNECTED:
            return True
        
        self.state = DOMConnectionState.CONNECTING
        stream_url = f"{self.WEBSOCKET_URL}/{self.get_stream_name()}"
        
        try:
            self.websocket = await websockets.connect(stream_url)
            self.state = DOMConnectionState.CONNECTED
            logger.info(f"Connected to Binance L2 feed for {self.symbol}")
            return True
        except Exception as e:
            self.state = DOMConnectionState.ERROR
            logger.error(f"Failed to connect to Binance: {e}")
            return False
    
    async def disconnect(self) -> None:
        """Disconnect from websocket"""
        self.running = False
        if self.websocket:
            await self.websocket.close()
        self.state = DOMConnectionState.DISCONNECTED
        logger.info("Disconnected from Binance L2 feed")
    
    def on_snapshot(self, callback: Callable[[RealDOMSnapshot], None]) -> None:
        """Register callback for DOM updates"""
        self.callbacks.append(callback)
    
    def _parse_depth_update(self, data: Dict[str, Any]) -> Optional[RealDOMSnapshot]:
        """Parse Binance depth update into RealDOMSnapshot"""
        try:
            timestamp = datetime.utcnow()
            
            # Parse bids and asks
            bids = []
            asks = []
            
            for bid in data.get("b", data.get("bids", []))[:self.depth]:
                price = float(bid[0])
                size = float(bid[1])
                if size > 0:
                    bids.append(DOMLevel(price=price, size=size, is_bid=True, timestamp=timestamp))
            
            for ask in data.get("a", data.get("asks", []))[:self.depth]:
                price = float(ask[0])
                size = float(ask[1])
                if size > 0:
                    asks.append(DOMLevel(price=price, size=size, is_bid=False, timestamp=timestamp))
            
            if not bids or not asks:
                return None
            
            # Sort bids descending, asks ascending
            bids.sort(key=lambda x: x.price, reverse=True)
            asks.sort(key=lambda x: x.price)
            
            # Calculate metrics
            best_bid = bids[0].price if bids else 0
            best_ask = asks[0].price if asks else 0
            spread = best_ask - best_bid if best_bid and best_ask else 0
            mid_price = (best_bid + best_ask) / 2 if best_bid and best_ask else 0
            
            total_bid_size = sum(b.size for b in bids)
            total_ask_size = sum(a.size for a in asks)
            
            # Book imbalance: positive = more bids, negative = more asks
            total_size = total_bid_size + total_ask_size
            book_imbalance = (total_bid_size - total_ask_size) / total_size if total_size > 0 else 0
            
            # Find liquidity walls (levels with size > 2x average)
            all_levels = bids + asks
            avg_size = sum(l.size for l in all_levels) / len(all_levels) if all_levels else 0
            liquidity_walls = [l for l in all_levels if l.size > avg_size * 2]
            
            return RealDOMSnapshot(
                symbol=self.symbol.upper(),
                exchange="BINANCE",
                timestamp=timestamp,
                bids=bids,
                asks=asks,
                spread=spread,
                mid_price=mid_price,
                book_imbalance=round(book_imbalance, 4),
                total_bid_size=total_bid_size,
                total_ask_size=total_ask_size,
                liquidity_walls=liquidity_walls
            )
        except Exception as e:
            logger.error(f"Error parsing depth update: {e}")
            return None
    
    async def run(self) -> None:
        """Run the feed loop"""
        self.running = True
        
        while self.running:
            if self.state != DOMConnectionState.CONNECTED:
                connected = await self.connect()
                if not connected:
                    await asyncio.sleep(self.reconnect_delay)
                    continue
            
            try:
                message = await self.websocket.recv()
                data = json.loads(message)
                
                snapshot = self._parse_depth_update(data)
                if snapshot:
                    self.latest_snapshot = snapshot
                    
                    # Record for replay
                    self.replay_data.append(snapshot.to_dict())
                    if len(self.replay_data) > 10000:
                        self.replay_data.pop(0)
                    
                    # Notify callbacks
                    for callback in self.callbacks:
                        try:
                            callback(snapshot)
                        except Exception as e:
                            logger.error(f"Callback error: {e}")
                            
            except Exception as e:
                if websockets is not None and isinstance(e, getattr(websockets, "ConnectionClosed", ())):
                    logger.warning("WebSocket connection closed, reconnecting...")
                    self.state = DOMConnectionState.DISCONNECTED
                    await asyncio.sleep(self.reconnect_delay)
                    continue
                logger.error(f"Error in feed loop: {e}")
                await asyncio.sleep(1)
    
    def get_latest(self) -> Optional[RealDOMSnapshot]:
        """Get the latest DOM snapshot"""
        return self.latest_snapshot
    
    def export_replay_data(self) -> List[Dict[str, Any]]:
        """Export recorded data for replay"""
        return self.replay_data.copy()
    
    def load_replay_data(self, data: List[Dict[str, Any]]) -> None:
        """Load replay data"""
        self.replay_data = data
        self.is_replay_mode = True
    
    def get_replay_snapshot(self, index: int) -> Optional[Dict[str, Any]]:
        """Get a specific snapshot from replay data"""
        if 0 <= index < len(self.replay_data):
            return self.replay_data[index]
        return None


class RealDOMManager:
    """
    Manager for Real DOM feeds.
    Implements REAL_DOM config switch with fail-closed behavior.
    """
    
    def __init__(self):
        self.feeds: Dict[str, BinanceL2Feed] = {}
        self.real_dom_enabled = os.environ.get("REAL_DOM", "false").lower() == "true"
        self.connected_symbols: List[str] = []
    
    def is_real_dom_available(self, symbol: str) -> bool:
        """Check if real DOM is available for a symbol"""
        if not self.real_dom_enabled:
            return False
        
        feed = self.feeds.get(symbol.lower())
        if not feed:
            return False
        
        return feed.state == DOMConnectionState.CONNECTED
    
    def fail_closed_check(self, symbol: str) -> bool:
        """
        FAIL-CLOSED: If REAL_DOM=true but feed not connected, return False.
        This blocks trading decisions that require real DOM.
        """
        if not self.real_dom_enabled:
            # Real DOM not required, allow synthetic display (but not for decisions)
            return True
        
        # Real DOM required - must be connected
        return self.is_real_dom_available(symbol)
    
    async def add_feed(self, symbol: str, depth: int = 20) -> BinanceL2Feed:
        """Add a new feed for a symbol"""
        symbol_lower = symbol.lower()
        
        if symbol_lower not in self.feeds:
            feed = BinanceL2Feed(symbol=symbol_lower, depth=depth)
            self.feeds[symbol_lower] = feed
        
        return self.feeds[symbol_lower]
    
    async def start_feed(self, symbol: str) -> bool:
        """Start a feed for a symbol"""
        symbol_lower = symbol.lower()
        feed = self.feeds.get(symbol_lower)
        
        if not feed:
            feed = await self.add_feed(symbol_lower)
        
        # Start the feed in background
        asyncio.create_task(feed.run())
        
        # Wait for connection
        for _ in range(10):
            if feed.state == DOMConnectionState.CONNECTED:
                self.connected_symbols.append(symbol_lower)
                return True
            await asyncio.sleep(0.5)
        
        return False
    
    def get_snapshot(self, symbol: str) -> Optional[RealDOMSnapshot]:
        """Get latest DOM snapshot for a symbol"""
        feed = self.feeds.get(symbol.lower())
        if feed:
            return feed.get_latest()
        return None
    
    def get_status(self) -> Dict[str, Any]:
        """Get status of all feeds"""
        return {
            "real_dom_enabled": self.real_dom_enabled,
            "connected_symbols": self.connected_symbols,
            "feeds": {
                symbol: {
                    "state": feed.state.value,
                    "has_data": feed.latest_snapshot is not None,
                    "replay_frames": len(feed.replay_data)
                }
                for symbol, feed in self.feeds.items()
            }
        }


# Global DOM manager
dom_manager = RealDOMManager()


def get_synthetic_dom_watermarked(symbol: str, bars: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Generate SYNTHETIC DOM data with mandatory watermark.
    This is TIER C data - CANNOT affect decisions.
    """
    if not bars:
        return {
            "bids": [],
            "asks": [],
            "is_real": False,
            "provenance_tier": "SYNTHETIC",
            "watermark": "SYNTHETIC / EDUCATIONAL ONLY",
            "warning": "This DOM is simulated from OHLCV data. DO NOT use for trading decisions."
        }
    
    current_bar = bars[-1]
    current_price = current_bar.get("close", 0)
    
    # Generate fake levels (for display only)
    avg_range = sum(b["high"] - b["low"] for b in bars[-10:]) / min(10, len(bars))
    spread = avg_range * 0.01
    
    bids = []
    asks = []
    
    for i in range(10):
        bid_price = current_price - spread * (i + 1)
        ask_price = current_price + spread * (i + 1)
        
        bids.append({
            "price": round(bid_price, 5),
            "size": 1000 + i * 100,
            "is_bid": True
        })
        asks.append({
            "price": round(ask_price, 5),
            "size": 1000 + i * 100,
            "is_bid": False
        })
    
    return {
        "symbol": symbol,
        "exchange": "SIMULATED",
        "timestamp": datetime.utcnow().isoformat(),
        "bids": bids,
        "asks": asks,
        "spread": round(spread, 6),
        "mid_price": round(current_price, 5),
        "book_imbalance": 0,
        "total_bid_size": sum(b["size"] for b in bids),
        "total_ask_size": sum(a["size"] for a in asks),
        "liquidity_walls": [],
        "is_real": False,
        "provenance_tier": "SYNTHETIC",
        "watermark": "SYNTHETIC / EDUCATIONAL ONLY",
        "warning": "This DOM is simulated from OHLCV data. DO NOT use for trading decisions."
    }
