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
        r"(?ix)\b(love|pyaar|pyar|prem|crush|boyfriend|girlfriend|bf|gf|"
        r"dating|flirt|one[\s-]?sided|true\s*love|sach+a\s*pyaar|sach+a\s*pyar|"
        r"mohabbat)\b"
    ),
    "career": re.compile(
        r"(?ix)\b(career|naukri|nokri|job|business|promotion|interview|"
        r"salary|boss|company|employment|youtuber|govt\s*job)\b"
    ),
    "finance": re.compile(
        r"(?ix)\b(paisa|paise|money|wealth|finance|income|saving|loan|"
        r"debt|invest|profit|loss|amir|crorepati|dhan|dhana|kamana|kamai|"
        r"earning|garib|bachat|kharcha|aamdani)\b"
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
    "vehicle": re.compile(
        r"(?ix)\b("
        r"car|cars|bike|bikes|scooter|scooty|motorcycle|motorbike|"
        r"vehicle|vehicles|gaadi|gadi|suv|sedan|hatchback|automobile"
        r")\b"
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
        r"(?ix)\b(loyal|trust|cheat|dhokha|dhoka|betray|vishwas|faithful|commitment|beimaan)\b"
    ),
    "manglik": re.compile(r"(?ix)\b(manglik|mangal\s*dosh)\b"),
}


