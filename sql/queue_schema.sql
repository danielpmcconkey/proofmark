-- Proofmark comparison queue table.
-- Run this against your PostgreSQL database, or use `proofmark serve --init-db`.

CREATE TABLE IF NOT EXISTS comparison_queue (
    task_id       SERIAL PRIMARY KEY,
    config_path   TEXT NOT NULL,
    lhs_path      TEXT NOT NULL,
    rhs_path      TEXT NOT NULL,
    job_key       TEXT,                -- optional grouping key for agent queries
    date_key      DATE,                -- optional date key for agent queries
    status        VARCHAR(20) NOT NULL DEFAULT 'Pending',
    result        VARCHAR(10),         -- 'PASS' or 'FAIL' (extracted from report)
    started_at    TIMESTAMP,
    completed_at  TIMESTAMP,
    result_json   JSONB,               -- full comparison report
    error_message TEXT,
    created_at    TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_comparison_queue_status
    ON comparison_queue (status);

CREATE INDEX IF NOT EXISTS idx_comparison_queue_keys
    ON comparison_queue (job_key, date_key);

-- Submit a task:
--   INSERT INTO comparison_queue (config_path, lhs_path, rhs_path, job_key, date_key)
--   VALUES ('/path/to/config.yaml', '/path/to/lhs', '/path/to/rhs', 'my_job', '2026-01-15');
--
-- Check results:
--   SELECT task_id, status, result FROM comparison_queue
--   WHERE job_key = 'my_job' AND date_key = '2026-01-15';
