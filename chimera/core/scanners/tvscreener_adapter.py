from __future__ import annotations

import hashlib
import json
import random
import threading
import time
from collections import deque
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional, Sequence, TypedDict


class NormalizedRow(TypedDict):
    # Strict schema (required keys).
    symbol: str
    exchange: str
    asset_class: str
    price: Optional[float]
    change_pct: Optional[float]
    volume: Optional[float]
    market_cap: Optional[float]
    volatility: Optional[float]
    rsi: Optional[float]
    timeframe: str
    source: str
    ts: str
    # Extra reliability signal. Not part of the minimum strict schema, but
    # required by this adapter's risk-controls.
    stale: bool


@dataclass(frozen=True)
class _TVScreenerConfig:
    enabled: bool = True
    ttl_seconds: int = 60
    max_requests_per_min: int = 30
    timeout_seconds: int = 10


@dataclass
class _CacheEntry:
    fetched_ts: float
    expires_ts: float
    rows: list[NormalizedRow]


class _RateLimitError(RuntimeError):
    pass


_CACHE: dict[str, _CacheEntry] = {}
_CACHE_LOCK = threading.Lock()

_REQUEST_TIMES: deque[float] = deque()
_REQUEST_TIMES_LOCK = threading.Lock()


def _repo_root() -> Path:
    # chimera/core/scanners/tvscreener_adapter.py -> repo root is 3 parents up
    return Path(__file__).resolve().parents[3]


def _now_ts() -> float:
    return time.time()


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _clamp_int(value: Any, *, min_value: int, max_value: int, default: int) -> int:
    try:
        v = int(value)
    except (TypeError, ValueError):
        return default
    return max(min_value, min(max_value, v))


def _parse_simple_yaml(text: str) -> dict[str, Any]:
    """Parse a minimal subset of YAML needed for config/scanners.yaml.

    Supports:
    - top-level mapping keys
    - one level of nested mapping (2-space indentation)
    - bool/int/float/str scalars
    """
    result: dict[str, Any] = {}
    current_section: Optional[str] = None

    for raw_line in text.splitlines():
        line = raw_line.split("#", 1)[0].rstrip()
        if not line.strip():
            continue

        if not line.startswith(" "):
            # section header: "tvscreener:"
            if line.endswith(":"):
                current_section = line[:-1].strip()
                result[current_section] = {}
            else:
                # top-level key: value
                if ":" in line:
                    k, v = line.split(":", 1)
                    result[k.strip()] = v.strip()
            continue

        if current_section is None:
            continue

        # nested "  key: value"
        stripped = line.strip()
        if ":" not in stripped:
            continue
        k, v = stripped.split(":", 1)
        key = k.strip()
        val_raw = v.strip()

        if val_raw.lower() in {"true", "false"}:
            val: Any = val_raw.lower() == "true"
        else:
            # int / float fallback
            try:
                val = int(val_raw)
            except ValueError:
                try:
                    val = float(val_raw)
                except ValueError:
                    val = val_raw

        section_obj = result.get(current_section)
        if isinstance(section_obj, dict):
            section_obj[key] = val

    return result


def _load_config(config_path: Optional[Path] = None) -> _TVScreenerConfig:
    path = config_path or (_repo_root() / "config" / "scanners.yaml")
    data: dict[str, Any] = {}
    if path.exists():
        text = path.read_text(encoding="utf-8")
        try:
            import yaml  # type: ignore
        except Exception:
            data = _parse_simple_yaml(text)
        else:
            loaded = yaml.safe_load(text)  # type: ignore[attr-defined]
            if isinstance(loaded, dict):
                data = loaded

    tv = data.get("tvscreener", {}) if isinstance(data.get("tvscreener", {}), dict) else {}
    enabled = bool(tv.get("enabled", True))

    # TTL is constrained to 30-120s per requirements.
    ttl_seconds = _clamp_int(tv.get("ttl_seconds", 60), min_value=30, max_value=120, default=60)
    max_rpm = _clamp_int(tv.get("max_requests_per_min", 30), min_value=1, max_value=600, default=30)
    timeout_seconds = _clamp_int(tv.get("timeout_seconds", 10), min_value=1, max_value=60, default=10)

    return _TVScreenerConfig(
        enabled=enabled,
        ttl_seconds=ttl_seconds,
        max_requests_per_min=max_rpm,
        timeout_seconds=timeout_seconds,
    )


def _make_cache_key(
    *,
    asset_class: str,
    filters: Optional[Sequence[dict[str, Any]]],
    columns: Optional[Sequence[str]],
    sort: Any,
    limit: int,
    timeframe: str,
) -> str:
    payload = {
        "asset_class": asset_class,
        "filters": list(filters) if filters else [],
        "columns": list(columns) if columns else [],
        "sort": sort,
        "limit": int(limit),
        "timeframe": timeframe,
    }
    blob = json.dumps(payload, sort_keys=True, default=str).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()


