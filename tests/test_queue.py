"""Integration tests for the PostgreSQL comparison queue runner."""

import json
import os
import threading
import time
from pathlib import Path
from unittest.mock import patch

import pytest

psycopg2 = pytest.importorskip("psycopg2")

from proofmark.queue import (
    claim_task,
    init_db,
    mark_failed,
    mark_succeeded,
    serve,
    worker_loop,
)

# Use env var or default to the ATC dev database
DSN = os.environ.get(
    "PROOFMARK_TEST_DSN",
    "host=172.18.0.1 dbname=atc user=claude password=claude",
)
TEST_TABLE = "control.proofmark_test_queue"

FIXTURES = Path(__file__).parent / "fixtures"
CSV_CONFIG = str(FIXTURES / "configs" / "csv_simple.yaml")
CSV_LHS = str(FIXTURES / "csv" / "simple_match" / "lhs.csv")
CSV_RHS = str(FIXTURES / "csv" / "simple_match" / "rhs.csv")


def _db_available():
    try:
        conn = psycopg2.connect(DSN)
        conn.close()
        return True
    except Exception:
        return False


skip_no_db = pytest.mark.skipif(
    not _db_available(), reason="PostgreSQL not reachable"
)


def _reset_table():
    """Drop and recreate the test table."""
    conn = psycopg2.connect(DSN)
    try:
        with conn.cursor() as cur:
            cur.execute(f"DROP TABLE IF EXISTS {TEST_TABLE};")
        conn.commit()
    finally:
        conn.close()
    init_db(DSN, TEST_TABLE)


def _insert_task(config_path, lhs_path, rhs_path, job_key=None, date_key=None):
    """Insert a task into the test queue."""
    conn = psycopg2.connect(DSN)
    try:
        with conn.cursor() as cur:
            cur.execute(
                f"""INSERT INTO {TEST_TABLE}
                    (config_path, lhs_path, rhs_path, job_key, date_key)
                    VALUES (%s, %s, %s, %s, %s)
                    RETURNING task_id;""",
                (config_path, lhs_path, rhs_path, job_key, date_key),
            )
            task_id = cur.fetchone()[0]
        conn.commit()
        return task_id
    finally:
        conn.close()


def _get_task(task_id):
    """Fetch a task row by ID."""
    conn = psycopg2.connect(DSN)
    try:
        with conn.cursor() as cur:
            cur.execute(
                f"SELECT task_id, status, result, error_message, result_json "
                f"FROM {TEST_TABLE} WHERE task_id = %s;",
                (task_id,),
            )
            row = cur.fetchone()
            if row:
                return {
                    "task_id": row[0],
                    "status": row[1],
                    "result": row[2],
                    "error_message": row[3],
                    "result_json": row[4],
                }
        return None
    finally:
        conn.close()


def _count_by_status():
    """Get task counts grouped by status."""
    conn = psycopg2.connect(DSN)
    try:
        with conn.cursor() as cur:
            cur.execute(
                f"SELECT status, COUNT(*) FROM {TEST_TABLE} GROUP BY status;"
            )
            return dict(cur.fetchall())
    finally:
        conn.close()


@skip_no_db
class TestInitDb:
    def setup_method(self):
        conn = psycopg2.connect(DSN)
        try:
            with conn.cursor() as cur:
                cur.execute(f"DROP TABLE IF EXISTS {TEST_TABLE};")
            conn.commit()
        finally:
            conn.close()

    def test_creates_table(self):
        init_db(DSN, TEST_TABLE)
        # Parse schema.table for information_schema query
        if "." in TEST_TABLE:
            schema, tname = TEST_TABLE.split(".", 1)
        else:
            schema, tname = "public", TEST_TABLE
        conn = psycopg2.connect(DSN)
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT column_name FROM information_schema.columns "
                    "WHERE table_schema = %s AND table_name = %s "
                    "ORDER BY ordinal_position;",
                    (schema, tname),
                )
                columns = [row[0] for row in cur.fetchall()]
        finally:
            conn.close()

        assert "task_id" in columns
        assert "config_path" in columns
        assert "status" in columns
        assert "result_json" in columns

    def test_idempotent(self):
        init_db(DSN, TEST_TABLE)
        init_db(DSN, TEST_TABLE)  # should not raise


