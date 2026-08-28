"""Hard engine-match gate — DNA domain/bucket/intent/subject should match executed engine.

Product rule:
  - Prefer correct engine (retry coerce/reclass within deadline).
  - Engine required + matched → open engine path.
  - Engine not required (knowledge / general chart / open chart) → direct LLM.
  - Unresolved mismatch → direct LLM fallback (never leave V1 with zero answer).
"""
from __future__ import annotations

import os
import time
from dataclasses import asdict, dataclass, field
from typing import Any

from engine_collision_registry import DOMAIN_PRIMARY_ENGINE

_STATIC_KEYS = (
    "education", "children", "property", "vehicle", "travel",
    "litigation", "gap", "network", "luck", "career", "finance", "health", "mr",
)

# Free-form Phase-2 / LLM labels → catalog ids (love buckets or MR/career/…)
_FREEFORM_ALIASES: dict[str, str] = {
    "partner_loyalty": "trust_loyalty",
    "loyalty": "trust_loyalty",
    "loyal": "trust_loyalty",
    "dhoka": "trust_loyalty",
    "cheat": "trust_loyalty",
    "cheating": "trust_loyalty",
    "betrayal": "trust_loyalty",
    "marriage_timing": "dating_courtship",
    "shaadi_timing": "dating_courtship",
    "job_promotion": "career_milestones",
    "promotion": "career_milestones",
    "naukri": "general_career",
    "paisa": "wealth_potential",
    "money": "wealth_potential",
    "wealth": "wealth_potential",
    "sehat": "overall_vitality",
    "health": "overall_vitality",
    "younger_sibling": "general_siblings",
    "sibling": "general_siblings",
    "gemstone_remedy": "general_remedy",
    "remedy": "general_remedy",
}


@dataclass
class EngineMatchDecision:
    ok: bool
    path: str  # engine | direct_llm | blocked
    engine_key: str | None = None
    domain: str = ""
    bucket: str = ""
    archetype: str | None = None
    intent: str = ""
    subject: str = ""
    flags: dict[str, bool] = field(default_factory=dict)
    is_timing: bool = False
    attempts: int = 0
    elapsed_ms: int = 0
    reason: str = ""
    failed_checks: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def engine_match_gate_enabled() -> bool:
    return (os.environ.get("ASK_ENGINE_MATCH_GATE") or "1").strip() != "0"


def engine_match_deadline_s() -> float:
    try:
        return max(5.0, float(os.environ.get("ASK_ENGINE_MATCH_DEADLINE_S") or "60"))
    except (TypeError, ValueError):
        return 60.0


def _empty_flags() -> dict[str, bool]:
    return {k: False for k in _STATIC_KEYS}


def _one_hot(engine_key: str | None) -> dict[str, bool]:
    out = _empty_flags()
    eng = (engine_key or "").strip().lower()
    if eng in out:
        out[eng] = True
    return out


def _winner(flags: dict[str, bool] | None) -> str | None:
    if not flags:
        return None
    active = [k for k, v in flags.items() if v]
    if len(active) == 1:
        return active[0]
    return None


def _primary_dna_item(admin: dict[str, Any] | None) -> dict[str, Any]:
    if not isinstance(admin, dict):
        return {}
    dna = admin.get("question_dna")
    if not isinstance(dna, dict):
        return {}
    items = dna.get("questions")
    if isinstance(items, list) and items and isinstance(items[0], dict):
        return items[0]
    return {}


def _alias_raw_bucket(raw: str) -> str:
    s = (raw or "").strip().lower().replace(" ", "_").replace("-", "_")
    return _FREEFORM_ALIASES.get(s, s)


def _normalize_domain(domain: str) -> str:
    d = (domain or "").strip().lower()
    aliases = {
        "relationship": "love",
        "pyaar": "love",
        "shaadi": "marriage",
        "job": "career",
        "money": "finance",
        "wealth": "finance",
        "sehat": "health",
        "legal": "litigation",
        "friends": "network",
        "social_circle": "network",
    }
    return aliases.get(d, d)


