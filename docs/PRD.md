# AI Log Analysis Platform - Product Requirements Document

> Version: 1.0 (MVP)  
> Last Updated: 2026-09-17  
> Status: Draft

---

## 1. Target Users & Core Scenarios

### 1.1 User Personas

| Persona | Role | Pain Point | Primary Goal |
|---------|------|------------|--------------|
| **SRE Engineer** | Site Reliability | Incident triage takes 30+ min to correlate logs across services | Reduce MTTR by quickly identifying root cause from logs |
| **Application Engineer** | Backend Developer | Debugging production issues requires manual log grep across multiple files | Find relevant error patterns without knowing exact search terms |
| **Security Engineer** | SecOps | Detecting anomalies in access logs requires writing complex regex rules | Surface suspicious patterns without predefined rules |

### 1.2 Core Scenarios

#### Scenario A: Incident Triage (SRE)
```
Trigger: Alert fires at 3 AM
Action:  Upload last hour's nginx + syslog
Query:   "What errors correlate with the spike at 02:45?"
Output:  3 related error clusters with evidence snippets
```

#### Scenario B: Production Debugging (App Engineer)
```
Trigger: User reports intermittent 500 errors
Action:  Upload application logs from affected timeframe
Query:   "Show me all 5xx errors and their stack traces"
Output:  Grouped errors with frequency and sample payloads
```

#### Scenario C: Security Anomaly Detection (Security Engineer)
```
Trigger: Weekly security review
Action:  Upload access logs for the week
Query:   "Any unusual access patterns or potential attacks?"
Output:  Flagged entries: brute force attempts, unusual user agents, geo anomalies
```

### 1.3 Usage Frequency

| User Type | Expected Usage | Session Duration |
|-----------|----------------|------------------|
| SRE | 2-5x per incident | 10-30 min |
| App Engineer | 3-10x per week | 5-15 min |
| Security Engineer | 1-2x per week | 30-60 min |

---

## 2. MVP Scope

### 2.1 In Scope

| ID | Feature | Description | API Endpoint |
|----|---------|-------------|--------------|
| F1 | **Log Upload** | Upload single file (Nginx/Apache/syslog), async processing | `POST /logs/upload` |
| F2 | **Job Status** | Poll processing status, view chunk/anomaly counts | `GET /logs/jobs/{id}` |
| F3 | **Log Browse** | List recent log chunks, filter by anomaly score | `GET /logs` |
| F4 | **NL Query** | Natural language question → LLM analysis with evidence | `POST /chat/query` |
| F5 | **Health Check** | Service availability check | `GET /health` |

### 2.2 Out of Scope (MVP)

| Feature | Reason | Future Consideration |
|---------|--------|----------------------|
| Multi-tenancy / User Auth | Training demo, single-user | v2 |
| Real-time log streaming | Complexity, requires different arch | v2 |
| Custom anomaly rules | MVP uses LLM judgment only | v2 |
| Log retention / deletion | Demo scope, no data lifecycle | v2 |
| Dashboard / Visualization | Focus on API + basic UI | v2 |
| Alert / Notification | Out of demo scope | v2 |
| Multi-file correlation | Single file per upload in MVP | v1.1 |
| Export / Report generation | Out of demo scope | v2 |

### 2.3 Constraints

| Constraint | Limit | Rationale |
|------------|-------|-----------|
| Max file size | 100 MB | Memory/processing time |
| Supported formats | nginx, apache, syslog | Common formats for demo |
| Chunk size | 50 lines | Balance context vs embedding |
| LLM rate limit | 10 req/min | Cost control |
| Vector dimension | 384 (fixed) | Embedding model output |
| **Language support** | **Chinese + English** | Logs and queries in both languages |

> **Note**: Chinese support requires multilingual embedding model. Current `bge-small-en` is English-only. Recommend switching to `BAAI/bge-m3` (1024-dim) or `intfloat/multilingual-e5-small` (384-dim). See CLAUDE.md for tech stack update.

---

## 3. Data Flow & Module Responsibilities

### 3.1 Data Flow Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              USER ACTIONS                                    │
└─────────────────────────────────────────────────────────────────────────────┘
        │                           │                           │
        │ Upload Log                │ Check Status              │ Ask Question
        ▼                           ▼                           ▼
