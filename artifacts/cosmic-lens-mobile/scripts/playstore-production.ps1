# Cosmic Lens — Play Store production build + submit (v1.0.16+)
# Run from repo root OR from artifacts/cosmic-lens-mobile

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

Write-Host "=== Cosmic Lens Play Store production ===" -ForegroundColor Cyan
Write-Host "Folder: $Root"

if (-not (Test-Path "./upload-keystore.jks")) {
  Write-Host "MISSING: upload-keystore.jks in cosmic-lens-mobile folder." -ForegroundColor Red
  Write-Host "Copy your Play upload keystore here before building."
  exit 1
}

if (-not (Test-Path "./credentials.json")) {
  Write-Host "MISSING: credentials.json" -ForegroundColor Red
  exit 1
}

Write-Host "`n1/2 — EAS production build (AAB)..." -ForegroundColor Yellow
npx eas-cli build --profile production --platform android --non-interactive
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "`n2/2 — Submit latest AAB to Play Store (production track)..." -ForegroundColor Yellow
Write-Host "Tip: If submit fails, upload the AAB manually from expo.dev build page." -ForegroundColor DarkGray
npx eas-cli submit --profile production --platform android --latest --non-interactive
if ($LASTEXITCODE -ne 0) {
  Write-Host "Submit failed — download AAB from https://expo.dev and upload in Play Console." -ForegroundColor Yellow
  exit $LASTEXITCODE
}

Write-Host "`nDone. Open Play Console -> Production -> review release and roll out." -ForegroundColor Green
