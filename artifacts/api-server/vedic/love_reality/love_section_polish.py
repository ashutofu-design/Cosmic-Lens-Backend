"""
Love Reality Pro — per-section LLM calls (S02–S03, blueprint, chapters, harmony, dasha, roadmap).
Shared astrologer voice; no mega-prompt.
"""
from __future__ import annotations

import hashlib
import json
import logging
import os
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Callable

from vedic.compat.openai_pdf_telemetry import PdfGenOpenAITelemetry, stub_meta
from vedic.love_reality.pdf_text_safe import (
    love_script_directive,
    love_write_script_label,
    polish_content_lang,
    sanitize_love_reality_pro_premium,
)
from vedic.compat.premium_chapters import CHAPTER_BODY_KEY, normalize_pro_pdf_lang

log = logging.getLogger(__name__)

_ASSEMBLY_VER = "lr_sections_v17_section8_llm"
_CHAPTER_MIN_WORDS = int(os.environ.get("LOVE_REALITY_SECTION_CHAPTER_MIN_WORDS", "95"))
_HARMONY_MIN_WORDS = int(os.environ.get("LOVE_REALITY_SECTION_HARMONY_MIN_WORDS", "130"))

_CHAPTER_KEYS = ("breakup", "loyalty")
_BLUEPRINT_REALITY_KEY = "love_connection"
_RED_FLAGS_KEY = "red_flags"


def _env_flag(name: str, default: str = "0") -> bool:
    return (os.environ.get(name) or default).strip().lower() in ("1", "true", "yes", "on")


def _word_count(text: str) -> int:
    return len(re.findall(r"\b[\w']+\b", text or ""))


def _narrative_architecture(lang: str) -> str:
    if lang == "hi":
        return """NARRATIVE ARCHITECTURE (पूरी रिपोर्ट एक परामर्श जैसी — AI रिपोर्ट नहीं):
- 25+ वर्षों के वरिष्ठ ज्योतिषी की तरह लिखें — केवल दिए गए चार्ट संकेत।
- पहले SINGLE सबसे मजबूत मूल कारण पहचानें (user message में ROOT_CAUSE)।
- पूरी कहानी उसी मूल कारण के इर्द-गिर्द — हर अध्याय नया कोण, एक ही निष्कर्ष दोबारा नहीं।
- पिछले अध्यायों के निष्कर्ष / चेतावनी / स्कोर दोहराएँ नहीं।
- हर निष्कर्ष किसी विशिष्ट ज्योतिषीय कारक से जुड़ा हो (Moon, Mercury, 7th lord, dasha)।
- सामान्य relationship सलाह नहीं — जब तक चार्ट समर्थन न करे।
- स्कोर एक बार बताने के बाद दोबारा नहीं — "इस स्तर" / "इस चरण" कहें।
- पैटर्न क्यों है — सिर्फ क्या है नहीं।"""
    if lang == "hn":
        return """NARRATIVE ARCHITECTURE (poori report ek consultation jaisi — AI report nahi):
- 25+ saal ke senior astrologer ki tarah likho — sirf diye gaye chart signals use karo.
- Pehle SINGLE strongest root cause identify karo (user message me ROOT_CAUSE block).
- Poori story us root cause ke around — har chapter alag angle, same conclusion repeat mat.
- Har chapter pichhle sections ki conclusion / warning / score repeat NA kare — naya insight add kare.
- Har conclusion kisi specific astrological factor se trace ho (Moon, Mercury, 7th lord, dasha, etc.).
- Generic relationship advice mat — jab tak chart signal support na kare.
- Score / percentage / probability ek baar establish ho chuki ho to dubara mat likho — "yeh band" / "is phase" bolo.
- Pattern KYUN exist karta hai explain karo — sirf WHAT mat.
- Personalized consultation tone — experienced astrologer, AI ya coach nahi."""
    return """NARRATIVE ARCHITECTURE (one consultation, not an AI report):
- Act as a senior astrologer with 25+ years of consulting experience — use only provided chart signals.
- Identify the single strongest root cause first (see ROOT_CAUSE block in user message).
- Build the entire narrative around that root cause — each chapter a new angle, never the same conclusion twice.
- Never repeat a conclusion, score, warning, or sentence structure already stated in PRIOR_SECTIONS.
- Every conclusion must trace to a specific astrological factor (Moon, Mercury, 7th lord, dasha, etc.).
- No generic relationship advice unless supported by chart signals.
- Do not repeat scores, percentages, or probabilities once already established — say "this band" / "this phase".
- Explain WHY the pattern exists, not just what the pattern is.
- Sound like a personalized consultation — not an AI report or coach script."""


def _human_prose_rhythm(lang: str) -> str:
    if lang == "hi":
        return """HUMAN PROSE RHYTHM (देवनागरी हिंदी — जैसे ज्योतिषी सामने समझा रहे हों):
- 100% देवनागरी — Roman वाक्य मना (नाम/स्कोर Latin में ठीक)।
- छोटे वाक्य (8–15 शब्द)। हर पैराग्राफ 3–4 वाक्य, फिर \\n\\n।
- हर चार्ट बिंदु के बाद बताएँ — रोज़मर्रा में कैसा दिखता है।
- पूरे सेक्शन में अधिकतम 2 स्कोर — वाक्य में बुनें।
- कोच / थेरेपिस्ट टोन नहीं — अंत में एक तीखा observation।"""
    if lang == "hn":
        return """HUMAN PROSE RHYTHM (Roman Hinglish — PDF me aisa padhe jaise astrologer ne likha):
- 100% Latin script — kabhi Devanagari mat likho (क, ख, म forbidden).
- Tone: samne baith kar samjha rahe ho — WhatsApp voice note jaisa, textbook nahi.
- Sentences chhoti (8–15 words). Har paragraph 3–4 sentences max, phir \\n\\n.
- Hindi verbs + simple English nouns: "aap push karte ho", "chart keh raha hai", "repair delay ho".
- Har chart point ke baad likho yeh real life me kya dikhta hai — engine label mat dump karo.
- Poori section me max 2 scores — sentence ke andar weave karo, scorecard mat banao.
- Mat likho: dynamics, navigate, leverage, testament, underlying tension, emotional pacing.
- Mat likho: "communication important hai", "dono ko benefit", "effort se improve" — jab tak chart fact na ho.
- Safe counseling wrap mat — ek sharp observation par khatam karo."""
    return """HUMAN PROSE RHYTHM (must read like a human astrologer wrote it):
- Face-to-face tone — not a report, not a coach, not an AI summary.
- Short sentences (8–15 words). Max 3–4 sentences per paragraph, then \\n\\n.
- After every chart point, say what it looks like in daily life — no engine label dumps.
- At most two scores in the whole section — woven into sentences, not a scorecard.
- Do not use: dynamics, navigate, leverage, testament, underlying tension, emotional pacing.
- No generic therapy wrap — end on a sharp observation that lands for p1."""


def _love_llm_shared_voice(lang: str) -> str:
    from vedic.love_reality.premium_polish import (
        _verdict_page_banned_block,
        _verdict_page_direct_voice,
        _verdict_page_primary_reader,
    )

    if lang == "hi":
        persona = (
            "आप एक वरिष्ठ relationship ज्योतिषी हैं — सीधी, सरल देवनागरी हिंदी, "
            "जैसे सामने बैठकर समझा रहे हों। Textbook या coach tone नहीं।"
        )
    elif lang == "hn":
        persona = (
            "Aap ek senior relationship astrologer hain — seedha, simple Roman Hinglish, "
            "jaise samne baith kar samjha rahe ho. Textbook ya coach tone nahi."
        )
    else:
        persona = (
            "You are a senior relationship astrologer — simple everyday English, "
            "like explaining face-to-face. No textbook or coach tone."
        )
    return (
        f"{persona}\n\n"
        f"{_narrative_architecture(lang)}\n\n"
        f"{_human_prose_rhythm(lang)}\n\n"
        f"{_verdict_page_primary_reader(lang)}\n\n"
        f"{_verdict_page_direct_voice(lang)}\n\n"
        f"{_verdict_page_banned_block(lang)}"
    )


def _section_model(env_key: str) -> str:
    from vedic.love_reality.premium_polish import _VERDICT_PAGE_QUALITY_MODEL, _verdict_page_model

    explicit = (os.environ.get(env_key) or "").strip()
    if explicit:
        return explicit
    quality_flag = env_key.replace("_MODEL", "_QUALITY")
    if _env_flag(quality_flag):
        return _VERDICT_PAGE_QUALITY_MODEL
    return _verdict_page_model()


def _openai_kwargs(model: str, max_tokens: int, *, temp_env: str) -> dict[str, Any]:
    kwargs: dict[str, Any] = {
        "model": model,
        "response_format": {"type": "json_object"},
        "max_tokens": max_tokens,
        "timeout": float(os.environ.get("LOVE_REALITY_OPENAI_TIMEOUT", "120")),
    }
    if not model.lower().startswith("gpt-5"):
        kwargs["temperature"] = float(os.environ.get(temp_env, "0.78"))
        kwargs["presence_penalty"] = float(os.environ.get("LOVE_REALITY_SECTION_PRESENCE_PENALTY", "0.5"))
        kwargs["frequency_penalty"] = float(os.environ.get("LOVE_REALITY_SECTION_FREQUENCY_PENALTY", "0.3"))
    return kwargs


def _cache_dir() -> str:
    base = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "..", ".cache", "love_polish")
    )
    os.makedirs(base, exist_ok=True)
    return base


