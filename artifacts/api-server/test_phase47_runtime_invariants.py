"""Phase 4.7 — RUNTIME invariant tests.

Architect-flagged need (Apr 28): Phase 4.5/4.6 tests are static source-
string checks (`assertIn` on file contents). These cannot catch silent
no-ops like Phase 4.6's broken Rule N gate (literal mismatch on the
wrong variable).

These tests intercept the OpenAI `chat.completions.create` call and
assert the EFFECTIVE message stack — what the model actually sees —
respects the narrative-mode contract.
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
    """Stand-in for the OpenAI client. Captures every chat.completions.create
    invocation and returns a canned reply so post-processing keeps running."""

    def __init__(self) -> None:
        self.calls: list[dict] = []
        # Build the chained .chat.completions.create surface the helper uses.
        outer = self

        class _FakeCompletions:
            def create(self, **kwargs):  # noqa: D401 — match SDK signature
                outer.calls.append({
                    "messages": kwargs.get("messages") or [],
                    "model": kwargs.get("model"),
                    "stream": bool(kwargs.get("stream")),
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


class Phase47BannedNarrativeSubstrings(unittest.TestCase):
    """In NARRATIVE_MODE, the EFFECTIVE prompt sent to OpenAI MUST NOT
    contain any of the loud MANDATORY-citation strings that compete with
    the 3-5 sentence FUSED combo verdict shape.

    These tests fail loudly if Phase 4.7 (or any future change) silently
    regresses, instead of letting the bug ship like Phase 4.6 did."""

    QUESTION = ("mera abhi jo dasha chal raha he kya mera love ho sakta "
                "he abhi kisi ke sath")

    BANNED_IN_NARRATIVE_MODE = (
        # Fix-1 (FINAL REMINDERS gate)
        "KP citation is MANDATORY this turn",
        "Skipping this is a hallucination-class error",
        "MANDATORY citations sit ABOVE",
        "trim the prose, NOT the citations",
        "you MUST cite the 7L's D9 placement",
        "you MUST cite the 10L's D10 placement",
        # Fix-2 (Rule N gate moved to `user`)
        "Rule N — MANDATORY citation",
        "you MUST include one natural KP citation sentence",
        "weave ONE natural KP citation alongside Vedic reasoning",
    )

    REQUIRED_IN_NARRATIVE_MODE = (
        "Rule N — NARRATIVE-MODE: ADVISORY only",
        "These reminders are ADVISORY",
        "BACKGROUND",
    )

    @classmethod
    def setUpClass(cls):
        import openai_helper as oh
        cls.oh = oh
        cls.chart = _load_user21_chart()

    def _capture_messages(self) -> list[dict]:
        client = _CaptureClient()
        with patch.object(self.oh, "_get_client", lambda: client):
            try:
                self.oh.ai_ask(
                    question=self.QUESTION, kundli=self.chart, lang="hi",
                    reply_idx=0, birth=None, history=None,
                    preferred_language="hi",
                )
            except Exception:
                # Post-processing may complain about the canned reply —
                # that's fine. We only need the captured prompt.
                pass
        if not client.calls:
            self.fail("ai_ask did not call chat.completions.create — "
                      "rule-engine fallback may be active")
        # ai_ask may chain multiple calls (router, validator, narrator).
        # The narrator call is the LAST one with the largest payload —
        # that's the one the user sees.
        narrator_call = max(
            client.calls,
            key=lambda c: sum(len(m.get("content") or "") for m in c["messages"]),
        )
        return narrator_call["messages"]

    def setUp(self):
        self.msgs = self._capture_messages()
        self.combined = "\n".join(m.get("content") or "" for m in self.msgs)

    # ── Banned substrings ────────────────────────────────────────────
    def test_no_banned_substrings(self):
        for needle in self.BANNED_IN_NARRATIVE_MODE:
            with self.subTest(banned=needle):
                count = self.combined.count(needle)
                self.assertEqual(
                    count, 0,
                    f"Phase 4.7 invariant violated: '{needle}' appears "
                    f"{count}× in the effective prompt — narrative-mode "
                    f"gate did not fire (silent no-op like Phase 4.6).",
                )

    # ── Required replacement substrings ──────────────────────────────
    def test_required_advisory_substrings_present(self):
        for needle in self.REQUIRED_IN_NARRATIVE_MODE:
            with self.subTest(required=needle):
                self.assertIn(
                    needle, self.combined,
                    f"Phase 4.7 advisory replacement '{needle}' missing — "
                    f"the narrative-mode swap text didn't reach the model.",
                )

    # ── KP-paddhati template guard ───────────────────────────────────
    def test_kp_paddhati_template_only_in_bad_example(self):
        """The exact template phrase 'KP paddhati se bhi {N}th cusp ka
        sub-lord {planet} hai jo {CONFIRMS/PARTIAL/DENIES} karta hai'
        must NOT appear as an instruction. The only allowed occurrence
        is inside the BAD-example block ('✗ KP paddhati se bhi …'),
        which TELLS the model what to AVOID."""
        # Allowed locations only contain it as a NEGATIVE example.
        instruction_phrasings = (
            "weave ONE natural KP citation",
            "weave ONE natural sentence: 'KP paddhati",
            "State whether KP confirms or modifies",
        )
        for phrase in instruction_phrasings:
            with self.subTest(phrase=phrase):
                self.assertNotIn(
                    phrase, self.combined,
                    f"Phase 4.7: imperative KP-cite phrasing '{phrase}' "
                    f"is back — narrative-mode guard regressed.",
                )

    # ── Phase 4.6 body still fires ───────────────────────────────────
    def test_narrative_body_discipline_still_fires(self):
        """Phase 4.6 narrative body (BAD/GOOD examples + TOPIC FIDELITY)
        must still ride along — Phase 4.7 only neutralised the loud
        MANDATORY signals, not the body discipline."""
        self.assertIn("PHASE 4.6 — COMBO-FUSION DISCIPLINE", self.combined)
        self.assertIn("TOPIC FIDELITY", self.combined)

    # ── Supertype contract still installed ───────────────────────────
    def test_narrative_answer_supertype_contract_installed(self):
        self.assertIn("NARRATIVE_ANSWER", self.combined)


class Phase47NonNarrativeModePreserved(unittest.TestCase):
    """When NARRATIVE_MODE is OFF (NARRATIVE_MODE=0), the legacy
    MANDATORY-citation behaviour MUST be preserved — the gate is a
    feature flag, not a deletion."""

    QUESTION = ("mera abhi jo dasha chal raha he kya mera love ho sakta "
                "he abhi kisi ke sath")

    @classmethod
    def setUpClass(cls):
        cls.chart = _load_user21_chart()

    def test_legacy_mandatory_lead_present_in_source(self):
        """Source still contains the MANDATORY lead — gate only swaps it
        in narrative mode, doesn't delete it. (Static source check —
        cheap regression guard.)"""
        import openai_helper as oh
        with open(oh.__file__, "r", encoding="utf-8") as fh:
            src = fh.read()
        self.assertIn(
            "🛡️ KP CROSS-CHECK (Rule N — MANDATORY citation)", src,
            "Phase 4.7 must KEEP the legacy MANDATORY lead in source — "
            "it's still active when NARRATIVE_MODE=0.",
        )
        # Also assert the else-branch in FINAL REMINDERS still has the
        # MANDATORY language for non-narrative mode.
        self.assertIn(
            "KP citation is MANDATORY this turn", src,
            "Phase 4.7 must KEEP the FINAL REMINDERS MANDATORY KP line "
            "in the NARRATIVE_MODE=0 else-branch.",
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
