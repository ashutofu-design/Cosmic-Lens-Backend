# Cosmic Lens — D drive setup (Node + Python deps)
# Run in PowerShell:  Set-ExecutionPolicy -Scope Process Bypass; .\scripts\setup-d-drive.ps1

$ErrorActionPreference = "Continue"
$Root = "D:\Cosmic-Lens-Backend"
$Log = Join-Path $Root "setup-d-drive.log"
$ToolsDir = Join-Path $Root ".tools"

function Write-Log($msg) {
    $line = "[$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')] $msg"
    Write-Host $line
    Add-Content -Path $Log -Value $line
}

Remove-Item $Log -ErrorAction SilentlyContinue
Set-Location $Root
Write-Log "=== Cosmic Lens D-drive setup ==="
Write-Log "Root: $Root"

# --- Node.js on D (optional portable install) ---
$NodeDir = Join-Path $ToolsDir "node"
$NodeExe = Join-Path $NodeDir "node.exe"

function Ensure-NodeOnD {
    if (Test-Path $NodeExe) {
        Write-Log "Node already at $NodeDir"
        return $true
    }
    Write-Log "Downloading Node.js LTS to $NodeDir ..."
    New-Item -ItemType Directory -Force -Path $NodeDir | Out-Null
    $zip = Join-Path $env:TEMP "node-win-x64.zip"
    $url = "https://nodejs.org/dist/v22.15.0/node-v22.15.0-win-x64.zip"
    try {
        Invoke-WebRequest -Uri $url -OutFile $zip -UseBasicParsing
        Expand-Archive -Path $zip -DestinationPath $ToolsDir -Force
        $extracted = Get-ChildItem (Join-Path $ToolsDir "node-v*") -Directory | Select-Object -First 1
        if ($extracted) {
            Get-ChildItem $extracted.FullName | Move-Item -Destination $NodeDir -Force
            Remove-Item $extracted.FullName -Recurse -Force
        }
        Remove-Item $zip -Force -ErrorAction SilentlyContinue
        Write-Log "Node installed to $NodeDir"
        return (Test-Path $NodeExe)
    } catch {
        Write-Log "Node download failed: $_"
        return $false
    }
}

# Prefer D-local node, then PATH
$env:PATH = "$NodeDir;$env:PATH"

if (-not (Get-Command node -ErrorAction SilentlyContinue)) {
    Write-Log "node not in PATH — trying D:\.tools\node ..."
    if (-not (Ensure-NodeOnD)) {
        Write-Log "ERROR: Install Node.js manually to D or add to PATH, then re-run."
    }
}

if (Get-Command node -ErrorAction SilentlyContinue) {
    Write-Log "node: $(node --version) at $(Get-Command node | Select-Object -ExpandProperty Source)"
    Write-Log "npm:  $(npm --version)"
} else {
    Write-Log "SKIP: node unavailable"
}

# pnpm via corepack or npm
if (-not (Get-Command pnpm -ErrorAction SilentlyContinue)) {
    Write-Log "Installing pnpm globally (npm) ..."
    npm install -g pnpm 2>&1 | ForEach-Object { Write-Log $_ }
}
if (Get-Command pnpm -ErrorAction SilentlyContinue) {
    Write-Log "pnpm: $(pnpm --version) at $(Get-Command pnpm | Select-Object -ExpandProperty Source)"
} else {
    Write-Log "ERROR: pnpm not available"
}

# --- pnpm install (node_modules on D in project root) ---
Write-Log "--- pnpm install (may take several minutes) ---"
$env:PNPM_HOME = Join-Path $Root ".pnpm-store"
$env:NPM_CONFIG_CACHE = Join-Path $Root ".npm-cache"
New-Item -ItemType Directory -Force -Path $env:PNPM_HOME, $env:NPM_CONFIG_CACHE | Out-Null

if (Get-Command pnpm -ErrorAction SilentlyContinue) {
    pnpm install 2>&1 | ForEach-Object { Write-Log $_ }
    if (Test-Path (Join-Path $Root "node_modules")) {
        Write-Log "OK: node_modules created at $Root\node_modules"
    } else {
        Write-Log "WARN: node_modules still missing after pnpm install"
    }
} else {
    Write-Log "SKIP: pnpm install"
}

# --- Python venv on D ---
$VenvPython = Join-Path $Root "artifacts\api-server\venv\Scripts\python.exe"
$VenvPip = Join-Path $Root "artifacts\api-server\venv\Scripts\pip.exe"
$Requirements = Join-Path $Root "artifacts\api-server\requirements.txt"

if (Test-Path $VenvPython) {
    Write-Log "venv python: $(& $VenvPython --version 2>&1)"
    Write-Log "--- pip install -r requirements.txt ---"
    & $VenvPip install -r $Requirements 2>&1 | ForEach-Object { Write-Log $_ }
    Write-Log "OK: Python venv at artifacts\api-server\venv"
} else {
    Write-Log "Creating Python venv on D ..."
    $py = Get-Command python -ErrorAction SilentlyContinue
    if (-not $py) {
        Write-Log "ERROR: python not in PATH. Install Python 3.12+ and re-run."
    } else {
        & python -m venv (Join-Path $Root "artifacts\api-server\venv")
        & $VenvPip install -r $Requirements 2>&1 | ForEach-Object { Write-Log $_ }
    }
}

Write-Log "=== Done. Log: $Log ==="
