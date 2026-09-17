"""pgvector CRUD operations for log chunks."""
import logging
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.schemas import ChunkDTO

logger = logging.getLogger(__name__)


async def insert_log(
    db: AsyncSession,
    log_id: UUID,
    source: str,
    raw: str,
    byte_size: int,
) -> None:
    """Insert a log record."""
    await db.execute(
        text("""
            INSERT INTO logs (id, source, raw, byte_size)
            VALUES (:id, :source, :raw, :byte_size)
        """),
        {"id": log_id, "source": source, "raw": raw, "byte_size": byte_size},
    )


async def insert_chunks(
    db: AsyncSession,
    log_id: UUID,
    chunks: list[ChunkDTO],
) -> int:
    """Insert multiple log chunks with embeddings."""
    if not chunks:
        return 0

    for chunk in chunks:
        embedding_str = None
        if chunk.embedding:
            embedding_str = "[" + ",".join(str(x) for x in chunk.embedding) + "]"

        await db.execute(
            text("""
                INSERT INTO log_chunks (log_id, chunk_idx, line_start, line_end, text, embedding)
                VALUES (:log_id, :chunk_idx, :line_start, :line_end, :text, :embedding::vector)
            """),
            {
                "log_id": log_id,
                "chunk_idx": chunk.chunk_idx,
                "line_start": chunk.line_start,
                "line_end": chunk.line_end,
                "text": chunk.text,
                "embedding": embedding_str,
            },
        )

    return len(chunks)


async def insert_job(
    db: AsyncSession,
    job_id: UUID,
    log_id: UUID,
) -> None:
    """Insert an analysis job."""
    await db.execute(
        text("""
            INSERT INTO analysis_jobs (id, log_id, status)
            VALUES (:id, :log_id, 'pending')
        """),
        {"id": job_id, "log_id": log_id},
    )


async def get_job(db: AsyncSession, job_id: UUID) -> dict | None:
    """Get job by ID."""
    result = await db.execute(
        text("""
            SELECT id, log_id, status, summary, evidence, sample_entries, error,
                   created_at, finished_at
            FROM analysis_jobs
            WHERE id = :job_id
        """),
        {"job_id": job_id},
    )
    row = result.fetchone()

    if not row:
        return None

    return {
        "job_id": row.id,
        "log_id": row.log_id,
        "status": row.status,
        "summary": row.summary,
        "evidence": row.evidence,
        "sample_entries": row.sample_entries,
        "error": row.error,
        "created_at": row.created_at,
        "finished_at": row.finished_at,
    }


async def update_job(
    db: AsyncSession,
    job_id: UUID,
    status: str,
    summary: str | None = None,
    evidence: list | None = None,
    sample_entries: list | None = None,
    error: str | None = None,
) -> None:
    """Update job status and results."""
    import json

    await db.execute(
        text("""
            UPDATE analysis_jobs
            SET status = :status,
                summary = :summary,
                evidence = :evidence::jsonb,
                sample_entries = :sample_entries::jsonb,
                error = :error,
                finished_at = CASE WHEN :status IN ('done', 'failed') THEN NOW() ELSE finished_at END
            WHERE id = :job_id
        """),
        {
            "job_id": job_id,
            "status": status,
            "summary": summary,
            "evidence": json.dumps(evidence) if evidence else None,
            "sample_entries": json.dumps(sample_entries) if sample_entries else None,
            "error": error,
        },
    )


async def search_similar_chunks(
    db: AsyncSession,
    query_embedding: list[float],
    limit: int = 10,
    log_id: UUID | None = None,
    threshold: float | None = None,
) -> list[dict]:
    """Search for similar log chunks using cosine similarity."""
    threshold = threshold or settings.vector_similarity_threshold
    embedding_str = "[" + ",".join(str(x) for x in query_embedding) + "]"

    sql = """
        SELECT
            id,
            log_id,
            chunk_idx,
            text,
            line_start,
            line_end,
            1 - (embedding <=> :embedding::vector) as relevance_score
        FROM log_chunks
        WHERE embedding IS NOT NULL
    """

    params: dict = {"embedding": embedding_str, "limit": limit}

    if log_id:
        sql += " AND log_id = :log_id"
        params["log_id"] = log_id

    sql += """
        ORDER BY embedding <=> :embedding::vector
        LIMIT :limit
    """

    result = await db.execute(text(sql), params)
    rows = result.fetchall()

    return [
        {
            "chunk_id": row.id,
            "log_id": row.log_id,
            "chunk_idx": row.chunk_idx,
            "text": row.text,
            "line_start": row.line_start,
            "line_end": row.line_end,
            "relevance_score": float(row.relevance_score),
        }
        for row in rows
        if row.relevance_score >= threshold
    ]


async def get_recent_chunks(
    db: AsyncSession,
    limit: int = 10,
    cursor: str | None = None,
) -> tuple[list[dict], str | None]:
    """Get recent log chunks with cursor pagination."""
    sql = """
        SELECT id, log_id, chunk_idx, text, line_start, line_end, created_at
        FROM log_chunks
    """
    params: dict = {"limit": limit + 1}

    if cursor:
        sql += " WHERE created_at < :cursor"
        params["cursor"] = cursor

    sql += " ORDER BY created_at DESC LIMIT :limit"

    result = await db.execute(text(sql), params)
    rows = result.fetchall()

    items = [
        {
            "id": row.id,
            "log_id": row.log_id,
            "chunk_idx": row.chunk_idx,
            "text": row.text,
            "line_start": row.line_start,
            "line_end": row.line_end,
            "created_at": row.created_at,
        }
        for row in rows[:limit]
    ]

    next_cursor = None
    if len(rows) > limit:
        next_cursor = str(items[-1]["created_at"].isoformat())

    return items, next_cursor


async def get_chunks_count(db: AsyncSession) -> int:
    """Get total count of log chunks."""
    result = await db.execute(text("SELECT COUNT(*) FROM log_chunks"))
    return result.scalar() or 0


async def delete_log(db: AsyncSession, log_id: UUID) -> bool:
    """Delete a log and its associated chunks (cascades)."""
    result = await db.execute(
        text("DELETE FROM logs WHERE id = :log_id"),
        {"log_id": log_id},
    )
    return result.rowcount > 0
