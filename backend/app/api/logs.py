"""Log upload and retrieval endpoints."""
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import (
    JobStatusResponse,
    LogListResponse,
    LogUploadResponse,
    ResponseEnvelope,
)
from app.security.auth import verify_api_key
from app.services.job import get_job_status
from app.services.log_parser import process_log_upload

router = APIRouter()


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

    if source not in ("nginx", "app", "custom"):
        raise HTTPException(status_code=400, detail="Invalid source type")

    result = await process_log_upload(db, file, source)

    return ResponseEnvelope(
        code=0,
        message="success",
        data=LogUploadResponse(
            log_id=result["log_id"],
            job_id=result["job_id"],
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

    job = await get_job_status(db, job_id)
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
    limit: int = 20,
    cursor: str | None = None,
    db: AsyncSession = Depends(get_db),
    _: None = Depends(verify_api_key),
) -> ResponseEnvelope:
    """List log chunks with pagination."""
    request_id = str(uuid.uuid4())

    # TODO: Implement pagination logic in services/search.py
    items: list = []
    next_cursor = None

    return ResponseEnvelope(
        code=0,
        message="success",
        data=LogListResponse(items=items, next_cursor=next_cursor).model_dump(),
        request_id=request_id,
    )
