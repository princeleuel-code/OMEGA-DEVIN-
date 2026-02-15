import json
import tempfile
import unittest
from pathlib import Path


from agents.evolution_loop import EvalReport, EvolutionConfig, EvolutionLoop, EvolutionLoopConfig, FoldResult


class _ReliabilityHarnessConfig:
    def __init__(self, spread_pips: float = 1.0, slippage_pips: float = 0.5):
        self.spread_pips = spread_pips
        self.slippage_pips = slippage_pips
        self.commission_per_lot = 0.0
        self.test_bars = 10


class _FlakyHarness:
    def __init__(self, fail_times: int = 0):
        self.fail_times = int(fail_times)
        self.calls = 0
        self.config = _ReliabilityHarnessConfig()

    def evaluate(self, variant_config, data, manifest, variant_id=None):  # type: ignore[no-untyped-def]
        self.calls += 1
        if self.calls <= self.fail_times:
            raise RuntimeError("transient feed disconnect")

        metrics = {
            "sharpe": 1.4,
            "net_return": 2.5,
            "max_drawdown": 1.2,
            "turnover": 8.0,
        }
        fold = FoldResult(
            fold_id=0,
            train_start="0",
            train_end="10",
            test_start="10",
            test_end="20",
            regime="trend",
            metrics=metrics,
            passed=True,
            fail_reasons=[],
        )
        return EvalReport(
            variant_id=variant_id or "stub",
            manifest_id=manifest.run_id,
            evaluated_at="stub",
            folds=[fold],
            aggregate_metrics=metrics,
            passed_all_gates=True,
            gate_results={"all_folds_passed": True, "min_sharpe": True},
            integrity_violations=[],
        )


class _AlwaysPassChampionTester:
    def test_against_champions(self, **kwargs):  # type: ignore[no-untyped-def]
        return True, {"passed": True}

    def add_to_history(self, config, fitness):  # type: ignore[no-untyped-def]
        return None


def _toy_data(n: int = 200):
    out = []
    base = 100.0
    for i in range(n):
        px = base + i * 0.01
        out.append(
            {
                "timestamp": f"2024-01-01T{i:05d}",
                "open": px,
                "high": px * 1.001,
                "low": px * 0.999,
                "close": px * 1.0002,
                "volume": 1000,
            }
        )
    return out


class TestSakanaReliability(unittest.TestCase):
    def test_retry_recovers_after_transient_error(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            loop = EvolutionLoop(
                config=EvolutionLoopConfig(
                    variants_per_round=1,
                    max_rounds=1,
                    output_dir=tmp,
                    attack_enabled=False,
                    eval_retry_attempts=2,
                    eval_retry_backoff_seconds=0.0,
                )
            )
            loop.harness = _FlakyHarness(fail_times=1)
            loop.champion_tester = _AlwaysPassChampionTester()

            summary = loop.run(data=_toy_data(), max_rounds=1)
            self.assertEqual(summary["total_variants_evaluated"], 1)
            self.assertGreaterEqual(summary["archive_size"], 1)

            failure_path = Path(tmp) / "FAILURE_ARCHIVE.jsonl"
            self.assertTrue(failure_path.exists())
            reasons = {json.loads(line)["reason"] for line in failure_path.read_text().splitlines() if line.strip()}
            self.assertIn("EVALUATION_EXCEPTION", reasons)
            self.assertIn("RECOVERED_AFTER_RETRY", reasons)

    def test_watchdog_and_round_memory_written(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            loop = EvolutionLoop(
                config=EvolutionLoopConfig(
                    variants_per_round=1,
                    max_rounds=1,
                    output_dir=tmp,
                    attack_enabled=False,
                    watchdog_enabled=True,
                    long_horizon_memory_enabled=True,
                )
            )
            loop.harness = _FlakyHarness(fail_times=0)
            loop.champion_tester = _AlwaysPassChampionTester()

            loop.run(data=_toy_data(), max_rounds=1)

            watchdog_path = Path(tmp) / "WATCHDOG_HEARTBEAT.json"
            memory_path = Path(tmp) / "ROUND_MEMORY.jsonl"
            self.assertTrue(watchdog_path.exists())
            self.assertTrue(memory_path.exists())
            self.assertIn("RUN_COMPLETE", watchdog_path.read_text())
            self.assertGreater(len(memory_path.read_text().splitlines()), 0)

    def test_auto_resume_uses_existing_champion(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            champion = EvolutionConfig().to_dict()
            champion["rl_epsilon_start"] = 0.77
            Path(tmp, "CHAMPION_CONFIG.json").write_text(json.dumps(champion, indent=2))

            loop = EvolutionLoop(
                config=EvolutionLoopConfig(
                    variants_per_round=0,
                    max_rounds=1,
                    output_dir=tmp,
                    attack_enabled=False,
                    auto_resume=True,
                )
            )
            loop.harness = _FlakyHarness(fail_times=0)

            summary = loop.run(data=_toy_data(80), initial_config=None, max_rounds=1)
            self.assertTrue(summary["resumed_from_state"])
            self.assertAlmostEqual(summary["final_champion"]["rl_epsilon_start"], 0.77, places=6)


if __name__ == "__main__":
    unittest.main()
