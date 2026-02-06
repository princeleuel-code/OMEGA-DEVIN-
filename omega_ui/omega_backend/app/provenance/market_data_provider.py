"""
Pluggable real DOM provider interface + registry (fail-closed).

Implements the SSOT policy in:
- OMEGA_CODEX_HANDOFF/_claude_zip/CLAUDE EB6 644/REAL_DOM_POLICY.md

Design goals:
- Import-safe even when optional websocket dependencies are missing.
- Fail-closed when REAL_DOM=true and the provider is disconnected/stale/unqualified.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

from .dom_types import DOMLevel, RealDOMSnapshot

logger = logging.getLogger(__name__)


class FeedState(Enum):
    DISCONNECTED = "DISCONNECTED"
    CONNECTING = "CONNECTING"
    CONNECTED = "CONNECTED"
    STALE = "STALE"
    ERROR = "ERROR"


def _env_int(name: str, default: int) -> int:
    try:
        return int(os.environ.get(name, str(default)))
    except Exception:
        return default


def _env_float(name: str, default: float) -> float:
    try:
        return float(os.environ.get(name, str(default)))
    except Exception:
        return default


def _is_real_dom_required() -> bool:
    return os.environ.get("REAL_DOM", "false").lower() == "true"


def _reconnect_delay_seconds(attempt: int) -> int:
    # REAL_DOM_POLICY.md §4.1
    if attempt <= 3:
        return 5
    if attempt <= 6:
        return 15
    if attempt <= 10:
        return 30
    return 60


@dataclass
class ProviderHealth:
    symbol: str
    provider: str
    state: str
    is_real: bool
    snapshots_received: int
    consecutive_valid_snapshots: int
    warmup_required: int
    last_snapshot_ts: Optional[str]
    last_snapshot_age_sec: Optional[float]
    stale_threshold_sec: float
    last_error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "symbol": self.symbol,
            "provider": self.provider,
            "state": self.state,
            "is_real": self.is_real,
            "snapshots_received": self.snapshots_received,
            "consecutive_valid_snapshots": self.consecutive_valid_snapshots,
            "warmup_required": self.warmup_required,
            "last_snapshot_ts": self.last_snapshot_ts,
            "last_snapshot_age_sec": self.last_snapshot_age_sec,
            "stale_threshold_sec": self.stale_threshold_sec,
            "last_error": self.last_error,
        }


class MarketDataProvider:
    """Provider interface (per-symbol instance)."""

    venue_name: str = "unknown"
    is_real: bool = False

    def __init__(self, symbol: str):
        self.symbol = symbol.upper()
        self.state: FeedState = FeedState.DISCONNECTED
        self.latest_snapshot: Optional[RealDOMSnapshot] = None
        self.last_error: Optional[str] = None
        self.snapshots_received: int = 0
        self.consecutive_valid_snapshots: int = 0
        self.callbacks: List[Callable[[RealDOMSnapshot], None]] = []

        self._warmup_required: int = _env_int("DOM_SNAPSHOT_WARMUP", 10)
        self._stale_threshold_sec: float = _env_float("DOM_STALE_THRESHOLD_SEC", 5.0)

    @classmethod
    def supports_symbol(cls, symbol: str) -> bool:
        return False

    def on_snapshot(self, cb: Callable[[RealDOMSnapshot], None]) -> None:
        self.callbacks.append(cb)

    def is_stale(self, now: Optional[datetime] = None) -> bool:
        if not self.latest_snapshot:
            return True
        return self.latest_snapshot.age_seconds(now=now) > self._stale_threshold_sec

    def is_ready(self) -> bool:
        return (
            self.state == FeedState.CONNECTED
            and self.latest_snapshot is not None
            and not self.is_stale()
            and self.consecutive_valid_snapshots >= self._warmup_required
        )

    def get_snapshot(self) -> Optional[RealDOMSnapshot]:
        return self.latest_snapshot

    async def start(self) -> bool:
        raise NotImplementedError

    async def stop(self) -> None:
        raise NotImplementedError

    def get_health(self) -> ProviderHealth:
        last_ts = self.latest_snapshot.timestamp.isoformat() if self.latest_snapshot else None
        age = self.latest_snapshot.age_seconds() if self.latest_snapshot else None
        return ProviderHealth(
            symbol=self.symbol,
            provider=self.venue_name,
            state=self.state.value,
            is_real=self.is_real,
            snapshots_received=self.snapshots_received,
            consecutive_valid_snapshots=self.consecutive_valid_snapshots,
            warmup_required=self._warmup_required,
            last_snapshot_ts=last_ts,
            last_snapshot_age_sec=age,
            stale_threshold_sec=self._stale_threshold_sec,
            last_error=self.last_error,
        )


class NoDOMProvider(MarketDataProvider):
    venue_name = "no_dom"
    is_real = False

    def __init__(self, symbol: str):
        super().__init__(symbol=symbol)
        # Always connected with an empty (Tier C) snapshot.
        now = datetime.now(timezone.utc)
        self.state = FeedState.CONNECTED
        self.latest_snapshot = RealDOMSnapshot(
            symbol=self.symbol,
            venue=self.venue_name,
            timestamp=now,
            bids=[],
            asks=[],
            spread=0.0,
            mid_price=0.0,
            book_imbalance=0.0,
            total_bid_size=0.0,
            total_ask_size=0.0,
            liquidity_walls=[],
            is_real=False,
        )
        self.consecutive_valid_snapshots = self._warmup_required
        self.snapshots_received = 1

    @classmethod
    def supports_symbol(cls, symbol: str) -> bool:
        return True

    def is_stale(self, now: Optional[datetime] = None) -> bool:
        # NoDOM is synthetic/empty; treat as always "fresh" for display.
        return False

    async def start(self) -> bool:
        return True

    async def stop(self) -> None:
        self.state = FeedState.DISCONNECTED


class CoinbaseL2Provider(MarketDataProvider):
    venue_name = "coinbase"
    is_real = True

    @classmethod
    def supports_symbol(cls, symbol: str) -> bool:
        # REAL_DOM_POLICY.md §2.1: USD pairs (but NOT USDT).
        s = symbol.upper()
        return s.endswith("USD") and not s.endswith("USDT")

    async def start(self) -> bool:
        # Stub implementation (policy says STUB is acceptable for now).
        self.state = FeedState.ERROR
        self.last_error = "CoinbaseL2Provider is a stub (not implemented)"
        return False

    async def stop(self) -> None:
        self.state = FeedState.DISCONNECTED


class BinanceL2Provider(MarketDataProvider):
    venue_name = "binance"
    is_real = True

    WEBSOCKET_URL = "wss://stream.binance.com:9443/ws"

    def __init__(self, symbol: str, depth: int = 20):
        super().__init__(symbol=symbol)
        self.depth = depth
        self.websocket: Any = None
        self.running: bool = False
        self._reconnect_attempt: int = 0
        self._max_retries: int = _env_int("DOM_RECONNECT_MAX_RETRIES", 100)
        self._spread_alert_multiplier: float = _env_float("DOM_SPREAD_ALERT_MULTIPLIER", 3.0)
        self._baseline_spread: Optional[float] = None
        self._warmup_spreads: List[float] = []

    @classmethod
    def supports_symbol(cls, symbol: str) -> bool:
        # REAL_DOM_POLICY.md §2.1: Binance pairs ending in USDT/BUSD/BTC/ETH/BNB
        s = symbol.upper()
        return s.endswith(("USDT", "BUSD", "BTC", "ETH", "BNB"))

    def _stream_name(self) -> str:
        return f"{self.symbol.lower()}@depth{self.depth}@100ms"

    def _ensure_deps(self) -> Optional[Any]:
        try:
            import websockets  # type: ignore
        except Exception:
            return None
        return websockets

    async def _connect(self) -> bool:
        websockets = self._ensure_deps()
        if websockets is None:
            self.state = FeedState.ERROR
            self.last_error = "Missing dependency: websockets (pip install websockets)"
            logger.error(self.last_error)
            return False

        if self.state == FeedState.CONNECTED and self.websocket is not None:
            return True

        self.state = FeedState.CONNECTING
        stream_url = f"{self.WEBSOCKET_URL}/{self._stream_name()}"
        try:
            self.websocket = await websockets.connect(stream_url)
            logger.info("Connected Binance L2: %s", stream_url)
            return True
        except Exception as e:
            self.last_error = f"connect_failed: {type(e).__name__}: {e}"
            self.state = FeedState.DISCONNECTED
            logger.error("BinanceL2Provider connect failed: %s", self.last_error)
            return False

    async def _disconnect(self) -> None:
        self.running = False
        ws = self.websocket
        self.websocket = None
        if ws is not None:
            try:
                await ws.close()
            except Exception:
                pass
        self.state = FeedState.DISCONNECTED

    def _parse_depth_update(self, data: Dict[str, Any]) -> Optional[RealDOMSnapshot]:
        timestamp = datetime.now(timezone.utc)

        bids: List[DOMLevel] = []
        asks: List[DOMLevel] = []

        # Binance payload keys: "b"/"a" or "bids"/"asks"
        for bid in data.get("b", data.get("bids", []))[: self.depth]:
            try:
                price = float(bid[0])
                size = float(bid[1])
            except Exception:
                continue
            if size > 0:
                bids.append(DOMLevel(price=price, size=size, is_bid=True, timestamp=timestamp))

        for ask in data.get("a", data.get("asks", []))[: self.depth]:
            try:
                price = float(ask[0])
                size = float(ask[1])
            except Exception:
                continue
            if size > 0:
                asks.append(DOMLevel(price=price, size=size, is_bid=False, timestamp=timestamp))

        if not bids or not asks:
            return None

        bids.sort(key=lambda x: x.price, reverse=True)
        asks.sort(key=lambda x: x.price)

        best_bid = bids[0].price
        best_ask = asks[0].price
        spread = best_ask - best_bid
        mid = (best_bid + best_ask) / 2

        total_bid_size = sum(b.size for b in bids)
        total_ask_size = sum(a.size for a in asks)
        total_size = total_bid_size + total_ask_size
        imbalance = (total_bid_size - total_ask_size) / total_size if total_size > 0 else 0.0

        all_levels = bids + asks
        avg_size = sum(l.size for l in all_levels) / len(all_levels)
        liquidity_walls = [l for l in all_levels if l.size > avg_size * 2]

        return RealDOMSnapshot(
            symbol=self.symbol.upper(),
            venue=self.venue_name,
            timestamp=timestamp,
            bids=bids,
            asks=asks,
            spread=float(spread),
            mid_price=float(mid),
            book_imbalance=round(float(imbalance), 4),
            total_bid_size=float(total_bid_size),
            total_ask_size=float(total_ask_size),
            liquidity_walls=liquidity_walls,
            is_real=True,
        )

    def _update_state_from_snapshot(self, snapshot: RealDOMSnapshot) -> None:
        # Warmup: require N consecutive valid snapshots.
        self.snapshots_received += 1

        if snapshot.bids and snapshot.asks:
            # Spread monitoring: build baseline during warmup.
            if self._baseline_spread is None:
                self._warmup_spreads.append(snapshot.spread)
                if len(self._warmup_spreads) >= self._warmup_required:
                    avg = sum(self._warmup_spreads) / len(self._warmup_spreads)
                    self._baseline_spread = max(avg, 1e-12)

            if self._baseline_spread is not None and snapshot.spread > self._baseline_spread * self._spread_alert_multiplier:
                # Abnormal spread: do not count as valid.
                self.consecutive_valid_snapshots = 0
                self.state = FeedState.CONNECTING
                logger.warning(
                    "BinanceL2Provider spread abnormal (%s): spread=%s baseline=%s",
                    self.symbol,
                    snapshot.spread,
                    self._baseline_spread,
                )
                return

            self.consecutive_valid_snapshots += 1
        else:
            self.consecutive_valid_snapshots = 0

        # Staleness is checked dynamically in fail_closed_check; keep state CONNECTING until warmup met.
        if self.consecutive_valid_snapshots >= self._warmup_required:
            self.state = FeedState.CONNECTED
        else:
            self.state = FeedState.CONNECTING

    async def start(self) -> bool:
        if self.running:
            return True

        self.running = True
        self._reconnect_attempt = 0

        async def _run_loop() -> None:
            while self.running:
                if self._reconnect_attempt >= self._max_retries:
                    self.state = FeedState.ERROR
                    self.last_error = "reconnect_max_retries_exceeded"
                    logger.error("BinanceL2Provider max retries exceeded: %s", self.symbol)
                    return

                connected = await self._connect()
                if not connected:
                    self._reconnect_attempt += 1
                    await asyncio.sleep(_reconnect_delay_seconds(self._reconnect_attempt))
                    continue

                try:
                    assert self.websocket is not None
                    raw = await self.websocket.recv()
                    data = json.loads(raw)
                    snapshot = self._parse_depth_update(data)
                    if snapshot is None:
                        continue
                    self.latest_snapshot = snapshot
                    self._update_state_from_snapshot(snapshot)
                    for cb in self.callbacks:
                        try:
                            cb(snapshot)
                        except Exception as e:
                            logger.error("snapshot callback error: %s", e)
                except Exception as e:
                    self.last_error = f"feed_loop_error: {type(e).__name__}: {e}"
                    logger.warning("BinanceL2Provider error (%s): %s", self.symbol, self.last_error)
                    await self._disconnect()
                    self._reconnect_attempt += 1
                    await asyncio.sleep(_reconnect_delay_seconds(self._reconnect_attempt))

        asyncio.create_task(_run_loop())
        return True

    async def stop(self) -> None:
        await self._disconnect()


class MarketDataRegistry:
    """
    Provider registry + policy enforcement.

    The registry owns provider instances and is the single place where fail-closed
    checks are performed.
    """

    def __init__(self) -> None:
        self.providers: Dict[str, MarketDataProvider] = {}

    def _provider_for_symbol(self, symbol: str) -> MarketDataProvider:
        sym = symbol.upper()
        if BinanceL2Provider.supports_symbol(sym):
            return BinanceL2Provider(symbol=sym)
        if CoinbaseL2Provider.supports_symbol(sym):
            return CoinbaseL2Provider(symbol=sym)
        return NoDOMProvider(symbol=sym)

    def get_provider(self, symbol: str) -> MarketDataProvider:
        sym = symbol.upper()
        if sym not in self.providers:
            self.providers[sym] = self._provider_for_symbol(sym)
        return self.providers[sym]

    def override_provider(self, symbol: str, provider: MarketDataProvider) -> None:
        """Test hook: force a provider instance for a symbol."""
        self.providers[symbol.upper()] = provider

    async def start(self, symbol: str) -> bool:
        provider = self.get_provider(symbol)
        return await provider.start()

    async def stop(self, symbol: str) -> None:
        provider = self.get_provider(symbol)
        await provider.stop()

    def get_snapshot(self, symbol: str) -> Optional[RealDOMSnapshot]:
        return self.get_provider(symbol).get_snapshot()

    def get_status(self) -> Dict[str, Any]:
        return {
            "real_dom_required": _is_real_dom_required(),
            "providers": {sym: p.get_health().to_dict() for sym, p in self.providers.items()},
        }

    def fail_closed_check(self, symbol: str) -> Dict[str, Any]:
        provider = self.get_provider(symbol)
        health = provider.get_health()
        required = _is_real_dom_required()

        # Refresh stale state on-demand.
        is_stale = provider.latest_snapshot is not None and provider.is_stale()
        if is_stale:
            provider.state = FeedState.STALE

        if required:
            if not provider.is_real:
                return {
                    "allowed": False,
                    "reason": f"No qualified real DOM provider for {symbol}",
                    "provider": provider.venue_name,
                    "state": provider.state.value,
                    "is_real": False,
                    "health": health.to_dict(),
                }
            if is_stale:
                return {
                    "allowed": False,
                    "reason": f"DOM data stale for {symbol}",
                    "provider": provider.venue_name,
                    "state": FeedState.STALE.value,
                    "is_real": True,
                    "health": health.to_dict(),
                }
            if provider.state != FeedState.CONNECTED:
                return {
                    "allowed": False,
                    "reason": f"DOM feed not connected for {symbol}",
                    "provider": provider.venue_name,
                    "state": provider.state.value,
                    "is_real": True,
                    "health": health.to_dict(),
                }
            if provider.consecutive_valid_snapshots < _env_int("DOM_SNAPSHOT_WARMUP", 10):
                return {
                    "allowed": False,
                    "reason": f"DOM warmup not met for {symbol}",
                    "provider": provider.venue_name,
                    "state": FeedState.CONNECTING.value,
                    "is_real": True,
                    "health": health.to_dict(),
                }

        return {
            "allowed": True,
            "reason": "OK",
            "provider": provider.venue_name,
            "state": provider.state.value,
            "is_real": provider.is_real,
            "health": health.to_dict(),
        }


# Global registry instance (used by API layer)
market_data_registry = MarketDataRegistry()