def coerce_admin_dna_for_routing(
    admin: dict[str, Any] | None,
    *,
    question: str = "",
) -> dict[str, Any]:
    """Rewrite admin Question DNA onto catalog domain/bucket/archetype.

    Returns the same admin dict (mutated) for chaining.
    """
    if not isinstance(admin, dict):
        return {}
    item = dict(_primary_dna_item(admin) or {})
    if not item:
        item = {
            "domain": admin.get("routed_domain") or admin.get("domain") or "general",
            "bucket": admin.get("bucket") or admin.get("routed_archetype") or "general",
            "intent": admin.get("intent") or admin.get("question_summary") or "",
            "subject": admin.get("subject") or "unknown",
            "target": admin.get("target") or "unknown",
            "timing": bool(admin.get("routed_timing") or admin.get("is_timing")),
            "confidence": float(admin.get("confidence") or 0.7),
            "normalized_question": (question or "")[:500],
        }

    domain = _normalize_domain(str(item.get("domain") or "general"))
    raw_bucket = _alias_raw_bucket(
        str(item.get("bucket") or item.get("engine_archetype") or admin.get("routed_archetype") or "")
    )
    item["domain"] = domain
    item["bucket"] = raw_bucket
    if question and not item.get("normalized_question"):
        item["normalized_question"] = question[:500]

    try:
        from ask_question_dna import (
            apply_question_dna_to_routing,
            validate_question_dna_item,
        )

        validated = validate_question_dna_item(item, original_question=question or "")
        dna = {
            "questions": [validated],
            "source": str((admin.get("question_dna") or {}).get("source") or "engine_match_gate"),
            "latency_ms": int((admin.get("question_dna") or {}).get("latency_ms") or 0),
        }
        apply_question_dna_to_routing(question or "", admin, dna)
    except Exception as exc:
        print(f"[engine_match_gate] coerce dna failed: {exc}", flush=True)
        admin["domain"] = domain
        admin["routed_domain"] = domain
        admin["bucket"] = raw_bucket
    return admin


def expected_engine_from_admin(admin: dict[str, Any] | None) -> dict[str, Any]:
    """Derive required engine from coerced DNA. engine_key=None → direct LLM path."""
    if not isinstance(admin, dict):
        return {
            "engine_key": None,
            "domain": "general",
            "bucket": "",
            "archetype": None,
            "intent": "",
            "subject": "unknown",
            "is_timing": False,
            "requires_engine": False,
            "reason": "no_admin",
        }

    branch = str(admin.get("branch") or "").strip().lower()
    if branch == "knowledge" or admin.get("knowledge"):
        return {
            "engine_key": None,
            "domain": str(admin.get("domain") or "general"),
            "bucket": str(admin.get("bucket") or ""),
            "archetype": None,
            "intent": str(admin.get("intent") or "")[:240],
            "subject": str(admin.get("subject") or "unknown"),
            "is_timing": False,
            "requires_engine": False,
            "reason": "knowledge_branch",
        }

    item = _primary_dna_item(admin)
    domain = _normalize_domain(
        str(item.get("domain") or admin.get("routed_domain") or admin.get("domain") or "general")
    )
    bucket = str(item.get("bucket") or admin.get("bucket") or "").strip().lower()
    intent = str(
        item.get("intent") or item.get("user_wants") or admin.get("intent") or ""
    ).strip()[:240]
    subject = str(item.get("subject") or admin.get("subject") or "unknown").strip().lower()
    if "timing" in item:
        is_timing = bool(item.get("timing"))
    else:
        is_timing = bool(admin.get("routed_timing") or admin.get("is_timing"))

    try:
        from ask_question_dna import resolve_engine_archetype_from_dna_item

        archetype = resolve_engine_archetype_from_dna_item(item) if item else None
    except Exception:
        archetype = None
    if not archetype:
        archetype = str(
            admin.get("dna_engine_archetype")
            or admin.get("routed_archetype")
            or bucket
            or ""
        ).strip().lower() or None

    if domain in ("", "general") or admin.get("general_chart"):
        return {
            "engine_key": None,
            "domain": domain or "general",
            "bucket": bucket,
            "archetype": archetype,
            "intent": intent,
            "subject": subject,
            "is_timing": is_timing,
            "requires_engine": False,
            "reason": "general_or_chart",
        }

    engine_key = DOMAIN_PRIMARY_ENGINE.get(domain)
    if not engine_key:
        return {
            "engine_key": None,
            "domain": domain,
            "bucket": bucket,
            "archetype": archetype,
            "intent": intent,
            "subject": subject,
            "is_timing": is_timing,
            "requires_engine": False,
            "reason": f"no_primary_engine:{domain}",
        }

    return {
        "engine_key": engine_key,
        "domain": domain,
        "bucket": bucket,
        "archetype": archetype,
        "intent": intent,
        "subject": subject,
        "is_timing": is_timing,
        "requires_engine": True,
        "reason": f"dna:{domain}/{bucket or archetype}",
    }


