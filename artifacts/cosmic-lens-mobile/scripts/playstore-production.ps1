# Cosmic Lens — Play Store production build + submit (v1.0.16+)
# Run from repo root OR from artifacts/cosmic-lens-mobile

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

Write-Host "=== Cosmic Lens Play Store production ===" -ForegroundColor Cyan
Write-Host "Folder: $Root"

# Signing files are gitignored — never commit keystore passwords or credentials.json.
$keystorePath = $env:ANDROID_KEYSTORE_PATH
if (-not $keystorePath) { $keystorePath = "./upload-keystore.jks" }
if (-not (Test-Path $keystorePath)) {
  Write-Host "MISSING: Android upload keystore at $keystorePath" -ForegroundColor Red
  Write-Host "Set ANDROID_KEYSTORE_PATH or place upload-keystore.jks locally (not in git)."
  Write-Host "If the old key was exposed in git history, request an upload-key reset in Play Console."
  exit 1
}

if (-not (Test-Path "./credentials.json")) {
  Write-Host "MISSING: credentials.json (local EAS signing config — gitignored)." -ForegroundColor Red
  Write-Host "Create from credentials.json.example; store passwords in env / a password manager only."
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