def _few_shot_name_rule(lang: str) -> str:
    if lang == "hn":
        return "CRITICAL: Example mein jo naam hain wo sirf style hain — user message ke ACTUAL p1/p2 naam use karo. Aarav/Riya mat likho."
    if lang == "hi":
        return "CRITICAL: उदाहरण के नाम सिर्फ शैली के लिए हैं — user message के ACTUAL p1/p2 नाम लिखो। Aarav/Riya मत लिखो।"
    return "CRITICAL: Example names are style only — use ACTUAL p1/p2 names from the user message. Never write Aarav or Riya."


def _chapter_few_shot(chapter_key: str, lang: str) -> str:
    name_rule = _few_shot_name_rule(lang)
    if chapter_key == "love_connection":
        if lang == "hn":
            return f"""{name_rule}
MAT AISE MAT LIKHO: "Chart signals for this theme are active..."
AISE LIKHO (p1 ideal vs partner reality — real names):
"[p1_name], tumhari 7th house aur Upapada stability chahte hain. Par [p2_name] ki chart alag rhythm laati hai. Tumhe lagta hai sunai nahi deti; unhe lagta hai tum push karte ho."
"""
        if lang == "hi":
            return f"""{name_rule}
ऐसे मत लिखो: "Chart signals for this theme are active..."
ऐसे लिखो (p1 का ideal बनाम partner की reality — असली नाम):
"[p1_name], आपकी 7th house और Upapada स्थिरता चाहती है। पर [p2_name] की कुंडली अलग लय लाती है। आपको लगता है सुना नहीं जाता; उन्हें लगता है आप दबाव डालते हैं।"
"""
        return f"""{name_rule}
DO NOT: "Chart signals for this theme are active between both partners..."
WRITE (p1 — ideal blueprint vs partner reality, use real names):
"[p1_name], your 7th house and Upapada point to warmth and steadiness. [p2_name]'s chart runs on a different rhythm — processes inside first. You feel unheard when they go quiet; they feel pushed when you chase answers."
"""
    if chapter_key == "breakup":
        if lang == "hn":
            return f"""{name_rule}
AISE LIKHO: "[p1_name], jab baat atakti hai tum turant solve karna chahte ho. [p2_name] chup ho jate hain, tum push karte ho. Repair 48 ghante delay ho to separation feel hoti hai."
"""
        if lang == "hi":
            return f"""{name_rule}
ऐसे लिखो: "[p1_name], जब बात अटकती है आप तुरंत हल चाहते हैं। [p2_name] चुप हो जाते हैं, आप दबाव बढ़ाते हैं। मरम्मत में ४८ घंटे देरी हो तो अलग होने जैसा लगता है।"
"""
        return f"""{name_rule}
WRITE: "[p1_name], when talk stalls you move to fix it fast. [p2_name] goes quiet and you push harder. Separation feels close when repair waits more than 48 hours."
"""
    if chapter_key == "loyalty":
        if lang == "hn":
            return f"""{name_rule}
AISE LIKHO: "[p1_name], trust consistency se measure karte ho — jab [p2_name] silent hote hain mind worst-case bharta hai."
"""
        if lang == "hi":
            return f"""{name_rule}
ऐसे लिखो: "[p1_name], आप भरोसा consistency से मापते हैं — जब [p2_name] चुप होते हैं दिमाग worst-case भर देता है।"
"""
        return f"""{name_rule}
WRITE: "[p1_name], you measure trust through consistency — when [p2_name] is silent your mind fills worst-case stories."
"""
    if chapter_key == "red_flags":
        if lang == "hn":
            return f"""{name_rule}
AISE LIKHO (sharp, 3 chhoti paragraphs):
"[p1_name], do pattern bar-bar dikhte hain — gusse ke peak par ultimatum, aur silence ko jaan-bujhkar ignore samajhna. Chart breakup pressure high hai — matlab chhoti fight bhi separation jaisi feel ho sakti hai. Yeh lecture nahi, pattern recognition hai."
"""
        if lang == "hi":
            return f"""{name_rule}
ऐसे लिखो (तीखा, 3 छोटे paragraphs):
"[p1_name], दो पैटर्न बार-बार दिखते हैं — गुस्से के peak पर ultimatum, और चुप्पी को जान-बूjhकर ignore समझना। Chart breakup pressure high है — छोटी लड़ाई भी separation जaisa feel हो सकती है। यeh lecture नहीं, pattern recognition है।"
"""
        return f"""{name_rule}
WRITE (sharp, 3 short paragraphs, real names):
"[p1_name], two patterns keep returning — ultimatums at peak anger, and reading silence as intentional ignore. Breakup pressure is high on the chart — small fights can feel like the end. Name both plainly; this is pattern recognition, not a lecture."
"""
    return ""


def _harmony_few_shot(lang: str) -> str:
    name_rule = _few_shot_name_rule(lang)
    if lang == "hn":
        return f"""{name_rule}
AISE LIKHO (honest, real names):
"[p1_name], Fire aur Earth mix me tum jaldi react karte ho, [p2_name] slow recharge karte hain. Agar alag hue to chart genuine return ko kam probability deta hai — false reunion promise mat do. Repair habit ke bina 6-8 mahine ka loop wapas aata hai."
"""
    if lang == "hi":
        return f"""{name_rule}
AISE LIKHO (honest, real names — Devanagari Hindi, hn/en jitni depth):
"[p1_name], Fire aur Earth mix me aap jaldi react karte ho, [p2_name] slow recharge karte hain. Alag hue to chart genuine return ko kam probability deta hai — false reunion promise mat do. Repair habit ke bina 6-8 mahine ka loop wapas aata hai."
"""
    return f"""{name_rule}
WRITE (honest, real names):
"[p1_name], your Fire and their Earth pull at different speeds — you react fast, they recharge slow. If apart the chart gives low genuine-return probability — do not promise reunion. Without repair habits the same six-to-eight month loop returns."
"""


def _dasha_few_shot(lang: str) -> str:
    name_rule = _few_shot_name_rule(lang)
    if lang == "hn":
        return f"""{name_rule}
AISE LIKHO:
"[p1_name], abhi aap Jupiter MD mein ho, Rahu AD chal raha hai — patience stretch hoti hai. [p2_name] Saturn AD mein slow reply dete hain. Jab dono cycles communication ko stress karein, 24 ghante ke andar friction naam karo — ultimatum mat."
"""
    if lang == "hi":
        return f"""{name_rule}
AISE LIKHO (Devanagari Hindi — hn/en jitni depth):
"[p1_name], abhi aap Jupiter MD mein ho, Rahu AD chal raha hai — patience stretch hoti hai. [p2_name] Saturn AD mein slow reply dete hain. Jab dono cycles communication ko stress karein, 24 ghante ke andar friction naam karo — ultimatum mat."
"""
    return f"""{name_rule}
WRITE:
"[p1_name], you're in Jupiter MD with Rahu AD running — patience gets stretched. [p2_name] is in Saturn AD and replies slow. When both cycles stress communication, name the friction within 24 hours — no ultimatums."
"""


def _roadmap_few_shot(lang: str) -> str:
    name_rule = _few_shot_name_rule(lang)
    if lang == "hn":
        return f"""{name_rule}
AISE LIKHO (3/12/36 month alag paragraphs):
"Agle 3 mahine: trend mixed — repair habit bina wahi loop. 12 mahine: outlook strained — clarity ke liye ek baar calmly baithna. 36 mahine: return probability low — false reunion promise mat, chart honest hai."
"""
    if lang == "hi":
        return f"""{name_rule}
AISE LIKHO (3/12/36 month alag paragraphs — Devanagari, hn/en jitni depth):
"Agle 3 mahine: trend mixed — repair habit bina wahi loop. 12 mahine: outlook strained — clarity ke liye ek baar calmly baithna. 36 mahine: return probability low — false reunion promise mat, chart honest hai."
"""
    return f"""{name_rule}
WRITE (separate paragraphs for 3 / 12 / 36 months):
"Next 3 months: mixed trend — same loop without repair habits. Next 12 months: strained outlook — one calm sit-down for clarity. Next 36 months: low return probability — no false reunion promise; the chart is honest."
"""


def _red_flags_engine_facts(bundle: dict) -> str:
    rf = bundle.get("hidden_red_flags") or {}
    bu = bundle.get("breakup_chances") or {}
    ly = bundle.get("loyalty_check") or {}
    lines = [
        f"Breakup pressure score: {bu.get('breakup_score') or bu.get('score') or '?'}/100",
        f"Loyalty score: {ly.get('loyalty_score') or ly.get('score') or '?'}/100",
    ]
    for r in (rf.get("reasons") or [])[:6]:
        lines.append(f"Red-flag signal: {r}")
    for r in (bu.get("reasons") or [])[:3]:
        lines.append(f"Friction signal: {r}")
    return "ENGINE RED-FLAG FACTS (name these patterns in prose):\n" + "\n".join(lines)


