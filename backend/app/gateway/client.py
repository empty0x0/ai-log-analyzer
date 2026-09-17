"""Envoy AI Gateway HTTP client."""
import httpx

from app.config import settings


def _get_gateway_path(model: str) -> str:
    """Determine gateway path based on model name."""
    if model.startswith("deepseek"):
        return "/api/deepseek/chat/completions"
    elif model.startswith("qwen"):
        return "/api/qwen/chat/completions"
    elif model.startswith("claude"):
        return f"/api/vertex/{model}:rawPredict"
    else:
        return "/api/deepseek/chat/completions"


def _build_request_body(model: str, system_prompt: str, user_prompt: str) -> dict:
    """Build request body based on model type."""
    if model.startswith("claude"):
        return {
            "anthropic_version": "vertex-2023-10-16",
            "max_tokens": 4096,
            "system": system_prompt,
            "messages": [{"role": "user", "content": user_prompt}],
        }
    else:
        return {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "max_tokens": 4096,
        }


def _extract_response_text(model: str, response: dict) -> str:
    """Extract text from response based on model type."""
    if model.startswith("claude"):
        content = response.get("content", [])
        if content and isinstance(content, list):
            return content[0].get("text", "")
        return ""
    else:
        choices = response.get("choices", [])
        if choices:
            return choices[0].get("message", {}).get("content", "")
        return ""


async def call_llm(
    model: str,
    system_prompt: str,
    user_prompt: str,
    timeout: float = 120.0,
) -> str:
    """Call LLM via Envoy AI Gateway."""
    path = _get_gateway_path(model)
    url = f"{settings.ai_gateway_url}{path}"
    body = _build_request_body(model, system_prompt, user_prompt)

    async with httpx.AsyncClient(timeout=timeout) as client:
        response = await client.post(url, json=body)
        response.raise_for_status()
        data = response.json()

    return _extract_response_text(model, data)
