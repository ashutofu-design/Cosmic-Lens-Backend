"""Open chart QA — question-relevant D1 facts + LLM narrator (no wrong engine).

Policy: dedicated engine → engine facts + LLM narrator.
No engine + interpretation/combo/meaning → open_chart_qa locked facts + LLM.
Pure placement lookup only → chart_fact (no LLM).
"""

from __future__ import annotations

import re
from typing import Any

from ask_gaps_shared import TIMING_RX, house_axis, planet_line, reader
from ask_mr.types import EngineResult
from ask_question_normalize import normalize_ask_typos
from ask_universal_chart_llm import _TOPIC_FOCUS, build_topic_focus_block, infer_chart_topic

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

_HOUSE_LABELS: dict[int, str] = {
    1: "Self/vitality (1H)",
    2: "Wealth/speech (2H)",
    3: "Courage/siblings (3H)",
    4: "Home/peace (4H)",
    5: "Romance/children (5H)",
    6: "Service/obstacles (6H)",
    7: "Partnership (7H)",
    8: "Karma/transform (8H)",
    9: "Dharma/guru (9H)",
    10: "Career/status (10H)",
    11: "Gains/network (11H)",
    12: "Moksha/letting-go (12H)",
}

_INTERPRETIVE_RX = re.compile(
    r"(?ix)\b("
    r"kaise|kya|kab\s+nahi|strong|weak|yog|bhagy|suitable|possible|milta|milti|"
    r"moksha|mukti|spiritual|dharma|fame|personality|nature|swabhav|"
    r"chance|probability|tendency|pattern|affect|prabhav|impact|influence"
    r")\b"
)

_OPEN_CHART_QA_RULES = """
=== OPEN CHART QA (locked facts — anti-hallucination) ===
• Answer ONLY from LOCKED CHART FACTS in the engine block. Missing placement → say signal unclear; do NOT invent sign/house/lord/date.
• Stay on TOPIC_LOCK houses/karakas — do NOT drift (e.g. marriage/partner if user asked moksha/career).
• STATIC mode: no invented calendar years/months or dasha windows unless explicitly listed in facts.
• Translate chart lines into plain Hinglish — hide jargon in the user-facing reply.
""".strip()


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
    return False


def is_open_chart_interpretation_question(
    question: str,
    llm_intent: dict[str, Any] | None = None,
) -> bool:
    """Broader interpretive Q — no dedicated engine, not timing, not chart lookup."""
    q = normalize_ask_typos((question or "").strip())
    if not q:
        return False
    try:
        from chart_fact_answer import needs_llm_chart_answer

        if needs_llm_chart_answer(q):
            return True
    except Exception:
        pass
    if TIMING_RX.search(q):
        return False
    if isinstance(llm_intent, dict) and llm_intent.get("is_timing"):
        return False
    try:
        from chart_fact_answer import is_chart_lookup_question

        if is_chart_lookup_question(q):
            return False
    except Exception:
        pass
    if is_native_self_chart_interpretation_question(q):
        return True
    topic = infer_chart_topic(q, llm_intent)
    if topic != "general":
        return True
    if _INTERPRETIVE_RX.search(q):
        return True
    summary = str((llm_intent or {}).get("question_summary") or "").strip()
    if len(summary) >= 24:
        return True
    return False


def open_chart_qa_fallback_eligible(
    question: str,
    llm_intent: dict[str, Any] | None = None,
    *,
    qtype: str = "STATIC",
    checks: dict[str, Any] | None = None,
) -> bool:
    """Prefer locked open_chart_qa over full D1 dump when no domain engine ran."""
    if str(qtype or "").upper() == "TIMING":
        return False
    if isinstance(llm_intent, dict) and llm_intent.get("is_timing"):
        return False
    q = (question or "").strip()
    if not q:
        return False
    try:
        from chart_fact_answer import is_chart_lookup_question

        if is_chart_lookup_question(q):
            return False
    except Exception:
        pass
    try:
        from ask_hard_guards import mandatory_static_domain_detected

        if mandatory_static_domain_detected(q, llm_intent, checks or {}):
            return False
    except Exception:
        pass
    if is_open_chart_interpretation_question(q, llm_intent):
        return True
    try:
        from ask_hard_guards import controlled_llm_fallback_eligible

        return controlled_llm_fallback_eligible(
            q, llm_intent, qtype=qtype, checks=checks,
        )
    except Exception:
        return False


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


