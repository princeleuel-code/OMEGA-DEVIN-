#!/usr/bin/env python3
"""
OmegaQuant Chimera - Main Runner

Command-line interface for running backtests, evolution, and analysis.
"""

import argparse
import itertools
import json
import logging
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from datetime import datetime, timezone
from typing import Any

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

from chimera.data.loader import DataLoader
from chimera.data.integrity import IntegrityChecker
from chimera.data.features import FeatureEngine
from chimera.evolution.genome import StrategyGenome, create_default_genome, create_random_genome
from chimera.evolution.drq_loop import DRQLoop, DRQConfig, Scenario, EvaluationResult
from chimera.evolution.behaviors import compute_behavior
from chimera.evaluation.backtest import Backtester, BacktestConfig, BacktestResult
from chimera.evaluation.walk_forward import walk_forward, WalkForwardConfig
from chimera.evaluation.score import Scorer, ScoreCard
from chimera.evaluation.robustness import (
    reality_check_bootstrap_max,
    robustness_report,
)
from chimera.core.decision_engine import Action, create_trade_signal, create_wait_signal
from chimera.core.truth_manifest import TruthManifest

# Sakana-style evolution imports
from agents.evolution_loop import (
    EvolutionLoop, EvolutionLoopConfig, EvalConfig, EvolutionConfig,
    LiveGatingState, CanaryMode, _generate_synthetic_data
)


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("omegaquant")


def _parse_float_grid(raw: str, name: str) -> list[float]:
    vals = []
    for token in raw.split(","):
        token = token.strip()
        if not token:
            continue
        vals.append(float(token))
    if not vals:
        raise ValueError(f"{name} grid is empty")
    return vals


def _aether_gate_failure_local(feat, genome) -> str | None:
    if not genome.use_aether_gate:
        return None
    payload = feat.aether if isinstance(feat.aether, dict) else None
    if not payload:
        return "AETHER gate enabled but no AETHER payload"
    s = float(payload.get("S", 1.0))
    n = float(payload.get("N", 0.0))
    pc = float(payload.get("Pc", 0.0))
    f = abs(float(payload.get("F", 0.0)))
    seam = bool(payload.get("SEAM", False))
    if s > genome.aether_entropy_max:
        return f"AETHER entropy too high ({s:.2f})"
    if n < genome.aether_coherence_min:
        return f"AETHER coherence too low ({n:.2f})"
    if pc < genome.aether_pc_min:
        return f"AETHER cycle confidence too low ({pc:.2f})"
    if f < genome.aether_force_min:
        return f"AETHER force too weak ({f:.2f})"
    if genome.aether_block_on_seam and seam and f < genome.aether_seam_force_override:
        return "AETHER seam active without force override"
    return None


def _isolation_signal_generator(feat, genome):
    gate_fail = _aether_gate_failure_local(feat, genome)
    if gate_fail:
        return create_wait_signal(gate_fail)

    # Simple directional proxy: momentum sign. This isolates gate quality.
    direction = 1 if feat.momentum >= 0 else -1
    entry = feat.close
    atr = max(1e-9, feat.atr)
    if direction == 1:
        stop_loss = entry - atr * genome.atr_multiplier_sl
        take_profit = entry + atr * genome.atr_multiplier_tp
        action = Action.LONG
    else:
        stop_loss = entry + atr * genome.atr_multiplier_sl
        take_profit = entry - atr * genome.atr_multiplier_tp
        action = Action.SHORT

    conf = min(1.0, max(genome.min_confidence, 0.55))
    return create_trade_signal(
        action=action,
        confidence=conf,
        entry=entry,
        stop_loss=stop_loss,
        take_profit=take_profit,
        size=genome.risk_per_trade_pct / 100.0,
        reason="AETHER gate pass + momentum direction (isolation mode)",
    )


def _aether_policy_failures(
    *,
    trades: int,
    sharpe: float,
    max_drawdown_pct: float,
    no_trade_rate: float,
    min_trades: int,
    min_sharpe: float,
    max_drawdown: float,
    max_no_trade_rate: float,
) -> list[str]:
    reasons: list[str] = []
    if trades < min_trades:
        reasons.append(f"TRADES_{trades}<{min_trades}")
    if sharpe < min_sharpe:
        reasons.append(f"SHARPE_{sharpe:.4f}<{min_sharpe:.4f}")
    if max_drawdown_pct > max_drawdown:
        reasons.append(f"MAX_DD_{max_drawdown_pct:.4f}>{max_drawdown:.4f}")
    if no_trade_rate > max_no_trade_rate:
        reasons.append(f"NO_TRADE_{no_trade_rate:.4f}>{max_no_trade_rate:.4f}")
    return reasons


