# Copy missing files from C-drive Cosmic-Lens copy -> D:\Cosmic-Lens-Backend
# Run: powershell -ExecutionPolicy Bypass -File scripts\copy-from-c-drive.ps1

$ErrorActionPreference = "Continue"
$Dest = "D:\Cosmic-Lens-Backend"
$Log = Join-Path $Dest "copy-from-c-drive.log"
Remove-Item $Log -ErrorAction SilentlyContinue

function Log($m) {
    $line = "[$(Get-Date -Format 'HH:mm:ss')] $m"
    Write-Host $line
    Add-Content $Log $line
}

function Find-SourceProject {
    $roots = @(
        "C:\Users\HP\Cosmic-Lens-Backend",
        "C:\Cosmic-Lens-Backend",
        "C:\Users\HP\Documents\Cosmic-Lens-Backend",
        "C:\Users\HP\Desktop\Cosmic-Lens-Backend",
        "C:\Users\HP\source\repos\Cosmic-Lens-Backend",
        "C:\Users\HP\projects\Cosmic-Lens-Backend",
        "C:\Users\HP\OneDrive\Cosmic-Lens-Backend",
        "C:\Users\HP\Downloads\Cosmic-Lens-Backend"
    )
    foreach ($r in $roots) {
        if ((Test-Path (Join-Path $r "artifacts\api-server\flask_app.py")) -and $r -ne $Dest) {
            return $r
        }
    }
    Log "Searching C:\Users\HP for flask_app.py (depth 5)..."
    $hits = Get-ChildItem "C:\Users\HP" -Recurse -Filter "flask_app.py" -ErrorAction SilentlyContinue |
        Where-Object { $_.FullName -match 'api-server\\flask_app\.py$' } |
        Select-Object -First 5
    foreach ($h in $hits) {
        $proj = Split-Path (Split-Path $h.FullName -Parent) -Parent
        if ($proj -ne $Dest) { return $proj }
    }
    return $null
}

Log "=== Copy C -> D started ==="
$Src = Find-SourceProject
if (-not $Src) {
    Log "ERROR: No Cosmic-Lens project found on C drive."
    Log "Manually set source: `$Src = 'C:\path\to\Cosmic-Lens-Backend'"
    exit 1
}
Log "SOURCE: $Src"
Log "DEST:   $Dest"

# --- 1) node_modules (root + mobile) ---
$copyDirs = @(
    @{ Rel = "node_modules"; Desc = "root node_modules" },
    @{ Rel = "artifacts\cosmic-lens-mobile\node_modules"; Desc = "mobile node_modules" },
    @{ Rel = ".pnpm-store"; Desc = "pnpm store" }
)
foreach ($item in $copyDirs) {
    $from = Join-Path $Src $item.Rel
    $to = Join-Path $Dest $item.Rel
    if (-not (Test-Path $from)) {
        Log "SKIP $($item.Desc): not on C ($from)"
        continue
    }
    Log "COPY $($item.Desc): robocopy..."
    New-Item -ItemType Directory -Force -Path (Split-Path $to -Parent) | Out-Null
    robocopy $from $to /E /MT:8 /R:2 /W:3 /NFL /NDL /NP | ForEach-Object { Log $_ }
    Log "DONE $($item.Desc)"
}

# --- 2) Critical empty files on D (openai_helper etc.) ---
$criticalFiles = @(
    "artifacts\api-server\openai_helper.py",
    "artifacts\api-server\ask_engine.py",
    "artifacts\api-server\intent_router.py"
)
foreach ($rel in $criticalFiles) {
    $destFile = Join-Path $Dest $rel
    $srcFile = Join-Path $Src $rel
    $destLen = if (Test-Path $destFile) { (Get-Item $destFile).Length } else { -1 }
    $srcLen = if (Test-Path $srcFile) { (Get-Item $srcFile).Length } else { 0 }
    if ($srcLen -gt 1000 -and $destLen -lt 1000) {
        Log "COPY file $rel ($destLen -> $srcLen bytes)"
        Copy-Item $srcFile $destFile -Force
    } else {
        Log "SKIP $rel dest=$destLen src=$srcLen"
    }
}

# --- 3) All zero-byte .py on D that have content on C ---
Log "--- Zero-byte .py repair ---"
Get-ChildItem (Join-Path $Dest "artifacts\api-server") -Filter "*.py" -File -ErrorAction SilentlyContinue |
    Where-Object { $_.Length -eq 0 } |
    ForEach-Object {
        $rel = $_.FullName.Substring($Dest.Length + 1)
        $srcFile = Join-Path $Src $rel
        if ((Test-Path $srcFile) -and (Get-Item $srcFile).Length -gt 0) {
            Log "REPAIR $rel"
            Copy-Item $srcFile $_.FullName -Force
        } else {
            Log "STILL EMPTY $rel (no C source)"
        }
    }

# --- 4) pnpm install if node_modules still missing ---
if (-not (Test-Path (Join-Path $Dest "node_modules"))) {
    Log "node_modules still missing — running pnpm install..."
    Set-Location $Dest
    if (-not (Get-Command pnpm -ErrorAction SilentlyContinue)) { npm install -g pnpm }
    pnpm install 2>&1 | ForEach-Object { Log $_ }
}

Log "=== Done. Log: $Log ==="
Log "Verify: Test-Path D:\Cosmic-Lens-Backend\node_modules"
Log "Verify: (Get-Item D:\Cosmic-Lens-Backend\artifacts\api-server\openai_helper.py).Length"
