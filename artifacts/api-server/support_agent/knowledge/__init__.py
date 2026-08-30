"""Approved Support Knowledge Base (markdown files in this folder)."""
from __future__ import annotations

from pathlib import Path

_DIR = Path(__file__).resolve().parent

# Client-facing verified facts only — loaded + chunk-retrieved (not full dump to LLM).
KNOWLEDGE_FILES = (
    "app.md",
    "home_radar.md",
    "payments.md",
    "ask_packs.md",
    "subscription.md",
    "reports.md",
    "numerology.md",
    "relationship.md",
    "vastu.md",
    "faq.md",
)


def knowledge_dir() -> Path:
    return _DIR


def load_knowledge() -> str:
    """Full corpus (indexing / tests). Prefer retrieve_chunks for LLM prompts."""
    parts: list[str] = []
    for name in KNOWLEDGE_FILES:
        path = _DIR / name
        try:
            parts.append(path.read_text(encoding="utf-8").strip())
        except OSError:
            continue
    return "\n\n".join(p for p in parts if p)


ALLOWED_KNOWLEDGE = load_knowledge()


def pick(answers: dict[str, str], lang: str) -> str:
    L = (lang or "").strip().lower()
    if L == "hi":
        L = "hn"
    return answers.get(L) or answers.get("hn") or answers.get("en") or ""
