# Queue Runner

The queue runner (`queue.py`) implements the serve-mode task processing loop.

**Source**: `src/proofmark/queue.py`

## Queue Table Schema

```sql
CREATE TABLE comparison_queue (
    task_id       SERIAL PRIMARY KEY,
    config_path   TEXT NOT NULL,
    lhs_path      TEXT NOT NULL,
    rhs_path      TEXT NOT NULL,
    job_key       TEXT,                -- optional grouping key
    date_key      DATE,               -- optional date key
    status        VARCHAR(20) NOT NULL DEFAULT 'Pending',
    result        VARCHAR(10),         -- 'PASS' or 'FAIL'
    started_at    TIMESTAMP,
    completed_at  TIMESTAMP,
    result_json   JSONB,               -- full comparison report
    error_message TEXT,
    created_at    TIMESTAMP DEFAULT NOW()
);
```

Indexes on `status` and `(job_key, date_key)`.

A reference DDL is in `sql/queue_schema.sql`. The table can also be created at runtime with `proofmark serve --init-db`.

## Task Lifecycle

```
Pending -> Running -> Succeeded
                   -> Failed
```

1. **Pending**: Inserted by an external process. The runner ignores it until a worker claims it.
2. **Running**: Claimed atomically by a worker via `UPDATE ... FOR UPDATE SKIP LOCKED`. `started_at` is set.
3. **Succeeded**: Comparison completed. `result` is set to `"PASS"` or `"FAIL"`, `result_json` holds the full report, `completed_at` is set.
4. **Failed**: Comparison threw an exception. `error_message` is set, `completed_at` is set. The original error type and message are preserved.

## Task Claiming

```sql
UPDATE comparison_queue
SET status = 'Running', started_at = NOW()
WHERE task_id = (
    SELECT task_id FROM comparison_queue
    WHERE status = 'Pending'
    ORDER BY task_id
    FOR UPDATE SKIP LOCKED
    LIMIT 1
)
RETURNING task_id, config_path, lhs_path, rhs_path;
```

- **FIFO order**: `ORDER BY task_id` ensures oldest task is claimed first.
- **SKIP LOCKED**: Multiple workers will never claim the same task. Each worker gets a different pending task or nothing.
- **Atomic**: The claim and status update happen in a single statement.

## Worker Loop

Each worker thread runs `worker_loop()` in an infinite loop:

1. Try to claim a task.
2. If no task: wait `poll_interval_seconds`, loop.
3. If task claimed:
   - Resolve path tokens (`{ETL_ROOT}`) via `PathSettings.resolve()`.
   - Run `pipeline.run()` with the resolved paths.
   - On success: `mark_succeeded()` stores the report.
   - On exception: `mark_failed()` stores the error message.
4. Immediately check for next task (no sleep between tasks).

Workers are daemon threads. They stop when the `stop_event` is set.

## Database Connections

Each worker thread opens one persistent psycopg2 connection at startup and uses it for all database operations (claim, mark succeeded, mark failed). If a connection error occurs mid-loop, the worker reconnects automatically. The connection is closed on worker shutdown.

## `{TOKEN}` Path Expansion

Queue task paths can contain tokens that are resolved at runtime:

| Token | Source | Example |
|---|---|---|
| `{ETL_ROOT}` | `ETL_ROOT` env var | `/media/dan/fdrive/codeprojects/MockEtlFrameworkPython` |

This allows the same queue rows to work across environments without changing paths.

**Example**: A task row might have:
```
config_path = {ETL_ROOT}/configs/daily_balances.yaml
lhs_path    = {ETL_ROOT}/output/daily_balances/
rhs_path    = {ETL_ROOT}/output/daily_balances/
```

With `ETL_ROOT=/media/dan/fdrive/codeprojects/MockEtlFrameworkPython`, these resolve to:
```
/media/dan/fdrive/codeprojects/MockEtlFrameworkPython/configs/daily_balances.yaml
/media/dan/fdrive/codeprojects/MockEtlFrameworkPython/output/daily_balances/
/media/dan/fdrive/codeprojects/MockEtlFrameworkPython/output/daily_balances/
```

Resolution is done by `PathSettings.resolve()`, which is passed to `worker_loop` as the `resolve_path` callable. Simple string replacement -- no validation of the resulting paths.

## Idle Shutdown

The `_ActivityTracker` monitors whether any worker is actively processing a task.

- When a worker claims a task: `task_started()` increments the active count.
- When a worker finishes a task: `task_ended()` decrements. If count reaches zero, records the timestamp.
- `idle_seconds()` returns time since all workers became idle. Returns 0.0 if any worker is active.

The main thread checks `idle_seconds()` every second. If it exceeds `idle_shutdown_seconds` (default 8 hours), the service shuts down cleanly.

This prevents the service from running indefinitely when there's no work. Useful when launched on-demand by an orchestrator that expects the service to self-terminate.

## Signal Handling

`serve()` installs handlers for `SIGINT` and `SIGTERM`. Either signal sets the `stop_event`, causing:
1. Workers to finish their current task (if any) and exit.
2. Main thread to join workers with a 30-second timeout.
3. Clean shutdown.

## Submitting Tasks

Insert rows into the queue table:

```sql
INSERT INTO comparison_queue (config_path, lhs_path, rhs_path, job_key, date_key)
VALUES (
  '{ETL_ROOT}/configs/daily_balances.yaml',
  '{ETL_ROOT}/output/daily_balances/',
  '{ETL_ROOT}/output/daily_balances/',
  'daily_balances',
  '2026-01-15'
);
```

## Checking Results

```sql
SELECT task_id, status, result, error_message
FROM comparison_queue
WHERE job_key = 'daily_balances' AND date_key = '2026-01-15';
```

The full JSON report is in `result_json` for succeeded tasks.
