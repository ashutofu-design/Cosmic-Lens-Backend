#!/usr/bin/env python3
"""
Generate full Love Reality Pro PDF for local preview (ReportLab = production).

Output:
  artifacts/love-reality-report/public/preview-report.pdf
  artifacts/love-reality-report/public/preview-report-meta.json

Default: reuse preview-verdict-llm.json when present; else built-in Aarav/Riya prose (no dev labels).
Optional: LOVE_REALITY_VERDICT_PAGE_LLM=1 — OpenAI Section 02 (frozen — avoid re-calling).
Optional: LOVE_REALITY_DEEP_ANALYSIS_LLM=1 — OpenAI Section 03 only (Deep Connection Analysis).
Optional: LOVE_REALITY_PREMIUM_SECTIONS=1 — full per-section assembly (S02–S11, production parity).
Cost savers (local preview):
  - Default model gpt-4o-mini (override: LOVE_REALITY_VERDICT_PAGE_MODEL)
  - File cache in .cache/love_polish/ — re-run without --force = free
  - --dev — shorter output, max_tokens ~1400
  - --reuse — load preview-verdict-llm.json, zero OpenAI (layout-only tweaks)
  - --force — skip cache (use only after prompt change)
"""
from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

_API = Path(__file__).resolve().parents[1]
_REPO = _API.parent / "love-reality-report" / "public"
if str(_API) not in sys.path:
    sys.path.insert(0, str(_API))

# Load artifacts/api-server/.env (OPENAI_API_KEY) when running gen script directly
try:
    from dotenv import load_dotenv

    load_dotenv(_API / ".env", override=True)
except ImportError:
    pass


def _count_pages(pdf: bytes) -> int:
    return len(re.findall(rb"/Type\s*/Page(?!s)", pdf))


def _env_on(name: str) -> bool:
    return (os.environ.get(name) or "").strip().lower() in ("1", "true", "yes", "on")


def _builtin_deep_analysis() -> list[dict]:
    """Section 03 fallback — p1-centric, no generic placeholder."""
    return [
        {
            "key": "emotional",
            "explanation": (
                "Aarav, you bring feelings up fast — your Aries Moon pushes you to react before you cool down. "
                "When Riya needs quiet inside, you read it as distance growing. That's not less love; it's a different emotional speed."
            ),
        },
        {
            "key": "communication",
            "explanation": (
                "Aarav, when you want an answer now and Riya goes still, you often misread her tone. "
                "In Mercury-sensitive weeks a small delay can feel like disrespect — your chart trains you to speak before the heat drops."
            ),
        },
        {
            "key": "trust",
            "explanation": (
                "Aarav, you measure trust through consistency — when Riya is silent, your mind fills the gap with worst-case stories. "
                "The chart flags trust eroding when you treat pause as rejection, not processing."
            ),
        },
        {
            "key": "long_term",
            "explanation": (
                "Aarav, this bond has warmth but without repair habits the same six-to-eight month loop returns. "
                "Your chart holds long-term when you stop trying to fix everything in the peak of anger."
            ),
        },
    ]


def _rich_pro() -> dict:
    body = (
        "Chart signals for this theme are active between both partners. "
        "Daily rhythm and repair style shape how this score lands in real life. "
        "When stress rises, the pattern repeats unless named within 24 hours."
    )
    keys = [
        "love_connection",
        "breakup",
        "loyalty",
        "will_return",
        "future_outcome",
        "red_flags",
    ]
    return {
        "hidden_truth": "Something unspoken still binds you — naming it changes the tone.",
        "verdict": (
            "Aarav, when something feels off, you move to fix it right away — you want the answer now. "
            "Your chart pushes you to react before you cool down. When Riya goes quiet, you feel shut out; "
            "she needs time inside before she can speak. The more you push for closure, the more she pulls back — "
            "and you read that as proof she doesn't care. Your chart shows real pull here; Venus fuels the attraction, "
            "but when you chase an answer and she goes still, the same fight returns."
        ),
        "practical": [
            (
                "Aarav, when you want an answer now and Riya is still processing inside, you feel pressure "
                "building — she feels pushed. You tend to read her silence as rejection when for her it's a pause. "
                "That misread is the loop your chart keeps flagging."
            ),
            (
                "Mercury-sensitive weeks hit you hard — a late reply lands like an insult on your side. "
                "You carry enough warmth in this bond for small bumps to pass; the gap opens when you fill "
                "her silence with the worst guess, not when love is actually missing."
            ),
        ],
        "chapters": [
            {
                "key": k,
                "title": k.replace("_", " ").title(),
                "score_0_10": 7.2,
                "chapter_body": body,
                "full_read": body,
            }
            for k in keys
        ],
        "special": ["Emotional magnetism runs high under calm conditions."],
        "damage": ["Silence beyond 48 hours erodes loyalty scores fastest."],
        "deep_analysis": _builtin_deep_analysis(),
    }


