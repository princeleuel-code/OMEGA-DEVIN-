"""
WhyWait generator (Evidence Pins + Conflict Map).

Spec reference (SSOT):
- OMEGA_CODEX_HANDOFF/_claude_zip/CLAUDE EB6 644/WOVEN_SPEC_CHECKLIST.md

Rule: Tier C (synthetic) inputs may be shown as advisory pins, but must never
enable trading or increase confidence.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from uuid import uuid4


@dataclass(frozen=True)
class EvidencePin:
    pin_id: str
    pin_type: str  # "veto" | "missing_confirmation" | "conflict"
    bar_indices: List[int]
    feature_name: str
    description: str
    severity: int = 1  # 1=info, 2=warning, 3=block
    zone: Optional[Dict[str, float]] = None  # {price_low, price_high}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "pin_id": self.pin_id,
            "pin_type": self.pin_type,
            "bar_indices": self.bar_indices,
            "feature_name": self.feature_name,
            "description": self.description,
            "severity": self.severity,
            "zone": self.zone,
        }


@dataclass(frozen=True)
class ConflictMapEntry:
    signal_a: str
    signal_b: str
    weight_a: float
    weight_b: float
    resolution: str  # "a_wins" | "b_wins" | "cancelled_out"
    bar_indices: List[int]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "signal_a": self.signal_a,
            "signal_b": self.signal_b,
            "weight_a": self.weight_a,
            "weight_b": self.weight_b,
            "resolution": self.resolution,
            "bar_indices": self.bar_indices,
        }


@dataclass
class WhyWaitResult:
    evidence_pins: List[EvidencePin] = field(default_factory=list)
    conflict_map: List[ConflictMapEntry] = field(default_factory=list)
    missing_conditions: List[str] = field(default_factory=list)

    def top_pins(self, limit: int = 3) -> List[EvidencePin]:
        pins = sorted(self.evidence_pins, key=lambda p: (-p.severity, p.pin_type, p.feature_name))
        return pins[: max(0, limit)]


def _new_pin_id() -> str:
    return str(uuid4())


def generate_why_wait(
    *,
    bar_index: int,
    dom_check: Dict[str, Any],
    has_tier_ab_features: bool,
    synthetic_conflict: Optional[Dict[str, Any]] = None,
    current_price: Optional[float] = None,
) -> WhyWaitResult:
    """
    Generate WhyWait pins and conflict map for a single bar.

    Args:
        dom_check: output of MarketDataRegistry.fail_closed_check(symbol)
        synthetic_conflict: optional advisory conflict dict with keys:
            - signal_a, signal_b, weight_a, weight_b, resolution, zone (optional)
    """

    result = WhyWaitResult()

    if not dom_check.get("allowed", False):
        # Severity 3 veto: fail-closed on REAL_DOM.
        result.evidence_pins.append(
            EvidencePin(
                pin_id=_new_pin_id(),
                pin_type="veto",
                bar_indices=[bar_index],
                feature_name="real_dom",
                description=str(dom_check.get("reason") or "DOM check failed"),
                severity=3,
            )
        )
        result.missing_conditions.append("REAL_DOM feed must be CONNECTED and not STALE")

    if not has_tier_ab_features:
        result.evidence_pins.append(
            EvidencePin(
                pin_id=_new_pin_id(),
                pin_type="veto",
                bar_indices=[bar_index],
                feature_name="provenance_firewall",
                description="No Tier A/B features available: trading blocked (fail-closed).",
                severity=3,
            )
        )
        result.missing_conditions.append("Tier A/B features required to trade (Tier C is blocked)")

    if synthetic_conflict:
        entry = ConflictMapEntry(
            signal_a=str(synthetic_conflict.get("signal_a") or "A"),
            signal_b=str(synthetic_conflict.get("signal_b") or "B"),
            weight_a=float(synthetic_conflict.get("weight_a") or 1.0),
            weight_b=float(synthetic_conflict.get("weight_b") or 1.0),
            resolution=str(synthetic_conflict.get("resolution") or "cancelled_out"),
            bar_indices=[bar_index],
        )
        result.conflict_map.append(entry)
        result.evidence_pins.append(
            EvidencePin(
                pin_id=_new_pin_id(),
                pin_type="conflict",
                bar_indices=[bar_index],
                feature_name="synthetic_conflict",
                description="Advisory conflict between synthetic signals (Tier C): does not gate trading.",
                severity=1,
                zone=synthetic_conflict.get("zone"),
            )
        )

    if current_price is not None:
        # Mild reminder pin if we're blocked, to anchor the UI at the current price.
        if any(p.severity >= 3 for p in result.evidence_pins):
            zone = {"price_low": float(current_price), "price_high": float(current_price)}
            result.evidence_pins.append(
                EvidencePin(
                    pin_id=_new_pin_id(),
                    pin_type="missing_confirmation",
                    bar_indices=[bar_index],
                    feature_name="price",
                    description="Current price context for resolution conditions.",
                    severity=1,
                    zone=zone,
                )
            )

    return result

