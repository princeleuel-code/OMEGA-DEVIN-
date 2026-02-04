"""
Autonomy Agent

A self-improvement research agent that analyzes trading performance,
proposes improvements, and helps the system evolve over time.

Key Features:
- Analyzes trading logs and performance metrics
- Proposes parameter adjustments and new rules
- Generates code suggestions for improvements
- Validates proposals through backtesting
- Maintains a knowledge base of lessons learned

Note: This is a framework implementation. For full LLM integration,
you would connect to OpenAI API, local GPT, or similar.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple
import hashlib

logger = logging.getLogger(__name__)


class TaskType(Enum):
    """Types of research tasks."""
    ANALYZE_PERFORMANCE = "analyze_performance"
    ANALYZE_VETOES = "analyze_vetoes"
    ANALYZE_LOSSES = "analyze_losses"
    PROPOSE_PARAMETERS = "propose_parameters"
    PROPOSE_RULES = "propose_rules"
    GENERATE_CODE = "generate_code"
    VALIDATE_IMPROVEMENT = "validate_improvement"
    SUMMARIZE_WEEK = "summarize_week"


class ImprovementStatus(Enum):
    """Status of a proposed improvement."""
    PROPOSED = "proposed"
    TESTING = "testing"
    VALIDATED = "validated"
    REJECTED = "rejected"
    DEPLOYED = "deployed"


@dataclass
class AgentConfig:
    """Configuration for the autonomy agent."""
    # Analysis settings
    min_trades_for_analysis: int = 20
    lookback_days: int = 30
    
    # Improvement thresholds
    min_improvement_pct: float = 5.0  # Minimum improvement to consider
    max_risk_increase_pct: float = 10.0  # Maximum acceptable risk increase
    
    # Validation settings
    validation_bars: int = 1000
    validation_runs: int = 5
    
    # Safety settings
    require_human_approval: bool = True
    max_auto_deployments_per_day: int = 1
    
    # Knowledge base
    knowledge_base_path: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "min_trades_for_analysis": self.min_trades_for_analysis,
            "lookback_days": self.lookback_days,
            "min_improvement_pct": self.min_improvement_pct,
            "max_risk_increase_pct": self.max_risk_increase_pct,
            "validation_bars": self.validation_bars,
            "validation_runs": self.validation_runs,
            "require_human_approval": self.require_human_approval,
            "max_auto_deployments_per_day": self.max_auto_deployments_per_day,
        }


@dataclass
class ResearchTask:
    """A research task for the agent."""
    task_type: TaskType
    description: str
    context: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    result: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_type": self.task_type.value,
            "description": self.description,
            "context": self.context,
            "created_at": self.created_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "result": self.result,
        }


@dataclass
class Improvement:
    """A proposed improvement to the system."""
    id: str
    title: str
    description: str
    improvement_type: str  # parameter, rule, code
    changes: Dict[str, Any]
    expected_benefit: str
    risk_assessment: str
    status: ImprovementStatus = ImprovementStatus.PROPOSED
    validation_results: Optional[Dict[str, Any]] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    deployed_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "improvement_type": self.improvement_type,
            "changes": self.changes,
            "expected_benefit": self.expected_benefit,
            "risk_assessment": self.risk_assessment,
            "status": self.status.value,
            "validation_results": self.validation_results,
            "created_at": self.created_at.isoformat(),
            "deployed_at": self.deployed_at.isoformat() if self.deployed_at else None,
        }


@dataclass
class Lesson:
    """A lesson learned from trading."""
    id: str
    title: str
    description: str
    context: str  # What happened
    insight: str  # What we learned
    action: str  # What to do differently
    tags: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "context": self.context,
            "insight": self.insight,
            "action": self.action,
            "tags": self.tags,
            "created_at": self.created_at.isoformat(),
        }


class KnowledgeBase:
    """
    Knowledge base for storing lessons and improvements.
    """
    
    def __init__(self, path: Optional[Path] = None):
        self.path = path
        self.lessons: List[Lesson] = []
        self.improvements: List[Improvement] = []
        self.patterns: Dict[str, int] = {}  # Pattern -> count
        
        if path and path.exists():
            self.load()
    
    def add_lesson(self, lesson: Lesson) -> None:
        """Add a lesson to the knowledge base."""
        self.lessons.append(lesson)
        for tag in lesson.tags:
            self.patterns[tag] = self.patterns.get(tag, 0) + 1
        self._save_if_path()
    
    def add_improvement(self, improvement: Improvement) -> None:
        """Add an improvement to the knowledge base."""
        self.improvements.append(improvement)
        self._save_if_path()
    
    def search_lessons(self, query: str, limit: int = 5) -> List[Lesson]:
        """Search lessons by keyword."""
        query_lower = query.lower()
        scored = []
        for lesson in self.lessons:
            score = 0
            if query_lower in lesson.title.lower():
                score += 3
            if query_lower in lesson.description.lower():
                score += 2
            if query_lower in lesson.insight.lower():
                score += 2
            if any(query_lower in tag.lower() for tag in lesson.tags):
                score += 1
            if score > 0:
                scored.append((score, lesson))
        
        scored.sort(key=lambda x: x[0], reverse=True)
        return [lesson for _, lesson in scored[:limit]]
    
    def get_common_patterns(self, limit: int = 10) -> List[Tuple[str, int]]:
        """Get most common patterns/tags."""
        sorted_patterns = sorted(self.patterns.items(), key=lambda x: x[1], reverse=True)
        return sorted_patterns[:limit]
    
    def _save_if_path(self) -> None:
        if self.path:
            self.save()
    
    def save(self) -> None:
        """Save knowledge base to file."""
        if not self.path:
            return
        
        data = {
            "lessons": [l.to_dict() for l in self.lessons],
            "improvements": [i.to_dict() for i in self.improvements],
            "patterns": self.patterns,
        }
        with open(self.path, "w") as f:
            json.dump(data, f, indent=2)
    
    def load(self) -> None:
        """Load knowledge base from file."""
        if not self.path or not self.path.exists():
            return
        
        with open(self.path, "r") as f:
            data = json.load(f)
        
        self.lessons = [
            Lesson(
                id=l["id"],
                title=l["title"],
                description=l["description"],
                context=l["context"],
                insight=l["insight"],
                action=l["action"],
                tags=l.get("tags", []),
                created_at=datetime.fromisoformat(l["created_at"]),
            )
            for l in data.get("lessons", [])
        ]
        self.patterns = data.get("patterns", {})


class AutonomyAgent:
    """
    Self-improvement research agent.
    
    Analyzes trading performance and proposes improvements.
    Can be connected to an LLM for more sophisticated analysis.
    """
    
    def __init__(
        self,
        config: Optional[AgentConfig] = None,
        knowledge_base_path: Optional[Path] = None,
    ):
        self.config = config or AgentConfig()
        self.knowledge_base = KnowledgeBase(knowledge_base_path)
        self.pending_tasks: List[ResearchTask] = []
        self.completed_tasks: List[ResearchTask] = []
        self.proposed_improvements: List[Improvement] = []
        self.deployments_today: int = 0
        self.last_deployment_date: Optional[datetime] = None
        
        logger.info("AutonomyAgent initialized")
    
    def analyze_performance(
        self,
        trades: List[Dict[str, Any]],
        metrics: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Analyze trading performance and identify areas for improvement.
        
        Args:
            trades: List of trade records
            metrics: Performance metrics (win_rate, sharpe, etc.)
            
        Returns:
            Analysis results with insights and recommendations
        """
        if len(trades) < self.config.min_trades_for_analysis:
            return {
                "status": "insufficient_data",
                "message": f"Need at least {self.config.min_trades_for_analysis} trades for analysis",
                "trades_count": len(trades),
            }
        
        analysis = {
            "status": "complete",
            "timestamp": datetime.utcnow().isoformat(),
            "trades_analyzed": len(trades),
            "insights": [],
            "recommendations": [],
        }
        
        # Analyze win rate
        winning_trades = [t for t in trades if t.get("pnl", 0) > 0]
        losing_trades = [t for t in trades if t.get("pnl", 0) <= 0]
        win_rate = len(winning_trades) / len(trades) if trades else 0
        
        if win_rate < 0.5:
            analysis["insights"].append({
                "type": "low_win_rate",
                "value": win_rate,
                "message": f"Win rate is {win_rate:.1%}, below 50% threshold",
            })
            analysis["recommendations"].append({
                "type": "parameter",
                "target": "min_confidence",
                "suggestion": "Increase min_confidence threshold to filter out lower quality setups",
            })
        
        # Analyze average win vs loss
        if winning_trades and losing_trades:
            avg_win = sum(t.get("pnl", 0) for t in winning_trades) / len(winning_trades)
            avg_loss = abs(sum(t.get("pnl", 0) for t in losing_trades) / len(losing_trades))
            risk_reward = avg_win / avg_loss if avg_loss > 0 else 0
            
            if risk_reward < 1.5:
                analysis["insights"].append({
                    "type": "low_risk_reward",
                    "value": risk_reward,
                    "message": f"Risk/reward ratio is {risk_reward:.2f}, below 1.5 target",
                })
                analysis["recommendations"].append({
                    "type": "parameter",
                    "target": "atr_multiplier_tp",
                    "suggestion": "Increase take profit multiplier to improve risk/reward",
                })
        
        # Analyze drawdown
        max_dd = metrics.get("max_drawdown", 0)
        if max_dd > 0.1:  # 10%
            analysis["insights"].append({
                "type": "high_drawdown",
                "value": max_dd,
                "message": f"Max drawdown is {max_dd:.1%}, above 10% threshold",
            })
            analysis["recommendations"].append({
                "type": "parameter",
                "target": "risk_per_trade_pct",
                "suggestion": "Reduce risk per trade to limit drawdown",
            })
        
        # Analyze consecutive losses
        max_consecutive_losses = self._calculate_max_consecutive_losses(trades)
        if max_consecutive_losses >= 5:
            analysis["insights"].append({
                "type": "consecutive_losses",
                "value": max_consecutive_losses,
                "message": f"Had {max_consecutive_losses} consecutive losses",
            })
            analysis["recommendations"].append({
                "type": "rule",
                "target": "loss_streak_pause",
                "suggestion": "Add rule to pause trading after 3 consecutive losses",
            })
        
        # Analyze by time of day (if timestamp available)
        time_analysis = self._analyze_by_time(trades)
        if time_analysis:
            analysis["insights"].append(time_analysis)
        
        return analysis
    
    def _calculate_max_consecutive_losses(self, trades: List[Dict[str, Any]]) -> int:
        """Calculate maximum consecutive losing trades."""
        max_streak = 0
        current_streak = 0
        
        for trade in trades:
            if trade.get("pnl", 0) <= 0:
                current_streak += 1
                max_streak = max(max_streak, current_streak)
            else:
                current_streak = 0
        
        return max_streak
    
    def _analyze_by_time(self, trades: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Analyze performance by time of day."""
        time_buckets: Dict[str, List[float]] = {}
        
        for trade in trades:
            timestamp = trade.get("timestamp")
            if not timestamp:
                continue
            
            if isinstance(timestamp, str):
                timestamp = datetime.fromisoformat(timestamp)
            
            hour = timestamp.hour
            bucket = f"{hour:02d}:00-{(hour+1)%24:02d}:00"
            
            if bucket not in time_buckets:
                time_buckets[bucket] = []
            time_buckets[bucket].append(trade.get("pnl", 0))
        
        if not time_buckets:
            return None
        
        # Find best and worst hours
        bucket_stats = {}
        for bucket, pnls in time_buckets.items():
            if len(pnls) >= 3:  # Minimum sample
                bucket_stats[bucket] = {
                    "count": len(pnls),
                    "total_pnl": sum(pnls),
                    "win_rate": len([p for p in pnls if p > 0]) / len(pnls),
                }
        
        if not bucket_stats:
            return None
        
        best_bucket = max(bucket_stats.items(), key=lambda x: x[1]["total_pnl"])
        worst_bucket = min(bucket_stats.items(), key=lambda x: x[1]["total_pnl"])
        
        return {
            "type": "time_analysis",
            "best_hour": best_bucket[0],
            "best_hour_stats": best_bucket[1],
            "worst_hour": worst_bucket[0],
            "worst_hour_stats": worst_bucket[1],
            "message": f"Best performance at {best_bucket[0]}, worst at {worst_bucket[0]}",
        }
    
    def analyze_vetoes(
        self,
        veto_records: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Analyze veto patterns to identify potential issues.
        
        Args:
            veto_records: List of veto records with reason codes
            
        Returns:
            Analysis of veto patterns
        """
        if not veto_records:
            return {"status": "no_data", "message": "No veto records to analyze"}
        
        # Count veto reasons
        reason_counts: Dict[str, int] = {}
        for record in veto_records:
            reasons = record.get("reasons", [])
            for reason in reasons:
                reason_counts[reason] = reason_counts.get(reason, 0) + 1
        
        # Sort by frequency
        sorted_reasons = sorted(reason_counts.items(), key=lambda x: x[1], reverse=True)
        
        analysis = {
            "status": "complete",
            "total_vetoes": len(veto_records),
            "reason_distribution": dict(sorted_reasons),
            "insights": [],
            "recommendations": [],
        }
        
        # Identify dominant veto reasons
        if sorted_reasons:
            top_reason, top_count = sorted_reasons[0]
            top_pct = top_count / len(veto_records)
            
            if top_pct > 0.5:
                analysis["insights"].append({
                    "type": "dominant_veto",
                    "reason": top_reason,
                    "percentage": top_pct,
                    "message": f"{top_reason} accounts for {top_pct:.1%} of all vetoes",
                })
                
                # Suggest adjustments based on reason
                if "VOLATILITY" in top_reason:
                    analysis["recommendations"].append({
                        "type": "parameter",
                        "target": "volatility_threshold",
                        "suggestion": "Consider adjusting volatility threshold if too many valid trades are being blocked",
                    })
                elif "SPREAD" in top_reason:
                    analysis["recommendations"].append({
                        "type": "parameter",
                        "target": "max_spread_atr_ratio",
                        "suggestion": "Review spread threshold - may be too tight for current market conditions",
                    })
        
        return analysis
    
    def propose_improvement(
        self,
        analysis: Dict[str, Any],
    ) -> Optional[Improvement]:
        """
        Generate an improvement proposal based on analysis.
        
        Args:
            analysis: Analysis results from analyze_performance or analyze_vetoes
            
        Returns:
            Improvement proposal or None if no improvement needed
        """
        recommendations = analysis.get("recommendations", [])
        if not recommendations:
            return None
        
        # Take the first recommendation
        rec = recommendations[0]
        
        # Generate unique ID
        id_str = f"{rec['type']}_{rec['target']}_{datetime.utcnow().timestamp()}"
        improvement_id = hashlib.md5(id_str.encode()).hexdigest()[:12]
        
        improvement = Improvement(
            id=improvement_id,
            title=f"Adjust {rec['target']}",
            description=rec["suggestion"],
            improvement_type=rec["type"],
            changes={rec["target"]: rec["suggestion"]},
            expected_benefit="Improved risk-adjusted returns based on analysis",
            risk_assessment="Low risk - parameter adjustment within safe bounds",
        )
        
        self.proposed_improvements.append(improvement)
        self.knowledge_base.add_improvement(improvement)
        
        return improvement
    
    def validate_improvement(
        self,
        improvement: Improvement,
        backtest_func: Callable[[Dict[str, Any]], Dict[str, Any]],
        baseline_metrics: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Validate an improvement through backtesting.
        
        Args:
            improvement: The improvement to validate
            backtest_func: Function to run backtest with given parameters
            baseline_metrics: Baseline performance metrics to compare against
            
        Returns:
            Validation results
        """
        improvement.status = ImprovementStatus.TESTING
        
        # Run validation backtests
        results = []
        for i in range(self.config.validation_runs):
            try:
                result = backtest_func(improvement.changes)
                results.append(result)
            except Exception as e:
                logger.error(f"Validation backtest {i} failed: {e}")
        
        if not results:
            improvement.status = ImprovementStatus.REJECTED
            return {
                "status": "failed",
                "message": "All validation backtests failed",
            }
        
        # Calculate average metrics
        avg_return = sum(r.get("total_return", 0) for r in results) / len(results)
        avg_sharpe = sum(r.get("sharpe_ratio", 0) for r in results) / len(results)
        avg_drawdown = sum(r.get("max_drawdown", 0) for r in results) / len(results)
        
        baseline_return = baseline_metrics.get("total_return", 0)
        baseline_sharpe = baseline_metrics.get("sharpe_ratio", 0)
        baseline_drawdown = baseline_metrics.get("max_drawdown", 0)
        
        # Check improvement
        return_improvement = (avg_return - baseline_return) / max(abs(baseline_return), 0.01) * 100
        sharpe_improvement = (avg_sharpe - baseline_sharpe) / max(abs(baseline_sharpe), 0.01) * 100
        drawdown_change = (avg_drawdown - baseline_drawdown) / max(abs(baseline_drawdown), 0.01) * 100
        
        validation_results = {
            "status": "complete",
            "runs": len(results),
            "avg_return": avg_return,
            "avg_sharpe": avg_sharpe,
            "avg_drawdown": avg_drawdown,
            "return_improvement_pct": return_improvement,
            "sharpe_improvement_pct": sharpe_improvement,
            "drawdown_change_pct": drawdown_change,
        }
        
        # Determine if improvement is valid
        is_valid = (
            return_improvement >= self.config.min_improvement_pct or
            sharpe_improvement >= self.config.min_improvement_pct
        ) and drawdown_change <= self.config.max_risk_increase_pct
        
        if is_valid:
            improvement.status = ImprovementStatus.VALIDATED
            validation_results["recommendation"] = "DEPLOY"
        else:
            improvement.status = ImprovementStatus.REJECTED
            validation_results["recommendation"] = "REJECT"
            if drawdown_change > self.config.max_risk_increase_pct:
                validation_results["rejection_reason"] = "Risk increase exceeds threshold"
            else:
                validation_results["rejection_reason"] = "Improvement below minimum threshold"
        
        improvement.validation_results = validation_results
        return validation_results
    
    def create_lesson(
        self,
        title: str,
        context: str,
        insight: str,
        action: str,
        tags: Optional[List[str]] = None,
    ) -> Lesson:
        """
        Create a new lesson from trading experience.
        
        Args:
            title: Short title for the lesson
            context: What happened (the situation)
            insight: What we learned
            action: What to do differently
            tags: Tags for categorization
            
        Returns:
            The created Lesson
        """
        lesson_id = hashlib.md5(f"{title}_{datetime.utcnow().timestamp()}".encode()).hexdigest()[:12]
        
        lesson = Lesson(
            id=lesson_id,
            title=title,
            description=f"{context}\n\nInsight: {insight}\n\nAction: {action}",
            context=context,
            insight=insight,
            action=action,
            tags=tags or [],
        )
        
        self.knowledge_base.add_lesson(lesson)
        logger.info(f"Created lesson: {title}")
        
        return lesson
    
    def generate_weekly_summary(
        self,
        trades: List[Dict[str, Any]],
        metrics: Dict[str, Any],
        vetoes: List[Dict[str, Any]],
    ) -> str:
        """
        Generate a weekly performance summary.
        
        Args:
            trades: Trades from the week
            metrics: Performance metrics
            vetoes: Veto records
            
        Returns:
            Summary text
        """
        n_trades = len(trades)
        n_vetoes = len(vetoes)
        
        winning_trades = [t for t in trades if t.get("pnl", 0) > 0]
        win_rate = len(winning_trades) / n_trades if n_trades > 0 else 0
        
        total_pnl = sum(t.get("pnl", 0) for t in trades)
        
        summary = f"""
WEEKLY TRADING SUMMARY
======================
Period: Last 7 days
Generated: {datetime.utcnow().isoformat()}

PERFORMANCE OVERVIEW
--------------------
Total Trades: {n_trades}
Win Rate: {win_rate:.1%}
Total P&L: ${total_pnl:.2f}
Sharpe Ratio: {metrics.get('sharpe_ratio', 'N/A')}
Max Drawdown: {metrics.get('max_drawdown', 0):.1%}

VETO ANALYSIS
-------------
Total Vetoes: {n_vetoes}
Veto Rate: {n_vetoes / (n_trades + n_vetoes) * 100 if (n_trades + n_vetoes) > 0 else 0:.1f}%

"""
        
        # Add performance analysis
        analysis = self.analyze_performance(trades, metrics)
        if analysis.get("insights"):
            summary += "KEY INSIGHTS\n------------\n"
            for insight in analysis["insights"]:
                summary += f"- {insight.get('message', '')}\n"
        
        if analysis.get("recommendations"):
            summary += "\nRECOMMENDATIONS\n---------------\n"
            for rec in analysis["recommendations"]:
                summary += f"- {rec.get('suggestion', '')}\n"
        
        # Add lessons learned
        recent_lessons = [l for l in self.knowledge_base.lessons 
                        if (datetime.utcnow() - l.created_at).days <= 7]
        if recent_lessons:
            summary += f"\nLESSONS LEARNED ({len(recent_lessons)})\n"
            summary += "-" * 20 + "\n"
            for lesson in recent_lessons[:3]:
                summary += f"- {lesson.title}: {lesson.insight}\n"
        
        return summary
    
    def can_auto_deploy(self) -> bool:
        """Check if auto-deployment is allowed."""
        if self.config.require_human_approval:
            return False
        
        # Reset daily counter
        today = datetime.utcnow().date()
        if self.last_deployment_date and self.last_deployment_date.date() != today:
            self.deployments_today = 0
        
        return self.deployments_today < self.config.max_auto_deployments_per_day
    
    def record_deployment(self, improvement: Improvement) -> None:
        """Record that an improvement was deployed."""
        improvement.status = ImprovementStatus.DEPLOYED
        improvement.deployed_at = datetime.utcnow()
        self.deployments_today += 1
        self.last_deployment_date = datetime.utcnow()
        
        logger.info(f"Deployed improvement: {improvement.title}")
    
    def get_pending_improvements(self) -> List[Improvement]:
        """Get improvements awaiting deployment."""
        return [i for i in self.proposed_improvements 
                if i.status == ImprovementStatus.VALIDATED]
    
    def get_improvement_history(self) -> List[Dict[str, Any]]:
        """Get history of all improvements."""
        return [i.to_dict() for i in self.proposed_improvements]
    
    def save_state(self, path: Path) -> None:
        """Save agent state to file."""
        state = {
            "config": self.config.to_dict(),
            "pending_tasks": [t.to_dict() for t in self.pending_tasks],
            "completed_tasks": [t.to_dict() for t in self.completed_tasks],
            "proposed_improvements": [i.to_dict() for i in self.proposed_improvements],
            "deployments_today": self.deployments_today,
            "last_deployment_date": self.last_deployment_date.isoformat() if self.last_deployment_date else None,
        }
        with open(path, "w") as f:
            json.dump(state, f, indent=2)
        
        # Also save knowledge base
        if self.knowledge_base.path:
            self.knowledge_base.save()
    
    def load_state(self, path: Path) -> None:
        """Load agent state from file."""
        if not path.exists():
            return
        
        with open(path, "r") as f:
            state = json.load(f)
        
        self.deployments_today = state.get("deployments_today", 0)
        if state.get("last_deployment_date"):
            self.last_deployment_date = datetime.fromisoformat(state["last_deployment_date"])
