"""LLM Selected JSON Blocks — question-relevant subset FROM relationship Engine Execution only.

- Source of truth: relationship_engine_execution (D1/D9)
- Never invents planets/houses outside EE
- Does NOT dump entire EE — only question-relevant keys that exist in EE
"""

from __future__ import annotations

import re
from typing import Any

_PLANET_NAMES = (
    "Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu",
)

_LOYALTY_RX = re.compile(
    r"(?ix)\b(loyal|loyalty|dhokh|cheat|affair|vishwas|trust|faithful)\b"
)
_COMMIT_RX = re.compile(
    r"(?ix)\b(commit|serious|shaadi|vivah|marriage|long.?term|stable)\b"
)
_MANGLIK_RX = re.compile(r"(?ix)\b(manglik|mangal\s*dosh|kuja)\b")
_BREAKUP_RX = re.compile(
    r"(?ix)\b(break\s*up|breakup|tod|alag|separate|separation|end\s+relationship)\b"
)
_COMM_RX = re.compile(
    r"(?ix)\b(communicat|baat|talk|message|call|samajh|misunderstand)\b"
)
_CHEM_RX = re.compile(
    r"(?ix)\b(chemistr|attraction|spark|dating|crush|romance|pyaar|prem)\b"
)
_PARTNER_RX = re.compile(
    r"(?ix)\b(partner|spouse|pati|patni|husband|wife|boyfriend|girlfriend|kaisa\s+hoga)\b"
)
_PATCH_RX = re.compile(r"(?ix)\b(patch\s*up|reconcile|wapas|return|back\s+together)\b")
_FAMILY_RX = re.compile(r"(?ix)\b(family|ghar\s*wale|parents|approval|maan\s*baap)\b")
_INTIMACY_RX = re.compile(r"(?ix)\b(intimacy|bed|physical|sex|sukha)\b")
_HOUSE_RX = re.compile(
    r"(?ix)\b(?:(?:(\d{1,2})(?:st|nd|rd|th)?)\s*(?:ghar|house)|(?:ghar|house|h)\s*(\d{1,2})|"
    r"h\s*(\d{1,2}))\b"
)
_PLANET_IN_HOUSE_RX = re.compile(
    r"(?ix)\b(Sun|Moon|Mars|Mercury|Jupiter|Venus|Saturn|Rahu|Ketu)\b"
    r".{0,40}?(?:(?:ghar|house|h)\s*(\d{1,2})|(\d{1,2})(?:st|nd|rd|th)?\s*(?:ghar|house))"
)

