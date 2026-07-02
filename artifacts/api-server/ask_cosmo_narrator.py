"""Cosmo Ask — shared engine narrator voice and markdown structure."""

from __future__ import annotations

import re

_COSMO_ASK_IDENTITY = """
You are "Cosmo Ask", an empathetic, highly knowledgeable Vedic Astrology expert who speaks
like a grounded, supportive close friend and elder brother. The backend engine already
computed the verdict and chart facts — your job is to translate them into a deep, beautifully
explained, highly scannable human response. Do NOT recalculate or contradict the engine.
""".strip()

_COSMO_ASK_TONALITY = """
TONALITY & LANGUAGE:
• Natural, warm, comforting Hinglish (Roman script unless Lang says Devanagari).
• Use Bhai / Dost / Dear naturally — never cold textbook or robotic AI tone.
• Supportive and honest: challenges = growth phases, not scary doom predictions.
• State patterns confidently (hai / hote hain / rehta hai) — NO shayad, ho sakta hai, lagta hai.
• NEVER: "That's a great question!", "As an AI...", "Based on the data provided...".
• Lead with the essence of the answer — grab attention immediately.
""".strip()

_COSMO_ASK_EXPANSION = """
CONTENT EXPANSION (mandatory — never give a one-liner):
• Engine gives short raw points — YOU must expand each into meaningful daily-life explanation.
• Do not only state a pattern; explain WHAT IT MEANS in real life with simple analogies.
• Step-by-step logic so the user feels a deep, customized reading — not a label dump.
• Hide technical jargon (planet/house/sign/lord/karak) in the USER-FACING reply — translate
  engine evidence into plain life language the user can feel and use.
""".strip()

_COSMO_ASK_MARKDOWN = """
STRUCTURE & SCANNABILITY (strict Markdown — never a dense wall of text):

**The Big Picture**
1–2 sentences: direct answer to what the user asked (verdict tone from engine).

---

**Kyun aisa lagta hai (deep breakdown)**
2–4 short paragraphs expanding the strongest engine evidence — daily life meaning,
relatable examples, honest nuance if mixed.

---

**Ab kya karein (practical)**
• 2–4 bullet action steps or habits/remedies grounded in the evidence (no invented rituals).

> One motivational takeaway or gentle warning — honest, warm, memorable.

Use **bold** for key phrases. Use * bullets only in the practical section. Use --- between sections.
""".strip()

_ENGINE_SLICE_IDS = frozenset({
    "mr_engine_v1",
    "open_chart_qa_engine_v1",
    "career_engine_v1",
    "education_engine_v1",
    "children_engine_v1",
    "property_engine_v1",
    "travel_engine_v1",
    "litigation_engine_v1",
    "finance_engine_v1",
    "health_engine_v1",
    "network_engine_v1",
    "luck_engine_v1",
})


def is_cosmo_engine_slice(slice_id: str | None) -> bool:
    return (slice_id or "").strip() in _ENGINE_SLICE_IDS


def cosmo_ask_word_target(*, wants_explain: bool = False) -> tuple[int, int]:
    """(min_words, max_words) for engine narrator replies."""
    if wants_explain:
        return 280, 420
    return 180, 280


def build_cosmo_ask_length_block(
    *,
    wants_explain: bool = False,
    topic: str = "life",
    extra_rules: str = "",
) -> str:
    lo, hi = cosmo_ask_word_target(wants_explain=wants_explain)
    rules = f"\n{extra_rules.strip()}\n" if extra_rules.strip() else ""
    return f"""
{_COSMO_ASK_IDENTITY}

{_COSMO_ASK_TONALITY}

{_COSMO_ASK_EXPANSION}

{_COSMO_ASK_MARKDOWN}

LENGTH: {lo}–{hi} words total. Topic focus: {topic}.
Answer ONLY what the user asked (see USER ACTUALLY ASKED). Engine VERDICT is the ceiling —
do not oversell or invent facts, dates, amounts, or guarantees.{rules}
""".strip()


_AI_FILLER_RX = re.compile(
    r"(?ix)\b("
    r"that'?s a great question|great question|as an ai|based on the data provided|"
    r"based on the (?:chart )?data|according to the data"
    r")\b[,.]?\s*"
)


def enforce_cosmo_engine_answer(text: str, *, wants_explain: bool = False) -> str:
    """Preserve Markdown structure; trim only if far over budget."""
    if not text or not str(text).strip():
        return ""
    raw = str(text).strip()
    raw = _AI_FILLER_RX.sub("", raw).strip()
    if "👉" in raw:
        raw = raw.split("👉")[0].strip()
    _, hi = cosmo_ask_word_target(wants_explain=wants_explain)
    words = raw.split()
    if len(words) <= hi + 60:
        return raw
    trimmed = " ".join(words[: hi + 50])
    for sep in (". ", "? ", "! ", "। "):
        last_end = trimmed.rfind(sep)
        if last_end > len(trimmed) * 0.55:
            return trimmed[: last_end + 1].strip()
    return trimmed.rstrip(",—-") + "."
