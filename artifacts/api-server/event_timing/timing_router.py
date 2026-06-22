"""Unified timing router — domain detect + engine dispatch + user demand."""
from __future__ import annotations

import re
from typing import Any, Optional

from event_timing.domain_specs import DOMAIN_TIMING_SPECS, get_domain_spec
from event_timing.formatters import (
    format_engine_window_block,
    format_spec_directive_block,
    format_travel_block,
)
from event_timing._shared.timing_pipeline import PipelineContext, TimingDemand

# Shared timing marker (aligned with ask_question_router)
_TIMING_RX = re.compile(
    r"(?ix)\b("
    r"kab|kab\s+tak|kab\s+hoga|kab\s+hogi|kab\s+milega|kab\s+milegi|"
    r"kab\s+lagega|kab\s+lagegi|when|when\s+will|kis\s+(saal|year|mahine|month)|"
    r"kitna\s+time|time\s+lagega|muhurat|timing|dasha|transit|gochar"
    r")\b|(?:कब|कितना\s+समय)"
)

_MARRIAGE_RX = re.compile(
    r"(?ix)\b(shaadi|shadi|vivah|marriage|wedding|biwi|pati|patni)\b"
)
_MARRIAGE_EVENT_RX = re.compile(
    r"(?ix)\b("
    r"engagement|roka|sagai|"
    r"rishta\s+pakk|rishta\s+fix|rishta\s+tay|rishta\s+lag|rishta\s+final|"
    r"rishta\s+pakk[ae]\s+hona|delay\s+in\s+marriage|7th\s+house\s+marriage"
    r")\b"
)


def detect_timing_intent(question: str, llm_intent: Optional[dict] = None) -> bool:
    q = (question or "").strip()
    if not q:
        return False
    if isinstance(llm_intent, dict) and llm_intent.get("is_timing"):
        return True
    return bool(_TIMING_RX.search(q))


_STOCK_TIMING_DEFER_RX = re.compile(
    r"(?ix)\b(nifty|sensex|share[\s-]*market|stock|intraday|sip|crypto|portfolio)\b"
)


def resolve_timing_domain(
    question: str,
    llm_intent: Optional[dict] = None,
) -> tuple[str, str, bool]:
    """Return (domain, bucket, is_timing)."""
    q = (question or "").strip()
    if not q:
        return "general", "general", False

    if _STOCK_TIMING_DEFER_RX.search(q):
        return "general", "general", False

    is_timing = detect_timing_intent(q, llm_intent)
    if not is_timing:
        return "general", "general", False

    domain = "general"
    bucket = "general"

    if isinstance(llm_intent, dict):
        domain = str(llm_intent.get("domain") or "general").strip().lower()
        bucket = (
            llm_intent.get("career_archetype")
            or llm_intent.get("travel_archetype")
            or llm_intent.get("property_archetype")
            or llm_intent.get("litigation_archetype")
            or llm_intent.get("education_archetype")
            or llm_intent.get("children_archetype")
            or llm_intent.get("finance_archetype")
            or llm_intent.get("mr_archetype")
            or "general"
        )
        if isinstance(bucket, str):
            bucket = bucket.strip().lower()
        else:
            bucket = "general"

    # Priority order (specific domains before career/general foreign overlap)
    if _MARRIAGE_RX.search(q) or _MARRIAGE_EVENT_RX.search(q):
        return "marriage", "timing", True

    try:
        from ask_love.timing_registry import is_love_timing_question  # type: ignore

        if is_love_timing_question(q, llm_intent):
            dom, bkt = _love_route(q, llm_intent)
            return dom, bkt, True
    except Exception:
        pass

    try:
        from ask_children.timing_registry import is_children_timing_question  # type: ignore

        if is_children_timing_question(q, llm_intent):
            return "children", "conception", True
    except Exception:
        pass

    # Career before education/property/litigation (muhurat, interview, police job)
    try:
        from ask_career.timing_registry import is_career_timing_question  # type: ignore

        if is_career_timing_question(q, llm_intent):
            return "career", _career_bucket(q, llm_intent), True
    except Exception:
        pass

    try:
        from ask_education.timing_registry import is_education_timing_question  # type: ignore

        if is_education_timing_question(q, llm_intent):
            return "education", "exam_success", True
    except Exception:
        pass

    try:
        from ask_travel.timing_registry import is_travel_timing_question  # type: ignore

        if is_travel_timing_question(q, llm_intent):
            return "travel", _travel_bucket(q), True
    except Exception:
        pass

    try:
        from ask_property.timing_registry import is_property_timing_question  # type: ignore

        if is_property_timing_question(q, llm_intent):
            return "property", "registry", True
    except Exception:
        pass

    try:
        from ask_litigation.timing_registry import is_litigation_timing_question  # type: ignore

        if is_litigation_timing_question(q, llm_intent):
            return "litigation", _lit_bucket(q), True
    except Exception:
        pass

    # LLM domain for finance/health (no dedicated timing registry yet)
    if isinstance(llm_intent, dict):
        dom = str(llm_intent.get("domain") or "").strip().lower()
        if dom in DOMAIN_TIMING_SPECS and dom not in ("general", "career", "marriage"):
            if bool(llm_intent.get("is_timing")):
                return dom, bucket if bucket != "general" else dom, True

    if domain in DOMAIN_TIMING_SPECS:
        return domain, bucket, True

    return domain, bucket, is_timing


