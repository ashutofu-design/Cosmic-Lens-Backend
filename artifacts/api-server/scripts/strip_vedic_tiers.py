"""Remove Vedic tier renderers and kundli logic from numerology_pdf_part2.py."""
from __future__ import annotations

import re
from pathlib import Path

P = Path(__file__).resolve().parents[1] / "numerology_pdf_part2.py"


def main() -> None:
    text = P.read_text(encoding="utf-8")
    before = len(text.splitlines())

    lines = text.splitlines(keepends=True)
    start = next(
        i for i, l in enumerate(lines) if l.startswith("def _tier2_vedic_classical_section")
    )
    end = next(
        i for i, l in enumerate(lines) if l.startswith("def _build_flagship_ai_texts")
    )
    lines = lines[:start] + lines[end:]
    text = "".join(lines)

    # Drop Vedic-only AI fact builders inside _build_flagship_ai_texts
    text = re.sub(
        r"\n    # ── Tier 2–3 AI specs.*?log\.warning\(\"tier17 facts build failed[^\n]*\n",
        "\n",
        text,
        flags=re.DOTALL,
    )

    text = re.sub(
        r"def _build_flagship_ai_texts\([^)]*kundli: Optional\[Dict\[str, Any\]\] = None,\s*",
        "def _build_flagship_ai_texts(",
        text,
    )

    text = re.sub(
        r"from numerology\.core\.numerology_report_scope import \([^)]+\)\s+"
        r"_vedic = include_vedic_tiers\(\)\s+"
        r"# Numerology report: never build kundli.*?kundli = None\s+"
        r"# AI narrations[^\n]+\n\s+ai_texts = _build_flagship_ai_texts\(\s*"
        r"name, dob, tob, driver, lang,\s*"
        r"kundli=kundli if _vedic else None,\s*"
        r"conductor=conductor,\s*\)",
        "from numerology.core.scope import include_celebrity_match, include_extended_extras\n\n"
        "    ai_texts = _build_flagship_ai_texts(\n"
        "        name, dob, tob, driver, lang, conductor=conductor,\n"
        "    )",
        text,
        flags=re.DOTALL,
    )

    text = re.sub(
        r"\n    # ── FULL VEDIC STACK \(NUMEROLOGY_INCLUDE_VEDIC_TIERS=1 only\) ──.*?",
        "\n",
        text,
        count=1,
        flags=re.DOTALL,
    )
    text = re.sub(
        r"if _vedic:.*?story\.append\(PageBreak\(\)\)\n",
        "",
        text,
        count=1,
        flags=re.DOTALL,
    )

    text = text.replace(
        "Legacy Vedic stack only if NUMEROLOGY_INCLUDE_VEDIC_TIERS=1 (separate product).",
        "Pure numerology — digit psychology and behavioral patterns only.",
    )

    after = len(text.splitlines())
    P.write_text(text, encoding="utf-8")
    print(f"stripped {before} -> {after} lines ({before - after} removed)")


if __name__ == "__main__":
    main()