def _sample_payload() -> dict:
    return {
        "report_id": "LR-PREVIEW",
        "p1": {"name": "Aarav", "nakshatra": "Ashwini", "rashi": "Aries"},
        "p2": {"name": "Riya", "nakshatra": "Pushya", "rashi": "Cancer"},
        "pro_premium": _rich_pro(),
        "love_compatibility": {
            "score": 72,
            "insight": "Strong mutual pull with uneven emotional pacing.",
            "emotional_summary": (
                "Strong mutual pull with uneven emotional pacing. Attraction is authentic; "
                "friction spikes when silence replaces repair. Next 90 days favor honest conversations."
            ),
            "reasons": [
                "Moon rhythm mismatch — emotional pacing differs between partners.",
                "Venus–Mars axis drives attraction but also jealousy triggers.",
            ],
            "score_ledger": [
                {"label": "Base synastry", "base": 52, "note": "Moon–Venus anchor"},
                {"label": "Dasha alignment", "delta": 12, "note": "Favorable window"},
                {"label": "Repair bonus", "delta": 8, "note": "Communication potential"},
            ],
        },
        "breakup_chances": {
            "score": 58,
            "reasons": ["Mercury stress windows amplify misread signals."],
        },
        "loyalty_check": {"score": 64},
        "will_return": {"score": 41},
        "future_outcome": {"score": 61},
        "narrative_bridge": "Repair within 48 hours — silence beyond that is the highest-risk behavior.",
        "chart_snapshot": {"lines": ["Moon: Aries", "Venus: Taurus house 7"]},
        "chapter_groundings": {"love_connection": "Engine score 72/100."},
    }


def _verdict_snapshot_path() -> Path:
    return _REPO / "preview-verdict-llm.json"


def _load_verdict_snapshot() -> dict | None:
    """Load last saved Section 02 prose (free — no OpenAI)."""
    snap_path = _verdict_snapshot_path()
    if not snap_path.is_file():
        return None
    try:
        data = json.loads(snap_path.read_text(encoding="utf-8"))
        if not data.get("verdict"):
            return None
        meta = dict(data.get("_meta") or {})
        meta["cache"] = "preview_snapshot"
        meta["openai_skipped"] = True
        data["_meta"] = meta
        return data
    except Exception as exc:
        print(f"WARN: snapshot read failed ({exc})")
        return None


def _try_reuse_verdict_snapshot(force: bool) -> dict | None:
    """Explicit --reuse only (legacy flag); default path uses _load_verdict_snapshot."""
    if force:
        return None
    if not _env_on("LOVE_REALITY_VERDICT_PAGE_REUSE_SNAPSHOT"):
        return None
    data = _load_verdict_snapshot()
    if data:
        print(f"Section 02: reusing snapshot (no OpenAI) -> {_verdict_snapshot_path()}")
    else:
        print("WARN: --reuse requested but preview-verdict-llm.json missing — will call OpenAI or cache")
    return data


def _print_verdict_cost_hint(meta: dict, *, force: bool) -> None:
    cache = meta.get("cache")
    if cache in ("verdict_page_file", "preview_snapshot"):
        print(f"Section 02: cache hit ({cache}) — no OpenAI cost")
        return
    if meta.get("openai_skipped"):
        print(f"Section 02: OpenAI skipped ({meta.get('reason', 'unknown')})")
        return
    model = meta.get("model") or "?"
    max_tok = meta.get("max_tokens") or "?"
    print(f"Section 02: OpenAI call model={model} max_tokens={max_tok}")
    if force:
        print("TIP: --force / LOVE_REALITY_VERDICT_PAGE_FORCE skips cache every run — omit for free re-runs")
    else:
        print("TIP: same prompt + sample couple → next run uses file cache (free)")


def _apply_section02(pro: dict, llm: dict) -> None:
    if llm.get("verdict"):
        pro["verdict"] = llm["verdict"]
    if llm.get("practical"):
        pro["practical"] = llm["practical"]


