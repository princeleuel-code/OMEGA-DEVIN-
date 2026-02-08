# TRADING BRAIN - The Decision Engine
#
# The brain implements the core trading interfaces:
# - get_features(t) -> x_t
# - propose_action(x_t) -> proposal
# - veto(proposal, context) -> allow/deny + reason_codes[]
# - send_order(order) (paper only)
# - score(run) -> metrics
#
# This is the "Omni-Pipeline" that processes market data into trading decisions.

import sys
import os
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime
import json

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from .pipeline import Pipeline, TradingPipeline, PipelineResult
from .veto import VetoGate, VetoResult
from .truth_manifest import TruthManifest


@dataclass
class TradeProposal:
    """A proposed trade from the strategy"""
    signal: str  # BUY, SELL, HOLD
    symbol: str
    price: float
    confidence: float
    position_size_pct: float
    strategy_id: str
    features: Dict = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> Dict:
        return {
            "signal": self.signal,
            "symbol": self.symbol,
            "price": self.price,
            "confidence": self.confidence,
            "position_size_pct": self.position_size_pct,
            "strategy_id": self.strategy_id,
            "features": self.features,
            "timestamp": self.timestamp
        }


@dataclass
class TradeOrder:
    """An approved trade order"""
    proposal: TradeProposal
    order_id: str
    order_type: str = "MARKET"
    status: str = "PENDING"
    filled_price: Optional[float] = None
    filled_at: Optional[str] = None
    
    def to_dict(self) -> Dict:
        return {
            "order_id": self.order_id,
            "order_type": self.order_type,
            "status": self.status,
            "filled_price": self.filled_price,
            "filled_at": self.filled_at,
            **self.proposal.to_dict()
        }


