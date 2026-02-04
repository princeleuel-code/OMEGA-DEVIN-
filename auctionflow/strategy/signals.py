from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from auctionflow.data.schema import Candle
from auctionflow.flow.acceptance import AcceptanceResult, acceptance_score, failed_auction, in_value_area
from auctionflow.profile.build import ProfileConfig, VolumeProfile, build_volume_profile
from auctionflow.profile.nodes import detect_nodes, next_hvn
from auctionflow.strategy.tricks import detect_bos, detect_fvg, detect_liquidity_sweep


@dataclass(frozen=True)
class StrategyConfig:
    profile: ProfileConfig = ProfileConfig()
    session_lookback_candles: int = 300
    acceptance_lookback: int = 8
    acceptance_threshold: float = 0.65
    lvn_proximity_ticks: int = 4
    min_rr: float = 1.8


@dataclass(frozen=True)
class Signal:
    kind: str  # FAILED_AUCTION | ACCEPTANCE_BREAKOUT | LVN_TRAVEL
    side: str  # long | short
    entry: float
    stop: float
    target: float
    tags: List[str]


def generate_signal(candles: List[Candle], cfg: StrategyConfig) -> Optional[Signal]:
    """Generate at most one signal for the newest candle."""
    if len(candles) < max(cfg.session_lookback_candles, 3) + 2:
        return None

    window = candles[-cfg.session_lookback_candles:]
    prof = build_volume_profile(window, cfg.profile)
    nodes = detect_nodes(prof, window=cfg.profile.smooth_window, min_prominence=0.0)

    cur = candles[-1]
    prev = candles[-2]

    # Chart tricks (scout)
    sweep = detect_liquidity_sweep(candles, lookback=20)
    fvg = detect_fvg(candles)
    bos = detect_bos(candles, lookback=50)

    # 1) Failed auction fade (highest priority)
    if failed_auction(prev, cur, val=prof.val, vah=prof.vah):
        tags = ["auction_failed"]
        if sweep:
            tags.append(sweep.kind)
        if fvg:
            tags.append(fvg[0])
        if bos:
            tags.append(bos)

        if prev.close > prof.vah:  # failed up auction -> short
            entry = cur.close
            stop = max(prev.high, cur.high)
            target = prof.poc
            sig = Signal("FAILED_AUCTION", "short", entry, stop, target, tags)
            return sig
        if prev.close < prof.val:  # failed down auction -> long
            entry = cur.close
            stop = min(prev.low, cur.low)
            target = prof.poc
            sig = Signal("FAILED_AUCTION", "long", entry, stop, target, tags)
            return sig

    # 2) Acceptance breakout
    # Only if price is outside value area now
    if cur.close > prof.vah:
        acc = acceptance_score(candles[-cfg.acceptance_lookback:], val=prof.val, vah=prof.vah, direction="up")
        if acc.score >= cfg.acceptance_threshold:
            entry = cur.close
            stop = prof.vah  # conservative: back inside value
            target = next_hvn(prof, nodes, price=cur.close, direction="above") or (cur.close + (cur.close - stop) * 2.0)
            tags = ["accept_up", f"acc={acc.score:.2f}"]
            if bos:
                tags.append(bos)
            if fvg:
                tags.append(fvg[0])
            return Signal("ACCEPTANCE_BREAKOUT", "long", entry, stop, float(target), tags)

    if cur.close < prof.val:
        acc = acceptance_score(candles[-cfg.acceptance_lookback:], val=prof.val, vah=prof.vah, direction="down")
        if acc.score >= cfg.acceptance_threshold:
            entry = cur.close
            stop = prof.val
            target = next_hvn(prof, nodes, price=cur.close, direction="below") or (cur.close - (stop - cur.close) * 2.0)
            tags = ["accept_down", f"acc={acc.score:.2f}"]
            if bos:
                tags.append(bos)
            if fvg:
                tags.append(fvg[0])
            return Signal("ACCEPTANCE_BREAKOUT", "short", entry, stop, float(target), tags)

    # 3) LVN travel (proxy): if we're in value but moving fast toward a node
    # We approximate LVN proximity by nearest LVN node price and candle body direction.
    lvns = [n for n in nodes if n.kind == "LVN"]
    if lvns:
        nearest = min(lvns, key=lambda n: abs(n.price - cur.close))
        ticks = abs(nearest.price - cur.close) / cfg.profile.tick_size
        body = cur.close - cur.open
        if ticks <= cfg.lvn_proximity_ticks and abs(body) > 0:
            # direction by candle body
            side = "long" if body > 0 else "short"
            entry = cur.close
            stop = cur.low if side == "long" else cur.high
            target = next_hvn(prof, nodes, price=cur.close, direction="above" if side=="long" else "below")
            if target is None:
                return None
            tags = ["lvn_travel", f"lvn@{nearest.price:.2f}"]
            return Signal("LVN_TRAVEL", side, entry, stop, float(target), tags)

    return None