def _save_verdict_snapshot(pro: dict, meta: dict) -> None:
    snap_path = _verdict_snapshot_path()
    snap_path.write_text(
        json.dumps(
            {
                "verdict": pro.get("verdict"),
                "practical": pro.get("practical"),
                "_meta": meta,
            },
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    print(f"Section 02 snapshot -> {snap_path}")


def _merge_verdict_llm(payload: dict) -> tuple[dict, str]:
    """Section 02: snapshot (default) → optional OpenAI → built-in couple prose."""
    pro = dict(payload.get("pro_premium") or _rich_pro())
    force = _env_on("LOVE_REALITY_VERDICT_PAGE_FORCE")
    llm_enabled = _env_on("LOVE_REALITY_VERDICT_PAGE_LLM")

    if not force:
        snap = _load_verdict_snapshot()
        if snap:
            _apply_section02(pro, snap)
            print(f"Section 02: loaded from {_verdict_snapshot_path().name} (no OpenAI)")
            return pro, "snapshot_reuse"

    if not llm_enabled:
        print("Section 02: built-in Aarav/Riya prose (run pnpm gen:pdf:verdict-llm:force for fresh LLM)")
        return pro, "builtin_prose"

    if force:
        print("NOTE: LOVE_REALITY_VERDICT_PAGE_FORCE=1 — fresh OpenAI call for Section 02")

    reused = _try_reuse_verdict_snapshot(force)
    if reused:
        llm = reused
    else:
        from vedic.love_reality.chart_facts import enrich_bundle_for_pdf
        from vedic.love_reality.premium_polish import polish_love_reality_verdict_page_only

        bundle = {k: v for k, v in payload.items() if k != "pro_premium"}
        bundle = enrich_bundle_for_pdf(bundle)
        llm = polish_love_reality_verdict_page_only(bundle, lang="en", force_llm=force)

    meta = dict(llm.get("_meta") or {})
    if llm.get("verdict"):
        _apply_section02(pro, llm)
        source = "llm_verdict_page"
    else:
        print(f"WARN: verdict LLM skipped ({meta.get('reason', 'unknown')}) — using built-in Section 02")
        source = f"builtin_prose ({meta.get('reason', 'llm_miss')})"

    _print_verdict_cost_hint(meta, force=force)
    if pro.get("verdict"):
        _save_verdict_snapshot(pro, meta)

    return pro, source


def _deep_analysis_snapshot_path() -> Path:
    return _REPO / "preview-deep-analysis-llm.json"


def _load_deep_analysis_snapshot() -> dict | None:
    snap_path = _deep_analysis_snapshot_path()
    if not snap_path.is_file():
        return None
    try:
        data = json.loads(snap_path.read_text(encoding="utf-8"))
        if isinstance(data.get("deep_analysis"), list) and len(data["deep_analysis"]) >= 4:
            return data
    except Exception as exc:
        print(f"WARN: deep analysis snapshot read failed ({exc})")
    return None


def _save_deep_analysis_snapshot(pro: dict, meta: dict) -> None:
    snap_path = _deep_analysis_snapshot_path()
    snap_path.write_text(
        json.dumps(
            {"deep_analysis": pro.get("deep_analysis"), "_meta": meta},
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    print(f"Section 03 snapshot -> {snap_path}")


def _merge_deep_analysis_llm(payload: dict, pro: dict) -> tuple[dict, str]:
    """Section 03: snapshot (default) → optional OpenAI → built-in blocks."""
    force = _env_on("LOVE_REALITY_DEEP_ANALYSIS_FORCE")
    llm_enabled = _env_on("LOVE_REALITY_DEEP_ANALYSIS_LLM")

    if not force:
        snap = _load_deep_analysis_snapshot()
        if snap and snap.get("deep_analysis"):
            pro["deep_analysis"] = snap["deep_analysis"]
            print(f"Section 03: loaded from {_deep_analysis_snapshot_path().name} (no OpenAI)")
            return pro, "snapshot_reuse"

    if not llm_enabled:
        if not pro.get("deep_analysis"):
            pro["deep_analysis"] = _builtin_deep_analysis()
        print("Section 03: built-in blocks (run pnpm gen:pdf:deep-analysis-llm:force for fresh LLM)")
        return pro, "builtin_prose"

    if force:
        print("NOTE: LOVE_REALITY_DEEP_ANALYSIS_FORCE=1 — fresh OpenAI call for Section 03")

    from vedic.love_reality.chart_facts import enrich_bundle_for_pdf
    from vedic.love_reality.premium_polish import polish_love_reality_deep_analysis_only

    bundle = {k: v for k, v in payload.items() if k != "pro_premium"}
    bundle = enrich_bundle_for_pdf(bundle)
    llm = polish_love_reality_deep_analysis_only(bundle, lang="en", force_llm=force)
    meta = dict(llm.get("_meta") or {})

    if llm.get("deep_analysis"):
        pro["deep_analysis"] = llm["deep_analysis"]
        source = "llm_deep_analysis"
    else:
        pro.setdefault("deep_analysis", _builtin_deep_analysis())
        print(f"WARN: deep analysis LLM skipped ({meta.get('reason', 'unknown')}) — using built-in Section 03")
        source = f"builtin_prose ({meta.get('reason', 'llm_miss')})"

    if pro.get("deep_analysis"):
        _save_deep_analysis_snapshot(pro, meta)

    return pro, source


def _section_assembly_enabled() -> bool:
    return _env_on("LOVE_REALITY_PREMIUM_SECTIONS") or _env_on("LOVE_REALITY_SECTION_LLM")


def _merge_premium_sections(payload: dict) -> tuple[dict, str]:
    """Production parity — all section LLM calls via polish_love_reality_premium."""
    from vedic.love_reality.chart_facts import enrich_bundle_for_pdf
    from vedic.love_reality.premium_polish import _polish_enabled, polish_love_reality_premium

    if not _polish_enabled():
        return _rich_pro(), "builtin_prose (polish_off)"

    force = (
        _env_on("LOVE_REALITY_FORCE")
        or _env_on("LOVE_REALITY_PREMIUM_SECTIONS_FORCE")
        or _env_on("LOVE_REALITY_VERDICT_PAGE_FORCE")
        or _env_on("LOVE_REALITY_DEEP_ANALYSIS_FORCE")
    )
    if force:
        print("NOTE: section assembly force — fresh OpenAI for all LLM sections")

    bundle = {k: v for k, v in payload.items() if k != "pro_premium"}
    bundle = enrich_bundle_for_pdf(bundle)
    pro = polish_love_reality_premium(bundle, lang="en", force_llm=force)
    meta = pro.get("_meta") or {}
    sections = meta.get("sections") or {}

    if pro.get("verdict") and meta.get("assembly"):
        skipped = [k for k, v in sections.items() if (v or {}).get("openai_skipped")]
        source = "section_assembly"
        if skipped:
            source += f" (skipped: {', '.join(skipped)})"
        if pro.get("verdict"):
            _save_verdict_snapshot(pro, sections.get("verdict_page") or meta)
        if pro.get("deep_analysis"):
            _save_deep_analysis_snapshot(pro, sections.get("deep_analysis") or meta)
        return pro, source

    print(f"WARN: section assembly incomplete ({meta.get('reason', 'partial')}) — partial merge")
    pro, s02 = _merge_verdict_llm(payload)
    pro, s03 = _merge_deep_analysis_llm(payload, pro)
    return pro, f"fallback s02={s02}, s03={s03}"


def main() -> None:
    from love_reality_pdf import render_love_reality_pro_pdf

    _REPO.mkdir(parents=True, exist_ok=True)
    payload = _sample_payload()
    if _section_assembly_enabled():
        pro, premium_source = _merge_premium_sections(payload)
        section02_source = premium_source
        section03_source = premium_source
    else:
        pro, section02_source = _merge_verdict_llm(payload)
        pro, section03_source = _merge_deep_analysis_llm(payload, pro)
        premium_source = None
    payload["pro_premium"] = pro

    pdf = render_love_reality_pro_pdf(payload, lang="en")
    pdf_path = _REPO / "preview-report.pdf"
    meta_path = _REPO / "preview-report-meta.json"
    pages = _count_pages(pdf)
    pdf_path.write_bytes(pdf)
    meta = {
        "pages": pages,
        "report_id": payload["report_id"],
        "couple": f"{payload['p1']['name']} & {payload['p2']['name']}",
        "section02_source": section02_source,
        "section03_source": section03_source,
        "premium_source": premium_source,
        "description": "Full Love Reality Pro report (ReportLab preview).",
        "generated_by": "artifacts/api-server/scripts/gen_love_exec_preview_pdf.py",
    }
    meta_path.write_text(json.dumps(meta, indent=2), encoding="utf-8")
    print(f"OK: {pages} PDF page(s) -> {pdf_path}")
    print(f"Section 02 source: {section02_source}")
    print(f"Section 03 source: {section03_source}")
    print(f"Meta: {meta_path}")


if __name__ == "__main__":
    main()
