"""MR engine narrator — thin LLM prompt (facts only, no chart calculation)."""

from __future__ import annotations

import re

from .types import EngineResult

_MR_CONFIDENT_TONE = """
TONE — confident chart reading (engine already decided; do NOT sound doubtful):
• State patterns directly: hai / hote hain / rehta hai / rehti hai / hota hai / hoti hai / dikhta hai.
• Example: "partner chatty hote hain", "rishta intense rehta hai", "love side zyada hai".
• BANNED hedging: shayad, ho sakta hai, ho sakti hai, ho sakte hain, lagta hai, lagti hai,
  lagte hain, lag sakta hai, mumkin hai, maybe, perhaps, might, possibly, could be.
• NEVER: pakka hoga, 100%, guarantee, fixed fate, milega hi, yahi hoga.
""".strip()

_NARRATOR_LANG = {
    "hn": "Reply in natural Hinglish (Roman script). No Devanagari. No planet/house jargon.",
    "hi": "Reply in Hindi (Devanagari). No planet/house jargon.",
    "en": "Reply in simple English. No jargon.",
}

_MR_HEDGE_RX: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"\bshayad\b", re.I), ""),
    (re.compile(r"\bperhaps\b", re.I), ""),
    (re.compile(r"\bmaybe\b", re.I), ""),
    (re.compile(r"\bmight\b", re.I), ""),
    (re.compile(r"\bpossibly\b", re.I), ""),
    (re.compile(r"\bcould be\b", re.I), "hai"),
    (re.compile(r"\bmumkin hai\b", re.I), ""),
    (re.compile(r"\bho sakte hain\b", re.I), "hain"),
    (re.compile(r"\bho sakti hai\b", re.I), "hai"),
    (re.compile(r"\bho sakta hai\b", re.I), "hai"),
    (re.compile(r"\blag sakte hain\b", re.I), "hain"),
    (re.compile(r"\blag sakti hai\b", re.I), "hai"),
    (re.compile(r"\blag sakta hai\b", re.I), "hai"),
    (re.compile(r"\blagte hain\b", re.I), "hain"),
    (re.compile(r"\blagti hai\b", re.I), "hai"),
    (re.compile(r"\blagta hai\b", re.I), "hai"),
    (re.compile(r"\bfeel hoti hai\b", re.I), "hoti hai"),
    (re.compile(r"\bfeel hota hai\b", re.I), "hota hai"),
    (re.compile(r"\bfeel hote hain\b", re.I), "hote hain"),
    (re.compile(r"\bunique lagta hai\b", re.I), "unique hai"),
    (re.compile(r"\bdepend karega\b", re.I), "mix rehta hai"),
    (re.compile(r"\bdepend karti hai\b", re.I), "mix rehti hai"),
    (re.compile(r"\s+,", re.I), ","),
]


