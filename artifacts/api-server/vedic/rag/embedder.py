"""
Sprint 52 — RAG Embedder
Wraps OpenAI's text-embedding-3-small (1536-dim) for chunk + query embedding.

Uses the same OPENAI_API_KEY env-var as the rest of the app.
"""
from __future__ import annotations
import os
import time
from typing import Iterable

EMBED_MODEL = "text-embedding-3-small"  # 1536 dims, cheap, accurate
EMBED_DIMS  = 1536
BATCH_SIZE  = 96   # OpenAI allows ~2048 inputs/req; 96 keeps payload <8000 tokens


def _client():
    from openai import OpenAI  # type: ignore
    key = os.environ.get("OPENAI_API_KEY")
    if not key:
        raise RuntimeError("OPENAI_API_KEY not set")
    return OpenAI(api_key=key)


def embed_one(text: str) -> list[float]:
    """Embed a single string (e.g. user query)."""
    if not text or not text.strip():
        return [0.0] * EMBED_DIMS
    cl = _client()
    r = cl.embeddings.create(model=EMBED_MODEL, input=text[:8000])
    return r.data[0].embedding


def embed_batch(texts: list[str]) -> list[list[float]]:
    """Embed a list of strings, batched. Retries on transient errors."""
    if not texts:
        return []
    cl = _client()
    out: list[list[float]] = []
    for i in range(0, len(texts), BATCH_SIZE):
        batch = [t[:8000] for t in texts[i:i + BATCH_SIZE]]
        for attempt in range(3):
            try:
                r = cl.embeddings.create(model=EMBED_MODEL, input=batch)
                out.extend(d.embedding for d in r.data)
                break
            except Exception as exc:  # noqa: BLE001
                if attempt == 2:
                    raise RuntimeError(f"embed_batch failed after 3 retries: {exc}") from exc
                time.sleep(1.5 * (attempt + 1))
    return out
