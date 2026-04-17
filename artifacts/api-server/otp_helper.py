"""
OTP-based authentication helper for Cosmic Lens.

Production: sends OTPs via MSG91 (https://msg91.com) — Indian DLT-compliant SMS gateway.
Dev mode: when MSG91_AUTH_KEY is not configured, OTPs are logged to console only.

Security model:
- 6-digit OTP, generated server-side (NOT taken from client)
- Stored as werkzeug salted hash (never plaintext)
- 10-minute TTL
- 60-second cooldown between consecutive sends to the same phone
- Max 5 incorrect verify attempts per OTP request → request invalidated
- Max 5 send-OTP requests per phone per hour (anti-spam)
- After verify success, OtpRequest is marked verified and cannot be reused

Phone format normalization:
- Strips all non-digits
- Country code separated from number
- Storage canonical form: "+{cc}{digits}" e.g. "+919876543210"
"""

import os
import re
import secrets
import logging
import urllib.parse
import urllib.request
import urllib.error
import json
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash

log = logging.getLogger(__name__)

# ── Config (knobs) ────────────────────────────────────────────────────────────
OTP_LENGTH          = 6
OTP_TTL_MINUTES     = 10
COOLDOWN_SECONDS    = 60          # min interval between two send-OTP for same phone
MAX_VERIFY_ATTEMPTS = 5           # incorrect OTP entries before request is invalidated
MAX_SENDS_PER_HOUR  = 5           # anti-spam: max OTP sends per phone per rolling hour

# MSG91 endpoints (Flow API — sends DLT-compliant template SMS)
MSG91_SEND_URL = "https://control.msg91.com/api/v5/flow"


# ── Helpers ───────────────────────────────────────────────────────────────────

def normalize_phone(country_code: str, phone: str) -> tuple[str, str, str]:
    """
    Normalize phone input to canonical E.164.
    Returns (country_code_digits, phone_digits, canonical_e164_like).
    Raises ValueError on invalid input.

    Canonicalization:
    - country_code: digits only, leading zeros stripped, default "91"
    - phone:       digits only, leading zeros from a national-trunk-prefix kept (no auto-strip)
    - total cc + national digits must respect E.164 max of 15
    """
    cc = re.sub(r"\D", "", country_code or "91").lstrip("0") or "91"
    ph = re.sub(r"\D", "", phone or "")
    if len(cc) > 3:
        # E.164 country codes are 1–3 digits
        raise ValueError("Invalid country code")
    if cc == "91":
        # India: must be exactly 10 digits, starting 6/7/8/9
        if len(ph) != 10 or ph[0] not in "6789":
            raise ValueError("Indian mobile number 10 digits ka hona chahiye, 6/7/8/9 se shuru")
    else:
        if len(ph) < 6 or len(ph) > (15 - len(cc)):
            raise ValueError(f"Phone must be 6–{15 - len(cc)} digits for country code +{cc}")
    return cc, ph, f"+{cc}{ph}"


def generate_otp() -> str:
    """Cryptographically-strong numeric OTP."""
    # Use secrets.randbelow for uniform distribution (avoids modulo bias)
    n = secrets.randbelow(10 ** OTP_LENGTH)
    return str(n).zfill(OTP_LENGTH)


# ── MSG91 SMS delivery ────────────────────────────────────────────────────────

def _msg91_configured() -> bool:
    return bool(
        os.environ.get("MSG91_AUTH_KEY")
        and os.environ.get("MSG91_TEMPLATE_ID")
    )


