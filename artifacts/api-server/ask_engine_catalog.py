"""Canonical Ask engine numbers for admin — static, gap, timing, special."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

# Stable admin IDs — do not renumber once published.
ENGINE_CATALOG: tuple[dict[str, Any], ...] = (
    # Static domain engines (1–12)
    {"no": 1, "slice": "education_engine_v1", "key": "education", "kind": "static", "label": "Education"},
    {"no": 2, "slice": "children_engine_v1", "key": "children", "kind": "static", "label": "Children"},
    {"no": 3, "slice": "property_engine_v1", "key": "property", "kind": "static", "label": "Property"},
    {"no": 4, "slice": "vehicle_engine_v1", "key": "vehicle", "kind": "static", "label": "Vehicle"},
    {"no": 5, "slice": "travel_engine_v1", "key": "travel", "kind": "static", "label": "Travel"},
    {"no": 6, "slice": "litigation_engine_v1", "key": "litigation", "kind": "static", "label": "Litigation"},
    {"no": 7, "slice": "network_engine_v1", "key": "network", "kind": "static", "label": "Network"},
    {"no": 8, "slice": "luck_engine_v1", "key": "luck", "kind": "static", "label": "Luck"},
    {"no": 9, "slice": "career_engine_v1", "key": "career", "kind": "static", "label": "Career"},
    {"no": 10, "slice": "finance_engine_v1", "key": "finance", "kind": "static", "label": "Finance"},
    {"no": 11, "slice": "health_engine_v1", "key": "health", "kind": "static", "label": "Health"},
    {"no": 12, "slice": "mr_engine_v1", "key": "mr", "kind": "static", "label": "Love / Marriage"},
    # Gap sub-engines (13–26)
    {"no": 13, "slice": "siblings_engine_v1", "key": "siblings", "kind": "static", "label": "Siblings"},
    {"no": 14, "slice": "spiritual_engine_v1", "key": "spiritual", "kind": "static", "label": "Spiritual (static)"},
    {"no": 15, "slice": "parents_engine_v1", "key": "parents", "kind": "static", "label": "Parents"},
    {"no": 16, "slice": "enemies_engine_v1", "key": "enemies", "kind": "static", "label": "Enemies"},
    {"no": 17, "slice": "fame_engine_v1", "key": "fame", "kind": "static", "label": "Fame (static)"},
    {"no": 18, "slice": "personality_engine_v1", "key": "personality", "kind": "static", "label": "Personality"},
    {"no": 19, "slice": "dreams_engine_v1", "key": "dreams", "kind": "static", "label": "Dreams"},
    {"no": 20, "slice": "anger_engine_v1", "key": "anger", "kind": "static", "label": "Anger"},
    {"no": 21, "slice": "remedy_engine_v1", "key": "remedy", "kind": "static", "label": "Remedy"},
    {"no": 22, "slice": "charity_engine_v1", "key": "charity", "kind": "static", "label": "Charity"},
    {"no": 23, "slice": "settlement_engine_v1", "key": "settlement", "kind": "static", "label": "Settlement"},
    {"no": 24, "slice": "vastu_engine_v1", "key": "vastu", "kind": "static", "label": "Vastu"},
    {"no": 25, "slice": "pets_engine_v1", "key": "pets", "kind": "static", "label": "Pets"},
    {"no": 26, "slice": "wellness_engine_v1", "key": "wellness", "kind": "static", "label": "Wellness"},
    # Special static (27–31)
    {"no": 27, "slice": "open_chart_qa_engine_v1", "key": "open_chart_qa", "kind": "special", "label": "Open chart Q&A"},
    {"no": 28, "slice": "love_static_engine_v1", "key": "love_static", "kind": "special", "label": "Love static"},
    {"no": 29, "slice": "milan_engine_v1", "key": "milan", "kind": "special", "label": "Kundli Milan"},
    {"no": 30, "slice": "chart_fact", "key": "chart_fact", "kind": "special", "label": "Chart fact (deterministic)"},
    {"no": 31, "slice": "gap_engine_v1", "key": "gap", "kind": "static", "label": "Gap router"},
    # Timing engines (32–47)
    {"no": 32, "slice": "marriage_timing_m17", "key": "marriage", "kind": "timing", "label": "Marriage timing (M17)"},
    {"no": 33, "slice": "love_timing_v1", "key": "love", "kind": "timing", "label": "Love timing"},
    {"no": 34, "slice": "career_timing_v1", "key": "career", "kind": "timing", "label": "Career timing"},
    {"no": 35, "slice": "travel_timing_v1", "key": "travel", "kind": "timing", "label": "Travel timing"},
    {"no": 36, "slice": "property_timing_v1", "key": "property", "kind": "timing", "label": "Property timing"},
    {"no": 37, "slice": "vehicle_timing_v1", "key": "vehicle", "kind": "timing", "label": "Vehicle timing"},
    {"no": 38, "slice": "finance_timing_v1", "key": "finance", "kind": "timing", "label": "Finance timing"},
    {"no": 39, "slice": "health_timing_v1", "key": "health", "kind": "timing", "label": "Health timing"},
    {"no": 40, "slice": "children_timing_v1", "key": "children", "kind": "timing", "label": "Children timing"},
    {"no": 41, "slice": "education_timing_v1", "key": "education", "kind": "timing", "label": "Education timing"},
    {"no": 42, "slice": "foreign_education_timing_v1", "key": "foreign_education", "kind": "timing", "label": "Foreign education timing"},
    {"no": 43, "slice": "litigation_timing_v1", "key": "litigation", "kind": "timing", "label": "Litigation timing"},
    {"no": 44, "slice": "spiritual_timing_v1", "key": "spiritual", "kind": "timing", "label": "Spiritual timing"},
    {"no": 45, "slice": "fame_timing_v1", "key": "fame", "kind": "timing", "label": "Fame timing"},
    {"no": 46, "slice": "network_timing_v1", "key": "network", "kind": "timing", "label": "Network timing"},
    {"no": 47, "slice": "universal_timing_v1", "key": "universal", "kind": "timing", "label": "Universal timing (fallback)"},
)

_SLICE_INDEX: dict[str, dict[str, Any]] = {e["slice"]: e for e in ENGINE_CATALOG}
_KEY_TIMING_INDEX: dict[str, dict[str, Any]] = {
    e["key"]: e for e in ENGINE_CATALOG if e["kind"] == "timing"
}
_KEY_STATIC_INDEX: dict[str, dict[str, Any]] = {
    e["key"]: e for e in ENGINE_CATALOG if e["kind"] in ("static", "special")
}

# Spiritual timing buckets → engine #44 (not separate engines).
_SPIRITUAL_TIMING_BUCKETS = frozenset({
    "guru_deeksha",
    "occult_learning",
    "pilgrimage",
    "inner_peace",
    "general_spiritual",
})


@dataclass
class EngineDisplay:
    engine_no: int | None
    slice_id: str | None
    engine_key: str | None
    kind: str | None
    label: str | None
    archetype: str | None
    admin_line: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _entry_by_slice(slice_id: str | None) -> dict[str, Any] | None:
    sl = (slice_id or "").strip()
    if not sl:
        return None
    if sl in _SLICE_INDEX:
        return _SLICE_INDEX[sl]
    if sl.endswith("_timing_v1") and sl not in _SLICE_INDEX:
        return {"no": None, "slice": sl, "key": sl.replace("_timing_v1", ""), "kind": "timing", "label": sl}
    return None


def _entry_by_key(engine_key: str | None, *, is_timing: bool) -> dict[str, Any] | None:
    key = (engine_key or "").strip().lower()
    if not key:
        return None
    if is_timing:
        return _KEY_TIMING_INDEX.get(key)
    entry = _KEY_STATIC_INDEX.get(key)
    if entry:
        return entry
    # gap sub-keys routed via gap_static_key
    for e in ENGINE_CATALOG:
        if e["key"] == key and e["kind"] == "static" and e["slice"].endswith("_engine_v1"):
            return e
    return _KEY_TIMING_INDEX.get(key) if key in _KEY_TIMING_INDEX else None


def resolve_engine_display(
    *,
    slice_id: str | None = None,
    engine_key: str | None = None,
    archetype: str | None = None,
    is_timing: bool = False,
    engine_trace_engine: str | None = None,
    gap_static_key: str | None = None,
) -> EngineDisplay:
    """Resolve admin engine number + line from slice, key, trace, or archetype."""
    arch = (archetype or "").strip() or None
    trace_sl = (engine_trace_engine or "").strip() or None
    gap_key = (gap_static_key or "").strip().lower() or None

    entry: dict[str, Any] | None = None
    resolved_slice: str | None = None

    for candidate in (trace_sl, slice_id, None):
        if candidate:
            entry = _entry_by_slice(candidate)
            if entry:
                resolved_slice = entry.get("slice") or candidate
                break

    if not entry and gap_key:
        gap_slice = f"{gap_key}_engine_v1"
        entry = _entry_by_slice(gap_slice)
        if entry:
            resolved_slice = entry.get("slice")

    if not entry:
        entry = _entry_by_key(engine_key, is_timing=is_timing)
        if entry:
            resolved_slice = entry.get("slice")

    # Timing bucket alone (e.g. occult_learning) → parent timing engine
    if not entry and arch and is_timing:
        if arch in _SPIRITUAL_TIMING_BUCKETS:
            entry = _SLICE_INDEX.get("spiritual_timing_v1")
            resolved_slice = "spiritual_timing_v1"
        else:
            for e in ENGINE_CATALOG:
                if e["kind"] == "timing" and arch.startswith(str(e["key"])):
                    entry = e
                    resolved_slice = e["slice"]
                    break

    if not entry and arch and not is_timing:
        # MR / domain archetype on known static slice
        pass

    no = entry.get("no") if entry else None
    kind = entry.get("kind") if entry else ("timing" if is_timing else "static")
    label = entry.get("label") if entry else None
    key = (entry.get("key") if entry else None) or (engine_key or "").strip().lower() or None
    sl_out = resolved_slice or trace_sl or (slice_id or "").strip() or None

    parts: list[str] = []
    if no is not None:
        parts.append(f"Engine #{no}")
    if sl_out:
        parts.append(sl_out)
    if arch and arch != sl_out and arch != key:
        parts.append(f"bucket: {arch}")
    elif arch and not sl_out:
        parts.append(arch)

    admin_line = " · ".join(parts) if parts else (arch or sl_out or key or "—")

    return EngineDisplay(
        engine_no=no,
        slice_id=sl_out,
        engine_key=key,
        kind=kind,
        label=label,
        archetype=arch,
        admin_line=admin_line,
    )


def enrich_admin_context_engine_display(
    ctx: dict[str, Any],
    *,
    llm_intent: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Attach engine_display to admin llm_context dict."""
    intent = llm_intent if isinstance(llm_intent, dict) else {}
    if not isinstance(ctx, dict):
        return ctx
    slice_meta = ctx.get("slice_meta") if isinstance(ctx.get("slice_meta"), dict) else {}
    blocks = ctx.get("blocks") if isinstance(ctx.get("blocks"), dict) else {}
    trace = blocks.get("engine_trace") or blocks.get("marriage_engine_trace") or blocks.get("career_engine_trace")
    trace_engine = None
    if isinstance(trace, dict):
        trace_engine = trace.get("engine")

    ev = ctx.get("engine_verification_summary")
    ev_arch = None
    if isinstance(ev, dict):
        ev_arch = ev.get("ran_archetype")

    engine_facts = ctx.get("engine_facts") if isinstance(ctx.get("engine_facts"), dict) else {}
    arch = (
        str(slice_meta.get("archetype") or engine_facts.get("archetype") or ev_arch or intent.get("routed_archetype") or "")
        .strip()
        or None
    )

    display = resolve_engine_display(
        slice_id=str(
            slice_meta.get("slice")
            or intent.get("engine_ran_slice")
            or (ctx.get("checks") or {}).get("slice_type")
            or ""
        ),
        engine_key=str(ctx.get("engine_ran") or intent.get("engine_ran") or ""),
        archetype=arch,
        is_timing=bool(ctx.get("is_timing") or ctx.get("question_type") == "TIMING"),
        engine_trace_engine=str(trace_engine or "") or None,
        gap_static_key=str(intent.get("gap_static_key") or ""),
    )
    out = dict(ctx)
    out["engine_display"] = display.to_dict()
    return out
