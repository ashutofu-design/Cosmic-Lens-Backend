# Batch ASK AUDIT — 5 relationship questions (or edit ask_audit_batch.py).
# Usage (repo root):
#   .\scripts\ask-audit-batch.ps1

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)

$py = "python"
if (-not (Get-Command $py -ErrorAction SilentlyContinue)) {
    $py = "python3"
}

Set-Location $root
& $py (Join-Path $root "scripts\ask_audit_batch.py")
$code = $LASTEXITCODE

Write-Host ""
Write-Host "Results:" -ForegroundColor Cyan
Write-Host "  scripts\ask_audit_batch_results.json"
Write-Host "  scripts\ask_audit_batch_results.txt"

exit $code
