"""
Love Reality Pro PDF — GPT polish + chapter depth regen (Milan-style pipeline).
"""
from __future__ import annotations

import hashlib
import json
import logging
import os
import re
from typing import Any

from vedic.love_reality.pdf_text_safe import (
    love_script_directive,
    polish_content_lang,
    sanitize_love_reality_pro_premium,
)
from vedic.compat.llm_polish import (
    _cache_get as _l1_get,
    _cache_put as _l1_put,
    _db_cache_get as _l2_get,
    _db_cache_put as _l2_put,
)
from vedic.compat.premium_chapters import (
    CHAPTER_BODY_KEY,
    normalize_pro_pdf_lang,
    _openai_regen_chapters_depth,
    _parsed_chapter_row_for_key,
)
from vedic.compat.premium_chapters import _PREMIUM_DEPTH_REGEN_MAX_ROUNDS
from vedic.compat.openai_pdf_telemetry import (
    PdfGenOpenAITelemetry,
    merge_pdf_generation_into_meta,
    publish_and_log_pdf_generation,
    stub_meta,
)
from vedic.love_reality.love_section_polish import (
    _deep_analysis_row_en_ok,
    _deep_analysis_row_hi_ok,
    deep_analysis_en_ready,
    deep_analysis_hi_ready,
)

log = logging.getLogger(__name__)

_LOVE_VERSION = "lr_sections_v1"
_DEFAULT_MODEL = os.environ.get("LOVE_REALITY_PREMIUM_MODEL") or os.environ.get(
    "COMPAT_PREMIUM_MODEL", "gpt-4o"
)
# Section 02-only: gpt-4o-mini default (cheap dev). Set LOVE_REALITY_VERDICT_PAGE_QUALITY=1 or
# LOVE_REALITY_VERDICT_PAGE_MODEL=gpt-4o for most natural human prose.
_VERDICT_PAGE_DEFAULT_MODEL = "gpt-4o-mini"
_VERDICT_PAGE_QUALITY_MODEL = "gpt-4o"
LOVE_CHAPTER_KEYS = ["ch1", "ch2", "ch3", "ch4", "ch5", "ch6"]
LOVE_SEMANTIC_KEYS = [
    "love_connection",
    "breakup",
    "loyalty",
    "will_return",
    "future_outcome",
    "red_flags",
]
KEY_BY_CH = {
    "ch1": "love_connection",
    "ch2": "breakup",
    "ch3": "loyalty",
    "ch4": "will_return",
    "ch5": "future_outcome",
    "ch6": "red_flags",
}
_LOVE_MIN_CHAPTER_WORDS = int(os.environ.get("LOVE_REALITY_MIN_CHAPTER_WORDS", "220"))
_LOVE_MIN_CHAPTER_CHARS = int(os.environ.get("LOVE_REALITY_MIN_CHAPTER_CHARS", "1200"))
_LOVE_MIN_PARAGRAPHS = int(os.environ.get("LOVE_REALITY_MIN_PARAGRAPHS", "3"))
_LOVE_MIN_PARA_WORDS = int(os.environ.get("LOVE_REALITY_MIN_PARA_WORDS", "25"))
_BULLET_LINE_RE = re.compile(r"^\s*[-•*]\s+", re.M)
_CHART_SIGNAL_RE = re.compile(
    r"\b(?:Lagna|Moon|Mercury|Venus|Jupiter|Mars|Rahu|Ketu|7th|12th|Upapada|UL|dasha|house)\b",
    re.I,
)
_BANNED_ELITE_PHRASES = (
    "fraught",
    "volatile",
    "landscape",
    "inherent",
    "furthermore",
    "evidenced",
    "mitigate",
    "propensity",
    "paramount",
    "paradigm",
    "underscores",
    "navigate",
    "dynamics",
    "trajectory",
    "facilitate",
    "leverage",
    "holistic",
    "multifaceted",
    "notwithstanding",
)


def _env_flag(name: str, default: str = "0") -> bool:
    return (os.environ.get(name) or default).strip().lower() in ("1", "true", "yes", "on")


def _polish_enabled() -> bool:
    env = (os.environ.get("LOVE_REALITY_PREMIUM_POLISH") or "").strip().lower()
    if env in ("0", "false", "no", "off"):
        return False
    if env in ("1", "true", "yes", "on"):
        return True
    return _env_flag("COMPAT_PREMIUM_POLISH", "1")


def _depth_regen_enabled() -> bool:
    if not _env_flag("LOVE_REALITY_DEPTH_REGEN", ""):
        return _env_flag("COMPAT_PREMIUM_DEPTH_REGEN", "1")
    return _env_flag("LOVE_REALITY_DEPTH_REGEN", "1")


def _cache_disabled() -> bool:
    return _env_flag("LOVE_REALITY_CACHE_DISABLE") or _env_flag(
        "COMPAT_PREMIUM_CACHE_DISABLE"
    )


def _verdict_page_dev_mode() -> bool:
    """Local preview: shorter output + lower max_tokens (cheaper smoke tests)."""
    return _env_flag("LOVE_REALITY_VERDICT_PAGE_DEV")


def _verdict_page_prompt_fingerprint(lang: str) -> str:
    """Auto-invalidate file cache when Section 02 prompt text changes."""
    blob = _build_verdict_page_only_system_prompt(lang, include_dev_note=False)
    return hashlib.sha256(blob.encode()).hexdigest()[:10]


def _love_polish_fingerprint(bundle: dict, lang: str, model: str) -> str:
    """Stable key from engine scores + lang + model (Milan-style L1/L2 reuse)."""
    from vedic.love_reality.love_section_polish import _ASSEMBLY_VER

    lc = bundle.get("love_compatibility") or {}
    bu = bundle.get("breakup_chances") or {}
    ly = bundle.get("loyalty_check") or {}
    wr = bundle.get("will_return") or {}
    fo = bundle.get("future_outcome") or {}
    p1 = bundle.get("p1") or {}
    p2 = bundle.get("p2") or {}
    parts = [
        f"love={_LOVE_VERSION}",
        f"assembly={_ASSEMBLY_VER}",
        f"model={model}",
        f"lang={lang}",
        p1.get("nakshatra", ""),
        p1.get("moonSign", "") or p1.get("rashi", ""),
        p2.get("nakshatra", ""),
        p2.get("moonSign", "") or p2.get("rashi", ""),
        f"lc={lc.get('score', '')}",
        f"bu={bu.get('breakup_score', bu.get('score', ''))}",
        f"ly={ly.get('loyalty_score', ly.get('score', ''))}",
        f"wr={wr.get('return_probability', wr.get('score', ''))}",
        f"fo={fo.get('future_score', fo.get('score', ''))}",
        f"aff={((bundle.get('couple_signals') or {}).get('combined_affliction', ''))}",
    ]
    raw = "|".join(str(x) for x in parts).encode("utf-8")
    return "love_" + hashlib.sha1(raw).hexdigest()


def _love_polish_cache_depth_ok(hit: dict) -> bool:
    """Reject shallow cached polish (treat as miss)."""
    meta = hit.get("_meta") or {}
    assembly = str(meta.get("assembly") or "")
    if assembly.startswith("lr_sections_v"):
        from vedic.love_reality.love_section_polish import _assembly_depth_ok

        return _assembly_depth_ok(hit)
    chapters = hit.get("chapters") or []
    if len(chapters) < 6:
        return False
    ok_bodies = 0
    for ch in chapters:
        body = (ch.get(CHAPTER_BODY_KEY) or ch.get("chapter_body") or "").strip()
        if _love_chapter_depth_failure_reason(body) is None:
            ok_bodies += 1
    return ok_bodies >= 6


def _empty_shell(model: str, reason: str) -> dict[str, Any]:
    return {
        "hidden_truth": "",
        "chapters": [],
        "special": [],
        "damage": [],
        "practical": [],
        "verdict": "",
        "_meta": {"model": model, "version": _LOVE_VERSION, "reason": reason},
    }


def _facts_summary(bundle: dict) -> str:
    lc = bundle.get("love_compatibility") or {}
    bu = bundle.get("breakup_chances") or {}
    ly = bundle.get("loyalty_check") or {}
    wr = bundle.get("will_return") or {}
    fo = bundle.get("future_outcome") or {}
    p1 = bundle.get("p1") or {}
    p2 = bundle.get("p2") or {}

    def _lines(label: str, d: dict) -> list[str]:
        field_labels = {
            "score": "Score",
            "breakup_score": "Breakup score",
            "loyalty_score": "Loyalty score",
            "return_probability": "Return probability",
            "future_score": "Future score",
            "risk_level": "Risk level",
            "loyalty_level": "Loyalty level",
            "return_chance": "Return chance",
            "outcome": "Outcome",
            "current_phase": "Current phase",
            "emotional_summary": "Summary",
        }
        out = [f"=== {label} ==="]
        for k in ("score", "breakup_score", "loyalty_score", "return_probability", "future_score"):
            if k in d and d[k] is not None:
                out.append(f"{field_labels[k]}: {d[k]}")
        for k in ("risk_level", "loyalty_level", "return_chance", "outcome", "current_phase"):
            if d.get(k):
                out.append(f"{field_labels[k]}: {d[k]}")
        if d.get("emotional_summary"):
            out.append(f"{field_labels['emotional_summary']}: {d['emotional_summary']}")
        reasons = d.get("reasons") or []
        if reasons:
            out.append("reasons:")
            for r in reasons[:12]:
                out.append(f"  - {r}")
        return out

    rc = bundle.get("reader_context") or {}

    parts = [
        f"p1_name: {p1.get('name', 'You')}",
        f"p1_moon: {p1.get('moonSign') or p1.get('rashi', '?')}",
        f"p1_nakshatra: {p1.get('nakshatra', '?')}",
        f"p2_name: {p2.get('name', 'Partner')}",
        f"p2_moon: {p2.get('moonSign') or p2.get('rashi', '?')}",
        f"p2_nakshatra: {p2.get('nakshatra', '?')}",
    ]
    if rc.get("primary_gender_inferred"):
        parts.append(
            f"READER_PRIMARY_GENDER (p1 profile, tone only): {rc.get('primary_gender_inferred')} "
            f"(raw: {rc.get('primary_gender_raw') or 'n/a'})"
        )
    if rc.get("will_return_note"):
        parts.append(
            "WILL_RETURN_REALITY_PRIOR: ~90% of estranged situations do not see X return in a real way; "
            "match prose to return_probability — only strong reunion yogas justify optimistic reunion language."
        )
    ledger = lc.get("score_ledger") or []
    if ledger:
        parts.append("=== LOVE_SCORE_LEDGER (cite when explaining cover score) ===")
        for row in ledger[:16]:
            if isinstance(row, dict):
                if row.get("base") is not None:
                    parts.append(f"  {row.get('label')}: base {row.get('base')} — {row.get('note', '')}")
                elif row.get("delta") is not None:
                    parts.append(f"  {row.get('label')}: {row.get('delta'):+} — {row.get('note', '')}")
                else:
                    parts.append(f"  {row.get('label')}: {row.get('note', '')}")
    bridge = bundle.get("narrative_bridge")
    if bridge:
        parts.append(f"NARRATIVE_BRIDGE (use in verdict if scores conflict): {bridge}")
    parts.extend(
        [
            *_lines("LOVE_COMPATIBILITY", lc),
            *_lines("BREAKUP_CHANCES", bu),
            *_lines("LOYALTY_CHECK", ly),
            *_lines("WILL_RETURN", wr),
            *_lines("FUTURE_OUTCOME", fo),
            *_lines("HIDDEN_RED_FLAGS", bundle.get("hidden_red_flags") or {}),
        ],
    )
    ly_locks = ly.get("narrative_locks") or []
    if ly_locks:
        parts.append("=== LOYALTY_NARRATIVE_LOCKS (MANDATORY) ===")
        for line in ly_locks:
            parts.append(f"  - {line}")
    if ly.get("loyalty_score") is not None and int(ly.get("loyalty_score") or 0) < 52:
        parts.append(
            "LOYALTY_CHAPTER_RULE: loyalty_score is LOW — do NOT write that any partner is "
            "'naturally loyal', 'devoted by nature', or 'faithful because Venus is strong'. "
            "Venus in own sign (e.g. Taurus) = attachment STYLE only, NOT proof of real-world loyalty."
        )
    k1 = bundle.get("kundli_p1") or {}
    k2 = bundle.get("kundli_p2") or {}
    try:
        parts.append(
            "<STRUCTURED_CHART_DATA>\n"
            + json.dumps({"p1_planets": k1.get("planets"), "p2_planets": k2.get("planets")}, ensure_ascii=False)[:12000]
            + "\n</STRUCTURED_CHART_DATA>"
        )
    except Exception:
        pass
    return "\n".join(parts)


