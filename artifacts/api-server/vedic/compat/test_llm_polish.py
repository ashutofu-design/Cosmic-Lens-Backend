"""
Phase 2.5.11.20 — Tests for vedic.compat.llm_polish

Covers:
  • Toggle-off short-circuit returns fallback verbatim
  • Fingerprint determinism + sensitivity to facts
  • Validator rejects: missing total, missing nakshatra, banned terms,
    challenges without remedy, length anomalies
  • Validator accepts well-formed output
  • Cache hit returns same dict without LLM call
  • Build_user_prompt includes both nakshatra names + manglik line
"""
from __future__ import annotations

import os
import unittest
from unittest.mock import patch, MagicMock

from vedic.compat.llm_polish import (
    polish_compat_analysis,
    _build_user_prompt,
    _fingerprint,
    _validate,
    _cache,
    _cache_lock,
    ALLOWED_REMEDIES,
    _PROMPT_VERSION,
)
import vedic.compat.llm_polish as _polish_mod


def _sample_facts():
    return {
        "p1": {"name": "ashu", "nakshatra": "Ardra", "pada": 2,
               "rashi": "Gemini", "manglik": True},
        "p2": {"name": "r", "nakshatra": "Mula", "pada": 1,
               "rashi": "Sagittarius", "manglik": True},
        "total": 14.5, "max": 36, "percent": 40,
        "grade": {"label": "Low Compatibility", "color": "#ef4444", "emoji": "❤️‍🩹"},
        "manglik_dosh": False,
        "koots": [
            {"key": "varna",  "label": "Varna",  "score": 0,   "max": 1, "detail": "Mismatched"},
            {"key": "vasya",  "label": "Vasya",  "score": 2,   "max": 2, "detail": "Strong"},
            {"key": "tara",   "label": "Tara",   "score": 1.5, "max": 3, "detail": "Moderate"},
            {"key": "yoni",   "label": "Yoni",   "score": 3,   "max": 4, "detail": "Good"},
            {"key": "maitri", "label": "Maitri", "score": 2,   "max": 5, "detail": "Weak"},
            {"key": "gana",   "label": "Gana",   "score": 0,   "max": 6, "detail": "Mismatched"},
            {"key": "bhakut", "label": "Bhakut", "score": 7,   "max": 7, "detail": "Auspicious"},
            {"key": "nadi",   "label": "Nadi",   "score": 0,   "max": 8, "detail": "Same Nadi"},
        ],
    }


def _good_llm_output():
    return {
        "compatibility_insight": (
            "Ashu and r share a thoughtful but uneven dynamic. Your Ashtakoot "
            "Milan totals 14.5 out of 36, placing the match in a low-compatibility "
            "zone in classical terms. Yet the foundation has real strengths worth "
            "honouring — what you build together depends more on intention than score. "
            "Ardra and Mula bring intensity that, when channelled, becomes depth."
        ),
        "strengths": [
            "Bhakut 7/7 between Gemini and Sagittarius brings natural prosperity at home.",
            "Vasya 2/2 means decisions flow without one person dominating — daily life feels balanced.",
            "Yoni 3/4 keeps physical and emotional intimacy easy and unforced.",
        ],
        "challenges": [
            "Nadi 0/8 indicates shared Vata constitution — Maha Mrityunjaya Jaap before marriage helps.",
            "Gana mismatch creates temperament friction; gratitude practice together softens this over time.",
        ],
        "marriage_outlook": (
            "This is a challenging match in classical Vedic terms but far from hopeless. "
            "Both being Manglik creates mutual cancellation, which is a quiet blessing here. "
            "Before marriage, consult a qualified Jyotishi and complete Kumbh Vivah; "
            "Navagraha Shanti during the first year of marriage adds further support. "
            "Sincere effort over time can transform this bond into something deeply meaningful."
        ),
    }


