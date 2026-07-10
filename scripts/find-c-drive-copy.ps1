$Log = "D:\Cosmic-Lens-Backend\c-drive-scan.log"
Remove-Item $Log -ErrorAction SilentlyContinue

function Log($m) { Add-Content $Log $m; Write-Host $m }

Log "=== Scan started $(Get-Date) ==="

# Common project locations on C
$candidates = @(
    "C:\Users\HP\Cosmic-Lens-Backend",
    "C:\Users\HP\Documents\Cosmic-Lens-Backend",
    "C:\Cosmic-Lens-Backend",
    "C:\Users\HP\source\repos\Cosmic-Lens-Backend",
    "C:\Users\HP\Desktop\Cosmic-Lens-Backend",
    "C:\Users\HP\projects\Cosmic-Lens-Backend",
    "C:\Users\HP\OneDrive\Cosmic-Lens-Backend",
    "C:\Users\HP\Downloads\Cosmic-Lens-Backend"
)

foreach ($p in $candidates) {
    if (Test-Path $p) {
        $nm = Test-Path (Join-Path $p "node_modules")
        $venv = Test-Path (Join-Path $p "artifacts\api-server\venv")
        $oai = (Get-Item (Join-Path $p "artifacts\api-server\openai_helper.py") -ErrorAction SilentlyContinue).Length
        Log "FOUND: $p | node_modules=$nm | venv=$venv | openai_helper_bytes=$oai"
    }
}

# Search HP home for cosmic-lens folders (depth 3)
Log "--- Searching C:\Users\HP for cosmic/lens folders ---"
Get-ChildItem "C:\Users\HP" -Directory -ErrorAction SilentlyContinue | ForEach-Object {
    $hits = Get-ChildItem $_.FullName -Directory -Recurse -Depth 2 -ErrorAction SilentlyContinue |
        Where-Object { $_.Name -match 'cosmic|Cosmic-Lens' }
    foreach ($h in $hits) {
        $nm = Test-Path (Join-Path $h.FullName "node_modules")
        Log "HIT: $($h.FullName) node_modules=$nm"
    }
}

# Search for node_modules with cosmic-lens-mobile inside
Log "--- node_modules with @workspace or cosmic-lens ---"
$searchRoots = @("C:\Users\HP", "C:\dev", "C:\projects", "C:\code")
foreach ($root in $searchRoots) {
    if (-not (Test-Path $root)) { continue }
    Get-ChildItem $root -Directory -Filter "node_modules" -Recurse -Depth 4 -ErrorAction SilentlyContinue |
        Where-Object { $_.FullName -match 'Cosmic|cosmic-lens' } |
        Select-Object -First 10 |
        ForEach-Object { Log "NM: $($_.FullName)" }
}

# Replit cache
$replit = @(
    "C:\Users\HP\.cache\replit",
    "C:\Users\HP\AppData\Local\replit",
    "C:\Users\HP\.local\share\replit"
)
foreach ($r in $replit) {
    if (Test-Path $r) { Log "REPLIT: $r"; Get-ChildItem $r -ErrorAction SilentlyContinue | Select-Object -First 5 | ForEach-Object { Log "  $($_.Name)" } }
}

Log "=== Scan done ==="