def _verdict_page_facts_summary(bundle: dict, lang: str = "en") -> str:
    """Plain-language couple facts for Section 02 LLM — no ledger/bonus labels to parrot."""
    lang_lane = polish_content_lang(normalize_pro_pdf_lang(lang))
    lc = bundle.get("love_compatibility") or {}
    bu = bundle.get("breakup_chances") or {}
    ly = bundle.get("loyalty_check") or {}
    wr = bundle.get("will_return") or {}
    fo = bundle.get("future_outcome") or {}
    rf = bundle.get("hidden_red_flags") or {}
    p1 = bundle.get("p1") or {}
    p2 = bundle.get("p2") or {}

    def _score(d: dict, *keys: str) -> int | None:
        for k in keys:
            if d.get(k) is not None:
                try:
                    return int(d[k])
                except (TypeError, ValueError):
                    pass
        return None

    def _reasons_plain(d: dict, limit: int = 4) -> list[str]:
        out: list[str] = []
        for r in (d.get("reasons") or [])[:limit]:
            t = str(r).strip()
            if t:
                out.append(t)
        summ = str(d.get("emotional_summary") or "").strip()
        if summ and summ not in out:
            out.insert(0, summ)
        return out

    love = _score(lc, "score")
    breakup = _score(bu, "breakup_score", "score")
    loyalty = _score(ly, "loyalty_score", "score")
    reunion = _score(wr, "return_probability", "score")
    future = _score(fo, "future_score", "score")

    p1_name = str(p1.get("name") or "Partner A").strip()
    p2_name = str(p2.get("name") or "Partner B").strip()
    if lang_lane == "hn":
        lines = [
            "OUTPUT LANGUAGE: natural Roman Hinglish ONLY (Latin script). Poori JSON output Hinglish me — English paragraphs forbidden.",
            "Is specific couple ke liye likho. Live consultation notes jaisa.",
            "",
            f"PRIMARY READER (p1 / pehli kundli — report owner): {p1_name}",
            f"Partner (p2 / doosri kundli): {p2_name}",
            f"~70% prose {p1_name} ki side se — woh kya feel karte hain, unka chart kaise react karta hai.",
            f"{p2_name} ko explain karo {p1_name} ke experience ke through — equal airtime nahi.",
            "",
            f"{p1_name} Moon: {p1.get('moonSign') or p1.get('rashi', '?')} · nakshatra {p1.get('nakshatra', '?')}",
            f"{p2_name} Moon: {p2.get('moonSign') or p2.get('rashi', '?')} · nakshatra {p2.get('nakshatra', '?')}",
        ]
        if love is not None:
            lines.append(f"Dono ke beech emotional pull: lagbhag {love}/100.")
        for r in _reasons_plain(lc, 3):
            lines.append(f"Chemistry note: {r}")
        if breakup is not None:
            lines.append(
                f"Friction separation ki taraf badh sakti hai: lagbhag {breakup}/100 (zyada = zyada strain)."
            )
        for r in _reasons_plain(bu, 2):
            lines.append(f"Friction pattern: {r}")
        if loyalty is not None:
            lines.append(f"Pressure me trust/consistency: lagbhag {loyalty}/100.")
        for r in _reasons_plain(ly, 2):
            lines.append(f"Trust note: {r}")
        if reunion is not None:
            lines.append(
                f"Agar alag ho gaye to genuine reconnection: lagbhag {reunion}/100 — "
                "honest likho; zyada cases me real return nahi hota."
            )
        for r in _reasons_plain(wr, 2):
            lines.append(f"Reconnection note: {r}")
        if future is not None:
            lines.append(f"Long-term bond direction: lagbhag {future}/100.")
        for r in _reasons_plain(fo, 2):
            lines.append(f"Long-term note: {r}")
        for r in _reasons_plain(rf, 2):
            lines.append(f"Hidden friction (gently naam do): {r}")
        bridge = str(bundle.get("narrative_bridge") or "").strip()
        if bridge:
            lines.append(f"Timing / short-term friction vs long hope: {bridge}")
        for row in (lc.get("score_ledger") or [])[:6]:
            if not isinstance(row, dict):
                continue
            note = str(row.get("note") or row.get("label") or "").strip()
            if note:
                lines.append(f"Background factor ('bonus' / '+N' mat bolo): {note}")
        ly_low = loyalty is not None and loyalty < 52
        if ly_low:
            lines.append(
                "Important: trust weak hai — kisi ko 'naturally loyal' ya 'devoted by nature' mat bolo."
            )
    elif lang_lane == "hi":
        lines = [
            "OUTPUT LANGUAGE: पूरी JSON output देवनागरी हिंदी में — Roman वाक्य मना (नाम/स्कोर Latin ठीक)।",
            "इस विशिष्ट जोड़े के लिए लिखें। लाइव परामर्श नोट्स जैसा।",
            "",
            f"PRIMARY READER (p1 / पहली कुंडली): {p1_name}",
            f"Partner (p2 / दूसरी कुंडली): {p2_name}",
            f"~70% prose {p1_name} की दृष्टि से — वे क्या महसूस करते हैं, उनका चार्ट कैसे react करता है।",
            f"{p2_name} को {p1_name} के अनुभव के ज़रिए समझाएँ — बराबर समय नहीं।",
            "",
            f"{p1_name} Moon: {p1.get('moonSign') or p1.get('rashi', '?')} · nakshatra {p1.get('nakshatra', '?')}",
            f"{p2_name} Moon: {p2.get('moonSign') or p2.get('rashi', '?')} · nakshatra {p2.get('nakshatra', '?')}",
        ]
        if love is not None:
            lines.append(f"दोनों के बीच भावनात्मक खिंचाव: लगभग {love}/100।")
        for r in _reasons_plain(lc, 3):
            lines.append(f"Chemistry note: {r}")
        if breakup is not None:
            lines.append(f"अलग होने का दबाव: लगभग {breakup}/100 (ज़्यादा = ज़्यादा तनाव)।")
        for r in _reasons_plain(bu, 2):
            lines.append(f"Friction pattern: {r}")
        if loyalty is not None:
            lines.append(f"दबाव में भरोसा: लगभग {loyalty}/100।")
        for r in _reasons_plain(ly, 2):
            lines.append(f"Trust note: {r}")
        if reunion is not None:
            lines.append(
                f"अलग होने पर वापसी की संभावना: लगभग {reunion}/100 — "
                "ईमानदार लिखें; ज़्यादातर मामलों में असली वापसी नहीं होती।"
            )
        for r in _reasons_plain(wr, 2):
            lines.append(f"Reconnection note: {r}")
        if future is not None:
            lines.append(f"लंबी अवधि की दिशा: लगभग {future}/100।")
        for r in _reasons_plain(fo, 2):
            lines.append(f"Long-term note: {r}")
        for r in _reasons_plain(rf, 2):
            lines.append(f"छिपा हुआ तनाव (सौम्यता से नाम लें): {r}")
        bridge = str(bundle.get("narrative_bridge") or "").strip()
        if bridge:
            lines.append(f"Timing / short-term vs long hope: {bridge}")
        for row in (lc.get("score_ledger") or [])[:6]:
            if not isinstance(row, dict):
                continue
            note = str(row.get("note") or row.get("label") or "").strip()
            if note:
                lines.append(f"Background factor ('bonus' / '+N' मत बोलें): {note}")
        ly_low = loyalty is not None and loyalty < 52
        if ly_low:
            lines.append(
                "Important: भरोसा कमज़ोर है — किसी को 'naturally loyal' मत कहें।"
            )
    else:
        lines = [
            "Write for this specific couple. Sound like live consultation notes.",
            "",
            f"PRIMARY READER (p1 / first kundli — report owner): {p1_name}",
            f"Partner (p2 / second kundli): {p2_name}",
            f"~70% of prose FROM {p1_name}'s side — what they feel, how their chart reacts, what lands on them.",
            f"Explain {p2_name} in relation to how {p1_name} experiences the bond — not equal airtime.",
            "",
            f"{p1_name} Moon: {p1.get('moonSign') or p1.get('rashi', '?')} · nakshatra {p1.get('nakshatra', '?')}",
            f"{p2_name} Moon: {p2.get('moonSign') or p2.get('rashi', '?')} · nakshatra {p2.get('nakshatra', '?')}",
        ]

        if love is not None:
            lines.append(f"Overall emotional pull between them: roughly {love} out of 100.")
        for r in _reasons_plain(lc, 3):
            lines.append(f"Pull / chemistry note: {r}")

        if breakup is not None:
            lines.append(f"How easily friction could escalate toward separation: roughly {breakup} out of 100 (higher = more strain).")
        for r in _reasons_plain(bu, 2):
            lines.append(f"Friction pattern: {r}")

        if loyalty is not None:
            lines.append(f"Trust and consistency under pressure: roughly {loyalty} out of 100.")
        for r in _reasons_plain(ly, 2):
            lines.append(f"Trust note: {r}")

        if reunion is not None:
            lines.append(
                f"If they were apart, odds of a genuine reconnection: roughly {reunion} out of 100 — "
                "write honestly; most estranged situations do not see a real return."
            )
        for r in _reasons_plain(wr, 2):
            lines.append(f"Reconnection note: {r}")

        if future is not None:
            lines.append(f"Longer-term direction of the bond: roughly {future} out of 100.")
        for r in _reasons_plain(fo, 2):
            lines.append(f"Long-term note: {r}")

        for r in _reasons_plain(rf, 2):
            lines.append(f"Hidden friction to name gently: {r}")

        bridge = str(bundle.get("narrative_bridge") or "").strip()
        if bridge:
            lines.append(f"Timing / tension between short-term friction and longer hope: {bridge}")

        for row in (lc.get("score_ledger") or [])[:6]:
            if not isinstance(row, dict):
                continue
            note = str(row.get("note") or row.get("label") or "").strip()
            if note:
                lines.append(f"Background factor (do not say 'bonus' or '+N'): {note}")

        ly_low = loyalty is not None and loyalty < 52
        if ly_low:
            lines.append(
                "Important: trust is weak on this chart — do not call either partner "
                "'naturally loyal' or 'devoted by nature'."
            )

    k1 = bundle.get("kundli_p1") or {}
    k2 = bundle.get("kundli_p2") or {}
    try:
        planets_note = []
        for label, k in ((p1_name, k1), (p2_name, k2)):
            pl = k.get("planets") or []
            if isinstance(pl, list) and pl:
                snippets = []
                for p in pl[:12]:
                    if isinstance(p, dict):
                        nm = p.get("name") or p.get("planet")
                        sign = p.get("sign") or p.get("rashi")
                        house = p.get("house")
                        if nm:
                            bit = f"{nm} in {sign}" if sign else str(nm)
                            if house is not None:
                                bit += f" (house {house})"
                            snippets.append(bit)
                if snippets:
                    planets_note.append(f"{label}: " + "; ".join(snippets[:8]))
        if planets_note:
            hdr = (
                "Key placements (plain words me interpret karo — output me list dump mat karo):"
                if lang_lane == "hn"
                else "Key placements (interpret in plain words — do not dump as a list in output):"
            )
            lines.append(hdr)
            lines.extend(f"  {x}" for x in planets_note)
    except Exception:
        pass

    return "\n".join(lines)


def _love_word_count(text: str) -> int:
    return len(re.findall(r"\b[\w']+\b", text or ""))


def _love_meaningful_paragraph_count(body: str) -> int:
    parts = [p.strip() for p in re.split(r"\n\s*\n", (body or "").strip()) if p.strip()]
    return sum(1 for p in parts if _love_word_count(p) >= _LOVE_MIN_PARA_WORDS)


def _love_is_bullet_heavy(body: str) -> bool:
    t = (body or "").strip()
    if not t:
        return False
    lines = [ln.strip() for ln in t.splitlines() if ln.strip()]
    if not lines:
        return False
    bullet_lines = sum(1 for ln in lines if _BULLET_LINE_RE.match(ln))
    if bullet_lines >= 3 and bullet_lines >= len(lines) * 0.55:
        return True
    return t.count("•") >= 4 and _love_word_count(t) < _LOVE_MIN_CHAPTER_WORDS


def _love_chapter_depth_failure_reason(body: str) -> str | None:
    t = (body or "").strip()
    if not t:
        return "empty"
    wc = _love_word_count(t)
    if wc < _LOVE_MIN_CHAPTER_WORDS:
        return f"words:{wc}<{_LOVE_MIN_CHAPTER_WORDS}"
    if len(t) < _LOVE_MIN_CHAPTER_CHARS:
        return f"chars:{len(t)}<{_LOVE_MIN_CHAPTER_CHARS}"
    mpc = _love_meaningful_paragraph_count(t)
    if mpc < _LOVE_MIN_PARAGRAPHS:
        return f"paras:{mpc}<{_LOVE_MIN_PARAGRAPHS}"
    if _love_is_bullet_heavy(t):
        return "bullet_heavy"
    if len(_CHART_SIGNAL_RE.findall(t)) < 2:
        return "chart_signals<2"
    return None


def _normalize_chapter_body_from_llm(body: str) -> str:
    if not body:
        return ""
    if isinstance(body, list):
        body = "\n\n".join(str(x).strip() for x in body if str(x).strip())
    text = str(body).strip()
    text = re.sub(r"\n{3,}", "\n\n", text)
    if _love_is_bullet_heavy(text):
        lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
        prose_bits = [
            re.sub(r"^[-•*]\s+", "", ln).strip()
            for ln in lines
            if _BULLET_LINE_RE.match(ln)
        ]
        if prose_bits:
            grouped: list[str] = []
            for i in range(0, len(prose_bits), 2):
                grouped.append(" ".join(prose_bits[i : i + 2]))
            text = "\n\n".join(grouped)
    return text