def _career_bucket(q: str, llm_intent: Optional[dict]) -> str:
    try:
        from ask_career.timing_registry import classify_career_timing_bucket  # type: ignore

        pre = None
        if isinstance(llm_intent, dict):
            pre = llm_intent.get("career_archetype")
        return classify_career_timing_bucket(q, pre)
    except Exception:
        return "general_career"


def _travel_bucket(q: str) -> str:
    try:
        from ask_travel.travel_registry import detect_travel_archetype  # type: ignore

        a = detect_travel_archetype(q)
        return a or "general_travel"
    except Exception:
        return "general_travel"


def _lit_bucket(q: str) -> str:
    ql = q.lower()
    if re.search(r"\bbail\b", ql):
        return "bail_theme"
    if re.search(r"\b(verdict|faisla|judgment)\b", ql):
        return "case_outcome"
    if re.search(r"\b(delay|late|adjourn)\b", ql):
        return "court_delay"
    return "general_litigation"


def _love_route(q: str, llm_intent: Optional[dict]) -> tuple[str, str]:
    if re.search(r"(?ix)\b(love\s*marriage|pyaar\s*shaadi|prem\s*vivah)\b", q):
        return "marriage", "timing"
    if isinstance(llm_intent, dict) and llm_intent.get("domain") in ("marriage", "love"):
        if _MARRIAGE_RX.search(q):
            return "marriage", "timing"
    return "love", "timing"


def build_timing_demand(
    question: str,
    llm_intent: Optional[dict] = None,
    birth: Any = None,
    kundli: Any = None,
) -> TimingDemand:
    domain, bucket, is_timing = resolve_timing_domain(question, llm_intent)
    user_age = None
    try:
        from ask_career.timing_registry import resolve_user_age  # type: ignore

        user_age = resolve_user_age(question, birth, kundli)
    except Exception:
        pass
    tense = "future"
    if re.search(r"(?ix)\b(abhi|aaj|currently|chal raha|ho raha)\b", question or ""):
        tense = "present"
    tone = "neutral"
    if isinstance(llm_intent, dict):
        tone = str(llm_intent.get("emotional_tone") or "neutral")
    wants_explain = bool((llm_intent or {}).get("wants_explain"))
    focus = str((llm_intent or {}).get("interpretation") or "")[:120]
    return TimingDemand(
        domain=domain,
        bucket=bucket,
        is_timing=is_timing,
        tense=tense,
        user_age=user_age,
        emotional_tone=tone,
        wants_explain=wants_explain,
        question_focus=focus,
    )


