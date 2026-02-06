"""
WEAVE_PACKET - Decision Trace System
=====================================
Every decision outputs a trace packet with:
- Feature values
- Provenance tags
- Reason codes
- Render anchors (which candles/zones were referenced)

Must be replayable candle-by-candle.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any, List, Optional
from enum import Enum
import json
import hashlib


class DecisionType(Enum):
    TRADE = "TRADE"
    WAIT = "WAIT"
    SKIP = "SKIP"
    CONFLICT = "CONFLICT"


class ReasonCode(Enum):
    # Trade reasons
    CONFLUENCE_HIGH = "CONFLUENCE_HIGH"
    REAL_DATA_CONFIRMS = "REAL_DATA_CONFIRMS"
    
    # Wait reasons
    INSUFFICIENT_REAL_DATA = "INSUFFICIENT_REAL_DATA"
    CONFLICTING_SIGNALS = "CONFLICTING_SIGNALS"
    BELOW_CONFIDENCE_THRESHOLD = "BELOW_CONFIDENCE_THRESHOLD"
    WAITING_FOR_CONFIRMATION = "WAITING_FOR_CONFIRMATION"
    
    # Skip reasons
    NO_REAL_DATA = "NO_REAL_DATA"
    SYNTHETIC_ONLY = "SYNTHETIC_ONLY"
    KILL_SWITCH_ACTIVE = "KILL_SWITCH_ACTIVE"
    
    # Conflict reasons
    VOLUME_DELTA_CONFLICT = "VOLUME_DELTA_CONFLICT"
    STRUCTURE_TREND_CONFLICT = "STRUCTURE_TREND_CONFLICT"
    TIMEFRAME_CONFLICT = "TIMEFRAME_CONFLICT"


@dataclass
class RenderAnchor:
    """
    Anchor point for click-to-highlight functionality.
    Links a claim to specific chart elements.
    """
    anchor_type: str  # "candle", "zone", "level", "range"
    bar_index: Optional[int] = None
    bar_indices: Optional[List[int]] = None  # For multi-candle highlights
    price_low: Optional[float] = None
    price_high: Optional[float] = None
    timestamp: Optional[str] = None
    description: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "anchor_type": self.anchor_type,
            "bar_index": self.bar_index,
            "bar_indices": self.bar_indices,
            "price_low": self.price_low,
            "price_high": self.price_high,
            "timestamp": self.timestamp,
            "description": self.description
        }


@dataclass
class FeatureValue:
    """A feature value with its provenance and render anchors"""
    name: str
    value: Any
    tier: str  # "REAL", "DERIVED", "SYNTHETIC"
    source: str
    can_affect_decisions: bool
    render_anchors: List[RenderAnchor] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "value": self.value,
            "tier": self.tier,
            "source": self.source,
            "can_affect_decisions": self.can_affect_decisions,
            "render_anchors": [a.to_dict() for a in self.render_anchors],
            "is_synthetic": self.tier == "SYNTHETIC"
        }


@dataclass
class ConflictInfo:
    """Information about signal conflicts"""
    conflict_type: str
    signals_in_conflict: List[str]
    resolution_conditions: List[str]
    resolution_anchors: List[RenderAnchor] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "conflict_type": self.conflict_type,
            "signals_in_conflict": self.signals_in_conflict,
            "resolution_conditions": self.resolution_conditions,
            "resolution_anchors": [a.to_dict() for a in self.resolution_anchors]
        }


@dataclass
class WeavePacket:
    """
    Complete decision trace packet.
    Stores everything needed to replay and audit a decision.
    """
    # Identification
    packet_id: str
    timestamp: datetime
    symbol: str
    timeframe: str
    bar_index: int
    
    # Feature values with provenance
    features: Dict[str, FeatureValue]
    
    # Decision
    decision: DecisionType
    confidence: float
    reason_codes: List[ReasonCode]
    reason_text: str
    
    # Invalidation conditions
    invalidation_conditions: List[str]
    invalidation_anchors: List[RenderAnchor]
    
    # Conflict info (if in CONFLICT mode)
    conflict_info: Optional[ConflictInfo] = None
    
    # Evidence pins for "Why Wait" display
    evidence_pins: List[Dict[str, Any]] = field(default_factory=list)
    
    # Resolution conditions (drawn on chart)
    resolution_conditions: List[Dict[str, Any]] = field(default_factory=list)
    
    def __post_init__(self):
        if not self.packet_id:
            # Generate unique packet ID
            data = f"{self.timestamp.isoformat()}{self.symbol}{self.bar_index}"
            self.packet_id = hashlib.sha256(data.encode()).hexdigest()[:16]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "packet_id": self.packet_id,
            "timestamp": self.timestamp.isoformat(),
            "symbol": self.symbol,
            "timeframe": self.timeframe,
            "bar_index": self.bar_index,
            "features": {k: v.to_dict() for k, v in self.features.items()},
            "decision": self.decision.value,
            "confidence": self.confidence,
            "reason_codes": [r.value for r in self.reason_codes],
            "reason_text": self.reason_text,
            "invalidation_conditions": self.invalidation_conditions,
            "invalidation_anchors": [a.to_dict() for a in self.invalidation_anchors],
            "conflict_info": self.conflict_info.to_dict() if self.conflict_info else None,
            "evidence_pins": self.evidence_pins,
            "resolution_conditions": self.resolution_conditions
        }
    
    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "WeavePacket":
        """Reconstruct packet from dict (for replay)"""
        features = {}
        for k, v in data.get("features", {}).items():
            features[k] = FeatureValue(
                name=v["name"],
                value=v["value"],
                tier=v["tier"],
                source=v["source"],
                can_affect_decisions=v["can_affect_decisions"],
                render_anchors=[
                    RenderAnchor(**a) for a in v.get("render_anchors", [])
                ]
            )
        
        conflict_info = None
        if data.get("conflict_info"):
            ci = data["conflict_info"]
            conflict_info = ConflictInfo(
                conflict_type=ci["conflict_type"],
                signals_in_conflict=ci["signals_in_conflict"],
                resolution_conditions=ci["resolution_conditions"],
                resolution_anchors=[
                    RenderAnchor(**a) for a in ci.get("resolution_anchors", [])
                ]
            )
        
        return cls(
            packet_id=data["packet_id"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            symbol=data["symbol"],
            timeframe=data["timeframe"],
            bar_index=data["bar_index"],
            features=features,
            decision=DecisionType(data["decision"]),
            confidence=data["confidence"],
            reason_codes=[ReasonCode(r) for r in data["reason_codes"]],
            reason_text=data["reason_text"],
            invalidation_conditions=data["invalidation_conditions"],
            invalidation_anchors=[
                RenderAnchor(**a) for a in data.get("invalidation_anchors", [])
            ],
            conflict_info=conflict_info,
            evidence_pins=data.get("evidence_pins", []),
            resolution_conditions=data.get("resolution_conditions", [])
        )


class WeavePacketStore:
    """
    Storage for WEAVE_PACKETs.
    Enables replay mode and audit trails.
    """
    
    def __init__(self, max_packets: int = 10000):
        self.packets: List[WeavePacket] = []
        self.max_packets = max_packets
        self.packet_index: Dict[str, int] = {}  # packet_id -> index
    
    def store(self, packet: WeavePacket) -> None:
        """Store a packet"""
        if len(self.packets) >= self.max_packets:
            # Remove oldest packet
            old_packet = self.packets.pop(0)
            if old_packet.packet_id in self.packet_index:
                del self.packet_index[old_packet.packet_id]
        
        self.packets.append(packet)
        self.packet_index[packet.packet_id] = len(self.packets) - 1
    
    def get_by_id(self, packet_id: str) -> Optional[WeavePacket]:
        """Get packet by ID"""
        idx = self.packet_index.get(packet_id)
        if idx is not None and idx < len(self.packets):
            return self.packets[idx]
        return None
    
    def get_by_bar(self, symbol: str, bar_index: int) -> Optional[WeavePacket]:
        """Get packet for a specific bar (for replay)"""
        for packet in reversed(self.packets):
            if packet.symbol == symbol and packet.bar_index == bar_index:
                return packet
        return None
    
    def get_range(self, symbol: str, start_bar: int, end_bar: int) -> List[WeavePacket]:
        """Get packets for a bar range (for replay timeline)"""
        return [
            p for p in self.packets
            if p.symbol == symbol and start_bar <= p.bar_index <= end_bar
        ]
    
    def get_recent(self, symbol: str, count: int = 100) -> List[WeavePacket]:
        """Get most recent packets for a symbol"""
        symbol_packets = [p for p in self.packets if p.symbol == symbol]
        return symbol_packets[-count:]
    
    def export_for_replay(self, symbol: str) -> List[Dict[str, Any]]:
        """Export packets for replay mode"""
        return [p.to_dict() for p in self.packets if p.symbol == symbol]
    
    def import_for_replay(self, data: List[Dict[str, Any]]) -> None:
        """Import packets for replay mode"""
        for d in data:
            packet = WeavePacket.from_dict(d)
            self.store(packet)


# Global packet store
packet_store = WeavePacketStore()


def create_wait_packet(
    symbol: str,
    timeframe: str,
    bar_index: int,
    features: Dict[str, FeatureValue],
    reason_codes: List[ReasonCode],
    reason_text: str,
    evidence_pins: List[Dict[str, Any]],
    resolution_conditions: List[Dict[str, Any]],
    conflict_info: Optional[ConflictInfo] = None
) -> WeavePacket:
    """
    Create a WAIT decision packet with evidence pins and resolution conditions.
    """
    # Calculate confidence from real features only
    real_features = {k: v for k, v in features.items() if v.can_affect_decisions}
    confidence = len(real_features) / max(len(features), 1) * 100 if features else 0
    
    packet = WeavePacket(
        packet_id="",  # Will be auto-generated
        timestamp=datetime.utcnow(),
        symbol=symbol,
        timeframe=timeframe,
        bar_index=bar_index,
        features=features,
        decision=DecisionType.CONFLICT if conflict_info else DecisionType.WAIT,
        confidence=confidence,
        reason_codes=reason_codes,
        reason_text=reason_text,
        invalidation_conditions=[],
        invalidation_anchors=[],
        conflict_info=conflict_info,
        evidence_pins=evidence_pins,
        resolution_conditions=resolution_conditions
    )
    
    # Store packet
    packet_store.store(packet)
    
    return packet
