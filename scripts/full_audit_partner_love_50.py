#!/usr/bin/env python3
"""Full live ASK AUDIT — 50 partner-love / pyaar questions (no skips)."""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import ask_audit_question as audit  # noqa: E402

QUESTIONS = [
    "Kya mera partner mujhse sach me pyaar karta hai?",
    "Kya meri feelings genuine hain?",
    "Kya hum dono ek dusre se equally pyaar karte hain?",
    "Kya mera partner emotionally attached hai?",
    "Kya partner sirf attraction feel karta hai ya love bhi?",
    "Kya partner mujhe miss karta hai?",
    "Kya partner mujhe dil se chahta hai?",
    "Kya partner ke emotions real hain?",
    "Kya partner sirf time pass kar raha hai?",
    "Kya partner serious feelings rakhta hai?",
    "Kya partner mujhe life partner ke roop me dekhta hai?",
    "Kya partner emotionally available hai?",
    "Kya partner mujhe priority deta hai?",
    "Kya partner mujhe importance deta hai?",
    "Kya partner mere bina reh sakta hai?",
    "Kya partner mujhe deeply love karta hai?",
    "Kya partner apni feelings chhupa raha hai?",
    "Kya partner mujhe express nahi kar pata?",
    "Kya partner emotionally confused hai?",
    "Kya partner mujhe sirf friend maanta hai?",
    "Kya partner romantic feelings rakhta hai?",
    "Kya partner mujhe sirf physical attraction ki wajah se pasand karta hai?",
    "Kya hamara emotional connection strong hai?",
    "Kya hamare beech emotional bonding achhi hai?",
    "Kya partner mujhe respect ke saath pyaar karta hai?",
    "Kya partner mujhe emotionally support karega?",
    "Kya partner meri feelings samajhta hai?",
    "Kya partner meri care karta hai?",
    "Kya partner ko meri value hai?",
    "Kya partner mujhe lose karne se darta hai?",
    "Kya partner mujhe lekar possessive hai?",
    "Kya partner jealous hota hai kyunki woh pyaar karta hai?",
    "Kya partner emotionally mature hai?",
    "Kya partner emotionally dependent hai?",
    "Kya partner mujhe ignore kar raha hai ya busy hai?",
    "Kya partner ka pyaar waqt ke saath kam ho jayega?",
    "Kya hamara pyaar one-sided hai?",
    "Kaun zyada pyaar karta hai?",
    "Kaun relationship me zyada emotionally invested hai?",
    "Kya hum dono emotionally compatible hain?",
    "Kya partner mujhe hurt karna chahta hai ya galti se hota hai?",
    "Kya partner mere liye sacrifice karega?",
    "Kya partner mere saath emotional future dekh raha hai?",
    "Kya partner mujhe emotionally trust karta hai?",
    "Kya hamara pyaar temporary hai ya genuine?",
    "Kya partner mujhe dil se accept karta hai?",
    "Kya partner mujhe kabhi bhool payega?",
    "Kya partner ka pyaar unconditional hai?",
    "Kya hamare relationship me emotional intimacy strong hai?",
    "Overall, kya hamare beech sachcha pyaar hai?",
]

OUT_JSON = ROOT / "scripts" / "full_audit_partner_love_50.json"
OUT_TXT = ROOT / "scripts" / "full_audit_partner_love_50.txt"
OUT_SUMMARY = ROOT / "scripts" / "full_audit_partner_love_50_summary.txt"


def _content_ok(report: dict) -> bool:
    """MR static path + real answer (ignores admin-evidence strict fail)."""
    src = str(report.get("ask_source") or "")
    text = str(report.get("answer_text") or "").strip()
    issues = report.get("issues") or []
    blocked = any(
        x.startswith("BLOCKED")
        or x.startswith("ENGINE_REFUSAL")
        or x.startswith("DIRECT_LLM")
        or x.startswith("TIMING_Q_BUT_STATIC")
        or "timing_domain_clarifier" in src
        or x.startswith("WRONG_ENGINE")
        for x in issues
    )
    return bool(text) and src == "mr_engine_then_llm" and not blocked


