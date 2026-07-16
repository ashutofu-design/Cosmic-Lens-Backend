"""Fast path for non-personal astrology knowledge (theory / kisi-ka lagna advice).

Named-lagna gemstone Qs answer INSTANTLY from classical rules (no LLM wait).
That avoids mobile soft-fail: "Kshama karein, abhi jawab dene mein dikkat…".
"""
from __future__ import annotations

import os
import re
from typing import Any

from ask_question_normalize import normalize_ask_typos

_PERSONAL_RX = re.compile(
    r"(?ix)\b(mera|meri|mere|mujhe|mujhko|main|mai|hum|ham|hamari|hamara|"
    r"my\s+(?:chart|kundli|lagna)|i\s+am)\b|(?:(?<![a-z])me(?![a-z]))"
)

_KNOWLEDGE_RX = re.compile(
    r"(?ix)\b("
    r"gemstone|gem\s*stone|ratna|ratn|stone|mani|pukhraj|neelam|manik|moti|"
    r"remedy|upay|upaay|mantra|dharan|pehne|pehen|"
    r"kya\s+(?:hai|he|hota|hoti)|matlab|meaning|explain|samjha|"
    r"kisi\s+ka|kisi\s+ke|kisi\s+ki|agar\s+kisi|if\s+someone"
    r")\b"
)

_SIGN_TOKEN_RX = re.compile(
    r"(?ix)\b("
    r"leo|aries|taurus|gemini|cancer|virgo|libra|scorpio|"
    r"sagittarius|capricorn|aquarius|pisces|"
    r"mesh|vrishabh|mithun|kark|singh|simha|kanya|tula|"
    r"vrishchik|dhanu|makar|kumbh|meen"
    r")\b"
)

_EXPLICIT_LAGNA_RX = re.compile(
    r"(?ix)\b("
    r"leo|aries|taurus|gemini|cancer|virgo|libra|scorpio|"
    r"sagittarius|capricorn|aquarius|pisces|"
    r"mesh|vrishabh|mithun|kark|singh|simha|kanya|tula|"
    r"vrishchik|dhanu|makar|kumbh|meen"
    r")\s+(?:lagna|ascendant)\b"
)

_GEM_HINT_RX = re.compile(
    r"(?ix)\b(gemstone|gem\s*stone|ratna|ratn|stone|mani|dharan|pehne|pehen|"
    r"pukhraj|neelam|manik|moti|remedy|upay)\b"
)

# Classical lagna-lord → primary gemstone (popular Jyotish consensus).
_LAGNA_PRIMARY_GEM: dict[str, tuple[str, str]] = {
    "aries": ("Moonga (Red Coral)", "Mangal"),
    "mesh": ("Moonga (Red Coral)", "Mangal"),
    "taurus": ("Heera / Opal (Diamond family)", "Shukra"),
    "vrishabh": ("Heera / Opal (Diamond family)", "Shukra"),
    "gemini": ("Panna (Emerald)", "Budh"),
    "mithun": ("Panna (Emerald)", "Budh"),
    "cancer": ("Moti (Pearl)", "Chandra"),
    "kark": ("Moti (Pearl)", "Chandra"),
    "leo": ("Manik (Ruby)", "Surya"),
    "singh": ("Manik (Ruby)", "Surya"),
    "simha": ("Manik (Ruby)", "Surya"),
    "virgo": ("Panna (Emerald)", "Budh"),
    "kanya": ("Panna (Emerald)", "Budh"),
    "libra": ("Heera / Opal (Diamond family)", "Shukra"),
    "tula": ("Heera / Opal (Diamond family)", "Shukra"),
    "scorpio": ("Moonga (Red Coral)", "Mangal"),
    "vrishchik": ("Moonga (Red Coral)", "Mangal"),
    "sagittarius": ("Pukhraj (Yellow Sapphire)", "Guru"),
    "dhanu": ("Pukhraj (Yellow Sapphire)", "Guru"),
    "capricorn": ("Neelam (Blue Sapphire) — trial pehle", "Shani"),
    "makar": ("Neelam (Blue Sapphire) — trial pehle", "Shani"),
    "aquarius": ("Neelam (Blue Sapphire) — trial pehle", "Shani"),
    "kumbh": ("Neelam (Blue Sapphire) — trial pehle", "Shani"),
    "pisces": ("Pukhraj (Yellow Sapphire)", "Guru"),
    "meen": ("Pukhraj (Yellow Sapphire)", "Guru"),
}


def _parse_named_lagna(q: str) -> str | None:
    """Prefer explicit 'leo lagna'; else sign + gem/dharan in same question."""
    m = _EXPLICIT_LAGNA_RX.search(q or "")
    if m:
        return (m.group(1) or "").strip().lower()
    if not _GEM_HINT_RX.search(q or ""):
        return None
    m2 = _SIGN_TOKEN_RX.search(q or "")
    if not m2:
        return None
    return (m2.group(1) or "").strip().lower()


def is_astrology_knowledge_fast_question(question: str) -> bool:
    """Non-personal jyotish theory / kisi-ka lagna advice — skip heavy Ask pipeline."""
    q = normalize_ask_typos((question or "").strip())
    if not q or len(q) > 280:
        return False
    if not _KNOWLEDGE_RX.search(q):
        return False
    # Own-chart personal asks stay on full D1/D9 path.
    if _PERSONAL_RX.search(q) and not re.search(
        r"(?ix)\b(kisi\s+ka|kisi\s+ke|kisi\s+ki|agar\s+kisi)\b", q
    ):
        return False
    if _parse_named_lagna(q):
        return True
    if re.search(r"(?ix)\b(kisi\s+ka|kisi\s+ke|kisi\s+ki|agar\s+kisi)\b", q):
        return True
    if re.search(r"(?ix)\b(gemstone|ratna|remedy|upay)\b", q) and not _PERSONAL_RX.search(q):
        return True
    return False


