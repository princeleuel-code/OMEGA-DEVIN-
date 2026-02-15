import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from run import run_aether_deploy, run_aether_supervise


def _research_payload() -> dict:
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
        "oos_evaluation": {"verdict": "EDGE_CONFIRMED"},
        "verdict": {
            "label": "EDGE_CONFIRMED",
            "claim_edge": True,
        },
    }


class TestAetherSupervisor(unittest.TestCase):
    def _deploy_state(self, tmp: Path) -> Path:
        report = tmp / "report.json"
        report.write_text(json.dumps(_research_payload(), indent=2))
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
        return out_dir / "LIVE_GATING_STATE.json"

    def test_supervisor_updates_state_from_feed(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            state_path = self._deploy_state(tmp)
            feed_path = tmp / "feed.json"
            feed_path.write_text(json.dumps({"trades": 10, "pnl": 25.0, "max_dd": 1.2}))

            hb = tmp / "hb.json"
            log = tmp / "supervisor.jsonl"
            rc = run_aether_supervise(
                SimpleNamespace(
                    state=str(state_path),
                    feed=str(feed_path),
                    interval_seconds=0.0,
                    max_iterations=1,
                    require_fresh_seconds=0.0,
                    update_on_unchanged=False,
                    canary_trades_required=10,
                    min_pnl_to_promote=0.0,
                    max_errors=5,
                    no_stop_on_kill_switch=False,
                    heartbeat=str(hb),
                    log=str(log),
                )
            )
            self.assertEqual(rc, 0)
            state = json.loads(state_path.read_text())
            self.assertEqual(state["canary_mode"], "micro")
            self.assertFalse(state["kill_switch_active"])

            beat = json.loads(hb.read_text())
            self.assertEqual(beat["status"], "UPDATED")
            self.assertEqual(beat["live_state"]["canary_mode"], "micro")
            self.assertTrue(log.exists())

    def test_supervisor_stops_when_kill_switch_activates(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            state_path = self._deploy_state(tmp)
            feed_path = tmp / "feed.json"
            feed_path.write_text(json.dumps({"trades": 3, "pnl": -40.0, "max_dd": 9.5}))

            hb = tmp / "hb.json"
            log = tmp / "supervisor.jsonl"
            rc = run_aether_supervise(
                SimpleNamespace(
                    state=str(state_path),
                    feed=str(feed_path),
                    interval_seconds=0.0,
                    max_iterations=0,
                    require_fresh_seconds=0.0,
                    update_on_unchanged=False,
                    canary_trades_required=10,
                    min_pnl_to_promote=0.0,
                    max_errors=5,
                    no_stop_on_kill_switch=False,
                    heartbeat=str(hb),
                    log=str(log),
                )
            )
            self.assertEqual(rc, 3)
            state = json.loads(state_path.read_text())
            self.assertTrue(state["kill_switch_active"])
            self.assertEqual(state["canary_mode"], "off")
            self.assertIn("MAX_DD_BREACH", state["kill_switch_reason"])

            beat = json.loads(hb.read_text())
            self.assertTrue(beat["live_state"]["kill_switch_active"])
            self.assertTrue(log.exists())


if __name__ == "__main__":
    unittest.main()