┌───────────────┐          ┌───────────────┐          ┌───────────────┐
│ POST          │          │ GET           │          │ POST          │
│ /logs/upload  │          │ /logs/jobs/X  │          │ /chat/query   │
└───────┬───────┘          └───────┬───────┘          └───────┬───────┘
        │                           │                           │
        ▼                           ▼                           ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           api/ (FastAPI Routers)                             │
│  - Request validation (Pydantic)                                             │
│  - Response envelope wrapping                                                │
│  - Error code mapping                                                        │
└─────────────────────────────────────────────────────────────────────────────┘
        │                           │                           │
        ▼                           ▼                           ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         services/ (Business Logic)                           │
│  - log_parser: Format detection, chunking                                    │
│  - embedding: Local sentence-transformers (384-dim)                          │
│  - anomaly: Score calculation                                                │
│  - search: Vector similarity search                                          │
└─────────────────────────────────────────────────────────────────────────────┘
        │                                                       │
        │ Store chunks + embeddings                             │ Retrieve context
        ▼                                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                        Postgres 16 + pgvector                                │
│  - jobs table (status tracking)                                              │
│  - log_chunks table (content + embedding + anomaly_score)                    │
└─────────────────────────────────────────────────────────────────────────────┘
                                                                │
                                                                │ Context for LLM
                                                                ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                          agents/ (LLM Orchestration)                         │
│  - Prompt construction with retrieved evidence                               │
│  - Response parsing and evidence extraction                                  │
└─────────────────────────────────────────────────────────────────────────────┘
                                                                │
                                                                │ LLM call
                                                                ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         gateway/ (Envoy Client)                              │
│  - Unified interface to Envoy AI Gateway                                     │
│  - Model selection (deepseek/qwen/claude)                                    │
│  - Retry and timeout handling                                                │
└─────────────────────────────────────────────────────────────────────────────┘
                                                                │
                                                                ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                          Envoy AI Gateway                                    │
