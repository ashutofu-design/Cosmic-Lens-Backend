#!/usr/bin/env python3
"""Verify one or more Ask questions — routing + answer (local pipeline or live API).

Usage:
  python scripts/verify_ask_question.py "Meri shaadi kab hogi?"
  python scripts/verify_ask_question.py --api https://stood-brian-simply-cedar.trycloudflare.com "Career kaisi rahegi?"
  python scripts/verify_ask_question.py -q questions.txt
"""
from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

SAMPLE_KUNDLI = {
    "ascendant": "Sagittarius",
    "moonSign": "Gemini",
    "planets": [
        {"name": "Moon", "sign": "Gemini", "house": 7},
        {"name": "Saturn", "sign": "Virgo", "house": 10},
        {"name": "Mars", "sign": "Cancer", "house": 8},
        {"name": "Venus", "sign": "Leo", "house": 9},
        {"name": "Mercury", "sign": "Aries", "house": 5},
        {"name": "Jupiter", "sign": "Pisces", "house": 4},
        {"name": "Rahu", "sign": "Aquarius", "house": 3},
        {"name": "Ketu", "sign": "Leo", "house": 9},
        {"name": "Sun", "sign": "Capricorn", "house": 2},
    ],
    "dashas": [
        {
            "lord": "Sun",
            "start": "2020-01-01",
            "end": "2026-01-01",
            "subDashas": [
                {
                    "lord": "Moon",
                    "start": "2024-01-01",
                    "end": "2026-01-01",
                    "subDashas": [
                        {"lord": "Mars", "start": "2025-01-01", "end": "2025-08-01"}
                    ],
                }
            ],
        }
    ],
}


def ask_local(question: str, lang: str = "hn") -> dict:
    from openai_helper import raw_passthrough_ask

    return raw_passthrough_ask(question, SAMPLE_KUNDLI, lang=lang) or {}


def ask_api(base: str, question: str, lang: str = "hn") -> dict:
    url = base.rstrip("/") + "/api/ask"
    payload = json.dumps(
        {"question": question, "kundli": SAMPLE_KUNDLI, "lang": lang},
        ensure_ascii=False,
    ).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=payload,
        headers={"Content-Type": "application/json; charset=utf-8"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=120) as resp:
        return json.loads(resp.read().decode("utf-8"))


def summarize(question: str, result: dict) -> str:
    text = (result.get("text") or result.get("answer") or "").strip()
    preview = text[:400] + ("…" if len(text) > 400 else "")
    lines = [
        f"Q: {question}",
        f"  topic:       {result.get('topic', '—')}",
        f"  engine_tag:  {result.get('engine_tag', '—')}",
        f"  source:      {result.get('source', '—')}",
        f"  confidence:  {result.get('confidence', '—')}",
    ]
    ctx = result.get("admin_llm_context") or {}
    if isinstance(ctx, dict):
        understood = ctx.get("understanding_line") or ctx.get("question_understood")
        if understood:
            lines.append(f"  LLM understood: {understood}")
        path = ctx.get("answer_path_label") or ctx.get("answer_path")
        if path:
            lines.append(f"  answer_path: {path}")
        li = ctx.get("llm_intent") or {}
        if isinstance(li, dict) and li.get("domain"):
            lines.append(
                f"  intent: domain={li.get('domain')} timing={li.get('is_timing')} "
                f"conf={li.get('confidence')}"
            )
    lines.append(f"  answer: {preview or '(empty)'}")
    return "\n".join(lines)


def main() -> int:
    p = argparse.ArgumentParser(description="Verify Ask questions")
    p.add_argument("questions", nargs="*", help="Question text(s)")
    p.add_argument("-q", "--file", help="File with one question per line")
    p.add_argument("--api", help="Live API base URL (default: local pipeline)")
    p.add_argument("--lang", default="hn")
    args = p.parse_args()

    questions: list[str] = list(args.questions)
    if args.file:
        questions.extend(
            ln.strip()
            for ln in Path(args.file).read_text(encoding="utf-8").splitlines()
            if ln.strip() and not ln.strip().startswith("#")
        )
    if not questions:
        p.error("Provide question(s) or -q file")

    errors = 0
    for i, q in enumerate(questions, 1):
        print(f"\n{'='*60}\n[{i}/{len(questions)}]")
        try:
            if args.api:
                result = ask_api(args.api, q, args.lang)
            else:
                result = ask_local(q, args.lang)
            print(summarize(q, result))
            if not (result.get("text") or result.get("answer")):
                print("  ⚠ NO ANSWER TEXT")
                errors += 1
        except Exception as e:
            print(f"Q: {q}\n  ERROR: {e}")
            errors += 1

    print(f"\nDone: {len(questions) - errors}/{len(questions)} OK")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
