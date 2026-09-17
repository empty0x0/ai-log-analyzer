"""Analysis job management service."""
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


async def get_job_status(db: AsyncSession, job_id: UUID) -> dict | None:
    """Get job status and results."""
    result = await db.execute(
        text("""
            SELECT
                id as job_id,
                log_id,
                status,
                summary,
                evidence,
                sample_entries,
                error,
                created_at,
                finished_at
            FROM analysis_jobs
            WHERE id = :job_id
        """),
        {"job_id": job_id},
    )
    row = result.fetchone()

    if not row:
        return None

    return {
        "job_id": row.job_id,
        "log_id": row.log_id,
        "status": row.status,
        "summary": row.summary,
        "evidence": row.evidence,
        "sample_entries": row.sample_entries,
        "error": row.error,
        "created_at": row.created_at,
        "finished_at": row.finished_at,
    }


async def update_job_status(
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
            SET
                status = :status,
                summary = :summary,
                evidence = :evidence,
                sample_entries = :sample_entries,
                error = :error,
                finished_at = CASE WHEN :status IN ('done', 'failed') THEN NOW() ELSE NULL END
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
    await db.commit()