# routing_label / focus → preferred EE keys (must exist in EE).
_FOCUS_WANT: dict[str, dict[str, Any]] = {
    "loyalty_trust": {
        "label": "Loyalty / trust — question-relevant EE blocks",
        "lords": ("h7", "h8"),
        "houses": (7, 8, 12),
        "planets": ("Venus", "Saturn", "Moon", "Rahu"),
        "signals": ("loyalty_risk_high", "third_person_risk", "venus_afflicted", "moon_afflicted"),
        "want_keys": ("afflictions", "axes", "manglik"),
    },
    "commitment": {
        "label": "Commitment — question-relevant EE blocks",
        "lords": ("h7", "h1"),
        "houses": (7, 1),
        "planets": ("Venus", "Jupiter", "Saturn"),
        "signals": ("seventh_lord_dusthana", "seventh_lord_debil", "saturn_on_7th"),
        "want_keys": ("afflictions", "axes"),
    },
    "manglik": {
        "label": "Manglik — question-relevant EE blocks",
        "lords": ("h1", "h7"),
        "houses": (1, 4, 7, 8, 12),
        "planets": ("Mars",),
        "want_keys": ("manglik", "axes"),
    },
    "breakup_risk": {
        "label": "Breakup risk — question-relevant EE blocks",
        "lords": ("h7", "h8", "h12"),
        "houses": (7, 8, 12),
        "planets": ("Saturn", "Rahu", "Ketu", "Mars"),
        "signals": ("separation_yoga", "ketu_detachment", "seventh_lord_dusthana"),
        "want_keys": ("afflictions", "axes"),
    },
    "communication": {
        "label": "Communication — question-relevant EE blocks",
        "lords": ("h3", "h7"),
        "houses": (3, 7),
        "planets": ("Mercury", "Moon", "Venus"),
        "want_keys": ("axes", "afflictions"),
    },
    "chemistry": {
        "label": "Chemistry / dating — question-relevant EE blocks",
        "lords": ("h5", "h7"),
        "houses": (5, 7),
        "planets": ("Venus", "Mars", "Moon"),
        "signals": ("venus_mars_conjunct", "fifth_lord_weak"),
        "want_keys": ("axes",),
    },
    "dating_courtship": {
        "label": "Dating / courtship — question-relevant EE blocks",
        "lords": ("h5", "h7"),
        "houses": (5, 7),
        "planets": ("Venus", "Mars", "Moon"),
        "want_keys": ("axes",),
    },
    "one_sided_love": {
        "label": "One-sided love — question-relevant EE blocks",
        "lords": ("h5", "h12"),
        "houses": (5, 12, 7),
        "planets": ("Venus", "Moon"),
        "signals": ("fifth_lord_in_twelfth", "twelfth_lord_in_fifth", "emotional_instability"),
        "want_keys": ("axes", "afflictions"),
    },
    "emotional_attachment": {
        "label": "Emotional attachment — question-relevant EE blocks",
        "lords": ("h4", "h5", "h7"),
        "houses": (4, 5, 7),
        "planets": ("Moon", "Venus"),
        "signals": ("moon_afflicted", "moon_debil", "emotional_instability"),
        "want_keys": ("axes",),
    },
    "partner_nature": {
        "label": "Partner nature — question-relevant EE blocks",
        "lords": ("h7",),
        "houses": (7,),
        "planets": ("Venus", "Moon", "Mars", "Jupiter"),
        "want_keys": ("axes",),
    },
    "patchup": {
        "label": "Patch-up — question-relevant EE blocks",
        "lords": ("h7", "h5"),
        "houses": (7, 5, 11),
        "planets": ("Venus", "Jupiter", "Mercury"),
        "signals": ("reconnection_yoga", "separation_yoga"),
        "want_keys": ("axes",),
    },
    "family_approval": {
        "label": "Family approval — question-relevant EE blocks",
        "lords": ("h4", "h7", "h10"),
        "houses": (4, 7, 10),
        "planets": ("Moon", "Saturn", "Jupiter"),
        "want_keys": ("axes",),
    },
    "bed_intimacy": {
        "label": "Intimacy — question-relevant EE blocks",
        "lords": ("h7", "h8", "h12"),
        "houses": (7, 8, 12),
        "planets": ("Venus", "Mars", "Moon"),
        "want_keys": ("axes",),
    },
    "compatibility": {
        "label": "Compatibility — question-relevant EE blocks",
        "lords": ("h1", "h5", "h7"),
        "houses": (1, 5, 7),
        "planets": ("Venus", "Moon", "Jupiter"),
        "want_keys": ("axes", "afflictions"),
    },
    "general_mr": {
        "label": "General relationship — question-relevant EE blocks",
        "lords": ("h1", "h5", "h7"),
        "houses": (1, 5, 7, 8, 12),
        "planets": ("Venus", "Moon", "Mars", "Jupiter", "Saturn"),
        "want_keys": ("afflictions", "axes", "manglik"),
    },
}


