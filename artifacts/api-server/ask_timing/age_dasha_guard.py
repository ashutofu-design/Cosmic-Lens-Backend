"""LLM + soft-heuristic guard: user age vs timing question vs engine dasha.

Marriage timing is EXCLUDED (M17 / BCP path stays deterministic).

Flow for all other timing domains:
  1. Read user age + question
  2. Walk ranked dashas in order
  3. LLM/heuristic: does this dasha match age + question?
  4. If no → take NEXT dasha only (no random jump)
  5. Lock that window for narrator
  6. Same timing Q asked again (without agla/next) → SAME timing (stable)
"""
from __future__ import annotations

import json
import os
import re
from datetime import datetime
from typing import Any, Optional

_JUDGE_JSON_RX = re.compile(r"\{[\s\S]*\}")

# Soft life-stage onset — above PMF legal/practical floor. Used when engine
# locks an imminent ("now"/this-year) window that is early for the event.
_TYPICAL_ONSET_AGE: dict[str, int] = {
    "children": 25,
    "property": 27,
    "vehicle": 22,
    "finance": 22,
    "career": 21,
    "education": 16,
    "foreign_education": 18,
    "travel": 20,
    "love": 20,
    "health": 16,
    "litigation": 21,
    "spiritual": 21,
    "fame": 20,
    "network": 18,
    "universal": 20,
    "general": 20,
}

_IMMINENT_RX = re.compile(
    r"(?ix)\b("
    r"abhi|ab\s+hi|current|isi\s+(?:saal|mahine|dasha)|this\s+(?:year|month)|"
    r"ongoing|running|active\s+now|present"
    r")\b"
)


def timing_age_dasha_guard_enabled() -> bool:
    return (os.environ.get("ASK_TIMING_AGE_DASHA_GUARD") or "1").strip() != "0"


def timing_age_dasha_guard_model(default: str = "gpt-4.1-mini") -> str:
    return (os.environ.get("ASK_TIMING_AGE_DASHA_GUARD_MODEL") or default).strip() or default


def _parse_judge_json(raw: str) -> dict[str, Any]:
    text = (raw or "").strip()
    if not text:
        return {}
    try:
        obj = json.loads(text)
        return obj if isinstance(obj, dict) else {}
    except json.JSONDecodeError:
        pass
    m = _JUDGE_JSON_RX.search(text)
    if not m:
        return {}
    try:
        obj = json.loads(m.group(0))
        return obj if isinstance(obj, dict) else {}
    except json.JSONDecodeError:
        return {}


def _domain_from_engine_id(engine_id: str | None) -> str:
    eid = (engine_id or "").strip().lower()
    if not eid:
        return "universal"
    for d in (
        "children", "property", "vehicle", "finance", "career", "education",
        "foreign_education", "travel", "love", "health", "litigation",
        "spiritual", "fame", "network", "universal",
    ):
        if eid.startswith(d) or f"_{d}_" in eid or eid.endswith(f"_{d}"):
            return d
    return eid.split("_")[0] or "universal"


def _window_start_year(w: dict[str, Any] | None) -> Optional[int]:
    if not isinstance(w, dict):
        return None
    for key in ("start", "start_iso", "end", "end_iso"):
        raw = str(w.get(key) or "").strip()
        if len(raw) >= 4 and raw[:4].isdigit():
            y = int(raw[:4])
            if 1990 <= y <= 2100:
                return y
    label = str(w.get("window") or w.get("label") or "")
    m = re.search(r"(20\d{2})", label)
    if m:
        return int(m.group(1))
    return None


def _age_at_year(user_age: int, year: Optional[int], now_year: int | None = None) -> Optional[int]:
    if year is None:
        return None
    cy = now_year if now_year is not None else datetime.now().year
    return int(user_age) + (int(year) - int(cy))


def _is_imminent_window(w: dict[str, Any] | None, now_year: int | None = None) -> bool:
    if not isinstance(w, dict):
        return False
    cy = now_year if now_year is not None else datetime.now().year
    y = _window_start_year(w)
    if y is not None and y <= cy + 1:
        return True
    label = str(w.get("window") or w.get("label") or "")
    return bool(_IMMINENT_RX.search(label))


def _typical_onset(domain: str) -> int:
    return int(_TYPICAL_ONSET_AGE.get((domain or "universal").lower(), 20))


