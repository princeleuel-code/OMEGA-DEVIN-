import unittest
from datetime import datetime, timedelta


from chimera.data.loader import OHLCV
from chimera.evaluation.backtest import BacktestConfig
from chimera.evaluation.robustness import (
    permute_ohlcv_returns,
    permutation_test,
    reality_check_bootstrap_max,
    robustness_report,
)
from chimera.evolution.genome import create_default_genome


class TestRobustnessSuite(unittest.TestCase):
    def _toy_bars(self) -> list[OHLCV]:
        # Deterministic price path with varying returns.
        ts = datetime(2024, 1, 1)
        closes = [100.0, 110.0, 100.0, 105.0, 90.0]
        bars: list[OHLCV] = []
        for i, c in enumerate(closes):
            bars.append(
                OHLCV(
                    timestamp=ts + timedelta(hours=i),
                    open=c,
                    high=c * 1.01,
                    low=c * 0.99,
                    close=c,
                    volume=1.0,
                    symbol="TEST",
                )
            )
        return bars

    def test_permute_ohlcv_returns_deterministic(self) -> None:
        bars = self._toy_bars()
        p1 = permute_ohlcv_returns(bars, seed=1)
        p2 = permute_ohlcv_returns(bars, seed=1)
        p3 = permute_ohlcv_returns(bars, seed=2)
        self.assertEqual([b.close for b in p1], [b.close for b in p2])
        self.assertNotEqual([b.close for b in p1], [b.close for b in p3])

    def test_permutation_test_bounds(self) -> None:
        res = permutation_test([1.0, 2.0, 3.0], permutations=50, seed=123)
        self.assertIn("p_value", res)
        p = float(res["p_value"])  # type: ignore[arg-type]
        self.assertGreaterEqual(p, 0.0)
        self.assertLessEqual(p, 1.0)

    def test_reality_check_shapes(self) -> None:
        s1 = [0.0, 0.0, 0.0, 0.0]
        s2 = [0.1, -0.1, 0.1, -0.1]
        rc = reality_check_bootstrap_max([s1, s2], bootstrap_samples=50, seed=7)
        self.assertGreaterEqual(rc.p_value, 0.0)
        self.assertLessEqual(rc.p_value, 1.0)
        self.assertEqual(rc.strategies, 2)

    def test_robustness_report_runs(self) -> None:
        bars = self._toy_bars() * 40  # enough for features/backtest
        genome = create_default_genome()
        cfg = BacktestConfig(symbol="EURUSD", spread_pips=1.0)
        rep = robustness_report(bars=bars, genome=genome, backtest_config=cfg, permutations=5, seed=1)
        self.assertIn("observed", rep)
        self.assertIn("permutation_null", rep)


if __name__ == "__main__":
    unittest.main()

