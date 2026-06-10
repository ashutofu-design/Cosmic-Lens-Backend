"""
Post-polish validation for Love Reality Pro — ban filler, cross-chapter repeats.
"""
from __future__ import annotations

import re
from typing import Any

from vedic.compat.premium_chapters import THERAPY_CLICHES, CHAPTER_BODY_KEY
from vedic.love_reality.chart_facts import build_narrative_bridge
from vedic.love_reality.pdf_text_safe import polish_content_lang, humanize_display_tokens

def _scrub_cliches(text: str) -> str:
    t = text
    for phrase in THERAPY_CLICHES:
        if len(phrase) < 8:
            continue
        pat = re.compile(re.escape(phrase), re.I)
        t = pat.sub("", t)
    t = re.sub(
        r"\bYeh zaroori hai ki tum dono\b[^.]*\.",
        "",
        t,
        flags=re.I,
    )
    t = re.sub(
        r"\bOpen communication aur mutual understanding\b[^.]*\.",
        "",
        t,
        flags=re.I,
    )
    t = re.sub(r"\n{3,}", "\n\n", t)
    return humanize_display_tokens(t.strip())


def _normalize_para(p: str) -> str:
    return re.sub(r"\s+", " ", (p or "").strip().lower())[:220]


def _narrative_text_fields(parsed: dict) -> list[tuple[str, str, str]]:
    """(container, field_key, text) — container is 'root', chapter key, or deep_analysis key."""
    out: list[tuple[str, str, str]] = []
    if parsed.get("verdict"):
        out.append(("root", "verdict", str(parsed["verdict"])))
    for key in (
        "blueprint_reality",
        "red_flags_narrative",
        "harmony",
        "dasha_narrative",
        "roadmap_narrative",
        "moon_sync_narrative",
        "remedies_action_narrative",
    ):
        if parsed.get(key):
            out.append(("root", key, str(parsed[key])))
    for c in parsed.get("chapters") or []:
        if not isinstance(c, dict):
            continue
        body = str(c.get(CHAPTER_BODY_KEY) or "").strip()
        if body:
            out.append(("chapter", str(c.get("key") or ""), body))
    for row in parsed.get("deep_analysis") or []:
        if not isinstance(row, dict):
            continue
        expl = str(row.get("explanation") or row.get("body") or "").strip()
        if expl:
            out.append(("deep", str(row.get("key") or row.get("title") or ""), expl))
    return out


def _write_narrative_field(parsed: dict, container: str, field_key: str, text: str) -> None:
    if container == "root" and field_key == "verdict":
        parsed["verdict"] = text
    elif container == "root":
        parsed[field_key] = text
    elif container == "chapter":
        for c in parsed.get("chapters") or []:
            if isinstance(c, dict) and str(c.get("key") or "") == field_key:
                c[CHAPTER_BODY_KEY] = text
                return
    elif container == "deep":
        for row in parsed.get("deep_analysis") or []:
            if isinstance(row, dict) and str(row.get("key") or row.get("title") or "") == field_key:
                if "explanation" in row:
                    row["explanation"] = text
                else:
                    row["body"] = text
                return


def _dedupe_identical_paragraphs(parsed: dict) -> None:
    """Drop verbatim paragraph repeats across sections (post-LLM safety net)."""
    seen: dict[str, str] = {}
    for container, field_key, text in _narrative_text_fields(parsed):
        paras = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
        kept: list[str] = []
        for para in paras:
            norm = _normalize_para(para)
            if len(norm) < 50:
                kept.append(para)
                continue
            if norm in seen:
                continue
            seen[norm] = field_key or container
            kept.append(para)
        if kept:
            _write_narrative_field(parsed, container, field_key, "\n\n".join(kept))


def _dedupe_cross_chapter(parsed: dict) -> None:
    """Strip repeated opener templates across chapters."""
    openers = [
        r"^Yeh zaroori hai ki tum dono[^.]*\.\s*",
        r"^Open communication aur mutual understanding[^.]*\.\s*",
        r"^Chart signals for this theme[^.]*\.\s*",
        r"^Taaki misunderstandings aur emotional distance[^.]*\.\s*",
        r"^The single strongest friction[^.]*\.\s*",
        r"^Sabse bada friction point[^.]*\.\s*",
    ]
    seen: set[str] = set()
    for c in parsed.get("chapters") or []:
        if not isinstance(c, dict):
            continue
        body = str(c.get(CHAPTER_BODY_KEY) or "")
        for op in openers:
            m = re.match(op, body, re.I | re.M)
            if not m:
                continue
            frag = m.group(0).lower()[:48]
            if frag in seen:
                c[CHAPTER_BODY_KEY] = body[m.end():].lstrip()
            else:
                seen.add(frag)
            break


def apply_love_premium_validation(parsed: dict, bundle: dict | None, lang: str = "en") -> dict:
    """Mutates parsed in place; returns parsed."""
    lang = polish_content_lang(lang)
    for c in parsed.get("chapters") or []:
        if not isinstance(c, dict):
            continue
        for field in (CHAPTER_BODY_KEY, "full_read", "grounding", "verdict"):
            if field in c and c[field]:
                c[field] = _scrub_cliches(str(c[field]))
        if CHAPTER_BODY_KEY in c and c.get(CHAPTER_BODY_KEY):
            c[CHAPTER_BODY_KEY] = _scrub_cliches(str(c[CHAPTER_BODY_KEY]))
    if parsed.get("verdict"):
        parsed["verdict"] = _scrub_cliches(str(parsed["verdict"]))
    for field in ("hidden_truth",):
        if parsed.get(field):
            parsed[field] = _scrub_cliches(str(parsed[field]))
    _dedupe_cross_chapter(parsed)
    _dedupe_identical_paragraphs(parsed)

    if bundle:
        assembly = str((parsed.get("_meta") or {}).get("assembly") or "")
        skip_bridge = assembly.startswith("lr_sections")
        bridge = build_narrative_bridge(bundle, lang)
        verdict = str(parsed.get("verdict") or "").strip()
        if (
            not skip_bridge
            and bridge
            and bridge[:40].lower() not in verdict.lower()
        ):
            parsed["verdict"] = (verdict + "\n\n" + bridge).strip() if verdict else bridge
        groundings = bundle.get("chapter_groundings") or {}
        for c in parsed.get("chapters") or []:
            if not isinstance(c, dict):
                continue
            if not str(c.get("grounding") or "").strip():
                g = groundings.get(str(c.get("key") or "").strip().lower())
                if g:
                    c["grounding"] = g
    return parsed