def _moon_engine_facts(bundle: dict) -> str:
    from vedic.love_reality.pdf_data_v2 import _moon_sign_idx, _shashtashtak

    p1 = bundle.get("p1") or {}
    p2 = bundle.get("p2") or {}
    k1 = bundle.get("kundli_p1") or {}
    k2 = bundle.get("kundli_p2") or {}
    lc = bundle.get("love_compatibility") or {}
    sig = bundle.get("couple_signals") or {}
    m1, m2 = _moon_sign_idx(k1), _moon_sign_idx(k2)
    shash = _shashtashtak(m1, m2)
    p1m = p1.get("moonSign") or p1.get("rashi") or k1.get("moonSign") or "?"
    p2m = p2.get("moonSign") or p2.get("rashi") or k2.get("moonSign") or "?"
    lines = [
        "MOON SYNC ENGINE FACTS (explain emotional rhythm for p1 in prose):",
        f"{p1.get('name') or 'p1'} Moon: {p1m} · nakshatra {p1.get('nakshatra') or k1.get('nakshatra') or '?'}",
        f"{p2.get('name') or 'p2'} Moon: {p2m} · nakshatra {p2.get('nakshatra') or k2.get('nakshatra') or '?'}",
        f"Shashtashtak (6-8 Moon clash): {'yes' if shash else 'no'}",
        f"Moon mismatch signal: {sig.get('moon_mismatch') if sig.get('moon_mismatch') is not None else 'unknown'}",
    ]
    for n in (sig.get("synastry_notes") or [])[:4]:
        t = str(n).strip()
        if t:
            lines.append(f"Synastry note: {t}")
    for r in (lc.get("reasons") or [])[:4]:
        t = str(r).strip()
        if t:
            lines.append(f"Emotional signal: {t}")
    return "\n".join(lines)


def _dasha_engine_facts(bundle: dict) -> str:
    p1 = bundle.get("p1") or {}
    p2 = bundle.get("p2") or {}
    k1 = bundle.get("kundli_p1") or {}
    k2 = bundle.get("kundli_p2") or {}
    fo = bundle.get("future_outcome") or {}
    lines = ["VIMSHOTTARI DASHA FACTS (explain in plain guide for p1):"]
    for nm, kraw in ((p1.get("name") or "p1", k1), (p2.get("name") or "p2", k2)):
        cd = kraw.get("currentDasha") or {}
        maha, antar = cd.get("maha"), cd.get("antar")
        start, end = cd.get("startDate"), cd.get("endDate")
        if maha:
            bit = f"{nm}: Mahadasha {maha}"
            if antar:
                bit += f", Antardasha {antar}"
            if start and end:
                bit += f" (window {start} → {end})"
            lines.append(bit)
    if fo.get("next_shift"):
        lines.append(f"Couple dasha outlook: {fo.get('next_shift')}")
    sig = bundle.get("couple_signals") or {}
    for n in (sig.get("synastry_notes") or [])[:3]:
        lines.append(f"Synastry note: {n}")
    return "\n".join(lines)


def _roadmap_engine_facts(bundle: dict) -> str:
    fo = bundle.get("future_outcome") or {}
    wr = bundle.get("will_return") or {}
    bu = bundle.get("breakup_chances") or {}
    lc = bundle.get("love_compatibility") or {}
    timeline = fo.get("timeline_flow") or []
    t3 = timeline[1] if len(timeline) > 1 else {}
    lines = [
        "ROADMAP ENGINE SCORES (use once — elsewhere say 'this band' / 'this phase', do NOT repeat numbers):",
        f"Love score: {lc.get('score') or '?'}/100",
        f"Future outlook score: {fo.get('future_score') or fo.get('score') or '?'}/100",
        f"Return probability: {wr.get('return_probability') or wr.get('score') or '?'}/100",
        f"Breakup pressure: {bu.get('breakup_score') or bu.get('score') or '?'}/100",
        f"Next 3 months trend: {t3.get('trend') or 'mixed'} — {t3.get('reason') or fo.get('emotional_summary') or ''}",
        f"Next 12 months outlook: {fo.get('outcome') or 'mixed'} — {fo.get('current_phase') or ''}",
        f"Next 36 months / return band: {wr.get('return_chance') or 'mixed'} — {wr.get('time_window') or fo.get('outcome') or ''}",
    ]
    if fo.get("next_shift"):
        lines.append(f"Phase shift note: {fo.get('next_shift')}")
    return "\n".join(lines)


def _pick_root_cause_text(bundle: dict) -> tuple[str, list[str]]:
    """Engine-picked single strongest friction line + chart hooks for narrative anchor."""
    bu = bundle.get("breakup_chances") or {}
    rf = bundle.get("hidden_red_flags") or {}
    lc = bundle.get("love_compatibility") or {}
    sig = bundle.get("couple_signals") or {}
    p1 = bundle.get("p1") or {}
    p2 = bundle.get("p2") or {}

    candidates: list[str] = []
    summ = str(bu.get("emotional_summary") or "").strip()
    if summ:
        candidates.append(summ)
    for r in (bu.get("reasons") or [])[:3]:
        t = str(r).strip()
        if t and t not in candidates:
            candidates.append(t)
    for r in (rf.get("reasons") or [])[:2]:
        t = str(r).strip()
        if t and t not in candidates:
            candidates.append(t)
    if not candidates:
        fallback = str(lc.get("emotional_summary") or "").strip()
        candidates.append(fallback or "Chart affliction creates recurring emotional friction between these two Moons.")

    hooks: list[str] = []
    for n in (sig.get("synastry_notes") or [])[:3]:
        t = str(n).strip()
        if t:
            hooks.append(t)
    mm = sig.get("moon_mismatch")
    if mm:
        hooks.append(f"Moon mismatch signal: {mm}")
    p1m = p1.get("moonSign") or p1.get("rashi")
    p2m = p2.get("moonSign") or p2.get("rashi")
    if p1m and p2m:
        hooks.append(
            f"{p1.get('name') or 'p1'} Moon {p1m} vs {p2.get('name') or 'p2'} Moon {p2m}"
        )
    return candidates[0], hooks


def _build_root_cause_anchor(bundle: dict, lang: str) -> str:
    primary, hooks = _pick_root_cause_text(bundle)
    hook_block = "\n".join(f"- {h}" for h in hooks[:4]) if hooks else "- Use Moon / Mercury / 7th-lord facts from chart summary below."
    if lang == "hn":
        return (
            "ROOT_CAUSE (poori report isi ek reason ke around — har chapter alag angle):\n"
            f"Primary friction: {primary}\n\n"
            f"Chart hooks (har conclusion inme se trace ho):\n{hook_block}\n\n"
            "Breakup chapter = root cause KYUN exist karta hai explain kare. "
            "Baaki chapters = root cause par naya angle — same warning / score repeat mat."
        )
    return (
        "ROOT_CAUSE (entire report orbits this one friction — each chapter a new angle):\n"
        f"Primary friction: {primary}\n\n"
        f"Chart hooks (every conclusion must trace to one of these):\n{hook_block}\n\n"
        "Breakup chapter OWNS why this root cause exists astrologically. "
        "Other chapters extend it — never repeat the same warning or score."
    )


def _build_prior_sections_digest(pro: dict, lang: str) -> str:
    parts: list[str] = []
    verdict = str(pro.get("verdict") or "").strip()
    if verdict:
        excerpt = verdict[:480] + ("…" if len(verdict) > 480 else "")
        parts.append(excerpt)

    da = pro.get("deep_analysis") or []
    if da:
        for row in da[:6]:
            if not isinstance(row, dict):
                continue
            key = str(row.get("key") or row.get("title") or "?").strip()
            expl = str(row.get("explanation") or row.get("body") or "").strip()
            if expl:
                parts.append(f"[{key}]: {expl[:140]}")

    if not parts:
        return ""

    header = (
        "PRIOR_SECTIONS (already stated — do NOT repeat conclusions, scores, warnings, or opener patterns):"
        if lang == "en"
        else (
            "PRIOR_SECTIONS (pahle bol chuke — nishkarsh / score / chetavani dubara mat likho):"
            if lang == "hi"
            else "PRIOR_SECTIONS (yeh pehle bol chuke — conclusion / score / warning dubara mat likho):"
        )
    )
    return header + "\n" + "\n".join(parts)