def _rank_aether_trials(trials: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(
        trials,
        key=lambda t: (
            1 if t["passes_policy"] else 0,
            1 if t["passed_risk_gates"] else 0,
            float(t["fitness"]),
            float(t["metrics"]["sharpe"]),
            float(t["metrics"]["return_pct"]),
        ),
        reverse=True,
    )


def evaluate_oos_edge_policy(
    report,
    *,
    min_pass_rate: float,
    min_avg_sharpe: float,
    min_avg_return: float,
    max_worst_drawdown: float,
    min_total_trades: int,
    max_avg_no_trade_rate: float,
    min_return_ci_lower: float,
) -> dict[str, Any]:
    """Evaluate strict OOS gates and return an explicit EDGE/NO_EDGE verdict."""
    folds = list(getattr(report, "folds", []) or [])
    aggregate = dict(getattr(report, "aggregate", {}) or {})

    total_trades = sum(int(f.metrics.get("total_trades", 0)) for f in folds)
    avg_no_trade_rate = (
        sum(float(f.metrics.get("no_trade_rate", 1.0)) for f in folds) / len(folds)
        if folds
        else 1.0
    )

    pass_rate = float(aggregate.get("pass_rate", 0.0))
    avg_sharpe = float(aggregate.get("avg_sharpe", 0.0))
    avg_return = float(aggregate.get("avg_return", 0.0))
    worst_drawdown = float(aggregate.get("worst_drawdown", float("inf")))
    return_ci_lower = aggregate.get("return_ci_lower")
    ci_lower_ok = (
        (return_ci_lower is not None)
        and (float(return_ci_lower) >= float(min_return_ci_lower))
    )

    gates = {
        "wf_internal_gates": bool(getattr(report, "passed_all_gates", False)),
        "min_pass_rate": pass_rate >= min_pass_rate,
        "min_avg_sharpe": avg_sharpe >= min_avg_sharpe,
        "min_avg_return": avg_return >= min_avg_return,
        "max_worst_drawdown": worst_drawdown <= max_worst_drawdown,
        "min_total_trades": total_trades >= min_total_trades,
        "max_avg_no_trade_rate": avg_no_trade_rate <= max_avg_no_trade_rate,
        "min_return_ci_lower": ci_lower_ok,
    }

    failure_reasons: list[str] = []
    if not gates["wf_internal_gates"]:
        failure_reasons.append("WF_INTERNAL_GATES_FAILED")
    if not gates["min_pass_rate"]:
        failure_reasons.append(f"PASS_RATE_{pass_rate:.4f}<{min_pass_rate:.4f}")
    if not gates["min_avg_sharpe"]:
        failure_reasons.append(f"AVG_SHARPE_{avg_sharpe:.4f}<{min_avg_sharpe:.4f}")
    if not gates["min_avg_return"]:
        failure_reasons.append(f"AVG_RETURN_{avg_return:.4f}<{min_avg_return:.4f}")
    if not gates["max_worst_drawdown"]:
        failure_reasons.append(f"WORST_DD_{worst_drawdown:.4f}>{max_worst_drawdown:.4f}")
    if not gates["min_total_trades"]:
        failure_reasons.append(f"TOTAL_TRADES_{total_trades}<{min_total_trades}")
    if not gates["max_avg_no_trade_rate"]:
        failure_reasons.append(
            f"AVG_NO_TRADE_{avg_no_trade_rate:.4f}>{max_avg_no_trade_rate:.4f}"
        )
    if not gates["min_return_ci_lower"]:
        if return_ci_lower is None:
            failure_reasons.append("RETURN_CI_LOWER_MISSING")
        else:
            failure_reasons.append(
                f"RETURN_CI_LOWER_{float(return_ci_lower):.4f}<{float(min_return_ci_lower):.4f}"
            )

    passes = all(gates.values())
    verdict = "EDGE_CONFIRMED" if passes else "NO_EDGE"
    return {
        "verdict": verdict,
        "passes": passes,
        "gates": gates,
        "metrics": {
            "pass_rate": pass_rate,
            "avg_sharpe": avg_sharpe,
            "avg_return": avg_return,
            "worst_drawdown": worst_drawdown,
            "total_trades": total_trades,
            "avg_no_trade_rate": avg_no_trade_rate,
            "return_ci_lower": return_ci_lower,
            "return_ci_upper": aggregate.get("return_ci_upper"),
        },
        "failure_reasons": failure_reasons,
    }


def run_backtest(args):
    """Run a single backtest"""
    logger.info("=" * 60)
    logger.info("OmegaQuant Chimera - Backtest")
    logger.info("=" * 60)
    
    # Load or create genome
    if args.genome:
        logger.info(f"Loading genome from {args.genome}")
        genome = StrategyGenome.load(args.genome)
    else:
        logger.info("Using default genome")
        genome = create_default_genome()
    
    logger.info(f"Genome ID: {genome.genome_id}")
    
    # Load or generate data
    loader = DataLoader(symbol=args.symbol)
    
    if args.data:
        logger.info(f"Loading data from {args.data}")
        data = loader.load_csv(Path(args.data))
    else:
        logger.info(f"Generating {args.bars} bars of synthetic data")
        if args.regime_data:
            data = loader.generate_regime_data(num_bars=args.bars)
        else:
            data = loader.generate_synthetic(num_bars=args.bars)
    
    logger.info(f"Data: {len(data)} bars from {data[0].timestamp} to {data[-1].timestamp}")
    
    # Check data integrity
    checker = IntegrityChecker()
    integrity = checker.check_series(data)
    
    if not integrity.valid:
        logger.error(f"Data integrity check failed: {len(integrity.issues)} issues")
        for issue in integrity.issues[:5]:
            logger.error(f"  - {issue.code.name}: {issue.details}")
        if not args.force:
            logger.error("Use --force to run anyway")
            return 1
    else:
        logger.info("Data integrity check passed")
    
    # Configure backtest
    config = BacktestConfig(
        initial_capital=args.capital,
        symbol=args.symbol,
        spread_pips=args.spread
    )
    
    # Run backtest
    logger.info("Running backtest...")
    backtester = Backtester(config=config)
    result = backtester.run(data, genome)
    
    # Score result
    scorer = Scorer()
    scorecard = scorer.score(result)
    
    # Print results
    print("\n" + "=" * 60)
    print("BACKTEST RESULTS")
    print("=" * 60)
    
    print(f"\nGenome: {genome.genome_id}")
    print(f"Symbol: {args.symbol}")
    print(f"Bars: {len(data)}")
    print(f"Initial Capital: ${config.initial_capital:,.2f}")
    
    print("\n--- Performance ---")
    pm = result.performance_metrics
    print(f"Final Equity: ${result.equity_curve[-1]:,.2f}")
    print(f"Total Return: {pm.total_return_pct:.2f}%")
    print(f"Sharpe Ratio: {pm.sharpe_ratio:.3f}")
    print(f"Max Drawdown: {pm.max_drawdown_pct:.2f}%")
    print(f"Calmar Ratio: {pm.calmar_ratio:.3f}")
    
    print("\n--- Trade Statistics ---")
    tm = result.trade_metrics
    print(f"Total Trades: {tm.total_trades}")
    print(f"Win Rate: {tm.win_rate:.1%}")
    print(f"Profit Factor: {tm.profit_factor:.2f}")
    print(f"Avg Winner: ${tm.avg_winner:.2f}")
    print(f"Avg Loser: ${tm.avg_loser:.2f}")
    print(f"Expectancy: ${tm.expectancy:.2f}")
    
    print("\n--- Decision Analysis ---")
    print(f"Total Decisions: {result.total_decisions}")
    print(f"No-Trade Decisions: {result.no_trade_decisions}")
    print(f"No-Trade Rate: {pm.no_trade_rate:.1%}")
    
    print("\n--- Fitness Score ---")
    print(f"Fitness: {scorecard.fitness:.4f}")
    print(f"  Return Score: {scorecard.return_score:.4f}")
    print(f"  Risk Score: {scorecard.risk_score:.4f}")
    print(f"  Consistency Score: {scorecard.consistency_score:.4f}")
    print(f"  Efficiency Score: {scorecard.efficiency_score:.4f}")
    print(f"Passed Risk Gates: {scorecard.passed_risk_gates}")
    
    if not scorecard.passed_risk_gates:
        print(f"Gate Failures: {scorecard.risk_gate_failures}")
    
    # Save results if requested
    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        result.save(output_path)
        logger.info(f"Results saved to {output_path}")
    
    print("\n" + "=" * 60)
    
    return 0


def run_evolution(args):
    """Run DRQ evolution loop"""
    logger.info("=" * 60)
    logger.info("OmegaQuant Chimera - DRQ Evolution")
    logger.info("=" * 60)
    
    # Create evaluator function
    def evaluator(genome: StrategyGenome, scenario: Scenario) -> EvaluationResult:
        """Evaluate a genome on a scenario"""
        # Generate data for scenario
        loader = DataLoader(symbol=args.symbol)
        data = loader.generate_synthetic(
            num_bars=args.bars,
            volatility=scenario.volatility,
            trend=scenario.trend
        )
        
        # Run backtest
        config = BacktestConfig(
            initial_capital=args.capital,
            symbol=args.symbol,
            spread_pips=args.spread * scenario.spread_multiplier
        )
        backtester = Backtester(config=config)
        result = backtester.run(data, genome, create_manifest=False)
        
        # Score
        scorer = Scorer()
        scorecard = scorer.score(result)
        
        return EvaluationResult(
            genome_id=genome.genome_id,
            scenario_name=scenario.name,
            fitness=scorecard.fitness,
            metrics={
                "trades_per_day": result.performance_metrics.trades_per_day,
                "avg_holding_bars": result.trade_metrics.avg_bars_held,
                "sharpe": result.performance_metrics.sharpe_ratio,
                "max_dd": result.performance_metrics.max_drawdown_pct,
                "win_rate": result.trade_metrics.win_rate
            },
            passed_risk_gates=scorecard.passed_risk_gates
        )
    
    # Configure DRQ
    drq_config = DRQConfig(
        initial_population_size=args.population,
        children_per_generation=args.children,
        max_generations=args.generations,
        mutation_rate=args.mutation_rate,
        stagnation_limit=args.stagnation_limit
    )
    
    # Create and run DRQ loop
    drq = DRQLoop(evaluator=evaluator, config=drq_config)
    
    logger.info(f"Starting evolution for {args.generations} generations")
    logger.info(f"Population: {args.population}, Children: {args.children}")
    
    summary = drq.run(max_generations=args.generations)
    
    # Print results
    print("\n" + "=" * 60)
    print("EVOLUTION RESULTS")
    print("=" * 60)
    
    print(f"\nGenerations Run: {summary['generations_run']}")
    print(f"Total Evaluations: {summary['total_evaluations']}")
    print(f"Archive Size: {summary['final_archive_size']}")
    print(f"Archive Coverage: {summary['final_coverage']:.1%}")
    print(f"Best Fitness: {summary['best_fitness']:.4f}")
    
    # Get champions
    champions = drq.get_champions(5)
    print("\n--- Top 5 Champions ---")
    for i, champ in enumerate(champions):
        print(f"\n{i+1}. {champ.genome_id}")
        print(f"   Confidence: {champ.min_confidence:.2f}")
        print(f"   SL Mult: {champ.atr_multiplier_sl:.2f}")
        print(f"   TP Mult: {champ.atr_multiplier_tp:.2f}")
        print(f"   Risk/Trade: {champ.risk_per_trade_pct:.2f}%")
    
    # Save state if requested
    if args.output:
        output_dir = Path(args.output)
        drq.save_state(output_dir)
        logger.info(f"Evolution state saved to {output_dir}")
    
    print("\n" + "=" * 60)
    
    return 0


def run_walkforward(args):
    """Run purged walk-forward evaluation (costs always on)."""
    logger.info("=" * 60)
    logger.info("OmegaQuant Chimera - Walk-Forward Evaluation")
    logger.info("=" * 60)

    # Load or create genome
    if args.genome:
        logger.info(f"Loading genome from {args.genome}")
        genome = StrategyGenome.load(args.genome)
    else:
        logger.info("Using default genome")
        genome = create_default_genome()

    # Load or generate data
    loader = DataLoader(symbol=args.symbol)
    if args.data:
        logger.info(f"Loading data from {args.data}")
        data = loader.load_csv(Path(args.data))
    else:
        logger.info(f"Generating {args.bars} bars of synthetic data")
        if args.regime_data:
            data = loader.generate_regime_data(num_bars=args.bars)
        else:
            data = loader.generate_synthetic(num_bars=args.bars)

    # Integrity check (fail-closed unless --force)
    checker = IntegrityChecker()
    integrity = checker.check_series(data)
    if not integrity.valid and not args.force:
        logger.error(f"Data integrity check failed: {len(integrity.issues)} issues")
        logger.error("Use --force to run anyway")
        return 1

    bt_config = BacktestConfig(
        initial_capital=args.capital,
        symbol=args.symbol,
        spread_pips=args.spread,
        slippage_pips=args.slippage,
        commission_per_lot=args.commission,
    )

    wf_config = WalkForwardConfig(
        n_folds=args.folds,
        train_bars=args.train_bars,
        test_bars=args.test_bars,
        step_bars=args.step_bars,
        purge_bars=args.purge_bars,
        min_trades_per_fold=args.min_trades_per_fold,
        bootstrap_samples=args.bootstrap,
    )

    report = walk_forward(data=data, genome=genome, backtest_config=bt_config, wf_config=wf_config)

    print("\n" + "=" * 60)
    print("WALK-FORWARD REPORT")
    print("=" * 60)
    print(f"\nSymbol: {report.symbol}")
    print(f"Bars: {report.total_bars}")
    print(f"Folds: {len(report.folds)}")
    print(f"Verdict: {report.verdict}")
    print("\n--- Aggregate ---")
    for k in ["avg_return", "avg_sharpe", "avg_trades", "avg_win_rate", "pass_rate", "return_ci_lower", "return_ci_upper"]:
        if k in report.aggregate:
            print(f"{k}: {report.aggregate[k]}")

    # Save results if requested
    if args.output:
        out = Path(args.output)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(report.to_dict(), indent=2))
        logger.info(f"Wrote walk-forward report to {out}")

    print("\n" + "=" * 60)
    return 0


def run_analyze(args):
    """Analyze a genome or backtest result"""
    logger.info("=" * 60)
    logger.info("OmegaQuant Chimera - Analysis")
    logger.info("=" * 60)
    
    if args.genome:
        genome = StrategyGenome.load(args.genome)
        print("\n--- Genome Analysis ---")
        print(json.dumps(genome.to_dict(), indent=2))
    
    if args.result:
        with open(args.result) as f:
            result = json.load(f)
        print("\n--- Result Analysis ---")
        print(json.dumps(result, indent=2))
    
    return 0


def run_sakana_evolve(args):
    """Run Sakana-style DGM + DRQ hybrid evolution loop"""
    logger.info("=" * 60)
    logger.info("OmegaQuant Chimera - Sakana Evolution (DGM + DRQ)")
    logger.info("=" * 60)
    
    # Generate synthetic data
    logger.info(f"Generating {args.bars} bars of synthetic data...")
    data = _generate_synthetic_data(args.bars)
    logger.info(f"Data generated: {len(data)} bars")
    
    # Configure evolution loop
    loop_config = EvolutionLoopConfig(
        max_rounds=args.rounds,
        variants_per_round=args.variants,
        mutation_rate=args.mutation_rate,
        mutation_strength=args.mutation_strength,
        patch_budget=args.patch_budget,
        attack_enabled=not args.no_attack,
        attack_min_pass_rate=args.attack_min_pass_rate,
        attack_max_fitness_degradation=args.attack_max_fitness_degradation,
        attack_drop_every_n=args.attack_drop_every_n,
        attack_noise_sigma=args.attack_noise_sigma,
        attack_aether_enabled=not args.no_aether_attack,
        attack_aether_window_bars=args.attack_aether_window_bars,
        attack_entropy_window=args.attack_entropy_window,
        eval_retry_attempts=args.eval_retries,
        eval_retry_backoff_seconds=args.eval_retry_backoff,
        auto_resume=not args.no_auto_resume,
        watchdog_enabled=not args.no_watchdog,
        watchdog_stale_seconds=args.watchdog_stale_seconds,
        long_horizon_memory_enabled=not args.no_long_memory,
        output_dir=args.output,
        canary_trades_required=args.canary_trades,
        # CLI uses --canary-max-dd but config field is canary_max_dd_pct
        canary_max_dd_pct=args.canary_max_dd,
    )
    
    eval_config = EvalConfig(
        train_bars=args.train_bars,
        test_bars=args.test_bars,
        n_folds=args.folds,
        max_drawdown_threshold=args.max_dd,
        min_sharpe_threshold=args.min_sharpe,
        max_turnover_threshold=args.max_turnover,
        stability_threshold=args.stability,
    )
    
    # Create initial config if provided
    initial_config = None
    if args.config:
        with open(args.config) as f:
            config_dict = json.load(f)
        initial_config = EvolutionConfig.from_dict(config_dict)
        logger.info(f"Loaded initial config from {args.config}")
    
    # Run evolution
    logger.info(f"Starting Sakana evolution: {args.rounds} rounds, {args.variants} variants/round")
    loop = EvolutionLoop(loop_config, eval_config)
    result = loop.run(data, initial_config=initial_config, max_rounds=args.rounds)
    
    # Print results
    print("\n" + "=" * 60)
    print("SAKANA EVOLUTION RESULTS")
    print("=" * 60)
    
    print(f"\nRounds Completed: {result['rounds_completed']}")
    print(f"Total Variants Evaluated: {result['total_variants_evaluated']}")
    print(f"Archive Size: {result['archive_size']}")
    print(f"Best Fitness: {result['best_fitness']:.4f}")
    
    champion_variant_id = None
    if getattr(loop, "live_state", None):
        champion_variant_id = loop.live_state.active_variant_id
    if champion_variant_id and champion_variant_id != "initial":
        print(f"\nChampion Variant: {champion_variant_id}")
    
    print(f"\nOutput Directory: {args.output}")
    print("Truth Objects Created:")
    print("  - RUN_MANIFEST_*.json (provenance)")
    print("  - VARIANT_PATCH_*.json (config diffs)")
    print("  - EVAL_REPORT_*.json (walk-forward results)")
    print("  - ARCHIVE_INDEX.json (MAP-Elites buckets)")
    print("  - LIVE_GATING_STATE.json (canary/kill-switch)")
    print("  - CHAMPION_CONFIG.json (active config)")
    
    print("\n" + "=" * 60)
    
    return 0


