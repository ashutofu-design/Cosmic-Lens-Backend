from __future__ import annotations

import re

from chart_tone_disclaimers import TAX_LEGAL_HI

from ..types import EngineResult
from ._property_base import (
    dimension_lines,
    house_axis,
    planet_line,
    property_snapshot,
    property_strength_score,
    reader,
)


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
    dim_key: str = "yog",
    ignore: list[str] | None = None,
) -> EngineResult:
    score, label = property_strength_score(kundli)
    evidence = property_snapshot(kundli)
    dims = dimension_lines(kundli)
    dim_blob = next((d for d in dims if dim_key.title() in d or dim_key in d.lower()), "")
    if dim_blob:
        evidence.append(dim_blob)
    evidence.append(f"{focus_label}: property strength index {score}/100 — {label}.")
    yog_v = ""
    try:
        from property_static.property_engine import compute_property_facts

        yog_v = ((compute_property_facts(kundli).get("dimensions") or {}).get(dim_key) or {}).get(
            "verdict", ""
        )
    except Exception:
        pass
    if yog_v == "STRONG" or score >= 68:
        verdict, confidence = verdict_strong, "high"
    elif yog_v in {"MODERATE", "CAUTION"} or score >= 52:
        verdict, confidence = verdict_mixed, "medium"
    else:
        verdict, confidence = verdict_weak, "medium"
    return EngineResult(
        archetype=archetype,
        verdict=verdict,
        confidence=confidence,
        word_budget=95 if wants_explain else 80,
        answer_plan=f"Direct answer for {archetype.replace('_', ' ')} → 4H/2H/11H + karaka evidence.",
        summary=summary_lines,
        evidence=evidence[:12],
        ignore=ignore or ["timing", "exact date", "exact price", "location guarantee"],
        checks={"slice_type": "property_engine_v1", "archetype": archetype, "property_score": score},
    )


def run_property_yog(kundli: dict, question: str, *, wants_explain: bool = False) -> EngineResult:
    return _themed_result(
        archetype="property_yog",
        kundli=kundli,
        wants_explain=wants_explain,
        focus_label="Property yog axis",
        dim_key="yog",
        verdict_strong="Property yog strong — chart supports home/land ownership with realistic planning",
        verdict_mixed="Property yog moderate — ownership possible with patience, savings and legal checks",
        verdict_weak="Property yog needs effort — foundation weak; build capacity before big purchase",
        summary_lines=[
            "QUESTION FOCUS: property/home yog — NOT when you will buy.",
            "Do NOT promise exact date or location.",
        ],
    )


def run_property_capacity(kundli: dict, question: str, *, wants_explain: bool = False) -> EngineResult:
    return _themed_result(
        archetype="property_capacity",
        kundli=kundli,
        wants_explain=wants_explain,
        focus_label="Property capacity axis",
        dim_key="capacity",
        verdict_strong="Property capacity strong — wealth flow supports buying/owning with structured plan",
        verdict_mixed="Property capacity moderate — possible with savings discipline and loan planning",
        verdict_weak="Property capacity tight now — strengthen 2H/11H wealth before major purchase",
        summary_lines=["QUESTION FOCUS: readiness/capacity — NOT exact budget figure."],
    )


def run_property_risk(kundli: dict, question: str, *, wants_explain: bool = False) -> EngineResult:
    r = reader(kundli)
    evidence = property_snapshot(kundli)
    evidence.append(planet_line(r, "Rahu", "dispute/unconventional property axis"))
    evidence.append(planet_line(r, "Saturn", "delay/legal/documentation lessons"))
    score, label = property_strength_score(kundli)
    evidence.append(f"Risk review: property strength index {score}/100 — {label}.")
    try:
        from property_static.property_engine import compute_property_facts

        risk_v = ((compute_property_facts(kundli).get("dimensions") or {}).get("risk") or {}).get(
            "verdict", "CAUTION"
        )
    except Exception:
        risk_v = "CAUTION"
    if risk_v == "HIGH_RISK":
        verdict = "Property risk high — extra legal/title verification and documentation caution essential"
    elif risk_v == "CAUTION":
        verdict = "Property risk moderate — due diligence, registry check and clear paperwork important"
    else:
        verdict = "Property risk relatively clean — still verify title and documents before deal"
    return EngineResult(
        archetype="property_risk",
        verdict=verdict,
        confidence="medium",
        word_budget=95 if wants_explain else 80,
        answer_plan="Risk answer → 4H affliction + Rahu/Saturn + risk dim.",
        summary=["QUESTION FOCUS: dispute/legal/documentation risk — NOT fear-mongering."],
        evidence=evidence[:12],
        ignore=["timing", "guarantee", "exact legal outcome"],
        checks={"slice_type": "property_engine_v1", "archetype": "property_risk"},
    )


