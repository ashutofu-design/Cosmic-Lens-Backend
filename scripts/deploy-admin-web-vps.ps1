# Build admin-web locally and upload dist/ to VPS.
# Usage (from repo root):
#   .\scripts\deploy-admin-web-vps.ps1
# Optional: $env:VPS_HOST = "root@187.127.174.55"
# Optional: $env:ADMIN_WEB_REMOTE = "/root/Cosmic-Lens-Backend/artifacts/admin-web/dist"

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$admin = Join-Path $root "artifacts\admin-web"
$vpsHost = if ($env:VPS_HOST) { $env:VPS_HOST } else { "root@187.127.174.55" }
$remote = if ($env:ADMIN_WEB_REMOTE) {
    $env:ADMIN_WEB_REMOTE
} else {
    "/root/Cosmic-Lens-Backend/artifacts/admin-web/dist"
}

Write-Host "Building admin-web ..." -ForegroundColor Cyan

$envFile = Join-Path $admin ".env"
if (-not (Test-Path $envFile)) {
    Write-Host "ERROR: artifacts/admin-web/.env missing." -ForegroundColor Red
    Write-Host "  copy artifacts\admin-web\.env.example artifacts\admin-web\.env"
    Write-Host "  Set VITE_ADMIN_SECRET = same as VPS ADMIN_SECRET"
    Write-Host "  Set VITE_API_BASE = http://YOUR_VPS_IP:8080  (required for static dist)"
    exit 1
}

$envText = Get-Content $envFile -Raw
if ($envText -notmatch 'VITE_ADMIN_SECRET\s*=\s*\S+' -or $envText -match 'VITE_ADMIN_SECRET\s*=\s*your-admin-secret') {
    Write-Host "ERROR: Set a real VITE_ADMIN_SECRET in artifacts/admin-web/.env" -ForegroundColor Red
    exit 1
}
if ($envText -notmatch 'VITE_API_BASE\s*=\s*https?://') {
    Write-Host "WARN: VITE_API_BASE not set in .env — static build may not reach API." -ForegroundColor Yellow
    Write-Host "  Add: VITE_API_BASE=http://187.127.174.55:8080" -ForegroundColor Yellow
}

Push-Location $admin
try {
    if (Get-Command pnpm -ErrorAction SilentlyContinue) {
        pnpm run build
    } else {
        npm run build
    }
} finally {
    Pop-Location
}

$dist = Join-Path $admin "dist"
if (-not (Test-Path (Join-Path $dist "index.html"))) {
    throw "Build failed — dist/index.html missing"
}

Write-Host "Uploading dist/ to ${vpsHost}:${remote} ..." -ForegroundColor Cyan
ssh $vpsHost "mkdir -p $remote"
scp -r "$dist\*" "${vpsHost}:${remote}/"

Write-Host ""
Write-Host "Done. Hard refresh admin panel (Ctrl+F5) -> Ask Q&A tab." -ForegroundColor Green
Write-Host "Copy button appears on its own line below each question." -ForegroundColor Green