def run_timing_engine(
    question: str,
    kundli: dict,
    intel: dict,
    kp: dict,
    birth: Any = None,
    llm_intent: Optional[dict] = None,
) -> PipelineContext:
    """Dispatch to the best available timing engine for this question."""
    demand = build_timing_demand(question, llm_intent, birth, kundli)
    ctx = PipelineContext(
        question=question or "",
        demand=demand,
        kundli=kundli if isinstance(kundli, dict) else {},
        intel=intel or {},
        kp=kp or {},
        birth=birth,
        engine_id=demand.domain,
    )
    spec = get_domain_spec(demand.domain)
    ctx.engine_status = str(spec.get("status") or "partial")

    if not demand.is_timing:
        ctx.engine_status = "skipped_non_timing"
        ctx.verdict = "N/A — static question; timing engine not invoked"
        return ctx

    domain = demand.domain

    if domain == "career":
        try:
            from event_timing.career import assess_career, format_verdict_for_prompt  # type: ignore

            raw = assess_career(
                ctx.kundli, ctx.intel, ctx.kp, birth, question,
                pre_classified_bucket=demand.bucket,
            )
            ctx.raw = raw if isinstance(raw, dict) else {}
            ctx.verdict = str(ctx.raw.get("verdict") or "")
            ctx.confidence = int(ctx.raw.get("confidence") or 0)
            ctx.factors = list(ctx.raw.get("reasons") or [])[:8]
            ctx.engine_status = "ready"
            ctx.raw["_prompt_block"] = format_verdict_for_prompt(ctx.raw, question)
        except Exception as exc:
            ctx.engine_status = "error"
            ctx.factors.append(f"career_timing error: {exc}")

    elif domain == "travel":
        try:
            from event_timing.travel.travel_engine_v1 import compute_travel_window  # type: ignore

            raw = compute_travel_window(ctx.kundli, ctx.intel, ctx.kp, birth)
            ctx.raw = raw if isinstance(raw, dict) else {}
            ctx.verdict = str(ctx.raw.get("verdict") or "")
            ctx.factors = list(ctx.raw.get("factors") or [])[:8]
            ctx.engine_status = "ready"
            ctx.raw["_prompt_block"] = format_travel_block(ctx.raw)
            cw = ctx.raw.get("current_window") or {}
            if cw:
                ctx.windows.append(cw)
        except Exception as exc:
            ctx.engine_status = "error"
            ctx.factors.append(f"travel_timing error: {exc}")

    elif domain == "marriage":
        ctx.engine_status = "ready"
        ctx.factors.append("marriage uses dedicated _passthrough_marriage_block path")
        ctx.raw["_prompt_block"] = format_spec_directive_block(domain, spec, demand.bucket)

    elif domain == "property":
        try:
            from event_timing.property.property_timing_v1 import (  # type: ignore
                compute_property_window,
                format_property_timing_for_prompt,
            )

            raw = compute_property_window(
                ctx.kundli, ctx.intel, ctx.kp, birth, question,
                bucket=demand.bucket,
            )
            ctx.raw = raw if isinstance(raw, dict) else {}
            ctx.verdict = str(ctx.raw.get("verdict") or "")
            ctx.factors = list(ctx.raw.get("factors") or [])[:8]
            ctx.engine_status = "ready"
            ctx.raw["_prompt_block"] = format_property_timing_for_prompt(ctx.raw, question)
            cw = ctx.raw.get("current_window") or {}
            if cw:
                ctx.windows.append(cw)
        except Exception as exc:
            ctx.engine_status = "error"
            ctx.factors.append(f"property_timing error: {exc}")
            ctx.raw["_prompt_block"] = format_spec_directive_block(domain, spec, demand.bucket)

    elif domain == "education":
        try:
            from event_timing.education.education_timing_v1 import (  # type: ignore
                compute_education_window,
                format_education_timing_for_prompt,
            )

            raw = compute_education_window(
                ctx.kundli, ctx.intel, ctx.kp, birth, question,
                bucket=demand.bucket,
            )
            ctx.raw = raw if isinstance(raw, dict) else {}
            ctx.verdict = str(ctx.raw.get("verdict") or "")
            ctx.factors = list(ctx.raw.get("factors") or [])[:8]
            ctx.engine_status = "ready"
            ctx.raw["_prompt_block"] = format_education_timing_for_prompt(ctx.raw, question)
            cw = ctx.raw.get("current_window") or {}
            if cw:
                ctx.windows.append(cw)
        except Exception as exc:
            ctx.engine_status = "error"
            ctx.factors.append(f"education_timing error: {exc}")
            ctx.raw["_prompt_block"] = format_spec_directive_block(domain, spec, demand.bucket)

    elif domain == "litigation":
        try:
            from event_timing.litigation.litigation_timing_v1 import (  # type: ignore
                compute_litigation_window,
                format_litigation_timing_for_prompt,
            )

            raw = compute_litigation_window(
                ctx.kundli, ctx.intel, ctx.kp, birth, question,
                bucket=demand.bucket,
            )
            ctx.raw = raw if isinstance(raw, dict) else {}
            ctx.verdict = str(ctx.raw.get("verdict") or "")
            ctx.factors = list(ctx.raw.get("factors") or [])[:8]
            ctx.engine_status = "ready"
            ctx.raw["_prompt_block"] = format_litigation_timing_for_prompt(ctx.raw, question)
            cw = ctx.raw.get("current_window") or {}
            if cw:
                ctx.windows.append(cw)
        except Exception as exc:
            ctx.engine_status = "error"
            ctx.factors.append(f"litigation_timing error: {exc}")
            ctx.raw["_prompt_block"] = format_spec_directive_block(domain, spec, demand.bucket)

    elif domain == "love":
        try:
            from event_timing.love.love_timing_v1 import (  # type: ignore
                compute_love_window,
                format_love_timing_for_prompt,
            )

            raw = compute_love_window(
                ctx.kundli, ctx.intel, ctx.kp, birth, question,
                bucket=demand.bucket,
            )
            ctx.raw = raw if isinstance(raw, dict) else {}
            ctx.verdict = str(ctx.raw.get("verdict") or "")
            ctx.factors = list(ctx.raw.get("factors") or [])[:8]
            ctx.engine_status = "ready"
            ctx.raw["_prompt_block"] = format_love_timing_for_prompt(ctx.raw, question)
            cw = ctx.raw.get("current_window") or {}
            if cw:
                ctx.windows.append(cw)
        except Exception as exc:
            ctx.engine_status = "error"
            ctx.factors.append(f"love_timing error: {exc}")
            ctx.raw["_prompt_block"] = format_spec_directive_block(domain, spec, demand.bucket)

    elif domain == "finance":
        try:
            from event_timing.finance.finance_engine_v1 import compute_finance_window  # type: ignore

            raw = compute_finance_window(ctx.kundli, ctx.intel, ctx.kp, birth)
            ctx.raw = raw if isinstance(raw, dict) else {}
            ctx.verdict = str(ctx.raw.get("verdict") or "")
            ctx.engine_status = "ready"
            ctx.raw["_prompt_block"] = format_engine_window_block(
                ctx.raw, domain.upper(), spec.get("label", domain)
            )
            cw = ctx.raw.get("current_window") or {}
            if cw:
                ctx.windows.append(cw)
        except Exception:
            ctx.raw["_prompt_block"] = format_spec_directive_block(domain, spec, demand.bucket)

    elif domain == "health":
        try:
            from event_timing.health.health_engine_v1 import compute_health_window  # type: ignore

            raw = compute_health_window(ctx.kundli, ctx.intel, ctx.kp, birth)
            ctx.raw = raw if isinstance(raw, dict) else {}
            ctx.verdict = str(ctx.raw.get("verdict") or "")
            ctx.engine_status = "ready"
            ctx.raw["_prompt_block"] = format_engine_window_block(
                ctx.raw, domain.upper(), spec.get("label", domain)
            )
            cw = ctx.raw.get("current_window") or {}
            if cw:
                ctx.windows.append(cw)
        except Exception:
            ctx.raw["_prompt_block"] = format_spec_directive_block(domain, spec, demand.bucket)

    elif domain == "children":
        try:
            from event_timing.baby.baby_engine_v1 import compute_baby_window  # type: ignore

            raw = compute_baby_window(ctx.kundli, ctx.intel, ctx.kp, birth)
            ctx.raw = raw if isinstance(raw, dict) else {}
            ctx.verdict = str(ctx.raw.get("verdict") or "")
            ctx.engine_status = "ready"
            ctx.raw["_prompt_block"] = format_engine_window_block(
                ctx.raw, domain.upper(), spec.get("label", domain)
            )
            cw = ctx.raw.get("current_window") or {}
            if cw:
                ctx.windows.append(cw)
        except Exception:
            ctx.raw["_prompt_block"] = format_spec_directive_block(domain, spec, demand.bucket)

    else:
        ctx.engine_status = "partial"
        ctx.raw["_prompt_block"] = format_spec_directive_block(
            domain, get_domain_spec("career"), demand.bucket
        )

    return ctx


def format_timing_block(ctx: PipelineContext) -> str:
    block = (ctx.raw or {}).get("_prompt_block") or ""
    return block if isinstance(block, str) else ""
