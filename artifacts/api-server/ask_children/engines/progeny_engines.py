from __future__ import annotations

from ..types import EngineResult
from ._children_base import progeny_snapshot, progeny_strength_score, reader, planet_line


def _themed_result(
    *,
    archetype: str,
    kundli: dict,
    wants_explain: bool,
    focus_label: str,
    verdict_strong: str,
    verdict_mixed: str,
    verdict_weak: str,
    summary_lines: list[str],
    ignore: list[str] | None = None,
) -> EngineResult:
    score, label = progeny_strength_score(kundli)
    r = reader(kundli)
    jup = r.planet("Jupiter") or {}
    evidence = progeny_snapshot(kundli)
    evidence.append(
        f"{focus_label}: Jupiter H{jup.get('house')} (putra karaka) "
        f"+ 5H progeny axis."
    )
    evidence.append(f"Progeny strength index: {score}/100 — {label}.")
    if score >= 68:
        verdict, confidence = verdict_strong, "high"
    elif score >= 52:
        verdict, confidence = verdict_mixed, "medium"
    else:
        verdict, confidence = verdict_weak, "medium"
    return EngineResult(
        archetype=archetype,
        verdict=verdict,
        confidence=confidence,
        word_budget=90 if wants_explain else 75,
        answer_plan=f"Direct answer for {archetype.replace('_', ' ')} → 5H/Jupiter/D7 evidence.",
        summary=summary_lines,
        evidence=evidence[:8],
        ignore=ignore or ["timing", "exact child count", "guaranteed gender"],
        checks={"slice_type": "children_engine_v1", "archetype": archetype, "progeny_score": score},
    )


def run_child_promise(kundli: dict, question: str, *, wants_explain: bool = False) -> EngineResult:
    return _themed_result(
        archetype="child_promise",
        kundli=kundli,
        wants_explain=wants_explain,
        focus_label="Child promise axis",
        verdict_strong="Progeny promise strong — chart supports children/blessing with faith and steady effort",
        verdict_mixed="Progeny promise possible — chart mixed; remedies + patience matter alongside medical care if needed",
        verdict_weak="Progeny needs dedicated effort — chart shows delay/obstacle tone; specialist + remedies both important",
        summary_lines=[
            "QUESTION FOCUS: will I have children / santan yog — NOT when.",
            "Do NOT guarantee exact count or gender.",
        ],
    )


def run_fertility_conception(kundli: dict, question: str, *, wants_explain: bool = False) -> EngineResult:
    return _themed_result(
        archetype="fertility_conception",
        kundli=kundli,
        wants_explain=wants_explain,
        focus_label="Fertility/conception axis",
        verdict_strong="Conception/fertility chart supportive — IVF/natural both possible with discipline and medical guidance",
        verdict_mixed="Conception possible — chart mixed; cycle tracking + specialist consult decide path",
        verdict_weak="Conception needs structured medical support — chart shows effort-gap; do not skip specialist",
        summary_lines=[
            "QUESTION FOCUS: conceive/IVF/infertility chart tone — NOT medical diagnosis.",
            "Always say specialist/doctor consult is primary.",
        ],
        ignore=["timing", "diagnosis", "guaranteed pregnancy", "exact gender"],
    )


def run_pregnancy_wellbeing(kundli: dict, question: str, *, wants_explain: bool = False) -> EngineResult:
    return _themed_result(
        archetype="pregnancy_wellbeing",
        kundli=kundli,
        wants_explain=wants_explain,
        focus_label="Pregnancy/support axis",
        verdict_strong="Pregnancy support tone good — chart favours safe nurturing phase with care and positivity",
        verdict_mixed="Pregnancy support mixed — chart shows caution + care; follow doctor advice closely",
        verdict_weak="Pregnancy needs extra care — chart shows stress tone; medical monitoring essential",
        summary_lines=[
            "QUESTION FOCUS: pregnancy/good news/garbh tone — NOT due date.",
            "No medical diagnosis or treatment advice.",
        ],
        ignore=["timing", "due date", "diagnosis", "guaranteed outcome"],
    )


def run_child_delay(kundli: dict, question: str, *, wants_explain: bool = False) -> EngineResult:
    r = reader(kundli)
    sat = r.planet("Saturn") or {}
    evidence = progeny_snapshot(kundli)
    evidence.append(planet_line(r, "Saturn", "delay/discipline lessons in progeny"))
    evidence.append("Child delay axis: Saturn + 5H/8H patience pattern — delay not denial.")
    score, label = progeny_strength_score(kundli)
    evidence.append(f"Progeny strength index: {score}/100 — {label}.")
    sh = int(sat.get("house") or 0)
    if sh in {6, 8, 12}:
        verdict = "Child delay real but workable — chart shows late santan after patience/remedies"
    else:
        verdict = "Delay tone moderate — chart supports progeny after sustained effort"
    return EngineResult(
        archetype="child_delay",
        verdict=verdict,
        confidence="medium",
        word_budget=90 if wants_explain else 75,
        answer_plan="Acknowledge delay tone → Saturn/5H evidence → patience + remedies.",
        summary=["QUESTION FOCUS: delay in children — NOT when child comes."],
        evidence=evidence[:8],
        ignore=["timing", "exact year", "guarantee"],
        checks={"slice_type": "children_engine_v1", "archetype": "child_delay"},
    )


