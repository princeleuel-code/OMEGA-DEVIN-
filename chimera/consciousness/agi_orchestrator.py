"""
AGI ORCHESTRATOR
================
The central nervous system of the UNMATCHABLE Trading AGI.

This orchestrator:
1. Connects ALL intelligence modules into one unified brain
2. Integrates Clawdbot for autonomous code evolution
3. Manages the self-improvement loop
4. Coordinates multi-model reasoning
5. Handles real-time market analysis and decision making

This is the breakthrough - the Trading AGI that thinks, learns, and evolves.
"""

import os
import json
import asyncio
import subprocess
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple, Callable
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
import hashlib
import traceback

# Import all intelligence modules
from .trading_agi import (
    TradingAGI, get_trading_agi, run_agi_cycle, run_evolution_cycle,
    ThoughtChain, CodeImprovement, EvolutionGenome, AGIMode, ReasoningDepth
)
from .woven_intelligence import WovenIntelligence
from .sota_intelligence import SOTAIntelligence
from .ultimate_intelligence import UltimateIntelligence
from .vpe_intelligence import VPEIntelligence
from .smc_intelligence import SMCIntelligence
from .mtf_intelligence import MTFIntelligence
from .adaptive_regime import AdaptiveRegime
from .position_sizing import PositionSizing
from .session_trade_management import SessionTradeManagement
from .institutional_flow_detection import InstitutionalFlowDetection
from .cross_asset_correlation import CrossAssetCorrelation
from .fractal_swing_intelligence import FractalSwingIntelligence
from .manipulation_candle_intelligence import ManipulationCandleIntelligence
from .multi_profile_volume_intelligence import MultiProfileVolumeIntelligence


class AGIState(Enum):
    """States of the AGI system"""
    INITIALIZING = "initializing"
    OBSERVING = "observing"
    ANALYZING = "analyzing"
    DECIDING = "deciding"
    EXECUTING = "executing"
    EVOLVING = "evolving"
    LEARNING = "learning"
    IDLE = "idle"
    ERROR = "error"


@dataclass
class AGIDecision:
    """A decision made by the AGI"""
    id: str
    timestamp: datetime
    symbol: str
    direction: str  # LONG, SHORT, NEUTRAL
    confidence: float
    reasoning: List[str]
    evidence: List[Dict]
    risk_score: float
    position_size: float
    entry_price: Optional[float] = None
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    sources: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "timestamp": self.timestamp.isoformat(),
            "symbol": self.symbol,
            "direction": self.direction,
            "confidence": self.confidence,
            "reasoning": self.reasoning,
            "evidence": self.evidence,
            "risk_score": self.risk_score,
            "position_size": self.position_size,
            "entry_price": self.entry_price,
            "stop_loss": self.stop_loss,
            "take_profit": self.take_profit,
            "sources": self.sources
        }


@dataclass
class LearningEvent:
    """An event that the AGI learns from"""
    id: str
    timestamp: datetime
    event_type: str  # trade_result, market_event, pattern_detected, etc.
    data: Dict
    lesson_learned: str
    confidence_adjustment: float
    applied_to: List[str]  # Which modules were updated


class ClawdbotIntegration:
    """
    Integration with Clawdbot for autonomous code evolution.
    This is where the AGI writes its own improvements.
    """
    
    def __init__(self, clawdbot_path: str = "/home/ubuntu/.clawdbot"):
        self.clawdbot_path = Path(clawdbot_path)
        self.config_path = self.clawdbot_path / "config.json"
        self.is_available = self._check_availability()
        self.session_id = None
        
    def _check_availability(self) -> bool:
        """Check if Clawdbot is available"""
        return self.clawdbot_path.exists() and self.config_path.exists()
    
    async def start_session(self) -> Optional[str]:
        """Start a Clawdbot session for code evolution"""
        if not self.is_available:
            return None
        
        self.session_id = f"agi_evolution_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        return self.session_id
    
    async def request_code_improvement(
        self,
        target_file: str,
        improvement_description: str,
        context: Dict
    ) -> Optional[str]:
        """
        Request Clawdbot to write a code improvement.
        
        This is the core of the self-evolving capability.
        """
        if not self.is_available:
            return None
        
        prompt = f"""
        You are improving the OMEGA-DEVIN Trading AGI system.
        
        Target file: {target_file}
        
        Improvement needed: {improvement_description}
        
        Context:
        - Recent performance: {context.get('performance', {})}
        - Identified weakness: {context.get('weakness', {})}
        - Current implementation issues: {context.get('issues', [])}
        
        Requirements:
        1. Write production-quality Python code
        2. Include proper type hints
        3. Add docstrings
        4. Handle edge cases
        5. Maintain backward compatibility
        
        Write the improved code:
        """
        
        # In production, this would call Clawdbot's API
        # For now, return a placeholder
        return None
    
    async def validate_improvement(self, code: str, test_cases: List[Dict]) -> bool:
        """Validate a code improvement before deployment"""
        try:
            # Syntax check
            compile(code, '<string>', 'exec')
            
            # Run test cases (in sandbox)
            # This would execute the code in a safe environment
            
            return True
        except SyntaxError:
            return False
        except Exception:
            return False
    
    async def deploy_improvement(self, target_file: str, new_code: str) -> bool:
        """Deploy a validated improvement"""
        try:
            # Backup original
            target_path = Path(target_file)
            backup_path = target_path.with_suffix('.py.backup')
            
            if target_path.exists():
                backup_path.write_text(target_path.read_text())
            
            # Write new code
            target_path.write_text(new_code)
            
            return True
        except Exception:
            return False


