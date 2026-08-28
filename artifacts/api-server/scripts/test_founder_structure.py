"""Quick sanity checks for founder_structure parser."""
from __future__ import annotations

from founder_structure import (
    iter_structured_blocks,
    match_heading_line,
    parse_founder_sections,
)

SAMPLE = """
# Comprehensive Numerological Analysis Report: January 10, 2001

## Table of Contents

1. Core Energy Architecture & Planetary Matrix
2. Lo Shu Grid Vibrational Dynamics

---

## 1. Core Energy Architecture & Planetary Matrix

Your primary numerological profile is built on Driver Number 1.

## 2. Lo Shu Grid Vibrational Dynamics

When your birth date is mapped onto the Lo Shu Grid.
""".strip()


def main() -> None:
    assert match_heading_line("1. Core Energy Architecture") is None
    assert match_heading_line("## 1. Core Energy Architecture") == (
        "1. Core Energy Architecture"
    )
    secs = parse_founder_sections(SAMPLE)
    titles = [s.title for s in secs]
    assert "Table of Contents" in titles
    assert "1. Core Energy Architecture & Planetary Matrix" in titles
    # Numbered TOC lines must NOT become their own sections
    assert titles.count("Core Energy Architecture & Planetary Matrix") == 0
    blocks = iter_structured_blocks(SAMPLE)
    headings = [b.text for b in blocks if b.kind == "heading"]
    assert "What You Will Find Inside" not in headings
    # TOC numbered lines appear as paras, not headings
    para_text = " ".join(b.text for b in blocks if b.kind == "para")
    assert "1. Core Energy Architecture & Planetary Matrix" in para_text
    print("OK founder_structure checks passed", titles)


if __name__ == "__main__":
    main()
