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
    r"hamari|hamara|hamare|humari|humara|humare|"
    r"between\s+(?:us|the\s+two\s+of\s+us|both\s+of\s+us)"
    r")\b"
)

_CHEMISTRY_TOPIC_RX = re.compile(
    r"(?ix)\b(chemistry|attraction|spark|passion|romance|romantic)\b"
)


def is_dyadic_couple_question(question: str) -> bool:
    return bool(_DYAD_COUPLE_RX.search((question or "").strip()))


_COMPAT_ANGLE_RULES: list[tuple[str, re.Pattern[str]]] = [
    (
        "personalities_match",
        re.compile(r"(?ix)\b(personality|personalities|swabhav)\b.{0,40}\b(match|milt)"),
    ),
    (
        "thinking_match",
        re.compile(r"(?ix)\b(thinking|soch)\b.{0,40}\b(match|milt)"),
    ),
    (
        "values_match",
        re.compile(r"(?ix)\b(values?|sanskaar)\b.{0,40}\b(same|match|milt|align)"),
    ),
    (
        "life_goals_match",
        re.compile(
            r"(?ix)\b(life\s*goals?|goals?|sapne|ambition|ambitions)\b.{0,40}\b(match|milt|align)"
        ),
    ),
    (
        "expectations_match",
        re.compile(r"(?ix)\b(expectations?|ummeed|expect)\b"),
    ),
    (
        "emotional_compatibility",
        re.compile(r"(?ix)\b(emotionally|emotional)\b.{0,30}\b(compat|match|milt)"),
    ),
    (
        "mental_compatibility",
        re.compile(r"(?ix)\b(mentally|mental)\b.{0,30}\b(compat|match|milt)"),
    ),
    (
        "intellectual_compatibility",
        re.compile(r"(?ix)\b(intellectually|intellectual)\b.{0,30}\b(compat|match|milt)"),
    ),
    (
        "general_compatibility",
        re.compile(r"(?ix)\b(compat(?:ible|ibility)?|match)\b"),
    ),
]

_COMPAT_ANGLE_LABELS: dict[str, str] = {
    "personalities_match": (
        "Personality / nature match — daily temperament, traits, vibe dono ka"
    ),
    "thinking_match": "Thinking / mindset match — soch, ideas, samajhne ka style",
    "values_match": "Values / principles — kya dono ki soch aur ethics align hain",
    "life_goals_match": "Life goals / ambitions — long-term sapne aur direction align hain ya nahi",
    "expectations_match": "Expectations — dono ki ummeedein aur priorities same hain ya nahi",
    "emotional_compatibility": (
        "Emotional compatibility — feelings, mood-sync, dil ka connection"
    ),
    "mental_compatibility": (
        "Mental compatibility — dimaag ka match, processing style, soch ka rhythm"
    ),
    "intellectual_compatibility": (
        "Intellectual compatibility — ideas, learning, debate, depth of conversation"
    ),
    "general_compatibility": "General couple compatibility — overall match / bond",
}


def infer_compatibility_angle(question: str) -> str | None:
    """Exact compatibility sub-angle for couple matrix questions."""
    q = (question or "").strip()
    if not q:
        return None
    if not (
        is_dyadic_couple_question(q)
        or re.search(r"(?ix)\b(compat|match|values?|personalities?|expectations?)\b", q)
    ):
        return None
    for name, rx in _COMPAT_ANGLE_RULES:
        if rx.search(q):
            return name
    return None


def compatibility_angle_label(angle: str | None) -> str:
    key = (angle or "").strip().lower()
    return _COMPAT_ANGLE_LABELS.get(key, key.replace("_", " "))


_PARTNER_COMMITMENT_ANGLE_RULES: list[tuple[str, re.Pattern[str]]] = [
    ("commitment_ready", re.compile(r"(?ix)\b(commitment|commit).{0,35}\b(ready|taiyaar)\b|\bready\b.{0,35}\bcommit")),
    ("serious_relationship", re.compile(r"(?ix)\bserious\b.{0,25}\b(relationship|rishta)\b")),
    ("casual_relationship", re.compile(r"(?ix)\bcasual\b.{0,25}\b(relationship|rishta)\b")),
    ("long_term_intent", re.compile(r"(?ix)\blong[\s-]*term\b")),
    ("future_together", re.compile(r"(?ix)\b(future|aage|kal).{0,30}\b(saath|sath|with\s+me)\b")),
    ("life_partner_view", re.compile(r"(?ix)\b(life\s*partner|jeevan\s*sathi)\b")),
    ("loyalty_intent", re.compile(r"(?ix)\b(loyal|exclusive|faithful|wafad|vafad)\b")),
    ("time_pass", re.compile(r"(?ix)\b(time\s*pass|waqt\s*pass)\b")),
    ("genuine_intent", re.compile(r"(?ix)\b(genuine|sachcha|sachhe)\b")),
    ("effort_and_maintain", re.compile(r"(?ix)\b(effort|maintain|nibha|responsibility|sacrifice|compromise)\b")),
    ("trust_blockers", re.compile(r"(?ix)\b(trust\s*issues|past\s*relationship|emotionally\s*unavailable|commitment[\s-]*phobic|darta)\b")),
    ("public_acceptance", re.compile(r"(?ix)\b(public|family|official|introduce|secret)\b")),
]