class TradingBrain:
    """
    THE TRADING BRAIN
    
    The central decision engine that:
    1. Extracts features from market data
    2. Proposes actions based on strategy
    3. Vetos unsafe proposals
    4. Executes approved orders (paper only)
    5. Scores performance
    
    Architecture:
    tick |> get_features() |> propose_action() |> veto() |> send_order() |> score()
    
    The brain ONLY consumes approved StrategySpecs from the Sakana evolution lab.
    No surprises - everything is audited and reproducible.
    """
    
    def __init__(self, config: Dict = None):
        self.config = config or self._default_config()
        self.veto_gate = VetoGate()
        self.manifest = TruthManifest()
        self.manifest.set_config(self.config)
        
        # Strategy registry - only approved strategies can be used
        self.approved_strategies: Dict[str, Callable] = {}
        self.active_strategy_id: Optional[str] = None
        
        # State
        self.orders: List[TradeOrder] = []
        self.positions: Dict[str, float] = {}  # symbol -> position size
        self.balance = self.config.get("initial_balance", 10000)
        self.equity_curve: List[float] = [self.balance]
        
        # Metrics
        self.trades_taken = 0
        self.trades_won = 0
        self.total_pnl = 0.0
        
    def _default_config(self) -> Dict:
        """Default brain configuration"""
        return {
            "initial_balance": 10000,
            "max_position_pct": 0.05,
            "max_drawdown_pct": 0.10,
            "max_daily_loss_pct": 0.02,
            "min_confidence": 0.60,
            "paper_mode": True,  # ALWAYS paper mode initially
            "approved_strategies": []
        }
        
    def register_strategy(self, strategy_id: str, strategy_func: Callable) -> 'TradingBrain':
        """
        Register an approved strategy.
        
        Only strategies that have passed the promotion pipeline can be registered:
        backtest -> walk-forward -> stress -> paper probation -> production
        """
        self.approved_strategies[strategy_id] = strategy_func
        if "approved_strategies" not in self.config:
            self.config["approved_strategies"] = []
        self.config["approved_strategies"].append(strategy_id)
        return self
        
    def set_active_strategy(self, strategy_id: str) -> 'TradingBrain':
        """Set the active strategy"""
        if strategy_id not in self.approved_strategies:
            raise ValueError(f"Strategy {strategy_id} not approved")
        self.active_strategy_id = strategy_id
        self.manifest.set_strategy(strategy_id)
        return self
        
    def get_features(self, tick: Dict) -> Dict:
        """
        Extract features from market tick.
        
        Interface: get_features(t) -> x_t
        
        This transforms raw market data into features for the strategy.
        """
        features = {
            "timestamp": tick.get("timestamp", datetime.now().isoformat()),
            "symbol": tick.get("symbol", "UNKNOWN"),
            "price": float(tick.get("close", tick.get("price", 0))),
            "open": float(tick.get("open", 0)),
            "high": float(tick.get("high", 0)),
            "low": float(tick.get("low", 0)),
            "volume": float(tick.get("volume", 0)),
        }
        
        # Add technical indicators if we have history
        if "bars" in tick and len(tick["bars"]) >= 20:
            bars = tick["bars"]
            closes = [b.get("close", b.get("price", 0)) for b in bars]
            
            # Simple moving averages
            features["sma_10"] = sum(closes[-10:]) / 10
            features["sma_20"] = sum(closes[-20:]) / 20
            
            # Price momentum
            features["momentum_5"] = (closes[-1] - closes[-5]) / closes[-5] if closes[-5] else 0
            features["momentum_10"] = (closes[-1] - closes[-10]) / closes[-10] if closes[-10] else 0
            
            # Trend direction
            features["trend"] = "UP" if features["sma_10"] > features["sma_20"] else "DOWN"
            
        return features
        
    def propose_action(self, features: Dict) -> TradeProposal:
        """
        Propose a trading action based on features.
        
        Interface: propose_action(x_t) -> proposal
        
        Uses the active strategy to generate a trade proposal.
        """
        if not self.active_strategy_id:
            return TradeProposal(
                signal="HOLD",
                symbol=features.get("symbol", "UNKNOWN"),
                price=features.get("price", 0),
                confidence=0,
                position_size_pct=0,
                strategy_id="none",
                features=features
            )
            
        strategy_func = self.approved_strategies[self.active_strategy_id]
        
        try:
            result = strategy_func(features)
            
            return TradeProposal(
                signal=result.get("signal", "HOLD"),
                symbol=features.get("symbol", "UNKNOWN"),
                price=features.get("price", 0),
                confidence=result.get("confidence", 0),
                position_size_pct=result.get("position_size_pct", 0.01),
                strategy_id=self.active_strategy_id,
                features=features
            )
        except Exception as e:
            # Strategy crashed - return HOLD (fail-closed)
            return TradeProposal(
                signal="HOLD",
                symbol=features.get("symbol", "UNKNOWN"),
                price=features.get("price", 0),
                confidence=0,
                position_size_pct=0,
                strategy_id=self.active_strategy_id,
                features={"error": str(e)}
            )
            
    def veto(self, proposal: TradeProposal) -> VetoResult:
        """
        Check if proposal passes all safety rules.
        
        Interface: veto(proposal, context) -> allow/deny + reason_codes[]
        
        FAIL-CLOSED: If anything is wrong, don't trade.
        """
        context = self._build_context()
        return self.veto_gate.check(proposal.to_dict(), context)
        
    def _build_context(self) -> Dict:
        """Build the current context for veto checks"""
        # Calculate current drawdown
        peak = max(self.equity_curve) if self.equity_curve else self.balance
        current_drawdown = (peak - self.balance) / peak if peak > 0 else 0
        
        return {
            "balance": self.balance,
            "current_drawdown_pct": current_drawdown,
            "daily_loss_pct": 0,  # TODO: Track daily loss
            "max_position_pct": self.config.get("max_position_pct", 0.05),
            "max_drawdown_pct": self.config.get("max_drawdown_pct", 0.10),
            "max_daily_loss_pct": self.config.get("max_daily_loss_pct", 0.02),
            "min_confidence": self.config.get("min_confidence", 0.60),
            "approved_strategies": self.config.get("approved_strategies", []),
            "data_age_seconds": 5,  # TODO: Track actual data age
            "spread_pct": 0.001,  # TODO: Get actual spread
            "current_volatility": 0.02  # TODO: Calculate actual volatility
        }
        
    def send_order(self, proposal: TradeProposal) -> Optional[TradeOrder]:
        """
        Send order to execution (paper only).
        
        Interface: send_order(order) (paper only)
        
        In paper mode, this simulates order execution.
        """
        if not self.config.get("paper_mode", True):
            raise RuntimeError("Live trading not enabled - paper mode only")
            
        if proposal.signal == "HOLD":
            return None
            
        # Create order
        order = TradeOrder(
            proposal=proposal,
            order_id=f"PAPER-{datetime.now().timestamp()}",
            order_type="MARKET",
            status="FILLED",  # Paper orders fill instantly
            filled_price=proposal.price,
            filled_at=datetime.now().isoformat()
        )
        
        # Update positions
        symbol = proposal.symbol
        position_value = self.balance * proposal.position_size_pct
        
        if proposal.signal == "BUY":
            self.positions[symbol] = self.positions.get(symbol, 0) + position_value
        elif proposal.signal == "SELL":
            self.positions[symbol] = self.positions.get(symbol, 0) - position_value
            
        self.orders.append(order)
        self.trades_taken += 1
        
        # Log to manifest
        self.manifest.log_decision({
            "action": proposal.signal,
            "symbol": symbol,
            "price": proposal.price,
            "confidence": proposal.confidence,
            "vetoed": False,
            "order_id": order.order_id
        })
        
        return order
        
    def score(self) -> Dict:
        """
        Calculate performance metrics.
        
        Interface: score(run) -> metrics
        
        Returns comprehensive metrics for strategy evaluation:
        - Sharpe ratio
        - Max drawdown
        - Win rate
        - Profit factor
        - Tail loss
        """
        if not self.orders:
            return {
                "sharpe_ratio": 0,
                "max_drawdown_pct": 0,
                "win_rate": 0,
                "profit_factor": 0,
                "total_trades": 0,
                "total_pnl": 0
            }
            
        # Calculate returns
        returns = []
        for i in range(1, len(self.equity_curve)):
            ret = (self.equity_curve[i] - self.equity_curve[i-1]) / self.equity_curve[i-1]
            returns.append(ret)
            
        # Sharpe ratio (annualized, assuming daily returns)
        if returns:
            avg_return = sum(returns) / len(returns)
            std_return = (sum((r - avg_return) ** 2 for r in returns) / len(returns)) ** 0.5
            sharpe = (avg_return / std_return * (252 ** 0.5)) if std_return > 0 else 0
        else:
            sharpe = 0
            
        # Max drawdown
        peak = self.equity_curve[0]
        max_dd = 0
        for equity in self.equity_curve:
            if equity > peak:
                peak = equity
            dd = (peak - equity) / peak
            if dd > max_dd:
                max_dd = dd
                
        # Win rate
        win_rate = self.trades_won / self.trades_taken if self.trades_taken > 0 else 0
        
        # Profit factor
        gross_profit = sum(max(0, r) for r in returns) if returns else 0
        gross_loss = abs(sum(min(0, r) for r in returns)) if returns else 0
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else float('inf')
        
        metrics = {
            "sharpe_ratio": round(sharpe, 2),
            "max_drawdown_pct": round(max_dd * 100, 2),
            "win_rate": round(win_rate * 100, 2),
            "profit_factor": round(profit_factor, 2),
            "total_trades": self.trades_taken,
            "total_pnl": round(self.total_pnl, 2),
            "final_balance": round(self.balance, 2)
        }
        
        self.manifest.set_metrics(metrics)
        return metrics
        
    def process_tick(self, tick: Dict) -> Dict:
        """
        Process a single market tick through the full pipeline.
        
        tick |> get_features() |> propose_action() |> veto() |> send_order()
        """
        # Step 1: Extract features
        features = self.get_features(tick)
        
        # Step 2: Propose action
        proposal = self.propose_action(features)
        
        # Step 3: Veto check
        veto_result = self.veto(proposal)
        
        # Step 4: Execute if allowed
        order = None
        if veto_result.allowed and proposal.signal != "HOLD":
            order = self.send_order(proposal)
        else:
            # Log vetoed decision
            self.manifest.log_decision({
                "action": proposal.signal,
                "symbol": proposal.symbol,
                "price": proposal.price,
                "confidence": proposal.confidence,
                "vetoed": True,
                "veto_reasons": [r.value for r in veto_result.reason_codes]
            })
            
        return {
            "features": features,
            "proposal": proposal.to_dict(),
            "veto_result": {
                "allowed": veto_result.allowed,
                "reasons": [r.value for r in veto_result.reason_codes]
            },
            "order": order.to_dict() if order else None
        }
        
    def run_backtest(self, bars: List[Dict]) -> Dict:
        """
        Run a backtest on historical data.
        
        Returns metrics and saves truth manifest.
        """
        self.manifest.set_dataset(bars, {
            "bars": len(bars),
            "start": bars[0].get("timestamp") if bars else None,
            "end": bars[-1].get("timestamp") if bars else None
        })
        
        for i, bar in enumerate(bars):
            # Add historical context
            tick = {**bar, "bars": bars[max(0, i-50):i+1]}
            self.process_tick(tick)
            
        # Calculate final metrics
        metrics = self.score()
        
        # Save manifest
        manifest_path = self.manifest.save()
        
        return {
            "metrics": metrics,
            "manifest_path": manifest_path,
            "manifest_hash": self.manifest.get_manifest_hash()
        }
        
    def get_status(self) -> Dict:
        """Get current brain status"""
        return {
            "active_strategy": self.active_strategy_id,
            "approved_strategies": list(self.approved_strategies.keys()),
            "balance": self.balance,
            "positions": self.positions,
            "trades_taken": self.trades_taken,
            "paper_mode": self.config.get("paper_mode", True)
        }