def _dasha_hint_line(kundli: dict) -> str | None:
    """One-line current dasha if present — context only, not invented timing."""
    dasha = kundli.get("dasha") or kundli.get("currentDasha") or kundli.get("vimshottari")
    if not isinstance(dasha, dict):
        return None
    md = dasha.get("mahadasha") or dasha.get("md") or dasha.get("major")
    ad = dasha.get("antardasha") or dasha.get("ad") or dasha.get("minor")
    if not md and not ad:
        return None
    parts = []
    if md:
        parts.append(f"MD {md}")
    if ad:
        parts.append(f"AD {ad}")
    return f"Current dasha (context only): {' · '.join(parts)}."


def _divisional_chart_facts(kundli: dict, question: str) -> list[str]:
    """Locked divisional lines when user names D9/D10/etc."""
    try:
        from chart_fact_answer import _detect_divisional

        varga = _detect_divisional(question or "")
        if not varga:
            return []
        div = (kundli.get("divisionalCharts") or {}).get(varga)
        if not isinstance(div, dict):
            return [f"{varga}: divisional data not in chart payload."]
        planets = div.get("planets") or []
        mentioned = _mentioned_planets(question)
        lines: list[str] = []
        asc = div.get("ascendant") or div.get("lagna")
        if asc:
            lines.append(f"{varga} lagna: {asc}.")
        if mentioned:
            for name in mentioned[:3]:
                pl = next(
                    (
                        p for p in planets
                        if isinstance(p, dict)
                        and (p.get("name") or "").lower() == name.lower()
                    ),
                    None,
                )
                if pl:
                    lines.append(
                        f"{varga}: {name} in H{pl.get('house', '?')} sign {pl.get('sign', '?')}."
                    )
        elif planets:
            for pl in planets[:4]:
                if not isinstance(pl, dict):
                    continue
                nm = pl.get("name")
                if nm:
                    lines.append(
                        f"{varga}: {nm} in H{pl.get('house', '?')} sign {pl.get('sign', '?')}."
                    )
        return lines[:5]
    except Exception:
        return []


def build_question_relevant_chart_facts(
    kundli: dict,
    question: str,
    llm_intent: dict[str, Any] | None = None,
) -> list[str]:
    """Targeted D1 lines for the question — not a full chart dump."""
    q = normalize_ask_typos((question or "").strip())
    if not kundli or not q:
        return []
    r = reader(kundli)
    facts: list[str] = []

    topic = infer_chart_topic(q, llm_intent)
    spec = _TOPIC_FOCUS.get(topic) or _TOPIC_FOCUS["general"]
    houses = list(spec["houses"])
    karakas = _mentioned_planets(q) or list(spec["karakas"])

    facts.append(build_topic_focus_block(q, llm_intent))

    asc = (kundli.get("ascendant") or "").strip()
    if asc:
        lord = r.house_lord(1)
        pl = r.planet(lord) if lord else None
        facts.append(
            f"Lagna: {asc}; lord {lord or '?'} in H"
            f"{pl.get('house') if pl else '?'} sign {pl.get('sign') if pl else '?'}."
        )

    for h in houses[:4]:
        label = _HOUSE_LABELS.get(h, f"House {h}")
        facts.append(house_axis(r, h, label))
        lord = r.house_lord(h)
        if lord:
            facts.append(planet_line(r, lord, f"{h}H lord"))

    for name in karakas[:4]:
        if name == "Lagna lord":
            lagna_lord = r.house_lord(1)
            if lagna_lord:
                facts.append(planet_line(r, lagna_lord, "Lagna lord"))
            continue
        role = "love karak" if name == "Venus" and topic == "love" else f"{topic} karaka"
        facts.append(planet_line(r, name, role))
        rules = r.houses_ruled_by(name)
        if rules:
            facts.append(f"{name} rules houses {rules} from lagna.")

    if topic == "love":
        moon = r.planet("Moon") or {}
        if moon.get("house"):
            facts.append(planet_line(r, "Moon", "emotional expression in love"))

    h_explicit = None
    try:
        from chart_fact_answer import _parse_house_num

        h_explicit = _parse_house_num(q)
    except Exception:
        pass
    if h_explicit and h_explicit not in houses:
        facts.append(house_axis(r, h_explicit, f"Asked house {h_explicit}"))
        lord = r.house_lord(h_explicit)
        if lord:
            facts.append(planet_line(r, lord, f"{h_explicit}H lord (asked)"))

    dasha_line = _dasha_hint_line(kundli)
    if dasha_line:
        facts.append(dasha_line)

    facts.extend(_divisional_chart_facts(kundli, q))

    seen: set[str] = set()
    out: list[str] = []
    for line in facts:
        if line not in seen:
            seen.add(line)
            out.append(line)
    return out[:16]