def _section_angle_block(section_key: str, lang: str) -> str:
    angles_en = {
        "blueprint_reality": (
            "SECTION ANGLE: Ideal partner blueprint (7th, Upapada, Venus) vs who p2 actually is — "
            "show mismatch through ROOT_CAUSE, not a new unrelated reason."
        ),
        "breakup": (
            "SECTION ANGLE: OWN the root cause — explain WHY this friction pattern exists in the charts. "
            "Do not list generic breakup advice."
        ),
        "loyalty": (
            "SECTION ANGLE: How ROOT_CAUSE erodes trust and consistency — do not re-explain the root cause from scratch."
        ),
        "red_flags": (
            "SECTION ANGLE: Name the sharpest friction patterns tied to chart signals — "
            "no repeated warnings from PRIOR_SECTIONS."
        ),
        "harmony": (
            "SECTION ANGLE: Long-term element balance and what shifts the bond — connect to ROOT_CAUSE, new theory."
        ),
        "dasha": (
            "SECTION ANGLE: When ROOT_CAUSE peaks or eases in dasha — timing only, no score rehash."
        ),
        "roadmap": (
            "SECTION ANGLE: 3/12/36 month practical arc for p1 — refer to bands/phases, do not repeat score numbers."
        ),
        "moon_sync": (
            "SECTION ANGLE: Moon emotional rhythm — how p1 and p2 feel, react, and repair under stress. "
            "Connect to ROOT_CAUSE through Moon signs / nakshatra / shashtashtak — no generic moon sign list."
        ),
        "remedies_action": (
            "SECTION ANGLE: Practical remedies + what p1 should do NOW and over next 3–12 months. "
            "Behavior-first, simple chart-tied habits second — NO score dump, NO generic therapy clichés."
        ),
    }
    angles_hn = {
        "blueprint_reality": (
            "SECTION ANGLE: p1 ka ideal partner vs p2 ki asli nature — ROOT_CAUSE se mismatch dikhao, naya alag reason mat."
        ),
        "breakup": (
            "SECTION ANGLE: ROOT_CAUSE KYUN hai — chart se explain karo. Generic breakup advice mat."
        ),
        "loyalty": (
            "SECTION ANGLE: ROOT_CAUSE trust ko kaise todta hai — root cause dubara poori tarah mat samjhao."
        ),
        "red_flags": (
            "SECTION ANGLE: Chart-backed red flags — PRIOR_SECTIONS ki warning repeat mat."
        ),
        "harmony": (
            "SECTION ANGLE: Long-term elements + bond shift — ROOT_CAUSE se judo, naya insight."
        ),
        "dasha": (
            "SECTION ANGLE: ROOT_CAUSE kab peak / ease — timing, score dubara mat."
        ),
        "roadmap": (
            "SECTION ANGLE: 3/12/36 month guide — band/phase bolo, score numbers repeat mat."
        ),
        "moon_sync": (
            "SECTION ANGLE: Moon emotional rhythm — p1/p2 feel aur react kaise karte hain stress mein. "
            "ROOT_CAUSE se Moon signs / nakshatra / shashtashtak se judo — generic moon list mat."
        ),
        "remedies_action": (
            "SECTION ANGLE: Practical upay + ab kya karein + agle 3–12 mahine ka plan. "
            "Pehle daily habits / repair steps — score numbers mat likho."
        ),
    }
    angles_hi = {
        "blueprint_reality": (
            "SECTION ANGLE: p1 ka ideal partner vs p2 ki asli nature — ROOT_CAUSE se mismatch dikhao; "
            "naya alag reason mat. Har chart point ke baad daily life me kya dikhta hai explain karo."
        ),
        "breakup": (
            "SECTION ANGLE: ROOT_CAUSE KYUN hai — chart se explain karo. Generic breakup advice mat."
        ),
        "loyalty": (
            "SECTION ANGLE: ROOT_CAUSE trust ko kaise todta hai — root cause dubara poori tarah mat samjhao."
        ),
        "red_flags": (
            "SECTION ANGLE: Chart-backed red flags — PRIOR_SECTIONS ki warning repeat mat."
        ),
        "harmony": (
            "SECTION ANGLE: Long-term elements + bond shift — ROOT_CAUSE se judo, naya insight."
        ),
        "dasha": (
            "SECTION ANGLE: ROOT_CAUSE kab peak / ease — timing, score dubara mat."
        ),
        "roadmap": (
            "SECTION ANGLE: 3/12/36 month guide — band/phase bolo, score numbers repeat mat."
        ),
        "moon_sync": (
            "SECTION ANGLE: Moon emotional rhythm — p1/p2 stress me feel aur react kaise karte hain. "
            "ROOT_CAUSE se Moon signs / nakshatra / shashtashtak se judo — generic moon list mat."
        ),
        "remedies_action": (
            "SECTION ANGLE: Practical upay + ab kya karein + agle 3–12 mahine ka plan. "
            "Pehle daily habits / repair steps — score numbers mat likho."
        ),
    }
    if lang == "hn":
        table = angles_hn
    elif lang == "hi":
        table = angles_hi
    else:
        table = angles_en
    return table.get(section_key, "")


def _chapter_section_brief(chapter_key: str, lang: str) -> str:
    briefs = {
        "love_connection": (
            "PDF Section 05 — Partner Blueprint vs Reality. "
            "p1 ideal signature (7th, Upapada, Venus) vs p2 actual nature. "
            "Connect to ROOT_CAUSE — no unrelated second reason."
        ),
        "breakup": (
            "PDF Section 08 — Core Root Cause. OWN why friction escalates — every paragraph traces to a chart factor."
        ),
        "loyalty": (
            "PDF Section 09 — Loyalty & Trust under pressure. "
            "Extend ROOT_CAUSE into trust — do NOT say 'naturally loyal' if score is low."
        ),
        "red_flags": (
            "PDF Section 10 — Red Flags lead-in. Chart-backed patterns only — sharp, no bullet list, no generic advice."
        ),
    }
    return briefs.get(chapter_key, "")


def _build_chapter_system_prompt(chapter_key: str, lang: str) -> str:
    lang = polish_content_lang(lang)
    script = love_write_script_label(lang)
    return f"""Write ONLY one Love Reality chapter — key `{chapter_key}`.

{love_script_directive(lang)}

Return STRICT JSON:
{{
  "chapter_body": "long prose",
  "grounding": "2-3 chart fact lines in plain words"
}}

Write entirely in {script}.

{_chapter_section_brief(chapter_key, lang)}

RULES:
- Minimum {_CHAPTER_MIN_WORDS}+ words, {_CHAPTER_MIN_WORDS // 3}+ paragraphs (\\n\\n).
- Simple words — no high-end English, no corporate psychology.
- Talk TO p1 (first kundli). Partner as context.
- Every conclusion must trace to a specific astrological factor from user message.
- Never repeat conclusions, scores, or warnings from PRIOR_SECTIONS — add a new angle on ROOT_CAUSE.
- No safe counseling wrap ending.

{_love_llm_shared_voice(lang)}

{_chapter_few_shot(chapter_key, lang)}

Use ONLY facts from the user message."""


def _build_harmony_system_prompt(lang: str) -> str:
    lang = polish_content_lang(lang)
    script = love_write_script_label(lang)
    return f"""Write ONLY PDF Section 11 — Harmony Formula (long-term + reconnection context combined).

{love_script_directive(lang)}

Return STRICT JSON:
{{
  "harmony": "long prose"
}}

Write entirely in {script}.

RULES:
- Minimum {_HARMONY_MIN_WORDS}+ words. Honest about return_probability — no false reunion promises.
- Long-term direction + what shifts the bond — p1 lens, simple English.
- Element clash (Fire/Earth/Air/Water) from Moon signs if in facts.

{_love_llm_shared_voice(lang)}

{_harmony_few_shot(lang)}

Use ONLY facts from the user message."""


def _blueprint_chart_facts(bundle: dict) -> str:
    """Deterministic 7th/UL/Venus lines — anchor LLM for Partner Blueprint vs Reality."""
    from vedic.love_reality.pdf_data_v2 import _partner_blueprint

    p1 = bundle.get("p1") or {}
    p2 = bundle.get("p2") or {}
    k1 = bundle.get("kundli_p1") or {}
    k2 = bundle.get("kundli_p2") or {}
    lc = bundle.get("love_compatibility") or {}
    p1_bp = _partner_blueprint(k1, p1.get("name") or "You")
    p2_bp = _partner_blueprint(k2, p2.get("name") or "Partner")
    love = int(lc.get("score") or 0)
    return (
        "CHART BLUEPRINT FACTS (cite these in prose — ideal vs actual):\n\n"
        f"YOUR IDEAL PARTNER SIGNATURE ({p1.get('name') or 'p1'}):\n"
        + "\n".join(p1_bp["lines"])
        + f"\n\nPARTNER ACTUAL SIGNATURE ({p2.get('name') or 'p2'}):\n"
        + "\n".join(p2_bp["lines"])
        + f"\n\nElement mix: You {p1_bp['element']} · Partner {p2_bp['element']}\n"
        f"Love compatibility score: {love}/100 — explain gap between ideal blueprint and partner reality."
    )


def _build_blueprint_reality_system_prompt(lang: str) -> str:
    lang = polish_content_lang(lang)
    script = love_write_script_label(lang)
    return f"""Write ONLY PDF Section — Partner Blueprint vs Reality (love_connection).

Return STRICT JSON:
{{
  "blueprint_reality": "long prose comparing p1 ideal partner signature vs p2 actual nature",
  "chapter_body": "same text as blueprint_reality",
  "grounding": "2-3 chart fact lines"
}}

Write entirely in {script}.

{love_script_directive(lang)}

TASK:
- Page title: Partner Blueprint vs Reality
- p1 chart shows IDEAL partner (7th lord, Venus, Jupiter, Upapada)
- p2 chart shows ACTUAL partner nature
- Explain the GAP in simple words — not generic love advice
- Minimum 100 words, 3 paragraphs separated by \\n\\n
- Use REAL names from user message for p1 and p2

{_love_llm_shared_voice(lang)}

{_few_shot_name_rule(lang)}
DO NOT copy engine one-liner summaries verbatim.
DO NOT write only one sentence.

{_few_shot_name_rule(lang)}
Example shape (replace [p1_name]/[p2_name] with ACTUAL names from user message):
"[p1_name], tumhari 7th house steady partner maangti hai — clear baat, warmth. [p2_name] ki chart alag rhythm laati hai — pehle andar process. Tumhe lagta hai sunai nahi deti; unhe lagta hai tum dabav daal rahe ho. Love score is gap ko measure karta hai."

Use ONLY facts from the user message."""


def polish_love_reality_blueprint_reality_only(
    bundle: dict,
    lang: str = "en",
    *,
    force_llm: bool = False,
    tel: PdfGenOpenAITelemetry | None = None,
) -> dict[str, Any]:
    """Dedicated LLM for PDF Page 5 — Partner Blueprint vs Reality."""
    requested_lang = normalize_pro_pdf_lang(lang)
    lang = polish_content_lang(requested_lang)
    model = _section_model("LOVE_REALITY_BLUEPRINT_REALITY_MODEL")
    system = _build_blueprint_reality_system_prompt(lang)
    user = (
        _build_section_user_prompt(
            bundle,
            lang,
            section_note="Write Partner Blueprint vs Reality for p1 — ideal chart vs partner actual.",
        )
        + "\n\n"
        + _blueprint_chart_facts(bundle)
        + "\n\nEmit JSON with blueprint_reality and chapter_body (same text)."
    )
    max_tok = min(int(os.environ.get("LOVE_REALITY_BLUEPRINT_REALITY_MAX_TOKENS", "2400")), 4096)

    def _parse(parsed: dict) -> dict[str, Any]:
        body = str(
            parsed.get("blueprint_reality")
            or parsed.get("chapter_body")
            or parsed.get(CHAPTER_BODY_KEY)
            or ""
        ).strip()
        if _word_count(body) < 50:
            return {}
        grounding = str(parsed.get("grounding") or "").strip()
        return {
            "chapter_key": _BLUEPRINT_REALITY_KEY,
            "chapter_body": body,
            "blueprint_reality": body,
            "grounding": grounding,
        }

    return _run_section_llm(
        scope="blueprint_reality",
        bundle=bundle,
        lang=lang,
        model=model,
        system=system,
        user=user,
        max_tokens=max_tok,
        temp_env="LOVE_REALITY_BLUEPRINT_REALITY_TEMPERATURE",
        force_llm=force_llm,
        parse_fn=_parse,
        tel=tel,
    )