def run_indicator(args):
    """Compute and print AETHER indicator state from OHLCV data."""
    logger.info("=" * 60)
    logger.info("OmegaQuant Chimera - AETHER Indicator")
    logger.info("=" * 60)

    loader = DataLoader(symbol=args.symbol)
    if args.data:
        logger.info(f"Loading data from {args.data}")
        data = loader.load_csv(Path(args.data), date_format=args.date_format)
    else:
        logger.info(f"Generating {args.bars} bars of synthetic data")
        if args.regime_data:
            data = loader.generate_regime_data(num_bars=args.bars)
        else:
            data = loader.generate_synthetic(num_bars=args.bars)

    if args.max_bars and len(data) > args.max_bars:
        logger.info(f"Truncating to last {args.max_bars} bars for indicator compute")
        data = data[-args.max_bars:]

    checker = IntegrityChecker()
    integrity = checker.check_series(data)
    if not integrity.valid and not args.force:
        logger.error(f"Data integrity check failed: {len(integrity.issues)} issues")
        logger.error("Use --force to run anyway")
        return 1

    feature_engine = FeatureEngine()
    features = feature_engine.compute(data)
    if not features:
        logger.error("No features available. Increase data size or validate input CSV.")
        return 1

    tail = max(1, int(args.tail))
    selection = features[-tail:]
    rows = []
    for feat in selection:
        a = feat.aether or {}
        rows.append(
            {
                "timestamp": feat.timestamp.isoformat(),
                "close": feat.close,
                "S": a.get("S"),
                "dS": a.get("dS"),
                "F": a.get("F"),
                "P": a.get("P"),
                "Pc": a.get("Pc"),
                "N": a.get("N"),
                "LOCK": a.get("LOCK"),
                "SEAM": a.get("SEAM"),
                "STAMP": a.get("STAMP"),
                "TRIGGER": a.get("TRIGGER"),
                "REGIME": a.get("REGIME"),
            }
        )

    print("\n" + "=" * 60)
    print("AETHER INDICATOR")
    print("=" * 60)
    for row in rows:
        print(
            f"{row['timestamp']} | close={row['close']:.5f} | "
            f"S={row['S']:.3f} dS={row['dS']:+.3f} F={row['F']:+.3f} | "
            f"P={row['P']} Pc={row['Pc']:.3f} N={row['N']:.3f} | "
            f"LOCK={row['LOCK']} SEAM={row['SEAM']} TRIGGER={row['TRIGGER']} | "
            f"{row['STAMP']} {row['REGIME']}"
        )

    if args.output:
        out = Path(args.output)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(rows, indent=2))
        logger.info(f"Wrote indicator output to {out}")

    return 0


def run_aether_calibrate(args):
    """Grid-search AETHER gate thresholds and rank configurations."""
    logger.info("=" * 60)
    logger.info("OmegaQuant Chimera - AETHER Calibrate")
    logger.info("=" * 60)

    # Base genome
    if args.genome:
        logger.info(f"Loading base genome from {args.genome}")
        base_genome = StrategyGenome.load(args.genome)
    else:
        logger.info("Using default genome as calibration base")
        base_genome = create_default_genome()

    # Data load/generation
    loader = DataLoader(symbol=args.symbol)
    if args.data:
        logger.info(f"Loading data from {args.data}")
        data = loader.load_csv(Path(args.data), date_format=args.date_format)
    else:
        logger.info(f"Generating {args.bars} bars of synthetic data")
        if args.regime_data:
            data = loader.generate_regime_data(num_bars=args.bars)
        else:
            data = loader.generate_synthetic(num_bars=args.bars)

    if args.max_bars and len(data) > args.max_bars:
        logger.info(f"Truncating to last {args.max_bars} bars for calibration")
        data = data[-args.max_bars:]

    checker = IntegrityChecker()
    integrity = checker.check_series(data)
    if not integrity.valid and not args.force:
        logger.error(f"Data integrity check failed: {len(integrity.issues)} issues")
        logger.error("Use --force to run anyway")
        return 1

    # Parse grids
    try:
        entropy_grid = _parse_float_grid(args.entropy_grid, "entropy")
        coherence_grid = _parse_float_grid(args.coherence_grid, "coherence")
        pc_grid = _parse_float_grid(args.pc_grid, "pc")
        force_grid = _parse_float_grid(args.force_grid, "force")
        seam_override_grid = _parse_float_grid(args.seam_override_grid, "seam-override")
    except ValueError as e:
        logger.error(str(e))
        return 1

    seam_modes = [True, False] if args.include_seam_off else [True]
    total_trials = (
        len(entropy_grid)
        * len(coherence_grid)
        * len(pc_grid)
        * len(force_grid)
        * len(seam_override_grid)
        * len(seam_modes)
    )
    logger.info(f"Running {total_trials} AETHER threshold trials")

    config = BacktestConfig(
        initial_capital=args.capital,
        symbol=args.symbol,
        spread_pips=args.spread,
    )
    backtester = Backtester(config=config)
    scorer = Scorer()
    trials = []
    decision_logger = logging.getLogger("chimera.core.decision_engine")
    veto_logger = logging.getLogger("chimera.core.veto_cascade")
    prev_decision_level = decision_logger.level
    prev_veto_level = veto_logger.level
    decision_logger.setLevel(logging.ERROR)
    veto_logger.setLevel(logging.ERROR)

    try:
        for idx, (ent, coh, pc_min, f_min, seam_override, block_on_seam) in enumerate(
            itertools.product(
                entropy_grid,
                coherence_grid,
                pc_grid,
                force_grid,
                seam_override_grid,
                seam_modes,
            ),
            start=1,
        ):
            genome = StrategyGenome.from_dict(base_genome.to_dict())
            genome.use_aether_gate = True
            genome.aether_entropy_max = float(ent)
            genome.aether_coherence_min = float(coh)
            genome.aether_pc_min = float(pc_min)
            genome.aether_force_min = float(f_min)
            genome.aether_block_on_seam = bool(block_on_seam)
            genome.aether_seam_force_override = float(seam_override)

            # Optional: isolate AETHER impact by neutralizing other hard filters.
            if args.isolate_aether:
                genome.require_displacement = False
                genome.min_volume_ratio = 0.0
                genome.min_atr = 0.0
                genome.min_confidence = min(genome.min_confidence, 0.4)

            genome.genome_id = genome._generate_id()

            runner = (
                Backtester(config=config, signal_generator=_isolation_signal_generator)
                if args.isolate_aether
                else backtester
            )
            result = runner.run(data, genome, create_manifest=False)
            score = scorer.score(result)

            tm = result.trade_metrics
            pm = result.performance_metrics
            policy_failures = _aether_policy_failures(
                trades=tm.total_trades,
                sharpe=pm.sharpe_ratio,
                max_drawdown_pct=pm.max_drawdown_pct,
                no_trade_rate=pm.no_trade_rate,
                min_trades=args.min_trades,
                min_sharpe=args.min_sharpe,
                max_drawdown=args.max_drawdown,
                max_no_trade_rate=args.max_no_trade_rate,
            )
            passes_policy = len(policy_failures) == 0
            trials.append(
                {
                    "rank_score": score.fitness,
                    "fitness": score.fitness,
                    "passed_risk_gates": score.passed_risk_gates,
                    "passes_policy": passes_policy,
                    "policy_failures": policy_failures,
                    "metrics": {
                        "return_pct": pm.total_return_pct,
                        "sharpe": pm.sharpe_ratio,
                        "max_drawdown_pct": pm.max_drawdown_pct,
                        "no_trade_rate": pm.no_trade_rate,
                        "trades": tm.total_trades,
                        "win_rate": tm.win_rate,
                        "profit_factor": tm.profit_factor,
                    },
                    "aether_gate": {
                        "entropy_max": ent,
                        "coherence_min": coh,
                        "pc_min": pc_min,
                        "force_min": f_min,
                        "block_on_seam": bool(block_on_seam),
                        "seam_force_override": seam_override,
                    },
                }
            )

            if idx % 25 == 0 or idx == total_trials:
                logger.info(f"Calibrate progress: {idx}/{total_trials}")
    finally:
        decision_logger.setLevel(prev_decision_level)
        veto_logger.setLevel(prev_veto_level)

    ranked = _rank_aether_trials(trials)

    top_k = max(1, int(args.top_k))
    top = ranked[:top_k]
    champion = top[0]

    print("\n" + "=" * 60)
    print("AETHER CALIBRATION REPORT")
    print("=" * 60)
    print(f"\nTrials: {len(trials)}")
    print(
        f"Policy: trades>={args.min_trades}, sharpe>={args.min_sharpe}, "
        f"max_dd<={args.max_drawdown}, no_trade_rate<={args.max_no_trade_rate}"
    )
    print("\n--- Champion Gate ---")
    for k, v in champion["aether_gate"].items():
        print(f"{k}: {v}")
    print("\n--- Champion Metrics ---")
    for k, v in champion["metrics"].items():
        print(f"{k}: {v}")
    print(f"fitness: {champion['fitness']}")
    print(f"passed_risk_gates: {champion['passed_risk_gates']}")
    print(f"passes_policy: {champion['passes_policy']}")

    print("\n--- Top Configs ---")
    for i, row in enumerate(top, start=1):
        gate = row["aether_gate"]
        m = row["metrics"]
        print(
            f"{i:02d}. fit={row['fitness']:.4f} sharpe={m['sharpe']:.3f} "
            f"ret={m['return_pct']:.2f}% dd={m['max_drawdown_pct']:.2f}% "
            f"trades={m['trades']} no_trade={m['no_trade_rate']:.3f} | "
            f"S<={gate['entropy_max']}, N>={gate['coherence_min']}, "
            f"Pc>={gate['pc_min']}, |F|>={gate['force_min']}, "
            f"seam_block={gate['block_on_seam']}, seam_override={gate['seam_force_override']}"
        )

    if args.output:
        out = Path(args.output)
        out.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "meta": {
                "timestamp": datetime.utcnow().isoformat(),
                "symbol": args.symbol,
                "bars": len(data),
                "trials": len(trials),
            },
            "policy": {
                "min_trades": args.min_trades,
                "min_sharpe": args.min_sharpe,
                "max_drawdown": args.max_drawdown,
                "max_no_trade_rate": args.max_no_trade_rate,
                "isolate_aether": bool(args.isolate_aether),
            },
            "champion": champion,
            "top": top,
        }
        out.write_text(json.dumps(payload, indent=2))
        logger.info(f"Wrote calibration report to {out}")

    return 0