def send_sms_via_msg91(phone_e164: str, otp_code: str) -> tuple[bool, str]:
    """
    Send OTP via MSG91 Flow API. Requires DLT-registered template.
    Template variable convention: ##OTP## placeholder in template body
    (configurable via MSG91_OTP_VAR env var, default "OTP").

    Returns (success, message_or_error).
    """
    auth_key    = os.environ.get("MSG91_AUTH_KEY", "").strip()
    template_id = os.environ.get("MSG91_TEMPLATE_ID", "").strip()
    sender_id   = os.environ.get("MSG91_SENDER_ID", "").strip()  # optional, template default used
    otp_var     = os.environ.get("MSG91_OTP_VAR", "OTP").strip() or "OTP"

    if not auth_key or not template_id:
        return False, "MSG91 not configured (missing MSG91_AUTH_KEY/MSG91_TEMPLATE_ID)"

    # MSG91 expects mobile WITHOUT '+' prefix
    mobile = phone_e164.lstrip("+")

    # Flow API body — template variables are arbitrary keys
    payload = {
        "template_id": template_id,
        "recipients": [
            {
                "mobiles": mobile,
                otp_var:   otp_code,
            }
        ],
    }
    if sender_id:
        payload["sender"] = sender_id

    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        MSG91_SEND_URL,
        data=body,
        method="POST",
        headers={
            "Content-Type": "application/json",
            "authkey":      auth_key,
            "accept":       "application/json",
        },
    )

    try:
        with urllib.request.urlopen(req, timeout=8) as resp:
            raw  = resp.read().decode("utf-8", errors="replace")
            data = {}
            try:
                data = json.loads(raw)
            except Exception:
                pass
            # MSG91 success shape: {"type":"success", ...} or {"message":"..."}
            if (data.get("type") == "success") or (resp.status in (200, 201)):
                return True, data.get("message", "sent")
            return False, f"MSG91 rejected: {raw[:200]}"
    except urllib.error.HTTPError as e:
        try:
            err_body = e.read().decode("utf-8", errors="replace")[:200]
        except Exception:
            err_body = ""
        return False, f"MSG91 HTTP {e.code}: {err_body}"
    except Exception as e:
        return False, f"MSG91 network error: {e}"


# ── Public OTP API (used by Flask routes) ─────────────────────────────────────

def _phone_lock_key(phone_e164: str) -> int:
    """Stable 63-bit signed-int hash for Postgres advisory locks (per-phone serialization)."""
    import hashlib
    h = hashlib.sha256(phone_e164.encode("utf-8")).digest()
    # Take first 8 bytes as signed int64 (advisory locks accept BIGINT)
    return int.from_bytes(h[:8], "big", signed=True)


def _acquire_phone_lock(db, phone_e164: str) -> bool:
    """
    Acquire a per-phone advisory lock for the duration of the current transaction.
    Postgres-only; on other DBs returns True (no-op — single-process dev only).
    """
    try:
        from sqlalchemy import text
        # Only meaningful on Postgres
        bind_url = str(db.engine.url)
        if "postgresql" not in bind_url:
            return True
        key = _phone_lock_key(phone_e164)
        # pg_try_advisory_xact_lock returns true on success, false if held elsewhere
        row = db.session.execute(text("SELECT pg_try_advisory_xact_lock(:k)"), {"k": key}).scalar()
        return bool(row)
    except Exception as e:
        log.warning("[OTP] advisory lock acquire failed: %s", e)
        return True  # fail-open in dev; production is Postgres so this won't trigger