def verify_engine_match(
    *,
    expected_engine: str | None,
    requires_engine: bool,
    flags: dict[str, bool] | None,
    is_timing: bool = False,
    executed_engine: str | None = None,
) -> tuple[bool, list[str]]:
    """Return (ok, failed_checks). Timing path: no static flag required."""
    failed: list[str] = []
    winner = executed_engine or _winner(flags)

    if not requires_engine:
        # Direct LLM — static engines must be off.
        if winner:
            failed.append(f"direct_llm_but_engine_on={winner}")
            return False, failed
        return True, failed

    if is_timing:
        # Timing engines are separate; static one-hot should be clear.
        if winner and expected_engine and winner != expected_engine:
            failed.append(f"timing_static_conflict winner={winner} expected={expected_engine}")
            return False, failed
        return True, failed

    if not expected_engine:
        failed.append("requires_engine_but_no_key")
        return False, failed

    if winner != expected_engine:
        failed.append(f"dna_engine={expected_engine}")
        failed.append(f"winner={winner or 'none'}")
        return False, failed
    return True, failed


def _try_reclassify_domain_from_text(question: str) -> str | None:
    """Cheap text fallback when DNA domain is wrong/empty — never invents engines."""
    q = (question or "").strip()
    if not q:
        return None
    try:
        from ask_intent_fidelity import infer_primary_domain

        dom = infer_primary_domain(q)
        if dom:
            return _normalize_domain(str(dom))
    except Exception:
        pass
    try:
        from ask_mr.classifier import is_mr_static_question

        if is_mr_static_question(q):
            return "love"
    except Exception:
        pass
    try:
        from ask_health.health_registry import is_health_static_question

        if is_health_static_question(q):
            return "health"
    except Exception:
        pass
    return None


def _refresh_dna_via_llm(
    question: str,
    admin: dict[str, Any],
    *,
    client: Any = None,
    history: Any = None,
) -> bool:
    """Optional second DNA extract when first routing mismatches. Returns True if applied."""
    try:
        from ask_question_dna import (
            apply_question_dna_to_routing,
            extract_question_dna,
            question_dna_enabled,
        )

        if not question_dna_enabled():
            return False
        dna = extract_question_dna(question or "", history=history, client=client)
        if not isinstance(dna, dict) or not dna.get("questions"):
            return False
        return bool(apply_question_dna_to_routing(question or "", admin, dna))
    except Exception as exc:
        print(f"[engine_match_gate] dna refresh failed: {exc}", flush=True)
        return False


