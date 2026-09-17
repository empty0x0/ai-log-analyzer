"""Mock LLM server for local development and testing."""
import uuid
from fastapi import FastAPI, Request

app = FastAPI(title="Mock LLM Server")


@app.post("/v1/chat/completions")
async def chat_completions(request: Request):
    """OpenAI-compatible chat completions endpoint."""
    body = await request.json()
    model = body.get("model", "mock-model")
    messages = body.get("messages", [])

    last_message = messages[-1]["content"] if messages else "No message"

    return {
        "id": f"mock-{uuid.uuid4().hex[:8]}",
        "object": "chat.completion",
        "model": model,
        "choices": [
            {
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": f"[MOCK RESPONSE] Received: {last_message[:100]}..."
                },
                "finish_reason": "stop"
            }
        ],
        "usage": {
            "prompt_tokens": 10,
            "completion_tokens": 20,
            "total_tokens": 30
        }
    }


@app.post("/v1/projects/{project}/locations/{location}/publishers/{publisher}/models/{model}:rawPredict")
async def vertex_raw_predict(project: str, location: str, publisher: str, model: str, request: Request):
    """Vertex AI rawPredict endpoint mock."""
    body = await request.json()
    messages = body.get("messages", [])

    last_message = messages[-1]["content"] if messages else "No message"

    return {
        "id": f"mock-vertex-{uuid.uuid4().hex[:8]}",
        "type": "message",
        "role": "assistant",
        "content": [
            {
                "type": "text",
                "text": f"[MOCK VERTEX RESPONSE] Model: {model}, Received: {last_message[:100]}..."
            }
        ],
        "model": model,
        "stop_reason": "end_turn",
        "usage": {
            "input_tokens": 10,
            "output_tokens": 20
        }
    }


@app.get("/health")
async def health():
    return {"status": "ok", "mock": True}
