# Deploy Ask Q&A admin API files to VPS and restart PM2.
# Usage (from repo root):
#   .\scripts\deploy-ask-admin-vps.ps1
#
# One-time (no more passwords): .\scripts\setup-vps-ssh-key.ps1
# Optional: $env:VPS_HOST = "root@187.127.174.55"

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$api = Join-Path $root "artifacts\api-server"
$vpsHost = if ($env:VPS_HOST) { $env:VPS_HOST } else { "root@187.127.174.55" }
$remote = "/root/Cosmic-Lens-Backend/artifacts/api-server"

$files = @(
    "flask_app.py",
    "shortcuts.py",
    "ask_scope_gate.py",
    "ask_scope_llm.py",
    "ask_question_normalize.py",
    "ask_native_overview.py",
    "ask_intent_fidelity.py",
    "chart_fact_answer.py",
    "ask_kundli_resolver.py",
    "admin_dashboard.py",
    "question_history.py",
    "ask_token_telemetry.py",
    "subscription_helper.py",
    "models.py",
    "database.py",
    "openai_helper.py",
    "ask_llm_context_debug.py",
    "ask_hard_guards.py",
    "ask_timing_clarify.py",
    "ask_timing_followup.py",
    "health_focus_routing.py",
    "ask_user_signals.py",
    "user_ask_profile.py",
    "event_timing/timing_router.py"
)

$folders = @(
    "ask_mr",
    "ask_health",
    "event_timing/marriage",
    "event_timing/_shared",
    "event_timing/career"
)

foreach ($f in $files) {
    $local = Join-Path $api $f
    if (-not (Test-Path $local)) {
        throw "Missing local file: $local"
    }
}
foreach ($dir in $folders) {
    if (-not (Test-Path (Join-Path $api $dir))) {
        throw "Missing local folder: $(Join-Path $api $dir)"
    }
}

Write-Host "Deploying Ask Q&A admin API to $vpsHost (single upload bundle) ..." -ForegroundColor Cyan

$staging = Join-Path $env:TEMP "cosmic-ask-deploy-$([Guid]::NewGuid().ToString('n').Substring(0, 8))"
$archive = Join-Path $env:TEMP "cosmic-ask-deploy.tar.gz"
New-Item -ItemType Directory -Path $staging -Force | Out-Null

try {
    foreach ($f in $files) {
        Copy-Item (Join-Path $api $f) -Destination (Join-Path $staging $f) -Force
    }
    foreach ($dir in $folders) {
        $dest = Join-Path $staging $dir
        if (Test-Path $dest) { Remove-Item $dest -Recurse -Force }
        Copy-Item (Join-Path $api $dir) -Destination $dest -Recurse -Force
    }

    if (Test-Path $archive) { Remove-Item $archive -Force }
    Push-Location $staging
    try {
        & tar -czf $archive *
        if ($LASTEXITCODE -ne 0) { throw "tar failed (exit $LASTEXITCODE)" }
    } finally {
        Pop-Location
    }

    $sizeKb = [math]::Round((Get-Item $archive).Length / 1KB, 1)
    Write-Host "  Uploading $sizeKb KB archive (1 connection) ..." -ForegroundColor Cyan
    scp $archive "${vpsHost}:/tmp/cosmic-ask-deploy.tar.gz"

    Write-Host "  Extract + restart on VPS (1 connection) ..." -ForegroundColor Cyan
    ssh $vpsHost @"
set -e
cd $remote
tar xzf /tmp/cosmic-ask-deploy.tar.gz
rm -f /tmp/cosmic-ask-deploy.tar.gz
echo '--- py_compile (abort restart on syntax error) ---'
python3 -m py_compile openai_helper.py ask_hard_guards.py ask_timing_clarify.py ask_llm_context_debug.py health_focus_routing.py chart_fact_answer.py flask_app.py subscription_helper.py ask_user_signals.py user_ask_profile.py event_timing/timing_router.py event_timing/_shared/step_audit.py event_timing/_shared/generic_timing_engine.py || { echo 'COMPILE_FAILED — fix syntax before restart'; exit 1; }
python3 -c "from ask_timing_clarify import needs_timing_domain_clarifier; assert needs_timing_domain_clarifier('Mera life me struggle kab jaayega'); print('ask_timing_clarify OK')" || { echo 'MISSING ask_timing_clarify.py — git pull or redeploy'; exit 1; }
python3 -c "from subscription_helper import finalize_ask_out_after_llm; print('finalize_ask_out_after_llm OK')" || { echo 'MISSING finalize_ask_out_after_llm — deploy subscription_helper.py'; exit 1; }
python3 -c "from ask_mr import run_mr_static_engine; print('ask_mr engine OK')" || { echo 'MISSING ask_mr/ — deploy ask_mr folder or git pull'; exit 1; }
grep -c 'ask-questions' flask_app.py || true
pm2 restart cosmic-api --update-env 2>/dev/null || pm2 restart cosmiclens-api --update-env 2>/dev/null || pm2 restart all --update-env
sleep 3
curl -s -o /dev/null -w 'health HTTP %{http_code}\n' http://127.0.0.1:8080/api/health || true
echo '--- smoke ask (Mars strength) ---'
curl -s -m 25 -X POST http://127.0.0.1:8080/api/ask/stream \
  -H 'Content-Type: application/json' \
  -d '{\"question\":\"Mars strong hai ya weak?\",\"lang\":\"hi\",\"kundli\":{\"planets\":[{\"name\":\"Mars\",\"longitude\":10,\"house\":1,\"sign\":\"Aries\"}],\"ascendant\":\"Aries\",\"moonSign\":\"Taurus\"}}' \
  | head -c 400 || true
echo ''
"@
} finally {
    if (Test-Path $staging) { Remove-Item $staging -Recurse -Force -ErrorAction SilentlyContinue }
    if (Test-Path $archive) { Remove-Item $archive -Force -ErrorAction SilentlyContinue }
}

Write-Host ""
Write-Host "Done. Refresh admin panel -> Ask Q&A tab." -ForegroundColor Green
Write-Host "Tip: run .\scripts\setup-vps-ssh-key.ps1 once - then deploy never asks password." -ForegroundColor DarkGray