def _parse_love_premium_response(parsed: dict) -> dict:
    chapters = parsed.get("chapters")
    if isinstance(chapters, list):
        for ch in chapters:
            if not isinstance(ch, dict):
                continue
            raw = ch.get(CHAPTER_BODY_KEY) or ch.get("full_read") or ch.get("body") or ""
            normalized = _normalize_chapter_body_from_llm(raw)
            ch[CHAPTER_BODY_KEY] = normalized
            if ch.get("full_read"):
                ch["full_read"] = normalized
    practical = parsed.get("practical")
    if isinstance(practical, str) and practical.strip():
        parsed["practical"] = [practical.strip()]
    elif isinstance(practical, list):
        parsed["practical"] = [str(x).strip() for x in practical if str(x).strip()]
    return parsed


def _cro_voice_rules(lang: str) -> str:
    """Shared CRO + Hinglish voice contract for primary and depth-regen prompts."""
    lang = polish_content_lang(lang)
    banned = ", ".join(f'"{w}"' for w in _BANNED_ELITE_PHRASES)
    if lang == "hn":
        return f"""VOICE & LANGUAGE (NON-NEGOTIABLE):
- Aap ek elite relationship counselor hain jo Indian user se seedha, raw, emotionally hitting baat karta hai.
- Output 100% natural Hinglish hona chahiye — jaise North India me WhatsApp ya face-to-face baat hoti hai (Roman script).
- Direct address: "Aap" (primary reader) aur "Unka/Unki" (partner). Kabhi textbook English tone mat use karo.
- Latin letters ONLY — kabhi Devanagari Unicode mat likho (PDF render nahi karta).
- Banned words/phrases (kabhi mat likho): {banned}.
- Banned filler: "communication is important", "open communication", "mutual understanding", "with effort things improve" — jab tak kisi specific grah/house se tied na ho.
- Tone: deeply personal, brutally honest, conversion-focused — reader ko lagna chahiye koi unki real story samajh raha hai, textbook padh rahe hain nahi."""
    return f"""VOICE & LANGUAGE (NON-NEGOTIABLE):
- You are an elite relationship counselor speaking plainly to an Indian user — warm, direct, emotionally hitting, zero textbook English.
- Write in simple conversational English (not Hinglish). Address the reader as "You" and the partner as "They/Their".
- Banned words/phrases (never use): {banned}.
- Banned filler: generic therapy-speak unless tied to a named chart placement.
- Tone: deeply personal, brutally honest, conversion-focused — the reader must feel seen, not lectured."""


# --- Section 02 (Final Verdict) LLM design contract — DO NOT over-constrain ---
# Voice: senior astrologer persona + ONE golden few-shot (_cro_verdict_page_few_shot).
# Quality lever = example tone/style, not 20+ rules. Coach-phrase + anti-AI vocab bans only.
# No regex post-scrub on LLM output (causes artifacts). Min words ~120.
# API: temp ~0.78, presence_penalty ~0.5, frequency_penalty ~0.3 (non-gpt-5).
# Target: chart observation ✅ | engine jargon ❌ | therapist/coach tone ❌
_VERDICT_PAGE_MIN_PRACTICAL_WORDS = 120
_VERDICT_PAGE_BANNED_PHRASES = (
    "both partners will benefit",
    "important to note",
    "future holds potential",
    "growth opportunity",
    "stronger bond",
    "healthy communication",
    "navigate challenges",
    "emerge stronger",
    "healing journey",
    "relationship check-in",
    "open and honest conversations",
    "significant opportunity",
    "actionable guidance",
    "what to do next",
    "communication tips",
    "relationship recommendations",
)
_VERDICT_PAGE_ANTI_AI_WORDS = (
    "emotional pacing",
    "contrast in emotional pacing",
    "push-pull dynamic",
    "avalanche of emotions",
    "underlying tension",
    "testament",
    "notable mismatch",
    "resonance",
    "strong emotional connection",
    "noticeable mismatch",
    "rhythm clash",
    "conflict resolution differently",
    "engage honestly through those friction points",
    "as long as both of you are willing",
    "snowball into bigger issues",
)


def _verdict_page_interpretation_first(lang: str) -> str:
    """Interpretation-first contract — reverses coach/therapist drift."""
    if lang == "hn":
        return """INTERPRETATION PEHLE, ADVICE BAAD ME (critical):
- Primary goal interpretation hai, advice nahi.
- ~80% section me chart pattern real life me kya dikhta hai — woh explain karo.
- Kam se kam ~20% par practical implication — observation ke andar naturally weave karo.
- Therapist, coach, counselor, ya self-help author ki tarah mat likho — chart review karte astrologer jaisa.
- Pehle observed dynamics describe karo. Koi implication chhota ho aur chart se naturally aaye.
- Motivational, reassurance, ya future-hope language avoid karo.

Mat likho jaise aapka kaam hai:
- "practical advice dena" / "actionable guidance" / "what to do next"
- "communication tips" / "relationship recommendations" / "check-in" suggest karna"""
    if lang == "hi":
        return """INTERPRETATION PEHLE, ADVICE BAAD ME (critical — hn/en jitni depth):
- Primary goal interpretation hai, advice nahi.
- ~80% section me chart pattern real life me kya dikhta hai — woh explain karo.
- Kam se kam ~20% par practical implication — observation ke andar naturally weave karo.
- Therapist/coach tone nahi — chart review karte astrologer jaisa.
- Pehle observed dynamics describe karo. Implication chhota ho aur chart se naturally aaye.
- Motivational ya future-hope language avoid karo."""
    return """INTERPRETATION FIRST, NOT ADVICE (critical):
- Primary goal is interpretation, not advice.
- Spend ~80% of the section explaining what the chart pattern means in real life.
- Spend at most ~20% on practical implications — woven into observations, not a separate checklist.
- Write like an astrologer reviewing a chart, not a therapist, coach, counselor, or self-help author.
- Describe observed dynamics first. Any implication should be brief and arise naturally from the chart.
- Avoid motivational language, reassurance language, and future-hope language.

Do NOT write as if your job is to:
- "Give practical advice" / "Provide actionable guidance" / "Tell them what to do next"
- "Offer communication tips" / "Provide relationship recommendations" / "Suggest a check-in"
"""


def _verdict_page_banned_block(lang: str) -> str:
    phrases = ", ".join(f'"{p}"' for p in _VERDICT_PAGE_BANNED_PHRASES)
    ai_words = ", ".join(f'"{w}"' for w in _VERDICT_PAGE_ANTI_AI_WORDS)
    if lang == "hn":
        return f"""BANNED PHRASES (coach/AI smell — kabhi mat likho):
{phrases}

ANTI-AI VOCABULARY (corporate/psychology buzzwords — strictly forbidden):
{ai_words}
- Sentences mat kholo: "However", "In contrast", "Despite", "Furthermore", "Yet".
- Chai pe baith kar samjhane wala tone — short, direct Hinglish sentences."""
    if lang == "hi":
        return f"""BANNED PHRASES (coach/AI smell — kabhi mat likho):
{phrases}

ANTI-AI VOCABULARY (corporate/psychology buzzwords — strictly forbidden):
{ai_words}
- Sentences mat kholo: "However", "In contrast", "Despite", "Furthermore", "Yet".
- Devanagari Hindi — short, direct sentences; hn/en jitni depth, chhota summary mat."""
    return f"""BANNED PHRASES (coach/AI smell — never write):
{phrases}

ANTI-AI VOCABULARY (corporate/psychology buzzwords — strictly forbidden):
{ai_words}
- Do not open sentences with: "However", "In contrast", "Despite", "Furthermore", "Yet".
- Short, conversational sentences — like an experienced counselor over tea, not a report."""


def _verdict_page_model() -> str:
    explicit = (os.environ.get("LOVE_REALITY_VERDICT_PAGE_MODEL") or "").strip()
    if explicit:
        return explicit
    if _env_flag("LOVE_REALITY_VERDICT_PAGE_QUALITY"):
        return _VERDICT_PAGE_QUALITY_MODEL
    return _VERDICT_PAGE_DEFAULT_MODEL


def _cro_verdict_page_consultation_persona(lang: str) -> str:
    """Premium consultation voice — astrologer observation, not coach."""
    interp = _verdict_page_interpretation_first(lang)
    banned = _verdict_page_banned_block(lang)
    if lang == "hn":
        return f"""Aap ek senior relationship astrologer hain jo premium paid consultation report likh rahe ho.

Aise likho jaise aapne personally dono charts padhe hon aur real clients ko findings explain kar rahe ho.

Goal astrology terms se impress karna nahi hai.
Goal hai reader ko samjhana ki relationship daily life me actually kaise behave karti hai.

Rules:
- Natural, human, thoughtful, confident — experienced astrologer jaisa, AI assistant nahi.
- Astrology insight ka source ho, par sab kuch plain language me explain karo.
- Har astrological observation ke baad likho yeh real life me kaise dikhega.
- Focus: emotions, communication, trust, attraction, conflict patterns, expectations, attachment, timing.

Avoid:
- software/engine language, scorecard language, technical astrology dumps
- generic motivational writing, marketing language, exaggerated destiny claims
- bonus, boost, ledger, +12, stress window, narrative bridge, synastry anchor, compatibility engine, matrix

- Mat kholo: "The chart indicates…" / "The analysis shows…" / "There is a significant opportunity…"
- Mat likho: "honest conversations", "Mercury stress", "reconnect and strengthen", "misunderstandings" baar-baar — har paragraph naya insight de.

Instead, explain kya actually dono logon ke beech ho raha hai.

ASTROLOGER, COACH NAHI (critical):
Write like an astrologer explaining a real couple — not a coach, therapist, report generator, or AI assistant.
Observations ko advice se upar rakho. Upay chart interpretation se naturally aaye — alag checklist ki tarah nahi.

- Relationship coach / therapist ki tarah mat likho — chart pattern interpret karo.
- Kuch suggest karne se pehle pattern KYUN exist karta hai — explain karo.
- Scripted dialogue mat do. Generic communication frameworks mat use karo.

{interp}

{banned}

UNIFIED FLOW (critical — PDF me ek hi note dikhega, alag advice box nahi):
- `verdict` + `practical[]` milkar EK consultation note jaisa padho — interpretation aur observation same flow me.
- `practical[]` alag section, coaching block, ya "What To Do Next" mat likho; note ke aage ke paragraphs hon.
- "Key Takeaway:" label mat use karo — end naturally with one plain closing line.
- Mat kholo: "[Name], tumhara X Moon…" / "[Name], your X Moon…" / "real spark" / "You both feel…"
- "Mercury stress" / "stress window" / "stress windows" mat likho — "Mercury ke phases" / "communication-sensitive weeks".

OBSERVATIONAL ASTROLOGER VOICE:
- Coach ki tarah instruct mat karo ("try karo", "check in", "lean into", "open conversations can help").
- Pattern describe karo — chart, daily life, timing. Names + nakshatra facts se naturally weave karo.
- Har paragraph conclusion dena zaroori nahi — kabhi observation par hi khatam karo.

Same insight repeat mat karo. Paragraphs concise aur meaningful.

Reader feel kare: 'Ek real astrologer ne is relationship ko samjha aur chart se explain kiya.'
Reader kabhi na feel kare: 'Yeh software engine ne generate kiya.'"""
    if lang == "hi":
        return f"""Aap ek senior relationship astrologer hain jo premium paid consultation report likh rahe ho.
Output 100% Devanagari Hindi — Roman script sirf names/scores ke liye. Hinglish (hn) aur English reports jitni depth mandatory.

Aise likho jaise aapne personally dono charts padhe hon aur real clients ko findings explain kar rahe ho.

Goal: reader ko samjhana ki relationship daily life me actually kaise behave karti hai — har chart point ke baad real life example.

Rules:
- Natural, human, thoughtful — experienced astrologer, AI assistant nahi.
- Har astrological observation ke baad likho yeh real life me kaise dikhega.
- Focus: emotions, communication, trust, conflict patterns, timing.

Avoid: software/engine language, scorecard dumps, generic motivational writing, therapy/coach tone.

{interp}

{banned}

UNIFIED FLOW: `verdict` + `practical[]` milkar EK consultation note — hn/en jitni lambai aur detail.
Reader feel kare: ek real astrologer ne chart se explain kiya."""
    return f"""You are a senior relationship astrologer writing a premium paid consultation report.

Write as if you personally studied these two charts and are explaining your findings to real clients.

Your goal is not to impress with astrology terminology.
Your goal is to help the reader understand how the relationship actually behaves in daily life.

Rules:
- Sound natural, human, thoughtful, and confident.
- Write like an experienced astrologer, not an AI assistant.
- Use astrology as the source of insight, but explain everything in plain language.
- After every astrological observation, explain how it may appear in real life.
- Focus on emotions, communication, trust, attraction, conflict patterns, expectations, attachment styles, and timing.

Avoid:
- software/engine language
- scorecard language
- technical astrology dumps
- generic motivational writing
- marketing language
- exaggerated destiny claims
- bonus, boost, ledger, +12, stress window, narrative bridge, synastry anchor, compatibility engine, matrix

Do not write like:
"The chart indicates..."
"The analysis shows..."
"There is a significant opportunity..."
"There is a strong emotional connection..."

Do not repeat these filler phrases across paragraphs: "honest conversations", "misunderstandings", "silence after conflict", "Mercury stress", "reconnect and strengthen". Each paragraph must add a new insight.

Instead, explain what is actually happening between the two people.

ASTROLOGER, NOT COACH (critical):
Write like an astrologer explaining a real couple, not like a coach, therapist, report generator, or AI assistant.
Prioritize observations over advice. Advice should emerge naturally from the chart interpretation rather than appearing as a separate checklist.

Do not write as a relationship coach or therapist — interpret chart patterns.
Explain why a pattern exists before suggesting what to do.
Never write quoted dialogue scripts ("Aarav should say…").

{interp}

{banned}

UNIFIED FLOW (critical — PDF renders as ONE note, not Analysis + Advice boxes):
- `verdict` + `practical[]` must read as ONE continuous consultation note — interpretation in the same voice throughout.
- Do NOT write `practical[]` as a separate advice section, coaching block, or "What To Do Next"; continue the note as further paragraphs.
- Do NOT use a "Key Takeaway:" label — end with one natural closing sentence if needed.
- Do NOT open with "[Name], your X Moon…" / "has a real spark" / "You both feel…"
- Do NOT write "Mercury stress" / "stress window" / "stress windows" — say "Mercury periods" or "communication-sensitive weeks".

OBSERVATIONAL ASTROLOGER VOICE:
- Do NOT instruct like a coach ("try to", "check in", "lean into", "honest conversations can help").
- Describe patterns — chart, daily life, timing. Weave names and nakshatra from facts naturally.
- Not every paragraph needs a conclusion — sometimes end on an observation.

Do not repeat the same insight multiple times. Keep paragraphs concise.

The reader should feel:
'A real astrologer understood this relationship and explained it through the chart.'

The reader should never feel:
'This was generated by a software engine.'"""


