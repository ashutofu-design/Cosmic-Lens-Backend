"""Follow-up thread lock — keep same DNA domain/bucket/engine across refine turns.

When user says \"exact month?\", \"aur detail\", \"uske baare me\", the answer
must stay on the SAME specialist engine as the prior question — not re-route
cold to a wrong domain.
"""
from __future__ import annotations

import os
import re
from typing import Any


def followup_lock_enabled() -> bool:
    return (os.environ.get("ASK_FOLLOWUP_LOCK") or "1").strip() != "0"


def _norm_text(s: Any) -> str:
    return re.sub(r"\s+", " ", str(s or "").strip())


def extract_prior_thread(history: Any) -> dict[str, Any]:
    """Pull prior user question + DNA hints from chat history.

    History items may include optional fields from the mobile client:
      domain, bucket, topic, archetype, intent, subject
    """
    if not isinstance(history, (list, tuple)) or not history:
        return {}

    prior_user = ""
    prior_meta: dict[str, Any] = {}

    # Walk newest → oldest
    for item in reversed(list(history)):
        if not isinstance(item, dict):
            continue
        role = str(item.get("role") or "").strip().lower()
        text = _norm_text(item.get("text") or item.get("content") or "")

        if role in ("assistant", "bot", "cosmo") and not prior_meta:
            # Prefer structured DNA fields on the last assistant turn.
            for key in (
                "domain", "bucket", "topic", "archetype", "engine_archetype",
                "intent", "subject", "engine_key",
            ):
                val = item.get(key)
                if val not in (None, ""):
                    prior_meta[key] = val

        if role in ("user", "human") and text:
            # Skip meta / transparency follow-ups as the "topic root"
            try:
                from ask_general_followup import is_explicit_followup
                from ask_timing_followup import is_timing_refine_followup

                if is_explicit_followup(text) or is_timing_refine_followup(text):
                    # Keep looking for a fuller prior ask
                    if not prior_user:
                        prior_user = text
                    continue
            except Exception:
                pass
            prior_user = text
            for key in (
                "domain", "bucket", "topic", "archetype", "engine_archetype",
                "intent", "subject", "engine_key",
            ):
                val = item.get(key)
                if val not in (None, "") and key not in prior_meta:
                    prior_meta[key] = val
            break

    if not prior_user and not prior_meta:
        return {}

    domain = str(prior_meta.get("domain") or "").strip().lower()
    topic = str(prior_meta.get("topic") or "").strip().lower()
    if not domain and topic in (
        "marriage", "love", "career", "finance", "health", "education",
        "children", "property", "travel", "litigation", "timing",
    ):
        domain = "marriage" if topic == "timing" else topic

    return {
        "prior_question": prior_user,
        "domain": domain,
        "bucket": str(prior_meta.get("bucket") or "").strip().lower(),
        "archetype": str(
            prior_meta.get("archetype")
            or prior_meta.get("engine_archetype")
            or ""
        ).strip().lower(),
        "topic": topic,
        "intent": str(prior_meta.get("intent") or "")[:240],
        "subject": str(prior_meta.get("subject") or "").strip().lower(),
        "engine_key": str(prior_meta.get("engine_key") or "").strip().lower(),
    }


def detect_followup_turn(
    question: str,
    history: Any,
    *,
    phase2: dict[str, Any] | None = None,
) -> bool:
    """True when this turn continues the prior thread."""
    if isinstance(phase2, dict):
        turn = str(phase2.get("turn_type") or "").strip().lower()
        if turn == "followup" or phase2.get("is_followup") or phase2.get("wants_explain"):
            return True
        # Phase-2 said new — still allow regex safety net for short deixis.
        if turn == "new" and _norm_text(phase2.get("effective_question") or "") == _norm_text(question):
            pass  # fall through to regex

    try:
        from ask_general_followup import is_generic_followup
        from ask_timing_followup import is_timing_refine_followup

        if is_generic_followup(question) or is_timing_refine_followup(question):
            return bool(extract_prior_thread(history).get("prior_question"))
    except Exception:
        pass
    return False


def _merge_effective(prior_q: str, current_q: str, *, phase2_eff: str = "") -> str:
    """Build one standalone question for engines + narrator."""
    eff = _norm_text(phase2_eff) or _norm_text(current_q)
    prior = _norm_text(prior_q)
    cur = _norm_text(current_q)
    if not prior:
        return eff or cur
    # Phase-2 already expanded well (contains prior topic words)
    if prior and eff and prior.lower()[:40] in eff.lower():
        return eff
    if cur.lower() in prior.lower():
        return prior
    try:
        from ask_general_followup import merge_general_followup_question

        return merge_general_followup_question(prior, cur)
    except Exception:
        return f"{prior} — user refine: {cur}"


