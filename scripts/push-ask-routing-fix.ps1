# Push ONLY Ask routing + language fixes (no node_modules / whole repo).
# Usage (PowerShell, repo root):
#   .\scripts\push-ask-routing-fix.ps1

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $root

$files = @(
    "artifacts/api-server/ask_question_normalize.py",
    "artifacts/api-server/ask_love/timing_registry.py",
    "artifacts/api-server/event_timing/timing_router.py",
    "artifacts/api-server/chart_fact_answer.py",
    "artifacts/api-server/openai_helper.py",
    "artifacts/api-server/tests/test_prem_sambandh_routing.py",
    "artifacts/admin-web/src/questionLang.ts",
    "artifacts/admin-web/src/QuestionLangBadge.tsx",
    "artifacts/admin-web/src/AskQuestionDetailPage.tsx",
    "artifacts/admin-web/src/App.tsx",
    "artifacts/admin-web/src/index.css"
)

Write-Host "Staging fixed files only ($($files.Count) paths)..." -ForegroundColor Cyan
foreach ($f in $files) {
    if (-not (Test-Path (Join-Path $root $f))) {
        Write-Host "MISSING: $f" -ForegroundColor Red
        exit 1
    }
    git add -- $f
}

$st = git diff --cached --name-only
if (-not $st) {
    Write-Host "Nothing to commit — already pushed or no local changes." -ForegroundColor Yellow
    git status -sb
    exit 0
}

Write-Host "Staged:" -ForegroundColor Green
$st | ForEach-Object { Write-Host "  $_" }

git commit -m "Ask: love routing typos, Devanagari replies, prem sambandh fix, admin language badge"
git push origin main

Write-Host ""
Write-Host "Done. On VPS run:" -ForegroundColor Green
Write-Host "  cd /root/Cosmic-Lens-Backend && git pull origin main"
Write-Host "  cd artifacts/api-server && pm2 restart cosmic-api --update-env"
Write-Host "  cd ../admin-web && pnpm run build"