def ensure_correct_engine_route(
    question: str,
    admin: dict[str, Any] | None,
    flags: dict[str, bool] | None = None,
    *,
    client: Any = None,
    history: Any = None,
    is_timing: bool = False,
    direct_llm_bypass: bool = False,
    deadline_s: float | None = None,
) -> EngineMatchDecision:
    """Retry until DNA-required engine is selected, or open direct-LLM path.

    Gate does NOT open for engine-required questions until winner == DNA engine.
    """
    t0 = time.monotonic()
    limit = float(deadline_s if deadline_s is not None else engine_match_deadline_s())
    attempts = 0
    working_flags = dict(flags or _empty_flags())
    admin_out: dict[str, Any] = admin if isinstance(admin, dict) else {}
    last_failed: list[str] = []
    last_reason = "init"

    if not engine_match_gate_enabled():
        return EngineMatchDecision(
            ok=True,
            path="engine" if _winner(working_flags) else "direct_llm",
            engine_key=_winner(working_flags),
            flags=working_flags,
            reason="gate_disabled",
            attempts=0,
            elapsed_ms=0,
        )

    if direct_llm_bypass:
        return EngineMatchDecision(
            ok=True,
            path="direct_llm",
            engine_key=None,
            flags=_empty_flags(),
            reason="direct_llm_bypass",
            attempts=0,
            elapsed_ms=int((time.monotonic() - t0) * 1000),
        )

    # Chart interpretive / placement → LLM, no engine force.
    try:
        from ask_routing_policy import should_bypass_static_engines_for_direct_llm

        bypass, why = should_bypass_static_engines_for_direct_llm(
            question or "",
            admin_out if admin_out else None,
        )
        if bypass:
            return EngineMatchDecision(
                ok=True,
                path="direct_llm",
                engine_key=None,
                flags=_empty_flags(),
                reason=f"bypass:{why}",
                attempts=0,
                elapsed_ms=int((time.monotonic() - t0) * 1000),
            )
    except Exception:
        pass
    try:
        from chart_fact_answer import needs_llm_chart_answer

        if needs_llm_chart_answer(question or ""):
            return EngineMatchDecision(
                ok=True,
                path="direct_llm",
                engine_key=None,
                flags=_empty_flags(),
                reason="chart_interpretive_llm",
                attempts=0,
                elapsed_ms=int((time.monotonic() - t0) * 1000),
            )
    except Exception:
        pass

    while True:
        attempts += 1
        elapsed = time.monotonic() - t0
        if elapsed > limit and attempts > 1:
            break

        coerce_admin_dna_for_routing(admin_out, question=question or "")
        expected = expected_engine_from_admin(admin_out)
        req = bool(expected.get("requires_engine"))
        eng = expected.get("engine_key")
        timing = bool(expected.get("is_timing") or is_timing)

        if not req:
            working_flags = _empty_flags()
            ok, failed = verify_engine_match(
                expected_engine=None,
                requires_engine=False,
                flags=working_flags,
                is_timing=False,
            )
            if ok:
                decision = EngineMatchDecision(
                    ok=True,
                    path="direct_llm",
                    engine_key=None,
                    domain=str(expected.get("domain") or ""),
                    bucket=str(expected.get("bucket") or ""),
                    archetype=expected.get("archetype"),
                    intent=str(expected.get("intent") or ""),
                    subject=str(expected.get("subject") or ""),
                    flags=working_flags,
                    is_timing=False,
                    attempts=attempts,
                    elapsed_ms=int((time.monotonic() - t0) * 1000),
                    reason=str(expected.get("reason") or "direct_llm"),
                )
                if isinstance(admin, dict):
                    admin["engine_match_gate"] = decision.to_dict()
                return decision

        # Force DNA engine one-hot (static) unless timing-only.
        if timing:
            working_flags = _empty_flags()
        else:
            working_flags = _one_hot(str(eng) if eng else None)

        ok, failed = verify_engine_match(
            expected_engine=str(eng) if eng else None,
            requires_engine=req,
            flags=working_flags,
            is_timing=timing,
        )
        last_failed = failed
        last_reason = str(expected.get("reason") or "match")

        if ok:
            # Sync admin archetype keys for downstream engines.
            arch = expected.get("archetype")
            if isinstance(admin, dict) and arch:
                admin["dna_engine_archetype"] = arch
                admin["routed_archetype"] = arch
                dom = str(expected.get("domain") or "")
                if dom in ("love", "marriage"):
                    admin["mr_archetype"] = arch
                elif dom == "career":
                    admin["career_archetype"] = arch
                elif dom == "finance":
                    admin["finance_archetype"] = arch
                elif dom == "health":
                    admin["health_archetype"] = arch
            decision = EngineMatchDecision(
                ok=True,
                path="engine",
                engine_key=str(eng) if eng else None,
                domain=str(expected.get("domain") or ""),
                bucket=str(expected.get("bucket") or ""),
                archetype=expected.get("archetype"),
                intent=str(expected.get("intent") or ""),
                subject=str(expected.get("subject") or ""),
                flags=working_flags,
                is_timing=timing,
                attempts=attempts,
                elapsed_ms=int((time.monotonic() - t0) * 1000),
                reason=f"matched:{last_reason}",
            )
            if isinstance(admin, dict):
                admin["engine_match_gate"] = decision.to_dict()
                admin["dna_routing_applied"] = True
            print(
                f"[engine_match_gate] OPEN path=engine engine={eng} "
                f"domain={expected.get('domain')} bucket={expected.get('bucket')} "
                f"subject={expected.get('subject')} attempts={attempts} "
                f"q={(question or '')[:60]!r}",
                flush=True,
            )
            return decision

        # ── Repair attempts before next verify ──────────────────────────
        print(
            f"[engine_match_gate] MISMATCH attempt={attempts} failed={failed} "
            f"expected={eng} q={(question or '')[:60]!r}",
            flush=True,
        )

        remaining = limit - (time.monotonic() - t0)
        if remaining < 1.5:
            break

        # 1) Text domain reclassify into admin DNA
        if attempts == 1:
            inferred = _try_reclassify_domain_from_text(question or "")
            if inferred and inferred != str(expected.get("domain") or ""):
                item = _primary_dna_item(admin_out) or {}
                item["domain"] = inferred
                item["bucket"] = _alias_raw_bucket(
                    str(item.get("bucket") or expected.get("bucket") or "")
                )
                dna = admin_out.get("question_dna") if isinstance(admin_out.get("question_dna"), dict) else {}
                admin_out["question_dna"] = {
                    **(dna or {}),
                    "questions": [item],
                    "source": "engine_match_gate:text_reclass",
                }
                admin_out["domain"] = inferred
                admin_out["routed_domain"] = inferred
                continue

        # 2) Real DNA LLM refresh (expensive — once, if time left)
        if attempts == 2 and client is not None and remaining > 12:
            if _refresh_dna_via_llm(
                question or "",
                admin_out,
                client=client,
                history=history,
            ):
                continue

        # 3) Soft alias re-coerce only
        if attempts >= 3:
            break

        # Force one-hot again next loop (already forced above) — tiny sleep to
        # avoid busy-spin if something else mutates flags externally.
        time.sleep(0.05)

    # Deadline / exhausted — prefer correct engine when matched; never leave
    # the user with zero answer. Unresolved mismatch → direct LLM (chart
    # context) so Cosmic Intelligence V1 still replies.
    expected = expected_engine_from_admin(admin_out)
    decision = EngineMatchDecision(
        ok=True,
        path="direct_llm",
        engine_key=None,
        domain=str(expected.get("domain") or ""),
        bucket=str(expected.get("bucket") or ""),
        archetype=expected.get("archetype"),
        intent=str(expected.get("intent") or ""),
        subject=str(expected.get("subject") or ""),
        flags=_empty_flags(),
        is_timing=bool(expected.get("is_timing") or is_timing),
        attempts=attempts,
        elapsed_ms=int((time.monotonic() - t0) * 1000),
        reason=(
            "deadline_direct_llm"
            if not expected.get("requires_engine")
            else "mismatch_fallback_direct_llm"
        ),
        failed_checks=last_failed
        or (
            [f"expected={expected.get('engine_key')}"]
            if expected.get("requires_engine")
            else []
        ),
    )
    if isinstance(admin, dict):
        admin["engine_match_gate"] = decision.to_dict()
    print(
        f"[engine_match_gate] FALLBACK direct_llm "
        f"expected={expected.get('engine_key')} "
        f"requires_engine={bool(expected.get('requires_engine'))} "
        f"failed={last_failed} attempts={attempts} "
        f"elapsed_ms={decision.elapsed_ms} q={(question or '')[:60]!r}",
        flush=True,
    )
    return decision


def apply_match_decision_to_static_bools(
    decision: EngineMatchDecision,
) -> dict[str, bool]:
    """Convenience: flags dict for raw_passthrough static bools."""
    if decision.path != "engine" or decision.is_timing:
        return _empty_flags()
    return dict(decision.flags or _one_hot(decision.engine_key))
