#!/usr/bin/env python3
"""Verify one or more Ask questions — routing + answer (local pipeline or live API).

Usage:
  python scripts/verify_ask_question.py "Meri shaadi kab hogi?"
  python scripts/verify_ask_question.py -v "Mera pyaar kab milega?"
  python scripts/verify_ask_question.py --api http://127.0.0.1:3000 "Career kaisi rahegi?"
  python scripts/verify_ask_question.py -v -q scripts/love_live_test_questions.txt
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


def _ctx(result: dict) -> dict:
    ctx = result.get("admin_llm_context")
    return ctx if isinstance(ctx, dict) else {}


def _trace(ctx: dict) -> dict:
    blocks = ctx.get("blocks") if isinstance(ctx.get("blocks"), dict) else {}
    tr = blocks.get("engine_trace")
    return tr if isinstance(tr, dict) else {}


def _step8_month(trace: dict, ctx: dict) -> str:
    sa = trace.get("step_audit") if isinstance(trace.get("step_audit"), dict) else {}
    s8 = sa.get("step8") if isinstance(sa.get("step8"), dict) else {}
    sm = ctx.get("slice_meta") if isinstance(ctx.get("slice_meta"), dict) else {}
    sa2 = sm.get("step_audit") if isinstance(sm.get("step_audit"), dict) else {}
    s8b = sa2.get("step8") if isinstance(sa2.get("step8"), dict) else {}
    for block in (s8, s8b):
        for key in ("event_month_year", "marriage_month_year", "primary_window"):
            val = block.get(key)
            if val:
                return str(val)
    return ""


def classify_routing(ctx: dict, trace: dict) -> str:
    checks = ctx.get("checks") if isinstance(ctx.get("checks"), dict) else {}
    sm = ctx.get("slice_meta") if isinstance(ctx.get("slice_meta"), dict) else {}
    slice_id = str(sm.get("slice") or checks.get("slice_type") or "")
    engine = str(trace.get("engine") or "")
    llm_called = ctx.get("llm_called")
    answer_path = str(ctx.get("answer_path") or "")
    is_timing = ctx.get("is_timing")

    if engine == "marriage_timing_m17" or slice_id in (
        "marriage_timing_m17",
        "timing_marriage_engine",
    ):
        return "MARRIAGE_TIMING (M17)"
    if engine == "love_timing_v1" or slice_id == "love_timing_v1":
        return "LOVE_TIMING (engine + Kaal)"
    if slice_id == "mr_engine_v1" or checks.get("mr_engine"):
        return "MR_STATIC (relationship engine)"
    if slice_id == "marriage_relationship":
        return "DCR_LOVE (static slice + LLM)"
    if answer_path == "direct_llm" or checks.get("direct_llm_bypass"):
        return "DIRECT_LLM (no engine)"
    if llm_called is False or answer_path == "engine_only":
        return "ENGINE_ONLY (template, no LLM narrator)"
    if is_timing and engine:
        return f"TIMING_ENGINE ({engine or slice_id})"
    if llm_called:
        return f"ENGINE_THEN_LLM ({engine or slice_id or 'unknown'})"
    return f"UNKNOWN ({slice_id or engine or '—'})"


def summarize(question: str, result: dict, *, verbose: bool = False) -> str:
    text = (result.get("text") or result.get("answer") or "").strip()
    preview = text[:400] + ("…" if len(text) > 400 else "")
    ctx = _ctx(result)
    trace = _trace(ctx)
    checks = ctx.get("checks") if isinstance(ctx.get("checks"), dict) else {}
    sm = ctx.get("slice_meta") if isinstance(ctx.get("slice_meta"), dict) else {}

    lines = [
        f"Q: {question}",
        f"  topic:          {result.get('topic', '—')}",
        f"  engine_tag:     {result.get('engine_tag', '—')}",
        f"  source:         {result.get('source', '—')}",
        f"  routing:        {classify_routing(ctx, trace)}",
    ]

    if ctx:
        lines.extend([
            f"  question_type:  {ctx.get('question_type', '—')}",
            f"  is_timing:      {ctx.get('is_timing', '—')}",
            f"  route:          {ctx.get('route', '—')}",
            f"  intent_source:  {ctx.get('intent_source', '—')}",
            f"  llm_called:     {ctx.get('llm_called', '—')}",
            f"  answer_path:    {ctx.get('answer_path_label') or ctx.get('answer_path', '—')}",
        ])
        understood = ctx.get("understanding_line") or ctx.get("question_understood")
        if understood:
            lines.append(f"  understood:     {understood}")
        li = ctx.get("llm_intent") or {}
        if isinstance(li, dict) and (li.get("domain") or li.get("mr_archetype")):
            lines.append(
                f"  llm_intent:     domain={li.get('domain')} timing={li.get('is_timing')} "
                f"archetype={li.get('mr_archetype')} conf={li.get('confidence')}"
            )

    lines.extend([
        f"  slice:          {sm.get('slice') or checks.get('slice_type') or '—'}",
        f"  engine_trace:   {trace.get('engine') or '—'}",
        f"  pipeline:       {trace.get('pipeline_version') or '—'}",
        f"  verdict:        {sm.get('verdict') or trace.get('verdict') or '—'}",
        f"  primary_window: {trace.get('primary_window') or '—'}",
        f"  step8_month:    {_step8_month(trace, ctx) or '—'}",
        f"  answer:         {preview or '(empty)'}",
    ])

    if verbose and trace.get("step_audit"):
        sa = trace["step_audit"]
        order = trace.get("step_order") or list(sa.keys())
        lines.append("  --- admin step_audit ---")
        for key in order:
            if key not in sa:
                continue
            step = sa[key]
            if not isinstance(step, dict):
                continue
            detail = str(step.get("detail") or "")[:120]
            lines.append(f"    {key}: {step.get('name', key)} | {step.get('status', '—')} | {detail}")

    return "\n".join(lines)


def main() -> int:
    p = argparse.ArgumentParser(description="Verify Ask questions (live test helper)")
    p.add_argument("questions", nargs="*", help="Question text(s)")
    p.add_argument("-q", "--file", help="File with one question per line (# comments ok)")
    p.add_argument("--api", help="Live API base URL (default: local pipeline on server)")
    p.add_argument("--lang", default="hn")
    p.add_argument("-v", "--verbose", action="store_true", help="Show step_audit lines")
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
            print(summarize(q, result, verbose=args.verbose))
            if not (result.get("text") or result.get("answer")):
                print("  WARN: NO ANSWER TEXT")
                errors += 1
        except Exception as e:
            print(f"Q: {q}\n  ERROR: {e}")
            errors += 1

    print(f"\nDone: {len(questions) - errors}/{len(questions)} OK")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
