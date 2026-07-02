"""Open chart QA — question-relevant D1 facts + LLM narrator (no wrong engine)."""

from __future__ import annotations

import re
from typing import Any

from ask_gaps_shared import house_axis, planet_line, reader
from ask_mr.types import EngineResult
from ask_question_normalize import normalize_ask_typos

_NATIVE_SELF_RX = re.compile(
    r"(?ix)\b(mer[eiay]?|mujh|main|apn[aei]|my|i\s+)\b"
)
_PARTNER_SUBJECT_RX = re.compile(
    r"(?ix)\b(partner|spouse|wife|husband|pati|pati\b|patni|biwi|"
    r"boyfriend|girlfriend|shaadi\s*ke\s*baad|after\s*marriage|"
    r"mera\s*partner|meri\s*(?:wife|husband|biwi|pati|patni))\b"
)
_PLANET_RX = re.compile(
    r"(?ix)\b(sun|surya|moon|chandra|mars|mangal|mercury|budh|"
    r"jupiter|guru|venus|shukra|saturn|shani|sani|rahu|ketu)\b"
)
_PLANET_CANON: dict[str, str] = {
    "sun": "Sun",
    "surya": "Sun",
    "moon": "Moon",
    "chandra": "Moon",
    "mars": "Mars",
    "mangal": "Mars",
    "mercury": "Mercury",
    "budh": "Mercury",
    "jupiter": "Jupiter",
    "guru": "Jupiter",
    "venus": "Venus",
    "shukra": "Venus",
    "saturn": "Saturn",
    "shani": "Saturn",
    "sani": "Saturn",
    "rahu": "Rahu",
    "ketu": "Ketu",
}


def is_native_self_chart_interpretation_question(question: str) -> bool:
    """Placement/affect on native self — not partner/spouse subject."""
    q = normalize_ask_typos((question or "").strip())
    if not q:
        return False
    try:
        from chart_fact_answer import is_domain_life_area_interpretation_question

        if not is_domain_life_area_interpretation_question(q):
            return False
    except Exception:
        return False
    if _PARTNER_SUBJECT_RX.search(q):
        return False
    if _NATIVE_SELF_RX.search(q):
        return True
    if re.search(r"(?ix)\b(love\s*style|love\s*language|affection\s*style)\b", q):
        return True
    if re.search(r"(?ix)\b(mera|meri|mere)\b", q):
        return True
    return True


def should_use_open_chart_qa(
    question: str,
    llm_intent: dict[str, Any] | None = None,
) -> bool:
    q = (question or "").strip()
    if not q:
        return False
    if isinstance(llm_intent, dict) and llm_intent.get("open_chart_qa"):
        return True
    arch = str(
        llm_intent.get("mr_archetype") or llm_intent.get("routed_archetype") or ""
    ).strip().lower() if isinstance(llm_intent, dict) else ""
    if arch == "open_chart_qa":
        return True
    return is_native_self_chart_interpretation_question(q)


def _mentioned_planets(q: str) -> list[str]:
    found: list[str] = []
    for m in _PLANET_RX.finditer(q or ""):
        canon = _PLANET_CANON.get((m.group(0) or "").lower())
        if canon and canon not in found:
            found.append(canon)
    return found


def _topic_context(q: str) -> tuple[str, list[int], list[str]]:
    """Return (topic_label, extra_houses, default_planets)."""
    ql = (q or "").lower()
    if re.search(r"(?ix)\b(love|pyaar|pyar|prem|affection|romance|rishta)\b", ql):
        planets = _mentioned_planets(q) or ["Venus"]
        houses = [5]
        if "venus" not in ql and "shukra" not in ql:
            houses.append(7)
        return "love_style", houses, planets
    if re.search(r"(?ix)\b(career|naukri|job|kaam)\b", ql):
        return "career", [10, 6], _mentioned_planets(q) or ["Saturn", "Sun"]
    if re.search(r"(?ix)\b(wealth|dhan|paisa|money|finance)\b", ql):
        return "finance", [2, 11], _mentioned_planets(q) or ["Jupiter", "Venus"]
    if re.search(r"(?ix)\b(health|swasth|bimari)\b", ql):
        return "health", [1, 6, 8], _mentioned_planets(q) or ["Moon", "Saturn"]
    return "general", [], _mentioned_planets(q)


