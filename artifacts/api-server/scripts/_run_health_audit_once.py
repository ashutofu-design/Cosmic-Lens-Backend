#!/usr/bin/env python3
"""One-shot runner for health audit + unit tests (avoids shell encoding issues)."""
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
    [sys.executable, os.path.join("scripts", "audit_health_full.py")],
    capture_output=True,
    text=True,
    encoding="utf-8",
    env=env,
)
print(audit.stdout)
if audit.stderr:
    print(audit.stderr, file=sys.stderr)

with open("audit_health_latest.log", "w", encoding="utf-8") as fh:
    fh.write(audit.stdout)
    if audit.stderr:
        fh.write("\n--- stderr ---\n")
        fh.write(audit.stderr)

tests = subprocess.run(
    [sys.executable, os.path.join("tests", "test_ask_health_engine.py")],
    capture_output=True,
    text=True,
    encoding="utf-8",
    env=env,
)
print("\n--- PYTEST ---\n")
print(tests.stdout)
if tests.stderr:
    print(tests.stderr, file=sys.stderr)

raise SystemExit(audit.returncode or tests.returncode)
