from __future__ import annotations

import argparse
import logging
from datetime import datetime, timezone
from pathlib import Path

from agent.orchestrator import (
    CriticConfig,
    EvaluationConfig,
    PlannerConfig,
    ResearchAgent,
    ResearchAgentConfig,
)
from agent.registry import ExperimentRegistry
from context_store.store import DataContextStore, OHLCVSource


def _repo_root() -> Path:
    # tools/research_agent.py -> repo root is one parent up
    return Path(__file__).resolve().parents[1]


def _utc_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def main(argv: list[str] | None = None) -> int:
    # Keep CLI output focused on artifacts; evaluation internals are persisted
    # to JSON under runs/. (Chimera emits many WARNING logs for vetoes.)
    logging.basicConfig(level=logging.ERROR)

    parser = argparse.ArgumentParser(description="Recursive Quant Research Agent (offline-safe).")
    parser.add_argument("--symbol", default="XAUUSD", help="Symbol (e.g., XAUUSD, EURUSD).")
    parser.add_argument(
        "--timeframe",
        default="1h",
        choices=["1m", "5m", "1h", "4h", "1d"],
        help="Dataset timeframe (context store key).",
    )
    parser.add_argument(
        "--data",
        default=None,
        help="Path to OHLCV CSV (timestamp,open,high,low,close,volume). Defaults to runs/sample_data/xauusd_1h_sample.csv if present.",
    )
    parser.add_argument("--max-experiments", type=int, default=12, help="Max experiments to run.")
    parser.add_argument("--max-depth", type=int, default=4, help="Max mutation depth.")
    parser.add_argument("--seed", type=int, default=1337, help="RNG seed.")

    # Evaluation knobs (keep defaults conservative + fast).
    parser.add_argument("--spread", type=float, default=1.0, help="Spread in pips (costs must be on).")
    parser.add_argument("--slippage", type=float, default=0.5, help="Slippage in pips.")
    parser.add_argument("--permutations", type=int, default=100, help="Robustness permutation runs.")
    parser.add_argument("--mc-sims", type=int, default=250, help="Trade-order Monte Carlo simulations.")
    parser.add_argument("--stability-variants", type=int, default=8, help="Parameter stability variants to test.")

    args = parser.parse_args(argv)

    root = _repo_root()
    runs_root = root / "runs"
    runs_root.mkdir(parents=True, exist_ok=True)

    # Resolve default sample data if user didn't pass --data.
    data_path: Path
    if args.data:
        data_path = Path(args.data).expanduser()
    else:
        candidate = runs_root / "sample_data" / "xauusd_1h_sample.csv"
        data_path = candidate if candidate.exists() else Path("xauusd_1h_sample.csv")

    store = DataContextStore()
    store.register_ohlcv(
        OHLCVSource(
            symbol=str(args.symbol),
            timeframe=str(args.timeframe),
            path=data_path,
            fmt="csv",
        )
    )
    bars = store.get_ohlcv(symbol=str(args.symbol), timeframe=str(args.timeframe))
    dataset_hash = store.dataset_hash(symbol=str(args.symbol), timeframe=str(args.timeframe))

    run_dir = runs_root / f"rqra_{_utc_stamp()}_{str(args.symbol).lower()}_{str(args.timeframe)}"
    registry = ExperimentRegistry(runs_root / "experiment_registry.sqlite")

    cfg = ResearchAgentConfig(
        symbol=str(args.symbol),
        timeframe=str(args.timeframe),
        planner=PlannerConfig(
            seed=int(args.seed),
            max_experiments=int(args.max_experiments),
            max_depth=int(args.max_depth),
        ),
        evaluation=EvaluationConfig(
            spread_pips=float(args.spread),
            slippage_pips=float(args.slippage),
            robustness_permutations=int(args.permutations),
            mc_simulations=int(args.mc_sims),
            stability_variants=int(args.stability_variants),
        ),
        critic=CriticConfig(),
    )

    agent = ResearchAgent(
        config=cfg,
        bars=bars,
        dataset_hash=dataset_hash,
        run_dir=run_dir,
        repo_root=root,
        registry=registry,
    )
    report = agent.run()

    print(str(run_dir / "run_report.json"))
    return 0 if report.get("experiments_total", 0) else 1


if __name__ == "__main__":
    raise SystemExit(main())
