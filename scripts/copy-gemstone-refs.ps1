$srcDir = "C:\Users\HP\.cursor\projects\d-Cosmic-Lens-Backend\assets"
$mobile = "d:\Cosmic-Lens-Backend\artifacts\cosmic-lens-mobile\assets\gemstones"
$api = "d:\Cosmic-Lens-Backend\artifacts\api-server\gemstone_media"
New-Item -ItemType Directory -Force -Path $mobile, $api | Out-Null

$pairs = @(
  @("c__Users_HP_AppData_Roaming_Cursor_User_workspaceStorage_9da6a3f89f649eed21cefcf12c23e1a9_images_ceylon-pukhraj-yellow-sapphire-5-25-ratti-gemstone-original-unheated-500x500-3a7ea633-50e7-40f9-bf92-bdfea5c3b766.png", "pukhraj-hero.png"),
  @("c__Users_HP_AppData_Roaming_Cursor_User_workspaceStorage_9da6a3f89f649eed21cefcf12c23e1a9_images_images-0ecbfeaa-9ce2-47f9-a207-3e71ff4a2e35.png", "pukhraj-cushion.png"),
  @("c__Users_HP_AppData_Roaming_Cursor_User_workspaceStorage_9da6a3f89f649eed21cefcf12c23e1a9_images_images__1_-4796d852-8044-4544-a563-e1c7cbc77000.png", "pukhraj-wear.png"),
  @("c__Users_HP_AppData_Roaming_Cursor_User_workspaceStorage_9da6a3f89f649eed21cefcf12c23e1a9_images_1551dd95-6-Buy-Online-Yellow-Sapphire-5000-14a75558-946c-4185-a751-15d72f7c34b5.png", "pukhraj-lifestyle.png")
)

python -m pip install Pillow -q 2>$null
python "d:\Cosmic-Lens-Backend\scripts\restore-gemstone-images.py"
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

foreach ($p in $pairs) {
  $m = Join-Path $mobile $p[1]
  Write-Output "$($p[1]): $((Get-Item $m).Length) bytes"
}
