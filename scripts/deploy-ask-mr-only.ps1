# Copy ask_mr folder to VPS (MR static engine). Run from repo root in PowerShell:
#   .\scripts\deploy-ask-mr-only.ps1
#
# Requires: OpenSSH scp (Windows 10+), SSH access to VPS.

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$local = Join-Path $root "artifacts\api-server\ask_mr"
$vpsHost = if ($env:VPS_HOST) { $env:VPS_HOST } else { "root@187.127.174.55" }
$remote = "/root/Cosmic-Lens-Backend/artifacts/api-server"

if (-not (Test-Path $local)) {
    throw "Missing folder: $local"
}

Write-Host "Uploading ask_mr to $vpsHost ..." -ForegroundColor Cyan
scp -r $local "${vpsHost}:${remote}/"

Write-Host "Verifying on VPS ..." -ForegroundColor Cyan
ssh $vpsHost @"
cd $remote
ls -la ask_mr | head -5
python3 -c "from ask_mr import run_mr_static_engine; print('ask_mr OK')"
pm2 restart cosmic-api --update-env
"@

Write-Host "Done. Test Ask question in app; admin should show mr_engine_v1." -ForegroundColor Green
