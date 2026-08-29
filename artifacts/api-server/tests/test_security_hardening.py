"""Adversarial verification for the 12 security layers.

Every test here is written from the attacker's side: it performs the attack and
asserts the server refuses it. Tests that need the full Flask app import it
lazily so the pure-config tests still run when optional deps are missing.
"""

from __future__ import annotations

import os
import unittest
from unittest.mock import MagicMock, patch


PROD_ENV = {
    "PROD": "1",
    "ADMIN_SECRET": "A" * 20 + "b7Kq2xZ9r4Tn6Wv1",
    "ADMIN_LOGIN_USER": "cl-ops-9f2c",
    "ADMIN_LOGIN_PASS": "Xq7#vT2m!Lp9wR4z",
    "ADMIN_LOGIN_MPIN": "918273",
    "ADMIN_ENROLL_CODE": "enroll-7f2b91cc",
    "SESSION_SECRET": "S" * 16 + "k3Mq8zR1t5Yb7Nv2",
    "DATABASE_URL": "postgresql://u:p@db:5432/cosmiclens",
    "RAZORPAY_KEY_ID": "rzp_live_abc123",
    "RAZORPAY_KEY_SECRET": "rzp_secret_abc123",
    "RAZORPAY_WEBHOOK_SECRET": "whsec_abc123",
    "REDIS_URL": "redis://127.0.0.1:6379/0",
}


_SECURITY_ENV_MARKERS = (
    "ADMIN_",
    "PAYMENT_",
    "RAZORPAY_",
    "PLAY_INTEGRITY",
    "APP_CHECK",
    "FIREBASE_",
    "LOVE_REALITY_",
    "ASK_",
    "ASTROVASTU_",
    "HEALTH_STATIC_",
    "ROOM_UPLOAD_",
    "CAREER_",
    "COUPLE_REPORT_",
    "NUMEROLOGY_REPORT_",
    "PALMISTRY_",
    "FACE_READING_",
    "BUSINESS_VASTU_",
    "BIRTH_TIME_RECTIFICATION_",
)


def _SECURITY_ENV_PREFIXES_MATCHED(key: str) -> tuple[str, ...]:
    """Return a non-empty tuple containing `key` when it is security-relevant."""
    if any(key.startswith(m) for m in _SECURITY_ENV_MARKERS):
        return (key,)
    if key in ("PROD", "FLASK_ENV", "DEV_PAYMENT_BYPASS", "REDIS_URL", "DATABASE_URL"):
        return (key,)
    return ()


class EnvSandbox(unittest.TestCase):
    def setUp(self) -> None:
        self._env = dict(os.environ)

    def tearDown(self) -> None:
        os.environ.clear()
        os.environ.update(self._env)

    def set_prod(self, **overrides: str) -> None:
        for key in list(os.environ):
            if key in PROD_ENV or key in _SECURITY_ENV_PREFIXES_MATCHED(key):
                os.environ.pop(key, None)
        os.environ.update(PROD_ENV)
        os.environ.update(overrides)


# ── Layer 8 / 12: production startup fails closed on bad configuration ────────