def _build_red_flags_system_prompt(lang: str) -> str:
    lang = polish_content_lang(lang)
    script = love_write_script_label(lang)
    return f"""Write ONLY PDF Section — Red Flags Matrix (lead-in prose before bullet list).

Return STRICT JSON:
{{
  "red_flags_narrative": "long sharp prose",
  "chapter_body": "same as red_flags_narrative",
  "grounding": "2 chart fact lines"
}}

Write entirely in {script}.

{love_script_directive(lang)}

TASK:
- Name the top 2–4 friction patterns for THIS couple — chart-backed
- Talk TO p1 (first kundli). Sharp, specific, no lecture, no bullet list in prose
- Minimum 80 words, 3 short paragraphs (\\n\\n)
- Match breakup/loyalty scores — if high breakup pressure, say so plainly

{_love_llm_shared_voice(lang)}
{_chapter_few_shot("red_flags", lang)}

DO NOT write generic "be careful" advice.
Use ONLY engine facts from user message."""


def polish_love_reality_red_flags_only(
    bundle: dict,
    lang: str = "en",
    *,
    force_llm: bool = False,
    tel: PdfGenOpenAITelemetry | None = None,
) -> dict[str, Any]:
    """Dedicated LLM for PDF Red Flags body (Page 12)."""
    requested_lang = normalize_pro_pdf_lang(lang)
    lang = polish_content_lang(requested_lang)
    model = _section_model("LOVE_REALITY_RED_FLAGS_MODEL")
    system = _build_red_flags_system_prompt(lang)
    user = (
        _build_section_user_prompt(bundle, lang, section_note="Write Red Flags lead-in for p1.")
        + "\n\n"
        + _red_flags_engine_facts(bundle)
    )
    max_tok = min(int(os.environ.get("LOVE_REALITY_RED_FLAGS_MAX_TOKENS", "2000")), 4096)

    def _parse(parsed: dict) -> dict[str, Any]:
        body = str(
            parsed.get("red_flags_narrative")
            or parsed.get("chapter_body")
            or parsed.get(CHAPTER_BODY_KEY)
            or ""
        ).strip()
        if _word_count(body) < 45:
            return {}
        return {
            "chapter_key": _RED_FLAGS_KEY,
            "chapter_body": body,
            "red_flags_narrative": body,
            "grounding": str(parsed.get("grounding") or "").strip(),
        }

    return _run_section_llm(
        scope="red_flags",
        bundle=bundle,
        lang=lang,
        model=model,
        system=system,
        user=user,
        max_tokens=max_tok,
        temp_env="LOVE_REALITY_RED_FLAGS_TEMPERATURE",
        force_llm=force_llm,
        parse_fn=_parse,
        tel=tel,
    )


def _build_moon_sync_system_prompt(lang: str) -> str:
    lang = polish_content_lang(lang)
    script = love_write_script_label(lang)
    return f"""Write ONLY PDF Section — Moon Sync (emotional rhythm between both Moons).

Return STRICT JSON:
{{
  "moon_sync_narrative": "long prose explaining how p1 and p2 feel, react, and repair under stress"
}}

Write entirely in {script}.

{love_script_directive(lang)}

TASK:
- Section title: Moon Sync — emotional pacing, not a textbook moon-sign list
- Explain how p1's Moon processes feelings vs p2's Moon — daily life examples
- If shashtashtak / moon mismatch is true, say what that looks like in arguments and silence
- If Moons are smoother, say what still triggers stress and how to protect rhythm
- Guide p1: what to do when partner goes quiet / when p1 reacts fast
- Minimum 80 words, 3 paragraphs (\\n\\n)
- Use REAL partner names from user message

{_love_llm_shared_voice(lang)}

Use ONLY facts from user message."""


def polish_love_reality_moon_sync_only(
    bundle: dict,
    lang: str = "en",
    *,
    force_llm: bool = False,
    tel: PdfGenOpenAITelemetry | None = None,
) -> dict[str, Any]:
    """Dedicated LLM for Moon Sync — emotional rhythm prose for in-app + PDF."""
    requested_lang = normalize_pro_pdf_lang(lang)
    lang = polish_content_lang(requested_lang)
    model = _section_model("LOVE_REALITY_MOON_SYNC_MODEL")
    system = _build_moon_sync_system_prompt(lang)
    user = (
        _build_section_user_prompt(bundle, lang, section_note="Write Moon Sync emotional rhythm guide for p1.")
        + "\n\n"
        + _moon_engine_facts(bundle)
    )
    max_tok = min(int(os.environ.get("LOVE_REALITY_MOON_SYNC_MAX_TOKENS", "2200")), 4096)

    def _parse(parsed: dict) -> dict[str, Any]:
        body = str(parsed.get("moon_sync_narrative") or "").strip()
        if _word_count(body) < 55:
            return {}
        return {"moon_sync_narrative": body}

    return _run_section_llm(
        scope="moon_sync",
        bundle=bundle,
        lang=lang,
        model=model,
        system=system,
        user=user,
        max_tokens=max_tok,
        temp_env="LOVE_REALITY_MOON_SYNC_TEMPERATURE",
        force_llm=force_llm,
        parse_fn=_parse,
        tel=tel,
    )


def _remedies_action_engine_facts(bundle: dict) -> str:
    from vedic.love_reality.pdf_data_v2 import _build_remedies

    lc = bundle.get("love_compatibility") or {}
    bu = bundle.get("breakup_chances") or {}
    fo = bundle.get("future_outcome") or {}
    wr = bundle.get("will_return") or {}
    lines = [
        "REMEDIES & ACTION FACTS (use for practical guidance — do NOT quote scores in prose):",
        f"Connection band: {lc.get('risk_level') or 'mixed'} — emotional summary: {str(lc.get('emotional_summary') or '')[:200]}",
        f"Stress pattern: {str(bu.get('emotional_summary') or '')[:180]}",
        f"Near-term outlook: {str(fo.get('current_phase') or fo.get('emotional_summary') or '')[:180]}",
        f"Return window note: {str(wr.get('time_window') or wr.get('return_chance') or '')[:120]}",
    ]
    for r in _build_remedies(bundle, {}):
        lines.append(f"Chart-linked habit: {r}")
    for r in (lc.get("reasons") or [])[:2]:
        t = str(r).strip()
        if t:
            lines.append(f"Friction to address: {t}")
    return "\n".join(lines)


def _build_remedies_action_system_prompt(lang: str) -> str:
    lang = polish_content_lang(lang)
    script = love_write_script_label(lang)
    return f"""Write ONLY Section 4 — Practical Remedies & What To Do Next (in-app action plan for p1).

Return STRICT JSON:
{{
  "remedies_action_narrative": "long prose: daily practical remedies + next steps + next 3–12 month plan",
  "action_steps": ["5–7 short practical one-liners — habits, repair rituals, timing, simple chart-tied upay"]
}}

Write entirely in {script}.

{love_script_directive(lang)}

TASK — focus 80% PRACTICAL, 20% simple chart-linked habits:
1) Ab kya karein (next 7–30 days): repair habits, communication rules, conflict cooldown — specific to ROOT_CAUSE
2) Practical remedies: daily/weekly actions p1 can actually do (not vague "communicate better")
3) Simple upay where chart facts support it (e.g. Monday calm hour, Friday gratitude note) — NO gemstone shopping lists
4) Agle 3 mahine + 12 mahine: what to build, what to avoid, when to seek clarity — honest if outlook is strained
5) If connection feels weak, say what improves odds — never false reunion promises

RULES:
- Minimum 110 words in remedies_action_narrative, 3–4 paragraphs (\\n\\n)
- action_steps: exactly 5–7 bullets, each 8–18 words, verb-first ("Repair within 24h…")
- Do NOT repeat verdict paragraphs or moon/blueprint analysis
- Do NOT write scores like "13/100" or "love score" — say "jab connection kamzor lagta hai"
- No generic therapy clichés ("open communication", "mutual understanding")

{_love_llm_shared_voice(lang)}

Use ONLY facts from user message."""


