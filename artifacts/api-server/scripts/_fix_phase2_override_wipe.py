"""Fix Phase2 archetype override wipe + ensure classify skip."""
from pathlib import Path

path = Path(__file__).resolve().parents[1] / "openai_helper.py"
src = path.read_text(encoding="utf-8")

old = '''        except Exception as _p2r_exc:
            print(f"[raw_passthrough] PHASE2_SOLE_ROUTE skipped: {_p2r_exc}", flush=True)

    _mr_archetype_override = None
    _career_archetype_override = None
    _finance_archetype_override = None
    _health_archetype_override = None
    _education_archetype_override = None
    _children_archetype_override = None
    _property_archetype_override = None
    _travel_archetype_override = None
    _litigation_archetype_override = None
    if (not _phase2_ok) and (os.environ.get("ASK_LLM_INTENT") or "1").strip() == "1":
'''

new = '''        except Exception as _p2r_exc:
            print(f"[raw_passthrough] PHASE2_SOLE_ROUTE skipped: {_p2r_exc}", flush=True)

    if not _phase2_ok:
        _mr_archetype_override = None
        _career_archetype_override = None
        _finance_archetype_override = None
        _health_archetype_override = None
        _education_archetype_override = None
        _children_archetype_override = None
        _property_archetype_override = None
        _travel_archetype_override = None
        _litigation_archetype_override = None
    if (not _phase2_ok) and (os.environ.get("ASK_LLM_INTENT") or "1").strip() == "1":
'''

if old not in src:
    # maybe already fixed or classify line differs
    old2 = '''        except Exception as _p2r_exc:
            print(f"[raw_passthrough] PHASE2_SOLE_ROUTE skipped: {_p2r_exc}", flush=True)

    _mr_archetype_override = None
    _career_archetype_override = None
    _finance_archetype_override = None
    _health_archetype_override = None
    _education_archetype_override = None
    _children_archetype_override = None
    _property_archetype_override = None
    _travel_archetype_override = None
    _litigation_archetype_override = None
    if (os.environ.get("ASK_LLM_INTENT") or "1").strip() == "1":
'''
    new2 = new
    if old2 in src:
        src = src.replace(old2, new2, 1)
        print("fixed wipe + classify gate (variant2)")
    else:
        # show context
        i = src.find("PHASE2_SOLE_ROUTE skipped")
        print("NOT FOUND; context:")
        print(repr(src[i:i+500] if i >= 0 else "no sole route"))
        raise SystemExit(1)
else:
    src = src.replace(old, new, 1)
    print("fixed wipe (variant1)")

# Also init overrides to None BEFORE phase2 block if missing
init = '''    # ── Understand meaning → route to specific static/timing engine ─────
    _llm_intent = None
    _llm_intent_record = None
    _intent_source = "regex"
    if _phase2_ok and isinstance(_phase2_understand, dict):
'''
init_fix = '''    # ── Understand meaning → route to specific static/timing engine ─────
    _llm_intent = None
    _llm_intent_record = None
    _intent_source = "regex"
    _mr_archetype_override = None
    _career_archetype_override = None
    _finance_archetype_override = None
    _health_archetype_override = None
    _education_archetype_override = None
    _children_archetype_override = None
    _property_archetype_override = None
    _travel_archetype_override = None
    _litigation_archetype_override = None
    if _phase2_ok and isinstance(_phase2_understand, dict):
'''
if init in src and "_mr_archetype_override = None\n    _career_archetype_override = None\n    _finance_archetype_override = None\n    _health_archetype_override = None\n    _education_archetype_override = None\n    _children_archetype_override = None\n    _property_archetype_override = None\n    _travel_archetype_override = None\n    _litigation_archetype_override = None\n    if _phase2_ok" not in src:
    src = src.replace(init, init_fix, 1)
    print("added pre-init before phase2")

path.write_text(src, encoding="utf-8")
print("ok")