def _enforce_rate_limit(max_requests_per_min: int) -> None:
    now = _now_ts()
    window_start = now - 60.0
    with _REQUEST_TIMES_LOCK:
        while _REQUEST_TIMES and _REQUEST_TIMES[0] < window_start:
            _REQUEST_TIMES.popleft()
        if len(_REQUEST_TIMES) >= max_requests_per_min:
            raise _RateLimitError(f"tvscreener rate limit exceeded: {len(_REQUEST_TIMES)}/{max_requests_per_min} rpm")
        _REQUEST_TIMES.append(now)


def _normalize_timeframe(timeframe: str) -> str:
    tf = (timeframe or "1D").strip()
    tf_upper = tf.upper()
    # Common aliases
    if tf_upper in {"D", "1D", "1DAY", "DAY"}:
        return "1D"
    if tf_upper in {"W", "1W", "1WK", "WEEK"}:
        return "1W"
    if tf_upper in {"M", "1M", "1MO", "MONTH"}:
        return "1M"
    if tf_upper in {"1H", "H"}:
        return "60"
    if tf_upper == "4H":
        return "240"
    if tf_upper.endswith("MIN"):
        # "15min" -> "15"
        digits = "".join([c for c in tf_upper if c.isdigit()])
        return digits or tf
    return tf


def _safe_float(value: Any) -> Optional[float]:
    try:
        if value is None:
            return None
        if isinstance(value, bool):
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _parse_symbol_exchange(symbol_field: str) -> tuple[str, str]:
    raw = (symbol_field or "").strip()
    if ":" in raw:
        exch, sym = raw.split(":", 1)
        return sym, exch
    return raw, ""


def _pick_field_enum(asset_class: str):
    """Return (ScreenerClass, FieldEnum) for tvscreener, or raise ValueError."""
    ac = (asset_class or "").strip().lower()

    try:
        import tvscreener  # type: ignore  # noqa: F401
    except Exception as e:  # pragma: no cover
        raise ImportError("tvscreener dependency not available") from e

    if ac in {"forex", "fx", "currency", "currencies"}:
        from tvscreener import ForexScreener  # type: ignore
        from tvscreener.field.forex import ForexField  # type: ignore

        return ForexScreener, ForexField

    if ac in {"crypto", "cryptocurrency"}:
        from tvscreener import CryptoScreener  # type: ignore
        from tvscreener.field.crypto import CryptoField  # type: ignore

        return CryptoScreener, CryptoField

    if ac in {"stock", "stocks", "equity"}:
        from tvscreener import StockScreener  # type: ignore
        from tvscreener.field.stock import StockField  # type: ignore

        return StockScreener, StockField

    if ac in {"futures"}:
        from tvscreener import FuturesScreener  # type: ignore
        from tvscreener.field.futures import FuturesField  # type: ignore

        return FuturesScreener, FuturesField

    if ac in {"bond", "bonds"}:
        from tvscreener import BondScreener  # type: ignore
        from tvscreener.field.bond import BondField  # type: ignore

        return BondScreener, BondField

    if ac in {"coin", "coins"}:
        from tvscreener import CoinScreener  # type: ignore
        from tvscreener.field.coin import CoinField  # type: ignore

        return CoinScreener, CoinField

    raise ValueError(f"Unsupported asset_class: {asset_class}")


def _resolve_change_field(FieldEnum: Any, timeframe: str):
    tf = _normalize_timeframe(timeframe)
    mapping = {
        "60": "CHANGE_1H_PERCENT",
        "240": "CHANGE_4H_PERCENT",
        "15": "CHANGE_15MIN_PERCENT",
        "5": "CHANGE_5MIN_PERCENT",
        "1W": "CHANGE_1W_PERCENT",
        "1M": "CHANGE_1M_PERCENT",
        "1D": "CHANGE_PERCENT",
    }
    field_name = mapping.get(tf, "CHANGE_PERCENT")
    return getattr(FieldEnum, field_name, getattr(FieldEnum, "CHANGE_PERCENT"))


def _resolve_rsi_field(FieldEnum: Any, timeframe: str):
    tf = _normalize_timeframe(timeframe)
    if tf in {"1D", ""}:
        return getattr(FieldEnum, "RSI10")
    candidate = f"RSI10_{tf}"
    return getattr(FieldEnum, candidate, getattr(FieldEnum, "RSI10"))


def _resolve_market_cap_field(FieldEnum: Any):
    return getattr(FieldEnum, "MARKET_CAPITALIZATION", None)


def _resolve_volatility_field(FieldEnum: Any):
    return getattr(FieldEnum, "VOLATILITY", None)


