"""
Celery application — Face Reading PDF workers.

Broker/result backend use Redis DB 1/2 by default (cache stays on DB 0).

Start worker:
  celery -A celery_app worker -Q face_pdf -c 2 -n face_pdf@%h --prefetch-multiplier=1
"""
from __future__ import annotations

import os

from celery import Celery
from kombu import Queue

_broker = (
    os.environ.get("CELERY_BROKER_URL")
    or os.environ.get("REDIS_URL", "redis://localhost:6379/0").rsplit("/", 1)[0]
    + "/1"
)
_result = os.environ.get("CELERY_RESULT_BACKEND") or _broker.replace("/1", "/2")

_face_q = os.environ.get("CELERY_FACE_PDF_QUEUE", "face_pdf")
_default_q = os.environ.get("CELERY_DEFAULT_QUEUE", "celery")

celery_app = Celery(
    "cosmic_lens",
    broker=_broker,
    backend=_result,
    include=["tasks.face_report_tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    worker_prefetch_multiplier=int(os.environ.get("CELERY_PREFETCH", "1")),
    task_default_queue=_default_q,
    task_queues=(
        Queue(_face_q, routing_key=_face_q),
        Queue(_default_q, routing_key=_default_q),
    ),
    task_routes={
        "face.generate_pdf_report": {"queue": _face_q},
    },
    task_soft_time_limit=int(os.environ.get("FACE_PDF_SOFT_TIME_LIMIT", "300")),
    task_time_limit=int(os.environ.get("FACE_PDF_TIME_LIMIT", "360")),
    broker_connection_retry_on_startup=True,
    result_expires=int(os.environ.get("CELERY_RESULT_EXPIRES", "86400")),
)

# Import tasks so decorators register
try:
    import tasks.face_report_tasks  # noqa: F401
except ImportError:
    pass
