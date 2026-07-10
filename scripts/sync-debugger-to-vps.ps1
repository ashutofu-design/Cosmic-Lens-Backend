# Copy admin + API files to VPS WITHOUT git commit/push.
# Run on laptop PowerShell:
#   .\scripts\sync-debugger-to-vps.ps1
#
# Needs SSH to VPS. If SSH times out, use Hostinger File Manager (see below).

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$vps = if ($env:VPS_HOST) { $env:VPS_HOST } else { "root@187.127.174.55" }
$remote = "/root/Cosmic-Lens-Backend"

$files = @(
    "artifacts\api-server\ask_observability_debug.py",
    "artifacts\api-server\ask_mr\v2\adapter.py",
    "artifacts\api-server\ask_mr\engine_narrate.py",
    "artifacts\api-server\question_history.py",
    "artifacts\api-server\tests\test_ask_observability_debug.py",
    "artifacts\admin-web\src\AskObservabilityDebugger.tsx",
    "artifacts\admin-web\src\askObservability.ts",
    "artifacts\admin-web\src\AskQuestionDetailPage.tsx",
    "artifacts\admin-web\src\AskLlmContextPanel.tsx",
    "artifacts\admin-web\src\App.tsx",
    "artifacts\admin-web\src\index.css",
    "artifacts\admin-web\index.html"
)

Write-Host "Uploading debugger + mobile admin files to VPS..." -ForegroundColor Cyan
foreach ($f in $files) {
    $local = Join-Path $root $f
    if (-not (Test-Path $local)) {
        Write-Host "SKIP (missing): $f" -ForegroundColor Yellow
        continue
    }
    $remotePath = "$remote/$($f -replace '\\','/')"
    $remoteDir = Split-Path $remotePath -Parent
    ssh $vps "mkdir -p `"$remoteDir`""
    scp $local "${vps}:${remotePath}"
    Write-Host "  OK $f" -ForegroundColor Green
}

Write-Host ""
Write-Host "Files uploaded. Now run on VPS Browser Terminal:" -ForegroundColor Green
Write-Host @'

pm2 restart cosmic-api --update-env

cd /root/Cosmic-Lens-Backend/artifacts/admin-web
ADMIN_SECRET=$(grep '^ADMIN_SECRET=' ../api-server/.env | cut -d= -f2-)
export VITE_API_BASE=""
export VITE_ADMIN_SECRET="$ADMIN_SECRET"
pnpm run build
rm -rf /var/www/cosmic-admin/*
cp -a dist/. /var/www/cosmic-admin/
chown -R www-data:www-data /var/www/cosmic-admin

'@

Write-Host "Then Cloudflare -> Purge Everything -> hard refresh phone/laptop." -ForegroundColor Cyan