def classify_relationship_question_focus(
    question: str,
    *,
    routing_label: str = "",
) -> str:
    # DNA routing label is boss; "sab chahiye" widens only when DNA gave no focus.
    label = (routing_label or "").strip().lower()
    if label in _FOCUS_WANT:
        return label
    try:
        from ask_selected_blocks_common import question_wants_everything

        if question_wants_everything(question or ""):
            return "general_mr"
    except Exception:
        pass
    q = (question or "").strip()
    if not q:
        return "general_mr"
    if _MANGLIK_RX.search(q):
        return "manglik"
    if _LOYALTY_RX.search(q):
        return "loyalty_trust"
    if _BREAKUP_RX.search(q):
        return "breakup_risk"
    if _PATCH_RX.search(q):
        return "patchup"
    if _COMM_RX.search(q):
        return "communication"
    if _INTIMACY_RX.search(q):
        return "bed_intimacy"
    if _FAMILY_RX.search(q):
        return "family_approval"
    if _CHEM_RX.search(q):
        return "chemistry"
    if _COMMIT_RX.search(q):
        return "commitment"
    if _PARTNER_RX.search(q):
        return "partner_nature"
    return "general_mr"


def _execution_from_meta(meta: dict[str, Any] | None) -> dict[str, Any]:
    if not isinstance(meta, dict):
        return {}
    checks = meta.get("checks") if isinstance(meta.get("checks"), dict) else {}
    pack = checks.get("relationship_engine_execution")
    if isinstance(pack, dict) and pack:
        return pack
    if meta.get("d1") or meta.get("d9"):
        return {
            "d1": meta.get("d1") or {},
            "d9": meta.get("d9") or {},
            "routing_label": meta.get("routing_label") or "",
            "relationship_signals": meta.get("relationship_signals") or {},
            "manglik": meta.get("manglik") or {},
        }
    return {
        "d1": checks.get("d1_relationship_facts") or {},
        "d9": checks.get("d9_relationship_facts") or {},
        "routing_label": checks.get("routing_label") or "",
        "relationship_signals": (
            (checks.get("relationship_engine_execution") or {}).get("relationship_signals")
            if isinstance(checks.get("relationship_engine_execution"), dict)
            else {}
        ),
    }


def _chart_ok(chart: Any) -> dict[str, Any]:
    if not isinstance(chart, dict) or chart.get("error"):
        return {}
    return chart


def _planet_house_map(execution: dict[str, Any]) -> dict[str, set[int]]:
    out: dict[str, set[int]] = {}
    for chart_key in ("d1", "d9"):
        chart = _chart_ok(execution.get(chart_key))
        for row in chart.get("planets") or []:
            if not isinstance(row, dict):
                continue
            name = str(row.get("name") or "").strip()
            house = int(row.get("house") or 0)
            if name and house:
                out.setdefault(name.lower(), set()).add(house)
    return out


def _planet_strength_detail(row: dict[str, Any]) -> tuple[str, int]:
    dignity = str(row.get("dignity") or "").strip().lower() or "?"
    score = int(row.get("strength_score") or 0)
    parts = [
        str(row.get("sign") or ""),
        f"dignity={dignity}",
        f"strength_score={score}",
    ]
    if row.get("retrograde"):
        parts.append("retrograde")
    if row.get("combust"):
        parts.append("combust")
    priority = 50 - (score * 12)
    if dignity in ("debilitated", "debility", "enemy", "fall"):
        priority += 40
    elif dignity in ("exalted", "exaltation", "own", "moolatrikona", "friend"):
        priority -= 25
    if row.get("combust"):
        priority += 15
    if row.get("retrograde"):
        priority += 8
    return " | ".join(p for p in parts if p), priority


def _lord_strength_detail(st: dict[str, Any]) -> tuple[str, int]:
    lord = str(st.get("lord") or "").strip()
    lord_h = st.get("lord_house")
    dig = str(st.get("lord_dignity") or "").strip().lower() or "?"
    score = int(st.get("lord_strength_score") or 0)
    parts = [lord]
    if lord_h:
        parts.append(f"in H{lord_h}")
    parts.append(f"dignity={dig}")
    parts.append(f"strength_score={score}")
    if st.get("lord_in_dusthana"):
        parts.append("lord_in_dusthana")
    priority = 50 - (score * 12)
    if dig in ("debilitated", "debility", "enemy", "fall"):
        priority += 40
    elif dig in ("exalted", "exaltation", "own", "moolatrikona", "friend"):
        priority -= 25
    if st.get("lord_in_dusthana"):
        priority += 30
    return " | ".join(str(p) for p in parts if p), priority


