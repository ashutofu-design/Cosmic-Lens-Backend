"""One-shot: remove stray line before def _language_personality_profile."""
from pathlib import Path

path = Path(__file__).resolve().parent / "vedic" / "compat" / "premium_chapters.py"
text = path.read_text(encoding="utf-8")
needle = "def _language_personality_profile(lang: str) -> str:"
idx = text.index(needle)
prefix, suffix = text[:idx], text[idx:]
plines = prefix.splitlines(keepends=True)
j = len(plines) - 1
while j >= 0 and plines[j].strip() == "":
    j -= 1
if j >= 0 and plines[j].strip() != '"""':
    del plines[j]
path.write_text("".join(plines) + suffix, encoding="utf-8")
(Path(__file__).resolve().parent / "_strip691_ok.txt").write_text("ok", encoding="utf-8")
