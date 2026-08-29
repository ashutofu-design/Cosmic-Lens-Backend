"""Tests for shared API authentication helpers."""

import os
import unittest
from unittest.mock import patch

from flask import Flask


class ApiAuthTests(unittest.TestCase):
    def setUp(self) -> None:
        self.app = Flask(__name__)
        self._env = dict(os.environ)
        os.environ["DATABASE_URL"] = os.environ.get(
            "DATABASE_URL", "sqlite:///:memory:"
        )

    def tearDown(self) -> None:
        os.environ.clear()
        os.environ.update(self._env)

    def test_require_authed_user_rejects_missing_headers(self) -> None:
        from api_auth import require_authed_user

        with self.app.test_request_context("/"):
            user, err = require_authed_user()
        self.assertIsNone(user)
        self.assertIsNotNone(err)
        body, code = err
        self.assertEqual(code, 401)

    def test_auth_error_response_none_when_no_guard(self) -> None:
        from api_auth import auth_error_response

        with self.app.test_request_context("/"):
            self.assertIsNone(auth_error_response(None))

    def test_authed_user_rejects_body_header_mismatch(self) -> None:
        from api_auth import authed_user_from_request

        with self.app.test_request_context(
            "/",
            headers={"X-User-Id": "1", "X-API-Key": "secret"},
            json={"user_id": 2},
        ):
            user, err = authed_user_from_request({"user_id": 2})
        self.assertIsNone(user)
        self.assertIsNotNone(err)
        _body, code = err
        self.assertEqual(code, 403)

    def test_assert_route_user_id_rejects_url_mismatch(self) -> None:
        from api_auth import assert_route_user_id
        from unittest.mock import MagicMock

        mock_user = MagicMock()
        mock_user.id = 1
        with self.app.test_request_context(
            "/api/user/99/app-usage",
            headers={"X-User-Id": "1", "X-API-Key": "secret"},
        ):
            with patch("api_auth.require_authed_user", return_value=(mock_user, None)):
                user, err = assert_route_user_id(99)
        self.assertIsNone(user)
        self.assertIsNotNone(err)
        _body, code = err
        self.assertEqual(code, 403)


class ProtectedRouteSmokeTests(unittest.TestCase):
    """Smoke-test that key routes reject anonymous callers."""

    @classmethod
    def setUpClass(cls) -> None:
        os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
        os.environ.pop("PROD", None)
        from flask_app import app

        cls.app = app
        cls.client = app.test_client()

    def test_kp_kundli_requires_auth(self) -> None:
        resp = self.client.post(
            "/api/kp_kundli",
            json={
                "day": 1,
                "month": 1,
                "year": 2000,
                "hour": 10,
                "minute": 0,
                "ampm": "AM",
                "lat": 28.6,
                "lon": 77.2,
                "tz": 5.5,
            },
        )
        self.assertEqual(resp.status_code, 401)

    def test_dosh_analysis_requires_auth(self) -> None:
        resp = self.client.post(
            "/api/dosh-analysis",
            json={"planets": [{"name": "Sun", "house": 1}], "nakshatra": "Ashwini"},
        )
        self.assertEqual(resp.status_code, 401)

    def test_face_scan_requires_auth_when_blueprint_loaded(self) -> None:
        from flask_app import _OPTIONAL_SCAN_STATUS

        if not (_OPTIONAL_SCAN_STATUS.get("vedic.face_scan.api") or {}).get("ok"):
            self.skipTest("face_scan blueprint not loaded in this environment")
        resp = self.client.post("/api/face-scan")
        self.assertEqual(resp.status_code, 401)


