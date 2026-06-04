#!/usr/bin/env bash
set -euo pipefail

# EAS runs from repo root when monorepo is detected; ensure install uses workspace root.
ROOT="${EAS_BUILD_WORKINGDIR:-$(pwd)}"
cd "$ROOT"

if [[ ! -f pnpm-lock.yaml ]]; then
  echo "eas-build-pre-install: pnpm-lock.yaml missing at $ROOT"
  exit 1
fi

echo "eas-build-pre-install: monorepo root OK ($ROOT)"
