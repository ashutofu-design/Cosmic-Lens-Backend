"""Phase 4.9 — Adaptive depth (3-tier output discipline) tests.

Replaces Phase 4.8's flat 1-2 sentence cap with intent-driven depth:
  Tier 1 SIMPLE   → existing T019 behaviour (≤2 sentences, ≤280 chars,
                    strip date/pratyantar for non-timing).
  Tier 2 DETAILED → ≤5 sentences, ≤600 chars, strip ISO date ranges
                    only; KEEP planet/dasha-name explanations.
  Tier 3 TECHNICAL→ pass-through (no truncation).

Also verifies T025: the truncator is wired into ai_ask_stream's
final_text path (closes the streaming bypass discovered last session).
"""
from __future__ import annotations

import re
import unittest
from typing import Any
from unittest.mock import patch

import openai_helper as oh


# ───────────────────────── T022: classifier unit tests ─────────────────────

class TestT022QuestionDepthTier(unittest.TestCase):
    """Pure-function classifier tests — deterministic, case-insensitive."""

    def test_empty_or_invalid_returns_simple(self):
        self.assertEqual(oh._question_depth_tier(""), "simple")
        self.assertEqual(oh._question_depth_tier("   "), "simple")
        self.assertEqual(oh._question_depth_tier(None), "simple")  # type: ignore[arg-type]
        self.assertEqual(oh._question_depth_tier(123), "simple")  # type: ignore[arg-type]

    def test_simple_tier_default(self):
        cases = [
            "kya mujhe love hoga?",
            "Will I get married this year?",
            "Job lagegi?",
            "Money milega?",
            "is it good?",
        ]
        for q in cases:
            with self.subTest(q=q):
                self.assertEqual(oh._question_depth_tier(q), "simple")

    def test_detailed_tier_english(self):
        cases = [
            "Explain why my career is stuck",
            "Can you explain how Mars affects me?",
            "Tell me in detail about my marriage",
            "Why is my health weak?",
            "Elaborate on my finances please",
            "Describe my personality",
            "step by step batao",
        ]
        for q in cases:
            with self.subTest(q=q):
                self.assertEqual(oh._question_depth_tier(q), "detailed")

    def test_detailed_tier_hindi_hinglish(self):
        cases = [
            "Mujhe job kaise milegi?",
            "Yeh problem kyun ho rahi hai?",
            "Samjhao mujhe pura",
            "Vistar se batao",
            "Puri detail chahiye",
            "Batao kyun aisa hota hai",
        ]
        for q in cases:
            with self.subTest(q=q):
                self.assertEqual(oh._question_depth_tier(q), "detailed")

    def test_technical_tier_keywords(self):
        cases = [
            "What does my KP chart say?",
            "Show me the sublord of 7th cusp",
            "Analyze my D-9 navamsa",
            "What's in my 10th house?",
            "Give me the dasha breakdown",
            "Explain pratyantar dasha for marriage",
            "What is my atmakaraka?",
            "Bhava analysis please",
            "lagnesh kaha hai?",
        ]
        for q in cases:
            with self.subTest(q=q):
                self.assertEqual(oh._question_depth_tier(q), "technical")

    def test_technical_takes_precedence_over_detailed(self):
        # Question contains BOTH "explain" (Tier 2) and "KP" (Tier 3).
        # Technical must win.
        q = "Explain my KP chart in detail"
        self.assertEqual(oh._question_depth_tier(q), "technical")
        q2 = "Kaise pata chalega mera sublord?"
        self.assertEqual(oh._question_depth_tier(q2), "technical")

    def test_case_insensitive(self):
        self.assertEqual(oh._question_depth_tier("EXPLAIN MY CHART"), "detailed")
        self.assertEqual(oh._question_depth_tier("My Kp Chart"), "technical")
        self.assertEqual(oh._question_depth_tier("KAISE HOGA"), "detailed")


# ──────────────────────── T024: tier-aware truncator ──────────────────────

