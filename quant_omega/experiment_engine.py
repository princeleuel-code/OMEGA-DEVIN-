#!/usr/bin/env python3
"""
QUANT-OMEGA: Recursive Improvement Loop / Experiment Engine
Version: 1.0.0

This module implements the closed-loop experiment engine for continuous
improvement of the QUANT-OMEGA trading system.

Features:
- Champion tracking and versioning
- Variant generation and testing
- Promotion pipeline
- Adversarial replay
- Weekly experiment cycle automation

Usage:
    python experiment_engine.py --mode propose --data data.csv
    python experiment_engine.py --mode evaluate --variant variant_001.json
    python experiment_engine.py --mode promote --variant variant_001.json
    python experiment_engine.py --mode adversarial --champion champion.json
"""

import argparse
import json
import os
import random
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any
import hashlib

import numpy as np
import pandas as pd

from quant_omega_backtest import (
    Parameters, QuantOmegaEngine, Backtester, 
    BacktestMetrics, load_data, evaluate_results
)


# ============================================================================
# CONFIGURATION
# ============================================================================

ARCHIVE_DIR = Path("archive")
CHAMPION_FILE = Path("champion.json")
IMPROVEMENT_LOG = Path("improvement_log.md")
EXPERIMENT_HISTORY = Path("experiment_history.json")


# ============================================================================
# DATA CLASSES
# ============================================================================

@dataclass
class Variant:
    """A parameter variant for testing."""
    id: str
    parent_id: str
    created: str
    parameters: Dict
    mutation_type: str
    mutation_details: str
    status: str = "PROPOSED"
    metrics: Optional[Dict] = None
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Variant':
        return cls(**data)


@dataclass
class Champion:
    """The current best performing configuration."""
    version: str
    created: str
    parameters: Dict
    performance: Dict
    regime_performance: Optional[Dict] = None
    stress_performance: Optional[Dict] = None
    history: List[str] = None
    
    def to_dict(self) -> Dict:
        d = asdict(self)
        if d['history'] is None:
            d['history'] = []
        return d
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Champion':
        return cls(**data)


@dataclass
class ExperimentResult:
    """Result of an experiment."""
    variant_id: str
    timestamp: str
    test_type: str
    passed: bool
    metrics: Dict
    notes: str


# ============================================================================
# VARIANT GENERATION
# ============================================================================

