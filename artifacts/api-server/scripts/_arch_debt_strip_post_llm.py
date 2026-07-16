"""One-shot: replace post-narrator modifier block with narrator-final pass."""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "openai_helper.py"

START = "    try:\n        text = _llm_raw_text\n        _answer_fidelity: dict = {}"
END = "        # ── Prompt-cache telemetry ──────────────────────────────────────"

REPLACEMENT = '''    try:
        # FINAL ARCH: Narrator LLM output is FINAL — no post-modifiers.
        # Tone/structure live in narrator prompts (relationship_narrator / mr narrator).
        text = (_llm_raw_text or "").strip()
        _answer_fidelity: dict = {
            "skipped": "narrator_final",
            "ok": True,
            "attempts": 0,
            "issues": [],
            "repairs": [],
        }
        if not text:
            text = (
                "Maaf kijiye, abhi response generate nahi ho paaya. "
                "Phir try karein."
            )
        print(
            f"[raw_passthrough] PHASE1_RAW_NARRATOR no post-modifiers chars={len(text)}",
            flush=True,
        )

        # ── Prompt-cache telemetry ──────────────────────────────────────'''

def main() -> None:
    src = PATH.read_text(encoding="utf-8")
    i0 = src.find(START)
    if i0 < 0:
        # Already replaced?
        if "PHASE1_RAW_NARRATOR no post-modifiers" in src and "enforce_cosmo_engine_answer" not in src.split("PHASE1_RAW_NARRATOR", 1)[-1][:2000]:
            print("already_narrator_final")
            return
        raise SystemExit("START marker not found")
    i1 = src.find(END, i0)
    if i1 < 0:
        raise SystemExit("END marker not found")
    new = src[:i0] + REPLACEMENT + src[i1 + len(END) :]
    # Only first occurrence in raw_passthrough
    PATH.write_text(new, encoding="utf-8")
    print(f"stripped post-llm block bytes_removed={i1 - i0}")


if __name__ == "__main__":
    main()