def question_relevant_blocks_from_execution(
    question: str,
    execution: dict[str, Any],
    *,
    routing_label: str = "",
) -> tuple[str, str, list[dict[str, Any]]]:
    focus = classify_relationship_question_focus(
        question,
        routing_label=routing_label or str(execution.get("routing_label") or ""),
    )
    want = _FOCUS_WANT.get(focus) or _FOCUS_WANT["general_mr"]
    label = str(want["label"])
    out: list[dict[str, Any]] = []
    seen: set[str] = set()

    def add(
        block_id: str,
        block_label: str,
        why: str,
        detail: str = "",
        *,
        priority: int = 0,
        role: str = "neutral",
    ) -> None:
        if block_id in seen:
            return
        seen.add(block_id)
        row: dict[str, Any] = {
            "id": block_id,
            "label": block_label,
            "why": why,
            "priority": int(priority),
            "role": role,
        }
        if detail:
            row["detail"] = detail
        out.append(row)

    for chart_key in ("d1", "d9"):
        chart = _chart_ok(execution.get(chart_key))
        if not chart:
            continue
        prefix = chart_key.upper()

        lords = chart.get("house_lords") if isinstance(chart.get("house_lords"), dict) else {}
        for hk in want.get("lords") or ():
            st = lords.get(hk)
            if not isinstance(st, dict):
                continue
            detail, pr = _lord_strength_detail(st)
            role = "weak" if pr >= 60 else ("strong" if pr <= 20 else "neutral")
            add(
                f"{chart_key}.house_lords.{hk}",
                f"{prefix} · {hk.upper()} lord",
                f"Question focus={focus}; lord dignity/strength from EE",
                detail,
                priority=pr + 10,
                role=role,
            )

        planets = chart.get("planets") if isinstance(chart.get("planets"), list) else []
        want_houses = set(want.get("houses") or ())
        want_planets = {str(p).lower() for p in (want.get("planets") or ())}
        for row in planets:
            if not isinstance(row, dict):
                continue
            name = str(row.get("name") or "").strip()
            house = int(row.get("house") or 0)
            if not name:
                continue
            if house in want_houses or name.lower() in want_planets:
                detail, pr = _planet_strength_detail(row)
                role = "weak" if pr >= 60 else ("strong" if pr <= 20 else "neutral")
                add(
                    f"{chart_key}.planet.{name}.H{house}",
                    f"{prefix} · {name} in H{house}",
                    f"Question focus={focus}; planet dignity/strength from EE",
                    detail,
                    priority=pr,
                    role=role,
                )

        for key in want.get("want_keys") or ():
            if key == "manglik":
                continue  # pack-level below
            val = chart.get(key)
            if val is None or val == "" or val == [] or val == {}:
                continue
            detail = ""
            pr = 40
            if key == "afflictions" and isinstance(val, list):
                detail = "; ".join(str(x) for x in val[:3])
                pr = 70
            elif key == "axes" and isinstance(val, dict):
                sev = val.get("seventh_lord") if isinstance(val.get("seventh_lord"), dict) else {}
                ven = val.get("venus") if isinstance(val.get("venus"), dict) else {}
                detail = (
                    f"7L={sev.get('lord')} H{sev.get('lord_house')} {sev.get('lord_dignity')}; "
                    f"Venus H{ven.get('house')} {ven.get('dignity')}"
                )
                pr = 65
            add(
                f"{chart_key}.{key}",
                f"{prefix} · {key}",
                f"Question focus={focus}; present in EE",
                detail,
                priority=pr,
                role="weak" if pr >= 60 else "neutral",
            )

    # Pack-level manglik + relationship_signals
    manglik = execution.get("manglik") if isinstance(execution.get("manglik"), dict) else {}
    if manglik and ("manglik" in (want.get("want_keys") or ()) or focus == "manglik"):
        add(
            "pack.manglik",
            "Manglik",
            "From EE manglik block",
            f"is_manglik={manglik.get('is_manglik')} mars_house={manglik.get('mars_house')}",
            priority=85 if manglik.get("is_manglik") else 40,
            role="weak" if manglik.get("is_manglik") else "neutral",
        )

    signals = (
        execution.get("relationship_signals")
        if isinstance(execution.get("relationship_signals"), dict)
        else {}
    )
    for sig_key in want.get("signals") or ():
        if sig_key not in signals:
            continue
        val = signals.get(sig_key)
        if val in (None, False, "", 0):
            continue
        add(
            f"pack.signal.{sig_key}",
            f"Signal · {sig_key}",
            f"Question focus={focus}; relationship_signals from EE",
            f"{sig_key}={val}",
            priority=75 if val is True else 50,
            role="weak" if val is True else "neutral",
        )

    out.sort(key=lambda b: (-int(b.get("priority") or 0), str(b.get("id") or "")))
    for i, block in enumerate(out, start=1):
        block["rank"] = i
    return focus, label, out


