"""Phase 4.7 T016 — RUNTIME context-diet invariant tests.

Pre-Phase-4.7 the user-turn (msg[2]) was 116K chars / ~29K tokens.
ChatGPT achieves the same Vedic answer with <2K tokens. The context-
diet helpers (`_slim_locked_facts_for_narrative`,
`_slim_intel_for_narrative`, `_slim_transit_for_narrative`) drop the
17 Sprint-19+ engine dumps + raw transit degrees + KP cuspal table
in narrative mode while preserving the core allowlist needed for the
3-5 sentence FUSED combo verdict.

These tests intercept `chat.completions.create` and assert the
EFFECTIVE prompt size + content respects the diet. They mirror the
runtime-invariant pattern from `test_phase47_runtime_invariants.py`
to catch silent regressions (Phase 4.6's broken Rule N gate showed
that source-string tests are insufficient).
"""

from __future__ import annotations

import json
import os
import sys
import unittest
from types import SimpleNamespace
from unittest.mock import patch

os.environ.setdefault("NARRATIVE_MODE", "1")

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


class _FakeChoice:
    def __init__(self, content: str):
        self.message = SimpleNamespace(content=content, role="assistant")
        self.finish_reason = "stop"


class _FakeResp:
    def __init__(self, content: str):
        self.choices = [_FakeChoice(content)]


class _CaptureClient:
    """Captures every chat.completions.create invocation and returns a
    canned reply so post-processing keeps running."""

    def __init__(self) -> None:
        self.calls: list[dict] = []
        outer = self

        class _FakeCompletions:
            def create(self, **kwargs):  # noqa: D401
                outer.calls.append({
                    "messages": kwargs.get("messages") or [],
                    "model": kwargs.get("model"),
                })
                if kwargs.get("stream"):
                    return iter([])
                return _FakeResp("Test reply.")

        class _FakeChat:
            def __init__(self):
                self.completions = _FakeCompletions()

        self.chat = _FakeChat()


def _load_user21_chart() -> dict:
    from flask_app import app, db, User                # noqa: WPS433
    with app.app_context():
        u = db.session.get(User, 21)
        chart = u.kundli.chart_data
        if isinstance(chart, str):
            chart = json.loads(chart)
        return chart


# ────────────────────────────────────────────────────────────────────────────
# UNIT TESTS — slim functions in isolation
# ────────────────────────────────────────────────────────────────────────────