class ProductionStartupTests(EnvSandbox):
    def test_clean_production_config_passes(self) -> None:
        from startup_security import validate_production_config

        self.set_prod()
        self.assertEqual(validate_production_config(), [])

    def test_missing_mandatory_secret_blocks_boot(self) -> None:
        from startup_security import validate_production_config

        for var in (
            "ADMIN_SECRET",
            "SESSION_SECRET",
            "RAZORPAY_KEY_SECRET",
            "RAZORPAY_WEBHOOK_SECRET",
            "DATABASE_URL",
        ):
            with self.subTest(var=var):
                self.set_prod()
                os.environ.pop(var, None)
                errors = validate_production_config()
                self.assertTrue(any(var in e for e in errors), errors)

    def test_default_admin_credentials_blocked(self) -> None:
        from startup_security import validate_production_config

        self.set_prod(ADMIN_LOGIN_USER="admin", ADMIN_LOGIN_PASS="password1234")
        errors = validate_production_config()
        self.assertTrue(any("ADMIN_LOGIN_USER" in e for e in errors), errors)

    def test_short_admin_secret_blocked(self) -> None:
        from startup_security import validate_production_config

        self.set_prod(ADMIN_SECRET="tooshort")
        errors = validate_production_config()
        self.assertTrue(any("ADMIN_SECRET" in e for e in errors), errors)

    def test_low_entropy_secret_blocked(self) -> None:
        from startup_security import validate_production_config

        self.set_prod(SESSION_SECRET="a" * 40)
        errors = validate_production_config()
        self.assertTrue(any("SESSION_SECRET" in e for e in errors), errors)

    def test_payment_bypass_flag_blocks_boot(self) -> None:
        from startup_security import validate_production_config

        for flag in (
            "DEV_PAYMENT_BYPASS",
            "COUPLE_REPORT_PAYMENT_BYPASS",
            "FACE_READING_PAYMENT_BYPASS",
            "ASK_QUOTA_BYPASS",
            "LOVE_REALITY_PRO_FREE",
        ):
            with self.subTest(flag=flag):
                self.set_prod(**{flag: "1"})
                errors = validate_production_config()
                self.assertTrue(any(flag in e for e in errors), errors)

    def test_disabled_paywall_blocks_boot(self) -> None:
        from startup_security import validate_production_config

        self.set_prod(COUPLE_REPORT_PAYMENT_REQUIRED="0")
        errors = validate_production_config()
        self.assertTrue(
            any("COUPLE_REPORT_PAYMENT_REQUIRED" in e for e in errors), errors
        )

    def test_admin_no_auth_blocks_boot(self) -> None:
        from startup_security import validate_production_config

        self.set_prod(ADMIN_NO_AUTH="1")
        errors = validate_production_config()
        self.assertTrue(any("ADMIN_NO_AUTH" in e for e in errors), errors)

    def test_missing_shared_rate_limit_storage_blocks_boot(self) -> None:
        from startup_security import validate_production_config

        self.set_prod()
        os.environ.pop("REDIS_URL", None)
        errors = validate_production_config()
        self.assertTrue(any("REDIS_URL" in e for e in errors), errors)

    def test_sqlite_database_blocked_in_production(self) -> None:
        from startup_security import validate_production_config

        self.set_prod(DATABASE_URL="sqlite:///prod.db")
        errors = validate_production_config()
        self.assertTrue(any("SQLite" in e for e in errors), errors)


# ── Layer 5: admin bypasses are inert in production ───────────────────────────


class AdminBypassTests(EnvSandbox):
    def test_admin_no_auth_ignored_in_production(self) -> None:
        from admin_dashboard import admin_no_auth

        self.set_prod(ADMIN_NO_AUTH="1")
        self.assertFalse(admin_no_auth())

    def test_admin_relaxed_ignored_in_production(self) -> None:
        import admin_security

        self.set_prod(ADMIN_SECURITY_RELAXED="1", ADMIN_ALLOW_ALL_DEVICES="1")
        self.assertFalse(admin_security.admin_security_relaxed())
        self.assertFalse(admin_security.admin_allow_all_devices())

    def test_session_token_bound_to_device(self) -> None:
        import admin_security

        self.set_prod()
        device_a = "a" * 32
        device_b = "b" * 32
        token, _exp = admin_security.issue_session_token(device_a)
        self.assertTrue(admin_security.verify_session_token(token, device_a))
        self.assertFalse(admin_security.verify_session_token(token, device_b))

    def test_admin_secret_alone_is_not_a_session_token(self) -> None:
        import admin_security

        self.set_prod()
        secret = os.environ["ADMIN_SECRET"]
        self.assertFalse(admin_security.verify_session_token(secret, "c" * 32))

    def test_forged_session_signature_rejected(self) -> None:
        import admin_security

        self.set_prod()
        device = "d" * 32
        token, exp = admin_security.issue_session_token(device)
        forged = f"{device}:{exp}:{'0' * 64}"
        self.assertNotEqual(token, forged)
        self.assertFalse(admin_security.verify_session_token(forged, device))


