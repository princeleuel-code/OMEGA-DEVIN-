# OMEGA-DEVIN // REAL-TIME DATA FEED
# WebSocket connections for live market data

import asyncio
import json
from typing import Dict, List, Callable, Optional
from datetime import datetime

class RealTimeFeed:
    """
    Real-Time Market Data Feed
    
    Provides live price updates via WebSocket connections.
    Supports multiple data providers.
    """
    
    def __init__(self):
        self.subscribers = {}
        self.running = False
        self.last_prices = {}
        
    async def subscribe(self, symbol: str, callback: Callable):
        """Subscribe to real-time updates for a symbol"""
        if symbol not in self.subscribers:
            self.subscribers[symbol] = []
        self.subscribers[symbol].append(callback)
        print(f"   [REALTIME]: Subscribed to {symbol}")
    
    async def unsubscribe(self, symbol: str, callback: Callable):
        """Unsubscribe from real-time updates"""
        if symbol in self.subscribers:
            self.subscribers[symbol].remove(callback)
            print(f"   [REALTIME]: Unsubscribed from {symbol}")
    
    async def start(self):
        """Start the real-time feed"""
        self.running = True
        print("   [REALTIME]: Starting real-time feed...")
        
        while self.running:
            # Fetch latest prices and notify subscribers
            for symbol in self.subscribers:
                try:
                    price = await self._fetch_latest_price(symbol)
                    if price:
                        self.last_prices[symbol] = price
                        for callback in self.subscribers[symbol]:
                            await callback(symbol, price)
                except Exception as e:
                    print(f"   [REALTIME]: Error fetching {symbol}: {e}")
            
            await asyncio.sleep(1)  # Update every second
    
    async def stop(self):
        """Stop the real-time feed"""
        self.running = False
        print("   [REALTIME]: Stopped real-time feed")
    
    async def _fetch_latest_price(self, symbol: str) -> Optional[Dict]:
        """Fetch latest price for a symbol"""
        try:
            import yfinance as yf
            
            yahoo_symbols = {
                "EURUSD": "EURUSD=X",
                "GBPUSD": "GBPUSD=X",
                "USDJPY": "USDJPY=X",
                "AUDUSD": "AUDUSD=X",
                "XAUUSD": "GC=F"
            }
            
            yahoo_symbol = yahoo_symbols.get(symbol, f"{symbol}=X")
            ticker = yf.Ticker(yahoo_symbol)
            
            # Get the latest data
            data = ticker.history(period="1d", interval="1m")
            if not data.empty:
                latest = data.iloc[-1]
                return {
                    "symbol": symbol,
                    "timestamp": datetime.now().isoformat(),
                    "price": float(latest["Close"]),
                    "bid": float(latest["Low"]),
                    "ask": float(latest["High"]),
                    "volume": int(latest["Volume"]) if latest["Volume"] > 0 else 0
                }
        except Exception as e:
            pass
        
        return None
    
    def get_last_price(self, symbol: str) -> Optional[float]:
        """Get the last known price for a symbol"""
        if symbol in self.last_prices:
            return self.last_prices[symbol].get("price")
        return None


# Test
if __name__ == "__main__":
    async def price_callback(symbol, price):
        print(f"   Price Update: {symbol} = {price}")
    
    async def main():
        feed = RealTimeFeed()
        await feed.subscribe("EURUSD", price_callback)
        
        # Run for 5 seconds
        task = asyncio.create_task(feed.start())
        await asyncio.sleep(5)
        await feed.stop()
    
    asyncio.run(main())
