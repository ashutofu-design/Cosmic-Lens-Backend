#!/usr/bin/env python3
"""Quick audit for MR questions --from/--to."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from ask_mr import run_mr_static_engine
from ask_mr.classifier import classify_mr_archetype
from scripts.mr_question_one_by_one import QUESTIONS, SAMPLE_KUNDLI, format_block


def audit_item(qid: int, expected: str, question: str) -> dict:
    routed = classify_mr_archetype(question)
    res = run_mr_static_engine(SAMPLE_KUNDLI, question, wants_explain=False)
    ql = question.lower()
    joined = " ".join(res.evidence or []).lower()
    verdict_l = (res.verdict or "").lower()
    intent = (res.checks or {}).get("question_intent", "")
    notes: list[str] = []

    if routed != expected or res.archetype != expected:
        notes.append(f"route expected={expected} routed={routed} ran={res.archetype}")
    if "strength" in ql and intent != "strengths":
        notes.append(f"strengths Q but intent={intent!r}")
    if "strength" in ql and verdict_l.startswith("marriage/relationship quality: strained"):
        notes.append("strengths Q but strained verdict")
    if "compat" in ql and "physical" not in ql and res.archetype == "general_mr":
        if intent != "emotional_compatibility":
            notes.append(f"compat Q but intent={intent!r}")
    if ("challenge" in ql or "conflict" in ql) and intent != "challenges":
        notes.append(f"challenge Q but intent={intent!r}")
    if "background" in ql and "different background" not in joined:
        notes.append("background Q missing Rahu line")
    if "positive changes" in ql and intent != "strengths":
        notes.append(f"positive changes Q but intent={intent!r}")

    return {
        "qid": qid,
        "question": question,
        "status": "ISSUE" if notes else "OK",
        "notes": notes,
        "verdict": res.verdict,
        "intent": intent,
        "archetype": res.archetype,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--from", dest="from_id", type=int, default=12)
    ap.add_argument("--to", dest="to_id", type=int, default=60)
    ap.add_argument("--out", default="scripts/mr_audit_12_60.txt")
    args = ap.parse_args()

    items = [x for x in QUESTIONS if args.from_id <= x[0] <= args.to_id]
    rows = [audit_item(qid, exp, q) for qid, exp, q in items]
    issues = [r for r in rows if r["status"] == "ISSUE"]
    ok = [r for r in rows if r["status"] == "OK"]

    lines = [
        f"MR Audit IDs {args.from_id}-{args.to_id}",
        f"Total: {len(rows)} | OK: {len(ok)} | Issues: {len(issues)}",
        "",
    ]
    for r in issues:
        lines.append(f"#{r['qid']} [{r['archetype']}] intent={r['intent']!r}")
        lines.append(f"  Q: {r['question'][:72]}")
        for n in r["notes"]:
            lines.append(f"  - {n}")
        lines.append(f"  verdict: {r['verdict'][:100]}")
        lines.append("")

    lines.append("--- OK IDs ---")
    lines.append(", ".join(str(r["qid"]) for r in ok))

    # Full blocks for flagged + sample either/or questions
    sample_ids = {r["qid"] for r in issues} | {12, 16, 17, 35, 47}
    lines.append("")
    lines.append("=" * 78)
    lines.append("DETAILED BLOCKS (issues + samples)")
    lines.append("=" * 78)
    for qid, exp, q in items:
        if qid in sample_ids:
            lines.append(format_block(qid, exp, q))

    out = ROOT / args.out
    out.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {out} | OK={len(ok)} issues={len(issues)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