def lock_admin_to_prior_dna(
    admin: dict[str, Any] | None,
    prior: dict[str, Any],
    *,
    question: str = "",
    is_timing: bool | None = None,
) -> dict[str, Any]:
    """Force admin Question DNA onto prior domain/bucket so engine match stays put."""
    out = admin if isinstance(admin, dict) else {}
    domain = str(prior.get("domain") or out.get("domain") or "").strip().lower()
    if domain == "relationship":
        domain = "love"
    bucket = str(
        prior.get("bucket")
        or prior.get("archetype")
        or out.get("bucket")
        or ""
    ).strip().lower()
    archetype = str(
        prior.get("archetype")
        or out.get("dna_engine_archetype")
        or bucket
        or ""
    ).strip().lower()
    subject = str(prior.get("subject") or out.get("subject") or "unknown").strip().lower()
    intent = str(prior.get("intent") or out.get("intent") or "")[:240]
    timing = bool(out.get("routed_timing") or out.get("is_timing"))
    if is_timing is not None:
        timing = bool(is_timing)

    if not domain or domain == "general":
        return out

    item = {
        "normalized_question": (question or prior.get("prior_question") or "")[:500],
        "domain": domain,
        "bucket": bucket or "general",
        "engine_archetype": archetype or None,
        "intent": intent or f"Follow-up on prior {domain} question",
        "subject": subject or "unknown",
        "target": out.get("target") or "unknown",
        "question_type": "timing" if timing else (out.get("question_type_dna") or "prediction"),
        "timing": timing,
        "tense": "future" if timing else "present",
        "emotion": "neutral",
        "risk": "low",
        "is_followup": True,
        "followup_of": str(prior.get("prior_question") or "")[:300],
        "confidence": float(out.get("confidence") or 0.85),
        "user_wants": intent or f"Continue prior {domain} thread",
        "understanding_confidence": float(out.get("confidence") or 0.85),
        "answer_style": "short_paragraph",
        "answer_approach": "followup_lock",
        "bucket_match_confidence": "high",
    }
    try:
        from ask_question_dna import (
            apply_question_dna_to_routing,
            validate_question_dna_item,
        )

        validated = validate_question_dna_item(item, original_question=question or "")
        validated["is_followup"] = True
        validated["followup_of"] = item["followup_of"]
        dna = {
            "questions": [validated],
            "source": "followup_lock",
            "latency_ms": 0,
        }
        apply_question_dna_to_routing(question or "", out, dna)
    except Exception as exc:
        print(f"[followup_lock] dna apply failed: {exc}", flush=True)
        out["domain"] = domain
        out["routed_domain"] = domain
        out["bucket"] = bucket
        out["dna_routing_applied"] = True
        if archetype:
            out["dna_engine_archetype"] = archetype
            out["routed_archetype"] = archetype

    out["is_followup"] = True
    out["turn_type"] = "followup"
    out["followup_lock"] = {
        "prior_question": (prior.get("prior_question") or "")[:120],
        "domain": out.get("domain") or domain,
        "bucket": out.get("bucket") or bucket,
        "archetype": out.get("dna_engine_archetype") or archetype,
    }
    out["dna_routing_applied"] = True
    return out


def apply_followup_lock(
    question: str,
    history: Any,
    *,
    phase2: dict[str, Any] | None = None,
    admin: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Return lock result used by raw_passthrough.

    Keys:
      is_followup, effective_question, admin, prior, reason
    """
    q = (question or "").strip()
    admin_out = admin if isinstance(admin, dict) else {}
    if not followup_lock_enabled():
        return {
            "is_followup": False,
            "effective_question": q,
            "admin": admin_out,
            "prior": {},
            "reason": "disabled",
        }

    prior = extract_prior_thread(history)
    is_fu = detect_followup_turn(q, history, phase2=phase2)
    if not is_fu:
        return {
            "is_followup": False,
            "effective_question": q,
            "admin": admin_out,
            "prior": prior,
            "reason": "new_turn",
        }

    if not prior.get("prior_question") and not prior.get("domain"):
        # Still mark followup so Phase-2 effective_question is kept.
        eff = ""
        if isinstance(phase2, dict):
            eff = str(phase2.get("effective_question") or "").strip()
        return {
            "is_followup": True,
            "effective_question": eff or q,
            "admin": admin_out,
            "prior": prior,
            "reason": "followup_no_prior_meta",
        }

    # Infer domain from prior question text when history lacks DNA fields.
    if not prior.get("domain") and prior.get("prior_question"):
        try:
            from ask_intent_fidelity import infer_primary_domain

            inferred = infer_primary_domain(str(prior.get("prior_question") or ""))
            if inferred:
                prior = dict(prior)
                prior["domain"] = str(inferred).strip().lower()
        except Exception:
            pass

    phase2_eff = ""
    timing_hint = None
    if isinstance(phase2, dict):
        phase2_eff = str(phase2.get("effective_question") or "").strip()
        if phase2.get("timing") is not None:
            timing_hint = bool(phase2.get("timing"))
        # Prefer Phase-2 domain only when prior has none
        if not prior.get("domain") and phase2.get("domain"):
            prior = dict(prior)
            prior["domain"] = str(phase2.get("domain") or "").strip().lower()
            prior["bucket"] = str(
                phase2.get("archetype") or phase2.get("bucket") or ""
            ).strip().lower()

    # Timing refine follow-ups → keep domain, set timing true
    try:
        from ask_timing_followup import is_timing_refine_followup

        if is_timing_refine_followup(q):
            timing_hint = True
    except Exception:
        pass

    effective = _merge_effective(
        str(prior.get("prior_question") or ""),
        q,
        phase2_eff=phase2_eff,
    )
    admin_locked = lock_admin_to_prior_dna(
        admin_out,
        prior,
        question=effective,
        is_timing=timing_hint,
    )
    admin_locked["effective_question"] = effective
    admin_locked["is_followup"] = True
    admin_locked["turn_type"] = "followup"

    print(
        f"[followup_lock] LOCKED domain={admin_locked.get('domain')} "
        f"bucket={admin_locked.get('bucket')} "
        f"arch={admin_locked.get('dna_engine_archetype')} "
        f"timing={admin_locked.get('routed_timing')} "
        f"eff={effective[:72]!r}",
        flush=True,
    )
    return {
        "is_followup": True,
        "effective_question": effective,
        "admin": admin_locked,
        "prior": prior,
        "reason": "locked",
    }
