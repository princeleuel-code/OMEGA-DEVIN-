"""
LAYER 6: REFLECTION - Meta-Cognitive Monitor

The sixth layer of consciousness: REFLECTING on performance.

This module monitors the system's own performance and detects:
1. When predictions are wrong
2. When the model is miscalibrated
3. When the market regime has changed
4. When the system should stop trading

This is META-COGNITION - the system thinking about its own thinking.

Key innovations:
- Real-time calibration monitoring
- Regime change detection
- Performance attribution
- Automatic strategy adjustment triggers

This is what separates a static system from a LEARNING system.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional, Tuple, Callable
from enum import Enum
from collections import deque
import numpy as np

from .perception import MarketState, MarketRegime
from .prediction import ForecastDistribution, ForecastHorizon
from .decision import TradingDecision, DecisionType


class PerformanceMetric(Enum):
    """Types of performance metrics to track."""
    ACCURACY = "accuracy"
    CALIBRATION = "calibration"
    SHARPE = "sharpe"
    PROFIT_FACTOR = "profit_factor"
    WIN_RATE = "win_rate"
    EXPECTANCY = "expectancy"
    MAX_DRAWDOWN = "max_drawdown"


class AlertSeverity(Enum):
    """Severity levels for performance alerts."""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"
    EMERGENCY = "emergency"


class SystemState(Enum):
    """Overall system health states."""
    OPTIMAL = "optimal"
    NORMAL = "normal"
    DEGRADED = "degraded"
    IMPAIRED = "impaired"
    CRITICAL = "critical"
    HALTED = "halted"


@dataclass
class PerformanceAlert:
    """An alert about system performance."""
    timestamp: datetime
    severity: AlertSeverity
    metric: PerformanceMetric
    message: str
    current_value: float
    threshold: float
    recommendation: str
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp.isoformat(),
            "severity": self.severity.value,
            "metric": self.metric.value,
            "message": self.message,
            "current_value": self.current_value,
            "threshold": self.threshold,
            "recommendation": self.recommendation,
        }


@dataclass
class CalibrationReport:
    """Report on forecast calibration."""
    timestamp: datetime
    sample_size: int
    
    # Coverage rates (should match nominal)
    coverage_50: float  # Should be ~50%
    coverage_80: float  # Should be ~80%
    coverage_95: float  # Should be ~95%
    
    # Calibration errors
    calibration_error_50: float
    calibration_error_80: float
    calibration_error_95: float
    
    # Overall calibration score
    overall_score: float
    
    # Is the system well-calibrated?
    is_calibrated: bool
    
    # Recommendations
    recommendations: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp.isoformat(),
            "sample_size": self.sample_size,
            "coverage_50": self.coverage_50,
            "coverage_80": self.coverage_80,
            "coverage_95": self.coverage_95,
            "calibration_error_50": self.calibration_error_50,
            "calibration_error_80": self.calibration_error_80,
            "calibration_error_95": self.calibration_error_95,
            "overall_score": self.overall_score,
            "is_calibrated": self.is_calibrated,
            "recommendations": self.recommendations,
        }


@dataclass
class PerformanceState:
    """
    Complete state of system performance.
    
    This is the "self-awareness" of the system - understanding
    how well it's doing and what needs to change.
    """
    timestamp: datetime
    
    # Overall health
    system_state: SystemState
    health_score: float  # 0-1
    
    # Trading performance
    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    win_rate: float = 0.0
    
    # Returns
    total_return: float = 0.0
    sharpe_ratio: float = 0.0
    sortino_ratio: float = 0.0
    max_drawdown: float = 0.0
    current_drawdown: float = 0.0
    
    # Calibration
    calibration_report: Optional[CalibrationReport] = None
    
    # Regime performance
    regime_performance: Dict[MarketRegime, Dict[str, float]] = field(default_factory=dict)
    
    # Recent alerts
    active_alerts: List[PerformanceAlert] = field(default_factory=list)
    
    # Metrics history
    metrics_history: Dict[PerformanceMetric, List[float]] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp.isoformat(),
            "system_state": self.system_state.value,
            "health_score": self.health_score,
            "total_trades": self.total_trades,
            "winning_trades": self.winning_trades,
            "losing_trades": self.losing_trades,
            "win_rate": self.win_rate,
            "total_return": self.total_return,
            "sharpe_ratio": self.sharpe_ratio,
            "sortino_ratio": self.sortino_ratio,
            "max_drawdown": self.max_drawdown,
            "current_drawdown": self.current_drawdown,
            "calibration_report": self.calibration_report.to_dict() if self.calibration_report else None,
            "active_alerts": [a.to_dict() for a in self.active_alerts],
        }


@dataclass
class TradeResult:
    """Result of a completed trade."""
    decision: TradingDecision
    entry_price: float
    exit_price: float
    pnl: float
    pnl_pct: float
    duration_bars: int
    regime_at_entry: MarketRegime
    regime_at_exit: MarketRegime
    hit_stop: bool
    hit_target: bool
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "symbol": self.decision.symbol,
            "direction": self.decision.direction,
            "entry_price": self.entry_price,
            "exit_price": self.exit_price,
            "pnl": self.pnl,
            "pnl_pct": self.pnl_pct,
            "duration_bars": self.duration_bars,
            "regime_at_entry": self.regime_at_entry.value,
            "regime_at_exit": self.regime_at_exit.value,
            "hit_stop": self.hit_stop,
            "hit_target": self.hit_target,
        }


class MetaCognitiveMonitor:
    """
    The meta-cognitive monitoring system.
    
    This monitors:
    1. Forecast accuracy and calibration
    2. Trading performance
    3. Regime changes
    4. System health
    
    And triggers:
    1. Alerts when performance degrades
    2. Strategy adjustments
    3. Trading halts when necessary
    """
    
    # Thresholds for alerts
    THRESHOLDS = {
        "calibration_error": 0.15,      # Max acceptable calibration error
        "min_win_rate": 0.35,           # Minimum acceptable win rate
        "max_drawdown": 0.20,           # Maximum acceptable drawdown
        "min_sharpe": 0.5,              # Minimum acceptable Sharpe
        "min_profit_factor": 1.2,       # Minimum acceptable profit factor
        "max_losing_streak": 5,         # Maximum consecutive losses
        "min_trades_for_eval": 20,      # Minimum trades before evaluation
    }
    
    def __init__(self):
        # Forecast tracking
        self.forecasts: deque = deque(maxlen=1000)  # (forecast, actual)
        
        # Trade tracking
        self.trades: List[TradeResult] = []
        self.open_trades: Dict[str, TradingDecision] = {}
        
        # Equity tracking
        self.equity_curve: List[float] = [10000.0]
        self.peak_equity: float = 10000.0
        
        # Regime tracking
        self.regime_history: deque = deque(maxlen=500)
        self.current_regime: MarketRegime = MarketRegime.UNKNOWN
        
        # Alert history
        self.alert_history: List[PerformanceAlert] = []
        
        # Callbacks for alerts
        self.alert_callbacks: List[Callable[[PerformanceAlert], None]] = []
        
        # Current state
        self.current_state: Optional[PerformanceState] = None
        
        # Losing streak counter
        self.current_losing_streak: int = 0
        self.max_losing_streak: int = 0
    
    def record_forecast(
        self,
        forecast: ForecastDistribution,
        actual_price: float,
    ) -> None:
        """Record a forecast and its actual outcome."""
        self.forecasts.append({
            "forecast": forecast,
            "actual": actual_price,
            "timestamp": datetime.now(timezone.utc),
        })
        
        # Check calibration periodically
        if len(self.forecasts) % 50 == 0:
            self._check_calibration()
    
    def record_trade_entry(
        self,
        decision: TradingDecision,
        regime: MarketRegime,
    ) -> None:
        """Record a trade entry."""
        self.open_trades[decision.symbol] = decision
    
    def record_trade_exit(
        self,
        symbol: str,
        exit_price: float,
        regime: MarketRegime,
        hit_stop: bool = False,
        hit_target: bool = False,
        duration_bars: int = 0,
    ) -> Optional[TradeResult]:
        """Record a trade exit and compute result."""
        if symbol not in self.open_trades:
            return None
        
        decision = self.open_trades.pop(symbol)
        entry_price = decision.entry_price or 0
        
        # Compute PnL
        if decision.direction > 0:  # Long
            pnl = exit_price - entry_price
        else:  # Short
            pnl = entry_price - exit_price
        
        pnl_pct = pnl / entry_price if entry_price > 0 else 0
        
        # Create result
        result = TradeResult(
            decision=decision,
            entry_price=entry_price,
            exit_price=exit_price,
            pnl=pnl,
            pnl_pct=pnl_pct,
            duration_bars=duration_bars,
            regime_at_entry=self.current_regime,
            regime_at_exit=regime,
            hit_stop=hit_stop,
            hit_target=hit_target,
        )
        
        self.trades.append(result)
        
        # Update equity
        position_value = decision.position_sizing.size_pct * self.equity_curve[-1] if decision.position_sizing else 0
        equity_change = position_value * pnl_pct
        new_equity = self.equity_curve[-1] + equity_change
        self.equity_curve.append(new_equity)
        
        if new_equity > self.peak_equity:
            self.peak_equity = new_equity
        
        # Update losing streak
        if pnl < 0:
            self.current_losing_streak += 1
            self.max_losing_streak = max(self.max_losing_streak, self.current_losing_streak)
        else:
            self.current_losing_streak = 0
        
        # Check for alerts
        self._check_trade_alerts(result)
        
        return result
    
    def update_regime(self, regime: MarketRegime) -> bool:
        """Update current regime and detect changes."""
        old_regime = self.current_regime
        self.current_regime = regime
        
        self.regime_history.append({
            "regime": regime,
            "timestamp": datetime.now(timezone.utc),
        })
        
        # Detect regime change
        if old_regime != regime and old_regime != MarketRegime.UNKNOWN:
            self._on_regime_change(old_regime, regime)
            return True
        
        return False
    
    def get_performance_state(self) -> PerformanceState:
        """Get current performance state."""
        timestamp = datetime.now(timezone.utc)
        
        # Compute metrics
        total_trades = len(self.trades)
        winning_trades = sum(1 for t in self.trades if t.pnl > 0)
        losing_trades = sum(1 for t in self.trades if t.pnl < 0)
        win_rate = winning_trades / total_trades if total_trades > 0 else 0
        
        # Returns
        if len(self.equity_curve) > 1:
            total_return = (self.equity_curve[-1] / self.equity_curve[0]) - 1
            
            # Compute Sharpe
            returns = np.diff(self.equity_curve) / np.array(self.equity_curve[:-1])
            if len(returns) > 1 and np.std(returns) > 0:
                sharpe_ratio = np.mean(returns) / np.std(returns) * np.sqrt(252)
                
                # Sortino (downside deviation)
                downside_returns = returns[returns < 0]
                if len(downside_returns) > 0:
                    sortino_ratio = np.mean(returns) / np.std(downside_returns) * np.sqrt(252)
                else:
                    sortino_ratio = sharpe_ratio
            else:
                sharpe_ratio = 0.0
                sortino_ratio = 0.0
        else:
            total_return = 0.0
            sharpe_ratio = 0.0
            sortino_ratio = 0.0
        
        # Drawdown
        max_drawdown = self._compute_max_drawdown()
        current_drawdown = (self.peak_equity - self.equity_curve[-1]) / self.peak_equity if self.peak_equity > 0 else 0
        
        # Calibration
        calibration_report = self._compute_calibration_report()
        
        # Regime performance
        regime_performance = self._compute_regime_performance()
        
        # Health score
        health_score = self._compute_health_score(
            win_rate, sharpe_ratio, max_drawdown, calibration_report
        )
        
        # System state
        system_state = self._determine_system_state(health_score, current_drawdown)
        
        # Active alerts
        active_alerts = [a for a in self.alert_history[-20:] if a.severity in [AlertSeverity.WARNING, AlertSeverity.CRITICAL, AlertSeverity.EMERGENCY]]
        
        self.current_state = PerformanceState(
            timestamp=timestamp,
            system_state=system_state,
            health_score=health_score,
            total_trades=total_trades,
            winning_trades=winning_trades,
            losing_trades=losing_trades,
            win_rate=win_rate,
            total_return=total_return,
            sharpe_ratio=sharpe_ratio,
            sortino_ratio=sortino_ratio,
            max_drawdown=max_drawdown,
            current_drawdown=current_drawdown,
            calibration_report=calibration_report,
            regime_performance=regime_performance,
            active_alerts=active_alerts,
        )
        
        return self.current_state
    
    def should_halt_trading(self) -> Tuple[bool, Optional[str]]:
        """Check if trading should be halted."""
        if not self.current_state:
            self.get_performance_state()
        
        state = self.current_state
        
        # Check critical conditions
        if state.current_drawdown > self.THRESHOLDS["max_drawdown"]:
            return True, f"Drawdown {state.current_drawdown:.1%} exceeds maximum {self.THRESHOLDS['max_drawdown']:.1%}"
        
        if self.current_losing_streak >= self.THRESHOLDS["max_losing_streak"]:
            return True, f"Losing streak of {self.current_losing_streak} exceeds maximum {self.THRESHOLDS['max_losing_streak']}"
        
        if state.system_state in [SystemState.CRITICAL, SystemState.HALTED]:
            return True, f"System state is {state.system_state.value}"
        
        # Check calibration
        if state.calibration_report and not state.calibration_report.is_calibrated:
            if state.calibration_report.overall_score < 0.5:
                return True, "Severe calibration issues detected"
        
        return False, None
    
    def _check_calibration(self) -> None:
        """Check forecast calibration and raise alerts if needed."""
        if len(self.forecasts) < 50:
            return
        
        report = self._compute_calibration_report()
        
        if not report.is_calibrated:
            alert = PerformanceAlert(
                timestamp=datetime.now(timezone.utc),
                severity=AlertSeverity.WARNING if report.overall_score > 0.6 else AlertSeverity.CRITICAL,
                metric=PerformanceMetric.CALIBRATION,
                message=f"Forecast calibration degraded. Score: {report.overall_score:.0%}",
                current_value=report.overall_score,
                threshold=0.8,
                recommendation="Consider recalibrating forecasters or reducing position sizes",
            )
            self._raise_alert(alert)
    
    def _check_trade_alerts(self, result: TradeResult) -> None:
        """Check for alerts after a trade."""
        # Check losing streak
        if self.current_losing_streak >= 3:
            alert = PerformanceAlert(
                timestamp=datetime.now(timezone.utc),
                severity=AlertSeverity.WARNING if self.current_losing_streak < 5 else AlertSeverity.CRITICAL,
                metric=PerformanceMetric.WIN_RATE,
                message=f"Losing streak: {self.current_losing_streak} consecutive losses",
                current_value=self.current_losing_streak,
                threshold=self.THRESHOLDS["max_losing_streak"],
                recommendation="Review recent trades and consider reducing size or pausing",
            )
            self._raise_alert(alert)
        
        # Check drawdown
        current_dd = (self.peak_equity - self.equity_curve[-1]) / self.peak_equity if self.peak_equity > 0 else 0
        if current_dd > 0.10:
            severity = AlertSeverity.WARNING if current_dd < 0.15 else AlertSeverity.CRITICAL
            alert = PerformanceAlert(
                timestamp=datetime.now(timezone.utc),
                severity=severity,
                metric=PerformanceMetric.MAX_DRAWDOWN,
                message=f"Drawdown alert: {current_dd:.1%}",
                current_value=current_dd,
                threshold=self.THRESHOLDS["max_drawdown"],
                recommendation="Consider reducing position sizes or pausing trading",
            )
            self._raise_alert(alert)
    
    def _on_regime_change(self, old_regime: MarketRegime, new_regime: MarketRegime) -> None:
        """Handle regime change."""
        alert = PerformanceAlert(
            timestamp=datetime.now(timezone.utc),
            severity=AlertSeverity.INFO,
            metric=PerformanceMetric.ACCURACY,
            message=f"Regime change detected: {old_regime.value} -> {new_regime.value}",
            current_value=0,
            threshold=0,
            recommendation="Review strategy parameters for new regime",
        )
        self._raise_alert(alert)
    
    def _raise_alert(self, alert: PerformanceAlert) -> None:
        """Raise an alert and notify callbacks."""
        self.alert_history.append(alert)
        
        for callback in self.alert_callbacks:
            try:
                callback(alert)
            except Exception:
                pass
    
    def _compute_calibration_report(self) -> CalibrationReport:
        """Compute calibration report from forecast history."""
        if len(self.forecasts) < 20:
            return CalibrationReport(
                timestamp=datetime.now(timezone.utc),
                sample_size=len(self.forecasts),
                coverage_50=0.5,
                coverage_80=0.8,
                coverage_95=0.95,
                calibration_error_50=0,
                calibration_error_80=0,
                calibration_error_95=0,
                overall_score=0.5,
                is_calibrated=True,
                recommendations=["Insufficient data for calibration assessment"],
            )
        
        # Compute coverage rates
        in_50 = 0
        in_80 = 0
        in_95 = 0
        
        for record in self.forecasts:
            forecast = record["forecast"]
            actual = record["actual"]
            
            if forecast.ci_50[0] <= actual <= forecast.ci_50[1]:
                in_50 += 1
            if forecast.ci_80[0] <= actual <= forecast.ci_80[1]:
                in_80 += 1
            if forecast.ci_95[0] <= actual <= forecast.ci_95[1]:
                in_95 += 1
        
        n = len(self.forecasts)
        coverage_50 = in_50 / n
        coverage_80 = in_80 / n
        coverage_95 = in_95 / n
        
        # Calibration errors
        error_50 = abs(coverage_50 - 0.50)
        error_80 = abs(coverage_80 - 0.80)
        error_95 = abs(coverage_95 - 0.95)
        
        # Overall score (1 - average error)
        avg_error = (error_50 + error_80 + error_95) / 3
        overall_score = max(0, 1 - avg_error * 2)
        
        # Is calibrated?
        is_calibrated = avg_error < self.THRESHOLDS["calibration_error"]
        
        # Recommendations
        recommendations = []
        if coverage_50 < 0.45:
            recommendations.append("50% CI under-covering - widen intervals")
        elif coverage_50 > 0.55:
            recommendations.append("50% CI over-covering - narrow intervals")
        
        if coverage_95 < 0.90:
            recommendations.append("95% CI under-covering - increase uncertainty estimates")
        
        return CalibrationReport(
            timestamp=datetime.now(timezone.utc),
            sample_size=n,
            coverage_50=coverage_50,
            coverage_80=coverage_80,
            coverage_95=coverage_95,
            calibration_error_50=error_50,
            calibration_error_80=error_80,
            calibration_error_95=error_95,
            overall_score=overall_score,
            is_calibrated=is_calibrated,
            recommendations=recommendations,
        )
    
    def _compute_max_drawdown(self) -> float:
        """Compute maximum drawdown from equity curve."""
        if len(self.equity_curve) < 2:
            return 0.0
        
        peak = self.equity_curve[0]
        max_dd = 0.0
        
        for equity in self.equity_curve:
            if equity > peak:
                peak = equity
            dd = (peak - equity) / peak if peak > 0 else 0
            max_dd = max(max_dd, dd)
        
        return max_dd
    
    def _compute_regime_performance(self) -> Dict[MarketRegime, Dict[str, float]]:
        """Compute performance by regime."""
        regime_trades: Dict[MarketRegime, List[TradeResult]] = {}
        
        for trade in self.trades:
            regime = trade.regime_at_entry
            if regime not in regime_trades:
                regime_trades[regime] = []
            regime_trades[regime].append(trade)
        
        performance = {}
        for regime, trades in regime_trades.items():
            if not trades:
                continue
            
            wins = sum(1 for t in trades if t.pnl > 0)
            total_pnl = sum(t.pnl_pct for t in trades)
            
            performance[regime] = {
                "trades": len(trades),
                "win_rate": wins / len(trades),
                "total_return": total_pnl,
                "avg_return": total_pnl / len(trades),
            }
        
        return performance
    
    def _compute_health_score(
        self,
        win_rate: float,
        sharpe: float,
        max_dd: float,
        calibration: Optional[CalibrationReport],
    ) -> float:
        """Compute overall health score."""
        scores = []
        
        # Win rate score (0.35 = 0, 0.55 = 1)
        wr_score = max(0, min(1, (win_rate - 0.35) / 0.20))
        scores.append(wr_score)
        
        # Sharpe score (0 = 0, 2 = 1)
        sharpe_score = max(0, min(1, sharpe / 2))
        scores.append(sharpe_score)
        
        # Drawdown score (0.20 = 0, 0 = 1)
        dd_score = max(0, 1 - max_dd / 0.20)
        scores.append(dd_score)
        
        # Calibration score
        if calibration:
            scores.append(calibration.overall_score)
        
        return sum(scores) / len(scores) if scores else 0.5
    
    def _determine_system_state(
        self,
        health_score: float,
        current_drawdown: float,
    ) -> SystemState:
        """Determine overall system state."""
        if current_drawdown > self.THRESHOLDS["max_drawdown"]:
            return SystemState.HALTED
        
        if self.current_losing_streak >= self.THRESHOLDS["max_losing_streak"]:
            return SystemState.CRITICAL
        
        if health_score >= 0.8:
            return SystemState.OPTIMAL
        elif health_score >= 0.6:
            return SystemState.NORMAL
        elif health_score >= 0.4:
            return SystemState.DEGRADED
        elif health_score >= 0.2:
            return SystemState.IMPAIRED
        else:
            return SystemState.CRITICAL
    
    def register_alert_callback(self, callback: Callable[[PerformanceAlert], None]) -> None:
        """Register a callback for alerts."""
        self.alert_callbacks.append(callback)
    
    def get_summary(self) -> Dict[str, Any]:
        """Get summary of monitoring state."""
        state = self.get_performance_state()
        
        return {
            "system_state": state.system_state.value,
            "health_score": state.health_score,
            "total_trades": state.total_trades,
            "win_rate": state.win_rate,
            "total_return": state.total_return,
            "sharpe_ratio": state.sharpe_ratio,
            "max_drawdown": state.max_drawdown,
            "current_drawdown": state.current_drawdown,
            "current_losing_streak": self.current_losing_streak,
            "active_alerts": len(state.active_alerts),
            "calibration_score": state.calibration_report.overall_score if state.calibration_report else None,
        }