_DOMAIN_PRIORITY = (
    "litigation",
    "vehicle",
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


def _clip_one_line(text: str, *, max_len: int = 320) -> str:
    s = " ".join((text or "").split()).strip()
    if not s:
        return ""
    if len(s) <= max_len:
        return s
    cut = s[:max_len].rsplit(" ", 1)[0]
    return f"{cut}…" if cut else s[:max_len]


def summarize_question_one_line(
    question: str,
    llm_intent: dict[str, Any] | None = None,
) -> str:
    """Plain one-line restatement of what the user asked (admin + narrator)."""
    li = llm_intent if isinstance(llm_intent, dict) else {}
    summary = str(li.get("question_summary") or "").strip()
    if summary:
        return _clip_one_line(summary)

    interp = str(li.get("interpretation") or "").strip()
    if interp.lower().startswith("user asked:"):
        inner = interp.split(":", 1)[-1].strip().strip('"').strip("'")
        if inner:
            return _clip_one_line(inner)

    q = " ".join((question or "").split()).strip()
    if not q:
        return "Khali sawal"
    inferred = infer_primary_domain(q)
    if inferred:
        return _clip_one_line(f"{inferred}: {q}", max_len=260)
    return _clip_one_line(q, max_len=260)


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
    q = question or ""
    if arch == "dating_courtship" and re.search(
        r"(?ix)\b(dhokha|dhoka|betray|cheat|cheating|loyal|trust|vishwas|faithful|beimaan)\b",
        q,
    ):
        return False
    rx = _ARCHETYPE_ANCHOR_RX.get(arch)
    if rx is None:
        return True
    return bool(rx.search(q))


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


def resolve_question_understood(
    question: str,
    llm_intent: dict[str, Any] | None = None,
    *,
    skip_reason: str = "",
    intent_source: str = "",
    has_engine_facts: bool = False,
) -> str:
    """One-word admin answer: did the LLM understand the question? yes | no."""
    q = (question or "").strip()
    if not q:
        return "no"

    li = llm_intent if isinstance(llm_intent, dict) else {}
    summary = str(li.get("question_summary") or "").strip()
    if summary and len(summary) >= 10:
        return "yes"

    src = str(li.get("source") or intent_source or "").strip().lower()
    if src == "llm_mismatch":
        return "no"

    try:
        conf = float(li.get("confidence") or 0.0)
    except (TypeError, ValueError):
        conf = 0.0
    dom = str(li.get("domain") or "").strip().lower()
    inferred = infer_primary_domain(q)

    if has_engine_facts:
        return "yes"

    try:
        from ask_native_overview import is_native_overview_question

        if is_native_overview_question(q):
            return "yes"
    except Exception:
        pass

    if dom and dom != "general" and conf >= 0.5:
        return "yes"
    if inferred and src in ("llm", "llm_repaired", "llm_low_conf", ""):
        return "yes"
    if inferred and intent_source in ("llm", "llm_repaired", "regex"):
        return "yes"

    skip = (skip_reason or "").strip().lower()
    if "engine_required" in skip:
        return "yes" if (dom and dom != "general") or inferred else "no"

    if src in ("llm", "llm_repaired") and conf >= 0.65:
        return "yes"
    if src == "llm_low_conf" and conf >= 0.45 and (dom != "general" or inferred):
        return "yes"

    if intent_source == "regex" and (inferred or (dom and dom != "general")):
        return "yes"

    return "no"


def build_question_understanding_detail(
    question: str,
    llm_intent: dict[str, Any] | None = None,
    *,
    skip_reason: str = "",
    intent_source: str = "",
    engine_archetype: str = "",
) -> str:
    """Optional Hinglish detail — how routing worked (admin only)."""
    q = (question or "").strip()
    li = llm_intent if isinstance(llm_intent, dict) else {}
    skip = (skip_reason or "").strip().lower()
    dom = str(li.get("domain") or "general").strip().lower()
    try:
        conf = float(li.get("confidence") or 0.0)
    except (TypeError, ValueError):
        conf = 0.0
    src = str(li.get("source") or intent_source or "").strip().lower()
    timing = "timing" if li.get("is_timing") else "static"
    inferred = infer_primary_domain(q)
    engine_arch = str(engine_archetype or "").strip().lower()
    llm_arch = str(
        li.get("finance_archetype")
        or li.get("mr_archetype")
        or li.get("health_archetype")
        or li.get("career_archetype")
        or ""
    ).strip().lower()

    def _arch_detail(arch: str) -> str:
        base = f"{dom} / {arch} ({timing}), confidence {conf:.0%}."
        if engine_arch and llm_arch and engine_arch != llm_arch:
            return f"{base} Engine={engine_arch}, LLM guess={llm_arch}."
        return base

    if "engine_required" in skip:
        if dom and dom != "general":
            return (
                f"{dom} samjha (confidence {conf:.0%}) lekin engine facts nahi mile."
            )
        if inferred:
            return f"{inferred} samjha lekin engine facts nahi mile."
        return "Engine match nahi — chart-only answer block."

    if src == "llm_mismatch":
        return "Galat topic samjha tha — exact words par repair kiya."

    try:
        from ask_native_overview import is_native_overview_question

        if is_native_overview_question(q):
            return "General native overview — specific domain nahi."
    except Exception:
        pass

    arch = engine_arch or llm_arch
    if arch:
        return _arch_detail(arch)
    if dom != "general":
        return f"{dom} domain ({timing}), confidence {conf:.0%}."
    if inferred:
        return f"Regex anchor: {inferred} ({timing})."
    return f"General/vague ({timing}), confidence {conf:.0%}."


def build_question_understanding_line(
    question: str,
    llm_intent: dict[str, Any] | None = None,
    *,
    skip_reason: str = "",
    intent_source: str = "",
    has_engine_facts: bool = False,
    engine_archetype: str = "",
) -> str:
    """One admin line: Yes/No + how routing worked."""
    return build_llm_understood_one_liner(
        question,
        llm_intent,
        skip_reason=skip_reason,
        intent_source=intent_source,
        has_engine_facts=has_engine_facts,
        engine_archetype=engine_archetype,
    )


def build_llm_understood_one_liner(
    question: str,
    llm_intent: dict[str, Any] | None = None,
    *,
    skip_reason: str = "",
    intent_source: str = "",
    has_engine_facts: bool = False,
    engine_archetype: str = "",
) -> str:
    """Single admin line: Yes/No + one-line what user asked + routing hint."""
    word = resolve_question_understood(
        question,
        llm_intent,
        skip_reason=skip_reason,
        intent_source=intent_source,
        has_engine_facts=has_engine_facts,
    )
    yes_no = "Yes" if word == "yes" else "No"
    summary = summarize_question_one_line(question, llm_intent)
    route = build_question_understanding_detail(
        question,
        llm_intent,
        skip_reason=skip_reason,
        intent_source=intent_source,
        engine_archetype=engine_archetype,
    ).strip().rstrip(".")
    if summary and route:
        return f"{yes_no} — {summary} · {route}."
    if summary:
        return f"{yes_no} — {summary}."
    if route:
        return f"{yes_no} — {route}."
    return yes_no


def repair_llm_intent(question: str, result: dict[str, Any] | None) -> dict[str, Any]:
    """Validate LLM routing against question text; fix or reject hallucinations."""
    if not isinstance(result, dict):
        return result or {}

    q = (question or "").strip()
    out = dict(result)
    summary = str(out.get("question_summary") or "").strip()
    combined = f"{q} {summary}".strip() if summary else q
    repaired = False
    reject = False

    domain = str(out.get("domain") or "general").strip().lower()
    mr_arch = out.get("mr_archetype")
    interp = str(out.get("interpretation") or "").strip()

    if _interpretation_hallucinates(combined, interp):
        repaired = True

    try:
        from ask_route_from_understanding import is_native_love_chart_question
    except Exception:
        def is_native_love_chart_question(_t: str) -> bool:  # type: ignore[misc]
            return False

    if domain in ("marriage", "love") and not (
        _DOMAIN_ANCHOR_RX["marriage"].search(combined)
        or _DOMAIN_ANCHOR_RX["love"].search(combined)
        or _PARTNER_SUBJECT_RX.search(combined)
        or is_native_love_chart_question(combined)
    ):
        domain = "general"
        mr_arch = None
        out["is_timing"] = False
        repaired = True

    if not _domain_supported(combined, domain):
        domain = "general"
        _clear_domain_archetypes(out)
        mr_arch = None
        repaired = True

    if mr_arch and not _archetype_supported(combined, str(mr_arch)):
        mr_arch = None
        repaired = True

    # partner_nature without any partner/in-law anchor → never trust
    if str(mr_arch or "").lower() == "partner_nature" and not _PARTNER_SUBJECT_RX.search(combined):
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

    try:
        from ask_vehicle.timing_registry import is_vehicle_timing_question  # type: ignore

        if is_vehicle_timing_question(combined, out):
            out["domain"] = "vehicle"
            out["is_timing"] = True
            out["is_decision"] = False
            _clear_domain_archetypes(out)
            mr_arch = None
            repaired = True
    except Exception:
        pass

    inferred = infer_primary_domain(combined)
    if inferred and domain == "general":
        domain = inferred
        mr_arch = None
        _clear_domain_archetypes(out)
        _upgrade_domain_archetypes(combined, domain, out)
        repaired = True

    # Native love chart (true love yog) — keep love + dating_courtship without partner subject.
    if domain in ("marriage", "love") and not mr_arch and is_native_love_chart_question(combined):
        try:
            from ask_mr.classifier import classify_mr_archetype

            mr_arch = classify_mr_archetype(combined) or "dating_courtship"
            out["mr_archetype"] = mr_arch
            repaired = True
        except Exception:
            out["mr_archetype"] = "dating_courtship"
            mr_arch = "dating_courtship"
            repaired = True

    if domain in ("marriage", "love") and not mr_arch and not _PARTNER_SUBJECT_RX.search(combined):
        if not is_native_love_chart_question(combined):
            domain = "general"
            repaired = True

    out["domain"] = domain
    out["mr_archetype"] = mr_arch
    out["interpretation"] = faithful_interpretation(q)
    out["question_echo"] = q
    if not str(out.get("question_summary") or "").strip():
        out["question_summary"] = summarize_question_one_line(q, out)
    if repaired:
        out.pop("understanding_line", None)
    out["question_understood"] = resolve_question_understood(
        q, out, intent_source=str(out.get("source") or "")
    )
    out["understanding_detail"] = build_question_understanding_detail(
        q, out, intent_source=str(out.get("source") or "")
    )
    out["understanding_line"] = build_llm_understood_one_liner(
        q, out, intent_source=str(out.get("source") or "")
    )

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
