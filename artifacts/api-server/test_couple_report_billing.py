"""Couple report billing — params hash + catalog."""
from __future__ import annotations

import os

import couple_report_billing as billing


def test_catalog_milan_and_love():
    m = billing.catalog_for(billing.PRODUCT_MILAN)
    l = billing.catalog_for(billing.PRODUCT_LOVE)
    assert m and m["amount_inr"] > 0
    assert l and l["amount_inr"] > 0


def test_params_hash_stable_for_same_birth():
    p1 = {"name": "A", "day": 1, "month": 1, "year": 1990, "hour": 10, "minute": 0, "lat": 28.6, "lon": 77.2, "tz": 5.5}
    p2 = {"name": "B", "day": 5, "month": 6, "year": 1992, "hour": 14, "minute": 30, "lat": 19.0, "lon": 72.8, "tz": 5.5}
    cp1 = billing.cache_params_from_birth("hi", p1, p2)
    cp2 = billing.cache_params_from_birth("hi", dict(p1), dict(p2))
    assert billing.params_hash(cp1) == billing.params_hash(cp2)


def test_params_hash_changes_with_lang():
    p1 = {"day": 1, "month": 1, "year": 1990, "lat": 28.6, "lon": 77.2}
    p2 = {"day": 5, "month": 6, "year": 1992, "lat": 19.0, "lon": 72.8}
    h_en = billing.params_hash(billing.cache_params_from_birth("en", p1, p2))
    h_hi = billing.params_hash(billing.cache_params_from_birth("hi", p1, p2))
    assert h_en != h_hi


def test_payment_bypass_entitles(monkeypatch):
    monkeypatch.setenv("COUPLE_REPORT_PAYMENT_BYPASS", "1")
    monkeypatch.delenv("COUPLE_REPORT_PAYMENT_REQUIRED", raising=False)
    assert billing.payment_bypass()
    cp = billing.cache_params_from_birth("en", {"day": 1, "month": 1, "year": 1990, "lat": 1, "lon": 1}, {"day": 2, "month": 2, "year": 1991, "lat": 2, "lon": 2})
    access = billing.check_access(99, billing.PRODUCT_LOVE, cp)
    assert access["entitled"] is True
    assert access["payment_required"] is False
