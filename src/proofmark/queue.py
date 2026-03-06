"""PostgreSQL-backed comparison queue runner."""

import json
import logging
import signal
import threading
import time
from pathlib import Path

from proofmark.pipeline import run
from proofmark.report import serialize_report

logger = logging.getLogger("proofmark.queue")

INIT_SQL = """
CREATE TABLE IF NOT EXISTS {table} (
    task_id SERIAL PRIMARY KEY,
    config_path TEXT NOT NULL,
    lhs_path TEXT NOT NULL,
    rhs_path TEXT NOT NULL,
    job_key TEXT,
    date_key DATE,
    status VARCHAR(20) NOT NULL DEFAULT 'Pending',
    result VARCHAR(10),
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    result_json JSONB,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_{safe}_status ON {table} (status);
CREATE INDEX IF NOT EXISTS idx_{safe}_keys ON {table} (job_key, date_key);
"""


def _connect(dsn):
    import psycopg2
    return psycopg2.connect(dsn)


def init_db(dsn, table):
    """Create the queue table if it doesn't exist."""
    safe = table.replace(".", "_")
    sql = INIT_SQL.format(table=table, safe=safe)
    conn = _connect(dsn)
    try:
        with conn.cursor() as cur:
            cur.execute(sql)
        conn.commit()
        logger.info("Table %s ready", table)
    finally:
        conn.close()


def claim_task(dsn, table):
    """Claim the next pending task atomically. Returns dict or None."""
    sql = f"""
    UPDATE {table}
    SET status = 'Running', started_at = NOW()
    WHERE task_id = (
        SELECT task_id FROM {table}
        WHERE status = 'Pending'
        ORDER BY task_id
        FOR UPDATE SKIP LOCKED
        LIMIT 1
    )
    RETURNING task_id, config_path, lhs_path, rhs_path;
    """
    conn = _connect(dsn)
    try:
        with conn.cursor() as cur:
            cur.execute(sql)
            row = cur.fetchone()
            conn.commit()
            if row:
                return {
                    "task_id": row[0],
                    "config_path": row[1],
                    "lhs_path": row[2],
                    "rhs_path": row[3],
                }
        return None
    finally:
        conn.close()


def mark_succeeded(dsn, table, task_id, report):
    """Mark a task as Succeeded and store the report."""
    result = report.get("summary", {}).get("result", "UNKNOWN")
    report_json = json.dumps(report)
    sql = f"""
    UPDATE {table}
    SET status = 'Succeeded', completed_at = NOW(),
        result = %s, result_json = %s
    WHERE task_id = %s;
    """
    conn = _connect(dsn)
    try:
        with conn.cursor() as cur:
            cur.execute(sql, (result, report_json, task_id))
        conn.commit()
    finally:
        conn.close()


def mark_failed(dsn, table, task_id, error_msg):
    """Mark a task as Failed with an error message."""
    sql = f"""
    UPDATE {table}
    SET status = 'Failed', completed_at = NOW(), error_message = %s
    WHERE task_id = %s;
    """
    conn = _connect(dsn)
    try:
        with conn.cursor() as cur:
            cur.execute(sql, (error_msg, task_id))
        conn.commit()
    finally:
        conn.close()


def worker_loop(worker_id, dsn, table, poll_interval, stop_event):
    """Worker loop: claim tasks, run comparisons, write results."""
    label = f"worker-{worker_id}"
    logger.info("[%s] started", label)

    while not stop_event.is_set():
        task = None
        try:
            task = claim_task(dsn, table)
        except Exception:
            logger.exception("[%s] error claiming task", label)
            stop_event.wait(poll_interval)
            continue

        if task is None:
            stop_event.wait(poll_interval)
            continue

        task_id = task["task_id"]
        logger.info("[%s] claimed task %d", label, task_id)

        try:
            report = run(
                Path(task["config_path"]),
                Path(task["lhs_path"]),
                Path(task["rhs_path"]),
            )
            mark_succeeded(dsn, table, task_id, report)
            result = report.get("summary", {}).get("result", "?")
            logger.info("[%s] task %d completed: %s", label, task_id, result)
        except Exception as e:
            error_msg = f"{type(e).__name__}: {e}"
            logger.error("[%s] task %d failed: %s", label, task_id, error_msg)
            try:
                mark_failed(dsn, table, task_id, error_msg)
            except Exception:
                logger.exception(
                    "[%s] failed to write error for task %d", label, task_id
                )

        # No sleep between tasks — immediately check for next one


def serve(dsn, table="comparison_queue", workers=5, poll_interval=5,
          do_init=False):
    """Start the queue runner: parent thread + N workers.

    Runs until SIGINT/SIGTERM. Does not self-terminate.
    """
    if do_init:
        init_db(dsn, table)

    # Verify connectivity before spawning workers
    conn = _connect(dsn)
    conn.close()

    stop_event = threading.Event()

    def handle_signal(signum, frame):
        logger.info("Received signal %d, shutting down...", signum)
        stop_event.set()

    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)

    threads = []
    for i in range(workers):
        t = threading.Thread(
            target=worker_loop,
            args=(i, dsn, table, poll_interval, stop_event),
            daemon=True,
        )
        t.start()
        threads.append(t)

    logger.info(
        "Queue runner started: %d workers, polling every %ds, table: %s",
        workers, poll_interval, table,
    )
    logger.info("Send SIGINT (Ctrl+C) or SIGTERM to stop")

    # Block until stop signal
    try:
        while not stop_event.is_set():
            stop_event.wait(1)
    except KeyboardInterrupt:
        stop_event.set()

    logger.info("Waiting for workers to finish current tasks...")
    for t in threads:
        t.join(timeout=30)

    logger.info("Queue runner stopped")
