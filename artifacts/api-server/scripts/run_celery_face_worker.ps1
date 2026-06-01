# Face Reading PDF Celery worker (Windows)
$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $Root
$env:PYTHONPATH = "$Root"
if (-not $env:CELERY_BROKER_URL) { $env:CELERY_BROKER_URL = "redis://localhost:6379/1" }
if (-not $env:CELERY_RESULT_BACKEND) { $env:CELERY_RESULT_BACKEND = "redis://localhost:6379/2" }
if (-not $env:REDIS_URL) { $env:REDIS_URL = "redis://localhost:6379/0" }
if (-not $env:CELERY_FACE_PDF_QUEUE) { $env:CELERY_FACE_PDF_QUEUE = "face_pdf" }
$Concurrency = if ($env:FACE_PDF_WORKER_CONCURRENCY) { $env:FACE_PDF_WORKER_CONCURRENCY } else { "2" }

celery -A celery_app worker `
  -Q $env:CELERY_FACE_PDF_QUEUE `
  -c $Concurrency `
  -n "face_pdf@%h" `
  --prefetch-multiplier=1 `
  --loglevel=info
