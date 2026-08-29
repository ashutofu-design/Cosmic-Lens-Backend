"""Webhook amount verification helpers."""
from __future__ import annotations

import payment_gateway as pg


def test_webhook_captured_amount_paise_from_payment_entity():
    payload = {
        "payload": {
            "payment": {
                "entity": {
                    "status": "captured",
                    "amount": 49900,
                }
            }
        }
    }
    assert pg.webhook_captured_amount_paise(payload) == 49900


def test_webhook_payment_satisfies_rejects_underpayment(monkeypatch):
    payload = {
        "payload": {
            "payment": {
                "entity": {
                    "status": "captured",
                    "amount": 10000,
                }
            }
        }
    }
    assert pg.webhook_payment_satisfies(payload, "order_1", 499) is False


def test_webhook_payment_satisfies_accepts_matching_amount():
    payload = {
        "payload": {
            "payment": {
                "entity": {
                    "status": "captured",
                    "amount": 49900,
                }
            }
        }
    }
    assert pg.webhook_payment_satisfies(payload, "order_1", 499) is True