# ── Layer 6: payments — server is the only authority ──────────────────────────


class PaymentAuthorityTests(EnvSandbox):
    def tearDown(self) -> None:
        super().tearDown()
        # Several tests reload payment_gateway with stripped env; restore the
        # module so later tests see the original configuration.
        import importlib
        import sys

        if "payment_gateway" in sys.modules:
            importlib.reload(sys.modules["payment_gateway"])

    def test_forged_webhook_signature_rejected(self) -> None:
        self.set_prod()
        import importlib

        import payment_gateway

        importlib.reload(payment_gateway)
        body = b'{"event":"order.paid"}'
        self.assertFalse(payment_gateway.verify_webhook_signature(body, "deadbeef"))
        self.assertFalse(payment_gateway.verify_webhook_signature(body, ""))

    def test_webhook_rejected_when_secret_missing(self) -> None:
        self.set_prod()
        os.environ.pop("RAZORPAY_WEBHOOK_SECRET", None)
        import importlib

        import payment_gateway

        importlib.reload(payment_gateway)
        self.assertFalse(payment_gateway.verify_webhook_signature(b"{}", "any"))

    def test_misconfigured_gateway_never_reports_paid(self) -> None:
        self.set_prod()
        os.environ.pop("RAZORPAY_KEY_ID", None)
        os.environ.pop("RAZORPAY_KEY_SECRET", None)
        import importlib

        import payment_gateway

        importlib.reload(payment_gateway)
        self.assertFalse(payment_gateway.configured())
        self.assertIsNone(payment_gateway.receipt_payment_details("CL1_X_1"))
        self.assertFalse(payment_gateway.is_receipt_paid("CL1_X_1"))

    def test_paywalls_cannot_be_switched_off_in_production(self) -> None:
        self.set_prod(
            DEV_PAYMENT_BYPASS="1",
            COUPLE_REPORT_PAYMENT_BYPASS="1",
            COUPLE_REPORT_PAYMENT_REQUIRED="0",
            NUMEROLOGY_REPORT_PAYMENT_REQUIRED="0",
            PALMISTRY_PAYMENT_REQUIRED="0",
            FACE_READING_PAYMENT_REQUIRED="0",
            BUSINESS_VASTU_PAYMENT_REQUIRED="0",
            BIRTH_TIME_RECTIFICATION_PAYMENT_REQUIRED="0",
            LOVE_REALITY_PRO_FREE="1",
        )
        import couple_report_billing as crb
        import face_reading_report_billing as frb
        import numerology_report_billing as nrb
        import palmistry_report_billing as prb

        self.assertTrue(crb.payment_required())
        self.assertTrue(nrb.payment_required())
        self.assertTrue(prb.payment_required())
        self.assertTrue(frb.payment_required())
        self.assertFalse(crb.payment_bypass())
        self.assertFalse(crb.love_reality_pro_free())

    def test_telegram_webhook_has_no_default_secret(self) -> None:
        from flask import Flask

        import love_reality_telegram_deliver as tg

        self.set_prod()
        os.environ.pop("TELEGRAM_WEBHOOK_SECRET", None)
        app = Flask(__name__)
        tg.register_telegram_deliver_routes(app)
        client = app.test_client()
        # The value that used to be hardcoded as a fallback.
        resp = client.post("/api/telegram/webhook/cosmic-lens-lr", json={})
        self.assertEqual(resp.status_code, 403)
        resp = client.post("/api/telegram/webhook/anything", json={})
        self.assertEqual(resp.status_code, 403)

    def test_telegram_webhook_secret_required_in_webhook_mode(self) -> None:
        from startup_security import validate_production_config

        self.set_prod(TELEGRAM_USE_POLLING="0")
        errors = validate_production_config()
        self.assertTrue(any("TELEGRAM_WEBHOOK_SECRET" in e for e in errors), errors)

    def test_dev_bypass_is_inert_in_production(self) -> None:
        from billing_security import (
            dev_payment_bypass_enabled,
            free_mode_enabled,
            payment_bypass_from_env,
            payment_required_flag,
        )

        self.set_prod(DEV_PAYMENT_BYPASS="1", COUPLE_REPORT_PAYMENT_BYPASS="1")
        self.assertFalse(dev_payment_bypass_enabled())
        self.assertFalse(payment_bypass_from_env("COUPLE_REPORT_PAYMENT_BYPASS"))
        self.assertFalse(free_mode_enabled("LOVE_REALITY_PRO_FREE"))
        self.assertTrue(payment_required_flag("COUPLE_REPORT_PAYMENT_REQUIRED"))


