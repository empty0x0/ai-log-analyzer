"""Log parsing and chunking service."""
import uuid

from fastapi import UploadFile
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.services.embedding import get_embedding


async def detect_format(content: str) -> str:
    """Detect log format from content. Returns 'nginx', 'app', or 'custom'."""
    # TODO: Implement format detection heuristics
    return "custom"


def chunk_lines(lines: list[str], chunk_size: int, overlap: int) -> list[dict]:
    """Split lines into overlapping chunks."""
    chunks = []
    i = 0
    chunk_idx = 0

    while i < len(lines):
        end = min(i + chunk_size, len(lines))
        chunk_text = "\n".join(lines[i:end])
        chunks.append({
            "chunk_idx": chunk_idx,
            "line_start": i + 1,
            "line_end": end,
            "text": chunk_text,
        })
        chunk_idx += 1
        i += chunk_size - overlap

    return chunks


async def process_log_upload(
    db: AsyncSession,
    file: UploadFile,
    source: str,
) -> dict:
    """Process uploaded log file: store, chunk, embed."""
    content = await file.read()
    content_str = content.decode("utf-8", errors="replace")
    byte_size = len(content)

    # Insert log record
    log_id = uuid.uuid4()
    await db.execute(
        text("""
            INSERT INTO logs (id, source, raw, byte_size)
            VALUES (:id, :source, :raw, :byte_size)
        """),
        {"id": log_id, "source": source, "raw": content_str, "byte_size": byte_size},
    )

    # Create analysis job
    job_id = uuid.uuid4()
    await db.execute(
        text("""
            INSERT INTO analysis_jobs (id, log_id, status)
            VALUES (:id, :log_id, 'pending')
        """),
        {"id": job_id, "log_id": log_id},
    )

    await db.commit()

    # TODO: Trigger background task to chunk and embed
    # For now, process inline (blocking)
    lines = content_str.split("\n")
    chunks = chunk_lines(
        lines,
        settings.chunk_size_lines,
        settings.chunk_overlap_lines,
    )

    for chunk in chunks:
        embedding = await get_embedding(chunk["text"])
        await db.execute(
            text("""
                INSERT INTO log_chunks (log_id, chunk_idx, line_start, line_end, text, embedding)
                VALUES (:log_id, :chunk_idx, :line_start, :line_end, :text, :embedding)
            """),
            {
                "log_id": log_id,
                "chunk_idx": chunk["chunk_idx"],
                "line_start": chunk["line_start"],
                "line_end": chunk["line_end"],
                "text": chunk["text"],
                "embedding": embedding,
            },
        )

    await db.commit()

    return {"log_id": log_id, "job_id": job_id}
