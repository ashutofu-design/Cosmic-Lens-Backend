"""Generate a sample Universal Pro Report PDF for visual QA."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from founder_text_pdf import render_founder_text_pdf  # noqa: E402

PAGES = [
    """Your Moolank is 5 — curious, adaptable, and strong with communication.

Bhagyank 7 points to deep insight and research energy this year. Quiet focus
beats rushed decisions; protect mornings for deep work.""",
    """Name number reinforces networking and short travel. Destiny favors learning
new skills and publishing your ideas.

Focus months: March, July, and November for career moves. Keep documents
ready in June for a possible opportunity window.""",
    """Remedy: Keep a silver coin in your wallet on Fridays and chant your name
number jaap for 11 minutes. Prefer north-east seating for important calls.

This page is paste-only — nothing was invented by the layout engine.""",
]

OUT = ROOT / "_sample_pro_report_design.pdf"


def main() -> None:
    pdf = render_founder_text_pdf(
        title="Numerology Pro Report",
        subject="Ashutosh Kumar",
        subtitle="",
        lang="en",
        pages=PAGES,
        order_id="abcd1234-sample",
        mystic_theme=True,
        prepared_by="Ashutosh Bharadwaj",
    )
    OUT.write_bytes(pdf)
    print(f"Wrote {OUT} ({len(pdf)} bytes)")


if __name__ == "__main__":
    main()