def run_child_gender_note(kundli: dict, question: str, *, wants_explain: bool = False) -> EngineResult:
    evidence = progeny_snapshot(kundli)
    evidence.append(
        "Gender note: classical chart cannot guarantee boy/girl — cite 5H/Jupiter tone only, stay uncertain."
    )
    score, label = progeny_strength_score(kundli)
    evidence.append(f"Progeny strength index: {score}/100 — {label}.")
    return EngineResult(
        archetype="child_gender_note",
        verdict="Gender from chart is uncertain — focus on healthy progeny promise from 5H/Jupiter, not fixed boy/girl claim",
        confidence="medium",
        word_budget=85 if wants_explain else 70,
        answer_plan="Say gender is uncertain → 5H/Jupiter progeny tone → healthy child focus.",
        summary=[
            "QUESTION FOCUS: ladka/ladki/beta/beti — NEVER guarantee gender.",
            "Say chart alone cannot confirm boy or girl reliably.",
        ],
        evidence=evidence[:8],
        ignore=["timing", "guaranteed gender", "exact sex prediction"],
        checks={"slice_type": "children_engine_v1", "archetype": "child_gender_note"},
    )


def run_number_of_children(kundli: dict, question: str, *, wants_explain: bool = False) -> EngineResult:
    evidence = progeny_snapshot(kundli)
    evidence.append(
        "Count note: do NOT invent exact number — describe progeny strength/twins possibility from 5H/11H only."
    )
    score, label = progeny_strength_score(kundli)
    evidence.append(f"Progeny strength index: {score}/100 — {label}.")
    return EngineResult(
        archetype="number_of_children",
        verdict="Child-count tone from 5H/11H — chart shows progeny potential; avoid exact number prediction",
        confidence="medium",
        word_budget=85 if wants_explain else 70,
        answer_plan="No exact count — 5H/11H qualitative tone only.",
        summary=["QUESTION FOCUS: kitne bachche/twins — NO exact count.", "Use qualitative tone only."],
        evidence=evidence[:8],
        ignore=["timing", "exact child count", "guaranteed twins"],
        checks={"slice_type": "children_engine_v1", "archetype": "number_of_children"},
    )


def run_child_nature(kundli: dict, question: str, *, wants_explain: bool = False) -> EngineResult:
    r = reader(kundli)
    evidence = progeny_snapshot(kundli)
    evidence.append(planet_line(r, "Mercury", "intellect/communication style of child"))
    evidence.append(planet_line(r, "Venus", "affection/creativity tone of child"))
    return EngineResult(
        archetype="child_nature",
        verdict="Child nature: read Mercury/Venus + 5H occupants for temperament — supportive/mixed tone",
        confidence="medium",
        word_budget=90 if wants_explain else 75,
        answer_plan="Describe child nature from 5H + Mercury/Venus — no fixed personality label.",
        summary=["QUESTION FOCUS: child nature/personality — NOT career prediction."],
        evidence=evidence[:8],
        ignore=["timing", "exact profession", "guaranteed traits"],
        checks={"slice_type": "children_engine_v1", "archetype": "child_nature"},
    )


def run_parent_child_bond(kundli: dict, question: str, *, wants_explain: bool = False) -> EngineResult:
    r = reader(kundli)
    evidence = progeny_snapshot(kundli)
    evidence.append(planet_line(r, "Moon", "emotional bond/nurture"))
    evidence.append(planet_line(r, "Venus", "affection/play bond"))
    return EngineResult(
        archetype="parent_child_bond",
        verdict="Parent-child bond tone from Moon/Venus + 5H — warm bond possible with conscious nurturing",
        confidence="medium",
        word_budget=90 if wants_explain else 75,
        answer_plan="Bond answer → Moon/Venus + 5H occupants.",
        summary=["QUESTION FOCUS: native's bond with own children — NOT spouse parenting (MR)."],
        evidence=evidence[:8],
        ignore=["timing", "blame", "guarantee"],
        checks={"slice_type": "children_engine_v1", "archetype": "parent_child_bond"},
    )


def run_child_success(kundli: dict, question: str, *, wants_explain: bool = False) -> EngineResult:
    return _themed_result(
        archetype="child_success",
        kundli=kundli,
        wants_explain=wants_explain,
        focus_label="Child future/success axis",
        verdict_strong="Child future support tone good — 5H/9H/Jupiter favour growth with guidance",
        verdict_mixed="Child future mixed — chart shows potential with mentoring and stable environment",
        verdict_weak="Child future needs active guidance — chart shows effort-gap; parental support crucial",
        summary_lines=["QUESTION FOCUS: child's future/success — NOT exact career/marks."],
    )


