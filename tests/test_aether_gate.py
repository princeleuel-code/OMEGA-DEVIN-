import unittest
from datetime import datetime

from chimera.core.decision_engine import Action
from chimera.data.features import Features, MarketStructure, Trend
from chimera.evaluation.backtest import Backtester
from chimera.evolution.genome import create_default_genome
from chimera.execution.router import Router


def _feature_with_aether(payload: dict) -> Features:
    structure = MarketStructure(trend=Trend.BULLISH)
    return Features(
        timestamp=datetime(2024, 1, 1),
        close=100.0,
        atr=0.50,
        volatility=0.40,
        momentum=1.2,
        roc=0.8,
        relative_volume=1.8,
        structure=structure,
        displacement=True,
        displacement_direction=1,
        aether=payload,
    )


def _strict_gate_genome():
    g = create_default_genome()
    g.use_aether_gate = True
    g.aether_entropy_max = 0.50
    g.aether_coherence_min = 0.40
    g.aether_pc_min = 0.40
    g.aether_force_min = 0.25
    g.aether_block_on_seam = True
    g.aether_seam_force_override = 0.55
    g.require_displacement = True
    g.min_confidence = 0.5
    return g


class TestAetherGate(unittest.TestCase):
    def test_router_blocks_untradable_state(self) -> None:
        feat = _feature_with_aether(
            {
                "S": 0.90,  # too noisy
                "N": 0.75,
                "Pc": 0.85,
                "F": 0.60,
                "SEAM": False,
            }
        )
        genome = _strict_gate_genome()
        signal = Router().generate_signal(feat, genome)
        self.assertEqual(signal.action, Action.WAIT)
        self.assertTrue(signal.reasons)
        self.assertIn("AETHER", signal.reasons[0].details or "")

    def test_router_allows_tradable_state(self) -> None:
        feat = _feature_with_aether(
            {
                "S": 0.22,
                "N": 0.65,
                "Pc": 0.70,
                "F": 0.55,
                "SEAM": False,
            }
        )
        genome = _strict_gate_genome()
        signal = Router().generate_signal(feat, genome)
        self.assertEqual(signal.action, Action.LONG)

    def test_backtester_signal_generator_uses_same_gate(self) -> None:
        feat = _feature_with_aether(
            {
                "S": 0.21,
                "N": 0.64,
                "Pc": 0.72,
                "F": 0.50,
                "SEAM": True,
            }
        )
        genome = _strict_gate_genome()

        # Seam with insufficient force override must block.
        signal_blocked = Backtester()._default_signal_generator(feat, genome)
        self.assertEqual(signal_blocked.action, Action.WAIT)
        self.assertIn("seam", (signal_blocked.reasons[0].details or "").lower())

        # Increase force so seam override passes.
        feat.aether["F"] = 0.80
        signal_allowed = Backtester()._default_signal_generator(feat, genome)
        self.assertEqual(signal_allowed.action, Action.LONG)


if __name__ == "__main__":
    unittest.main()

