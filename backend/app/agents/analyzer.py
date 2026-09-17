"""Log analysis agent using LLM."""
import logging
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.prompts import ANALYSIS_PROMPT_TEMPLATE, SYSTEM_PROMPT
from app.gateway.client import call_llm
from app.schemas import EvidenceItem
from app.services import vector_store
from app.services.embedding import get_embedding

logger = logging.getLogger(__name__)


async def analyze_logs(
    db: AsyncSession,
    query: str,
    model: str,
    context_limit: int = 10,
    log_id: UUID | None = None,
) -> dict:
    """Analyze logs using LLM based on natural language query."""
    query_embedding = await get_embedding(query)

    chunks = await vector_store.search_similar_chunks(
        db=db,
        query_embedding=query_embedding,
        limit=context_limit,
        log_id=log_id,
    )

    if not chunks:
        return {
            "answer": "No relevant log entries found for your query.",
            "evidence": [],
            "model_used": model,
        }

    context_parts = []
    for i, chunk in enumerate(chunks, 1):
        context_parts.append(
            f"[Entry {i}] Lines {chunk['line_start']}-{chunk['line_end']}:\n{chunk['text']}"
        )
    context = "\n\n".join(context_parts)

    user_prompt = ANALYSIS_PROMPT_TEMPLATE.format(context=context, query=query)

    try:
        response = await call_llm(
            model=model,
            system_prompt=SYSTEM_PROMPT,
            user_prompt=user_prompt,
        )
    except Exception as e:
        logger.error(f"LLM call failed: {e}")
        response = f"Analysis failed: Unable to connect to LLM gateway. Error: {str(e)}"

    evidence = [
        EvidenceItem(
            chunk_id=chunk["chunk_id"],
            text=chunk["text"][:500],
            relevance_score=chunk["relevance_score"],
            line_start=chunk["line_start"],
            line_end=chunk["line_end"],
        ).model_dump()
        for chunk in chunks
    ]

    return {
        "answer": response,
        "evidence": evidence,
        "model_used": model,
    }


async def run_analysis_job(
    db: AsyncSession,
    job_id: UUID,
    log_id: UUID,
) -> None:
    """Run async analysis job on uploaded log."""
    try:
        await vector_store.update_job(db, job_id, status="running")
        await db.commit()

        query_embedding = await get_embedding("anomalies errors warnings exceptions")

        chunks = await vector_store.search_similar_chunks(
            db=db,
            query_embedding=query_embedding,
            limit=20,
            log_id=log_id,
            threshold=0.3,
        )

        if not chunks:
            await vector_store.update_job(
                db, job_id,
                status="done",
                summary="No significant anomalies detected.",
                evidence=[],
                sample_entries=[],
            )
            await db.commit()
            return

        context_parts = []
        for i, chunk in enumerate(chunks[:10], 1):
            context_parts.append(f"[{i}] {chunk['text'][:300]}")
        context = "\n\n".join(context_parts)

        prompt = f"""Analyze these log entries and provide:
1. A brief summary of any anomalies or issues found
2. Severity assessment (low/medium/high/critical)
3. Recommended actions if any

Log entries:
{context}"""

        try:
            summary = await call_llm(
                model="deepseek-chat",
                system_prompt=SYSTEM_PROMPT,
                user_prompt=prompt,
            )
        except Exception as e:
            summary = f"Analysis completed with {len(chunks)} potential anomalies found. (LLM unavailable: {e})"

        evidence = [
            {
                "chunk_id": str(c["chunk_id"]),
                "text": c["text"][:200],
                "score": c["relevance_score"],
            }
            for c in chunks[:5]
        ]

        sample_entries = [
            {"line_start": c["line_start"], "line_end": c["line_end"], "preview": c["text"][:100]}
            for c in chunks[:3]
        ]

        await vector_store.update_job(
            db, job_id,
            status="done",
            summary=summary,
            evidence=evidence,
            sample_entries=sample_entries,
        )
        await db.commit()

    except Exception as e:
        logger.exception(f"Analysis job {job_id} failed")
        await vector_store.update_job(db, job_id, status="failed", error=str(e))
        await db.commit()