class TestToggleOff(unittest.TestCase):
    def test_toggle_off_returns_fallback_unchanged(self):
        os.environ.pop("COMPAT_LLM_POLISH", None)
        facts = _sample_facts()
        fallback = {"compatibility_insight": "FB", "strengths": ["a"],
                    "challenges": ["b"], "marriage_outlook": "FB-out"}
        out = polish_compat_analysis(facts, fallback, lang="en")
        self.assertIs(out, fallback)


class TestFingerprint(unittest.TestCase):
    def test_deterministic(self):
        f1, f2 = _sample_facts(), _sample_facts()
        self.assertEqual(_fingerprint(f1, "en"), _fingerprint(f2, "en"))

    def test_changes_with_score(self):
        f1, f2 = _sample_facts(), _sample_facts()
        f2["total"] = 28.0
        self.assertNotEqual(_fingerprint(f1, "en"), _fingerprint(f2, "en"))

    def test_changes_with_lang(self):
        f = _sample_facts()
        self.assertNotEqual(_fingerprint(f, "en"), _fingerprint(f, "hi"))


class TestPromptBuilder(unittest.TestCase):
    def test_includes_both_nakshatras_and_total(self):
        prompt = _build_user_prompt(_sample_facts(), lang="en")
        self.assertIn("Ardra", prompt)
        self.assertIn("Mula", prompt)
        self.assertIn("14.5", prompt)
        self.assertIn("both_manglik", prompt)
        self.assertIn("ALLOWED_REMEDIES", prompt)

    def test_strength_dosha_markers(self):
        prompt = _build_user_prompt(_sample_facts(), lang="en")
        # Bhakut 7/7 should be marked STRENGTH
        self.assertIn("STRENGTH", prompt)
        # Nadi 0/8 should be marked DOSHA
        self.assertIn("DOSHA", prompt)


