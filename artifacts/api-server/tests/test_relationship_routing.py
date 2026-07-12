"""Tests for Domain → DNA → Engine relationship routing."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from relationship_routing import (
    RELATIONSHIP_DOMAIN,
    SUBDOMAIN_MARRIAGE,
    SUBDOMAIN_PARTNER,
    SUBDOMAIN_ROMANCE,
    classify_relationship_subdomain,
    resolve_relationship_route,
    resolve_relationship_timing_domain,
)


def _item(**kwargs):
    base = {
        "domain": "love",
        "bucket": "",
        "timing": False,
        "subject": "self",
        "target": "self",
        "intent": "",
        "confidence": 0.95,
        "bucket_match_confidence": "high",
    }
    base.update(kwargs)
    return base


@pytest.mark.parametrize(
    "question,item,expected_subdomain,expected_timing_engine,expected_archetype",
    [
        (
            "Meri shaadi kab hogi",
            _item(domain="marriage", bucket="marriage_timing", timing=True),
            SUBDOMAIN_MARRIAGE,
            "marriage_timing_m17",
            "general_mr",
        ),
        (
            "Mera bf loyal hai",
            _item(domain="love", bucket="trust_loyalty", subject="boyfriend"),
            SUBDOMAIN_PARTNER,
            None,
            "loyalty_trust",
        ),
        (
            "Mera ex wapas aayega",
            _item(domain="love", bucket="reconciliation_ex", subject="ex"),
            SUBDOMAIN_PARTNER,
            None,
            "patchup",
        ),
        (
            "Love marriage hogi",
            _item(domain="love", bucket="marriage_potential", timing=False),
            SUBDOMAIN_MARRIAGE,
            None,
            "love_vs_arranged",
        ),
    ],
)
def test_resolve_relationship_route_examples(
    question,
    item,
    expected_subdomain,
    expected_timing_engine,
    expected_archetype,
):
    route = resolve_relationship_route(question, dna_item=item)
    assert route is not None
    assert route.domain == RELATIONSHIP_DOMAIN
    assert route.subdomain == expected_subdomain
    assert route.timing_engine == expected_timing_engine
    assert route.archetype == expected_archetype


def test_timing_domain_dna_first_not_love_keyword_priority():
    """Shaadi timing uses marriage M17 even without love keywords."""
    item = _item(domain="marriage", bucket="marriage_timing", timing=True)
    dom, bkt = resolve_relationship_timing_domain(
        "Meri shaadi kab hogi",
        {"question_dna": {"questions": [item]}},
    )
    assert dom == "marriage"
    assert bkt == "marriage_timing"


def test_love_marriage_static_not_timing_engine():
    item = _item(domain="love", bucket="marriage_potential", timing=False)
    route = resolve_relationship_route("Love marriage hogi ya arranged", dna_item=item)
    assert route is not None
    assert route.is_timing is False
    assert route.archetype == "love_vs_arranged"
    assert route.subdomain == SUBDOMAIN_MARRIAGE


def test_romance_subdomain_default():
    item = _item(domain="love", bucket="dating_courtship", subject="crush")
    assert classify_relationship_subdomain(item, "Crush ko propose karu?") == SUBDOMAIN_ROMANCE
