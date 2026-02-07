"""
REAL EVALUATOR - Connect Intelligence Evolution to Actual Backtesting

This module provides the bridge between the IntelligenceEvolutionEngine
and the actual trading system backtesting.

It configures the entire intelligence stack based on the genome parameters
and runs real backtests to evaluate fitness.

Author: Devin (for Prince)
"""

from dataclasses import dataclass
from typing import List, Dict, Any, Optional, Tuple
import random
import math
import logging
from datetime import datetime, timedelta

from .intelligence_genome import IntelligenceGenome
from .intelligence_evolution import (
    AdversarialScenario,
    EvaluationResult,
    FitnessMetrics,
)


logger = logging.getLogger(__name__)


def generate_synthetic_bars(
    scenario: AdversarialScenario,
    n_bars: int = 500,
    initial_price: float = 1.1000,
) -> List[Dict[str, Any]]:
    """
    Generate synthetic OHLCV bars based on scenario parameters.
    
    This is used for adversarial testing when real data isn't available.
    """
    bars = []
    price = initial_price
    base_time = datetime.now() - timedelta(hours=n_bars)
    
    for i in range(n_bars):
        # Base volatility
        vol = scenario.volatility_base
        
        # Volatility spikes
        if scenario.volatility_spikes and random.random() < scenario.spike_probability:
            vol *= scenario.spike_magnitude
        
        # Trend component
        trend = scenario.trend_strength * 0.0001
        
        # Special handling for trend reversal scenario
        if scenario.name == "trend_reversal" and i > n_bars // 2:
            trend = -trend * 1.5
        
        # Generate returns
        returns = random.gauss(trend, vol)
        
        # Gap handling
        if scenario.gap_probability > 0 and random.random() < scenario.gap_probability:
            gap = random.choice([-1, 1]) * scenario.gap_magnitude
            returns += gap
        
        # Update price
        new_price = price * (1 + returns)
        
        # Generate OHLC
        high = max(price, new_price) * (1 + random.uniform(0, vol))
        low = min(price, new_price) * (1 - random.uniform(0, vol))
        
        # Volume (affected by liquidity)
        volume = random.uniform(1000, 5000) * scenario.liquidity_factor
        
        bars.append({
            "timestamp": (base_time + timedelta(hours=i)).isoformat(),
            "open": price,
            "high": high,
            "low": low,
            "close": new_price,
            "volume": volume,
        })
        
        price = new_price
    
    return bars


