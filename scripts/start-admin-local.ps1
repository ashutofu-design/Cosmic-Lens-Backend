# Start local API + admin panel (no VPS / DNS / firewall needed).
# Usage (repo root):
#   .\scripts\start-admin-local.ps1

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$apiDir = Join-Path $root "artifacts\api-server"
$adminDir = Join-Path $root "artifacts\admin-web"
$apiUrl = "http://127.0.0.1:8080"
$healthUrl = "$apiUrl/api/healthz"

function Test-ApiUp {
    try {
        $r = Invoke-WebRequest -Uri $healthUrl -UseBasicParsing -TimeoutSec 3
        return $r.StatusCode -ge 200 -and $r.StatusCode -lt 500
    } catch {
        return $false
    }
}

Write-Host "=== Cosmic Lens local admin ===" -ForegroundColor Cyan
Write-Host "API:   $apiUrl" -ForegroundColor Gray
Write-Host "Admin: http://127.0.0.1:5174" -ForegroundColor Gray
Write-Host ""

if (-not (Test-ApiUp)) {
    Write-Host "Starting local API on :8080 ..." -ForegroundColor Yellow
    $apiCmd = @"
Set-Location '$apiDir'
`$env:PORT = '8080'
`$env:ADMIN_NO_AUTH = '1'
`$env:FLASK_ENV = 'development'
python flask_app.py
"@
    Start-Process powershell -ArgumentList "-NoExit", "-Command", $apiCmd | Out-Null

    $deadline = (Get-Date).AddSeconds(45)
    while ((Get-Date) -lt $deadline) {
        Start-Sleep -Seconds 2
        if (Test-ApiUp) {
            Write-Host "Local API is up." -ForegroundColor Green
            break
        }
    }
    if (-not (Test-ApiUp)) {
        Write-Host "ERROR: API did not start on $apiUrl" -ForegroundColor Red
        Write-Host "Check the API PowerShell window for errors (missing python packages, etc.)."
        exit 1
    }
} else {
    Write-Host "Local API already running." -ForegroundColor Green
}

$env:VITE_API_PROXY_TARGET = $apiUrl
$env:VITE_ADMIN_SECRET = "local-dev"
Push-Location $adminDir
try {
    Write-Host "Starting admin-web (Ctrl+C to stop) ..." -ForegroundColor Cyan
    if (Get-Command pnpm -ErrorAction SilentlyContinue) {
        pnpm dev
    } else {
        npm run dev
    }
} finally {
    Pop-Location
}
