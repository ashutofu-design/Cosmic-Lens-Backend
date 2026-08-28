#!/usr/bin/env python3
"""Ask Cosmic Help from the VS Code / terminal — answer prints here.

Usage (from artifacts/api-server):
  python scripts/ask_cosmic_help.py "Bhai signup ke baad free me kitne sawaal milte hain?"
  python scripts/ask_cosmic_help.py --pricing
  python scripts/ask_cosmic_help.py --pricing --from 1 --to 5
  python scripts/ask_cosmic_help.py -q scripts/cosmic_help_pricing_questions.txt
"""
from __future__ import annotations

import argparse
import os
import sys
import time
from pathlib import Path

API_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(API_ROOT))
os.chdir(API_ROOT)

try:
    from dotenv import load_dotenv

    load_dotenv(API_ROOT / ".env", override=True)
except Exception:
    pass

# Roundabout pricing questions for manual / batch check (expected in comments).
PRICING_QUESTIONS: list[tuple[str, str]] = [
    (
        "Bhai signup ke baad free me kitne sawaal milte hain Ask pe?",
        "3 free V1",
    ),
    (
        "Sabse sasta pack kitne ka hota hai aur usme questions kitne?",
        "Starter ₹49 · 8 Q · 7 days",
    ),
    (
        "Woh jo popular wala pack log lete hain, uska rate aur validity kya hai?",
        "Popular ₹99 · 15 Q · 14 days",
    ),
    (
        "Zyada questions chahiye to power pack kitna padta hai?",
        "Power ₹299 · 45 Q · 30 days",
    ),
    (
        "V3 Live me half hour session roughly kitne ka?",
        "30 min ₹699",
    ),
    (
        "Sirf 15 minute live guide se baat karni ho to kitna charge?",
        "15 min ₹399",
    ),
    (
        "Poora 1 hour V3 Live book karun to total kitna?",
        "60 min ₹1299",
    ),
    (
        "Kya yahan monthly Basic/Pro subscription chal raha hai jaise ₹199 ya ₹499 mahine?",
        "No monthly plan — one-time only",
    ),
    (
        "App me Pro likha hai to kya har mahine paise katenge?",
        "Pro = one-time, not subscription",
    ),
    (
        "Love Reality Basic free hai ya pehle pay karna padta hai?",
        "Basic free on-screen",
    ),
    (
        "Love Reality ka PDF report roughly kitne ka padta hai?",
        "Pro PDF ₹499 (+ Priority ₹299)",
    ),
    (
        "Kundli Milan ka personalized video kitna costly hai?",
        "Video ₹1299 (PDF ₹699)",
    ),
    (
        "Numerology me sirf PDF lena ho to offer price kya dikhaya jata hai?",
        "PDF ₹299",
    ),
    (
        "Palmistry Pro PDF aur VIP video ka difference price me kitna hai?",
        "PDF ₹1499 · VIP ₹2999",
    ),
    (
        "AstroVastu me 1 room scan credit pack approximately kitna?",
        "1 Room Scan ₹99",
    ),
    (
        "Business Vastu me shop ka full floor-plan PDF roughly kitna?",
        "Shop PDF ₹2999",
    ),
    (
        "Career Life Map kholne se pehle ₹1 wala unlock kab lagta hai?",
        "Career ₹1 unlock only",
    ),
    (
        "Birth time sahi nahi pata — rectification roughly kitne ka?",
        "BTR ₹999",
    ),
    (
        "Priority delivery extra kitna lagta hai report vs video pe?",
        "Report ~₹149 · video ~₹299",
    ),
    (
        "Wallet me paise add karke baad me use kar sakte hain kya?",
        "No rupee wallet",
    ),
]


def _ask(text: str, lang: str | None) -> dict:
    from support_agent.agent import run

    return run(text, lang=lang)


def _print_result(i: int | None, q: str, expect: str | None, out: dict, ms: int) -> None:
    prefix = f"Q{i}. " if i is not None else ""
    print("=" * 72)
    print(f"{prefix}USER: {q}")
    if expect:
        print(f"EXPECT: {expect}")
    print("-" * 72)
    print(f"source={out.get('source')}  escalate={out.get('escalate')}  "
          f"state={out.get('agent_state')}  {ms}ms")
    print()
    print(str(out.get("reply") or "").strip() or "(empty reply)")
    print()


def _load_file(path: Path) -> list[str]:
    lines = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        lines.append(line)
    return lines


def main() -> int:
    p = argparse.ArgumentParser(description="Ask Cosmic Help from the terminal")
    p.add_argument("question", nargs="*", help="Question text (or use --pricing / -q)")
    p.add_argument("--pricing", action="store_true", help="Run built-in 20 pricing questions")
    p.add_argument("-q", "--questions-file", type=Path, help="One question per line")
    p.add_argument("--from", dest="from_i", type=int, default=1, help="Start index (1-based)")
    p.add_argument("--to", dest="to_i", type=int, default=0, help="End index inclusive (0=all)")
    p.add_argument("--lang", default=None, help="Force lang: en | hi | hn")
    p.add_argument("-v", "--verbose", action="store_true")
    args = p.parse_args()

    cases: list[tuple[str, str | None]] = []
    if args.pricing:
        cases = [(q, exp) for q, exp in PRICING_QUESTIONS]
    elif args.questions_file:
        for line in _load_file(args.questions_file):
            cases.append((line, None))
    elif args.question:
        cases = [(" ".join(args.question), None)]
    else:
        p.print_help()
        print("\nExamples:")
        print('  python scripts/ask_cosmic_help.py "Starter pack kitne ka hai?"')
        print("  python scripts/ask_cosmic_help.py --pricing")
        return 2

    start = max(1, args.from_i)
    end = args.to_i if args.to_i > 0 else len(cases)
    slice_cases = list(enumerate(cases[start - 1 : end], start=start))

    from openai_helper import _get_client
    from support_agent.agent import _model

    client = _get_client()
    print(f"model={_model()}  openai={'YES' if client else 'NO'}")
    if client is None:
        print("WARN: OpenAI client missing — answers may escalate / fail")
    print(f"running {len(slice_cases)} question(s)\n")

    for i, (q, expect) in slice_cases:
        t0 = time.monotonic()
        try:
            out = _ask(q, args.lang)
        except Exception as exc:
            print("=" * 72)
            print(f"Q{i}. USER: {q}")
            print(f"ERROR: {exc}")
            print()
            continue
        ms = int((time.monotonic() - t0) * 1000)
        _print_result(i if len(slice_cases) > 1 or args.pricing else None, q, expect, out, ms)
        if args.verbose and isinstance(out.get("tools"), dict):
            tools = out["tools"]
            print(f"[tools keys] {sorted(tools.keys())}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
