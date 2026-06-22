# Build admin-web locally and upload dist/ to VPS.
# Usage (from repo root):
#   .\scripts\deploy-admin-web-vps.ps1
# Optional: $env:VPS_HOST = "root@187.127.174.55"
# Optional: $env:ADMIN_WEB_REMOTE = "/root/Cosmic-Lens-Backend/artifacts/admin-web/dist"

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$admin = Join-Path $root "artifacts\admin-web"
$host = if ($env:VPS_HOST) { $env:VPS_HOST } else { "root@187.127.174.55" }
$remote = if ($env:ADMIN_WEB_REMOTE) {
    $env:ADMIN_WEB_REMOTE
} else {
    "/root/Cosmic-Lens-Backend/artifacts/admin-web/dist"
}

Write-Host "Building admin-web ..." -ForegroundColor Cyan
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

Write-Host "Uploading dist/ to ${host}:${remote} ..." -ForegroundColor Cyan
ssh $host "mkdir -p $remote"
scp -r "$dist\*" "${host}:${remote}/"

Write-Host ""
Write-Host "Done. Hard refresh admin panel (Ctrl+F5) -> Ask Q&A tab." -ForegroundColor Green
Write-Host "Copy button appears on its own line below each question." -ForegroundColor Green