def _write_summary(results: list[dict], elapsed_s: float) -> None:
    strict = sum(1 for r in results if r.get("pass"))
    content = sum(1 for r in results if _content_ok(r))
    no_admin = sum(
        1 for r in results if any("NO_ADMIN_ENGINE" in str(i) for i in (r.get("issues") or []))
    )
    no_answer = sum(1 for r in results if not (r.get("answer_text") or "").strip())
    wrong_route = [r for r in results if not _content_ok(r) and (r.get("answer_text") or "").strip()]

    lines = [
        f"API: {audit.DEFAULT_API}",
        f"Total: {len(results)}/{len(QUESTIONS)}",
        f"Elapsed: {elapsed_s:.0f}s",
        f"Strict PASS: {strict}/{len(results)}",
        f"Content OK (mr_engine_then_llm + answer): {content}/{len(results)}",
        f"NO_ADMIN_ENGINE: {no_admin}/{len(results)}",
        f"No answer: {no_answer}",
        "",
        "=== FAILURES (content/routing) ===",
    ]
    for r in wrong_route:
        lines.append(
            f"Q{results.index(r) + 1}: {r.get('question')!r} | "
            f"source={r.get('ask_source')} | issues={r.get('issues')}"
        )
    if not wrong_route:
        lines.append("(none)")

    OUT_SUMMARY.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--start-from", type=int, default=1, help="Resume from question index (1-50)")
    args = parser.parse_args()
    start = max(1, min(int(args.start_from or 1), len(QUESTIONS)))

    if len(QUESTIONS) != 50:
        print(f"ERROR: expected 50 questions, got {len(QUESTIONS)}", file=sys.stderr)
        return 2

    t0 = time.time()
    admin_token = audit._read_admin_secret()
    if not admin_token:
        print("WARN: ADMIN_SECRET not set — admin row fetch may fail", file=sys.stderr)

    print(f"API: {audit.DEFAULT_API}")
    demo = audit._demo_login()
    uid = int(demo["id"])
    api_key = str(demo["api_key"])
    print(f"Demo user id={uid}")
    kundli, birth = audit._user_kundli(uid, api_key)
    print(f"Chart planets={len(kundli.get('planets') or [])}")
    print(f"Running Q{start}..{len(QUESTIONS)} (no skips)...", flush=True)

    results: list[dict] = []
    lines: list[str] = [
        f"FULL AUDIT 50 — {audit.DEFAULT_API}",
        f"Demo user id={uid}",
        "",
    ]

    if start > 1 and OUT_JSON.is_file():
        try:
            prev = json.loads(OUT_JSON.read_text(encoding="utf-8"))
            if isinstance(prev, list):
                results = [r for r in prev if int(r.get("q_index") or 0) < start]
                print(f"Resumed: kept {len(results)} prior results", flush=True)
        except Exception as exc:
            print(f"Resume load skipped: {exc}", flush=True)

    if OUT_TXT.is_file() and start > 1:
        try:
            lines = OUT_TXT.read_text(encoding="utf-8").splitlines()
        except Exception:
            pass

    for i, q in enumerate(QUESTIONS, 1):
        if i < start:
            continue
        print(f"[{i}/50] {q[:60]}...", flush=True)
        lines.append(f"\n{'=' * 72}\n[{i}/50] {q}\n{'=' * 72}")
        try:
            ask_out = audit._ask_stream(q, "hi", uid, api_key, kundli, birth)
            admin_row = audit._admin_latest(uid, admin_token, q) if admin_token else None
            report = audit._audit(q, ask_out, admin_row)
        except Exception as exc:
            report = {
                "question": q,
                "pass": False,
                "issues": [f"RUNTIME_ERROR — {exc}"],
                "answer_text": "",
                "ask_source": "",
                "admin_engine": "",
            }

        report["q_index"] = i
        results.append(report)

        lines.append("\n=== ANSWER (first 400) ===\n" + (report.get("answer_text") or "(empty)")[:400])
        lines.append(
            f"\n=== PATH ===\nsource={report.get('ask_source')} | engine_tag={report.get('engine_tag')} | "
            f"admin_engine={report.get('admin_engine')!r} | pass={report.get('pass')} | "
            f"content_ok={_content_ok(report)}"
        )
        ev = report.get("evidence_audit") or {}
        lines.append(f"evidence_ok={ev.get('evidence_ok')}")
        for w in ev.get("warnings") or []:
            lines.append(f"  WARN: {w}")
        lines.append(f"issues: {report.get('issues')}")

        # Incremental save — crash-safe
        OUT_JSON.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
        OUT_TXT.write_text("\n".join(lines), encoding="utf-8")
        print(
            f"  done pass={report.get('pass')} content_ok={_content_ok(report)} source={report.get('ask_source')}",
            flush=True,
        )

    elapsed = time.time() - t0
    _write_summary(results, elapsed)
    strict = sum(1 for r in results if r.get("pass"))
    content = sum(1 for r in results if _content_ok(r))
    print(f"\nSUMMARY: strict {strict}/50 | content {content}/50 | {elapsed:.0f}s")
    print(f"JSON -> {OUT_JSON}")
    print(f"TXT  -> {OUT_TXT}")
    print(f"SUMMARY -> {OUT_SUMMARY}")
    return 0 if strict == len(QUESTIONS) else 1


if __name__ == "__main__":
    raise SystemExit(main())