def _verdict_page_primary_reader(lang: str) -> str:
    """p1 = first kundli / report owner — they get most of the voice and airtime."""
    if lang == "hn":
        return """PRIMARY READER = p1 (pehli kundli — yeh report JISKE liye hai):
- User message me `p1_name` wahi insaan hai — unse "Aap" bol kar baat karo (ya unka naam + aap).
- `p2_name` partner hai — "Unka/Unki", "wo", ya naam se; unhe equal paragraph time mat do.
- ~70% note p1 ke lens se: unka feel, unka gussa/urge, unke chart se un par kya padta hai, jab partner doori banata hai to AAPKO kya lagta hai.
- Partner ko p1 ke experience ke around explain karo — neutral case study nahi."""
    if lang == "hi":
        return """PRIMARY READER = p1 (pehli kundli — yeh report JISKE liye hai):
- User message me `p1_name` wahi insaan hai — unse "Aap" bol kar baat karo (Devanagari).
- `p2_name` partner hai — "Unka/Unki", "wo", ya naam se; unhe equal paragraph time mat do.
- ~70% note p1 ke lens se: unka feel, urge, chart un par kya padta hai, partner doori par AAPKO kya lagta hai.
- Partner ko p1 ke experience ke around explain karo — neutral case study nahi."""
    return """PRIMARY READER = p1 (first kundli — this report is FOR them):
- In the user message, `p1_name` is the person reading the report — address them as "You" (or name + you).
- `p2_name` is the partner — "they/their" or by name; do not give equal paragraph airtime.
- ~70% of the note from p1's lens: what they feel, their urge to fix or chase, how their chart shows up in daily fights, what it does TO THEM when the partner goes quiet.
- Explain the partner in relation to p1's experience — not as a balanced two-subject case study."""


def _verdict_page_direct_voice(lang: str) -> str:
    """Break contrast-loop syntax — talk TO p1 first, not ABOUT both equally."""
    if lang == "hn":
        return """DIRECT CONVERSATION (AI structure loop todna — critical):
- Har paragraph me "X karta hai jabki Y karti hai" formula MAT repeat karo — poori note me max ek baar.
- Pehle p1 (Aap) se baat karo — partner ko unke around samjhao, dono ko barabar judge mat karo.
- Astrologer jaisa — p1 ko samne bitha kar samjha rahe ho ki unke chart me kya chal raha hai.
- Aakhir me safe counseling wrap mat do — ek sharp observation par khatam karo (p1 ke liye meaningful)."""
    if lang == "hi":
        return """DIRECT CONVERSATION (AI structure loop todna — critical):
- Har paragraph me "X karta hai jabki Y karti hai" formula MAT repeat karo — poori note me max ek baar.
- Pehle p1 (Aap) se baat karo — partner ko unke around samjhao, dono ko barabar judge mat karo.
- Astrologer jaisa — p1 ko samne bitha kar chart explain karo; hn/en jitni detail.
- Aakhir me safe counseling wrap mat do — ek sharp observation par khatam karo."""
    return """DIRECT CONVERSATION (break the AI structure loop — critical):
- Do NOT repeat "one does X while the other does Y" in every paragraph — at most once in the whole note.
- Talk TO p1 first (You) — frame the partner around what p1 feels and sees, not 50/50 narration.
- Sound like an astrologer speaking mainly to the person who ordered the report.
- Do not end with a safe counseling wrap — end on a sharp observation that lands for p1."""


def _cro_verdict_page_facts_lock() -> str:
    """How to use engine facts without sounding like a report."""
    return """Use the couple facts naturally — observational astrologer note, not a score dump or coaching script.
- Open from p1's experience first (how THEY feel the bond, THEIR urge, what lands on THEM) — partner as context.
- Not "[Name], your Moon…" opener or "real spark" — but p1 (first kundli) should lead the narrative.
- At most two scores in the whole note, woven into sentences.
- Every chart point → what happens in daily life — describe the pattern, do not instruct ("try to", "check in").
- Weave nakshatra / friction notes from facts — at least two couple-specific details.
- Do not repeat the same insight twice.
- Use only facts from the user message — do not invent scores."""


def _cro_verdict_page_few_shot(lang: str) -> str:
    """One golden example — tone/style only; replace placeholders with real p1/p2 names."""
    if lang == "hn":
        return """STYLE GUIDE — sirf TONE copy karo. [p1_name]/[p2_name] ko user message ke ACTUAL naam se replace karo. Aarav/Riya kabhi mat likho.

MAT AISE LIKHNA (AI smell + contrast loop — strictly forbidden):
"When something feels off, Aarav often wants to jump right in and fix it, while Riya tends to retreat... This contrast in emotional pacing... rhythm clash... engage honestly through those friction points."

AISE LIKHNA (p1 = pehli kundli, unse seedha — zyada waqt un par):
"Aarav, jab bhi rishte mein kuch alag lagta hai, aap turant kood padte ho ki abhi ke abhi isko theek karna hai. Aapka chart aapko jaldi react karwata hai — yeh aapki galti nahi, swabhav hai. Jab Riya chup ho jati hai, aapko lagta hai ignore ho rahe ho; unhe actually andar process karna padta hai. Aap jab dabav banate ho, unhe aur band ho jana padta hai — aur aap aur ulajh jaate ho."

GOLDEN JSON (p1 = pehli kundli in user facts — names/signs wahi se lo):
{
  "verdict": "[p1_name], jab rishte mein kuch alag lagta hai, aap turant theek karna chahte ho. Moon aapko jaldi react karwata hai — yeh aapka tareeka hai. Jab [p2_name] chup hote hain, andar se lagta hai ignore ho rahe ho; unhe settle hone ka waqt chahiye. Aap push karte ho, wo band hote hain — dono galat story padh lete ho.\\n\\nChart me pull sachha hai — attraction strong hai, par jab aap turant jawab maangte ho aur wo chup hote hain, wahi loop repeat hota hai. Pyaar kam nahi — timing alag hai.",
  "practical": [
    "[p1_name], jab aap turant closure maangte ho aur [p2_name] andar process kar rahe hain, aap pressure feel karte ho. Silence ko rejection samajh lete ho — unke liye pause hai. Yahi point baar-baar ulajhata hai.",
    "Warmth hai is bond me. Gap tab khulta hai jab silence me sabse bura assume kar lete ho. Pehle gussa settle, phir baat — warna wahi fight wapas."
  ]
}

Notice: No Key Takeaway. No What To Do Next. No scripted dialogue. No therapist tone."""
    if lang == "hi":
        return f"""STYLE GUIDE — sirf TONE copy karo. [p1_name]/[p2_name] ko user message ke ACTUAL naam se replace karo. Output 100% Devanagari Hindi (hn/en jitni depth).

MAT AISE LIKHNA (AI smell + contrast loop — forbidden):
"When something feels off, one partner wants to fix it while the other retreats..."

AISE LIKHO (p1 = pehli kundli, unse seedha — zyada waqt un par):
"[p1_name], jab rishte mein kuch alag lagta hai, aap turant theek karna chahte ho. Moon aapko jaldi react karwata hai. Jab [p2_name] chup hote hain, andar se lagta hai ignore ho rahe ho; unhe settle hone ka waqt chahiye."

GOLDEN JSON (Devanagari output — same structure as Hinglish):
{{
  "verdict": "[p1_name], jab rishte mein kuch alag lagta hai, aap turant theek karna chahte ho... (2-3 paragraphs, chart + daily life explain)",
  "practical": [
    "[p1_name], jab aap turant closure maangte ho aur [p2_name] andar process kar rahe hain...",
    "Is bond me warmth hai. Gap tab khulta hai jab silence me sabse bura assume kar lete ho..."
  ]
}}

Notice: No Key Takeaway. No coaching block. Same depth as Hinglish report."""
    return """STYLE GUIDE — copy TONE only. Replace [p1_name]/[p2_name] with ACTUAL names from user message. Never write Aarav or Riya.

DO NOT WRITE LIKE THIS (AI smell + contrast loop — strictly forbidden):
"When something feels off, one partner wants to fix it while the other retreats... This contrast in emotional pacing... rhythm clash..."

WRITE IN THIS DIRECT, p1-FIRST STYLE:
"[p1_name], when something feels off, you move to fix it right away — your chart pushes you to react fast. When [p2_name] goes quiet, you feel ignored; they need time inside. The more you push, the more they shut down."

GOLDEN JSON (ACTUAL p1/p2 names from user facts):
{
  "verdict": "[p1_name], when something feels off, you want the answer now. Your Moon trains you to react before you cool down — that's your pattern. When [p2_name] goes quiet, you feel shut out; they need time inside first. The more you push for closure, the more they pull back — you both read the wrong story.\\n\\nThe chart shows real pull — attraction is strong, but when you chase an answer and they go still, the same fight returns. It can feel like they care less; the chart says timing clashes, not the bond.",
  "practical": [
    "[p1_name], when you want an answer now and [p2_name] is still processing inside, you feel pressure — they feel pushed. You read silence as rejection when for them it's a pause. That misread is the loop the chart keeps flagging.",
    "You carry enough warmth in this bond for small bumps to pass. The gap opens when you fill her silence with the worst guess — your chart points at your urge to fix it instantly, not at a lack of love on her side."
  ]
}

Notice: No Key Takeaway. No What To Do Next. No scripted dialogue. No therapist tone."""


def _cro_verdict_page_contract(lang: str) -> str:
    """
    Section 02 voice — consultation persona + JSON fields + few-shot example.
    """
    from vedic.love_reality.love_section_polish import _human_prose_rhythm

    lang = polish_content_lang(lang)
    min_w = _VERDICT_PAGE_MIN_PRACTICAL_WORDS
    persona = _cro_verdict_page_consultation_persona(lang)
    if lang == "hn":
        return f"""{persona}

{love_script_directive(lang)}

{_human_prose_rhythm(lang)}

SECTION 02 OUTPUT (Roman Hinglish):
Fields: `verdict` (string) + `practical` (exactly 2 strings) — PDF me ek unified note banega.

`verdict`: 2–3 paragraphs (\\n\\n). Observation se shuru — "[Name], tumhara Moon…" mat. Key Takeaway label mat.
`practical[0]` + `practical[1]`: note ke aage ke paragraphs (~{min_w}+ words each) — alag advice section nahi, coach tone nahi.

{_cro_verdict_page_facts_lock()}

{_verdict_page_primary_reader(lang)}

{_verdict_page_direct_voice(lang)}

{_cro_verdict_page_few_shot(lang)}"""
    if lang == "hi":
        return f"""{persona}

{love_script_directive(lang)}

{_human_prose_rhythm(lang)}

SECTION 02 OUTPUT (देवनागरी हिंदी):
Fields: `verdict` (string) + `practical` (exactly 2 strings) — PDF में एक unified note बनेगा।

`verdict`: 2–3 paragraphs (\\n\\n). Observation से शुरू — coach tone नहीं।
`practical[0]` + `practical[1]`: आगे के paragraphs (~{min_w}+ words each)।

{_cro_verdict_page_facts_lock()}

{_verdict_page_primary_reader(lang)}

{_verdict_page_direct_voice(lang)}

{_cro_verdict_page_few_shot(lang)}"""
    return f"""{persona}

{_human_prose_rhythm(lang)}

SECTION 02 OUTPUT:
Fields: `verdict` (string) + `practical` (exactly 2 strings) — rendered as ONE unified note in the PDF.

`verdict`: 2–3 paragraphs (\\n\\n). Start with the dynamic between them — not "[Name], your X Moon leads you…". No "Key Takeaway:" label.
`practical[0]` + `practical[1]`: continue the same note as further paragraphs (~{min_w}+ words each) — not a separate advice section or coaching block.

{_cro_verdict_page_facts_lock()}

{_verdict_page_primary_reader(lang)}

{_verdict_page_direct_voice(lang)}

{_cro_verdict_page_few_shot(lang)}"""


