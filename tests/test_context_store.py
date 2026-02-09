import csv
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from context_store.store import DataContextStore, OHLCVSource, TickSource


class TestDataContextStore(unittest.TestCase):
    def _write_ohlcv_csv(self, path: Path) -> None:
        start = datetime(2025, 1, 1, 0, 1, 0, tzinfo=timezone.utc)
        rows = []
        price = 100.0
        for i in range(10):
            ts = start + timedelta(minutes=i)
            o = price
            c = price + 1.0
            h = max(o, c) + 0.5
            l = min(o, c) - 0.5
            rows.append(
                {
                    "timestamp": ts.strftime("%Y-%m-%d %H:%M:%S"),
                    "open": f"{o:.2f}",
                    "high": f"{h:.2f}",
                    "low": f"{l:.2f}",
                    "close": f"{c:.2f}",
                    "volume": "10",
                }
            )
            price = c

        with path.open("w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=["timestamp", "open", "high", "low", "close", "volume"])
            w.writeheader()
            w.writerows(rows)

    def test_lazy_load_and_resample(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "bars.csv"
            self._write_ohlcv_csv(p)

            store = DataContextStore()
            store.register_ohlcv(OHLCVSource(symbol="TEST", timeframe="1m", path=p, fmt="csv"))

            # First access loads once.
            df_1m = store.get_ohlcv(symbol="TEST", timeframe="1m")
            stats = store.debug_stats()
            self.assertEqual(stats["load_counts"].get("TEST:1m"), 1)
            self.assertEqual(len(df_1m), 10)

            # Derived timeframe should not re-load the base CSV.
            df_5m = store.get_ohlcv(symbol="TEST", timeframe="5m")
            stats2 = store.debug_stats()
            self.assertEqual(stats2["load_counts"].get("TEST:1m"), 1)
            self.assertGreaterEqual(len(df_5m), 1)

            # Calling again should hit cache (still one load).
            _ = store.get_ohlcv(symbol="TEST", timeframe="5m")
            stats3 = store.debug_stats()
            self.assertEqual(stats3["load_counts"].get("TEST:1m"), 1)

    def test_ticks_optional(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "ticks.csv"
            rows = [
                {"timestamp": "2025-01-01 00:00:00", "bid": "1.0", "ask": "1.1"},
                {"timestamp": "2025-01-01 00:00:01", "bid": "1.1", "ask": "1.2"},
            ]
            with p.open("w", newline="") as f:
                w = csv.DictWriter(f, fieldnames=["timestamp", "bid", "ask"])
                w.writeheader()
                w.writerows(rows)

            store = DataContextStore()
            store.register_ticks(TickSource(symbol="EURUSD", path=p, fmt="csv"))
            df = store.get_ticks(symbol="EURUSD")
            self.assertIn("mid", df.columns)
            self.assertIn("spread", df.columns)
            self.assertEqual(len(df), 2)


if __name__ == "__main__":
    unittest.main()