@skip_no_db
class TestClaimTask:
    def setup_method(self):
        _reset_table()

    def test_claims_pending_task(self):
        tid = _insert_task(CSV_CONFIG, CSV_LHS, CSV_RHS)
        task = claim_task(DSN, TEST_TABLE)

        assert task is not None
        assert task["task_id"] == tid
        assert task["config_path"] == CSV_CONFIG

        # Should be marked Running in DB
        row = _get_task(tid)
        assert row["status"] == "Running"

    def test_returns_none_when_empty(self):
        task = claim_task(DSN, TEST_TABLE)
        assert task is None

    def test_skips_running_tasks(self):
        tid = _insert_task(CSV_CONFIG, CSV_LHS, CSV_RHS)
        # Claim it first
        claim_task(DSN, TEST_TABLE)
        # Try to claim again — should get None
        task = claim_task(DSN, TEST_TABLE)
        assert task is None

    def test_fifo_order(self):
        tid1 = _insert_task(CSV_CONFIG, CSV_LHS, CSV_RHS)
        tid2 = _insert_task(CSV_CONFIG, CSV_LHS, CSV_RHS)
        task = claim_task(DSN, TEST_TABLE)
        assert task["task_id"] == tid1


@skip_no_db
class TestMarkResults:
    def setup_method(self):
        _reset_table()

    def test_mark_succeeded(self):
        tid = _insert_task(CSV_CONFIG, CSV_LHS, CSV_RHS)
        claim_task(DSN, TEST_TABLE)

        report = {"summary": {"result": "PASS"}, "metadata": {"version": "0.1.0"}}
        mark_succeeded(DSN, TEST_TABLE, tid, report)

        row = _get_task(tid)
        assert row["status"] == "Succeeded"
        assert row["result"] == "PASS"
        assert row["result_json"]["summary"]["result"] == "PASS"

    def test_mark_failed(self):
        tid = _insert_task(CSV_CONFIG, CSV_LHS, CSV_RHS)
        claim_task(DSN, TEST_TABLE)

        mark_failed(DSN, TEST_TABLE, tid, "ConfigError: bad config")

        row = _get_task(tid)
        assert row["status"] == "Failed"
        assert "ConfigError" in row["error_message"]


@skip_no_db
class TestWorkerLoop:
    def setup_method(self):
        _reset_table()

    def test_processes_single_task(self):
        tid = _insert_task(CSV_CONFIG, CSV_LHS, CSV_RHS)

        stop_event = threading.Event()

        def run_worker():
            worker_loop(0, DSN, TEST_TABLE, poll_interval=1, stop_event=stop_event)

        t = threading.Thread(target=run_worker, daemon=True)
        t.start()

        # Wait for the task to be processed
        for _ in range(30):
            row = _get_task(tid)
            if row and row["status"] in ("Succeeded", "Failed"):
                break
            time.sleep(0.5)

        stop_event.set()
        t.join(timeout=5)

        row = _get_task(tid)
        assert row["status"] == "Succeeded"
        assert row["result"] == "PASS"
        assert row["result_json"] is not None

    def test_handles_bad_config(self):
        tid = _insert_task("/nonexistent/config.yaml", CSV_LHS, CSV_RHS)

        stop_event = threading.Event()
        t = threading.Thread(
            target=worker_loop,
            args=(0, DSN, TEST_TABLE, 1, stop_event),
            daemon=True,
        )
        t.start()

        for _ in range(30):
            row = _get_task(tid)
            if row and row["status"] in ("Succeeded", "Failed"):
                break
            time.sleep(0.5)

        stop_event.set()
        t.join(timeout=5)

        row = _get_task(tid)
        assert row["status"] == "Failed"
        assert row["error_message"] is not None

    def test_processes_multiple_tasks(self):
        tids = [_insert_task(CSV_CONFIG, CSV_LHS, CSV_RHS) for _ in range(3)]

        stop_event = threading.Event()
        t = threading.Thread(
            target=worker_loop,
            args=(0, DSN, TEST_TABLE, 1, stop_event),
            daemon=True,
        )
        t.start()

        for _ in range(60):
            counts = _count_by_status()
            if counts.get("Succeeded", 0) == 3:
                break
            time.sleep(0.5)

        stop_event.set()
        t.join(timeout=5)

        counts = _count_by_status()
        assert counts.get("Succeeded", 0) == 3


@skip_no_db
class TestSkipLocked:
    """Verify two workers don't claim the same task."""

    def setup_method(self):
        _reset_table()

    def test_no_double_claim(self):
        # Insert 6 tasks
        tids = [_insert_task(CSV_CONFIG, CSV_LHS, CSV_RHS) for _ in range(6)]

        stop_event = threading.Event()
        threads = []
        for i in range(3):
            t = threading.Thread(
                target=worker_loop,
                args=(i, DSN, TEST_TABLE, 1, stop_event),
                daemon=True,
            )
            t.start()
            threads.append(t)

        # Wait for all tasks to complete
        for _ in range(90):
            counts = _count_by_status()
            if counts.get("Succeeded", 0) + counts.get("Failed", 0) == 6:
                break
            time.sleep(0.5)

        stop_event.set()
        for t in threads:
            t.join(timeout=5)

        # Every task should have been processed exactly once
        counts = _count_by_status()
        assert counts.get("Succeeded", 0) == 6
        assert counts.get("Running", 0) == 0
