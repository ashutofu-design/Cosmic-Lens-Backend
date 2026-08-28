"""Mount Numerology Agent on Cosmic Lens flask_app + PDF → My Reports.

Does not replace /api/numerology/pdf. Prefix stays /api/numerology-agent.
"""
from __future__ import annotations

import os
import sys
from typing import Any

from flask import Response, jsonify, request


def _agent_root() -> str:
    here = os.path.dirname(os.path.abspath(__file__))
    return os.path.abspath(os.path.join(here, "..", "..", "numerology agent"))


def register_numerology_agent_routes(app: Any) -> None:
    root = _agent_root()
    if os.path.isdir(root) and root not in sys.path:
        sys.path.insert(0, root)
    from numerology_agent.integrations.cosmic_lens import register_on_flask_app

    register_on_flask_app(app)
    _register_deliver(app)
    print("[numerology_agent] mounted at /api/numerology-agent", flush=True)


def _pdf_lang(raw: str) -> str:
    key = (raw or "").strip().lower()
    if key in ("hi", "hindi"):
        return "hi"
    if key in ("hn", "hinglish"):
        return "hn"
    return "en"


MIN_NARRATIVE_PAGES = 10
MIN_NARRATIVE_CHARS = 2500


def _looks_like_dump(body: str) -> bool:
    try:
        from numerology_agent.quality.dump import looks_like_dump

        return looks_like_dump(body)
    except Exception:
        text = (body or "").strip()
        return (not text) or ("→" in text and len(text) < 1200)


def narrative_page_count(pages: list[Any]) -> int:
    n = 0
    for p in _clean_pages(pages):
        body = p["body"]
        if len(body) >= MIN_NARRATIVE_CHARS and not _looks_like_dump(body):
            n += 1
    return n


def _clean_pages(pages: list[Any]) -> list[dict[str, str]]:
    out: list[dict[str, str]] = []
    for page in pages:
        if not isinstance(page, dict):
            continue
        body = str(page.get("body") or "").strip()
        if not body:
            continue
        title = str(page.get("title") or page.get("role") or "").strip() or "Reading"
        out.append({"title": title, "body": body})
    return out


def _parse_visual_table(block: str) -> tuple[str, list[list[str]]]:
    lines = [ln.strip() for ln in (block or "").splitlines() if ln.strip()]
    title = "Grid"
    if lines and lines[0].upper().startswith("TABLE:"):
        title = lines[0].split(":", 1)[-1].strip() or title
        lines = lines[1:]
    rows = [[cell.strip() for cell in line.split("|")] for line in lines if "|" in line]
    return title, rows


def _append_body_flow(
    story: list[Any],
    body: str,
    *,
    attempt_lang: str,
    s: Any,
    h_bold: str,
    section_h: Any,
) -> None:
    from founder_text_pdf import _founder_body_markup, _sanitize_founder_plain, _split_paragraphs
    from milan_pdf import BRAND_GOLD, TEXT_MID, _latinize_pdf_plain, _pick_body_premium, _safe
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_LEFT
    from reportlab.lib.units import mm
    from reportlab.platypus import Paragraph, Spacer, Table, TableStyle

    remaining = body or ""
    while remaining:
        start = remaining.find("TABLE:")
        end = remaining.find("ENDTABLE")
        take_table = start >= 0 and end > start
        if take_table:
            text_chunk = remaining[:start]
            block = remaining[start:end]
            remaining = remaining[end + len("ENDTABLE") :]
        else:
            text_chunk = remaining
            remaining = ""
        for para in _split_paragraphs(text_chunk):
            plain = _sanitize_founder_plain(_latinize_pdf_plain(para, attempt_lang))
            if not plain:
                continue
            body_style = _pick_body_premium(plain, s, attempt_lang, relax=True)
            body_style.alignment = TA_LEFT
            body_style.spaceAfter = 8
            body_style.leading = 15
            story.append(Paragraph(_founder_body_markup(plain), body_style))
        if not take_table:
            break
        title, rows = _parse_visual_table(block)
        if not rows:
            continue
        story.append(Spacer(1, 2 * mm))
        story.append(Paragraph(_safe(title), section_h))
        table = Table(rows, hAlign="LEFT")
        table.setStyle(
            TableStyle(
                [
                    ("FONTNAME", (0, 0), (-1, 0), h_bold),
                    ("FONTSIZE", (0, 0), (-1, -1), 8.5),
                    ("TEXTCOLOR", (0, 0), (-1, 0), BRAND_GOLD),
                    ("TEXTCOLOR", (0, 1), (-1, -1), TEXT_MID),
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1B2430")),
                    ("GRID", (0, 0), (-1, -1), 0.4, BRAND_GOLD),
                    ("LEFTPADDING", (0, 0), (-1, -1), 6),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                    ("TOPPADDING", (0, 0), (-1, -1), 4),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ]
            )
        )
        story.append(table)
        story.append(Spacer(1, 4 * mm))