def format_priority_facts_for_llm(blocks: list[dict[str, Any]], *, limit: int = 5) -> str:
    """Compact ranked facts for narrator — weak / question-relevant first."""
    if not blocks:
        return ""
    lines = [
        "QUESTION_PRIORITY_FACTS (from Engine Execution only — use in this order):",
        "Rules: #1 = main reason + MUST include its natural chart proof in the answer",
        "(planet + house/dignity, e.g. Venus 7th debilitated). Max 2–3 facts total.",
        "Weak/dignity pressure > exalted support; exalted/strong = support only.",
        "Do not invent planets outside this list; do not dump every fact.",
    ]
    for b in blocks[: max(1, limit)]:
        rank = b.get("rank") or "?"
        role = b.get("role") or "neutral"
        proof_hint = ""
        if rank == 1 or rank == "1":
            proof_hint = " ← CITE THIS as proof"
        lines.append(
            f"#{rank} [{role}] {b.get('label')}: {b.get('detail') or b.get('why')}{proof_hint}"
        )
    return "\n".join(lines)


def used_blocks_from_execution(
    answer: str,
    execution: dict[str, Any],
    *,
    relevant_ids: set[str] | None = None,
) -> dict[str, Any]:
    text = (answer or "").strip()
    planet_houses = _planet_house_map(execution)
    relevant_ids = relevant_ids or set()

    planets: list[str] = []
    for name in _PLANET_NAMES:
        if re.search(rf"(?i)\b{re.escape(name)}\b", text):
            if name.lower() in planet_houses:
                planets.append(name)

    houses: list[int] = []
    for m in _HOUSE_RX.finditer(text):
        for g in m.groups():
            if g:
                try:
                    houses.append(int(g))
                except ValueError:
                    pass
    houses = sorted(set(h for h in houses if 1 <= h <= 12))

    cites: list[str] = []
    for m in _PLANET_IN_HOUSE_RX.finditer(text):
        pname = m.group(1)
        h = m.group(2) or m.group(3)
        if pname and h:
            cites.append(f"{pname} H{int(h)}")

    used_blocks: list[dict[str, str]] = []
    if cites:
        used_blocks.append({
            "id": "execution.planet_house_cites",
            "label": "Planet + house (from EE)",
            "detail": ", ".join(cites),
            "why": "Matched Engine Execution placements",
        })
    if planets and not cites:
        used_blocks.append({
            "id": "execution.planets",
            "label": "Planets named (from EE)",
            "detail": ", ".join(planets),
            "why": "Planet exists in Engine Execution",
        })
    if houses:
        used_blocks.append({
            "id": "execution.houses",
            "label": "Houses (from EE)",
            "detail": ", ".join(f"H{h}" for h in houses),
            "why": "House exists in Engine Execution",
        })
    if not used_blocks and text:
        used_blocks.append({
            "id": "execution.plain_language",
            "label": "Plain-language answer",
            "detail": "No explicit EE planet/house cite in text",
            "why": "Full EE still available to LLM",
        })

    relevant_hit = False
    for c in cites:
        m = re.match(r"(\w+)\s+H(\d+)$", c)
        if m and any(
            f".planet.{m.group(1)}.H{m.group(2)}" in rid for rid in relevant_ids
        ):
            relevant_hit = True
            break
    return {
        "planets": planets,
        "houses": houses,
        "planet_house_cites": cites,
        "blocks": used_blocks,
        "source": "relationship_engine_execution",
        "matched_question_relevant": relevant_hit,
    }


