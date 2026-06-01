"""Remove orphan Gujarati line by UTF-8 bytes (avoids editor Unicode mismatch)."""
from pathlib import Path

path = Path(__file__).resolve().parent / "vedic" / "compat" / "premium_chapters.py"
raw = path.read_bytes()
# જીવંત, વિશ્વસનીય (standard NFC decomposition used on disk)
needle = (
    b"\xe0\xaa\x9c\xe0\xaa\xbf\xe0\xaa\xb5\xe0\xaa\x82\xe0\xaa\xa4"  # જીવંત
    b", \xe0\xaa\xb5\xe0\xaa\xbf\xe0\xaa\xb6\xe0\xab\x8d\xe0\xaa\xb5"  # , વિશ્વ
    b"\xe0\xaa\xb8\xe0\xaa\xa8\xe0\xaa\xbf\xe0\xaa\xaf"  # સનીય
)
for nl in (b"\r\n", b"\n"):
    blob = needle + nl
    if blob in raw:
        path.write_bytes(raw.replace(blob, b"", 1))
        print("removed_ok", repr(nl))
        raise SystemExit(0)
print("needle_missing_try_alt")
# Alternate spelling જીરંત or mixed encoding — scan line-by-line
text = raw.decode("utf-8")
lines = text.splitlines(keepends=True)
for i, ln in enumerate(lines):
    if ln.startswith("def _language_personality_profile"):
        j = i - 1
        while j >= 0 and lines[j].strip() == "":
            j -= 1
        if j >= 0 and lines[j].strip() != '"""':
            del lines[j]
            path.write_text("".join(lines), encoding="utf-8")
            print("removed_via_linesplit")
            raise SystemExit(0)
        break
raise SystemExit("could_not_remove")
