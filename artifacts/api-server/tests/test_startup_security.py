"""Production startup security validation tests."""

import os
import unittest


class StartupSecurityTests(unittest.TestCase):
    def setUp(self) -> None:
        self._env = dict(os.environ)
        os.environ.pop("PROD", None)
        os.environ.pop("FLASK_ENV", None)

    def tearDown(self) -> None:
        os.environ.clear()
        os.environ.update(self._env)

    def test_non_production_skips_validation(self) -> None:
        from startup_security import validate_production_config

        self.assertEqual(validate_production_config(), [])

    def test_production_requires_razorpay_webhook_secret(self) -> None:
        os.environ["PROD"] = "1"
        os.environ["ADMIN_SECRET"] = "x" * 32
        os.environ["ADMIN_LOGIN_USER"] = "admin@test"
        os.environ["ADMIN_LOGIN_PASS"] = "long-enough"
        os.environ["ADMIN_LOGIN_MPIN"] = "1234"
        os.environ["SESSION_SECRET"] = "y" * 32
        os.environ["DATABASE_URL"] = "postgresql://localhost/test"
        os.environ["RAZORPAY_KEY_ID"] = "rzp_test"
        os.environ["RAZORPAY_KEY_SECRET"] = "secret"
        os.environ["ADMIN_ENROLL_CODE"] = "enroll"
        os.environ.pop("RAZORPAY_WEBHOOK_SECRET", None)

        from startup_security import validate_production_config

        errors = validate_production_config()
        self.assertTrue(any("RAZORPAY_WEBHOOK_SECRET" in e for e in errors))


    def test_production_blocks_dev_grant_and_quota_bypass(self) -> None:
        os.environ["PROD"] = "1"
        os.environ["ADMIN_SECRET"] = "x" * 32
        os.environ["ADMIN_LOGIN_USER"] = "admin@test"
        os.environ["ADMIN_LOGIN_PASS"] = "long-enough"
        os.environ["ADMIN_LOGIN_MPIN"] = "1234"
        os.environ["SESSION_SECRET"] = "y" * 32
        os.environ["DATABASE_URL"] = "postgresql://localhost/test"
        os.environ["RAZORPAY_KEY_ID"] = "rzp_test"
        os.environ["RAZORPAY_KEY_SECRET"] = "secret"
        os.environ["RAZORPAY_WEBHOOK_SECRET"] = "whsec_test"
        os.environ["ADMIN_ENROLL_CODE"] = "enroll"
        os.environ["ASTROVASTU_DEV_GRANT_ENABLED"] = "1"

        from startup_security import validate_production_config

        errors = validate_production_config()
        self.assertTrue(any("ASTROVASTU_DEV_GRANT_ENABLED" in e for e in errors))

        os.environ.pop("ASTROVASTU_DEV_GRANT_ENABLED", None)
        os.environ["ASK_QUOTA_BYPASS"] = "1"
        errors = validate_production_config()
        self.assertTrue(any("ASK_QUOTA_BYPASS" in e for e in errors))

        os.environ.pop("ASK_QUOTA_BYPASS", None)
        os.environ["HEALTH_STATIC_BYPASS"] = "1"
        errors = validate_production_config()
        self.assertTrue(any("HEALTH_STATIC_BYPASS" in e for e in errors))


if __name__ == "__main__":
    unittest.main()
