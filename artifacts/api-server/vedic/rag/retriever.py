"""
Sprint 52 — RAG Retriever
Top-k semantic search over knowledge_chunks via pgvector cosine distance.

Public API:
  retrieve(query, k=5, source_filter=None) -> list of dict chunks
  format_for_prompt(chunks) -> str (ready to inject into system prompt)
"""
from __future__ import annotations
import os
import psycopg2
from psycopg2.extras import RealDictCursor
from .embedder import embed_one


def _conn():
    url = os.environ.get("DATABASE_URL")
    if not url:
        raise RuntimeError("DATABASE_URL not set")
    return psycopg2.connect(url)


def retrieve(query: str, k: int = 5,
             source_filter: str | None = None) -> list[dict]:
    """Return top-k most-similar knowledge chunks for `query`."""
    if not query or not query.strip():
        return []
    qv = embed_one(query)
    qv_str = "[" + ",".join(f"{x:.6f}" for x in qv) + "]"

    sql = """
        SELECT id, source, section, chunk_text,
               1 - (embedding <=> %s::vector) AS similarity
        FROM knowledge_chunks
    """
    params: list = [qv_str]
    if source_filter:
        sql += " WHERE source = %s"
        params.append(source_filter)
    sql += " ORDER BY embedding <=> %s::vector LIMIT %s"
    params.extend([qv_str, k])

    try:
        with _conn() as c, c.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(sql, params)
            return [dict(r) for r in cur.fetchall()]
    except Exception as exc:  # noqa: BLE001
        print(f"[retriever] query failed: {exc}")
        return []


def format_for_prompt(chunks: list[dict],
                      max_chars: int = 4000) -> str:
    """Pack retrieved chunks into a compact system-prompt block."""
    if not chunks:
        return ""
    lines = ["▸ CLASSICAL KNOWLEDGE (RAG-retrieved, use as background reasoning ONLY — never cite as timing fact):"]
    used = 0
    for i, ch in enumerate(chunks, 1):
        body = (ch.get("chunk_text") or "").strip()
        section = ch.get("section") or "?"
        source = ch.get("source") or "?"
        sim = ch.get("similarity") or 0.0
        block = f"  [{i}] {source} » {section}  (sim={sim:.2f})\n      {body}"
        if used + len(block) > max_chars:
            break
        lines.append(block)
        used += len(block)
    lines.append("  ⚐ Use this knowledge to REASON about the chart — NEVER as a source of dates/timing. Timing comes ONLY from the engine block above.")
    return "\n".join(lines)


def retrieve_and_format(query: str, k: int = 5,
                        source_filter: str | None = None,
                        max_chars: int = 4000) -> str:
    return format_for_prompt(retrieve(query, k, source_filter), max_chars=max_chars)