class TestValidator(unittest.TestCase):
    def setUp(self):
        self.facts = _sample_facts()

    def test_accepts_well_formed(self):
        ok, reason = _validate(_good_llm_output(), self.facts)
        self.assertTrue(ok, f"expected ok, got {reason}")

    def test_rejects_missing_total(self):
        out = _good_llm_output()
        out["compatibility_insight"] = out["compatibility_insight"].replace("14.5", "around half")
        ok, reason = _validate(out, self.facts)
        self.assertFalse(ok)
        self.assertEqual(reason, "total_not_cited")

    def test_rejects_missing_nakshatra(self):
        out = _good_llm_output()
        # Strip Mula from everything
        for k in ("compatibility_insight", "marriage_outlook"):
            out[k] = out[k].replace("Mula", "the second partner")
        out["strengths"] = [s.replace("Mula", "x") for s in out["strengths"]]
        out["challenges"] = [s.replace("Mula", "x") for s in out["challenges"]]
        # Also strip the rashi anchor (Sagittarius) so neither
        # nakshatra nor rashi for p2 appears anywhere.
        for k in ("compatibility_insight", "marriage_outlook"):
            out[k] = out[k].replace("Sagittarius", "the other sign")
        out["strengths"] = [s.replace("Sagittarius", "x") for s in out["strengths"]]
        out["challenges"] = [s.replace("Sagittarius", "x") for s in out["challenges"]]
        ok, reason = _validate(out, self.facts)
        self.assertFalse(ok)
        self.assertEqual(reason, "p2_anchor_missing")

    def test_rejects_banned_term(self):
        out = _good_llm_output()
        out["marriage_outlook"] += " This is guaranteed to succeed."
        ok, reason = _validate(out, self.facts)
        self.assertFalse(ok)
        self.assertTrue(reason.startswith("banned_term"))

    def test_rejects_challenge_without_remedy(self):
        # Validator now accepts a remedy keyword anywhere in the
        # challenges block OR in the outlook (per-bullet check was too
        # strict for gpt-4o-mini). To trigger this rejection both
        # surfaces must be remedy-free.
        out = _good_llm_output()
        out["challenges"] = ["Generic friction with no path forward described."]
        out["marriage_outlook"] = "The future of this union is uncertain."
        ok, reason = _validate(out, self.facts)
        self.assertFalse(ok)
        self.assertEqual(reason, "challenge_missing_remedy")

    def test_rejects_missing_key(self):
        out = _good_llm_output()
        del out["marriage_outlook"]
        ok, reason = _validate(out, self.facts)
        self.assertFalse(ok)
        self.assertTrue(reason.startswith("missing_key"))

    def test_rejects_non_dict(self):
        ok, reason = _validate("not a dict", self.facts)
        self.assertFalse(ok)

    def test_rejects_hallucinated_koot_score(self):
        # LLM cites "Bhakut 5/7" but real Bhakut is 7/7
        out = _good_llm_output()
        out["strengths"][0] = "Bhakut 5 out of 7 hints at strong family alignment between you both."
        ok, reason = _validate(out, self.facts)
        self.assertFalse(ok)
        self.assertTrue(reason.startswith("hallucinated_score"), reason)

    def test_rejects_unknown_nakshatra(self):
        # LLM name-drops "Krittika" — neither partner has it
        out = _good_llm_output()
        out["compatibility_insight"] += " The Krittika influence is also notable here."
        ok, reason = _validate(out, self.facts)
        self.assertFalse(ok)
        self.assertTrue(reason.startswith("unknown_nakshatra"), reason)

    def test_anchor_accepts_shortened_nakshatra_token(self):
        # Phase 2.5.11.20-B: anchor logic mirrors vocab logic — when LLM
        # references only "Bhadrapada" (no name, no rashi), it should still
        # count as a valid anchor for partner whose nakshatra is "Purva Bhadrapada".
        facts = _sample_facts()
        facts["p2"]["nakshatra"] = "Purva Bhadrapada"
        facts["p2"]["name"] = "X"  # 1-char → too short to anchor by name
        out = _good_llm_output()
        # Wipe every reference to p2 except the shortened "Bhadrapada"
        for k in ("compatibility_insight", "marriage_outlook"):
            out[k] = out[k].replace("Mula", "Bhadrapada").replace(" r ", " X ").replace("Sagittarius", "Pisces-area")
        out["strengths"] = [s.replace("Sagittarius", "the second sign") for s in out["strengths"]]
        ok, reason = _validate(out, facts)
        self.assertTrue(ok, f"shortened-token anchor rejected: {reason}")

    def test_max_tokens_higher_for_non_latin_lang(self):
        # Phase 2.5.11.20-B: non-Latin languages must request 900 tokens
        # to avoid mid-JSON truncation; Latin scripts stay at 600.
        facts = _sample_facts()
        captured: dict = {}

        class _FakeResp:
            class _Choice:
                class _Msg:
                    content = '{"compatibility_insight":"x","strengths":["y"],"challenges":["z"],"marriage_outlook":"w"}'
                message = _Msg()
            choices = [_Choice()]

        class _FakeClient:
            class chat:
                class completions:
                    @staticmethod
                    def create(**kwargs):
                        captured.update(kwargs)
                        return _FakeResp()

        import openai_helper  # type: ignore
        with patch.dict(os.environ, {"COMPAT_LLM_POLISH": "1"}, clear=False), \
             patch.object(openai_helper, "_get_client", return_value=_FakeClient()), \
             patch.object(_polish_mod, "_validate", return_value=(False, "ok")), \
             patch.object(_polish_mod, "_db_cache_get", return_value=None), \
             patch.object(_polish_mod, "_db_cache_put", return_value=None):
            with _cache_lock:
                _cache.clear()
            polish_compat_analysis(facts, {"compatibility_insight": "fb"}, lang="hi")
            self.assertEqual(captured.get("max_tokens"), 900, "non-Latin lang must use 900")
            captured.clear()
            polish_compat_analysis(facts, {"compatibility_insight": "fb"}, lang="en")
            self.assertEqual(captured.get("max_tokens"), 600, "Latin lang must use 600")

    def test_accepts_shortened_multiword_nakshatra(self):
        # Phase 2.5.11.20-B regression: facts have "Purva Bhadrapada" but LLM
        # commonly shortens to just "Bhadrapada". Pre-fix the validator only
        # registered the first word ("Purva"), so the shortened form was
        # rejected as `unknown_nakshatra:Bhadrapada` and the polish silently
        # fell back to the rule-based template (visible bug in Hinglish output).
        facts = _sample_facts()
        # Only change p2's nakshatra to multi-word; rashi stays Sagittarius
        # so the existing _good_llm_output() (which references it) still passes.
        facts["p2"]["nakshatra"] = "Purva Bhadrapada"
        out = _good_llm_output()
        # Replace the original "Mula" mention with a shortened "Bhadrapada"
        # — this is the exact LLM behaviour we observed in production.
        out["compatibility_insight"] = out["compatibility_insight"].replace(
            "Ardra and Mula", "Ardra and Bhadrapada"
        )
        ok, reason = _validate(out, facts)
        self.assertTrue(ok, f"shortened nakshatra wrongly rejected: {reason}")

    def test_rejects_unknown_rashi(self):
        # LLM mentions "Aries" — neither partner has it
        out = _good_llm_output()
        out["marriage_outlook"] += " The Aries impulse will need patience."
        ok, reason = _validate(out, self.facts)
        self.assertFalse(ok)
        self.assertTrue(reason.startswith("unknown_rashi"), reason)

    def test_rejects_banned_gemstone_remedy(self):
        # Architect's actual concern: LLM tacks on valid keyword
        # ("jyotishi") but also pushes unapproved gemstone advice.
        out = _good_llm_output()
        out["challenges"] = [
            "Friction may arise; consult a qualified Jyotishi and wear a blue sapphire ring."
        ]
        ok, reason = _validate(out, self.facts)
        self.assertFalse(ok)
        self.assertTrue(reason.startswith("banned_remedy"), reason)

    def test_rejects_tantrik_remedy(self):
        out = _good_llm_output()
        out["challenges"] = [
            "Energetic conflict suggests a tantrik ritual along with Maha Mrityunjaya Jaap."
        ]
        ok, reason = _validate(out, self.facts)
        self.assertFalse(ok)
        self.assertTrue(reason.startswith("banned_remedy"), reason)

    # ── Architect-flagged blind spots (Phase 2.5.11.20 v7) ──────────────
    def test_anchor_rejects_substring_collision(self):
        # p1 nakshatra "Mula" must not be matched by the substring
        # inside "formula"; the prose must contain a real anchor.
        facts = _sample_facts()
        facts["p1"]["nakshatra"] = "Mula"
        facts["p1"]["rashi"] = "Sagittarius"  # also won't appear
        facts["p1"]["name"] = "x"  # too short to qualify (len < 3)
        # Build a bad output where p1 has NO real anchor but the
        # prose accidentally contains "formula" (which contains "mula").
        out = _good_llm_output()
        out["compatibility_insight"] = (
            "This relationship totals 14.5 out of 36. Together you can find a "
            "formula for understanding each other's needs over time, with patience."
        )
        out["strengths"] = ["The dynamic between you both is steady and warm."]
        out["challenges"] = [
            "Some friction may surface; consult a qualified Jyotishi for guidance."
        ]
        out["marriage_outlook"] = (
            "The path ahead requires effort. Both being Manglik creates mutual "
            "cancellation. Consider Kumbh Vivah and Navagraha Shanti to strengthen "
            "the bond. Sustained intention can carry this union far."
        )
        # p2 is still anchored via Mula/Sagittarius elsewhere? No — we
        # explicitly stripped the prose. So p1 is the first to fail.
        ok, reason = _validate(out, facts)
        self.assertFalse(ok)
        self.assertTrue(reason.endswith("_anchor_missing"), reason)

    def test_vocab_lock_catches_lowercase_hallucination(self):
        # LLM writes "shravana" (lowercase) — neither partner has it.
        # Old regex only matched capitalized tokens and would miss this.
        out = _good_llm_output()
        out["marriage_outlook"] += " Yeh shravana energy bhi influence karti hai."
        ok, reason = _validate(out, self.facts)
        self.assertFalse(ok)
        self.assertTrue(reason.startswith("unknown_nakshatra"), reason)

    def test_rejects_paraphrase_only_remedy(self):
        # LLM says "consult a spiritual healer" — no whitelisted phrase.
        # Old keyword-only check would have falsely passed because
        # "healer" was never on the list either way; this guards the
        # tighter exact-phrase contract for any future paraphrase like
        # "spiritual jyotishi" → must remain "qualified Jyotishi".
        out = _good_llm_output()
        out["challenges"] = [
            "Friction may arise; consult a spiritual healer for clarity over time."
        ]
        out["marriage_outlook"] = (
            "The path ahead requires effort. Both being Manglik creates mutual "
            "cancellation. Trust the process and stay rooted in shared intention. "
            "Time and patience are your greatest allies in this union."
        )
        ok, reason = _validate(out, self.facts)
        self.assertFalse(ok)
        self.assertEqual(reason, "challenge_missing_remedy")

    def test_rejects_banned_remedy_in_outlook(self):
        # Banned-remedy denylist must also cover marriage_outlook,
        # not just challenges (LLM often shifts advice into outlook).
        out = _good_llm_output()
        out["marriage_outlook"] = (
            "The match has its difficulties but is workable. Both being Manglik "
            "creates mutual cancellation. We strongly recommend you wear a yellow "
            "sapphire pendant and complete Kumbh Vivah. Time will smoothen the rest."
        )
        ok, reason = _validate(out, self.facts)
        self.assertFalse(ok)
        self.assertTrue(reason.startswith("banned_remedy_in_outlook"), reason)


