#!/usr/bin/env bash
# Remove tracked .env from the last commit (GitHub push protection).
# Run on the machine that made the bad commit (usually your PC), from repo root:
#   bash scripts/fix-secret-push.sh
#   git push origin main

set -euo pipefail
cd "$(dirname "$0")/.."

for f in artifacts/api-server/.env artifacts/api-server/.env.txt artifacts/admin-web/.env; do
  if git ls-files --error-unmatch "$f" &>/dev/null; then
    git rm --cached -f "$f"
    echo "Untracked from git (file kept on disk): $f"
  fi
done

git add .gitignore artifacts/api-server/.gitignore
echo "Amending commit $(git rev-parse --short HEAD)..."
git commit --amend --no-edit
echo "Done. Push with: git push origin main"
