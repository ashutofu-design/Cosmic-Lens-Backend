# Deploy Ask Q&A admin API files to VPS and restart PM2.
# Usage (from repo root):
#   .\scripts\deploy-ask-admin-vps.ps1
# Optional: $env:VPS_HOST = "root@187.127.174.55"

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$api = Join-Path $root "artifacts\api-server"
$host = if ($env:VPS_HOST) { $env:VPS_HOST } else { "root@187.127.174.55" }
$remote = "/root/Cosmic-Lens-Backend/artifacts/api-server"

$files = @(
    "flask_app.py",
    "shortcuts.py",
    "ask_scope_gate.py",
    "chart_fact_answer.py",
    "ask_kundli_resolver.py",
    "admin_dashboard.py",
    "question_history.py",
    "ask_token_telemetry.py",
    "subscription_helper.py",
    "models.py",
    "database.py",
    "openai_helper.py",
    "ask_llm_context_debug.py"
)

$folders = @(
    "ask_mr"
)

Write-Host "Deploying Ask Q&A admin API to $host ..." -ForegroundColor Cyan
foreach ($f in $files) {
    $local = Join-Path $api $f
    if (-not (Test-Path $local)) {
        throw "Missing local file: $local"
    }
    Write-Host "  scp $f"
    scp $local "${host}:${remote}/$f"
}

foreach ($dir in $folders) {
    $localDir = Join-Path $api $dir
    if (-not (Test-Path $localDir)) {
        throw "Missing local folder: $localDir"
    }
    Write-Host "  scp -r $dir/"
    scp -r $localDir "${host}:${remote}/$dir"
}

Write-Host "Restarting API ..." -ForegroundColor Cyan
ssh $host @"
cd $remote
echo '--- py_compile (abort restart on syntax error) ---'
python3 -m py_compile openai_helper.py chart_fact_answer.py flask_app.py subscription_helper.py || { echo 'COMPILE_FAILED — fix syntax before restart'; exit 1; }
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

Write-Host ""
Write-Host "Done. Refresh admin panel -> Ask Q&A tab." -ForegroundColor Green
Write-Host "If still 404, run on VPS: grep ask-questions $remote/flask_app.py"
