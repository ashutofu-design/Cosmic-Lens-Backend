# Copies protected feature files to backups/snapshots/<timestamp>/
# Run before big edits:  powershell -File scripts/snapshot-protected.ps1

$ErrorActionPreference = "Stop"
$Root = Split-Path $PSScriptRoot -Parent
Set-Location $Root

$manifestPath = Join-Path $Root "protected\MANIFEST.json"
if (-not (Test-Path $manifestPath)) {
    Write-Error "protected/MANIFEST.json not found at $Root"
}

$manifest = Get-Content $manifestPath -Raw | ConvertFrom-Json
$stamp = Get-Date -Format "yyyy-MM-dd_HH-mm-ss"
$dest = Join-Path $Root "backups\snapshots\$stamp"
New-Item -ItemType Directory -Force -Path $dest | Out-Null

$copied = 0
foreach ($rel in $manifest.paths) {
    $relWin = $rel -replace "/", [IO.Path]::DirectorySeparatorChar
    $src = Join-Path $Root $relWin
    if (-not (Test-Path -LiteralPath $src)) {
        Write-Warning "Skip (missing): $rel"
        continue
    }
    $target = Join-Path $dest $relWin
    $targetDir = Split-Path -Parent $target
    if ($targetDir) { New-Item -ItemType Directory -Force -Path $targetDir | Out-Null }
    Copy-Item -LiteralPath $src -Destination $target -Force
    $copied++
}

Write-Host "Snapshot OK: $copied files -> backups\snapshots\$stamp"
Write-Host "Restore example:"
Write-Host "  Copy-Item -Recurse backups\snapshots\$stamp\artifacts\* artifacts\ -Force"