_PARTNER_COMMITMENT_LABELS: dict[str, str] = {
    "commitment_ready": "Partner commitment ke liye ready hai ya nahi",
    "serious_relationship": "Partner serious long-term relationship chahta hai ya nahi",
    "casual_relationship": "Partner casual / time-pass relationship me hai ya nahi",
    "long_term_intent": "Partner long-term relationship chahta hai ya nahi",
    "future_together": "Partner future user ke saath dekhta hai ya nahi",
    "life_partner_view": "Partner user ko life partner maanta hai ya nahi",
    "loyalty_intent": "Partner loyal / exclusive rehna chahta hai ya nahi",
    "time_pass": "Partner sirf time pass kar raha hai ya nahi",
    "genuine_intent": "Partner genuinely invested hai ya nahi",
    "effort_and_maintain": "Partner relationship me effort / responsibility lega ya nahi",
    "trust_blockers": "Trust / past / emotional unavailability commitment block kar rahi hai ya nahi",
    "public_acceptance": "Partner relationship ko public / family ke saamne accept karega ya secret rakhega",
}


def infer_partner_commitment_angle(question: str) -> str | None:
    q = (question or "").strip()
    if not q:
        return None
    if not re.search(r"(?ix)\b(partner|spouse|bf|gf|pati|patni|boyfriend|girlfriend)\b", q):
        return None
    if not re.search(
        r"(?ix)\b(commit|serious|casual|loyal|relationship|nibha|trust|genuine|time\s*pass|"
        r"exclusive|sacrifice|compromise|responsibility|effort|maintain|future|official|secret)\b",
        q,
    ):
        return None
    for name, rx in _PARTNER_COMMITMENT_ANGLE_RULES:
        if rx.search(q):
            return name
    return "general_commitment"


