"""
Phase 2.5.11.21 — Tests for vedic.compat.llm_polish (7-section deep schema).

Schema upgrade:
  Before (v10): { compatibility_insight, strengths[], challenges[], marriage_outlook }
  Now    (v11): {
    relationship_snapshot: { summary, tags: {emotional_pull, marriage_potential, long_term_stability} },
    emotional_alignment:   { text, grounding },
    trust_loyalty:         { text, grounding },
    conflict_patterns:     { text, grounding },
    marriage_stability:    { text, grounding },
    commitment_strength:   { text, grounding },
    future_direction:      { text, grounding },
  }
  + legacy 4-key flat schema derived from the above for backward-compat.

Covers:
  • Toggle-off short-circuit returns fallback verbatim
  • Fingerprint determinism + sensitivity
  • Validator: shape, total citation, anchors, banned terms, remedy whitelist,
    banned remedies, hallucinated scores, unknown nakshatra/rashi, lengths
  • Cache hit returns same dict
  • Build_user_prompt includes both nakshatras + manglik line
  • polish_compat_analysis emits BOTH new 7-section keys AND legacy 4 keys
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
    """Well-formed 7-section deep schema that passes the validator."""
    return {
        "relationship_snapshot": {
            "summary": (
                "Ashu and r share a thoughtful but uneven dynamic — totaling "
                "14.5 out of 36, with strong attachment but uneven emotional timing."
            ),
            "tags": {
                "emotional_pull": "Strong",
                "marriage_potential": "Medium",
                "long_term_stability": "Depends on communication maturity",
            },
        },
        "emotional_alignment": {
            "text": (
                "One of you processes feelings internally while the other waits "
                "for visible reassurance. Ardra brings intensity that surfaces "
                "quickly; Mula moves with quieter depth. When both learn the "
                "other's tempo, what feels like distance becomes simple difference."
            ),
            "grounding": "Based on Moon-sign harmony, Maitri (mental friendship), and Gana koot.",
        },
        "trust_loyalty": {
            "text": (
                "Trust here grows in long stretches of shared silence, not loud "
                "promises. The harder phase comes when one of you withdraws "
                "after a small misunderstanding — the other reads it as distance. "
                "Loyalty is real on both sides; the test is patience during quiet phases."
            ),
            "grounding": "Based on Bhakut, Mangal balance, and 7th-house loyalty indicators.",
        },
        "conflict_patterns": {
            "text": (
                "Arguments rarely begin with the topic at hand. They start with "
                "an unspoken expectation, escalate when neither names the real "
                "feeling, and only heal when one of you breaks the silence first. "
                "Naming the underlying need early defuses most of these cycles."
            ),
            "grounding": "Based on Yoni, Gana, and Mars-Mercury behavioral indicators.",
        },
        "marriage_stability": {
            "text": (
                "Marriage is genuinely possible at 14.5 out of 36, but stability "
                "improves only after one specific adjustment: each of you must "
                "stop expecting the other to read your emotions without words. "
                "Family acceptance is workable. Both being Manglik creates mutual "
                "cancellation, which quietly helps. Maha Mrityunjaya Jaap before "
                "marriage anchors the foundation."
            ),
            "grounding": "Based on total Ashtakoot score, Bhakut, Nadi, and Manglik balance.",
        },
        "commitment_strength": {
            "text": (
                "One of you attaches faster, while the other commits more slowly "
                "but more permanently. Breakup-reconciliation cycles are uncommon "
                "once the bond stabilises. Long-term effort balances out over years, "
                "even if it looks uneven in any single month."
            ),
            "grounding": "Based on Maitri (planetary friendship), Vasya, and 7th-lord placement.",
        },
        "future_direction": {
            "text": (
                "Over the next 2-3 years this bond evolves through emotional "
                "pressure rather than fading. The real outcome rests on one quiet "
                "choice: whether both of you decide to communicate before reacting. "
                "Sustained intention transforms this match. Consider Kumbh Vivah "
                "and Navagraha Shanti to support the early years."
            ),
            "grounding": "Based on overall compatibility score, dasha context, and 7th-house yogas.",
        },
    }


def _legacy_fallback():
    """Old 4-key fallback shape — used by callers that haven't migrated."""
    return {
        "compatibility_insight": "FB",
        "strengths": ["a"],
        "challenges": ["b"],
        "marriage_outlook": "FB-out",
    }


