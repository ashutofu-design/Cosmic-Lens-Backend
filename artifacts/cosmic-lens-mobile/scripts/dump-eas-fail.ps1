# Dump latest failed EAS Android build reason into _eas_fail_dump.txt
# Run from VS Code terminal (PowerShell):
#   cd d:\Cosmic-Lens-Backend\artifacts\cosmic-lens-mobile
#   powershell -ExecutionPolicy Bypass -File .\scripts\dump-eas-fail.ps1

$ErrorActionPreference = "Continue"
Set-Location $PSScriptRoot\..
$out = Join-Path (Get-Location) "_eas_fail_dump.txt"

"=== EAS FAIL DUMP $(Get-Date -Format o) ===" | Set-Content $out -Encoding UTF8

"--- build:list ---" | Add-Content $out
$listJson = & eas build:list --platform android --limit 5 --non-interactive --json 2>&1 | Out-String
$listJson | Add-Content $out

$buildId = $null
try {
  $builds = $listJson | ConvertFrom-Json
  if ($builds -isnot [Array]) { $builds = @($builds) }
  foreach ($b in $builds) {
    $st = [string]$b.status
    if ($st -match "errored|failed|canceled") {
      $buildId = $b.id
      "Picked failed build: $buildId status=$st" | Add-Content $out
      break
    }
  }
  if (-not $buildId -and $builds.Count -gt 0) {
    $buildId = $builds[0].id
    "Picked latest build: $buildId status=$($builds[0].status)" | Add-Content $out
  }
} catch {
  "JSON parse failed: $_" | Add-Content $out
}

if ($buildId) {
  "`n--- build:view $buildId ---" | Add-Content $out
  & eas build:view $buildId --non-interactive 2>&1 | Out-String | Add-Content $out

  "`n--- trying log URL hint ---" | Add-Content $out
  "https://expo.dev/accounts/cosmiclens/projects/cosmic-lens-mobile/builds/$buildId" | Add-Content $out
}

"`nDONE. File: $out" | Add-Content $out
Write-Host "Wrote $out"
