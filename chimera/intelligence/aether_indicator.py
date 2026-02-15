"""
AETHER Indicator

Topological/spectral state indicator for market coherence detection.

This module intentionally avoids mystical claims and computes a glass-box
state vector from OHLCV:
- S: spectral entropy (0..1)
- dS: entropy slope
- F: force proxy (-1..1)
- P: dominant cycle period (bars)
- Pc: cycle confidence (0..1)
- N: multi-window node coherence (0..1)
- LOCK / SEAM / TRIGGER booleans
- STAMP and regime labels for UI/ops
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Sequence, Tuple
import math

from ..data.loader import OHLCV


@dataclass
class AetherState:
    """AETHER state vector for one bar."""

    s_entropy: float = 0.5
    ds_entropy: float = 0.0
    force: float = 0.0
    dominant_period: int = 20
    cycle_confidence: float = 0.5
    node_coherence: float = 0.3
    lock: bool = False
    seam: bool = False
    seam_reasons: List[str] = None
    trigger: bool = False
    stamp: str = "GHOST"
    regime: str = "STABLE"
    phase_deg: float = 0.0
    at_node: bool = False
    wall_gradient: float = 0.0

    def __post_init__(self) -> None:
        if self.seam_reasons is None:
            self.seam_reasons = []

    def to_dict(self) -> Dict[str, Any]:
        return {
            "S": self.s_entropy,
            "dS": self.ds_entropy,
            "F": self.force,
            "P": self.dominant_period,
            "Pc": self.cycle_confidence,
            "N": self.node_coherence,
            "LOCK": self.lock,
            "SEAM": self.seam,
            "SEAM_REASONS": list(self.seam_reasons),
            "TRIGGER": self.trigger,
            "STAMP": self.stamp,
            "REGIME": self.regime,
            "PHASE_DEG": self.phase_deg,
            "AT_NODE": self.at_node,
            "WALL_GRADIENT": self.wall_gradient,
        }


@dataclass
class AetherConfig:
    """Configuration for AETHER indicator computation."""

    entropy_window: int = 64
    force_window: int = 20
    impulse_window: int = 5
    cycle_window: int = 64
    node_windows: Tuple[int, ...] = (10, 20, 40, 80)
    wall_window: int = 12


class AetherIndicator:
    """Compute AETHER state vector series from OHLCV bars."""

    def __init__(self, config: Optional[AetherConfig] = None):
        self.config = config or AetherConfig()

    def compute(self, data: Sequence[OHLCV]) -> List[AetherState]:
        if not data:
            return []

        closes = [float(b.close) for b in data]
        volumes = [float(b.volume) for b in data]
        returns = [0.0]
        for i in range(1, len(closes)):
            returns.append(closes[i] - closes[i - 1])

        states: List[AetherState] = []

        smooth_s = 0.5
        smooth_f = 0.0
        smooth_pc = 0.5
        smooth_n = 0.3
        prev_s = smooth_s
        prev_wall_gradient = 0.0

        for i in range(len(data)):
            ret_win = self._window(returns, i, self.config.entropy_window)
            s_raw = self._spectral_entropy(ret_win)
            smooth_s = (smooth_s * 0.85) + (s_raw * 0.15)
            ds = smooth_s - prev_s
            prev_s = smooth_s

            f_raw = self._force(returns, i)
            smooth_f = (smooth_f * 0.70) + (f_raw * 0.30)

            cyc_signal = self._window(returns, i, self.config.cycle_window)
            period, pc_raw = self._dominant_cycle_with_confidence(cyc_signal)
            pc_before = smooth_pc
            smooth_pc = (smooth_pc * 0.80) + (pc_raw * 0.20)

            node_n, phase, at_node = self._node_coherence(closes, i)
            smooth_n = (smooth_n * 0.80) + (node_n * 0.20)

            wall_grad = self._wall_gradient(returns, volumes, i)
            seam, seam_reasons = self._detect_seam(
                ds=ds,
                prev_pc=pc_before,
                pc=smooth_pc,
                prev_wall_gradient=prev_wall_gradient,
                wall_gradient=wall_grad,
            )
            prev_wall_gradient = wall_grad

            lock = (
                smooth_s < 0.35
                and abs(ds) < 0.06
                and smooth_pc > 0.45
                and smooth_n > 0.40
            )
            trigger = lock and abs(smooth_f) > 0.30
            stamp = self._classify_stamp(s=smooth_s, ds=ds, force=smooth_f, pc=smooth_pc)
            regime = self._classify_regime(s=smooth_s, ds=ds, pc=smooth_pc, seam=seam, force=smooth_f)

            states.append(
                AetherState(
                    s_entropy=self._clamp01(smooth_s),
                    ds_entropy=ds,
                    force=max(-1.0, min(1.0, smooth_f)),
                    dominant_period=int(period),
                    cycle_confidence=self._clamp01(smooth_pc),
                    node_coherence=self._clamp01(smooth_n),
                    lock=lock,
                    seam=seam,
                    seam_reasons=seam_reasons,
                    trigger=trigger,
                    stamp=stamp,
                    regime=regime,
                    phase_deg=phase,
                    at_node=at_node,
                    wall_gradient=max(-1.0, min(1.0, wall_grad)),
                )
            )

        return states

    def _window(self, series: Sequence[float], idx: int, width: int) -> List[float]:
        start = max(0, idx - max(1, width) + 1)
        return [float(x) for x in series[start : idx + 1]]

    def _spectral_entropy(self, signal: Sequence[float]) -> float:
        if len(signal) < 8:
            return 0.5
        psd = self._power_spectrum(signal)
        if not psd:
            return 1.0
        total = sum(psd)
        if total <= 1e-12:
            return 1.0
        h = 0.0
        for p in psd:
            prob = p / total
            if prob > 1e-12:
                h -= prob * math.log(prob, 2)
        h_max = math.log(max(2, len(psd)), 2)
        if h_max <= 0:
            return 0.5
        return self._clamp01(h / h_max)

    def _dominant_cycle_with_confidence(self, signal: Sequence[float]) -> Tuple[int, float]:
        n = len(signal)
        if n < 16:
            return 20, 0.0
        psd = self._power_spectrum(signal)
        if len(psd) < 3:
            return 20, 0.0

        max_idx = 0
        max_val = psd[0]
        for i in range(1, len(psd)):
            if psd[i] > max_val:
                max_val = psd[i]
                max_idx = i

        sorted_psd = sorted(psd)
        median = sorted_psd[len(sorted_psd) // 2] if sorted_psd else 1e-12
        confidence = min(1.0, (max_val / (median + 1e-12)) / 20.0)

        # max_idx 0 corresponds to k=1 in the DFT loop.
        harmonic_k = max_idx + 1
        period = int(round(n / max(1, harmonic_k)))
        period = max(3, min(period, int(n * 0.8)))
        return period, confidence

    def _power_spectrum(self, signal: Sequence[float]) -> List[float]:
        n = len(signal)
        if n < 4:
            return []
        mags: List[float] = []
        half = n // 2
        for k in range(1, half):
            re = 0.0
            im = 0.0
            for i in range(n):
                angle = (2.0 * math.pi * k * i) / n
                re += signal[i] * math.cos(angle)
                im -= signal[i] * math.sin(angle)
            mags.append((re * re + im * im) / n)
        return mags

    def _force(self, returns: Sequence[float], idx: int) -> float:
        if idx < 2:
            return 0.0
        recent = self._window(returns, idx, self.config.impulse_window)
        impulse = sum(recent)
        vol_window = self._window(returns, idx, self.config.force_window)
        if len(vol_window) < 2:
            return 0.0
        mean = sum(vol_window) / len(vol_window)
        var = sum((x - mean) ** 2 for x in vol_window) / len(vol_window)
        std = math.sqrt(max(1e-12, var))
        return max(-1.0, min(1.0, impulse / (std * 3.0 + 1e-12)))

    def _node_coherence(self, closes: Sequence[float], idx: int) -> Tuple[float, float, bool]:
        nodes = 0
        phase_20 = 0.0
        node_20 = False
        windows = list(self.config.node_windows)
        for w in windows:
            phase, at_node = self._phase_on_detrended(closes, idx, w)
            if w == 20:
                phase_20 = phase
                node_20 = at_node
            if at_node:
                nodes += 1
        coherence = nodes / max(1, len(windows))
        return coherence, phase_20, node_20

    def _phase_on_detrended(self, closes: Sequence[float], idx: int, window: int) -> Tuple[float, bool]:
        if idx < (window + 4):
            return 0.0, False

        start = max(0, idx - (window + 10) + 1)
        segment = [float(x) for x in closes[start : idx + 1]]
        if len(segment) < window:
            return 0.0, False

        alpha = 2.0 / (window + 1.0)
        ema = segment[0]
        detrended: List[float] = []
        for x in segment:
            ema = alpha * x + (1.0 - alpha) * ema
            detrended.append(x - ema)
        tail = detrended[-window:]

        amp = max(1e-12, max(abs(x) for x in tail))
        norm = tail[-1] / amp
        norm = max(-1.0, min(1.0, norm))
        phase = math.degrees(math.asin(norm))
        at_node = abs(norm) < 0.10
        return phase, at_node

    def _wall_gradient(self, returns: Sequence[float], volumes: Sequence[float], idx: int) -> float:
        start = max(0, idx - self.config.wall_window + 1)
        signed = []
        for i in range(start, idx + 1):
            sign = 1.0 if returns[i] >= 0 else -1.0
            signed.append(sign * volumes[i])
        if not signed:
            return 0.0
        num = sum(signed)
        den = sum(abs(x) for x in signed) + 1e-12
        return max(-1.0, min(1.0, num / den))

    def _detect_seam(
        self,
        ds: float,
        prev_pc: float,
        pc: float,
        prev_wall_gradient: float,
        wall_gradient: float,
    ) -> Tuple[bool, List[str]]:
        votes = 0
        reasons: List[str] = []

        if abs(ds) > 0.12:
            votes += 1
            reasons.append("dS_SPIKE")
        # Either absolute cycle confidence is weak, or confidence collapsed quickly.
        if pc < 0.25:
            votes += 1
            reasons.append("PC_DROP")
        elif (prev_pc - pc) > 0.10:
            votes += 1
            reasons.append("PC_COLLAPSE")
        if prev_wall_gradient * wall_gradient < 0 and abs(prev_wall_gradient) > 0.05:
            votes += 1
            reasons.append("WALL_FLIP")

        return votes >= 2, reasons

    def _classify_stamp(self, s: float, ds: float, force: float, pc: float) -> str:
        abs_f = abs(force)
        if abs_f > 0.35 and abs(ds) < 0.08 and pc > 0.40:
            return "SPEAR"
        if abs_f > 0.25 and s > 0.50 and abs(ds) < 0.05:
            return "SHIELD"
        return "GHOST"

    def _classify_regime(self, s: float, ds: float, pc: float, seam: bool, force: float) -> str:
        if s < 0.28 and abs(ds) < 0.06:
            regime = "HARMONIC"
        elif s < 0.45:
            regime = "STABLE"
        elif abs(ds) > 0.06 or pc < 0.30:
            regime = "TRANSITION"
        else:
            regime = "DIFFUSE"

        if seam and abs(force) > 0.50:
            regime = "CRISIS"
        return regime

    def _clamp01(self, x: float) -> float:
        return max(0.0, min(1.0, x))
