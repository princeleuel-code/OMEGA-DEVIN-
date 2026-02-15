import json
import tempfile
import unittest
from pathlib import Path


from agents.evolution_loop import EvalReport, EvolutionLoop, EvolutionLoopConfig, FoldResult


class _AttackHarnessConfig:
    def __init__(self, spread_pips: float = 1.0, slippage_pips: float = 0.5):
        self.spread_pips = spread_pips
        self.slippage_pips = slippage_pips
        self.commission_per_lot = 0.0
        self.test_bars = 10


class _AttackHarness:
    """Harness stub that can deterministically fail under stressed costs."""

    def __init__(self, fail_under_stress: bool, spread_pips: float = 1.0, slippage_pips: float = 0.5):
        self.fail_under_stress = fail_under_stress
        self.config = _AttackHarnessConfig(spread_pips=spread_pips, slippage_pips=slippage_pips)

    def clone_with_costs(self, spread_mult: float, slippage_mult: float):  # type: ignore[no-untyped-def]
        return _AttackHarness(
            fail_under_stress=self.fail_under_stress,
            spread_pips=self.config.spread_pips * spread_mult,
            slippage_pips=self.config.slippage_pips * slippage_mult,
        )

    def evaluate(self, variant_config, data, manifest, variant_id=None):  # type: ignore[no-untyped-def]
        stressed = self.config.spread_pips > 1.0
        passed = not (self.fail_under_stress and stressed)

        metrics = {
            "sharpe": 1.2 if passed else -0.4,
            "net_return": 2.0 if passed else -1.0,
            "max_drawdown": 2.0 if passed else 12.0,
            "turnover": 7.0,
        }
        fold = FoldResult(
            fold_id=0,
            train_start="0",
            train_end="10",
            test_start="10",
            test_end="20",
            regime="trend",
            metrics=metrics,
            passed=passed,
            fail_reasons=[] if passed else ["ATTACK_STRESS_FAIL"],
        )
        return EvalReport(
            variant_id=variant_id or "stub",
            manifest_id=manifest.run_id,
            evaluated_at="stub",
            folds=[fold],
            aggregate_metrics=metrics,
            passed_all_gates=passed,
            gate_results={"all_folds_passed": passed, "min_sharpe": passed},
            integrity_violations=[],
        )


class _AlwaysPassChampionTester:
    def test_against_champions(self, **kwargs):  # type: ignore[no-untyped-def]
        return True, {"passed": True}

    def add_to_history(self, config, fitness):  # type: ignore[no-untyped-def]
        return None


def _toy_data(n: int = 200):
    base = 100.0
    out = []
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


class TestSakanaAttackPhase(unittest.TestCase):
    def test_aether_attack_scenarios_are_built(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            loop = EvolutionLoop(
                config=EvolutionLoopConfig(
                    variants_per_round=1,
                    max_rounds=1,
                    output_dir=tmp,
                    attack_enabled=True,
                    attack_aether_enabled=True,
                    attack_aether_window_bars=160,
                    attack_entropy_window=32,
                )
            )
            loop.harness = _AttackHarness(fail_under_stress=False)
            scenarios = loop._build_attack_scenarios(_toy_data(400), variant_id="abc123")
            names = {s["name"] for s in scenarios}
            self.assertTrue(any(name.startswith("AETHER_") for name in names))

    def test_attack_failure_blocks_promotion_and_archival(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            loop = EvolutionLoop(
                config=EvolutionLoopConfig(
                    variants_per_round=1,
                    max_rounds=1,
                    output_dir=tmp,
                    attack_enabled=True,
                    attack_min_pass_rate=1.0,
                )
            )
            loop.harness = _AttackHarness(fail_under_stress=True)
            loop.champion_tester = _AlwaysPassChampionTester()

            summary = loop.run(data=_toy_data(), max_rounds=1)

            self.assertEqual(summary["total_variants_evaluated"], 1)
            self.assertEqual(summary["archive_size"], 0)
            self.assertIsNotNone(loop.live_state)
            self.assertEqual(loop.live_state.active_variant_id, "initial")

            failure_path = Path(tmp) / "FAILURE_ARCHIVE.jsonl"
            self.assertTrue(failure_path.exists())
            stages = {json.loads(line)["stage"] for line in failure_path.read_text().splitlines() if line.strip()}
            self.assertIn("ATTACK", stages)

    def test_attack_success_allows_promotion(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            loop = EvolutionLoop(
                config=EvolutionLoopConfig(
                    variants_per_round=1,
                    max_rounds=1,
                    output_dir=tmp,
                    attack_enabled=True,
                    attack_min_pass_rate=1.0,
                )
            )
            loop.harness = _AttackHarness(fail_under_stress=False)
            loop.champion_tester = _AlwaysPassChampionTester()

            summary = loop.run(data=_toy_data(), max_rounds=1)

            self.assertEqual(summary["total_variants_evaluated"], 1)
            self.assertGreaterEqual(summary["archive_size"], 1)
            self.assertIsNotNone(loop.live_state)
            self.assertNotEqual(loop.live_state.active_variant_id, "initial")


if __name__ == "__main__":
    unittest.main()
