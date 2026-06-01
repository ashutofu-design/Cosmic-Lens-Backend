"""One-shot: remove stray non-Python line before _language_personality_profile."""
from pathlib import Path

path = Path(__file__).resolve().parent / "vedic" / "compat" / "premium_chapters.py"
lines = path.read_text(encoding="utf-8").splitlines(keepends=True)
needle = "def _language_personality_profile(lang: str) -> str:"
out = []
i = 0
removed = False
while i < len(lines):
    line = lines[i]
    if line.startswith(needle):
        j = len(out) - 1
        while j >= 0 and out[j].strip() == "":
            j -= 1
        if j >= 0 and out[j].strip() != '"""':
            del out[j]
            removed = True
        out.append(line)
        i += 1
        continue
    out.append(line)
    i += 1
path.write_text("".join(out), encoding="utf-8", newline="")
print(f"removed_orphan={removed}")
