"""MR engine narrator — thin LLM prompt (facts only, no chart calculation)."""

from __future__ import annotations

from .types import EngineResult

_NARRATOR_LANG = {
    "hn": "Reply in natural Hinglish (Roman script). No Devanagari. No planet/house jargon.",
    "hi": "Reply in Hindi (Devanagari). No planet/house jargon.",
    "en": "Reply in simple English. No jargon.",
}


def build_mr_narrator_user_lang_block(code: str) -> str:
    """Minimal language lock for MR narrator (~80 chars vs ~350)."""
    c = (code or "hn").strip().lower()
    if c == "hi":
        return "Lang: Hindi (Devanagari).\n\n"
    if c == "en":
        return "Lang: English.\n\n"
    return "Lang: Hinglish (Roman).\n\n"


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
            "MANDATORY: exactly 3 paragraphs separated by ONE blank line (\\n\\n).\n"
            "Total 90–120 words. Wise friend Hinglish. No planet/house/sign/lord/karak words.\n\n"
            "PARAGRAPH 1 (~30–40 words): ONLY 7th house sign evidence → social/chatty/curious vibe.\n"
            "PARAGRAPH 2 (~30–40 words): ONLY 7th lord + planets-in-7th evidence → emotional tone + private/thoughtful mindset.\n"
            "PARAGRAPH 3 (~30–40 words): ONLY partner-karak evidence → warm presence / attraction in relationship.\n\n"
            "Do NOT write one long essay. Do NOT add 'unique vibes' or facts outside EVIDENCE.\n"
            "USE: ho sakta hai, lagta hai, shayad. NEVER: pakka, 100%, definitely."
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

    return f"""You are Cosmo — warm wise friend. NOT calculating charts.

{_NARRATOR_LANG[rl]}

RULES: ENGINE FACTS below are final. Narrate VERDICT + EVIDENCE only in plain language.
Do NOT add planets/houses/D9/dasha or new reasons. Do NOT contradict VERDICT.
Use ho sakta hai / lagta hai / shayad — never pakka or 100%. No bullets or [Checked].

Topic: {topic_hint}
{length_block}

ENGINE FACTS:
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