def _resolve_volume_field(FieldEnum: Any):
    return getattr(FieldEnum, "VOLUME", None)


def _resolve_price_field(FieldEnum: Any):
    return getattr(FieldEnum, "PRICE", None)


def _fetch_raw_rows(
    *,
    asset_class: str,
    filters: Optional[Sequence[dict[str, Any]]],
    columns: Optional[Sequence[str]],
    sort: Any,
    limit: int,
    timeframe: str,
    timeout_seconds: int,
) -> tuple[list[dict[str, Any]], dict[str, Optional[str]], str]:
    """Fetch raw rows from tvscreener.

    Returns:
    - raw rows (list of dicts)
    - label map from normalized keys to raw dict keys
    - normalized timeframe string
    """
    tf = _normalize_timeframe(timeframe)
    ScreenerClass, FieldEnum = _pick_field_enum(asset_class)

    # Configure tvscreener timeout (library uses a global constant).
    import tvscreener.core.base as tv_base  # type: ignore

    tv_base.REQUEST_TIMEOUT = int(timeout_seconds)

    screener = ScreenerClass()
    screener.set_range(0, int(limit))

    requested: list[Any] = []

    exchange_field = getattr(FieldEnum, "EXCHANGE", None)
    if exchange_field is not None:
        requested.append(exchange_field)

    price_field = _resolve_price_field(FieldEnum)
    if price_field is not None:
        requested.append(price_field)

    change_field = _resolve_change_field(FieldEnum, tf)
    if change_field is not None:
        requested.append(change_field)

    volume_field = _resolve_volume_field(FieldEnum)
    if volume_field is not None:
        requested.append(volume_field)

    # Optional fields based on requested columns, but safe defaults if columns is None.
    want = set([c.strip().lower() for c in columns]) if columns else {"market_cap", "volatility", "rsi"}

    market_cap_field = _resolve_market_cap_field(FieldEnum)
    if market_cap_field is not None and "market_cap" in want:
        requested.append(market_cap_field)

    volatility_field = _resolve_volatility_field(FieldEnum)
    if volatility_field is not None and "volatility" in want:
        requested.append(volatility_field)

    rsi_field = _resolve_rsi_field(FieldEnum, tf)
    if rsi_field is not None and "rsi" in want:
        requested.append(rsi_field)

    # Apply basic filters if provided.
    if filters:
        try:
            from tvscreener.filter import FilterOperator  # type: ignore
        except Exception:
            FilterOperator = None  # type: ignore
        for f in filters:
            if not isinstance(f, dict):
                continue
            field_name = str(f.get("field", "")).strip()
            op = str(f.get("op", "")).strip()
            value = f.get("value")
            if not field_name:
                continue
            field_obj = getattr(FieldEnum, field_name, None)
            if field_obj is None or FilterOperator is None:
                continue
            op_map = {
                ">": FilterOperator.ABOVE,
                ">=": FilterOperator.ABOVE_OR_EQUAL,
                "<": FilterOperator.BELOW,
                "<=": FilterOperator.BELOW_OR_EQUAL,
                "==": FilterOperator.EQUAL,
                "!=": FilterOperator.NOT_EQUAL,
                "in": FilterOperator.IN_RANGE,
                "between": FilterOperator.IN_RANGE,
            }
            op_obj = op_map.get(op)
            if op_obj is None:
                continue
            screener.add_filter(field_obj, op_obj, value)

    # Sort config (optional).
    if sort:
        try:
            ascending = True
            sort_field = None
            if isinstance(sort, str):
                s = sort.strip()
                if s.startswith("-"):
                    ascending = False
                    s = s[1:]
                sort_field = s
            elif isinstance(sort, dict):
                sort_field = sort.get("field") or sort.get("by")
                ascending = bool(sort.get("ascending", True))

            if sort_field:
                # Support normalized field names.
                sf = str(sort_field).strip().lower()
                if sf in {"change", "change_pct", "changepct"}:
                    screener.sort_by(change_field, ascending=ascending)
                elif sf in {"price"} and price_field is not None:
                    screener.sort_by(price_field, ascending=ascending)
            else:
                # Default: change descending.
                screener.sort_by(change_field, ascending=False)
        except Exception:
            # Ignore sort issues (non-critical).
            pass
    else:
        try:
            screener.sort_by(change_field, ascending=False)
        except Exception:
            pass

    # Execute request.
    df = screener.select(*requested).get()
    raw_rows: list[dict[str, Any]] = df.to_dict(orient="records")

    labels = {
        "price": getattr(price_field, "label", None),
        "change_pct": getattr(change_field, "label", None),
        "volume": getattr(volume_field, "label", None),
        "market_cap": getattr(market_cap_field, "label", None) if market_cap_field is not None else None,
        "volatility": getattr(volatility_field, "label", None) if volatility_field is not None else None,
        "rsi": getattr(rsi_field, "label", None) if rsi_field is not None else None,
        "exchange": getattr(exchange_field, "label", "Exchange") if exchange_field is not None else "Exchange",
        "symbol": "Symbol",
    }
    return raw_rows, labels, tf


