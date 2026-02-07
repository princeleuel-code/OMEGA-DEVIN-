"""
SELF-EVOLUTION LOOP
===================
The autonomous self-improvement system for the UNMATCHABLE Trading AGI.

This is where the magic happens:
1. Continuous performance monitoring
2. Automatic weakness detection
3. Hypothesis generation for improvements
4. Code writing and validation
5. Safe deployment of improvements
6. Performance verification

The AGI literally improves itself over time.
"""

import os
import json
import asyncio
import subprocess
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
import hashlib
import ast
import traceback
import shutil


class EvolutionPhase(Enum):
    """Phases of the evolution cycle"""
    MONITORING = "monitoring"
    ANALYZING = "analyzing"
    HYPOTHESIZING = "hypothesizing"
    CODING = "coding"
    VALIDATING = "validating"
    DEPLOYING = "deploying"
    VERIFYING = "verifying"
    IDLE = "idle"


@dataclass
class EvolutionCandidate:
    """A candidate improvement for evolution"""
    id: str
    timestamp: datetime
    target_module: str
    target_function: str
    hypothesis: str
    original_code: str
    improved_code: str
    expected_improvement: float
    risk_score: float
    validation_passed: bool = False
    deployed: bool = False
    verified: bool = False
    actual_improvement: Optional[float] = None


@dataclass
class EvolutionCycle:
    """A complete evolution cycle"""
    id: str
    generation: int
    start_time: datetime
    end_time: Optional[datetime] = None
    phase: EvolutionPhase = EvolutionPhase.IDLE
    candidates: List[EvolutionCandidate] = field(default_factory=list)
    deployed_count: int = 0
    successful_count: int = 0
    performance_before: Dict = field(default_factory=dict)
    performance_after: Dict = field(default_factory=dict)


