from pathlib import Path

lines = Path("vedic/compat/premium_chapters.py").read_text(encoding="utf-8").splitlines()
Path("_line691_repr.txt").write_text(repr(lines[690]) + "\n", encoding="utf-8")