def _normalize_rows(
    *,
    raw_rows: list[dict[str, Any]],
    labels: dict[str, Optional[str]],
    asset_class: str,
    timeframe: str,
    ts_iso: str,
    stale: bool,
) -> list[NormalizedRow]:
    out: list[NormalizedRow] = []
    for row in raw_rows:
        symbol_field = str(row.get(labels.get("symbol") or "Symbol") or "")
        sym, exch_from_symbol = _parse_symbol_exchange(symbol_field)

        exchange = str(row.get(labels.get("exchange") or "Exchange") or exch_from_symbol or "")

        out.append(
            {
                "symbol": sym,
                "exchange": exchange,
                "asset_class": asset_class,
                "price": _safe_float(row.get(labels.get("price") or "Price")),
                "change_pct": _safe_float(row.get(labels.get("change_pct") or "Change %")),
                "volume": _safe_float(row.get(labels.get("volume") or "Volume")),
                "market_cap": _safe_float(row.get(labels.get("market_cap") or "Market Capitalization")),
                "volatility": _safe_float(row.get(labels.get("volatility") or "Volatility")),
                "rsi": _safe_float(row.get(labels.get("rsi") or "Rsi10")),
                "timeframe": timeframe,
                "source": "tvscreener",
                "ts": ts_iso,
                "stale": bool(stale),
            }
        )
    return out


def scan(  # noqa: PLR0913 - adapter signature is intentionally explicit
    asset_class: str,
    filters: Optional[Sequence[dict[str, Any]]] = None,
    columns: Optional[Sequence[str]] = None,
    sort: Any = None,
    limit: int = 50,
    timeframe: str = "1D",
    *,
    config_path: Optional[str | Path] = None,
) -> list[NormalizedRow]:
    """Scan TradingView screener via deepentropy/tvscreener and return normalized rows.

    Non-critical behavior:
    - Rate-limited + backoff
    - In-memory cache with TTL (30-120s)
    - If request fails: return last cached result with `stale=True`
    """
    cfg = _load_config(Path(config_path) if config_path else None)
    if not cfg.enabled:
        return []

    tf = _normalize_timeframe(timeframe)
    limit_i = _clamp_int(limit, min_value=1, max_value=500, default=50)

    cache_key = _make_cache_key(
        asset_class=asset_class,
        filters=filters,
        columns=columns,
        sort=sort,
        limit=limit_i,
        timeframe=tf,
    )

    now = _now_ts()
    with _CACHE_LOCK:
        entry = _CACHE.get(cache_key)
        if entry and now < entry.expires_ts:
            # Fresh cache hit.
            return [dict(r, stale=False) for r in entry.rows]  # type: ignore[misc]

    # Cache miss/expired -> try network with backoff.
    max_attempts = 3
    last_err: Optional[Exception] = None
    for attempt in range(max_attempts):
        try:
            _enforce_rate_limit(cfg.max_requests_per_min)
            raw_rows, labels, tf_effective = _fetch_raw_rows(
                asset_class=asset_class,
                filters=filters,
                columns=columns,
                sort=sort,
                limit=limit_i,
                timeframe=tf,
                timeout_seconds=cfg.timeout_seconds,
            )
            ts_iso = _utc_now_iso()
            rows = _normalize_rows(
                raw_rows=raw_rows,
                labels=labels,
                asset_class=asset_class,
                timeframe=tf_effective,
                ts_iso=ts_iso,
                stale=False,
            )
            with _CACHE_LOCK:
                _CACHE[cache_key] = _CacheEntry(
                    fetched_ts=now,
                    expires_ts=now + float(cfg.ttl_seconds),
                    rows=rows,
                )
            return rows
        except Exception as e:  # pragma: no cover - errors depend on runtime env
            last_err = e
            if attempt == max_attempts - 1:
                break
            # Exponential backoff with jitter, capped.
            delay = min(4.0, (0.5 * (2**attempt)) + random.random() * 0.1)
            time.sleep(delay)

    # Failure path: return last cached results as stale, if any.
    with _CACHE_LOCK:
        entry = _CACHE.get(cache_key)
        if entry:
            return [dict(r, stale=True) for r in entry.rows]  # type: ignore[misc]

    # No cache available: fail safely with empty output.
    _ = last_err
    return []


def healthcheck(*, config_path: Optional[str | Path] = None) -> bool:
    cfg = _load_config(Path(config_path) if config_path else None)
    if not cfg.enabled:
        return False
    try:
        import tvscreener  # type: ignore  # noqa: F401

        return True
    except Exception:
        return False

