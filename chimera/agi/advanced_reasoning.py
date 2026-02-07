"""
ADVANCED REASONING ENGINE
=========================
Deep reasoning capabilities for the TRUE Trading AGI.

This module implements:
1. Tree-of-Thought reasoning
2. Monte Carlo Tree Search for decision making
3. Causal reasoning about market movements
4. Counterfactual analysis
5. Meta-cognitive monitoring

This is what makes the AGI truly THINK, not just compute.
"""

import asyncio
import random
import math
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict
import numpy as np


class ReasoningMode(Enum):
    """Different modes of reasoning"""
    FAST = "fast"           # Quick intuitive reasoning
    SLOW = "slow"           # Deep analytical reasoning
    CREATIVE = "creative"   # Exploratory reasoning
    CRITICAL = "critical"   # Skeptical evaluation
    META = "meta"           # Reasoning about reasoning


@dataclass
class ThoughtNode:
    """A node in the thought tree"""
    id: str
    content: str
    value: float = 0.0
    visits: int = 0
    parent_id: Optional[str] = None
    children_ids: List[str] = field(default_factory=list)
    reasoning_mode: ReasoningMode = ReasoningMode.FAST
    evidence: List[Dict] = field(default_factory=list)
    confidence: float = 0.5
    timestamp: datetime = field(default_factory=datetime.now)
    
    def ucb1(self, parent_visits: int, exploration: float = 1.414) -> float:
        """Upper Confidence Bound for tree search"""
        if self.visits == 0:
            return float('inf')
        exploitation = self.value / self.visits
        exploration_term = exploration * math.sqrt(math.log(parent_visits) / self.visits)
        return exploitation + exploration_term