def polish_love_reality_remedies_action_only(
    bundle: dict,
    lang: str = "en",
    *,
    force_llm: bool = False,
    tel: PdfGenOpenAITelemetry | None = None,
) -> dict[str, Any]:
    """Dedicated LLM for Section 4 — practical remedies + action plan + near future."""
    requested_lang = normalize_pro_pdf_lang(lang)
    lang = polish_content_lang(requested_lang)
    model = _section_model("LOVE_REALITY_REMEDIES_ACTION_MODEL")
    system = _build_remedies_action_system_prompt(lang)
    user = (
        _build_section_user_prompt(
            bundle,
            lang,
            section_note="Write Section 4 practical remedies and what p1 should do next (include 3–12 month plan).",
        )
        + "\n\n"
        + _remedies_action_engine_facts(bundle)
    )
    max_tok = min(int(os.environ.get("LOVE_REALITY_REMEDIES_ACTION_MAX_TOKENS", "2600")), 4096)

    def _parse(parsed: dict) -> dict[str, Any]:
        body = str(parsed.get("remedies_action_narrative") or "").strip()
        steps_raw = parsed.get("action_steps")
        steps: list[str] = []
        if isinstance(steps_raw, list):
            steps = [str(x).strip() for x in steps_raw if str(x).strip()]
        elif isinstance(steps_raw, str) and steps_raw.strip():
            steps = [steps_raw.strip()]
        if _word_count(body) < 70:
            return {}
        return {"remedies_action_narrative": body, "action_steps": steps[:7]}

    return _run_section_llm(
        scope="remedies_action",
        bundle=bundle,
        lang=lang,
        model=model,
        system=system,
        user=user,
        max_tokens=max_tok,
        temp_env="LOVE_REALITY_REMEDIES_ACTION_TEMPERATURE",
        force_llm=force_llm,
        parse_fn=_parse,
        tel=tel,
    )


def _build_dasha_system_prompt(lang: str) -> str:
    lang = polish_content_lang(lang)
    script = love_write_script_label(lang)
    return f"""Write ONLY PDF Section — Vimshottari Dasha Synchronization (guide for p1).

Return STRICT JSON:
{{
  "dasha_narrative": "long prose explaining both partners' dasha cycles and what p1 should watch"
}}

Write entirely in {script}.

{love_script_directive(lang)}

TASK:
- Explain p1 and p2 current MD/AD in simple words — not textbook Sanskrit
- Say how cycles align OR clash for this couple right now
- Guide p1: what to do / avoid in this antardasha window (repair, patience, no ultimatums)
- Minimum 90 words, 3 paragraphs (\\n\\n)
- Use exact dasha names and date windows from facts only

{_love_llm_shared_voice(lang)}
{_dasha_few_shot(lang)}

Use ONLY facts from user message."""


def polish_love_reality_dasha_only(
    bundle: dict,
    lang: str = "en",
    *,
    force_llm: bool = False,
    tel: PdfGenOpenAITelemetry | None = None,
) -> dict[str, Any]:
    """Dedicated LLM for PDF Dasha page — prose guide + engine bullets at render."""
    requested_lang = normalize_pro_pdf_lang(lang)
    lang = polish_content_lang(requested_lang)
    model = _section_model("LOVE_REALITY_DASHA_MODEL")
    system = _build_dasha_system_prompt(lang)
    user = (
        _build_section_user_prompt(bundle, lang, section_note="Write Dasha sync guide for p1.")
        + "\n\n"
        + _dasha_engine_facts(bundle)
    )
    max_tok = min(int(os.environ.get("LOVE_REALITY_DASHA_MAX_TOKENS", "2200")), 4096)

    def _parse(parsed: dict) -> dict[str, Any]:
        body = str(parsed.get("dasha_narrative") or "").strip()
        if _word_count(body) < 60:
            return {}
        return {"dasha_narrative": body}

    return _run_section_llm(
        scope="dasha",
        bundle=bundle,
        lang=lang,
        model=model,
        system=system,
        user=user,
        max_tokens=max_tok,
        temp_env="LOVE_REALITY_DASHA_TEMPERATURE",
        force_llm=force_llm,
        parse_fn=_parse,
        tel=tel,
    )


def _build_roadmap_system_prompt(lang: str) -> str:
    lang = polish_content_lang(lang)
    script = love_write_script_label(lang)
    return f"""Write ONLY PDF Section — 1–3 Year Chronological Roadmap (p1 action guide).

Return STRICT JSON:
{{
  "roadmap_narrative": "long prose guiding p1 through next 3, 12, and 36 months based on engine scores"
}}

Write entirely in {script}.

{love_script_directive(lang)}

TASK:
- Use engine trends for Next 3 months, Next 12 months, Next 36 months from facts
- Guide p1 what to expect and what TO DO each phase — repair habits, patience, clarity
- If trend is down/strained/unlikely — say honestly, no false hope
- If return probability is low — do not promise reunion
- Minimum 100 words, 3 paragraphs mapped to 3/12/36 month windows (\\n\\n)
- Simple English — astrologer advising face-to-face

{_love_llm_shared_voice(lang)}
{_roadmap_few_shot(lang)}

DO NOT invent scores or dates not in facts.
Use ONLY facts from user message."""


def polish_love_reality_roadmap_only(
    bundle: dict,
    lang: str = "en",
    *,
    force_llm: bool = False,
    tel: PdfGenOpenAITelemetry | None = None,
) -> dict[str, Any]:
    """Dedicated LLM for PDF Roadmap page — score-based guide for p1."""
    requested_lang = normalize_pro_pdf_lang(lang)
    lang = polish_content_lang(requested_lang)
    model = _section_model("LOVE_REALITY_ROADMAP_MODEL")
    system = _build_roadmap_system_prompt(lang)
    user = (
        _build_section_user_prompt(bundle, lang, section_note="Write 3/12/36 month roadmap guide for p1.")
        + "\n\n"
        + _roadmap_engine_facts(bundle)
    )
    max_tok = min(int(os.environ.get("LOVE_REALITY_ROADMAP_MAX_TOKENS", "2400")), 4096)

    def _parse(parsed: dict) -> dict[str, Any]:
        body = str(parsed.get("roadmap_narrative") or "").strip()
        if _word_count(body) < 70:
            return {}
        return {"roadmap_narrative": body}

    return _run_section_llm(
        scope="roadmap",
        bundle=bundle,
        lang=lang,
        model=model,
        system=system,
        user=user,
        max_tokens=max_tok,
        temp_env="LOVE_REALITY_ROADMAP_TEMPERATURE",
        force_llm=force_llm,
        parse_fn=_parse,
        tel=tel,
    )


def _build_section_user_prompt(bundle: dict, lang: str, *, section_note: str) -> str:
    from vedic.love_reality.premium_polish import _verdict_page_facts_summary

    p1 = bundle.get("p1") or {}
    p1_name = str(p1.get("name") or "Partner A").strip()
    lang_voice = polish_content_lang(normalize_pro_pdf_lang(lang))
    if lang_voice == "hi":
        voice = f"आप = {p1_name} (p1/पहली कुंडली)।"
    elif lang_voice == "hn":
        voice = f"Aap = {p1_name} (p1/pehli kundli)."
    else:
        voice = f"You = {p1_name} (p1/first kundli)."
    blocks = [love_script_directive(lang_voice), section_note]
    section_key = str(bundle.get("_lr_section_key") or "").strip()
    angle = _section_angle_block(section_key, lang_voice) if section_key else ""
    if angle:
        blocks.append(angle)
    root = str(bundle.get("_lr_root_cause") or "").strip()
    if root:
        blocks.append(root)
    prior = str(bundle.get("_lr_prior_digest") or "").strip()
    if prior:
        blocks.append(prior)
    blocks.append(_verdict_page_facts_summary(bundle, lang))
    blocks.append(f"language: {lang}")
    blocks.append(f"narration_style: {voice}")
    blocks.append("Emit JSON only.")
    return "\n\n".join(blocks)


def _fingerprint(blob: str) -> str:
    return hashlib.sha256(blob.encode()).hexdigest()[:10]


def _section_cache_key(bundle: dict, lang: str, model: str, scope: str, prompt_fp: str) -> str:
    from vedic.love_reality.premium_polish import _love_polish_fingerprint

    raw = "|".join([_love_polish_fingerprint(bundle, lang, model), scope, prompt_fp, _ASSEMBLY_VER])
    return hashlib.sha256(raw.encode()).hexdigest()[:32]


def _run_section_llm(
    *,
    scope: str,
    bundle: dict,
    lang: str,
    model: str,
    system: str,
    user: str,
    max_tokens: int,
    temp_env: str,
    force_llm: bool,
    parse_fn: Callable[[dict], dict[str, Any]],
    tel: PdfGenOpenAITelemetry | None,
) -> dict[str, Any]:
    empty: dict[str, Any] = {"_meta": {"scope": scope, "openai_skipped": True}}
    from vedic.love_reality.premium_polish import _polish_enabled

    if not _polish_enabled():
        empty["_meta"]["reason"] = "polish_off"
        return empty

    prompt_fp = _fingerprint(system)
    cache_key = _section_cache_key(bundle, lang, model, scope, prompt_fp)
    cache_path = os.path.join(_cache_dir(), f"{scope}_{cache_key}.json")
    force = force_llm or _env_flag(f"LOVE_REALITY_{scope.upper()}_FORCE")

    if not force and os.path.isfile(cache_path):
        try:
            with open(cache_path, "r", encoding="utf-8") as fh:
                hit = json.load(fh)
            if isinstance(hit, dict) and parse_fn(hit):
                hit.setdefault("_meta", {})["cache"] = f"{scope}_file"
                hit["_meta"]["openai_skipped"] = True
                return hit
        except Exception as exc:
            log.warning("[%s] cache read failed: %s", scope, exc)

    try:
        from openai_helper import _get_client  # type: ignore
    except Exception:
        empty["_meta"]["reason"] = "openai_import_fail"
        return empty

    client = _get_client()
    if client is None:
        empty["_meta"]["reason"] = "openai_client_none"
        return empty

    kwargs = _openai_kwargs(model, max_tokens, temp_env=temp_env)
    kwargs["messages"] = [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]
    try:
        resp = client.chat.completions.create(**kwargs)
        if tel is not None:
            tel.record(resp, scope)
        raw = (resp.choices[0].message.content or "").strip()
        if not raw:
            empty["_meta"]["reason"] = "empty_openai_body"
            return empty
        parsed = json.loads(raw)
        if not isinstance(parsed, dict):
            empty["_meta"]["reason"] = "json_not_object"
            return empty
        out = parse_fn(parsed)
        if not out:
            retry_user = user + "\n\nRETRY: prior response too short. Write LONGER — minimum 3 paragraphs."
            kwargs["messages"] = [
                {"role": "system", "content": system},
                {"role": "user", "content": retry_user},
            ]
            try:
                resp2 = client.chat.completions.create(**kwargs)
                if tel is not None:
                    tel.record(resp2, f"{scope}_retry")
                raw2 = (resp2.choices[0].message.content or "").strip()
                if raw2:
                    parsed2 = json.loads(raw2)
                    if isinstance(parsed2, dict):
                        out = parse_fn(parsed2)
            except Exception as exc2:
                log.warning("[%s] retry fail: %s", scope, exc2)
        if not out:
            empty["_meta"]["reason"] = "parse_empty"
            return empty
    except Exception as exc:
        log.warning("[%s] openai fail: %s", scope, exc)
        empty["_meta"]["reason"] = "openai_fail"
        return empty

    out.setdefault("_meta", {})
    out["_meta"].update({
        "scope": scope,
        "model": model,
        "lang": lang,
        "prompt_fingerprint": prompt_fp,
        "cache_key": cache_key[:12],
        "openai_skipped": False,
    })
    try:
        with open(cache_path, "w", encoding="utf-8") as fh:
            json.dump(out, fh, ensure_ascii=False, indent=2)
    except Exception as exc:
        log.warning("[%s] cache write failed: %s", scope, exc)
    return out


