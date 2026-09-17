"""Pydantic schemas - single source of truth for all request/response models."""
from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


# =============================================================================
# Response Envelope
# =============================================================================

class ResponseEnvelope(BaseModel):
    """Unified API response wrapper."""

    code: int = 0
    message: str = "success"
    data: Any = None
    request_id: str


class ErrorDetail(BaseModel):
    """Error detail for failed responses."""

    code: str
    message: str


# =============================================================================
# Log Upload
# =============================================================================

class LogUploadResponse(BaseModel):
    """Response for POST /logs/upload."""

    log_id: UUID
    job_id: UUID
    status: str = "pending"


# =============================================================================
# Job Status
# =============================================================================

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


# =============================================================================
# Log List
# =============================================================================

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
    total: int
    next_cursor: str | None = None


# =============================================================================
# Chat Query
# =============================================================================

class ChatQueryRequest(BaseModel):
    """Request for POST /chat/query."""

    query: str = Field(..., min_length=1, max_length=2000)
    model: str = Field(default="deepseek-chat", description="LLM model to use")
    context_limit: int = Field(default=10, ge=1, le=50)
    log_id: UUID | None = Field(default=None, description="Filter to specific log")


class EvidenceItem(BaseModel):
    """Single evidence item in chat response."""

    chunk_id: UUID
    text: str
    relevance_score: float
    line_start: int
    line_end: int


class ChatQueryResponse(BaseModel):
    """Response for POST /chat/query."""

    answer: str
    evidence: list[EvidenceItem]
    model_used: str


# =============================================================================
# Health Check
# =============================================================================

class HealthResponse(BaseModel):
    """Response for GET /health."""

    status: str
    db: str = "up"
    gateway: str = "unknown"


# =============================================================================
# Internal DTOs (not exposed via API)
# =============================================================================

class ChunkDTO(BaseModel):
    """Internal DTO for log chunk."""

    chunk_idx: int
    line_start: int
    line_end: int
    text: str
    embedding: list[float] | None = None


class LogMetadata(BaseModel):
    """Metadata extracted from log parsing."""

    source: str
    total_lines: int
    total_chunks: int
    byte_size: int
