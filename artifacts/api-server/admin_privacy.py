"""Strip user phone numbers from admin-facing API payloads."""
from __future__ import annotations

from typing import Any

_ADMIN_PII_KEYS = frozenset(
    {"phone", "user_phone", "country_code", "contact_value", "customer_phone"}
)


def strip_phone_fields(row: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(row, dict):
        return row
    return {k: v for k, v in row.items() if k not in _ADMIN_PII_KEYS}


def strip_admin_pii_deep(obj: Any) -> Any:
    if isinstance(obj, dict):
        return {
            k: strip_admin_pii_deep(v)
            for k, v in obj.items()
            if k not in _ADMIN_PII_KEYS
        }
    if isinstance(obj, list):
        return [strip_admin_pii_deep(x) for x in obj]
    return obj
