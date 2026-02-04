"""
Data Loader - Ingest FX data from various sources

Supports CSV files, and can be extended for live feeds.
"""

import csv
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional, Iterator, Dict, Any
import logging


logger = logging.getLogger(__name__)


@dataclass
class OHLCV:
    """Single OHLCV bar"""
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float
    symbol: str = ""
    
    @property
    def mid(self) -> float:
        """Mid price"""
        return (self.high + self.low) / 2
    
    @property
    def range(self) -> float:
        """Bar range (high - low)"""
        return self.high - self.low
    
    @property
    def body(self) -> float:
        """Candle body size"""
        return abs(self.close - self.open)
    
    @property
    def is_bullish(self) -> bool:
        """Is this a bullish candle"""
        return self.close > self.open
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp.isoformat(),
            "open": self.open,
            "high": self.high,
            "low": self.low,
            "close": self.close,
            "volume": self.volume,
            "symbol": self.symbol
        }


@dataclass
class Tick:
    """Single tick/quote"""
    timestamp: datetime
    bid: float
    ask: float
    symbol: str = ""
    
    @property
    def mid(self) -> float:
        return (self.bid + self.ask) / 2
    
    @property
    def spread(self) -> float:
        return self.ask - self.bid


class DataLoader:
    """
    Load FX data from files or generate synthetic data for testing.
    """
    
    def __init__(self, symbol: str = "EURUSD"):
        self.symbol = symbol
        self._data: List[OHLCV] = []
    
    def load_csv(self, path: Path, date_format: str = "%Y-%m-%d %H:%M:%S") -> List[OHLCV]:
        """
        Load OHLCV data from CSV file.
        
        Expected columns: timestamp, open, high, low, close, volume
        """
        self._data = []
        
        with open(path, "r") as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    bar = OHLCV(
                        timestamp=datetime.strptime(row["timestamp"], date_format),
                        open=float(row["open"]),
                        high=float(row["high"]),
                        low=float(row["low"]),
                        close=float(row["close"]),
                        volume=float(row.get("volume", 0)),
                        symbol=self.symbol
                    )
                    self._data.append(bar)
                except (KeyError, ValueError) as e:
                    logger.warning(f"Skipping invalid row: {e}")
        
        logger.info(f"Loaded {len(self._data)} bars from {path}")
        return self._data
    
    def generate_synthetic(
        self,
        start_price: float = 1.1000,
        num_bars: int = 1000,
        volatility: float = 0.0002,
        trend: float = 0.0,
        start_time: Optional[datetime] = None
    ) -> List[OHLCV]:
        """
        Generate synthetic OHLCV data for testing.
        
        Uses a simple random walk with configurable volatility and trend.
        """
        import random
        
        self._data = []
        price = start_price
        current_time = start_time or datetime(2024, 1, 1, 0, 0, 0)
        
        for i in range(num_bars):
            # Random walk with trend
            change = random.gauss(trend, volatility)
            
            # Generate OHLCV
            open_price = price
            
            # Intrabar movement
            moves = [random.gauss(0, volatility) for _ in range(4)]
            prices = [open_price + sum(moves[:j+1]) for j in range(4)]
            
            high = max(open_price, max(prices))
            low = min(open_price, min(prices))
            close = open_price + change
            
            # Ensure high/low contain open/close
            high = max(high, open_price, close)
            low = min(low, open_price, close)
            
            bar = OHLCV(
                timestamp=current_time,
                open=round(open_price, 5),
                high=round(high, 5),
                low=round(low, 5),
                close=round(close, 5),
                volume=random.uniform(1000, 10000),
                symbol=self.symbol
            )
            self._data.append(bar)
            
            price = close
            current_time = current_time + timedelta(hours=1)
        
        logger.info(f"Generated {len(self._data)} synthetic bars")
        return self._data
    
    def generate_regime_data(
        self,
        num_bars: int = 2000,
        start_price: float = 1.1000
    ) -> List[OHLCV]:
        """
        Generate data with distinct market regimes for testing.
        
        Regimes:
        - Trending up
        - Trending down
        - Ranging/choppy
        - High volatility spike
        """
        import random
        
        self._data = []
        price = start_price
        current_time = datetime(2024, 1, 1, 0, 0, 0)
        
        # Define regime segments
        bars_per_regime = num_bars // 5
        regimes = [
            ("trend_up", 0.0001, 0.0001),      # Uptrend
            ("range", 0.0, 0.00015),            # Ranging
            ("trend_down", -0.0001, 0.0001),   # Downtrend
            ("volatile", 0.0, 0.0004),          # High volatility
            ("trend_up", 0.00005, 0.00012),    # Mild uptrend
        ]
        
        for regime_name, trend, vol in regimes:
            for i in range(bars_per_regime):
                change = random.gauss(trend, vol)
                
                open_price = price
                moves = [random.gauss(0, vol) for _ in range(4)]
                prices = [open_price + sum(moves[:j+1]) for j in range(4)]
                
                high = max(open_price, max(prices))
                low = min(open_price, min(prices))
                close = open_price + change
                
                high = max(high, open_price, close)
                low = min(low, open_price, close)
                
                bar = OHLCV(
                    timestamp=current_time,
                    open=round(open_price, 5),
                    high=round(high, 5),
                    low=round(low, 5),
                    close=round(close, 5),
                    volume=random.uniform(1000, 10000),
                    symbol=self.symbol
                )
                self._data.append(bar)
                
                price = close
                current_time = current_time + timedelta(hours=1)
        
        logger.info(f"Generated {len(self._data)} bars with regime changes")
        return self._data
    
    @property
    def data(self) -> List[OHLCV]:
        return self._data
    
    def __len__(self) -> int:
        return len(self._data)
    
    def __iter__(self) -> Iterator[OHLCV]:
        return iter(self._data)
    
    def __getitem__(self, idx: int) -> OHLCV:
        return self._data[idx]