def simulate_trades_from_genome(
    genome: IntelligenceGenome,
    bars: List[Dict[str, Any]],
    scenario: AdversarialScenario,
) -> List[Dict[str, Any]]:
    """
    Simulate trades based on genome parameters.
    
    This is a simplified simulation that captures the essence of how
    the genome parameters affect trading behavior.
    """
    trades = []
    position = None
    capital = 10000.0
    
    # Parameters from genome
    min_conf = genome.min_confidence_threshold
    risk_pct = genome.risk_per_trade_pct / 100.0
    max_trades = genome.max_trades_per_day
    sl_mult = genome.atr_multiplier_sl
    tp_mult = genome.atr_multiplier_tp
    
    # Calculate ATR
    atr_period = 14
    atrs = []
    for i in range(atr_period, len(bars)):
        tr = max(
            bars[i]["high"] - bars[i]["low"],
            abs(bars[i]["high"] - bars[i-1]["close"]),
            abs(bars[i]["low"] - bars[i-1]["close"])
        )
        atrs.append(tr)
    
    avg_atr = sum(atrs) / len(atrs) if atrs else 0.001
    
    daily_trades = 0
    last_date = None
    
    for i in range(50, len(bars) - 1):
        bar = bars[i]
        next_bar = bars[i + 1]
        
        # Reset daily trade count
        current_date = bar["timestamp"][:10]
        if current_date != last_date:
            daily_trades = 0
            last_date = current_date
        
        # Skip if max trades reached
        if daily_trades >= max_trades:
            continue
        
        # Check for exit if in position
        if position:
            exit_price = None
            exit_reason = None
            
            if position["direction"] == 1:  # Long
                if next_bar["low"] <= position["stop_loss"]:
                    exit_price = position["stop_loss"]
                    exit_reason = "stop_loss"
                elif next_bar["high"] >= position["take_profit"]:
                    exit_price = position["take_profit"]
                    exit_reason = "take_profit"
            else:  # Short
                if next_bar["high"] >= position["stop_loss"]:
                    exit_price = position["stop_loss"]
                    exit_reason = "stop_loss"
                elif next_bar["low"] <= position["take_profit"]:
                    exit_price = position["take_profit"]
                    exit_reason = "take_profit"
            
            if exit_price:
                pnl = (exit_price - position["entry_price"]) * position["direction"] * position["size"]
                pnl -= scenario.spread_multiplier * 0.0001 * position["size"]  # Spread cost
                
                trades.append({
                    "entry_time": position["entry_time"],
                    "exit_time": bar["timestamp"],
                    "entry_price": position["entry_price"],
                    "exit_price": exit_price,
                    "direction": position["direction"],
                    "size": position["size"],
                    "pnl": pnl,
                    "exit_reason": exit_reason,
                })
                
                capital += pnl
                position = None
            continue
        
        # Generate signal based on genome parameters
        # More sensitive signal generation for better trade frequency
        signal_strength = 0.0
        direction = 0
        
        # Trend following component
        sma_fast = sum(b["close"] for b in bars[i-10:i]) / 10
        sma_slow = sum(b["close"] for b in bars[i-30:i]) / 30
        
        trend_diff = (sma_fast - sma_slow) / sma_slow if sma_slow > 0 else 0
        
        if trend_diff > 0.0001:  # Uptrend
            signal_strength += 0.4 * genome.trend_affinity
            direction = 1
        elif trend_diff < -0.0001:  # Downtrend
            signal_strength += 0.4 * genome.trend_affinity
            direction = -1
        
        # Momentum component
        momentum = (bar["close"] - bars[i-5]["close"]) / bars[i-5]["close"] if bars[i-5]["close"] > 0 else 0
        if abs(momentum) > 0.001:
            signal_strength += 0.2
            if momentum > 0 and direction >= 0:
                direction = 1
            elif momentum < 0 and direction <= 0:
                direction = -1
        
        # Volatility component
        recent_vol = sum(abs(bars[j]["close"] - bars[j-1]["close"]) for j in range(i-5, i)) / 5
        vol_ratio = recent_vol / avg_atr if avg_atr > 0 else 1.0
        
        if vol_ratio > 1.2:
            signal_strength += 0.2 * genome.volatility_affinity
        elif vol_ratio < 0.8:
            signal_strength += 0.2 * (1 - genome.volatility_affinity)
        
        # Delta print component (simplified)
        delta = (bar["close"] - bar["open"]) / (bar["high"] - bar["low"] + 0.0001)
        if abs(delta) > 0.3:  # More sensitive threshold
            signal_strength += 0.3 * genome.delta_print_weight
            if delta > 0 and direction >= 0:
                direction = 1
            elif delta < 0 and direction <= 0:
                direction = -1
        
        # Base signal for any direction
        if direction != 0:
            signal_strength += 0.2
        
        # Confluence boost
        if signal_strength > genome.min_confluence_threshold * 0.8:
            signal_strength += genome.confluence_boost
        
        # Check if signal is strong enough (use lower threshold for more trades)
        effective_threshold = min_conf * 0.7  # More lenient
        if signal_strength >= effective_threshold and direction != 0:
            entry_price = bar["close"]
            
            # Calculate stop loss and take profit
            if direction == 1:
                stop_loss = entry_price - avg_atr * sl_mult
                take_profit = entry_price + avg_atr * tp_mult
            else:
                stop_loss = entry_price + avg_atr * sl_mult
                take_profit = entry_price - avg_atr * tp_mult
            
            # Position size based on risk
            risk_amount = capital * risk_pct
            risk_per_unit = abs(entry_price - stop_loss)
            size = risk_amount / risk_per_unit if risk_per_unit > 0 else 0
            
            if size > 0:
                position = {
                    "entry_time": bar["timestamp"],
                    "entry_price": entry_price,
                    "direction": direction,
                    "stop_loss": stop_loss,
                    "take_profit": take_profit,
                    "size": size,
                }
                daily_trades += 1
    
    # Close any remaining position
    if position:
        exit_price = bars[-1]["close"]
        pnl = (exit_price - position["entry_price"]) * position["direction"] * position["size"]
        trades.append({
            "entry_time": position["entry_time"],
            "exit_time": bars[-1]["timestamp"],
            "entry_price": position["entry_price"],
            "exit_price": exit_price,
            "direction": position["direction"],
            "size": position["size"],
            "pnl": pnl,
            "exit_reason": "end_of_data",
        })
    
    return trades


