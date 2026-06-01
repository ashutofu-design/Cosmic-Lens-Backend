"""Move pure numerology modules to numerology.core and fix relative imports."""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "vedic" / "numerology"
DST = ROOT / "numerology" / "core"

MOVE = [
    "narratives.py",
    "meanings.py",
    "framing.py",
    "pure_numerology.py",
    "phase_s.py",
    "tier_a.py",
    "practical.py",
    "extended.py",
    "career.py",
    "tier1_content.py",
    "core_ext.py",
    "ai_narrator.py",
    "report_voice.py",
    "narration_cache.py",
]

DELETE_VEDIC = [
    "vedic_classical.py",
    "moksha.py",
    "spirituality.py",
    "remedies.py",
    "transits.py",
    "audits.py",
    "relationships.py",
    "wealth.py",
    "health.py",
    "family.py",
    "marriage.py",
    "progeny.py",
    "property.py",
    "foreign.py",
    "longevity.py",
]

IMPORT_FIXES = [
    (r"from vedic\.numerology\.(\w+)", r"from numerology.core.\1"),
    (r"from vedic\.numerology import", r"from numerology.core import"),
    (r"from \.meanings", r"from numerology.core.meanings"),
    (r"from \.phase_s", r"from numerology.core.phase_s"),
    (r"from \.pure_numerology", r"from numerology.core.pure_numerology"),
    (r"from \.extended", r"from numerology.core.extended"),
    (r"from \.practical", r"from numerology.core.practical"),
    (r"from \.career", r"from numerology.core.career"),
    (r"from \.narratives", r"from numerology.core.narratives"),
    (r"from \.core_ext", r"from numerology.core.core_ext"),
    (r"from \.tier1_content", r"from numerology.core.tier1_content"),
    (r"from \.tier_a", r"from numerology.core.tier_a"),
    (r"from \.numerology_report_scope", r"from numerology.core.scope"),
    (r"from \.ai_narrator", r"from numerology.core.ai_narrator"),
    (r"from \.narration_cache", r"from numerology.core.narration_cache"),
    (r"from \.report_voice", r"from numerology.core.report_voice"),
]


def fix_imports(text: str) -> str:
    for pat, repl in IMPORT_FIXES:
        text = re.sub(pat, repl, text)
    return text


def main() -> None:
    for name in MOVE:
        sp = SRC / name
        if not sp.exists():
            print("skip missing", sp)
            continue
        text = fix_imports(sp.read_text(encoding="utf-8"))
        (DST / name).write_text(text, encoding="utf-8")
        print("moved", name)

    for name in DELETE_VEDIC:
        p = SRC / name
        if p.exists():
            p.unlink()
            print("deleted", name)

    # Shims in vedic/numerology
    for name in MOVE:
        shim = SRC / name
        mod = name.removesuffix(".py")
        shim.write_text(
            f'"""Shim — use numerology.core.{mod}"""\n'
            f"from numerology.core.{mod} import *  # noqa: F403\n",
            encoding="utf-8",
        )

    shim_init = SRC / "__init__.py"
    shim_init.write_text(
        '"""Backward-compatible shim — import from numerology.core."""\n'
        "from numerology.core import *  # noqa: F403\n",
        encoding="utf-8",
    )
    scope_shim = SRC / "numerology_report_scope.py"
    scope_shim.write_text(
        '"""Shim — numerology.core.scope"""\n'
        "from numerology.core.scope import *  # noqa: F403\n"
        "from numerology.core.scope import include_celebrity_match, include_extended_extras\n\n\n"
        "def include_vedic_tiers() -> bool:\n"
        '    return False\n',
        encoding="utf-8",
    )

    # Replace imports repo-wide under api-server
    for py in ROOT.rglob("*.py"):
        if "venv" in py.parts or "__pycache__" in py.parts:
            continue
        if py.parts[-3:-1] == ("vedic", "numerology") and py.name in MOVE:
            continue
        text = py.read_text(encoding="utf-8")
        new = fix_imports(text)
        if new != text:
            py.write_text(new, encoding="utf-8")
            print("patched", py.relative_to(ROOT))

    print("done")


if __name__ == "__main__":
    main()
