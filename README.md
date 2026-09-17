# AI Log Analysis Platform

Training demo: Upload server logs → AI-powered anomaly detection → Natural language queries → Explainable evidence.

## Tech Stack

| Layer | Technology |
|-------|------------|
| Frontend | Next.js 14 (App Router) + Tailwind |
| Backend | Python 3.11 + FastAPI + Pydantic v2 |
| Vector DB | Postgres 16 + pgvector |
| LLM Gateway | Envoy → DeepSeek / Qwen / Vertex AI Claude |
| Embedding | Local sentence-transformers (bge-small-en-v1.5, 384-dim) |

## Quick Start

```bash
# 1. Copy environment template
cp .env.example .env
# Edit .env with your API keys

# 2. Start services
docker-compose up -d

# 3. Access
# Frontend: http://localhost:3000
# Backend API: http://localhost:8000
# API Docs: http://localhost:8000/docs
```

## Project Structure

```
ai-log-analyzer/
├── CLAUDE.md          # Project memory (for Claude Code)
├── DESIGN.md          # Architecture constraints
├── WORKFLOW.md        # Development phase protocol
├── README.md          # This file
├── .env.example       # Environment template
│
├── backend/
│   ├── api/           # FastAPI routers
│   ├── services/      # Business logic
│   ├── agents/        # LLM agent orchestration
│   ├── security/      # Auth/authz
│   └── gateway/       # Envoy client wrapper
│
├── frontend/          # Next.js 14 App Router
│
├── infra/             # docker-compose, envoy.yaml
│
└── docs/              # Additional documentation
```

## Features

- **Log Upload**: Support for Nginx, Apache, and syslog formats
- **Anomaly Detection**: AI-powered analysis of log patterns
- **Natural Language Query**: Ask questions about your logs in plain English
- **Explainable Evidence**: See which log entries support each finding

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/logs/upload` | Upload log file (async) |
| GET | `/logs/jobs/{id}` | Check job status |
| GET | `/logs` | List recent log chunks |
| POST | `/chat/query` | Natural language query |
| GET | `/health` | Health check |

## Documentation

- [DESIGN.md](./DESIGN.md) - Architecture and API contracts
- [WORKFLOW.md](./WORKFLOW.md) - Development workflow phases
- [CLAUDE.md](./CLAUDE.md) - Project constraints for AI assistants

## License

Internal training demo - Not for production use.
