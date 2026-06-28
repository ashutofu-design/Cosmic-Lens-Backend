#!/usr/bin/env python3
"""Run MR full audit + unit smoke tests."""
from __future__ import annotations

import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
env = os.environ.copy()
env["PYTHONUTF8"] = "1"
env["PYTHONIOENCODING"] = "utf-8"

audit = subprocess.run(
    [sys.executable, os.path.join("scripts", "audit_mr_full.py")],
    capture_output=True,
    text=True,
    encoding="utf-8",
    env=env,
)
print(audit.stdout)
if audit.stderr:
    print(audit.stderr, file=sys.stderr)

with open("audit_mr_latest.log", "w", encoding="utf-8") as fh:
    fh.write(audit.stdout)
    if audit.stderr:
        fh.write("\n--- stderr ---\n")
        fh.write(audit.stderr)

tests = subprocess.run(
    [sys.executable, "-m", "pytest", "tests/test_ask_mr_engine_phase1.py", "-q"],
    capture_output=True,
    text=True,
    encoding="utf-8",
    env=env,
)
print("\n--- PYTEST ---\n")
print(tests.stdout or tests.stderr)

raise SystemExit(audit.returncode or tests.returncode)