class TestFingerprintVersioning(unittest.TestCase):
    def test_version_invalidates_cache(self):
        f = _sample_facts()
        original_fp = _fingerprint(f, "en")
        # Simulate a policy bump
        with patch.object(_polish_mod, "_PROMPT_VERSION", "v999"):
            new_fp = _fingerprint(f, "en")
        self.assertNotEqual(original_fp, new_fp)

    def test_grade_change_invalidates(self):
        f1 = _sample_facts()
        f2 = _sample_facts()
        f2["grade"] = {"label": "Excellent Match"}
        self.assertNotEqual(_fingerprint(f1, "en"), _fingerprint(f2, "en"))


class TestPolishWithMockedLLM(unittest.TestCase):
    def setUp(self):
        os.environ["COMPAT_LLM_POLISH"] = "1"
        with _cache_lock:
            _cache.clear()

    def tearDown(self):
        os.environ.pop("COMPAT_LLM_POLISH", None)
        with _cache_lock:
            _cache.clear()

    def _mock_client(self, payload_dict):
        client = MagicMock()
        choice = MagicMock()
        choice.message.content = __import__("json").dumps(payload_dict)
        client.chat.completions.create.return_value = MagicMock(choices=[choice])
        return client

    def test_polished_output_returned_on_success(self):
        client = self._mock_client(_good_llm_output())
        with patch("openai_helper._get_client", return_value=client):
            facts = _sample_facts()
            fallback = {"compatibility_insight": "FB", "strengths": ["a"],
                        "challenges": ["b"], "marriage_outlook": "FB-out"}
            out = polish_compat_analysis(facts, fallback, lang="en")
        self.assertIn("14.5", out["compatibility_insight"])
        self.assertIn("Ardra", out["compatibility_insight"])
        self.assertEqual(len(out["strengths"]), 3)

    def test_invalid_llm_output_falls_back(self):
        bad = _good_llm_output()
        bad["compatibility_insight"] = "Missing the score completely here."
        client = self._mock_client(bad)
        with patch("openai_helper._get_client", return_value=client):
            facts = _sample_facts()
            fallback = {"compatibility_insight": "FB", "strengths": ["a"],
                        "challenges": ["b"], "marriage_outlook": "FB-out"}
            out = polish_compat_analysis(facts, fallback, lang="en")
        self.assertIs(out, fallback)

    def test_cache_hit_skips_llm_call(self):
        client = self._mock_client(_good_llm_output())
        with patch("openai_helper._get_client", return_value=client):
            facts = _sample_facts()
            fallback = {"compatibility_insight": "FB", "strengths": ["a"],
                        "challenges": ["b"], "marriage_outlook": "FB-out"}
            out1 = polish_compat_analysis(facts, fallback, lang="en")
            out2 = polish_compat_analysis(facts, fallback, lang="en")
        self.assertEqual(out1, out2)
        # Only ONE LLM call should have been made; second was cache hit
        self.assertEqual(client.chat.completions.create.call_count, 1)

    def test_no_client_falls_back(self):
        with patch("openai_helper._get_client", return_value=None):
            facts = _sample_facts()
            fallback = {"compatibility_insight": "FB", "strengths": ["a"],
                        "challenges": ["b"], "marriage_outlook": "FB-out"}
            out = polish_compat_analysis(facts, fallback, lang="en")
        self.assertIs(out, fallback)