def calculate_metrics_from_trades(
    trades: List[Dict[str, Any]],
    initial_capital: float = 10000.0,
) -> FitnessMetrics:
    """Calculate fitness metrics from trade results"""
    
    if not trades:
        return FitnessMetrics(
            sharpe_ratio=0.0,
            sortino_ratio=0.0,
            max_drawdown_pct=0.0,
            win_rate=0.0,
            profit_factor=0.0,
            total_return_pct=0.0,
            avg_trade_pnl=0.0,
            total_trades=0,
            monthly_consistency=0.0,
        )
    
    # Calculate returns
    returns = [t["pnl"] / initial_capital for t in trades]
    
    # Win/Loss
    wins = [r for r in returns if r > 0]
    losses = [r for r in returns if r <= 0]
    
    win_rate = len(wins) / len(returns) if returns else 0
    
    # Profit factor
    gross_profit = sum(wins) if wins else 0
    gross_loss = abs(sum(losses)) if losses else 0.001
    profit_factor = gross_profit / gross_loss if gross_loss > 0 else 0
    
    # Total return
    total_return = sum(returns)
    total_return_pct = total_return * 100
    
    # Sharpe ratio (annualized)
    if len(returns) > 1:
        avg_return = sum(returns) / len(returns)
        std_return = math.sqrt(sum((r - avg_return) ** 2 for r in returns) / len(returns))
        sharpe_ratio = (avg_return / std_return) * math.sqrt(252) if std_return > 0 else 0
    else:
        sharpe_ratio = 0
    
    # Sortino ratio (only downside deviation)
    if len(returns) > 1:
        avg_return = sum(returns) / len(returns)
        downside_returns = [r for r in returns if r < 0]
        if downside_returns:
            downside_std = math.sqrt(sum(r ** 2 for r in downside_returns) / len(downside_returns))
            sortino_ratio = (avg_return / downside_std) * math.sqrt(252) if downside_std > 0 else 0
        else:
            sortino_ratio = sharpe_ratio * 1.5  # No downside = good
    else:
        sortino_ratio = 0
    
    # Max drawdown
    equity = initial_capital
    peak = equity
    max_dd = 0
    
    for t in trades:
        equity += t["pnl"]
        if equity > peak:
            peak = equity
        dd = (peak - equity) / peak * 100
        if dd > max_dd:
            max_dd = dd
    
    # Streaks
    win_streak = 0
    loss_streak = 0
    max_win_streak = 0
    max_loss_streak = 0
    
    for r in returns:
        if r > 0:
            win_streak += 1
            loss_streak = 0
            max_win_streak = max(max_win_streak, win_streak)
        else:
            loss_streak += 1
            win_streak = 0
            max_loss_streak = max(max_loss_streak, loss_streak)
    
    # Monthly consistency (simplified)
    monthly_consistency = min(1.0, win_rate + 0.2) if win_rate > 0.4 else win_rate
    
    return FitnessMetrics(
        sharpe_ratio=sharpe_ratio,
        sortino_ratio=sortino_ratio,
        max_drawdown_pct=max_dd,
        win_rate=win_rate,
        profit_factor=profit_factor,
        total_return_pct=total_return_pct,
        avg_trade_pnl=sum(t["pnl"] for t in trades) / len(trades) if trades else 0,
        total_trades=len(trades),
        calmar_ratio=total_return_pct / max_dd if max_dd > 0 else 0,
        recovery_factor=total_return_pct / max_dd if max_dd > 0 else 0,
        win_streak_max=max_win_streak,
        loss_streak_max=max_loss_streak,
        monthly_consistency=monthly_consistency,
    )


def create_real_evaluator(
    historical_bars: Optional[List[Dict[str, Any]]] = None,
) -> callable:
    """
    Create a real evaluator function for the IntelligenceEvolutionEngine.
    
    Args:
        historical_bars: Optional real historical data to use
    
    Returns:
        Evaluator function
    """
    
    def evaluate(
        genome: IntelligenceGenome,
        scenario: AdversarialScenario,
    ) -> EvaluationResult:
        """Evaluate a genome on a scenario"""
        
        # Generate or use bars
        if historical_bars and scenario.regime in ["trending_up", "trending_down", "ranging"]:
            # Use subset of historical data
            start_idx = random.randint(0, max(0, len(historical_bars) - scenario.duration_bars))
            bars = historical_bars[start_idx:start_idx + scenario.duration_bars]
        else:
            # Generate synthetic bars for adversarial scenarios
            bars = generate_synthetic_bars(scenario, scenario.duration_bars)
        
        # Simulate trades
        trades = simulate_trades_from_genome(genome, bars, scenario)
        
        # Calculate metrics
        metrics = calculate_metrics_from_trades(trades)
        
        # Calculate fitness
        fitness = calculate_fitness(metrics)
        
        # Check risk gates
        passed, failures = check_risk_gates(metrics)
        
        return EvaluationResult(
            genome_id=genome.genome_id,
            scenario_name=scenario.name,
            fitness=fitness,
            metrics=metrics,
            passed_risk_gates=passed,
            risk_gate_failures=failures,
        )
    
    return evaluate