# ─────────────────────────────────────────────────────────────────────────────
# Toggle / fingerprint / prompt-builder
# ─────────────────────────────────────────────────────────────────────────────
class TestToggleOff(unittest.TestCase):
    def test_toggle_off_returns_fallback_unchanged(self):
        os.environ.pop("COMPAT_LLM_POLISH", None)
        out = polish_compat_analysis(_sample_facts(), _legacy_fallback(), lang="en")
        self.assertIs(out, _legacy_fallback.__call__() and out, out)
        self.assertEqual(out.get("compatibility_insight"), "FB")


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
        self.assertIn("STRENGTH", prompt)
        self.assertIn("DOSHA", prompt)


# ─────────────────────────────────────────────────────────────────────────────
# Validator — shape (snapshot + 6 sections + grounding)
# ─────────────────────────────────────────────────────────────────────────────
class TestValidatorShape(unittest.TestCase):
    def setUp(self):
        self.facts = _sample_facts()

    def test_accepts_well_formed(self):
        ok, reason = _validate(_good_llm_output(), self.facts)
        self.assertTrue(ok, f"expected ok, got {reason}")

    def test_rejects_non_dict(self):
        ok, reason = _validate("not a dict", self.facts)
        self.assertFalse(ok)

    def test_rejects_missing_snapshot(self):
        out = _good_llm_output()
        del out["relationship_snapshot"]
        ok, reason = _validate(out, self.facts)
        self.assertFalse(ok)
        self.assertEqual(reason, "missing_or_bad:relationship_snapshot")

    def test_rejects_snapshot_summary_too_short(self):
        out = _good_llm_output()
        out["relationship_snapshot"]["summary"] = "short"
        ok, reason = _validate(out, self.facts)
        self.assertFalse(ok)
        self.assertEqual(reason, "snapshot_summary_bad")

    def test_rejects_missing_snapshot_tag(self):
        out = _good_llm_output()
        del out["relationship_snapshot"]["tags"]["emotional_pull"]
        ok, reason = _validate(out, self.facts)
        self.assertFalse(ok)
        self.assertTrue(reason.startswith("snapshot_tag_bad"), reason)

    def test_rejects_missing_section(self):
        out = _good_llm_output()
        del out["trust_loyalty"]
        ok, reason = _validate(out, self.facts)
        self.assertFalse(ok)
        self.assertEqual(reason, "missing_or_bad:trust_loyalty")

    def test_rejects_section_missing_grounding(self):
        out = _good_llm_output()
        del out["conflict_patterns"]["grounding"]
        ok, reason = _validate(out, self.facts)
        self.assertFalse(ok)
        self.assertEqual(reason, "conflict_patterns_grounding_bad")

    def test_rejects_section_text_too_short(self):
        out = _good_llm_output()
        out["emotional_alignment"]["text"] = "tiny"
        ok, reason = _validate(out, self.facts)
        self.assertFalse(ok)
        self.assertEqual(reason, "emotional_alignment_text_length")

    def test_rejects_grounding_too_short(self):
        out = _good_llm_output()
        out["future_direction"]["grounding"] = "tiny"
        ok, reason = _validate(out, self.facts)
        self.assertFalse(ok)
        self.assertEqual(reason, "future_direction_grounding_length")


