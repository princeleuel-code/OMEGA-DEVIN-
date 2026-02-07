"""
Live Data Feed
==============

This module provides data feeds for paper trading:

1. LiveDataFeed - Connects to real-time market data (via yfinance or other APIs)
2. SimulatedFeed - Replays historical data for testing

The feeds provide a consistent interface for the paper trader to consume.
"""

from dataclasses import dataclass
from typing import List, Dict, Optional, Callable, Generator
from datetime import datetime, timedelta
from abc import ABC, abstractmethod
import threading
import time
import pandas as pd


@dataclass
class PriceBar:
    """A single price bar."""
    symbol: str
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float


@dataclass
class PriceTick:
    """A single price tick."""
    symbol: str
    timestamp: datetime
    bid: float
    ask: float
    mid: float


class DataFeed(ABC):
    """Abstract base class for data feeds."""
    
    @abstractmethod
    def start(self):
        """Start the data feed."""
        pass
    
    @abstractmethod
    def stop(self):
        """Stop the data feed."""
        pass
    
    @abstractmethod
    def get_latest_prices(self) -> Dict[str, float]:
        """Get latest prices for all symbols."""
        pass
    
    @abstractmethod
    def subscribe(self, callback: Callable[[Dict[str, float]], None]):
        """Subscribe to price updates."""
        pass


class LiveDataFeed(DataFeed):
    """
    Live data feed using yfinance.
    
    Note: yfinance has rate limits and delays. For production,
    use a proper market data provider like:
    - OANDA API
    - Interactive Brokers
    - Alpaca
    - Polygon.io
    """
    
    def __init__(
        self,
        symbols: List[str],
        update_interval: int = 60,  # seconds
    ):
        self.symbols = symbols
        self.update_interval = update_interval
        
        # Symbol mapping for yfinance
        self._yf_symbols = {
            "EURUSD": "EURUSD=X",
            "GBPUSD": "GBPUSD=X",
            "USDJPY": "USDJPY=X",
            "AUDUSD": "AUDUSD=X",
            "XAUUSD": "GC=F",
        }
        
        self._latest_prices: Dict[str, float] = {}
        self._callbacks: List[Callable] = []
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()
    
    def start(self):
        """Start the live data feed."""
        if self._running:
            return
        
        self._running = True
        self._thread = threading.Thread(target=self._update_loop, daemon=True)
        self._thread.start()
    
    def stop(self):
        """Stop the live data feed."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=5)
    
    def get_latest_prices(self) -> Dict[str, float]:
        """Get latest prices for all symbols."""
        with self._lock:
            return self._latest_prices.copy()
    
    def subscribe(self, callback: Callable[[Dict[str, float]], None]):
        """Subscribe to price updates."""
        self._callbacks.append(callback)
    
    def _update_loop(self):
        """Background thread to update prices."""
        while self._running:
            try:
                self._fetch_prices()
                
                # Notify subscribers
                prices = self.get_latest_prices()
                for callback in self._callbacks:
                    try:
                        callback(prices)
                    except Exception as e:
                        print(f"Callback error: {e}")
                
            except Exception as e:
                print(f"Price fetch error: {e}")
            
            time.sleep(self.update_interval)
    
    def _fetch_prices(self):
        """Fetch latest prices from yfinance."""
        try:
            import yfinance as yf
            
            for symbol in self.symbols:
                yf_symbol = self._yf_symbols.get(symbol, f"{symbol}=X")
                
                try:
                    ticker = yf.Ticker(yf_symbol)
                    hist = ticker.history(period="1d", interval="1m")
                    
                    if len(hist) > 0:
                        price = hist['Close'].iloc[-1]
                        with self._lock:
                            self._latest_prices[symbol] = float(price)
                except Exception as e:
                    print(f"Error fetching {symbol}: {e}")
        
        except ImportError:
            print("yfinance not installed. Using simulated prices.")
            self._generate_simulated_prices()
    
    def _generate_simulated_prices(self):
        """Generate simulated prices for testing."""
        import random
        
        base_prices = {
            "EURUSD": 1.0800,
            "GBPUSD": 1.2500,
            "USDJPY": 150.00,
            "AUDUSD": 0.6500,
            "XAUUSD": 2000.00,
        }
        
        with self._lock:
            for symbol in self.symbols:
                base = base_prices.get(symbol, 1.0)
                # Add small random movement
                change = random.uniform(-0.001, 0.001) * base
                
                if symbol in self._latest_prices:
                    self._latest_prices[symbol] += change
                else:
                    self._latest_prices[symbol] = base


class SimulatedFeed(DataFeed):
    """
    Simulated data feed that replays historical data.
    
    This is useful for:
    1. Testing the paper trading system
    2. Walk-forward simulation
    3. Strategy development without waiting for real-time data
    """
    
    def __init__(
        self,
        data: Dict[str, List[dict]],  # symbol -> list of bars
        speed_multiplier: float = 1.0,  # 1.0 = real-time, 10.0 = 10x speed
        bar_interval_seconds: int = 3600,  # 1 hour bars
    ):
        self.data = data
        self.speed_multiplier = speed_multiplier
        self.bar_interval_seconds = bar_interval_seconds
        
        self._current_index: Dict[str, int] = {s: 0 for s in data.keys()}
        self._latest_prices: Dict[str, float] = {}
        self._callbacks: List[Callable] = []
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()
        
        # Initialize with first prices
        for symbol, bars in data.items():
            if bars:
                self._latest_prices[symbol] = bars[0]['close']
    
    def start(self):
        """Start the simulated feed."""
        if self._running:
            return
        
        self._running = True
        self._thread = threading.Thread(target=self._replay_loop, daemon=True)
        self._thread.start()
    
    def stop(self):
        """Stop the simulated feed."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=5)
    
    def get_latest_prices(self) -> Dict[str, float]:
        """Get latest prices for all symbols."""
        with self._lock:
            return self._latest_prices.copy()
    
    def subscribe(self, callback: Callable[[Dict[str, float]], None]):
        """Subscribe to price updates."""
        self._callbacks.append(callback)
    
    def get_current_bars(self) -> Dict[str, dict]:
        """Get current bars for all symbols."""
        bars = {}
        with self._lock:
            for symbol, idx in self._current_index.items():
                if idx < len(self.data[symbol]):
                    bars[symbol] = self.data[symbol][idx]
        return bars
    
    def get_history(self, symbol: str, lookback: int = 200) -> List[dict]:
        """Get historical bars for a symbol."""
        with self._lock:
            idx = self._current_index.get(symbol, 0)
            start = max(0, idx - lookback)
            return self.data.get(symbol, [])[start:idx + 1]
    
    def _replay_loop(self):
        """Background thread to replay data."""
        sleep_time = self.bar_interval_seconds / self.speed_multiplier
        
        while self._running:
            # Advance all symbols
            all_done = True
            
            with self._lock:
                for symbol in self.data.keys():
                    idx = self._current_index[symbol]
                    if idx < len(self.data[symbol]) - 1:
                        self._current_index[symbol] += 1
                        new_idx = self._current_index[symbol]
                        self._latest_prices[symbol] = self.data[symbol][new_idx]['close']
                        all_done = False
            
            if all_done:
                self._running = False
                break
            
            # Notify subscribers
            prices = self.get_latest_prices()
            for callback in self._callbacks:
                try:
                    callback(prices)
                except Exception as e:
                    print(f"Callback error: {e}")
            
            time.sleep(sleep_time)
    
    def reset(self):
        """Reset to beginning of data."""
        with self._lock:
            self._current_index = {s: 0 for s in self.data.keys()}
            for symbol, bars in self.data.items():
                if bars:
                    self._latest_prices[symbol] = bars[0]['close']
    
    def is_complete(self) -> bool:
        """Check if all data has been replayed."""
        with self._lock:
            for symbol, idx in self._current_index.items():
                if idx < len(self.data[symbol]) - 1:
                    return False
        return True