class TestDbCacheLayer(unittest.TestCase):
    """Phase 2.5.11.20-A — verify L2 (persistent DB) cache integration.
    Both helpers must be best-effort: no app context = swallow + return None,
    never raise into the orchestrator."""

    def setUp(self):
        with _cache_lock:
            _cache.clear()

    def test_db_cache_get_no_app_context_returns_none(self):
        # No Flask app context here; must NOT raise.
        from vedic.compat.llm_polish import _db_cache_get
        self.assertIsNone(_db_cache_get("nonexistent_fp_xyz"))

    def test_db_cache_put_no_app_context_swallows(self):
        from vedic.compat.llm_polish import _db_cache_put
        # Must NOT raise even without app context
        try:
            _db_cache_put("fp_test", {"compatibility_insight": "x",
                                       "strengths": [], "challenges": [],
                                       "marriage_outlook": "y"}, "gpt-4o-mini")
        except Exception as exc:
            self.fail(f"_db_cache_put raised unexpectedly: {exc}")

    def test_db_cache_put_concurrent_duplicate_does_not_raise(self):
        """Architect 2.5.11.20-A: simulate the concurrent-write path —
        the helper must NEVER raise even if the underlying upsert/insert
        produces an IntegrityError under a real race."""
        from vedic.compat import llm_polish as _lp
        from sqlalchemy.exc import IntegrityError

        class _BoomSession:
            bind = None
            def get(self, *a, **kw): return None
            def add(self, *a, **kw): pass
            def execute(self, *a, **kw): pass
            def commit(self): raise IntegrityError("dup", {}, Exception())
            def rollback(self): pass

        class _BoomDB:
            session = _BoomSession()

        with patch.dict(
            "sys.modules",
            {"database": type("M", (), {"db": _BoomDB()})()},
        ):
            try:
                _lp._db_cache_put("fp_dup", {"compatibility_insight": "x",
                                              "strengths": [], "challenges": [],
                                              "marriage_outlook": "y"}, "gpt-4o-mini")
            except Exception as exc:
                self.fail(f"_db_cache_put leaked exception under race: {exc}")

    def test_polish_db_cache_hit_skips_llm(self):
        """Even with empty L1, a populated L2 should short-circuit the LLM call."""
        good = _good_llm_output()
        from vedic.compat import llm_polish as _lp

        with patch.object(_lp, "_db_cache_get", return_value=good) as mocked_get, \
             patch.object(_lp, "_db_cache_put") as mocked_put:
            client = MagicMock()
            with patch("openai_helper._get_client", return_value=client), \
                 patch.dict(os.environ, {"COMPAT_LLM_POLISH": "1"}):
                facts = _sample_facts()
                fallback = {"compatibility_insight": "FB", "strengths": ["a"],
                            "challenges": ["b"], "marriage_outlook": "FB-out"}
                out = polish_compat_analysis(facts, fallback, lang="en")
        self.assertEqual(out["compatibility_insight"], good["compatibility_insight"])
        # LLM was never called — DB hit short-circuited
        self.assertEqual(client.chat.completions.create.call_count, 0)
        mocked_get.assert_called_once()
        mocked_put.assert_not_called()


if __name__ == "__main__":
    unittest.main()
