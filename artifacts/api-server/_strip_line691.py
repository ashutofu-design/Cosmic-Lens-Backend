"""Remove any non-''' residue line immediately above _language_personality_profile."""
from pathlib import Path

path = Path(__file__).resolve().parent / "vedic" / "compat" / "premium_chapters.py"
lines = path.read_text(encoding="utf-8").splitlines(keepends=True)
for i, line in enumerate(lines):
    if not line.startswith("def _language_personality_profile"):
        continue
    j = i - 1
    while j >= 0 and lines[j].strip() == "":
        j -= 1
    if j >= 0 and lines[j].strip() != '"""':
        del lines[j]
    break
path.write_text("".join(lines), encoding="utf-8")
