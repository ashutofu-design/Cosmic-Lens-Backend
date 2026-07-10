#!/usr/bin/env python3
"""Full live ASK AUDIT — 50 relationship promise/static questions (no skips)."""
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
    "Kya meri life me serious relationship ka yog hai?",
    "Kya mujhe true love milega?",
    "Kya meri kundli relationship support karti hai?",
    "Kya meri life me romantic relationship banega?",
    "Kya meri love life achhi rahegi?",
    "Kya meri kundli me long-term relationship ka yog hai?",
    "Kya main committed relationship ke liye bana/bani hoon?",
    "Kya meri kundli stable relationship ka indication deti hai?",
    "Kya mujhe genuine partner milega?",
    "Kya meri life me meaningful relationship hoga?",
    "Kya meri kundli me lifelong companionship ka yog hai?",
    "Kya meri love life successful hogi?",
    "Kya meri kundli healthy relationship support karti hai?",
    "Kya meri kundli me relationship weak hai ya strong?",
    "Kya meri life me lasting emotional bond banega?",
    "Kya meri life me soulmate jaisa connection possible hai?",
    "Kya meri kundli ek serious relationship ka promise deti hai?",
    "Kya meri kundli me multiple relationships ke yog hain?",
    "Kya meri life me sirf casual relationships rahenge?",
    "Kya meri life me meaningful love experience hoga?",
    "Kya meri kundli emotional fulfillment dikhati hai?",
    "Kya mujhe loyal partner milne ka yog hai?",
    "Kya meri kundli me supportive partner ka yog hai?",
    "Kya meri life me trustworthy relationship banega?",
    "Kya meri love life satisfying rahegi?",
    "Kya meri kundli relationship ke liye favorable hai?",
    "Kya mujhe emotionally compatible partner milega?",
    "Kya meri kundli me relationship ki kami dikh rahi hai?",
    "Kya meri life me permanent relationship possible hai?",
    "Kya meri kundli me relationship naturally sustain hoga?",
    "Kya meri love life me happiness milegi?",
    "Kya meri life me real emotional connection banega?",
    "Kya meri kundli successful partnership support karti hai?",
    "Kya mujhe life partner ke saath achha bond milega?",
    "Kya meri life me pyaar tik paayega?",
    "Kya meri kundli strong relationship foundation dikhati hai?",
    "Kya meri life me genuine companionship milegi?",
    "Kya meri kundli me relationship se zyada loneliness dikh rahi hai?",
    "Kya meri love life balanced rahegi?",
    "Kya meri kundli relationship me satisfaction dikhati hai?",
    "Kya mujhe emotionally secure relationship milega?",
    "Kya meri life me deep emotional attachment possible hai?",
    "Kya meri kundli lasting love indicate karti hai?",
    "Kya meri life me meaningful romantic journey hogi?",
    "Kya meri kundli relationship happiness ka promise deti hai?",
    "Kya meri life me pyaar aur support dono milenge?",
    "Kya meri kundli committed partnership ke liye strong hai?",
    "Kya meri life me genuine affection aur care milegi?",
    "Kya meri kundli relationship ke liye positive hai?",
    "Overall, kya meri kundli relationship ke liye strong promise deti hai?",
]

OUT_JSON = ROOT / "scripts" / "full_audit_promise_50.json"
OUT_TXT = ROOT / "scripts" / "full_audit_promise_50.txt"
OUT_SUMMARY = ROOT / "scripts" / "full_audit_promise_50_summary.txt"


def _content_ok(report: dict) -> bool:
    """MR static path + real answer (ignores admin evidence strict fail)."""
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
        1
        for r in results
        if any("NO_ADMIN_ENGINE" in str(i) for i in (r.get("issues") or []))
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
    lines: list[str] = [f"FULL AUDIT 50 — {audit.DEFAULT_API}", f"Demo user id={uid}", ""]
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
            f"  done pass={report.get('pass')} content_ok={_content_ok(report)} "
            f"source={report.get('ask_source')}",
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
