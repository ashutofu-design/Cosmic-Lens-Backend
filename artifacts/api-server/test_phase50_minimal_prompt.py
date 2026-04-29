"""Phase 5.0 — Minimal Ask Prompt tests (T032).

Asserts the Final Strip contract:
  • Mini chart summary builder returns chart facts WITHOUT dasha dates.
  • The 2-message minimal prompt contains NO supertype contract literals,
    NO UNIFIED NARRATOR preamble, NO Rule 1-N text, NO KP MANDATORY
    forcing, NO tier/length hint inside the prompt body.
  • Verdict-fact extractor produces ≤6 short lines from build_meta.
  • Sync (`ai_ask`) gate produces exactly 2 messages with roles
    `["system","user"]` when the env flag is ON.
  • Stream (`ai_ask_stream`) gate produces the same 2 messages — sync/
    stream parity (no logic drift).
  • When the env flag is "0" the legacy heavy path is restored
    (>2 messages and contract literals present).
  • Tier hint constant `_PHASE50_TIER_HINT` is empty (Final Strip).
"""
from __future__ import annotations

import os
import unittest
from typing import Any
from unittest.mock import patch, MagicMock

# Ensure flag is ON for the import-time defaults; individual tests
# override as needed.
os.environ.setdefault("PHASE50_MINIMAL_PROMPT", "1")

import openai_helper as oh


# ───────────────────────── Fixtures ─────────────────────────

def _sample_kundli() -> dict:
    """Realistic kundli shape used by /api/kundli responses."""
    return {
        "ascendant":      "Sagittarius",
        "moonSign":       "Gemini",
        "sunSign":        "Libra",
        "nakshatra":      "Ardra",
        "nakshatraPada":  2,
        "nakshatraRuler": "Rahu",
        "currentDasha": {
            "maha":      "Jupiter",
            "antar":     "Rahu",
            "startDate": "2010-06-27",
            "endDate":   "2026-06-27",
        },
        "planets": [
            {"name": "Mars",    "sign": "Sagittarius", "house": 1, "retrograde": False, "degrees": 12.5},
            {"name": "Ketu",    "sign": "Capricorn",   "house": 2, "retrograde": True,  "degrees": 8.1},
            {"name": "Jupiter", "sign": "Aries",       "house": 5, "retrograde": True,  "degrees": 22.0},
            {"name": "Saturn",  "sign": "Aries",       "house": 5, "retrograde": True,  "degrees": 14.7},
            {"name": "Moon",    "sign": "Gemini",      "house": 7, "retrograde": False, "degrees": 5.4},
            {"name": "Rahu",    "sign": "Cancer",      "house": 8, "retrograde": True,  "degrees": 2.0},
            {"name": "Venus",   "sign": "Leo",         "house": 9, "retrograde": False, "degrees": 18.3},
            {"name": "Sun",     "sign": "Libra",       "house": 11, "retrograde": False, "degrees": 11.9},
            {"name": "Mercury", "sign": "Scorpio",     "house": 12, "retrograde": False, "degrees": 27.4},
        ],
    }


def _sample_build_meta() -> dict:
    """Build-meta with a marriage verdict + a wealth verdict."""
    return {
        "marriage_verdict_block": (
            "Vivah mein patience zaroori — significant rukawat\n"
            "    (engine score 17, Jaimini UL Capricorn)"
        ),
        "wealth_verdict_obj": {
            "verdict": "Stable income with periodic gains",
            "bucket":  "moderate",
        },
        # Other domain verdicts left absent — must not raise.
    }


# ───────────────────────── T028 / T029 unit tests ─────────────────────────

