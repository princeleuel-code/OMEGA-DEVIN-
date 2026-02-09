import unittest

from eval.trade_order_mc import trade_order_monte_carlo


class TestTradeOrderMonteCarlo(unittest.TestCase):
    def test_deterministic(self):
        rets = [10.0, -5.0, 2.0, 1.0]
        r1 = trade_order_monte_carlo(rets, initial_capital=1000.0, simulations=50, seed=123)
        r2 = trade_order_monte_carlo(rets, initial_capital=1000.0, simulations=50, seed=123)
        self.assertEqual(r1, r2)
        self.assertIn("observed", r1)
        self.assertIn("final_equity", r1)
        self.assertIn("max_drawdown_pct", r1)
        self.assertEqual(r1["simulations"], 50)


if __name__ == "__main__":
    unittest.main()

