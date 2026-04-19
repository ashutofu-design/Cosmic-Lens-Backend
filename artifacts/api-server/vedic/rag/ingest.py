"""
Sprint 52 — RAG Ingest pipeline
Reads vedic/knowledge/*.md → chunks → embeds → upserts into knowledge_chunks.

Run as:
  cd artifacts/api-server && python -m vedic.rag.ingest
  cd artifacts/api-server && python -m vedic.rag.ingest --reset
"""
from __future__ import annotations
import os
import sys
import argparse
import psycopg2
from pathlib import Path

from .chunker import chunk_directory, Chunk
from .embedder import embed_batch, EMBED_DIMS

KNOWLEDGE_DIR = Path(__file__).parent.parent / "knowledge"

CREATE_SQL = f"""
CREATE EXTENSION IF NOT EXISTS vector;
CREATE TABLE IF NOT EXISTS knowledge_chunks (
    id          SERIAL PRIMARY KEY,
    source      TEXT NOT NULL,
    section     TEXT NOT NULL,
    chunk_idx   INT  NOT NULL,
    chunk_text  TEXT NOT NULL,
    embedding   VECTOR({EMBED_DIMS}),
    metadata    JSONB DEFAULT '{{}}'::jsonb,
    created_at  TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (source, chunk_idx)
);
CREATE INDEX IF NOT EXISTS idx_kc_source ON knowledge_chunks(source);
CREATE INDEX IF NOT EXISTS idx_kc_embedding
  ON knowledge_chunks USING ivfflat (embedding vector_cosine_ops)
  WITH (lists = 50);
"""


def _conn():
    return psycopg2.connect(os.environ["DATABASE_URL"])


def ensure_schema() -> None:
    with _conn() as c:
        c.autocommit = True
        with c.cursor() as cur:
            cur.execute(CREATE_SQL)
    print("[ingest] schema OK")


def reset_table() -> None:
    with _conn() as c:
        c.autocommit = True
        with c.cursor() as cur:
            cur.execute("DROP TABLE IF EXISTS knowledge_chunks CASCADE")
    print("[ingest] table dropped")


def upsert_chunks(chunks: list[Chunk]) -> int:
    if not chunks:
        return 0
    print(f"[ingest] embedding {len(chunks)} chunks via OpenAI...")
    vectors = embed_batch([c.text for c in chunks])
    print(f"[ingest] got {len(vectors)} embeddings; upserting...")

    sql = """
        INSERT INTO knowledge_chunks (source, section, chunk_idx, chunk_text, embedding)
        VALUES (%s, %s, %s, %s, %s::vector)
        ON CONFLICT (source, chunk_idx) DO UPDATE SET
            section = EXCLUDED.section,
            chunk_text = EXCLUDED.chunk_text,
            embedding = EXCLUDED.embedding
    """
    n = 0
    with _conn() as c:
        with c.cursor() as cur:
            for ch, vec in zip(chunks, vectors):
                vstr = "[" + ",".join(f"{x:.6f}" for x in vec) + "]"
                cur.execute(sql, (ch.source, ch.section, ch.chunk_idx, ch.text, vstr))
                n += 1
        c.commit()
    return n


def run(reset: bool = False) -> None:
    if reset:
        reset_table()
    ensure_schema()
    print(f"[ingest] reading {KNOWLEDGE_DIR}")
    chunks = chunk_directory(KNOWLEDGE_DIR)
    print(f"[ingest] {len(chunks)} chunks across {len({c.source for c in chunks})} sources")
    if not chunks:
        print("[ingest] no markdown found — add files to vedic/knowledge/")
        return
    n = upsert_chunks(chunks)
    print(f"[ingest] ✅ upserted {n} chunks into knowledge_chunks")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--reset", action="store_true", help="Drop & recreate table")
    args = ap.parse_args()
    run(reset=args.reset)
