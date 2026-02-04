"""
Scorer - Deterministic scoring for strategy evaluation

Produces a single fitness score from backtest results.
Used by the DRQ loop to compare strategies.
"""

from dataclasses import dataclass
from typing import Dict, Any, Optional
import logging

from .metrics import TradeMetrics, PerformanceMetrics
from .backtest import BacktestResult


logger = logging.getLogger(__name__)


@dataclass
class ScoreCard:
    """
    Complete scorecard for a strategy evaluation.
    
    Contains the fitness score and all component scores.
    """
    # Final fitness (weighted combination)
    fitness: float = 0.0
    
    # Component scores (0-1 scale)
    return_score: float = 0.0
    risk_score: float = 0.0
    consistency_score: float = 0.0
    efficiency_score: float = 0.0
    
    # Risk gate results
    passed_risk_gates: bool = True
    risk_gate_failures: list = None
    
    # Raw metrics used
    sharpe_ratio: float = 0.0
    max_drawdown_pct: float = 0.0
    win_rate: float = 0.0
    profit_factor: float = 0.0
    total_return_pct: float = 0.0
    no_trade_rate: float = 0.0
    
    def __post_init__(self):
        if self.risk_gate_failures is None:
            self.risk_gate_failures = []
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "fitness": round(self.fitness, 4),
            "component_scores": {
                "return": round(self.return_score, 4),
                "risk": round(self.risk_score, 4),
                "consistency": round(self.consistency_score, 4),
                "efficiency": round(self.efficiency_score, 4)
            },
            "passed_risk_gates": self.passed_risk_gates,
            "risk_gate_failures": self.risk_gate_failures,
            "raw_metrics": {
                "sharpe_ratio": round(self.sharpe_ratio, 3),
                "max_drawdown_pct": round(self.max_drawdown_pct, 2),
                "win_rate": round(self.win_rate, 4),
                "profit_factor": round(self.profit_factor, 2),
                "total_return_pct": round(self.total_return_pct, 2),
                "no_trade_rate": round(self.no_trade_rate, 4)
            }
        }


@dataclass
class ScorerConfig:
    """Configuration for the scorer"""
    
    # Component weights (must sum to 1.0)
    weight_return: float = 0.3
    weight_risk: float = 0.3
    weight_consistency: float = 0.25
    weight_efficiency: float = 0.15
    
    # Risk gates (hard limits)
    min_sharpe_ratio: float = 0.3
    max_drawdown_pct: float = 20.0
    min_win_rate: float = 0.30
    min_trades: int = 10
    max_no_trade_rate: float = 0.99  # Must take some trades
    
    # Scaling parameters for score normalization
    sharpe_scale: float = 2.0  # Sharpe of 2.0 = score of 1.0
    return_scale: float = 50.0  # 50% return = score of 1.0
    drawdown_scale: float = 20.0  # 20% DD = score of 0.0
    profit_factor_scale: float = 3.0  # PF of 3.0 = score of 1.0


