# Admin panel -> REAL VPS data (users, Ask Q&A history, etc.)
# Uses SSH tunnel because home WiFi cannot reach VPS :8080 / domain DNS.
#
# Usage (repo root):
#   .\scripts\start-admin-vps.ps1
#
# Prerequisite: SSH access to VPS (see scripts\setup-vps-ssh-key.ps1)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$adminDir = Join-Path $root "artifacts\admin-web"
$vpsHost = if ($env:VPS_HOST) { $env:VPS_HOST } else { "root@187.127.174.55" }
$localPort = if ($env:ADMIN_TUNNEL_PORT) { $env:ADMIN_TUNNEL_PORT } else { "18080" }
$apiUrl = "http://127.0.0.1:$localPort"
$healthUrl = "$apiUrl/api/healthz"
$remoteEnv = "/root/Cosmic-Lens-Backend/artifacts/api-server/.env"

function Test-TunnelUp {
    try {
        $r = Invoke-WebRequest -Uri $healthUrl -UseBasicParsing -TimeoutSec 4
        return $r.StatusCode -ge 200 -and $r.StatusCode -lt 500
    } catch {
        return $false
    }
}

function Get-VpsAdminSecret {
    $raw = ssh $vpsHost "grep '^ADMIN_SECRET=' $remoteEnv 2>/dev/null | head -1"
    if (-not $raw) {
        return ""
    }
    $parts = $raw -split "=", 2
    if ($parts.Count -lt 2) {
        return ""
    }
    return $parts[1].Trim().Trim('"').Trim("'")
}

Write-Host "=== Cosmic Lens admin (VPS production data) ===" -ForegroundColor Cyan
Write-Host "Tunnel: localhost:$localPort -> VPS:8080" -ForegroundColor Gray
Write-Host "Admin:  http://127.0.0.1:5174" -ForegroundColor Gray
Write-Host ""

$secret = Get-VpsAdminSecret
if (-not $secret) {
    Write-Host "ERROR: Could not read ADMIN_SECRET from VPS ($remoteEnv)." -ForegroundColor Red
    Write-Host ('SSH manually and check: ssh ' + $vpsHost + ' "grep ADMIN_SECRET ' + $remoteEnv + '"')
    exit 1
}
Write-Host "VPS ADMIN_SECRET loaded." -ForegroundColor Green

if (-not (Test-TunnelUp)) {
    Write-Host "Opening SSH tunnel (keep tunnel window open) ..." -ForegroundColor Yellow
    $tunnelCmd = "ssh -N -L ${localPort}:127.0.0.1:8080 $vpsHost"
    Start-Process powershell -ArgumentList "-NoExit", "-Command", $tunnelCmd | Out-Null

    $deadline = (Get-Date).AddSeconds(30)
    while ((Get-Date) -lt $deadline) {
        Start-Sleep -Seconds 2
        if (Test-TunnelUp) {
            Write-Host "SSH tunnel is up - connected to VPS API." -ForegroundColor Green
            break
        }
    }
    if (-not (Test-TunnelUp)) {
        Write-Host "ERROR: Tunnel failed. Check SSH key / VPS is online." -ForegroundColor Red
        Write-Host "Manual: ssh -N -L ${localPort}:127.0.0.1:8080 $vpsHost"
        exit 1
    }
} else {
    Write-Host "SSH tunnel already active." -ForegroundColor Green
}

$env:VITE_API_PROXY_TARGET = $apiUrl
$env:VITE_ADMIN_SECRET = $secret

Push-Location $adminDir
try {
    Write-Host "Starting admin-web against VPS data ..." -ForegroundColor Cyan
    if (Get-Command pnpm -ErrorAction SilentlyContinue) {
        pnpm dev
    } else {
        npm run dev
    }
} finally {
    Pop-Location
}
