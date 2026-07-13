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

_COSMO_ASK_MARKDOWN_BATCH = """
STRUCTURE (batch test — short direct answer only):
• 2–4 sentences total: direct stance (haan / nahi / mixed) + 1–2 plain reasons from engine evidence.
• NO section headers, NO "---" dividers, NO bullet lists.
• Plain paragraph(s) only. No planet/house/sign jargon in the reply.
""".strip()

_COSMO_HEALTH_ADAPTIVE = """
1. Pehle user ka sawal samjho — kya puch raha hai aur kitna detail chahiye.
2. HEALTH_ENGINE_EXECUTION_JSON POORA padho — d1/d9 planets, health_houses, house_lords,
   afflictions, dimensions, vargottama. Sirf isi JSON se facts lo; khud se mat banao.
3. Sawal ke hisaab se JSON me relevant ghar/planet dhundho (6th=disease, 8th=chronic, 12th=hospital)
   aur jawab me wahi planet + ghar/sign/affliction cite karo — MANDATORY.
   Example: "Moon 6th ghar me weak hai, isliye immunity kamzor lag sakti hai."
   Bina planet+ghar cite kiye health claim mat likho.
4. Sirf pucha hua jawab do — extra filler mat do. Har claim ke saath chart proof ho. Paisa/kharcha/career tabhi likho jab user ne woh pucha ho.
5. Signal nahi ho to seedha bolo tendency zyada nahi; generic advice bina proof ke mat do.
6. "Kya kya disease/bimari" = vulnerability zones (6th/8th/12th + planet proof) — diabetes/cancer
   jaise specific naam mat likho.
7. Proof jawab ke beech natural — alag "(Proof:...)" line mat likho.
8. Natural Hinglish astrologer tone.
""".strip()

_COSMO_HEALTH_OVERVIEW = """
1. User ne general health overview maanga hai — soft paragraph do, technical breakdown nahi.
2. HEALTH_ENGINE_EXECUTION_JSON padho sirf overall tendency samajhne ke liye — user ko planet+ghar list mat do.
3. Jawab me overall health foundation, stress/energy/digestion themes (1-2), healthy routine/sleep/exercise tip do.
4. NO vitality score /100, NO Mars H1 / Rahu H8 jaisi listing, NO remedies/upay, NO specific disease naam.
5. End me likho: yeh long-term health tendencies hain, medical diagnosis nahi.
6. Natural warm Hinglish — 4-6 sentences, short_paragraph style.
""".strip()

_COSMO_ASK_MARKDOWN = """
STRUCTURE (natural paragraph — never use section headers or template labels):
• Open with a direct answer to what the user asked (verdict tone from engine).
• Then 2–4 short paragraphs: expand strongest engine evidence in daily-life language.
• End with 1–2 practical habits or next steps woven into prose (no bullet list required).
• NO section headers, NO "---" dividers, NO "Big Picture / Kyun / Ab kya karein" labels.
• Hide planet/house/sign jargon — plain Hinglish the user can feel and use.
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


def cosmo_ask_word_target(*, wants_explain: bool = False, concise: bool = False) -> tuple[int, int]:
    """(min_words, max_words) for engine narrator replies."""
    if concise:
        return 35, 90
    if wants_explain:
        return 280, 420
    return 180, 280


def build_health_ask_length_block(
    *,
    wants_explain: bool = False,
    extra_rules: str = "",
    overview_mode: bool = False,
) -> str:
    rules = f"\n{extra_rules.strip()}\n" if extra_rules.strip() else ""
    adaptive = _COSMO_HEALTH_OVERVIEW if overview_mode else _COSMO_HEALTH_ADAPTIVE
    return f"""
You are Cosmo Ask — Vedic health chart par natural jawab dete ho.

{adaptive}
{rules}
""".strip()


def build_cosmo_ask_length_block(
    *,
    wants_explain: bool = False,
    topic: str = "life",
    extra_rules: str = "",
    concise: bool = False,
) -> str:
    lo, hi = cosmo_ask_word_target(wants_explain=wants_explain, concise=concise)
    rules = f"\n{extra_rules.strip()}\n" if extra_rules.strip() else ""
    expansion = "" if concise else f"\n\n{_COSMO_ASK_EXPANSION}"
    markdown = _COSMO_ASK_MARKDOWN_BATCH if concise else _COSMO_ASK_MARKDOWN
    return f"""
{_COSMO_ASK_IDENTITY}

{_COSMO_ASK_TONALITY}{expansion}

{markdown}

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

_COSMO_SECTION_HEADER_RX = re.compile(
    r"(?im)^\*\*(?:The Big Picture|Kyun aisa(?:\s+lagta\s+hai)?(?:\s*\(deep breakdown\))?|"
    r"Ab kya karein(?:\s*\(practical\))?|मुख्य बात|क्यों ऐसा लगता है|अब क्या करें)\*\*\s*\n?"
)


def enforce_cosmo_engine_answer(
    text: str,
    *,
    wants_explain: bool = False,
    concise: bool = False,
) -> str:
    """Preserve Markdown structure; trim only if far over budget."""
    if not text or not str(text).strip():
        return ""
    raw = str(text).strip()
    raw = _AI_FILLER_RX.sub("", raw).strip()
    if "👉" in raw:
        raw = raw.split("👉")[0].strip()
    raw = _COSMO_SECTION_HEADER_RX.sub("", raw)
    raw = re.sub(r"\n*---+\n*", "\n\n", raw).strip()
    if concise:
        raw = re.sub(r"\*\*[^*]+\*\*", "", raw)
        raw = re.sub(r"\n*---+\n*", " ", raw)
        raw = re.sub(r"^[*•]\s+", "", raw, flags=re.M)
        raw = re.sub(r"\s{2,}", " ", raw).strip()
    _, hi = cosmo_ask_word_target(wants_explain=wants_explain, concise=concise)
    words = raw.split()
    if len(words) <= hi + 60:
        return raw
    trimmed = " ".join(words[: hi + 50])
    for sep in (". ", "? ", "! ", "। "):
        last_end = trimmed.rfind(sep)
        if last_end > len(trimmed) * 0.55:
            return trimmed[: last_end + 1].strip()
    return trimmed.rstrip(",—-") + "."