def _classical_lagna_gem_answer(question: str, lang: str = "hn") -> dict | None:
    q = normalize_ask_typos((question or "").strip())
    key = _parse_named_lagna(q)
    if not key or key not in _LAGNA_PRIMARY_GEM:
        return None
    gem, lord = _LAGNA_PRIMARY_GEM[key]
    lagna_label = key[:1].upper() + key[1:]
    if lang == "en":
        text = (
            f"For {lagna_label} lagna, the classical primary gemstone is {gem} "
            f"(lagna lord {lord}). Wear only after proper purification and, "
            f"for strong stones like Neelam, a short trial. That person's full chart "
            f"(dasha / afflictions) can change the final choice."
        )
    else:
        text = (
            f"{lagna_label} lagna ke liye classical primary gemstone {gem} maana jata hai "
            f"(lagna lord {lord}). Pehle shuddhi / sahi metal-finger se dharan karein; "
            f"Neelam jaise strong stone pe pehle short trial. Us vyakti ki poori kundli "
            f"(dasha / peeda) dekh ke final choice badal sakti hai — yeh general rule hai."
        )
    return {
        "text": text,
        "topic": "remedy",
        "question_type": "STATIC",
        "confidence": 0.92,
        "source": "knowledge_fast_classical",
        "engine_tag": "ans-cosmo",
        "follow_ups": [
            "Mere chart ke hisaab se kaunsa ratn better hai?",
            "Neelam kab avoid karna chahiye?",
        ],
    }


_KNOWLEDGE_LLM_SYSTEM = (
    "You are a natural Vedic astrologer answering general astrology questions.\n"
    "Read the user's language (English, Hindi, or Hinglish) and reply in the same language.\n"
    "Give one short simple paragraph that directly answers the question.\n"
    "Tone: professional consultation — respectful aap. "
    "Never address the user as bhai, yaar, dost, bro, buddy, or beta.\n"
    "Do not invent this user's personal chart. No greetings, no lists, no headers."
)


def _llm_knowledge_answer(question: str, lang: str = "hn") -> str | None:
    """Short paragraph knowledge answer; language follows the question."""
    del lang  # language comes from the question text, not app locale
    try:
        from openai_helper import _get_client
    except Exception:
        return None
    client = _get_client()
    if client is None:
        return None
    model = os.environ.get(
        "ASK_KNOWLEDGE_FAST_MODEL",
        os.environ.get("OPENAI_MODEL", "gpt-4.1-mini"),
    )
    try:
        kwargs: dict[str, Any] = {
            "model": model,
            "messages": [
                {"role": "system", "content": _KNOWLEDGE_LLM_SYSTEM},
                {"role": "user", "content": (question or "")[:500]},
            ],
            "temperature": 0.3,
        }
        try:
            resp = client.chat.completions.create(
                **kwargs,
                max_completion_tokens=220,
                timeout=12,
            )
        except TypeError:
            resp = client.chat.completions.create(**kwargs, max_tokens=220)
        text = ((resp.choices[0].message.content or "") if resp.choices else "").strip()
        return text or None
    except Exception as exc:
        print(f"[knowledge_fast] LLM failed: {exc}", flush=True)
        return None


def try_astrology_knowledge_fast_answer(
    question: str,
    *,
    lang: str = "hn",
    force: bool = False,
) -> dict | None:
    """Knowledge answers for theory / named-lagna gem Qs.

    Phase 2: call only when Understand says branch=knowledge.
    Pass force=True to skip the legacy regex gate (Understand is authority).
    """
    q = normalize_ask_typos((question or "").strip())
    if not force and not is_astrology_knowledge_fast_question(q):
        return None

    # 1) Instant classical (Leo → Manik) — this is the product path.
    classical = _classical_lagna_gem_answer(q, lang=lang)
    if classical:
        return classical

    # 2) LLM short paragraph (default ON; set ASK_KNOWLEDGE_FAST_LLM=0 to disable).
    use_llm = (os.environ.get("ASK_KNOWLEDGE_FAST_LLM") or "1").strip().lower() not in (
        "0",
        "off",
        "false",
        "no",
    )
    if use_llm:
        llm_text = _llm_knowledge_answer(q, lang=lang)
        if llm_text:
            return {
                "text": llm_text,
                "topic": "remedy",
                "question_type": "STATIC",
                "confidence": 0.85,
                "source": "knowledge_fast_llm",
                "engine_tag": "ans-cosmo",
                "follow_ups": [],
            }

    # 3) Still answer — never soft-fail.
    return {
        "text": (
            "Yeh general jyotish sawaal hai. Seedha classical rule: sawal ke hisaab se "
            "house/planet ka role short mein bataya jaata hai; personal chart alag check hota hai."
            if lang != "en"
            else "This is a general Jyotish question. Classical rules answer the topic briefly; "
            "a personal chart reading is separate."
        ),
        "topic": "remedy",
        "question_type": "STATIC",
        "confidence": 0.7,
        "source": "knowledge_fast_fallback",
        "engine_tag": "ans-cosmo",
        "follow_ups": [],
    }
