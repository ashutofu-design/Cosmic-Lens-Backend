# Build admin-web locally and upload ONLY dist/ to VPS (fast + safe).
# Usage (from repo root):
#   .\scripts\deploy-admin-web-vps.ps1
#
# Do NOT use `scp -r dist\*` on Windows OpenSSH - it can expand wrong and
# upload huge junk (Recovery/winre.wim, desktop.ini, etc.).

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
if (-not $root -or -not (Test-Path (Join-Path $root "artifacts\admin-web"))) {
    throw "Bad repo root: '$root' (expected ...\Cosmic-Lens-Backend)"
}
$admin = Join-Path $root "artifacts\admin-web"
$vpsHost = if ($env:VPS_HOST) { $env:VPS_HOST } else { "root@187.127.174.55" }
$remote = if ($env:ADMIN_WEB_REMOTE) {
    $env:ADMIN_WEB_REMOTE
} else {
    "/root/Cosmic-Lens-Backend/artifacts/admin-web/dist"
}
$nginxRoot = "/var/www/cosmic-admin"

Write-Host "Repo root: $root" -ForegroundColor DarkGray
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
    Write-Host "WARN: VITE_API_BASE not set in .env - static build may not reach API." -ForegroundColor Yellow
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
$indexHtml = Join-Path $dist "index.html"
if (-not (Test-Path $indexHtml)) {
    throw "Build failed - dist/index.html missing at $dist"
}

# Safety: refuse obvious wrong trees
$bad = Get-ChildItem -LiteralPath $dist -Recurse -File -ErrorAction SilentlyContinue |
    Where-Object { $_.Name -match '^(winre\.wim|boot\.sdi|csrss\.exe)$' -or $_.Length -gt 20MB }
if ($bad) {
    throw "Refusing upload - unexpected huge/system files inside dist: $($bad.FullName -join ', ')"
}

$files = @(Get-ChildItem -LiteralPath $dist -Recurse -File)
$totalBytes = ($files | Measure-Object -Property Length -Sum).Sum
Write-Host ("dist OK: {0} files, {1:N1} MB" -f $files.Count, ($totalBytes / 1MB)) -ForegroundColor Green

# One archive - fast, no Windows scp glob bug
$stamp = Get-Date -Format "yyyyMMddHHmmss"
$tarLocal = Join-Path $env:TEMP "cosmic-admin-dist-$stamp.tgz"
if (Test-Path $tarLocal) { Remove-Item -LiteralPath $tarLocal -Force }

Write-Host "Packing dist -> $tarLocal ..." -ForegroundColor Cyan
# tar.exe is built into Win10+; -C enters dist so archive root is index.html + assets/
& tar.exe -czf $tarLocal -C $dist .
if ($LASTEXITCODE -ne 0 -or -not (Test-Path $tarLocal)) {
    throw "tar pack failed"
}
$tarSize = (Get-Item -LiteralPath $tarLocal).Length
Write-Host ("Archive {0:N1} MB - uploading one file..." -f ($tarSize / 1MB)) -ForegroundColor Cyan

$tarRemote = "/tmp/cosmic-admin-dist-$stamp.tgz"
$scpOk = $false
for ($i = 1; $i -le 5; $i++) {
    Write-Host ("  scp archive try {0}/5 ..." -f $i) -ForegroundColor DarkGray
    & scp -o ConnectTimeout=20 -o ServerAliveInterval=15 -O $tarLocal "${vpsHost}:${tarRemote}"
    if ($LASTEXITCODE -eq 0) { $scpOk = $true; break }
    Start-Sleep -Seconds (3 * $i)
}
if (-not $scpOk) { throw "scp archive failed after retries" }

Write-Host "Extracting on VPS + syncing nginx ..." -ForegroundColor Cyan
& ssh -o ConnectTimeout=20 -o ServerAliveInterval=15 $vpsHost @"
set -e
mkdir -p '$remote' '$nginxRoot'
rm -rf '$remote'/* '$nginxRoot'/*
tar -xzf '$tarRemote' -C '$remote'
test -f '$remote/index.html'
cp -a '$remote'/. '$nginxRoot'/
chown -R www-data:www-data '$nginxRoot'
chmod -R a+rX '$nginxRoot'
rm -f '$tarRemote'
echo 'remote index.html OK'
"@
if ($LASTEXITCODE -ne 0) { throw "remote extract/sync failed" }

Remove-Item -LiteralPath $tarLocal -Force -ErrorAction SilentlyContinue

Write-Host ""
Write-Host "Done. Hard refresh (Ctrl+Shift+R)." -ForegroundColor Green
Write-Host "  Homepage: https://admin.coosmic.icu/"
Write-Host "  Admin:    https://admin.coosmic.icu/admin"