class VariantGenerator:
    """Generate parameter variants for testing."""
    
    MUTATION_TYPES = [
        "parameter_tweak",
        "regime_threshold",
        "risk_adjustment",
        "signal_sensitivity",
        "exit_optimization"
    ]
    
    PARAMETER_RANGES = {
        # Regime Detection
        'adx_period': (10, 20),
        'adx_threshold': (20, 35),
        'atr_period': (10, 20),
        'atr_slow_period': (40, 70),
        
        # Trend Following
        'ema_fast': (5, 12),
        'ema_slow': (15, 30),
        'ema_trend': (40, 80),
        
        # Mean Reversion
        'bb_period': (15, 30),
        'bb_std': (1.5, 2.5),
        'rsi_period': (10, 20),
        
        # Breakout
        'donchian_period': (15, 30),
        'squeeze_kc_mult': (1.2, 2.0),
        
        # Confidence
        'conf_no_trade': (20, 40),
        'conf_watch': (40, 60),
        'conf_small': (60, 80),
        'conf_strong': (75, 95),
        
        # Risk Management
        'risk_per_trade': (0.5, 2.0),
        'stop_multiplier': (1.5, 3.0),
        'tp_multiplier': (2.0, 5.0),
    }
    
    def __init__(self, base_params: Parameters):
        self.base_params = base_params
    
    def generate_id(self) -> str:
        """Generate unique variant ID."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        random_suffix = hashlib.md5(str(random.random()).encode()).hexdigest()[:6]
        return f"variant_{timestamp}_{random_suffix}"
    
    def mutate_parameter(self, param_name: str, current_value: Any, 
                        mutation_strength: float = 0.2) -> Any:
        """Mutate a single parameter."""
        if param_name not in self.PARAMETER_RANGES:
            return current_value
        
        min_val, max_val = self.PARAMETER_RANGES[param_name]
        
        if isinstance(current_value, int):
            delta = int((max_val - min_val) * mutation_strength)
            new_value = current_value + random.randint(-delta, delta)
            return max(min_val, min(max_val, new_value))
        else:
            delta = (max_val - min_val) * mutation_strength
            new_value = current_value + random.uniform(-delta, delta)
            return max(min_val, min(max_val, round(new_value, 2)))
    
    def generate_variant(self, mutation_type: str = None, 
                        parent_id: str = "champion") -> Variant:
        """Generate a new variant."""
        if mutation_type is None:
            mutation_type = random.choice(self.MUTATION_TYPES)
        
        params = self.base_params.to_dict()
        mutation_details = []
        
        if mutation_type == "parameter_tweak":
            # Randomly tweak 1-3 parameters
            n_params = random.randint(1, 3)
            param_names = random.sample(list(self.PARAMETER_RANGES.keys()), n_params)
            for param in param_names:
                if param in params:
                    old_val = params[param]
                    params[param] = self.mutate_parameter(param, old_val)
                    mutation_details.append(f"{param}: {old_val} -> {params[param]}")
        
        elif mutation_type == "regime_threshold":
            # Adjust regime detection thresholds
            for param in ['adx_threshold', 'atr_period', 'atr_slow_period']:
                if param in params:
                    old_val = params[param]
                    params[param] = self.mutate_parameter(param, old_val, 0.15)
                    mutation_details.append(f"{param}: {old_val} -> {params[param]}")
        
        elif mutation_type == "risk_adjustment":
            # Adjust risk parameters
            for param in ['risk_per_trade', 'stop_multiplier', 'tp_multiplier']:
                if param in params:
                    old_val = params[param]
                    params[param] = self.mutate_parameter(param, old_val, 0.25)
                    mutation_details.append(f"{param}: {old_val} -> {params[param]}")
        
        elif mutation_type == "signal_sensitivity":
            # Adjust signal generation parameters
            for param in ['ema_fast', 'ema_slow', 'rsi_period', 'bb_std']:
                if param in params:
                    old_val = params[param]
                    params[param] = self.mutate_parameter(param, old_val, 0.2)
                    mutation_details.append(f"{param}: {old_val} -> {params[param]}")
        
        elif mutation_type == "exit_optimization":
            # Optimize exit parameters
            for param in ['stop_multiplier', 'tp_multiplier', 'conf_small', 'conf_strong']:
                if param in params:
                    old_val = params[param]
                    params[param] = self.mutate_parameter(param, old_val, 0.2)
                    mutation_details.append(f"{param}: {old_val} -> {params[param]}")
        
        return Variant(
            id=self.generate_id(),
            parent_id=parent_id,
            created=datetime.now().isoformat(),
            parameters=params,
            mutation_type=mutation_type,
            mutation_details="; ".join(mutation_details)
        )
    
    def generate_batch(self, n_variants: int = 3) -> List[Variant]:
        """Generate a batch of variants."""
        variants = []
        mutation_types = random.sample(self.MUTATION_TYPES, min(n_variants, len(self.MUTATION_TYPES)))
        
        for i, mt in enumerate(mutation_types):
            variant = self.generate_variant(mutation_type=mt)
            variants.append(variant)
        
        return variants


# ============================================================================
# EXPERIMENT ENGINE
# ============================================================================

class ExperimentEngine:
    """Main experiment engine for recursive improvement."""
    
    def __init__(self, data_path: str, output_dir: str = "experiments"):
        self.data_path = data_path
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.archive_dir = self.output_dir / "archive"
        self.archive_dir.mkdir(exist_ok=True)
        
        self.champion_file = self.output_dir / "champion.json"
        self.history_file = self.output_dir / "experiment_history.json"
        self.log_file = self.output_dir / "improvement_log.md"
        
        self.df = None
        self.history: List[Dict] = []
        
        self._load_history()
    
    def _load_history(self):
        """Load experiment history."""
        if self.history_file.exists():
            with open(self.history_file) as f:
                self.history = json.load(f)
    
    def _save_history(self):
        """Save experiment history."""
        with open(self.history_file, 'w') as f:
            json.dump(self.history, f, indent=2, default=str)
    
    def _load_data(self):
        """Load market data."""
        if self.df is None:
            self.df = load_data(self.data_path)
        return self.df
    
    def get_champion(self) -> Optional[Champion]:
        """Get current champion."""
        if self.champion_file.exists():
            with open(self.champion_file) as f:
                return Champion.from_dict(json.load(f))
        return None
    
    def save_champion(self, champion: Champion):
        """Save champion."""
        with open(self.champion_file, 'w') as f:
            json.dump(champion.to_dict(), f, indent=2, default=str)
    
    def save_variant(self, variant: Variant):
        """Save variant to archive."""
        variant_file = self.archive_dir / f"{variant.id}.json"
        with open(variant_file, 'w') as f:
            json.dump(variant.to_dict(), f, indent=2, default=str)
    
    def load_variant(self, variant_id: str) -> Optional[Variant]:
        """Load variant from archive."""
        variant_file = self.archive_dir / f"{variant_id}.json"
        if variant_file.exists():
            with open(variant_file) as f:
                return Variant.from_dict(json.load(f))
        return None
    
    def propose_variants(self, n_variants: int = 3) -> List[Variant]:
        """Propose new variants for testing."""
        champion = self.get_champion()
        
        if champion:
            base_params = Parameters(**champion.parameters)
            parent_id = champion.version
        else:
            base_params = Parameters()
            parent_id = "default"
        
        generator = VariantGenerator(base_params)
        variants = generator.generate_batch(n_variants)
        
        for variant in variants:
            variant.parent_id = parent_id
            self.save_variant(variant)
            print(f"Proposed: {variant.id} ({variant.mutation_type})")
            print(f"  Changes: {variant.mutation_details}")
        
        return variants
    
    def quick_test(self, variant: Variant) -> BacktestMetrics:
        """Run quick test (1-year backtest, no walk-forward)."""
        df = self._load_data()
        
        # Use last year of data
        if len(df) > 252:
            df = df.iloc[-252:]
        
        params = Parameters(**variant.parameters)
        engine = QuantOmegaEngine(params)
        backtester = Backtester(engine)
        
        metrics = backtester.run(df)
        return metrics
    
    def full_evaluation(self, variant: Variant) -> Dict:
        """Run full evaluation (walk-forward + regime slicing + stress tests)."""
        df = self._load_data()
        
        params = Parameters(**variant.parameters)
        engine = QuantOmegaEngine(params)
        backtester = Backtester(engine)
        
        results = {
            'main': backtester.run(df).to_dict(),
            'walk_forward': [],
            'regime': {},
            'stress': {}
        }
        
        # Walk-forward
        wf_results = backtester.walk_forward(df)
        results['walk_forward'] = [m.to_dict() for m in wf_results]
        
        # Regime slicing
        regime_results = backtester.regime_slice(df)
        results['regime'] = {k: v.to_dict() for k, v in regime_results.items()}
        
        # Stress tests
        stress_results = backtester.stress_test(df)
        results['stress'] = {k: v.to_dict() for k, v in stress_results.items()}
        
        # Evaluation gates
        main_metrics = BacktestMetrics(**results['main'])
        results['gates'] = evaluate_results(main_metrics, params)
        
        # Update variant
        variant.metrics = results
        variant.status = "EVALUATED"
        self.save_variant(variant)
        
        return results
    
    def compare_to_champion(self, variant: Variant) -> Dict:
        """Compare variant to current champion."""
        champion = self.get_champion()
        
        if not champion:
            return {'beats_champion': True, 'reason': 'No champion exists'}
        
        if not variant.metrics:
            return {'beats_champion': False, 'reason': 'Variant not evaluated'}
        
        champion_exp = champion.performance.get('expectancy', 0)
        variant_exp = variant.metrics['main'].get('expectancy', 0)
        
        champion_sharpe = champion.performance.get('sharpe_ratio', 0)
        variant_sharpe = variant.metrics['main'].get('sharpe_ratio', 0)
        
        champion_dd = champion.performance.get('max_drawdown_pct', 100)
        variant_dd = variant.metrics['main'].get('max_drawdown_pct', 100)
        
        # Variant must beat champion on expectancy AND not have worse drawdown
        beats = (variant_exp > champion_exp * 1.05 and  # 5% improvement
                 variant_dd <= champion_dd * 1.1 and  # Not more than 10% worse DD
                 variant_sharpe >= champion_sharpe * 0.9)  # Not more than 10% worse Sharpe
        
        return {
            'beats_champion': beats,
            'champion_expectancy': champion_exp,
            'variant_expectancy': variant_exp,
            'champion_sharpe': champion_sharpe,
            'variant_sharpe': variant_sharpe,
            'champion_dd': champion_dd,
            'variant_dd': variant_dd
        }
    
    def promote_variant(self, variant: Variant) -> bool:
        """Promote variant to champion."""
        if not variant.metrics:
            print("Cannot promote: variant not evaluated")
            return False
        
        gates = variant.metrics.get('gates', {})
        if not gates.get('all_passed', False):
            print("Cannot promote: evaluation gates not passed")
            return False
        
        comparison = self.compare_to_champion(variant)
        if not comparison['beats_champion']:
            print(f"Cannot promote: does not beat champion")
            print(f"  Reason: {comparison}")
            return False
        
        # Get current champion for history
        old_champion = self.get_champion()
        history = old_champion.history if old_champion else []
        if old_champion:
            history.append(old_champion.version)
        
        # Create new champion
        new_version = f"1.{len(history)}.0"
        new_champion = Champion(
            version=new_version,
            created=datetime.now().isoformat(),
            parameters=variant.parameters,
            performance=variant.metrics['main'],
            regime_performance=variant.metrics.get('regime'),
            stress_performance=variant.metrics.get('stress'),
            history=history
        )
        
        self.save_champion(new_champion)
        
        # Update variant status
        variant.status = "PROMOTED"
        self.save_variant(variant)
        
        # Log promotion
        self._log_promotion(variant, old_champion, new_champion, comparison)
        
        print(f"Promoted {variant.id} to champion v{new_version}")
        return True
    
    def _log_promotion(self, variant: Variant, old_champion: Optional[Champion], 
                      new_champion: Champion, comparison: Dict):
        """Log promotion to improvement log."""
        with open(self.log_file, 'a') as f:
            f.write(f"\n## Promotion: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n")
            f.write(f"**Variant:** {variant.id}\n")
            f.write(f"**New Version:** {new_champion.version}\n")
            f.write(f"**Mutation Type:** {variant.mutation_type}\n")
            f.write(f"**Changes:** {variant.mutation_details}\n\n")
            
            f.write("**Performance Comparison:**\n")
            f.write(f"- Expectancy: {comparison.get('champion_expectancy', 'N/A')} -> {comparison.get('variant_expectancy', 'N/A')}\n")
            f.write(f"- Sharpe: {comparison.get('champion_sharpe', 'N/A')} -> {comparison.get('variant_sharpe', 'N/A')}\n")
            f.write(f"- Max DD: {comparison.get('champion_dd', 'N/A')}% -> {comparison.get('variant_dd', 'N/A')}%\n\n")
    
    def adversarial_replay(self) -> Dict:
        """Run adversarial replay on champion."""
        champion = self.get_champion()
        if not champion:
            return {'passed': False, 'reason': 'No champion exists'}
        
        df = self._load_data()
        params = Parameters(**champion.parameters)
        engine = QuantOmegaEngine(params)
        backtester = Backtester(engine)
        
        results = {}
        
        # Find worst drawdown periods
        full_metrics = backtester.run(df)
        
        # Test with 3x costs (extreme stress)
        extreme_stress = backtester.run(df, cost_multiplier=3.0, slippage_multiplier=3.0)
        results['extreme_stress'] = {
            'expectancy': extreme_stress.expectancy,
            'passed': extreme_stress.expectancy > 0
        }
        
        # Test on low volatility periods only
        df_indicators = engine.calculate_indicators(df)
        low_vol_mask = df_indicators['atr_ratio'] < 0.8
        if low_vol_mask.sum() > 100:
            low_vol_df = df[low_vol_mask]
            low_vol_metrics = backtester.run(low_vol_df)
            results['low_vol'] = {
                'expectancy': low_vol_metrics.expectancy,
                'passed': low_vol_metrics.expectancy >= 0  # Just don't lose money
            }
        
        # Overall pass
        all_passed = all(r.get('passed', False) for r in results.values())
        results['overall_passed'] = all_passed
        
        if not all_passed:
            print("WARNING: Champion failed adversarial replay!")
            print(f"Results: {results}")
        
        return results
    
    def weekly_cycle(self):
        """Run the weekly experiment cycle."""
        print("=" * 60)
        print("QUANT-OMEGA Weekly Experiment Cycle")
        print(f"Date: {datetime.now().strftime('%Y-%m-%d')}")
        print("=" * 60)
        
        # Step 1: Adversarial replay on current champion
        print("\n[1/5] Running adversarial replay on champion...")
        adversarial_results = self.adversarial_replay()
        if not adversarial_results.get('overall_passed', True):
            print("WARNING: Champion failed adversarial replay - investigation needed")
        
        # Step 2: Propose variants
        print("\n[2/5] Proposing new variants...")
        variants = self.propose_variants(n_variants=3)
        
        # Step 3: Quick test variants
        print("\n[3/5] Running quick tests...")
        promising = []
        for variant in variants:
            metrics = self.quick_test(variant)
            print(f"  {variant.id}: expectancy=${metrics.expectancy:.2f}, win_rate={metrics.win_rate:.2%}")
            if metrics.expectancy > 0 and metrics.win_rate > 0.4:
                promising.append(variant)
        
        # Step 4: Full evaluation on promising variants
        print(f"\n[4/5] Full evaluation on {len(promising)} promising variants...")
        candidates = []
        for variant in promising:
            print(f"  Evaluating {variant.id}...")
            results = self.full_evaluation(variant)
            if results['gates'].get('all_passed', False):
                candidates.append(variant)
                print(f"    PASSED all gates")
            else:
                print(f"    FAILED gates: {[k for k, v in results['gates'].items() if not v]}")
        
        # Step 5: Promote best candidate
        print(f"\n[5/5] Promotion decision for {len(candidates)} candidates...")
        promoted = False
        for variant in candidates:
            comparison = self.compare_to_champion(variant)
            if comparison['beats_champion']:
                if self.promote_variant(variant):
                    promoted = True
                    break
        
        if not promoted:
            print("No variant promoted this cycle")
        
        # Log weekly question
        self._log_weekly_question()
        
        print("\n" + "=" * 60)
        print("Weekly cycle complete")
        print("=" * 60)
    
    def _log_weekly_question(self):
        """Log the weekly reflection question."""
        with open(self.log_file, 'a') as f:
            f.write(f"\n## Weekly Reflection: {datetime.now().strftime('%Y-%m-%d')}\n\n")
            f.write("**Question:** What did we learn this week that reduces self-deception in evaluation?\n\n")
            f.write("**Answer:** [TO BE FILLED]\n\n")
            f.write("---\n")


# ============================================================================
# PARAMETER SENSITIVITY ANALYSIS
# ============================================================================

class SensitivityAnalyzer:
    """Analyze parameter sensitivity."""
    
    def __init__(self, base_params: Parameters, data_path: str):
        self.base_params = base_params
        self.data_path = data_path
        self.df = load_data(data_path)
    
    def analyze_parameter(self, param_name: str, 
                         variations: List[float] = [-0.2, -0.1, 0, 0.1, 0.2]) -> Dict:
        """Analyze sensitivity to a single parameter."""
        results = []
        base_value = getattr(self.base_params, param_name)
        
        for var in variations:
            # Create modified params
            params_dict = self.base_params.to_dict()
            
            if isinstance(base_value, int):
                new_value = int(base_value * (1 + var))
            else:
                new_value = base_value * (1 + var)
            
            params_dict[param_name] = new_value
            params = Parameters(**params_dict)
            
            # Run backtest
            engine = QuantOmegaEngine(params)
            backtester = Backtester(engine)
            metrics = backtester.run(self.df)
            
            results.append({
                'variation': var,
                'value': new_value,
                'expectancy': metrics.expectancy,
                'win_rate': metrics.win_rate,
                'sharpe': metrics.sharpe_ratio,
                'max_dd': metrics.max_drawdown_pct
            })
        
        # Calculate stability
        expectancies = [r['expectancy'] for r in results]
        stability = 1 - (np.std(expectancies) / (np.mean(expectancies) + 1e-10))
        
        return {
            'parameter': param_name,
            'base_value': base_value,
            'results': results,
            'stability': stability,
            'stable': stability > 0.7  # 70% stability threshold
        }
    
    def full_analysis(self) -> Dict:
        """Run full sensitivity analysis on all key parameters."""
        key_params = [
            'adx_threshold', 'ema_fast', 'ema_slow', 'bb_period', 'bb_std',
            'rsi_period', 'donchian_period', 'stop_multiplier', 'tp_multiplier'
        ]
        
        results = {}
        for param in key_params:
            print(f"Analyzing {param}...")
            results[param] = self.analyze_parameter(param)
        
        # Overall stability
        stable_count = sum(1 for r in results.values() if r['stable'])
        results['overall'] = {
            'stable_params': stable_count,
            'total_params': len(key_params),
            'stability_ratio': stable_count / len(key_params)
        }
        
        return results


# ============================================================================
# MAIN
# ============================================================================

def main():
    parser = argparse.ArgumentParser(description='QUANT-OMEGA Experiment Engine')
    parser.add_argument('--mode', type=str, required=True,
                       choices=['propose', 'quick-test', 'evaluate', 'promote', 
                               'adversarial', 'weekly', 'sensitivity'],
                       help='Operation mode')
    parser.add_argument('--data', type=str, required=True, help='Path to OHLCV CSV')
    parser.add_argument('--output', type=str, default='experiments', help='Output directory')
    parser.add_argument('--variant', type=str, help='Variant ID for evaluate/promote')
    parser.add_argument('--n-variants', type=int, default=3, help='Number of variants to propose')
    
    args = parser.parse_args()
    
    engine = ExperimentEngine(args.data, args.output)
    
    if args.mode == 'propose':
        variants = engine.propose_variants(args.n_variants)
        print(f"\nProposed {len(variants)} variants")
    
    elif args.mode == 'quick-test':
        if not args.variant:
            print("Error: --variant required for quick-test mode")
            return
        variant = engine.load_variant(args.variant)
        if not variant:
            print(f"Error: variant {args.variant} not found")
            return
        metrics = engine.quick_test(variant)
        print(f"Quick test results for {args.variant}:")
        print(f"  Expectancy: ${metrics.expectancy:.2f}")
        print(f"  Win rate: {metrics.win_rate:.2%}")
        print(f"  Sharpe: {metrics.sharpe_ratio:.2f}")
    
    elif args.mode == 'evaluate':
        if not args.variant:
            print("Error: --variant required for evaluate mode")
            return
        variant = engine.load_variant(args.variant)
        if not variant:
            print(f"Error: variant {args.variant} not found")
            return
        results = engine.full_evaluation(variant)
        print(f"Full evaluation results for {args.variant}:")
        print(f"  Gates passed: {results['gates']['all_passed']}")
        for gate, passed in results['gates'].items():
            if gate != 'all_passed':
                print(f"    {gate}: {'PASS' if passed else 'FAIL'}")
    
    elif args.mode == 'promote':
        if not args.variant:
            print("Error: --variant required for promote mode")
            return
        variant = engine.load_variant(args.variant)
        if not variant:
            print(f"Error: variant {args.variant} not found")
            return
        success = engine.promote_variant(variant)
        if success:
            print(f"Successfully promoted {args.variant}")
        else:
            print(f"Failed to promote {args.variant}")
    
    elif args.mode == 'adversarial':
        results = engine.adversarial_replay()
        print("Adversarial replay results:")
        for test, result in results.items():
            if isinstance(result, dict):
                print(f"  {test}: {'PASS' if result.get('passed') else 'FAIL'}")
    
    elif args.mode == 'weekly':
        engine.weekly_cycle()
    
    elif args.mode == 'sensitivity':
        champion = engine.get_champion()
        if champion:
            params = Parameters(**champion.parameters)
        else:
            params = Parameters()
        
        analyzer = SensitivityAnalyzer(params, args.data)
        results = analyzer.full_analysis()
        
        print("\nSensitivity Analysis Results:")
        print(f"Overall stability: {results['overall']['stability_ratio']:.2%}")
        print("\nParameter stability:")
        for param, data in results.items():
            if param != 'overall':
                status = "STABLE" if data['stable'] else "UNSTABLE"
                print(f"  {param}: {status} (stability={data['stability']:.2f})")


if __name__ == '__main__':
    main()