def run_aether_research(args):
    """
    Falsifiable AETHER gate research pipeline:
    1) calibrate thresholds on train only
    2) validate champion on purged walk-forward OOS only
    3) refuse edge claims unless OOS gates pass
    """
    logger.info("=" * 60)
    logger.info("OmegaQuant Chimera - AETHER Research")
    logger.info("=" * 60)

    # Base genome
    if args.genome:
        logger.info(f"Loading base genome from {args.genome}")
        base_genome = StrategyGenome.load(args.genome)
    else:
        logger.info("Using default genome as calibration base")
        base_genome = create_default_genome()

    # Data load/generation
    loader = DataLoader(symbol=args.symbol)
    if args.data:
        logger.info(f"Loading data from {args.data}")
        data = loader.load_csv(Path(args.data), date_format=args.date_format)
    else:
        logger.info(f"Generating {args.bars} bars of synthetic data")
        if args.regime_data:
            data = loader.generate_regime_data(num_bars=args.bars)
        else:
            data = loader.generate_synthetic(num_bars=args.bars)

    if args.max_bars and len(data) > args.max_bars:
        logger.info(f"Truncating to last {args.max_bars} bars for research")
        data = data[-args.max_bars:]

    checker = IntegrityChecker()
    integrity = checker.check_series(data)
    if not integrity.valid and not args.force:
        logger.error(f"Data integrity check failed: {len(integrity.issues)} issues")
        logger.error("Use --force to run anyway")
        return 1

    # Parse grids
    try:
        entropy_grid = _parse_float_grid(args.entropy_grid, "entropy")
        coherence_grid = _parse_float_grid(args.coherence_grid, "coherence")
        pc_grid = _parse_float_grid(args.pc_grid, "pc")
        force_grid = _parse_float_grid(args.force_grid, "force")
        seam_override_grid = _parse_float_grid(args.seam_override_grid, "seam-override")
    except ValueError as e:
        logger.error(str(e))
        return 1

    seam_modes = [True, False] if args.include_seam_off else [True]
    wf_step_bars = args.wf_step_bars if args.wf_step_bars > 0 else args.wf_test_bars
    min_oos_bars = (
        args.wf_train_bars
        + args.wf_purge_bars
        + args.wf_test_bars
        + max(0, args.wf_folds - 1) * wf_step_bars
    )

    if args.train_bars > 0:
        split_idx = int(args.train_bars)
    else:
        split_idx = int(len(data) * args.train_ratio)

    max_train_bars = len(data) - min_oos_bars
    if max_train_bars < args.min_train_bars:
        logger.error(
            "Insufficient data for requested split. "
            f"Need at least {args.min_train_bars + min_oos_bars} bars, got {len(data)}."
        )
        return 1

    if split_idx > max_train_bars:
        logger.warning(
            "Requested train split leaves insufficient OOS bars; "
            f"clamping train bars from {split_idx} to {max_train_bars}."
        )
        split_idx = max_train_bars

    if split_idx < args.min_train_bars:
        logger.error(
            f"Train split too small ({split_idx} bars). Increase data or lower --min-train-bars."
        )
        return 1

    train_data = data[:split_idx]
    oos_data = data[split_idx:]

    if len(oos_data) < min_oos_bars:
        logger.error(
            "OOS split too small for walk-forward. "
            f"Need >= {min_oos_bars} bars, got {len(oos_data)}."
        )
        return 1

    total_trials = (
        len(entropy_grid)
        * len(coherence_grid)
        * len(pc_grid)
        * len(force_grid)
        * len(seam_override_grid)
        * len(seam_modes)
    )
    logger.info(f"Running {total_trials} train-only AETHER calibration trials")

    train_config = BacktestConfig(
        initial_capital=args.capital,
        symbol=args.symbol,
        spread_pips=args.spread,
    )
    backtester = Backtester(config=train_config)
    scorer = Scorer()
    trials = []
    decision_logger = logging.getLogger("chimera.core.decision_engine")
    veto_logger = logging.getLogger("chimera.core.veto_cascade")
    prev_decision_level = decision_logger.level
    prev_veto_level = veto_logger.level
    decision_logger.setLevel(logging.ERROR)
    veto_logger.setLevel(logging.ERROR)

    try:
        for idx, (ent, coh, pc_min, f_min, seam_override, block_on_seam) in enumerate(
            itertools.product(
                entropy_grid,
                coherence_grid,
                pc_grid,
                force_grid,
                seam_override_grid,
                seam_modes,
            ),
            start=1,
        ):
            genome = StrategyGenome.from_dict(base_genome.to_dict())
            genome.use_aether_gate = True
            genome.aether_entropy_max = float(ent)
            genome.aether_coherence_min = float(coh)
            genome.aether_pc_min = float(pc_min)
            genome.aether_force_min = float(f_min)
            genome.aether_block_on_seam = bool(block_on_seam)
            genome.aether_seam_force_override = float(seam_override)

            # Optional: isolate gate quality from other hard filters.
            if args.isolate_aether:
                genome.require_displacement = False
                genome.min_volume_ratio = 0.0
                genome.min_atr = 0.0
                genome.min_confidence = min(genome.min_confidence, 0.4)

            genome.genome_id = genome._generate_id()

            runner = (
                Backtester(config=train_config, signal_generator=_isolation_signal_generator)
                if args.isolate_aether
                else backtester
            )
            result = runner.run(train_data, genome, create_manifest=False)
            score = scorer.score(result)

            tm = result.trade_metrics
            pm = result.performance_metrics
            policy_failures = _aether_policy_failures(
                trades=tm.total_trades,
                sharpe=pm.sharpe_ratio,
                max_drawdown_pct=pm.max_drawdown_pct,
                no_trade_rate=pm.no_trade_rate,
                min_trades=args.min_trades,
                min_sharpe=args.min_sharpe,
                max_drawdown=args.max_drawdown,
                max_no_trade_rate=args.max_no_trade_rate,
            )
            passes_policy = len(policy_failures) == 0
            trials.append(
                {
                    "rank_score": score.fitness,
                    "fitness": score.fitness,
                    "passed_risk_gates": score.passed_risk_gates,
                    "passes_policy": passes_policy,
                    "policy_failures": policy_failures,
                    "metrics": {
                        "return_pct": pm.total_return_pct,
                        "sharpe": pm.sharpe_ratio,
                        "max_drawdown_pct": pm.max_drawdown_pct,
                        "no_trade_rate": pm.no_trade_rate,
                        "trades": tm.total_trades,
                        "win_rate": tm.win_rate,
                        "profit_factor": tm.profit_factor,
                    },
                    "aether_gate": {
                        "entropy_max": ent,
                        "coherence_min": coh,
                        "pc_min": pc_min,
                        "force_min": f_min,
                        "block_on_seam": bool(block_on_seam),
                        "seam_force_override": seam_override,
                    },
                }
            )

            if idx % 25 == 0 or idx == total_trials:
                logger.info(f"Calibration progress: {idx}/{total_trials}")
    finally:
        decision_logger.setLevel(prev_decision_level)
        veto_logger.setLevel(prev_veto_level)

    ranked = _rank_aether_trials(trials)
    champion = ranked[0]
    top_k = max(1, int(args.top_k))
    top = ranked[:top_k]

    # Build champion genome for OOS validation.
    champion_genome = StrategyGenome.from_dict(base_genome.to_dict())
    champion_genome.use_aether_gate = True
    champion_genome.aether_entropy_max = float(champion["aether_gate"]["entropy_max"])
    champion_genome.aether_coherence_min = float(champion["aether_gate"]["coherence_min"])
    champion_genome.aether_pc_min = float(champion["aether_gate"]["pc_min"])
    champion_genome.aether_force_min = float(champion["aether_gate"]["force_min"])
    champion_genome.aether_block_on_seam = bool(champion["aether_gate"]["block_on_seam"])
    champion_genome.aether_seam_force_override = float(champion["aether_gate"]["seam_force_override"])
    champion_genome.genome_id = champion_genome._generate_id()

    # Purged OOS walk-forward validation.
    wf_config = WalkForwardConfig(
        n_folds=args.wf_folds,
        train_bars=args.wf_train_bars,
        test_bars=args.wf_test_bars,
        step_bars=wf_step_bars,
        purge_bars=args.wf_purge_bars,
        min_trades_per_fold=args.wf_min_trades_per_fold,
        bootstrap_samples=args.wf_bootstrap,
    )
    oos_bt_config = BacktestConfig(
        initial_capital=args.capital,
        symbol=args.symbol,
        spread_pips=args.spread,
        slippage_pips=args.slippage,
        commission_per_lot=args.commission,
    )
    decision_logger = logging.getLogger("chimera.core.decision_engine")
    veto_logger = logging.getLogger("chimera.core.veto_cascade")
    prev_decision_level = decision_logger.level
    prev_veto_level = veto_logger.level
    decision_logger.setLevel(logging.ERROR)
    veto_logger.setLevel(logging.ERROR)
    try:
        oos_report = walk_forward(
            data=oos_data,
            genome=champion_genome,
            backtest_config=oos_bt_config,
            wf_config=wf_config,
        )
    finally:
        decision_logger.setLevel(prev_decision_level)
        veto_logger.setLevel(prev_veto_level)
    oos_eval = evaluate_oos_edge_policy(
        oos_report,
        min_pass_rate=args.oos_min_pass_rate,
        min_avg_sharpe=args.oos_min_avg_sharpe,
        min_avg_return=args.oos_min_avg_return,
        max_worst_drawdown=args.oos_max_worst_drawdown,
        min_total_trades=args.oos_min_total_trades,
        max_avg_no_trade_rate=args.oos_max_avg_no_trade_rate,
        min_return_ci_lower=args.oos_min_return_ci_lower,
    )

    train_policy_pass = bool(champion["passes_policy"])
    if not train_policy_pass:
        oos_eval["failure_reasons"].insert(0, "TRAIN_POLICY_FAILED")

    claim_edge = train_policy_pass and bool(oos_eval["passes"])
    verdict = "EDGE_CONFIRMED" if claim_edge else "NO_EDGE"

    train_failures = [t for t in ranked if not t["passes_policy"]][: max(1, args.failure_cases)]
    oos_fold_failures = [
        {
            "fold_id": f.fold_id,
            "fail_reasons": list(f.fail_reasons),
            "metrics": dict(f.metrics),
        }
        for f in oos_report.folds
        if not f.passed
    ][: max(1, args.failure_cases)]

    print("\n" + "=" * 60)
    print("AETHER RESEARCH REPORT")
    print("=" * 60)
    print(f"\nData bars: total={len(data)} train={len(train_data)} oos={len(oos_data)}")
    print(
        f"Calibration policy: trades>={args.min_trades}, sharpe>={args.min_sharpe}, "
        f"max_dd<={args.max_drawdown}, no_trade_rate<={args.max_no_trade_rate}"
    )
    print(
        f"OOS policy: pass_rate>={args.oos_min_pass_rate}, avg_sharpe>={args.oos_min_avg_sharpe}, "
        f"avg_return>={args.oos_min_avg_return}, worst_dd<={args.oos_max_worst_drawdown}, "
        f"total_trades>={args.oos_min_total_trades}, avg_no_trade<={args.oos_max_avg_no_trade_rate}, "
        f"ci_lower>={args.oos_min_return_ci_lower}"
    )
    print("\n--- Champion Thresholds (Train) ---")
    for k, v in champion["aether_gate"].items():
        print(f"{k}: {v}")
    print("\n--- Champion Train Metrics ---")
    for k, v in champion["metrics"].items():
        print(f"{k}: {v}")
    print(f"fitness: {champion['fitness']}")
    print(f"passes_train_policy: {champion['passes_policy']}")
    print(f"train_policy_failures: {champion.get('policy_failures', [])}")
    print("\n--- OOS Purged Walk-Forward Verdict ---")
    print(f"walkforward_verdict: {oos_report.verdict}")
    print(f"pipeline_verdict: {verdict}")
    print(f"claim_edge: {claim_edge}")
    if oos_eval["failure_reasons"]:
        print("failure_reasons:")
        for reason in oos_eval["failure_reasons"]:
            print(f"  - {reason}")

    payload = {
        "meta": {
            "timestamp": datetime.utcnow().isoformat(),
            "symbol": args.symbol,
            "total_bars": len(data),
            "train_bars": len(train_data),
            "oos_bars": len(oos_data),
            "trials": len(trials),
        },
        "train_split": {
            "train_ratio": args.train_ratio,
            "train_bars_arg": args.train_bars,
            "effective_train_bars": len(train_data),
            "effective_oos_bars": len(oos_data),
        },
        "calibration_policy": {
            "min_trades": args.min_trades,
            "min_sharpe": args.min_sharpe,
            "max_drawdown": args.max_drawdown,
            "max_no_trade_rate": args.max_no_trade_rate,
            "isolate_aether": bool(args.isolate_aether),
        },
        "oos_policy": {
            "min_pass_rate": args.oos_min_pass_rate,
            "min_avg_sharpe": args.oos_min_avg_sharpe,
            "min_avg_return": args.oos_min_avg_return,
            "max_worst_drawdown": args.oos_max_worst_drawdown,
            "min_total_trades": args.oos_min_total_trades,
            "max_avg_no_trade_rate": args.oos_max_avg_no_trade_rate,
            "min_return_ci_lower": args.oos_min_return_ci_lower,
        },
        "champion": champion,
        "top": top,
        "oos_walkforward": oos_report.to_dict(),
        "oos_evaluation": oos_eval,
        "failure_cases": {
            "train_policy_failures": train_failures,
            "oos_fold_failures": oos_fold_failures,
            "oos_gate_failures": list(oos_eval["failure_reasons"]),
        },
        "verdict": {
            "label": verdict,
            "claim_edge": claim_edge,
            "train_policy_pass": train_policy_pass,
            "oos_policy_pass": bool(oos_eval["passes"]),
            "refuse_reason": None if claim_edge else "Out-of-sample gates failed or train policy failed.",
        },
    }

    if args.output:
        out = Path(args.output)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(payload, indent=2))
        logger.info(f"Wrote research report to {out}")

    if (not claim_edge) and args.fail_on_no_edge:
        return 2
    return 0


