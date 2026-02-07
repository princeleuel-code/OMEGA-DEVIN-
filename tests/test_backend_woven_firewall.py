import os
import sys
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path


_BACKEND_ROOT = Path(__file__).resolve().parents[1] / "omega_ui" / "omega_backend"
sys.path.insert(0, str(_BACKEND_ROOT))


from app.provenance import (  # noqa: E402
    ProvenanceFirewall,
    ProvenanceViolationError,
    create_tagged_feature,
)
from app.provenance.dom_types import DOMLevel, RealDOMSnapshot  # noqa: E402
from app.provenance.market_data_provider import (  # noqa: E402
    FeedState,
    MarketDataProvider,
    MarketDataRegistry,
)
from app.provenance.why_wait import generate_why_wait  # noqa: E402


class TestProvenanceFirewallGuard(unittest.TestCase):
    def test_tier_c_cannot_inflate_confidence(self) -> None:
        firewall = ProvenanceFirewall()

        tier_a = create_tagged_feature(
            name="real_dom_bids",
            value=[{"price": 100.0, "size": 1.0}],
            source="test_feed",
        )
        tier_c = create_tagged_feature(
            name="estimated_delta",
            value=123,
            source="candle_estimation",
        )
        firewall.register_feature(tier_a)
        firewall.register_feature(tier_c)

        conf_a_only = firewall.compute_confidence({"real_dom_bids": tier_a.value})
        conf_with_c = firewall.compute_confidence(
            {"real_dom_bids": tier_a.value, "estimated_delta": tier_c.value}
        )

        # Tier C must never increase confidence (it can only dilute or be ignored).
        self.assertLessEqual(conf_with_c, conf_a_only)

    def test_validate_decision_input_blocks_tier_c(self) -> None:
        firewall = ProvenanceFirewall()
        tier_c = create_tagged_feature(
            name="simulated_dom",
            value={"bids": [], "asks": []},
            source="candle_estimation",
        )
        firewall.register_feature(tier_c)
        with self.assertRaises(ProvenanceViolationError):
            firewall.validate_decision_input(["simulated_dom"])


class _FakeRealProvider(MarketDataProvider):
    venue_name = "fake"
    is_real = True

    @classmethod
    def supports_symbol(cls, symbol: str) -> bool:
        return True

    async def start(self) -> bool:
        self.state = FeedState.CONNECTED
        now = datetime.now(timezone.utc)
        self.latest_snapshot = RealDOMSnapshot(
            symbol=self.symbol,
            venue=self.venue_name,
            timestamp=now,
            bids=[DOMLevel(price=100.0, size=1.0, is_bid=True, timestamp=now)],
            asks=[DOMLevel(price=100.1, size=1.0, is_bid=False, timestamp=now)],
            spread=0.1,
            mid_price=100.05,
            book_imbalance=0.0,
            total_bid_size=1.0,
            total_ask_size=1.0,
            liquidity_walls=[],
            is_real=True,
        )
        self.consecutive_valid_snapshots = int(os.environ.get("DOM_SNAPSHOT_WARMUP", "10"))
        self.snapshots_received += 1
        return True

    async def stop(self) -> None:
        self.state = FeedState.DISCONNECTED


class _FakeNoDOMProvider(MarketDataProvider):
    venue_name = "no_dom"
    is_real = False

    @classmethod
    def supports_symbol(cls, symbol: str) -> bool:
        return True

    async def start(self) -> bool:
        self.state = FeedState.CONNECTED
        self.latest_snapshot = None
        return True

    async def stop(self) -> None:
        self.state = FeedState.DISCONNECTED


class TestRealDOMFailClosed(unittest.TestCase):
    def setUp(self) -> None:
        self._env_before = dict(os.environ)
        os.environ["REAL_DOM"] = "true"
        os.environ["DOM_SNAPSHOT_WARMUP"] = "1"
        os.environ["DOM_STALE_THRESHOLD_SEC"] = "1"

    def tearDown(self) -> None:
        os.environ.clear()
        os.environ.update(self._env_before)

    def test_fail_closed_blocks_unqualified_provider(self) -> None:
        reg = MarketDataRegistry()
        reg.override_provider("SPY", _FakeNoDOMProvider("SPY"))
        res = reg.fail_closed_check("SPY")
        self.assertFalse(res["allowed"])
        self.assertIn("No qualified real DOM provider", res["reason"])

    def test_fail_closed_blocks_disconnected_real_provider(self) -> None:
        reg = MarketDataRegistry()
        p = _FakeRealProvider("BTCUSDT")
        p.state = FeedState.DISCONNECTED
        reg.override_provider("BTCUSDT", p)
        res = reg.fail_closed_check("BTCUSDT")
        self.assertFalse(res["allowed"])
        self.assertIn("not connected", res["reason"])

    def test_fail_closed_blocks_stale_provider(self) -> None:
        reg = MarketDataRegistry()
        p = _FakeRealProvider("BTCUSDT")
        now = datetime.now(timezone.utc)
        p.state = FeedState.CONNECTED
        p.latest_snapshot = RealDOMSnapshot(
            symbol="BTCUSDT",
            venue=p.venue_name,
            timestamp=now - timedelta(seconds=10),
            bids=[],
            asks=[],
            spread=0.0,
            mid_price=0.0,
            book_imbalance=0.0,
            total_bid_size=0.0,
            total_ask_size=0.0,
            liquidity_walls=[],
            is_real=True,
        )
        p.consecutive_valid_snapshots = 1
        reg.override_provider("BTCUSDT", p)
        res = reg.fail_closed_check("BTCUSDT")
        self.assertFalse(res["allowed"])
        self.assertIn("stale", res["reason"].lower())


class TestWhyWaitPins(unittest.TestCase):
    def test_pin_schema_and_sorting(self) -> None:
        dom_check = {"allowed": False, "reason": "DOM feed not connected", "provider": "binance", "state": "DISCONNECTED"}
        why = generate_why_wait(
            bar_index=123,
            dom_check=dom_check,
            has_tier_ab_features=False,
            synthetic_conflict={"signal_a": "VP: BULL", "signal_b": "Delta: BEAR", "resolution": "cancelled_out"},
            current_price=1.2345,
        )
        pins = [p.to_dict() for p in why.top_pins(limit=3)]

        self.assertTrue(pins)
        for p in pins:
            for k in ["pin_id", "pin_type", "bar_indices", "feature_name", "description", "severity", "zone"]:
                self.assertIn(k, p)
            self.assertIsInstance(p["bar_indices"], list)

        # Severity should be non-increasing.
        severities = [p["severity"] for p in pins]
        self.assertEqual(severities, sorted(severities, reverse=True))


if __name__ == "__main__":
    unittest.main()

