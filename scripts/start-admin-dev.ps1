# Local admin UI (pnpm dev) + VPS production API on port 80.
# Usage: .\scripts\start-admin-dev.ps1
#
# No SSH needed. UI: http://127.0.0.1:5174

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$adminDir = Join-Path $root "artifacts\admin-web"
$apiBase = if ($env:VITE_API_PROXY_TARGET) { $env:VITE_API_PROXY_TARGET } else { "http://187.127.174.55" }
$healthUrl = "$apiBase/api/healthz"

Write-Host "=== Admin dev (local UI + VPS data) ===" -ForegroundColor Cyan
Write-Host "UI:   http://127.0.0.1:5174" -ForegroundColor Gray
Write-Host "API:  $apiBase" -ForegroundColor Gray
Write-Host ""

try {
    $r = Invoke-WebRequest -Uri $healthUrl -UseBasicParsing -TimeoutSec 12
    if ($r.StatusCode -ge 200 -and $r.StatusCode -lt 500) {
        Write-Host "VPS API reachable." -ForegroundColor Green
    }
} catch {
    Write-Host "WARN: Cannot reach $healthUrl from this PC ($($_.Exception.Message))" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Your home network blocks the VPS IP. Use a Cloudflare tunnel:" -ForegroundColor Cyan
    Write-Host "  1) VPS Browser Terminal: bash /root/Cosmic-Lens-Backend/scripts/vps-expose-api-tunnel.sh"
    Write-Host "  2) Copy https://....trycloudflare.com URL"
    Write-Host "  3) Set VITE_API_PROXY_TARGET= that URL in artifacts\admin-web\.env"
    Write-Host "  4) Run this script again OR pnpm dev"
    Write-Host ""
    Write-Host "OR try mobile hotspot. OR Hostinger hPanel -> VPS -> Firewall -> Allow TCP 80."
    if (-not $env:SKIP_VPS_REACHABILITY_CHECK) {
        exit 1
    }
}

Write-Host "Clearing stale shell env vars (if any) ..." -ForegroundColor Gray
Remove-Item Env:VITE_API_PROXY_TARGET -ErrorAction SilentlyContinue
Remove-Item Env:VITE_ADMIN_SECRET -ErrorAction SilentlyContinue

$envFile = Join-Path $adminDir ".env"
$secret = (Get-Content $envFile -ErrorAction SilentlyContinue | Where-Object { $_ -match '^\s*VITE_ADMIN_SECRET\s*=\s*\S+' } | Select-Object -First 1)
if (-not $secret -or $secret -match 'VITE_ADMIN_SECRET\s*=\s*$') {
    Write-Host ""
    Write-Host "Set VITE_ADMIN_SECRET in artifacts\admin-web\.env" -ForegroundColor Yellow
    Write-Host "Same value as VPS: grep ADMIN_SECRET /root/Cosmic-Lens-Backend/artifacts/api-server/.env"
    exit 1
}

$env:VITE_API_PROXY_TARGET = $apiBase
$secretLine = Get-Content $envFile -ErrorAction SilentlyContinue | Where-Object { $_ -match '^\s*VITE_ADMIN_SECRET\s*=\s*\S+' } | Select-Object -First 1
if ($secretLine -match '=\s*(.+)$') {
    $env:VITE_ADMIN_SECRET = $matches[1].Trim()
}
Push-Location $adminDir
try {
    Write-Host "Starting pnpm dev ..." -ForegroundColor Cyan
    if (Get-Command pnpm -ErrorAction SilentlyContinue) {
        pnpm dev
    } else {
        npm run dev
    }
} finally {
    Pop-Location
}