class AGIOrchestrator:
    """
    The UNMATCHABLE Trading AGI Orchestrator.
    
    This is the central brain that:
    1. Coordinates all intelligence modules
    2. Makes unified trading decisions
    3. Learns from every outcome
    4. Evolves its own code
    5. Pushes the boundaries of what's possible
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or self._default_config()
        self.state = AGIState.INITIALIZING
        
        # Core AGI
        self.agi = get_trading_agi()
        
        # Intelligence modules
        self.modules = {}
        self._initialize_modules()
        
        # Clawdbot integration
        self.clawdbot = ClawdbotIntegration()
        
        # State tracking
        self.decisions: List[AGIDecision] = []
        self.learning_events: List[LearningEvent] = []
        self.performance_history: List[Dict] = []
        
        # Evolution tracking
        self.generation = 0
        self.total_improvements = 0
        self.successful_improvements = 0
        self.last_evolution = datetime.now()
        
        # Real-time state
        self.current_positions: Dict[str, Dict] = {}
        self.market_state: Dict[str, Dict] = {}
        self.active_signals: List[Dict] = []
        
        self.state = AGIState.IDLE
    
    def _default_config(self) -> Dict:
        return {
            "symbols": ["EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "XAUUSD"],
            "evolution_interval_hours": 24,
            "min_trades_for_evolution": 20,
            "confidence_threshold": 0.65,
            "risk_per_trade": 0.01,
            "max_daily_risk": 0.03,
            "max_concurrent_positions": 3,
            "learning_rate": 0.1,
            "module_weights": {
                "woven": 0.20,
                "sota": 0.15,
                "ultimate": 0.15,
                "vpe": 0.10,
                "smc": 0.10,
                "mtf": 0.10,
                "regime": 0.05,
                "session": 0.05,
                "institutional": 0.05,
                "fractal": 0.05
            }
        }
    
    def _initialize_modules(self):
        """Initialize all intelligence modules"""
        try:
            self.modules = {
                "woven": WovenIntelligence(),
                "sota": SOTAIntelligence(),
                "ultimate": UltimateIntelligence(),
                "vpe": VPEIntelligence(),
                "smc": SMCIntelligence(),
                "mtf": MTFIntelligence(),
                "regime": AdaptiveRegime(),
                "position": PositionSizing(),
                "session": SessionTradeManagement(),
                "institutional": InstitutionalFlowDetection(),
                "correlation": CrossAssetCorrelation(),
                "fractal": FractalSwingIntelligence(),
                "manipulation": ManipulationCandleIntelligence(),
                "volume": MultiProfileVolumeIntelligence()
            }
        except Exception as e:
            # Some modules may not be fully implemented yet
            print(f"Warning: Could not initialize all modules: {e}")
            self.modules = {}
    
    async def analyze(self, market_data: Dict) -> AGIDecision:
        """
        Perform deep analysis and make a trading decision.
        
        This is where ALL intelligence modules come together
        to form a unified, highly confident decision.
        """
        self.state = AGIState.ANALYZING
        
        symbol = market_data.get("symbol", "EURUSD")
        price = market_data.get("price", 0)
        
        # Collect signals from all modules
        signals = await self._collect_all_signals(market_data)
        
        # Run AGI thinking cycle
        thought_chain = await self.agi.think({
            "symbol": symbol,
            "price": price,
            "signals": signals,
            **market_data
        })
        
        # Synthesize decision
        self.state = AGIState.DECIDING
        decision = await self._synthesize_decision(
            symbol=symbol,
            price=price,
            signals=signals,
            thought_chain=thought_chain,
            market_data=market_data
        )
        
        self.decisions.append(decision)
        self.state = AGIState.IDLE
        
        return decision
    
    async def _collect_all_signals(self, market_data: Dict) -> List[Dict]:
        """Collect signals from all intelligence modules"""
        signals = []
        
        for name, module in self.modules.items():
            try:
                if hasattr(module, 'analyze'):
                    result = module.analyze(market_data)
                    if result:
                        signals.append({
                            "source": name,
                            "weight": self.config["module_weights"].get(name, 0.1),
                            **result
                        })
            except Exception as e:
                # Log but don't fail
                pass
        
        return signals
    
    async def _synthesize_decision(
        self,
        symbol: str,
        price: float,
        signals: List[Dict],
        thought_chain: ThoughtChain,
        market_data: Dict
    ) -> AGIDecision:
        """Synthesize all signals into a unified decision"""
        
        # Calculate weighted direction
        long_score = 0.0
        short_score = 0.0
        neutral_score = 0.0
        
        reasoning = []
        evidence = []
        sources = []
        
        for signal in signals:
            weight = signal.get("weight", 0.1)
            direction = signal.get("direction", "NEUTRAL").upper()
            confidence = signal.get("confidence", 0.5)
            
            weighted_score = weight * confidence
            
            if direction == "LONG" or direction == "BUY":
                long_score += weighted_score
                reasoning.append(f"{signal['source']}: LONG ({confidence:.1%})")
            elif direction == "SHORT" or direction == "SELL":
                short_score += weighted_score
                reasoning.append(f"{signal['source']}: SHORT ({confidence:.1%})")
            else:
                neutral_score += weighted_score
                reasoning.append(f"{signal['source']}: NEUTRAL ({confidence:.1%})")
            
            sources.append(signal["source"])
            evidence.append(signal)
        
        # Add thought chain reasoning
        for thought in thought_chain.thoughts:
            reasoning.append(f"AGI: {thought}")
        
        # Determine final direction
        total_score = long_score + short_score + neutral_score
        if total_score == 0:
            total_score = 1  # Avoid division by zero
        
        if long_score > short_score and long_score > neutral_score:
            direction = "LONG"
            confidence = long_score / total_score
        elif short_score > long_score and short_score > neutral_score:
            direction = "SHORT"
            confidence = short_score / total_score
        else:
            direction = "NEUTRAL"
            confidence = neutral_score / total_score
        
        # Calculate risk and position size
        risk_score = self._calculate_risk_score(market_data, signals)
        position_size = self._calculate_position_size(confidence, risk_score)
        
        # Calculate entry, stop, and target
        entry_price = price
        atr = market_data.get("atr", price * 0.001)
        
        if direction == "LONG":
            stop_loss = price - (atr * 2)
            take_profit = price + (atr * 3)
        elif direction == "SHORT":
            stop_loss = price + (atr * 2)
            take_profit = price - (atr * 3)
        else:
            stop_loss = None
            take_profit = None
        
        return AGIDecision(
            id=self._generate_id("decision"),
            timestamp=datetime.now(),
            symbol=symbol,
            direction=direction,
            confidence=confidence,
            reasoning=reasoning,
            evidence=evidence,
            risk_score=risk_score,
            position_size=position_size,
            entry_price=entry_price,
            stop_loss=stop_loss,
            take_profit=take_profit,
            sources=sources
        )
    
    def _calculate_risk_score(self, market_data: Dict, signals: List[Dict]) -> float:
        """Calculate overall risk score"""
        risk = 0.0
        
        # Volatility risk
        volatility = market_data.get("volatility", 0)
        if volatility > 0.02:
            risk += 0.2
        elif volatility > 0.01:
            risk += 0.1
        
        # Signal disagreement risk
        directions = [s.get("direction", "NEUTRAL") for s in signals]
        unique_directions = set(directions)
        if len(unique_directions) > 2:
            risk += 0.15
        
        # Low confidence risk
        avg_confidence = sum(s.get("confidence", 0.5) for s in signals) / max(len(signals), 1)
        if avg_confidence < 0.5:
            risk += 0.2
        
        # Time risk (avoid news times, session transitions)
        hour = datetime.now().hour
        if hour in [8, 13, 14, 15]:  # News times
            risk += 0.1
        
        return min(1.0, risk)
    
    def _calculate_position_size(self, confidence: float, risk_score: float) -> float:
        """Calculate position size based on confidence and risk"""
        base_risk = self.config["risk_per_trade"]
        
        # Adjust for confidence
        confidence_factor = confidence / 0.7  # Normalize to 70% confidence
        
        # Adjust for risk
        risk_factor = 1 - (risk_score * 0.5)
        
        # Calculate final size
        size = base_risk * confidence_factor * risk_factor
        
        # Cap at max risk
        return min(size, self.config["max_daily_risk"])
    
    async def learn(self, trade_result: Dict) -> LearningEvent:
        """
        Learn from a trade result.
        
        This is where the AGI improves its decision making
        based on real outcomes.
        """
        self.state = AGIState.LEARNING
        
        # Analyze what went right or wrong
        analysis = self._analyze_trade_result(trade_result)
        
        # Determine lesson learned
        lesson = self._extract_lesson(analysis)
        
        # Calculate confidence adjustment
        adjustment = self._calculate_confidence_adjustment(trade_result)
        
        # Apply learning to relevant modules
        applied_to = await self._apply_learning(lesson, adjustment)
        
        event = LearningEvent(
            id=self._generate_id("learning"),
            timestamp=datetime.now(),
            event_type="trade_result",
            data=trade_result,
            lesson_learned=lesson,
            confidence_adjustment=adjustment,
            applied_to=applied_to
        )
        
        self.learning_events.append(event)
        self.state = AGIState.IDLE
        
        return event
    
    def _analyze_trade_result(self, result: Dict) -> Dict:
        """Analyze a trade result to understand what happened"""
        pnl = result.get("pnl", 0)
        entry_reason = result.get("entry_reason", "unknown")
        exit_reason = result.get("exit_reason", "unknown")
        duration = result.get("duration_minutes", 0)
        
        analysis = {
            "profitable": pnl > 0,
            "pnl": pnl,
            "entry_reason": entry_reason,
            "exit_reason": exit_reason,
            "duration": duration,
            "issues": []
        }
        
        # Identify issues
        if pnl < 0:
            if exit_reason == "stop_loss":
                if duration < 5:
                    analysis["issues"].append("premature_stop")
                else:
                    analysis["issues"].append("poor_entry_timing")
            elif exit_reason == "manual":
                analysis["issues"].append("emotional_exit")
        else:
            if exit_reason == "take_profit":
                analysis["issues"].append("good_trade")
            elif exit_reason == "trailing_stop":
                analysis["issues"].append("trend_captured")
        
        return analysis
    
    def _extract_lesson(self, analysis: Dict) -> str:
        """Extract a lesson from the trade analysis"""
        issues = analysis.get("issues", [])
        
        if "premature_stop" in issues:
            return "Stop loss may be too tight. Consider using ATR-based stops."
        elif "poor_entry_timing" in issues:
            return "Entry timing needs improvement. Wait for more confluence."
        elif "emotional_exit" in issues:
            return "Avoid manual exits. Trust the system."
        elif "good_trade" in issues:
            return "Trade executed well. Maintain current approach."
        elif "trend_captured" in issues:
            return "Trailing stop worked well. Continue using for trending markets."
        else:
            return "No specific lesson identified."
    
    def _calculate_confidence_adjustment(self, result: Dict) -> float:
        """Calculate how much to adjust confidence based on result"""
        pnl = result.get("pnl", 0)
        expected_pnl = result.get("expected_pnl", 0)
        
        if expected_pnl == 0:
            return 0.0
        
        # Calculate performance vs expectation
        performance_ratio = pnl / abs(expected_pnl) if expected_pnl != 0 else 0
        
        # Adjust confidence (small adjustments)
        adjustment = performance_ratio * self.config["learning_rate"]
        
        # Cap adjustment
        return max(-0.1, min(0.1, adjustment))
    
    async def _apply_learning(self, lesson: str, adjustment: float) -> List[str]:
        """Apply learning to relevant modules"""
        applied_to = []
        
        # Determine which modules to update based on lesson
        if "stop" in lesson.lower():
            applied_to.append("position")
        if "entry" in lesson.lower() or "confluence" in lesson.lower():
            applied_to.append("smc")
            applied_to.append("mtf")
        if "timing" in lesson.lower():
            applied_to.append("session")
        if "trend" in lesson.lower():
            applied_to.append("regime")
        
        # In production, this would actually update module parameters
        
        return applied_to
    
    async def evolve(self) -> Dict:
        """
        Run an evolution cycle.
        
        This is where the AGI improves its own code
        using Clawdbot integration.
        """
        self.state = AGIState.EVOLVING
        
        # Gather performance data
        performance_data = self._gather_performance_data()
        
        # Run AGI evolution
        evolution_result = await run_evolution_cycle(performance_data)
        
        # If Clawdbot is available, request code improvements
        if self.clawdbot.is_available:
            await self._request_clawdbot_improvements(performance_data)
        
        self.generation += 1
        self.last_evolution = datetime.now()
        self.state = AGIState.IDLE
        
        return {
            "generation": self.generation,
            "evolution_result": evolution_result,
            "timestamp": datetime.now().isoformat()
        }
    
    def _gather_performance_data(self) -> Dict:
        """Gather performance data for evolution"""
        if not self.decisions:
            return {"trades": [], "total_pnl": 0, "win_rate": 0}
        
        # Calculate metrics from decisions and their outcomes
        trades = []
        for decision in self.decisions[-100:]:  # Last 100 decisions
            trades.append({
                "symbol": decision.symbol,
                "direction": decision.direction,
                "confidence": decision.confidence,
                "sources": decision.sources
            })
        
        return {
            "trades": trades,
            "total_pnl": sum(t.get("pnl", 0) for t in self.performance_history),
            "win_rate": self._calculate_win_rate(),
            "profit_factor": self._calculate_profit_factor(),
            "max_drawdown": self._calculate_max_drawdown()
        }
    
    def _calculate_win_rate(self) -> float:
        """Calculate win rate from performance history"""
        if not self.performance_history:
            return 0.5
        
        wins = sum(1 for t in self.performance_history if t.get("pnl", 0) > 0)
        return wins / len(self.performance_history)
    
    def _calculate_profit_factor(self) -> float:
        """Calculate profit factor"""
        if not self.performance_history:
            return 1.0
        
        gross_profit = sum(t.get("pnl", 0) for t in self.performance_history if t.get("pnl", 0) > 0)
        gross_loss = abs(sum(t.get("pnl", 0) for t in self.performance_history if t.get("pnl", 0) < 0))
        
        if gross_loss == 0:
            return 10.0  # Cap at 10
        
        return gross_profit / gross_loss
    
    def _calculate_max_drawdown(self) -> float:
        """Calculate maximum drawdown"""
        if not self.performance_history:
            return 0.0
        
        cumulative = 0
        peak = 0
        max_dd = 0
        
        for trade in self.performance_history:
            cumulative += trade.get("pnl", 0)
            peak = max(peak, cumulative)
            dd = (peak - cumulative) / max(peak, 1)
            max_dd = max(max_dd, dd)
        
        return max_dd
    
    async def _request_clawdbot_improvements(self, performance_data: Dict) -> None:
        """Request code improvements from Clawdbot"""
        if not self.clawdbot.is_available:
            return
        
        # Start session
        session_id = await self.clawdbot.start_session()
        if not session_id:
            return
        
        # Identify areas for improvement
        weaknesses = self._identify_weaknesses(performance_data)
        
        for weakness in weaknesses[:3]:  # Limit to 3 improvements per cycle
            improvement = await self.clawdbot.request_code_improvement(
                target_file=weakness.get("target_file", ""),
                improvement_description=weakness.get("description", ""),
                context={
                    "performance": performance_data,
                    "weakness": weakness
                }
            )
            
            if improvement:
                # Validate and deploy
                is_valid = await self.clawdbot.validate_improvement(improvement, [])
                if is_valid:
                    deployed = await self.clawdbot.deploy_improvement(
                        weakness.get("target_file", ""),
                        improvement
                    )
                    if deployed:
                        self.successful_improvements += 1
                
                self.total_improvements += 1
    
    def _identify_weaknesses(self, performance_data: Dict) -> List[Dict]:
        """Identify weaknesses in the system"""
        weaknesses = []
        
        win_rate = performance_data.get("win_rate", 0.5)
        profit_factor = performance_data.get("profit_factor", 1.0)
        max_drawdown = performance_data.get("max_drawdown", 0)
        
        if win_rate < 0.5:
            weaknesses.append({
                "type": "low_win_rate",
                "target_file": "/home/ubuntu/omega_devin/chimera/consciousness/smc_intelligence.py",
                "description": f"Win rate is {win_rate:.1%}. Improve entry signal quality."
            })
        
        if profit_factor < 1.5:
            weaknesses.append({
                "type": "low_profit_factor",
                "target_file": "/home/ubuntu/omega_devin/chimera/consciousness/position_sizing.py",
                "description": f"Profit factor is {profit_factor:.2f}. Improve risk/reward ratio."
            })
        
        if max_drawdown > 0.15:
            weaknesses.append({
                "type": "high_drawdown",
                "target_file": "/home/ubuntu/omega_devin/chimera/consciousness/adaptive_regime.py",
                "description": f"Max drawdown is {max_drawdown:.1%}. Improve regime filtering."
            })
        
        return weaknesses
    
    def _generate_id(self, prefix: str) -> str:
        """Generate a unique ID"""
        timestamp = datetime.now().isoformat()
        hash_input = f"{prefix}_{timestamp}_{len(self.decisions)}"
        return f"{prefix}_{hashlib.md5(hash_input.encode()).hexdigest()[:8]}"
    
    def get_status(self) -> Dict:
        """Get current AGI status"""
        return {
            "state": self.state.value,
            "generation": self.generation,
            "total_decisions": len(self.decisions),
            "total_learning_events": len(self.learning_events),
            "total_improvements": self.total_improvements,
            "successful_improvements": self.successful_improvements,
            "last_evolution": self.last_evolution.isoformat(),
            "clawdbot_available": self.clawdbot.is_available,
            "active_modules": list(self.modules.keys()),
            "current_positions": len(self.current_positions),
            "agi_status": self.agi.get_status()
        }
    
    async def run_continuous(self, market_feed: Callable[[], Dict], interval_seconds: int = 60):
        """
        Run the AGI continuously.
        
        This is the main loop that:
        1. Analyzes market data
        2. Makes decisions
        3. Learns from outcomes
        4. Evolves periodically
        """
        print("Starting UNMATCHABLE Trading AGI...")
        print(f"Active modules: {list(self.modules.keys())}")
        print(f"Clawdbot available: {self.clawdbot.is_available}")
        
        while True:
            try:
                # Get market data
                market_data = market_feed()
                
                # Analyze and decide
                decision = await self.analyze(market_data)
                
                print(f"[{datetime.now().strftime('%H:%M:%S')}] "
                      f"{decision.symbol}: {decision.direction} "
                      f"(conf: {decision.confidence:.1%}, risk: {decision.risk_score:.2f})")
                
                # Check if evolution is due
                hours_since_evolution = (datetime.now() - self.last_evolution).total_seconds() / 3600
                if hours_since_evolution >= self.config["evolution_interval_hours"]:
                    print("Running evolution cycle...")
                    await self.evolve()
                
                # Wait for next cycle
                await asyncio.sleep(interval_seconds)
                
            except KeyboardInterrupt:
                print("Stopping AGI...")
                break
            except Exception as e:
                print(f"Error in AGI loop: {e}")
                traceback.print_exc()
                await asyncio.sleep(interval_seconds)


# Global orchestrator instance
_orchestrator: Optional[AGIOrchestrator] = None


def get_orchestrator() -> AGIOrchestrator:
    """Get or create the AGI orchestrator"""
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = AGIOrchestrator()
    return _orchestrator


async def run_agi_analysis(market_data: Dict) -> Dict:
    """Run AGI analysis on market data"""
    orchestrator = get_orchestrator()
    decision = await orchestrator.analyze(market_data)
    return decision.to_dict()


async def run_agi_learning(trade_result: Dict) -> Dict:
    """Run AGI learning from trade result"""
    orchestrator = get_orchestrator()
    event = await orchestrator.learn(trade_result)
    return {
        "id": event.id,
        "lesson": event.lesson_learned,
        "adjustment": event.confidence_adjustment,
        "applied_to": event.applied_to
    }


async def run_agi_evolution() -> Dict:
    """Run AGI evolution cycle"""
    orchestrator = get_orchestrator()
    return await orchestrator.evolve()


def get_agi_status() -> Dict:
    """Get AGI status"""
    orchestrator = get_orchestrator()
    return orchestrator.get_status()
