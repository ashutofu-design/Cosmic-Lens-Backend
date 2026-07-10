# Permanent admin access setup (Windows laptop)
# Run in PowerShell (repo root):
#   .\scripts\windows-permanent-admin-setup.ps1

$ErrorActionPreference = "Continue"
$PublicIp = "187.127.174.55"
$ApiDomain = "api.cosmiclens.app"
$AdminEnv = Join-Path $PSScriptRoot "..\artifacts\admin-web\.env"

Write-Host "=== Permanent Admin Setup ===" -ForegroundColor Cyan
Write-Host ""

function Test-Port {
    param([string]$HostName, [int]$Port)
    try {
        $r = Test-NetConnection -ComputerName $HostName -Port $Port -WarningAction SilentlyContinue
        return $r.TcpTestSucceeded
    } catch {
        return $false
    }
}

Write-Host "Testing connectivity..." -ForegroundColor Yellow
$ip80 = Test-Port $PublicIp 80
$ip22 = Test-Port $PublicIp 22
$dnsOk = $false
try {
    $resolved = [System.Net.Dns]::GetHostAddresses($ApiDomain)
    $dnsOk = $resolved.Count -gt 0
    Write-Host "DNS $ApiDomain -> $($resolved[0].IPAddressToString)" -ForegroundColor Gray
} catch {
    Write-Host "DNS $ApiDomain -> FAILED (ENOTFOUND)" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "Port 80 ($PublicIp): $(if ($ip80) { 'OK' } else { 'BLOCKED' })" -ForegroundColor $(if ($ip80) { 'Green' } else { 'Red' })
Write-Host "Port 22 ($PublicIp): $(if ($ip22) { 'OK' } else { 'BLOCKED' })" -ForegroundColor $(if ($ip22) { 'Green' } else { 'Red' })
Write-Host "DNS $ApiDomain : $(if ($dnsOk) { 'OK' } else { 'FAIL' })" -ForegroundColor $(if ($dnsOk) { 'Green' } else { 'Yellow' })

if (-not $ip80) {
    Write-Host ""
    Write-Host "PERMANENT FIX REQUIRED — Hostinger Firewall:" -ForegroundColor Red
    Write-Host "  1. https://hpanel.hostinger.com -> VPS -> your server"
    Write-Host "  2. Security -> Firewall -> Add rule"
    Write-Host "  3. Inbound ACCEPT: TCP 22, TCP 80, TCP 443"
    Write-Host "  4. Save, wait 2 min, run this script again"
    Write-Host ""
    Write-Host "Also on VPS Browser Terminal run:"
    Write-Host "  cd /root/Cosmic-Lens-Backend && bash scripts/vps-permanent-access-fix.sh"
}

if (-not $dnsOk) {
    Write-Host ""
    Write-Host "DNS fix (Windows):" -ForegroundColor Yellow
    Write-Host "  Settings -> Network -> WiFi/Ethernet -> DNS -> Manual"
    Write-Host "  Preferred: 8.8.8.8   Alternate: 8.8.4.4"
    Write-Host ""
    Write-Host "Or hosts file (Run PowerShell as Administrator):"
    Write-Host "  Add-Content -Path C:\Windows\System32\drivers\etc\hosts -Value `"$PublicIp $ApiDomain`""
}

if ($ip80) {
    Write-Host ""
    Write-Host "SUCCESS — permanent admin URLs:" -ForegroundColor Green
    Write-Host "  Browser admin:  http://${PublicIp}/"
    Write-Host "  pnpm dev:       cd artifacts\admin-web; pnpm dev"
    Write-Host "                  -> http://127.0.0.1:5174"
    Write-Host ""
    try {
        $h = Invoke-WebRequest -Uri "http://${PublicIp}/api/healthz" -UseBasicParsing -TimeoutSec 10
        Write-Host "API health: $($h.Content)" -ForegroundColor Green
    } catch {
        Write-Host "API health check failed: $($_.Exception.Message)" -ForegroundColor Yellow
    }
}

Write-Host ""
Write-Host ".env location: $AdminEnv" -ForegroundColor Gray
Write-Host "Should contain: VITE_API_PROXY_TARGET=http://${PublicIp}" -ForegroundColor Gray
