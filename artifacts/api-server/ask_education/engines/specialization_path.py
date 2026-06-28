from __future__ import annotations

import re

from ..types import EngineResult
from ._education_base import education_snapshot, planet_line, reader


def _line_hint(q: str) -> str:
    if re.search(r"(?ix)\b(medical|mbbs|doctor|bds)\b", q):
        return "medical/health-sciences line (Mercury precision + Jupiter wisdom)"
    if re.search(r"(?ix)\b(engineer|engineering|b\.?tech)\b", q):
        return "engineering/technical line (Mercury logic + Mars application)"
    if re.search(r"(?ix)\b(law|llb|lawyer)\b", q):
        return "law/legal studies line (Mercury argument + Jupiter dharma)"
    if re.search(r"(?ix)\b(ca|chartered|account|cs\b|cma\b)\b", q):
        return "commerce/accountancy line (Mercury detail + Venus commerce)"
    if re.search(r"(?ix)\b(teach|teacher|b\.?ed)\b", q):
        return "teaching/education line (Jupiter guru-karaka + Mercury communication)"
    if re.search(r"(?ix)\b(architect|design)\b", q):
        return "architecture/design line (Venus aesthetics + Mercury planning)"
    if re.search(r"(?ix)\b(commerce|b\.?com)\b", q):
        return "commerce/business studies line (Mercury + Venus)"
    if re.search(r"(?ix)\b(science|b\.?sc|pcm|pcb)\b", q):
        return "pure/applied sciences line (Mercury + Jupiter)"
    if re.search(r"(?ix)\b(arts|humanities|b\.?a)\b", q):
        return "arts/humanities line (Moon creativity + Jupiter breadth)"
    return "specialized study line aligned to strongest karaka house"


def run_specialization_path(kundli: dict, question: str, *, wants_explain: bool = False) -> EngineResult:
    r = reader(kundli)
    hint = _line_hint(question or "")
    evidence = education_snapshot(kundli)
    evidence.append(planet_line(r, "Mercury", "specialization/intellect fit"))
    evidence.append(planet_line(r, "Jupiter", "higher-field depth fit"))
    ven = r.planet("Venus") or {}
    if ven.get("house"):
        evidence.append(planet_line(r, "Venus", "creative/commerce/arts fit"))
    verdict = f"Specialization path: {hint} — chart supports this study direction with consistent effort"
    return EngineResult(
        archetype="specialization_path",
        verdict=verdict,
        confidence="medium",
        word_budget=90 if wants_explain else 75,
        answer_plan="Name the study line asked → match to Mercury/Jupiter/Venus houses.",
        summary=["QUESTION FOCUS: medical/engineering/law/CA line as STUDY — NOT job/career outcome."],
        evidence=evidence[:8],
        ignore=["timing", "salary", "job placement"],
        checks={"slice_type": "education_engine_v1", "archetype": "specialization_path", "line_hint": hint},
    )
