"""
Post-polish validation for Love Reality Pro — ban filler, cross-chapter repeats.
"""
from __future__ import annotations

import re
from typing import Any

from vedic.compat.premium_chapters import THERAPY_CLICHES, CHAPTER_BODY_KEY
from vedic.love_reality.chart_facts import build_narrative_bridge
from vedic.love_reality.pdf_text_safe import polish_content_lang

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
    return t.strip()


def _dedupe_cross_chapter(parsed: dict) -> None:
    """Strip repeated opener templates across chapters."""
    openers = [
        r"^Yeh zaroori hai ki tum dono[^.]*\.\s*",
        r"^Open communication aur mutual understanding[^.]*\.\s*",
        r"^Chart signals for this theme[^.]*\.\s*",
        r"^Taaki misunderstandings aur emotional distance[^.]*\.\s*",
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

    if bundle:
        bridge = build_narrative_bridge(bundle, lang)
        verdict = str(parsed.get("verdict") or "").strip()
        if bridge and bridge[:40].lower() not in verdict.lower():
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
