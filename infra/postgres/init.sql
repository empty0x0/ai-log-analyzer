-- AI Log Analysis Platform - Database Initialization
-- Extensions
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- Table: logs
CREATE TABLE logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source TEXT CHECK (source IN ('nginx', 'app', 'custom')) NOT NULL,
    raw TEXT NOT NULL,
    byte_size INT NOT NULL,
    uploaded_at TIMESTAMPTZ DEFAULT NOW()
);

-- Table: log_chunks
CREATE TABLE log_chunks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    log_id UUID REFERENCES logs(id) ON DELETE CASCADE NOT NULL,
    chunk_idx INT NOT NULL,
    line_start INT NOT NULL,
    line_end INT NOT NULL,
    text TEXT NOT NULL,
    embedding vector(384),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (log_id, chunk_idx)
);

-- Index: ivfflat cosine similarity on embedding
CREATE INDEX idx_log_chunks_embedding ON log_chunks
    USING ivfflat (embedding vector_cosine_ops)
    WITH (lists = 100);

-- Table: analysis_jobs
CREATE TABLE analysis_jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    log_id UUID REFERENCES logs(id) ON DELETE CASCADE NOT NULL,
    status TEXT CHECK (status IN ('pending', 'running', 'done', 'failed')) DEFAULT 'pending',
    summary TEXT,
    evidence JSONB,
    sample_entries JSONB,
    error TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    finished_at TIMESTAMPTZ
);

-- Index: job status lookup
CREATE INDEX idx_analysis_jobs_status ON analysis_jobs (status);
CREATE INDEX idx_analysis_jobs_log_id ON analysis_jobs (log_id);
