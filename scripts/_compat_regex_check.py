from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
API_SERVER = ROOT / "artifacts" / "api-server"
sys.path.insert(0, str(API_SERVER))

from ask_scope_gate import assess_ask_scope  # type: ignore
from ask_marriage_relationship_slice import (  # type: ignore
    is_marriage_relationship_static_question,
)


def main() -> None:
    cases_scope = [
        "Kya hum dono compatible hain?",
        "Kya hamare values same hain?",
        "Kya hamare life goals match karte hain?",
        "Kya hum emotionally compatible hain?",
        "Kya hum mentally compatible hain?",
        "Kya hamari sexual compatibility achhi hai?",
        "Kya hamari communication compatibility achhi hai?",
        "Kya lifestyle compatibility achhi hai?",
        "Kya hum ek dusre ko respect karte hain?",
        "Kya hum ek dusre ko space de payenge?",
        "Kya jealousy relationship ko affect karegi?",
        "Kya hum compromise kar payenge?",
    ]

    print("=== scope_gate allowed? ===")
    for q in cases_scope:
        v = assess_ask_scope(q)
        print(f"Q: {q}")
        print(f"  allowed={v.allowed} reason={v.reason} category={getattr(v,'category',None)}")

    print("\n=== MR static detection? ===")
    cases_mr = [
        "Kya hum difficult situations me saath denge?",
        "Kya jealousy relationship ko affect karegi?",
        "Kya hum dono compatible hain?",
        "Kya hum ek dusre ko respect karte hain?",
        "Kya hamari bonding naturally strong hai?",
    ]
    for q in cases_mr:
        print(f"Q: {q}")
        print(f"  is_marriage_relationship_static_question={is_marriage_relationship_static_question(q)}")


if __name__ == "__main__":
    main()