def _cro_depth_contract() -> str:
    return f"""STRICT NO-BLANK DEPTH CONTRACT (har field ke liye — koi chapter khali ya chhota nahi):
- FORBIDDEN: blank strings, one-liners, bullet-only text, engine reason copy-paste, parameter dumps, score regurgitation without WHY.
- REQUIRED: har chapter_body me minimum {_LOVE_MIN_PARAGRAPHS} alag paragraphs (\\n\\n se separated).
- REQUIRED: har chapter_body minimum {_LOVE_MIN_CHAPTER_WORDS} words (~200–250+ words) — continuous deep prose, short bullets nahi.
- REQUIRED: har practical[] string bhi ek full long paragraph (minimum 180 words) — remedies + action checklist dono cover karo prose me.
- REQUIRED: hidden_truth minimum 4–5 sentences; verdict minimum 3 paragraphs.
- Har claim me pehle chart fact (Lagna, Moon, house, grah) cite karo, phir real-life behaviour explain karo.
- STRUCTURED_CHART_DATA se actual signs/placements lo — example signs hardcode mat karo; jo chart me hai wahi likho."""


def _cro_pdf_field_map(lang: str) -> str:
    lang = polish_content_lang(lang)
    self_change_hdr = (
        "Aapko Apne Me Kya Badlav Chahiye"
        if lang == "hn"
        else (
            "Aapko Apne Me Kya Badlav Chahiye"
            if lang == "hi"
            else "What You Need to Change in Yourself"
        )
    )
    partner_change_hdr = (
        "Partner Ko Kya Change Karna Hoga"
        if lang == "hn"
        else (
            "Partner Ko Kya Change Karna Hoga"
            if lang == "hi"
            else "What Your Partner Needs to Change"
        )
    )
    return f"""PDF PAGE-AWARE FIELD MAP (renderer ke blank pages ko fill karna mandatory):

1) love_connection → Pages 2 & 3 (Blueprint vs Reality Breakdown)
   - Minimum {_LOVE_MIN_PARAGRAPHS}+ long paragraphs. Destiny blueprint (7th lord, Upapada/UL, Venus, Jupiter) vs partner ki real chart signature.
   - STRUCTURED_CHART_DATA se p1 ka actual Lagna + Moon aur p2 ka actual Lagna + Moon explicitly name karo aur contrast explain karo.
   - Agar partner ke chart me 12th house me heavy planet stack hai (jaise Sun, Moon, Mars, Guru, Shukra) — is secrecy ko raw Hinglish me explain karo: aapko kyun lagta hai aap sunte nahi / unheard feel hota hai.
   - LOVE_SCORE_LEDGER cite karo jab love score explain karo. score_0_10 = engine score/100. grounding = 2–4 factual chart lines.

2) breakup → Page 6 (Root Cause — separation half)
   - BREAKUP_CHANCES ka actual score (chahe 100/100 ho ya kuch aur) — sirf number mat do, *kyun* yeh risk hai explain karo.
   - 12th-house secrecy, 7th-axis Saturn/Mars, Mercury clash, ego cold wars — story ki tarah, bullets nahi.
   - Agar chart me Gemini Moon Saturn/Rahu ke neeche afflicted hai (Punahsu/Punardhoo pattern) — feelings andar dab kar volcano ki tarah erupt hone ka real-world loop explain karo; partner disconnected kyun feel karta hai.

3) loyalty → Page 7 (Loyalty Triggers — breakup se alag chapter)
   - LOYALTY_CHECK ka actual score (chahe 0/100 ho) — *kyun* loyalty itni kam hai, trust psychology + secrecy + external pull.
   - Breakup chapter repeat mat karo — yahan loyalty triggers, attachment style vs real faithfulness ka farq.
   - loyalty_score < 52: kabhi "naturally loyal", "devoted by nature", "faithful by nature" mat likho.

4) will_return → Page 9 part 1 (Harmony Formula — reconnection context)
   - Probability language ONLY — kabhi "X wapas aa jayega" mat likho.
   - {_LOVE_MIN_PARAGRAPHS}+ paragraphs: return_probability ke hisaab se honest reconnection context.

5) future_outcome → Page 9 part 2 (Harmony Formula — elemental bridge)
   - Pehla block: Moon/sign se Air vs Earth / Fire vs Water clash — kaise A ka nature instant baat chahta hai aur R ka nature silence me chala jata hai (actual elements chart se lo).
   - Doosra block: exact behaviour shifts jo is gap ko bridge karein — generic advice nahi.
   - Explicit sub-sections prose me weave karo:
     • "{self_change_hdr}" — aapko kya andar se badalna hoga (concrete).
     • "{partner_change_hdr}" — unko kya change karna hoga (concrete).

6) red_flags → Page 8 lead-in narrative
   - {_LOVE_MIN_PARAGRAPHS}+ sharp paragraphs — top friction patterns jo neeche deterministic matrix set karein. Bullet list format duplicate mat karo.

7) practical → Section 02 (Verdict page recommendations) + Pages 12–13 (Remedies & Checklist)
   - EXACTLY 2 array strings — follow FINAL COSMIC VERDICT & RECOMMENDATIONS voice contract below.
   - String 1: Planetary remedies — afflicted graha tied advisory prose. Minimum 180 words.
   - String 2: Human action plan — repair, communication, dasha timing. Minimum 180 words.

8) verdict → Section 02 (Final Cosmic Verdict hero card) AND Page 14 (Closing Guidance)
   - Follow FINAL COSMIC VERDICT & RECOMMENDATIONS voice contract below.
   - NARRATIVE_BRIDGE lock use karo — breakup vs future tension resolve karo.
   - Minimum 3 paragraphs; chemistry + repair speed + dasha timing; probabilities only.

ALSO REQUIRED:
- hidden_truth: woh ek deep pattern jo dono partners poori tarah nahi dekhte (4–5+ sentences).
- special: exactly 3 strings — strengths (chart support kare to honest; warna fragile strengths honestly name karo).
- damage: exactly 2 strings — sharp risk statements.
- Focus: CURRENT romantic partner bond — marriage koot / 36 gun report nahi."""


def _cro_mandatory_locks() -> str:
    return """MANDATORY LOCKS (user message se — non-negotiable):
- LOVE_SCORE_LEDGER: love_connection score / cover alignment explain karte waqt cite karo.
- NARRATIVE_BRIDGE: verdict me aur breakup-vs-future tension resolve karte waqt use karo.
- LOYALTY_NARRATIVE_LOCKS + LOYALTY_CHAPTER_RULE: loyalty_score < 52 par exactly obey karo.
- WILL_RETURN_REALITY_PRIOR: ~90% estranged cases me real reunion nahi hota — return_probability ke hisaab se prose match karo.
- Use ONLY facts from user message. Scores invent mat karo.
- score_0_10 MUST match engine score/100 (e.g. 78 → 7.8, loyalty 35 → 3.5). Never inflate."""


def _build_love_regen_system_prompt(lang: str) -> str:
    lang = polish_content_lang(lang)
    script = {
        "en": "plain conversational English",
        "hn": "natural Roman Hinglish (WhatsApp-style)",
        "hi": "natural Devanagari Hindi (same depth as Hinglish)",
    }[lang]
    return f"""You are a Conversion Rate Optimization (CRO) relationship counselor re-expanding Love Reality Pro PDF chapters that failed depth QA.

Return STRICT JSON with ONE top-level key `chapters` (array).
Each element: {{"key": "<semantic_key>", "chapter_body": "<long prose>"}}.

Valid keys ONLY: {", ".join(LOVE_SEMANTIC_KEYS)}.

{_cro_voice_rules(lang)}

Write entirely in {script}.

{_cro_depth_contract()}

{_cro_pdf_field_map(lang)}

REGEN RULE: Failed chapters ko poori tarah dubara likho — previous shallow output mat extend karo. Har chapter_body me chart facts + raw emotional truth + minimum word count dono mandatory hain."""


def _build_system_prompt(lang: str) -> str:
    lang = polish_content_lang(lang)
    script = {
        "en": "plain conversational English",
        "hn": "natural Roman Hinglish (WhatsApp-style)",
        "hi": "natural Devanagari Hindi (same depth as Hinglish)",
    }[lang]
    return f"""You are a Conversion Rate Optimization (CRO) Expert and an Elite Relationship Counselor writing a Love Reality Pro PDF for a couple in a current romantic bond (not a marriage report).

Your JSON fields map directly into a fixed 14-page deterministic PDF renderer. Scores, tables, and bullet matrices render separately from engine data — aapka kaam har field me deep, continuous human story layer likhna hai taaki koi page blank na rahe.

{_cro_voice_rules(lang)}

Write entirely in {script}.

OUTPUT: JSON only — schema me koi key add/remove mat karo:
{{
  "hidden_truth": "string",
  "chapters": [
    {{"key": "love_connection", "chapter_body": "long prose", "score_0_10": number|null, "grounding": "short chart bridge"}},
    {{"key": "breakup", "chapter_body": "long prose", "score_0_10": number|null, "grounding": "short chart bridge"}},
    {{"key": "loyalty", "chapter_body": "long prose", "score_0_10": number|null, "grounding": "short chart bridge"}},
    {{"key": "will_return", "chapter_body": "long prose", "score_0_10": number|null, "grounding": "short chart bridge"}},
    {{"key": "future_outcome", "chapter_body": "long prose", "score_0_10": number|null, "grounding": "short chart bridge"}},
    {{"key": "red_flags", "chapter_body": "long prose", "score_0_10": number|null, "grounding": "short chart bridge"}}
  ],
  "special": ["string", "string", "string"],
  "damage": ["string", "string"],
  "practical": ["string", "string"],
  "verdict": "string"
}}

All 6 chapter keys MUST be present exactly once each.

{_cro_depth_contract()}

{_cro_verdict_page_contract(lang)}

{_cro_pdf_field_map(lang)}

{_cro_mandatory_locks()}"""


def _build_user_prompt(bundle: dict, lang: str) -> str:
    lang_norm = normalize_pro_pdf_lang(lang)
    lang_voice = polish_content_lang(lang_norm)
    voice_note = (
        "Roman Hinglish me likho — Aap/Unka, WhatsApp-style raw honesty."
        if lang_voice == "hn"
        else "Plain conversational English — direct, raw, no textbook tone."
    )
    return (
        _facts_summary(bundle)
        + f"\n\nlanguage: {lang_norm}\n"
        + f"narration_style: {voice_note}\n"
        + "Har chapter 200-250+ words, koi field blank mat chhodo. JSON only.\n"
        + "Emit JSON only."
    )


_LOYALTY_BANNED_RE = re.compile(
    r"naturally\s+loyal|naturally\s+faithful|devoted\s+romantic\s+nature|"
    r"faithful\s+by\s+nature|woh\s+naturally\s+loyal|naturally\s+loyal\s+hain",
    re.I,
)


def _scrub_loyalty_contradictions(parsed: dict, bundle: dict) -> None:
    """Remove 'naturally loyal' etc. when engine says loyalty is low."""
    ly = bundle.get("loyalty_check") or {}
    score = int(ly.get("loyalty_score") or ly.get("score") or 100)
    if score >= 52:
        return
    for ch in parsed.get("chapters") or []:
        if not isinstance(ch, dict):
            continue
        if str(ch.get("key") or "").strip().lower() != "loyalty":
            continue
        for field in (CHAPTER_BODY_KEY, "full_read", "grounding"):
            text = str(ch.get(field) or "")
            if not text:
                continue
            text = _LOYALTY_BANNED_RE.sub(
                "loyalty is unstable on this chart — surface Venus strength does not prove faithfulness",
                text,
            )
            text = re.sub(
                r"clear communication aur mutual support se aap in challenges ko overcome kar sakte hain[.]?",
                "Chart shows impulse and hidden layers — do not equate chemistry with loyalty.",
                text,
                flags=re.I,
            )
            ch[field] = text
        break


def _normalize_parsed(parsed: dict) -> None:
    """Ensure chapters list has ch1..ch6 aliases for depth regen."""
    chs = parsed.get("chapters")
    if not isinstance(chs, list):
        parsed["chapters"] = []
        return
    by_key = {}
    for c in chs:
        if isinstance(c, dict):
            by_key[str(c.get("key") or "").strip().lower()] = c
    out = []
    for i, ck in enumerate(LOVE_CHAPTER_KEYS, start=1):
        ik = KEY_BY_CH[ck]
        row = dict(by_key.get(ik) or by_key.get(ck) or {})
        row["key"] = ik
        if CHAPTER_BODY_KEY not in row and row.get("full_read"):
            row[CHAPTER_BODY_KEY] = row["full_read"]
        out.append(row)
    parsed["chapters"] = out
    # Milan depth regen expects ch1..ch7 keys on rows — duplicate index keys
    for i, row in enumerate(out, start=1):
        row["ch_index"] = f"ch{i}"

def _love_failing_chapter_keys(parsed: dict) -> list[str]:
    out: list[str] = []
    for ik in LOVE_SEMANTIC_KEYS:
        row = _parsed_chapter_row_for_key(parsed, ik)
        body = str((row or {}).get(CHAPTER_BODY_KEY) or "").strip()
        if _love_chapter_depth_failure_reason(body):
            out.append(ik)
    return out


def _attach_polish_telemetry(meta: dict, pg: dict[str, Any]) -> None:
    merge_pdf_generation_into_meta(meta, pg)
    publish_and_log_pdf_generation(pg)


