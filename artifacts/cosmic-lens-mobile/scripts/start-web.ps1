# Simple Windows web start for Cosmic Lens
$ErrorActionPreference = "Continue"
$App = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $App

Write-Host "=== Cosmic Lens web ===" -ForegroundColor Cyan
Write-Host "folder: $App"

# Temp on D: (C: full breaks Metro)
New-Item -ItemType Directory -Path "D:\Temp" -Force | Out-Null
$env:TEMP = "D:\Temp"
$env:TMP = "D:\Temp"

# Kill anything on Metro port
foreach ($port in @(18987, 8081, 19000, 19006)) {
  try {
    $lines = netstat -ano | Select-String ":$port\s+.*LISTENING"
    foreach ($line in $lines) {
      $parts = ($line.ToString() -split "\s+") | Where-Object { $_ -ne "" }
      $ownPid = $parts[-1]
      if ($ownPid -match "^\d+$" -and [int]$ownPid -gt 0) {
        Write-Host "killing pid $ownPid on port $port"
        Stop-Process -Id ([int]$ownPid) -Force -ErrorAction SilentlyContinue
      }
    }
  } catch {}
}
Start-Sleep -Seconds 1

if (-not (Test-Path ".\node_modules\expo\bin\cli")) {
  Write-Host "expo missing - run from repo root: pnpm install" -ForegroundColor Red
  exit 1
}

Write-Host ""
Write-Host "Starting Metro web..." -ForegroundColor Yellow
Write-Host "Chrome khulega ~12 sec baad: http://localhost:18987" -ForegroundColor Yellow
Write-Host "Is window mein Bundling % dikhega - 1-3 min wait karo" -ForegroundColor Yellow
Write-Host "Band karne ke liye Ctrl+C" -ForegroundColor DarkGray
Write-Host ""

node .\scripts\dev-local.mjs --web