def _load_json(path: Path) -> dict[str, Any]:
    with open(path, "r") as f:
        return json.load(f)


def _set_aether_gate_from_champion(genome: StrategyGenome, champion_gate: dict[str, Any]) -> None:
    genome.use_aether_gate = True
    genome.aether_entropy_max = float(champion_gate["entropy_max"])
    genome.aether_coherence_min = float(champion_gate["coherence_min"])
    genome.aether_pc_min = float(champion_gate["pc_min"])
    genome.aether_force_min = float(champion_gate["force_min"])
    genome.aether_block_on_seam = bool(champion_gate["block_on_seam"])
    genome.aether_seam_force_override = float(champion_gate["seam_force_override"])
    genome.genome_id = genome._generate_id()


def _compute_kill_switch_reasons(
    *,
    max_dd: float,
    dd_threshold: float,
    anomaly_score: float | None,
    anomaly_threshold: float,
) -> list[str]:
    reasons: list[str] = []
    if max_dd > dd_threshold:
        reasons.append(f"MAX_DD_BREACH_{max_dd:.2f}PCT>{dd_threshold:.2f}PCT")
    if anomaly_score is not None and anomaly_score > anomaly_threshold:
        reasons.append(f"ANOMALY_BREACH_{anomaly_score:.3f}>{anomaly_threshold:.3f}")
    return reasons


def run_aether_deploy(args):
    """
    Deploy champion thresholds from an AETHER research report into live canary artifacts.

    Produces:
    - CHAMPION_GENOME.json
    - LIVE_GATING_STATE.json
    - AETHER_DEPLOYMENT.json
    """
    logger.info("=" * 60)
    logger.info("OmegaQuant Chimera - AETHER Deploy")
    logger.info("=" * 60)

    report_path = Path(args.research)
    payload = _load_json(report_path)

    verdict = dict(payload.get("verdict", {}))
    claim_edge = bool(verdict.get("claim_edge", False))
    label = str(verdict.get("label", "NO_EDGE"))
    if not claim_edge or label != "EDGE_CONFIRMED":
        msg = (
            f"Refusing deployment: report verdict is {label} "
            f"(claim_edge={claim_edge}). Use --allow-no-edge to override."
        )
        logger.error(msg)
        if not args.allow_no_edge:
            return 2

    champion = dict(payload.get("champion", {}))
    champion_gate = dict(champion.get("aether_gate", {}))
    required = {
        "entropy_max",
        "coherence_min",
        "pc_min",
        "force_min",
        "block_on_seam",
        "seam_force_override",
    }
    if not champion_gate or not required.issubset(champion_gate.keys()):
        logger.error("Research payload missing champion.aether_gate fields")
        return 1

    if args.genome:
        genome = StrategyGenome.load(args.genome)
    else:
        genome = create_default_genome()
    _set_aether_gate_from_champion(genome, champion_gate)

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    champion_path = output_dir / "CHAMPION_GENOME.json"
    genome.save(str(champion_path))

    canary_mode = args.canary_mode.lower()
    if canary_mode not in {m.value for m in CanaryMode}:
        logger.error(f"Invalid canary mode: {args.canary_mode}")
        return 1

    now_iso = datetime.now(timezone.utc).isoformat()
    live_state = LiveGatingState(
        updated_at=now_iso,
        active_variant_id=genome.genome_id,
        active_config=genome.to_dict(),
        canary_mode=canary_mode,
        canary_start_time=now_iso if canary_mode != CanaryMode.OFF.value else None,
        canary_trades=0,
        canary_pnl=0.0,
        kill_switch_active=False,
        kill_switch_reason=None,
        previous_variant_id=args.previous_variant_id,
        max_drawdown_threshold=float(args.canary_max_dd),
        anomaly_threshold=float(args.anomaly_threshold),
    )
    live_state_path = output_dir / "LIVE_GATING_STATE.json"
    live_state.save(live_state_path)

    deployment = {
        "meta": {
            "timestamp": now_iso,
            "source_research_report": str(report_path.resolve()),
            "source_verdict": label,
            "source_claim_edge": claim_edge,
            "symbol": payload.get("meta", {}).get("symbol"),
        },
        "canary": {
            "mode": canary_mode,
            "canary_trades_required": int(args.canary_trades_required),
            "canary_max_dd_pct": float(args.canary_max_dd),
            "anomaly_threshold": float(args.anomaly_threshold),
        },
        "oos_policy": payload.get("oos_policy", {}),
        "oos_evaluation": payload.get("oos_evaluation", {}),
        "champion_gate": champion_gate,
        "champion_genome_id": genome.genome_id,
        "artifacts": {
            "champion_genome": str(champion_path),
            "live_gating_state": str(live_state_path),
        },
    }
    deployment_path = output_dir / "AETHER_DEPLOYMENT.json"
    deployment_path.write_text(json.dumps(deployment, indent=2))

    print("\n" + "=" * 60)
    print("AETHER DEPLOYMENT")
    print("=" * 60)
    print(f"report: {report_path}")
    print(f"source_verdict: {label}")
    print(f"source_claim_edge: {claim_edge}")
    print(f"genome_id: {genome.genome_id}")
    print(f"canary_mode: {canary_mode}")
    print(f"max_drawdown_threshold: {args.canary_max_dd}")
    print(f"anomaly_threshold: {args.anomaly_threshold}")
    print(f"wrote: {champion_path}")
    print(f"wrote: {live_state_path}")
    print(f"wrote: {deployment_path}")
    return 0


def run_aether_canary_update(args):
    """
    Update canary status and trigger kill-switch/promotions.
    """
    logger.info("=" * 60)
    logger.info("OmegaQuant Chimera - AETHER Canary Update")
    logger.info("=" * 60)

    state_path = Path(args.state)
    if not state_path.exists():
        logger.error(f"State file not found: {state_path}")
        return 1

    state = LiveGatingState.load(state_path)
    state.canary_trades = int(args.trades)
    state.canary_pnl = float(args.pnl)
    state.updated_at = datetime.now(timezone.utc).isoformat()

    kill_reasons = _compute_kill_switch_reasons(
        max_dd=float(args.max_dd),
        dd_threshold=float(state.max_drawdown_threshold),
        anomaly_score=(None if args.anomaly_score is None else float(args.anomaly_score)),
        anomaly_threshold=float(state.anomaly_threshold),
    )
    if kill_reasons:
        state.activate_kill_switch("|".join(kill_reasons))

    # Promote only if still armed.
    if not state.kill_switch_active:
        if (
            state.canary_mode == CanaryMode.PAPER.value
            and state.canary_trades >= int(args.canary_trades_required)
            and state.canary_pnl >= float(args.min_pnl_to_promote)
        ):
            state.canary_mode = CanaryMode.MICRO.value
        elif (
            state.canary_mode == CanaryMode.MICRO.value
            and state.canary_trades >= int(args.canary_trades_required) * 2
            and state.canary_pnl >= float(args.min_pnl_to_promote)
        ):
            state.canary_mode = CanaryMode.FULL.value

    state.save(state_path)

    print("\n" + "=" * 60)
    print("AETHER CANARY STATE")
    print("=" * 60)
    print(f"state: {state_path}")
    print(f"canary_mode: {state.canary_mode}")
    print(f"canary_trades: {state.canary_trades}")
    print(f"canary_pnl: {state.canary_pnl}")
    print(f"kill_switch_active: {state.kill_switch_active}")
    print(f"kill_switch_reason: {state.kill_switch_reason}")
    return 0


def _extract_feed_metrics(payload: dict[str, Any]) -> tuple[int, float, float, float | None]:
    missing = [k for k in ("trades", "pnl", "max_dd") if k not in payload]
    if missing:
        raise ValueError(f"FEED_MISSING_KEYS:{','.join(missing)}")
    trades = int(payload["trades"])
    pnl = float(payload["pnl"])
    max_dd = float(payload["max_dd"])
    anomaly_raw = payload.get("anomaly_score")
    anomaly = None if anomaly_raw is None else float(anomaly_raw)
    return trades, pnl, max_dd, anomaly


