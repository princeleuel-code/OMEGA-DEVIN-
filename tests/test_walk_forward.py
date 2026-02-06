import unittest


from chimera.data.loader import DataLoader
from chimera.evolution.genome import create_default_genome
from chimera.evaluation.backtest import BacktestConfig
from chimera.evaluation.walk_forward import WalkForwardConfig, walk_forward


class TestWalkForward(unittest.TestCase):
    def test_purge_gap_applied(self) -> None:
        loader = DataLoader(symbol="EURUSD")
        data = loader.generate_synthetic(num_bars=400)

        genome = create_default_genome()
        bt_cfg = BacktestConfig(symbol="EURUSD", spread_pips=1.0, slippage_pips=0.5)
        wf_cfg = WalkForwardConfig(
            train_bars=80,
            test_bars=40,
            purge_bars=5,
            n_folds=2,
            bootstrap_samples=50,  # keep test fast
            min_trades_per_fold=0,  # do not gate on trades for this structural test
        )

        report = walk_forward(data=data, genome=genome, backtest_config=bt_cfg, wf_config=wf_cfg)
        self.assertGreaterEqual(len(report.folds), 1)

        f0 = report.folds[0]
        self.assertEqual(f0.test_start - f0.train_end, wf_cfg.purge_bars)

    def test_costs_required(self) -> None:
        loader = DataLoader(symbol="EURUSD")
        data = loader.generate_synthetic(num_bars=200)
        genome = create_default_genome()

        bt_cfg = BacktestConfig(symbol="EURUSD", spread_pips=0.0, slippage_pips=0.0)
        with self.assertRaises(ValueError):
            walk_forward(data=data, genome=genome, backtest_config=bt_cfg)


if __name__ == "__main__":
    unittest.main()

