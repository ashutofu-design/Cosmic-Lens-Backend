"""
JSON codec for Redis payloads (numpy, dataclasses, datetime, Decimal).

Face sessions store landmark dicts + metadata — never numpy rgb_image arrays.
"""
from __future__ import annotations

import base64
import json
import logging
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Optional

log = logging.getLogger(__name__)

try:
    import numpy as np
except Exception:
    np = None  # type: ignore


class _Encoder(json.JSONEncoder):
    def default(self, o: Any) -> Any:
        if np is not None:
            if isinstance(o, np.ndarray):
                return {"__np__": True, "dtype": str(o.dtype), "shape": o.shape,
                        "data": base64.b64encode(o.tobytes()).decode("ascii")}
            if isinstance(o, (np.integer, np.floating)):
                return o.item()
        if isinstance(o, (datetime, date)):
            return {"__dt__": True, "iso": o.isoformat()}
        if isinstance(o, Decimal):
            return {"__dec__": True, "s": str(o)}
        if isinstance(o, bytes):
            return {"__b64__": True, "data": base64.b64encode(o).decode("ascii")}
        if hasattr(o, "__dataclass_fields__"):
            from dataclasses import asdict
            return {"__dc__": type(o).__name__, "d": asdict(o)}
        return super().default(o)


def _object_hook(obj: dict) -> Any:
    if "__np__" in obj and np is not None:
        arr = np.frombuffer(
            base64.b64decode(obj["data"]),
            dtype=obj["dtype"],
        ).reshape(obj["shape"])
        return arr
    if "__dt__" in obj:
        s = obj["iso"]
        try:
            return datetime.fromisoformat(s.replace("Z", "+00:00"))
        except Exception:
            return s
    if "__dec__" in obj:
        return Decimal(obj["s"])
    if "__b64__" in obj:
        return base64.b64decode(obj["data"])
    return obj


def dumps(obj: Any) -> bytes:
    return json.dumps(obj, cls=_Encoder, ensure_ascii=False, separators=(",", ":")).encode("utf-8")


def loads(raw: Optional[bytes]) -> Any:
    if not raw:
        return None
    return json.loads(raw.decode("utf-8"), object_hook=_object_hook)


def estimate_bytes(obj: Any) -> int:
    try:
        return len(dumps(obj))
    except Exception:
        return 0
