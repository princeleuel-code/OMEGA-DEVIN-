import unittest


from chimera.orderflow.imbalance_bars import build_tick_imbalance_bars
from chimera.orderflow.vpin import Trade


class TestTickImbalanceBars(unittest.TestCase):
    def test_builds_bars_on_threshold(self) -> None:
        # Construct a tape that hits imbalance_threshold=3 twice.
        trades = [
            Trade(price=100.0, size=1.0, is_buy=True),
            Trade(price=100.1, size=1.0, is_buy=True),
            Trade(price=100.2, size=1.0, is_buy=True),  # imbalance=3 -> bar closes
            Trade(price=100.3, size=1.0, is_buy=False),
            Trade(price=100.2, size=1.0, is_buy=False),
            Trade(price=100.1, size=1.0, is_buy=False),  # imbalance=-3 -> bar closes
        ]

        bars = build_tick_imbalance_bars(trades, imbalance_threshold=3, min_trades_per_bar=1)
        self.assertEqual(len(bars), 2)
        self.assertEqual(bars[0].tick_imbalance, 3)
        self.assertEqual(bars[1].tick_imbalance, -3)
        self.assertAlmostEqual(bars[0].open, 100.0)
        self.assertAlmostEqual(bars[0].close, 100.2)
        self.assertAlmostEqual(bars[1].open, 100.3)
        self.assertAlmostEqual(bars[1].close, 100.1)


if __name__ == "__main__":
    unittest.main()

