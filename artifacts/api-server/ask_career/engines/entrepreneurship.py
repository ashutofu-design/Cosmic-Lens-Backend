from __future__ import annotations

import re

from ask_career.types import EngineResult
from ._career_base import inclination_evidence, load_inclination, trait_line

_BIZ_RX = [
    (re.compile(r"(?ix)\b(start\s*(up|apna\s*business)|business\s*start|startup\s*founder)\b"), "startup"),
    (re.compile(r"(?ix)\b(partnership\s*business|partner\s*ke\s*saath\s*business)\b"), "partnership"),
    (re.compile(r"(?ix)\b(solo\s*business|apna\s*akela|single\s*owner)\b"), "solo"),
    (re.compile(r"(?ix)\b(family\s*business|parivar\s*business|paitrik\s*business)\b"), "family"),
    (re.compile(r"(?ix)\b(online\s*business|e[\s-]?commerce|digital\s*business)\b"), "online"),
    (re.compile(r"(?ix)\b(trading\s*business|trader|share\s*trading)\b"), "trading"),
    (re.compile(r"(?ix)\b(consulting\s*business|consulting\s*practice)\b"), "consulting"),
    (re.compile(r"(?ix)\b(manufacturing|factory|production)\b"), "manufacturing"),
    (re.compile(r"(?ix)\b(import[\s-]?export|export\s*business)\b"), "import_export"),
    (re.compile(r"(?ix)\b(self[\s-]?employment|freelanc)\b"), "freelance"),
    (re.compile(r"(?ix)\b(business|entrepreneur|apna\s*dhandha)\b"), "general"),
]


def _mode(q: str) -> str:
    for rx, name in _BIZ_RX:
        if rx.search(q or ""):
            return name
    return "general"


def run_entrepreneurship(kundli: dict, question: str, *, wants_explain: bool = False) -> EngineResult:
    inc = load_inclination(kundli)
    mode = _mode(question or "")
    biz = int(inc.get("business_pct") or 50)
    exec_s = int(inc.get("execution_score") or 0)
    free_s = int(inc.get("freelance_score") or 0)

    evidence = inclination_evidence(inc, limit=5)
    evidence.append(trait_line(inc, "risk_appetite", high="risk comfort supports entrepreneurship", low="stable employment safer than heavy business risk"))
    evidence.append(trait_line(inc, "independence", high="independent operator fit", low="partnership/employer support helps"))

    notes = {
        "startup": "Startup fit: Mercury-Rahu/digital + execution score drives founder-style ventures.",
        "partnership": "Partnership business: Jupiter-Mercury advisory/commerce subtype — shared ventures can work with clear agreements.",
        "solo": "Solo business: high independence + execution favors single-owner setup.",
        "family": "Family business: Saturn/Sun structure + lineage duty theme — joining family trade can suit if chart supports business %.",
        "online": "Online business: Mercury-Rahu digital subtype strongly supports e-commerce/online models.",
        "trading": "Trading: Mercury-Rahu commercial axis — fast turnover fields need risk control discipline.",
        "consulting": "Consulting practice: freelance + commercial scores + Jupiter-Mercury advisory subtype.",
        "manufacturing": "Manufacturing: Mars-Saturn execution/operations subtype supports production businesses.",
        "import_export": "Import-export: Rahu foreign/commerce + Mars execution supports trade ventures.",
        "freelance": f"Freelance score {free_s}/100 — independent client-based work pattern.",
    }
    evidence.append(notes.get(mode, f"General entrepreneurship: business tilt ~{biz}%, execution {exec_s}/100."))

    fit = biz >= 48 and exec_s >= 20
    if mode == "freelance":
        fit = free_s >= 8 or biz >= 45
    verdict = f"Entrepreneurship ({mode}): {'chart supports' if fit else 'possible with planning — employment may be safer base first'}"

    return EngineResult(
        archetype="entrepreneurship",
        verdict=verdict,
        confidence="medium",
        word_budget=95 if wants_explain else 70,
        answer_plan="Direct business-type answer → 2 evidence reasons → one risk note.",
        summary=[f"QUESTION FOCUS: {mode} business/entrepreneurship."],
        evidence=evidence[:8],
        ignore=["timing", "guaranteed profit", "stock tips"],
        checks={"slice_type": "career_engine_v1", "archetype": "entrepreneurship", "mode": mode, "business_pct": biz},
    )