def partner_commitment_angle_label(angle: str | None) -> str:
    key = (angle or "").strip().lower()
    return _PARTNER_COMMITMENT_LABELS.get(key, "Partner commitment / relationship intent")


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
        r"(?ix)\b(loyal|trust|cheat|dhokha|dhoka|betray|vishwas|faithful|beimaan)\b"
    ),
    "commitment": re.compile(
        r"(?ix)\b(commitment|committed|serious\s*relationship|casual|time\s*pass|timepass|"
        r"genuinely|genuine\s*intent|long[\s-]*term|shaadi\s*karega|shaadi\s*karegi)\b"
    ),
    "communication": re.compile(
        r"(?ix)\b(communication|baat\s*cheet|misunderstand|silent|silence|argument|jhagda|samajh\s*payeg\w*)\b"
    ),
    "relationship_future": re.compile(
        r"(?ix)\b(relationship\s+ka\s+future|hamare\s+relationship|aage\s+grow|grow\s+karega|bond\s+grow|future\s+kais)\b"
    ),
    "relationship_decisions": re.compile(
        r"(?ix)\b(stay\s+or\s+leave|should\s+i|mere\s+liye\s+sahi|rehna\s+chahiye|chhod\s+du|continue\s+karu)\b"
    ),
    "toxicity": re.compile(
        r"(?ix)\b(toxic|abuse|abusive|manipulat|controlling|red\s*flag|unhealthy)\b"
    ),
    "relationship_remedies": re.compile(
        r"(?ix)\b(upay|remedy|mantra|totka|puja).{0,40}(love|relationship|rishta|marriage)\b"
    ),
    "chemistry": re.compile(
        r"(?ix)\b(chemistry|attraction|spark|passion|romance|romantic)\b"
    ),
    "compatibility": re.compile(
        r"(?ix)\b("
        r"compat(?:ible|ibility)?|gun\s*milan|36\s*gun|match\s*making|"
        r"thinking\s*match|soch\s*match|values?\s*same|life\s*goals?\s*match|"
        r"personalities?\s*match|emotional\s*compat|mental\s*compat|intellectual\s*compat"
        r")\b"
    ),
    "dating_courtship": re.compile(
        r"(?ix)\b(true\s*love|sach+a\s*pyaar|sach+a\s*pyar|milne\s+ka\s+yog|"
        r"love\s+life|love\s+live|dating|courtship|relationship|"
        r"friend\s*to\s*lover|red\s*flags?|green\s*flags?|"
        r"kab\s+shuru|shuru\s+hoga)\b"
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
        pc_angle = infer_partner_commitment_angle(q)
        if pc_angle:
            lines.append(f"Exact focus: {partner_commitment_angle_label(pc_angle)}.")
            lines.append(
                "Yeh partner ke intent/commitment ka sawal hai — user ki shaadi timing / dasha mat do."
            )
        elif re.search(r"(?ix)\b(suit|match|compatible|thinking|soch|mental|nature|swabhav|tarah)\b", q):
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
        angle = infer_compatibility_angle(q)
        if angle:
            lines.append(f"Exact focus: {compatibility_angle_label(angle)}.")
            lines.append(
                "Yeh sirf isi angle ka jawab hai — doosre compatibility types (emotional vs mental vs intellectual) mein mat behko."
            )
        elif re.search(r"(?ix)\b(chemistry|passion|intense|attraction)\b", q):
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
    if is_dyadic_couple_question(q):
        return "couple"
    if is_partner_relationship_question(q):
        return "partner"
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


def enforce_commitment_archetype_from_question(question: str, out: dict[str, Any]) -> bool:
    """Raw question wins over LLM summary for commitment vs loyalty_trust misroutes."""
    q = (question or "").strip()
    if not q:
        return False
    try:
        from ask_mr.classifier import classify_mr_archetype

        classified = classify_mr_archetype(q)
    except Exception:
        return False
    if classified != "commitment":
        return False
    current = str(out.get("mr_archetype") or "").strip().lower()
    if current == "commitment":
        return False
    if current and current not in ("loyalty_trust", "loyalty", "trust"):
        return False
    out["mr_archetype"] = "commitment"
    out["domain"] = out.get("domain") or "love"
    out["is_timing"] = False
    out["routing_override"] = "commitment_classifier_raw_question"
    return True


def _archetype_supported(question: str, archetype: str | None) -> bool:
    if not archetype:
        return True
    arch = str(archetype).strip().lower()
    q = question or ""
    if arch == "loyalty_trust":
        try:
            from ask_mr.classifier import classify_mr_archetype

            if classify_mr_archetype(q) == "commitment":
                return False
        except Exception:
            pass
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
        from ask_chart_open_qa import is_native_self_chart_interpretation_question

        if is_native_love_chart_question(q) or is_native_self_chart_interpretation_question(q):
            if arch in (
                "chemistry",
                "compatibility",
                "commitment",
                "communication",
                "relationship_future",
                "relationship_decisions",
                "toxicity",
                "relationship_remedies",
                "emotional_attachment",
                "general_mr",
                "partner_nature",
            ):
                return False
            if arch in ("open_chart_qa", "dating_courtship"):
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
    if str(li.get("question_understood") or "").strip().lower() == "yes":
        return "yes"

    ran_arch = str(
        engine_archetype
        or li.get("routed_archetype")
        or li.get("mr_archetype")
        or ""
    ).strip().lower()

    if has_engine_facts:
        return "yes"

    try:
        from ask_question_understand import _echoes_question

        body = strip_scope_bracket(
            str(li.get("question_summary") or li.get("question_meaning") or "")
        )
        if body and _echoes_question(body, q):
            return "no"
    except Exception:
        pass
    if ran_arch in ("timing", "general_love", "general"):
        pass
    elif ran_arch and not archetype_allowed_for_question(q, ran_arch):
        return "no"

    summary = str(
        li.get("question_summary") or li.get("question_meaning") or ""
    ).strip()
    if summary and len(summary) >= 10:
        return "yes"

    src = str(li.get("source") or intent_source or "").strip().lower()
    if src == "llm_mismatch":
        return "no"

    try:
        conf = float(li.get("confidence") or 0.0)
    except (TypeError, ValueError):
        conf = 0.0
    dom = str(li.get("domain") or li.get("routed_domain") or "").strip().lower()
    inferred = infer_primary_domain(q)

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
    try:
        from ask_mr.timing_registry import (
            mr_static_overrides_llm_timing,
            question_requests_timing,
        )

        if question_requests_timing(q, li):
            timing = "timing" if li.get("is_timing") else "static"
        elif mr_static_overrides_llm_timing(q, li):
            timing = "static"
        else:
            timing = "static" if not li.get("is_timing") else "timing"
    except Exception:
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


def reconcile_question_type(
    question: str,
    intent: dict[str, Any] | None = None,
    *,
    mutate: bool = True,
) -> dict[str, Any]:
    """STATIC vs TIMING — deterministic gate; LLM is_timing is never final alone.

    Call after LLM intent and before routing engines / timing clarifier.
    Returns {is_timing, qtype, intent, reconciled, reasons}.
    """
    q = (question or "").strip()
    out: dict[str, Any] = dict(intent) if isinstance(intent, dict) else {}
    reasons: list[str] = []
    reconciled = False

    try:
        from ask_question_normalize import prepare_ask_question

        qn = prepare_ask_question(q)
    except Exception:
        qn = q

    try:
        from chart_fact_answer import is_domain_outcome_yoga_question

        if is_domain_outcome_yoga_question(qn):
            if out.get("is_timing"):
                reconciled = True
            out["is_timing"] = False
            reasons.append("domain_outcome_yoga_static")
    except Exception:
        pass

    try:
        from ask_health.timing_registry import health_static_overrides_llm_timing

        if health_static_overrides_llm_timing(qn, out):
            if out.get("is_timing"):
                reconciled = True
            out["is_timing"] = False
            reasons.append("health_static_override")
    except Exception:
        pass

    try:
        from ask_mr.timing_registry import (
            clear_timing_without_when_anchor,
            repair_llm_intent_mr_static_timing,
        )

        if repair_llm_intent_mr_static_timing(qn, out):
            reconciled = True
            reasons.append("mr_static_repair")
        if clear_timing_without_when_anchor(qn, out):
            reconciled = True
            reasons.append("cleared_timing_without_kab")
    except Exception:
        pass

    try:
        from ask_marriage_relationship_slice import is_marriage_relationship_static_question
        from ask_mr.timing_registry import has_explicit_timing_anchor

        if is_marriage_relationship_static_question(qn) and not has_explicit_timing_anchor(qn):
            if out.get("is_timing"):
                reconciled = True
            out["is_timing"] = False
            out["domain"] = out.get("domain") or "love"
            reasons.append("mr_promise_static")
    except Exception:
        pass

    try:
        from ask_mr.timing_registry import finalize_is_timing_flag, question_requests_timing

        wants_timing = question_requests_timing(qn, out)
        if bool(out.get("is_timing")) != wants_timing:
            reconciled = True
            reasons.append("question_requests_timing")
        out["is_timing"] = wants_timing
        is_timing = finalize_is_timing_flag(qn, wants_timing, out)
        if bool(out.get("is_timing")) != is_timing:
            reconciled = True
            out["is_timing"] = is_timing
    except Exception:
        is_timing = bool(out.get("is_timing"))

    qtype = "TIMING" if is_timing else "STATIC"
    out["question_type"] = qtype
    if reconciled:
        out["timing_reconciled"] = True
        out["timing_reconcile_reasons"] = reasons

    result = {
        "is_timing": is_timing,
        "qtype": qtype,
        "intent": out if mutate else dict(out),
        "reconciled": reconciled,
        "reasons": reasons,
    }
    if mutate and isinstance(intent, dict):
        intent.clear()
        intent.update(out)
    return result


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

    if mr_arch and not _archetype_supported(q, str(mr_arch)):
        mr_arch = None
        repaired = True

    if domain in ("marriage", "love") and not mr_arch:
        try:
            from ask_mr.classifier import classify_mr_archetype

            _cls = classify_mr_archetype(q)
            if _cls and _cls != "general_mr":
                mr_arch = _cls
                if _cls == "commitment":
                    out["routing_override"] = "commitment_classifier_raw_question"
                repaired = True
        except Exception:
            pass

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
        from ask_mr.timing_registry import (
            clear_timing_without_when_anchor,
            repair_llm_intent_mr_static_timing,
        )

        if repair_llm_intent_mr_static_timing(q, out):
            domain = str(out.get("domain") or domain)
            mr_arch = out.get("mr_archetype")
            repaired = True
        if clear_timing_without_when_anchor(q, out):
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

    try:
        reconcile_question_type(q, out, mutate=True)
        repaired = repaired or bool(out.get("timing_reconciled"))
    except Exception:
        pass

    if enforce_commitment_archetype_from_question(q, out):
        domain = str(out.get("domain") or domain)
        mr_arch = out.get("mr_archetype")
        repaired = True

    if (
        str(out.get("mr_archetype") or "").lower() == "commitment"
        and str(result.get("mr_archetype") or "").lower() in ("loyalty_trust", "loyalty", "trust")
        and not out.get("routing_override")
    ):
        out["routing_override"] = "commitment_classifier_raw_question"
        repaired = True

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
