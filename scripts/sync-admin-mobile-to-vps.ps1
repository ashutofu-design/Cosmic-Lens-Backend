# Copy mobile admin fixes to VPS (run on laptop PowerShell).
# Usage: .\scripts\sync-admin-mobile-to-vps.ps1
# Needs SSH to VPS working. If timeout, use git push + git pull on VPS instead.

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$vps = if ($env:VPS_HOST) { $env:VPS_HOST } else { "root@187.127.174.55" }
$remote = "/root/Cosmic-Lens-Backend/artifacts/admin-web"

$files = @(
    "src\App.tsx",
    "src\index.css",
    "index.html"
)

Write-Host "Uploading mobile layout files to VPS..." -ForegroundColor Cyan
foreach ($f in $files) {
    $local = Join-Path $root "artifacts\admin-web\$f"
    scp $local "${vps}:${remote}/$($f -replace '\\','/')"
}
Write-Host ""
Write-Host "Done. Now on VPS Browser Terminal run:" -ForegroundColor Green
Write-Host @"
cd /root/Cosmic-Lens-Backend/artifacts/admin-web
ADMIN_SECRET=`$(grep '^ADMIN_SECRET=' ../api-server/.env | cut -d= -f2-)
export VITE_API_BASE=""
export VITE_ADMIN_SECRET="`$ADMIN_SECRET"
pnpm run build
rm -rf /var/www/cosmic-admin/*
cp -a dist/. /var/www/cosmic-admin/
chown -R www-data:www-data /var/www/cosmic-admin
"@
