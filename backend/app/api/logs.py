"""Log upload and retrieval endpoints."""
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas import (
    JobStatusResponse,
    LogChunkItem,
    LogListResponse,
    LogUploadResponse,
    ResponseEnvelope,
)
from app.security.auth import verify_api_key
from app.services import vector_store
from app.services.embedding import get_embeddings_batch
from app.services.log_parser import parse_log_content, validate_source

router = APIRouter()

MAX_FILE_SIZE = 100 * 1024 * 1024


@router.post("/upload", response_model=ResponseEnvelope)
async def upload_log(
    request: Request,
    file: Annotated[UploadFile, File()],
    source: Annotated[str, Form()] = "custom",
    db: AsyncSession = Depends(get_db),
    _: None = Depends(verify_api_key),
) -> ResponseEnvelope:
    """Upload a log file for analysis."""
    request_id = str(uuid.uuid4())

    try:
        source = validate_source(source)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid source type")

    content = await file.read()

    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail="File too large")

    content_str = content.decode("utf-8", errors="replace")
    metadata, chunks = parse_log_content(content_str, source)

    log_id = uuid.uuid4()
    job_id = uuid.uuid4()

    await vector_store.insert_log(db, log_id, source, content_str, metadata.byte_size)
    await vector_store.insert_job(db, job_id, log_id)

    if chunks:
        texts = [c.text for c in chunks]
        embeddings = await get_embeddings_batch(texts)
        for chunk, emb in zip(chunks, embeddings):
            chunk.embedding = emb
        await vector_store.insert_chunks(db, log_id, chunks)

    await db.commit()

    return ResponseEnvelope(
        code=0,
        message="success",
        data=LogUploadResponse(
            log_id=log_id,
            job_id=job_id,
            status="pending",
        ).model_dump(),
        request_id=request_id,
    )


@router.get("/jobs/{job_id}", response_model=ResponseEnvelope)
async def get_job(
    request: Request,
    job_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _: None = Depends(verify_api_key),
) -> ResponseEnvelope:
    """Get analysis job status."""
    request_id = str(uuid.uuid4())

    job = await vector_store.get_job(db, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    return ResponseEnvelope(
        code=0,
        message="success",
        data=JobStatusResponse(**job).model_dump(),
        request_id=request_id,
    )


@router.get("", response_model=ResponseEnvelope)
async def list_logs(
    request: Request,
    limit: int = 10,
    cursor: str | None = None,
    db: AsyncSession = Depends(get_db),
    _: None = Depends(verify_api_key),
) -> ResponseEnvelope:
    """List recent log chunks (default 10)."""
    request_id = str(uuid.uuid4())

    if limit > 100:
        limit = 100

    items, next_cursor = await vector_store.get_recent_chunks(db, limit, cursor)
    total = await vector_store.get_chunks_count(db)

    chunk_items = [LogChunkItem(**item) for item in items]

    return ResponseEnvelope(
        code=0,
        message="success",
        data=LogListResponse(
            items=chunk_items,
            total=total,
            next_cursor=next_cursor,
        ).model_dump(),
        request_id=request_id,
    )