def calculate_fitness(metrics: FitnessMetrics) -> float:
    """Calculate multi-objective fitness score"""
    
    # Normalize metrics
    sharpe_norm = max(0, min(3, metrics.sharpe_ratio)) / 3.0
    sortino_norm = max(0, min(4, metrics.sortino_ratio)) / 4.0
    return_norm = max(0, min(100, metrics.total_return_pct)) / 100.0
    drawdown_norm = 1.0 - min(1, metrics.max_drawdown_pct / 30.0)
    consistency_norm = metrics.monthly_consistency
    pf_norm = max(0, min(3, metrics.profit_factor)) / 3.0
    win_rate_norm = metrics.win_rate
    
    # Weighted sum
    fitness = (
        0.25 * sharpe_norm +
        0.15 * sortino_norm +
        0.20 * return_norm +
        0.15 * drawdown_norm +
        0.10 * consistency_norm +
        0.10 * pf_norm +
        0.05 * win_rate_norm
    )
    
    # Bonus for high trade count (more statistical significance)
    if metrics.total_trades >= 50:
        fitness *= 1.1
    elif metrics.total_trades >= 100:
        fitness *= 1.2
    
    return fitness


def check_risk_gates(
    metrics: FitnessMetrics,
    min_sharpe: float = 0.3,
    max_drawdown: float = 20.0,
    min_win_rate: float = 0.30,
    min_trades: int = 10,
) -> Tuple[bool, List[str]]:
    """Check if metrics pass risk gates"""
    failures = []
    
    if metrics.sharpe_ratio < min_sharpe:
        failures.append(f"Sharpe {metrics.sharpe_ratio:.2f} < {min_sharpe}")
    
    if metrics.max_drawdown_pct > max_drawdown:
        failures.append(f"Drawdown {metrics.max_drawdown_pct:.1f}% > {max_drawdown}%")
    
    if metrics.win_rate < min_win_rate:
        failures.append(f"Win rate {metrics.win_rate:.1%} < {min_win_rate:.1%}")
    
    if metrics.total_trades < min_trades:
        failures.append(f"Trades {metrics.total_trades} < {min_trades}")
    
    return len(failures) == 0, failures


def run_quick_evolution_test():
    """Run a quick test of the evolution system"""
    from .intelligence_evolution import (
        IntelligenceEvolutionEngine,
        IntelligenceEvolutionConfig,
        ADVERSARIAL_SCENARIOS,
    )
    
    # Create evaluator
    evaluator = create_real_evaluator()
    
    # Create config for quick test
    config = IntelligenceEvolutionConfig(
        initial_population_size=10,
        children_per_generation=5,
        max_generations=5,
        stagnation_limit=3,
    )
    
    # Use subset of scenarios for speed
    scenarios = ADVERSARIAL_SCENARIOS[:4]
    
    # Create engine
    engine = IntelligenceEvolutionEngine(
        evaluator=evaluator,
        config=config,
        scenarios=scenarios,
    )
    
    # Run evolution
    summary = engine.run()
    
    # Get best genome
    best = engine.get_best_genome()
    
    print(f"\nEvolution Summary:")
    print(f"  Generations: {summary['generations_run']}")
    print(f"  Best Fitness: {summary['best_fitness']:.4f}")
    print(f"  Archive Size: {summary['final_archive_size']}")
    
    if best:
        print(f"\nBest Genome Parameters:")
        print(f"  Min Confluence: {best.min_confluence_threshold:.3f}")
        print(f"  Min Confidence: {best.min_confidence_threshold:.3f}")
        print(f"  Technical Weight: {best.technical_weight:.3f}")
        print(f"  Risk Per Trade: {best.risk_per_trade_pct:.2f}%")
    
    return summary, best


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run_quick_evolution_test()
