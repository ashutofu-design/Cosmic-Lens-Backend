# Face Reading — Redis cache migration

## Redis key structure

| Key | TTL | Content |
|-----|-----|---------|
| `face:session:{session_id}` | 24h (`FACE_SESSION_TTL`) | Landmarks JSON, report_payload (no image bytes), analysis_id |
| `face:session:{session_id}:img:front` | 2h (`FACE_EXTRACT_IMG_TTL`) | Raw front JPEG bytes |
| `face:dedup:{user_id}:{sha256}` | 90d | `{session_id, analysis_id}` |
| `face:analysis:{analysis_id}` | 24h | Immutable engines + sections snapshot |
| `face:narration:{analysis_id}:{lang}` | 30d | Assembled report (no bytes/engines) |
| `face:pdf:{analysis_id}:{lang}` | 30d | `{ledger_id, path, filename, size_bytes}` |
| `face:job:pdf:{session_id}:{lang}` | 1h | Job status for async Celery flow |
| `face:progress:{session_id}:{lang}` | 1h | Latest progress event (SSE/WS) |
| `face:lock:pdf:{analysis_id}:{lang}` | 1h | PDF build concurrency lock |
| `face:token:daily:{date}` | 48h | Global OpenAI USD spend |
| `face:token:user:{uid}:{date}` | 48h | Per-user spend |
| `face:ratelimit:{bucket}` | window | INCR counter (optional) |

## Files

| File | Role |
|------|------|
| `vedic/face_reading/redis_manager.py` | Singleton client, reconnect, stats |
| `vedic/face_reading/redis_codec.py` | JSON + numpy/datetime/bytes |
| `vedic/face_reading/face_cache.py` | Analysis, narration, PDF meta, tokens |
| `vedic/face_reading/session_cache.py` | Redis sessions + memory fallback |
| `vedic/face_reading/dedup_index.py` | Redis dedup + memory fallback |
| `vedic/face_reading/landmarks.py` | `landmark_set_from_dict()` for round-trip |

## API flow (unchanged URLs)

1. `POST /api/face_reading/extract` → `session_cache.put`
2. `POST /api/face_reading/analyze` → engines → `face_cache.put_analysis` + `session_cache.put`
3. `GET /api/face_reading/report.pdf` → PDF meta hit **or** narration hit **or** `assemble_report` → `put_pdf_meta`

## Failsafe

If `REDIS_URL` is down or `FACE_REDIS_ENABLED=0`:

- `session_cache` / `dedup_index` use in-process `OrderedDict` (same as before).
- Reports still generate; no crash.

## Local testing

```bash
cd artifacts/api-server
docker compose up -d redis
pip install redis
# .env: REDIS_URL=redis://localhost:6379/0
python flask_app.py
```

Verify Redis:

```bash
redis-cli KEYS "face:*"
redis-cli GET "face:session:<session_id>" | head -c 200
```

Check stats:

```bash
curl http://localhost:8080/api/face_reading/session/<session_id>
# → store_stats.redis
```

## Production

- Managed Redis (ElastiCache, Redis Cloud, Upstash) with TLS: `rediss://:password@host:6379/0`
- Set `FACE_REDIS_ENABLED=1` on all Gunicorn workers.
- Use **one shared Redis** — sessions work across workers.
- Do **not** store images in Redis long-term; front image key TTL = 2h by design.
- Scale workers horizontally; PDF cache hits avoid OpenAI + ReportLab when `face:pdf:*` exists.

## Migration from RAM-only

No DB migration required. Existing `FaceReadingLog` rows gain `analysis_id` on next analyze. Old sessions expire naturally; users re-run extract → analyze once after deploy.
