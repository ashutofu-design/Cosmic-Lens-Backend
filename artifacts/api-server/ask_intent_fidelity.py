"""Keep Ask intent aligned with the user's exact question — no hallucinated topics."""
from __future__ import annotations

import re
from typing import Any

# ── Question must mention these before LLM may route to a domain ───────────
_DOMAIN_ANCHOR_RX: dict[str, re.Pattern[str]] = {
    "marriage": re.compile(
        r"(?ix)\b(shaadi|shadi|marriage|vivah|rishta|sagai|engagement|"
        r"manglik|divorce|talak|breakup|patchup)\b"
    ),
    "love": re.compile(
        r"(?ix)\b(love|pyaar|prem|crush|boyfriend|girlfriend|bf|gf|"
        r"dating|flirt|one[\s-]?sided)\b"
    ),
    "career": re.compile(
        r"(?ix)\b(career|naukri|nokri|job|business|promotion|interview|"
        r"salary|boss|company|employment|youtuber|govt\s*job)\b"
    ),
    "finance": re.compile(
        r"(?ix)\b(paisa|paise|money|wealth|finance|income|saving|loan|"
        r"debt|invest|profit|loss|amir|crorepati)\b"
    ),
    "health": re.compile(
        r"(?ix)\b(health|sehat|tabiyat|swasth|illness|disease|bimari|"
        r"stress|anxiety|pain|dard|surgery)\b"
    ),
    "education": re.compile(
        r"(?ix)\b(padhai|study|exam|college|school|degree|neet|jee|"
        r"upsc|marks|rank|admission)\b"
    ),
    "children": re.compile(
        r"(?ix)\b(bachcha|bachche|child|children|pregnancy|conceive|"
        r"santaan|santan|beta|beti|progeny)\b"
    ),
    "property": re.compile(
        r"(?ix)\b(property|ghar|makaan|flat|plot|zameen|vastu|real\s*estate)\b"
    ),
    "travel": re.compile(
        r"(?ix)\b(visa|abroad|videsh|foreign|settle|immigration|yatra|travel)\b"
    ),
    "litigation": re.compile(
        r"(?ix)\b(court|case|mukadma|fir|bail|jail|lawyer|vakil|litigation|kanooni)\b"
    ),
}

_PARTNER_SUBJECT_RX = re.compile(
    r"(?ix)\b(partner|spouse|pati|patni|biwi|husband|wife|"
    r"jeevan\s*sathi|boyfriend|girlfriend|bf|gf|saas|sasur|"
    r"sasural|in[\s-]?law|in[\s-]?laws|family\s*wal|ghar\s*wal)\b"
)

_INLAW_RX = re.compile(
    r"(?ix)\b(saas|sasur|sasural|sasuraal|in[\s-]?law|in[\s-]?laws|"
    r"mother[\s-]?in[\s-]?law|father[\s-]?in[\s-]?law|devr|jeth|nanad)\b"
)

# Topics the LLM must NOT mention in interpretation unless present in question.
_INTERP_TOPIC_CHECKS: list[tuple[re.Pattern[str], re.Pattern[str], str]] = [
    (
        re.compile(r"(?ix)\bin[\s-]?law|inlaw|sasural|saas|sasur|mother[\s-]?in[\s-]?law"),
        _INLAW_RX,
        "in-laws",
    ),
    (
        re.compile(r"(?ix)\bpartner'?s?\b|\bspouse\b|\bhusband\b|\bwife\b"),
        _PARTNER_SUBJECT_RX,
        "partner/spouse",
    ),
    (
        re.compile(r"(?ix)\bcareer\b|\bjob\b|\bnaukri\b"),
        _DOMAIN_ANCHOR_RX["career"],
        "career",
    ),
    (
        re.compile(r"(?ix)\bmarriage\b|\bshaadi\b|\bshadi\b"),
        _DOMAIN_ANCHOR_RX["marriage"],
        "marriage",
    ),
    (
        re.compile(r"(?ix)\bhealth\b|\bsehat\b"),
        _DOMAIN_ANCHOR_RX["health"],
        "health",
    ),
]

_ARCHETYPE_ANCHOR_RX: dict[str, re.Pattern[str]] = {
    "partner_nature": _PARTNER_SUBJECT_RX,
    "spouse_profession": re.compile(
        r"(?ix)\b(partner|spouse|pati|patni|biwi|husband|wife).{0,40}"
        r"(job|career|profession|doctor|engineer|business)|"
        r"(job|career|profession).{0,40}(partner|spouse|pati|patni)"
    ),
    "spouse_wealth": re.compile(
        r"(?ix)\b(partner|spouse|pati|patni).{0,30}(rich|wealth|amir|paisa|money)|"
        r"(rich|wealth|amir).{0,30}(partner|spouse|pati|patni)"
    ),
    "spouse_appearance": re.compile(
        r"(?ix)\b(partner|spouse|pati|patni|wife|husband).{0,30}"
        r"(look|face|height|appearance|colour|color|beautiful|handsome)|"
        r"(look|face|height|appearance).{0,30}(partner|spouse|wife|husband)"
    ),
    "loyalty_trust": re.compile(
        r"(?ix)\b(loyal|trust|cheat|dhokha|vishwas|faithful|commitment)\b"
    ),
    "manglik": re.compile(r"(?ix)\b(manglik|mangal\s*dosh)\b"),
}


_DOMAIN_PRIORITY = (
    "litigation",
    "health",
    "children",
    "education",
    "travel",
    "property",
    "finance",
    "career",
    "marriage",
    "love",
)


def infer_primary_domain(question: str) -> str | None:
    """Best-effort domain from question words (regex only)."""
    q = (question or "").strip()
    if not q:
        return None
    for dom in _DOMAIN_PRIORITY:
        rx = _DOMAIN_ANCHOR_RX.get(dom)
        if rx and rx.search(q):
            return dom
    return None


