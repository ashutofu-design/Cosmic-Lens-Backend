"""Phase 4.8 — OUTPUT DISCIPLINE tests.

After Phase 4.7 trimmed the INPUT to ~25K chars, the model still emitted
6-10 line answers with date ranges, pratyantar names, and full dasha
breakdowns. The user wants 1-2 sentence narrative answers in the format
`[Verdict] → [1 reason]`.

Phase 4.8 adds three layers:
  T017 — drop `▸ PRATYANTAR` and `▸ DASHA WINDOW:` from the
         dasha-block allowlist (`_LF_KEEP_PREFIXES`).
  T018 — replace Rule 10's 100-140 word default with a 1-2 sentence
         HARD CAP in narrative mode.
  T019 — post-generation truncator (`_phase48_narrative_truncate`)
         that strips dates + pratyantar sentences and caps at
         2 sentences / 280 chars (skips date-stripping for timing Qs).

T017 + T018 are verified at runtime (the EFFECTIVE prompt seen by the
model). T019 is verified via direct unit tests against the helper —
calling through `ai_ask` would mix in unrelated post-processors.
"""

from __future__ import annotations

import json
import os
import re
import sys
import unittest
from types import SimpleNamespace
from unittest.mock import patch

os.environ.setdefault("NARRATIVE_MODE", "1")

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


# ── Shared fakes (same shape as Phase 4.7 invariant tests) ──────────────


class _FakeChoice:
    def __init__(self, content: str):
        self.message = SimpleNamespace(content=content, role="assistant")
        self.finish_reason = "stop"


class _FakeResp:
    def __init__(self, content: str):
        self.choices = [_FakeChoice(content)]


class _CaptureClient:
    def __init__(self, canned_reply: str = "Test reply.") -> None:
        self.calls: list[dict] = []
        self._canned = canned_reply
        outer = self

        class _FakeCompletions:
            def create(self, **kwargs):
                outer.calls.append({
                    "messages": kwargs.get("messages") or [],
                    "model": kwargs.get("model"),
                    "stream": bool(kwargs.get("stream")),
                })
                if kwargs.get("stream"):
                    return iter([])
                return _FakeResp(outer._canned)

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


# ── T017 — Allowlist source check ───────────────────────────────────────


class Phase48AllowlistDropsPratyantar(unittest.TestCase):
    """T017: the `_LF_KEEP_PREFIXES` tuple no longer keeps the
    `▸ PRATYANTAR` and `▸ DASHA WINDOW:` lines. Source-level check
    using the unique unicode arrow + label so we don't depend on a
    fragile paren-balanced extractor."""

    SOURCE_PATH = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "openai_helper.py",
    )

    @classmethod
    def setUpClass(cls):
        with open(cls.SOURCE_PATH, "r", encoding="utf-8") as fh:
            cls.src = fh.read()

    def _kept_lines(self) -> list[str]:
        """Return the literal string entries of _LF_KEEP_PREFIXES — the
        substring after each `"▸ ` up to the next `"`."""
        # Find _LF_KEEP_PREFIXES = ( ... ) by line scanning instead of
        # paren balancing (the tuple has comments and nested parens).
        lines = self.src.splitlines()
        in_block = False
        kept: list[str] = []
        for line in lines:
            if line.strip().startswith("_LF_KEEP_PREFIXES"):
                in_block = True
                continue
            if in_block:
                # End on the lone `)` that closes the tuple. Continue
                # past comment lines and blank lines.
                stripped = line.strip()
                if stripped.startswith(")") and not stripped.startswith(")#"):
                    break
                # SKIP commented lines — they may quote dropped entries
                # like:   # Phase 4.8 T017 — DROPPED: "▸ DASHA WINDOW:"
                if stripped.startswith("#"):
                    continue
                # Each entry like:  "▸ CURRENT DASHA: ",   # comment
                # Use the part of the line BEFORE any inline `#` comment.
                code_part = line.split("#", 1)[0]
                m = re.search(r'"(▸ [^"]+)"', code_part)
                if m:
                    kept.append(m.group(1))
        return kept

    def test_extractor_finds_entries(self):
        kept = self._kept_lines()
        self.assertGreater(
            len(kept), 0,
            "Phase 4.8 T017 test scaffolding broke — no '▸ ...' "
            "literals found between _LF_KEEP_PREFIXES = ( and the "
            "closing ).",
        )

    def test_pratyantar_dropped(self):
        kept = self._kept_lines()
        for entry in kept:
            self.assertFalse(
                entry.upper().startswith("▸ PRATYANTAR"),
                f"Phase 4.8 T017: '▸ PRATYANTAR' is still in the "
                f"allowlist (entry={entry!r}); narrative answers will "
                f"continue to leak pratyantar date ranges.",
            )

    def test_dasha_window_dropped(self):
        kept = self._kept_lines()
        for entry in kept:
            self.assertFalse(
                entry.upper().startswith("▸ DASHA WINDOW"),
                f"Phase 4.8 T017: '▸ DASHA WINDOW' is still in the "
                f"allowlist (entry={entry!r}); narrative answers will "
                f"keep emitting full dasha date dumps.",
            )

    def test_current_dasha_retained(self):
        """Just the lord names (MD-AD) must stay — the model still
        needs to know which lords are running, just not the calendar
        window."""
        kept = self._kept_lines()
        self.assertTrue(
            any(e.upper().startswith("▸ CURRENT DASHA") for e in kept),
            f"Phase 4.8 T017: removed too much — '▸ CURRENT DASHA' was "
            f"dropped. The model still needs MD-AD lord names. "
            f"Kept entries: {kept!r}",
        )


