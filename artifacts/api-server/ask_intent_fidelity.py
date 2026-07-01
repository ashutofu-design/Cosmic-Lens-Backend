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

# "Hum dono ke beech …" — chemistry between two people, not native solo attraction.
_DYAD_COUPLE_RX = re.compile(
    r"(?ix)\b("
    r"hum\s+dono\s+ke\s+beech|ham\s+dono\s+ke\s+beech|"
    r"hum\s+dono\s+mein?|ham\s+dono\s+mein?|"
    r"tum\s+dono\s+ke\s+beech|aap\s+dono\s+ke\s+beech|"
    r"dono\s+ke\s+beech|"
    r"between\s+(?:us|the\s+two\s+of\s+us|both\s+of\s+us)"
    r")\b"
)

_CHEMISTRY_TOPIC_RX = re.compile(
    r"(?ix)\b(chemistry|attraction|spark|passion|romance|romantic)\b"
)


def is_dyadic_couple_question(question: str) -> bool:
    return bool(_DYAD_COUPLE_RX.search((question or "").strip()))


_PARTNER_FIT_RX = re.compile(
    r"(?ix)\b("
    r"kis\s+tarah\s+ka\s+partner|kaisa\s+partner|kaisi\s+partner|"
    r"partner\s+suit|suit\s+kareg|suitable\s+partner|"
    r"partner\s+match|match\s+kareg|mera\s+partner\s+kaisa"
    r")\b"
)


def is_partner_relationship_question(question: str) -> bool:
    """Partner/spouse/couple subject — must not route to health/career/etc."""
    q = (question or "").strip()
    if not q:
        return False
    if is_dyadic_couple_question(q):
        return True
    if _PARTNER_SUBJECT_RX.search(q):
        return True
    if _PARTNER_FIT_RX.search(q):
        return True
    if re.search(r"(?ix)\b(partner|spouse|rishta|shaadi|vivah)\b", q) and re.search(
        r"(?ix)\b(suit|match|compatible|thinking|soch|mental|nature|swabhav|kaisa|kaisi|tarah)\b",
        q,
    ):
        return True
    return False


