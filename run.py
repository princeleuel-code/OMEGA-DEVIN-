#!/usr/bin/env python3
"""
OmegaQuant Chimera - Main Runner

Command-line interface for running backtests, evolution, and analysis.
"""

import argparse
import json
import logging
import sys
from pathlib import Path
from datetime import datetime

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

from chimera.data.loader import DataLoader
from chimera.data.integrity import IntegrityChecker
from chimera.data.features import FeatureEngine
from chimera.evolution.genome import StrategyGenome, create_default_genome, create_random_genome
from chimera.evolution.drq_loop import DRQLoop, DRQConfig, Scenario, EvaluationResult
from chimera.evolution.behaviors import compute_behavior
from chimera.evaluation.backtest import Backtester, BacktestConfig, BacktestResult
from chimera.evaluation.score import Scorer, ScoreCard
from chimera.core.truth_manifest import TruthManifest


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("omegaquant")


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
    
    args = parser.parse_args()
    
    if args.command == "backtest":
        return run_backtest(args)
    elif args.command == "evolve":
        return run_evolution(args)
    elif args.command == "analyze":
        return run_analyze(args)
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())
