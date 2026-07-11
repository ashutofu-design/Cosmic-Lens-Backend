"""Tests for shared Kaal Pipeline shell (all timing domains)."""
from __future__ import annotations

from event_timing._shared.kaal_pipeline import (
    expand_to_kaal_pipeline,
    human_month_year,
    is_kaal_pipeline_domain,
    parse_iso_month_year,
)
from event_timing._shared.step_audit import attach_timing_pipeline_audit, build_domain_timing_engine_trace


def test_kaal_domains_cover_sixteen():
    from event_timing._shared.kaal_pipeline import KAAL_PIPELINE_DOMAINS

    assert is_kaal_pipeline_domain("marriage")
    assert is_kaal_pipeline_domain("travel")
    assert len(KAAL_PIPELINE_DOMAINS) == 16


def test_parse_iso_month_year():
    assert parse_iso_month_year("2036-10-15") == ("October", 2036)
    assert human_month_year("2036-10") == "October 2036"


def test_expand_to_kaal_skips_step0a_for_travel():
    payload = {"verdict": "FAVOURABLE", "bucket": "general", "domain": "travel"}
    out = expand_to_kaal_pipeline(payload, "travel")
    assert "step0a" not in (out.get("step_audit") or {})


def test_generic_kaal_omits_kp_and_transit_verify():
    payload = {
        "verdict": "LOVE_WINDOW_SENSITIVE",
        "band": "MEDIUM",
        "bucket": "timing",
        "domain": "love",
        "current_window": {
            "md": "Saturn",
            "ad": "Saturn",
            "start_iso": "2026-06-27",
            "end_iso": "2026-12-18",
        },
        "factors": ["STEP6 double_transit=STRONG"],
        "double_transit": {"verdict": "STRONG", "active": True},
    }
    out = expand_to_kaal_pipeline(attach_timing_pipeline_audit(payload, "love"), "love")
    sa = out.get("step_audit") or {}
    assert "step0a" not in sa
    assert "step3" in sa
    assert "step7" not in sa
    assert "step8" in sa
    assert "step3" in (out.get("step_order") or [])
    assert "step7" not in (out.get("step_order") or [])


def test_expand_to_kaal_adds_step8_month_year():
    payload = {
        "verdict": "FAVOURABLE",
        "band": "MEDIUM",
        "bucket": "general",
        "domain": "travel",
        "current_window": {
            "md": "Jupiter",
            "ad": "Mercury",
            "pd": "Venus",
            "start_iso": "2026-10-01",
            "end_iso": "2027-03-01",
        },
        "factors": ["STEP1 top=['Jupiter']"],
    }
    out = expand_to_kaal_pipeline(attach_timing_pipeline_audit(payload, "travel"), "travel")
    s8 = out["step_audit"]["step8"]
    assert s8.get("event_month_year") == "October 2026"
    assert "marriage_month_year" not in s8
    assert s8.get("event_year") == 2026
    assert s8.get("event_month") == "October"
    assert out.get("pipeline_format") == "kaal_v1"


def test_build_domain_timing_engine_trace_kaal_primary():
    payload = {
        "verdict": "PROMISED",
        "band": "STRONG",
        "bucket": "general",
        "current_window": {
            "md": "Jupiter",
            "ad": "Mercury",
            "start_iso": "2027-05-01",
            "end_iso": "2028-01-01",
        },
        "factors": ["STEP1 top=['Jupiter']"],
    }
    trace = build_domain_timing_engine_trace(payload, "health")
    assert trace.get("pipeline_version") == "kaal_v1"
    assert "step8" in (trace.get("step_audit") or {})
    assert trace.get("primary_window")