def send_otp(phone_e164: str, OtpRequest, db, ip: str = "") -> dict:
    """
    Generate + send an OTP to a phone number. SERIALIZED per phone via Postgres
    advisory lock so parallel requests can't both bypass cooldown / anti-spam.

    Returns dict:
      {ok: True,  request_id, expires_in, cooldown}
      {ok: False, error, retry_after?}
    """
    # Acquire per-phone lock (held until commit/rollback). If another request is
    # already inside this critical section for the same phone, treat as cooldown.
    if not _acquire_phone_lock(db, phone_e164):
        return {"ok": False,
                "error": "Pehle se ek request process ho rahi hai. Thodi der baad try karein.",
                "retry_after": 3}

    try:
        now = datetime.utcnow()

        # Anti-spam: count sends in last hour (lock guarantees a stable read)
        one_hour_ago = now - timedelta(hours=1)
        sends_recent = (OtpRequest.query
                        .filter(OtpRequest.phone == phone_e164,
                                OtpRequest.created_at > one_hour_ago)
                        .count())
        if sends_recent >= MAX_SENDS_PER_HOUR:
            db.session.commit()  # release lock
            return {"ok": False,
                    "error": "Bahut zyada attempts. Ek ghante baad try karein.",
                    "retry_after": 3600}

        # Cooldown: most recent send must be older than COOLDOWN_SECONDS
        last = (OtpRequest.query
                .filter(OtpRequest.phone == phone_e164)
                .order_by(OtpRequest.created_at.desc())
                .first())
        if last:
            elapsed = (now - last.created_at).total_seconds()
            if elapsed < COOLDOWN_SECONDS:
                wait = int(COOLDOWN_SECONDS - elapsed)
                db.session.commit()
                return {"ok": False,
                        "error": f"Naya OTP {wait} second baad mangwa sakte hain.",
                        "retry_after": wait}

        code      = generate_otp()
        code_hash = generate_password_hash(code)

        # Invalidate any previous unverified OTPs for this phone
        OtpRequest.query.filter(
            OtpRequest.phone == phone_e164,
            OtpRequest.verified.is_(False),
            OtpRequest.expires_at > now,
        ).update({OtpRequest.expires_at: now}, synchronize_session=False)

        req = OtpRequest(
            phone      = phone_e164,
            otp_hash   = code_hash,
            expires_at = now + timedelta(minutes=OTP_TTL_MINUTES),
            attempts   = 0,
            verified   = False,
            ip         = (ip or "")[:64],
            created_at = now,
        )
        db.session.add(req)
        db.session.commit()  # releases advisory lock
    except Exception:
        db.session.rollback()
        raise

    # Deliver (outside lock — SMS gateway latency shouldn't block other phones)
    if _msg91_configured():
        ok, msg = send_sms_via_msg91(phone_e164, code)
        if not ok:
            log.error("[OTP] MSG91 failed for %s: %s", phone_e164, msg)
            return {"ok": False, "error": "OTP bhejne mein dikkat. Thodi der baad try karein."}
        log.info("[OTP] Sent via MSG91 to %s (request_id=%s)", phone_e164, req.id)
        return {"ok": True, "request_id": req.id,
                "expires_in": OTP_TTL_MINUTES * 60,
                "cooldown":   COOLDOWN_SECONDS}

    # DEV MODE: log to console only. NEVER expose code over the API unless
    # COSMIC_OTP_DEV_RETURN=1 is explicitly set (local debug flag).
    log.warning("[OTP][DEV] phone=%s code=%s (MSG91 not configured)", phone_e164, code)
    print(f"\n[OTP][DEV] {phone_e164} → {code}\n", flush=True)
    resp = {"ok": True, "request_id": req.id,
            "expires_in": OTP_TTL_MINUTES * 60,
            "cooldown":   COOLDOWN_SECONDS,
            "dev_mode":   True}
    if os.environ.get("COSMIC_OTP_DEV_RETURN") == "1":
        resp["dev_otp"] = code
    return resp


def verify_otp(phone_e164: str, code: str, OtpRequest, db) -> dict:
    """
    Verify a 6-digit OTP for a phone number. SERIALIZED per phone via Postgres
    advisory lock + row-level SELECT FOR UPDATE so concurrent verifies cannot:
      - both succeed (replay attack)
      - bypass attempts++ counter
      - race with send-otp invalidation

    Returns dict:
      {ok: True}                                — verified, may mint user session
      {ok: False, error, attempts_left?}
    """
    code = (code or "").strip()
    if not code.isdigit() or len(code) != OTP_LENGTH:
        return {"ok": False, "error": f"{OTP_LENGTH}-digit OTP enter karein"}

    if not _acquire_phone_lock(db, phone_e164):
        return {"ok": False, "error": "Verify in progress, try again in a moment."}

    try:
        now = datetime.utcnow()
        # Lock the most-recent unverified row for this phone within the txn
        req = (OtpRequest.query
               .filter(OtpRequest.phone == phone_e164,
                       OtpRequest.verified.is_(False),
                       OtpRequest.expires_at > now)
               .order_by(OtpRequest.created_at.desc())
               .with_for_update()
               .first())

        if not req:
            db.session.commit()
            return {"ok": False, "error": "OTP expire ho gaya. Naya OTP mangwa lijiye."}

        if req.attempts >= MAX_VERIFY_ATTEMPTS:
            req.expires_at = now
            db.session.commit()
            return {"ok": False, "error": "Bahut galat attempts. Naya OTP mangwa lijiye."}

        # Increment attempts atomically (still inside txn / lock)
        req.attempts += 1

        ok = check_password_hash(req.otp_hash, code)
        if ok:
            req.verified = True
            db.session.commit()
            return {"ok": True}

        # Wrong code path — decide whether to invalidate
        left = MAX_VERIFY_ATTEMPTS - req.attempts
        if left <= 0:
            req.expires_at = now
            db.session.commit()
            return {"ok": False, "error": "Bahut galat attempts. Naya OTP mangwa lijiye."}
        db.session.commit()
        return {"ok": False,
                "error": f"Galat OTP. {left} attempt baki hain.",
                "attempts_left": left}
    except Exception:
        db.session.rollback()
        raise
