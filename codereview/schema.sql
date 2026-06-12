CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS chunks (
  id          BIGSERIAL PRIMARY KEY,
  source_type TEXT NOT NULL CHECK (source_type IN ('code','style','pr_comment')),
  path        TEXT NOT NULL DEFAULT '',
  start_line  INT,
  end_line    INT,
  content     TEXT NOT NULL,
  embedding   vector(1024) NOT NULL,
  commit_sha  TEXT,
  indexed_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS chunks_embedding_idx ON chunks USING hnsw (embedding vector_cosine_ops);
CREATE INDEX IF NOT EXISTS chunks_path_idx ON chunks (path);

CREATE TABLE IF NOT EXISTS reviews (
  id              BIGSERIAL PRIMARY KEY,
  repo            TEXT NOT NULL,
  pr_number       INT  NOT NULL,
  head_sha        TEXT NOT NULL,
  status          TEXT NOT NULL CHECK (status IN
                    ('queued','running','completed','skipped','failed','cost_exceeded')),
  trigger         TEXT NOT NULL DEFAULT 'webhook',
  model           TEXT,
  findings_total  INT DEFAULT 0,
  comments_posted INT DEFAULT 0,
  input_tokens    INT DEFAULT 0,
  output_tokens   INT DEFAULT 0,
  cost_usd        NUMERIC(8,4) DEFAULT 0,
  duration_ms     INT,
  error           TEXT,
  created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
  completed_at    TIMESTAMPTZ
);
CREATE INDEX IF NOT EXISTS reviews_lookup_idx ON reviews (repo, pr_number, head_sha);

CREATE TABLE IF NOT EXISTS index_state (
  repo             TEXT PRIMARY KEY,
  last_indexed_sha TEXT NOT NULL,
  indexed_at       TIMESTAMPTZ NOT NULL DEFAULT now()
);
