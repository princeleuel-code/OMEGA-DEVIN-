"""
Unit Tests for Data Provenance Firewall
========================================
These tests MUST FAIL if Tier C (synthetic) features affect decisions.
"""

import pytest
from datetime import datetime
from . import (
    DataTier,
    ProvenanceTag,
    TaggedFeature,
    ProvenanceFirewall,
    ProvenanceViolationError,
    create_tagged_feature,
    FEATURE_PROVENANCE_TABLE
)


class TestProvenanceTag:
    """Test ProvenanceTag behavior"""
    
    def test_tier_c_cannot_affect_decisions(self):
        """CRITICAL: Tier C tags MUST have can_affect_decisions=False"""
        tag = ProvenanceTag(
            tier=DataTier.TIER_C,
            source="test",
            timestamp=datetime.utcnow(),
            can_affect_decisions=True  # Try to set True
        )
        # Must be forced to False
        assert tag.can_affect_decisions == False
        assert tag.watermark == "SYNTHETIC / EDUCATIONAL ONLY"
    
    def test_tier_c_always_watermarked(self):
        """Tier C data MUST always have watermark"""
        tag = ProvenanceTag(
            tier=DataTier.TIER_C,
            source="test",
            timestamp=datetime.utcnow(),
            can_affect_decisions=False
        )
        assert tag.watermark is not None
        assert "SYNTHETIC" in tag.watermark
    
    def test_tier_a_can_affect_decisions(self):
        """Tier A (real) data CAN affect decisions"""
        tag = ProvenanceTag(
            tier=DataTier.TIER_A,
            source="live_feed",
            timestamp=datetime.utcnow(),
            can_affect_decisions=True
        )
        assert tag.can_affect_decisions == True
        assert tag.watermark is None
    
    def test_tier_b_can_affect_decisions(self):
        """Tier B (derived from real) data CAN affect decisions"""
        tag = ProvenanceTag(
            tier=DataTier.TIER_B,
            source="computed_from_trades",
            timestamp=datetime.utcnow(),
            can_affect_decisions=True
        )
        assert tag.can_affect_decisions == True


class TestProvenanceFirewall:
    """Test ProvenanceFirewall blocking behavior"""
    
    def test_tier_c_blocked_from_decision_features(self):
        """CRITICAL: Tier C features MUST be blocked from decision features"""
        firewall = ProvenanceFirewall()
        
        # Register a Tier C feature
        tier_c_feature = create_tagged_feature(
            name="simulated_dom",
            value={"bids": [], "asks": []},
            source="candle_estimation"
        )
        firewall.register_feature(tier_c_feature)
        
        # Get decision features - should be empty
        decision_features = firewall.get_decision_features()
        assert "simulated_dom" not in decision_features
        assert len(decision_features) == 0
    
    def test_tier_a_included_in_decision_features(self):
        """Tier A features MUST be included in decision features"""
        firewall = ProvenanceFirewall()
        
        # Register a Tier A feature
        tier_a_feature = create_tagged_feature(
            name="real_dom_bids",
            value=[{"price": 100, "size": 50}],
            source="binance_l2_feed"
        )
        firewall.register_feature(tier_a_feature)
        
        # Get decision features - should include it
        decision_features = firewall.get_decision_features()
        assert "real_dom_bids" in decision_features
    
    def test_validate_decision_input_blocks_tier_c(self):
        """CRITICAL: validate_decision_input MUST raise error for Tier C"""
        firewall = ProvenanceFirewall()
        
        # Register a Tier C feature
        tier_c_feature = create_tagged_feature(
            name="estimated_delta",
            value=1000,
            source="candle_estimation"
        )
        firewall.register_feature(tier_c_feature)
        
        # Attempting to use Tier C for decisions MUST raise error
        with pytest.raises(ProvenanceViolationError) as exc_info:
            firewall.validate_decision_input(["estimated_delta"])
        
        assert "BLOCKED" in str(exc_info.value)
        assert "Tier C" in str(exc_info.value)
    
    def test_confidence_excludes_tier_c(self):
        """CRITICAL: Confidence calculation MUST exclude Tier C features"""
        firewall = ProvenanceFirewall()
        
        # Register mixed features
        tier_a = create_tagged_feature("real_trades", [1, 2, 3], "live_feed")
        tier_c = create_tagged_feature("estimated_delta", 1000, "candle_estimation")
        
        firewall.register_feature(tier_a)
        firewall.register_feature(tier_c)
        
        # Compute confidence with both
        features = {
            "real_trades": [1, 2, 3],
            "estimated_delta": 1000
        }
        confidence = firewall.compute_confidence(features)
        
        # Should only count the Tier A feature (1 out of 2 = 50%)
        assert confidence == 50.0
    
    def test_cannot_trade_without_real_data(self):
        """CRITICAL: Trading MUST be blocked if no Tier A/B data"""
        firewall = ProvenanceFirewall()
        
        # Register only Tier C features
        tier_c = create_tagged_feature("simulated_dom", {}, "candle_estimation")
        firewall.register_feature(tier_c)
        
        # Should not be able to trade
        assert firewall.can_trade(confidence=100.0) == False
    
    def test_can_trade_with_real_data(self):
        """Trading CAN proceed with sufficient Tier A/B data"""
        firewall = ProvenanceFirewall()
        
        # Register Tier A feature
        tier_a = create_tagged_feature("real_dom_bids", [1, 2, 3], "live_feed")
        firewall.register_feature(tier_a)
        
        # Should be able to trade with sufficient confidence
        assert firewall.can_trade(confidence=70.0) == True
        assert firewall.can_trade(confidence=50.0) == False  # Below threshold