class Scorer:
    """
    Score strategies based on backtest results.
    
    Produces a single fitness value that balances:
    - Returns (total and risk-adjusted)
    - Risk (drawdown, volatility)
    - Consistency (win rate, profit factor)
    - Efficiency (time in market, trade frequency)
    """
    
    def __init__(self, config: Optional[ScorerConfig] = None):
        self.config = config or ScorerConfig()
    
    def score(self, result: BacktestResult) -> ScoreCard:
        """
        Score a backtest result.
        
        Returns a ScoreCard with fitness and component scores.
        """
        card = ScoreCard()
        
        # Extract metrics
        tm = result.trade_metrics
        pm = result.performance_metrics
        
        card.sharpe_ratio = pm.sharpe_ratio
        card.max_drawdown_pct = pm.max_drawdown_pct
        card.win_rate = tm.win_rate
        card.profit_factor = tm.profit_factor
        card.total_return_pct = pm.total_return_pct
        card.no_trade_rate = pm.no_trade_rate
        
        # Check risk gates first
        card.passed_risk_gates = True
        card.risk_gate_failures = []
        
        if tm.total_trades < self.config.min_trades:
            card.passed_risk_gates = False
            card.risk_gate_failures.append(
                f"min_trades: {tm.total_trades} < {self.config.min_trades}"
            )
        
        if pm.sharpe_ratio < self.config.min_sharpe_ratio:
            card.passed_risk_gates = False
            card.risk_gate_failures.append(
                f"min_sharpe: {pm.sharpe_ratio:.2f} < {self.config.min_sharpe_ratio}"
            )
        
        if pm.max_drawdown_pct > self.config.max_drawdown_pct:
            card.passed_risk_gates = False
            card.risk_gate_failures.append(
                f"max_drawdown: {pm.max_drawdown_pct:.1f}% > {self.config.max_drawdown_pct}%"
            )
        
        if tm.win_rate < self.config.min_win_rate:
            card.passed_risk_gates = False
            card.risk_gate_failures.append(
                f"min_win_rate: {tm.win_rate:.2f} < {self.config.min_win_rate}"
            )
        
        if pm.no_trade_rate > self.config.max_no_trade_rate:
            card.passed_risk_gates = False
            card.risk_gate_failures.append(
                f"max_no_trade_rate: {pm.no_trade_rate:.2f} > {self.config.max_no_trade_rate}"
            )
        
        # If risk gates failed, return low fitness
        if not card.passed_risk_gates:
            card.fitness = -1.0
            logger.debug(f"Risk gates failed: {card.risk_gate_failures}")
            return card
        
        # Compute component scores
        card.return_score = self._score_returns(pm)
        card.risk_score = self._score_risk(pm)
        card.consistency_score = self._score_consistency(tm)
        card.efficiency_score = self._score_efficiency(pm, tm)
        
        # Weighted combination
        card.fitness = (
            self.config.weight_return * card.return_score +
            self.config.weight_risk * card.risk_score +
            self.config.weight_consistency * card.consistency_score +
            self.config.weight_efficiency * card.efficiency_score
        )
        
        logger.debug(
            f"Scored: fitness={card.fitness:.4f}, "
            f"return={card.return_score:.2f}, risk={card.risk_score:.2f}, "
            f"consistency={card.consistency_score:.2f}, efficiency={card.efficiency_score:.2f}"
        )
        
        return card
    
    def _score_returns(self, pm: PerformanceMetrics) -> float:
        """Score based on returns"""
        # Combine total return and Sharpe ratio
        
        # Total return score (capped at 1.0)
        return_score = min(1.0, max(0.0, pm.total_return_pct / self.config.return_scale))
        
        # Sharpe score (capped at 1.0)
        sharpe_score = min(1.0, max(0.0, pm.sharpe_ratio / self.config.sharpe_scale))
        
        # Weight Sharpe more heavily (risk-adjusted is more important)
        return 0.4 * return_score + 0.6 * sharpe_score
    
    def _score_risk(self, pm: PerformanceMetrics) -> float:
        """Score based on risk metrics (higher is better = lower risk)"""
        # Drawdown score (inverse - lower DD is better)
        dd_score = max(0.0, 1.0 - pm.max_drawdown_pct / self.config.drawdown_scale)
        
        # Volatility score (prefer lower volatility)
        vol_score = max(0.0, 1.0 - pm.volatility / 50.0)  # 50% vol = 0 score
        
        # Calmar ratio bonus
        calmar_bonus = min(0.2, pm.calmar_ratio / 5.0)  # Up to 0.2 bonus
        
        return min(1.0, 0.5 * dd_score + 0.3 * vol_score + calmar_bonus)
    
    def _score_consistency(self, tm: TradeMetrics) -> float:
        """Score based on consistency metrics"""
        # Win rate score
        win_score = min(1.0, tm.win_rate / 0.6)  # 60% win rate = 1.0
        
        # Profit factor score
        pf_score = min(1.0, tm.profit_factor / self.config.profit_factor_scale)
        
        # Expectancy score (normalized)
        exp_score = min(1.0, max(0.0, (tm.expectancy + 10) / 30))  # -10 to 20 range
        
        return 0.4 * win_score + 0.4 * pf_score + 0.2 * exp_score
    
    def _score_efficiency(self, pm: PerformanceMetrics, tm: TradeMetrics) -> float:
        """Score based on efficiency metrics"""
        # Time in market score (prefer moderate time in market)
        # Too little = not trading, too much = overtrading
        time_score = 1.0 - abs(pm.time_in_market_pct - 30) / 50  # Optimal around 30%
        time_score = max(0.0, time_score)
        
        # Trade frequency score (prefer moderate frequency)
        freq_score = 1.0 - abs(pm.trades_per_day - 2) / 5  # Optimal around 2/day
        freq_score = max(0.0, freq_score)
        
        # No-trade rate score (some no-trades is good, too many is bad)
        # Optimal around 70-80% no-trade (selective)
        no_trade_score = 1.0 - abs(pm.no_trade_rate - 0.75) / 0.25
        no_trade_score = max(0.0, min(1.0, no_trade_score))
        
        return 0.3 * time_score + 0.3 * freq_score + 0.4 * no_trade_score


def quick_score(result: BacktestResult) -> float:
    """Quick scoring function for simple use cases"""
    scorer = Scorer()
    card = scorer.score(result)
    return card.fitness
