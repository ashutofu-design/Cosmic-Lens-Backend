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
    def test_bcp_linkage_evidence_parse(self):
        from ask_llm_context_debug import (
            _bcp_linkage_evidence_lines,
            _marriage_bcp_linkage_snapshot,
            _parse_bcp_linkage_from_evidence,
        )

        linkage = {
            "d1_seventh_lord": "Mercury",
            "d1_7l_placement_house": 12,
            "d1_7l_aspect_houses": [4, 7],
            "d9_seventh_lord": "Venus",
            "d9_7l_placement_house": 5,
            "d9_7l_aspect_houses": [4],
            "shared_7l_linkage_houses": [4],
        }
        lines = _bcp_linkage_evidence_lines(linkage)
        assert any("BCP_LINKAGE D1" in x for x in lines)
        parsed = _parse_bcp_linkage_from_evidence(lines)
        assert parsed["d1_7l_placement_house"] == 12
        assert parsed["d1_7l_aspect_houses"] == [4, 7]
        assert parsed["shared_7l_linkage_houses"] == [4]


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
        self.assertEqual(parsed.get("chart_text"), "")
        self.assertGreaterEqual((parsed.get("sizes") or {}).get("chart_text_chars", 0), 10)

    def test_compact_serialize_preserves_engine_trace(self):
        from ask_llm_context_debug import build_marriage_timing_slice_meta

        huge_chart = "X" * 90_000
        trace = {
            "engine": "marriage_timing_m17",
            "primary_window": "March – April 2027",
            "step_audit": {"step0": {"name": "Early/Late", "status": "DONE"}},
            "timing_audit": {"status": "PASS"},
        }
        ctx = build_admin_llm_context(
            question="mera shaadi kab hoga",
            is_timing=True,
            llm_called=False,
            checks={"slice_type": "timing_marriage_engine", "is_marriage_engine": True},
            chart_text=huge_chart,
            slice_meta=build_marriage_timing_slice_meta(
                {
                    "primary_window": "March – April 2027",
                    "verdict": "PROMISED",
                    "bucket": "general_mr",
                    "step_audit": trace["step_audit"],
                    "timing_audit": trace["timing_audit"],
                }
            ),
            blocks={"engine_trace": trace},
        )
        raw = serialize_llm_context_for_db(ctx)
        self.assertIsNotNone(raw)
        self.assertLessEqual(len(raw), 80_000)
        parsed = parse_llm_context_from_db(raw)
        self.assertIsNotNone(parsed)
        blocks = parsed.get("blocks") or {}
        et = blocks.get("engine_trace") or {}
        self.assertEqual(et.get("primary_window"), "March – April 2027")
        self.assertIn("step0", et.get("step_audit") or {})

    def test_hydrate_engine_trace_from_slice_meta_on_load(self):
        import json

        saved = {
            "question": "mera shaadi kab hoga",
            "is_timing": True,
            "question_type": "TIMING",
            "checks": {"slice_type": "timing_marriage_engine"},
            "slice_meta": {
                "slice": "marriage_timing_m17",
                "verdict": "PROMISED",
                "summary": ["Marriage timing: March – April 2027"],
                "step_audit": {"step1": {"name": "BCP scan", "status": "DONE"}},
                "timing_audit": {"status": "PASS"},
            },
            "engine_facts": {
                "verdict": "PROMISED",
                "summary": ["Marriage timing: March – April 2027"],
                "evidence": ["Primary window: March – April 2027"],
            },
            "blocks": {},
        }
        parsed = parse_llm_context_from_db(json.dumps(saved))
        trace = (parsed.get("blocks") or {}).get("engine_trace") or {}
        self.assertEqual(trace.get("primary_window"), "March – April 2027")
        self.assertIn("step1", trace.get("step_audit") or {})

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

    def test_answer_path_direct_llm_bypass_flag(self):
        code, label = derive_answer_path(
            llm_called=True,
            checks={"direct_llm_bypass": True, "slice_type": "llm_no_engine_v1"},
            slice_meta={},
        )
        self.assertEqual(code, "direct_llm")
        self.assertIn("Direct LLM", label)

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

    def test_marriage_timing_slice_meta_for_admin_evidence(self):
        from ask_llm_context_debug import (
            build_admin_llm_context,
            build_marriage_timing_slice_meta,
        )

        raw = {
            "primary_window": "October – November 2026",
            "backup_window": "March – April 2027",
            "verdict": "FAVORABLE",
            "band": "green_go",
            "bucket": "general_mr",
            "factors": ["BCP_ANCHOR age 29", "7L Venus AD active"],
            "step_audit": {
                "step1": {"name": "BCP scan", "status": "DONE", "detail": "age 29 anchor"},
                "step8": {"name": "Final gate", "status": "DONE", "verdict": "FAVORABLE"},
            },
            "timing_audit": {
                "status": "PASS",
                "checks": [{"name": "answer_lock", "ok": True, "detail": "window locked"}],
            },
        }
        meta = build_marriage_timing_slice_meta(raw)
        self.assertEqual(meta["slice"], "marriage_timing_m17")
        self.assertTrue(meta.get("evidence"))
        self.assertIn("October", meta["evidence"][0])

        ctx = build_admin_llm_context(
            question="Shaadi kab hogi?",
            is_timing=True,
            llm_called=False,
            checks={"slice_type": "timing_marriage_engine", "is_marriage_engine": True},
            slice_meta=meta,
            blocks={"engine_trace": {"engine": "marriage_timing_m17", **raw}},
        )
        facts = ctx.get("engine_facts") or {}
        self.assertTrue(facts.get("verdict"))
        self.assertGreaterEqual(len(facts.get("evidence") or []), 1)

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

    def test_recompute_marriage_bcp_from_kundli_fills_houses(self):
        from ask_llm_context_debug import (
            build_marriage_bcp_step2_admin_payload,
            normalize_kundli_chart_payload,
            recompute_marriage_bcp_from_kundli,
        )

        SIGNS = [
            "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
            "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
        ]
        idx = {s: i for i, s in enumerate([
            "Mesh", "Vrishabh", "Mithun", "Kark", "Simha", "Kanya",
            "Tula", "Vrishchik", "Dhanu", "Makar", "Kumbh", "Meen",
        ])}
        planets = []
        for name, sign, house in [
            ("Sun", "Tula", 11),
            ("Moon", "Mithun", 7),
            ("Mars", "Dhanu", 1),
            ("Mercury", "Vrishchik", 12),
            ("Jupiter", "Mesh", 5),
            ("Venus", "Simha", 9),
            ("Saturn", "Mesh", 5),
            ("Rahu", "Kark", 8),
            ("Ketu", "Makar", 2),
        ]:
            si = idx[sign]
            planets.append({"name": name, "sign": SIGNS[si], "house": house})
        kundli = {"ascendant": "Sagittarius", "planets": planets}

        ctx = {
            "is_timing": True,
            "checks": {"is_marriage_engine": True, "user_age": 26},
            "slice_meta": {
                "slice": "marriage_timing_m17",
                "step_audit": {
                    "step0a": {
                        "d1_seventh_lord": "Mercury",
                        "d9_seventh_lord": "Venus",
                    }
                },
            },
        }
        out = recompute_marriage_bcp_from_kundli(ctx, kundli)
        s0a = out["slice_meta"]["step_audit"]["step0a"]
        self.assertEqual(s0a["d1_7l_placement_house"], 12)
        self.assertIsInstance(s0a.get("d1_7l_aspect_houses"), list)
        step_audit = out["slice_meta"]["step_audit"]
        self.assertIsInstance(step_audit.get("step0"), dict)
        self.assertTrue((step_audit.get("step0") or {}).get("result"))
        self.assertIsInstance(step_audit.get("step3"), dict)
        self.assertTrue(step_audit["step3"].get("planet_names") or step_audit["step3"].get("marriage_giving_planets"))
        disp = s0a.get("bcp_house_display") or {}
        self.assertTrue((disp.get("d1") or {}).get("items"))
        payload = build_marriage_bcp_step2_admin_payload(ctx, kundli)
        self.assertIsNotNone(payload)
        self.assertTrue(payload["linkage_lines"])
        self.assertIn("12H", payload["linkage_lines"][0])
        self.assertIsNotNone(normalize_kundli_chart_payload({"kundli": kundli}))


if __name__ == "__main__":
    unittest.main()