def _heuristic_fail(
    *,
    domain: str,
    user_age: int,
    locked: dict[str, Any] | None,
    now_year: int | None = None,
) -> tuple[bool, list[str]]:
    """Return (failed, issues). Soft check before/alongside LLM."""
    issues: list[str] = []
    onset = _typical_onset(domain)
    cy = now_year if now_year is not None else datetime.now().year
    y = _window_start_year(locked)
    age_at = _age_at_year(user_age, y, cy)

    if age_at is not None and age_at < onset:
        issues.append(f"age_at_window_{age_at}_below_typical_onset_{onset}")
    if _is_imminent_window(locked, cy) and user_age < onset:
        issues.append(f"imminent_window_while_age_{user_age}_below_onset_{onset}")

    try:
        from event_timing._shared.practical_manifestation_filter import min_eligible_age

        floor = min_eligible_age(domain, "")
        if age_at is not None and age_at < floor:
            issues.append(f"age_at_window_{age_at}_below_pmf_floor_{floor}")
    except Exception:
        pass

    return bool(issues), issues


def _build_llm_prompt(
    *,
    question: str,
    domain: str,
    user_age: int,
    windows: list[dict[str, Any]],
    candidate_idx: int,
    heuristic_issues: list[str],
) -> str:
    from event_timing._shared.timing_window_pick import window_range_label

    rows = []
    for i, w in enumerate(windows[:5]):
        mark = " ← CANDIDATE UNDER REVIEW" if i == candidate_idx else ""
        y = _window_start_year(w)
        age_at = _age_at_year(user_age, y)
        rows.append(
            f"#{i + 1}: label={window_range_label(w) or w.get('window') or '—'} | "
            f"start={w.get('start') or '—'} | end={w.get('end') or '—'} | "
            f"lords={w.get('lords') or '—'} | age_at_window≈{age_at if age_at is not None else '—'}{mark}"
        )
    window_block = "\n".join(rows) if rows else "(no ranked windows)"
    onset = _typical_onset(domain)
    issues_txt = ", ".join(heuristic_issues) if heuristic_issues else "none"
    cand = windows[candidate_idx] if 0 <= candidate_idx < len(windows) else {}
    cand_label = window_range_label(cand) if cand else "—"

    return f"""You are a strict Vedic timing QA verifier (NOT a narrator).
Compare USER AGE + QUESTION + this CANDIDATE DASHA window. Say if they MATCH.

USER AGE NOW: {user_age}
TIMING DOMAIN: {domain}
TYPICAL REALISTIC AGE for this event: ~{onset}+
USER QUESTION: {(question or "").strip()[:400] or "—"}

CANDIDATE DASHA WINDOW: #{candidate_idx + 1} → {cand_label}

ALL RANKED DASHAS (engine order — if mismatch, we take the NEXT one only):
{window_block}

HEURISTIC FLAGS: {issues_txt}

MATCH = true when:
- Age at this dasha window is realistic for the asked event, AND
- This dasha answers "kab" for the question without being unrealistically early.

MATCH = false when:
- Dasha is "abhi"/imminent but age is early for this event, OR
- Age at window is below typical onset, OR
- Dasha does not fit the question + age together.

IMPORTANT:
- Do NOT invent dates.
- Do NOT jump randomly to a far window — if mismatch, we always take the NEXT dasha in list order.
- Same question asked again must keep the SAME matched dasha (stability).

Return ONLY JSON:
{{
  "match": true/false,
  "issues": ["..."],
  "lock_note": "one short narrator note",
  "reason": "short"
}}
"""


def _llm_verify_match(
    client: Any,
    model: str,
    *,
    question: str,
    domain: str,
    user_age: int,
    windows: list[dict[str, Any]],
    candidate_idx: int,
    heuristic_issues: list[str],
) -> dict[str, Any]:
    prompt = _build_llm_prompt(
        question=question,
        domain=domain,
        user_age=user_age,
        windows=windows,
        candidate_idx=candidate_idx,
        heuristic_issues=heuristic_issues,
    )
    judge_model = timing_age_dasha_guard_model(model)
    try:
        resp = client.chat.completions.create(
            model=judge_model,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Verify age + question + dasha match. "
                        "JSON only. If mismatch we take next dasha. Do not invent dates."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            max_tokens=180,
        )
        raw = (resp.choices[0].message.content or "").strip()
        parsed = _parse_judge_json(raw)
        if not parsed:
            return {
                "match": None,
                "soft_pass_empty_json": True,
                "raw": raw[:400],
                "model": judge_model,
            }
        # Accept either "match" or legacy "passed"
        if "match" in parsed:
            matched = bool(parsed.get("match"))
        else:
            matched = bool(parsed.get("passed", True))
        return {
            "match": matched,
            "issues": [str(x) for x in (parsed.get("issues") or []) if str(x).strip()],
            "lock_note": str(parsed.get("lock_note") or "").strip()[:320],
            "reason": str(parsed.get("reason") or "").strip()[:240],
            "model": judge_model,
            "parsed": parsed,
        }
    except Exception as exc:
        return {
            "match": None,
            "soft_pass_on_error": True,
            "error": str(exc)[:160],
            "model": judge_model,
        }