class TestPhase50MiniChartSummary(unittest.TestCase):
    """Mini chart-summary builder: deterministic, defensive, no dates."""

    def test_basic_kundli_contains_lagna_moon_sun_dasha(self):
        s = oh._phase50_mini_chart_summary(_sample_kundli())
        # Core facts present.
        self.assertIn("Sagittarius", s)             # Lagna
        self.assertIn("Gemini",      s)             # Moon
        self.assertIn("Libra",       s)             # Sun
        self.assertIn("Jupiter",     s)             # MD lord
        self.assertIn("Rahu",        s)             # AD lord
        # Hard guard: NO dasha date strings ever.
        self.assertNotIn("2010", s)
        self.assertNotIn("2026", s)
        self.assertNotIn("-06-27", s)

    def test_planet_in_house_compact_format(self):
        s = oh._phase50_mini_chart_summary(_sample_kundli())
        # 1H: Mars, 5H: Jupiter+Saturn (both there), 7H: Moon, etc.
        self.assertIn("1H:", s)
        self.assertIn("Mars", s)
        self.assertIn("5H:", s)
        # Both planets in 5H must appear together.
        h5_idx = s.find("5H:")
        h5_segment = s[h5_idx:h5_idx + 80]
        self.assertIn("Jupiter", h5_segment)
        self.assertIn("Saturn",  h5_segment)

    def test_size_under_700_chars(self):
        s = oh._phase50_mini_chart_summary(_sample_kundli())
        self.assertLessEqual(len(s), 700,
            f"mini summary should stay compact (~500c); got {len(s)}c: {s!r}")

    def test_missing_kundli_does_not_raise(self):
        # None / empty / partial — must all return strings (possibly empty).
        for bad in [None, {}, {"planets": []}, {"ascendant": None}]:
            try:
                out = oh._phase50_mini_chart_summary(bad)
            except Exception as exc:
                self.fail(f"raised on {bad!r}: {exc}")
            self.assertIsInstance(out, str)

    def test_partial_dasha_does_not_raise(self):
        k = _sample_kundli()
        k["currentDasha"] = {"maha": "Jupiter"}   # no antar
        out = oh._phase50_mini_chart_summary(k)
        self.assertIsInstance(out, str)
        self.assertIn("Jupiter", out)