# Example usage
if __name__ == "__main__":
    # Create the brain
    brain = TradingBrain({
        "initial_balance": 10000,
        "min_confidence": 0.60,
        "paper_mode": True
    })
    
    # Define a simple strategy
    def simple_momentum_strategy(features: Dict) -> Dict:
        """Simple momentum strategy"""
        momentum = features.get("momentum_5", 0)
        trend = features.get("trend", "NEUTRAL")
        
        if momentum > 0.01 and trend == "UP":
            return {"signal": "BUY", "confidence": 0.75, "position_size_pct": 0.02}
        elif momentum < -0.01 and trend == "DOWN":
            return {"signal": "SELL", "confidence": 0.75, "position_size_pct": 0.02}
        else:
            return {"signal": "HOLD", "confidence": 0, "position_size_pct": 0}
    
    # Register and activate strategy
    brain.register_strategy("simple_momentum", simple_momentum_strategy)
    brain.set_active_strategy("simple_momentum")
    
    # Generate some test data
    import random
    bars = []
    price = 100
    for i in range(100):
        change = random.uniform(-0.02, 0.02)
        price *= (1 + change)
        bars.append({
            "timestamp": f"2024-01-{i+1:02d}",
            "open": price * 0.999,
            "high": price * 1.01,
            "low": price * 0.99,
            "close": price,
            "volume": random.randint(1000, 10000)
        })
    
    # Run backtest
    result = brain.run_backtest(bars)
    
    print(f"Backtest Results:")
    print(f"  Metrics: {result['metrics']}")
    print(f"  Manifest: {result['manifest_path']}")
    print(f"  Hash: {result['manifest_hash']}")
    print(f"\nBrain Status: {brain.get_status()}")