def load_data_for_simulation(
    data_dir: str = "/home/ubuntu/omega_devin/data",
    symbols: List[str] = None
) -> Dict[str, List[dict]]:
    """
    Load historical data for simulation.
    
    Args:
        data_dir: Directory containing CSV files
        symbols: List of symbols to load (default: all available)
        
    Returns:
        Dict of symbol -> list of bars
    """
    import os
    
    symbol_files = {
        "EURUSD": "eurusd_hourly_2y.csv",
        "GBPUSD": "gbpusd_hourly_2y.csv",
        "USDJPY": "usdjpy_hourly_2y.csv",
        "AUDUSD": "audusd_hourly_2y.csv",
        "XAUUSD": "xauusd_hourly_2y.csv",
    }
    
    if symbols is None:
        symbols = list(symbol_files.keys())
    
    data = {}
    
    for symbol in symbols:
        filename = symbol_files.get(symbol)
        if not filename:
            continue
        
        filepath = os.path.join(data_dir, filename)
        if not os.path.exists(filepath):
            print(f"Warning: {filepath} not found")
            continue
        
        try:
            df = pd.read_csv(filepath)
            bars = []
            
            for _, row in df.iterrows():
                bar = {
                    'timestamp': row['Datetime'],
                    'open': float(row['Open']),
                    'high': float(row['High']),
                    'low': float(row['Low']),
                    'close': float(row['Close']),
                    'volume': float(row['Volume']) if row['Volume'] > 0 else 1000.0
                }
                bars.append(bar)
            
            data[symbol] = bars
            print(f"Loaded {len(bars)} bars for {symbol}")
        
        except Exception as e:
            print(f"Error loading {symbol}: {e}")
    
    return data