def run_property_type_fit(kundli: dict, question: str, *, wants_explain: bool = False) -> EngineResult:
    from ._property_base import d4_lines

    evidence = property_snapshot(kundli)
    d4 = d4_lines(kundli)
    for line in d4:
        if line not in evidence:
            evidence.append(line)
    fit_line = next((d for d in dimension_lines(kundli) if d.startswith("Type fit")), "")
    if fit_line:
        evidence.append(fit_line)
    size_line = next((d for d in d4 if "property-size" in d.lower() or "size/style" in d.lower()), "")
    if size_line:
        evidence.append(f"Size/style note: use D4 Venus/Moon/Mars tone — not exact sqft.")
    try:
        from property_static.property_engine import compute_property_facts

        best = ((compute_property_facts(kundli).get("dimensions") or {}).get("type_fit") or {}).get(
            "best", "new_home"
        )
    except Exception:
        best = "new_home"
    q = (question or "").lower()
    if re.search(r"(?ix)\b(chota|bada|small|big|spacious|compact|2bhk|3bhk|4bhk)\b", q):
        verdict = (
            f"Property size/style from D4 + type-fit: {best.replace('_', ' ')} leaning — "
            "describe spacious vs compact qualitatively, no exact size guarantee"
        )
    else:
        verdict = f"Best property style from chart: {best.replace('_', ' ')} — D4 refines home type/size tone"
    return EngineResult(
        archetype="property_type_fit",
        verdict=verdict,
        confidence="medium",
        word_budget=95 if wants_explain else 80,
        answer_plan="Type/size answer → D4 Chaturthamsa + Mars/Venus/Moon + type_fit dim.",
        summary=[
            "QUESTION FOCUS: kis tarah ka ghar/chota-bada/type — NOT exact address or sqft.",
            "Use D4 Chaturthamsa for property refinement.",
        ],
        evidence=evidence[:12],
        ignore=["timing", "exact address", "exact sqft", "guaranteed type"],
        checks={"slice_type": "property_engine_v1", "archetype": "property_type_fit"},
    )


def run_property_inherit(kundli: dict, question: str, *, wants_explain: bool = False) -> EngineResult:
    r = reader(kundli)
    evidence = property_snapshot(kundli)
    evidence.append(planet_line(r, "Moon", "ancestral/family property karaka"))
    evidence.append("Inheritance axis: 8H/9H + Moon + 4H — family property theme.")
    return _themed_result(
        archetype="property_inherit",
        kundli=kundli,
        wants_explain=wants_explain,
        focus_label="Ancestral/inheritance axis",
        dim_key="yog",
        verdict_strong="Ancestral/family property support visible — inheritance/share theme possible",
        verdict_mixed="Family property theme mixed — legal share and patience both matter",
        verdict_weak="Ancestral property needs effort — family/legal clarity important",
        summary_lines=["QUESTION FOCUS: paitrik/virasat/family property — NOT legal will advice."],
    )


def run_property_dispute(kundli: dict, question: str, *, wants_explain: bool = False) -> EngineResult:
    r = reader(kundli)
    evidence = property_snapshot(kundli)
    evidence.append(planet_line(r, "Mars", "conflict/litigation tone"))
    evidence.append(planet_line(r, "Rahu", "dispute/complexity axis"))
    evidence.append("Dispute axis: 6H/8H influence on 4H — legal caution, not hopeless tone.")
    return EngineResult(
        archetype="property_dispute",
        verdict="Property dispute theme visible — chart shows friction; legal counsel + patience both needed",
        confidence="medium",
        word_budget=95 if wants_explain else 80,
        answer_plan="Dispute answer → 6H/8H on 4H + Mars/Rahu — practical legal line.",
        summary=["QUESTION FOCUS: property dispute/court — be practical, not alarmist."],
        evidence=evidence[:12],
        ignore=["timing", "guaranteed win/loss", "legal advice"],
        checks={"slice_type": "property_engine_v1", "archetype": "property_dispute"},
    )


