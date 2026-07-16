from pathlib import Path
p = Path(__file__).resolve().parents[1] / "openai_helper.py"
src = p.read_text(encoding="utf-8")
old = """        from ask_understand_phase2 import (
            phase2_understand_enabled,
            refuse_payload,
            run_understand_phase2,
            understand_to_admin,
        )
"""
new = """        from ask_understand_phase2 import (
            phase2_understand_enabled,
            run_understand_phase2,
            understand_to_admin,
        )
"""
if old in src:
    p.write_text(src.replace(old, new, 1), encoding="utf-8")
    print("removed refuse_payload import")
else:
    print("import already clean or pattern mismatch")
