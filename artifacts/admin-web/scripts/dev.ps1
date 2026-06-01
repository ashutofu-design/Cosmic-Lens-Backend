# Clean reinstall helper when Rollup native module errors on Windows
$root = Resolve-Path (Join-Path $PSScriptRoot "..\..\..")
Set-Location $root
Write-Host "Installing from repo root: $root"
pnpm install
Set-Location (Join-Path $root "artifacts\admin-web")
pnpm dev
