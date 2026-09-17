# AI Log Analysis Platform - Architecture Design

## System Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                                  Client                                      │
└─────────────────────────────────────┬───────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         Next.js 14 (App Router)                              │
│                              + Tailwind                                      │
└─────────────────────────────────────┬───────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                      FastAPI Backend (Python 3.11)                           │
│  ┌─────────┐  ┌──────────┐  ┌────────┐  ┌──────────┐  ┌─────────┐          │
│  │   api/  │  │ services/│  │ agents/│  │ security/│  │ gateway/│          │
│  └─────────┘  └──────────┘  └────────┘  └──────────┘  └─────────┘          │
└───────┬─────────────────────────┬───────────────────────────┬───────────────┘
        │                         │                           │
        │ Embedding               │ Vector Search             │ LLM Calls
        │ (Local)                 │                           │
        ▼                         ▼                           ▼
┌───────────────┐    ┌─────────────────────┐    ┌─────────────────────────────┐
│ sentence-     │    │  Postgres 16        │    │     Envoy AI Gateway        │
│ transformers  │    │  + pgvector         │    │     (Model Router)          │
│ bge-small-en  │    │                     │    └──────────┬──────────────────┘
│ (384-dim)     │    │  ┌───────────────┐  │               │
└───────────────┘    │  │ log_chunks    │  │    ┌──────────┼──────────┐
                     │  │ .embedding    │  │    │          │          │
                     │  │ vector(384)   │  │    ▼          ▼          ▼
                     │  └───────────────┘  │  ┌─────┐  ┌──────┐  ┌─────────┐
                     └─────────────────────┘  │Deep │  │ Qwen │  │Vertex AI│
                                              │Seek │  │      │  │ Claude  │
                                              └─────┘  └──────┘  └─────────┘
```

## API Contract

### Response Envelope (Unified Format)

```json
{
  "code": 0,
  "message": "success",
  "data": { ... },
  "request_id": "uuid-v4"
}
```

### Error Codes

| HTTP Status | Business Code | Description |
|-------------|---------------|-------------|
| 400 | `LOG_001` | Unsupported file format |
| 400 | `LOG_002` | File size exceeds limit |
| 404 | `LOG_003` | Job not found |
| 422 | `CHAT_001` | Query too long |
| 429 | `CHAT_002` | Rate limit exceeded |
| 500 | `SYS_001` | Internal error |
| 503 | `LLM_001` | LLM gateway unavailable |

### Endpoints

| Method | Path | Description | Through Gateway |
|--------|------|-------------|-----------------|
| `POST` | `/logs/upload` | Upload log file → returns `job_id` (async) | No |
| `GET` | `/logs/jobs/{id}` | Get job status and result | No |
| `GET` | `/logs` | List recent logs (descending, paginated) | No |
| `POST` | `/chat/query` | Natural language query → LLM analysis | **Yes** |
| `GET` | `/health` | Health check | No |

#### POST /logs/upload

Request:
```
Content-Type: multipart/form-data
file: <binary>
format: nginx | apache | syslog (optional, auto-detect if omitted)
```

Response:
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "job_id": "uuid",
    "status": "pending"
  },
  "request_id": "uuid"
}
```

#### GET /logs/jobs/{id}

Response:
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "job_id": "uuid",
    "status": "pending | processing | completed | failed",
    "file_name": "access.log",
    "chunks_processed": 42,
    "anomalies_found": 3,
    "created_at": "ISO8601",
    "completed_at": "ISO8601 | null",
    "error": "string | null"
  },
  "request_id": "uuid"
}
```

#### GET /logs

Query params:
- `limit`: int (default 20, max 100)
- `cursor`: string (optional, for pagination)

Response:
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "items": [
      {
        "id": "uuid",
        "job_id": "uuid",
        "content": "log content snippet...",
        "anomaly_score": 0.85,
        "metadata": { "source": "nginx", "line_start": 100 }
      }
    ],
    "next_cursor": "string | null"
  },
  "request_id": "uuid"
}
```

#### POST /chat/query

Request:
```json
{
  "query": "What errors occurred in the last hour?",
  "model": "claude-opus-5",
  "context_limit": 10
}
```

Response:
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "answer": "Based on the logs, I found 3 critical errors...",
    "evidence": [
      {
        "chunk_id": "uuid",
        "content": "relevant log snippet",
        "relevance_score": 0.92
      }
    ],
    "model_used": "claude-opus-5"
  },
  "request_id": "uuid"
}
```

## Data Models

### jobs

| Column | Type | Description |
|--------|------|-------------|
| id | uuid | Primary key |
| status | enum | pending, processing, completed, failed |
| file_name | varchar(255) | Original file name |
| file_size | bigint | File size in bytes |
| format | varchar(20) | nginx, apache, syslog |
| chunks_count | int | Total chunks created |
| anomalies_count | int | Anomalies detected |
| error | text | Error message if failed |
| created_at | timestamptz | Job creation time |
| completed_at | timestamptz | Job completion time |

### log_chunks

| Column | Type | Description |
|--------|------|-------------|
| id | uuid | Primary key |
| job_id | uuid | Foreign key → jobs |
| content | text | Log content (chunked) |
| embedding | vector(384) | bge-small-en embedding |
| anomaly_score | float | 0.0 - 1.0, higher = more anomalous |
| metadata | jsonb | {source, line_start, line_end, timestamp_range} |
| created_at | timestamptz | Chunk creation time |

### Indexes

```sql
-- Vector similarity search (HNSW for small dataset)
CREATE INDEX idx_log_chunks_embedding ON log_chunks 
  USING hnsw (embedding vector_cosine_ops);

-- Job lookup
CREATE INDEX idx_log_chunks_job_id ON log_chunks (job_id);

-- Anomaly filtering
CREATE INDEX idx_log_chunks_anomaly ON log_chunks (anomaly_score DESC);
```

## Technical Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Async task queue | BackgroundTasks + jobs table | Lightweight for training demo |
| Chunk strategy | 50 lines per chunk, 10-line overlap | Balance context vs embedding quality |
| Vector index | HNSW | Better for small-medium datasets |
| Similarity threshold | ≥ 0.7 | Return only relevant results |
| Auth | API Key header (`X-API-Key`) | Simple for demo |
| Rate limit | 10 req/min for `/chat/query` | Protect LLM cost |

## Gateway Routing (Envoy)

```yaml
# Model name → upstream mapping
routes:
  - match: { prefix: "/v1/chat" }
    route:
      cluster: deepseek    # if model starts with "deepseek-"
      cluster: qwen        # if model starts with "qwen-"
      cluster: vertex-ai   # if model starts with "claude-"
```

Authentication per upstream:
- DeepSeek: `Authorization: Bearer ${DEEPSEEK_API_KEY}`
- Qwen: `Authorization: Bearer ${QWEN_API_KEY}`
- Vertex AI: `Authorization: Bearer ${GCP_ACCESS_TOKEN}` (via ADC)
