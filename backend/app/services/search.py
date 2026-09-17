"""Vector similarity search service."""
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.services.embedding import get_embedding


async def search_similar_chunks(
    db: AsyncSession,
    query: str,
    limit: int = 10,
    log_id: UUID | None = None,
    threshold: float | None = None,
) -> list[dict]:
    """Search for log chunks similar to query."""
    threshold = threshold or settings.vector_similarity_threshold
    query_embedding = await get_embedding(query)

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

    params = {"embedding": query_embedding, "limit": limit}

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
