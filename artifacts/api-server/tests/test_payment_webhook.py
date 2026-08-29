"""Razorpay webhook signature tests."""

import unittest


class PaymentWebhookTests(unittest.TestCase):
    def test_missing_webhook_secret_rejects(self) -> None:
        import payment_gateway as pg

        original = pg.RAZORPAY_WEBHOOK_SECRET
        try:
            pg.RAZORPAY_WEBHOOK_SECRET = ""
            self.assertFalse(pg.verify_webhook_signature(b"{}", "deadbeef"))
        finally:
            pg.RAZORPAY_WEBHOOK_SECRET = original


if __name__ == "__main__":
    unittest.main()