def run_property_rent(kundli: dict, question: str, *, wants_explain: bool = False) -> EngineResult:
    r = reader(kundli)
    evidence = property_snapshot(kundli)
    evidence.append(planet_line(r, "Saturn", "rental/lease karaka"))
    evidence.append("Rental axis: 4H→11H gain link + Saturn — rental income theme.")
    return _themed_result(
        archetype="property_rent",
        kundli=kundli,
        wants_explain=wants_explain,
        focus_label="Rental income axis",
        dim_key="capacity",
        verdict_strong="Rental property theme supportive — Saturn/11H favour steady rental gains",
        verdict_mixed="Rental possible — tenant selection and contract clarity matter",
        verdict_weak="Rental needs careful planning — verify yield vs maintenance/legal load",
        summary_lines=["QUESTION FOCUS: rent out / rental income — NOT tenant name/date."],
    )


def run_property_build(kundli: dict, question: str, *, wants_explain: bool = False) -> EngineResult:
    r = reader(kundli)
    evidence = property_snapshot(kundli)
    evidence.append(planet_line(r, "Mars", "construction/build karaka"))
    evidence.append("Construction axis: Mars on 4H/4L — build timing discipline, not exact date.")
    return _themed_result(
        archetype="property_build",
        kundli=kundli,
        wants_explain=wants_explain,
        focus_label="Construction/build axis",
        dim_key="yog",
        verdict_strong="Home construction theme supportive — Mars/4H favour building with planning",
        verdict_mixed="Construction possible — cost overruns and delay caution both real",
        verdict_weak="Construction needs strong planning — stabilise budget/legal before starting",
        summary_lines=["QUESTION FOCUS: ghar banwana/construction — NOT muhurat date."],
    )


def run_property_sell(kundli: dict, question: str, *, wants_explain: bool = False) -> EngineResult:
    r = reader(kundli)
    evidence = property_snapshot(kundli)
    evidence.append(planet_line(r, "Mercury", "deal/contract axis for sale"))
    evidence.append("Sell/disposal axis: 3rd-from-4th / 12th themes — readiness + paperwork.")
    return _themed_result(
        archetype="property_sell",
        kundli=kundli,
        wants_explain=wants_explain,
        focus_label="Property sell/disposal axis",
        dim_key="capacity",
        verdict_strong="Selling/disposal theme workable — chart supports exit with clean paperwork",
        verdict_mixed="Sale possible — market timing and documentation both matter",
        verdict_weak="Sale needs patience — avoid rushed deal; verify legal clarity first",
        summary_lines=["QUESTION FOCUS: sell/dispose property — NOT exact sale date/price."],
    )


def run_property_sale_tax(kundli: dict, question: str, *, wants_explain: bool = False) -> EngineResult:
    r = reader(kundli)
    evidence = property_snapshot(kundli)
    evidence.append(planet_line(r, "Jupiter", "wealth preservation / reinvestment tone"))
    evidence.append(house_axis(r, 11, "11H sale gain axis"))
    evidence.append(house_axis(r, 2, "2H retained wealth axis"))
    score, label = property_strength_score(kundli)
    evidence.append(f"Post-sale gain tone: property index {score}/100 — {label}.")
    if score >= 68:
        verdict = (
            "Sale ke baad gain retain karne ka chart tone supportive — "
            "reinvestment planning strong; tax slabs/exemptions CA se map karein"
        )
    elif score >= 52:
        verdict = (
            "Mixed gain-retention tone — sale proceeds ko structured reinvest plan se rakhein; "
            "tax liability CA se calculate karein"
        )
    else:
        verdict = (
            "Tight gain-retention tone — pehle karz/emergency cover, phir reinvest; "
            "tax planning CA mandatory"
        )
    return EngineResult(
        archetype="property_sale_tax",
        verdict=f"{verdict} | {TAX_LEGAL_HI}",
        confidence="medium",
        word_budget=100 if wants_explain else 85,
        answer_plan="Sale proceeds tax Q → 2H/11H gain tone + CA disclaimer; NO tax-avoidance advice.",
        summary=[
            "QUESTION FOCUS: property sale ke baad tax/reinvest — chart gain-flow tone only.",
            TAX_LEGAL_HI,
        ],
        evidence=evidence[:12],
        ignore=[
            "timing",
            "exact tax amount",
            "tax evasion",
            "guaranteed zero tax",
            "section advice without CA",
        ],
        checks={"slice_type": "property_engine_v1", "archetype": "property_sale_tax"},
    )


