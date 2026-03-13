"""PostgreSQL-backed comparison queue runner."""

import gc
import json
import logging
import os
import signal
import threading
import time
from pathlib import Path

from proofmark.pipeline import run
from proofmark.report import serialize_report

logger = logging.getLogger("proofmark.queue")


def _rss_mb():
    """Current process RSS in MB, from /proc."""
    with open(f"/proc/{os.getpid()}/statm") as f:
        pages = int(f.read().split()[1])
    return pages * os.sysconf("SC_PAGE_SIZE") / (1024 * 1024)

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


def claim_task(conn, table):
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


def mark_succeeded(conn, table, task_id, report):
    """Mark a task as Succeeded and store the report."""
    result = report.get("summary", {}).get("result", "UNKNOWN")
    report_json = json.dumps(report)
    sql = f"""
    UPDATE {table}
    SET status = 'Succeeded', completed_at = NOW(),
        result = %s, result_json = %s
    WHERE task_id = %s;
    """
    with conn.cursor() as cur:
        cur.execute(sql, (result, report_json, task_id))
    conn.commit()


def mark_failed(conn, table, task_id, error_msg):
    """Mark a task as Failed with an error message."""
    sql = f"""
    UPDATE {table}
    SET status = 'Failed', completed_at = NOW(), error_message = %s
    WHERE task_id = %s;
    """
    with conn.cursor() as cur:
        cur.execute(sql, (error_msg, task_id))
    conn.commit()


class _ActivityTracker:
    """Thread-safe tracker for idle shutdown. Tracks how many workers are
    actively processing tasks, and when the system last became fully idle."""

    def __init__(self):
        self._lock = threading.Lock()
        self._active_count = 0
        self._last_idle_at = time.monotonic()

    def task_started(self):
        with self._lock:
            self._active_count += 1

    def task_ended(self):
        with self._lock:
            self._active_count -= 1
            if self._active_count == 0:
                self._last_idle_at = time.monotonic()

    def idle_seconds(self):
        """Seconds since all workers became idle. Returns 0 if any worker
        is currently processing a task."""
        with self._lock:
            if self._active_count > 0:
                return 0.0
            return time.monotonic() - self._last_idle_at


def _reconnect(dsn, label, old_conn=None):
    """Close old connection (if any) and open a fresh one."""
    if old_conn is not None:
        try:
            old_conn.close()
        except Exception:
            pass
    logger.info("[%s] connecting to database", label)
    return _connect(dsn)


def worker_loop(worker_id, dsn, table, poll_interval, stop_event,
                activity=None, resolve_path=None, telemetry=False):
    """Worker loop: claim tasks, run comparisons, write results.

    Each worker holds a single persistent database connection for its
    lifetime, reconnecting automatically if the connection drops.

    resolve_path: optional callable that expands path tokens
                  (e.g. {ETL_ROOT}) to real values. Identity if None.
    telemetry: if True, log RSS and GC stats after each task.
    """
    label = f"worker-{worker_id}"
    _resolve = resolve_path or (lambda p: p)
    logger.info("[%s] started", label)

    conn = _reconnect(dsn, label)

    while not stop_event.is_set():
        task = None
        try:
            task = claim_task(conn, table)
        except Exception:
            logger.exception("[%s] error claiming task, reconnecting", label)
            try:
                conn = _reconnect(dsn, label, conn)
            except Exception:
                logger.exception("[%s] reconnect failed", label)
            stop_event.wait(poll_interval)
            continue

        if task is None:
            stop_event.wait(poll_interval)
            continue

        task_id = task["task_id"]
        logger.info("[%s] claimed task %d", label, task_id)

        if activity:
            activity.task_started()

        report = None
        try:
            report = run(
                Path(_resolve(task["config_path"])),
                Path(_resolve(task["lhs_path"])),
                Path(_resolve(task["rhs_path"])),
            )
            mark_succeeded(conn, table, task_id, report)
            result = report.get("summary", {}).get("result", "?")
            logger.info("[%s] task %d completed: %s", label, task_id, result)
            del report
            gc.collect()
            if telemetry:
                gc_stats = gc.get_stats()
                uncollectable = sum(s.get("uncollectable", 0) for s in gc_stats)
                logger.info(
                    "[%s] task %d | rss=%.1f MB | uncollectable=%d",
                    label, task_id, _rss_mb(), uncollectable,
                )
        except Exception as e:
            error_msg = f"{type(e).__name__}: {e}"
            logger.error("[%s] task %d failed: %s", label, task_id, error_msg)
            if report is not None:
                del report
                gc.collect()
            try:
                mark_failed(conn, table, task_id, error_msg)
            except Exception:
                logger.exception(
                    "[%s] failed to write error for task %d, reconnecting",
                    label, task_id,
                )
                try:
                    conn = _reconnect(dsn, label, conn)
                except Exception:
                    logger.exception("[%s] reconnect failed", label)
        finally:
            if activity:
                activity.task_ended()

        # No sleep between tasks — immediately check for next one

    # Clean shutdown
    try:
        conn.close()
    except Exception:
        pass


def serve(config, do_init=False):
    """Start the queue runner using centralised AppConfig.

    Runs until SIGINT/SIGTERM or idle shutdown threshold is reached.
    """
    dsn = config.database.dsn
    table = config.queue.table
    workers = config.queue.workers
    poll_interval = config.queue.poll_interval_seconds
    idle_shutdown = config.queue.idle_shutdown_seconds
    telemetry = config.queue.telemetry

    if do_init:
        init_db(dsn, table)

    # Verify connectivity before spawning workers
    conn = _connect(dsn)
    conn.close()

    stop_event = threading.Event()
    activity = _ActivityTracker()

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
            kwargs={
                "activity": activity,
                "resolve_path": config.paths.resolve,
                "telemetry": telemetry,
            },
            daemon=True,
        )
        t.start()
        threads.append(t)

    logger.info(
        "Queue runner started: %d workers, polling every %ds, "
        "idle shutdown after %ds, table: %s",
        workers, poll_interval, idle_shutdown, table,
    )
    logger.info("Send SIGINT (Ctrl+C) or SIGTERM to stop")

    # Block until stop signal or idle shutdown
    try:
        while not stop_event.is_set():
            stop_event.wait(1)
            if activity.idle_seconds() >= idle_shutdown:
                logger.info(
                    "Idle shutdown: no tasks completed for %ds. Stopping.",
                    idle_shutdown,
                )
                stop_event.set()
    except KeyboardInterrupt:
        stop_event.set()

    logger.info("Waiting for workers to finish current tasks...")
    for t in threads:
        t.join(timeout=30)

    logger.info("Queue runner stopped")
