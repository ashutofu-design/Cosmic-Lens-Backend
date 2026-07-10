$ErrorActionPreference = "Continue"
$log = Join-Path $PSScriptRoot "..\deploy_automation.log"
function Log($msg) { $line = "$(Get-Date -Format o) $msg"; Add-Content -Path $log -Value $line; Write-Output $line }

Set-Location (Join-Path $PSScriptRoot "..")
Log "=== DEPLOY START ==="

Log "git status"
git status --short 2>&1 | Out-String | ForEach-Object { Log $_ }

$paths = @(
    "artifacts/api-server/ask_education",
    "artifacts/api-server/openai_helper.py",
    "artifacts/api-server/ask_intent_llm.py",
    "artifacts/api-server/ask_career/classifier.py",
    "artifacts/api-server/ask_career/sector_registry.py",
    "artifacts/api-server/scripts/audit_education_full.py",
    "artifacts/api-server/tests/test_ask_education_engine.py"
)
foreach ($p in $paths) {
    if (Test-Path $p) { git add $p 2>&1 | Out-String | ForEach-Object { Log "add $p : $_" } }
}

Log "git diff --cached --stat"
git diff --cached --stat 2>&1 | Out-String | ForEach-Object { Log $_ }

$status = git diff --cached --quiet 2>&1
if ($LASTEXITCODE -ne 0) {
    git commit -m "Ask: education engine (15 archetypes) + 241-question audit fixes and routing" 2>&1 | Out-String | ForEach-Object { Log $_ }
} else {
    Log "Nothing staged to commit"
}

Log "git log -1"
git log -1 --oneline 2>&1 | Out-String | ForEach-Object { Log $_ }

Log "git push"
git push 2>&1 | Out-String | ForEach-Object { Log $_ }
if ($LASTEXITCODE -ne 0) {
    git push -u origin HEAD 2>&1 | Out-String | ForEach-Object { Log "push -u: $_" }
}

Log "SSH deploy"
$sshCmd = "cd /root/Cosmic-Lens-Backend && find . -name '*.pyc' -delete && git pull && cd artifacts/api-server && pm2 restart cosmic-api --update-env && ls ask_education/engine.py && pm2 list | head -5"
ssh -o BatchMode=yes -o ConnectTimeout=60 root@187.127.174.55 $sshCmd 2>&1 | Out-String | ForEach-Object { Log $_ }

Log "=== DEPLOY END exit=$LASTEXITCODE ==="
