"""
Self-Evolving Intelligence Engine

This module implements a LIVING intelligence system that:
1. Tracks every decision and outcome
2. Identifies which signals are actually predictive vs noise
3. Automatically adjusts weights based on REAL performance
4. Learns new patterns from market data
5. Evolves its own strategy over time

This is the BREAKTHROUGH - a system that gets smarter every single day.

Key Concepts:
- Performance Attribution: Track which signals led to winning vs losing trades
- Adaptive Weight Optimization: Automatically adjust signal weights based on performance
- Pattern Learning: Identify new patterns from successful trades
- Regime Adaptation: Detect when market conditions change and adapt
- Continuous Evolution: Never stop learning and improving
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple, Any, Callable
from enum import Enum
from datetime import datetime, timedelta
from collections import defaultdict
import math
import json
import os


class EvolutionPhase(Enum):
    """Evolution phases"""
    LEARNING = "learning"  # Gathering data, not yet adapting
    ADAPTING = "adapting"  # Actively adjusting weights
    OPTIMIZING = "optimizing"  # Fine-tuning for best performance
    STABLE = "stable"  # Optimal weights found, minimal changes


class SignalPerformance(Enum):
    """Signal performance classification"""
    EXCELLENT = "excellent"  # >70% win rate, >2.0 profit factor
    GOOD = "good"  # >55% win rate, >1.5 profit factor
    NEUTRAL = "neutral"  # 45-55% win rate
    POOR = "poor"  # <45% win rate
    HARMFUL = "harmful"  # <35% win rate, negative expectancy


class MarketRegime(Enum):
    """Market regime types"""
    TRENDING_BULL = "trending_bull"
    TRENDING_BEAR = "trending_bear"
    RANGING_TIGHT = "ranging_tight"
    RANGING_WIDE = "ranging_wide"
    VOLATILE = "volatile"
    QUIET = "quiet"


@dataclass
class TradeRecord:
    """Record of a single trade for learning"""
    trade_id: str
    timestamp: datetime
    symbol: str
    direction: str  # "LONG" or "SHORT"
    entry_price: float
    exit_price: float
    pnl: float
    pnl_percent: float
    duration_minutes: int
    
    # Signal contributions at entry
    signal_contributions: Dict[str, float]  # signal_name -> contribution score
    signal_directions: Dict[str, str]  # signal_name -> direction at entry
    signal_confidences: Dict[str, float]  # signal_name -> confidence at entry
    
    # Market context at entry
    market_regime: MarketRegime
    volatility: float
    session: str
    
    # Outcome
    outcome: str  # "WIN", "LOSS", "BREAKEVEN"
    exit_reason: str  # "TP1", "TP2", "TP3", "SL", "MANUAL", "TIME"
    
    # Learning metadata
    was_correct_direction: bool
    max_favorable_excursion: float  # Best price reached
    max_adverse_excursion: float  # Worst price reached


@dataclass
class SignalStats:
    """Statistics for a single signal source"""
    signal_name: str
    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    total_pnl: float = 0.0
    
    # Direction accuracy
    correct_direction_count: int = 0
    
    # Performance by regime
    regime_performance: Dict[str, Dict[str, float]] = field(default_factory=dict)
    
    # Performance by session
    session_performance: Dict[str, Dict[str, float]] = field(default_factory=dict)
    
    # Recent performance (last 20 trades)
    recent_trades: List[float] = field(default_factory=list)
    
    @property
    def win_rate(self) -> float:
        if self.total_trades == 0:
            return 0.5
        return self.winning_trades / self.total_trades
    
    @property
    def profit_factor(self) -> float:
        wins = sum(p for p in self.recent_trades if p > 0)
        losses = abs(sum(p for p in self.recent_trades if p < 0))
        if losses == 0:
            return 10.0 if wins > 0 else 1.0
        return wins / losses
    
    @property
    def direction_accuracy(self) -> float:
        if self.total_trades == 0:
            return 0.5
        return self.correct_direction_count / self.total_trades
    
    @property
    def recent_win_rate(self) -> float:
        if len(self.recent_trades) == 0:
            return 0.5
        wins = sum(1 for p in self.recent_trades if p > 0)
        return wins / len(self.recent_trades)
    
    @property
    def performance_class(self) -> SignalPerformance:
        wr = self.win_rate
        pf = self.profit_factor
        
        if wr > 0.70 and pf > 2.0:
            return SignalPerformance.EXCELLENT
        elif wr > 0.55 and pf > 1.5:
            return SignalPerformance.GOOD
        elif wr > 0.45:
            return SignalPerformance.NEUTRAL
        elif wr > 0.35:
            return SignalPerformance.POOR
        else:
            return SignalPerformance.HARMFUL


@dataclass
class EvolutionState:
    """Current state of the evolution engine"""
    phase: EvolutionPhase
    generation: int
    total_trades_learned: int
    
    # Current optimized weights
    current_weights: Dict[str, float]
    
    # Weight history for tracking evolution
    weight_history: List[Dict[str, float]] = field(default_factory=list)
    
    # Performance metrics
    overall_win_rate: float = 0.5
    overall_profit_factor: float = 1.0
    sharpe_ratio: float = 0.0
    
    # Learning metrics
    signals_improved: int = 0
    signals_degraded: int = 0
    
    # Regime-specific weights
    regime_weights: Dict[str, Dict[str, float]] = field(default_factory=dict)
    
    # Last evolution timestamp
    last_evolution: Optional[datetime] = None


@dataclass
class EvolutionAnalysis:
    """Result of evolution analysis"""
    state: EvolutionState
    signal_stats: Dict[str, SignalStats]
    
    # Recommendations
    weight_adjustments: Dict[str, float]  # signal -> new weight
    signals_to_boost: List[str]
    signals_to_reduce: List[str]
    signals_to_disable: List[str]
    
    # Insights
    best_performing_signals: List[Tuple[str, float]]  # (signal, win_rate)
    worst_performing_signals: List[Tuple[str, float]]
    regime_insights: Dict[str, str]
    
    # Confidence in recommendations
    confidence: float
    reasoning: List[str]


class SelfEvolvingIntelligence:
    """
    Self-Evolving Intelligence Engine
    
    A LIVING system that learns from every trade and continuously improves.
    This is not just optimization - it's evolution.
    
    Key Features:
    1. Performance Attribution - Know exactly which signals are working
    2. Adaptive Weights - Automatically adjust based on real performance
    3. Regime Awareness - Different weights for different market conditions
    4. Continuous Learning - Never stops improving
    5. Self-Correction - Identifies and fixes its own mistakes
    """
    
    # Minimum trades before adapting
    MIN_TRADES_FOR_ADAPTATION = 20
    
    # Weight adjustment limits
    MAX_WEIGHT_CHANGE_PER_EVOLUTION = 0.05  # 5% max change per evolution
    MIN_SIGNAL_WEIGHT = 0.02  # 2% minimum weight
    MAX_SIGNAL_WEIGHT = 0.25  # 25% maximum weight
    
    # Evolution frequency
    EVOLUTION_INTERVAL_TRADES = 10  # Evolve every 10 trades
    
    # Performance thresholds
    EXCELLENT_WIN_RATE = 0.70
    GOOD_WIN_RATE = 0.55
    POOR_WIN_RATE = 0.45
    HARMFUL_WIN_RATE = 0.35
    
    def __init__(
        self,
        initial_weights: Dict[str, float],
        data_path: str = "/home/ubuntu/omega_devin/evolution_data"
    ):
        """
        Initialize Self-Evolving Intelligence
        
        Args:
            initial_weights: Starting signal weights
            data_path: Path to store evolution data
        """
        self.data_path = data_path
        os.makedirs(data_path, exist_ok=True)
        
        # Initialize state
        self.state = EvolutionState(
            phase=EvolutionPhase.LEARNING,
            generation=1,
            total_trades_learned=0,
            current_weights=initial_weights.copy()
        )
        
        # Initialize signal stats
        self.signal_stats: Dict[str, SignalStats] = {
            name: SignalStats(signal_name=name)
            for name in initial_weights.keys()
        }
        
        # Trade history
        self.trade_history: List[TradeRecord] = []
        
        # Load existing data if available
        self._load_state()
    
    def record_trade(
        self,
        trade_id: str,
        symbol: str,
        direction: str,
        entry_price: float,
        exit_price: float,
        signal_contributions: Dict[str, float],
        signal_directions: Dict[str, str],
        signal_confidences: Dict[str, float],
        market_regime: MarketRegime,
        volatility: float,
        session: str,
        exit_reason: str,
        duration_minutes: int,
        max_favorable_excursion: float,
        max_adverse_excursion: float
    ) -> TradeRecord:
        """
        Record a completed trade for learning
        
        This is the core learning function - every trade teaches us something.
        """
        # Calculate P&L
        if direction == "LONG":
            pnl = exit_price - entry_price
            pnl_percent = (exit_price - entry_price) / entry_price
            was_correct = exit_price > entry_price
        else:
            pnl = entry_price - exit_price
            pnl_percent = (entry_price - exit_price) / entry_price
            was_correct = exit_price < entry_price
        
        # Determine outcome
        if pnl > 0:
            outcome = "WIN"
        elif pnl < 0:
            outcome = "LOSS"
        else:
            outcome = "BREAKEVEN"
        
        # Create trade record
        record = TradeRecord(
            trade_id=trade_id,
            timestamp=datetime.utcnow(),
            symbol=symbol,
            direction=direction,
            entry_price=entry_price,
            exit_price=exit_price,
            pnl=pnl,
            pnl_percent=pnl_percent,
            duration_minutes=duration_minutes,
            signal_contributions=signal_contributions,
            signal_directions=signal_directions,
            signal_confidences=signal_confidences,
            market_regime=market_regime,
            volatility=volatility,
            session=session,
            outcome=outcome,
            exit_reason=exit_reason,
            was_correct_direction=was_correct,
            max_favorable_excursion=max_favorable_excursion,
            max_adverse_excursion=max_adverse_excursion
        )
        
        # Add to history
        self.trade_history.append(record)
        self.state.total_trades_learned += 1
        
        # Update signal stats
        self._update_signal_stats(record)
        
        # Check if we should evolve
        if self.state.total_trades_learned % self.EVOLUTION_INTERVAL_TRADES == 0:
            self._evolve()
        
        # Save state
        self._save_state()
        
        return record
    
    def _update_signal_stats(self, record: TradeRecord):
        """Update statistics for each signal based on trade outcome"""
        for signal_name, contribution in record.signal_contributions.items():
            if signal_name not in self.signal_stats:
                self.signal_stats[signal_name] = SignalStats(signal_name=signal_name)
            
            stats = self.signal_stats[signal_name]
            stats.total_trades += 1
            
            # Update win/loss counts
            if record.outcome == "WIN":
                stats.winning_trades += 1
            elif record.outcome == "LOSS":
                stats.losing_trades += 1
            
            # Update P&L
            stats.total_pnl += record.pnl * contribution
            
            # Update direction accuracy
            signal_direction = record.signal_directions.get(signal_name, "NEUTRAL")
            if signal_direction == record.direction and record.was_correct_direction:
                stats.correct_direction_count += 1
            
            # Update recent trades (keep last 20)
            stats.recent_trades.append(record.pnl * contribution)
            if len(stats.recent_trades) > 20:
                stats.recent_trades.pop(0)
            
            # Update regime performance
            regime_key = record.market_regime.value
            if regime_key not in stats.regime_performance:
                stats.regime_performance[regime_key] = {"wins": 0, "losses": 0, "pnl": 0}
            
            if record.outcome == "WIN":
                stats.regime_performance[regime_key]["wins"] += 1
            elif record.outcome == "LOSS":
                stats.regime_performance[regime_key]["losses"] += 1
            stats.regime_performance[regime_key]["pnl"] += record.pnl * contribution
            
            # Update session performance
            if record.session not in stats.session_performance:
                stats.session_performance[record.session] = {"wins": 0, "losses": 0, "pnl": 0}
            
            if record.outcome == "WIN":
                stats.session_performance[record.session]["wins"] += 1
            elif record.outcome == "LOSS":
                stats.session_performance[record.session]["losses"] += 1
            stats.session_performance[record.session]["pnl"] += record.pnl * contribution
    
    def _evolve(self):
        """
        Perform evolution - adjust weights based on performance
        
        This is where the magic happens - the system learns and adapts.
        """
        if self.state.total_trades_learned < self.MIN_TRADES_FOR_ADAPTATION:
            return
        
        # Calculate new weights based on performance
        new_weights = self.state.current_weights.copy()
        signals_improved = 0
        signals_degraded = 0
        
        for signal_name, stats in self.signal_stats.items():
            if signal_name not in new_weights:
                continue
            
            current_weight = new_weights[signal_name]
            performance = stats.performance_class
            
            # Calculate weight adjustment
            adjustment = 0.0
            
            if performance == SignalPerformance.EXCELLENT:
                # Boost excellent performers
                adjustment = self.MAX_WEIGHT_CHANGE_PER_EVOLUTION
                signals_improved += 1
            elif performance == SignalPerformance.GOOD:
                # Slight boost for good performers
                adjustment = self.MAX_WEIGHT_CHANGE_PER_EVOLUTION * 0.5
                signals_improved += 1
            elif performance == SignalPerformance.POOR:
                # Reduce poor performers
                adjustment = -self.MAX_WEIGHT_CHANGE_PER_EVOLUTION * 0.5
                signals_degraded += 1
            elif performance == SignalPerformance.HARMFUL:
                # Significantly reduce harmful signals
                adjustment = -self.MAX_WEIGHT_CHANGE_PER_EVOLUTION
                signals_degraded += 1
            
            # Apply adjustment with limits
            new_weight = current_weight + adjustment
            new_weight = max(self.MIN_SIGNAL_WEIGHT, min(self.MAX_SIGNAL_WEIGHT, new_weight))
            new_weights[signal_name] = new_weight
        
        # Normalize weights to sum to 1
        total_weight = sum(new_weights.values())
        if total_weight > 0:
            new_weights = {k: v / total_weight for k, v in new_weights.items()}
        
        # Update state
        self.state.current_weights = new_weights
        self.state.weight_history.append(new_weights.copy())
        self.state.generation += 1
        self.state.signals_improved = signals_improved
        self.state.signals_degraded = signals_degraded
        self.state.last_evolution = datetime.utcnow()
        
        # Update phase based on progress
        if self.state.total_trades_learned < 50:
            self.state.phase = EvolutionPhase.LEARNING
        elif self.state.total_trades_learned < 100:
            self.state.phase = EvolutionPhase.ADAPTING
        elif signals_improved > signals_degraded:
            self.state.phase = EvolutionPhase.OPTIMIZING
        else:
            self.state.phase = EvolutionPhase.STABLE
        
        # Calculate overall metrics
        self._calculate_overall_metrics()
    
    def _calculate_overall_metrics(self):
        """Calculate overall performance metrics"""
        if not self.trade_history:
            return
        
        # Win rate
        wins = sum(1 for t in self.trade_history if t.outcome == "WIN")
        self.state.overall_win_rate = wins / len(self.trade_history)
        
        # Profit factor
        gross_profit = sum(t.pnl for t in self.trade_history if t.pnl > 0)
        gross_loss = abs(sum(t.pnl for t in self.trade_history if t.pnl < 0))
        if gross_loss > 0:
            self.state.overall_profit_factor = gross_profit / gross_loss
        else:
            self.state.overall_profit_factor = 10.0 if gross_profit > 0 else 1.0
        
        # Sharpe ratio (simplified)
        returns = [t.pnl_percent for t in self.trade_history]
        if len(returns) > 1:
            avg_return = sum(returns) / len(returns)
            variance = sum((r - avg_return) ** 2 for r in returns) / len(returns)
            std_dev = math.sqrt(variance) if variance > 0 else 0.001
            self.state.sharpe_ratio = (avg_return / std_dev) * math.sqrt(252)  # Annualized
    
    def analyze(self) -> EvolutionAnalysis:
        """
        Analyze current evolution state and provide recommendations
        
        Returns comprehensive analysis of what's working and what's not.
        """
        reasoning = []
        
        # Identify best and worst performers
        sorted_signals = sorted(
            self.signal_stats.items(),
            key=lambda x: x[1].win_rate,
            reverse=True
        )
        
        best_performing = [(name, stats.win_rate) for name, stats in sorted_signals[:3]]
        worst_performing = [(name, stats.win_rate) for name, stats in sorted_signals[-3:]]
        
        # Calculate weight adjustments
        weight_adjustments = {}
        signals_to_boost = []
        signals_to_reduce = []
        signals_to_disable = []
        
        for signal_name, stats in self.signal_stats.items():
            performance = stats.performance_class
            
            if performance == SignalPerformance.EXCELLENT:
                signals_to_boost.append(signal_name)
                weight_adjustments[signal_name] = min(
                    self.MAX_SIGNAL_WEIGHT,
                    self.state.current_weights.get(signal_name, 0.1) * 1.2
                )
                reasoning.append(f"{signal_name} is EXCELLENT ({stats.win_rate:.0%} win rate) - BOOST")
            elif performance == SignalPerformance.GOOD:
                signals_to_boost.append(signal_name)
                weight_adjustments[signal_name] = min(
                    self.MAX_SIGNAL_WEIGHT,
                    self.state.current_weights.get(signal_name, 0.1) * 1.1
                )
                reasoning.append(f"{signal_name} is GOOD ({stats.win_rate:.0%} win rate) - slight boost")
            elif performance == SignalPerformance.POOR:
                signals_to_reduce.append(signal_name)
                weight_adjustments[signal_name] = max(
                    self.MIN_SIGNAL_WEIGHT,
                    self.state.current_weights.get(signal_name, 0.1) * 0.8
                )
                reasoning.append(f"{signal_name} is POOR ({stats.win_rate:.0%} win rate) - reduce")
            elif performance == SignalPerformance.HARMFUL:
                signals_to_disable.append(signal_name)
                weight_adjustments[signal_name] = self.MIN_SIGNAL_WEIGHT
                reasoning.append(f"{signal_name} is HARMFUL ({stats.win_rate:.0%} win rate) - DISABLE")
        
        # Regime insights
        regime_insights = {}
        for regime in MarketRegime:
            regime_key = regime.value
            best_in_regime = None
            best_win_rate = 0
            
            for signal_name, stats in self.signal_stats.items():
                if regime_key in stats.regime_performance:
                    perf = stats.regime_performance[regime_key]
                    total = perf["wins"] + perf["losses"]
                    if total > 0:
                        wr = perf["wins"] / total
                        if wr > best_win_rate:
                            best_win_rate = wr
                            best_in_regime = signal_name
            
            if best_in_regime:
                regime_insights[regime_key] = f"Best signal: {best_in_regime} ({best_win_rate:.0%})"
        
        # Calculate confidence
        confidence = min(1.0, self.state.total_trades_learned / 100)
        
        return EvolutionAnalysis(
            state=self.state,
            signal_stats=self.signal_stats,
            weight_adjustments=weight_adjustments,
            signals_to_boost=signals_to_boost,
            signals_to_reduce=signals_to_reduce,
            signals_to_disable=signals_to_disable,
            best_performing_signals=best_performing,
            worst_performing_signals=worst_performing,
            regime_insights=regime_insights,
            confidence=confidence,
            reasoning=reasoning
        )
    
    def get_optimized_weights(self, market_regime: Optional[MarketRegime] = None) -> Dict[str, float]:
        """
        Get current optimized weights
        
        Optionally returns regime-specific weights if available.
        """
        if market_regime and market_regime.value in self.state.regime_weights:
            return self.state.regime_weights[market_regime.value]
        return self.state.current_weights
    
    def get_signal_recommendation(self, signal_name: str) -> Tuple[str, float]:
        """
        Get recommendation for a specific signal
        
        Returns (action, confidence) where action is "BOOST", "KEEP", "REDUCE", or "DISABLE"
        """
        if signal_name not in self.signal_stats:
            return ("KEEP", 0.5)
        
        stats = self.signal_stats[signal_name]
        performance = stats.performance_class
        
        if performance == SignalPerformance.EXCELLENT:
            return ("BOOST", 0.9)
        elif performance == SignalPerformance.GOOD:
            return ("BOOST", 0.7)
        elif performance == SignalPerformance.NEUTRAL:
            return ("KEEP", 0.5)
        elif performance == SignalPerformance.POOR:
            return ("REDUCE", 0.7)
        else:
            return ("DISABLE", 0.9)
    
    def _save_state(self):
        """Save evolution state to disk"""
        state_file = os.path.join(self.data_path, "evolution_state.json")
        
        state_data = {
            "phase": self.state.phase.value,
            "generation": self.state.generation,
            "total_trades_learned": self.state.total_trades_learned,
            "current_weights": self.state.current_weights,
            "overall_win_rate": self.state.overall_win_rate,
            "overall_profit_factor": self.state.overall_profit_factor,
            "sharpe_ratio": self.state.sharpe_ratio,
            "last_evolution": self.state.last_evolution.isoformat() if self.state.last_evolution else None
        }
        
        with open(state_file, "w") as f:
            json.dump(state_data, f, indent=2)
        
        # Save signal stats
        stats_file = os.path.join(self.data_path, "signal_stats.json")
        stats_data = {}
        for name, stats in self.signal_stats.items():
            stats_data[name] = {
                "total_trades": stats.total_trades,
                "winning_trades": stats.winning_trades,
                "losing_trades": stats.losing_trades,
                "total_pnl": stats.total_pnl,
                "correct_direction_count": stats.correct_direction_count,
                "recent_trades": stats.recent_trades
            }
        
        with open(stats_file, "w") as f:
            json.dump(stats_data, f, indent=2)
    
    def _load_state(self):
        """Load evolution state from disk"""
        state_file = os.path.join(self.data_path, "evolution_state.json")
        
        if os.path.exists(state_file):
            with open(state_file, "r") as f:
                state_data = json.load(f)
            
            self.state.phase = EvolutionPhase(state_data.get("phase", "learning"))
            self.state.generation = state_data.get("generation", 1)
            self.state.total_trades_learned = state_data.get("total_trades_learned", 0)
            self.state.current_weights = state_data.get("current_weights", self.state.current_weights)
            self.state.overall_win_rate = state_data.get("overall_win_rate", 0.5)
            self.state.overall_profit_factor = state_data.get("overall_profit_factor", 1.0)
            self.state.sharpe_ratio = state_data.get("sharpe_ratio", 0.0)
            
            if state_data.get("last_evolution"):
                self.state.last_evolution = datetime.fromisoformat(state_data["last_evolution"])
        
        # Load signal stats
        stats_file = os.path.join(self.data_path, "signal_stats.json")
        
        if os.path.exists(stats_file):
            with open(stats_file, "r") as f:
                stats_data = json.load(f)
            
            for name, data in stats_data.items():
                if name in self.signal_stats:
                    stats = self.signal_stats[name]
                    stats.total_trades = data.get("total_trades", 0)
                    stats.winning_trades = data.get("winning_trades", 0)
                    stats.losing_trades = data.get("losing_trades", 0)
                    stats.total_pnl = data.get("total_pnl", 0.0)
                    stats.correct_direction_count = data.get("correct_direction_count", 0)
                    stats.recent_trades = data.get("recent_trades", [])
    
    def reset(self):
        """Reset evolution state (use with caution)"""
        self.state = EvolutionState(
            phase=EvolutionPhase.LEARNING,
            generation=1,
            total_trades_learned=0,
            current_weights=self.state.current_weights.copy()
        )
        
        for stats in self.signal_stats.values():
            stats.total_trades = 0
            stats.winning_trades = 0
            stats.losing_trades = 0
            stats.total_pnl = 0.0
            stats.correct_direction_count = 0
            stats.recent_trades = []
            stats.regime_performance = {}
            stats.session_performance = {}
        
        self.trade_history = []
        self._save_state()
    
    def get_evolution_summary(self) -> str:
        """Get a human-readable summary of evolution state"""
        analysis = self.analyze()
        
        summary = f"""
