"""API key authentication."""
from fastapi import HTTPException, Request

from app.config import settings


async def verify_api_key(request: Request) -> None:
    """Verify X-API-Key header."""
    api_key = request.headers.get(settings.api_key_header)

    if not api_key:
        raise HTTPException(
            status_code=401,
            detail="Missing API key",
        )

    if api_key != settings.api_key_secret:
        raise HTTPException(
            status_code=401,
            detail="Invalid API key",
        )
