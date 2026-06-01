from pathlib import Path

path = Path(__file__).resolve().parent / "vedic" / "compat" / "premium_chapters.py"
lines = path.read_text(encoding="utf-8").splitlines(keepends=True)
for i, ln in enumerate(lines):
    if ln.startswith("def _language_personality_profile"):
        j = i - 1
        while j >= 0 and lines[j].strip() == "":
            j -= 1
        if j >= 0 and lines[j].strip() != '"""':
            del lines[j]
        break
path.write_text("".join(lines), encoding="utf-8")