def _write_jsonl(path: Path, row: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a") as f:
        f.write(json.dumps(row) + "\n")


def run_aether_supervise(args):
    """
    Watch a live metrics feed and continuously apply canary updates.

    Feed format (JSON):
      {"trades": 12, "pnl": 87.5, "max_dd": 2.1, "anomaly_score": 0.7}
    """
    logger.info("=" * 60)
    logger.info("OmegaQuant Chimera - AETHER Supervisor")
    logger.info("=" * 60)

    state_path = Path(args.state)
    if not state_path.exists():
        logger.error(f"State file not found: {state_path}")
        return 1

    feed_path = Path(args.feed)
    output_dir = state_path.parent
    heartbeat_path = Path(args.heartbeat) if args.heartbeat else output_dir / "AETHER_SUPERVISOR_HEARTBEAT.json"
    log_path = Path(args.log) if args.log else output_dir / "AETHER_SUPERVISOR_LOG.jsonl"

    max_iterations = int(args.max_iterations)
    interval_seconds = max(0.0, float(args.interval_seconds))
    stale_seconds = float(args.require_fresh_seconds)
    max_errors = max(1, int(args.max_errors))
    stop_on_kill = not bool(args.no_stop_on_kill_switch)

    last_feed_sig: tuple[int, int] | None = None
    consecutive_errors = 0
    iteration = 0

    while True:
        iteration += 1
        now_iso = datetime.now(timezone.utc).isoformat()
        status = "IDLE"
        reason = None

        try:
            if not feed_path.exists():
                status = "ERROR"
                reason = "FEED_NOT_FOUND"
                consecutive_errors += 1
            else:
                st = feed_path.stat()
                age_seconds = max(0.0, time.time() - st.st_mtime)
                sig = (int(st.st_mtime_ns), int(st.st_size))

                if stale_seconds > 0 and age_seconds > stale_seconds:
                    status = "STALE"
                    reason = f"FEED_AGE_{age_seconds:.2f}>{stale_seconds:.2f}"
                elif (not args.update_on_unchanged) and sig == last_feed_sig:
                    status = "SKIP"
                    reason = "FEED_UNCHANGED"
                else:
                    payload = _load_json(feed_path)
                    trades, pnl, max_dd, anomaly = _extract_feed_metrics(payload)
                    update_args = argparse.Namespace(
                        state=str(state_path),
                        trades=trades,
                        pnl=pnl,
                        max_dd=max_dd,
                        anomaly_score=anomaly,
                        canary_trades_required=args.canary_trades_required,
                        min_pnl_to_promote=args.min_pnl_to_promote,
                    )
                    rc = run_aether_canary_update(update_args)
                    if rc != 0:
                        status = "ERROR"
                        reason = f"CANARY_UPDATE_RC_{rc}"
                        consecutive_errors += 1
                    else:
                        status = "UPDATED"
                        reason = "APPLIED"
                        consecutive_errors = 0
                        last_feed_sig = sig
        except Exception as exc:
            status = "ERROR"
            reason = f"EXCEPTION:{exc}"
            consecutive_errors += 1

        state_payload: dict[str, Any] = {}
        if state_path.exists():
            try:
                state_payload = _load_json(state_path)
            except Exception as exc:
                state_payload = {"state_load_error": str(exc)}

        heartbeat = {
            "timestamp": now_iso,
            "iteration": iteration,
            "status": status,
            "reason": reason,
            "consecutive_errors": consecutive_errors,
            "feed_path": str(feed_path),
            "state_path": str(state_path),
            "live_state": {
                "canary_mode": state_payload.get("canary_mode"),
                "canary_trades": state_payload.get("canary_trades"),
                "canary_pnl": state_payload.get("canary_pnl"),
                "kill_switch_active": state_payload.get("kill_switch_active"),
                "kill_switch_reason": state_payload.get("kill_switch_reason"),
            },
        }

        heartbeat_path.parent.mkdir(parents=True, exist_ok=True)
        heartbeat_path.write_text(json.dumps(heartbeat, indent=2))
        _write_jsonl(log_path, heartbeat)

        if state_payload.get("kill_switch_active") and stop_on_kill:
            logger.warning("Supervisor stopping: kill-switch is active")
            return 3

        if consecutive_errors >= max_errors:
            logger.error(f"Supervisor stopping: consecutive errors {consecutive_errors} >= {max_errors}")
            return 4

        if max_iterations > 0 and iteration >= max_iterations:
            return 0

        time.sleep(interval_seconds)


def run_robustness(args):
    """
    Adversarial robustness suite:
    - permutation test (return-shuffled OHLCV null)
    - bootstrap-max "reality check" across strategy variants
    - regime stress test scaffolding (scenario-based; currently synthetic)
    """
    logger.info("=" * 60)
    logger.info("OmegaQuant Chimera - Robustness Suite")
    logger.info("=" * 60)

    # This command can run many backtests (permutations/variants). Suppress
    # per-bar decision spam to keep output readable.
    logging.getLogger("chimera.core.decision_engine").setLevel(logging.ERROR)
    logging.getLogger("chimera.core.veto_cascade").setLevel(logging.ERROR)

    # Load or generate data
    loader = DataLoader(symbol=args.symbol)
    if args.data:
        logger.info(f"Loading data from {args.data}")
        data = loader.load_csv(Path(args.data))
    else:
        logger.info(f"Generating {args.bars} bars of synthetic data")
        if args.regime_data:
            data = loader.generate_regime_data(num_bars=args.bars)
        else:
            data = loader.generate_synthetic(num_bars=args.bars)

    # Integrity check (fail-closed unless --force)
    checker = IntegrityChecker()
    integrity = checker.check_series(data)
    if not integrity.valid and not args.force:
        logger.error(f"Data integrity check failed: {len(integrity.issues)} issues")
        logger.error("Use --force to run anyway")
        return 1

    # Backtest config (costs always on via spread)
    config = BacktestConfig(
        initial_capital=args.capital,
        symbol=args.symbol,
        spread_pips=args.spread,
    )

    # Strategy set: default genome + random variants
    genomes = [create_default_genome()]
    for _ in range(max(0, int(args.variants) - 1)):
        genomes.append(create_random_genome())

    # Observed + permutation null for the default genome
    perm_report = robustness_report(
        bars=data,
        genome=genomes[0],
        backtest_config=config,
        permutations=args.permutations,
        seed=args.seed,
    )

    # Bootstrap-max reality check across variants
    backtester = Backtester(config=config)
    series = []
    for g in genomes:
        res = backtester.run(data, g, create_manifest=False)
        eq = res.equity_curve
        rets = []
        for i in range(1, len(eq)):
            prev = eq[i - 1]
            cur = eq[i]
            rets.append(0.0 if prev == 0 else (cur - prev) / prev)
        series.append(rets)

    rc = reality_check_bootstrap_max(
        series,
        bootstrap_samples=args.bootstrap,
        seed=args.seed,
    )

    report = {
        "symbol": args.symbol,
        "bars": len(data),
        "config": {
            "spread_pips": args.spread,
            "permutations": args.permutations,
            "variants": args.variants,
            "bootstrap": args.bootstrap,
            "seed": args.seed,
        },
        "permutation_test": perm_report,
        "reality_check": {
            "observed_best_metric": rc.observed_best_metric,
            "p_value": rc.p_value,
            "strategies": rc.strategies,
            "bootstrap_samples": rc.bootstrap_samples,
        },
        "note": (
            "This report is a robustness aid, not a performance guarantee. "
            "Permutation nulls are synthetic unless real data is provided."
        ),
    }

    print("\n" + "=" * 60)
    print("ROBUSTNESS REPORT")
    print("=" * 60)
    print(f"\nSymbol: {report['symbol']}")
    print(f"Bars: {report['bars']}")
    print("\n--- Permutation Test (Return) ---")
    p_perm = report["permutation_test"]["permutation_null"]["p_value_return"]
    print(f"p_value_return: {p_perm}")
    print("\n--- Reality Check (Bootstrap-Max) ---")
    print(f"p_value: {report['reality_check']['p_value']}")
    print("\n" + "=" * 60)

    if args.output:
        out = Path(args.output)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(report, indent=2))
        logger.info(f"Wrote robustness report to {out}")

    return 0