# ─────────────────────────────────────────────────────────────────────────────
# Validator — content (total, anchors, vocab, remedies, banned terms)
# ─────────────────────────────────────────────────────────────────────────────
class TestValidatorContent(unittest.TestCase):
    def setUp(self):
        self.facts = _sample_facts()

    def test_rejects_missing_total(self):
        out = _good_llm_output()
        out["relationship_snapshot"]["summary"] = (
            "Ashu and r share a thoughtful but uneven dynamic — strong attachment "
            "but uneven emotional timing across both charts."
        )
        out["marriage_stability"]["text"] = out["marriage_stability"]["text"].replace("14.5 out of 36", "moderate")
        ok, reason = _validate(out, self.facts)
        self.assertFalse(ok)
        self.assertEqual(reason, "total_not_cited")

    def test_rejects_missing_partner_anchor(self):
        out = _good_llm_output()
        # Strip every reference to p2 (Mula nakshatra + Sagittarius rashi + name "r")
        for sec in ("emotional_alignment", "trust_loyalty", "conflict_patterns",
                    "marriage_stability", "commitment_strength", "future_direction"):
            t = out[sec]["text"]
            t = t.replace("Mula", "the second").replace("Sagittarius", "the other")
            out[sec]["text"] = t
        out["relationship_snapshot"]["summary"] = out["relationship_snapshot"]["summary"].replace(
            "Mula", "the second"
        )
        ok, reason = _validate(out, self.facts)
        self.assertFalse(ok)
        self.assertEqual(reason, "p2_anchor_missing")

    def test_rejects_banned_term(self):
        out = _good_llm_output()
        out["future_direction"]["text"] += " This is guaranteed to succeed."
        ok, reason = _validate(out, self.facts)
        self.assertFalse(ok)
        self.assertTrue(reason.startswith("banned_term"))

    def test_rejects_remedy_missing(self):
        out = _good_llm_output()
        # Strip allowed-remedy phrases from BOTH remedy-bearing sections
        for sec in ("marriage_stability", "future_direction"):
            t = out[sec]["text"]
            for r in ALLOWED_REMEDIES:
                t = t.replace(r, "spiritual support")
            out[sec]["text"] = t
        ok, reason = _validate(out, self.facts)
        self.assertFalse(ok)
        self.assertEqual(reason, "remedy_missing")

    def test_rejects_banned_gemstone_in_marriage_stability(self):
        out = _good_llm_output()
        out["marriage_stability"]["text"] += " Also wear a blue sapphire ring for support."
        ok, reason = _validate(out, self.facts)
        self.assertFalse(ok)
        self.assertTrue(reason.startswith("banned_remedy_in_marriage_stability"), reason)

    def test_rejects_banned_tantrik_in_future_direction(self):
        out = _good_llm_output()
        out["future_direction"]["text"] += " A tantrik ritual will lock the bond."
        ok, reason = _validate(out, self.facts)
        self.assertFalse(ok)
        self.assertTrue(reason.startswith("banned_remedy_in_future_direction"), reason)

    def test_rejects_hallucinated_koot_score(self):
        out = _good_llm_output()
        out["emotional_alignment"]["text"] += " Bhakut 5 out of 7 hints at family alignment."
        ok, reason = _validate(out, self.facts)
        self.assertFalse(ok)
        self.assertTrue(reason.startswith("hallucinated_score"), reason)

    def test_rejects_unknown_nakshatra(self):
        out = _good_llm_output()
        out["emotional_alignment"]["text"] += " The Krittika influence is also notable."
        ok, reason = _validate(out, self.facts)
        self.assertFalse(ok)
        self.assertTrue(reason.startswith("unknown_nakshatra"), reason)

    def test_rejects_unknown_rashi(self):
        out = _good_llm_output()
        out["future_direction"]["text"] += " The Aries impulse needs patience."
        ok, reason = _validate(out, self.facts)
        self.assertFalse(ok)
        self.assertTrue(reason.startswith("unknown_rashi"), reason)

    def test_vocab_lock_catches_lowercase_hallucination(self):
        # Hinglish-style: "yeh shravana wali..." — lowercase nakshatra
        out = _good_llm_output()
        out["future_direction"]["text"] += " Yeh shravana energy bhi influence karti hai."
        ok, reason = _validate(out, self.facts)
        self.assertFalse(ok)
        self.assertTrue(reason.startswith("unknown_nakshatra"), reason)

    def test_anchor_accepts_shortened_multiword_nakshatra(self):
        # facts have "Purva Bhadrapada" → LLM commonly shortens to "Bhadrapada"
        facts = _sample_facts()
        facts["p2"]["nakshatra"] = "Purva Bhadrapada"
        out = _good_llm_output()
        # Replace Mula reference with Bhadrapada in one section
        out["emotional_alignment"]["text"] = out["emotional_alignment"]["text"].replace(
            "Mula", "Bhadrapada"
        )
        for sec in ("trust_loyalty", "conflict_patterns", "marriage_stability",
                    "commitment_strength", "future_direction"):
            out[sec]["text"] = out[sec]["text"].replace("Mula", "the other")
        out["relationship_snapshot"]["summary"] = out["relationship_snapshot"]["summary"].replace(
            "Mula", "Bhadrapada"
        )
        ok, reason = _validate(out, facts)
        self.assertTrue(ok, f"shortened multiword nakshatra wrongly rejected: {reason}")

    def test_total_accepts_devanagari_digits(self):
        # Phase 2.5.11.21 fix: gpt-4o-mini in hi/mr/ta/etc re-renders the
        # numeric total in the target script's native digits ("२४" for 24).
        # Validator must normalize Indic digits to ASCII before checking.
        facts = _sample_facts()  # total=14.5
        out = _good_llm_output()
        # Replace every "14.5" occurrence with Devanagari "१४.५"
        for sec in out:
            if isinstance(out[sec], dict) and "text" in out[sec]:
                out[sec]["text"] = out[sec]["text"].replace("14.5", "१४.५")
            elif sec == "relationship_snapshot":
                out[sec]["summary"] = out[sec]["summary"].replace("14.5", "१४.५")
        ok, reason = _validate(out, facts, lang="hi")
        self.assertTrue(ok, f"devanagari digits wrongly rejected: {reason}")

    def test_anchor_check_skipped_for_non_latin_lang(self):
        # Phase 2.5.11.21: Devanagari/CJK/Indic LLM output transliterates
        # partner names/nakshatras into the target script, making Latin
        # word-boundary anchor matching impossible. Validator must skip
        # the anchor check for those languages and rely on total + koot
        # fact-lock + remedy whitelist for grounding.
        facts = _sample_facts()
        out = _good_llm_output()
        # Strip every Latin partner-anchor token from all sections — the
        # equivalent of fully-transliterated Devanagari output.
        for sec in ("emotional_alignment", "trust_loyalty", "conflict_patterns",
                    "marriage_stability", "commitment_strength", "future_direction"):
            t = out[sec]["text"]
            for w in ("Ardra", "Mula", "Gemini", "Sagittarius", "Ashu"):
                t = t.replace(w, "they")
            out[sec]["text"] = t
        out["relationship_snapshot"]["summary"] = (
            "A thoughtful but uneven dynamic — totals 14.5 out of 36 with strong attachment."
        )
        # Latin lang must reject (anchor missing)
        ok_en, reason_en = _validate(out, facts, lang="en")
        self.assertFalse(ok_en)
        self.assertTrue(reason_en.endswith("_anchor_missing"), reason_en)
        # Devanagari lang must accept (anchor check skipped)
        ok_hi, reason_hi = _validate(out, facts, lang="hi")
        self.assertTrue(ok_hi, f"hi wrongly rejected: {reason_hi}")
        # Hinglish (hn) keeps Latin so anchor check still applies
        ok_hn, reason_hn = _validate(out, facts, lang="hn")
        self.assertFalse(ok_hn)
        self.assertTrue(reason_hn.endswith("_anchor_missing"), reason_hn)

    def test_anchor_rejects_substring_collision(self):
        # p1 nakshatra "Mula" must not be matched by substring inside "formula"
        facts = _sample_facts()
        facts["p1"]["nakshatra"] = "Mula"
        facts["p1"]["rashi"] = "Sagittarius"
        facts["p1"]["name"] = "x"  # too short to anchor by name
        # p2 won't match either — strip its references too
        facts["p2"]["name"] = "y"
        out = _good_llm_output()
        # Wipe ALL real anchors but plant "formula" containing substring "mula"
        replacements = {
            "Ardra": "the first", "Mula": "the second",
            "Gemini": "the first sign", "Sagittarius": "the second sign",
        }
        for sec in ("emotional_alignment", "trust_loyalty", "conflict_patterns",
                    "marriage_stability", "commitment_strength", "future_direction"):
            t = out[sec]["text"]
            for old, new in replacements.items():
                t = t.replace(old, new)
            out[sec]["text"] = t
        out["relationship_snapshot"]["summary"] = (
            "This bond totals 14.5 out of 36 — together you can find a formula "
            "for understanding each other's needs over time, with patience."
        )
        out["emotional_alignment"]["text"] = (
            "Together you can find a formula for understanding each other. The "
            "first feels intensity quickly, while the second moves with quieter "
            "depth. Both learning each other's tempo bridges the gap over time."
        )
        ok, reason = _validate(out, facts)
        self.assertFalse(ok)
        self.assertTrue(reason.endswith("_anchor_missing"), reason)