class TestPhase50MinimalMessagesBuilder(unittest.TestCase):
    """The 2-message builder: strict shape, no contracts, no tier hints."""

    def test_returns_exactly_two_messages_system_user(self):
        msgs = oh._phase50_build_minimal_messages(
            "kya mera love marriage hoga?", _sample_kundli(), lang="hn",
        )
        self.assertEqual(len(msgs), 2)
        self.assertEqual([m["role"] for m in msgs], ["system", "user"])

    def test_no_contract_literals_in_either_message(self):
        msgs = oh._phase50_build_minimal_messages(
            "career kab achhi hogi?", _sample_kundli(), lang="hn",
        )
        joined = (msgs[0]["content"] + "\n" + msgs[1]["content"])
        # Literals from the heavy contracts that MUST be absent now.
        # Note: "MANDATORY" was previously forbidden as a contract-bloat
        # marker, but Phase 5.3 legitimately uses it for the classical
        # "MANDATORY D9 CHECK" rule (D9 verification before any verdict),
        # so it is no longer in the forbidden list. The other tokens still
        # represent old heavy-contract preamble that must stay out.
        forbidden = [
            "UNIFIED NARRATOR",
            "SUPERTYPE",
            "GENERAL_ANALYSIS",
            "Rule 10",
            "Rule N",
            "Rule O",
            "FINAL REMINDER",
            "KP CROSS-CHECK",
            "PLANET-STRENGTH RULE",
            "JAIMINI UL CITATION",
            "STRICT RESPONSE CONTROL",
        ]
        for token in forbidden:
            self.assertNotIn(token, joined,
                f"forbidden contract literal {token!r} leaked into minimal prompt")

    def test_no_tier_or_length_hint_in_prompt(self):
        """Final Strip: tier/length hints removed from inside the prompt."""
        # Run for all three tiers — none may contain length-control text.
        kundli = _sample_kundli()
        for tier in ["simple", "detailed", "technical", None]:
            msgs = oh._phase50_build_minimal_messages(
                "Saturn powerful hai ya weak?", kundli, lang="hn", tier=tier,
            )
            joined = msgs[0]["content"] + "\n" + msgs[1]["content"]
            for tier_token in [
                "1-2 short sentences",
                "3-5 short sentences",
                "Reply in 1-2",
                "Reply in 3-5",
                "Direct verdict + one reason",
                "Plain-language explanation OK",
                "full technical detail",
            ]:
                self.assertNotIn(tier_token, joined,
                    f"tier hint {tier_token!r} leaked into prompt for tier={tier!r}")

    def test_tier_hint_constant_is_empty(self):
        """The constant itself is empty — defensive against re-introduction."""
        self.assertEqual(oh._PHASE50_TIER_HINT, {})

    def test_chart_block_present_with_lagna(self):
        msgs = oh._phase50_build_minimal_messages(
            "career?", _sample_kundli(), lang="en",
        )
        # Phase 5.2: label changed from "CHART:" to "CHART (quick reference):"
        # because we now ALSO append a FULL_KUNDLI_JSON block. Keep the test
        # tolerant — only require the leading "CHART" token.
        self.assertIn("CHART", msgs[1]["content"])
        self.assertIn("Sagittarius", msgs[1]["content"])
        # Phase 5.2: full kundli JSON must also be present.
        self.assertIn("FULL_KUNDLI_JSON", msgs[1]["content"])

    def test_extra_facts_appended_when_provided(self):
        msgs = oh._phase50_build_minimal_messages(
            "marriage?", _sample_kundli(), lang="hn",
            extra_facts="Marriage verdict: Patience zaroori",
        )
        self.assertIn("FACTS:", msgs[1]["content"])
        self.assertIn("Patience zaroori", msgs[1]["content"])

    def test_question_present_in_user_message(self):
        q = "kya yog hai mere kundli mein?"
        msgs = oh._phase50_build_minimal_messages(q, _sample_kundli(), lang="hn")
        self.assertIn("QUESTION:", msgs[1]["content"])
        self.assertIn(q, msgs[1]["content"])

    def test_language_hint_in_system_message(self):
        msgs_hi = oh._phase50_build_minimal_messages("a?", _sample_kundli(), lang="hn")
        msgs_en = oh._phase50_build_minimal_messages("a?", _sample_kundli(), lang="en")
        self.assertIn("Hindi", msgs_hi[0]["content"])
        self.assertIn("English", msgs_en[0]["content"])

    def test_system_message_under_2500_chars(self):
        """System message must stay reasonable — no preamble bloat allowed.
        Phase 5.2: bumped from 400 → 1500c (ChatGPT-style guidance prompt
        + COPY-EXACTLY instruction).
        Phase 5.3: bumped 1500 → 2500c to accommodate the classical
        "MANDATORY D9 (NAVAMSHA) CHECK" rule block (Vargottama,
        neecha-bhanga, dignity-change, karaka-per-topic, D9-wins-over-D1).
        Anything > 2500c indicates new preamble drift beyond the D9 rule.
        """
        msgs = oh._phase50_build_minimal_messages("q?", _sample_kundli(), lang="hn")
        self.assertLessEqual(len(msgs[0]["content"]), 2500,
            f"system msg too long ({len(msgs[0]['content'])}c) — preamble drift?")


# ───────────────────────── T030 / T031 — verdict extractor ─────────────────

class TestPhase50ExtractVerdictFacts(unittest.TestCase):

    def test_extracts_marriage_first_line_only(self):
        out = oh._phase50_extract_verdict_facts(_sample_build_meta())
        self.assertIn("Marriage verdict: Vivah mein patience", out)
        # The follow-on indented line must NOT appear (we take first line).
        self.assertNotIn("engine score 17", out)

    def test_extracts_wealth_verdict_with_bucket(self):
        out = oh._phase50_extract_verdict_facts(_sample_build_meta())
        self.assertIn("Wealth verdict: Stable income", out)
        self.assertIn("(moderate)", out)

    def test_handles_none_and_empty(self):
        self.assertEqual(oh._phase50_extract_verdict_facts(None),  "")
        self.assertEqual(oh._phase50_extract_verdict_facts({}),    "")
        self.assertEqual(oh._phase50_extract_verdict_facts("not-a-dict"), "")

    def test_max_six_lines(self):
        bm = {
            "marriage_verdict_block": "MV verdict line",
            "wealth_verdict_obj":   {"verdict": "W"},
            "love_verdict_obj":     {"verdict": "L"},
            "career_verdict_obj":   {"verdict": "C"},
            "health_verdict_obj":   {"verdict": "H"},
            "stock_verdict_obj":    {"verdict": "S"},
        }
        lines = [ln for ln in oh._phase50_extract_verdict_facts(bm).splitlines() if ln.strip()]
        self.assertLessEqual(len(lines), 6)
        self.assertEqual(len(lines), 6)


