import unittest

from chimera.evaluation.walk_forward import WalkForwardFold, WalkForwardReport
from run import evaluate_oos_edge_policy


def _mk_report(
    *,
    pass_rate: float,
    avg_sharpe: float,
    avg_return: float,
    worst_drawdown: float,
    return_ci_lower,
    passed_all_gates: bool,
    trades_per_fold: list[int],
    no_trade_rates: list[float],
) -> WalkForwardReport:
    folds = []
    for idx, (trades, no_trade_rate) in enumerate(zip(trades_per_fold, no_trade_rates)):
        folds.append(
            WalkForwardFold(
                fold_id=idx,
                train_start=idx * 10,
                train_end=idx * 10 + 5,
                test_start=idx * 10 + 6,
                test_end=idx * 10 + 9,
                metrics={
                    "total_trades": trades,
                    "no_trade_rate": no_trade_rate,
                    "total_return_pct": avg_return,
                    "sharpe_ratio": avg_sharpe,
                    "max_drawdown_pct": worst_drawdown,
                },
                passed=trades > 0,
                fail_reasons=[] if trades > 0 else ["TRADES_0<1"],
            )
        )

    return WalkForwardReport(
        symbol="TEST",
        timestamp="2026-02-15T00:00:00Z",
        total_bars=1000,
        config={},
        folds=folds,
        aggregate={
            "pass_rate": pass_rate,
            "avg_sharpe": avg_sharpe,
            "avg_return": avg_return,
            "worst_drawdown": worst_drawdown,
            "return_ci_lower": return_ci_lower,
            "return_ci_upper": 1.0 if return_ci_lower is not None else None,
        },
        gate_results={},
        passed_all_gates=passed_all_gates,
        verdict="PASSED" if passed_all_gates else "FAILED",
    )


class TestAetherResearchPolicy(unittest.TestCase):
    def test_edge_confirmed_when_all_oos_gates_pass(self) -> None:
        report = _mk_report(
            pass_rate=1.0,
            avg_sharpe=0.9,
            avg_return=2.2,
            worst_drawdown=4.0,
            return_ci_lower=0.4,
            passed_all_gates=True,
            trades_per_fold=[8, 7, 9],
            no_trade_rates=[0.80, 0.78, 0.75],
        )

        res = evaluate_oos_edge_policy(
            report,
            min_pass_rate=0.6,
            min_avg_sharpe=0.0,
            min_avg_return=0.0,
            max_worst_drawdown=20.0,
            min_total_trades=10,
            max_avg_no_trade_rate=0.99,
            min_return_ci_lower=0.0,
        )
        self.assertTrue(res["passes"])
        self.assertEqual(res["verdict"], "EDGE_CONFIRMED")
        self.assertEqual(res["failure_reasons"], [])

    def test_no_edge_when_oos_gates_fail(self) -> None:
        report = _mk_report(
            pass_rate=0.2,
            avg_sharpe=-0.3,
            avg_return=-1.5,
            worst_drawdown=35.0,
            return_ci_lower=-2.0,
            passed_all_gates=False,
            trades_per_fold=[1, 0],
            no_trade_rates=[0.999, 1.0],
        )

        res = evaluate_oos_edge_policy(
            report,
            min_pass_rate=0.6,
            min_avg_sharpe=0.1,
            min_avg_return=0.5,
            max_worst_drawdown=15.0,
            min_total_trades=10,
            max_avg_no_trade_rate=0.95,
            min_return_ci_lower=0.0,
        )
        self.assertFalse(res["passes"])
        self.assertEqual(res["verdict"], "NO_EDGE")
        self.assertIn("WF_INTERNAL_GATES_FAILED", res["failure_reasons"])
        self.assertTrue(any(reason.startswith("AVG_SHARPE_") for reason in res["failure_reasons"]))
        self.assertTrue(any(reason.startswith("TOTAL_TRADES_") for reason in res["failure_reasons"]))


if __name__ == "__main__":
    unittest.main()
