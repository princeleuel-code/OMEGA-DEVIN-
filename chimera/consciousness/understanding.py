"""
LAYER 2: UNDERSTANDING - Causal World Model

The second layer of consciousness: UNDERSTANDING why prices move.

This module builds a CAUSAL MODEL of market dynamics:
- What causes price to move?
- What are the relationships between features?
- What would happen if X changed?

This is NOT correlation - this is CAUSATION.

The causal model allows:
1. Counterfactual reasoning: "What would have happened if...?"
2. Intervention reasoning: "If I do X, what happens to Y?"
3. Robust predictions: Predictions that work even when correlations break

Inspired by:
- Judea Pearl's Causal Inference
- Structural Causal Models (SCM)
- Do-calculus for interventions
- Transfer entropy for information flow
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Set, Tuple
from enum import Enum
import numpy as np
from collections import defaultdict

from .perception import MarketState, MarketRegime


class CausalRelationType(Enum):
    """Types of causal relationships."""
    DIRECT = "direct"           # X directly causes Y
    INDIRECT = "indirect"       # X causes Y through mediators
    CONFOUNDED = "confounded"   # X and Y share a common cause
    COLLIDER = "collider"       # X and Y both cause Z
    NONE = "none"               # No causal relationship


@dataclass
class CausalEdge:
    """A directed edge in the causal graph."""
    source: str
    target: str
    relation_type: CausalRelationType
    strength: float  # -1 to 1 (negative = inverse relationship)
    confidence: float  # 0 to 1
    lag: int = 0  # Time lag in bars
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "source": self.source,
            "target": self.target,
            "relation_type": self.relation_type.value,
            "strength": self.strength,
            "confidence": self.confidence,
            "lag": self.lag,
        }


@dataclass
class CausalNode:
    """A node in the causal graph."""
    name: str
    node_type: str  # "observable", "latent", "intervention"
    current_value: Optional[float] = None
    historical_values: List[float] = field(default_factory=list)
    
    # Causal parents and children
    parents: List[str] = field(default_factory=list)
    children: List[str] = field(default_factory=list)
    
    # Structural equation: value = f(parents) + noise
    # Represented as linear combination for simplicity
    parent_coefficients: Dict[str, float] = field(default_factory=dict)
    noise_std: float = 0.1


@dataclass
class CausalGraph:
    """
    The causal graph representing market dynamics.
    
    This is a Directed Acyclic Graph (DAG) where:
    - Nodes are market variables (price, volume, volatility, etc.)
    - Edges represent causal relationships
    - Edge weights represent causal strength
    """
    nodes: Dict[str, CausalNode] = field(default_factory=dict)
    edges: List[CausalEdge] = field(default_factory=list)
    
    # Adjacency list for efficient traversal
    adjacency: Dict[str, List[str]] = field(default_factory=lambda: defaultdict(list))
    reverse_adjacency: Dict[str, List[str]] = field(default_factory=lambda: defaultdict(list))
    
    def add_node(self, node: CausalNode) -> None:
        """Add a node to the graph."""
        self.nodes[node.name] = node
    
    def add_edge(self, edge: CausalEdge) -> None:
        """Add an edge to the graph."""
        self.edges.append(edge)
        self.adjacency[edge.source].append(edge.target)
        self.reverse_adjacency[edge.target].append(edge.source)
        
        # Update node parent/child relationships
        if edge.source in self.nodes:
            self.nodes[edge.source].children.append(edge.target)
        if edge.target in self.nodes:
            self.nodes[edge.target].parents.append(edge.source)
            self.nodes[edge.target].parent_coefficients[edge.source] = edge.strength
    
    def get_ancestors(self, node_name: str) -> Set[str]:
        """Get all ancestors of a node (transitive closure of parents)."""
        ancestors = set()
        to_visit = list(self.reverse_adjacency[node_name])
        
        while to_visit:
            current = to_visit.pop()
            if current not in ancestors:
                ancestors.add(current)
                to_visit.extend(self.reverse_adjacency[current])
        
        return ancestors
    
    def get_descendants(self, node_name: str) -> Set[str]:
        """Get all descendants of a node (transitive closure of children)."""
        descendants = set()
        to_visit = list(self.adjacency[node_name])
        
        while to_visit:
            current = to_visit.pop()
            if current not in descendants:
                descendants.add(current)
                to_visit.extend(self.adjacency[current])
        
        return descendants
    
    def get_edge(self, source: str, target: str) -> Optional[CausalEdge]:
        """Get edge between two nodes."""
        for edge in self.edges:
            if edge.source == source and edge.target == target:
                return edge
        return None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "nodes": list(self.nodes.keys()),
            "edges": [e.to_dict() for e in self.edges],
        }


@dataclass
class CausalQuery:
    """A causal query to be answered by the world model."""
    query_type: str  # "predict", "counterfactual", "intervention"
    target: str  # Variable to predict
    conditions: Dict[str, float] = field(default_factory=dict)  # Observed values
    interventions: Dict[str, float] = field(default_factory=dict)  # do(X=x)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "query_type": self.query_type,
            "target": self.target,
            "conditions": self.conditions,
            "interventions": self.interventions,
        }


@dataclass
class CausalAnswer:
    """Answer to a causal query."""
    query: CausalQuery
    prediction: float
    uncertainty: float
    confidence: float
    reasoning: List[str]  # Chain of causal reasoning
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "query": self.query.to_dict(),
            "prediction": self.prediction,
            "uncertainty": self.uncertainty,
            "confidence": self.confidence,
            "reasoning": self.reasoning,
        }


class CausalWorldModel:
    """
    The causal world model that understands WHY prices move.
    
    This model:
    1. Learns causal structure from data (causal discovery)
    2. Estimates causal effects (causal inference)
    3. Answers counterfactual queries
    4. Supports interventional reasoning
    """
    
    # Core market variables
    CORE_VARIABLES = [
        "price_return",
        "volume",
        "volatility",
        "order_flow",
        "spread",
        "book_imbalance",
        "momentum",
        "trend",
        "regime",
    ]
    
    def __init__(self):
        # The causal graph
        self.graph = CausalGraph()
        
        # Initialize with prior knowledge
        self._init_prior_graph()
        
        # Historical data for learning
        self.history: List[Dict[str, float]] = []
        self.max_history = 10000
        
        # Transfer entropy estimates
        self.transfer_entropy: Dict[Tuple[str, str], float] = {}
        
        # Granger causality p-values
        self.granger_pvalues: Dict[Tuple[str, str], float] = {}
        
        # Model confidence
        self.model_confidence = 0.5
    
    def _init_prior_graph(self) -> None:
        """Initialize causal graph with prior knowledge about markets."""
        # Add nodes for core variables
        for var in self.CORE_VARIABLES:
            self.graph.add_node(CausalNode(
                name=var,
                node_type="observable",
            ))
        
        # Add latent variables
        self.graph.add_node(CausalNode(
            name="informed_trading",
            node_type="latent",
        ))
        self.graph.add_node(CausalNode(
            name="market_sentiment",
            node_type="latent",
        ))
        
        # Prior causal relationships (based on market microstructure theory)
        prior_edges = [
            # Order flow causes price returns (Kyle's Lambda)
            ("order_flow", "price_return", 0.6, 0),
            
            # Volume causes volatility (volume-volatility relationship)
            ("volume", "volatility", 0.4, 0),
            
            # Spread affects price returns (transaction costs)
            ("spread", "price_return", -0.2, 0),
            
            # Book imbalance predicts order flow
            ("book_imbalance", "order_flow", 0.5, 1),
            
            # Momentum predicts returns (short-term)
            ("momentum", "price_return", 0.3, 1),
            
            # Trend affects momentum
            ("trend", "momentum", 0.4, 0),
            
            # Regime affects volatility
            ("regime", "volatility", 0.5, 0),
            
            # Informed trading affects order flow and volatility
            ("informed_trading", "order_flow", 0.7, 0),
            ("informed_trading", "volatility", 0.3, 0),
            
            # Market sentiment affects trend and volume
            ("market_sentiment", "trend", 0.5, 0),
            ("market_sentiment", "volume", 0.3, 0),
            
            # Volatility affects spread (market makers widen spreads)
            ("volatility", "spread", 0.6, 0),
            
            # Price returns affect momentum (by definition)
            ("price_return", "momentum", 0.8, 1),
        ]
        
        for source, target, strength, lag in prior_edges:
            self.graph.add_edge(CausalEdge(
                source=source,
                target=target,
                relation_type=CausalRelationType.DIRECT,
                strength=strength,
                confidence=0.7,  # Prior confidence
                lag=lag,
            ))
    
    def update(self, state: MarketState) -> None:
        """Update the causal model with new market state."""
        # Extract features from state
        features = self._extract_features(state)
        
        # Add to history
        self.history.append(features)
        if len(self.history) > self.max_history:
            self.history = self.history[-self.max_history:]
        
        # Update node values
        for var, value in features.items():
            if var in self.graph.nodes:
                self.graph.nodes[var].current_value = value
                self.graph.nodes[var].historical_values.append(value)
                if len(self.graph.nodes[var].historical_values) > 1000:
                    self.graph.nodes[var].historical_values = \
                        self.graph.nodes[var].historical_values[-1000:]
        
        # Periodically update causal structure
        if len(self.history) % 100 == 0 and len(self.history) >= 200:
            self._update_causal_structure()
    
    def _extract_features(self, state: MarketState) -> Dict[str, float]:
        """Extract causal variables from market state."""
        features = {}
        
        # Price return (from embedding or compute)
        if state.embedding is not None:
            features["price_return"] = float(state.embedding[1])  # momentum proxy
        else:
            features["price_return"] = 0.0
        
        # Volume (normalized)
        features["volume"] = 0.5  # Would need actual volume data
        
        # Volatility
        if state.timeframe_states:
            vols = [s.volatility for s in state.timeframe_states.values()]
            features["volatility"] = float(np.mean(vols)) if vols else 0.0
        else:
            features["volatility"] = 0.0
        
        # Order flow
        features["order_flow"] = state.order_flow_score
        
        # Spread
        if state.spread and state.price > 0:
            features["spread"] = state.spread / state.price * 10000  # In bps
        else:
            features["spread"] = 0.0
        
        # Book imbalance (from liquidity score)
        features["book_imbalance"] = state.liquidity_score - 0.5
        
        # Momentum
        if state.timeframe_states:
            moms = [s.momentum for s in state.timeframe_states.values()]
            features["momentum"] = float(np.mean(moms)) if moms else 0.0
        else:
            features["momentum"] = 0.0
        
        # Trend
        if state.timeframe_states:
            trends = [s.trend_direction for s in state.timeframe_states.values()]
            features["trend"] = float(np.mean(trends)) if trends else 0.0
        else:
            features["trend"] = 0.0
        
        # Regime (encoded as number)
        regime_encoding = {
            MarketRegime.TRENDING_BULLISH: 1.0,
            MarketRegime.TRENDING_BEARISH: -1.0,
            MarketRegime.MEAN_REVERTING: 0.0,
            MarketRegime.HIGH_VOLATILITY: 0.5,
            MarketRegime.LOW_VOLATILITY: -0.5,
            MarketRegime.BREAKOUT: 0.8,
            MarketRegime.CONSOLIDATION: -0.3,
            MarketRegime.UNKNOWN: 0.0,
        }
        features["regime"] = regime_encoding.get(state.primary_regime, 0.0)
        
        return features
    
    def _update_causal_structure(self) -> None:
        """Update causal structure using causal discovery algorithms."""
        if len(self.history) < 200:
            return
        
        # Convert history to numpy arrays
        data = {}
        for var in self.CORE_VARIABLES:
            values = [h.get(var, 0.0) for h in self.history]
            data[var] = np.array(values)
        
        # Update transfer entropy estimates
        self._compute_transfer_entropy(data)
        
        # Update Granger causality
        self._compute_granger_causality(data)
        
        # Update edge strengths based on evidence
        self._update_edge_strengths()
        
        # Update model confidence
        self._update_model_confidence()
    
    def _compute_transfer_entropy(self, data: Dict[str, np.ndarray]) -> None:
        """Compute transfer entropy between all pairs of variables."""
        for source in self.CORE_VARIABLES:
            for target in self.CORE_VARIABLES:
                if source != target:
                    te = self._transfer_entropy(data[source], data[target])
                    self.transfer_entropy[(source, target)] = te
    
    def _transfer_entropy(
        self, 
        source: np.ndarray, 
        target: np.ndarray, 
        lag: int = 1,
        bins: int = 10
    ) -> float:
        """
        Compute transfer entropy from source to target.
        
        TE(X->Y) = H(Y_t | Y_{t-1}) - H(Y_t | Y_{t-1}, X_{t-1})
        
        Higher TE means X provides more information about Y's future.
        """
        if len(source) < lag + 10 or len(target) < lag + 10:
            return 0.0
        
        # Discretize
        source_disc = np.digitize(source, np.linspace(source.min(), source.max(), bins))
        target_disc = np.digitize(target, np.linspace(target.min(), target.max(), bins))
        
        # Create lagged versions
        y_t = target_disc[lag:]
        y_past = target_disc[:-lag]
        x_past = source_disc[:-lag]
        
        # Compute entropies using histogram-based estimation
        def entropy(x):
            counts = np.bincount(x)
            probs = counts[counts > 0] / len(x)
            return -np.sum(probs * np.log2(probs + 1e-10))
        
        def joint_entropy(x, y):
            # Simple 2D histogram
            joint = np.zeros((bins + 1, bins + 1))
            for i in range(len(x)):
                joint[x[i], y[i]] += 1
            joint = joint / joint.sum()
            joint = joint[joint > 0]
            return -np.sum(joint * np.log2(joint + 1e-10))
        
        # H(Y_t | Y_{t-1}) = H(Y_t, Y_{t-1}) - H(Y_{t-1})
        h_y_given_ypast = joint_entropy(y_t, y_past) - entropy(y_past)
        
        # H(Y_t | Y_{t-1}, X_{t-1}) - approximated
        # Create combined past state
        combined_past = y_past * (bins + 1) + x_past
        h_y_given_both = joint_entropy(y_t, combined_past) - entropy(combined_past)
        
        # Transfer entropy
        te = max(0, h_y_given_ypast - h_y_given_both)
        
        return float(te)
    
    def _compute_granger_causality(self, data: Dict[str, np.ndarray]) -> None:
        """Compute Granger causality p-values between all pairs."""
        for source in self.CORE_VARIABLES:
            for target in self.CORE_VARIABLES:
                if source != target:
                    pvalue = self._granger_test(data[source], data[target])
                    self.granger_pvalues[(source, target)] = pvalue
    
    def _granger_test(
        self, 
        source: np.ndarray, 
        target: np.ndarray, 
        max_lag: int = 5
    ) -> float:
        """
        Simple Granger causality test.
        
        Returns p-value (lower = more likely causal).
        """
        if len(source) < max_lag + 20:
            return 1.0
        
        # Create lagged features
        n = len(target) - max_lag
        
        # Restricted model: Y_t ~ Y_{t-1}, ..., Y_{t-lag}
        y = target[max_lag:]
        X_restricted = np.column_stack([
            target[max_lag-i-1:-i-1] for i in range(max_lag)
        ])
        
        # Unrestricted model: Y_t ~ Y_{t-1}, ..., Y_{t-lag}, X_{t-1}, ..., X_{t-lag}
        X_unrestricted = np.column_stack([
            X_restricted,
            *[source[max_lag-i-1:-i-1] for i in range(max_lag)]
        ])
        
        # Fit models using least squares
        try:
            # Restricted
            beta_r = np.linalg.lstsq(X_restricted, y, rcond=None)[0]
            resid_r = y - X_restricted @ beta_r
            rss_r = np.sum(resid_r ** 2)
            
            # Unrestricted
            beta_u = np.linalg.lstsq(X_unrestricted, y, rcond=None)[0]
            resid_u = y - X_unrestricted @ beta_u
            rss_u = np.sum(resid_u ** 2)
            
            # F-statistic
            df1 = max_lag
            df2 = n - 2 * max_lag
            
            if rss_u == 0 or df2 <= 0:
                return 1.0
            
            f_stat = ((rss_r - rss_u) / df1) / (rss_u / df2)
            
            # Approximate p-value using F-distribution
            # For simplicity, use a threshold-based approach
            if f_stat > 3.0:
                return 0.01
            elif f_stat > 2.0:
                return 0.05
            elif f_stat > 1.5:
                return 0.1
            else:
                return 0.5
                
        except Exception:
            return 1.0
    
    def _update_edge_strengths(self) -> None:
        """Update edge strengths based on transfer entropy and Granger causality."""
        for edge in self.graph.edges:
            key = (edge.source, edge.target)
            
            # Get evidence
            te = self.transfer_entropy.get(key, 0.0)
            pvalue = self.granger_pvalues.get(key, 1.0)
            
            # Update confidence based on evidence
            te_confidence = min(1.0, te * 5)  # Scale TE to confidence
            granger_confidence = 1 - pvalue
            
            # Combine with prior
            prior_confidence = edge.confidence
            new_confidence = 0.3 * prior_confidence + 0.4 * te_confidence + 0.3 * granger_confidence
            
            edge.confidence = new_confidence
            
            # Update strength based on correlation
            if edge.source in self.graph.nodes and edge.target in self.graph.nodes:
                source_vals = self.graph.nodes[edge.source].historical_values
                target_vals = self.graph.nodes[edge.target].historical_values
                
                if len(source_vals) > 10 and len(target_vals) > 10:
                    min_len = min(len(source_vals), len(target_vals))
                    corr = np.corrcoef(source_vals[-min_len:], target_vals[-min_len:])[0, 1]
                    if not np.isnan(corr):
                        # Blend prior strength with observed correlation
                        edge.strength = 0.5 * edge.strength + 0.5 * corr
    
    def _update_model_confidence(self) -> None:
        """Update overall model confidence."""
        if not self.graph.edges:
            self.model_confidence = 0.5
            return
        
        # Average edge confidence
        avg_confidence = np.mean([e.confidence for e in self.graph.edges])
        
        # Data sufficiency
        data_factor = min(1.0, len(self.history) / 1000)
        
        self.model_confidence = 0.7 * avg_confidence + 0.3 * data_factor
    
    def query(self, query: CausalQuery) -> CausalAnswer:
        """
        Answer a causal query.
        
        Supports:
        - Prediction: P(Y | X=x)
        - Counterfactual: P(Y_x | X=x') - what would Y be if X had been x'?
        - Intervention: P(Y | do(X=x)) - what happens to Y if we set X to x?
        """
        if query.query_type == "predict":
            return self._predict(query)
        elif query.query_type == "counterfactual":
            return self._counterfactual(query)
        elif query.query_type == "intervention":
            return self._intervention(query)
        else:
            return CausalAnswer(
                query=query,
                prediction=0.0,
                uncertainty=1.0,
                confidence=0.0,
                reasoning=["Unknown query type"],
            )
    
    def _predict(self, query: CausalQuery) -> CausalAnswer:
        """Predict target given conditions (observational)."""
        target = query.target
        conditions = query.conditions
        
        if target not in self.graph.nodes:
            return CausalAnswer(
                query=query,
                prediction=0.0,
                uncertainty=1.0,
                confidence=0.0,
                reasoning=[f"Unknown target variable: {target}"],
            )
        
        # Get parents of target
        node = self.graph.nodes[target]
        reasoning = []
        
        # Compute prediction using structural equation
        prediction = 0.0
        total_weight = 0.0
        
        for parent in node.parents:
            if parent in conditions:
                coef = node.parent_coefficients.get(parent, 0.0)
                contribution = coef * conditions[parent]
                prediction += contribution
                total_weight += abs(coef)
                reasoning.append(f"{parent} ({conditions[parent]:.2f}) * {coef:.2f} = {contribution:.2f}")
        
        # Add current value as prior if no conditions
        if total_weight == 0 and node.current_value is not None:
            prediction = node.current_value
            reasoning.append(f"Using current value: {prediction:.2f}")
        
        # Uncertainty from noise and missing parents
        missing_parents = [p for p in node.parents if p not in conditions]
        uncertainty = node.noise_std + 0.1 * len(missing_parents)
        
        # Confidence from model and data
        confidence = self.model_confidence * (1 - 0.1 * len(missing_parents))
        
        return CausalAnswer(
            query=query,
            prediction=prediction,
            uncertainty=uncertainty,
            confidence=confidence,
            reasoning=reasoning,
        )
    
    def _counterfactual(self, query: CausalQuery) -> CausalAnswer:
        """Answer counterfactual query: What would Y be if X had been different?"""
        target = query.target
        conditions = query.conditions  # Actual observed values
        interventions = query.interventions  # Counterfactual values
        
        reasoning = []
        
        # Step 1: Abduction - infer noise terms from actual observations
        noise_terms = {}
        for var, node in self.graph.nodes.items():
            if var in conditions:
                # Compute what the noise must have been
                predicted = sum(
                    node.parent_coefficients.get(p, 0) * conditions.get(p, 0)
                    for p in node.parents
                )
                noise_terms[var] = conditions[var] - predicted
                reasoning.append(f"Abduction: noise[{var}] = {noise_terms[var]:.3f}")
        
        # Step 2: Intervention - set counterfactual values
        cf_values = dict(conditions)
        cf_values.update(interventions)
        reasoning.append(f"Intervention: setting {interventions}")
        
        # Step 3: Prediction - propagate through graph with fixed noise
        # Topological sort for proper ordering
        visited = set()
        order = []
        
        def topo_sort(node_name):
            if node_name in visited:
                return
            visited.add(node_name)
            for child in self.graph.adjacency[node_name]:
                topo_sort(child)
            order.append(node_name)
        
        for var in interventions:
            topo_sort(var)
        
        order.reverse()
        
        # Propagate
        for var in order:
            if var in interventions:
                continue  # Intervention fixes this value
            
            node = self.graph.nodes.get(var)
            if node is None:
                continue
            
            # Compute from parents + noise
            prediction = sum(
                node.parent_coefficients.get(p, 0) * cf_values.get(p, 0)
                for p in node.parents
            )
            prediction += noise_terms.get(var, 0)
            cf_values[var] = prediction
            reasoning.append(f"Propagate: {var} = {prediction:.3f}")
        
        # Get target prediction
        prediction = cf_values.get(target, 0.0)
        
        return CausalAnswer(
            query=query,
            prediction=prediction,
            uncertainty=0.2,  # Counterfactuals have inherent uncertainty
            confidence=self.model_confidence * 0.8,
            reasoning=reasoning,
        )
    
    def _intervention(self, query: CausalQuery) -> CausalAnswer:
        """Answer intervention query: What happens to Y if we do(X=x)?"""
        target = query.target
        interventions = query.interventions
        
        reasoning = []
        
        # do(X=x) removes all incoming edges to X
        # Then propagate through the graph
        
        # Create modified graph (conceptually)
        reasoning.append(f"Intervention do({interventions}): removing incoming edges")
        
        # Topological propagation
        values = dict(interventions)
        
        # Get descendants of intervened variables
        descendants = set()
        for var in interventions:
            descendants.update(self.graph.get_descendants(var))
        
        # Propagate to descendants
        for var in descendants:
            node = self.graph.nodes.get(var)
            if node is None:
                continue
            
            # Only use parents that are either intervened or already computed
            prediction = 0.0
            for parent in node.parents:
                if parent in values:
                    coef = node.parent_coefficients.get(parent, 0)
                    prediction += coef * values[parent]
            
            values[var] = prediction
            reasoning.append(f"do-propagate: {var} = {prediction:.3f}")
        
        prediction = values.get(target, 0.0)
        
        return CausalAnswer(
            query=query,
            prediction=prediction,
            uncertainty=0.15,
            confidence=self.model_confidence * 0.9,
            reasoning=reasoning,
        )
    
    def explain_relationship(self, source: str, target: str) -> Dict[str, Any]:
        """Explain the causal relationship between two variables."""
        edge = self.graph.get_edge(source, target)
        
        if edge:
            return {
                "relationship": "direct_cause",
                "strength": edge.strength,
                "confidence": edge.confidence,
                "lag": edge.lag,
                "explanation": f"{source} directly causes {target} with strength {edge.strength:.2f}",
                "transfer_entropy": self.transfer_entropy.get((source, target), 0.0),
                "granger_pvalue": self.granger_pvalues.get((source, target), 1.0),
            }
        
        # Check for indirect relationship
        source_descendants = self.graph.get_descendants(source)
        if target in source_descendants:
            # Find path
            path = self._find_path(source, target)
            return {
                "relationship": "indirect_cause",
                "path": path,
                "explanation": f"{source} indirectly causes {target} through: {' -> '.join(path)}",
            }
        
        # Check for common cause (confounding)
        source_ancestors = self.graph.get_ancestors(source)
        target_ancestors = self.graph.get_ancestors(target)
        common = source_ancestors & target_ancestors
        
        if common:
            return {
                "relationship": "confounded",
                "common_causes": list(common),
                "explanation": f"{source} and {target} share common causes: {common}",
            }
        
        return {
            "relationship": "none",
            "explanation": f"No causal relationship found between {source} and {target}",
        }
    
    def _find_path(self, source: str, target: str) -> List[str]:
        """Find causal path from source to target using BFS."""
        from collections import deque
        
        queue = deque([(source, [source])])
        visited = {source}
        
        while queue:
            current, path = queue.popleft()
            
            if current == target:
                return path
            
            for child in self.graph.adjacency[current]:
                if child not in visited:
                    visited.add(child)
                    queue.append((child, path + [child]))
        
        return []
    
    def get_causal_summary(self) -> Dict[str, Any]:
        """Get summary of the causal model."""
        return {
            "num_nodes": len(self.graph.nodes),
            "num_edges": len(self.graph.edges),
            "model_confidence": self.model_confidence,
            "history_size": len(self.history),
            "strongest_edges": sorted(
                [(e.source, e.target, e.strength, e.confidence) for e in self.graph.edges],
                key=lambda x: abs(x[2]) * x[3],
                reverse=True
            )[:5],
            "graph": self.graph.to_dict(),
        }