def _love_apply_depth_regen(
    *,
    client: Any,
    model: str,
    lang: str,
    regen_user: str,
    parsed: dict,
    oa_timeout: float,
    tel: PdfGenOpenAITelemetry | None = None,
) -> None:
    """Re-call OpenAI for any chapter that failed the Love Reality depth gate."""
    max_rounds = int(_PREMIUM_DEPTH_REGEN_MAX_ROUNDS)
    regen_system = _build_love_regen_system_prompt(lang)
    for _ in range(max_rounds):
        failing = _love_failing_chapter_keys(parsed)
        if not failing:
            return
        from vedic.compat.premium_chapters import _depth_regen_dynamic_max_tokens

        mt = max(4000, _depth_regen_dynamic_max_tokens(len(failing)))
        got = _openai_regen_chapters_depth(
            client,
            tel,
            model,
            lang,
            regen_system,
            regen_user,
            failing,
            parsed,
            oa_timeout,
            max_tokens=mt,
        )
        if not got:
            return
        for ck, body in got.items():
            row = _parsed_chapter_row_for_key(parsed, ck)
            if row is not None and body:
                normalized = _normalize_chapter_body_from_llm(body)
                row[CHAPTER_BODY_KEY] = normalized
                if row.get("full_read"):
                    row["full_read"] = normalized


def _build_verdict_page_only_system_prompt(lang: str, *, include_dev_note: bool = True) -> str:
    lang = polish_content_lang(lang)
    script = {
        "en": "plain conversational English",
        "hn": "natural Roman Hinglish (WhatsApp-style)",
        "hi": "natural Devanagari Hindi (same depth as Hinglish)",
    }[lang]
    dev_note = ""
    if include_dev_note and _verdict_page_dev_mode():
        dev_note = (
            "\n\nDEV MODE: `verdict` 2 paragraphs; each `practical` ~60 words. Same JSON keys."
        )
    return f"""Write ONLY Section 02 — Final Cosmic Verdict (astrologer's note).

Return STRICT JSON:
{{
  "verdict": "string — 2–3 paragraphs, unified consultation note (no Key Takeaway label)",
  "practical": ["string — continues the same note", "string — continues the same note"]
}}

Write entirely in {script}.

{_cro_verdict_page_contract(lang)}

Use ONLY facts from the user message.{dev_note}"""


def _build_verdict_page_only_user_prompt(bundle: dict, lang: str) -> str:
    from vedic.love_reality.human_narrative_engine import (
        build_story_cards,
        format_global_story_block,
        format_section_story_block,
    )

    lang_norm = normalize_pro_pdf_lang(lang)
    lang_voice = polish_content_lang(lang_norm)
    p1 = bundle.get("p1") or {}
    p1_name = str(p1.get("name") or "Partner A").strip()
    if lang_voice == "hi":
        voice_note = f"देवनागरी हिंदी — आप = {p1_name} (p1/पहली कुंडली), वे = partner।"
    elif lang_voice == "hn":
        voice_note = f"Roman Hinglish — Aap = {p1_name} (p1/pehli kundli), Unka/Unki = partner."
    else:
        voice_note = f"Plain English — You = {p1_name} (p1/first kundli), They = partner."
    cards = bundle.get("_lr_story_cards")
    if not isinstance(cards, dict):
        cards = build_story_cards(bundle, lang_norm)
    story_block = (
        format_global_story_block(cards)
        + "\n\n"
        + format_section_story_block(cards, "verdict")
    )
    return (
        love_script_directive(lang_norm)
        + "\n\n"
        + f"Write Section 02 for this couple. PRIMARY READER is {p1_name} (p1) — most airtime on them. "
        "Open with a real-life scene — NOT theory. Match the example voice in the system prompt.\n\n"
        + story_block
        + "\n\n"
        + _verdict_page_facts_summary(bundle, lang_norm)
        + f"\n\nlanguage: {lang_norm}\n"
        + f"narration_style: {voice_note}\n"
        + "Emit JSON only."
    )


def _verdict_page_cache_key(bundle: dict, lang: str, model: str) -> str:
    parts = [
        _love_polish_fingerprint(bundle, lang, model),
        _verdict_page_prompt_fingerprint(lang),
        "dev" if _verdict_page_dev_mode() else "prod",
    ]
    raw = "|".join(parts)
    return hashlib.sha256(raw.encode()).hexdigest()[:32]


def _verdict_page_cache_path(key: str) -> str:
    base = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".cache", "love_polish"))
    os.makedirs(base, exist_ok=True)
    return os.path.join(base, f"verdict_page_{key}.json")


def _parse_verdict_page_response(parsed: dict) -> dict[str, Any]:
    out: dict[str, Any] = {}
    verdict = str(parsed.get("verdict") or "").strip()
    if verdict:
        out["verdict"] = verdict
    practical = parsed.get("practical")
    if isinstance(practical, list):
        items = [str(x).strip() for x in practical if str(x).strip()]
        if len(items) >= 2:
            out["practical"] = items[:2]
        elif len(items) == 1:
            out["practical"] = items
    return out


def polish_love_reality_verdict_page_only(
    bundle: dict,
    lang: str = "en",
    *,
    force_llm: bool = False,
) -> dict[str, Any]:
    """
    LLM call for Section 02 only — `verdict` + `practical[2]`.
    ~3–5x cheaper than full premium polish. Never raises.
    """
    requested_lang = normalize_pro_pdf_lang(lang)
    lang = polish_content_lang(requested_lang)
    model = _verdict_page_model()
    empty: dict[str, Any] = {"_meta": {"scope": "verdict_page_only", "openai_skipped": True}}

    if not _polish_enabled():
        empty["_meta"]["reason"] = "polish_off"
        return empty

    cache_key = _verdict_page_cache_key(bundle, lang, model)
    cache_path = _verdict_page_cache_path(cache_key)
    force = force_llm or _env_flag("LOVE_REALITY_VERDICT_PAGE_FORCE")

    if not force and os.path.isfile(cache_path):
        try:
            with open(cache_path, "r", encoding="utf-8") as fh:
                hit = json.load(fh)
            if isinstance(hit, dict) and hit.get("verdict"):
                log.info("[love_verdict_page] cache hit %s", cache_key[:12])
                out = dict(hit)
                meta = dict(out.get("_meta") or {})
                meta["cache"] = "verdict_page_file"
                meta["openai_skipped"] = True
                meta["cache_key"] = cache_key[:12]
                out["_meta"] = meta
                return out
        except Exception as exc:
            log.warning("[love_verdict_page] cache read failed: %s", exc)

    if force:
        log.info("[love_verdict_page] FORCE=1 — skipping file cache (OpenAI call)")

    try:
        from openai_helper import _get_client  # type: ignore
    except Exception:
        empty["_meta"]["reason"] = "openai_import_fail"
        return empty

    client = _get_client()
    if client is None:
        empty["_meta"]["reason"] = "openai_client_none"
        return empty

    from vedic.love_reality.human_narrative_engine import build_story_cards

    tel = PdfGenOpenAITelemetry(model)
    work_bundle = dict(bundle)
    work_bundle["_lr_story_cards"] = build_story_cards(bundle, lang)
    system = _build_verdict_page_only_system_prompt(lang)
    user = _build_verdict_page_only_user_prompt(work_bundle, lang)
    default_mt = 1200 if _verdict_page_dev_mode() else 2000
    max_tok = min(
        int(os.environ.get("LOVE_REALITY_VERDICT_PAGE_MAX_TOKENS", str(default_mt))),
        8192,
    )
    kwargs: dict[str, Any] = {
        "model": model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "response_format": {"type": "json_object"},
        "max_tokens": max_tok,
    }
    if not model.lower().startswith("gpt-5"):
        kwargs["temperature"] = float(
            os.environ.get("LOVE_REALITY_VERDICT_PAGE_TEMPERATURE", "0.78")
        )
        kwargs["presence_penalty"] = float(
            os.environ.get("LOVE_REALITY_VERDICT_PAGE_PRESENCE_PENALTY", "0.5")
        )
        kwargs["frequency_penalty"] = float(
            os.environ.get("LOVE_REALITY_VERDICT_PAGE_FREQUENCY_PENALTY", "0.3")
        )
    kwargs["timeout"] = float(os.environ.get("LOVE_REALITY_OPENAI_TIMEOUT", "120"))

    try:
        resp = client.chat.completions.create(**kwargs)
        tel.record(resp, "verdict_page_only")
        raw = (resp.choices[0].message.content or "").strip()
        if not raw:
            empty["_meta"]["reason"] = "empty_openai_body"
            return empty
        parsed = json.loads(raw)
        if not isinstance(parsed, dict):
            empty["_meta"]["reason"] = "json_not_object"
            return empty
        out = _parse_verdict_page_response(parsed)
        if not out.get("verdict"):
            empty["_meta"]["reason"] = "missing_verdict"
            return empty

        from vedic.love_reality.love_section_polish import _human_narrative_gate_enabled
        from vedic.love_reality.repetition_gate import (
            check_section_human_quality,
            human_quality_retry_note,
        )

        if _human_narrative_gate_enabled() and lang in ("en", "hn", "hi"):
            p1_name = str((bundle.get("p1") or {}).get("name") or "")
            gate_err = check_section_human_quality(
                str(out.get("verdict") or ""),
                lang,
                section_key="verdict",
                p1_name=p1_name,
            )
            if gate_err:
                retry_user = user + "\n\n" + human_quality_retry_note(gate_err, lang)
                kwargs["messages"] = [
                    {"role": "system", "content": system},
                    {"role": "user", "content": retry_user},
                ]
                resp2 = client.chat.completions.create(**kwargs)
                tel.record(resp2, "verdict_page_human_gate")
                raw2 = (resp2.choices[0].message.content or "").strip()
                if raw2:
                    parsed2 = json.loads(raw2)
                    if isinstance(parsed2, dict):
                        out2 = _parse_verdict_page_response(parsed2)
                        if out2.get("verdict"):
                            out = out2
                            out.setdefault("_meta", {})["human_gate_retry"] = gate_err
    except Exception as exc:
        log.warning("[love_verdict_page] openai fail: %s", exc)
        empty["_meta"]["reason"] = "openai_fail"
        return empty

    out.setdefault("_meta", {})
    pg = tel.build_meta(
        fallback_used=False,
        final_status="OK",
        validator_attempts=0,
        cache_hit=False,
        openai_skipped=False,
    )
    out["_meta"].update({
        "scope": "verdict_page_only",
        "model": model,
        "lang": lang,
        "requested_lang": requested_lang,
        "prompt_fingerprint": _verdict_page_prompt_fingerprint(lang),
        "dev_mode": _verdict_page_dev_mode(),
        "max_tokens": max_tok,
        "cache_key": cache_key[:12],
    })
    _attach_polish_telemetry(out["_meta"], pg)

    try:
        with open(cache_path, "w", encoding="utf-8") as fh:
            json.dump(out, fh, ensure_ascii=False, indent=2)
    except Exception as exc:
        log.warning("[love_verdict_page] cache write failed: %s", exc)

    return out


# --- Section 03 (Deep Connection Analysis) — separate LLM; Section 02 frozen ---
_DEEP_ANALYSIS_KEYS = ("emotional", "communication", "trust", "long_term")
_DEEP_ANALYSIS_TITLES = {
    "emotional": "Emotional Compatibility",
    "communication": "Communication",
    "trust": "Trust & Loyalty",
    "long_term": "Long-Term Potential",
}
_DEEP_ANALYSIS_MIN_WORDS = 65
_DEEP_ANALYSIS_HI_MIN_WORDS = 65
_DEEP_ANALYSIS_MAX_EXPL_CHARS = 2000


def _deep_analysis_dev_mode() -> bool:
    return _env_flag("LOVE_REALITY_DEEP_ANALYSIS_DEV")


def _deep_analysis_model() -> str:
    explicit = (os.environ.get("LOVE_REALITY_DEEP_ANALYSIS_MODEL") or "").strip()
    if explicit:
        return explicit
    return _verdict_page_model()


def _deep_analysis_prompt_fingerprint(lang: str) -> str:
    blob = _build_deep_analysis_system_prompt(lang, include_dev_note=False)
    return hashlib.sha256(blob.encode()).hexdigest()[:10]