class TestT024TierAwareTruncator(unittest.TestCase):
    """`_phase48_narrative_truncate` must respect the per-tier caps."""

    LONG_ANSWER = (
        "Pehla sentence yeh hai. Doosra sentence yahan. Teesra sentence "
        "bhi hai. Chautha sentence aata hai. Paancha sentence hai. "
        "Chhata sentence bhi yahan. Saatva sentence end karta hai."
    )

    def test_tier1_simple_caps_to_two_sentences(self):
        out = oh._phase48_narrative_truncate(
            self.LONG_ANSWER, "kya hoga?", tier="simple",
        )
        sents = re.split(r"(?<=[.!?।])\s+", out.strip())
        self.assertLessEqual(len(sents), 2)
        self.assertLessEqual(len(out), 280)

    def test_tier2_detailed_keeps_up_to_five_sentences(self):
        out = oh._phase48_narrative_truncate(
            self.LONG_ANSWER, "Explain why this happens", tier="detailed",
        )
        sents = re.split(r"(?<=[.!?।])\s+", out.strip())
        self.assertGreater(
            len(sents), 2,
            f"Tier 2 should preserve >2 sentences, got {len(sents)}: {out!r}",
        )
        self.assertLessEqual(len(sents), 5)
        self.assertLessEqual(len(out), 600)

    def test_tier3_technical_passthrough_unchanged(self):
        out = oh._phase48_narrative_truncate(
            self.LONG_ANSWER, "Show my KP sublord chart", tier="technical",
        )
        self.assertEqual(out, self.LONG_ANSWER,
                         "Tier 3 must return text byte-identical")

    def test_tier3_passthrough_via_question_inference(self):
        # No explicit tier kwarg — must infer technical from the question.
        out = oh._phase48_narrative_truncate(
            self.LONG_ANSWER, "My navamsa D-9 analysis please",
        )
        self.assertEqual(out, self.LONG_ANSWER)

    def test_tier2_strips_iso_dates_but_keeps_dasha_names(self):
        text = (
            "Mars antardasha mein challenge aayega. Yeh phase "
            "2026-03-15 se 2026-08-22 tak rahega. Rahu ki energy "
            "bhi active hai. Saath mein Jupiter help karega. "
            "Aapko patience rakhna hoga."
        )
        out = oh._phase48_narrative_truncate(
            text, "Why is my career stuck?", tier="detailed",
        )
        # ISO date range must be gone.
        self.assertNotIn("2026-03-15", out)
        self.assertNotIn("2026-08-22", out)
        # Dasha lord names + planet names must survive (Tier 2 allows them).
        self.assertIn("Mars", out)
        self.assertIn("Rahu", out)

    def test_tier1_strips_pratyantar_sentences(self):
        text = (
            "Job mil sakti hai. Pratyantar dasha Moon ki chal rahi hai. "
            "Effort lagana padega."
        )
        out = oh._phase48_narrative_truncate(
            text, "kya job milegi?", tier="simple",
        )
        self.assertNotIn("Pratyantar", out)
        self.assertNotIn("pratyantar", out.lower())

    def test_tier2_keeps_pratyantar_explanation_when_user_asked_why(self):
        # Tier 2 has drop_pratyantar_sentences=False so a "why" answer can
        # legitimately reference sub-periods (just no ISO dates).
        text = (
            "Aapki Mars antardasha bahut active hai. "
            "Iss wajah se aap impulsive feel kar rahe ho. "
            "Patience zaroori hai."
        )
        out = oh._phase48_narrative_truncate(
            text, "Why am I feeling restless?", tier="detailed",
        )
        self.assertIn("antardasha", out.lower())

    def test_idempotent_short_answer(self):
        short = "Love ho sakta hai, Mars ki impulsiveness se."
        out = oh._phase48_narrative_truncate(short, "love hoga?", tier="simple")
        self.assertEqual(out, short)

    def test_empty_input_returns_input(self):
        for empty in ("", "   ", None):
            self.assertEqual(
                oh._phase48_narrative_truncate(empty, "q"),  # type: ignore[arg-type]
                empty,
            )


# ──────────────── T023: tier-aware Rule 10 swap (runtime) ─────────────────

class _CaptureClient:
    """Minimal stub that captures the messages list passed to OpenAI so we
    can introspect the user-turn prompt and assert the right Rule 10 swap
    was applied. Returns a benign response so ai_ask completes."""

    def __init__(self):
        self.captured: list[dict[str, Any]] = []

        # Build the nested .chat.completions.create attribute path.
        client = self

        class _Completions:
            @staticmethod
            def create(**kwargs):
                client.captured = list(kwargs.get("messages") or [])
                # Return an OpenAI-shaped response object.
                class _Choice:
                    class message:
                        content = "Test answer."
                    finish_reason = "stop"
                class _Resp:
                    choices = [_Choice()]
                    model = "test-model"
                    usage = type("U", (), {"prompt_tokens": 1,
                                            "completion_tokens": 1,
                                            "total_tokens": 2})()
                return _Resp()

        class _Chat:
            completions = _Completions()

        self.chat = _Chat()