def render_agent_report_pdf(
    *,
    name: str,
    dob: str,
    lang: str,
    pages: list[Any],
) -> bytes:
    import io

    from reportlab.lib.enums import TA_CENTER, TA_LEFT
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.units import mm
    from reportlab.platypus import PageBreak, Paragraph, SimpleDocTemplate, Spacer

    from milan_pdf import (
        BRAND_GOLD,
        TEXT_MID,
        _ensure_native_pdf_fonts_registered,
        _font_pair,
        _on_page,
        _safe,
        _styles,
    )

    sections = _clean_pages(pages)
    if not sections:
        raise ValueError("empty_report")

    render_lang = _pdf_lang(lang)
    last_exc: Exception | None = None
    for attempt_lang in (render_lang, "en"):
        try:
            _ensure_native_pdf_fonts_registered(attempt_lang)
            h_reg, h_bold = _font_pair(attempt_lang)
            buf = io.BytesIO()
            doc = SimpleDocTemplate(
                buf,
                pagesize=A4,
                leftMargin=18 * mm,
                rightMargin=18 * mm,
                topMargin=18 * mm,
                bottomMargin=18 * mm,
            )
            doc.milan_pdf_footer_center = "Cosmic Lens · Numerology"
            doc.milan_pdf_lang = attempt_lang
            s = _styles(attempt_lang)
            eyebrow = ParagraphStyle(
                "na_eyebrow",
                parent=s["body"],
                fontName=h_bold,
                fontSize=9,
                textColor=BRAND_GOLD,
                alignment=TA_CENTER,
                spaceAfter=4,
                leading=12,
            )
            h1 = ParagraphStyle(
                "na_h1",
                parent=s["body"],
                fontName=h_bold,
                fontSize=16,
                textColor=BRAND_GOLD,
                alignment=TA_CENTER,
                spaceAfter=6,
                leading=20,
            )
            h2 = ParagraphStyle(
                "na_h2",
                parent=s["body"],
                fontName=h_bold,
                fontSize=13,
                textColor=BRAND_GOLD,
                alignment=TA_CENTER,
                spaceAfter=10,
                leading=17,
            )
            section_h = ParagraphStyle(
                "na_section",
                parent=s["body"],
                fontName=h_bold,
                fontSize=13,
                textColor=BRAND_GOLD,
                alignment=TA_LEFT,
                spaceBefore=2,
                spaceAfter=10,
                leading=17,
            )
            meta = ParagraphStyle(
                "na_meta",
                parent=s["body"],
                fontName=h_reg,
                fontSize=8.5,
                textColor=TEXT_MID,
                alignment=TA_CENTER,
                spaceAfter=14,
            )
            story: list[Any] = [
                Spacer(1, 8 * mm),
                Paragraph("COSMIC LENS", eyebrow),
                Paragraph(_safe("Numerology Report"), h1),
                Paragraph(_safe(name or "Numerology"), h2),
                Paragraph(_safe(dob or ""), meta),
                Spacer(1, 4 * mm),
            ]
            for index, section in enumerate(sections):
                if index > 0:
                    story.append(PageBreak())
                    story.append(Spacer(1, 4 * mm))
                story.append(Paragraph(_safe(section["title"]), section_h))
                _append_body_flow(
                    story,
                    section["body"],
                    attempt_lang=attempt_lang,
                    s=s,
                    h_bold=h_bold,
                    section_h=section_h,
                )
            doc.build(story, onFirstPage=_on_page, onLaterPages=_on_page)
            return buf.getvalue()
        except Exception as exc:
            last_exc = exc
            if attempt_lang == "en":
                raise
    if last_exc:
        raise last_exc
    raise RuntimeError("numerology_agent_pdf_render_failed")


def _register_deliver(app: Any) -> None:
    if "numerology_agent_report_deliver" in getattr(app, "view_functions", {}):
        return

    @app.route("/api/numerology-agent/report/deliver", methods=["POST", "OPTIONS"])
    def numerology_agent_report_deliver():
        if request.method == "OPTIONS":
            return ("", 204)
        body = request.get_json(silent=True) or {}
        name = str(body.get("name") or "").strip() or "Report"
        dob = str(body.get("dob") or "").strip()
        lang = str(body.get("lang") or "english")
        pages = body.get("pages")
        if not isinstance(pages, list) or not pages:
            plan = body.get("report_plan") if isinstance(body.get("report_plan"), dict) else {}
            pages = plan.get("pages") if isinstance(plan, dict) else []
        if not isinstance(pages, list) or not pages:
            return jsonify({"error": "missing_pages", "message": "Report pages missing."}), 400
        if narrative_page_count(pages) < MIN_NARRATIVE_PAGES:
            return (
                jsonify(
                    {
                        "error": "incomplete_report",
                        "message": "Poori 10 page reading nahi bani. Dobara Try for free dabao.",
                    }
                ),
                409,
            )
        try:
            pdf_bytes = render_agent_report_pdf(name=name, dob=dob, lang=lang, pages=pages)
        except Exception as exc:
            app.logger.exception("[numerology_agent] pdf render failed: %s", exc)
            return jsonify({"error": "render_failed", "message": "PDF ban nahi payi."}), 500

        safe_name = "".join(c for c in name if c.isalnum() or c in "_- ").strip().replace(" ", "_") or "report"
        fname = f"Numerology_{safe_name}.pdf"
        report_id = ""

        user_id_header = request.headers.get("X-User-Id", "").strip()
        api_key = request.headers.get("X-API-Key", "").strip()
        if user_id_header and api_key:
            try:
                from models import User
                import report_cache as _rc

                uid = int(user_id_header)
                user = User.query.get(uid)
                if user and user.api_key == api_key:
                    report_id = _rc.save(
                        user.id,
                        "numerology_agent",
                        "Numerology Report",
                        {"name": name, "dob": dob, "lang": lang},
                        pdf_bytes,
                        fname,
                    ) or ""
            except Exception as exc:
                app.logger.warning("[numerology_agent] my-reports save failed: %s", exc)

        headers = {
            "Content-Disposition": f'attachment; filename="{fname}"',
            "Cache-Control": "private, max-age=60",
        }
        if report_id:
            headers["X-Report-Id"] = report_id
        return Response(pdf_bytes, mimetype="application/pdf", headers=headers)