def _deep_analysis_dimension_scores(bundle: dict) -> dict[str, int]:
    lc = bundle.get("love_compatibility") or {}
    bu = bundle.get("breakup_chances") or {}
    ly = bundle.get("loyalty_check") or {}
    love = int(lc.get("score") or 0)
    breakup = int(bu.get("breakup_score") or bu.get("score") or 0)
    loyalty = int(ly.get("loyalty_score") or ly.get("score") or 0)
    if love <= 0:
        love = 72
    if breakup <= 0:
        breakup = 58
    if loyalty <= 0:
        loyalty = 64
    return {
        "emotional": max(0, min(100, int(love * 0.9))),
        "communication": max(20, min(100, 100 - breakup)),
        "trust": loyalty,
        "long_term": max(0, min(100, (love + loyalty) // 2)),
    }


def _deep_analysis_expl_word_count(text: str) -> int:
    return len((text or "").split())


def _deep_analysis_few_shot(lang: str) -> str:
    if lang == "hi":
        return """CRITICAL: [p1_name] / [p2_name] placeholders hain — user message ke ACTUAL naam likho.

ऐसे मत लिखो: "Chart signals for this theme are active..." / bullet list / one-line facts.

ऐसे लिखो (देवनागरी, हर dimension 3–4 वाक्य — real names):
{
  "deep_analysis": [
    {"key": "emotional", "explanation": "[p1_name], आप भावनाएँ जल्दी सामने लाते हैं — चंद्र आपको तुरंत प्रतिक्रिया कराता है। जब [p2_name] भीतर सोचते हैं, आपको लगता है दूरी बढ़ रही है। यह प्यार कम नहीं, बस अलग भावनात्मक गति है।"},
    {"key": "communication", "explanation": "[p1_name], जब आप तुरंत जवाब चाहते हैं और [p2_name] चुप होते हैं, आप गलत टोन पढ़ लेते हैं। बुध के फेज़ में छोटी बात भी झगड़ा बन सकती है — चार्ट आपको गर्म होने से पहले बोलने पर धकेलता है।"},
    {"key": "trust", "explanation": "[p1_name], आप भरोसा consistency से मापते हैं — जब [p2_name] चुप होते हैं, दिमाग worst-case भर देता है। विश्वास तब दरार खाता है जब चुप्पी को अस्वीकार समझ लेते हैं।"},
    {"key": "long_term", "explanation": "[p1_name], इस बंधन में गर्मजोशी है पर repair की आदत नहीं तो वही ६–८ महीने का loop दोहरता है। दीर्घकाल तब टिकता है जब गुस्से के peak पर रुककर बात करते हैं।"}
  ]
}"""
    if lang == "hn":
        return """CRITICAL: [p1_name] aur [p2_name] placeholders hain — user message ke ACTUAL naam use karo. Aarav/Riya kabhi mat likho.

MAT AISE MAT LIKHO (generic / AI):
"Chart signals for this theme are active between both partners. Daily rhythm and repair style shape how this score lands."

AISE LIKHO (p1 = pehli kundli, seedha, chart-specific — real names):
{
  "deep_analysis": [
    {"key": "emotional", "explanation": "[p1_name], aap feelings jaldi surface par laate ho — Moon aapko turant react karwata hai. Jab [p2_name] andar process karte hain, aapko lagta hai doori badh rahi hai. Yeh pyaar ki kami nahi, bas alag emotional speed hai."},
    {"key": "communication", "explanation": "[p1_name], jab aap turant jawab maangte ho aur [p2_name] chup hote hain, aap galat tone padh lete ho. Mercury ke phases me chhoti baat bhi fight ban sakti hai — chart aapko jaldi bolne par push karta hai."},
    {"key": "trust", "explanation": "[p1_name], aap consistency se trust measure karte ho — jab [p2_name] silent hote hain, mind worst-case bharta hai. Trust tab crack hoti hai jab aap silence ko rejection samajh lete ho."},
    {"key": "long_term", "explanation": "[p1_name], is bond me warmth hai par bina repair habit ke wahi 6-8 mahine ka loop repeat hoga. Long-term tab hold hota hai jab gusse ke peak par ruk kar baat karte ho."}
  ]
}"""
    return """CRITICAL: [p1_name] and [p2_name] are placeholders — use ACTUAL names from the user message. Never write Aarav or Riya.

DO NOT WRITE (generic placeholder):
"Chart signals for this theme are active between both partners. Daily rhythm and repair style shape how this score lands."

WRITE LIKE THIS (p1 = first kundli, direct, chart-specific — real names):
{
  "deep_analysis": [
    {"key": "emotional", "explanation": "[p1_name], you bring feelings up fast — your Moon pushes you to react before you cool down. When [p2_name] needs quiet inside, you read it as distance growing. That's not less love; it's a different emotional speed."},
    {"key": "communication", "explanation": "[p1_name], when you want an answer now and [p2_name] goes still, you often misread their tone. In Mercury-sensitive weeks a small delay can feel like disrespect — your chart trains you to speak before the heat drops."},
    {"key": "trust", "explanation": "[p1_name], you measure trust through consistency — when [p2_name] is silent, your mind fills the gap with worst-case stories. Trust cracks when you treat pause as rejection, not processing."},
    {"key": "long_term", "explanation": "[p1_name], this bond has warmth but without repair habits the same six-to-eight month loop returns. Long-term holds when you pause at peak anger instead of fixing everything instantly."}
  ]
}"""


def _build_deep_analysis_system_prompt(lang: str, *, include_dev_note: bool = True) -> str:
    from vedic.love_reality.love_section_polish import _human_prose_rhythm

    lang = polish_content_lang(lang)
    script = {
        "en": "plain conversational English",
        "hn": "natural Roman Hinglish (WhatsApp-style)",
        "hi": "natural Devanagari Hindi (same depth as Hinglish)",
    }[lang]
    banned = _verdict_page_banned_block(lang)
    hi_lock = ""
    if lang == "hi":
        hi_lock = (
            "\n\nMANDATORY FOR hi — each explanation:\n"
            "- 100% देवनागरी Hindi, रोज़मर्रा की भाषा\n"
            f"- {_DEEP_ANALYSIS_HI_MIN_WORDS}+ words per block, 3–4 complete sentences\n"
            "- NO bullets, NO chart jargon dump, NO one-line facts\n"
            "- Talk TO p1 with real partner names\n"
        )
    dev_note = ""
    if include_dev_note and _deep_analysis_dev_mode():
        dev_note = "\n\nDEV MODE: each explanation ~35 words. Same JSON keys."
    return f"""Write ONLY Section 03 — Deep Connection Analysis (4 dimension blocks for PDF).

Return STRICT JSON:
{{
  "deep_analysis": [
    {{"key": "emotional", "explanation": "string"}},
    {{"key": "communication", "explanation": "string"}},
    {{"key": "trust", "explanation": "string"}},
    {{"key": "long_term", "explanation": "string"}}
  ]
}}

Write entirely in {script}.

You are a senior relationship astrologer. Four short deep-dives — one per dimension. Scores are pre-set in the user message; do NOT invent scores.

RULES:
- Each explanation: {_DEEP_ANALYSIS_MIN_WORDS}+ words — full paragraph prose, 3–4 sentences, specific, no filler.
- PRIMARY READER = p1 (first kundli). ~70% from their lens. Partner as context only.
- Name chart facts (Moon, Venus, Mercury) in plain words — no generic "chart signals active" text.
- No contrast loop every line ("X while Y"). Talk TO p1 directly.
- No safe counseling wrap at the end of each block.
- NO bullet lists or numbered points in any explanation.
{hi_lock}

{_human_prose_rhythm(lang)}

{banned}

{_verdict_page_primary_reader(lang)}

{_verdict_page_direct_voice(lang)}

{_deep_analysis_few_shot(lang)}

Use ONLY facts from the user message.{dev_note}"""


def _build_deep_analysis_user_prompt(bundle: dict, lang: str) -> str:
    from vedic.love_reality.human_narrative_engine import (
        build_story_cards,
        format_global_story_block,
    )

    p1 = bundle.get("p1") or {}
    p1_name = str(p1.get("name") or "Partner A").strip()
    scores = _deep_analysis_dimension_scores(bundle)
    score_lines = "\n".join(
        f"- {_DEEP_ANALYSIS_TITLES[k]} (key={k}): score {scores[k]}/100 — weave into prose once, no scorecard tone"
        for k in _DEEP_ANALYSIS_KEYS
    )
    lang_voice = polish_content_lang(normalize_pro_pdf_lang(lang))
    voice = (
        f"Aap = {p1_name} (p1). Unka/Unki = partner."
        if lang_voice == "hn"
        else f"You = {p1_name} (p1). They = partner."
    )
    cards = bundle.get("_lr_story_cards")
    if not isinstance(cards, dict):
        cards = build_story_cards(bundle, lang)
    story = format_global_story_block(cards)
    return (
        f"Write Deep Connection Analysis for {p1_name} (primary reader). "
        f"Each dimension = NEW angle on the SAME root cause — never repeat the same conclusion.\n\n"
        + story
        + "\n\n"
        + _verdict_page_facts_summary(bundle, lang)
        + f"\n\nDIMENSION SCORES (fixed — explain in real-life scenes, not as a list):\n{score_lines}\n\n"
        + f"language: {lang}\n"
        + f"narration_style: {voice}\n"
        + "Emit JSON only."
    )


def _parse_deep_analysis_response(parsed: dict, *, lang: str = "en") -> dict[str, Any]:
    rows = parsed.get("deep_analysis")
    if not isinstance(rows, list):
        return {}
    out_rows: list[dict[str, str]] = []
    by_key: dict[str, dict] = {}
    lane = polish_content_lang(lang)
    for row in rows:
        if not isinstance(row, dict):
            continue
        key = str(row.get("key") or "").strip().lower()
        expl = str(row.get("explanation") or "").strip()
        if not key or not expl:
            continue
        wc = _deep_analysis_expl_word_count(expl)
        if wc < _DEEP_ANALYSIS_MIN_WORDS:
            continue
        if lane == "hi" and not _deep_analysis_row_hi_ok(expl):
            continue
        if lane == "en" and not _deep_analysis_row_en_ok(expl):
            continue
        by_key[key] = {"key": key, "explanation": expl[:_DEEP_ANALYSIS_MAX_EXPL_CHARS]}
    for k in _DEEP_ANALYSIS_KEYS:
        if k in by_key:
            out_rows.append(by_key[k])
    if len(out_rows) < 4:
        return {}
    return {"deep_analysis": out_rows}


def _deep_analysis_cache_key(bundle: dict, lang: str, model: str) -> str:
    parts = [
        _love_polish_fingerprint(bundle, lang, model),
        _deep_analysis_prompt_fingerprint(lang),
        "dev" if _deep_analysis_dev_mode() else "prod",
        "deep_analysis",
    ]
    return hashlib.sha256("|".join(parts).encode()).hexdigest()[:32]


def _deep_analysis_cache_path(key: str) -> str:
    base = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".cache", "love_polish"))
    os.makedirs(base, exist_ok=True)
    return os.path.join(base, f"deep_analysis_{key}.json")


def polish_love_reality_deep_analysis_only(
    bundle: dict,
    lang: str = "en",
    *,
    force_llm: bool = False,
) -> dict[str, Any]:
    """LLM for Section 03 only — four deep_analysis explanations. Never raises."""
    requested_lang = normalize_pro_pdf_lang(lang)
    lang = polish_content_lang(requested_lang)
    model = _deep_analysis_model()
    empty: dict[str, Any] = {"_meta": {"scope": "deep_analysis_only", "openai_skipped": True}}

    if not _polish_enabled():
        empty["_meta"]["reason"] = "polish_off"
        return empty

    cache_key = _deep_analysis_cache_key(bundle, lang, model)
    cache_path = _deep_analysis_cache_path(cache_key)
    force = force_llm or _env_flag("LOVE_REALITY_DEEP_ANALYSIS_FORCE")

    if not force and os.path.isfile(cache_path):
        try:
            with open(cache_path, "r", encoding="utf-8") as fh:
                hit = json.load(fh)
            if isinstance(hit, dict) and hit.get("deep_analysis"):
                out = dict(hit)
                meta = dict(out.get("_meta") or {})
                meta["cache"] = "deep_analysis_file"
                meta["openai_skipped"] = True
                out["_meta"] = meta
                return out
        except Exception as exc:
            log.warning("[love_deep_analysis] cache read failed: %s", exc)

    try:
        from openai_helper import _get_client  # type: ignore
    except Exception:
        empty["_meta"]["reason"] = "openai_import_fail"
        return empty

    client = _get_client()
    if client is None:
        empty["_meta"]["reason"] = "openai_client_none"
        return empty

    from vedic.love_reality.human_narrative_engine import build_story_cards

    tel = PdfGenOpenAITelemetry(model)
    work_bundle = dict(bundle)
    work_bundle["_lr_story_cards"] = build_story_cards(bundle, lang)
    system = _build_deep_analysis_system_prompt(lang)
    user = _build_deep_analysis_user_prompt(work_bundle, lang)
    default_mt = 900 if _deep_analysis_dev_mode() else 3200
    max_tok = min(int(os.environ.get("LOVE_REALITY_DEEP_ANALYSIS_MAX_TOKENS", str(default_mt))), 4096)
    kwargs: dict[str, Any] = {
        "model": model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "response_format": {"type": "json_object"},
        "max_tokens": max_tok,
    }
    if not model.lower().startswith("gpt-5"):
        kwargs["temperature"] = float(os.environ.get("LOVE_REALITY_DEEP_ANALYSIS_TEMPERATURE", "0.78"))
        kwargs["presence_penalty"] = float(os.environ.get("LOVE_REALITY_DEEP_ANALYSIS_PRESENCE_PENALTY", "0.5"))
        kwargs["frequency_penalty"] = float(os.environ.get("LOVE_REALITY_DEEP_ANALYSIS_FREQUENCY_PENALTY", "0.3"))
    kwargs["timeout"] = float(os.environ.get("LOVE_REALITY_OPENAI_TIMEOUT", "120"))

    try:
        resp = client.chat.completions.create(**kwargs)
        tel.record(resp, "deep_analysis_only")
        raw = (resp.choices[0].message.content or "").strip()
        if not raw:
            empty["_meta"]["reason"] = "empty_openai_body"
            return empty
        parsed = json.loads(raw)
        if not isinstance(parsed, dict):
            empty["_meta"]["reason"] = "json_not_object"
            return empty
        out = _parse_deep_analysis_response(parsed, lang=lang)
        if not out.get("deep_analysis"):
            empty["_meta"]["reason"] = "missing_deep_analysis"
            return empty
    except Exception as exc:
        log.warning("[love_deep_analysis] openai fail: %s", exc)
        empty["_meta"]["reason"] = "openai_fail"
        return empty

    out.setdefault("_meta", {})
    pg = tel.build_meta(
        fallback_used=False,
        final_status="OK",
        validator_attempts=0,
        cache_hit=False,
        openai_skipped=False,
    )
    out["_meta"].update({
        "scope": "deep_analysis_only",
        "model": model,
        "lang": lang,
        "requested_lang": requested_lang,
        "prompt_fingerprint": _deep_analysis_prompt_fingerprint(lang),
        "dev_mode": _deep_analysis_dev_mode(),
        "max_tokens": max_tok,
        "cache_key": cache_key[:12],
    })
    _attach_polish_telemetry(out["_meta"], pg)

    try:
        with open(cache_path, "w", encoding="utf-8") as fh:
            json.dump(out, fh, ensure_ascii=False, indent=2)
    except Exception as exc:
        log.warning("[love_deep_analysis] cache write failed: %s", exc)

    return out


