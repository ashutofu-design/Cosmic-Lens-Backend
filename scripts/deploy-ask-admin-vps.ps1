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
    "ask_question_understand.py",
    "ask_route_from_understanding.py",
    "ask_master_router.py",
    "ask_routing_policy.py",
    "ask_intent_llm.py",
    "ask_engine.py",
    "ask_engine_resolver.py",
    "engine_collision_registry.py",
    "ask_universal_chart_llm.py",
    "ask_native_overview.py",
    "ask_intent_fidelity.py",
    "ask_answer_fidelity.py",
    "ask_marriage_relationship_slice.py",
    "dcr_love.py",
    "chart_fact_answer.py",
    "ask_batch_runner.py",
    "ask_question_dna.py",
    "relationship_dna_taxonomy.py",
    "ask_dna_runner.py",
    "ask_kundli_resolver.py",
    "admin_dashboard.py",
    "question_history.py",
    "ask_token_telemetry.py",
    "subscription_helper.py",
    "models.py",
    "database.py",
    "openai_helper.py",
    "ask_cosmo_narrator.py",
    "ask_llm_context_debug.py",
    "ask_hard_guards.py",
    "ask_gap_dispatch.py",
    "ask_gaps_shared.py",
    "ask_timing_clarify.py",
    "ask_timing_followup.py",
    "ask_general_followup.py",
    "health_focus_routing.py",
    "ask_user_signals.py",
    "user_ask_profile.py"
)

$folders = @(
    "ask_mr",
    "ask_luck",
    "ask_network",
    "ask_siblings",
    "ask_parents",
    "ask_enemies",
    "ask_personality",
    "ask_dreams",
    "ask_anger",
    "ask_remedy",
    "ask_settlement",
    "ask_pets",
    "ask_vastu",
    "ask_charity",
    "ask_wellness",
    "ask_spiritual",
    "ask_fame",
    "ask_health",
    "ask_children",
    "ask_property",
    "ask_vehicle",
    "ask_numerology",
    "property_static",
    "vehicle_static",
    "event_timing"
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
        $dest = Join-Path $staging $f
        $destDir = Split-Path $dest -Parent
        if ($destDir -and -not (Test-Path $destDir)) {
            New-Item -ItemType Directory -Path $destDir -Force | Out-Null
        }
        Copy-Item (Join-Path $api $f) -Destination $dest -Force
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
    $remoteScript = @'
set -e
cd __REMOTE__
tar xzf /tmp/cosmic-ask-deploy.tar.gz
rm -f /tmp/cosmic-ask-deploy.tar.gz
echo '--- py_compile (abort restart on syntax error) ---'
python3 -m py_compile openai_helper.py ask_cosmo_narrator.py ask_engine.py ask_hard_guards.py ask_timing_clarify.py ask_general_followup.py ask_llm_context_debug.py health_focus_routing.py chart_fact_answer.py flask_app.py ask_batch_runner.py subscription_helper.py ask_user_signals.py user_ask_profile.py ask_scope_gate.py ask_question_normalize.py question_history.py event_timing/timing_router.py event_timing/formatters.py event_timing/domain_specs.py event_timing/baby/baby_engine_v1.py event_timing/property/property_timing_v1.py event_timing/property/bcp_property_ages.py event_timing/property/property_practicality.py || { echo 'COMPILE_FAILED — fix syntax before restart'; exit 1; }
python3 <<'PY' || { echo 'TIMING_IMPORT_FAILED — event_timing bundle incomplete'; exit 1; }
from event_timing.timing_router import run_timing_engine, resolve_timing_domain
from event_timing.formatters import format_baby_timing_for_prompt
from event_timing.baby.baby_engine_v1 import compute_baby_window
from event_timing.property.bcp_property_ages import compute_bcp_property_ages
from ask_children.timing_registry import is_children_timing_question
from ask_property.timing_registry import is_property_timing_question
from ask_vehicle.vehicle_registry import is_vehicle_static_question
assert is_children_timing_question("mera baby kab hoga")
assert not is_property_timing_question("car konsa colour best hoga buy karne me")
assert is_vehicle_static_question("car konsa colour best hoga buy karne me")
print("timing_routing_imports OK")
PY
python3 <<'PY' || { echo 'MISSING ask_general_followup.py — redeploy'; exit 1; }
from ask_general_followup import is_generic_followup
assert is_generic_followup("Tell me more")
print("ask_general_followup OK")
PY
python3 <<'PY' || { echo 'MISSING ask_timing_clarify.py — git pull or redeploy'; exit 1; }
from ask_timing_clarify import needs_timing_domain_clarifier
assert needs_timing_domain_clarifier("Mera life me struggle kab jaayega")
print("ask_timing_clarify OK")
PY
python3 <<'PY' || { echo 'MISSING finalize_ask_out_after_llm — deploy subscription_helper.py'; exit 1; }
from subscription_helper import finalize_ask_out_after_llm
print("finalize_ask_out_after_llm OK")
PY
python3 <<'PY' || { echo 'MISSING ask_mr/ — deploy ask_mr folder or git pull'; exit 1; }
from ask_mr import run_mr_static_engine
print("ask_mr engine OK")
PY
python3 <<'PY' || { echo 'MISSING ask_luck/ — deploy ask_luck folder or git pull'; exit 1; }
from ask_luck import run_luck_static_engine
print("ask_luck engine OK")
PY
python3 <<'PY' || { echo 'MISSING ask_network/ — deploy ask_network folder or git pull'; exit 1; }
from ask_network import run_network_static_engine
print("ask_network engine OK")
PY
python3 <<'PY' || { echo 'MISSING ask_gap_dispatch.py — deploy gap engines'; exit 1; }
from ask_gap_dispatch import run_gap_static_engine
print("ask_gap_dispatch OK")
PY
grep -c 'ask-questions' flask_app.py || true
pm2 restart cosmic-api --update-env 2>/dev/null || pm2 restart cosmiclens-api --update-env 2>/dev/null || pm2 restart all --update-env
sleep 3
curl -s -o /dev/null -w 'health HTTP %{http_code}\n' http://127.0.0.1:8080/api/health || true
echo '--- smoke ask (Mars strength) ---'
curl -s -m 25 -X POST http://127.0.0.1:8080/api/ask/stream \
  -H 'Content-Type: application/json' \
  -d '{"question":"Mars strong hai ya weak?","lang":"hi","kundli":{"planets":[{"name":"Mars","longitude":10,"house":1,"sign":"Aries"}],"ascendant":"Aries","moonSign":"Taurus"}}' \
  | head -c 400 || true
echo ''
'@.Replace('__REMOTE__', $remote)
    $remoteScript | ssh $vpsHost "bash -s"
} finally {
    if (Test-Path $staging) { Remove-Item $staging -Recurse -Force -ErrorAction SilentlyContinue }
    if (Test-Path $archive) { Remove-Item $archive -Force -ErrorAction SilentlyContinue }
}

Write-Host ""
Write-Host "Done. Refresh admin panel -> Ask Q&A tab." -ForegroundColor Green
Write-Host "Tip: run .\scripts\setup-vps-ssh-key.ps1 once - then deploy never asks password." -ForegroundColor DarkGray
