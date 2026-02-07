"""
Backtester - Walk-forward backtesting engine

Simulates trading with realistic costs and slippage.
Produces deterministic, reproducible results.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Callable
from pathlib import Path
import json
import logging

from ..data.loader import OHLCV
from ..data.features import FeatureEngine, Features, Trend
from ..evolution.genome import StrategyGenome
from ..core.decision_engine import DecisionEngine, Action, Signal, create_wait_signal
from ..core.veto_cascade import MarketContext, VetoConfig
from ..core.truth_manifest import TruthManifest, create_manifest
from .metrics import Trade, TradeMetrics, PerformanceMetrics


logger = logging.getLogger(__name__)


@dataclass
class BacktestConfig:
    """Configuration for backtesting"""
    # Capital
    initial_capital: float = 10000.0
    
    # Costs
    spread_pips: float = 1.0  # Fixed spread in pips
    commission_per_lot: float = 0.0  # Commission per lot
    slippage_pips: float = 0.5  # Slippage in pips
    
    # Position sizing
    pip_value: float = 10.0  # Value per pip per lot (standard lot)
    
    # Timing
    bars_per_day: float = 24.0  # For hourly bars
    
    # Symbol info
    symbol: str = "EURUSD"
    pip_size: float = 0.0001  # 4 decimal places


@dataclass
class Position:
    """An open position"""
    direction: int  # 1 for long, -1 for short
    entry_price: float
    entry_time: datetime
    entry_bar: int
    size: float
    stop_loss: float
    take_profit: float
    
    def get_pnl(self, current_price: float, pip_value: float, pip_size: float) -> float:
        """Calculate current P&L"""
        price_diff = (current_price - self.entry_price) * self.direction
        pips = price_diff / pip_size
        return pips * pip_value * self.size
    
    def check_exit(self, bar: OHLCV) -> Optional[str]:
        """Check if position should be closed"""
        if self.direction == 1:  # Long
            if bar.low <= self.stop_loss:
                return "stop_loss"
            if bar.high >= self.take_profit:
                return "take_profit"
        else:  # Short
            if bar.high >= self.stop_loss:
                return "stop_loss"
            if bar.low <= self.take_profit:
                return "take_profit"
        return None


@dataclass
class BacktestResult:
    """Complete result of a backtest"""
    # Configuration
    genome_id: str
    config: Dict[str, Any]
    
    # Results
    trades: List[Trade]
    equity_curve: List[float]
    
    # Metrics
    trade_metrics: TradeMetrics
    performance_metrics: PerformanceMetrics
    
    # Decisions
    total_decisions: int = 0
    no_trade_decisions: int = 0
    
    # Manifest
    manifest: Optional[TruthManifest] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "genome_id": self.genome_id,
            "config": self.config,
            "trade_count": len(self.trades),
            "trades": [t.to_dict() for t in self.trades],
            "final_equity": self.equity_curve[-1] if self.equity_curve else 0,
            "trade_metrics": self.trade_metrics.to_dict(),
            "performance_metrics": self.performance_metrics.to_dict(),
            "total_decisions": self.total_decisions,
            "no_trade_decisions": self.no_trade_decisions,
            "no_trade_rate": self.no_trade_decisions / self.total_decisions if self.total_decisions > 0 else 0
        }
    
    def save(self, path: Path):
        """Save result to JSON file"""
        with open(path, "w") as f:
            json.dump(self.to_dict(), f, indent=2)


class Backtester:
    """
    Walk-forward backtesting engine.
    
    Simulates trading bar-by-bar with realistic execution.
    """
    
    def __init__(
        self,
        config: Optional[BacktestConfig] = None,
        signal_generator: Optional[Callable[[Features, StrategyGenome], Signal]] = None
    ):
        self.config = config or BacktestConfig()
        self.signal_generator = signal_generator or self._default_signal_generator
        
        # State
        self._position: Optional[Position] = None
        self._equity: float = 0
        self._equity_curve: List[float] = []
        self._trades: List[Trade] = []
        self._decisions: int = 0
        self._no_trades: int = 0
    
    def run(
        self,
        data: List[OHLCV],
        genome: StrategyGenome,
        create_manifest: bool = True,
        trade_start_bar: int = 0,
    ) -> BacktestResult:
        """
        Run backtest on data with given strategy genome.
        """
        # Reset state
        self._position = None
        self._equity = self.config.initial_capital
        self._equity_curve = [self._equity]
        self._trades = []
        self._decisions = 0
        self._no_trades = 0
        
        # Create manifest if requested
        manifest = None
        if create_manifest:
            manifest = TruthManifest(command="backtest")
            manifest.set_config({
                "genome_id": genome.genome_id,
                "initial_capital": self.config.initial_capital,
                "symbol": self.config.symbol,
                "data_bars": len(data)
            })
        
        # Compute features
        feature_engine = FeatureEngine()
        features = feature_engine.compute(data)
        
        if not features:
            logger.warning("No features computed - data too short")
            return self._create_result(genome, manifest)
        
        # Create decision engine
        veto_config = VetoConfig(
            max_daily_loss=-self.config.initial_capital * genome.max_drawdown_pct / 100,
            max_drawdown_pct=genome.max_drawdown_pct,
            max_trades_per_day=genome.max_trades_per_day
        )
        decision_engine = DecisionEngine(veto_config=veto_config, manifest=manifest)
        
        # Map features back to data indices
        warmup = len(data) - len(features)
        
        # Run simulation
        for i, feat in enumerate(features):
            bar_idx = warmup + i
            bar = data[bar_idx]

            # Optional: allow feature warmup / context, but do not trade or count
            # decisions until trade_start_bar. This is used by purged walk-forward
            # evaluation to avoid leaking across train/test boundaries.
            if bar_idx < trade_start_bar:
                current_equity = self._equity
                if self._position:
                    current_equity += self._position.get_pnl(
                        bar.close,
                        self.config.pip_value,
                        self.config.pip_size,
                    )
                self._equity_curve.append(current_equity)
                continue

            # Check for position exit first
            if self._position:
                exit_reason = self._position.check_exit(bar)
                if exit_reason:
                    self._close_position(bar, bar_idx, exit_reason)
            
            # Generate signal
            signal = self.signal_generator(feat, genome)
            
            # Create market context
            # In backtesting, last_update equals timestamp (data is always "fresh")
            context = MarketContext(
                symbol=self.config.symbol,
                timestamp=bar.timestamp,
                bid=bar.close - self.config.spread_pips * self.config.pip_size / 2,
                ask=bar.close + self.config.spread_pips * self.config.pip_size / 2,
                spread=self.config.spread_pips * self.config.pip_size,
                last_update=bar.timestamp,  # Same as timestamp for backtesting
                volatility=feat.volatility,
                session_open=True
            )
            
            # Process through decision engine
            decision = decision_engine.process(context, signal)
            self._decisions += 1
            
            if manifest:
                manifest.add_decision(decision.to_dict())
            
            # Execute decision
            if decision.final_action == Action.WAIT or decision.final_action == Action.FAIL_CLOSED:
                self._no_trades += 1
            elif decision.final_action in (Action.LONG, Action.SHORT) and not self._position:
                self._open_position(decision, bar, bar_idx, feat)
            
            # Update equity curve
            current_equity = self._equity
            if self._position:
                current_equity += self._position.get_pnl(
                    bar.close,
                    self.config.pip_value,
                    self.config.pip_size
                )
            self._equity_curve.append(current_equity)
            
            # Update risk state
            decision_engine.update_risk_state(
                daily_pnl=current_equity - self.config.initial_capital,
                max_drawdown=self._calculate_drawdown(),
                trades_today=len(self._trades)  # Simplified
            )
        
        # Close any remaining position
        if self._position and features:
            last_bar = data[-1]
            self._close_position(last_bar, len(data) - 1, "end_of_data")
        
        return self._create_result(genome, manifest)
    
    def _open_position(
        self,
        decision: Any,
        bar: OHLCV,
        bar_idx: int,
        feat: Features
    ):
        """Open a new position"""
        direction = 1 if decision.final_action == Action.LONG else -1
        
        # Calculate entry price with slippage
        slippage = self.config.slippage_pips * self.config.pip_size
        if direction == 1:
            entry_price = bar.close + slippage
        else:
            entry_price = bar.close - slippage
        
        # Get stop loss and take profit from signal
        if decision.signal.stop_loss and decision.signal.take_profit:
            stop_loss = decision.signal.stop_loss
            take_profit = decision.signal.take_profit
        else:
            # Default based on ATR
            atr = feat.atr
            if direction == 1:
                stop_loss = entry_price - atr * 2
                take_profit = entry_price + atr * 3
            else:
                stop_loss = entry_price + atr * 2
                take_profit = entry_price - atr * 3
        
        # Calculate position size based on risk
        risk_amount = self._equity * (decision.signal.size if decision.signal.size > 0 else 0.01)
        risk_pips = abs(entry_price - stop_loss) / self.config.pip_size
        if risk_pips > 0:
            size = risk_amount / (risk_pips * self.config.pip_value)
            size = min(size, 1.0)  # Cap at 1 lot
        else:
            size = 0.01  # Minimum size
        
        self._position = Position(
            direction=direction,
            entry_price=entry_price,
            entry_time=bar.timestamp,
            entry_bar=bar_idx,
            size=size,
            stop_loss=stop_loss,
            take_profit=take_profit
        )
        
        logger.debug(
            f"Opened {'LONG' if direction == 1 else 'SHORT'} at {entry_price:.5f}, "
            f"SL={stop_loss:.5f}, TP={take_profit:.5f}, size={size:.2f}"
        )
    
    def _close_position(self, bar: OHLCV, bar_idx: int, reason: str):
        """Close the current position"""
        if not self._position:
            return
        
        # Determine exit price
        if reason == "stop_loss":
            exit_price = self._position.stop_loss
        elif reason == "take_profit":
            exit_price = self._position.take_profit
        else:
            exit_price = bar.close
        
        # Add slippage
        slippage = self.config.slippage_pips * self.config.pip_size
        if self._position.direction == 1:
            exit_price -= slippage
        else:
            exit_price += slippage
        
        # Calculate P&L
        pnl = self._position.get_pnl(
            exit_price,
            self.config.pip_value,
            self.config.pip_size
        )
        
        # Subtract commission
        pnl -= self.config.commission_per_lot * self._position.size * 2  # Entry + exit
        
        # Calculate percentage P&L
        pnl_pct = pnl / self._equity * 100 if self._equity > 0 else 0
        
        # Record trade
        trade = Trade(
            entry_time=self._position.entry_time,
            exit_time=bar.timestamp,
            direction=self._position.direction,
            entry_price=self._position.entry_price,
            exit_price=exit_price,
            size=self._position.size,
            pnl=pnl,
            pnl_pct=pnl_pct,
            bars_held=bar_idx - self._position.entry_bar,
            exit_reason=reason
        )
        self._trades.append(trade)
        
        # Update equity
        self._equity += pnl
        
        logger.debug(
            f"Closed {'LONG' if self._position.direction == 1 else 'SHORT'} at {exit_price:.5f}, "
            f"P&L={pnl:.2f} ({pnl_pct:.2f}%), reason={reason}"
        )
        
        self._position = None
    
    def _calculate_drawdown(self) -> float:
        """Calculate current drawdown percentage"""
        if not self._equity_curve:
            return 0.0
        
        peak = max(self._equity_curve)
        current = self._equity_curve[-1]
        
        if peak <= 0:
            return 0.0
        
        return (peak - current) / peak * 100
    
    def _create_result(
        self,
        genome: StrategyGenome,
        manifest: Optional[TruthManifest]
    ) -> BacktestResult:
        """Create the backtest result"""
        trade_metrics = TradeMetrics.from_trades(self._trades)
        
        performance_metrics = PerformanceMetrics.from_equity_curve(
            self._equity_curve,
            self._trades,
            self.config.initial_capital,
            self.config.bars_per_day
        )
        performance_metrics.no_trade_decisions = self._no_trades
        performance_metrics.no_trade_rate = (
            self._no_trades / self._decisions if self._decisions > 0 else 0
        )
        
        if manifest:
            manifest.finalize(
                passed=len(self._trades),
                total=self._decisions,
                errors=[]
            )
        
        return BacktestResult(
            genome_id=genome.genome_id,
            config=self.config.__dict__,
            trades=self._trades,
            equity_curve=self._equity_curve,
            trade_metrics=trade_metrics,
            performance_metrics=performance_metrics,
            total_decisions=self._decisions,
            no_trade_decisions=self._no_trades,
            manifest=manifest
        )
    
    def _default_signal_generator(
        self,
        feat: Features,
        genome: StrategyGenome
    ) -> Signal:
        """
        Default signal generator based on market structure.
        
        This implements the "Ethiopian Method" structure-based trading.
        """
        from ..core.decision_engine import Signal, Action, create_wait_signal, create_trade_signal
        from ..core.reason_codes import ReasonCode
        
        # Check minimum ATR
        if feat.atr < genome.min_atr:
            return create_wait_signal("ATR too low")
        
        # Check volume
        if feat.relative_volume < genome.min_volume_ratio:
            return create_wait_signal("Volume too low")
        
        # Check for displacement if required
        if genome.require_displacement and not feat.displacement:
            return create_wait_signal("No displacement")
        
        # Check structure
        structure = feat.structure
        
        # Bullish setup: trend is bullish, or we have a change of character to bullish
        bullish_setup = (
            structure.trend == Trend.BULLISH or
            (structure.change_of_character and feat.displacement_direction == 1)
        )
        
        # Bearish setup: trend is bearish, or we have a change of character to bearish
        bearish_setup = (
            structure.trend == Trend.BEARISH or
            (structure.change_of_character and feat.displacement_direction == -1)
        )
        
        # Check regime affinity
        is_trending = structure.trend in (Trend.BULLISH, Trend.BEARISH)
        if is_trending and genome.trend_affinity < 0.3:
            return create_wait_signal("Trend regime but low trend affinity")
        if not is_trending and genome.trend_affinity > 0.7:
            return create_wait_signal("Range regime but high trend affinity")
        
        # Generate signal
        if bullish_setup:
            # Calculate levels
            entry = feat.close
            stop_loss = entry - feat.atr * genome.atr_multiplier_sl
            take_profit = entry + feat.atr * genome.atr_multiplier_tp
            
            # Confidence based on confluence
            confidence = 0.5
            if feat.displacement:
                confidence += 0.15
            if structure.trend == Trend.BULLISH:
                confidence += 0.15
            if feat.relative_volume > 1.5:
                confidence += 0.1
            
            if confidence >= genome.min_confidence:
                return create_trade_signal(
                    action=Action.LONG,
                    confidence=min(confidence, 1.0),
                    entry=entry,
                    stop_loss=stop_loss,
                    take_profit=take_profit,
                    size=genome.risk_per_trade_pct / 100,
                    reason="Bullish structure setup"
                )
        
        elif bearish_setup:
            entry = feat.close
            stop_loss = entry + feat.atr * genome.atr_multiplier_sl
            take_profit = entry - feat.atr * genome.atr_multiplier_tp
            
            confidence = 0.5
            if feat.displacement:
                confidence += 0.15
            if structure.trend == Trend.BEARISH:
                confidence += 0.15
            if feat.relative_volume > 1.5:
                confidence += 0.1
            
            if confidence >= genome.min_confidence:
                return create_trade_signal(
                    action=Action.SHORT,
                    confidence=min(confidence, 1.0),
                    entry=entry,
                    stop_loss=stop_loss,
                    take_profit=take_profit,
                    size=genome.risk_per_trade_pct / 100,
                    reason="Bearish structure setup"
                )
        
        return create_wait_signal("No valid setup")
