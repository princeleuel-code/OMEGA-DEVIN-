import json
import unittest
from pathlib import Path
from unittest.mock import patch

from chimera.core.scanners import tvscreener_adapter


class TestTVScreenerAdapter(unittest.TestCase):
    def setUp(self):
        # Ensure tests are isolated from module-level caches / rate-limiter state.
        with tvscreener_adapter._CACHE_LOCK:  # pylint: disable=protected-access
            tvscreener_adapter._CACHE.clear()  # pylint: disable=protected-access
        with tvscreener_adapter._REQUEST_TIMES_LOCK:  # pylint: disable=protected-access
            tvscreener_adapter._REQUEST_TIMES.clear()  # pylint: disable=protected-access

    def _load_fixture(self) -> dict:
        path = Path(__file__).parent / "fixtures" / "tvscreener_forex_golden_raw.json"
        return json.loads(path.read_text(encoding="utf-8"))

    def test_normalization_schema(self):
        fixture = self._load_fixture()
        raw_rows = fixture["raw_rows"]
        labels = fixture["labels"]

        rows = tvscreener_adapter._normalize_rows(  # pylint: disable=protected-access
            raw_rows=raw_rows,
            labels=labels,
            asset_class="forex",
            timeframe="1D",
            ts_iso="2026-02-08T00:00:00+00:00",
            stale=False,
        )

        self.assertEqual(len(rows), 2)
        for r in rows:
            # Required keys
            self.assertIn("symbol", r)
            self.assertIn("exchange", r)
            self.assertIn("asset_class", r)
            self.assertIn("price", r)
            self.assertIn("change_pct", r)
            self.assertIn("volume", r)
            self.assertIn("market_cap", r)
            self.assertIn("volatility", r)
            self.assertIn("rsi", r)
            self.assertIn("timeframe", r)
            self.assertIn("source", r)
            self.assertIn("ts", r)
            self.assertIn("stale", r)

        self.assertEqual(rows[0]["symbol"], "AEDAUD")
        self.assertEqual(rows[0]["exchange"], "FX_IDC")

    def test_cache_hits_within_ttl(self):
        fixture = self._load_fixture()
        raw_rows = fixture["raw_rows"]
        labels = fixture["labels"]

        cfg = tvscreener_adapter._TVScreenerConfig(  # pylint: disable=protected-access
            enabled=True,
            ttl_seconds=60,
            max_requests_per_min=30,
            timeout_seconds=1,
        )

        with (
            patch.object(tvscreener_adapter, "_load_config", return_value=cfg),
            patch.object(tvscreener_adapter, "_now_ts", return_value=1000.0),
            patch.object(tvscreener_adapter, "_utc_now_iso", return_value="2026-02-08T00:00:00+00:00"),
            patch.object(
                tvscreener_adapter,
                "_fetch_raw_rows",
                return_value=(raw_rows, labels, "1D"),
            ) as fetch_mock,
        ):
            r1 = tvscreener_adapter.scan("forex", limit=2)
            r2 = tvscreener_adapter.scan("forex", limit=2)

        self.assertEqual(fetch_mock.call_count, 1)
        self.assertEqual(r1, r2)
        self.assertFalse(any(x.get("stale") for x in r2))

    def test_returns_stale_cache_on_failure(self):
        fixture = self._load_fixture()
        raw_rows = fixture["raw_rows"]
        labels = fixture["labels"]

        cfg = tvscreener_adapter._TVScreenerConfig(  # pylint: disable=protected-access
            enabled=True,
            ttl_seconds=30,
            max_requests_per_min=30,
            timeout_seconds=1,
        )

        with (
            patch.object(tvscreener_adapter, "_load_config", return_value=cfg),
            patch.object(tvscreener_adapter, "_utc_now_iso", return_value="2026-02-08T00:00:00+00:00"),
            patch.object(tvscreener_adapter, "time") as time_mod,
        ):
            # First call succeeds at t=1000.
            time_mod.time.return_value = 1000.0
            with patch.object(
                tvscreener_adapter,
                "_fetch_raw_rows",
                return_value=(raw_rows, labels, "1D"),
            ):
                fresh = tvscreener_adapter.scan("forex", limit=2)

            # Second call after TTL expires fails at t=2000.
            time_mod.time.return_value = 2000.0
            with patch.object(
                tvscreener_adapter,
                "_fetch_raw_rows",
                side_effect=RuntimeError("network down"),
            ):
                stale = tvscreener_adapter.scan("forex", limit=2)

        self.assertEqual([r["symbol"] for r in fresh], [r["symbol"] for r in stale])
        self.assertTrue(all(r["stale"] for r in stale))


if __name__ == "__main__":
    unittest.main()