# ───────────────────────── Env-flag behaviour ─────────────────────────

class TestPhase50EnvFlag(unittest.TestCase):

    def test_default_is_on(self):
        # Clear any test override and check the default.
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("PHASE50_MINIMAL_PROMPT", None)
            self.assertTrue(oh._phase50_minimal_prompt_enabled())

    def test_off_when_set_to_zero(self):
        with patch.dict(os.environ, {"PHASE50_MINIMAL_PROMPT": "0"}):
            self.assertFalse(oh._phase50_minimal_prompt_enabled())

    def test_on_when_set_to_one(self):
        with patch.dict(os.environ, {"PHASE50_MINIMAL_PROMPT": "1"}):
            self.assertTrue(oh._phase50_minimal_prompt_enabled())

    def test_on_for_any_non_zero_string(self):
        with patch.dict(os.environ, {"PHASE50_MINIMAL_PROMPT": "true"}):
            self.assertTrue(oh._phase50_minimal_prompt_enabled())


# ───────────────────────── Sync / Stream parity ─────────────────────────

class TestPhase50InstallParity(unittest.TestCase):
    """Both sync and stream gates use `_phase50_install_minimal_messages`,
    so calling it with identical inputs must yield identical messages —
    proving "no sync/stream drift"."""

    def test_install_returns_same_messages_for_same_inputs(self):
        kundli = _sample_kundli()
        bm = _sample_build_meta()
        msgs_sync, _ = oh._phase50_install_minimal_messages(
            "kya mera love marriage hai?", kundli, "hn", bm,
            req_id="parity-test-sync", path_label="",
        )
        msgs_stream, _ = oh._phase50_install_minimal_messages(
            "kya mera love marriage hai?", kundli, "hn", bm,
            req_id="parity-test-stream", path_label="(stream)",
        )
        # Identical content — only the trace key differs (label).
        self.assertEqual(msgs_sync, msgs_stream)
        self.assertEqual(len(msgs_sync), 2)
        self.assertEqual([m["role"] for m in msgs_sync], ["system", "user"])

    def test_install_telemetry_shape(self):
        msgs, tele = oh._phase50_install_minimal_messages(
            "q?", _sample_kundli(), "hn", _sample_build_meta(),
            req_id="tele-test",
        )
        self.assertEqual(tele["message_count"], 2)
        self.assertEqual(tele["roles"], ["system", "user"])
        self.assertGreater(tele["user_chars"], 0)
        self.assertGreaterEqual(tele["facts_lines"], 1)
        # Tier key must NOT be in telemetry — Final Strip removed it.
        self.assertNotIn("tier", tele)


# ───────────────────────── Integration smoke ─────────────────────────

class TestPhase50ImportSmoke(unittest.TestCase):
    """Catch import-time / signature breaks before they hit the live ask."""

    def test_all_four_helpers_callable(self):
        for fn_name in [
            "_phase50_mini_chart_summary",
            "_phase50_build_minimal_messages",
            "_phase50_extract_verdict_facts",
            "_phase50_install_minimal_messages",
            "_phase50_minimal_prompt_enabled",
        ]:
            self.assertTrue(hasattr(oh, fn_name), f"missing {fn_name}")
            self.assertTrue(callable(getattr(oh, fn_name)), f"{fn_name} not callable")


if __name__ == "__main__":
    unittest.main()