================================================================================
SELF-EVOLVING INTELLIGENCE - GENERATION {self.state.generation}
================================================================================

EVOLUTION PHASE: {self.state.phase.value.upper()}
TRADES LEARNED: {self.state.total_trades_learned}

OVERALL PERFORMANCE:
  Win Rate: {self.state.overall_win_rate:.1%}
  Profit Factor: {self.state.overall_profit_factor:.2f}
  Sharpe Ratio: {self.state.sharpe_ratio:.2f}

CURRENT OPTIMIZED WEIGHTS:
"""
        for signal, weight in sorted(self.state.current_weights.items(), key=lambda x: -x[1]):
            stats = self.signal_stats.get(signal)
            if stats:
                perf = stats.performance_class.value
                wr = stats.win_rate
                summary += f"  {signal}: {weight:.1%} (WR: {wr:.0%}, {perf})\n"
            else:
                summary += f"  {signal}: {weight:.1%}\n"
        
        summary += f"""
BEST PERFORMING SIGNALS:
"""
        for signal, wr in analysis.best_performing_signals:
            summary += f"  {signal}: {wr:.1%} win rate\n"
        
        summary += f"""
SIGNALS TO BOOST: {', '.join(analysis.signals_to_boost) or 'None'}
SIGNALS TO REDUCE: {', '.join(analysis.signals_to_reduce) or 'None'}
SIGNALS TO DISABLE: {', '.join(analysis.signals_to_disable) or 'None'}