│  /api/deepseek/* → DeepSeek                                                  │
│  /api/qwen/*     → Qwen                                                      │
│  /api/vertex/*   → Vertex AI Claude                                          │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 3.2 Module Responsibilities

| Module | Responsibility | Dependencies |
|--------|----------------|--------------|
| `api/` | HTTP routing, validation, response formatting | Pydantic, services/ |
| `services/log_parser` | Format detection, line chunking, metadata extraction | None |
| `services/embedding` | Generate 384-dim vectors via sentence-transformers | torch, sentence-transformers |
| `services/anomaly` | Calculate anomaly scores (LLM-based or heuristic) | agents/ |
| `services/search` | Vector similarity search, result ranking | pgvector |
| `agents/` | Prompt engineering, LLM response parsing | gateway/ |
| `gateway/` | HTTP client for Envoy AI Gateway | httpx |
| `security/` | API key validation, rate limiting | None |

---

## 4. Acceptance Criteria

### 4.1 Log Upload (F1)

| ID | Criteria | Observable Indicator |
|----|----------|---------------------|
| AC1.1 | Upload 10MB nginx log completes within 5 seconds | API returns `job_id` in < 5s |
| AC1.2 | Unsupported format returns error code `LOG_001` | Response: `{"code": "LOG_001", ...}` |
| AC1.3 | File > 100MB returns error code `LOG_002` | Response: `{"code": "LOG_002", ...}` |
| AC1.4 | Job status is `pending` immediately after upload | `GET /logs/jobs/{id}` returns `status: "pending"` |

### 4.2 Job Status (F2)

| ID | Criteria | Observable Indicator |
|----|----------|---------------------|
| AC2.1 | Job status transitions: pending → processing → completed | Poll shows status progression |
| AC2.2 | Completed job shows `chunks_processed` count > 0 | `chunks_processed` field is integer > 0 |
| AC2.3 | Failed job shows error message | `status: "failed"`, `error` field non-null |
| AC2.4 | Non-existent job returns 404 with `LOG_003` | Response: HTTP 404, `{"code": "LOG_003"}` |

### 4.3 Log Browse (F3)

| ID | Criteria | Observable Indicator |
|----|----------|---------------------|
| AC3.1 | Default limit returns 20 items | `items` array length = 20 (if ≥20 exist) |
| AC3.2 | Results ordered by creation time descending | `items[0].created_at` > `items[1].created_at` |
| AC3.3 | Each item includes `anomaly_score` between 0 and 1 | All scores satisfy `0 <= score <= 1` |
| AC3.4 | Cursor pagination works for > 100 items | `next_cursor` non-null, subsequent call returns next page |

### 4.4 Natural Language Query (F4)

| ID | Criteria | Observable Indicator |
|----|----------|---------------------|
| AC4.1 | Query with uploaded logs returns answer within 30s | Response time < 30s |
| AC4.2 | Response includes `evidence` array with ≥1 item | `evidence` array length ≥ 1 |
| AC4.3 | Each evidence item has `relevance_score` ≥ 0.7 | All evidence scores ≥ 0.7 |
| AC4.4 | `model_used` field matches requested model | If request `model: "claude-opus-5"`, response shows same |
| AC4.5 | Rate limit exceeded returns `CHAT_002` | 11th request in 1 min returns `{"code": "CHAT_002"}` |
| AC4.6 | Query with no relevant logs returns empty evidence | `evidence: []`, `answer` explains no matches found |

### 4.5 Health Check (F5)

| ID | Criteria | Observable Indicator |
|----|----------|---------------------|
| AC5.1 | `/health` returns 200 when all dependencies up | HTTP 200, `{"status": "ok"}` |
| AC5.2 | `/health` returns 503 when DB unreachable | HTTP 503, `{"status": "degraded", "db": "down"}` |

### 4.6 Cross-Cutting

| ID | Criteria | Observable Indicator |
|----|----------|---------------------|
| AC6.1 | All responses include `request_id` | Every response has `request_id` field (UUID format) |
| AC6.2 | Invalid API key returns 401 | Missing/wrong `X-API-Key` header → HTTP 401 |
| AC6.3 | All errors follow envelope format | Error responses have `code`, `message`, `request_id` |

---

## 5. Risks & Open Questions

### 5.1 Technical Risks

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| **Vertex AI quota exhausted** | Cannot demo Claude model | High (已確認 quota=0) | Apply for quota increase; fallback to DeepSeek/Qwen |
| **Large log OOM** | Processing fails for big files | Medium | Streaming chunker; memory limit per job |
| **Embedding model download** | First run slow (download ~100MB model) | Low | Pre-download in Docker image |
| **LLM hallucination** | Incorrect anomaly attribution | Medium | Always show evidence; disclaimer in UI |

### 5.2 Product Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| **Demo too slow** | Poor training experience if query > 30s | Set expectation; show progress indicator |
| **Format detection fails** | User uploads unsupported log variant | Clear error message; manual format override option |
| **Query ambiguity** | User question too vague for useful answer | Suggest example queries; refine prompt |

### 5.3 Dependency Risks

| Dependency | Risk | Fallback |
|------------|------|----------|
| DeepSeek API | Service outage | Route to Qwen or Vertex AI |
| Qwen API | Service outage | Route to DeepSeek or Vertex AI |
| Vertex AI | Quota / outage | Route to DeepSeek or Qwen |
| sentence-transformers | Model download blocked | Pre-bundled model in image; hash fallback |

### 5.4 Confirmed Decisions

| # | Question | Decision | Confirmed |
|---|----------|----------|-----------|
| Q1 | Anomaly detection method | **LLM-based** (not heuristics) | 2026-09-17 |
| Q2 | Language support | **Chinese + English** (logs and queries) | 2026-09-17 |
| Q3 | Max concurrent jobs | **No limit** (demo scope) | 2026-09-17 |
| Q4 | Evidence line numbers | **No** (content snippet only) | 2026-09-17 |

---

## Appendix: Related Documents

- [CLAUDE.md](../CLAUDE.md) - Project constraints and tech stack
- [DESIGN.md](../DESIGN.md) - Architecture and API contracts
- [WORKFLOW.md](../WORKFLOW.md) - Development phase protocol
