#!/usr/bin/env python3
"""Full live ASK AUDIT — 50 compatibility questions (non-timing, no skips)."""
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
    "Kya hum dono compatible hain?",
    "Kya hum ek dusre ke liye sahi partner hain?",
    "Kya hamari relationship long-term compatible hai?",
    "Kya hamari personalities match karti hain?",
    "Kya hamari thinking match karti hai?",
    "Kya hamare values same hain?",
    "Kya hamare life goals match karte hain?",
    "Kya hamari expectations ek jaisi hain?",
    "Kya hum emotionally compatible hain?",
    "Kya hum mentally compatible hain?",
    "Kya hum intellectually compatible hain?",
    "Kya hum spiritually compatible hain?",
    "Kya hum physically compatible hain?",
    "Kya hamari sexual compatibility achhi hai?",
    "Kya hamari communication compatibility achhi hai?",
    "Kya hum ek dusre ko achhe se samajhte hain?",
    "Kya hum ek dusre ko complete karte hain?",
    "Kya hum ek dusre ki weaknesses handle kar sakte hain?",
    "Kya hum ek dusre ki strengths appreciate karte hain?",
    "Kya hamari bonding naturally strong hai?",
    "Kya hamare beech mutual understanding hai?",
    "Kya hum ek dusre par trust kar sakte hain?",
    "Kya hum difficult situations me saath denge?",
    "Kya hum ek team ki tarah kaam karenge?",
    "Kya hum conflict ko achhe se solve kar payenge?",
    "Kya hum arguments ke baad relationship sambhal lenge?",
    "Kya hamare beech ego clashes rahenge?",
    "Kya hamari communication style match karti hai?",
    "Kya hum emotionally ek dusre ko support karenge?",
    "Kya hum financially compatible hain?",
    "Kya money ko lekar hamari soch milti hai?",
    "Kya family values match karti hain?",
    "Kya lifestyle compatibility achhi hai?",
    "Kya hamari habits ek dusre ke saath fit hoti hain?",
    "Kya hamari priorities same hain?",
    "Kya hum ek dusre ko respect karte hain?",
    "Kya hum ek dusre ko space de payenge?",
    "Kya hum possessiveness ko handle kar payenge?",
    "Kya jealousy relationship ko affect karegi?",
    "Kya hamare differences relationship ko weak karenge?",
    "Kya hum compromise kar payenge?",
    "Kya hum future planning me compatible hain?",
    "Kya hum marriage ke liye compatible hain?",
    "Kya hamara relationship healthy rahega?",
    "Kya hamara relationship balanced rahega?",
    "Kya hum lifetime partners ban sakte hain?",
    "Kya hamari compatibility strong hai ya average?",
    "Kya hamari compatibility challenges ke baad bhi bani rahegi?",
    "Kya overall hum ek successful couple ban sakte hain?",
    "Overall, hamari compatibility kitni strong hai?",
]

OUT_JSON = ROOT / "scripts" / "full_audit_compatibility_50.json"
OUT_TXT = ROOT / "scripts" / "full_audit_compatibility_50.txt"
OUT_SUMMARY = ROOT / "scripts" / "full_audit_compatibility_50_summary.txt"


def _content_ok(report: dict) -> bool:
    """MR static path + real answer (ignores admin-evidence strict fail)."""
    src = str(report.get("ask_source") or "")
    text = str(report.get("answer_text") or "").strip()
    issues = report.get("issues") or []
    blocked = any(
        str(x).startswith(
            (
                "BLOCKED",
                "ENGINE_REFUSAL",
                "DIRECT_LLM",
                "TIMING_Q_BUT_STATIC",
                "WRONG_ENGINE",
                "RUNTIME",
            )
        )
        for x in issues
    )
    return bool(text) and src == "mr_engine_then_llm" and "timing_domain_clarifier" not in src and not blocked


def _write_summary(results: list[dict], elapsed_s: float) -> None:
    strict = sum(1 for r in results if r.get("pass"))
    content = sum(1 for r in results if _content_ok(r))
    no_admin = sum(
        1 for r in results if any("NO_ADMIN_ENGINE" in str(i) for i in (r.get("issues") or []))
    )
    no_answer = sum(1 for r in results if not (r.get("answer_text") or "").strip())
    wrong_route = [r for r in results if not _content_ok(r)]

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
            f"Q{r.get('q_index')}: {r.get('question')!r} | "
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
        print("WARN: ADMIN_SECRET not set - admin row fetch may fail", file=sys.stderr)

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
        f"FULL COMPATIBILITY AUDIT 50 - {audit.DEFAULT_API}",
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
                "issues": [f"RUNTIME_ERROR - {exc}"],
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