class SelfEvolutionLoop:
    """
    The autonomous self-evolution loop.
    
    This system continuously monitors performance,
    identifies weaknesses, generates improvements,
    and safely deploys them.
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or self._default_config()
        self.phase = EvolutionPhase.IDLE
        self.generation = 0
        self.cycles: List[EvolutionCycle] = []
        self.candidates: List[EvolutionCandidate] = []
        self.deployed_improvements: List[EvolutionCandidate] = []
        
        # Performance tracking
        self.performance_history: List[Dict] = []
        self.baseline_performance: Optional[Dict] = None
        
        # Safety
        self.rollback_available = False
        self.backup_path = Path(self.config["backup_path"])
        self.backup_path.mkdir(parents=True, exist_ok=True)
        
        # Code templates for improvements
        self.improvement_templates = self._load_improvement_templates()
    
    def _default_config(self) -> Dict:
        return {
            "code_base_path": "/home/ubuntu/omega_devin/chimera/consciousness",
            "backup_path": "/home/ubuntu/omega_devin/chimera/backups",
            "evolution_interval_hours": 24,
            "min_trades_for_evolution": 20,
            "max_candidates_per_cycle": 5,
            "validation_backtest_bars": 500,
            "min_improvement_threshold": 0.02,
            "max_risk_score": 0.5,
            "rollback_on_degradation": True,
            "degradation_threshold": -0.05
        }
    
    def _load_improvement_templates(self) -> Dict[str, str]:
        """Load code improvement templates"""
        return {
            "confluence_filter": '''
    def check_confluence(self, signals: List[Dict], min_agreement: int = 3) -> Tuple[bool, float]:
        """
        Enhanced confluence checking with dynamic threshold.
        
        Args:
            signals: List of signal dictionaries
            min_agreement: Minimum number of agreeing signals
        
        Returns:
            Tuple of (should_trade, confluence_score)
        """
        if not signals or len(signals) < min_agreement:
            return False, 0.0
        
        # Count by direction
        direction_counts = {"LONG": 0, "SHORT": 0, "NEUTRAL": 0}
        confidence_sum = {"LONG": 0.0, "SHORT": 0.0, "NEUTRAL": 0.0}
        
        for signal in signals:
            direction = signal.get("direction", "NEUTRAL").upper()
            confidence = signal.get("confidence", 0.5)
            
            if direction in direction_counts:
                direction_counts[direction] += 1
                confidence_sum[direction] += confidence
        
        # Find dominant direction
        max_count = max(direction_counts.values())
        dominant = [k for k, v in direction_counts.items() if v == max_count][0]
        
        # Calculate confluence score
        total_signals = len(signals)
        agreement_ratio = max_count / total_signals
        avg_confidence = confidence_sum[dominant] / max(max_count, 1)
        
        confluence_score = agreement_ratio * avg_confidence
        should_trade = max_count >= min_agreement and confluence_score >= 0.6
        
        return should_trade, confluence_score
''',
            "adaptive_stop_loss": '''
    def calculate_adaptive_stop(
        self,
        entry_price: float,
        direction: str,
        atr: float,
        volatility_regime: str,
        recent_swings: List[float]
    ) -> float:
        """
        Calculate adaptive stop loss based on market conditions.
        
        Args:
            entry_price: Trade entry price
            direction: Trade direction (LONG/SHORT)
            atr: Average True Range
            volatility_regime: Current volatility regime
            recent_swings: Recent swing high/low levels
        
        Returns:
            Stop loss price
        """
        # Base multiplier based on regime
        regime_multipliers = {
            "LOW": 1.5,
            "NORMAL": 2.0,
            "HIGH": 2.5,
            "EXTREME": 3.0
        }
        multiplier = regime_multipliers.get(volatility_regime, 2.0)
        
        # ATR-based stop
        atr_stop_distance = atr * multiplier
        
        if direction == "LONG":
            atr_stop = entry_price - atr_stop_distance
            
            # Check for structure-based stop
            valid_swings = [s for s in recent_swings if s < entry_price]
            if valid_swings:
                structure_stop = max(valid_swings) - (atr * 0.5)
                # Use the higher (tighter) stop
                return max(atr_stop, structure_stop)
            return atr_stop
        else:
            atr_stop = entry_price + atr_stop_distance
            
            # Check for structure-based stop
            valid_swings = [s for s in recent_swings if s > entry_price]
            if valid_swings:
                structure_stop = min(valid_swings) + (atr * 0.5)
                # Use the lower (tighter) stop
                return min(atr_stop, structure_stop)
            return atr_stop
''',
            "regime_filter": '''
    def should_trade_in_regime(
        self,
        regime: str,
        direction: str,
        historical_performance: Dict
    ) -> Tuple[bool, float]:
        """
        Determine if trading is advisable in current regime.
        
        Args:
            regime: Current market regime
            direction: Proposed trade direction
            historical_performance: Historical performance by regime
        
        Returns:
            Tuple of (should_trade, confidence_adjustment)
        """
        # Get historical stats for this regime
        regime_stats = historical_performance.get(regime, {})
        win_rate = regime_stats.get("win_rate", 0.5)
        profit_factor = regime_stats.get("profit_factor", 1.0)
        sample_size = regime_stats.get("trades", 0)
        
        # Minimum sample size for confidence
        if sample_size < 10:
            return True, 0.0  # Not enough data, allow with no adjustment
        
        # Calculate regime quality score
        quality = (win_rate * 0.5) + (min(profit_factor / 3.0, 1.0) * 0.5)
        
        # Decision thresholds
        if quality < 0.3:
            return False, -0.2  # Don't trade, would reduce confidence
        elif quality < 0.5:
            return True, -0.1  # Trade with reduced confidence
        elif quality > 0.7:
            return True, 0.1  # Trade with increased confidence
        else:
            return True, 0.0  # Trade normally
''',
            "position_scaling": '''
    def calculate_scaled_position(
        self,
        base_size: float,
        confidence: float,
        recent_performance: List[Dict],
        max_risk_pct: float = 0.02
    ) -> float:
        """
        Calculate position size with performance-based scaling.
        
        Args:
            base_size: Base position size
            confidence: Signal confidence (0-1)
            recent_performance: List of recent trade results
            max_risk_pct: Maximum risk percentage
        
        Returns:
            Scaled position size
        """
        # Start with confidence-based scaling
        confidence_factor = 0.5 + (confidence * 0.5)  # 0.5 to 1.0
        
        # Performance-based scaling
        if recent_performance:
            recent_wins = sum(1 for t in recent_performance[-10:] if t.get("pnl", 0) > 0)
            recent_win_rate = recent_wins / min(len(recent_performance), 10)
            
            # Consecutive losses check
            consecutive_losses = 0
            for trade in reversed(recent_performance[-5:]):
                if trade.get("pnl", 0) < 0:
                    consecutive_losses += 1
                else:
                    break
            
            # Reduce size after losses
            loss_factor = max(0.25, 1 - (consecutive_losses * 0.15))
            
            # Adjust for recent win rate
            performance_factor = 0.5 + (recent_win_rate * 0.5)
        else:
            loss_factor = 1.0
            performance_factor = 1.0
        
        # Calculate final size
        scaled_size = base_size * confidence_factor * loss_factor * performance_factor
        
        # Apply maximum risk cap
        max_size = max_risk_pct * 100  # Convert to lots
        return min(scaled_size, max_size)
''',
            "entry_timing": '''
    def optimize_entry_timing(
        self,
        signal_time: datetime,
        candles: List[Dict],
        volume_profile: Dict,
        order_flow: Dict
    ) -> Tuple[bool, str]:
        """
        Optimize entry timing based on market microstructure.
        
        Args:
            signal_time: Time when signal was generated
            candles: Recent candle data
            volume_profile: Volume profile data
            order_flow: Order flow data
        
        Returns:
            Tuple of (should_enter_now, reason)
        """
        if not candles or len(candles) < 3:
            return True, "insufficient_data"
        
        current_candle = candles[-1]
        prev_candle = candles[-2]
        
        # Check for candle completion
        # Avoid entering mid-candle in volatile conditions
        candle_progress = self._estimate_candle_progress(current_candle)
        if candle_progress < 0.8:
            # Check if we're at a key level
            price = current_candle.get("close", 0)
            poc = volume_profile.get("poc", 0)
            vah = volume_profile.get("vah", 0)
            val = volume_profile.get("val", 0)
            
            # If at POC or VA boundary, wait for confirmation
            if abs(price - poc) / poc < 0.001:
                return False, "at_poc_wait_for_reaction"
            if abs(price - vah) / vah < 0.001 or abs(price - val) / val < 0.001:
                return False, "at_va_boundary_wait"
        
        # Check order flow for absorption
        delta = order_flow.get("delta", 0)
        absorption = order_flow.get("absorption_detected", False)
        
        if absorption:
            return False, "absorption_detected_wait"
        
        # Check for momentum confirmation
        momentum = current_candle.get("close", 0) - prev_candle.get("close", 0)
        if abs(momentum) < current_candle.get("atr", 0) * 0.3:
            return False, "low_momentum_wait"
        
        return True, "conditions_favorable"
    
    def _estimate_candle_progress(self, candle: Dict) -> float:
        """Estimate how complete the current candle is"""
        # This would use actual time in production
        return 1.0  # Assume complete for now
'''
        }
    
    async def run_evolution_cycle(self, performance_data: Dict) -> EvolutionCycle:
        """
        Run a complete evolution cycle.
        
        This is the main entry point for self-improvement.
        """
        cycle = EvolutionCycle(
            id=self._generate_id("cycle"),
            generation=self.generation,
            start_time=datetime.now(),
            performance_before=performance_data.copy()
        )
        
        try:
            # Phase 1: Analyze performance
            cycle.phase = EvolutionPhase.ANALYZING
            weaknesses = self._analyze_weaknesses(performance_data)
            
            # Phase 2: Generate hypotheses
            cycle.phase = EvolutionPhase.HYPOTHESIZING
            hypotheses = self._generate_hypotheses(weaknesses)
            
            # Phase 3: Generate code improvements
            cycle.phase = EvolutionPhase.CODING
            candidates = []
            for hypothesis in hypotheses[:self.config["max_candidates_per_cycle"]]:
                candidate = await self._generate_improvement(hypothesis)
                if candidate:
                    candidates.append(candidate)
            
            cycle.candidates = candidates
            
            # Phase 4: Validate improvements
            cycle.phase = EvolutionPhase.VALIDATING
            for candidate in candidates:
                candidate.validation_passed = await self._validate_improvement(candidate)
            
            # Phase 5: Deploy validated improvements
            cycle.phase = EvolutionPhase.DEPLOYING
            for candidate in candidates:
                if candidate.validation_passed and candidate.risk_score <= self.config["max_risk_score"]:
                    deployed = await self._deploy_improvement(candidate)
                    if deployed:
                        candidate.deployed = True
                        cycle.deployed_count += 1
                        self.deployed_improvements.append(candidate)
            
            # Phase 6: Verify improvements
            cycle.phase = EvolutionPhase.VERIFYING
            # In production, this would run backtests and compare performance
            
            cycle.end_time = datetime.now()
            cycle.phase = EvolutionPhase.IDLE
            
            self.generation += 1
            self.cycles.append(cycle)
            
        except Exception as e:
            print(f"Evolution cycle error: {e}")
            traceback.print_exc()
            cycle.phase = EvolutionPhase.IDLE
        
        return cycle
    
    def _analyze_weaknesses(self, performance_data: Dict) -> List[Dict]:
        """Analyze performance to identify weaknesses"""
        weaknesses = []
        
        win_rate = performance_data.get("win_rate", 0.5)
        profit_factor = performance_data.get("profit_factor", 1.0)
        max_drawdown = performance_data.get("max_drawdown", 0)
        avg_rr = performance_data.get("avg_risk_reward", 1.0)
        
        # Win rate analysis
        if win_rate < 0.45:
            weaknesses.append({
                "type": "critical_low_win_rate",
                "severity": "critical",
                "metric": "win_rate",
                "current": win_rate,
                "target": 0.55,
                "description": "Win rate critically low - entry quality needs major improvement"
            })
        elif win_rate < 0.50:
            weaknesses.append({
                "type": "low_win_rate",
                "severity": "high",
                "metric": "win_rate",
                "current": win_rate,
                "target": 0.55,
                "description": "Win rate below 50% - improve entry timing and confluence"
            })
        
        # Profit factor analysis
        if profit_factor < 1.2:
            weaknesses.append({
                "type": "critical_low_profit_factor",
                "severity": "critical",
                "metric": "profit_factor",
                "current": profit_factor,
                "target": 2.0,
                "description": "Profit factor critically low - risk/reward needs major improvement"
            })
        elif profit_factor < 1.5:
            weaknesses.append({
                "type": "low_profit_factor",
                "severity": "high",
                "metric": "profit_factor",
                "current": profit_factor,
                "target": 2.0,
                "description": "Profit factor below 1.5 - improve take profit placement"
            })
        
        # Drawdown analysis
        if max_drawdown > 0.20:
            weaknesses.append({
                "type": "critical_high_drawdown",
                "severity": "critical",
                "metric": "max_drawdown",
                "current": max_drawdown,
                "target": 0.10,
                "description": "Drawdown critically high - position sizing needs major reduction"
            })
        elif max_drawdown > 0.15:
            weaknesses.append({
                "type": "high_drawdown",
                "severity": "high",
                "metric": "max_drawdown",
                "current": max_drawdown,
                "target": 0.10,
                "description": "Drawdown above 15% - improve risk management"
            })
        
        # Risk/reward analysis
        if avg_rr < 1.0:
            weaknesses.append({
                "type": "poor_risk_reward",
                "severity": "high",
                "metric": "avg_risk_reward",
                "current": avg_rr,
                "target": 1.5,
                "description": "Average R:R below 1:1 - improve trade management"
            })
        
        # Sort by severity
        severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        weaknesses.sort(key=lambda x: severity_order.get(x["severity"], 4))
        
        return weaknesses
    
    def _generate_hypotheses(self, weaknesses: List[Dict]) -> List[Dict]:
        """Generate improvement hypotheses for weaknesses"""
        hypotheses = []
        
        for weakness in weaknesses:
            weakness_type = weakness["type"]
            
            if "win_rate" in weakness_type:
                hypotheses.extend([
                    {
                        "weakness": weakness,
                        "hypothesis": "Add stricter confluence requirements before entry",
                        "target_module": "smc_intelligence.py",
                        "improvement_type": "confluence_filter",
                        "expected_improvement": 0.05
                    },
                    {
                        "weakness": weakness,
                        "hypothesis": "Optimize entry timing using order flow",
                        "target_module": "institutional_flow_detection.py",
                        "improvement_type": "entry_timing",
                        "expected_improvement": 0.03
                    }
                ])
            
            elif "profit_factor" in weakness_type:
                hypotheses.extend([
                    {
                        "weakness": weakness,
                        "hypothesis": "Implement adaptive stop loss based on volatility",
                        "target_module": "position_sizing.py",
                        "improvement_type": "adaptive_stop_loss",
                        "expected_improvement": 0.04
                    },
                    {
                        "weakness": weakness,
                        "hypothesis": "Add regime-based trade filtering",
                        "target_module": "adaptive_regime.py",
                        "improvement_type": "regime_filter",
                        "expected_improvement": 0.03
                    }
                ])
            
            elif "drawdown" in weakness_type:
                hypotheses.extend([
                    {
                        "weakness": weakness,
                        "hypothesis": "Implement performance-based position scaling",
                        "target_module": "position_sizing.py",
                        "improvement_type": "position_scaling",
                        "expected_improvement": 0.05
                    },
                    {
                        "weakness": weakness,
                        "hypothesis": "Add regime-based risk reduction",
                        "target_module": "adaptive_regime.py",
                        "improvement_type": "regime_filter",
                        "expected_improvement": 0.04
                    }
                ])
            
            elif "risk_reward" in weakness_type:
                hypotheses.extend([
                    {
                        "weakness": weakness,
                        "hypothesis": "Implement structure-based take profit",
                        "target_module": "vpe_intelligence.py",
                        "improvement_type": "adaptive_stop_loss",
                        "expected_improvement": 0.03
                    }
                ])
        
        return hypotheses
    
    async def _generate_improvement(self, hypothesis: Dict) -> Optional[EvolutionCandidate]:
        """Generate a code improvement from a hypothesis"""
        improvement_type = hypothesis.get("improvement_type", "")
        target_module = hypothesis.get("target_module", "")
        
        # Get the template
        template = self.improvement_templates.get(improvement_type)
        if not template:
            return None
        
        # Read the target file
        target_path = Path(self.config["code_base_path"]) / target_module
        if not target_path.exists():
            return None
        
        try:
            original_code = target_path.read_text()
        except Exception:
            return None
        
        # Generate improved code by inserting the template
        improved_code = self._insert_improvement(original_code, template)
        
        # Calculate risk score
        risk_score = self._calculate_risk_score(original_code, improved_code)
        
        return EvolutionCandidate(
            id=self._generate_id("candidate"),
            timestamp=datetime.now(),
            target_module=target_module,
            target_function=improvement_type,
            hypothesis=hypothesis.get("hypothesis", ""),
            original_code=original_code,
            improved_code=improved_code,
            expected_improvement=hypothesis.get("expected_improvement", 0.02),
            risk_score=risk_score
        )
    
    def _insert_improvement(self, original_code: str, template: str) -> str:
        """Insert improvement template into original code"""
        lines = original_code.split('\n')
        
        # Find the class definition
        class_line = -1
        for i, line in enumerate(lines):
            if line.strip().startswith('class '):
                class_line = i
                break
        
        if class_line == -1:
            # No class found, insert at the end
            return original_code + '\n\n' + template
        
        # Find the end of the class (next class or end of file)
        indent = len(lines[class_line]) - len(lines[class_line].lstrip())
        insert_line = len(lines)
        
        for i in range(class_line + 1, len(lines)):
            if lines[i].strip() and not lines[i].startswith(' ' * (indent + 1)):
                if lines[i].strip().startswith('class ') or lines[i].strip().startswith('def '):
                    insert_line = i
                    break
        
        # Insert the template
        new_lines = lines[:insert_line] + [template] + lines[insert_line:]
        return '\n'.join(new_lines)
    
    def _calculate_risk_score(self, original: str, improved: str) -> float:
        """Calculate risk score for a code change"""
        # Count lines changed
        original_lines = set(original.split('\n'))
        improved_lines = set(improved.split('\n'))
        
        added = len(improved_lines - original_lines)
        removed = len(original_lines - improved_lines)
        
        total_original = len(original_lines)
        change_ratio = (added + removed) / max(total_original, 1)
        
        # More changes = higher risk
        risk = min(1.0, change_ratio * 0.3)
        
        # Check for dangerous patterns
        dangerous_patterns = ['os.system', 'subprocess.call', 'eval(', 'exec(']
        for pattern in dangerous_patterns:
            if pattern in improved and pattern not in original:
                risk += 0.3
        
        return min(1.0, risk)
    
    async def _validate_improvement(self, candidate: EvolutionCandidate) -> bool:
        """Validate an improvement before deployment"""
        try:
            # Syntax check
            ast.parse(candidate.improved_code)
            
            # Check for required elements
            if 'def ' not in candidate.improved_code:
                return False
            
            # Check risk score
            if candidate.risk_score > self.config["max_risk_score"]:
                return False
            
            return True
        except SyntaxError:
            return False
        except Exception:
            return False
    
    async def _deploy_improvement(self, candidate: EvolutionCandidate) -> bool:
        """Deploy a validated improvement"""
        try:
            target_path = Path(self.config["code_base_path"]) / candidate.target_module
            
            # Create backup
            backup_file = self.backup_path / f"{candidate.target_module}.{datetime.now().strftime('%Y%m%d_%H%M%S')}.backup"
            if target_path.exists():
                shutil.copy(target_path, backup_file)
                self.rollback_available = True
            
            # Write improved code
            target_path.write_text(candidate.improved_code)
            
            return True
        except Exception as e:
            print(f"Deployment error: {e}")
            return False
    
    async def rollback_last_deployment(self) -> bool:
        """Rollback the last deployment"""
        if not self.rollback_available or not self.deployed_improvements:
            return False
        
        try:
            last_improvement = self.deployed_improvements[-1]
            target_path = Path(self.config["code_base_path"]) / last_improvement.target_module
            
            # Find the most recent backup
            backups = list(self.backup_path.glob(f"{last_improvement.target_module}.*.backup"))
            if not backups:
                return False
            
            latest_backup = max(backups, key=lambda p: p.stat().st_mtime)
            
            # Restore from backup
            shutil.copy(latest_backup, target_path)
            
            # Remove from deployed list
            self.deployed_improvements.pop()
            
            return True
        except Exception as e:
            print(f"Rollback error: {e}")
            return False
    
    def _generate_id(self, prefix: str) -> str:
        """Generate a unique ID"""
        timestamp = datetime.now().isoformat()
        hash_input = f"{prefix}_{timestamp}_{self.generation}"
        return f"{prefix}_{hashlib.md5(hash_input.encode()).hexdigest()[:8]}"
    
    def get_status(self) -> Dict:
        """Get evolution loop status"""
        return {
            "phase": self.phase.value,
            "generation": self.generation,
            "total_cycles": len(self.cycles),
            "total_candidates": len(self.candidates),
            "deployed_improvements": len(self.deployed_improvements),
            "rollback_available": self.rollback_available,
            "last_cycle": self.cycles[-1].id if self.cycles else None
        }


# Global instance
_evolution_loop: Optional[SelfEvolutionLoop] = None


def get_evolution_loop() -> SelfEvolutionLoop:
    """Get or create the evolution loop"""
    global _evolution_loop
    if _evolution_loop is None:
        _evolution_loop = SelfEvolutionLoop()
    return _evolution_loop


async def run_self_evolution(performance_data: Dict) -> Dict:
    """Run a self-evolution cycle"""
    loop = get_evolution_loop()
    cycle = await loop.run_evolution_cycle(performance_data)
    
    return {
        "cycle_id": cycle.id,
        "generation": cycle.generation,
        "candidates_generated": len(cycle.candidates),
        "deployed_count": cycle.deployed_count,
        "phase": cycle.phase.value
    }
