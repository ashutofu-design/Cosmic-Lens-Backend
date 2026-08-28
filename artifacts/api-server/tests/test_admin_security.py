import os
import tempfile
import unittest


class AdminSecurityTests(unittest.TestCase):
    def setUp(self) -> None:
        self._env = dict(os.environ)
        os.environ["ADMIN_SECRET"] = "test-admin-secret-key-32chars!!"
        os.environ["ADMIN_ENROLL_CODE"] = "enroll-me-now"
        os.environ["ADMIN_ALLOW_ALL_DEVICES"] = "0"
        os.environ.pop("ADMIN_SECURITY_RELAXED", None)
        fd, path = tempfile.mkstemp(suffix=".json")
        os.close(fd)
        self.store_path = path
        os.environ["ADMIN_DEVICE_STORE"] = path

    def tearDown(self) -> None:
        os.environ.clear()
        os.environ.update(self._env)
        try:
            os.remove(self.store_path)
        except OSError:
            pass

    def test_unlock_sequence_and_gate(self) -> None:
        from admin_security import (
            admin_security_enabled,
            issue_gate_token,
            validate_unlock_steps,
            verify_gate_token,
        )

        self.assertTrue(admin_security_enabled())
        self.assertTrue(
            validate_unlock_steps(["locate", "locate", "locate", "for", "for", "for"])
        )
        self.assertFalse(validate_unlock_steps(["locate", "for"]))
        device = "a" * 32
        token, exp = issue_gate_token(device)
        self.assertTrue(verify_gate_token(token, device))
        self.assertFalse(verify_gate_token(token, "b" * 32))
        self.assertGreater(exp, 0)

    def test_device_enroll_and_session(self) -> None:
        from admin_security import (
            is_device_allowed,
            issue_session_token,
            register_device,
            verify_session_token,
        )

        device = "c" * 32
        self.assertFalse(is_device_allowed(device))
        ok, reason = register_device(device, enroll_code="wrong")
        self.assertFalse(ok)
        self.assertEqual(reason, "enroll_code_required")
        ok, reason = register_device(device, enroll_code="enroll-me-now", label="laptop")
        self.assertTrue(ok)
        self.assertEqual(reason, "registered")
        self.assertTrue(is_device_allowed(device))
        token, _ = issue_session_token(device)
        self.assertTrue(verify_session_token(token, device))
        self.assertFalse(verify_session_token(token, "d" * 32))

    def test_allow_all_devices(self) -> None:
        os.environ["ADMIN_ALLOW_ALL_DEVICES"] = "1"
        from admin_security import is_device_allowed, register_device

        device = "e" * 32
        self.assertTrue(is_device_allowed(device))
        ok, reason = register_device(device, label="phone")
        self.assertTrue(ok)
        self.assertEqual(reason, "auto_allowed")


if __name__ == "__main__":
    unittest.main()
