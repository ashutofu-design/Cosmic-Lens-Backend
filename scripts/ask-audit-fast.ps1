# FAST ASK AUDIT — local routing + MR engine evidence only (~5 sec, no LLM/API).
# Usage (repo root):
#   .\scripts\ask-audit-fast.ps1

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$py = if (Get-Command python -ErrorAction SilentlyContinue) { "python" } else { "python3" }

Set-Location $root
& $py (Join-Path $root "scripts\ask_audit_fast.py")
exit $LASTEXITCODE