class AuthorizationFixVerificationTests(unittest.TestCase):
    """Attack-oriented checks for the six verified authorization gaps."""

    @classmethod
    def setUpClass(cls) -> None:
        cls._env = dict(os.environ)
        os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
        os.environ.pop("PROD", None)
        os.environ.pop("FLASK_ENV", None)
        from flask_app import app

        cls.app = app
        cls.client = app.test_client()

    @classmethod
    def tearDownClass(cls) -> None:
        os.environ.clear()
        os.environ.update(cls._env)

    def test_stt_requires_auth(self) -> None:
        resp = self.client.post("/api/stt")
        self.assertEqual(resp.status_code, 401)

    def test_tts_requires_auth(self) -> None:
        resp = self.client.post("/api/tts", json={"text": "hello"})
        self.assertEqual(resp.status_code, 401)

    def test_v3_media_requires_auth(self) -> None:
        resp = self.client.get(
            "/api/cosmic-intelligence-v3/media/deadbeefdeadbeefdeadbeefdeadbeef.jpg"
        )
        self.assertEqual(resp.status_code, 401)

    def test_v3_media_forbidden_for_non_owner(self) -> None:
        from unittest.mock import MagicMock, patch

        from cosmic_intelligence_v3_sessions import _UPLOADS, user_owns_v3_media

        os.makedirs(_UPLOADS, exist_ok=True)
        fname = "abababababababababababababababab.jpg"
        path = os.path.join(_UPLOADS, fname)
        meta = os.path.join(_UPLOADS, f"{fname}.owner")
        mock_user = MagicMock()
        mock_user.id = 1
        try:
            with open(path, "wb") as fh:
                fh.write(b"fakejpeg")
            with open(meta, "w", encoding="utf-8") as fh:
                fh.write("999")
            self.assertFalse(user_owns_v3_media(1, fname))
            with patch("api_auth.get_authed_user", return_value=(mock_user, None)):
                resp = self.client.get(
                    f"/api/cosmic-intelligence-v3/media/{fname}",
                    headers={"X-User-Id": "1", "X-API-Key": "k1"},
                )
            self.assertEqual(resp.status_code, 403)
        finally:
            for p in (path, meta):
                try:
                    os.remove(p)
                except OSError:
                    pass

    def _mock_authed_user(self, user_id: int = 1):
        from unittest.mock import MagicMock

        mock_user = MagicMock()
        mock_user.id = user_id
        return mock_user

    def test_face_analyze_blocks_foreign_session_id(self) -> None:
        from unittest.mock import patch

        foreign = {
            "landmark_sets": {"front": object()},
            "owner_user_id": 999,
            "gender": "U",
        }
        mock_user = self._mock_authed_user(1)
        with patch("api_auth.get_authed_user", return_value=(mock_user, None)), patch(
            "vedic.face_reading.session_cache.get", return_value=foreign
        ):
            resp = self.client.post(
                "/api/face_reading/analyze",
                data={"session_id": "victim-session"},
                headers={"X-User-Id": "1", "X-API-Key": "k1"},
            )
        self.assertEqual(resp.status_code, 403)
        self.assertEqual(resp.get_json().get("error"), "forbidden")

    def test_face_report_status_blocks_foreign_session_id(self) -> None:
        from unittest.mock import patch

        foreign = {"owner_user_id": 999, "report_payload": {"person": {}}}
        mock_user = self._mock_authed_user(1)
        with patch("api_auth.get_authed_user", return_value=(mock_user, None)), patch(
            "vedic.face_reading.session_cache.get", return_value=foreign
        ):
            resp = self.client.get(
                "/api/face_reading/report/status",
                query_string={"session_id": "victim-session"},
                headers={"X-User-Id": "1", "X-API-Key": "k1"},
            )
        self.assertEqual(resp.status_code, 403)

    def test_face_report_events_blocks_foreign_session_id(self) -> None:
        from unittest.mock import patch

        foreign = {"owner_user_id": 999, "report_payload": {"person": {}}}
        mock_user = self._mock_authed_user(1)
        with patch("api_auth.get_authed_user", return_value=(mock_user, None)), patch(
            "vedic.face_reading.session_cache.get", return_value=foreign
        ):
            resp = self.client.get(
                "/api/face_reading/report/events",
                query_string={"session_id": "victim-session"},
                headers={"X-User-Id": "1", "X-API-Key": "k1"},
            )
        self.assertEqual(resp.status_code, 403)

    def test_face_reading_rejects_header_body_user_mismatch(self) -> None:
        resp = self.client.post(
            "/api/face_reading/extract",
            data={"user_id": "2"},
            headers={"X-User-Id": "1", "X-API-Key": "k1"},
        )
        self.assertEqual(resp.status_code, 403)

    def test_face_analyze_anonymous_rejected(self) -> None:
        resp = self.client.post(
            "/api/face_reading/analyze", data={"session_id": "victim-session"}
        )
        self.assertEqual(resp.status_code, 401)

    def test_face_session_get_anonymous_rejected(self) -> None:
        resp = self.client.get("/api/face_reading/session/victim-session")
        self.assertEqual(resp.status_code, 401)

    def test_face_extract_anonymous_rejected(self) -> None:
        resp = self.client.post(
            "/api/face_reading/extract", data={"session_id": "victim-session"}
        )
        self.assertEqual(resp.status_code, 401)

    def test_face_analyze_blocks_missing_owner_user_id(self) -> None:
        from unittest.mock import patch

        legacy = {
            "landmark_sets": {"front": object()},
            "gender": "U",
        }
        mock_user = self._mock_authed_user(1)
        with patch("api_auth.get_authed_user", return_value=(mock_user, None)), patch(
            "vedic.face_reading.session_cache.get", return_value=legacy
        ):
            resp = self.client.post(
                "/api/face_reading/analyze",
                data={"session_id": "legacy-session"},
                headers={"X-User-Id": "1", "X-API-Key": "k1"},
            )
        self.assertEqual(resp.status_code, 403)
        self.assertEqual(resp.get_json().get("error"), "forbidden")

    def test_face_analyze_blocks_foreign_session_without_front(self) -> None:
        from unittest.mock import patch

        foreign = {
            "landmark_sets": {"left": object(), "right": object()},
            "owner_user_id": 999,
        }
        mock_user = self._mock_authed_user(1)
        with patch("api_auth.get_authed_user", return_value=(mock_user, None)), patch(
            "vedic.face_reading.session_cache.get", return_value=foreign
        ):
            resp = self.client.post(
                "/api/face_reading/analyze",
                data={"session_id": "victim-session"},
                headers={"X-User-Id": "1", "X-API-Key": "k1"},
            )
        self.assertEqual(resp.status_code, 403)
        self.assertEqual(resp.get_json().get("error"), "forbidden")

    def test_face_session_get_blocks_foreign_and_missing_owner(self) -> None:
        from unittest.mock import patch

        mock_user = self._mock_authed_user(1)
        with patch("api_auth.get_authed_user", return_value=(mock_user, None)):
            with patch(
                "vedic.face_reading.session_cache.get",
                return_value={"owner_user_id": 999, "landmark_sets": {}},
            ):
                resp = self.client.get(
                    "/api/face_reading/session/victim-session",
                    headers={"X-User-Id": "1", "X-API-Key": "k1"},
                )
            self.assertEqual(resp.status_code, 403)
            with patch(
                "vedic.face_reading.session_cache.get",
                return_value={"landmark_sets": {"front": object()}},
            ):
                resp2 = self.client.get(
                    "/api/face_reading/session/legacy-session",
                    headers={"X-User-Id": "1", "X-API-Key": "k1"},
                )
            self.assertEqual(resp2.status_code, 403)

    def test_face_extract_blocks_overwrite_of_foreign_session(self) -> None:
        from unittest.mock import patch

        mock_user = self._mock_authed_user(1)
        with patch("api_auth.get_authed_user", return_value=(mock_user, None)), patch(
            "vedic.face_reading.session_cache.get",
            return_value={"owner_user_id": 999, "landmark_sets": {"front": object()}},
        ), patch("vedic.face_reading.session_cache.put") as put:
            resp = self.client.post(
                "/api/face_reading/extract",
                data={"session_id": "victim-session"},
                headers={"X-User-Id": "1", "X-API-Key": "k1"},
            )
        self.assertEqual(resp.status_code, 403)
        put.assert_not_called()

    def test_face_extract_blocks_overwrite_of_legacy_session(self) -> None:
        from unittest.mock import patch

        mock_user = self._mock_authed_user(1)
        with patch("api_auth.get_authed_user", return_value=(mock_user, None)), patch(
            "vedic.face_reading.session_cache.get",
            return_value={"landmark_sets": {"front": object()}},
        ), patch("vedic.face_reading.session_cache.put") as put:
            resp = self.client.post(
                "/api/face_reading/extract",
                data={"session_id": "legacy-session"},
                headers={"X-User-Id": "1", "X-API-Key": "k1"},
            )
        self.assertEqual(resp.status_code, 403)
        put.assert_not_called()

    def test_face_report_status_blocks_missing_owner(self) -> None:
        from unittest.mock import patch

        mock_user = self._mock_authed_user(1)
        with patch("api_auth.get_authed_user", return_value=(mock_user, None)), patch(
            "vedic.face_reading.session_cache.get",
            return_value={"report_payload": {"person": {}}},
        ):
            resp = self.client.get(
                "/api/face_reading/report/status",
                query_string={"session_id": "legacy-session"},
                headers={"X-User-Id": "1", "X-API-Key": "k1"},
            )
        self.assertEqual(resp.status_code, 403)

    def test_face_ws_anonymous_blocked_before_subscribe(self) -> None:
        from types import SimpleNamespace
        from unittest.mock import patch

        from vedic.face_reading.flask_pdf_handlers import prepare_face_report_ws

        ws = SimpleNamespace(environ={"QUERY_STRING": "session_id=victim-session"})
        with self.app.test_request_context(
            "/api/face_reading/report/ws?session_id=victim-session"
        ):
            prepared, err = prepare_face_report_ws(ws)
        self.assertIsNone(prepared)
        self.assertIsNotNone(err)
        self.assertEqual(err.get("status"), 401)
        self.assertIn(err.get("error"), ("auth_required", "Unauthorized — invalid API key"))

    def test_face_ws_foreign_session_blocked_before_subscribe(self) -> None:
        from types import SimpleNamespace
        from unittest.mock import patch

        from vedic.face_reading.flask_pdf_handlers import prepare_face_report_ws

        mock_user = self._mock_authed_user(1)
        ws = SimpleNamespace(environ={"QUERY_STRING": "session_id=victim-session"})
        with self.app.test_request_context(
            "/api/face_reading/report/ws?session_id=victim-session",
            headers={"X-User-Id": "1", "X-API-Key": "k1"},
        ), patch("api_auth.get_authed_user", return_value=(mock_user, None)), patch(
            "vedic.face_reading.session_cache.get",
            return_value={"owner_user_id": 999, "report_payload": {}},
        ), patch(
            "vedic.face_reading.progress_events.subscribe"
        ) as sub:
            prepared, err = prepare_face_report_ws(ws)
        self.assertIsNone(prepared)
        self.assertEqual(err.get("status"), 403)
        self.assertEqual(err.get("error"), "forbidden")
        sub.assert_not_called()

    def test_face_ws_missing_owner_blocked_before_subscribe(self) -> None:
        from types import SimpleNamespace
        from unittest.mock import patch

        from vedic.face_reading.flask_pdf_handlers import prepare_face_report_ws

        mock_user = self._mock_authed_user(1)
        ws = SimpleNamespace(environ={"QUERY_STRING": "session_id=legacy-session"})
        with self.app.test_request_context(
            "/api/face_reading/report/ws?session_id=legacy-session",
            headers={"X-User-Id": "1", "X-API-Key": "k1"},
        ), patch("api_auth.get_authed_user", return_value=(mock_user, None)), patch(
            "vedic.face_reading.session_cache.get",
            return_value={"report_payload": {}},
        ):
            prepared, err = prepare_face_report_ws(ws)
        self.assertIsNone(prepared)
        self.assertEqual(err.get("status"), 403)

    def test_face_session_owner_error_fail_closed(self) -> None:
        from vedic.face_reading.flask_pdf_handlers import face_session_owner_error

        mock_user = self._mock_authed_user(1)
        with self.app.app_context():
            missing = face_session_owner_error({"landmark_sets": {}}, mock_user)
            self.assertIsNotNone(missing)
            self.assertEqual(missing[1], 403)
            mismatch = face_session_owner_error({"owner_user_id": 999}, mock_user)
            self.assertEqual(mismatch[1], 403)
            ok = face_session_owner_error({"owner_user_id": 1}, mock_user)
            self.assertIsNone(ok)

    def test_admin_no_auth_ignored_in_production(self) -> None:
        os.environ["PROD"] = "1"
        os.environ["ADMIN_NO_AUTH"] = "1"
        try:
            from admin_dashboard import admin_no_auth
            from flask_app import require_admin

            self.assertFalse(admin_no_auth())
            with self.app.test_request_context("/api/admin/dashboard"):
                err = require_admin()
            self.assertIsNotNone(err)
        finally:
            os.environ.pop("PROD", None)
            os.environ.pop("ADMIN_NO_AUTH", None)


if __name__ == "__main__":
    unittest.main()
