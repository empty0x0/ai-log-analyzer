"""Pydantic models for API request/response."""
from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class ResponseEnvelope(BaseModel):
    """Unified response envelope."""

    code: int = 0
    message: str = "success"
    data: Any = None
    request_id: str


class LogUploadResponse(BaseModel):
    """Response for POST /logs/upload."""

    log_id: UUID
    job_id: UUID
    status: str = "pending"


class JobStatusResponse(BaseModel):
    """Response for GET /logs/jobs/{id}."""

    job_id: UUID
    log_id: UUID
    status: str
    summary: str | None = None
    evidence: list[dict] | None = None
    sample_entries: list[dict] | None = None
    error: str | None = None
    created_at: datetime
    finished_at: datetime | None = None


class LogChunkItem(BaseModel):
    """Single log chunk in list response."""

    id: UUID
    log_id: UUID
    chunk_idx: int
    text: str
    line_start: int
    line_end: int
    created_at: datetime


class LogListResponse(BaseModel):
    """Response for GET /logs."""

    items: list[LogChunkItem]
    next_cursor: str | None = None


class ChatQueryRequest(BaseModel):
    """Request for POST /chat/query."""

    query: str = Field(..., min_length=1, max_length=2000)
    model: str = "claude-opus-5"
    context_limit: int = Field(default=10, ge=1, le=50)
    log_id: UUID | None = None


class EvidenceItem(BaseModel):
    """Single evidence item in chat response."""

    chunk_id: UUID
    text: str
    relevance_score: float


class ChatQueryResponse(BaseModel):
    """Response for POST /chat/query."""

    answer: str
    evidence: list[EvidenceItem]
    model_used: str


class HealthResponse(BaseModel):
    """Response for GET /health."""

    status: str
    db: str = "up"
    gateway: str = "unknown"
