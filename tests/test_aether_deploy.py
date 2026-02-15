import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from run import run_aether_canary_update, run_aether_deploy


def _research_payload(*, edge: bool) -> dict:
    return {
        "meta": {
            "timestamp": "2026-02-15T00:00:00Z",
            "symbol": "XAUUSD",
        },
        "champion": {
            "aether_gate": {
                "entropy_max": 0.95,
                "coherence_min": 0.15,
                "pc_min": 0.0,
                "force_min": 0.0,
                "block_on_seam": True,
                "seam_force_override": 0.45,
            }
        },
        "oos_policy": {"min_pass_rate": 0.6},
        "oos_evaluation": {"verdict": "EDGE_CONFIRMED" if edge else "NO_EDGE"},
        "verdict": {
            "label": "EDGE_CONFIRMED" if edge else "NO_EDGE",
            "claim_edge": edge,
        },
    }


class TestAetherDeploy(unittest.TestCase):
    def test_deploy_refuses_when_report_is_no_edge(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            report = tmp / "report.json"
            report.write_text(json.dumps(_research_payload(edge=False), indent=2))
            out_dir = tmp / "live"

            rc = run_aether_deploy(
                SimpleNamespace(
                    research=str(report),
                    genome=None,
                    output_dir=str(out_dir),
                    canary_mode="paper",
                    canary_trades_required=10,
                    canary_max_dd=5.0,
                    anomaly_threshold=3.0,
                    previous_variant_id=None,
                    allow_no_edge=False,
                )
            )
            self.assertEqual(rc, 2)
            self.assertFalse((out_dir / "LIVE_GATING_STATE.json").exists())

    def test_deploy_writes_champion_and_live_state(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            report = tmp / "report.json"
            report.write_text(json.dumps(_research_payload(edge=True), indent=2))
            out_dir = tmp / "live"

            rc = run_aether_deploy(
                SimpleNamespace(
                    research=str(report),
                    genome=None,
                    output_dir=str(out_dir),
                    canary_mode="paper",
                    canary_trades_required=10,
                    canary_max_dd=5.0,
                    anomaly_threshold=3.0,
                    previous_variant_id=None,
                    allow_no_edge=False,
                )
            )
            self.assertEqual(rc, 0)

            champion = json.loads((out_dir / "CHAMPION_GENOME.json").read_text())
            self.assertTrue(champion["use_aether_gate"])
            self.assertAlmostEqual(champion["aether_entropy_max"], 0.95)
            self.assertAlmostEqual(champion["aether_coherence_min"], 0.15)

            state = json.loads((out_dir / "LIVE_GATING_STATE.json").read_text())
            self.assertEqual(state["canary_mode"], "paper")
            self.assertFalse(state["kill_switch_active"])
            self.assertAlmostEqual(state["max_drawdown_threshold"], 5.0)

            deploy = json.loads((out_dir / "AETHER_DEPLOYMENT.json").read_text())
            self.assertEqual(deploy["meta"]["source_verdict"], "EDGE_CONFIRMED")
            self.assertEqual(deploy["canary"]["mode"], "paper")

    def test_canary_update_promotes_and_kills(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            report = tmp / "report.json"
            report.write_text(json.dumps(_research_payload(edge=True), indent=2))
            out_dir = tmp / "live"

            rc = run_aether_deploy(
                SimpleNamespace(
                    research=str(report),
                    genome=None,
                    output_dir=str(out_dir),
                    canary_mode="paper",
                    canary_trades_required=10,
                    canary_max_dd=5.0,
                    anomaly_threshold=3.0,
                    previous_variant_id=None,
                    allow_no_edge=False,
                )
            )
            self.assertEqual(rc, 0)
            state_path = out_dir / "LIVE_GATING_STATE.json"

            rc = run_aether_canary_update(
                SimpleNamespace(
                    state=str(state_path),
                    trades=10,
                    pnl=100.0,
                    max_dd=1.0,
                    anomaly_score=None,
                    canary_trades_required=10,
                    min_pnl_to_promote=0.0,
                )
            )
            self.assertEqual(rc, 0)
            state = json.loads(state_path.read_text())
            self.assertEqual(state["canary_mode"], "micro")

            rc = run_aether_canary_update(
                SimpleNamespace(
                    state=str(state_path),
                    trades=20,
                    pnl=120.0,
                    max_dd=2.0,
                    anomaly_score=None,
                    canary_trades_required=10,
                    min_pnl_to_promote=0.0,
                )
            )
            self.assertEqual(rc, 0)
            state = json.loads(state_path.read_text())
            self.assertEqual(state["canary_mode"], "full")
            self.assertFalse(state["kill_switch_active"])

            rc = run_aether_canary_update(
                SimpleNamespace(
                    state=str(state_path),
                    trades=21,
                    pnl=70.0,
                    max_dd=9.0,
                    anomaly_score=None,
                    canary_trades_required=10,
                    min_pnl_to_promote=0.0,
                )
            )
            self.assertEqual(rc, 0)
            state = json.loads(state_path.read_text())
            self.assertTrue(state["kill_switch_active"])
            self.assertEqual(state["canary_mode"], "off")
            self.assertIn("MAX_DD_BREACH", state["kill_switch_reason"])


if __name__ == "__main__":
    unittest.main()
