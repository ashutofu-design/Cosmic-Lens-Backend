# Cosmic Lens API — Windows dev starter (restart to pick up new routes)
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot
$env:PORT = if ($env:PORT) { $env:PORT } else { "8080" }
Write-Host "[start] Flask dev server on http://localhost:$($env:PORT)"
& ".\venv\Scripts\python.exe" flask_app.py
