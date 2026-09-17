"""Rate limiting for expensive endpoints."""
import time
from collections import defaultdict

from fastapi import HTTPException, Request

from app.config import settings

_request_counts: dict[str, list[float]] = defaultdict(list)


async def check_rate_limit(request: Request) -> None:
    """Check rate limit for /chat/query endpoint."""
    client_ip = request.client.host if request.client else "unknown"
    now = time.time()
    window = 60.0

    # Clean old entries
    _request_counts[client_ip] = [
        ts for ts in _request_counts[client_ip] if now - ts < window
    ]

    # Check limit
    if len(_request_counts[client_ip]) >= settings.rate_limit_chat_per_min:
        raise HTTPException(
            status_code=429,
            detail="Rate limit exceeded",
        )

    # Record request
    _request_counts[client_ip].append(now)