def build_open_chart_qa_llm_rules(
    question: str,
    llm_intent: dict[str, Any] | None = None,
) -> str:
    summary = ""
    if isinstance(llm_intent, dict):
        s = str(llm_intent.get("question_summary") or "").strip()
        if s:
            summary = f"\nUSER ASKED (lock): {s[:400]}\n"
    return f"{_OPEN_CHART_QA_RULES}\n{build_topic_focus_block(question, llm_intent)}{summary}"


def run_open_chart_qa(
    kundli: dict,
    question: str,
    *,
    wants_explain: bool = False,
    llm_intent: dict[str, Any] | None = None,
) -> EngineResult:
    evidence = build_question_relevant_chart_facts(
        kundli, question, llm_intent=llm_intent,
    )
    if not evidence:
        evidence = ["Chart data incomplete — answer cautiously from available factors."]
    topic = infer_chart_topic(question, llm_intent)
    return EngineResult(
        archetype="open_chart_qa",
        verdict=(
            "Open chart question — answer from question-relevant chart factors only "
            "(not a fixed engine verdict)."
        ),
        confidence="medium",
        word_budget=200 if wants_explain else 180,
        answer_plan=(
            "Read USER QUESTION → use ONLY LOCKED CHART FACTS below → "
            "clear stance + 2–3 plain reasons. No invented placements or dates."
        ),
        summary=[
            f"OPEN question ({topic}) — no dedicated engine. Use ONLY locked chart facts below.",
            "Answer the user's exact question — do not drift to unrelated life areas.",
            "If a fact is missing in the block, say unclear — never guess sign/house/lord/year.",
            "Confident pattern voice — no shayad/ho sakta hai. Plain Hinglish in reply.",
        ],
        evidence=evidence,
        ignore=[
            "invented placements",
            "invented dates or dasha windows",
            "partner traits when Q is about self",
            "unrelated topic drift",
        ],
        checks={
            "open_chart_qa": True,
            "slice_type": "open_chart_qa",
            "question_focus": "native_self",
            "chart_topic": topic,
        },
    )


def open_chart_qa_slice_meta(result: EngineResult) -> dict[str, Any]:
    pos, neg, neu = result._finalize_evidence_split()
    topic = str((result.checks or {}).get("chart_topic") or "general")
    return {
        "slice": "open_chart_qa_engine_v1",
        "topic": topic,
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


def try_open_chart_qa_for_question(
    kundli: dict,
    question: str,
    *,
    llm_intent: dict[str, Any] | None = None,
    wants_explain: bool = False,
    qtype: str = "STATIC",
    checks: dict[str, Any] | None = None,
) -> tuple[str, dict[str, Any]] | None:
    """Run open_chart_qa fallback when eligible; else None."""
    if not open_chart_qa_fallback_eligible(
        question, llm_intent, qtype=qtype, checks=checks,
    ):
        return None
    result = run_open_chart_qa(
        kundli if isinstance(kundli, dict) else {},
        question or "",
        wants_explain=wants_explain,
        llm_intent=llm_intent,
    )
    return result.to_narrator_payload(), open_chart_qa_slice_meta(result)
