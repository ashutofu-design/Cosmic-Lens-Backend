# Removes tracked .env from the last commit so GitHub push protection allows push.
# Run from repo root: powershell -ExecutionPolicy Bypass -File scripts/fix-secret-push.ps1

$ErrorActionPreference = "Stop"
$repoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $repoRoot
if (-not (Test-Path ".git")) {
    Write-Error "Expected .git in $repoRoot"
}

$tracked = @(
    "artifacts/api-server/.env",
    "artifacts/api-server/.env.txt",
    "artifacts/admin-web/.env"
)
foreach ($f in $tracked) {
    $listed = git ls-files --error-unmatch $f 2>$null
    if ($LASTEXITCODE -eq 0) {
        git rm --cached -f $f
        Write-Host "Untracked from git (file kept on disk): $f"
    }
}

git add .gitignore artifacts/api-server/.gitignore
$head = (git rev-parse --short HEAD).Trim()
Write-Host "Amending commit $head (removes .env from commit, keeps your code changes)..."
git commit --amend --no-edit

Write-Host ""
Write-Host "Done. Push with:  git push origin main"
Write-Host "Rotate OpenAI + Firebase/GCP keys if they were ever exposed (see GitHub email / this chat)."
