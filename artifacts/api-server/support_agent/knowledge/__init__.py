"""Approved Support Knowledge Base (markdown files in this folder)."""
from __future__ import annotations

from pathlib import Path

_DIR = Path(__file__).resolve().parent
_FILES = ("app.md", "payments.md", "reports.md", "numerology.md", "faq.md")


def load_knowledge() -> str:
    parts: list[str] = []
    for name in _FILES:
        path = _DIR / name
        try:
            parts.append(path.read_text(encoding="utf-8").strip())
        except OSError:
            continue
    return "\n\n".join(p for p in parts if p)


ALLOWED_KNOWLEDGE = load_knowledge()


def pick(answers: dict[str, str], lang: str) -> str:
    return answers.get(lang) or answers["hn"]
