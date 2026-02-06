import unittest


from chimera.evaluation.metrics import PerformanceMetrics


class TestMetricHardening(unittest.TestCase):
    def test_sharpe_zero_for_tiny_nonzero_returns(self) -> None:
        # One non-zero return should not produce a meaningful Sharpe.
        equity = [10000.0] * 100
        equity[50:] = [10500.0] * (100 - 50)

        metrics = PerformanceMetrics.from_equity_curve(
            equity=equity,
            trades=[],
            initial_capital=10000.0,
            bars_per_day=1.0,
            risk_free_rate=0.0,
        )

        self.assertEqual(metrics.sharpe_ratio, 0.0)
        self.assertEqual(metrics.sortino_ratio, 0.0)

    def test_sharpe_capped(self) -> None:
        # Construct a return series with tiny variance but positive mean.
        equity = [10000.0]
        for i in range(200):
            # ~0.10% per bar with tiny jitter.
            r = 0.001 + (1e-6 if i % 2 == 0 else -1e-6)
            equity.append(equity[-1] * (1.0 + r))

        metrics = PerformanceMetrics.from_equity_curve(
            equity=equity,
            trades=[],
            initial_capital=10000.0,
            bars_per_day=1.0,
            risk_free_rate=0.0,
        )

        self.assertLessEqual(abs(metrics.sharpe_ratio), 10.0)
        self.assertLessEqual(abs(metrics.sortino_ratio), 10.0)


if __name__ == "__main__":
    unittest.main()

