"""
Data Provenance Firewall System
================================
Ensures NO synthetic data can affect trading decisions.

Tier Classification:
- TIER_A (REAL): Direct from live feed (trades, quotes, L2 order book)
- TIER_B (DERIVED): Computed from Tier A data (e.g., VWAP from real trades)
- TIER_C (SYNTHETIC): Guessed/estimated from OHLCV candles (EDUCATIONAL ONLY)

RULE: Tier C data CANNOT affect confidence scoring or trade permission.
"""

from enum import Enum
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from datetime import datetime
import json


class DataTier(Enum):
    """Data provenance tiers - determines if data can affect decisions"""
    TIER_A = "REAL"           # Direct from live feed
    TIER_B = "DERIVED"        # Computed from Tier A
    TIER_C = "SYNTHETIC"      # Guessed from OHLCV (EDUCATIONAL ONLY)


@dataclass
class ProvenanceTag:
    """Tag attached to every data feature"""
    tier: DataTier
    source: str
    timestamp: datetime
    can_affect_decisions: bool
    watermark: Optional[str] = None
    
    def __post_init__(self):
        # Tier C data CANNOT affect decisions - enforce this
        if self.tier == DataTier.TIER_C:
            self.can_affect_decisions = False
            self.watermark = "SYNTHETIC / EDUCATIONAL ONLY"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "tier": self.tier.value,
            "source": self.source,
            "timestamp": self.timestamp.isoformat(),
            "can_affect_decisions": self.can_affect_decisions,
            "watermark": self.watermark
        }


@dataclass
class TaggedFeature:
    """A feature value with its provenance tag"""
    name: str
    value: Any
    provenance: ProvenanceTag
    highlight_anchors: List[Dict[str, Any]] = field(default_factory=list)  # For click-to-highlight
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "value": self.value,
            "provenance": self.provenance.to_dict(),
            "highlight_anchors": self.highlight_anchors,
            "is_synthetic": self.provenance.tier == DataTier.TIER_C
        }


class ProvenanceFirewall:
    """
    Runtime guard that blocks Tier C data from affecting decisions.
    
    RULE: If a feature is Tier C, the scoring pipeline MUST ignore it.
    """
    
    def __init__(self):
        self.feature_registry: Dict[str, TaggedFeature] = {}
        self.blocked_features: List[str] = []
        self.decision_trace: List[Dict[str, Any]] = []

    def reset(self) -> None:
        """Clear the current feature registry (per-decision)."""
        self.feature_registry.clear()
        self.blocked_features.clear()
    
    def register_feature(self, feature: TaggedFeature) -> None:
        """Register a feature with its provenance"""
        self.feature_registry[feature.name] = feature
        
        # Track blocked features
        if not feature.provenance.can_affect_decisions and feature.name not in self.blocked_features:
            self.blocked_features.append(feature.name)
    
    def get_decision_features(self) -> Dict[str, TaggedFeature]:
        """
        Get ONLY features that can affect decisions (Tier A and B).
        Tier C features are BLOCKED from this output.
        """
        return {
            name: feat for name, feat in self.feature_registry.items()
            if feat.provenance.can_affect_decisions
        }
    
    def get_display_features(self) -> Dict[str, TaggedFeature]:
        """
        Get ALL features for display (including Tier C with watermark).
        Tier C features will be watermarked as SYNTHETIC.
        """
        return self.feature_registry.copy()
    
    def validate_decision_input(self, feature_names: List[str]) -> bool:
        """
        Validate that NO Tier C features are being used for decisions.
        Returns False if any Tier C feature is in the input.
        """
        for name in feature_names:
            if name in self.feature_registry:
                feat = self.feature_registry[name]
                if feat.provenance.tier == DataTier.TIER_C:
                    raise ProvenanceViolationError(
                        f"BLOCKED: Tier C feature '{name}' cannot affect decisions. "
                        f"Source: {feat.provenance.source}"
                    )
        return True
    
    def compute_confidence(self, features: Dict[str, Any]) -> float:
        """
        Compute confidence score using ONLY Tier A and B features.
        Tier C features are automatically excluded.
        """
        decision_features = self.get_decision_features()
        
        # Filter input to only include decision-allowed features
        valid_features = {
            k: v for k, v in features.items()
            if k in decision_features
        }
        
        # Log what was blocked
        blocked = [k for k in features.keys() if k not in decision_features]
        if blocked:
            self.decision_trace.append({
                "action": "BLOCKED_FROM_CONFIDENCE",
                "features": blocked,
                "reason": "Tier C synthetic data cannot affect decisions"
            })
        
        # Return 0 confidence if no valid features
        if not valid_features:
            return 0.0
        
        # Simple confidence calculation (can be enhanced)
        return len(valid_features) / max(len(features), 1) * 100
    
    def can_trade(self, confidence: float, min_confidence: float = 60.0) -> bool:
        """
        Determine if trading is permitted.
        RULE: Must have sufficient Tier A/B data to trade.
        """
        decision_features = self.get_decision_features()
        
        # Fail-closed: No real data = no trading
        if len(decision_features) == 0:
            return False
        
        return confidence >= min_confidence
    
    def get_provenance_report(self) -> Dict[str, Any]:
        """Generate a full provenance report for audit"""
        report = {
            "total_features": len(self.feature_registry),
            "tier_a_count": 0,
            "tier_b_count": 0,
            "tier_c_count": 0,
            "blocked_from_decisions": self.blocked_features,
            "features": {}
        }
        
        for name, feat in self.feature_registry.items():
            tier = feat.provenance.tier
            if tier == DataTier.TIER_A:
                report["tier_a_count"] += 1
            elif tier == DataTier.TIER_B:
                report["tier_b_count"] += 1
            else:
                report["tier_c_count"] += 1
            
            report["features"][name] = feat.to_dict()
        
        return report