def _wants_next_timing_window(question: str, history: Any) -> bool:
    try:
        from event_timing._shared.timing_window_pick import (
            detect_later_timing_window_question,
            detect_next_timing_window_question,
        )

        q = question or ""
        if detect_later_timing_window_question(q):
            return True
        if detect_next_timing_window_question(q, history):
            return True
    except Exception:
        pass
    return False


def _first_age_ok_index(
    windows: list[dict[str, Any]],
    *,
    domain: str,
    user_age: int,
    start_at: int = 0,
) -> int:
    """Walk dashas in order until age matches; last window if none."""
    if not windows:
        return 0
    start = max(0, min(start_at, len(windows) - 1))
    for i in range(start, len(windows)):
        fail, _ = _heuristic_fail(domain=domain, user_age=user_age, locked=windows[i])
        if not fail:
            return i
    return len(windows) - 1


def _stamp_engine(engine_raw: dict[str, Any], audit: dict[str, Any], picked: dict[str, Any]) -> None:
    try:
        engine_raw["age_dasha_guard"] = audit
        engine_raw["locked_answer_window"] = (
            picked.get("window") or f"{picked.get('start')}→{picked.get('end')}"
        )
        engine_raw["answer_window"] = picked
        # Stable fingerprint — same windows + age → same lock on re-ask
        engine_raw["age_dasha_stable_key"] = (
            f"{picked.get('start')}|{picked.get('end')}|{picked.get('lords')}|{picked.get('window')}"
        )
    except Exception:
        pass


def _rewrite_locked_block(
    block: str,
    *,
    picked: dict[str, Any],
    rank: int,
    lock_note: str,
) -> str:
    from event_timing._shared.timing_window_pick import window_range_label

    label = window_range_label(picked) or str(picked.get("window") or "").strip()
    lords = str(picked.get("lords") or "").strip()
    if not lords:
        lords = "/".join(
            x for x in (picked.get("md"), picked.get("ad"), picked.get("pd")) if x
        )

    lines = []
    for line in (block or "").splitlines():
        s = line.strip()
        if s.startswith(">>> NARRATE THIS WINDOW"):
            continue
        if s.startswith(">>> AGE-DASHA GUARD"):
            continue
        if s.startswith(">>> STABLE TIMING LOCK"):
            continue
        if s.startswith("=== AGE–DASHA LLM VERIFY") or s.startswith("=== AGE-DASHA LLM VERIFY"):
            continue
        lines.append(line)
    cleaned = "\n".join(lines).rstrip()

    narrate = (
        f">>> NARRATE THIS WINDOW EXACTLY AS (#{rank + 1} — age/dasha verified): {label}"
    )
    guard_lines = [
        "",
        "=== AGE-DASHA LLM VERIFY (LOCKED — bind narrator) ===",
        narrate,
        ">>> STABLE TIMING LOCK: agar user SAME timing question dubara pooche "
        "(bina agla/next), YAHI window/dates do — timing change mat karo.",
    ]
    if lords:
        guard_lines.append(f"Verified dasha lords: {lords}")
    if lock_note:
        guard_lines.append(f">>> AGE-DASHA GUARD: {lock_note.strip()[:320]}")
    guard_lines.append(
        "Flow: age + question → check dasha match → mismatch pe NEXT dasha only."
    )
    return (cleaned + "\n" + "\n".join(guard_lines) + "\n").strip() + "\n"


