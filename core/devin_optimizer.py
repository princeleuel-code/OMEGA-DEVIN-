# OMEGA-DEVIN // SELF-OPTIMIZATION KERNEL
# MISSION: ANALYZE LOSSES AND MUTATE STRATEGY
# Combined with our 18 Intelligence Modules for TRUE AGI

import json
import os
from datetime import datetime
from typing import Dict, List, Optional, Any

class DevinBrain:
    """
    The DEVIN Brain - Self-Optimizing Trading Intelligence
    
    This is the Meta-Loop that allows the bot to:
    1. Analyze its own performance
    2. Identify losing patterns
    3. Mutate strategy parameters to improve
    4. Learn from mistakes autonomously
    """
    
    def __init__(self, logs_dir: str = "logs", strategies_dir: str = "strategies"):
        self.logs_dir = logs_dir
        self.strategies_dir = strategies_dir
        self.performance_log = os.path.join(logs_dir, "trade_history.json")
        self.strategy_config = os.path.join(strategies_dir, "config.json")
        self.evolution_log = os.path.join(logs_dir, "evolution_history.json")
        
        # Performance thresholds
        self.min_win_rate = 0.60  # 60% minimum win rate
        self.min_profit_factor = 1.5  # 1.5 minimum profit factor
        self.max_drawdown = 0.10  # 10% maximum drawdown
        
        # Mutation parameters
        self.mutation_rate = 0.1  # 10% change per mutation
        self.mutation_history = []
        
    def analyze_performance(self) -> Dict[str, Any]:
        """
        Analyze trading performance and determine if mutation is needed
        """
        print("   [DEVIN]: AUDITING TRADE HISTORY...")
        
        try:
            if not os.path.exists(self.performance_log):
                print("   [DEVIN]: NO DATA FOUND. AWAITING MARKET INPUT.")
                return {"status": "no_data", "action": "wait"}
            
            with open(self.performance_log, 'r') as f:
                trades = json.load(f)
            
            if not trades:
                print("   [DEVIN]: EMPTY TRADE LOG. AWAITING MARKET INPUT.")
                return {"status": "no_data", "action": "wait"}
            
            # Calculate metrics
            total_trades = len(trades)
            wins = [t for t in trades if t.get('pnl', 0) > 0]
            losses = [t for t in trades if t.get('pnl', 0) <= 0]
            
            win_rate = len(wins) / total_trades if total_trades > 0 else 0
            
            total_profit = sum(t.get('pnl', 0) for t in wins)
            total_loss = abs(sum(t.get('pnl', 0) for t in losses))
            profit_factor = total_profit / total_loss if total_loss > 0 else float('inf')
            
            # Calculate drawdown
            equity_curve = []
            running_equity = 10000  # Starting capital
            peak_equity = running_equity
            max_dd = 0
            
            for trade in trades:
                running_equity += trade.get('pnl', 0)
                equity_curve.append(running_equity)
                peak_equity = max(peak_equity, running_equity)
                dd = (peak_equity - running_equity) / peak_equity
                max_dd = max(max_dd, dd)
            
            metrics = {
                "total_trades": total_trades,
                "wins": len(wins),
                "losses": len(losses),
                "win_rate": win_rate,
                "profit_factor": profit_factor,
                "max_drawdown": max_dd,
                "total_pnl": sum(t.get('pnl', 0) for t in trades),
                "final_equity": running_equity
            }
            
            print(f"   [DEVIN]: PERFORMANCE METRICS:")
            print(f"            Total Trades: {total_trades}")
            print(f"            Win Rate: {win_rate:.2%}")
            print(f"            Profit Factor: {profit_factor:.2f}")
            print(f"            Max Drawdown: {max_dd:.2%}")
            
            # Determine if mutation is needed
            needs_mutation = False
            mutation_reasons = []
            
            if win_rate < self.min_win_rate:
                needs_mutation = True
                mutation_reasons.append(f"Win rate {win_rate:.2%} below threshold {self.min_win_rate:.2%}")
            
            if profit_factor < self.min_profit_factor:
                needs_mutation = True
                mutation_reasons.append(f"Profit factor {profit_factor:.2f} below threshold {self.min_profit_factor}")
            
            if max_dd > self.max_drawdown:
                needs_mutation = True
                mutation_reasons.append(f"Max drawdown {max_dd:.2%} above threshold {self.max_drawdown:.2%}")
            
            if needs_mutation:
                print("   [DEVIN]: PERFORMANCE BELOW THRESHOLD. INITIATING MUTATION.")
                for reason in mutation_reasons:
                    print(f"            - {reason}")
                self.mutate_parameters(metrics, mutation_reasons)
                return {"status": "mutated", "metrics": metrics, "reasons": mutation_reasons}
            else:
                print("   [DEVIN]: SYSTEM STABLE. MAINTAINING VECTOR.")
                return {"status": "stable", "metrics": metrics}
                
        except Exception as e:
            print(f"   [DEVIN]: ERROR ANALYZING PERFORMANCE: {e}")
            return {"status": "error", "error": str(e)}
    
    def mutate_parameters(self, metrics: Dict, reasons: List[str]):
        """
        Mutate strategy parameters based on performance analysis
        """
        print("   [DEVIN]: REWRITING CONFIGURATION...")
        
        try:
            if not os.path.exists(self.strategy_config):
                print("   [DEVIN]: NO CONFIG FOUND. CREATING DEFAULT.")
                config = self._create_default_config()
            else:
                with open(self.strategy_config, 'r') as f:
                    config = json.load(f)
            
            # Store original values
            original_config = json.loads(json.dumps(config))
            
            # Mutation Logic based on specific issues
            risk_mgmt = config.get('risk_management', {})
            
            # If win rate is low, tighten stop loss and widen take profit
            if metrics['win_rate'] < self.min_win_rate:
                current_stop = risk_mgmt.get('stop_loss_pct', 0.01)
                new_stop = max(0.005, current_stop * (1 - self.mutation_rate))
                risk_mgmt['stop_loss_pct'] = round(new_stop, 4)
                
                current_tp = risk_mgmt.get('take_profit_pct', 0.02)
                new_tp = min(0.05, current_tp * (1 + self.mutation_rate))
                risk_mgmt['take_profit_pct'] = round(new_tp, 4)
                
                print(f"   [DEVIN]: TIGHTENED STOP LOSS: {current_stop:.4f} -> {new_stop:.4f}")
                print(f"   [DEVIN]: WIDENED TAKE PROFIT: {current_tp:.4f} -> {new_tp:.4f}")
            
            # If drawdown is high, reduce position size
            if metrics['max_drawdown'] > self.max_drawdown:
                current_size = risk_mgmt.get('position_size_pct', 0.02)
                new_size = max(0.005, current_size * (1 - self.mutation_rate * 2))
                risk_mgmt['position_size_pct'] = round(new_size, 4)
                print(f"   [DEVIN]: REDUCED POSITION SIZE: {current_size:.4f} -> {new_size:.4f}")
            
            # If profit factor is low, increase confluence requirement
            if metrics['profit_factor'] < self.min_profit_factor:
                strategy = config.get('strategy_settings', {})
                current_confluence = strategy.get('min_confluence', 3)
                new_confluence = min(8, current_confluence + 1)
                strategy['min_confluence'] = new_confluence
                config['strategy_settings'] = strategy
                print(f"   [DEVIN]: INCREASED CONFLUENCE REQ: {current_confluence} -> {new_confluence}")
            
            config['risk_management'] = risk_mgmt
            
            # Save updated config
            os.makedirs(os.path.dirname(self.strategy_config), exist_ok=True)
            with open(self.strategy_config, 'w') as f:
                json.dump(config, f, indent=4)
            
            # Log the evolution
            evolution_entry = {
                "timestamp": datetime.now().isoformat(),
                "metrics_before": metrics,
                "reasons": reasons,
                "original_config": original_config,
                "new_config": config
            }
            self._log_evolution(evolution_entry)
            
            print("   [DEVIN]: EVOLUTION COMPLETE.")
            
        except Exception as e:
            print(f"   [DEVIN]: ERROR MUTATING PARAMETERS: {e}")
    
    def _create_default_config(self) -> Dict:
        """Create default strategy configuration"""
        return {
            "symbol": "EURUSD",
            "timeframe": "1h",
            "risk_management": {
                "stop_loss_pct": 0.01,
                "take_profit_pct": 0.02,
                "max_drawdown_daily": 0.03,
                "position_size_pct": 0.02,
                "max_positions": 3
            },
            "strategy_settings": {
                "liquidity_lookback": 20,
                "volume_threshold": 1000000,
                "min_confluence": 4,
                "min_confidence": 0.65
            },
            "intelligence_weights": {
                "smc": 0.15,
                "volume_profile": 0.15,
                "delta_flow": 0.12,
                "order_flow": 0.12,
                "structure": 0.10,
                "institutional": 0.10,
                "footprint": 0.08,
                "session": 0.08,
                "vwap": 0.05,
                "absorption": 0.05
            }
        }
    
    def _log_evolution(self, entry: Dict):
        """Log evolution history"""
        try:
            os.makedirs(os.path.dirname(self.evolution_log), exist_ok=True)
            
            if os.path.exists(self.evolution_log):
                with open(self.evolution_log, 'r') as f:
                    history = json.load(f)
            else:
                history = []
            
            history.append(entry)
            
            with open(self.evolution_log, 'w') as f:
                json.dump(history, f, indent=2)
                
        except Exception as e:
            print(f"   [DEVIN]: ERROR LOGGING EVOLUTION: {e}")
    
    def get_current_config(self) -> Dict:
        """Get current strategy configuration"""
        if os.path.exists(self.strategy_config):
            with open(self.strategy_config, 'r') as f:
                return json.load(f)
        return self._create_default_config()
    
    def get_evolution_history(self) -> List[Dict]:
        """Get evolution history"""
        if os.path.exists(self.evolution_log):
            with open(self.evolution_log, 'r') as f:
                return json.load(f)
        return []


# Test the brain
if __name__ == "__main__":
    brain = DevinBrain()
    result = brain.analyze_performance()
    print(f"\nResult: {result}")
