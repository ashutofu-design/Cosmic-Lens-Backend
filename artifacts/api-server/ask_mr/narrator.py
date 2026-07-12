"""MR engine narrator — Cosmo Ask voice: expand engine facts into deep Hinglish markdown."""

from __future__ import annotations

import re

from ask_cosmo_narrator import build_cosmo_ask_length_block, build_health_ask_length_block
from .types import EngineResult
from ask_career.job_registry import JOB_ENGINE_ARCHETYPES


def _is_health_archetype(archetype: str) -> bool:
    arch = (archetype or "").strip().lower()
    if not arch or arch.startswith("refuse_") or arch == "crisis_redirect":
        return False
    try:
        from ask_health.health_registry import HEALTH_ARCHETYPES

        return arch in HEALTH_ARCHETYPES
    except Exception:
        return arch in {
            "overall_vitality", "chronic_tendency", "mental_stress", "surgery_risk_tone",
            "preventive_risk", "recovery_capacity", "accident_risk", "parent_health",
            "addiction_support", "reproductive_support", "general_health",
            "digestive_health", "heart_blood_pressure", "cardio_health", "nervous_health",
            "musculoskeletal_health", "skin_health", "endocrine_health", "respiratory_health",
            "immune_health",
        }

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


def _archetype_extra_rules(
    *,
    archetype: str,
    is_partner_nature: bool,
    question_focus: str,
    open_chart_qa: bool,
) -> str:
    arch = (archetype or "").strip().lower()
    qf = (question_focus or "").strip().lower()
    rules: list[str] = []

    if is_partner_nature or arch == "partner_nature":
        rules.append(
            "Partner/spouse nature Q — expand 7H vibe, emotional tone, mindset, presence "
            "from evidence into warm trait portrait. No planet/house/sign words in reply."
        )
        if qf == "partnership_attachment":
            rules.append(
                "Focus: emotional attachment depth — bond strengths first, one caveat, "
                "practical patience/communication in bullets."
            )
    elif arch == "open_chart_qa" or open_chart_qa:
        rules.append(
            "Open chart Q — use ONLY LOCKED CHART FACTS in the engine block. "
            "Stay on TOPIC_LOCK — no invented placements, dates, or unrelated drift. "
            "Native-self focus when they asked about themselves."
        )
    elif _is_health_archetype(arch):
        rules.append(
            "Health Q — sawal identify karo, JSON facts padho, usi ke hisaab se natural jawab do."
        )
    elif arch in (
        "income_source", "savings_capacity", "save_vs_spend", "expense_pattern",
        "spending_personality", "financial_discipline", "investment_risk",
        "debt_loan", "property_money", "sudden_gain_loss", "business_profit",
        "loss_reasons", "wealth_potential", "dhana_yoga", "general_finance",
    ):
        rules.append(
            "Finance Q — direct money answer first. No lottery/satta/stock tips. "
            "Do not invent amounts or dates."
        )
    elif arch == "commitment":
        rules.append(
            "Relationship Q — direct answer first, then reasons, then practical line. "
            "No planet/house jargon."
        )
    elif arch in JOB_ENGINE_ARCHETYPES or arch.startswith("career") or arch in (
        "job_vs_business", "sector_fit", "creativity_innovation", "career_milestones",
        "govt_job", "vocational_trade", "entrepreneurship", "income_wealth",
        "foreign_career", "workplace_relations", "fame_recognition", "education_career",
        "career_obstacles", "retirement_legacy", "work_environment", "career_traits",
        "strengths_skills",
    ):
        rules.append(
            "Career Q — answer the EXACT job/business/milestone asked. "
            "Lead with clear haan/nahi or path pick per VERDICT, then explain why in daily work terms."
        )
    elif arch == "job_vs_business":
        rules.append(
            "Job vs business — Big Picture = clear JOB or BUSINESS pick per VERDICT "
            "(include ~% split if engine gives it). Do NOT say pehle job phir business unless Hybrid."
        )

    return "\n".join(rules)


def build_mr_engine_narrator_system_prompt(
    *,
    chart_text: str,
    reply_lang: str = "hn",
    wants_explain: bool = False,
    archetype: str = "",
    word_budget: int = 55,
    is_partner_nature: bool = False,
    question_focus: str = "",
    user_intent: str = "",
    open_chart_qa: bool = False,
    concise: bool = False,
) -> str:
    """Cosmo Ask narrator — expand engine facts into deep markdown Hinglish."""
    rl = (reply_lang or "hn").strip().lower()
    if rl not in _NARRATOR_LANG:
        rl = "hn"
    arch = (archetype or "").strip().lower()

    topic_hint = (
        "commitment"
        if arch == "commitment"
        else (
        "health"
        if _is_health_archetype(arch)
        else (
            "finance"
            if arch in (
                "income_source", "savings_capacity", "save_vs_spend", "expense_pattern",
                "spending_personality", "financial_discipline", "investment_risk",
                "debt_loan", "property_money", "sudden_gain_loss", "business_profit",
                "loss_reasons", "wealth_potential", "dhana_yoga", "general_finance",
            )
            else (
                "career"
                if arch and arch not in ("partner_nature", "general_mr", "open_chart_qa")
                and not arch.startswith("breakup")
                else (arch.replace("_", " ") if arch else "marriage/relationship")
            )
        )
        )
    )

    extras = _archetype_extra_rules(
        archetype=arch,
        is_partner_nature=is_partner_nature,
        question_focus=question_focus,
        open_chart_qa=open_chart_qa,
    )
    if (is_partner_nature or arch == "partner_nature") and question_focus != "partnership_attachment":
        extras = (
            "IF user asked a SPECIFIC trait (gussa, expressive, dominant, respect) — "
            "open Big Picture with clear haan/nahi from matching evidence.\n" + extras
        )
    if arch == "love_vs_arranged" or "arrange" in arch:
        extras += (
            "\nIf engine gives love vs arranged % split — LEAD Big Picture with those numbers only."
        )

    if _is_health_archetype(arch):
        length_block = build_health_ask_length_block(
            wants_explain=wants_explain,
            extra_rules=extras,
        )
        engine_lock = (
            "HEALTH JSON: HEALTH_ENGINE_EXECUTION_JSON me jo engine execution data hai woh sahi hai — "
            "unhi se sawal ka jawab banao."
        )
    else:
        try:
            length_block = build_cosmo_ask_length_block(
                wants_explain=wants_explain,
                topic=topic_hint,
                extra_rules=extras,
                concise=concise,
            )
        except TypeError:
            length_block = build_cosmo_ask_length_block(
                wants_explain=wants_explain,
                topic=topic_hint,
                extra_rules=extras,
            )
        engine_lock = (
            "ENGINE LOCK: Facts below are final — narrate and EXPAND them; never recalculate or contradict VERDICT.\n"
            "Do NOT add new planets/houses/dasha reasons beyond ENGINE FACTS.\n"
            "If user asked for % / kitna / ratio, lead Big Picture with engine numbers only — do not invent figures.\n"
            "BANNED section labels: Seedha jawab, Conclusion, निष्कर्ष — use the Markdown section headers given."
        )

    intent_block = ""
    if (user_intent or "").strip():
        intent_block = (
            "\nUSER ACTUALLY ASKED (answer THIS exact thing first, nothing off-track): "
            f"{user_intent.strip()}\n"
        )

    return f"""{_NARRATOR_LANG[rl]}
{intent_block}
{engine_lock}

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
