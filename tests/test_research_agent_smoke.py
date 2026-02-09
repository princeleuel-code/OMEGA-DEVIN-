import random
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pandas as pd

from agent.orchestrator import EvaluationConfig, PlannerConfig, ResearchAgent, ResearchAgentConfig
from agent.registry import ExperimentRegistry
from chimera.evaluation.walk_forward import WalkForwardConfig


class TestResearchAgentSmoke(unittest.TestCase):
    def _make_bars(self, n: int = 220) -> pd.DataFrame:
        random.seed(7)
        start = datetime(2025, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
        ts = [start + timedelta(hours=i) for i in range(n)]
        price = 1.0
        rows = []
        for _ in range(n):
            o = price
            c = o + random.gauss(0.0, 0.01)
            h = max(o, c) + abs(random.gauss(0.0, 0.005))
            l = min(o, c) - abs(random.gauss(0.0, 0.005))
            rows.append({"open": o, "high": h, "low": l, "close": c, "volume": 1000.0})
            price = c
        df = pd.DataFrame(rows, index=pd.DatetimeIndex(ts))
        return df

    def test_runs_one_experiment(self):
        bars = self._make_bars()
        dataset_hash = "TEST_HASH"
        with tempfile.TemporaryDirectory() as td:
            run_dir = Path(td) / "rqra_test_run"
            reg = ExperimentRegistry(Path(td) / "exp.sqlite")

            cfg = ResearchAgentConfig(
                symbol="EURUSD",
                timeframe="1h",
                planner=PlannerConfig(seed=1, max_experiments=1, max_depth=0),
                evaluation=EvaluationConfig(
                    wf=WalkForwardConfig(n_folds=1, train_bars=80, test_bars=40, purge_bars=5, bootstrap_samples=10),
                    robustness_permutations=5,
                    mc_simulations=20,
                    stability_variants=2,
                ),
            )

            agent = ResearchAgent(
                config=cfg,
                bars=bars,
                dataset_hash=dataset_hash,
                run_dir=run_dir,
                repo_root=Path(__file__).resolve().parents[1],
                registry=reg,
            )
            report = agent.run()
            self.assertEqual(report["experiments_total"], 1)
            self.assertTrue((run_dir / "run_report.json").exists())

            lb = reg.leaderboard(symbol="EURUSD", timeframe="1h", limit=10, passed_only=False)
            self.assertEqual(len(lb), 1)
            reg.close()


if __name__ == "__main__":
    unittest.main()
