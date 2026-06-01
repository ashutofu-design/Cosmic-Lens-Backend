"""One-off: strip orphaned Gujarati fragment before _language_personality_profile."""
from pathlib import Path

path = Path(__file__).resolve().parent / "vedic" / "compat" / "premium_chapters.py"
text = path.read_text(encoding="utf-8")
start = text.find("\n- મશીન અનુવાદ")
if start == -1:
    raise SystemExit("marker not found — nothing to fix")
end = text.find("\ndef _language_personality_profile", start)
if end == -1:
    raise SystemExit("def anchor not found")
path.write_text(text[:start] + text[end:], encoding="utf-8")
