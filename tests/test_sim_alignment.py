import sys
import unittest
from pathlib import Path


_BACKEND_ROOT = Path(__file__).resolve().parents[1] / "omega_ui" / "omega_backend"
sys.path.insert(0, str(_BACKEND_ROOT))


from app.sim_alignment import maybe_align_history_to_mid  # noqa: E402


class TestSimAlignment(unittest.TestCase):
    def test_align_shifts_history_to_mid(self) -> None:
        sym = "TESTUSDT"
        history = [
            {"open": 44900.0, "high": 45100.0, "low": 44800.0, "close": 45000.0, "volume": 1},
            {"open": 45000.0, "high": 45200.0, "low": 44950.0, "close": 45050.0, "volume": 1},
        ]
        aligned = set()
        current_prices = {sym: float(history[-1]["close"])}

        mid = 69000.0
        did_align = maybe_align_history_to_mid(
            sym,
            history,
            mid,
            aligned=aligned,
            current_prices=current_prices,
            threshold_ratio=0.0,  # force shift for test determinism
        )

        self.assertTrue(did_align)
        self.assertAlmostEqual(float(history[-1]["close"]), mid, places=6)
        self.assertAlmostEqual(float(current_prices[sym]), mid, places=6)

    def test_align_is_one_time(self) -> None:
        sym = "TEST2USDT"
        history = [{"open": 100.0, "high": 101.0, "low": 99.0, "close": 100.0, "volume": 1}]
        aligned = set()
        current_prices = {sym: 100.0}

        self.assertTrue(
            maybe_align_history_to_mid(
                sym,
                history,
                200.0,
                aligned=aligned,
                current_prices=current_prices,
                threshold_ratio=0.0,
            )
        )
        close_after_first = float(history[-1]["close"])

        # Second call should be a no-op for the same symbol.
        self.assertFalse(
            maybe_align_history_to_mid(
                sym,
                history,
                300.0,
                aligned=aligned,
                current_prices=current_prices,
                threshold_ratio=0.0,
            )
        )
        self.assertAlmostEqual(float(history[-1]["close"]), close_after_first, places=6)


if __name__ == "__main__":
    unittest.main()

