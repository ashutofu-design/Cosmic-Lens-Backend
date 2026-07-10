# Run one Ask question on VPS and print admin audit JSON.
# Usage (repo root):
#   .\scripts\ask-audit-question.ps1 "mera baby kab hoga"
#   .\scripts\ask-audit-question.ps1 "car konsa colour best hoga buy karne me"

param(
    [Parameter(Mandatory = $true, Position = 0)]
    [string]$Question,
    [string]$Lang = "hi",
    [string]$ApiBase = ""
)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
if ($ApiBase) { $env:ASK_AUDIT_API_BASE = $ApiBase }

$py = "python"
if (-not (Get-Command $py -ErrorAction SilentlyContinue)) {
    $py = "python3"
}

& $py (Join-Path $root "scripts\ask_audit_question.py") $Question --lang $Lang
exit $LASTEXITCODE