def polish_love_reality_chapter_only(
    bundle: dict,
    chapter_key: str,
    lang: str = "en",
    *,
    force_llm: bool = False,
    tel: PdfGenOpenAITelemetry | None = None,
) -> dict[str, Any]:
    if chapter_key not in _CHAPTER_KEYS:
        return {"_meta": {"scope": f"chapter_{chapter_key}", "reason": "invalid_key"}}
    requested_lang = normalize_pro_pdf_lang(lang)
    lang = polish_content_lang(requested_lang)
    scope = f"chapter_{chapter_key}"
    model = _section_model(f"LOVE_REALITY_CHAPTER_{chapter_key.upper()}_MODEL")
    system = _build_chapter_system_prompt(chapter_key, lang)
    user = _build_section_user_prompt(
        bundle,
        lang,
        section_note=f"Write chapter `{chapter_key}` for {bundle.get('p1', {}).get('name', 'p1')}.",
    )
    max_tok = min(int(os.environ.get("LOVE_REALITY_CHAPTER_MAX_TOKENS", "2800")), 4096)

    min_words = 70 if chapter_key == "red_flags" else max(90, _CHAPTER_MIN_WORDS - 30)

    def _parse(parsed: dict) -> dict[str, Any]:
        body = str(parsed.get("chapter_body") or parsed.get(CHAPTER_BODY_KEY) or "").strip()
        if _word_count(body) < min_words:
            return {}
        grounding = str(parsed.get("grounding") or "").strip()
        return {"chapter_key": chapter_key, "chapter_body": body, "grounding": grounding}

    return _run_section_llm(
        scope=scope,
        bundle=bundle,
        lang=lang,
        model=model,
        system=system,
        user=user,
        max_tokens=max_tok,
        temp_env="LOVE_REALITY_CHAPTER_TEMPERATURE",
        force_llm=force_llm,
        parse_fn=_parse,
        tel=tel,
    )


def polish_love_reality_harmony_only(
    bundle: dict,
    lang: str = "en",
    *,
    force_llm: bool = False,
    tel: PdfGenOpenAITelemetry | None = None,
) -> dict[str, Any]:
    requested_lang = normalize_pro_pdf_lang(lang)
    lang = polish_content_lang(requested_lang)
    model = _section_model("LOVE_REALITY_HARMONY_MODEL")
    system = _build_harmony_system_prompt(lang)
    user = _build_section_user_prompt(
        bundle,
        lang,
        section_note="Write Section 11 Harmony Formula — long-term + reconnection for p1.",
    )
    max_tok = min(int(os.environ.get("LOVE_REALITY_HARMONY_MAX_TOKENS", "2400")), 4096)

    def _parse(parsed: dict) -> dict[str, Any]:
        body = str(parsed.get("harmony") or "").strip()
        if _word_count(body) < max(80, _HARMONY_MIN_WORDS - 40):
            return {}
        return {"harmony": body}

    return _run_section_llm(
        scope="harmony",
        bundle=bundle,
        lang=lang,
        model=model,
        system=system,
        user=user,
        max_tokens=max_tok,
        temp_env="LOVE_REALITY_HARMONY_TEMPERATURE",
        force_llm=force_llm,
        parse_fn=_parse,
        tel=tel,
    )


def _breakup_chapter_body(pro: dict) -> str:
    for ch in pro.get("chapters") or []:
        if not isinstance(ch, dict):
            continue
        if str(ch.get("key") or "").strip().lower() == "breakup":
            return str(ch.get(CHAPTER_BODY_KEY) or ch.get("chapter_body") or "").strip()
    return ""


def breakup_chapter_word_count(pro: dict) -> int:
    return _word_count(_breakup_chapter_body(pro))


def _breakup_text_hi_ok(body: str) -> bool:
    if _word_count(body) < 80:
        return False
    try:
        from i18n_summary import prose_fully_hindi

        return prose_fully_hindi(body)
    except Exception:
        return len(re.findall(r"[\u0900-\u097F]", body)) >= 24


def breakup_chapter_hi_ready(pro: dict) -> bool:
    """Section 8 OK for Hindi — 80+ words and mostly Devanagari."""
    return _breakup_text_hi_ok(_breakup_chapter_body(pro))


def _bust_chapter_scope_file_cache(bundle: dict, lang: str, chapter_key: str) -> None:
    """Drop cached empty/short chapter_breakup LLM response so retry hits OpenAI."""
    scope = f"chapter_{chapter_key}"
    model = _section_model(f"LOVE_REALITY_CHAPTER_{chapter_key.upper()}_MODEL")
    system = _build_chapter_system_prompt(chapter_key, polish_content_lang(lang))
    prompt_fp = _fingerprint(system)
    cache_key = _section_cache_key(bundle, polish_content_lang(lang), model, scope, prompt_fp)
    cache_path = os.path.join(_cache_dir(), f"{scope}_{cache_key}.json")
    try:
        if os.path.isfile(cache_path):
            os.remove(cache_path)
    except OSError as exc:
        log.warning("[%s] cache bust failed: %s", scope, exc)


def bust_love_polish_section_caches(bundle: dict, lang: str) -> None:
    """Bust section LLM file caches — safe import from love_section_polish (always deployed with api)."""
    for chapter_key in _CHAPTER_KEYS:
        _bust_chapter_scope_file_cache(bundle, lang, chapter_key)
    try:
        base = _cache_dir()
        if os.path.isdir(base):
            for name in os.listdir(base):
                if name.endswith(".json"):
                    try:
                        os.remove(os.path.join(base, name))
                    except OSError:
                        pass
    except Exception as exc:
        log.warning("[love_section_polish] cache dir bust failed: %s", exc)


def ensure_breakup_section8_llm(
    bundle: dict,
    pro: dict,
    lang: str,
    *,
    force_llm: bool = False,
) -> dict:
    """Section 08 (Core Root Cause) — LLM breakup chapter if missing or too thin."""
    if not isinstance(pro, dict):
        return pro or {}
    body = _breakup_chapter_body(pro)
    if lang == "hi" and body and not breakup_chapter_hi_ready(pro):
        _upsert_chapter(pro, "breakup", "", "")
        body = ""
    elif _word_count(body) >= 80 and not force_llm:
        if lang != "hi" or breakup_chapter_hi_ready(pro):
            return pro
    try:
        from vedic.love_reality.pdf_text_safe import prose_matches_lang

        if (
            not force_llm
            and body
            and lang in ("hi", "hn")
            and prose_matches_lang(body, lang)
            and (lang != "hi" or breakup_chapter_hi_ready(pro))
        ):
            return pro
    except Exception:
        pass

    work = dict(bundle)
    work["_lr_root_cause"] = _build_root_cause_anchor(bundle, lang)
    work["_lr_prior_digest"] = _build_prior_sections_digest(pro, lang)
    last_meta: dict[str, Any] = {}
    max_attempts = max(1, int(os.environ.get("LOVE_REALITY_SECTION8_ATTEMPTS", "3")))
    for attempt in range(max_attempts):
        if attempt > 0:
            _bust_chapter_scope_file_cache(bundle, lang, "breakup")
        hit = polish_love_reality_chapter_only(
            work,
            "breakup",
            lang=lang,
            force_llm=True,
        )
        last_meta = hit.get("_meta") if isinstance(hit.get("_meta"), dict) else {}
        new_body = str(hit.get("chapter_body") or "").strip()
        if lang == "hi" and not _breakup_text_hi_ok(new_body):
            last_meta = {
                **last_meta,
                "reject": "not_devanagari_hi",
                "deva": len(re.findall(r"[\u0900-\u097F]", new_body)),
                "words": _word_count(new_body),
            }
            continue
        if _word_count(new_body) >= 80:
            _upsert_chapter(pro, "breakup", new_body, str(hit.get("grounding") or ""))
            pro.setdefault("_meta", {})["section8_breakup"] = {
                **last_meta,
                "attempt": attempt + 1,
                "words": _word_count(new_body),
            }
            return pro
    pro.setdefault("_meta", {})["section8_breakup"] = {
        **last_meta,
        "attempts": max_attempts,
        "words": _word_count(_breakup_chapter_body(pro)),
    }
    return pro