# ── T018 + runtime: HARD CAP rule reaches the model ─────────────────────


import openai_helper as _oh_p50

@unittest.skipIf(
    _oh_p50._phase50_minimal_prompt_enabled(),
    "Phase 5.0 minimal-prompt path removes the in-prompt HARD CAP rule "
    "(the model decides answer length naturally, not via tier hints). "
    "Re-enabled when PHASE50_MINIMAL_PROMPT=0."
)
class Phase48HardCapInPrompt(unittest.TestCase):
    """T018 runtime check: the actual user-turn message in narrative mode
    contains the new 1-2 sentence HARD CAP and NOT the old 100-140 word
    default. Also verifies T017's data-side effect: no DATE-BEARING
    pratyantar or ISO date ranges leak into the user turn (the literal
    word 'Pratyantar' may still appear in instructional rules — we only
    care about actual data leaks)."""

    QUESTION = ("mera abhi jo dasha chal raha he kya mera love ho sakta "
                "he abhi kisi ke sath")

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
                pass
        if not client.calls:
            self.fail("ai_ask did not call chat.completions.create")
        narrator_call = max(
            client.calls,
            key=lambda c: sum(len(m.get("content") or "") for m in c["messages"]),
        )
        return narrator_call["messages"]

    def setUp(self):
        self.msgs = self._capture_messages()
        self.combined = "\n".join(m.get("content") or "" for m in self.msgs)

    def test_old_140w_default_removed(self):
        # The OLD default sentence mentions "100 to 140 WORDS". After
        # T018 it should be replaced.
        self.assertNotIn(
            "100 to 140 WORDS", self.combined,
            "Phase 4.8 T018: Rule 10 100-140 word default still present "
            "in narrative-mode prompt — the replace() did not fire. The "
            "model will keep emitting 3-paragraph answers.",
        )

    def test_new_hard_cap_present(self):
        self.assertIn(
            "NARRATIVE-MODE HARD CAP", self.combined,
            "Phase 4.8 T018: new HARD CAP rule text missing — model has "
            "no instruction to keep answers to 1-2 sentences.",
        )
        self.assertIn(
            "1 to 2", self.combined,
            "Phase 4.8 T018: HARD CAP rule must spell out '1 to 2' "
            "sentences for the model.",
        )

    def test_no_dated_pratyantar_in_user_turn(self):
        """T017 data-side effect: no 'Pratyantar (YYYY-MM-DD ...)'
        leaks. (The bare word 'Pratyantar' may still appear in the
        rule-instruction text — that's fine; the user-visible bug is
        the dated data dump.)"""
        user_turn = self.msgs[-1].get("content") or ""
        # Specifically: a "Pratyantar" mention followed within ~60 chars
        # by an ISO date is the bug shape.
        leaks = []
        for m in re.finditer(r"(?i)pratyantar", user_turn):
            window = user_turn[m.end():m.end() + 60]
            if re.search(r"\d{4}-\d{2}-\d{2}", window):
                leaks.append(user_turn[max(0, m.start()-20):m.end()+60])
        self.assertEqual(
            leaks, [],
            f"Phase 4.8 T017: dated 'Pratyantar (YYYY-MM-DD ...)' still "
            f"leaks into narrative-mode user turn. Leaks:\n"
            f"{chr(10).join(leaks[:3])}",
        )

    def test_no_dasha_window_iso_dates_in_user_turn(self):
        """T017 effect: the dasha block should not contain ISO date
        ranges from `▸ DASHA WINDOW:`. We look only at the dasha section
        — instructional text elsewhere may legitimately use a single
        example date, but a tight cluster of YYYY-MM-DD tokens is a
        data leak."""
        user_turn = self.msgs[-1].get("content") or ""
        all_iso = re.findall(r"\b\d{4}-\d{2}-\d{2}\b", user_turn)
        # Some example dates may appear in instructional prose; a real
        # data dump from DASHA WINDOW is many dates. Threshold = 3.
        self.assertLess(
            len(all_iso), 3,
            f"Phase 4.8 T017: {len(all_iso)} ISO date(s) leaked into "
            f"narrative-mode user turn — DASHA WINDOW or another dated "
            f"block is still being kept. First 5: {all_iso[:5]}",
        )


