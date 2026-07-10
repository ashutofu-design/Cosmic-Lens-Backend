"""Remove orphaned mega-prompt text between system_prompt assignment and model =."""
from pathlib import Path

p = Path(__file__).resolve().parents[1] / "artifacts" / "api-server" / "openai_helper.py"
lines = p.read_text(encoding="utf-8").splitlines(keepends=True)

start = None
for i, ln in enumerate(lines):
    if ln.startswith("    system_prompt = _build_universal_ask_system_prompt("):
        start = i
        break
if start is None:
    raise SystemExit("system_prompt assignment not found")

# Find closing `    )` of the function call (paren depth on continuation lines).
depth = 0
close_i = None
for i in range(start, min(start + 20, len(lines))):
    ln = lines[i]
    depth += ln.count("(") - ln.count(")")
    if depth == 0 and i > start and ln.rstrip() == ")":
        close_i = i
        break
if close_i is None:
    raise SystemExit("closing paren not found")

model_i = None
for i in range(close_i + 1, len(lines)):
    if lines[i].startswith('    model = os.environ.get("RAW_PASSTHROUGH_MODEL"'):
        if i + 1 < len(lines) and "OPENAI_MODEL" in lines[i + 1]:
            model_i = i
            break
if model_i is None:
    raise SystemExit("model = line not found")

removed = model_i - close_i - 1
new_lines = lines[: close_i + 1] + ["\n"] + lines[model_i:]
p.write_text("".join(new_lines), encoding="utf-8")
print(f"Removed {removed} lines between system_prompt and model =")

import py_compile

py_compile.compile(str(p), doraise=True)
print("COMPILE_OK")