# ─────────────────────────────────────────────────────────────────────────────
# Versioning / cache-fingerprint
# ─────────────────────────────────────────────────────────────────────────────
class TestFingerprintVersioning(unittest.TestCase):
    def test_version_invalidates_cache(self):
        f = _sample_facts()
        original_fp = _fingerprint(f, "en")
        with patch.object(_polish_mod, "_PROMPT_VERSION", "v999"):
            new_fp = _fingerprint(f, "en")
        self.assertNotEqual(original_fp, new_fp)

    def test_grade_change_invalidates(self):
        f1 = _sample_facts()
        f2 = _sample_facts()
        f2["grade"] = {"label": "Excellent Match"}
        self.assertNotEqual(_fingerprint(f1, "en"), _fingerprint(f2, "en"))

    def test_prompt_version_is_v11(self):
        # Lock current schema version — bump test whenever prompt changes.
        self.assertEqual(_PROMPT_VERSION, "v11")


# ─────────────────────────────────────────────────────────────────────────────
# polish_compat_analysis with mocked LLM
# ─────────────────────────────────────────────────────────────────────────────
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

    def test_polished_output_emits_both_new_and_legacy_keys(self):
        client = self._mock_client(_good_llm_output())
        with patch("openai_helper._get_client", return_value=client), \
             patch.object(_polish_mod, "_db_cache_get", return_value=None), \
             patch.object(_polish_mod, "_db_cache_put", return_value=None):
            out = polish_compat_analysis(_sample_facts(), _legacy_fallback(), lang="en")
        # New deep schema present
        self.assertIn("relationship_snapshot", out)
        self.assertIn("summary", out["relationship_snapshot"])
        self.assertIn("tags", out["relationship_snapshot"])
        for sec in ("emotional_alignment", "trust_loyalty", "conflict_patterns",
                    "marriage_stability", "commitment_strength", "future_direction"):
            self.assertIn(sec, out)
            self.assertIn("text", out[sec])
            self.assertIn("grounding", out[sec])
        # Legacy schema also present (derived) for backward-compat
        self.assertIn("compatibility_insight", out)
        self.assertIsInstance(out["strengths"], list)
        self.assertEqual(len(out["strengths"]), 2)
        self.assertIsInstance(out["challenges"], list)
        self.assertEqual(len(out["challenges"]), 2)
        self.assertIn("marriage_outlook", out)
        # Legacy compatibility_insight = snapshot.summary
        self.assertEqual(out["compatibility_insight"], out["relationship_snapshot"]["summary"])
        # Legacy marriage_outlook = future_direction.text
        self.assertEqual(out["marriage_outlook"], out["future_direction"]["text"])

    def test_invalid_llm_output_falls_back(self):
        bad = _good_llm_output()
        bad["relationship_snapshot"]["summary"] = "missing the score completely"
        bad["marriage_stability"]["text"] = bad["marriage_stability"]["text"].replace(
            "14.5 out of 36", "moderate"
        )
        client = self._mock_client(bad)
        fallback = _legacy_fallback()
        with patch("openai_helper._get_client", return_value=client), \
             patch.object(_polish_mod, "_db_cache_get", return_value=None), \
             patch.object(_polish_mod, "_db_cache_put", return_value=None):
            out = polish_compat_analysis(_sample_facts(), fallback, lang="en")
        self.assertIs(out, fallback)

    def test_cache_hit_skips_llm_call(self):
        client = self._mock_client(_good_llm_output())
        with patch("openai_helper._get_client", return_value=client), \
             patch.object(_polish_mod, "_db_cache_get", return_value=None), \
             patch.object(_polish_mod, "_db_cache_put", return_value=None):
            out1 = polish_compat_analysis(_sample_facts(), _legacy_fallback(), lang="en")
            out2 = polish_compat_analysis(_sample_facts(), _legacy_fallback(), lang="en")
        self.assertEqual(out1, out2)
        self.assertEqual(client.chat.completions.create.call_count, 1)

    def test_no_client_falls_back(self):
        fallback = _legacy_fallback()
        with patch("openai_helper._get_client", return_value=None):
            out = polish_compat_analysis(_sample_facts(), fallback, lang="en")
        self.assertIs(out, fallback)

    def test_max_tokens_higher_for_non_latin_lang(self):
        # Phase 2.5.11.21: 7-section schema needs much bigger budgets.
        # en=2000, non-en=2800 (Hinglish/Devanagari/CJK ~3x token cost).
        facts = _sample_facts()
        captured: dict = {}

        class _FakeResp:
            class _Choice:
                class _Msg:
                    content = '{}'
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
            polish_compat_analysis(facts, _legacy_fallback(), lang="hi")
            self.assertEqual(captured.get("max_tokens"), 2800, "non-en lang must use 2800")
            captured.clear()
            polish_compat_analysis(facts, _legacy_fallback(), lang="hn")
            self.assertEqual(captured.get("max_tokens"), 2800, "hn (Hinglish) must use 2800")
            captured.clear()
            polish_compat_analysis(facts, _legacy_fallback(), lang="en")
            self.assertEqual(captured.get("max_tokens"), 2000, "plain en uses 2000")