# ── T019 — Post-generation truncator (direct unit tests) ────────────────


class Phase48TruncatorBehaviour(unittest.TestCase):
    """T019 unit tests for `_phase48_narrative_truncate(text, question)`.
    Tested in isolation so unrelated post-processors in `ai_ask` can't
    confound the assertions."""

    LONG_LOVE_REPLY = (
        "Mahadasha Mars aur Mercury antardasha (2026-02-18 se 2026-05-01) "
        "ke dauran emotional pull strong rahega. Moon Pratyantar mein "
        "(2026-06-22 tak) ek naya connection ban sakta hai. "
        "Lekin Mars ki impulsiveness aur Rahu ki confusion ki wajah se "
        "yeh zyada tar temporary rahega. KP paddhati se 7th cusp ka "
        "sub-lord Saturn confirm karta hai. "
        "Divisional chart D9 mein bhi yeh signal milta hai. "
        "Manglik dosh ka effect bhi hai. "
        "Aap dhyan se aage badhe."
    )

    @classmethod
    def setUpClass(cls):
        import openai_helper as oh
        # Wrap in staticmethod so descriptor protocol doesn't bind
        # `self` as the first arg when accessed via instance.
        cls.trunc = staticmethod(oh._phase48_narrative_truncate)
        cls.is_timing = staticmethod(oh._phase48_is_timing_question)

    # ── Intent detection ─────────────────────────────────────────────

    def test_timing_keywords_detected(self):
        for q in (
            "shaadi kab hogi?",
            "exact date kya hai?",
            "When will I get a job?",
            "kitna time lagega?",
            "next year mein hoga?",
            "muhurat batao",
        ):
            with self.subTest(q=q):
                self.assertTrue(
                    self.is_timing(q),
                    f"Phase 4.8 T019: timing question {q!r} not "
                    f"detected — date stripping will WRONGLY fire.",
                )

    def test_non_timing_keywords_not_detected(self):
        for q in (
            "kya mera love real ya temporary rahega?",
            "Will my marriage be successful?",
            "mera career kaisa hoga?",
        ):
            with self.subTest(q=q):
                self.assertFalse(
                    self.is_timing(q),
                    f"Phase 4.8 T019: decision question {q!r} "
                    f"misclassified as timing — dates will leak.",
                )

    # ── Non-timing decision Q: aggressive trim ───────────────────────

    def test_long_dated_reply_for_decision_q(self):
        """Non-timing decision question triggers full truncator: dates
        stripped, pratyantar/antardasha sentences dropped, first 2
        sentences kept."""
        q = "kya mera love real ya temporary rahega?"
        out = self.trunc(self.LONG_LOVE_REPLY, q)

        # Hard cap: ≤ 2 sentences
        sents = [s for s in re.split(r"(?<=[.!?।])\s+", out) if s.strip()]
        self.assertLessEqual(
            len(sents), 2,
            f"Phase 4.8 T019: should cap at 2 sentences for non-timing "
            f"decision queries. Got {len(sents)}: {out!r}",
        )
        # Hard cap: ≤ 280 chars
        self.assertLessEqual(
            len(out), 280,
            f"Phase 4.8 T019: should cap at 280 chars. "
            f"Got {len(out)}: {out!r}",
        )
        # Date-shaped tokens must be gone
        self.assertEqual(
            re.findall(r"\b\d{4}-\d{2}-\d{2}\b", out), [],
            f"Phase 4.8 T019: ISO dates leaked through truncator on a "
            f"non-timing question: {out!r}",
        )
        # Pratyantar/antardasha sentences must be gone
        self.assertNotIn(
            "Pratyantar", out,
            f"Phase 4.8 T019: 'Pratyantar' leaked through truncator on "
            f"a non-timing question: {out!r}",
        )
        self.assertNotIn(
            "antardasha", out.lower(),
            f"Phase 4.8 T019: 'antardasha' leaked through truncator on "
            f"a non-timing question: {out!r}",
        )

    # ── Idempotency on already-disciplined replies ───────────────────

    def test_short_reply_is_idempotent(self):
        canned = (
            "Love ho sakta hai, lekin Mars ki impulsiveness aur Rahu ki "
            "confusion ki wajah se yeh zyada tar temporary rahega."
        )
        q = "kya mera love real ya temporary rahega?"
        out = self.trunc(canned, q)
        self.assertEqual(
            out, canned,
            f"Phase 4.8 T019 idempotency violated — short, date-free, "
            f"single-sentence reply was mutated.\nIN:  {canned!r}\n"
            f"OUT: {out!r}",
        )

    def test_two_sentence_clean_reply_is_idempotent(self):
        canned = (
            "Love ho sakta hai. Lekin confusion ki wajah se yeh "
            "temporary rahega."
        )
        q = "real ya temporary?"
        out = self.trunc(canned, q)
        self.assertEqual(
            out, canned,
            f"Phase 4.8 T019: clean 2-sentence reply mutated.\n"
            f"IN:  {canned!r}\nOUT: {out!r}",
        )

    # ── Timing question: dates survive, sentence cap still applies ──

    def test_timing_question_keeps_dates(self):
        q = "shaadi kab hogi exact date kya hai?"
        out = self.trunc(self.LONG_LOVE_REPLY, q)
        # 2-sentence cap still applies
        sents = [s for s in re.split(r"(?<=[.!?।])\s+", out) if s.strip()]
        self.assertLessEqual(
            len(sents), 2,
            f"Phase 4.8 T019: 2-sentence cap should still apply for "
            f"timing questions. Got {len(sents)}: {out!r}",
        )
        # Dates from the first 2 sentences must survive (the long reply
        # opens with two dated sentences)
        self.assertTrue(
            re.search(r"\b\d{4}-\d{2}-\d{2}\b", out),
            f"Phase 4.8 T019: dates were stripped on a timing question "
            f"({q!r}) — they ARE the answer. Got: {out!r}",
        )
        # Pratyantar/antardasha words must survive on timing Qs (the
        # user asked WHEN — sub-period names are valid context)
        self.assertTrue(
            "antardasha" in out.lower() or "Pratyantar" in out,
            f"Phase 4.8 T019: sub-period names stripped on timing Q. "
            f"Got: {out!r}",
        )

    # ── Robustness ───────────────────────────────────────────────────

    def test_empty_input_passes_through(self):
        for empty in ("", "   ", None):
            with self.subTest(input=repr(empty)):
                self.assertEqual(self.trunc(empty, "kuch bhi"), empty)

    def test_devanagari_punctuation_split(self):
        canned = (
            "प्रेम हो सकता है। लेकिन यह अस्थायी रहेगा। तीसरा वाक्य।"
        )
        out = self.trunc(canned, "kya prem hoga?")
        # First 2 sentences kept; third dropped.
        self.assertIn("प्रेम हो सकता है।", out)
        self.assertNotIn("तीसरा", out)


if __name__ == "__main__":
    unittest.main(verbosity=2)