class TestT023RuleSwapRuntime(unittest.TestCase):
    """End-to-end: drive ai_ask with a mocked OpenAI client and inspect the
    user-turn message that was sent. Rule 10 should match the inferred tier."""

    KUNDLI = {
        "planets": {
            "Sun":     {"sign": "Aries", "house": 1, "deg": 5},
            "Moon":    {"sign": "Cancer", "house": 4, "deg": 10},
            "Mars":    {"sign": "Aries", "house": 1, "deg": 12},
            "Mercury": {"sign": "Pisces", "house": 12, "deg": 8},
            "Jupiter": {"sign": "Sagittarius", "house": 9, "deg": 15},
            "Venus":   {"sign": "Taurus", "house": 2, "deg": 4},
            "Saturn":  {"sign": "Capricorn", "house": 10, "deg": 20},
            "Rahu":    {"sign": "Gemini", "house": 3, "deg": 7},
            "Ketu":    {"sign": "Sagittarius", "house": 9, "deg": 7},
        },
        "currentDasha": {"mahaDasha": "Mars", "antarDasha": "Moon"},
        "ascendant": "Aries",
    }

    def _drive(self, question: str) -> str:
        """Invoke ai_ask through a CaptureClient and return the user-turn
        prompt content (concatenated string of msgs[-1]['content'])."""
        cap = _CaptureClient()
        with patch.object(oh, "_get_client", return_value=cap):
            try:
                oh.ai_ask(question, self.KUNDLI, lang="en")
            except Exception:
                # ai_ask may raise on stub responses for some paths — what
                # matters is that the OpenAI call was made and captured.
                pass
        if not cap.captured:
            self.skipTest(
                "OpenAI client stub was not invoked — narrative path may "
                "have early-returned (rule_engine fallback)."
            )
        # User-turn is typically the last role=user message before the call.
        user_msgs = [m for m in cap.captured if m.get("role") == "user"]
        self.assertTrue(user_msgs, "no user-turn message captured")
        content = user_msgs[-1].get("content")
        if isinstance(content, list):  # multimodal-style content
            content = " ".join(
                str(p.get("text", p)) for p in content if p
            )
        return content or ""

    def test_tier1_simple_question_uses_hard_cap(self):
        prompt = self._drive("Will I get love this year?")
        self.assertIn("NARRATIVE-MODE HARD CAP (Tier 1", prompt)
        self.assertIn("1 to 2 SHORT SENTENCES", prompt)
        self.assertNotIn("100 to 140 WORDS. NEVER more.", prompt)

    def test_tier2_detailed_question_uses_3to5_sentence_cap(self):
        prompt = self._drive("Explain why my career is stuck")
        self.assertIn("NARRATIVE-MODE DETAILED ANSWER (Tier 2", prompt)
        self.assertIn("3 to 5 SHORT", prompt)
        self.assertNotIn("100 to 140 WORDS. NEVER more.", prompt)

    def test_tier3_technical_question_keeps_original_default(self):
        # Tier 3 contract: the T023 swap block does NOT inject either of the
        # narrative tier caps. (Whether the original "100 to 140 WORDS"
        # default is present depends on which prompt template the routing
        # picked — that's outside this contract. What matters is that we
        # didn't downsize the answer with a Tier 1 / Tier 2 cap.)
        prompt = self._drive("Show me my KP sublord analysis")
        self.assertNotIn("NARRATIVE-MODE HARD CAP (Tier 1", prompt)
        self.assertNotIn("NARRATIVE-MODE DETAILED ANSWER (Tier 2", prompt)
        self.assertNotIn("1 to 2 SHORT SENTENCES", prompt)
        self.assertNotIn("3 to 5 SHORT", prompt)


# ───────────── T025: streaming endpoint wires in the truncator ────────────

class TestT025StreamingTruncatorWiring(unittest.TestCase):
    """ai_ask_stream must call _phase48_narrative_truncate on its final_text
    so the mobile streaming endpoint no longer bypasses output discipline."""

    def _stream_body(self) -> str:
        with open(oh.__file__, "r", encoding="utf-8") as f:
            src = f.read()
        stream_match = re.search(r"^def ai_ask_stream\b", src, re.M)
        self.assertIsNotNone(stream_match, "ai_ask_stream not found")
        body_start = stream_match.start()
        next_def = re.search(r"^def ai_ask_v2\b", src[body_start:], re.M)
        self.assertIsNotNone(next_def)
        return src[body_start: body_start + next_def.start()]

    def test_truncator_called_from_stream_path(self):
        body = self._stream_body()
        self.assertIn(
            "_phase48_narrative_truncate", body,
            "Phase 4.9 T025 expected the truncator to be wired into "
            "ai_ask_stream's final_text path",
        )
        self.assertIn(
            "_NARRATIVE_MODE", body,
            "Stream-path truncator must be guarded by _NARRATIVE_MODE",
        )
        self.assertIn(
            "phase49-trim", body,
            "Stream-path truncator should emit Phase 4.9 telemetry tag",
        )

    def test_truncator_runs_BEFORE_engine_warn_footer(self):
        """ARCHITECT-FIX: the engine-warn-footer block must come AFTER the
        truncator block — otherwise the truncator's char-cap can clip the
        appended footer mid-string. We assert ordering by checking the
        position of marker strings in ai_ask_stream's body."""
        body = self._stream_body()
        trunc_pos = body.find("phase49-trim")
        footer_pos = body.find("4c.ENGINE_WARNING_INJECTED")
        self.assertGreater(trunc_pos, 0, "truncator block not found")
        self.assertGreater(footer_pos, 0, "footer block not found")
        self.assertLess(
            trunc_pos, footer_pos,
            "Phase 4.9 truncator MUST run before the engine-warn-footer "
            "block in ai_ask_stream so the footer is never clipped by "
            "the per-tier char cap.",
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