# ── Layer 10: attestation gate ────────────────────────────────────────────────


class AttestationTests(EnvSandbox):
    def test_disabled_by_default(self) -> None:
        os.environ.pop("PLAY_INTEGRITY_REQUIRED", None)
        os.environ.pop("APP_CHECK_REQUIRED", None)
        from app_attestation import attestation_enabled

        self.assertFalse(attestation_enabled())

    def test_sensitive_paths_are_protected(self) -> None:
        from app_attestation import path_is_protected

        for path in (
            "/api/payment/verify",
            "/api/stt",
            "/api/tts",
            "/api/face_reading/analyze",
            "/api/cosmic-intelligence-v3/media/x.png",
        ):
            with self.subTest(path=path):
                self.assertTrue(path_is_protected(path))

    def test_webhook_and_health_are_never_gated(self) -> None:
        from app_attestation import path_is_protected

        for path in ("/api/payment/webhook", "/api/healthz", "/api/admin/login"):
            with self.subTest(path=path):
                self.assertFalse(path_is_protected(path))

    def test_missing_token_rejected_when_enforced(self) -> None:
        from flask import Flask

        from app_attestation import check_attestation_request

        os.environ["PLAY_INTEGRITY_REQUIRED"] = "1"
        app = Flask(__name__)
        with app.test_request_context("/api/payment/verify", method="POST"):
            ok, err = check_attestation_request()
        self.assertFalse(ok)
        self.assertEqual(err[1], 403)

    def test_forged_token_rejected_without_credentials(self) -> None:
        from flask import Flask

        from app_attestation import check_attestation_request

        os.environ["PLAY_INTEGRITY_REQUIRED"] = "1"
        os.environ.pop("PLAY_INTEGRITY_SERVICE_ACCOUNT_JSON", None)
        os.environ.pop("FIREBASE_SERVICE_ACCOUNT_JSON", None)
        os.environ.pop("PLAY_INTEGRITY_CREDENTIALS_PATH", None)
        app = Flask(__name__)
        with app.test_request_context(
            "/api/payment/verify",
            method="POST",
            headers={"X-Play-Integrity": "forged.token.value"},
        ):
            ok, err = check_attestation_request()
        self.assertFalse(ok)
        self.assertEqual(err[1], 403)

    def test_app_check_rejects_token_without_project_number(self) -> None:
        from app_attestation import verify_app_check_token

        os.environ.pop("FIREBASE_PROJECT_NUMBER", None)
        os.environ.pop("APP_CHECK_PROJECT_NUMBER", None)
        self.assertFalse(verify_app_check_token("eyJhbGciOiJSUzI1NiJ9.e30.sig"))


# ── Layers 1-4, 9, 12: live route behaviour ───────────────────────────────────