def ensure_deep_analysis_llm(
    bundle: dict,
    pro: dict,
    lang: str,
    *,
    force_llm: bool = False,
) -> dict:
    """Section 03 (Deep Connection / विस्तार) — full LLM Hindi per dimension."""
    if not isinstance(pro, dict):
        return pro or {}
    if lang == "hi" and deep_analysis_hi_ready(pro) and not force_llm:
        return pro
    if lang == "en" and deep_analysis_en_ready(pro) and not force_llm:
        return pro
    last_meta: dict[str, Any] = {}
    max_attempts = max(1, int(os.environ.get("LOVE_REALITY_DEEP_ANALYSIS_ATTEMPTS", "3")))
    for attempt in range(max_attempts):
        if attempt > 0:
            try:
                cache_key = _deep_analysis_cache_key(bundle, polish_content_lang(lang), _deep_analysis_model())
                cache_path = _deep_analysis_cache_path(cache_key)
                if os.path.isfile(cache_path):
                    os.remove(cache_path)
            except OSError:
                pass
        hit = polish_love_reality_deep_analysis_only(bundle, lang=lang, force_llm=True)
        last_meta = hit.get("_meta") if isinstance(hit.get("_meta"), dict) else {}
        rows = hit.get("deep_analysis")
        if isinstance(rows, list) and len(rows) >= 4:
            merged = {**pro, "deep_analysis": rows}
            lang_ok = (
                (lang == "hi" and deep_analysis_hi_ready(merged))
                or (lang == "en" and deep_analysis_en_ready(merged))
                or (lang not in ("hi", "en"))
            )
            if lang_ok:
                pro["deep_analysis"] = rows
                pro.setdefault("_meta", {})["section3_deep_analysis"] = {
                    **last_meta,
                    "source": "llm",
                    "attempt": attempt + 1,
                }
                return pro
        last_meta = {**last_meta, "reject": "thin_or_not_hi", "attempt": attempt + 1}
    pro.setdefault("_meta", {})["section3_deep_analysis"] = {
        **last_meta,
        "source": "failed",
        "attempts": max_attempts,
    }
    return pro


def bust_love_polish_all_caches(bundle: dict, lang: str, *, model: str | None = None) -> None:
    """Update Report — drop L1 + section file caches so Hindi/Hinglish cannot replay stale LLM."""
    from vedic.compat import llm_polish as _lp

    m = model or _DEFAULT_MODEL
    l1_key = _love_polish_fingerprint(bundle, lang, m)
    try:
        with _lp._cache_lock:
            _lp._cache.pop(l1_key, None)
    except Exception as exc:
        log.warning("[love_reality_premium] L1 bust failed: %s", exc)

    for key_fn, path_fn, section_model in (
        (_verdict_page_cache_key, _verdict_page_cache_path, _verdict_page_model()),
        (_deep_analysis_cache_key, _deep_analysis_cache_path, _deep_analysis_model()),
    ):
        try:
            sk = key_fn(bundle, lang, section_model)
            path = path_fn(sk)
            if os.path.isfile(path):
                os.remove(path)
        except Exception as exc:
            log.warning("[love_reality_premium] section cache bust failed: %s", exc)

    try:
        from vedic.love_reality.love_section_polish import _cache_dir

        base = _cache_dir()
        if os.path.isdir(base):
            for name in os.listdir(base):
                if name.endswith(".json"):
                    try:
                        os.remove(os.path.join(base, name))
                    except OSError:
                        pass
    except Exception as exc:
        log.warning("[love_reality_premium] assembly cache dir bust failed: %s", exc)


def polish_love_reality_premium(
    bundle: dict,
    lang: str = "en",
    *,
    force_llm: bool = False,
) -> dict[str, Any]:
    """Returns pro_premium block for PDF renderer. Never raises."""
    if not _env_flag("LOVE_REALITY_LEGACY_MEGA_POLISH"):
        from vedic.love_reality.love_section_polish import assemble_love_reality_pro_premium

        requested_lang = normalize_pro_pdf_lang(lang)
        lang = polish_content_lang(requested_lang)
        model = _DEFAULT_MODEL
        if not _polish_enabled():
            shell = _empty_shell(model, "polish_off")
            pg = stub_meta(
                model,
                final_status="polish_off",
                fallback_used=True,
                openai_skipped=True,
                reason="polish_off",
            )
            _attach_polish_telemetry(shell.setdefault("_meta", {}), pg)
            return shell

        cache_key = _love_polish_fingerprint(bundle, lang, model)
        if not force_llm and not _cache_disabled():
            hit = _l1_get(cache_key)
            if hit is not None and _love_polish_cache_depth_ok(hit):
                log.info("[love_reality_premium] L1 cache hit key=%s", cache_key[:16])
                out = dict(hit)
                meta = dict(out.get("_meta") or {})
                meta.setdefault("cache", "L1")
                pg = stub_meta(
                    model,
                    final_status="OK",
                    fallback_used=False,
                    openai_skipped=True,
                    cache_hit=True,
                    reason="polish_L1",
                )
                _attach_polish_telemetry(meta, pg)
                out["_meta"] = meta
                return out
            db_hit = _l2_get(cache_key)
            if db_hit is not None and _love_polish_cache_depth_ok(db_hit):
                log.info("[love_reality_premium] L2 cache hit key=%s", cache_key[:16])
                _l1_put(cache_key, db_hit)
                out = dict(db_hit)
                meta = dict(out.get("_meta") or {})
                meta.setdefault("cache", "L2")
                pg = stub_meta(
                    model,
                    final_status="OK",
                    fallback_used=False,
                    openai_skipped=True,
                    cache_hit=True,
                    reason="polish_L2",
                )
                _attach_polish_telemetry(meta, pg)
                out["_meta"] = meta
                return out

        try:
            pro = assemble_love_reality_pro_premium(
                bundle, lang=lang, force_llm=force_llm, model=model
            )
        except Exception as exc:
            log.exception("[love_reality_premium] assembly failed: %s", exc)
            pro = _empty_shell(model, "assembly_fail")
        if not _cache_disabled() and _love_polish_cache_depth_ok(pro):
            try:
                _l1_put(cache_key, pro)
                _l2_put(cache_key, pro, model)
            except Exception as exc:
                log.warning("[love_reality_premium] cache write failed: %s", exc)
        return pro

    return _polish_love_reality_premium_legacy(bundle, lang, force_llm=force_llm)


def _polish_love_reality_premium_legacy(
    bundle: dict,
    lang: str = "en",
    *,
    force_llm: bool = False,
) -> dict[str, Any]:
    """Legacy single mega-prompt polish (LOVE_REALITY_LEGACY_MEGA_POLISH=1)."""
    del force_llm  # legacy path ignores per-section force
    requested_lang = normalize_pro_pdf_lang(lang)
    lang = polish_content_lang(requested_lang)
    model = _DEFAULT_MODEL
    if not _polish_enabled():
        shell = _empty_shell(model, "polish_off")
        pg = stub_meta(
            model,
            final_status="polish_off",
            fallback_used=True,
            openai_skipped=True,
            reason="polish_off",
        )
        _attach_polish_telemetry(shell.setdefault("_meta", {}), pg)
        return shell

    cache_key = _love_polish_fingerprint(bundle, lang, model)
    if not _cache_disabled():
        hit = _l1_get(cache_key)
        if hit is not None and _love_polish_cache_depth_ok(hit):
            log.info("[love_reality_premium] L1 cache hit key=%s", cache_key[:16])
            out = dict(hit)
            meta = dict(out.get("_meta") or {})
            meta.setdefault("cache", "L1")
            pg = stub_meta(
                model,
                final_status="OK",
                fallback_used=False,
                openai_skipped=True,
                cache_hit=True,
                reason="polish_L1",
            )
            _attach_polish_telemetry(meta, pg)
            out["_meta"] = meta
            return out
        db_hit = _l2_get(cache_key)
        if db_hit is not None and _love_polish_cache_depth_ok(db_hit):
            log.info("[love_reality_premium] L2 cache hit key=%s", cache_key[:16])
            _l1_put(cache_key, db_hit)
            out = dict(db_hit)
            meta = dict(out.get("_meta") or {})
            meta.setdefault("cache", "L2")
            pg = stub_meta(
                model,
                final_status="OK",
                fallback_used=False,
                openai_skipped=True,
                cache_hit=True,
                reason="polish_L2",
            )
            _attach_polish_telemetry(meta, pg)
            out["_meta"] = meta
            return out

    try:
        from openai_helper import _get_client  # type: ignore
    except Exception:
        shell = _empty_shell(model, "openai_import_fail")
        pg = stub_meta(
            model,
            final_status="openai_import_fail",
            fallback_used=True,
            openai_skipped=True,
            reason="openai_import_fail",
        )
        _attach_polish_telemetry(shell.setdefault("_meta", {}), pg)
        return shell

    client = _get_client()
    if client is None:
        shell = _empty_shell(model, "openai_client_none")
        pg = stub_meta(
            model,
            final_status="openai_client_none",
            fallback_used=True,
            openai_skipped=True,
            reason="openai_client_none",
        )
        _attach_polish_telemetry(shell.setdefault("_meta", {}), pg)
        return shell

    tel = PdfGenOpenAITelemetry(model)

    system = _build_system_prompt(lang)
    user = _build_user_prompt(bundle, lang)
    kwargs: dict[str, Any] = {
        "model": model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "response_format": {"type": "json_object"},
        "max_tokens": min(
            int(os.environ.get("LOVE_REALITY_PREMIUM_MAX_TOKENS", "8000")),
            16384,
        ),
    }
    if not model.lower().startswith("gpt-5"):
        kwargs["temperature"] = 0.55
    kwargs["timeout"] = float(os.environ.get("LOVE_REALITY_OPENAI_TIMEOUT", "180"))

    try:
        resp = client.chat.completions.create(**kwargs)
        tel.record(resp, "primary")
        raw = (resp.choices[0].message.content or "").strip()
        if not raw:
            shell = _empty_shell(model, "empty_openai_body")
            pg = tel.build_meta(
                fallback_used=True,
                final_status="empty_openai_body",
                validator_attempts=0,
            )
            _attach_polish_telemetry(shell.setdefault("_meta", {}), pg)
            return shell
        parsed = json.loads(raw)
        if not isinstance(parsed, dict):
            shell = _empty_shell(model, "json_not_object")
            pg = tel.build_meta(
                fallback_used=True,
                final_status="json_not_object",
                validator_attempts=0,
            )
            _attach_polish_telemetry(shell.setdefault("_meta", {}), pg)
            return shell
        parsed = _parse_love_premium_response(parsed)
    except Exception as exc:
        log.warning("[love_reality_premium] openai fail: %s", exc)
        shell = _empty_shell(model, "openai_fail")
        pg = tel.build_meta(
            fallback_used=True,
            final_status="openai_fail",
            validator_attempts=0,
        )
        _attach_polish_telemetry(shell.setdefault("_meta", {}), pg)
        return shell

    _normalize_parsed(parsed)
    _scrub_loyalty_contradictions(parsed, bundle)

    if _depth_regen_enabled():
        try:
            _love_apply_depth_regen(
                client=client,
                model=model,
                lang=lang,
                regen_user=_build_user_prompt(bundle, lang),
                parsed=parsed,
                oa_timeout=kwargs["timeout"],
                tel=tel,
            )
        except Exception as exc:
            log.warning("[love_reality_premium] depth regen skipped: %s", exc)

    parsed = sanitize_love_reality_pro_premium(parsed, bundle, lang=requested_lang)

    from vedic.love_reality.premium_validate import apply_love_premium_validation

    apply_love_premium_validation(parsed, bundle, requested_lang)

    parsed.setdefault("_meta", {})
    parsed["_meta"].update({
        "model": model,
        "version": _LOVE_VERSION,
        "lang": lang,
        "requested_lang": requested_lang,
    })
    pg_ok = tel.build_meta(
        fallback_used=False,
        final_status="OK",
        validator_attempts=0,
        cache_hit=False,
        openai_skipped=False,
    )
    _attach_polish_telemetry(parsed["_meta"], pg_ok)
    if not _cache_disabled() and _love_polish_cache_depth_ok(parsed):
        try:
            _l1_put(cache_key, parsed)
            _l2_put(cache_key, parsed, model)
        except Exception as exc:
            log.warning("[love_reality_premium] cache write failed: %s", exc)
    return parsed
