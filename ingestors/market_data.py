# OMEGA-DEVIN // MARKET DATA INGESTOR
# Fetches REAL market data from multiple sources

import os
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import json

class MarketDataFeed:
    """
    Market Data Feed - Fetches REAL market data
    
    Supports multiple data sources:
    1. yfinance (Yahoo Finance) - Free, no API key
    2. Alpha Vantage - Free tier available
    3. Twelve Data - Free tier available
    4. Local CSV files - For backtesting
    """
    
    # Yahoo Finance symbols for forex
    YAHOO_SYMBOLS = {
        "EURUSD": "EURUSD=X",
        "GBPUSD": "GBPUSD=X",
        "USDJPY": "USDJPY=X",
        "AUDUSD": "AUDUSD=X",
        "XAUUSD": "GC=F",  # Gold futures
        "BTCUSD": "BTC-USD",
        "ETHUSD": "ETH-USD"
    }
    
    def __init__(self, data_source: str = "yfinance"):
        self.data_source = data_source
        self.cache = {}
        self.cache_expiry = {}
        self.cache_duration = 60  # seconds
        
    def fetch_ohlcv(self, symbol: str, timeframe: str = "1h", bars: int = 100) -> List[Dict]:
        """
        Fetch OHLCV data for a symbol
        
        Args:
            symbol: Trading symbol (e.g., "EURUSD")
            timeframe: Timeframe (e.g., "1h", "4h", "1d")
            bars: Number of bars to fetch
            
        Returns:
            List of OHLCV dictionaries
        """
        cache_key = f"{symbol}_{timeframe}_{bars}"
        
        # Check cache
        if cache_key in self.cache:
            if datetime.now().timestamp() < self.cache_expiry.get(cache_key, 0):
                return self.cache[cache_key]
        
        # Fetch based on data source
        if self.data_source == "yfinance":
            data = self._fetch_yfinance(symbol, timeframe, bars)
        elif self.data_source == "csv":
            data = self._fetch_csv(symbol, bars)
        else:
            data = self._generate_synthetic(symbol, bars)
        
        # Update cache
        self.cache[cache_key] = data
        self.cache_expiry[cache_key] = datetime.now().timestamp() + self.cache_duration
        
        return data
    
    def _fetch_yfinance(self, symbol: str, timeframe: str, bars: int) -> List[Dict]:
        """Fetch data from Yahoo Finance"""
        try:
            import yfinance as yf
            
            # Convert symbol to Yahoo format
            yahoo_symbol = self.YAHOO_SYMBOLS.get(symbol, f"{symbol}=X")
            
            # Convert timeframe to yfinance format
            interval_map = {
                "1m": "1m",
                "5m": "5m",
                "15m": "15m",
                "30m": "30m",
                "1h": "1h",
                "4h": "1h",  # yfinance doesn't support 4h, we'll resample
                "1d": "1d",
                "1w": "1wk"
            }
            interval = interval_map.get(timeframe, "1h")
            
            # Calculate period based on bars needed
            if interval in ["1m", "5m", "15m", "30m"]:
                period = "5d"
            elif interval == "1h":
                period = "30d"
            else:
                period = "1y"
            
            # Fetch data
            ticker = yf.Ticker(yahoo_symbol)
            df = ticker.history(period=period, interval=interval)
            
            if df.empty:
                print(f"   [INGESTOR]: No data from yfinance for {symbol}")
                return self._generate_synthetic(symbol, bars)
            
            # Convert to list of dicts
            data = []
            for idx, row in df.tail(bars).iterrows():
                data.append({
                    "timestamp": idx.strftime("%Y-%m-%d %H:%M:%S"),
                    "open": float(row["Open"]),
                    "high": float(row["High"]),
                    "low": float(row["Low"]),
                    "close": float(row["Close"]),
                    "volume": int(row["Volume"]) if row["Volume"] > 0 else 1000
                })
            
            print(f"   [INGESTOR]: Fetched {len(data)} REAL bars for {symbol} from Yahoo Finance")
            return data
            
        except ImportError:
            print("   [INGESTOR]: yfinance not installed. Using synthetic data.")
            return self._generate_synthetic(symbol, bars)
        except Exception as e:
            print(f"   [INGESTOR]: Error fetching from yfinance: {e}")
            return self._generate_synthetic(symbol, bars)
    
    def _fetch_csv(self, symbol: str, bars: int) -> List[Dict]:
        """Fetch data from local CSV file"""
        try:
            import pandas as pd
            
            # Look for CSV file
            csv_paths = [
                f"/home/ubuntu/omega_devin/data/{symbol.lower()}_hourly_2y.csv",
                f"/home/ubuntu/omega_devin/data/{symbol.lower()}.csv",
                f"data/{symbol.lower()}.csv"
            ]
            
            for csv_path in csv_paths:
                if os.path.exists(csv_path):
                    df = pd.read_csv(csv_path)
                    
                    data = []
                    for _, row in df.tail(bars).iterrows():
                        data.append({
                            "timestamp": row.get("Datetime", row.get("timestamp", "")),
                            "open": float(row["Open"]),
                            "high": float(row["High"]),
                            "low": float(row["Low"]),
                            "close": float(row["Close"]),
                            "volume": int(row.get("Volume", 1000))
                        })
                    
                    print(f"   [INGESTOR]: Loaded {len(data)} bars for {symbol} from CSV")
                    return data
            
            print(f"   [INGESTOR]: No CSV found for {symbol}")
            return self._generate_synthetic(symbol, bars)
            
        except Exception as e:
            print(f"   [INGESTOR]: Error loading CSV: {e}")
            return self._generate_synthetic(symbol, bars)
    
    def _generate_synthetic(self, symbol: str, bars: int) -> List[Dict]:
        """Generate synthetic data for testing"""
        import random
        
        # Starting prices for different symbols
        start_prices = {
            "EURUSD": 1.0850,
            "GBPUSD": 1.2650,
            "USDJPY": 154.50,
            "AUDUSD": 0.6280,
            "XAUUSD": 2045.00,
            "BTCUSD": 45000.00,
            "ETHUSD": 2500.00
        }
        
        price = start_prices.get(symbol, 1.0)
        data = []
        
        now = datetime.now()
        
        for i in range(bars):
            # Random walk with slight trend
            change_pct = random.gauss(0, 0.001)  # 0.1% std dev
            
            open_price = price
            close_price = price * (1 + change_pct)
            high_price = max(open_price, close_price) * (1 + random.uniform(0, 0.0005))
            low_price = min(open_price, close_price) * (1 - random.uniform(0, 0.0005))
            
            timestamp = now - timedelta(hours=bars - i)
            
            data.append({
                "timestamp": timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                "open": round(open_price, 5),
                "high": round(high_price, 5),
                "low": round(low_price, 5),
                "close": round(close_price, 5),
                "volume": random.randint(1000, 5000)
            })
            
            price = close_price
        
        print(f"   [INGESTOR]: Generated {len(data)} SYNTHETIC bars for {symbol}")
        return data
    
    def get_current_price(self, symbol: str) -> float:
        """Get current price for a symbol"""
        data = self.fetch_ohlcv(symbol, "1h", 1)
        if data:
            return data[-1]["close"]
        return 0.0
    
    def get_multiple_timeframes(self, symbol: str, timeframes: List[str] = ["1h", "4h", "1d"]) -> Dict[str, List[Dict]]:
        """Fetch data for multiple timeframes"""
        result = {}
        for tf in timeframes:
            result[tf] = self.fetch_ohlcv(symbol, tf, 100)
        return result


# Test the market data feed
if __name__ == "__main__":
    feed = MarketDataFeed(data_source="yfinance")
    
    print("\n=== TESTING MARKET DATA FEED ===")
    
    # Test EURUSD
    data = feed.fetch_ohlcv("EURUSD", "1h", 20)
    print(f"\nEURUSD Data ({len(data)} bars):")
    if data:
        print(f"  Latest: {data[-1]}")
        print(f"  Current Price: {feed.get_current_price('EURUSD')}")
    
    # Test XAUUSD (Gold)
    data = feed.fetch_ohlcv("XAUUSD", "1h", 20)
    print(f"\nXAUUSD Data ({len(data)} bars):")
    if data:
        print(f"  Latest: {data[-1]}")