def polish_mr_confident_tone(text: str) -> str:
    """Strip doubt-hedging from MR narrator output (all archetypes)."""
    if not text or not str(text).strip():
        return ""
    blocks = str(text).split("\n\n")
    out_blocks: list[str] = []
    for block in blocks:
        line = block.strip()
        if not line:
            continue
        for rx, repl in _MR_HEDGE_RX:
            line = rx.sub(repl, line)
        # No big dashes — em/en dash becomes a comma (user pref).
        line = re.sub(r"\s*[\u2014\u2013]\s*", ", ", line)
        line = re.sub(r",\s*,", ",", line)
        line = re.sub(r"\s{2,}", " ", line).strip()
        line = re.sub(r"\s+([,.;])", r"\1", line)
        line = re.sub(r",\s*([.?!])", r"\1", line)
        out_blocks.append(line)
    return "\n\n".join(out_blocks).strip()


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
    user_intent: str = "",
    open_chart_qa: bool = False,
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
            "IF the user asked about a SPECIFIC trait (gussa/temper, loyalty, expressive, "
            "dominant, respect, etc.) — look for a matching EVIDENCE line (e.g. 'Temper signal') "
            "or an 'Answer ... directly' HINT — then START paragraph 1 with ONE clear sentence "
            "that directly answers that exact question (clear haan/nahi), and continue.\n\n"
            "PARAGRAPH 1 (~30–40 words): direct trait answer (if asked) + 7th house sign social/chatty/curious vibe.\n"
            "PARAGRAPH 2 (~30–40 words): ONLY 7th lord + planets-in-7th evidence → emotional tone + private/thoughtful mindset.\n"
            "PARAGRAPH 3 (~30–40 words): ONLY partner-karak evidence → warm presence / attraction in relationship.\n\n"
            "Do NOT write one long essay. Do NOT add 'unique vibes' or facts outside EVIDENCE.\n"
            f"{_MR_CONFIDENT_TONE}"
        )
    elif archetype == "job_vs_business":
        length_block = (
            f"Write 2–3 short sentences (~{min(wb + 15, 90)} words max).\n"
            "Read USER ACTUALLY ASKED — answer job vs business (or business vs job) directly.\n"
            "Sentence 1 = clear pick JOB or BUSINESS per VERDICT (include ~% split if given).\n"
            "If VERDICT says Employment path stronger → job/naukri suits abhi — "
            "do NOT say 'pehle job phir business' unless VERDICT says Hybrid.\n"
            "Sentence 2–3 = WHY from ENGINE EVIDENCE in plain words "
            "(career mode, structure, independence, discipline — pick 1–2 reasons).\n"
            "End feeling: user ko samajh aaye poori kundli reading se yeh path kyun better hai.\n"
            "BANNED labels: 'Seedha jawab:', 'Conclusion:', 'निष्कर्ष:' — natural prose only.\n"
            f"{_MR_CONFIDENT_TONE}"
        )
    elif open_chart_qa:
        _ow = min(wb + 30, 130) if wants_explain else max(wb, 60)
        length_block = (
            f"Write 2–3 short sentences (~{_ow} words).\n"
            "This is an OPEN question with NO fixed engine verdict. Read the D1 RELATIONSHIP "
            "CHART facts below, pick ONLY the factors relevant to the user's exact question "
            "(see USER ACTUALLY ASKED), and answer THAT question directly: clear stance first, "
            "then 1–2 plain reasons from those factors. Do NOT list every factor and do NOT give "
            "a generic marriage summary — stay on the exact thing asked.\n"
            f"{_MR_CONFIDENT_TONE}"
        )
    elif wants_explain:
        length_block = (
            f"Write 3–5 short sentences (~{min(wb + 35, 130)} words).\n"
            "Explain the engine verdict using 3–5 evidence lines below — "
            "each in plain life language (no jargon).\n"
            f"{_MR_CONFIDENT_TONE}"
        )
    else:
        length_block = (
            f"Write 2 short sentences (~{wb} words max).\n"
            "Sentence 1 = engine verdict stated clearly (not hedged).\n"
            "Sentence 2 = the SINGLE strongest reason. Pick ONLY the most "
            "decisive EVIDENCE line and explain that one in plain life language. "
            "Strength ranking: deep-chart / D9 / Navamsha / conjunction "
            "confirmations are strongest, then single planet-lord placements, "
            "then general notes. Give the user ONE clear 'why' — do NOT list "
            "multiple reasons or stack evidence.\n"
            "BANNED labels: 'Seedha jawab:', 'Conclusion:', 'निष्कर्ष:' — natural prose only.\n"
            f"{_MR_CONFIDENT_TONE}"
        )

    topic_hint = (
        "career"
        if archetype and archetype not in ("partner_nature", "general_mr")
        and not archetype.startswith("breakup")
        else (archetype.replace("_", " ") if archetype else "marriage/relationship")
    )

    intent_block = ""
    if (user_intent or "").strip():
        intent_block = (
            "\nUSER ACTUALLY ASKED (answer THIS exact thing first, nothing off-track): "
            f"{user_intent.strip()}\n"
        )

    return f"""You are Cosmo — warm wise friend. NOT calculating charts.

{_NARRATOR_LANG[rl]}
{intent_block}
RULES: ENGINE FACTS below are final. Narrate VERDICT + EVIDENCE in plain language with confidence.
Match the answer to EXACTLY what the user asked — if they asked a specific thing
(percentage, yes/no, who, when-ish tilt), answer THAT directly first, then reason.
Do NOT add planets/houses/D9/dasha or new reasons. Do NOT contradict VERDICT.
Do NOT use section labels like Seedha jawab / Conclusion — write natural sentences only.
Do NOT hedge with shayad/ho sakta hai/lagta hai — state the pattern the engine found.
If the user asks for a percentage / number / "kitna" / ratio, LEAD with the
approx % split shown in ENGINE FACTS (e.g. "Love ~56%, arrange ~44%"), then one
short reason. Use ONLY the numbers given — do NOT invent your own figure.
No bullets or [Checked].

Topic: {topic_hint}
{length_block}

ENGINE FACTS:
{chart_text}"""


def render_template(result: EngineResult) -> str | None:
    """Return user-facing text when skip_llm is set; else None."""
    if not result.skip_llm or not (result.template_text or "").strip():
        return None
    text = result.template_text.strip()
    return polish_mr_confident_tone(text)


def build_manglik_template(result: EngineResult) -> str:
    is_yes = bool((result.checks or {}).get("is_manglik"))
    if is_yes:
        return (
            "Haan — chart mein manglik pattern hai. "
            "Gussa ya impulse ko sambhalna zaroori rehta hai, "
            "lekin yeh seedha barbaadi nahi hoti. "
            "Patience aur clear baat se rishta smooth rehta hai."
        )
    return (
        "Nahi — classic manglik position active nahi dikhti. "
        "Overall rishta baaki chart signals se decide hota hai."
    )
