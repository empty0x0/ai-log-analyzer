"""Log analysis agent."""
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.prompts import ANALYSIS_PROMPT_TEMPLATE, SYSTEM_PROMPT
from app.gateway.client import call_llm
from app.services.search import search_similar_chunks


async def analyze_logs(
    db: AsyncSession,
    query: str,
    model: str,
    context_limit: int = 10,
    log_id: UUID | None = None,
) -> dict:
    """Analyze logs using LLM based on natural language query."""
    # Search for relevant chunks
    chunks = await search_similar_chunks(
        db=db,
        query=query,
        limit=context_limit,
        log_id=log_id,
    )

    if not chunks:
        return {
            "answer": "No relevant log entries found for your query.",
            "evidence": [],
            "model_used": model,
        }

    # Build context from chunks
    context_parts = []
    for i, chunk in enumerate(chunks, 1):
        context_parts.append(
            f"[Entry {i}] Lines {chunk['line_start']}-{chunk['line_end']}:\n{chunk['text']}"
        )
    context = "\n\n".join(context_parts)

    # Build prompt
    user_prompt = ANALYSIS_PROMPT_TEMPLATE.format(context=context, query=query)

    # Call LLM via gateway
    response = await call_llm(
        model=model,
        system_prompt=SYSTEM_PROMPT,
        user_prompt=user_prompt,
    )

    # Build evidence list
    evidence = [
        {
            "chunk_id": chunk["chunk_id"],
            "text": chunk["text"][:500],
            "relevance_score": chunk["relevance_score"],
        }
        for chunk in chunks
    ]

    return {
        "answer": response,
        "evidence": evidence,
        "model_used": model,
    }
