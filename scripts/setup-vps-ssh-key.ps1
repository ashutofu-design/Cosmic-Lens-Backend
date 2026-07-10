# One-time: SSH key to VPS so deploy scripts ask password ZERO times.
# Usage (from repo root):
#   .\scripts\setup-vps-ssh-key.ps1
# Optional: $env:VPS_HOST = "root@187.127.174.55"

$ErrorActionPreference = "Stop"
$vpsHost = if ($env:VPS_HOST) { $env:VPS_HOST } else { "root@187.127.174.55" }
$sshDir = Join-Path $env:USERPROFILE ".ssh"
$key = Join-Path $sshDir "id_ed25519"
$pub = "$key.pub"

if (-not (Test-Path $sshDir)) {
    New-Item -ItemType Directory -Path $sshDir -Force | Out-Null
}

if (-not (Test-Path $key)) {
    Write-Host "Creating SSH key at $key ..." -ForegroundColor Cyan
    ssh-keygen -t ed25519 -f $key -N '""' -q
}

Write-Host "Copying public key to $vpsHost (enter VPS password ONE last time) ..." -ForegroundColor Cyan
Get-Content $pub | ssh $vpsHost "umask 077; mkdir -p ~/.ssh; chmod 700 ~/.ssh; cat >> ~/.ssh/authorized_keys; chmod 600 ~/.ssh/authorized_keys; echo SSH_key_installed"

Write-Host "Testing passwordless login ..." -ForegroundColor Cyan
ssh -o BatchMode=yes -o ConnectTimeout=10 $vpsHost "echo OK_no_password_needed"
if ($LASTEXITCODE -ne 0) {
    Write-Host "WARN: BatchMode test failed - try: ssh $vpsHost" -ForegroundColor Yellow
} else {
    Write-Host "Done. Run .\scripts\deploy-ask-admin-vps.ps1 - no more password prompts." -ForegroundColor Green
}