class TreeOfThought:
    """
    Tree-of-Thought reasoning system.
    
    Instead of linear chain-of-thought, this explores multiple
    reasoning paths and selects the best one.
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {
            "max_depth": 5,
            "branching_factor": 3,
            "exploration_constant": 1.414,
            "min_visits": 10
        }
        
        self.nodes: Dict[str, ThoughtNode] = {}
        self.root_id: Optional[str] = None
        self.node_counter = 0
    
    def create_root(self, content: str, context: Dict) -> str:
        """Create the root thought"""
        node_id = self._generate_id()
        
        self.nodes[node_id] = ThoughtNode(
            id=node_id,
            content=content,
            reasoning_mode=ReasoningMode.FAST,
            evidence=[context]
        )
        
        self.root_id = node_id
        return node_id
    
    def expand(self, node_id: str, thoughts: List[str]) -> List[str]:
        """Expand a node with multiple child thoughts"""
        if node_id not in self.nodes:
            return []
        
        parent = self.nodes[node_id]
        child_ids = []
        
        for thought in thoughts:
            child_id = self._generate_id()
            child_node = ThoughtNode(
                id=child_id,
                content=thought,
                parent_id=node_id,
                reasoning_mode=ReasoningMode.SLOW
            )
            
            self.nodes[child_id] = child_node
            parent.children_ids.append(child_id)
            child_ids.append(child_id)
        
        return child_ids
    
    def select(self) -> str:
        """Select the most promising node to expand (UCB1)"""
        if not self.root_id:
            return ""
        
        current_id = self.root_id
        
        while True:
            current = self.nodes[current_id]
            
            if not current.children_ids:
                return current_id
            
            # Select child with highest UCB1
            best_child_id = None
            best_ucb = -float('inf')
            
            for child_id in current.children_ids:
                child = self.nodes[child_id]
                ucb = child.ucb1(current.visits, self.config["exploration_constant"])
                
                if ucb > best_ucb:
                    best_ucb = ucb
                    best_child_id = child_id
            
            if best_child_id:
                current_id = best_child_id
            else:
                break
        
        return current_id
    
    def backpropagate(self, node_id: str, value: float):
        """Backpropagate value up the tree"""
        current_id = node_id
        
        while current_id:
            node = self.nodes[current_id]
            node.visits += 1
            node.value += value
            current_id = node.parent_id
    
    def get_best_path(self) -> List[ThoughtNode]:
        """Get the best reasoning path"""
        if not self.root_id:
            return []
        
        path = []
        current_id = self.root_id
        
        while current_id:
            node = self.nodes[current_id]
            path.append(node)
            
            if not node.children_ids:
                break
            
            # Select child with highest average value
            best_child_id = None
            best_value = -float('inf')
            
            for child_id in node.children_ids:
                child = self.nodes[child_id]
                if child.visits > 0:
                    avg_value = child.value / child.visits
                    if avg_value > best_value:
                        best_value = avg_value
                        best_child_id = child_id
            
            current_id = best_child_id
        
        return path
    
    def to_text(self) -> str:
        """Convert best path to readable text"""
        path = self.get_best_path()
        lines = []
        
        for i, node in enumerate(path):
            indent = "  " * i
            lines.append(f"{indent}[{node.reasoning_mode.value}] {node.content}")
            lines.append(f"{indent}  (confidence: {node.confidence:.1%}, visits: {node.visits})")
        
        return "\n".join(lines)
    
    def _generate_id(self) -> str:
        """Generate unique node ID"""
        self.node_counter += 1
        return f"thought_{self.node_counter}_{datetime.now().strftime('%H%M%S')}"


class CausalReasoner:
    """
    Causal reasoning about market movements.
    
    This goes beyond correlation to understand WHY prices move.
    """
    
    def __init__(self):
        # Causal graph of market factors
        self.causal_graph = {
            "institutional_flow": ["price_direction", "volume_spike"],
            "news_event": ["volatility", "price_direction"],
            "liquidity_sweep": ["reversal", "volume_spike"],
            "order_imbalance": ["price_direction", "momentum"],
            "support_break": ["price_direction", "stop_hunt"],
            "resistance_break": ["price_direction", "breakout"],
            "delta_divergence": ["reversal", "exhaustion"],
            "volume_climax": ["reversal", "exhaustion"],
            "absorption": ["reversal", "accumulation"],
            "session_open": ["volatility", "liquidity"],
            "session_close": ["volatility", "position_squaring"]
        }
        
        # Effect probabilities (learned from data)
        self.effect_probabilities = defaultdict(lambda: 0.5)
    
    def infer_causes(self, observed_effects: List[str]) -> List[Tuple[str, float]]:
        """Infer likely causes from observed effects"""
        cause_scores = defaultdict(float)
        
        for cause, effects in self.causal_graph.items():
            for effect in observed_effects:
                if effect in effects:
                    # Bayesian update
                    prior = 0.3  # Prior probability of cause
                    likelihood = self.effect_probabilities[(cause, effect)]
                    cause_scores[cause] += prior * likelihood
        
        # Normalize and sort
        total = sum(cause_scores.values()) or 1
        causes = [(cause, score / total) for cause, score in cause_scores.items()]
        causes.sort(key=lambda x: x[1], reverse=True)
        
        return causes
    
    def predict_effects(self, causes: List[str]) -> List[Tuple[str, float]]:
        """Predict effects from causes"""
        effect_scores = defaultdict(float)
        
        for cause in causes:
            if cause in self.causal_graph:
                for effect in self.causal_graph[cause]:
                    prob = self.effect_probabilities[(cause, effect)]
                    effect_scores[effect] = max(effect_scores[effect], prob)
        
        effects = [(effect, score) for effect, score in effect_scores.items()]
        effects.sort(key=lambda x: x[1], reverse=True)
        
        return effects
    
    def counterfactual(self, actual: Dict, intervention: Dict) -> Dict:
        """
        Counterfactual reasoning: What would have happened if...
        
        This is crucial for learning from mistakes.
        """
        # Start with actual outcome
        counterfactual_outcome = actual.copy()
        
        # Apply intervention effects
        for cause, value in intervention.items():
            if cause in self.causal_graph:
                effects = self.causal_graph[cause]
                for effect in effects:
                    # Modify outcome based on intervention
                    if effect in counterfactual_outcome:
                        # Simple linear intervention effect
                        counterfactual_outcome[effect] *= (1 + value * 0.5)
        
        return counterfactual_outcome
    
    def update_probabilities(self, cause: str, effect: str, observed: bool):
        """Update effect probabilities based on observation"""
        key = (cause, effect)
        current = self.effect_probabilities[key]
        
        # Bayesian update
        if observed:
            self.effect_probabilities[key] = current * 0.9 + 0.1
        else:
            self.effect_probabilities[key] = current * 0.9


class MetaCognition:
    """
    Meta-cognitive monitoring - thinking about thinking.
    
    This allows the AGI to:
    1. Monitor its own reasoning quality
    2. Detect when it's uncertain
    3. Know when to seek more information
    4. Calibrate its confidence
    """
    
    def __init__(self):
        self.reasoning_history: List[Dict] = []
        self.confidence_calibration: Dict[str, List[Tuple[float, bool]]] = defaultdict(list)
        self.decision_outcomes: List[Dict] = []
    
    def evaluate_reasoning(self, reasoning_chain: List[Dict]) -> Dict:
        """Evaluate the quality of a reasoning chain"""
        if not reasoning_chain:
            return {"quality": 0.0, "issues": ["empty_reasoning"]}
        
        issues = []
        quality = 1.0
        
        # Check for logical consistency
        directions = set()
        for step in reasoning_chain:
            if "direction" in step:
                directions.add(step["direction"])
        
        if len(directions) > 1 and "NEUTRAL" not in directions:
            issues.append("contradictory_conclusions")
            quality *= 0.7
        
        # Check for evidence support
        unsupported = sum(1 for step in reasoning_chain if not step.get("evidence"))
        if unsupported > len(reasoning_chain) * 0.5:
            issues.append("insufficient_evidence")
            quality *= 0.8
        
        # Check for overconfidence
        high_confidence = sum(1 for step in reasoning_chain if step.get("confidence", 0) > 0.9)
        if high_confidence > len(reasoning_chain) * 0.3:
            issues.append("potential_overconfidence")
            quality *= 0.9
        
        # Check reasoning depth
        if len(reasoning_chain) < 3:
            issues.append("shallow_reasoning")
            quality *= 0.85
        
        return {
            "quality": quality,
            "issues": issues,
            "depth": len(reasoning_chain),
            "avg_confidence": sum(s.get("confidence", 0.5) for s in reasoning_chain) / len(reasoning_chain)
        }
    
    def calibrate_confidence(self, domain: str, predicted_confidence: float, actual_outcome: bool):
        """Calibrate confidence based on outcomes"""
        self.confidence_calibration[domain].append((predicted_confidence, actual_outcome))
        
        # Keep only recent history
        if len(self.confidence_calibration[domain]) > 100:
            self.confidence_calibration[domain] = self.confidence_calibration[domain][-100:]
    
    def get_calibration_adjustment(self, domain: str, raw_confidence: float) -> float:
        """Get calibrated confidence based on historical accuracy"""
        history = self.confidence_calibration[domain]
        
        if len(history) < 10:
            return raw_confidence
        
        # Group by confidence buckets
        buckets = defaultdict(list)
        for conf, outcome in history:
            bucket = round(conf, 1)
            buckets[bucket].append(outcome)
        
        # Find closest bucket
        closest_bucket = round(raw_confidence, 1)
        if closest_bucket in buckets:
            actual_accuracy = sum(buckets[closest_bucket]) / len(buckets[closest_bucket])
            # Blend raw confidence with historical accuracy
            return raw_confidence * 0.5 + actual_accuracy * 0.5
        
        return raw_confidence
    
    def should_seek_more_info(self, current_confidence: float, decision_importance: float) -> bool:
        """Determine if more information should be gathered"""
        # Higher importance decisions require higher confidence
        required_confidence = 0.5 + decision_importance * 0.3
        
        return current_confidence < required_confidence
    
    def record_decision(self, decision: Dict, outcome: Dict):
        """Record a decision and its outcome for learning"""
        self.decision_outcomes.append({
            "decision": decision,
            "outcome": outcome,
            "timestamp": datetime.now().isoformat()
        })
        
        # Calibrate confidence
        domain = decision.get("domain", "general")
        confidence = decision.get("confidence", 0.5)
        success = outcome.get("success", False)
        
        self.calibrate_confidence(domain, confidence, success)


class AdvancedReasoningEngine:
    """
    The complete advanced reasoning engine.
    
    Combines:
    - Tree-of-Thought for exploring multiple paths
    - Causal reasoning for understanding WHY
    - Meta-cognition for self-monitoring
    - Monte Carlo search for decision making
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        
        self.tree = TreeOfThought()
        self.causal = CausalReasoner()
        self.meta = MetaCognition()
        
        # Reasoning state
        self.current_mode = ReasoningMode.FAST
        self.reasoning_depth = 0
    
    async def reason(self, context: Dict, question: str) -> Dict:
        """
        Perform advanced reasoning on a question.
        
        This is the main entry point for deep reasoning.
        """
        # Create root thought
        root_id = self.tree.create_root(
            f"Analyzing: {question}",
            context
        )
        
        # Generate initial hypotheses
        hypotheses = self._generate_hypotheses(context, question)
        
        # Expand tree with hypotheses
        hypothesis_ids = self.tree.expand(root_id, hypotheses)
        
        # Monte Carlo Tree Search
        for _ in range(self.config.get("mcts_iterations", 50)):
            # Select
            node_id = self.tree.select()
            
            # Expand
            node = self.tree.nodes[node_id]
            if node.visits > 0 and len(node.children_ids) < 3:
                sub_thoughts = self._generate_sub_thoughts(node, context)
                self.tree.expand(node_id, sub_thoughts)
            
            # Simulate
            value = self._simulate(node, context)
            
            # Backpropagate
            self.tree.backpropagate(node_id, value)
        
        # Get best path
        best_path = self.tree.get_best_path()
        
        # Evaluate reasoning quality
        reasoning_chain = [{"content": n.content, "confidence": n.confidence, "evidence": n.evidence} 
                          for n in best_path]
        quality = self.meta.evaluate_reasoning(reasoning_chain)
        
        # Causal analysis
        observed_effects = self._extract_effects(context)
        likely_causes = self.causal.infer_causes(observed_effects)
        predicted_effects = self.causal.predict_effects([c[0] for c in likely_causes[:3]])
        
        # Final conclusion
        conclusion = self._synthesize_conclusion(best_path, likely_causes, predicted_effects)
        
        return {
            "conclusion": conclusion,
            "reasoning_path": self.tree.to_text(),
            "quality": quality,
            "causal_analysis": {
                "likely_causes": likely_causes[:5],
                "predicted_effects": predicted_effects[:5]
            },
            "confidence": self._calculate_final_confidence(best_path, quality)
        }
    
    def _generate_hypotheses(self, context: Dict, question: str) -> List[str]:
        """Generate initial hypotheses"""
        hypotheses = []
        
        # Market direction hypotheses
        price = context.get("price", 0)
        delta = context.get("delta", 0)
        volume = context.get("volume", 0)
        
        if delta > 0:
            hypotheses.append(f"Bullish hypothesis: Positive delta ({delta}) suggests buying pressure")
        if delta < 0:
            hypotheses.append(f"Bearish hypothesis: Negative delta ({delta}) suggests selling pressure")
        
        # Volume analysis
        avg_volume = context.get("avg_volume", volume)
        if volume > avg_volume * 1.5:
            hypotheses.append("High volume hypothesis: Significant market interest, potential breakout")
        
        # Pattern-based hypotheses
        patterns = context.get("patterns", [])
        for pattern in patterns:
            hypotheses.append(f"Pattern hypothesis: {pattern.get('name', 'unknown')} suggests {pattern.get('bias', 'neutral')} bias")
        
        # Regime-based hypothesis
        regime = context.get("regime", "UNKNOWN")
        hypotheses.append(f"Regime hypothesis: Current {regime} regime affects strategy selection")
        
        # Default hypothesis
        if not hypotheses:
            hypotheses.append("Neutral hypothesis: Insufficient evidence for directional bias")
        
        return hypotheses[:5]  # Limit to 5 hypotheses
    
    def _generate_sub_thoughts(self, node: ThoughtNode, context: Dict) -> List[str]:
        """Generate sub-thoughts for a node"""
        content = node.content.lower()
        sub_thoughts = []
        
        if "bullish" in content:
            sub_thoughts.extend([
                "Supporting evidence: Check for higher lows and higher highs",
                "Risk consideration: Where would this thesis be invalidated?",
                "Entry timing: What's the optimal entry point?"
            ])
        elif "bearish" in content:
            sub_thoughts.extend([
                "Supporting evidence: Check for lower highs and lower lows",
                "Risk consideration: Where would this thesis be invalidated?",
                "Entry timing: What's the optimal entry point?"
            ])
        elif "volume" in content:
            sub_thoughts.extend([
                "Volume analysis: Is this accumulation or distribution?",
                "Delta confirmation: Does delta support the volume thesis?",
                "Historical comparison: How does this compare to similar events?"
            ])
        else:
            sub_thoughts.extend([
                "Further analysis needed: Gather more evidence",
                "Alternative explanation: Consider other possibilities",
                "Risk assessment: What could go wrong?"
            ])
        
        return sub_thoughts[:3]
    
    def _simulate(self, node: ThoughtNode, context: Dict) -> float:
        """Simulate the value of a thought path"""
        # Simple simulation based on content analysis
        content = node.content.lower()
        value = 0.5
        
        # Positive indicators
        positive_words = ["bullish", "support", "accumulation", "breakout", "momentum"]
        negative_words = ["bearish", "resistance", "distribution", "breakdown", "exhaustion"]
        
        for word in positive_words:
            if word in content:
                value += 0.1
        
        for word in negative_words:
            if word in content:
                value -= 0.1
        
        # Context alignment
        delta = context.get("delta", 0)
        if delta > 0 and "bullish" in content:
            value += 0.2
        elif delta < 0 and "bearish" in content:
            value += 0.2
        
        # Add some randomness for exploration
        value += random.uniform(-0.1, 0.1)
        
        return max(0, min(1, value))
    
    def _extract_effects(self, context: Dict) -> List[str]:
        """Extract observed effects from context"""
        effects = []
        
        delta = context.get("delta", 0)
        volume = context.get("volume", 0)
        avg_volume = context.get("avg_volume", volume)
        
        if delta > 500:
            effects.append("price_direction")
        if delta < -500:
            effects.append("price_direction")
        
        if volume > avg_volume * 1.5:
            effects.append("volume_spike")
        
        patterns = context.get("patterns", [])
        for pattern in patterns:
            if "reversal" in pattern.get("name", "").lower():
                effects.append("reversal")
            if "breakout" in pattern.get("name", "").lower():
                effects.append("breakout")
        
        return effects
    
    def _synthesize_conclusion(
        self,
        path: List[ThoughtNode],
        causes: List[Tuple[str, float]],
        effects: List[Tuple[str, float]]
    ) -> Dict:
        """Synthesize final conclusion from reasoning"""
        # Analyze path for direction
        bullish_score = 0
        bearish_score = 0
        
        for node in path:
            content = node.content.lower()
            if "bullish" in content or "buy" in content or "long" in content:
                bullish_score += node.confidence
            if "bearish" in content or "sell" in content or "short" in content:
                bearish_score += node.confidence
        
        # Determine direction
        if bullish_score > bearish_score * 1.2:
            direction = "LONG"
            confidence = bullish_score / (bullish_score + bearish_score + 0.1)
        elif bearish_score > bullish_score * 1.2:
            direction = "SHORT"
            confidence = bearish_score / (bullish_score + bearish_score + 0.1)
        else:
            direction = "NEUTRAL"
            confidence = 0.5
        
        # Build reasoning summary
        reasoning = []
        for node in path[:3]:  # Top 3 thoughts
            reasoning.append(node.content)
        
        # Add causal insights
        if causes:
            top_cause = causes[0]
            reasoning.append(f"Likely cause: {top_cause[0]} ({top_cause[1]:.1%})")
        
        if effects:
            top_effect = effects[0]
            reasoning.append(f"Expected effect: {top_effect[0]} ({top_effect[1]:.1%})")
        
        return {
            "direction": direction,
            "confidence": confidence,
            "reasoning": reasoning,
            "bullish_score": bullish_score,
            "bearish_score": bearish_score
        }
    
    def _calculate_final_confidence(self, path: List[ThoughtNode], quality: Dict) -> float:
        """Calculate final confidence with calibration"""
        if not path:
            return 0.0
        
        # Base confidence from path
        base_confidence = sum(n.confidence for n in path) / len(path)
        
        # Adjust for reasoning quality
        quality_factor = quality.get("quality", 1.0)
        
        # Apply calibration
        calibrated = self.meta.get_calibration_adjustment("trading", base_confidence)
        
        return calibrated * quality_factor


# Factory function
def create_advanced_reasoning_engine(config: Optional[Dict] = None) -> AdvancedReasoningEngine:
    """Create an advanced reasoning engine"""
    return AdvancedReasoningEngine(config)
