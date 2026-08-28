"""Advisory client runtime-integrity telemetry.

The mobile app self-reports root/emulator/debug state in ``X-Client-Integrity``.
A rooted device can forge or omit that header at will, so this module only
records the signal for abuse triage and admin visibility.

It deliberately exposes no gate: authentication (``api_auth``), payment
verification (``payment_gateway``) and entitlement (the ``*_billing`` modules)
stay the only authorization boundary. Nothing here may be wired into an
allow/deny decision for money or premium access.
"""

from __future__ import annotations

import logging
import os

log = logging.getLogger(__name__)

HEADER = "X-Client-Integrity"

# Closed vocabulary — an attacker controls this header, so we never log or
# store arbitrary attacker-supplied text.
KNOWN_FLAGS: frozenset[str] = frozenset(
    {"rooted", "emulator", "debug", "expo-go", "devtools"}
)
_CLEAN = "ok"
_MAX_FLAGS = 5


def parse_integrity_header(raw: str | None) -> list[str]:
    """Return the recognised risk flags in a client-supplied header value."""
    if not raw:
        return []
    flags: list[str] = []
    for part in str(raw).split(",")[: _MAX_FLAGS * 2]:
        token = part.strip().lower()
        if token in KNOWN_FLAGS and token not in flags:
            flags.append(token)
        if len(flags) >= _MAX_FLAGS:
            break
    return flags


def integrity_summary(raw: str | None) -> str:
    """Compact value safe to put in structured logs."""
    flags = parse_integrity_header(raw)
    if flags:
        return ",".join(flags)
    return _CLEAN if raw else "unreported"


def current_summary() -> str:
    from flask import request

    try:
        return integrity_summary(request.headers.get(HEADER))
    except Exception:
        return "unreported"


def _log_flagged() -> bool:
    return os.environ.get("CLIENT_INTEGRITY_LOG", "1").strip().lower() not in (
        "0",
        "false",
        "off",
    )


def install_client_integrity_telemetry(app) -> None:
    """Record the advisory signal. Never returns a response — never blocks."""

    @app.before_request
    def _client_integrity_probe():  # noqa: ANN202
        if not _log_flagged():
            return None
        from flask import request

        flags = parse_integrity_header(request.headers.get(HEADER))
        if not flags:
            return None
        try:
            from app_attestation import path_is_protected

            sensitive = path_is_protected(request.path or "")
        except Exception:
            sensitive = False
        if not sensitive:
            return None
        log.warning(
            "[client_integrity] flags=%s path=%s user=%s (advisory only)",
            ",".join(flags),
            request.path,
            (request.headers.get("X-User-Id") or "-")[:16],
        )
        return None