class TestFeatureProvenanceTable:
    """Test that all synthetic features are properly classified"""
    
    def test_simulated_dom_is_tier_c(self):
        """Simulated DOM MUST be Tier C"""
        assert FEATURE_PROVENANCE_TABLE["simulated_dom"] == DataTier.TIER_C
    
    def test_estimated_features_are_tier_c(self):
        """All estimated features MUST be Tier C"""
        estimated_features = [
            "estimated_volume_profile",
            "estimated_delta",
            "estimated_absorption",
            "estimated_cvd_divergence",
            "estimated_deep_trades",
            "estimated_footprint",
            "estimated_heatmap",
            "estimated_fvg",
            "estimated_footprint_patterns",
            "estimated_market_profile",
        ]
        for feat in estimated_features:
            assert FEATURE_PROVENANCE_TABLE[feat] == DataTier.TIER_C, \
                f"{feat} MUST be Tier C but is {FEATURE_PROVENANCE_TABLE[feat]}"
    
    def test_real_features_are_tier_a(self):
        """Real feed features MUST be Tier A"""
        real_features = [
            "real_dom_bids",
            "real_dom_asks",
            "real_trades",
            "real_quotes",
            "real_l2_depth",
        ]
        for feat in real_features:
            assert FEATURE_PROVENANCE_TABLE[feat] == DataTier.TIER_A, \
                f"{feat} MUST be Tier A but is {FEATURE_PROVENANCE_TABLE[feat]}"


class TestCreateTaggedFeature:
    """Test the create_tagged_feature helper"""
    
    def test_unknown_feature_defaults_to_tier_c(self):
        """Unknown features MUST default to Tier C (fail-safe)"""
        feature = create_tagged_feature(
            name="unknown_feature",
            value=123,
            source="unknown"
        )
        assert feature.provenance.tier == DataTier.TIER_C
        assert feature.provenance.can_affect_decisions == False
    
    def test_highlight_anchors_preserved(self):
        """Highlight anchors MUST be preserved for click-to-highlight"""
        anchors = [
            {"bar_index": 5, "price": 100.5},
            {"bar_index": 6, "price": 101.0}
        ]
        feature = create_tagged_feature(
            name="real_trades",
            value=[1, 2, 3],
            source="live_feed",
            highlight_anchors=anchors
        )
        assert feature.highlight_anchors == anchors


def run_tests():
    """Run all provenance tests"""
    pytest.main([__file__, "-v"])


if __name__ == "__main__":
    run_tests()