class ProvenanceViolationError(Exception):
    """Raised when Tier C data attempts to affect decisions"""
    pass


# Feature provenance definitions
FEATURE_PROVENANCE_TABLE = {
    # TIER A - REAL (from live feed)
    "real_dom_bids": DataTier.TIER_A,
    "real_dom_asks": DataTier.TIER_A,
    "real_trades": DataTier.TIER_A,
    "real_quotes": DataTier.TIER_A,
    "real_l2_depth": DataTier.TIER_A,
    
    # TIER B - DERIVED (computed from Tier A)
    "vwap_from_trades": DataTier.TIER_B,
    "book_imbalance": DataTier.TIER_B,
    "trade_flow": DataTier.TIER_B,
    "real_cvd": DataTier.TIER_B,
    
    # TIER C - SYNTHETIC (guessed from OHLCV) - CANNOT AFFECT DECISIONS
    "simulated_dom": DataTier.TIER_C,
    "estimated_volume_profile": DataTier.TIER_C,
    "estimated_delta": DataTier.TIER_C,
    "estimated_absorption": DataTier.TIER_C,
    "estimated_cvd_divergence": DataTier.TIER_C,
    "estimated_deep_trades": DataTier.TIER_C,
    "estimated_footprint": DataTier.TIER_C,
    "estimated_heatmap": DataTier.TIER_C,
    "estimated_fvg": DataTier.TIER_C,
    "estimated_footprint_patterns": DataTier.TIER_C,
    "estimated_market_profile": DataTier.TIER_C,
}


def create_tagged_feature(
    name: str,
    value: Any,
    source: str,
    highlight_anchors: Optional[List[Dict[str, Any]]] = None
) -> TaggedFeature:
    """
    Create a tagged feature with automatic tier classification.
    """
    tier = FEATURE_PROVENANCE_TABLE.get(name, DataTier.TIER_C)
    
    provenance = ProvenanceTag(
        tier=tier,
        source=source,
        timestamp=datetime.utcnow(),
        can_affect_decisions=(tier != DataTier.TIER_C)
    )
    
    return TaggedFeature(
        name=name,
        value=value,
        provenance=provenance,
        highlight_anchors=highlight_anchors or []
    )