# ═════════════════════════════════════════════════════════════════════════════
# Phase 5.5 — Deterministic LOVE-vs-ARRANGE engine (verdict-lock)
# ═════════════════════════════════════════════════════════════════════════════
# The engine computes a fixed verdict in pure Python from D1 + D9 so the LLM
# cannot flip the answer between requests. These tests pin the contract:
#   • question detector is conservative (only fires on real L-vs-A questions)
#   • engine is deterministic (same kundli → identical verdict every run)
#   • engine handles missing D9, missing planets, bad input without raising
#   • locked-verdict block contains the DO-NOT-CHANGE instruction
#   • the minimal-prompt builder substitutes the locked block for the
#     rule-checklist when the lock fires (so the model isn't told to
#     compute its own verdict in parallel)


def _kundli_with_d9() -> dict:
    """Bhubaneswar-style chart with Sag lagna + populated D9."""
    return {
        "ascendant": "Sagittarius",
        "moonSign":  "Gemini",
        "sunSign":   "Libra",
        "planets": [
            {"name": "Mars",    "sign": "Sagittarius", "house": 1},
            {"name": "Venus",   "sign": "Leo",         "house": 9},
            {"name": "Saturn",  "sign": "Aries",       "house": 5},
            {"name": "Jupiter", "sign": "Aries",       "house": 5},
            {"name": "Moon",    "sign": "Gemini",      "house": 7},
            {"name": "Sun",     "sign": "Libra",       "house": 11},
            {"name": "Mercury", "sign": "Scorpio",     "house": 12},
            {"name": "Rahu",    "sign": "Cancer",      "house": 8},
            {"name": "Ketu",    "sign": "Capricorn",   "house": 2},
        ],
        "divisionalCharts": {
            "D9": {
                "ascendantSignIndex": 8,  # Sagittarius
                "planets": [
                    {"name": "Mars",    "sign": "Sagittarius", "house": 1},
                    {"name": "Sun",     "sign": "Capricorn",   "house": 2},
                    {"name": "Venus",   "sign": "Pisces",      "house": 4},
                    {"name": "Jupiter", "sign": "Sagittarius", "house": 1},
                    {"name": "Saturn",  "sign": "Sagittarius", "house": 1},
                    {"name": "Moon",    "sign": "Cancer",      "house": 8},
                    {"name": "Mercury", "sign": "Virgo",       "house": 10},
                    {"name": "Rahu",    "sign": "Aries",       "house": 5},
                    {"name": "Ketu",    "sign": "Libra",       "house": 11},
                ],
            },
        },
    }


class TestPhase55QuestionDetector(unittest.TestCase):
    def test_fires_on_clear_love_vs_arrange(self):
        for q in [
            "Mera love marriage hoga ya arrange?",
            "Will I have love marriage or arranged?",
            "Love ya arrange?",
            "love or arranged marriage chance",
            "Pyaar wali ya arrange hogi shaadi?",
            "Romance ya arrange marriage?",
        ]:
            self.assertTrue(
                oh._phase55_is_love_vs_arrange_question(q),
                f"should fire on {q!r}",
            )

    def test_does_not_fire_on_unrelated(self):
        for q in [
            "",
            None,
            "Kab shaadi hogi?",
            "When will I marry?",
            "How is my love life?",       # love only, no arrange
            "Arrange marriage timing?",   # arrange only, no love
            "Career advice please",
            "Will I be rich?",
        ]:
            self.assertFalse(
                oh._phase55_is_love_vs_arrange_question(q),  # type: ignore[arg-type]
                f"should NOT fire on {q!r}",
            )