def _upgrade_domain_archetypes(question: str, domain: str, out: dict[str, Any]) -> None:
    q = question or ""
    if domain == "finance":
        try:
            from ask_finance.finance_registry import detect_finance_archetype

            out["finance_archetype"] = detect_finance_archetype(q) or "general_finance"
        except Exception:
            out["finance_archetype"] = "general_finance"
    elif domain == "career":
        try:
            from ask_career.classifier import classify_career_archetype

            out["career_archetype"] = classify_career_archetype(q)
        except Exception:
            out["career_archetype"] = "general_career"
    elif domain == "health":
        out["health_archetype"] = out.get("health_archetype") or "general_health"
    elif domain in ("marriage", "love"):
        try:
            from ask_mr.classifier import classify_mr_archetype

            out["mr_archetype"] = classify_mr_archetype(q)
        except Exception:
            out["mr_archetype"] = "general_mr"


def faithful_interpretation(question: str, *, user_turn: str | None = None) -> str:
    """Admin + narrator hint: always echo the user's actual question."""
    q = " ".join((user_turn or question or "").split()).strip()
    if not q:
        return "User asked an empty question."
    return f'User asked: "{q}"'


def _interpretation_hallucinates(question: str, interpretation: str) -> bool:
    q = question or ""
    interp = interpretation or ""
    if not interp.strip():
        return False
    for interp_rx, q_rx, _label in _INTERP_TOPIC_CHECKS:
        if interp_rx.search(interp) and not q_rx.search(q):
            return True
    return False


def _domain_supported(question: str, domain: str) -> bool:
    dom = (domain or "").strip().lower()
    if dom in ("", "general"):
        return True
    rx = _DOMAIN_ANCHOR_RX.get(dom)
    if rx is None:
        return True
    return bool(rx.search(question or ""))


def _archetype_supported(question: str, archetype: str | None) -> bool:
    if not archetype:
        return True
    arch = str(archetype).strip().lower()
    rx = _ARCHETYPE_ANCHOR_RX.get(arch)
    if rx is None:
        return True
    return bool(rx.search(question or ""))


def _clear_domain_archetypes(result: dict[str, Any]) -> None:
    result["mr_archetype"] = None
    result["career_archetype"] = None
    result["finance_archetype"] = None
    result["health_archetype"] = None
    result["education_archetype"] = None
    result["children_archetype"] = None
    result["property_archetype"] = None
    result["travel_archetype"] = None
    result["litigation_archetype"] = None


def archetype_allowed_for_question(question: str, archetype: str | None) -> bool:
    return _archetype_supported(question, archetype)


def repair_llm_intent(question: str, result: dict[str, Any] | None) -> dict[str, Any]:
    """Validate LLM routing against question text; fix or reject hallucinations."""
    if not isinstance(result, dict):
        return result or {}

    q = (question or "").strip()
    out = dict(result)
    repaired = False
    reject = False

    domain = str(out.get("domain") or "general").strip().lower()
    mr_arch = out.get("mr_archetype")
    interp = str(out.get("interpretation") or "").strip()

    if _interpretation_hallucinates(q, interp):
        repaired = True

    if domain in ("marriage", "love") and not (
        _DOMAIN_ANCHOR_RX["marriage"].search(q)
        or _DOMAIN_ANCHOR_RX["love"].search(q)
        or _PARTNER_SUBJECT_RX.search(q)
    ):
        domain = "general"
        mr_arch = None
        out["is_timing"] = False
        repaired = True

    if not _domain_supported(q, domain):
        domain = "general"
        _clear_domain_archetypes(out)
        mr_arch = None
        repaired = True

    if mr_arch and not _archetype_supported(q, str(mr_arch)):
        mr_arch = None
        repaired = True

    # partner_nature without any partner/in-law anchor → never trust
    if str(mr_arch or "").lower() == "partner_nature" and not _PARTNER_SUBJECT_RX.search(q):
        mr_arch = None
        if domain in ("marriage", "love"):
            domain = "general"
        repaired = True

    try:
        from ask_native_overview import is_native_overview_question

        if is_native_overview_question(q):
            domain = "general"
            mr_arch = None
            out["is_timing"] = False
            out["is_decision"] = False
            repaired = True
    except Exception:
        pass

    inferred = infer_primary_domain(q)
    if inferred and domain == "general":
        domain = inferred
        mr_arch = None
        _clear_domain_archetypes(out)
        _upgrade_domain_archetypes(q, domain, out)
        repaired = True

    # If marriage domain but no archetype and no clear MR signal → general chart Q
    if domain in ("marriage", "love") and not mr_arch and not _PARTNER_SUBJECT_RX.search(q):
        domain = "general"
        repaired = True

    out["domain"] = domain
    out["mr_archetype"] = mr_arch
    out["interpretation"] = faithful_interpretation(q)
    out["question_echo"] = q

    src = str(out.get("source") or "")
    if reject or (src == "llm" and repaired and domain == "general" and not mr_arch):
        # Heavy mismatch — regex fallback in caller
        if (
            str(result.get("domain") or "") in ("marriage", "love")
            and result.get("mr_archetype")
            and not _PARTNER_SUBJECT_RX.search(q)
        ):
            out["source"] = "llm_mismatch"
            out["repair_note"] = "LLM topic not in question — regex fallback"
        elif repaired:
            out["source"] = "llm_repaired"
            out["repair_note"] = "Routing aligned to question text"
    elif repaired and src == "llm":
        out["source"] = "llm_repaired"
        out["repair_note"] = "Routing aligned to question text"

    return out
