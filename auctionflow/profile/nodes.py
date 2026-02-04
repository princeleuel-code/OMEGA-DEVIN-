from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

import numpy as np

from .build import VolumeProfile


@dataclass(frozen=True)
class Node:
    kind: str  # 'HVN' or 'LVN'
    price: float
    strength: float


def smooth(x: np.ndarray, window: int) -> np.ndarray:
    if window <= 1:
        return x
    w = int(window)
    kernel = np.ones(w) / w
    return np.convolve(x, kernel, mode="same")


def detect_nodes(profile: VolumeProfile, *, window: int = 3, min_prominence: float = 0.0) -> List[Node]:
    """Detect HVN/LVN as local maxima/minima on a smoothed histogram."""
    v = smooth(profile.volume, window)
    nodes: List[Node] = []

    for i in range(1, len(v) - 1):
        if v[i] >= v[i - 1] and v[i] >= v[i + 1]:
            prom = v[i] - max(v[i - 1], v[i + 1])
            if prom >= min_prominence:
                nodes.append(Node("HVN", float(profile.prices[i]), float(prom)))
        if v[i] <= v[i - 1] and v[i] <= v[i + 1]:
            prom = min(v[i - 1], v[i + 1]) - v[i]
            if prom >= min_prominence:
                nodes.append(Node("LVN", float(profile.prices[i]), float(prom)))

    # sort by strength desc for convenience
    return sorted(nodes, key=lambda n: n.strength, reverse=True)


def next_hvn(profile: VolumeProfile, nodes: List[Node], price: float, direction: str) -> Optional[float]:
    hvns = sorted([n.price for n in nodes if n.kind == "HVN"])
    if not hvns:
        return None
    if direction == "above":
        for p in hvns:
            if p > price:
                return p
        return hvns[-1]
    if direction == "below":
        for p in reversed(hvns):
            if p < price:
                return p
        return hvns[0]
    raise ValueError("direction must be 'above' or 'below'")