class TestPhase55Engine(unittest.TestCase):
    def test_returns_required_keys(self):
        v = oh._phase55_compute_love_vs_arrange(_kundli_with_d9())
        self.assertIsNotNone(v)
        for k in ("verdict", "confidence", "love_score", "arrange_score",
                  "reasons_love", "reasons_arrange", "verdict_text_hi"):
            self.assertIn(k, v)
        self.assertIn(v["verdict"], ("love_likely", "arrange_likely", "mixed"))
        self.assertGreaterEqual(v["confidence"], 0.5)
        self.assertLessEqual(v["confidence"], 0.95)

    def test_deterministic_across_runs(self):
        """Same kundli MUST produce the same verdict every time —
        this is the whole point of the engine (LLM was flipping)."""
        k = _kundli_with_d9()
        first = oh._phase55_compute_love_vs_arrange(k)
        for _ in range(20):
            v = oh._phase55_compute_love_vs_arrange(k)
            self.assertEqual(v["verdict"],       first["verdict"])
            self.assertEqual(v["love_score"],    first["love_score"])
            self.assertEqual(v["arrange_score"], first["arrange_score"])
            self.assertEqual(v["confidence"],    first["confidence"])

    def test_arrange_heavy_kundli_returns_arrange(self):
        """Pile up arrange indicators (Manglik + Saturn-Venus + Saturn-7H +
        D9 Venus debilitated) — verdict must lean arrange_likely."""
        k = {
            "ascendant": "Aries",
            "planets": [
                {"name": "Mars",    "sign": "Aries",  "house": 1},   # Manglik
                {"name": "Saturn",  "sign": "Libra",  "house": 7},   # Sat in 7H
                {"name": "Venus",   "sign": "Libra",  "house": 7},   # Sat-Ven conj
                {"name": "Sun",     "sign": "Leo",    "house": 5},
                {"name": "Moon",    "sign": "Cancer", "house": 4},
                {"name": "Mercury", "sign": "Virgo",  "house": 6},
                {"name": "Jupiter", "sign": "Pisces", "house": 12},
                {"name": "Rahu",    "sign": "Scorpio","house": 8},   # Rahu 8H
                {"name": "Ketu",    "sign": "Taurus", "house": 2},
            ],
            "divisionalCharts": {
                "D9": {
                    "ascendantSignIndex": 0,
                    "planets": [
                        {"name": "Venus", "sign": "Virgo", "house": 6},  # debil + dusthana
                        {"name": "Sun",   "sign": "Aries", "house": 1},
                    ],
                },
            },
        }
        v = oh._phase55_compute_love_vs_arrange(k)
        self.assertIsNotNone(v)
        self.assertEqual(
            v["verdict"], "arrange_likely",
            f"expected arrange_likely; got {v}",
        )
        self.assertGreater(v["arrange_score"], v["love_score"])

    def test_love_heavy_kundli_returns_love(self):
        """Pile up love indicators (Venus 5H + Rahu 7H + Mars-Venus +
        D9 Venus exalted) — verdict must lean love_likely."""
        k = {
            "ascendant": "Leo",  # 5L=Jupiter, 7L=Saturn
            "planets": [
                {"name": "Venus",   "sign": "Sagittarius", "house": 5},   # Venus in 5H
                {"name": "Mars",    "sign": "Sagittarius", "house": 5},   # Mars-Venus same sign
                {"name": "Rahu",    "sign": "Aquarius",    "house": 7},   # Rahu 7H
                {"name": "Jupiter", "sign": "Sagittarius", "house": 5},   # 5L w/ 7L? no, but in 5H
                {"name": "Saturn",  "sign": "Sagittarius", "house": 5},   # 7L Sat in 5H w/ 5L Jup → same sign!
                {"name": "Sun",     "sign": "Leo",         "house": 1},
                {"name": "Moon",    "sign": "Pisces",      "house": 8},
                {"name": "Mercury", "sign": "Virgo",       "house": 2},
                {"name": "Ketu",    "sign": "Leo",         "house": 1},
            ],
            "divisionalCharts": {
                "D9": {
                    "ascendantSignIndex": 4,
                    "planets": [
                        {"name": "Venus",   "sign": "Pisces",     "house": 8},  # exalted
                        {"name": "Jupiter", "sign": "Sagittarius","house": 5},  # 5L in trine
                        {"name": "Saturn",  "sign": "Sagittarius","house": 5},  # 7L same sign as 5L
                    ],
                },
            },
        }
        v = oh._phase55_compute_love_vs_arrange(k)
        self.assertIsNotNone(v)
        self.assertEqual(
            v["verdict"], "love_likely",
            f"expected love_likely; got {v}",
        )
        self.assertGreater(v["love_score"], v["arrange_score"])

    def test_handles_missing_d9(self):
        k = _kundli_with_d9()
        del k["divisionalCharts"]
        v = oh._phase55_compute_love_vs_arrange(k)
        self.assertIsNotNone(v)  # should still work with D1 only
        self.assertIn(v["verdict"], ("love_likely", "arrange_likely", "mixed"))

    def test_evidence_floor_downgrades_sparse_directional(self):
        """Architect-review pin: with diff>=4 but total<6 (e.g. 4-vs-0),
        the engine MUST downgrade to mixed/0.55 — sparse evidence is not
        enough for a high-confidence directional verdict."""
        # Build a chart with exactly ONE love indicator firing (Venus in 5H,
        # +2) and a stacked Rahu+Mars-Venus to land at total=4 vs 0.
        sparse_love = {
            "ascendant": "Capricorn",  # 5L=Venus, 7L=Moon
            "planets": [
                {"name": "Venus",   "sign": "Taurus",      "house": 5},   # +2 (Venus 5H)
                {"name": "Mars",    "sign": "Taurus",      "house": 5},   # +2 (Mars-Ven same sign)
                {"name": "Sun",     "sign": "Sagittarius", "house": 12},
                {"name": "Moon",    "sign": "Pisces",      "house": 3},
                {"name": "Mercury", "sign": "Sagittarius", "house": 12},
                {"name": "Jupiter", "sign": "Sagittarius", "house": 12},
                {"name": "Saturn",  "sign": "Pisces",      "house": 3},
                {"name": "Rahu",    "sign": "Gemini",      "house": 6},
                {"name": "Ketu",    "sign": "Sagittarius", "house": 12},
            ],
        }
        v = oh._phase55_compute_love_vs_arrange(sparse_love)
        self.assertIsNotNone(v)
        # Total evidence is small — must NOT return high-confidence directional
        if v["love_score"] + v["arrange_score"] < 6:
            self.assertEqual(
                v["verdict"], "mixed",
                f"sparse evidence ({v['love_score']} vs {v['arrange_score']}) "
                f"must downgrade to mixed; got {v}",
            )
            self.assertEqual(v["confidence"], 0.55)

    def test_returns_none_on_bad_input(self):
        self.assertIsNone(oh._phase55_compute_love_vs_arrange(None))         # type: ignore[arg-type]
        self.assertIsNone(oh._phase55_compute_love_vs_arrange("string"))     # type: ignore[arg-type]
        self.assertIsNone(oh._phase55_compute_love_vs_arrange({}))           # no planets
        self.assertIsNone(oh._phase55_compute_love_vs_arrange(
            {"planets": [{"name": "Sun", "sign": "Leo", "house": 1}]}        # no ascendant
        ))

    def test_locked_block_has_do_not_change_instruction(self):
        v = oh._phase55_compute_love_vs_arrange(_kundli_with_d9())
        block = oh._phase55_format_locked_verdict_block(v)
        self.assertIn("AUTHORITATIVE_ENGINE_VERDICT", block)
        self.assertIn("DO NOT change", block)
        self.assertIn("HEADLINE", block)
        self.assertIn("1-2 short sentences", block)
        # Must NOT instruct the model to compute or analyze
        self.assertNotIn("compute your own verdict", block.lower())
        # Brevity is preserved — only explain when user asks why
        self.assertIn("kyun", block)


