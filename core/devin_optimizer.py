# OMEGA-DEVIN // SELF-OPTIMIZATION KERNEL
# MISSION: ANALYZE LOSSES AND MUTATE STRATEGY
# Combined with our 18 Intelligence Modules for TRUE AGI
# Enhanced with Gemini's "Pain Detection" + Aggression Levels

import json
import os
from datetime import datetime
from typing import Dict, List, Optional, Any

class DevinBrain:
    """
    The DEVIN Brain - Self-Optimizing Trading Intelligence
    
    This is the Meta-Loop that allows the bot to:
    1. Analyze its own performance
    2. Identify losing patterns (including 3-loss streak detection)
    3. Mutate strategy parameters to improve
    4. Learn from mistakes autonomously
    5. Adjust aggression levels based on market conditions
    
    EVOLUTION TRIGGERS:
    - Win rate below 60%
    - Profit factor below 1.5
    - Max drawdown above 10%
    - 3 consecutive losses (PAIN DETECTION)
    """
    
    def __init__(self, logs_dir: str = "logs", strategies_dir: str = "strategies"):
        self.logs_dir = logs_dir
        self.strategies_dir = strategies_dir
        self.performance_log = os.path.join(logs_dir, "trade_history.json")
        self.neural_memory = os.path.join(logs_dir, "neural_memory.json")
        self.strategy_config = os.path.join(strategies_dir, "config.json")
        self.evolution_log = os.path.join(logs_dir, "evolution_history.json")
        
        # Ensure neural memory exists
        self._ensure_memory()
        
        # Performance thresholds
        self.min_win_rate = 0.60  # 60% minimum win rate
        self.min_profit_factor = 1.5  # 1.5 minimum profit factor
        self.max_drawdown = 0.10  # 10% maximum drawdown
        self.consecutive_loss_trigger = 3  # Mutate after 3 losses
        
        # Mutation parameters
        self.mutation_rate = 0.1  # 10% change per mutation
        self.mutation_history = []
    
    def _ensure_memory(self):
        """Ensure neural memory file exists"""
        os.makedirs(self.logs_dir, exist_ok=True)
        if not os.path.exists(self.neural_memory):
            with open(self.neural_memory, 'w') as f:
                json.dump([], f)
    
    def get_synapses(self) -> Dict:
        """Get current DNA/Configuration (Gemini compatibility)"""
        return self.get_current_config()
    
    def store_memory(self, trade_result: Dict):
        """Store trade result in neural memory for learning"""
        try:
            with open(self.neural_memory, 'r') as f:
                history = json.load(f)
            
            trade_result['timestamp'] = datetime.now().isoformat()
            history.append(trade_result)
            
            with open(self.neural_memory, 'w') as f:
                json.dump(history, f, indent=2)
            
            print(f"   [DEVIN]: Memory stored. Total experiences: {len(history)}")
        except Exception as e:
            print(f"   [DEVIN]: Error storing memory: {e}")
    
    def evolve_strategy(self) -> Dict[str, Any]:
        """
        THE GOD ALGORITHM - Check if evolution is needed
        
        Triggers mutation if:
        1. Last 3 trades were all losses (PAIN DETECTION)
        2. Overall performance metrics are below threshold
        """
        print("   [DEVIN]: INITIATING INTROSPECTION PROTOCOL...")
        
        # First check for consecutive losses (fast trigger)
        pain_detected = self._detect_pain()
        if pain_detected:
            print("   [DEVIN]: PAIN DETECTED. INITIATING ADAPTATION PROTOCOL.")
            self._mutate_dna_aggressive()
            return {"status": "pain_mutation", "trigger": "3_consecutive_losses"}
        
        # Then do full performance analysis
        return self.analyze_performance()
        
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
    
    def _detect_pain(self) -> bool:
        """
        PAIN DETECTION - Check if last 3 trades were all losses
        This is the fast trigger for immediate adaptation
        """
        try:
            if not os.path.exists(self.neural_memory):
                return False
            
            with open(self.neural_memory, 'r') as f:
                history = json.load(f)
            
            if len(history) < self.consecutive_loss_trigger:
                return False
            
            # Check last N trades
            recent_pnl = [t.get('pnl', 0) for t in history[-self.consecutive_loss_trigger:]]
            
            # If all recent trades are losses, pain is detected
            if all(p < 0 for p in recent_pnl):
                print(f"   [DEVIN]: CONSECUTIVE LOSSES DETECTED: {recent_pnl}")
                return True
            
            return False
            
        except Exception as e:
            print(f"   [DEVIN]: Error in pain detection: {e}")
            return False
    
    def _mutate_dna_aggressive(self):
        """
        AGGRESSIVE MUTATION - Called when pain is detected
        
        This is more aggressive than normal mutation:
        1. Lower risk by 20% (defense mode)
        2. Decrease aggression level (sniper mode)
        3. Tighten entry requirements
        """
        print("   [DEVIN]: INITIATING AGGRESSIVE DNA MUTATION...")
        
        try:
            config = self.get_current_config()
            original_config = json.loads(json.dumps(config))
            
            risk_mgmt = config.get('risk_management', {})
            strategy = config.get('strategy_settings', {})
            
            # 1. DEFENSE MODE - Lower risk by 20%
            current_risk = risk_mgmt.get('stop_loss_pct', 0.01)
            new_risk = max(0.005, current_risk * 0.8)
            risk_mgmt['stop_loss_pct'] = round(new_risk, 4)
            print(f"   [DEVIN]: DEFENSE MODE - Risk: {current_risk:.4f} -> {new_risk:.4f}")
            
            # 2. SNIPER MODE - Decrease aggression level
            current_aggression = strategy.get('aggression_level', 5)
            new_aggression = max(1, current_aggression - 1)
            strategy['aggression_level'] = new_aggression
            print(f"   [DEVIN]: SNIPER MODE - Aggression: {current_aggression} -> {new_aggression}")
            
            # 3. HIGH-PRECISION MODE - If aggression is very low
            if new_aggression < 3:
                print("   [DEVIN]: SHIFTING TO HIGH-PRECISION MODE.")
                strategy['min_confluence'] = min(8, strategy.get('min_confluence', 4) + 1)
                strategy['min_confidence'] = min(0.85, strategy.get('min_confidence', 0.65) + 0.05)
            
            config['risk_management'] = risk_mgmt
            config['strategy_settings'] = strategy
            
            # Save mutated config
            os.makedirs(os.path.dirname(self.strategy_config), exist_ok=True)
            with open(self.strategy_config, 'w') as f:
                json.dump(config, f, indent=4)
            
            # Log evolution
            evolution_entry = {
                "timestamp": datetime.now().isoformat(),
                "trigger": "pain_detection",
                "reason": "3 consecutive losses",
                "original_config": original_config,
                "new_config": config
            }
            self._log_evolution(evolution_entry)
            
            print(f"   [DEVIN]: DNA MUTATION COMPLETE. NEW AGGRESSION LEVEL: {new_aggression}")
            
        except Exception as e:
            print(f"   [DEVIN]: Error in aggressive mutation: {e}")
    
    def _create_default_config(self) -> Dict:
        """Create default strategy configuration with aggression levels"""
        return {
            "symbol": "EURUSD",
            "timeframe": "1h",
            "risk_management": {
                "risk_pct": 0.02,
                "stop_loss_pct": 0.01,
                "take_profit_pct": 0.02,
                "max_drawdown_daily": 0.03,
                "position_size_pct": 0.02,
                "max_positions": 3
            },
            "strategy_settings": {
                "aggression_level": 5,
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
            },
            "pairs": ["EURUSD", "GBPUSD", "USDJPY", "XAUUSD"]
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
    
    def adjust_neuroplasticity(self, sentiment_score: float):
        """
        NEUROPLASTICITY - The Brain rewrites Config based on Market Sentiment
        
        This is the AGI adaptation layer that responds to market emotion:
        - FEAR (score < -0.5): Deploy shields, SHORT only, tight risk
        - GREED (score > 0.5): Hunter mode, LONG only, loose risk
        - NEUTRAL: Omni-directional trading allowed
        
        Args:
            sentiment_score: float from -1.0 (extreme fear) to +1.0 (extreme greed)
        """
        print(f"   [AGI]: NEUROPLASTICITY ENGAGED. SENTIMENT: {sentiment_score:.3f}")
        
        try:
            config = self.get_current_config()
            original_config = json.loads(json.dumps(config))
            
            risk_mgmt = config.get('risk_management', {})
            strategy = config.get('strategy_settings', {})
            
            # FEAR DETECTED - Deploy defensive shields
            if sentiment_score < -0.5:
                print("   [AGI]: FEAR DETECTED IN MARKET. DEPLOYING SHIELDS.")
                risk_mgmt['max_drawdown_daily'] = 0.01  # Tighten leash to 1%
                strategy['direction'] = "SHORT"
                strategy['aggression_level'] = max(1, strategy.get('aggression_level', 5) - 2)
                
            # GREED DETECTED - Activate hunter mode
            elif sentiment_score > 0.5:
                print("   [AGI]: GREED DETECTED. ACTIVATING HUNTER MODE.")
                risk_mgmt['max_drawdown_daily'] = 0.05  # Loosen leash to 5%
                strategy['direction'] = "LONG"
                strategy['aggression_level'] = min(10, strategy.get('aggression_level', 5) + 1)
                
            # NEUTRAL - Omni-directional
            else:
                print("   [AGI]: NEUTRAL SENTIMENT. OMNI-DIRECTIONAL MODE.")
                risk_mgmt['max_drawdown_daily'] = 0.03  # Standard 3%
                strategy['direction'] = "OMNI"
            
            config['risk_management'] = risk_mgmt
            config['strategy_settings'] = strategy
            
            # Save adapted config
            os.makedirs(os.path.dirname(self.strategy_config), exist_ok=True)
            with open(self.strategy_config, 'w') as f:
                json.dump(config, f, indent=4)
            
            # Log the neuroplasticity event
            evolution_entry = {
                "timestamp": datetime.now().isoformat(),
                "trigger": "neuroplasticity",
                "sentiment_score": sentiment_score,
                "direction": strategy.get('direction', 'OMNI'),
                "original_config": original_config,
                "new_config": config
            }
            self._log_evolution(evolution_entry)
            
            print(f"   [AGI]: ADAPTATION COMPLETE. DIRECTION: {strategy.get('direction', 'OMNI')}")
            
        except Exception as e:
            print(f"   [AGI]: Error in neuroplasticity: {e}")
    
    def pleasure_response(self, metrics: Dict):
        """
        PLEASURE RESPONSE - Called when performance is excellent
        
        If Win Rate > 70% over last 10 trades:
        - Increase position size by 10% (compound gains)
        - Loosen take profit targets
        - Increase aggression level
        """
        print("   [AGI]: PLEASURE DETECTED. COMPOUNDING GAINS.")
        
        try:
            config = self.get_current_config()
            risk_mgmt = config.get('risk_management', {})
            strategy = config.get('strategy_settings', {})
            
            # Increase position size by 10%
            current_size = risk_mgmt.get('position_size_pct', 0.02)
            new_size = min(0.05, current_size * 1.1)  # Cap at 5%
            risk_mgmt['position_size_pct'] = round(new_size, 4)
            
            # Loosen take profit
            current_tp = risk_mgmt.get('take_profit_pct', 0.02)
            new_tp = min(0.06, current_tp * 1.1)
            risk_mgmt['take_profit_pct'] = round(new_tp, 4)
            
            # Increase aggression
            current_aggression = strategy.get('aggression_level', 5)
            new_aggression = min(10, current_aggression + 1)
            strategy['aggression_level'] = new_aggression
            
            config['risk_management'] = risk_mgmt
            config['strategy_settings'] = strategy
            
            with open(self.strategy_config, 'w') as f:
                json.dump(config, f, indent=4)
            
            print(f"   [AGI]: POSITION SIZE: {current_size:.4f} -> {new_size:.4f}")
            print(f"   [AGI]: AGGRESSION: {current_aggression} -> {new_aggression}")
            
        except Exception as e:
            print(f"   [AGI]: Error in pleasure response: {e}")


# Test the brain
if __name__ == "__main__":
    brain = DevinBrain()
    result = brain.analyze_performance()
    print(f"\nResult: {result}")
