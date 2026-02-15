import tempfile
import unittest


from agents.evolution_loop import EvalReport, EvolutionLoop, EvolutionLoopConfig


class _StubHarnessConfig:
    spread_pips = 1.0
    slippage_pips = 0.5
    commission_per_lot = 0.0
    test_bars = 10


class _StubHarness:
    """
    Keep this test fast and deterministic by avoiding the full walk-forward harness.

    We only need to validate that the evolution loop records evaluation attempts
    even when variants fail gates (auditability).
    """

    def __init__(self) -> None:
        self.config = _StubHarnessConfig()

    def evaluate(self, variant_config, data, manifest, variant_id=None):  # type: ignore[no-untyped-def]
        return EvalReport(
            variant_id=variant_id or "stub",
            manifest_id=manifest.run_id,
            evaluated_at="stub",
            folds=[],
            aggregate_metrics={},
            passed_all_gates=False,
            gate_results={},
            integrity_violations=[],
        )


class TestSakanaEvolutionCounts(unittest.TestCase):
    def test_variants_evaluated_counts_failures(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            loop = EvolutionLoop(
                config=EvolutionLoopConfig(
                    variants_per_round=3,
                    max_rounds=1,
                    output_dir=tmp,
                )
            )
            loop.harness = _StubHarness()

            summary = loop.run(data=[{"i": i} for i in range(50)], max_rounds=1)
            self.assertEqual(summary["total_variants_evaluated"], 3)


if __name__ == "__main__":
    unittest.main()