# ─────────────────────────────────────────────────────────────────────────────
# DB cache layer (L2 persistence)
# ─────────────────────────────────────────────────────────────────────────────
class TestDbCacheLayer(unittest.TestCase):
    def setUp(self):
        with _cache_lock:
            _cache.clear()

    def test_db_cache_get_no_app_context_returns_none(self):
        from vedic.compat.llm_polish import _db_cache_get
        self.assertIsNone(_db_cache_get("nonexistent_fp_xyz"))

    def test_db_cache_put_no_app_context_swallows(self):
        from vedic.compat.llm_polish import _db_cache_put
        try:
            _db_cache_put("fp_test", {"compatibility_insight": "x",
                                       "strengths": [], "challenges": [],
                                       "marriage_outlook": "y"}, "gpt-4o-mini")
        except Exception as exc:
            self.fail(f"_db_cache_put raised unexpectedly: {exc}")

    def test_db_cache_put_concurrent_duplicate_does_not_raise(self):
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
        good = _good_llm_output()
        from vedic.compat import llm_polish as _lp

        with patch.object(_lp, "_db_cache_get", return_value=good) as mocked_get, \
             patch.object(_lp, "_db_cache_put") as mocked_put:
            client = MagicMock()
            with patch("openai_helper._get_client", return_value=client), \
                 patch.dict(os.environ, {"COMPAT_LLM_POLISH": "1"}):
                out = polish_compat_analysis(_sample_facts(), _legacy_fallback(), lang="en")
        # When L2 returns the raw cached dict, the function should return it
        # as-is (cache write path stores already-coerced 7-section output).
        self.assertEqual(out, good)
        self.assertEqual(client.chat.completions.create.call_count, 0)
        mocked_get.assert_called_once()
        mocked_put.assert_not_called()


if __name__ == "__main__":
    unittest.main()
