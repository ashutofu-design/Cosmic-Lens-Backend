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
    r"kab\s+lagega|kab\s+lagegi|when|when\s+will|kis\s+(?:specific\s+)?(?:date|week|saal|year|mahine|month)|"
    r"kitna\s+time|time\s+lagega|muhurat|timing|"
    r"dasha|antardasha|mahadasha|pratyantar|transit|gochar|"
    r"milega|milegi|hoga|hogi|aayega|aayegi|banega|banegi|"
    r"pahuchegi|lagenge|talegi|rukhega|rukhegi|"
    r"pass\s+ho|ho\s+jayega|"
    r"padega|padegi|paunga|paungi|jaunga|jaungi|jayega|jayegi|jayenge|"
    r"ban\s+raha|ban\s+rahi|mil\s+jayega|ho\s+jayega|ho\s+jaunga|"
    r"delay|dikh\s+raha|dikhayega|confirmed\s+period|safest.*period|"
    r"\bweek\b|\bdate\b|"
    r"vakri|retrograde|chance\s+milega"
    r")\b|(?:कब|कितना\s+समय)"
)

_MARRIAGE_RX = re.compile(
    r"(?ix)\b(shaadi|shadi|vivah|marriage|wedding|biwi|pati|patni)\b"
)
_MARRIAGE_EVENT_RX = re.compile(
    r"(?ix)\b("
    r"engagement|roka|sagai|mangni|mangetar|"
    r"rishta\s+pakk\w*|rishta\s+fix|rishta\s+tay|rishta\s+lag|rishta\s+final|"
    r"rishta\s+pakk[ae]\s+hona|delay\s+in\s+marriage|7th\s+house\s+marriage"
    r")\b"
)

# "Biwi kaisi hogi?" / "travel yog strong hai?" — quality/static, not WHEN.
_EXPLICIT_TIMING_RX = re.compile(
    r"(?ix)\b("
    r"kab|kab\s+tak|kab\s+se|when|when\s+will|kis\s+(?:specific\s+)?(?:date|week|saal|year|mahine|month|turning\s+point)|"
    r"kis\s+dasha|dasha\s+me|kitna\s+time|time\s+lagega|muhurat|timing|"
    r"kitne\s+mahine|dasha|antardasha|mahadasha|pratyantar|transit|gochar|"
    r"trigger\s+hoga|approve\s+hoga|prapt\s+hogi|active\s+honge|shuru\s+honge"
    r")\b|(?:कब|कितना\s+समय)"
)
_STATIC_QUALITY_RX = re.compile(
    r"(?ix)\b("
    r"kaisi|kaisa|kesi|kesa|kese|kaise|kya\s+tarah|kis\s+tarah|"
    r"nature|character|personality|appearance|height|colour|color|"
    r"strong\s+hai|best\s+rahegi|suit\s+karega|possible\s+hai|yog\s+strong"
    r")\b"
)


def detect_timing_intent(question: str, llm_intent: Optional[dict] = None) -> bool:
    q = (question or "").strip()
    if not q:
        return False
    try:
        from ask_love.timing_registry import is_love_timing_question, llm_says_love_timing

        if llm_says_love_timing(llm_intent):
            return True
        if is_love_timing_question(q, llm_intent):
            return True
    except Exception:
        pass
    try:
        from ask_travel.timing_registry import is_travel_timing_question, llm_says_travel_timing

        if llm_says_travel_timing(llm_intent):
            return True
        if is_travel_timing_question(q, llm_intent):
            return True
    except Exception:
        pass
    try:
        from ask_property.timing_registry import is_property_timing_question, llm_says_property_timing

        if llm_says_property_timing(llm_intent):
            return True
        if is_property_timing_question(q, llm_intent):
            return True
    except Exception:
        pass
    if isinstance(llm_intent, dict) and llm_intent.get("is_timing"):
        return True
    if re.search(r"(?ix)\bkya\b", q) and not _EXPLICIT_TIMING_RX.search(q):
        return False
    if _STATIC_QUALITY_RX.search(q) and not _EXPLICIT_TIMING_RX.search(q):
        return False
    return bool(_TIMING_RX.search(q))


_STOCK_TIMING_DEFER_RX = re.compile(
    r"(?ix)\b(nifty|sensex|share[\s-]*market|stock|intraday|sip|crypto|portfolio)\b"
)


