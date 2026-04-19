"""
Sprint 52 — RAG Chunker
Splits markdown knowledge files into semantic chunks for embedding.

Strategy:
  - Primary boundary: markdown headings (## H2 sections)
  - Secondary: paragraphs (blank-line separated)
  - Hard cap: ~800 chars per chunk (keeps embeddings tight)
  - Overlap: 100 chars between chunks for context continuity
"""
from __future__ import annotations
import re
from pathlib import Path
from dataclasses import dataclass

CHUNK_MAX = 800
CHUNK_OVERLAP = 100
HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*$", re.M)


@dataclass
class Chunk:
    source: str          # filename (e.g. "nakshatras.md")
    section: str         # nearest H1/H2 heading
    text: str            # chunk body
    chunk_idx: int       # ordinal within file


def _split_by_heading(md: str) -> list[tuple[str, str]]:
    """Return [(heading, body), ...] sections."""
    parts: list[tuple[str, str]] = []
    cur_heading = "Intro"
    cur_body: list[str] = []
    for line in md.splitlines():
        m = HEADING_RE.match(line)
        if m:
            if cur_body:
                parts.append((cur_heading, "\n".join(cur_body).strip()))
            cur_heading = m.group(2).strip()
            cur_body = []
        else:
            cur_body.append(line)
    if cur_body:
        parts.append((cur_heading, "\n".join(cur_body).strip()))
    return [p for p in parts if p[1]]


def _hard_split(text: str, cap: int = CHUNK_MAX,
                overlap: int = CHUNK_OVERLAP) -> list[str]:
    """Split body into <=cap-char windows with overlap."""
    if len(text) <= cap:
        return [text]
    out, i = [], 0
    while i < len(text):
        out.append(text[i:i + cap])
        i += cap - overlap
    return out


def chunk_markdown(md: str, source: str) -> list[Chunk]:
    chunks: list[Chunk] = []
    idx = 0
    for heading, body in _split_by_heading(md):
        for piece in _hard_split(body):
            chunks.append(Chunk(source=source, section=heading, text=piece, chunk_idx=idx))
            idx += 1
    return chunks


def chunk_directory(dir_path: str | Path) -> list[Chunk]:
    """Walk a directory, chunk every .md file."""
    p = Path(dir_path)
    out: list[Chunk] = []
    for md_file in sorted(p.glob("*.md")):
        try:
            md = md_file.read_text(encoding="utf-8")
            out.extend(chunk_markdown(md, md_file.name))
        except Exception as exc:  # noqa: BLE001
            print(f"[chunker] {md_file.name} failed: {exc}")
    return out
