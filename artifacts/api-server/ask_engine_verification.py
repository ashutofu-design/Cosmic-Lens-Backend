"""Verify static engine + archetype matches question subject and evidence quality."""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field
from typing import Any

from ask_intent_fidelity import _PARTNER_SUBJECT_RX, archetype_allowed_for_question

# Gap / personality engines — native self only.
_NATIVE_SELF_ARCHETYPES = frozenset({
    "personality_nature",
    "self_appearance",
    "general_personality",
})

_PARTNER_PERSONALITY_RX = re.compile(
    r"(?ix)"
    r"(?:\b(partner|spouse|pati|patni|biwi|husband|wife|jeevan\s*sathi|boyfriend|girlfriend)\b"
    r".{0,80}\b(personality|nature|swabhav|express|reserved|style|kaisa|kaisi|kaise)\b)"
    r"|(?:\b(expressive|reserved)\b.{0,60}\b(partner|spouse|pati|patni)\b)"
    r"|(?:\b(personality|nature|swabhav|style)\b.{0,60}\b(partner|spouse|pati|patni)\b)"
)

_NATIVE_SELF_FOCUS_RX = re.compile(
    r"(?ix)\b(mera\s+swabhav|meri?\s+nature|main\s+kaisa|who\s+am\s+i|kaun\s+hu|about\s+me)\b"
)


@dataclass
class EngineVerificationResult:
    ok: bool
    action: str  # keep | reroute_mr | d1_open_chart
    reason: str
    mr_archetype: str | None = None
    failed_checks: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def is_partner_personality_question(question: str) -> bool:
    q = (question or "").strip()
    if not q or not _PARTNER_SUBJECT_RX.search(q):
        return False
    return bool(_PARTNER_PERSONALITY_RX.search(q))


def should_suppress_gap_for_question(
    question: str,
    *,
    gap_key: str | None = None,
) -> bool:
    """Partner / spouse subject must not use native-only gap engines (personality, etc.)."""
    q = (question or "").strip()
    if not q:
        return False
    if not _PARTNER_SUBJECT_RX.search(q):
        return False
    if gap_key == "personality":
        return True
    if is_partner_personality_question(q):
        return True
    if gap_key and gap_key in ("anger", "dreams", "wellness") and _PARTNER_PERSONALITY_RX.search(q):
        return True
    return False


def suggest_mr_archetype_for_question(question: str) -> str | None:
    """Best MR archetype when verification reroutes from wrong engine."""
    q = (question or "").strip()
    if not q:
        return None
    if is_partner_personality_question(q):
        return "partner_nature"
    if _PARTNER_SUBJECT_RX.search(q):
        try:
            from ask_mr.classifier import classify_mr_archetype

            return classify_mr_archetype(q) or "partner_nature"
        except Exception:
            return "partner_nature"
    return None


def apply_pre_route_guards(
    flags: dict[str, bool],
    question: str,
    *,
    gap_key: str | None = None,
    llm_intent: dict[str, Any] | None = None,
) -> tuple[dict[str, bool], list[str]]:
    """Correct flags before resolver picks winner."""
    out = {k: bool(v) for k, v in (flags or {}).items()}
    notes: list[str] = []

    if should_suppress_gap_for_question(question, gap_key=gap_key):
        if out.get("gap"):
            out["gap"] = False
            notes.append("gap:suppressed_partner_subject")
        out["mr"] = True
        notes.append("mr:forced_partner_subject")

    if is_partner_personality_question(question):
        out["mr"] = True
        out["gap"] = False
        notes.append("mr:partner_personality")

    if _NATIVE_SELF_FOCUS_RX.search(question or "") and not _PARTNER_SUBJECT_RX.search(question or ""):
        if out.get("mr") and not out.get("gap"):
            pass
        elif out.get("gap") or gap_key == "personality":
            out["gap"] = True
            out["mr"] = False
            notes.append("gap:native_self_focus")

  # Love/marriage domain from intent
    if isinstance(llm_intent, dict):
        dom = str(llm_intent.get("domain") or "").lower()
        if dom in ("love", "marriage") and _PARTNER_SUBJECT_RX.search(question or ""):
            out["mr"] = True
            out["gap"] = False
            notes.append(f"mr:llm_domain_{dom}")

    return out, notes


