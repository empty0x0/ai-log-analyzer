# AI Log Analysis Platform - Project Memory

## Identity
Training demo: Upload Nginx/Apache/syslog logs → AI anomaly summarization → Natural language query → Explainable evidence output.

## Tech Stack (Contract - Do Not Change)

| Component | Selection |
|-----------|-----------|
| Backend | Python 3.11 + FastAPI + Pydantic v2 |
| Frontend | Next.js 14 (App Router) + Tailwind |
| Vector DB | Postgres 16 + pgvector |
| LLM Access | Envoy AI Gateway → 3 upstreams (DeepSeek, Qwen, Vertex AI Claude) |
| Embedding | Local sentence-transformers (intfloat/multilingual-e5-small, 384-dim, **Chinese+English**), NOT through gateway |
| Orchestration | docker-compose v2 |

### LLM Gateway Architecture
- Single endpoint: `AI_GATEWAY_URL` (Envoy)
- Model routing by `model` parameter:
  - `deepseek-*` → DeepSeek upstream (API Key)
  - `qwen-*` → Qwen upstream (API Key)
  - `claude-*` → Vertex AI upstream (GCP ADC)
- Business code is provider-agnostic, only talks to Envoy

### Embedding (Exception to Gateway Rule)
- Model: `intfloat/multilingual-e5-small` (supports Chinese + English)
- Local embedding via sentence-transformers is NOT an external provider call
- Does NOT go through Envoy gateway
- Offline fallback: deterministic hash vector
- pgvector column: `vector(384)`

## Directory Convention

```
ai-log-analyzer/
├── backend/
│   ├── api/          # FastAPI routers
│   ├── services/     # Business logic
│   ├── agents/       # LLM agent orchestration
│   ├── security/     # Auth/authz
│   └── gateway/      # Envoy client wrapper
├── frontend/         # Next.js 14 App Router
├── infra/            # docker-compose, envoy.yaml
└── docs/             # Additional documentation
```

## Red Lines (Prohibited)

1. **DO NOT** modify `.env` files directly (use `.env.example` as template)
2. **DO NOT** directly call any external LLM SDK/API (must go through Envoy gateway)
3. **DO NOT** drop or delete database tables without explicit approval
4. **DO NOT** hardcode API keys or secrets in code
5. **DO NOT** use `eval()`/`exec()` on user input
6. **EXCEPTION**: Local embedding (sentence-transformers) is allowed without gateway

## Must Execute (Before Commit)

```bash
# Backend
cd backend && poetry run ruff check . && poetry run pytest

# Frontend
cd frontend && pnpm lint && pnpm test
```

## Commit Convention
- Use Conventional Commits: `feat:`, `fix:`, `docs:`, `refactor:`, `test:`, `chore:`
- Branch strategy: `main` protected, feature branch → PR → squash merge

## Related Docs
- [DESIGN.md](./DESIGN.md) - Architecture constraints
- [WORKFLOW.md](./WORKFLOW.md) - Phase protocol
- [README.md](./README.md) - Human entry point