def run_property_buy(kundli: dict, question: str, *, wants_explain: bool = False) -> EngineResult:
    return _themed_result(
        archetype="property_buy",
        kundli=kundli,
        wants_explain=wants_explain,
        focus_label="Property buy/purchase axis",
        dim_key="yog",
        verdict_strong="Buying property supported — yog + capacity tone favour purchase with due diligence",
        verdict_mixed="Purchase possible — save, verify title and plan loan realistically",
        verdict_weak="Buying now tight — build capacity and reduce risk before committing",
        summary_lines=["QUESTION FOCUS: buy/purchase readiness — NOT when to buy."],
    )


def run_property_loan(kundli: dict, question: str, *, wants_explain: bool = False) -> EngineResult:
    r = reader(kundli)
    from ._property_base import house_axis as _ha

    evidence = property_snapshot(kundli)
    evidence.append(_ha(r, 6, "Loan/debt axis (6th house)"))
    evidence.append(planet_line(r, "Saturn", "long-term loan discipline"))
    score, label = property_strength_score(kundli)
    evidence.append(f"Home-loan tone: property index {score}/100 — {label}.")
    return EngineResult(
        archetype="property_loan",
        verdict="Home loan/EMI theme: 6H burden vs 11H gain — serviceability and stable income matter most",
        confidence="medium",
        word_budget=90 if wants_explain else 75,
        answer_plan="Loan answer → 6H/11H + capacity dim — practical affordability line.",
        summary=["QUESTION FOCUS: home loan/EMI from property lens — NOT bank approval guarantee."],
        evidence=evidence[:12],
        ignore=["timing", "exact EMI", "guaranteed approval"],
        checks={"slice_type": "property_engine_v1", "archetype": "property_loan"},
    )


def run_property_land(kundli: dict, question: str, *, wants_explain: bool = False) -> EngineResult:
    r = reader(kundli)
    evidence = property_snapshot(kundli)
    evidence.append(planet_line(r, "Mars", "land/plot primary karaka"))
    evidence.append("Land/plot axis: Mars strength + 4H earth-sign tone — plot/zameen theme.")
    fit = next((d for d in dimension_lines(kundli) if "plot" in d.lower() or "Type fit" in d), "")
    if fit:
        evidence.append(fit)
    return _themed_result(
        archetype="property_land",
        kundli=kundli,
        wants_explain=wants_explain,
        focus_label="Land/plot axis",
        dim_key="yog",
        verdict_strong="Land/plot theme strong — Mars/4H favour zameen/plot acquisition with verification",
        verdict_mixed="Land/plot possible — title, survey and legal check essential",
        verdict_weak="Land/plot needs caution — verify records and avoid disputed parcels",
        summary_lines=["QUESTION FOCUS: plot/zameen/land — NOT exact location or registry date."],
    )


def run_general_property(kundli: dict, question: str, *, wants_explain: bool = False) -> EngineResult:
    score, label = property_strength_score(kundli)
    evidence = property_snapshot(kundli)
    evidence.append(f"Overall property index: {score}/100 — {label}.")
    if score >= 68:
        verdict = "Overall property chart supportive — home/land theme with realistic planning"
    elif score >= 52:
        verdict = "Overall property chart mixed — capacity + legal caution together matter"
    else:
        verdict = "Overall property chart needs groundwork — strengthen savings and reduce risk first"
    return EngineResult(
        archetype="general_property",
        verdict=verdict,
        confidence="medium",
        word_budget=95 if wants_explain else 80,
        answer_plan="Open property Q using 4H/2H/11H + yog/capacity/risk/type_fit snapshot.",
        summary=["OPEN property Q — 4H karakas + property dims only.", "No dasha dates or exact prices."],
        evidence=evidence[:12],
        ignore=["timing", "exact price", "location guarantee"],
        checks={"slice_type": "property_engine_v1", "archetype": "general_property", "property_score": score},
    )