def apply_timing_age_dasha_guard(
    *,
    client: Any,
    model: str = "gpt-4.1-mini",
    question: str,
    domain: str,
    birth: Any = None,
    kundli: Any = None,
    engine_raw: dict[str, Any] | None,
    prompt_block: str,
    user_age: Optional[int] = None,
    history: Any = None,
    skip_marriage: bool = True,
) -> tuple[str, dict[str, Any]]:
    """Age + question vs dasha: match → lock; else next dasha. Stable on re-ask.

    Marriage excluded. Repeat of the same timing Q (no agla/next) keeps the
    same verified window — timing must not drift.
    """
    audit: dict[str, Any] = {
        "guard": "timing_age_dasha_v2",
        "enabled": timing_age_dasha_guard_enabled(),
    }
    block = prompt_block or ""
    dom = (domain or "").strip().lower() or _domain_from_engine_id(
        str((engine_raw or {}).get("engine_id") or "")
    )

    if skip_marriage and dom == "marriage":
        audit["skipped"] = "marriage_excluded"
        return block, audit
    if not timing_age_dasha_guard_enabled():
        audit["skipped"] = "ASK_TIMING_AGE_DASHA_GUARD=0"
        return block, audit
    if not (block or "").strip():
        audit["skipped"] = "empty_block"
        return block, audit
    if not isinstance(engine_raw, dict) or not engine_raw:
        audit["skipped"] = "no_engine_raw"
        return block, audit

    age = user_age
    if age is None:
        try:
            from ask_career.timing_registry import resolve_user_age

            age = resolve_user_age(question or "", birth, kundli)
        except Exception:
            age = None
    if age is None:
        try:
            age = int((engine_raw.get("user_age")
                       or (engine_raw.get("timing_eligibility") or {}).get("user_age")
                       or 0) or 0) or None
        except (TypeError, ValueError):
            age = None
    if age is None or int(age) <= 0:
        audit["skipped"] = "no_user_age"
        return block, audit
    age = int(age)
    audit["user_age"] = age
    audit["domain"] = dom

    from event_timing._shared.timing_window_pick import extract_ranked_timing_windows

    windows = extract_ranked_timing_windows(engine_raw)
    if not windows:
        audit["skipped"] = "no_windows"
        return block, audit

    wants_next = _wants_next_timing_window(question or "", history)
    audit["wants_next"] = wants_next

    # Stable base: first age-OK dasha (NOT history-bumped — that changed timing on re-ask).
    base_idx = _first_age_ok_index(windows, domain=dom, user_age=age, start_at=0)
    if wants_next:
        # Explicit agla/next only — then step forward from age-matched base.
        start_idx = min(base_idx + 1, len(windows) - 1)
    else:
        start_idx = base_idx

    idx = start_idx
    llm_trace: list[dict[str, Any]] = []
    lock_note = ""
    final_reason = "heuristic_age_walk"

    # Walk: check dasha vs age+question; mismatch → NEXT dasha only.
    while idx < len(windows):
        cand = windows[idx]
        heur_fail, heur_issues = _heuristic_fail(
            domain=dom, user_age=age, locked=cand,
        )
        matched: Optional[bool]
        if client is not None:
            llm_result = _llm_verify_match(
                client,
                model,
                question=question or "",
                domain=dom,
                user_age=age,
                windows=windows,
                candidate_idx=idx,
                heuristic_issues=heur_issues,
            )
            llm_trace.append({"idx": idx, **{
                k: llm_result.get(k)
                for k in ("match", "issues", "reason", "error", "soft_pass_on_error")
                if k in llm_result
            }})
            if llm_result.get("lock_note"):
                lock_note = str(llm_result.get("lock_note") or "")
            m = llm_result.get("match")
            if m is None:
                # Soft: trust heuristic only
                matched = not heur_fail
            else:
                matched = bool(m)
                # Imminent+young heuristic still forces next even if LLM says match
                if matched and heur_fail and any(
                    x.startswith("imminent_window") or "below_typical_onset" in x
                    for x in heur_issues
                ):
                    matched = False
                    final_reason = "heuristic_override_llm_match"
        else:
            matched = not heur_fail
            llm_trace.append({"idx": idx, "match": matched, "heuristic_only": True})

        if matched:
            final_reason = final_reason if final_reason == "heuristic_override_llm_match" else (
                "llm_match" if client is not None else "heuristic_match"
            )
            break

        # Mismatch → next dasha
        if idx >= len(windows) - 1:
            final_reason = "exhausted_use_last"
            break
        idx += 1
        final_reason = "advance_next_dasha"

    picked = dict(windows[idx])
    audit["llm_trace"] = llm_trace
    audit["picked_rank"] = idx + 1
    audit["picked_window"] = picked.get("window") or picked.get("start")
    audit["base_age_ok_rank"] = base_idx + 1
    audit["result"] = "locked"
    audit["reason"] = final_reason

    if not lock_note:
        from event_timing._shared.timing_window_pick import window_range_label

        label = window_range_label(picked) or str(picked.get("window") or "")
        lock_note = (
            f"Age {age} + question matched to dasha #{idx + 1}: {label}. "
            f"Same Q dubara → yahi timing."
        )

    new_block = _rewrite_locked_block(
        block, picked=picked, rank=idx, lock_note=lock_note,
    )
    _stamp_engine(engine_raw, audit, picked)
    return new_block, audit