def _upsert_chapter(pro: dict, key: str, body: str, grounding: str = "") -> None:
    chapters = pro.setdefault("chapters", [])
    if not isinstance(chapters, list):
        chapters = []
        pro["chapters"] = chapters
    row = {"key": key, CHAPTER_BODY_KEY: body, "chapter_body": body}
    if grounding:
        row["grounding"] = grounding
    for i, ch in enumerate(chapters):
        if isinstance(ch, dict) and str(ch.get("key") or "").lower() == key:
            chapters[i] = {**ch, **row}
            return
    chapters.append(row)


def _assembly_depth_ok(pro: dict) -> bool:
    if not str(pro.get("verdict") or "").strip():
        return False
    da = pro.get("deep_analysis")
    if not isinstance(da, list) or len(da) < 4:
        return False
    by_key = {}
    for ch in pro.get("chapters") or []:
        if isinstance(ch, dict):
            k = str(ch.get("key") or "").lower()
            body = str(ch.get(CHAPTER_BODY_KEY) or ch.get("chapter_body") or "")
            if k and _word_count(body) >= 70:
                by_key[k] = body
    if not str(pro.get("blueprint_reality") or "").strip() and _BLUEPRINT_REALITY_KEY not in by_key:
        return False
    for k in _CHAPTER_KEYS:
        if k not in by_key:
            return False
    rf = str(pro.get("red_flags_narrative") or "").strip() or by_key.get(_RED_FLAGS_KEY, "")
    if _word_count(rf) < 45:
        return False
    if not str(pro.get("harmony") or "").strip() and "will_return" not in by_key:
        return False
    if _word_count(str(pro.get("dasha_narrative") or "")) < 60:
        return False
    if _word_count(str(pro.get("roadmap_narrative") or "")) < 70:
        return False
    return True


def _section_body_from_hit(hit: dict, *keys: str) -> str:
    for k in keys:
        v = str(hit.get(k) or "").strip()
        if v:
            return v
    return ""


def _invoke_section_fn(
    fn: Callable[..., dict[str, Any]],
    bundle: dict,
    lang: str,
    force_llm: bool,
    *,
    chapter_key: str | None = None,
) -> dict[str, Any]:
    if chapter_key:
        return polish_love_reality_chapter_only(
            bundle, chapter_key, lang=lang, force_llm=force_llm, tel=None
        )
    return fn(bundle, lang=lang, force_llm=force_llm, tel=None)


def _run_section_job(
    label: str,
    fn: Callable[..., dict[str, Any]],
    bundle: dict,
    lang: str,
    force_llm: bool,
    *,
    body_keys: tuple[str, ...],
    pro_key: str | None = None,
    ch_key: str | None = None,
    chapter_key: str | None = None,
) -> tuple[str, dict[str, Any], str, str | None, str | None]:
    """Run one section LLM call with retry; never raises."""
    try:
        job_bundle = dict(bundle)
        job_bundle["_lr_section_key"] = label
        hit = _invoke_section_fn(
            fn, job_bundle, lang, force_llm, chapter_key=chapter_key
        )
        body = _section_body_from_hit(hit, *body_keys)
        if not body:
            log.warning(
                "[assembly] %s miss (%s) — retry forced",
                label,
                (hit.get("_meta") or {}).get("reason"),
            )
            hit = _invoke_section_fn(
                fn, job_bundle, lang, True, chapter_key=chapter_key
            )
            body = _section_body_from_hit(hit, *body_keys)
        if not body:
            log.warning("[assembly] %s still empty after retry", label)
        return label, hit, body, pro_key, ch_key
    except Exception as exc:
        log.exception("[assembly] %s failed: %s", label, exc)
        return label, {"_meta": {"reason": "section_exception", "error": str(exc)}}, "", pro_key, ch_key


def assemble_love_reality_pro_premium(
    bundle: dict,
    lang: str = "en",
    *,
    force_llm: bool = False,
    model: str = "",
) -> dict[str, Any]:
    """Orchestrate all section LLM calls into one pro_premium dict. Never raises."""
    from vedic.love_reality.premium_polish import (
        _DEFAULT_MODEL,
        _scrub_loyalty_contradictions,
        polish_love_reality_deep_analysis_only,
        polish_love_reality_verdict_page_only,
    )
    from vedic.love_reality.premium_validate import apply_love_premium_validation

    requested_lang = normalize_pro_pdf_lang(lang)
    lang = polish_content_lang(requested_lang)
    model = model or _DEFAULT_MODEL
    tel = PdfGenOpenAITelemetry(model)
    pro: dict[str, Any] = {
        "hidden_truth": "",
        "chapters": [],
        "special": [],
        "damage": [],
        "practical": [],
        "verdict": "",
        "_meta": {"assembly": _ASSEMBLY_VER, "version": _ASSEMBLY_VER},
    }
    section_meta: dict[str, Any] = {}

    try:
        s02 = polish_love_reality_verdict_page_only(bundle, lang=lang, force_llm=force_llm)
        if s02.get("verdict"):
            pro["verdict"] = s02["verdict"]
        if s02.get("practical"):
            pro["practical"] = s02["practical"]
        section_meta["verdict_page"] = s02.get("_meta") or {}

        s03 = polish_love_reality_deep_analysis_only(bundle, lang=lang, force_llm=force_llm)
        if s03.get("deep_analysis"):
            pro["deep_analysis"] = s03["deep_analysis"]
        section_meta["deep_analysis"] = s03.get("_meta") or {}

        work_bundle = dict(bundle)
        work_bundle["_lr_root_cause"] = _build_root_cause_anchor(bundle, lang)
        work_bundle["_lr_prior_digest"] = _build_prior_sections_digest(pro, lang)

        parallel_jobs: list[tuple] = [
            (
                "blueprint_reality",
                polish_love_reality_blueprint_reality_only,
                ("chapter_body", "blueprint_reality"),
                "blueprint_reality",
                _BLUEPRINT_REALITY_KEY,
                None,
            ),
            (
                "breakup",
                polish_love_reality_chapter_only,
                ("chapter_body",),
                None,
                "breakup",
                "breakup",
            ),
            (
                "loyalty",
                polish_love_reality_chapter_only,
                ("chapter_body",),
                None,
                "loyalty",
                "loyalty",
            ),
            (
                "harmony",
                polish_love_reality_harmony_only,
                ("harmony",),
                "harmony",
                None,
                None,
            ),
            (
                "moon_sync",
                polish_love_reality_moon_sync_only,
                ("moon_sync_narrative",),
                "moon_sync_narrative",
                None,
                None,
            ),
            (
                "remedies_action",
                polish_love_reality_remedies_action_only,
                ("remedies_action_narrative",),
                "remedies_action_narrative",
                None,
                None,
            ),
            (
                "red_flags",
                polish_love_reality_red_flags_only,
                ("red_flags_narrative", "chapter_body"),
                "red_flags_narrative",
                _RED_FLAGS_KEY,
                None,
            ),
            (
                "dasha",
                polish_love_reality_dasha_only,
                ("dasha_narrative",),
                "dasha_narrative",
                None,
                None,
            ),
            (
                "roadmap",
                polish_love_reality_roadmap_only,
                ("roadmap_narrative",),
                "roadmap_narrative",
                None,
                None,
            ),
        ]

        workers = min(7, int(os.environ.get("LOVE_REALITY_SECTION_WORKERS", "5")))
        with ThreadPoolExecutor(max_workers=workers) as pool:
            futures = [
                pool.submit(
                    _run_section_job,
                    label,
                    fn,
                    work_bundle,
                    lang,
                    force_llm,
                    body_keys=body_keys,
                    pro_key=pro_key,
                    ch_key=ch_key,
                    chapter_key=chapter_key,
                )
                for label, fn, body_keys, pro_key, ch_key, chapter_key in parallel_jobs
            ]
            for fut in as_completed(futures):
                label, hit, body, pro_key, ch_key = fut.result()
                section_meta[label] = hit.get("_meta") or {}
                if not body:
                    continue
                if pro_key:
                    pro[pro_key] = body
                if ch_key:
                    _upsert_chapter(pro, ch_key, body, hit.get("grounding") or "")
                if label == "harmony":
                    _upsert_chapter(pro, "will_return", body)
                    _upsert_chapter(pro, "future_outcome", body)
                elif label == "remedies_action":
                    steps = hit.get("action_steps")
                    if isinstance(steps, list):
                        pro["action_steps"] = [str(x).strip() for x in steps if str(x).strip()][:7]
                elif label in _CHAPTER_KEYS:
                    _upsert_chapter(pro, label, body, hit.get("grounding") or "")

        _scrub_loyalty_contradictions(pro, bundle)
        pro = sanitize_love_reality_pro_premium(pro, bundle, lang=requested_lang)
        apply_love_premium_validation(pro, bundle, lang)
    except Exception as exc:
        log.exception("[assembly] fatal: %s", exc)
        pro.setdefault("_meta", {})["assembly_error"] = str(exc)

    pro.setdefault("_meta", {})
    pro["_meta"].update({
        "model": model,
        "lang": lang,
        "requested_lang": requested_lang,
        "assembly": _ASSEMBLY_VER,
        "sections": section_meta,
    })
    pg = tel.build_meta(
        fallback_used=not _assembly_depth_ok(pro),
        final_status="OK" if _assembly_depth_ok(pro) else "partial",
        validator_attempts=0,
        cache_hit=False,
        openai_skipped=False,
    )
    from vedic.love_reality.premium_polish import _attach_polish_telemetry

    _attach_polish_telemetry(pro["_meta"], pg)
    return pro