def verify_static_engine_selection(
    question: str,
    *,
    engine_key: str | None,
    archetype: str | None = None,
    gap_key: str | None = None,
    llm_intent: dict[str, Any] | None = None,
) -> EngineVerificationResult:
    """Pre-run: is this engine key appropriate for the question?"""
    q = (question or "").strip()
    arch = str(archetype or "").strip().lower()
    failed: list[str] = []

    if not engine_key:
        return EngineVerificationResult(
            ok=False,
            action="d1_open_chart",
            reason="no_engine_selected",
            failed_checks=["no_engine"],
        )

    if engine_key == "gap" and should_suppress_gap_for_question(q, gap_key=gap_key):
        failed.append("gap_on_partner_subject")
        return EngineVerificationResult(
            ok=False,
            action="reroute_mr",
            reason="partner_question_not_gap",
            mr_archetype=suggest_mr_archetype_for_question(q),
            failed_checks=failed,
        )

    if arch in _NATIVE_SELF_ARCHETYPES and _PARTNER_SUBJECT_RX.search(q):
        failed.append("native_archetype_on_partner_question")
        return EngineVerificationResult(
            ok=False,
            action="reroute_mr",
            reason="native_archetype_partner_mismatch",
            mr_archetype=suggest_mr_archetype_for_question(q),
            failed_checks=failed,
        )

    if engine_key == "mr" and arch and not archetype_allowed_for_question(q, arch):
        failed.append("mr_archetype_not_allowed")
        return EngineVerificationResult(
            ok=False,
            action="reroute_mr",
            reason="mr_archetype_mismatch",
            mr_archetype=suggest_mr_archetype_for_question(q),
            failed_checks=failed,
        )

    return EngineVerificationResult(
        ok=True,
        action="keep",
        reason="selection_ok",
        mr_archetype=arch or None,
        failed_checks=[],
    )


def verify_engine_output(
    question: str,
    *,
    engine_key: str | None,
    archetype: str | None,
    slice_meta: dict[str, Any] | None,
    gap_key: str | None = None,
) -> EngineVerificationResult:
    """Post-run: evidence + subject focus match question."""
    q = (question or "").strip()
    arch = str(archetype or "").strip().lower()
    meta = slice_meta if isinstance(slice_meta, dict) else {}
    failed: list[str] = []

    pre = verify_static_engine_selection(
        q,
        engine_key=engine_key,
        archetype=arch,
        gap_key=gap_key,
    )
    if not pre.ok:
        return pre

    summary = " ".join(meta.get("summary") or [])
    if "native self only" in summary.lower() and _PARTNER_SUBJECT_RX.search(q):
        failed.append("native_focus_on_partner_q")
        return EngineVerificationResult(
            ok=False,
            action="reroute_mr",
            reason="output_focus_native_on_partner_q",
            mr_archetype=suggest_mr_archetype_for_question(q),
            failed_checks=failed,
        )

    evidence = list(meta.get("evidence") or [])
    pos = list(meta.get("evidence_positive") or [])
    neg = list(meta.get("evidence_negative") or [])
    neu = list(meta.get("evidence_neutral") or [])
    ev_count = len(evidence) or len(pos) + len(neg) + len(neu)

    if engine_key in ("gap", "mr", "health", "career", "finance") and ev_count == 0:
        if not meta.get("skip_llm") and not meta.get("template_text"):
            failed.append("empty_evidence")
            mr_arch = suggest_mr_archetype_for_question(q)
            if mr_arch and engine_key != "mr":
                return EngineVerificationResult(
                    ok=False,
                    action="reroute_mr",
                    reason="empty_evidence_reroute",
                    mr_archetype=mr_arch,
                    failed_checks=failed,
                )
            return EngineVerificationResult(
                ok=False,
                action="d1_open_chart",
                reason="empty_evidence_d1_fallback",
                failed_checks=failed,
            )

    return EngineVerificationResult(
        ok=True,
        action="keep",
        reason="output_ok",
        failed_checks=[],
    )
