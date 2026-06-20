"""MR engine narrator — thin LLM prompt (facts only, no chart calculation)."""

from __future__ import annotations

from .types import EngineResult

_NARRATOR_LANG = {
    "hn": "Reply entirely in natural Hinglish (Hindi + simple English mix).",
    "hi": "Reply entirely in Hindi (Devanagari).",
    "en": "Reply entirely in simple English.",
}


def build_mr_engine_narrator_system_prompt(
    *,
    chart_text: str,
    reply_lang: str = "hn",
    wants_explain: bool = False,
    archetype: str = "",
    word_budget: int = 55,
    is_partner_nature: bool = False,
) -> str:
    """Minimal system prompt: engine already computed the answer — LLM narrates only."""
    rl = (reply_lang or "hn").strip().lower()
    if rl not in _NARRATOR_LANG:
        rl = "hn"
    wb = max(25, min(int(word_budget or 55), 180))

    if is_partner_nature or archetype == "partner_nature":
        length_block = (
            "Write 3 flowing Hinglish paragraphs (~90–120 words total).\n"
            "Blend partner traits naturally — wise friend tone.\n"
            "NO step labels, NO bullets, NO boxes."
        )
    elif wants_explain:
        length_block = (
            f"Write 3–5 short sentences (~{min(wb + 35, 130)} words).\n"
            "Explain the engine verdict using 3–5 evidence lines below — "
            "each in plain life language (no jargon)."
        )
    else:
        length_block = (
            f"Write 2–3 short sentences (~{wb} words max).\n"
            "Line 1 = engine verdict in plain words.\n"
            "Line 2–3 = 1–2 reasons from evidence only (+ optional soft practical note)."
        )

    topic_hint = archetype.replace("_", " ") if archetype else "marriage/relationship"

    return f"""You are Cosmo — a warm, wise friend. You are NOT an astrologer calculating charts.

{_NARRATOR_LANG[rl]}

STRICT RULES (breaking any rule is wrong):
1. The ENGINE FACTS block below is the COMPLETE computed answer — already final.
2. Do NOT calculate, infer, or add planets, houses, signs, D9, dasha, or new reasons.
3. Do NOT contradict the engine VERDICT or invent facts missing from EVIDENCE.
4. Translate engine evidence into plain human language only.
5. Soft language: ho sakta hai, lagta hai, shayad, tendency — never pakka / 100% / definitely.
6. Hide technical terms in user text (no house numbers, no planet names, no D9).
7. NO bullets, NO 👉 Final, NO [Checked], NO "Based on your chart", NO essay.

Topic focus: {topic_hint}

{length_block}

ENGINE FACTS (use ONLY this block — nothing else exists):
{chart_text}"""


def render_template(result: EngineResult) -> str | None:
    """Return user-facing text when skip_llm is set; else None."""
    if not result.skip_llm or not (result.template_text or "").strip():
        return None
    return result.template_text.strip()


def build_manglik_template(result: EngineResult) -> str:
    is_yes = bool((result.checks or {}).get("is_manglik"))
    if is_yes:
        return (
            "Haan — aapke chart mein manglik pattern dikhta hai. "
            "Iska matlab gussa ya impulse ko sambhalna zaroori ho sakta hai, "
            "lekin yeh seedha barbaadi nahi hoti. "
            "Patience aur clear baat se rishta smooth ho sakta hai."
        )
    return (
        "Nahi — classic manglik position active nahi dikhti. "
        "Phir bhi overall rishta chart ke baaki signals se decide hota hai."
    )
