import math
import unittest
from datetime import datetime, timedelta

from chimera.data.features import FeatureEngine
from chimera.data.loader import OHLCV
from chimera.intelligence.aether_indicator import AetherIndicator


def _bars_with_shock(n: int = 180) -> list[OHLCV]:
    out: list[OHLCV] = []
    ts = datetime(2024, 1, 1)
    close = 100.0

    for i in range(n):
        prev = close
        if i < 80:
            delta = 0.15 * math.sin(i * 0.3)
        elif i < 120:
            delta = 1.8 if i % 2 == 0 else -1.8
        else:
            delta = 0.08 * math.sin(i * 0.5)

        close = max(1.0, close + delta)
        high = max(prev, close) + 0.2
        low = min(prev, close) - 0.2
        volume = 1000.0 + (300.0 if i % 3 == 0 else 0.0) + (1200.0 if 80 <= i < 120 else 0.0)
        out.append(
            OHLCV(
                timestamp=ts + timedelta(minutes=i),
                open=prev,
                high=high,
                low=low,
                close=close,
                volume=volume,
                symbol="TEST",
            )
        )
    return out


class TestAetherIndicator(unittest.TestCase):
    def test_indicator_outputs_valid_state_bounds(self) -> None:
        bars = _bars_with_shock()
        series = AetherIndicator().compute(bars)
        self.assertEqual(len(series), len(bars))
        self.assertGreater(len(series), 50)

        for st in series[-30:]:
            self.assertGreaterEqual(st.s_entropy, 0.0)
            self.assertLessEqual(st.s_entropy, 1.0)
            self.assertGreaterEqual(st.cycle_confidence, 0.0)
            self.assertLessEqual(st.cycle_confidence, 1.0)
            self.assertGreaterEqual(st.node_coherence, 0.0)
            self.assertLessEqual(st.node_coherence, 1.0)
            self.assertGreaterEqual(st.force, -1.0)
            self.assertLessEqual(st.force, 1.0)
            self.assertIn(st.stamp, {"SPEAR", "SHIELD", "GHOST"})
            self.assertIn(st.regime, {"HARMONIC", "STABLE", "TRANSITION", "DIFFUSE", "CRISIS"})

    def test_indicator_detects_seam_on_volatility_shock(self) -> None:
        bars = _bars_with_shock()
        series = AetherIndicator().compute(bars)
        seam_count = sum(1 for st in series[80:130] if st.seam)
        self.assertGreater(seam_count, 0)

    def test_feature_engine_embeds_aether_payload(self) -> None:
        bars = _bars_with_shock()
        feats = FeatureEngine().compute(bars)
        self.assertGreater(len(feats), 0)
        payload = feats[-1].aether
        self.assertIsInstance(payload, dict)
        assert payload is not None
        for key in ["S", "dS", "F", "P", "Pc", "N", "LOCK", "SEAM", "STAMP", "TRIGGER", "REGIME"]:
            self.assertIn(key, payload)


if __name__ == "__main__":
    unittest.main()
