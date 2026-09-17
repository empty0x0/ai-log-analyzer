"""Health check endpoint."""
from fastapi import APIRouter
from sqlalchemy import text

from app.database import async_session_maker
from app.models import HealthResponse

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Check service health."""
    db_status = "up"

    try:
        async with async_session_maker() as session:
            await session.execute(text("SELECT 1"))
    except Exception:
        db_status = "down"

    status = "ok" if db_status == "up" else "degraded"

    return HealthResponse(status=status, db=db_status)
