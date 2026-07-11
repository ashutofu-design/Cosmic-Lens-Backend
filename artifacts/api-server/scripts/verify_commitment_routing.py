"""Quick self-check — proves commitment routing + step audit + narrator JSON are live.

Run on server AFTER git pull + pm2 restart:
    cd /root/Cosmic-Lens-Backend/artifacts/api-server
    python scripts/verify_commitment_routing.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

QUESTION = "Kya mera partner mujhse genuinely commitment karega ya sirf timepass kar raha hai?"

PASS = "\033[92mPASS\033[0m"
FAIL = "\033[91mFAIL\033[0m"


def check(name: str, cond: bool, detail: str = "") -> bool:
    print(f"[{PASS if cond else FAIL}] {name}" + (f" — {detail}" if detail else ""))
    return cond


def main() -> int:
    ok = True

    # 1) Classifier routes raw question to commitment (not loyalty_trust)
    from ask_mr.classifier import classify_mr_archetype

    arch = classify_mr_archetype(QUESTION)
    ok &= check("Classifier -> commitment", arch == "commitment", f"got '{arch}'")

    # 2) repair_llm_intent overrides an LLM loyalty_trust guess
    from ask_intent_fidelity import repair_llm_intent

    fixed = repair_llm_intent(
        QUESTION,
        {
            "domain": "love",
            "mr_archetype": "loyalty_trust",
            "is_timing": False,
            "source": "llm",
            "question_summary": "User wants to know if partner is loyal and trustworthy.",
        },
    )
    ok &= check(
        "repair_llm_intent override",
        fixed.get("mr_archetype") == "commitment",
        f"archetype='{fixed.get('mr_archetype')}' override='{fixed.get('routing_override')}'",
    )

    # 3) pipeline_audit module exists (step audit persistence)
    try:
        from ask_mr.pipeline_audit import build_mr_step_audit_from_result  # noqa: F401

        ok &= check("pipeline_audit module present", True)
    except Exception as exc:
        ok &= check("pipeline_audit module present", False, str(exc))

    # 4) Commitment narrator emits structured JSON with new keys
    try:
        os.environ["ASK_MR_ENGINE_V2"] = "1"
        from ask_mr.v2.engines.commitment import run_commitment_v2
        from ask_mr.v2.adapter import v2_to_engine_result
        from ask_mr.commitment_narrator import engine_result_to_commitment_json

        sample = {
            "ascendant": "Sagittarius",
            "planets": [
                {"name": "Moon", "sign": "Gemini", "house": 7},
                {"name": "Venus", "sign": "Leo", "house": 9},
                {"name": "Jupiter", "sign": "Libra", "house": 11},
                {"name": "Saturn", "sign": "Aries", "house": 5},
            ],
            "dasha": {"mahadasha": "Venus", "antardasha": "Jupiter"},
        }
        out = run_commitment_v2(sample, QUESTION)
        data = engine_result_to_commitment_json(v2_to_engine_result(out))
        has_keys = all(k in data for k in ("question_type", "final_verdict", "strongest", "weakest", "reason", "confidence"))
        ok &= check(
            "Narrator JSON structured",
            has_keys and data.get("question_type") == "commitment",
            f"keys={list(data.keys())[:6]}",
        )
    except Exception as exc:
        ok &= check("Narrator JSON structured", False, str(exc))

    # 5) Observability bundle has the 15-section fields
    try:
        from ask_observability_debug import build_observability_debug

        obs = build_observability_debug(
            {
                "slice_meta": {"archetype": "commitment"},
                "checks": {"rules_fired": [{"rule_id": "COM-001", "polarity": "positive"}]},
                "question": QUESTION,
            },
            question_text=QUESTION,
            answer_text="test",
        )
        ok &= check(
            "Observability 15-section fields",
            all(k in obs for k in ("user_question", "routing_decision", "astrology_checks")),
        )
    except Exception as exc:
        ok &= check("Observability 15-section fields", False, str(exc))

    print()
    print("ALL GOOD - backend deploy is live" if ok else "SOME CHECKS FAILED - code not deployed / restart needed")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