class SlimLockedFactsUnit(unittest.TestCase):
    """Direct unit tests on `_slim_locked_facts_for_narrative` with crafted
    fixtures — no full pipeline."""

    @classmethod
    def setUpClass(cls):
        import openai_helper as oh
        cls.oh = oh

    def test_drops_sprint_engine_section(self):
        """A ▸ section NOT in the allowlist is dropped along with its
        indented sub-lines."""
        src = (
            "▸ LAGNA: Sagittarius\n"
            "▸ SARVASHTAKAVARGA (SAV) per house — total 337/337:\n"
            "   H1: 28  H2: 31  H3: 25\n"
            "   H4: 30  H5: 27\n"
            "▸ MOON SIGN (Rashi): Leo\n"
        )
        out = self.oh._slim_locked_facts_for_narrative(src)
        self.assertIn("LAGNA: Sagittarius", out)
        self.assertIn("MOON SIGN (Rashi): Leo", out)
        self.assertNotIn("SARVASHTAKAVARGA", out)
        self.assertNotIn("H1: 28", out)
        self.assertNotIn("H4: 30", out)

    def test_drops_double_dash_subblocks(self):
        """── Sprint-XX engine sub-block headers always drop in narrative
        mode."""
        src = (
            "▸ LAGNA: Sagittarius\n"
            "── KP DEEP (Sprint 25) ──\n"
            "    cuspal sub-lord 1: Mars\n"
            "    cuspal sub-lord 2: Venus\n"
            "▸ CURRENT DASHA: Rahu Mahadasha → Rahu Antardasha\n"
        )
        out = self.oh._slim_locked_facts_for_narrative(src)
        self.assertIn("LAGNA", out)
        self.assertIn("CURRENT DASHA", out)
        self.assertNotIn("KP DEEP", out)
        self.assertNotIn("cuspal sub-lord", out)

    def test_keeps_allowlisted_section_with_sublines(self):
        """Allowlisted ▸ sections keep their indented sub-lines."""
        src = (
            "▸ PLANET STRENGTHS:\n"
            "   Sun      WEAK     (Capricorn H2 — 43%)\n"
            "   Moon     WEAK     (Leo H9 — 36%)\n"
            "   Mars     WEAK     (Scorpio H12 — 44%)\n"
            "▸ EXTENDED BALA (BPHS sub-calculations beyond basic Shadbala):\n"
            "   Some bala line 1\n"
            "   Some bala line 2\n"
        )
        out = self.oh._slim_locked_facts_for_narrative(src)
        self.assertIn("Sun      WEAK", out)
        self.assertIn("Moon     WEAK", out)
        self.assertIn("Mars     WEAK", out)
        self.assertNotIn("EXTENDED BALA", out)
        self.assertNotIn("Some bala line", out)

    def test_topic_specific_upapada_for_marriage(self):
        """For love/marriage topic, UPAPADA LAGNA is added to allowlist."""
        src = (
            "▸ LAGNA: Sagittarius\n"
            "▸ UPAPADA LAGNA (UL = A12 — Jaimini marriage signature):\n"
            "   ▸ UL sign: Leo  (lord Sun in Capricorn — 6th from UL)\n"
        )
        out_marriage = self.oh._slim_locked_facts_for_narrative(src, topic="marriage")
        self.assertIn("UPAPADA LAGNA", out_marriage)

        out_love = self.oh._slim_locked_facts_for_narrative(src, topic="love")
        self.assertIn("UPAPADA LAGNA", out_love)

        # Other topics drop UPAPADA
        out_career = self.oh._slim_locked_facts_for_narrative(src, topic="career")
        self.assertNotIn("UPAPADA LAGNA", out_career)

    def test_indented_arrow_lines_treated_as_subline_not_header(self):
        """`   ▸ NOW: Rahu Pratyantar...` (indented ▸) is a sub-line under
        ▸ PRATYANTAR, NOT a new section. Must pass through when parent
        section is kept."""
        src = (
            "▸ PRATYANTAR (sub-period under Rahu MD → Rahu AD):\n"
            "   ▸ NOW: Rahu Pratyantar (2026-01-03 → 2026-05-30)\n"
            "   ▸ NEXT pratyantars (month-precision timing windows):\n"
            "      • Jupiter (2026-05-30 → 2026-10-09)\n"
        )
        out = self.oh._slim_locked_facts_for_narrative(src)
        self.assertIn("NOW: Rahu Pratyantar", out)
        self.assertIn("Jupiter (2026-05-30", out)

    def test_empty_input_returns_empty(self):
        self.assertEqual(self.oh._slim_locked_facts_for_narrative(""), "")
        self.assertEqual(self.oh._slim_locked_facts_for_narrative(None), None)


