from __future__ import annotations

import json
from dataclasses import asdict, is_dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

try:
    import numpy as np
except Exception:  # pragma: no cover
    np = None  # type: ignore


def _jsonable(x: Any) -> Any:
    """Best-effort JSON conversion."""
    if is_dataclass(x):
        return asdict(x)
    if isinstance(x, Path):
        return str(x)
    if isinstance(x, datetime):
        return x.isoformat()
    if np is not None and isinstance(x, getattr(np, "generic", ())):
        return x.item()
    if isinstance(x, (set, tuple)):
        return list(x)
    return x


def dumps(obj: Any) -> str:
    return json.dumps(obj, default=_jsonable, sort_keys=True, separators=(",", ":"))


def log_jsonl(path: str | Path, event: Dict[str, Any], *, add_ts: bool = True) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    if add_ts and "ts_utc" not in event:
        event = dict(event)
        event["ts_utc"] = datetime.now(timezone.utc).isoformat()
    with p.open("a", encoding="utf-8") as f:
        f.write(dumps(event) + "\n")


def read_jsonl(path: str | Path, limit: Optional[int] = None):
    p = Path(path)
    if not p.exists():
        return []
    out = []
    with p.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            out.append(json.loads(line))
            if limit is not None and len(out) >= limit:
                break
    return out
