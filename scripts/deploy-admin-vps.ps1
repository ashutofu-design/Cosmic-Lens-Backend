# One-click: push latest admin + API to VPS and rebuild admin panel.
# Run in VS Code terminal (repo root):
#   powershell -ExecutionPolicy Bypass -File .\scripts\deploy-admin-vps.ps1
#
# Needs: git push access + SSH to VPS (or use printed Browser Terminal fallback).

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
if (-not (Test-Path (Join-Path $root "artifacts\api-server\flask_app.py"))) {
    throw "Run from Cosmic-Lens-Backend repo root."
}

$vps = if ($env:VPS_HOST) { $env:VPS_HOST } else { "root@187.127.174.55" }
$remoteRepo = "/root/Cosmic-Lens-Backend"

$sshOpts = @(
    "-o", "ConnectTimeout=25",
    "-o", "ServerAliveInterval=15",
    "-o", "ServerAliveCountMax=4",
    "-o", "TCPKeepAlive=yes"
)

function Invoke-SshRetry {
    param(
        [Parameter(Mandatory = $true)][string]$RemoteCommand,
        [int]$Tries = 4
    )
    for ($i = 1; $i -le $Tries; $i++) {
        Write-Host ("  ssh try {0}/{1}" -f $i, $Tries) -ForegroundColor DarkGray
        & ssh @sshOpts $vps $RemoteCommand
        if ($LASTEXITCODE -eq 0) { return }
        Write-Host ("  ssh failed (exit {0}), waiting..." -f $LASTEXITCODE) -ForegroundColor Yellow
        Start-Sleep -Seconds (3 * $i)
    }
    throw "SSH failed after $Tries tries"
}

Write-Host "=== 1/3 Git push (laptop) ===" -ForegroundColor Cyan
Push-Location $root
try {
    $branch = (git rev-parse --abbrev-ref HEAD).Trim()
    $dirty = git status --porcelain -- artifacts/admin-web artifacts/api-server/instagram_answers.py artifacts/api-server/flask_app.py artifacts/api-server/models.py
    if ($dirty) {
        Write-Host "Uncommitted admin/API changes - auto-committing deploy bundle..." -ForegroundColor Yellow
        git add artifacts/admin-web/src artifacts/admin-web/public artifacts/admin-web/index.html artifacts/admin-web/vite.config.ts artifacts/admin-web/README.md
        git add artifacts/api-server/instagram_answers.py artifacts/api-server/flask_app.py artifacts/api-server/models.py artifacts/api-server/question_history.py
        git add artifacts/api-server/lifemap_admin_deliver.py artifacts/api-server/support_chat.py artifacts/api-server/admin_privacy.py artifacts/api-server/admin_push.py artifacts/api-server/admin_security.py
        git add artifacts/api-server/cosmic_intelligence_v3_sessions.py artifacts/api-server/founder_text_pdf.py artifacts/api-server/founder_structure.py
        git add artifacts/api-server/cosmic_pro_report_design.py artifacts/api-server/birth_time_rectification_orders.py
        git add artifacts/api-server/birth_time_rectification_api.py artifacts/api-server/birth_time_rectification_billing.py
        git add artifacts/api-server/business_vastu_api.py artifacts/api-server/business_vastu_billing.py
        git add artifacts/api-server/ask_v1_api.py artifacts/api-server/ask_v1_billing.py artifacts/api-server/ask_v3_api.py artifacts/api-server/ask_v3_billing.py
        git add artifacts/api-server/palmistry_human_orders.py artifacts/api-server/palmistry_report_api.py artifacts/api-server/palmistry_report_billing.py
        git add artifacts/api-server/numerology_human_orders.py artifacts/api-server/numerology_agent_bridge.py
        git add artifacts/api-server/v3_engine_polish.py artifacts/api-server/support_account.py
        git add artifacts/api-server/support_agent/
        git add scripts/deploy-admin-vps.ps1
        git commit -m "Deploy: admin-web source + API modules for VPS build"
        if ($LASTEXITCODE -ne 0) {
            Write-Host "Nothing new to commit (OK if already committed)." -ForegroundColor DarkGray
        }
    }
    git push -u origin $branch
    if ($LASTEXITCODE -ne 0) { throw "git push failed" }
    $sha = (git rev-parse --short HEAD).Trim()
    Write-Host ("Pushed {0} at {1}" -f $branch, $sha) -ForegroundColor Green
} finally {
    Pop-Location
}

Write-Host "=== 2/3 Sync VPS to GitHub (no git clean) ===" -ForegroundColor Cyan

$remoteCmd = @'
set -e
cd REPO_PLACEHOLDER
cp -a artifacts/api-server/.env /tmp/cosmic-api-env.bak 2>/dev/null || true
git fetch origin
git reset --hard origin/BRANCH_PLACEHOLDER
git log -1 --oneline
test -f artifacts/admin-web/src/PalmistryAnalysisWorkspace.tsx || { echo "MISSING PalmistryAnalysisWorkspace.tsx"; exit 1; }
test -f artifacts/api-server/instagram_answers.py || { echo "MISSING instagram_answers.py"; exit 1; }
grep -q "Instagram Answers" artifacts/admin-web/src/App.tsx
cd artifacts/api-server
find . -name '*.pyc' -delete
pm2 restart cosmic-api --update-env
sleep 5
cd REPO_PLACEHOLDER
bash scripts/vps-deploy-admin-mobile.sh
grep -l "Instagram Answers" /var/www/cosmic-admin/assets/*.js | head -1 || { echo "BUILD OK but string not in JS"; exit 1; }
echo VPS_DEPLOY_OK
'@

$remoteCmd = $remoteCmd.Replace("REPO_PLACEHOLDER", $remoteRepo).Replace("BRANCH_PLACEHOLDER", $branch)

try {
    Invoke-SshRetry -RemoteCommand $remoteCmd
} catch {
    Write-Host ""
    Write-Host "SSH failed - use Hostinger Browser Terminal and paste:" -ForegroundColor Red
    Write-Host ("cd {0}" -f $remoteRepo) -ForegroundColor Yellow
    Write-Host ("git fetch origin && git reset --hard origin/{0}" -f $branch) -ForegroundColor Yellow
    Write-Host "cd artifacts/api-server && find . -name '*.pyc' -delete && pm2 restart cosmic-api --update-env && sleep 5" -ForegroundColor Yellow
    Write-Host ("cd {0} && bash scripts/vps-deploy-admin-mobile.sh" -f $remoteRepo) -ForegroundColor Yellow
    throw
}

Write-Host ""
Write-Host "=== 3/3 DONE ===" -ForegroundColor Green
Write-Host "  Admin: https://admin.coosmic.icu/admin"
Write-Host "  Hard refresh: Ctrl+Shift+R - Instagram Answers tab should appear."
Write-Host "  Do NOT run git clean -fd on VPS."