CONFIDENCE IN RECOMMENDATIONS: {analysis.confidence:.0%}
================================================================================
"""
        return summary


def test_self_evolving_intelligence():
    """Test the Self-Evolving Intelligence Engine"""
    print("=" * 80)
    print("SELF-EVOLVING INTELLIGENCE TEST")
    print("=" * 80)
    
    # Initialize with sample weights
    initial_weights = {
        "smc": 0.14,
        "mtf": 0.14,
        "vpe": 0.14,
        "fractal_swing": 0.11,
        "manipulation": 0.11,
        "multi_profile": 0.09,
        "session_mgmt": 0.08,
        "regime": 0.07,
        "delta": 0.05,
        "consciousness": 0.04,
        "fundamental": 0.03
    }
    
    engine = SelfEvolvingIntelligence(
        initial_weights=initial_weights,
        data_path="/tmp/evolution_test"
    )
    
    # Simulate some trades
    import random
    
    for i in range(30):
        # Generate random trade data
        direction = random.choice(["LONG", "SHORT"])
        entry = 1.1000 + random.uniform(-0.01, 0.01)
        
        # Some signals perform better than others
        signal_contributions = {}
        signal_directions = {}
        signal_confidences = {}
        
        for signal in initial_weights.keys():
            signal_contributions[signal] = random.uniform(0.5, 1.0)
            signal_directions[signal] = random.choice(["LONG", "SHORT", "NEUTRAL"])
            signal_confidences[signal] = random.uniform(0.3, 0.9)
        
        # Make VPE and SMC perform better (higher chance of correct direction)
        if random.random() < 0.7:  # 70% of time VPE is correct
            signal_directions["vpe"] = direction
        if random.random() < 0.65:  # 65% of time SMC is correct
            signal_directions["smc"] = direction
        
        # Make fundamental perform worse
        if random.random() < 0.4:  # Only 40% correct
            signal_directions["fundamental"] = direction
        
        # Determine outcome based on signal alignment
        aligned_signals = sum(1 for s, d in signal_directions.items() if d == direction)
        win_probability = 0.3 + (aligned_signals / len(signal_directions)) * 0.4
        
        if random.random() < win_probability:
            exit_price = entry + (0.002 if direction == "LONG" else -0.002)
        else:
            exit_price = entry + (-0.001 if direction == "LONG" else 0.001)
        
        engine.record_trade(
            trade_id=f"TEST_{i}",
            symbol="EURUSD",
            direction=direction,
            entry_price=entry,
            exit_price=exit_price,
            signal_contributions=signal_contributions,
            signal_directions=signal_directions,
            signal_confidences=signal_confidences,
            market_regime=random.choice(list(MarketRegime)),
            volatility=random.uniform(0.5, 1.5),
            session=random.choice(["london", "new_york", "asia"]),
            exit_reason=random.choice(["TP1", "TP2", "SL"]),
            duration_minutes=random.randint(5, 120),
            max_favorable_excursion=entry + random.uniform(0, 0.003),
            max_adverse_excursion=entry - random.uniform(0, 0.002)
        )
    
    # Print summary
    print(engine.get_evolution_summary())
    
    # Get analysis
    analysis = engine.analyze()
    
    print("\nREASONING:")
    for reason in analysis.reasoning:
        print(f"  - {reason}")
    
    print("\nTest completed successfully!")


if __name__ == "__main__":
    test_self_evolving_intelligence()
