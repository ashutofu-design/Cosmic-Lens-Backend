import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ask_llm_context_debug import (
    build_admin_llm_context,
    derive_answer_path,
    parse_llm_context_from_db,
    serialize_llm_context_for_db,
)


class AskLlmContextDebugTests(unittest.TestCase):
    def test_roundtrip_serialize(self):
        ctx = build_admin_llm_context(
            question="mera partner kaisa hoga",
            checks={"slice_type": "marriage_relationship"},
            chart_text="=== MARRIAGE SLICE ===",
            system_prompt="You are Cosmo",
        )
        raw = serialize_llm_context_for_db(ctx)
        self.assertIsNotNone(raw)
        parsed = parse_llm_context_from_db(raw)
        self.assertEqual(parsed["checks"]["slice_type"], "marriage_relationship")
        self.assertIn("MARRIAGE SLICE", parsed["chart_text"])

    def test_answer_path_engine_then_llm(self):
        ctx = build_admin_llm_context(
            question="love marriage ya arrange",
            llm_called=True,
            checks={"slice_type": "mr_engine_v1", "mr_engine": "v1", "is_mr_static": True},
            slice_meta={
                "slice": "mr_engine_v1",
                "verdict": "Arrange side stronger",
                "evidence": ["Arrange indicator: Manglik dosha"],
                "evidence_positive": ["Jupiter in 5th — green flag"],
                "evidence_negative": ["Saturn on 7th — delay"],
            },
            model="gpt-4.1-mini",
        )
        self.assertEqual(ctx["answer_path"], "engine_then_llm")
        self.assertEqual(ctx["engine_facts"]["verdict"], "Arrange side stronger")
        self.assertEqual(len(ctx["engine_facts"]["evidence"]), 1)
        self.assertEqual(len(ctx["engine_facts"]["evidence_positive"]), 1)
        self.assertEqual(len(ctx["engine_facts"]["evidence_negative"]), 1)

    def test_answer_path_engine_only(self):
        code, label = derive_answer_path(
            llm_called=False,
            skip_reason="mr_engine_template",
            checks={"skip_llm": True},
            slice_meta={"slice": "mr_engine_v1", "verdict": "Manglik: yes"},
        )
        self.assertEqual(code, "engine_only")
        self.assertIn("no LLM", label)

    def test_answer_path_career_timing_engine_then_llm(self):
        code, label = derive_answer_path(
            llm_called=True,
            checks={"is_career_engine": True, "slice_type": "timing_full_chart"},
            slice_meta={
                "slice": "career_timing_v1",
                "verdict": "yellow_wait",
                "evidence": ["Jupiter MD supports stability"],
            },
        )
        self.assertEqual(code, "engine_then_llm")
        self.assertIn("Engine", label)

    def test_career_timing_slice_meta_builder(self):
        from ask_hard_guards import build_career_timing_slice_meta

        meta = build_career_timing_slice_meta({
            "bucket": "job_change",
            "verdict": "red_avoid",
            "score": 42,
            "confidence": 61,
            "strategy": "Wait 4-6 months",
            "triggers": {
                "T1_vimshottari": {
                    "why": [
                        "Current MD = Jupiter (career-significator) (+5)",
                        "Current AD lord Saturn debilitated — fragile window (-1)",
                    ],
                },
            },
            "reasons": [
                "10L Mercury is neutral-sign (+0)",
                "Sun is debilitated (-8)",
            ],
            "timing_window": {
                "current": {"lords": "Jupiter/Saturn/Mercury", "start": "2024-01", "end": "2026-06"},
                "next_career": {"ad": "Venus", "start": "2026-07", "end": "2027-01"},
            },
        })
        self.assertEqual(meta["slice"], "career_timing_v1")
        self.assertLessEqual(len(meta["evidence"]), 8)
        self.assertIn("Current MD", meta["evidence"][0])
        self.assertNotIn("10L Mercury", meta["evidence"][0])
        self.assertEqual(meta["dasha_trace"]["current_lords"], "Jupiter/Saturn/Mercury")

    def test_answer_path_direct_llm(self):
        code, _ = derive_answer_path(
            llm_called=True,
            checks={"slice_type": "compact_chart"},
            slice_meta={},
        )
        self.assertEqual(code, "direct_llm")

    def test_marriage_engine_trace(self):
        from ask_llm_context_debug import build_marriage_engine_trace

        trace = build_marriage_engine_trace(
            {
                "primary_window": "June – November 2029",
                "step_audit": {
                    "step0": {"name": "Early/Late", "status": "DONE", "user_age": 28},
                    "step8": {"name": "Final gate", "status": "DONE", "verdict": "FAVORABLE"},
                },
                "timing_audit": {
                    "status": "PASS",
                    "expected_reply": "June – November 2029",
                    "checks": [{"name": "answer_lock", "ok": True, "detail": "ok"}],
                },
                "factors": ["BCP_ANCHOR age 30"],
            }
        )
        self.assertIsNotNone(trace)
        self.assertEqual(trace["engine"], "marriage_timing_m17")
        self.assertEqual(trace["primary_window"], "June – November 2029")
        self.assertIn("step0", trace["step_audit"])
        self.assertEqual(trace["timing_audit"]["status"], "PASS")

    def test_normalize_legacy_transit_months_on_read(self):
        import json

        legacy = {
            "blocks": {
                "engine_trace": {
                    "step_audit": {
                        "step7": {
                            "name": "Transit verification",
                            "transit_confirmed": True,
                            "detail": (
                                "2029-06-30 Sat→7th house orb 1.97° + "
                                "2029-09-07 Jup→7th house"
                            ),
                            "samples": [],
                        }
                    },
                    "timing_audit": {
                        "transit": {
                            "detail": "2029-06-30 Sat→7th house orb 1.97°",
                            "samples": [],
                        }
                    },
                }
            }
        }
        parsed = parse_llm_context_from_db(json.dumps(legacy))
        s7 = parsed["blocks"]["engine_trace"]["step_audit"]["step7"]
        self.assertIn("Jun 2029", s7["detail"])
        self.assertNotIn("2029-06-30", s7["detail"])
        self.assertNotIn("7th", s7["detail"])
        tr = parsed["blocks"]["engine_trace"]["timing_audit"]["transit"]
        self.assertIn("Jun 2029", tr["detail"])


    def test_normalize_month_only_detail_gets_rashi(self):
        import json
        from event_timing.marriage import marriage_engine_v2 as me

        def _fake_rashis(iso):
            if "2029-06" in iso:
                return "Singh", "Kark"
            if "2029-09" in iso:
                return "Tula", "Makar"
            return None, None

        orig = me._transit_rashis_at_iso
        me._transit_rashis_at_iso = _fake_rashis
        try:
            legacy = {
                "blocks": {
                    "engine_trace": {
                        "step_audit": {
                            "step7": {
                                "transit_confirmed": True,
                                "detail": "Jun 2029 · Sep 2029",
                                "months": ["Jun 2029", "Sep 2029"],
                            }
                        }
                    }
                }
            }
            parsed = parse_llm_context_from_db(json.dumps(legacy))
            s7 = parsed["blocks"]["engine_trace"]["step_audit"]["step7"]
            self.assertIn("Guru Singh", s7["detail"])
            self.assertIn("Shani Kark", s7["detail"])
            self.assertIn("Guru Tula", s7["detail"])
            bm = s7.get("by_month") or []
            self.assertTrue(any(r.get("jupiter_rashi") == "Singh" for r in bm))
        finally:
            me._transit_rashis_at_iso = orig


if __name__ == "__main__":
    unittest.main()