class TestPhase55BuilderIntegration(unittest.TestCase):
    """When a love-vs-arrange question fires, the prompt builder must
    REPLACE the topic-rule checklist with the locked verdict block —
    otherwise the model would get told 'here is the verdict' AND 'here
    are the rules — go compute your own', which is exactly the bug
    that caused flipping verdicts."""

    def test_lock_replaces_topic_rules_for_lva_question(self):
        msgs = oh._phase50_build_minimal_messages(
            question="Mera love marriage hoga ya arrange?",
            kundli=_kundli_with_d9(),
            lang="hi",
            extra_facts="",
            topic="marriage",
        )
        user = msgs[-1]["content"]
        self.assertIn("AUTHORITATIVE_ENGINE_VERDICT", user)
        # MARRIAGE rules checklist (Phase 5.3) must be SUPPRESSED so the
        # model has nothing to derive its own verdict from.
        self.assertNotIn("MARRIAGE-question CHECKLIST", user)
        self.assertNotIn("Vargottama check", user)

    def test_lock_swaps_system_message_to_narrate_only(self):
        """Architect-review fix: when lock fires, system message must NOT
        tell the model to compute its own D9 verdict (otherwise it
        contradicts the locked block in the user message)."""
        msgs = oh._phase50_build_minimal_messages(
            question="Mera love marriage hoga ya arrange?",
            kundli=_kundli_with_d9(),
            lang="hi",
            extra_facts="",
            topic="marriage",
        )
        sysm = msgs[0]["content"]
        self.assertIn("VERDICT-LOCK MODE", sysm)
        # Default system msg "ARRIVE at the right verdict" must be GONE.
        self.assertNotIn("ARRIVE at the right verdict", sysm)
        self.assertNotIn("MANDATORY D9", sysm)

    def test_lock_combined_prompt_has_no_recompute_verbs(self):
        """Architect-review pin: across the COMBINED system+user prompt
        in lock mode, there must be NO instruction telling the model to
        compute, derive, analyze, walk through rules, or arrive at a
        verdict. Defense against future prompt-drift re-introducing the
        contradictory instructions."""
        msgs = oh._phase50_build_minimal_messages(
            question="Mera love marriage hoga ya arrange?",
            kundli=_kundli_with_d9(),
            lang="hi",
            extra_facts="",
            topic="marriage",
        )
        combined = (msgs[0]["content"] + "\n" + msgs[-1]["content"]).lower()
        # These are the exact phrases the model used to be told to do.
        # If any of them comes back, the lock is leaking.
        forbidden = [
            "arrive at the right verdict",
            "arrive at the correct verdict",
            "compute your own verdict",
            "compute the verdict",
            "walk through silently",
            "silently walking through the rules",
            "mandatory d9",
            "marriage-question checklist",
            "vargottama check",
        ]
        for phrase in forbidden:
            self.assertNotIn(
                phrase, combined,
                f"lock-mode prompt leaked recompute verb: {phrase!r}",
            )

    def test_lock_omits_full_kundli_json(self):
        """Architect-review fix: with locked verdict in user message, raw
        FULL_KUNDLI_JSON must NOT be included — without it the model has
        no material from which to recompute / flip the verdict."""
        msgs = oh._phase50_build_minimal_messages(
            question="Love marriage hoga ya arrange?",
            kundli=_kundli_with_d9(),
            lang="hi",
            extra_facts="",
            topic="marriage",
        )
        user = msgs[-1]["content"]
        self.assertNotIn("FULL_KUNDLI_JSON", user)
        # Mini chart summary stays — engine output stays — that's it.
        self.assertIn("AUTHORITATIVE_ENGINE_VERDICT", user)

    def test_no_lock_for_non_lva_marriage_question(self):
        """Pure timing question must keep the rule checklist (no lock)."""
        msgs = oh._phase50_build_minimal_messages(
            question="Meri shaadi kab hogi?",
            kundli=_kundli_with_d9(),
            lang="hi",
            extra_facts="",
            topic="marriage",
        )
        user = msgs[-1]["content"]
        self.assertNotIn("AUTHORITATIVE_ENGINE_VERDICT", user)

    def test_lock_fires_independent_of_topic(self):
        """Detector keys off the question text, not the topic — protects
        against topic-router miscategorising L-vs-A as 'general' or
        'relationship'."""
        msgs = oh._phase50_build_minimal_messages(
            question="Love ya arrange?",
            kundli=_kundli_with_d9(),
            lang="hi",
            extra_facts="",
            topic="general",
        )
        user = msgs[-1]["content"]
        self.assertIn("AUTHORITATIVE_ENGINE_VERDICT", user)
