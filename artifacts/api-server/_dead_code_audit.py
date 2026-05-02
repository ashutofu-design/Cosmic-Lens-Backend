"""
Dead-code audit for openai_helper.py.

Walks the AST to enumerate every top-level function (def + async def),
then counts how many times each name appears as an identifier across:
  (a) openai_helper.py itself  (excluding the def line)
  (b) every other .py file in artifacts/api-server/

Categorises by total external+internal call count and prints a sorted
report. Emphatically NOT a delete script — produces a TXT report only.
"""
from __future__ import annotations
import ast
import os
import re
from pathlib import Path
from collections import defaultdict

ROOT = Path(__file__).parent
TARGET = ROOT / "openai_helper.py"

src = TARGET.read_text(encoding="utf-8")
tree = ast.parse(src)

# ── 1. Collect every top-level function/method name + line range ────
funcs: list[tuple[str, int, int]] = []   # (name, start_line, end_line)
for node in tree.body:
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        end = node.end_lineno or node.lineno
        funcs.append((node.name, node.lineno, end))
    elif isinstance(node, ast.ClassDef):
        # one level deep — class methods (e.g. WealthStructuredError)
        end = node.end_lineno or node.lineno
        funcs.append((node.name, node.lineno, end))

print(f"Total top-level functions/classes: {len(funcs)}")

# ── 2. Build internal call index (within openai_helper.py) ──────────
# For each function, count occurrences of its name in the file MINUS
# the def-line itself. We use a word-boundary regex so partial matches
# don't inflate counts (e.g. _scrub vs _scrub_ai_tells).
src_lines = src.split("\n")

internal_counts: dict[str, int] = {}
for name, start, end in funcs:
    pattern = re.compile(rf"\b{re.escape(name)}\b")
    total = 0
    for i, line in enumerate(src_lines, 1):
        if i == start:
            # skip the "def name(" line itself
            continue
        total += len(pattern.findall(line))
    internal_counts[name] = total

# ── 3. Scan ALL OTHER .py files for external usage ──────────────────
external_callers: dict[str, list[tuple[str, int]]] = defaultdict(list)
other_py = [p for p in ROOT.glob("*.py") if p.name != "openai_helper.py"
            and p.name != "_dead_code_audit.py"]
# also recurse into subdirs (marriage_engine/, etc.)
for sub in ROOT.iterdir():
    if sub.is_dir() and not sub.name.startswith((".", "__", "disabled_")):
        other_py.extend(sub.glob("*.py"))

# Pre-compile patterns for every function name once.
patterns = {name: re.compile(rf"\b{re.escape(name)}\b") for name, _, _ in funcs}

for path in other_py:
    try:
        text = path.read_text(encoding="utf-8")
    except Exception:
        continue
    for i, line in enumerate(text.split("\n"), 1):
        # skip comments
        if line.lstrip().startswith("#"):
            continue
        for name, pat in patterns.items():
            if pat.search(line):
                external_callers[name].append((path.name, i))

# ── 4. Categorise ────────────────────────────────────────────────────
PUBLIC_API = {"ai_ask", "ai_ask_v2", "ai_ask_stream", "vastu_scan",
              "vastu_deep_scan", "is_available", "hinglishify_response",
              "extract_floor_plan_layout", "analyze_room_visuals",
              "WealthStructuredError"}

rows = []
for name, start, end in funcs:
    ic = internal_counts[name]
    ec = len(external_callers[name])
    total = ic + ec
    lines = end - start + 1
    if name in PUBLIC_API:
        cat = "PUBLIC_API"
    elif total == 0:
        cat = "DEAD" if not name.startswith("__") else "DUNDER"
    elif total <= 2:
        cat = "REVIEW"
    elif total <= 4:
        cat = "ACTIVE"
    else:
        cat = "CORE"
    rows.append((cat, total, ic, ec, name, start, lines))

# ── 5. Print report ─────────────────────────────────────────────────
def print_section(title, items):
    print(f"\n{'='*78}\n{title}  ({len(items)} items)\n{'='*78}")
    print(f"{'name':<48} {'L#':>6} {'lines':>6} {'int':>4} {'ext':>4}")
    print("-" * 78)
    for cat, total, ic, ec, name, start, lines in items:
        print(f"{name:<48} {start:>6} {lines:>6} {ic:>4} {ec:>4}")

# Group by category
by_cat: dict[str, list] = defaultdict(list)
for r in rows:
    by_cat[r[0]].append(r)

# Print: DEAD first (most useful), then REVIEW, then summary
for cat in ("DEAD", "REVIEW", "ACTIVE", "CORE", "PUBLIC_API", "DUNDER"):
    items = sorted(by_cat.get(cat, []), key=lambda r: -r[6])  # by lines desc
    if items:
        print_section(cat, items)

# Final summary
print(f"\n{'='*78}\nSUMMARY\n{'='*78}")
total_lines = sum(r[6] for r in rows)
for cat in ("DEAD", "REVIEW", "ACTIVE", "CORE", "PUBLIC_API", "DUNDER"):
    items = by_cat.get(cat, [])
    line_sum = sum(r[6] for r in items)
    pct = 100 * line_sum / total_lines if total_lines else 0
    print(f"  {cat:<12} {len(items):>4} funcs  {line_sum:>6} lines  ({pct:5.1f}%)")
print(f"  {'TOTAL':<12} {len(rows):>4} funcs  {total_lines:>6} lines")

# ── 6. For DEAD entries, show external-caller details ───────────────
dead_items = by_cat.get("DEAD", [])
if dead_items:
    print(f"\n{'='*78}\nDEAD CODE — DETAILED EXTERNAL CHECK\n{'='*78}")
    for cat, total, ic, ec, name, start, lines in dead_items:
        print(f"\n  {name}  (L{start}, {lines} lines)")
        if ec == 0:
            print(f"    → 0 external callers (truly dead)")
        else:
            for fp, ln in external_callers[name][:5]:
                print(f"    → {fp}:{ln}")

# ── 7. For REVIEW entries, show ALL callers ─────────────────────────
review_items = by_cat.get("REVIEW", [])
if review_items:
    print(f"\n{'='*78}\nREVIEW CANDIDATES — ALL CALLERS\n{'='*78}")
    for cat, total, ic, ec, name, start, lines in sorted(review_items, key=lambda r: -r[6]):
        if lines < 20:
            continue  # skip tiny helpers
        print(f"\n  {name}  (L{start}, {lines} lines, int={ic} ext={ec})")
        # internal call lines
        pat = patterns[name]
        ic_lines = []
        for i, line in enumerate(src_lines, 1):
            if i == start:
                continue
            if pat.search(line):
                ic_lines.append(i)
        if ic_lines:
            print(f"    internal: openai_helper.py:{','.join(map(str, ic_lines[:5]))}")
        for fp, ln in external_callers[name][:5]:
            print(f"    external: {fp}:{ln}")