def run_verify(args) -> int:
    """
    Unified verifier entrypoint (SSOT: CODEX_CONTEXT_PACK.md §7.8).

    Runs a minimal, reproducible suite:
    - compileall
    - unittest
    - CLI smoke (backtest + walkforward)
    - optional frontend lint/build (skippable)
    """

    repo_root = Path(__file__).parent.resolve()

    env = dict(os.environ)
    env.setdefault("PYTHONPYCACHEPREFIX", "/tmp/omega_pycache")

    def _run(cmd: list[str], *, cwd: Path) -> int:
        logger.info("verify: %s (cwd=%s)", " ".join(cmd), cwd)
        p = subprocess.run(cmd, cwd=str(cwd), env=env)
        return int(p.returncode)

    # 1) Python compile check
    rc = _run([sys.executable, "-m", "compileall", "-q", str(repo_root)], cwd=repo_root)
    if rc != 0:
        return rc

    # 2) Unit tests
    rc = _run([sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"], cwd=repo_root)
    if rc != 0:
        return rc

    # 3) CLI smokes
    tmp = Path(tempfile.gettempdir())
    rc = _run(
        [
            sys.executable,
            str(repo_root / "run.py"),
            "backtest",
            "--bars",
            "50",
            "--regime-data",
            "--spread",
            "1.0",
            "--output",
            str(tmp / "omega_verify_backtest.json"),
        ],
        cwd=repo_root,
    )
    if rc != 0:
        return rc

    rc = _run(
        [
            sys.executable,
            str(repo_root / "run.py"),
            "walkforward",
            "--bars",
            "300",
            "--regime-data",
            "--spread",
            "1.0",
            "--folds",
            "2",
            "--train-bars",
            "100",
            "--test-bars",
            "50",
            "--purge-bars",
            "5",
            "--bootstrap",
            "50",
            "--output",
            str(tmp / "omega_verify_wf.json"),
        ],
        cwd=repo_root,
    )
    if rc != 0:
        return rc

    # 4) Optional frontend checks (canonical UI only)
    if not getattr(args, "skip_frontend", False):
        npm = shutil.which("npm")
        if not npm:
            logger.warning("verify: npm not found; skipping frontend lint/build")
            return 0

        fe_root = repo_root / "omega_frontend"
        if getattr(args, "npm_ci", False):
            rc = _run([npm, "ci", "--no-audit", "--no-fund"], cwd=fe_root)
            if rc != 0:
                return rc

        rc = _run([npm, "run", "lint"], cwd=fe_root)
        if rc != 0:
            return rc

        rc = _run([npm, "run", "build"], cwd=fe_root)
        if rc != 0:
            return rc

    return 0


def main():
    parser = argparse.ArgumentParser(
        description="OmegaQuant Chimera - Fail-Closed FX Trading Brain"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # Backtest command
    bt_parser = subparsers.add_parser("backtest", help="Run a backtest")
    bt_parser.add_argument("--genome", "-g", help="Path to genome JSON file")
    bt_parser.add_argument("--data", "-d", help="Path to data CSV file")
    bt_parser.add_argument("--symbol", "-s", default="EURUSD", help="Symbol to trade")
    bt_parser.add_argument("--bars", "-b", type=int, default=2000, help="Number of bars for synthetic data")
    bt_parser.add_argument("--capital", "-c", type=float, default=10000, help="Initial capital")
    bt_parser.add_argument("--spread", type=float, default=1.0, help="Spread in pips")
    bt_parser.add_argument("--regime-data", action="store_true", help="Generate data with regime changes")
    bt_parser.add_argument("--output", "-o", help="Output path for results JSON")
    bt_parser.add_argument("--force", "-f", action="store_true", help="Run even if data integrity fails")
    
    # Evolution command
    evo_parser = subparsers.add_parser("evolve", help="Run DRQ evolution")
    evo_parser.add_argument("--symbol", "-s", default="EURUSD", help="Symbol to trade")
    evo_parser.add_argument("--bars", "-b", type=int, default=1000, help="Bars per scenario")
    evo_parser.add_argument("--capital", "-c", type=float, default=10000, help="Initial capital")
    evo_parser.add_argument("--spread", type=float, default=1.0, help="Base spread in pips")
    evo_parser.add_argument("--generations", "-n", type=int, default=20, help="Number of generations")
    evo_parser.add_argument("--population", "-p", type=int, default=20, help="Initial population size")
    evo_parser.add_argument("--children", type=int, default=10, help="Children per generation")
    evo_parser.add_argument("--mutation-rate", type=float, default=0.2, help="Mutation rate")
    evo_parser.add_argument("--stagnation-limit", type=int, default=10, help="Generations without improvement before stopping")
    evo_parser.add_argument("--output", "-o", help="Output directory for evolution state")
    
    # Analyze command
    analyze_parser = subparsers.add_parser("analyze", help="Analyze genome or results")
    analyze_parser.add_argument("--genome", "-g", help="Path to genome JSON file")
    analyze_parser.add_argument("--result", "-r", help="Path to result JSON file")
    
    # Sakana evolution command (DGM + DRQ hybrid)
    sakana_parser = subparsers.add_parser("sakana-evolve", help="Run Sakana-style DGM + DRQ evolution")
    sakana_parser.add_argument("--bars", "-b", type=int, default=1000, help="Total bars of data")
    sakana_parser.add_argument("--rounds", "-r", type=int, default=10, help="Number of evolution rounds")
    sakana_parser.add_argument("--variants", "-v", type=int, default=5, help="Variants per round")
    sakana_parser.add_argument("--train-bars", type=int, default=200, help="Training bars per fold")
    sakana_parser.add_argument("--test-bars", type=int, default=100, help="Test bars per fold")
    sakana_parser.add_argument("--folds", type=int, default=3, help="Number of walk-forward folds")
    sakana_parser.add_argument("--mutation-rate", type=float, default=0.2, help="Mutation rate")
    sakana_parser.add_argument("--mutation-strength", type=float, default=0.15, help="Mutation strength")
    sakana_parser.add_argument("--patch-budget", type=int, default=5, help="Max params to mutate per variant")
    sakana_parser.add_argument("--max-dd", type=float, default=15.0, help="Max drawdown threshold (%%)")
    sakana_parser.add_argument("--min-sharpe", type=float, default=0.0, help="Min Sharpe threshold")
    sakana_parser.add_argument("--max-turnover", type=float, default=50.0, help="Max turnover threshold")
    sakana_parser.add_argument("--stability", type=float, default=10.0, help="Max stability (return std) threshold")
    sakana_parser.add_argument("--no-attack", action="store_true", help="Disable adversarial attack phase")
    sakana_parser.add_argument("--attack-min-pass-rate", type=float, default=0.67, help="Min attack scenario pass ratio")
    sakana_parser.add_argument("--attack-max-fitness-degradation", type=float, default=0.50, help="Max allowed fitness degradation in attacks")
    sakana_parser.add_argument("--attack-drop-every-n", type=int, default=20, help="Drop every Nth bar in dropout attack")
    sakana_parser.add_argument("--attack-noise-sigma", type=float, default=0.0007, help="Noise sigma for price perturbation attack")
    sakana_parser.add_argument("--no-aether-attack", action="store_true", help="Disable Aether structural attack scenarios")
    sakana_parser.add_argument("--attack-aether-window-bars", type=int, default=240, help="Window length for Aether attack slices")
    sakana_parser.add_argument("--attack-entropy-window", type=int, default=64, help="Rolling entropy window for Aether attacks")
    sakana_parser.add_argument("--eval-retries", type=int, default=2, help="Retries for transient evaluator errors")
    sakana_parser.add_argument("--eval-retry-backoff", type=float, default=0.25, help="Backoff seconds between evaluation retries")
    sakana_parser.add_argument("--no-auto-resume", action="store_true", help="Disable state auto-resume from output artifacts")
    sakana_parser.add_argument("--no-watchdog", action="store_true", help="Disable watchdog heartbeat artifact")
    sakana_parser.add_argument("--watchdog-stale-seconds", type=int, default=900, help="Heartbeat stale threshold in seconds")
    sakana_parser.add_argument("--no-long-memory", action="store_true", help="Disable ROUND_MEMORY long-horizon ledger")
    sakana_parser.add_argument("--canary-trades", type=int, default=10, help="Trades required in canary mode")
    sakana_parser.add_argument("--canary-max-dd", type=float, default=5.0, help="Max DD in canary mode (%%)")
    sakana_parser.add_argument("--config", "-c", help="Path to initial config JSON")
    sakana_parser.add_argument("--output", "-o", default="./evolution_output", help="Output directory")

    # AETHER indicator command
    indicator_parser = subparsers.add_parser("indicator", help="Compute AETHER indicator state")
    indicator_parser.add_argument("--data", "-d", help="Path to OHLCV CSV file")
    indicator_parser.add_argument("--date-format", default="%Y-%m-%d %H:%M:%S", help="CSV timestamp format")
    indicator_parser.add_argument("--symbol", "-s", default="EURUSD", help="Symbol to analyze")
    indicator_parser.add_argument("--bars", "-b", type=int, default=800, help="Bars for synthetic data")
    indicator_parser.add_argument("--max-bars", type=int, default=5000, help="Max bars to process after loading")
    indicator_parser.add_argument("--regime-data", action="store_true", help="Generate synthetic regime-shift data")
    indicator_parser.add_argument("--tail", type=int, default=5, help="Print last N indicator rows")
    indicator_parser.add_argument("--output", "-o", help="Output path for indicator JSON")
    indicator_parser.add_argument("--force", "-f", action="store_true", help="Run even if data integrity fails")

    # AETHER gate calibration command
    calibrate_parser = subparsers.add_parser("aether-calibrate", help="Grid-search AETHER gate thresholds")
    calibrate_parser.add_argument("--genome", "-g", help="Path to base genome JSON file")
    calibrate_parser.add_argument("--data", "-d", help="Path to OHLCV CSV file")
    calibrate_parser.add_argument("--date-format", default="%Y-%m-%d %H:%M:%S", help="CSV timestamp format")
    calibrate_parser.add_argument("--symbol", "-s", default="EURUSD", help="Symbol to calibrate")
    calibrate_parser.add_argument("--bars", "-b", type=int, default=1200, help="Bars for synthetic data")
    calibrate_parser.add_argument("--max-bars", type=int, default=5000, help="Max bars to process after loading")
    calibrate_parser.add_argument("--regime-data", action="store_true", help="Generate synthetic regime-shift data")
    calibrate_parser.add_argument("--capital", "-c", type=float, default=10000, help="Initial capital")
    calibrate_parser.add_argument("--spread", type=float, default=1.0, help="Spread in pips")
    calibrate_parser.add_argument("--entropy-grid", default="0.65,0.8,0.95", help="Comma list for entropy max")
    calibrate_parser.add_argument("--coherence-grid", default="0.0,0.15,0.3", help="Comma list for coherence min")
    calibrate_parser.add_argument("--pc-grid", default="0.0,0.15,0.3", help="Comma list for cycle confidence min")
    calibrate_parser.add_argument("--force-grid", default="0.0,0.1,0.2", help="Comma list for absolute force min")
    calibrate_parser.add_argument("--seam-override-grid", default="0.25,0.45", help="Comma list for seam force override")
    calibrate_parser.add_argument("--include-seam-off", action="store_true", help="Also test block_on_seam=False")
    calibrate_parser.add_argument("--min-trades", type=int, default=10, help="Policy floor for trades")
    calibrate_parser.add_argument("--min-sharpe", type=float, default=0.0, help="Policy floor for Sharpe ratio")
    calibrate_parser.add_argument("--max-drawdown", type=float, default=20.0, help="Policy cap for max drawdown (%%)")
    calibrate_parser.add_argument("--max-no-trade-rate", type=float, default=0.995, help="Policy cap for no-trade rate")
    calibrate_parser.add_argument("--isolate-aether", action="store_true", help="Neutralize non-AETHER filters while calibrating")
    calibrate_parser.add_argument("--top-k", type=int, default=10, help="Show top K configs")
    calibrate_parser.add_argument("--output", "-o", help="Output path for calibration JSON")
    calibrate_parser.add_argument("--force", "-f", action="store_true", help="Run even if data integrity fails")

    # Falsifiable AETHER research pipeline (train calibrate + OOS purged walk-forward)
    research_parser = subparsers.add_parser(
        "aether-research",
        help="Calibrate AETHER gate on train, validate on purged OOS walk-forward, and enforce NO_EDGE on failure",
    )
    research_parser.add_argument("--genome", "-g", help="Path to base genome JSON file")
    research_parser.add_argument("--data", "-d", help="Path to OHLCV CSV file")
    research_parser.add_argument("--date-format", default="%Y-%m-%d %H:%M:%S", help="CSV timestamp format")
    research_parser.add_argument("--symbol", "-s", default="EURUSD", help="Symbol to research")
    research_parser.add_argument("--bars", "-b", type=int, default=2400, help="Bars for synthetic data")
    research_parser.add_argument("--max-bars", type=int, default=5000, help="Max bars to process after loading")
    research_parser.add_argument("--regime-data", action="store_true", help="Generate synthetic regime-shift data")
    research_parser.add_argument("--capital", "-c", type=float, default=10000, help="Initial capital")
    research_parser.add_argument("--spread", type=float, default=1.0, help="Spread in pips")
    research_parser.add_argument("--slippage", type=float, default=0.5, help="Slippage in pips for OOS walk-forward")
    research_parser.add_argument("--commission", type=float, default=0.0, help="Commission per lot for OOS walk-forward")
    research_parser.add_argument("--train-ratio", type=float, default=0.60, help="Train ratio if --train-bars is not set")
    research_parser.add_argument("--train-bars", type=int, default=0, help="Explicit train bars (0 uses --train-ratio)")
    research_parser.add_argument("--min-train-bars", type=int, default=300, help="Minimum train bars required")
    research_parser.add_argument("--entropy-grid", default="0.65,0.8,0.95", help="Comma list for entropy max")
    research_parser.add_argument("--coherence-grid", default="0.0,0.15,0.3", help="Comma list for coherence min")
    research_parser.add_argument("--pc-grid", default="0.0,0.15,0.3", help="Comma list for cycle confidence min")
    research_parser.add_argument("--force-grid", default="0.0,0.1,0.2", help="Comma list for absolute force min")
    research_parser.add_argument("--seam-override-grid", default="0.25,0.45", help="Comma list for seam force override")
    research_parser.add_argument("--include-seam-off", action="store_true", help="Also test block_on_seam=False")
    research_parser.add_argument("--min-trades", type=int, default=10, help="Train policy floor for trades")
    research_parser.add_argument("--min-sharpe", type=float, default=0.0, help="Train policy floor for Sharpe ratio")
    research_parser.add_argument("--max-drawdown", type=float, default=20.0, help="Train policy cap for max drawdown (%%)")
    research_parser.add_argument("--max-no-trade-rate", type=float, default=0.995, help="Train policy cap for no-trade rate")
    research_parser.add_argument("--isolate-aether", action="store_true", help="Neutralize non-AETHER filters during train calibration")
    research_parser.add_argument("--top-k", type=int, default=10, help="Include top K train configs in output")
    research_parser.add_argument("--wf-folds", type=int, default=5, help="OOS walk-forward folds")
    research_parser.add_argument("--wf-train-bars", type=int, default=250, help="OOS fold training bars")
    research_parser.add_argument("--wf-test-bars", type=int, default=125, help="OOS fold test bars")
    research_parser.add_argument("--wf-step-bars", type=int, default=0, help="OOS fold step bars (0 uses wf-test-bars)")
    research_parser.add_argument("--wf-purge-bars", type=int, default=5, help="OOS purge bars")
    research_parser.add_argument("--wf-min-trades-per-fold", type=int, default=3, help="OOS minimum trades per fold")
    research_parser.add_argument("--wf-bootstrap", type=int, default=1000, help="OOS bootstrap samples")
    research_parser.add_argument("--oos-min-pass-rate", type=float, default=0.60, help="OOS minimum fold pass rate")
    research_parser.add_argument("--oos-min-avg-sharpe", type=float, default=0.0, help="OOS minimum average Sharpe")
    research_parser.add_argument("--oos-min-avg-return", type=float, default=0.0, help="OOS minimum average return")
    research_parser.add_argument("--oos-max-worst-drawdown", type=float, default=20.0, help="OOS maximum worst drawdown (%%)")
    research_parser.add_argument("--oos-min-total-trades", type=int, default=10, help="OOS minimum total trades")
    research_parser.add_argument("--oos-max-avg-no-trade-rate", type=float, default=0.995, help="OOS maximum average no-trade rate")
    research_parser.add_argument("--oos-min-return-ci-lower", type=float, default=0.0, help="OOS minimum lower CI bound for average return")
    research_parser.add_argument("--failure-cases", type=int, default=10, help="Max failure cases to include per section")
    research_parser.add_argument("--fail-on-no-edge", action="store_true", help="Return non-zero when verdict is NO_EDGE")
    research_parser.add_argument("--output", "-o", help="Output path for research JSON")
    research_parser.add_argument("--force", "-f", action="store_true", help="Run even if data integrity fails")

    # AETHER deployment command (promote champion into live canary state)
    deploy_parser = subparsers.add_parser(
        "aether-deploy",
        help="Deploy champion from aether-research report into LIVE_GATING_STATE + CHAMPION_GENOME artifacts",
    )
    deploy_parser.add_argument("--research", "-r", required=True, help="Path to aether-research JSON report")
    deploy_parser.add_argument("--genome", "-g", help="Optional base genome JSON to patch with champion gate")
    deploy_parser.add_argument("--output-dir", "-o", default="./aether_live", help="Deployment artifact directory")
    deploy_parser.add_argument("--canary-mode", default="paper", choices=["off", "paper", "micro", "full"], help="Initial canary mode")
    deploy_parser.add_argument("--canary-trades-required", type=int, default=10, help="Trades required before canary promotion")
    deploy_parser.add_argument("--canary-max-dd", type=float, default=5.0, help="Kill-switch drawdown threshold (%%)")
    deploy_parser.add_argument("--anomaly-threshold", type=float, default=3.0, help="Kill-switch anomaly-score threshold")
    deploy_parser.add_argument("--previous-variant-id", help="Optional previous variant for manual rollback context")
    deploy_parser.add_argument("--allow-no-edge", action="store_true", help="Allow deployment even if report verdict is NO_EDGE")

    # Canary status update command (for live supervisors/watchdogs)
    canary_parser = subparsers.add_parser(
        "aether-canary-update",
        help="Update canary PnL/trades and enforce kill-switch or promotion transitions",
    )
    canary_parser.add_argument("--state", "-s", required=True, help="Path to LIVE_GATING_STATE.json")
    canary_parser.add_argument("--trades", type=int, required=True, help="Observed canary trade count")
    canary_parser.add_argument("--pnl", type=float, required=True, help="Observed canary PnL")
    canary_parser.add_argument("--max-dd", type=float, required=True, help="Observed max drawdown percent")
    canary_parser.add_argument("--anomaly-score", type=float, help="Optional anomaly score from watchdog")
    canary_parser.add_argument("--canary-trades-required", type=int, default=10, help="Trades required before canary promotion")
    canary_parser.add_argument("--min-pnl-to-promote", type=float, default=0.0, help="Minimum pnl required to promote canary mode")

    # Canary supervisor loop (auto-update from a live metrics feed)
    supervise_parser = subparsers.add_parser(
        "aether-supervise",
        help="Watch feed JSON and continuously apply canary updates with heartbeat/log artifacts",
    )
    supervise_parser.add_argument("--state", "-s", required=True, help="Path to LIVE_GATING_STATE.json")
    supervise_parser.add_argument("--feed", "-f", required=True, help="Path to live metrics JSON feed")
    supervise_parser.add_argument("--interval-seconds", type=float, default=60.0, help="Polling interval in seconds")
    supervise_parser.add_argument("--max-iterations", type=int, default=0, help="Max loop iterations (0 = run forever)")
    supervise_parser.add_argument("--require-fresh-seconds", type=float, default=0.0, help="Skip update if feed older than this (0 disables)")
    supervise_parser.add_argument("--update-on-unchanged", action="store_true", help="Apply update every loop even when feed file is unchanged")
    supervise_parser.add_argument("--canary-trades-required", type=int, default=10, help="Trades required before canary promotion")
    supervise_parser.add_argument("--min-pnl-to-promote", type=float, default=0.0, help="Minimum pnl required to promote canary mode")
    supervise_parser.add_argument("--max-errors", type=int, default=5, help="Stop after N consecutive supervisor errors")
    supervise_parser.add_argument("--no-stop-on-kill-switch", action="store_true", help="Do not stop loop when kill-switch becomes active")
    supervise_parser.add_argument("--heartbeat", help="Path for heartbeat JSON (default: state dir/AETHER_SUPERVISOR_HEARTBEAT.json)")
    supervise_parser.add_argument("--log", help="Path for jsonl log (default: state dir/AETHER_SUPERVISOR_LOG.jsonl)")

    # Walk-forward evaluation (purged)
    wf_parser = subparsers.add_parser("walkforward", help="Run purged walk-forward evaluation")
    wf_parser.add_argument("--genome", "-g", help="Path to genome JSON file")
    wf_parser.add_argument("--data", "-d", help="Path to data CSV file")
    wf_parser.add_argument("--symbol", "-s", default="EURUSD", help="Symbol to trade")
    wf_parser.add_argument("--bars", "-b", type=int, default=2000, help="Number of bars for synthetic data")
    wf_parser.add_argument("--capital", "-c", type=float, default=10000, help="Initial capital")
    wf_parser.add_argument("--spread", type=float, default=1.0, help="Spread in pips (must be > 0)")
    wf_parser.add_argument("--slippage", type=float, default=0.5, help="Slippage in pips")
    wf_parser.add_argument("--commission", type=float, default=0.0, help="Commission per lot")
    wf_parser.add_argument("--regime-data", action="store_true", help="Generate data with regime changes")
    wf_parser.add_argument("--force", "-f", action="store_true", help="Run even if data integrity fails")
    wf_parser.add_argument("--folds", type=int, default=5, help="Number of walk-forward folds")
    wf_parser.add_argument("--train-bars", type=int, default=250, help="Training bars per fold")
    wf_parser.add_argument("--test-bars", type=int, default=125, help="Test bars per fold")
    wf_parser.add_argument("--step-bars", type=int, default=0, help="Step size between folds (0 = test-bars)")
    wf_parser.add_argument("--purge-bars", type=int, default=5, help="Purge gap between train/test (bars)")
    wf_parser.add_argument("--min-trades-per-fold", type=int, default=3, help="Minimum trades required per fold")
    wf_parser.add_argument("--bootstrap", type=int, default=1000, help="Bootstrap samples for CI on avg return")
    wf_parser.add_argument("--output", "-o", help="Output path for report JSON")

    # Robustness suite (permutation tests + bootstrap-max reality check)
    rb_parser = subparsers.add_parser("robustness", help="Run robustness suite (permutation + reality check)")
    rb_parser.add_argument("--data", "-d", help="Path to data CSV file")
    rb_parser.add_argument("--symbol", "-s", default="EURUSD", help="Symbol to trade")
    rb_parser.add_argument("--bars", "-b", type=int, default=500, help="Number of bars for synthetic data")
    rb_parser.add_argument("--capital", "-c", type=float, default=10000, help="Initial capital")
    rb_parser.add_argument("--spread", type=float, default=1.0, help="Spread in pips (must be > 0)")
    rb_parser.add_argument("--regime-data", action="store_true", help="Generate data with regime changes")
    rb_parser.add_argument("--force", "-f", action="store_true", help="Run even if data integrity fails")
    rb_parser.add_argument("--permutations", type=int, default=200, help="Permutation runs for null distribution")
    rb_parser.add_argument("--variants", type=int, default=10, help="Strategy variants for reality check")
    rb_parser.add_argument("--bootstrap", type=int, default=500, help="Bootstrap samples for reality check")
    rb_parser.add_argument("--seed", type=int, default=1337, help="RNG seed")
    rb_parser.add_argument("--output", "-o", help="Output path for robustness JSON")

    # Unified verifier entrypoint
    verify_parser = subparsers.add_parser("verify", help="Run the unified verifier suite")
    verify_parser.add_argument(
        "--skip-frontend",
        action="store_true",
        help="Skip frontend lint/build (useful for Python-only environments)",
    )
    verify_parser.add_argument(
        "--npm-ci",
        action="store_true",
        help="Run `npm ci` in the canonical frontend before lint/build",
    )
    
    args = parser.parse_args()
    
    if args.command == "backtest":
        return run_backtest(args)
    elif args.command == "evolve":
        return run_evolution(args)
    elif args.command == "analyze":
        return run_analyze(args)
    elif args.command == "sakana-evolve":
        return run_sakana_evolve(args)
    elif args.command == "indicator":
        return run_indicator(args)
    elif args.command == "aether-calibrate":
        return run_aether_calibrate(args)
    elif args.command == "aether-research":
        return run_aether_research(args)
    elif args.command == "aether-deploy":
        return run_aether_deploy(args)
    elif args.command == "aether-canary-update":
        return run_aether_canary_update(args)
    elif args.command == "aether-supervise":
        return run_aether_supervise(args)
    elif args.command == "walkforward":
        # Normalize step-bars default.
        if getattr(args, "step_bars", 0) == 0:
            args.step_bars = args.test_bars
        return run_walkforward(args)
    elif args.command == "robustness":
        return run_robustness(args)
    elif args.command == "verify":
        return run_verify(args)
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())
