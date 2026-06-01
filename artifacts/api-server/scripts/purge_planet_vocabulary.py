#!/usr/bin/env python3
"""In-place purge of planet/astrology words from numerology product sources."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from numerology.core.sanitize import sanitize_text  # noqa: E402

TARGETS = [
    ROOT / "numerology",
    ROOT / "numerology_pdf.py",
    ROOT / "numerology_pdf_part2.py",
    ROOT / "vedic" / "numerology",
]

# Identifier renames (numerology-only; safe for JSON keys in returns)
IDENT_REPLACEMENTS = [
    ('"planet":', '"archetype":'),
    ("'planet':", "'archetype':"),
    ("first_letter_planet", "first_letter_archetype"),
    ("driver_planet", "driver_archetype"),
    ("conductor_planet", "conductor_archetype"),
    ("name_planet", "name_archetype"),
    ("primary_planet", "primary_archetype"),
    ("secondary_planet", "secondary_archetype"),
    ("PLANET_BY_NUMBER", "ARCHETYPE_BY_NUMBER"),
    ("PLANET_BY_DRIVER", "ARCHETYPE_BY_DRIVER"),
]


def process_file(path: Path) -> bool:
    raw = path.read_text(encoding="utf-8")
    out = sanitize_text(raw)
    for old, new in IDENT_REPLACEMENTS:
        out = out.replace(old, new)
    if out != raw:
        path.write_text(out, encoding="utf-8")
        return True
    return False


def main() -> int:
    changed = []
    for base in TARGETS:
        if base.is_file():
            files = [base]
        else:
            files = sorted(base.rglob("*.py"))
        for fp in files:
            if "__pycache__" in fp.parts:
                continue
            if process_file(fp):
                changed.append(fp)
    print(f"Updated {len(changed)} files")
    for fp in changed:
        print(f"  {fp.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