def build_relationship_selected_blocks(
    question: str,
    answer: str = "",
    *,
    meta: dict[str, Any] | None = None,
    execution: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Question-specific EE blocks only (not full EE dump) — health parallel."""
    meta = meta if isinstance(meta, dict) else {}
    pack = execution if isinstance(execution, dict) and execution else _execution_from_meta(meta)
    routing = str(
        pack.get("routing_label")
        or meta.get("routing_label")
        or (meta.get("checks") or {}).get("routing_label")
        or meta.get("archetype")
        or ""
    ).strip().lower()
    focus, focus_label, relevant = question_relevant_blocks_from_execution(
        question, pack, routing_label=routing,
    )
    _boost_applied: list[str] = []
    try:
        from ask_selected_blocks_common import dna_boost_selected_blocks

        relevant, _boost_applied = dna_boost_selected_blocks(
            question or "", relevant, meta=meta, pack=pack,
        )
    except Exception:
        pass
    used = used_blocks_from_execution(
        answer, pack, relevant_ids={b["id"] for b in relevant},
    )
    priority_text = format_priority_facts_for_llm(relevant, limit=5)

    contract: dict[str, str] = {}
    for key in ("user_wants", "intent", "normalized_question", "question_type"):
        val = str(meta.get(key) or "").strip()
        if val:
            contract[key] = val

    notes = [
        "Source: relationship Engine Execution only — dignity/strength included; ranked weak-first.",
        f"Question focus={focus}: top facts are for LLM priority reading (not full EE dump).",
        "LLM still receives full D1/D9; QUESTION_PRIORITY_FACTS tell pehle kya bolna.",
    ]
    if not relevant:
        notes.append("No matching question-relevant keys found inside Engine Execution.")

    audit = {
        "applies": True,
        "source": "relationship_engine_execution",
        "focus": focus,
        "focus_label": focus_label,
        "routing_label": routing,
        "known_focuses": sorted(_FOCUS_WANT.keys()),
        "available_blocks": relevant,
        "expected_blocks": relevant,
        "used_in_answer": used,
        "priority_facts_for_llm": priority_text,
        "overlap_notes": notes,
        "contract": contract,
        "expected_block_ids": sorted({b["id"] for b in relevant}),
        "has_d1": bool(_chart_ok(pack.get("d1"))),
        "has_d9": bool(_chart_ok(pack.get("d9"))),
        "question": (question or "").strip()[:200],
    }
    try:
        from ask_selected_blocks_common import (
            coverage_check_selected_blocks,
            coverage_note_lines,
        )

        coverage = coverage_check_selected_blocks(
            question or "",
            meta=meta,
            audit=audit,
            execution=pack,
            general_focus="general_mr",
        )
        audit["coverage"] = coverage
        from ask_selected_blocks_common import dna_boost_note_lines

        audit["overlap_notes"] = (
            coverage_note_lines(coverage) + dna_boost_note_lines(_boost_applied) + notes
        )
    except Exception:
        pass
    return audit