def run_adoption_path(kundli: dict, question: str, *, wants_explain: bool = False) -> EngineResult:
    r = reader(kundli)
    rahu = r.planet("Rahu") or {}
    evidence = progeny_snapshot(kundli)
    evidence.append(planet_line(r, "Rahu", "adoption/alternate path/unconventional family"))
    if rahu.get("house"):
        evidence.append(
            f"Adoption/alternate-path axis: Rahu H{rahu.get('house')} — unconventional family routes possible."
        )
    return EngineResult(
        archetype="adoption_path",
        verdict="Adoption/surrogacy/alternate family path possible — 5H + Rahu/Jupiter tone supports non-biological routes too",
        confidence="medium",
        word_budget=90 if wants_explain else 75,
        answer_plan="Adoption/surrogate answer → 5H + Rahu/Jupiter — legal/medical process separate.",
        summary=["QUESTION FOCUS: adoption/surrogacy/gode lena — NOT legal advice."],
        evidence=evidence[:8],
        ignore=["timing", "legal advice", "guarantee"],
        checks={"slice_type": "children_engine_v1", "archetype": "adoption_path"},
    )


def run_child_loss_concern(kundli: dict, question: str, *, wants_explain: bool = False) -> EngineResult:
    r = reader(kundli)
    evidence = progeny_snapshot(kundli)
    evidence.append(planet_line(r, "Saturn", "grief/patience lessons"))
    evidence.append(planet_line(r, "Ketu", "spiritual/detachment axis in loss themes"))
    return EngineResult(
        archetype="child_loss_concern",
        verdict="Loss/miscarriage concern acknowledged — chart shows recovery hope with care, faith and medical support",
        confidence="medium",
        word_budget=95 if wants_explain else 80,
        answer_plan="Sensitive tone → acknowledge fear → 5H/Jupiter hope → medical care.",
        summary=[
            "QUESTION FOCUS: miscarriage/loss fear — be gentle.",
            "No blame; encourage medical and emotional support.",
        ],
        evidence=evidence[:8],
        ignore=["timing", "blame", "guarantee", "death"],
        checks={"slice_type": "children_engine_v1", "archetype": "child_loss_concern", "sensitive": True},
    )


def run_progeny_obstacles(kundli: dict, question: str, *, wants_explain: bool = False) -> EngineResult:
    r = reader(kundli)
    sat = r.planet("Saturn") or {}
    evidence = progeny_snapshot(kundli)
    evidence.append("Progeny obstacle axis: 5H affliction + Saturn delay lessons — obstacle not final denial.")
    evidence.append(planet_line(r, "Saturn", "karma/delay in santan"))
    sh = int(sat.get("house") or 0)
    if sh in {6, 8, 12}:
        verdict = "Progeny obstacles real — chart shows remedies, patience and specialist path both needed"
    else:
        verdict = "Progeny obstacles workable — chart supports breakthrough after sustained effort"
    return EngineResult(
        archetype="progeny_obstacles",
        verdict=verdict,
        confidence="medium",
        word_budget=90 if wants_explain else 75,
        answer_plan="Obstacle/backlog tone → Saturn/5H → remedies + hope.",
        summary=["QUESTION FOCUS: nisantan/obstacle/dosh — NOT hopeless tone."],
        evidence=evidence[:8],
        ignore=["timing", "hopeless", "curse certainty"],
        checks={"slice_type": "children_engine_v1", "archetype": "progeny_obstacles"},
    )


def run_general_children(kundli: dict, question: str, *, wants_explain: bool = False) -> EngineResult:
    score, label = progeny_strength_score(kundli)
    evidence = progeny_snapshot(kundli)
    evidence.append(f"Overall progeny index: {score}/100 — {label}.")
    if score >= 68:
        verdict = "Overall children/progeny chart supportive — blessing tone with realistic patience"
    elif score >= 52:
        verdict = "Overall children chart mixed — faith, remedies and practical steps together matter"
    else:
        verdict = "Overall children chart needs effort layer — specialist + spiritual support both help"
    return EngineResult(
        archetype="general_children",
        verdict=verdict,
        confidence="medium",
        word_budget=90 if wants_explain else 75,
        answer_plan="Answer the children Q using 5H/9H/Jupiter/D7 snapshot.",
        summary=["OPEN children Q — 5H/Jupiter/D7 only.", "No dasha dates or exact counts."],
        evidence=evidence[:8],
        ignore=["timing", "exact count", "guaranteed gender"],
        checks={"slice_type": "children_engine_v1", "archetype": "general_children", "progeny_score": score},
    )