def resolve_timing_domain(
    question: str,
    llm_intent: Optional[dict] = None,
) -> tuple[str, str, bool]:
    """Return (domain, bucket, is_timing)."""
    try:
        from ask_question_normalize import prepare_ask_question

        q = prepare_ask_question((question or "").strip())
    except Exception:
        q = (question or "").strip()
    if not q:
        return "general", "general", False

    if _STOCK_TIMING_DEFER_RX.search(q):
        return "general", "general", False

    # Narrow topic guards before broad registries (foreign/finance/career words
    # overlap heavily). These remain timing-only and fall back to the universal
    # atlas when there is no dedicated domain engine.
    if detect_timing_intent(q, llm_intent):
        if re.search(
            r"(?ix)\b(foreign|abroad|videsh|overseas)\b.{0,30}\b("
            r"settle|settlement|shift|move|pr|green\s*card)\b",
            q,
        ):
            return "travel", _travel_bucket(q), True
        if re.search(r"(?ix)\b(teerth\s*yatra|teerthyatra|tirth\s*yatra|pilgrimage)\b", q):
            try:
                from ask_spiritual.timing_registry import classify_spiritual_timing_bucket

                return "spiritual", classify_spiritual_timing_bucket(q), True
            except Exception:
                return "spiritual", "pilgrimage", True
        if re.search(
            r"(?ix)\b(bade\s+log|influential|powerful\s+(?:people|person)|"
            r"senior\s+contact)\b.{0,35}\b(help|support|madad|connect)\b",
            f"{q} {question or ''}",
        ):
            try:
                from ask_network.timing_registry import classify_network_timing_bucket

                return "network", classify_network_timing_bucket(q), True
            except Exception:
                return "network", "influential_support", True
        if re.search(
            r"(?ix)\b(lottery|jackpot|pet\s+(?:dog|cat)?\s*.*adopt|"
            r"dog\s+kab\s+adopt|cat\s+kab\s+adopt)\b",
            q,
        ):
            from event_timing.universal.topic_atlas import classify_universal_bucket

            return "universal", classify_universal_bucket(q), True

    if _MARRIAGE_EVENT_RX.search(q) and detect_timing_intent(q, llm_intent):
        return "marriage", "timing", True

    # Love timing first — any phrasing/length; LLM love+timing or regex match.
    try:
        from ask_love.timing_registry import is_love_timing_question  # type: ignore

        if is_love_timing_question(q, llm_intent):
            dom, bkt = _love_route(q, llm_intent)
            return dom, bkt, True
    except Exception:
        pass

    try:
        from ask_spiritual.timing_registry import (  # type: ignore
            classify_spiritual_timing_bucket,
            is_spiritual_timing_question,
        )

        if is_spiritual_timing_question(q, llm_intent):
            return "spiritual", classify_spiritual_timing_bucket(q), True
    except Exception:
        pass

    try:
        from ask_fame.timing_registry import (  # type: ignore
            classify_fame_timing_bucket,
            is_fame_timing_question,
        )

        if is_fame_timing_question(q, llm_intent):
            return "fame", classify_fame_timing_bucket(q), True
    except Exception:
        pass

    try:
        from ask_network.timing_registry import (  # type: ignore
            classify_network_timing_bucket,
            is_network_timing_question,
        )

        if is_network_timing_question(q, llm_intent):
            return "network", classify_network_timing_bucket(q), True
    except Exception:
        pass

    try:
        from ask_litigation.timing_registry import (  # type: ignore
            classify_litigation_timing_bucket,
            is_litigation_timing_question,
        )

        if is_litigation_timing_question(q, llm_intent):
            return "litigation", classify_litigation_timing_bucket(q), True
    except Exception:
        pass

    # Foreign edu / visa / PR — includes yoga-only timing (before global is_timing gate)
    try:
        from ask_foreign_education.timing_registry import (  # type: ignore
            classify_foreign_education_bucket,
            is_foreign_education_timing_question,
        )

        if is_foreign_education_timing_question(q, llm_intent):
            return "foreign_education", classify_foreign_education_bucket(q), True
    except Exception:
        pass

    try:
        from ask_health.timing_registry import (  # type: ignore
            classify_health_timing_bucket,
            is_health_timing_question,
        )

        if is_health_timing_question(q, llm_intent):
            return "health", classify_health_timing_bucket(q), True
    except Exception:
        pass

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
    _love_commitment_rx = re.compile(
        r"(?ix)"
        r"\b(commitment|haan\s+kab|propose|proposal)\b.{0,40}\b(shaadi|marriage)\b|"
        r"\b(shaadi|marriage)\b.{0,20}\b(haan|commitment|propose)\b",
    )
    if (_MARRIAGE_RX.search(q) or _MARRIAGE_EVENT_RX.search(q)) and not _love_commitment_rx.search(q):
        if not re.search(
            r"(?ix)\b(pr\b|green\s+card|visa|settlement|foreign|videsh|abroad|overseas)\b", q
        ):
            return "marriage", "timing", True

    try:
        from ask_children.timing_registry import is_children_timing_question  # type: ignore

        if is_children_timing_question(q, llm_intent):
            return "children", "conception", True
    except Exception:
        pass

    # Education/travel/finance before career (career core overlaps exam/videsh/paisa)
    try:
        from ask_education.timing_registry import is_education_timing_question  # type: ignore

        if is_education_timing_question(q, llm_intent):
            from event_timing.education.education_timing_v1 import classify_education_timing_bucket

            return "education", classify_education_timing_bucket(q), True
    except Exception:
        pass

    try:
        from ask_travel.timing_registry import is_travel_timing_question  # type: ignore
        from ask_travel.timing_registry import classify_travel_timing_bucket  # type: ignore

        if is_travel_timing_question(q, llm_intent):
            return "travel", classify_travel_timing_bucket(q), True
    except Exception:
        pass

    try:
        from ask_vehicle.timing_registry import is_vehicle_timing_question  # type: ignore

        if is_vehicle_timing_question(q, llm_intent):
            from event_timing.vehicle.vehicle_timing_v1 import classify_vehicle_timing_bucket
            return "vehicle", classify_vehicle_timing_bucket(q), True
    except Exception:
        pass

    try:
        from ask_property.timing_registry import is_property_timing_question  # type: ignore

        if is_property_timing_question(q, llm_intent):
            from event_timing.property.property_timing_v1 import classify_property_timing_bucket
            return "property", classify_property_timing_bucket(q), True
    except Exception:
        pass

    try:
        from ask_finance.timing_registry import is_finance_timing_question  # type: ignore

        if is_finance_timing_question(q, llm_intent):
            return "finance", "general_finance", True
    except Exception:
        pass

    try:
        from ask_litigation.timing_registry import is_litigation_timing_question  # type: ignore

        if is_litigation_timing_question(q, llm_intent):
            return "litigation", _lit_bucket(q), True
    except Exception:
        pass

    try:
        from ask_career.timing_registry import is_career_timing_question  # type: ignore

        if is_career_timing_question(q, llm_intent):
            return "career", _career_bucket(q, llm_intent), True
    except Exception:
        pass

    # property/finance/career/litigation reordered above — removed duplicate blocks below

    # LLM love timing last resort before universal fallback.
    try:
        from ask_love.timing_registry import is_love_timing_question

        if is_love_timing_question(q, llm_intent):
            dom, bkt = _love_route(q, llm_intent)
            return dom, bkt, True
    except Exception:
        pass

    if is_timing:
        from event_timing.universal.topic_atlas import classify_universal_bucket  # type: ignore

        return "universal", classify_universal_bucket(q), True

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
    try:
        from event_timing.litigation.litigation_timing_v1 import classify_litigation_timing_bucket

        return classify_litigation_timing_bucket(q)
    except Exception:
        pass
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

    if domain == "marriage":
        ctx.engine_status = "ready"
        ctx.factors.append("marriage uses dedicated _passthrough_marriage_block path")
        ctx.raw["_prompt_block"] = format_spec_directive_block(domain, spec, demand.bucket)

    elif domain == "love":
        try:
            from event_timing.love.love_timing_engine_v1 import (  # type: ignore
                assess_love_timing,
                classify_love_timing_bucket,
            )
            from event_timing.love.love_timing_v1 import format_love_timing_for_prompt

            pre_bucket = demand.bucket
            if pre_bucket in ("timing", "general", "dating_courtship"):
                pre_bucket = None
            bucket = classify_love_timing_bucket(question, pre_bucket)
            raw = assess_love_timing(
                ctx.kundli,
                ctx.intel,
                ctx.kp,
                ctx.birth,
                question,
                bucket=bucket,
                user_age=demand.user_age,
            )
            ctx.raw = raw if isinstance(raw, dict) else {}
            ctx.verdict = str(ctx.raw.get("verdict") or "")
            ctx.factors = list(ctx.raw.get("factors") or ctx.raw.get("reasons") or [])[:12]
            ctx.engine_status = "ready"
            ctx.engine_id = "love_timing_v1"
            ctx.raw["_prompt_block"] = format_love_timing_for_prompt(ctx.raw, question)
            cw = ctx.raw.get("current_window") or ctx.raw.get("timing_window") or {}
            if cw:
                ctx.windows.append(cw)
        except Exception as exc:
            ctx.engine_status = "error"
            ctx.factors.append(f"love_timing_engine_v1 error: {exc}")
            ctx.raw["_prompt_block"] = format_spec_directive_block(domain, spec, demand.bucket)

    elif domain == "travel":
        try:
            from ask_travel.timing_registry import classify_travel_timing_bucket
            from event_timing.formatters import format_travel_block
            from event_timing.travel.travel_engine_v1 import compute_travel_window

            bucket = classify_travel_timing_bucket(question)
            if demand.bucket and demand.bucket not in ("timing", "general"):
                bucket = demand.bucket
            raw = compute_travel_window(
                ctx.kundli,
                ctx.intel,
                ctx.kp,
                ctx.birth,
            )
            ctx.raw = raw if isinstance(raw, dict) else {}
            ctx.raw["bucket"] = bucket
            ctx.raw["domain"] = "travel"
            ctx.verdict = str(ctx.raw.get("verdict") or "")
            ctx.factors = list(ctx.raw.get("factors") or ctx.raw.get("reasons") or [])[:12]
            verdict = str(ctx.raw.get("verdict") or "").upper()
            ctx.engine_status = "ready" if verdict and verdict != "UNKNOWN" else "partial"
            ctx.engine_id = "travel_timing_v1"
            ctx.raw["_prompt_block"] = format_travel_block(ctx.raw)
            cw = ctx.raw.get("current_window") or {}
            if cw:
                ctx.windows.append(cw)
        except Exception as exc:
            ctx.engine_status = "error"
            ctx.factors.append(f"travel_timing_engine_v1 error: {exc}")
            ctx.raw["_prompt_block"] = format_spec_directive_block(domain, spec, demand.bucket)

    elif domain == "property":
        try:
            from event_timing.property.property_timing_v1 import (
                classify_property_timing_bucket,
                compute_property_window,
                format_property_timing_for_prompt,
            )

            bucket = classify_property_timing_bucket(question)
            if demand.bucket and demand.bucket not in ("timing", "general"):
                bucket = demand.bucket
            raw = compute_property_window(
                ctx.kundli,
                ctx.intel,
                ctx.kp,
                ctx.birth,
                question,
                bucket=bucket,
            )
            ctx.raw = raw if isinstance(raw, dict) else {}
            ctx.raw["bucket"] = bucket
            ctx.raw["domain"] = "property"
            ctx.verdict = str(ctx.raw.get("verdict") or "")
            ctx.factors = list(ctx.raw.get("factors") or [])[:12]
            verdict = str(ctx.raw.get("verdict") or "").upper()
            ctx.engine_status = "ready" if verdict and verdict != "UNKNOWN" else "partial"
            ctx.engine_id = "property_timing_v1"
            ctx.raw["_prompt_block"] = format_property_timing_for_prompt(ctx.raw, question)
            cw = ctx.raw.get("answer_window") or ctx.raw.get("current_window") or {}
            if cw:
                ctx.windows.append(cw)
        except Exception as exc:
            ctx.engine_status = "error"
            ctx.factors.append(f"property_timing_engine_v1 error: {exc}")
            ctx.raw["_prompt_block"] = format_spec_directive_block(domain, spec, demand.bucket)

    elif domain == "children":
        try:
            from event_timing.baby.baby_engine_v1 import compute_baby_window
            from event_timing.formatters import format_baby_timing_for_prompt

            raw = compute_baby_window(
                ctx.kundli,
                ctx.intel,
                ctx.kp,
                ctx.birth,
            )
            ctx.raw = raw if isinstance(raw, dict) else {}
            ctx.raw["bucket"] = demand.bucket or "conception"
            ctx.raw["domain"] = "children"
            ctx.verdict = str(ctx.raw.get("verdict") or "")
            ctx.factors = list(ctx.raw.get("factors") or [])[:12]
            verdict = str(ctx.raw.get("verdict") or "").upper()
            ctx.engine_status = "ready" if verdict and verdict != "UNKNOWN" else "partial"
            ctx.engine_id = "children_timing_v1"
            ctx.raw["_prompt_block"] = format_baby_timing_for_prompt(ctx.raw, question)
            cw = (
                ctx.raw.get("next_child_window")
                or ctx.raw.get("current_window")
                or {}
            )
            if cw:
                ctx.windows.append(cw)
        except Exception as exc:
            ctx.engine_status = "error"
            ctx.factors.append(f"baby_engine_v1 error: {exc}")
            ctx.raw["_prompt_block"] = format_spec_directive_block(domain, spec, demand.bucket)

    else:
        try:
            from event_timing._shared.universal_timing_formula import (  # type: ignore
                compute_universal_timing,
                format_universal_timing_for_prompt,
            )

            raw = compute_universal_timing(
                ctx.kundli,
                domain,
                demand.bucket,
                birth,
                question,
                ctx.intel,
            )
            ctx.raw = raw if isinstance(raw, dict) else {}
            ctx.verdict = str(ctx.raw.get("verdict") or "")
            ctx.factors = list(ctx.raw.get("factors") or [])[:12]
            ctx.engine_status = "ready"
            ctx.engine_id = str(ctx.raw.get("engine_id") or f"{domain}_utf_v1")
            ctx.raw["_prompt_block"] = format_universal_timing_for_prompt(ctx.raw, question)
            cw = ctx.raw.get("current_window") or {}
            if cw:
                ctx.windows.append(cw)
        except Exception as exc:
            ctx.engine_status = "error"
            ctx.factors.append(f"universal_timing_formula error: {exc}")
            ctx.raw["_prompt_block"] = format_spec_directive_block(domain, spec, demand.bucket)

    if (
        demand.is_timing
        and domain not in ("marriage", "love", "travel", "property")
        and isinstance(ctx.raw, dict)
        and ctx.engine_status in ("ready", "partial")
        and ctx.raw
        and ctx.raw.get("engine_arch") != "UNIVERSAL_TIMING_FORMULA_V1"
    ):
        try:
            from event_timing._shared.dual_track_timing import (
                concern_houses_from_spec,
                enrich_dual_track_timing,
                format_dual_track_block,
                karakas_from_spec,
            )

            concern = concern_houses_from_spec(spec, ctx.raw)
            if concern:
                ctx.raw = enrich_dual_track_timing(
                    ctx.raw,
                    ctx.kundli,
                    ctx.kp,
                    concern_houses=concern,
                    karakas=karakas_from_spec(spec, ctx.raw),
                    domain=domain,
                )
                ctx.verdict = str(ctx.raw.get("verdict") or ctx.verdict)
                ctx.factors = list(ctx.raw.get("factors") or [])[:12]
                dt_block = format_dual_track_block(ctx.raw)
                if dt_block:
                    base = ctx.raw.get("_prompt_block") or ""
                    if dt_block not in base:
                        ctx.raw["_prompt_block"] = (base + "\n" + dt_block).strip()
                cw = ctx.raw.get("current_window") or {}
                if cw:
                    ctx.windows = [cw]
        except Exception as exc:
            ctx.factors.append(f"dual_track error: {exc}")

    if (
        demand.is_timing
        and domain != "marriage"
        and isinstance(ctx.raw, dict)
        and ctx.raw.get("verdict")
        and ctx.raw.get("engine_arch") != "UNIVERSAL_TIMING_FORMULA_V1"
    ):
        try:
            from event_timing._shared.step_audit import attach_timing_pipeline_audit

            ctx.raw = attach_timing_pipeline_audit(ctx.raw, domain)
        except Exception:
            pass

    return ctx


def format_timing_block(ctx: PipelineContext) -> str:
    block = (ctx.raw or {}).get("_prompt_block") or ""
    return block if isinstance(block, str) else ""
