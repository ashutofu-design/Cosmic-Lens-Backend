"""
Line-by-line parity: in-app scroll sections must match page1 + pdf_context payload.
PDF renders only when every content line matches the server snapshot.
"""
from __future__ import annotations

import re
from typing import Any

_SCORE_IN_TEXT = re.compile(r"\d+\s*/\s*100")


def _norm_line(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").strip())


def _is_risk_metric(label: str) -> bool:
    return bool(
        re.search(
            r"breakup|risk|challenge|conflict|gap|stress|escalation|misalign",
            label or "",
            re.I,
        )
    )


def _human_score_band(score: int, label: str, lang: str = "en") -> str:
    v = max(0, min(100, round(score)))
    risk = _is_risk_metric(label)
    if lang == "hn":
        if risk:
            if v >= 70:
                return "Risk zyada"
            if v >= 45:
                return "Risk moderate"
            return "Risk kam"
        if v >= 70:
            return "Strong"
        if v >= 45:
            return "Mixed"
        if v >= 25:
            return "Low"
        return "Bahut kam"
    if lang == "hi":
        if risk:
            if v >= 70:
                return "जोखिम अधिक"
            if v >= 45:
                return "मध्यम जोखिम"
            return "कम जोखिम"
        if v >= 70:
            return "मजबूत"
        if v >= 45:
            return "मिश्रित"
        if v >= 25:
            return "कम"
        return "बहुत कम"
    if risk:
        if v >= 70:
            return "High risk"
        if v >= 45:
            return "Moderate risk"
        return "Lower risk"
    if v >= 70:
        return "Strong"
    if v >= 45:
        return "Mixed"
    if v >= 25:
        return "Low"
    return "Very low"


def _format_metric_line(
    label: str,
    value: int | None,
    interpretation: str | None,
    lang: str,
) -> str:
    v = value if value is not None else 0
    band = _human_score_band(v, label, lang)
    if interpretation and interpretation.lower() != band.lower():
        return f"{label}: {v}/100 — {band}"
    return f"{label}: {v}/100 — {band}"


def _pick_summary(primary: str | None, secondary: str | None) -> str:
    a = (primary or "").strip()
    b = (secondary or "").strip()
    if not a:
        return b
    if not b:
        return a
    a_start, b_start = a[:72].lower(), b[:72].lower()
    if (
        a_start == b_start
        or (len(a) >= 48 and a[:48] in b)
        or (len(b) >= 48 and b[:48] in a)
    ):
        return a if len(a) >= len(b) else b
    return a


def _insight_bullets_without_scores(items: list[Any] | None, max_n: int = 4) -> list[str]:
    out: list[str] = []
    for item in items or []:
        t = str(item or "").strip()
        if not t or _SCORE_IN_TEXT.search(t):
            continue
        out.append(t)
        if len(out) >= max_n:
            break
    return out


def _section_content_lines(sec: dict[str, Any]) -> list[str]:
    lines: list[str] = []
    body = str(sec.get("body") or "")
    for part in body.split("\n"):
        n = _norm_line(part)
        if n:
            lines.append(n)
    for bullet in sec.get("bullets") or []:
        n = _norm_line(str(bullet))
        if n:
            lines.append(n)
    rows = sec.get("table_rows") or sec.get("tableRows") or []
    if isinstance(rows, list):
        for row in rows:
            if not isinstance(row, list):
                continue
            for cell in row:
                n = _norm_line(str(cell))
                if n:
                    lines.append(n)
    return lines


def _push_section(sections: list[dict[str, Any]], sec: dict[str, Any] | None) -> None:
    if not sec:
        return
    lines = _section_content_lines(sec)
    if lines:
        sections.append(sec)


def build_in_app_page_sections(
    page1: dict[str, Any],
    pdf_context: dict[str, Any],
    lang: str = "en",
) -> list[dict[str, Any]]:
    """Mirror mobile buildLoveReportSectionsForPage — content fields only."""
    sections: list[dict[str, Any]] = []
    ctx = pdf_context or {}

    summary = _pick_summary(
        page1.get("relationship_summary"),
        page1.get("insights_narrative"),
    )
    _push_section(
        sections,
        {
            "id": "exec_summary",
            "body": summary or None,
            "bullets": _insight_bullets_without_scores(page1.get("key_insights"), 4),
        },
    )

    scorecard_lines: list[str] = []
    for m in page1.get("metrics") or []:
        if not isinstance(m, dict):
            continue
        scorecard_lines.append(
            _format_metric_line(
                str(m.get("label") or "Metric"),
                m.get("value"),
                m.get("interpretation"),
                lang,
            )
        )
    for s in page1.get("strengths") or []:
        if not isinstance(s, dict):
            continue
        label = str(s.get("label") or "")
        val = int(s.get("value") or 0)
        scorecard_lines.append(
            f"{label}: {val}/100 — {_human_score_band(val, label, lang)}"
        )
    for c in page1.get("challenges") or []:
        if not isinstance(c, dict):
            continue
        label = str(c.get("label") or "challenge")
        val = int(c.get("value") or 0)
        scorecard_lines.append(
            f"{label}: {val}/100 — {_human_score_band(val, label, lang)}"
        )
    _push_section(
        sections,
        {
            "id": "scorecard",
            "bullets": scorecard_lines or None,
        },
    )

    verdict = str(page1.get("verdict") or "").strip()
    _push_section(sections, {"id": "verdict", "body": verdict or None})

    rec_paras = page1.get("recommendation_paragraphs") or []
    rec_body = "\n\n".join(str(p).strip() for p in rec_paras if str(p).strip()).strip()
    rec_bullets = [str(b).strip() for b in (page1.get("recommendations") or [])[:7] if str(b).strip()]
    _push_section(
        sections,
        {
            "id": "recommendations",
            "body": rec_body or None,
            "bullets": rec_bullets or None,
        },
    )

    deep_lines: list[str] = []
    for item in page1.get("analysis") or []:
        if not isinstance(item, dict):
            continue
        expl = str(item.get("explanation") or "").strip()
        if not expl:
            continue
        title = str(item.get("title") or "Analysis").strip()
        deep_lines.append(f"{title}\n{expl}")
    _push_section(
        sections,
        {
            "id": "deep_connection",
            "body": "\n\n".join(deep_lines) if deep_lines else None,
        },
    )

    bp = ctx.get("page2_3_blueprint") or {}
    blueprint_body = str(bp.get("part2") or bp.get("part1") or "").strip()
    _push_section(sections, {"id": "blueprint_vs", "body": blueprint_body or None})

    moon = ctx.get("page5_moon") or {}
    moon_body = str(moon.get("body") or "").strip()
    _push_section(sections, {"id": "moon", "body": moon_body or None})

    root = str(ctx.get("page6_root_cause") or "").strip()
    _push_section(sections, {"id": "root_cause", "body": root or None})

    return sections


def _index_by_id(sections: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    for sec in sections:
        if not isinstance(sec, dict):
            continue
        sid = str(sec.get("id") or "").strip().lower()
        if sid:
            out[sid] = sec
    return out


def validate_app_sections_parity(
    *,
    app_sections: list[Any],
    page1: dict[str, Any],
    pdf_context: dict[str, Any],
    lang: str = "en",
) -> str | None:
    """
    Return human-readable error if app_sections content differs from page1/pdf_context.
    None means parity OK — safe to render WYSIWYG PDF.
    """
    if not isinstance(app_sections, list) or not app_sections:
        return "No app_sections sent — reload the report and try Download PDF again."

    expected = build_in_app_page_sections(page1, pdf_context, lang=lang)
    exp_by_id = _index_by_id(expected)
    got_by_id = _index_by_id([s for s in app_sections if isinstance(s, dict)])

    if not got_by_id:
        return "app_sections missing section ids — reload the app and try again."

    missing = [sid for sid in exp_by_id if sid not in got_by_id]
    if missing:
        return (
            "Page sections incomplete — missing: "
            + ", ".join(missing)
            + ". Tap Update Report, then Download PDF."
        )

    for sid, exp_sec in exp_by_id.items():
        got_sec = got_by_id[sid]
        exp_lines = _section_content_lines(exp_sec)
        got_lines = _section_content_lines(got_sec)
        if len(exp_lines) != len(got_lines):
            return (
                f'Section "{sid}": line count mismatch '
                f"(page data {len(exp_lines)} vs screen {len(got_lines)}). "
                "Tap Update Report, then Download PDF."
            )
        for idx, (exp_line, got_line) in enumerate(zip(exp_lines, got_lines), start=1):
            if exp_line != got_line:
                preview_exp = exp_line[:120] + ("…" if len(exp_line) > 120 else "")
                preview_got = got_line[:120] + ("…" if len(got_line) > 120 else "")
                return (
                    f'Section "{sid}" line {idx} does not match page data.\n'
                    f"Expected: {preview_exp}\n"
                    f"On screen: {preview_got}\n"
                    "Tap Update Report, then Download PDF."
                )

    return None