def build_question_relevant_chart_facts(kundli: dict, question: str) -> list[str]:
    """Targeted D1 lines for the question — not a full chart dump."""
    q = normalize_ask_typos((question or "").strip())
    if not kundli or not q:
        return []
    r = reader(kundli)
    facts: list[str] = []

    asc = (kundli.get("ascendant") or "").strip()
    if asc:
        lord = r.house_lord(1)
        pl = r.planet(lord) if lord else None
        facts.append(
            f"Lagna: {asc}; lord {lord or '?'} in H"
            f"{pl.get('house') if pl else '?'} sign {pl.get('sign') if pl else '?'}."
        )

    topic, houses, planets = _topic_context(q)
    for name in planets[:4]:
        role = "love karak" if name == "Venus" and topic == "love_style" else "queried planet"
        facts.append(planet_line(r, name, role))
        rules = r.houses_ruled_by(name)
        if rules:
            facts.append(f"{name} rules houses {rules} from lagna.")

    if topic == "love_style":
        moon = r.planet("Moon") or {}
        if moon.get("house"):
            facts.append(
                planet_line(r, "Moon", "emotional expression in love")
            )

    for h in houses[:3]:
        label = {5: "Romance/love expression (5H)", 7: "Partnership house (7H)"}.get(
            h, f"House {h}"
        )
        facts.append(house_axis(r, h, label))

    h_explicit = None
    try:
        from chart_fact_answer import _parse_house_num

        h_explicit = _parse_house_num(q)
    except Exception:
        pass
    if h_explicit and h_explicit not in houses:
        facts.append(house_axis(r, h_explicit, f"Asked house {h_explicit}"))

    seen: set[str] = set()
    out: list[str] = []
    for line in facts:
        if line not in seen:
            seen.add(line)
            out.append(line)
    return out[:10]


def run_open_chart_qa(
    kundli: dict,
    question: str,
    *,
    wants_explain: bool = False,
) -> EngineResult:
    evidence = build_question_relevant_chart_facts(kundli, question)
    if not evidence:
        evidence = ["Chart data incomplete — answer cautiously from available factors."]
    return EngineResult(
        archetype="open_chart_qa",
        verdict=(
            "Open chart question — answer from question-relevant chart factors only "
            "(not a fixed engine verdict)."
        ),
        confidence="medium",
        word_budget=200 if wants_explain else 180,
        answer_plan=(
            "Read USER QUESTION → pick only matching chart facts → "
            "clear stance + 1–2 plain reasons. No generic marriage/partner summary."
        ),
        summary=[
            "OPEN question — no dedicated engine. Use ONLY chart facts relevant to what was asked.",
            "Answer the native's exact question (self-focus when question is about user).",
            "Confident pattern voice — no shayad/ho sakta hai. Plain language in reply.",
        ],
        evidence=evidence,
        ignore=["invented placements", "exact dates", "partner traits when Q is about self"],
        checks={
            "open_chart_qa": True,
            "slice_type": "open_chart_qa",
            "question_focus": "native_self",
        },
    )


def open_chart_qa_slice_meta(result: EngineResult) -> dict[str, Any]:
    pos, neg, neu = result._finalize_evidence_split()
    return {
        "slice": "open_chart_qa_engine_v1",
        "topic": "chart_interpretation",
        "archetype": result.archetype,
        "verdict": result.verdict,
        "summary": list(result.summary or []),
        "evidence": list(result.evidence or []),
        "evidence_positive": pos,
        "evidence_negative": neg,
        "evidence_neutral": neu,
        "ignore": list(result.ignore or []),
        "checks": dict(result.checks or {}),
        "skip_llm": False,
        "word_budget": int(result.word_budget or 60),
        "narrator_mode": "open_chart_qa",
    }
