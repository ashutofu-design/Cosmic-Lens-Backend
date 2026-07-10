# Deploy full Marriage M17 engine package to VPS (run from Windows PowerShell).
$ErrorActionPreference = "Stop"
$VPS = if ($env:COSMIC_VPS) { $env:COSMIC_VPS } else { "root@187.127.174.55" }
$ROOT = Split-Path -Parent $PSScriptRoot
$API = Join-Path $ROOT "artifacts\api-server"
$REMOTE = "/root/Cosmic-Lens-Backend/artifacts/api-server"

Write-Host "Deploying Marriage M17 to $VPS ..."

$files = @(
    "ask_kundli_resolver.py",
    "openai_helper.py",
    "ask_hard_guards.py",
    "question_history.py",
    "ask_llm_context_debug.py",
    "flask_app.py"
)
foreach ($f in $files) {
    scp (Join-Path $API $f) "${VPS}:${REMOTE}/"
}

$marriageLocal = Join-Path $API "event_timing\marriage"
$marriageRemote = "${REMOTE}/event_timing/marriage"
ssh $VPS "mkdir -p $marriageRemote"
Get-ChildItem $marriageLocal -Filter "*.py" | ForEach-Object {
    scp $_.FullName "${VPS}:${marriageRemote}/"
}

ssh $VPS "cd $REMOTE && python3 -c `"from event_timing.marriage.marriage_timing import compute_timing_window; from event_timing.marriage.marriage_step0 import run_marriage_step0; print('marriage_m17_import_ok')`" && pm2 restart cosmic-api"
Write-Host "Done. Ask a NEW question: mera shaadi kab hoga"
