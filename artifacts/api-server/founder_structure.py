"""Parse admin-pasted founder report text into topic sections.

Markdown paste (recommended):
  # Report title
  ## Section One
  body…

Only `#` / `##` / `###` lines become gold headings.
Numbered TOC lines (`1. Foo`) stay as body text — never auto-duplicated.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Literal, Sequence


@dataclass(frozen=True)
class FounderSection:
    title: str
    body: str


@dataclass(frozen=True)
class StoryBlock:
    kind: Literal["heading", "para", "rule", "page_break"]
    text: str = ""


_MD_HEADING = re.compile(r"^#{1,3}\s+(.+)$")
_HR = re.compile(r"^[-*_]{3,}\s*$")
_BULLET = re.compile(r"^[-*•]\s+(.*)$")
_BOLD = re.compile(r"\*\*(.+?)\*\*")
_ITAL = re.compile(r"(?<!\*)\*([^*\n]+?)\*(?!\*)")
_UNDER = re.compile(r"__(.+?)__")
_GOLD = re.compile(r"\{\{(.+?)\}\}")


def split_paragraphs(text: str) -> list[str]:
    chunks = [p.strip() for p in re.split(r"\n\s*\n+", (text or "").strip()) if p.strip()]
    if chunks:
        return chunks
    return [ln.strip() for ln in (text or "").splitlines() if ln.strip()]


def match_heading_line(line: str) -> str | None:
    """Only markdown headings — avoids hijacking TOC numbered lists."""
    s = (line or "").strip()
    if not s:
        return None
    m = _MD_HEADING.match(s)
    if not m:
        return None
    title = m.group(1).strip().rstrip(":").strip()
    return title or None


def parse_founder_sections(text: str) -> list[FounderSection]:
    """Split paste text into titled sections; fallback = one untitled block."""
    raw = (text or "").replace("\r\n", "\n").replace("\r", "\n").strip()
    if not raw:
        return [FounderSection("", "")]

    lines = raw.split("\n")
    sections: list[FounderSection] = []
    cur_title: str | None = None
    cur_body: list[str] = []
    found_heading = False

    def _flush() -> None:
        nonlocal cur_title, cur_body
        body = "\n".join(cur_body).strip()
        if cur_title is not None or body:
            sections.append(FounderSection(title=(cur_title or "").strip(), body=body))
        cur_title = None
        cur_body = []

    for line in lines:
        stripped = line.strip()
        if not stripped:
            if cur_body and cur_body[-1] != "":
                cur_body.append("")
            continue

        title = match_heading_line(stripped)
        if title is not None:
            if cur_title is not None or any(x.strip() for x in cur_body):
                _flush()
            cur_title = title
            cur_body = []
            found_heading = True
            continue

        cur_body.append(stripped)

    _flush()

    if not found_heading:
        return [FounderSection("", raw)]

    return [s for s in sections if s.title or s.body] or [FounderSection("", raw)]


def toc_titles_from_sections(
    sections: Sequence[FounderSection],
    *,
    default: Sequence[str] | None = None,
) -> list[str]:
    """Deprecated for auto-inject — kept for callers; returns [] by default."""
    return list(default or [])


def iter_structured_blocks(
    body_text: str,
    *,
    page_break_between_sections: bool = False,
) -> list[StoryBlock]:
    """Flatten sections into heading / para / rule blocks (continuous flow)."""
    sections = parse_founder_sections(body_text)
    blocks: list[StoryBlock] = []
    section_index = 0
    for sec in sections:
        has_heading = bool((sec.title or "").strip())
        if not has_heading and not (sec.body or "").strip():
            continue
        if section_index > 0 and page_break_between_sections and has_heading:
            blocks.append(StoryBlock("page_break"))
        if has_heading:
            blocks.append(StoryBlock("heading", sec.title.strip()))
        for para in split_paragraphs(sec.body or ""):
            # Expand multi-line paragraphs line-by-line for HR / bullets
            for ln in para.split("\n"):
                s = ln.strip()
                if not s:
                    continue
                if _HR.match(s):
                    blocks.append(StoryBlock("rule"))
                    continue
                blocks.append(StoryBlock("para", s))
        section_index += 1
    if not blocks:
        for para in split_paragraphs(body_text):
            for ln in para.split("\n"):
                s = ln.strip()
                if not s:
                    continue
                if _HR.match(s):
                    blocks.append(StoryBlock("rule"))
                else:
                    blocks.append(StoryBlock("para", s))
    return blocks


def iter_verbatim_blocks(body_text: str) -> list[StoryBlock]:
    """Paste-only blocks: blank-line paragraphs, no heading/TOC invent."""
    raw = (body_text or "").replace("\r\n", "\n").replace("\r", "\n").strip()
    if not raw:
        return []
    blocks: list[StoryBlock] = []
    for para in split_paragraphs(raw):
        text = para.strip()
        if text:
            blocks.append(StoryBlock("para", text))
    return blocks


def normalize_founder_pages(
    body_text: str = "",
    pages: Sequence[str] | None = None,
) -> list[str]:
    """Admin page list → non-empty page bodies (fallback: single body_text)."""
    if pages:
        out = [str(p or "").strip() for p in pages]
        out = [p for p in out if p]
        if out:
            return out
    body = (body_text or "").strip()
    return [body] if body else []


def normalize_founder_pages_and_images(
    body_text: str = "",
    pages: Sequence[str] | None = None,
    page_images: Sequence[str | None] | None = None,
) -> tuple[list[str], list[str | None]]:
    """Keep page↔image index alignment. Keep page if it has text and/or image."""
    imgs = list(page_images) if page_images is not None else []
    if pages is not None:
        raw_pages = [str(p or "") for p in pages]
    elif (body_text or "").strip():
        raw_pages = [str(body_text)]
    else:
        raw_pages = []

    # Pad images to match pages
    while len(imgs) < len(raw_pages):
        imgs.append(None)
    # Extra trailing images without text pages
    if len(imgs) > len(raw_pages):
        raw_pages.extend([""] * (len(imgs) - len(raw_pages)))

    out_p: list[str] = []
    out_i: list[str | None] = []
    for i, p in enumerate(raw_pages):
        img = imgs[i] if i < len(imgs) else None
        img_s = str(img).strip() if img else ""
        text = (p or "").strip()
        if text or img_s:
            out_p.append(p if p is not None else "")
            out_i.append(img_s or None)
    if out_p:
        return out_p, out_i
    body = (body_text or "").strip()
    return ([body], [None]) if body else ([], [])


def founder_verbatim_markup(plain: str, *, escape_fn) -> str:
    """Admin-controlled rich text: **bold** *italic* __underline__ {{gold}} bullets.

    No auto headings / TOC invent — only inline marks the admin typed or applied.
    """
    t = (plain or "").replace("\r\n", "\n").replace("\r", "\n")
    if not t.strip():
        return ""

    def _line_markup(line: str) -> str:
        s = line
        prefix = ""
        m = _BULLET.match(s.strip())
        if m:
            prefix = "• "
            s = m.group(1)

        holds: list[str] = []

        def _stash(html: str) -> str:
            holds.append(html)
            return f"@@MD{len(holds) - 1}@@"

        s = _BOLD.sub(lambda m: _stash(f"<b>{escape_fn(m.group(1))}</b>"), s)
        s = _UNDER.sub(lambda m: _stash(f"<u>{escape_fn(m.group(1))}</u>"), s)
        s = _GOLD.sub(
            lambda m: _stash(
                f"<font color='#C9A86A'><b>{escape_fn(m.group(1))}</b></font>"
            ),
            s,
        )
        s = _ITAL.sub(lambda m: _stash(f"<i>{escape_fn(m.group(1))}</i>"), s)
        s = escape_fn(s).replace("%", "&#37;")
        for i, html in enumerate(holds):
            s = s.replace(f"@@MD{i}@@", html)
        return prefix + s

    return "<br/>".join(_line_markup(ln) for ln in t.split("\n"))


def founder_inline_markup(plain: str, *, escape_fn) -> str:
    return founder_verbatim_markup(plain, escape_fn=escape_fn)
