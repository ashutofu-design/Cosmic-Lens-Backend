#!/usr/bin/env bash
# Face Reading PDF Celery worker (run from artifacts/api-server)
set -euo pipefail
cd "$(dirname "$0")/.."
export PYTHONPATH="${PYTHONPATH:-}:$(pwd)"
export CELERY_BROKER_URL="${CELERY_BROKER_URL:-redis://localhost:6379/1}"
export CELERY_RESULT_BACKEND="${CELERY_RESULT_BACKEND:-redis://localhost:6379/2}"
export REDIS_URL="${REDIS_URL:-redis://localhost:6379/0}"
export CELERY_FACE_PDF_QUEUE="${CELERY_FACE_PDF_QUEUE:-face_pdf}"
CONCURRENCY="${FACE_PDF_WORKER_CONCURRENCY:-2}"

exec celery -A celery_app worker \
  -Q "${CELERY_FACE_PDF_QUEUE}" \
  -c "${CONCURRENCY}" \
  -n "face_pdf@%h" \
  --prefetch-multiplier=1 \
  --loglevel=info
