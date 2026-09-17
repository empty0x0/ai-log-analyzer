"""Chat query endpoint."""
import uuid

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas import ChatQueryRequest, ChatQueryResponse, ResponseEnvelope
from app.security.auth import verify_api_key
from app.security.rate_limit import check_rate_limit
from app.agents.analyzer import analyze_logs

router = APIRouter()


@router.post("/query", response_model=ResponseEnvelope)
async def chat_query(
    request: Request,
    body: ChatQueryRequest,
    db: AsyncSession = Depends(get_db),
    _: None = Depends(verify_api_key),
    __: None = Depends(check_rate_limit),
) -> ResponseEnvelope:
    """Natural language query over logs."""
    request_id = str(uuid.uuid4())

    result = await analyze_logs(
        db=db,
        query=body.query,
        model=body.model,
        context_limit=body.context_limit,
        log_id=body.log_id,
    )

    return ResponseEnvelope(
        code=0,
        message="success",
        data=ChatQueryResponse(**result).model_dump(),
        request_id=request_id,
    )