def is_native_solo_chemistry_question(question: str) -> bool:
    """Native-chart chemistry read — not 'between us two'."""
    q = (question or "").strip()
    return bool(_CHEMISTRY_TOPIC_RX.search(q)) and not is_dyadic_couple_question(q)

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
        r"(?ix)\b(partner|spouse|pati|patni|wife|husband).{0,40}"
        r"(look|face|height|appearance|colour|color|beautiful|handsome|attract\w*|dikh\w*|good[\s-]?looking)|"
        r"(look|face|height|appearance|attract\w*|dikh\w*|good[\s-]?looking).{0,40}(partner|spouse|wife|husband)"
    ),
    "loyalty_trust": re.compile(
        r"(?ix)\b(loyal|trust|cheat|dhokha|dhoka|betray|vishwas|faithful|commitment|beimaan)\b"
    ),
    "chemistry": re.compile(
        r"(?ix)\b(chemistry|attraction|spark|passion|romance|romantic)\b"
    ),
    "dating_courtship": re.compile(
        r"(?ix)\b(true\s*love|sach+a\s*pyaar|sach+a\s*pyar|milne\s+ka\s+yog|"
        r"dating|courtship|friend\s*to\s*lover|red\s*flags?|green\s*flags?)\b"
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


def _clip_explanation(text: str, *, max_len: int = 1800, max_lines: int = 10) -> str:
    raw = (text or "").strip().replace("\\n", "\n")
    if not raw:
        return ""
    lines = [ln.strip() for ln in raw.splitlines() if ln.strip()]
    if not lines:
        lines = [_clip_one_line(raw, max_len=max_len)]
    lines = lines[:max_lines]
    out = "\n".join(lines)
    if len(out) <= max_len:
        return out
    trimmed: list[str] = []
    used = 0
    for ln in lines:
        if used + len(ln) + 1 > max_len:
            break
        trimmed.append(ln)
        used += len(ln) + 1
    return "\n".join(trimmed) if trimmed else _clip_one_line(out, max_len=max_len)


def build_question_explanation_fallback(
    question: str,
    llm_intent: dict[str, Any] | None = None,
) -> str:
    """Regex/template intent explanation — never echo the question verbatim."""
    q = (question or "").strip()
    if not q:
        return "Khali ya incomplete sawal."
    scope = infer_question_scope(q, llm_intent)
    lines: list[str] = []

    if scope == "partner" or is_partner_relationship_question(q):
        lines.append("User partner / life-partner ke baare mein guidance maang raha hai.")
        if re.search(r"(?ix)\b(suit|match|compatible|thinking|soch|mental|nature|swabhav|tarah)\b", q):
            lines.append(
                "Core intent: kaun sa type ka partner unki soch, mental style aur personality ke saath fit baithega."
            )
            lines.append("Yeh sehat/body health sawal nahi — rishta / partner traits ka sawal hai.")
        elif re.search(r"(?ix)\b(loyal|trust|cheat|dhokha|commit)\b", q):
            lines.append("User partner ki wafadari, trust ya commitment level samajhna chahta hai.")
        else:
            lines.append("User partner ke nature, behaviour ya rishta pattern ke baare mein jaanna chahta hai.")
    elif scope == "couple" or is_dyadic_couple_question(q):
        lines.append("User do logon ke beech ke rishte / bond ke baare mein pooch raha hai.")
        if re.search(r"(?ix)\b(chemistry|passion|intense|attraction)\b", q):
            lines.append("Focus: dono ke beech chemistry, passion ya emotional pull kaisi rahegi.")
        else:
            lines.append("Focus: dono ke beech compatibility, closeness ya dynamic kaisi rahegi.")
    elif scope in ("love", "marriage"):
        lines.append(f"User {scope} / romantic life se related astrology guidance chahta hai.")
        if re.search(r"(?ix)\b(kab|when|timing|kitne\s+saal)\b", q):
            lines.append("Timing / kab hoga type ka sawal lag raha hai.")
        else:
            lines.append("Quality / pattern / chances type ka static sawal lag raha hai.")
    elif scope == "career":
        lines.append("User career, job, business ya professional growth ke baare mein jaanna chahta hai.")
    elif scope == "health":
        lines.append("User apni sehat, body, recovery ya health risk ke baare mein pooch raha hai.")
    elif scope == "finance":
        lines.append("User paisa, dhan, savings, loss ya wealth ke baare mein guidance maang raha hai.")
    elif scope == "self":
        lines.append("User apne baare mein — apni personality, nature ya life pattern — samajhna chahta hai.")
    else:
        dom = infer_primary_domain(q)
        if dom:
            lines.append(f"User ka {dom} area se related astrology sawal hai.")
        else:
            lines.append("User chart se apni situation ke baare mein general guidance maang raha hai.")

    if re.search(r"(?ix)\b(kab|when|kitne\s+saal|timing|muhurat)\b", q) and "Timing" not in " ".join(lines):
        lines.append("Sawal mein timing / kab element bhi hai.")
    if re.search(r"(?ix)\b(ya|or|aur)\b", q):
        lines.append("User ne do options ya multiple parts compare kiye hain — sab cover karna hoga.")

    return _clip_explanation("\n".join(lines), max_lines=10)


_VALID_QUESTION_SCOPES = frozenset({
    "love",
    "marriage",
    "partner",
    "couple",
    "career",
    "health",
    "finance",
    "education",
    "children",
    "property",
    "travel",
    "legal",
    "vehicle",
    "spiritual",
    "self",
    "family",
    "general",
})

_SCOPE_ALIASES = {
    "relationship": "love",
    "romance": "love",
    "job": "career",
    "jobs": "career",
    "money": "finance",
    "wealth": "finance",
    "litigation": "legal",
    "court": "legal",
    "native": "self",
    "personal": "self",
    "spouse": "partner",
}

_SCOPE_BRACKET_RX = re.compile(r"^\[([a-z][a-z0-9_]*)\]\s*", re.IGNORECASE)


def normalize_question_scope(scope: str) -> str:
    s = (scope or "").strip().lower().replace(" ", "_").replace("-", "_")
    s = _SCOPE_ALIASES.get(s, s)
    return s if s in _VALID_QUESTION_SCOPES else "general"


def strip_scope_bracket(text: str) -> str:
    return _SCOPE_BRACKET_RX.sub("", (text or "").strip(), count=1).strip()


def parse_scoped_summary(text: str) -> tuple[str, str]:
    """Return (scope, body) from '[love] User wants…' or infer general."""
    raw = (text or "").strip()
    m = _SCOPE_BRACKET_RX.match(raw)
    if m:
        return normalize_question_scope(m.group(1)), raw[m.end() :].strip()
    return "general", raw


def infer_question_scope(question: str, llm_intent: dict[str, Any] | None = None) -> str:
    li = llm_intent if isinstance(llm_intent, dict) else {}
    explicit = str(li.get("question_scope") or "").strip()
    if explicit:
        return normalize_question_scope(explicit)

    summary_scope, _ = parse_scoped_summary(str(li.get("question_summary") or ""))
    if summary_scope != "general":
        return summary_scope

    q = (question or "").strip()
    if is_partner_relationship_question(q):
        return "partner"
    if is_dyadic_couple_question(q):
        return "couple"
    if _PARTNER_SUBJECT_RX.search(q):
        return "partner"

    dom = str(li.get("routed_domain") or li.get("domain") or "").strip().lower()
    if dom == "litigation":
        return "legal"
    if dom and dom != "general":
        return normalize_question_scope(dom)

    inferred = infer_primary_domain(q)
    if inferred == "litigation":
        return "legal"
    if inferred:
        return normalize_question_scope(inferred)

    if re.search(r"(?ix)\b(mera|meri|mere|main|mujhe|my)\b", q) and not _PARTNER_SUBJECT_RX.search(q):
        return "self"
    return "general"


def format_question_understanding(scope: str, summary: str) -> str:
    body = _clip_explanation(strip_scope_bracket(summary))
    sc = normalize_question_scope(scope)
    if not body:
        return f"[{sc}]"
    return f"[{sc}]\n{body}"


def summarize_question_one_line(
    question: str,
    llm_intent: dict[str, Any] | None = None,
    *,
    with_scope: bool = True,
) -> str:
    """Plain one-line restatement of what the user asked (admin + narrator)."""
    li = llm_intent if isinstance(llm_intent, dict) else {}
    summary = strip_scope_bracket(str(li.get("question_summary") or "").strip())
    if summary:
        body = _clip_explanation(summary)
        if with_scope:
            scope = infer_question_scope(question, li)
            return format_question_understanding(scope, body)
        return body

    interp = str(li.get("interpretation") or "").strip()
    if interp.lower().startswith("user asked:"):
        inner = interp.split(":", 1)[-1].strip().strip('"').strip("'")
        if inner:
            body = _clip_one_line(inner)
            if with_scope:
                return format_question_understanding(infer_question_scope(question, li), body)
            return body

    q = " ".join((question or "").split()).strip()
    if not q:
        return "Khali sawal"
    try:
        from ask_route_from_understanding import is_native_love_chart_question

        if is_native_love_chart_question(q):
            body = _clip_one_line(
                "User pooch raha hai kya unki kundli me sacha pyaar / true love milne ka yog hai",
            )
            if with_scope:
                return format_question_understanding("love", body)
            return body
    except Exception:
        pass
    inferred = infer_primary_domain(q)
    if inferred:
        body = build_question_explanation_fallback(q, li).split("\n")[0].strip()
        if with_scope:
            return format_question_understanding(infer_question_scope(q, li), body)
        return body
    body = build_question_explanation_fallback(q, li).split("\n")[0].strip()
    if with_scope:
        return format_question_understanding(infer_question_scope(q, li), body)
    return body


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
    arch = str(archetype or "").strip().lower()
    q = question or ""
    if arch == "chemistry" and is_dyadic_couple_question(q):
        return False
    if arch.startswith("general_health") or arch in (
        "mental_stress",
        "overall_vitality",
        "chronic_tendency",
    ):
        if is_partner_relationship_question(q):
            return False
    try:
        from ask_route_from_understanding import is_native_love_chart_question

        if is_native_love_chart_question(q):
            if arch in ("chemistry", "emotional_attachment", "general_mr", "partner_nature"):
                return False
            if arch == "dating_courtship":
                return True
    except Exception:
        pass
    return _archetype_supported(question, archetype)


def resolve_question_understood(
    question: str,
    llm_intent: dict[str, Any] | None = None,
    *,
    skip_reason: str = "",
    intent_source: str = "",
    has_engine_facts: bool = False,
    engine_archetype: str = "",
) -> str:
    """One-word admin answer: did the LLM understand the question? yes | no."""
    q = (question or "").strip()
    if not q:
        return "no"

    li = llm_intent if isinstance(llm_intent, dict) else {}
    ran_arch = str(
        engine_archetype
        or li.get("routed_archetype")
        or li.get("mr_archetype")
        or ""
    ).strip().lower()
    try:
        from ask_question_understand import _echoes_question

        body = strip_scope_bracket(str(li.get("question_summary") or ""))
        if body and _echoes_question(body, q):
            return "no"
    except Exception:
        pass
    if ran_arch and not archetype_allowed_for_question(q, ran_arch):
        return "no"

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

    scope_tag = infer_question_scope(q, li)
    scope_prefix = f"[{scope_tag}] "

    def _detail(msg: str) -> str:
        m = (msg or "").strip()
        if scope_prefix and m and not m.startswith("["):
            return f"{scope_prefix}{m}"
        return m

    if "engine_required" in skip:
        if dom and dom != "general":
            return _detail(
                f"{dom} samjha (confidence {conf:.0%}) lekin engine facts nahi mile."
            )
        if inferred:
            return _detail(f"{inferred} samjha lekin engine facts nahi mile.")
        return _detail("Engine match nahi — chart-only answer block.")

    if src == "llm_mismatch":
        return _detail("Galat topic samjha tha — exact words par repair kiya.")

    try:
        from ask_native_overview import is_native_overview_question

        if is_native_overview_question(q):
            return _detail("General native overview — specific domain nahi.")
    except Exception:
        pass

    arch = engine_arch or llm_arch
    if arch:
        return _detail(_arch_detail(arch))
    if dom != "general":
        return _detail(f"{dom} domain ({timing}), confidence {conf:.0%}.")
    if inferred:
        return _detail(f"Regex anchor: {inferred} ({timing}).")
    return _detail(f"General/vague ({timing}), confidence {conf:.0%}.")


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
    li = llm_intent if isinstance(llm_intent, dict) else {}
    body = strip_scope_bracket(str(li.get("question_summary") or "")).strip()
    if not body:
        body = build_question_explanation_fallback(question, li).split("\n")[0].strip()
    else:
        body = body.split("\n")[0].strip()
    scope = infer_question_scope(question, li)
    summary = f"[{scope}] {body}" if body else ""
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

    try:
        from ask_mr.timing_registry import repair_llm_intent_mr_static_timing

        if repair_llm_intent_mr_static_timing(q, out):
            domain = str(out.get("domain") or domain)
            mr_arch = out.get("mr_archetype")
            repaired = True
    except Exception:
        pass

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
