$srcDir = "C:\Users\HP\.cursor\projects\d-Cosmic-Lens-Backend\assets"
$names = @(
  "pukhraj-hero.png", "pukhraj-cushion.png", "pukhraj-wear.png",
  "pukhraj-specs.png", "pukhraj-care.png", "pukhraj-lifestyle.png"
)
$dests = @(
  "d:\Cosmic-Lens-Backend\artifacts\cosmic-lens-mobile\assets\gemstones",
  "d:\Cosmic-Lens-Backend\artifacts\api-server\gemstone_media"
)
$report = "d:\Cosmic-Lens-Backend\gemstone-copy-report.txt"
$files = Get-ChildItem $srcDir -Filter "*.png" -ErrorAction SilentlyContinue | Sort-Object Name
if (-not $files) { Write-Error "No PNG files in $srcDir"; exit 1 }
foreach ($d in $dests) { New-Item -ItemType Directory -Force -Path $d | Out-Null }
$log = @()
for ($i = 0; $i -lt [Math]::Min($names.Count, $files.Count); $i++) {
  $dst = Join-Path $dests[0] $names[$i]
  Copy-Item $files[$i].FullName $dst -Force
  Copy-Item $files[$i].FullName (Join-Path $dests[1] $names[$i]) -Force
  $log += "$($files[$i].Name) -> $($names[$i]) ($((Get-Item $dst).Length) bytes)"
}
$log | Set-Content $report
$log | ForEach-Object { Write-Host $_ }
