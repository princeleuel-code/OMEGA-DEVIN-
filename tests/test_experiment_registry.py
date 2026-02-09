import tempfile
import unittest
from pathlib import Path

from agent.registry import ExperimentRegistry, ExperimentRow


class TestExperimentRegistry(unittest.TestCase):
    def test_upsert_get_leaderboard(self):
        with tempfile.TemporaryDirectory() as td:
            db = Path(td) / "exp.sqlite"
            reg = ExperimentRegistry(db)
            try:
                row = ExperimentRow(
                    experiment_id="exp1",
                    run_id="runA",
                    created_at="2026-02-09T00:00:00Z",
                    symbol="XAUUSD",
                    timeframe="1h",
                    dataset_hash="hash",
                    genome_id="genome_x",
                    passed=True,
                    score=1.23,
                    fail_reasons=[],
                    artifacts_dir="/tmp/exp1",
                    genome_json={"genome_id": "genome_x"},
                    results_json={"scorecard": {"fitness": 1.23}},
                )
                reg.upsert(row)

                got = reg.get("exp1")
                self.assertIsNotNone(got)
                self.assertTrue(got["passed"])
                self.assertEqual(got["symbol"], "XAUUSD")

                lb = reg.leaderboard(symbol="XAUUSD", timeframe="1h", limit=10)
                self.assertEqual(len(lb), 1)
                self.assertEqual(lb[0]["experiment_id"], "exp1")
            finally:
                reg.close()


if __name__ == "__main__":
    unittest.main()