class SlimIntelUnit(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import openai_helper as oh
        cls.oh = oh

    def test_drops_raw_transit_degree_block(self):
        """The 'Current transits today, sidereal Lahiri' raw-degree block
        is removed; structural intel is preserved."""
        src = (
            "DERIVED CHART INTELLIGENCE (pre-computed — use these as facts):\n"
            "  Lagna: Sagittarius\n"
            "  Planet status:\n"
            "    Sun: Capricorn H2 [enemy-sign] aspects H8\n"
            "  House-lord placements: H1→Jupiter sits in H7\n"
            "\n"
            "Current transits (today, sidereal Lahiri, UTC 2026-04-28 16:46):\n"
            "  Sun: 14.18° Aries\n"
            "  Moon: 159.82° Virgo\n"
            "  Mars: 350.38° Pisces\n"
            "\n"
            "next-block-line\n"
        )
        out = self.oh._slim_intel_for_narrative(src)
        self.assertIn("Lagna: Sagittarius", out)
        self.assertIn("Planet status", out)
        self.assertIn("House-lord placements", out)
        self.assertNotIn("Current transits", out)
        self.assertNotIn("14.18° Aries", out)
        self.assertNotIn("159.82° Virgo", out)


class SlimTransitUnit(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import openai_helper as oh
        cls.oh = oh

    def test_drops_entire_standalone_transit_block(self):
        """Phase 4.7 T016 — `_slim_transit_for_narrative` returns "" for
        the standalone transit block in narrative mode. The locked-facts
        allowlist already retains the structural CURRENT TRANSITS summary
        (slow-planet sign + house mapping); the standalone block leaks
        raw degrees + 'sidereal Lahiri, UTC' which biases the model
        toward enumeration/pseudo-precision instead of human language.
        """
        src = (
            "Current transits (today, sidereal Lahiri, UTC 2026-04-28 17:11):\n"
            "  Sun:     38.21° Aries\n"
            "  Moon:    158.92° Virgo\n"
            "  Jupiter: 84.38° Gemini\n"
            "  Saturn:  344.66° Pisces\n"
            "  Rahu:    315.10° Aquarius\n"
            "  Ketu:    135.10° Leo\n"
        )
        out = self.oh._slim_transit_for_narrative(src)
        self.assertEqual(out, "", "standalone transit block should be empty")

    def test_returns_empty_input_unchanged(self):
        """Empty input must round-trip as-is (preserves the prior
        contract that callers always get a string, never None)."""
        self.assertEqual(self.oh._slim_transit_for_narrative(""), "")
        self.assertEqual(self.oh._slim_transit_for_narrative(None), None)


# ────────────────────────────────────────────────────────────────────────────
# RUNTIME INTEGRATION TESTS — full _build_messages → assert effective prompt
# ────────────────────────────────────────────────────────────────────────────

class Phase47ContextDietRuntime(unittest.TestCase):
    """Full pipeline: ai_ask → intercepted client → assert msg[2] respects
    the diet. Mirrors Phase 4.7 Fix-1/Fix-2 runtime invariant pattern."""

    QUESTION = ("mera abhi jo dasha chal raha he kya mera love ho sakta "
                "he abhi kisi ke sath")

    # Heavy Sprint-19+ section headers that MUST be absent from msg[2] in
    # narrative mode. We test for the bullet-prefixed DATA section header
    # ("▸ X" or "X (...):") rather than the bare label, because some labels
    # legitimately appear in retained anti-bias rule text (e.g. Rule O for
    # love/marriage topic still references "JAIMINI ARUDHA PADAS" in
    # guard-rail prose). The bullet "▸ " is the unambiguous data-section
    # signature.
    BANNED_ENGINE_SECTIONS = (
        "▸ SARVASHTAKAVARGA",
        "▸ BHAVA BALA",
        "▸ EXTENDED BALA",
        "▸ JAIMINI CHARA KARAKAS",
        "D2 HORA",
        "D3 DREKKANA",
        "D7 SAPTAMSA",
        "D12 DWADASAMSA",
        "D16 SHODASAMSA",
        "D20 VIMSAMSA",
        "D24 CHATURVIMSAMSA",
        "D27 BHAMSA",
        "D30 TRIMSAMSA",
        "D40 KHAVEDAMSA",
        "D45 AKSHAVEDAMSA",
        "D60 SHASHTYAMSA",
        "ASHTAKAVARGA DEEP",
        "TRANSIT DEEP",
        "KP DEEP",
        "JAIMINI RASHI DRISHTI",
        "AVASHTAS",
        "PHASE Q MUHURTA",
        "PHASE R PANCHANG",
        "PHASE S NUMEROLOGY",
        "ASTRO-VASTU ENGINE",
        "MEDICAL ASTROLOGY ENGINE",
        "FINANCIAL ASTROLOGY ENGINE",
        "REMEDIES DEEP ENGINE",
        "ASTROCARTOGRAPHY ENGINE",
        "MODERN CONTEXT REFRAME ENGINE",
        "TIMING ENGINE (Sprint-51",
        "▸ JAIMINI ARUDHA PADAS",
        "CLASSICAL YOGAS (Sprint-19",
        "EXTRA CLASSICAL YOGAS",
        "DEEP DOSHAS (Sprint-20",
        "EXTRA DASHAS (Sprint-21",
        "PHASE C MISSING YOGAS",
        "PHASE E DASHAS",
        "PHASE F PER-VARGA",
        "PHASE H TRANSITS-ECLIPSES",
        "KP PHASE-I",
        "PHASE J TAJIK",
        "PHASE L SPECIAL LAGNAS",
        "PHASE M SAHAMS",
        "PHASE N NADI",
        "PHASE O LAL KITAB",
        "PHASE P COMPATIBILITY",
        "VARGOTTAMA MATRIX",
        "SHADVARGA BALA",
        "ARGALA / VIRODHARGALA",
    )

    # Allowlisted essentials that MUST remain in msg[2] in narrative mode
    REQUIRED_ESSENTIALS = (
        "▸ LAGNA:",
        "▸ MOON SIGN",
        "▸ SUN SIGN:",
        "▸ NAKSHATRA:",
        "▸ PLANET STRENGTHS:",
        "▸ ACTIVE DOSHAS:",
        "▸ CURRENT DASHA:",
        "▸ DASHA WINDOW:",
        "▸ HOUSE-LORD PLACEMENTS:",
        "DEVOTEE'S BIRTH CHART:",
    )

    @classmethod
    def setUpClass(cls):
        import openai_helper as oh
        cls.oh = oh
        cls.chart = _load_user21_chart()

        client = _CaptureClient()
        with patch.object(cls.oh, "_get_client", lambda: client):
            try:
                cls.oh.ai_ask(
                    question=cls.QUESTION, kundli=cls.chart, lang="hi",
                    reply_idx=0, birth=None, history=None,
                    preferred_language="hi",
                )
            except Exception:
                pass
        cls.client = client
        if not client.calls:
            raise unittest.SkipTest("ai_ask did not invoke the client")
        # ai_ask makes 2-3 calls: intent classifier (1 user msg), optional
        # follow-up planner, and the MAIN answer (system+system+user+system).
        # Pick the main-answer call by selecting the one with >= 3 messages
        # AND the longest user content. Fall back to longest if structure
        # differs.
        def _user_chars(call):
            return sum(
                len(m["content"]) for m in call["messages"] if m["role"] == "user"
            )
        main_calls = [c for c in client.calls if len(c["messages"]) >= 3]
        if not main_calls:
            main_calls = client.calls
        main_call = max(main_calls, key=_user_chars)
        cls.messages = main_call["messages"]
        cls.user_msg = next(
            (m["content"] for m in cls.messages if m["role"] == "user"),
            "",
        )

    def test_user_msg_under_8k_tokens(self):
        """Target: msg[2] < 8K tokens. Conservative ratio 1 token = 4 chars
        for English-heavy prompt → 32K char ceiling."""
        char_count = len(self.user_msg)
        approx_tokens = char_count // 4
        self.assertLess(
            char_count, 32_000,
            f"msg[2] exceeded 32K char ceiling: {char_count:,} chars "
            f"(~{approx_tokens:,} tokens). Context diet not slimming enough.",
        )

    def test_total_prompt_under_64k_chars(self):
        """All 4 messages combined should stay under 64K chars (~16K tokens)
        — half of pre-Phase-4.7 baseline of 141K."""
        total = sum(len(m["content"]) for m in self.messages)
        self.assertLess(
            total, 64_000,
            f"Total prompt exceeded 64K chars: {total:,}",
        )

    def test_no_sprint_engine_sections(self):
        """None of the 17 Sprint-19+ engine section headers may appear in
        msg[2] — they're the heart of the context diet."""
        present = [s for s in self.BANNED_ENGINE_SECTIONS if s in self.user_msg]
        self.assertEqual(
            present, [],
            f"{len(present)} Sprint-19+ engine sections still in msg[2]: {present}",
        )

    def test_essentials_preserved(self):
        """The narrative-mode allowlist must still appear — model needs the
        core lagna / moon / dasha / strengths / dosh / house-lords to give
        a fused combo verdict."""
        missing = [e for e in self.REQUIRED_ESSENTIALS if e not in self.user_msg]
        self.assertEqual(
            missing, [],
            f"{len(missing)} essentials missing from msg[2]: {missing}",
        )

    def test_kp_block_dropped_in_narrative(self):
        """The standalone _kp_context() data block must be dropped in
        narrative mode. The block's unambiguous signature is the header
        line `KP (Krishnamurti Paddhati) cross-check:` (set in
        openai_helper.py line 1553). Some retained anti-bias rule text
        (Rule N advisory, Rule 3 KP advisory, Rule 11 anti-invention)
        legitimately uses the words 'KP', 'cusp', and 'sub-lord' to
        TELL the model not to surface them — so the test checks for the
        data-block header signature, not those generic words.
        """
        self.assertNotIn(
            "KP (Krishnamurti Paddhati) cross-check:", self.user_msg,
            "Standalone _kp_context() data block leaked into "
            "narrative-mode user turn — kp_block should be empty per "
            "Phase 4.7 Fix 1+2.",
        )

    def test_raw_transit_degrees_dropped(self):
        """The standalone transit block's 'Current transits (today,
        sidereal Lahiri, UTC ...)' raw-degree dump should be removed —
        the structural transit summary in CURRENT TRANSITS (locked-facts
        allowlist) already covers it for narrative mode."""
        self.assertNotIn(
            "sidereal Lahiri, UTC", self.user_msg,
            "Raw transit-degree dump should be removed by "
            "_slim_transit_for_narrative() (which now returns '' in "
            "narrative mode)",
        )

    def test_engine_diet_telemetry_present_in_source(self):
        """Phase 4.7 T016 telemetry log must exist in source so any future
        regression that bypasses the diet is observable."""
        with open(self.oh.__file__, "r", encoding="utf-8") as f:
            src = f.read()
        self.assertIn(
            "Phase 4.7 T016: narrative-mode context diet", src,
            "Diet telemetry log message removed — silent regressions are "
            "now possible.",
        )


class Phase47ContextDietPreservation(unittest.TestCase):
    """When NARRATIVE_MODE is OFF, the legacy 116K block must reappear —
    the diet is a feature flag, not a permanent removal."""

    def test_slim_helpers_only_run_when_narrative_mode(self):
        """The slim invocations are wrapped in `if _NARRATIVE_MODE:` —
        confirm the source still has the gate so NARRATIVE_MODE=0 reverts."""
        import openai_helper as oh
        with open(oh.__file__, "r", encoding="utf-8") as f:
            src = f.read()
        self.assertIn(
            "if _NARRATIVE_MODE:\n        _orig_lf_chars = len(locked_facts_str)",
            src,
            "Diet block gate signature changed — NARRATIVE_MODE=0 may no "
            "longer revert correctly.",
        )
        self.assertIn(
            "_slim_locked_facts_for_narrative(locked_facts_str, topic=topic)",
            src,
        )


class Phase47DeadRuleStripRuntime(unittest.TestCase):
    """Architect-flagged: assert that Rules F/G/I/J/K (and conditionally O)
    are actually absent from the effective msg[2] in narrative mode. The
    paragraph-strip is only ~3K chars so it does not show up in size-only
    invariants — needs explicit content assertions."""

    @classmethod
    def setUpClass(cls):
        os.environ.setdefault("NARRATIVE_MODE", "1")
        import openai_helper as oh
        cls.oh = oh

    def _capture_user(self, question: str) -> str:
        from unittest.mock import patch
        chart = _load_user21_chart()
        client = _CaptureClient()
        with patch.object(self.oh, "_get_client", lambda: client):
            try:
                self.oh.ai_ask(
                    question=question, kundli=chart, lang="hi",
                    reply_idx=0, birth=None, history=None,
                    preferred_language="hi",
                )
            except Exception:
                pass
        main_calls = [c for c in client.calls if len(c["messages"]) >= 3]
        mc = max(main_calls, key=lambda c: sum(
            len(m["content"]) for m in c["messages"] if m["role"] == "user"
        ))
        return next(m["content"] for m in mc["messages"] if m["role"] == "user")

    # Each Rule's distinctive prefix line — none of these substrings should
    # appear in the user turn after the dead-rule strip in narrative mode.
    BANNED_RULE_PREFIXES_ALL_TOPICS = (
        "🛡️ ASHTAKAVARGA (Rule F):",
        "🛡️ ASPECTS (Rule G):",
        "🛡️ KARAKAS (Rule I):",
        "🛡️ BHAVA BALA (Rule J):",
        "🛡️ DIVISIONAL CHARTS (Rule K):",
    )
    RULE_O_PREFIX = "🛡️ JAIMINI ARUDHA / UPAPADA (Rule O):"

    def test_rules_F_G_I_J_K_stripped_in_narrative(self):
        """Architect Action #2: explicit runtime assertion that the 5
        always-stripped rules are gone from msg[2]."""
        user = self._capture_user(
            "career mein ab kya scope hai aage"
        )
        present = [r for r in self.BANNED_RULE_PREFIXES_ALL_TOPICS if r in user]
        self.assertEqual(
            present, [],
            f"{len(present)} dead-code rule paragraph(s) leaked into "
            f"narrative-mode user turn — dead-rule strip "
            f"(openai_helper.py ~3067-3129) regressed: {present}",
        )

    def test_rule_O_dropped_for_non_love_marriage_topic(self):
        """Rule O (UPAPADA) is dropped for non-love/marriage topics
        because UPAPADA LAGNA data is also dropped from locked-facts
        for those topics. Use a clearly non-love/marriage question."""
        user = self._capture_user("paisa kab milega career mein")
        self.assertNotIn(
            self.RULE_O_PREFIX, user,
            "Rule O should be stripped for career/finance topics "
            "(no UPAPADA data block in narrative-mode locked-facts "
            "for non-love/marriage topics)",
        )

    def test_rule_O_retained_for_love_topic(self):
        """Rule O (UPAPADA) is RETAINED for love topic because UPAPADA
        LAGNA data IS kept in locked-facts for that topic via the
        topic-specific allowlist. NOTE: marriage topic uses a separate
        deterministic marriage-engine template (Phase 4.6) that bypasses
        the regular rule injection — this test uses a love question
        (not marriage) to exercise the regular `_build_messages` path
        where Rule O retention matters."""
        user = self._capture_user(
            "mera abhi jo dasha chal raha he kya mera love ho sakta "
            "he abhi kisi ke sath"
        )
        self.assertIn(
            self.RULE_O_PREFIX, user,
            "Rule O must be retained for love topic — UPAPADA data is "
            "allowlist-kept for love/marriage topics, so the model "
            "needs the citation guidance.",
        )

    def test_drift_detection_telemetry_present(self):
        """Architect Action #1: loud-fail drift detection must exist in
        source so silent regressions (text reindented, emoji changed,
        rule renamed) are surfaced at runtime."""
        with open(self.oh.__file__, "r", encoding="utf-8") as f:
            src = f.read()
        self.assertIn(
            "Phase 4.7 T016 DRIFT WARNING", src,
            "Drift-detection telemetry removed — silent dead-rule strip "
            "regressions are now possible.",
        )


if __name__ == "__main__":
    unittest.main()