class RouteAttackTests(unittest.TestCase):
    """Anonymous / cross-user attacks against the running app."""

    @classmethod
    def setUpClass(cls) -> None:
        os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
        os.environ.pop("PROD", None)
        from flask_app import app

        cls.app = app
        cls.client = app.test_client()

    def test_anonymous_blocked_on_compute_endpoints(self) -> None:
        cases = [
            ("/api/numerology/basic", {"name": "A", "day": 1, "month": 1, "year": 1990}),
            (
                "/api/numerology/advanced",
                {"name": "A", "day": 1, "month": 1, "year": 1990},
            ),
            ("/api/numerology/chaldean", {"name": "A"}),
            ("/api/numerology/karmic_lessons", {"name": "A"}),
            ("/api/numerology/name_correction", {"name": "A", "dob": "1990-01-01"}),
            ("/api/numerology/number_check", {"value": "9876543210"}),
            (
                "/api/numerology/compatibility",
                {"person1_dob": "1990-01-01", "person2_dob": "1991-01-01"},
            ),
            ("/api/daily_alerts", {"lagna_deg": 10.0, "nakshatra": "Ashwini"}),
            ("/api/prashna/ask", {"question": "kab hoga?"}),
            ("/api/prashna/number-ask", {"number": 42}),
            ("/api/stt", {}),
            ("/api/tts", {"text": "hello"}),
        ]
        for path, body in cases:
            with self.subTest(path=path):
                resp = self.client.post(path, json=body)
                self.assertIn(
                    resp.status_code,
                    (401, 403),
                    f"{path} allowed anonymous access: {resp.status_code}",
                )

    def test_header_body_user_id_mismatch_rejected(self) -> None:
        resp = self.client.post(
            "/api/prashna/ask",
            headers={"X-User-Id": "1", "X-API-Key": "k"},
            json={"question": "q", "user_id": 2},
        )
        self.assertEqual(resp.status_code, 403)

    def test_cross_user_face_session_rejected(self) -> None:
        victim = MagicMock()
        victim.id = 1
        with patch("api_auth.get_authed_user", return_value=victim):
            resp = self.client.get(
                "/api/face_reading/session/victim-session",
                headers={"X-User-Id": "1", "X-API-Key": "k"},
            )
        self.assertIn(resp.status_code, (401, 403, 404))
        self.assertNotEqual(resp.status_code, 200)

    def test_v3_media_requires_auth(self) -> None:
        resp = self.client.get("/api/cosmic-intelligence-v3/media/anything.png")
        self.assertIn(resp.status_code, (401, 403))

    def test_admin_routes_require_credentials(self) -> None:
        for path in ("/api/admin/users", "/api/admin/stats", "/api/admin/orders"):
            with self.subTest(path=path):
                resp = self.client.get(path)
                self.assertNotEqual(resp.status_code, 200)
                self.assertIn(resp.status_code, (401, 403, 404, 405))

    def test_security_headers_present(self) -> None:
        resp = self.client.get("/api/healthz")
        self.assertEqual(resp.headers.get("X-Content-Type-Options"), "nosniff")
        self.assertEqual(resp.headers.get("X-Frame-Options"), "DENY")
        self.assertEqual(resp.headers.get("Referrer-Policy"), "no-referrer")

    def test_cors_rejects_unknown_origin(self) -> None:
        resp = self.client.get(
            "/api/healthz", headers={"Origin": "https://evil.example.com"}
        )
        self.assertNotEqual(
            resp.headers.get("Access-Control-Allow-Origin"),
            "https://evil.example.com",
        )

    def test_rate_limit_key_isolates_users(self) -> None:
        import flask_app

        key_func = getattr(flask_app, "rate_limit_key", None)
        if key_func is None:
            self.skipTest("flask_limiter unavailable")
        with self.app.test_request_context("/api/tts", headers={"X-User-Id": "7"}):
            key_user = key_func()
        with self.app.test_request_context("/api/tts"):
            key_anon = key_func()
        self.assertIn("u:7", key_user)
        self.assertNotEqual(key_user, key_anon)


if __name__ == "__main__":
    unittest.main()
