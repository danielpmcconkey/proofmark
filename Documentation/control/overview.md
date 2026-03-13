# Serve Mode Overview

The `proofmark serve` command runs Proofmark as a long-lived service. Instead of comparing files from CLI arguments, it polls a PostgreSQL queue table for comparison tasks, processes them with a thread pool, and writes results back to the database.

## Why

An automated ETL pipeline produces dozens of jobs per run. The queue runner processes a batch of comparisons without per-invocation overhead.

An external process (agent, cron job, ETL orchestrator) inserts rows into the `comparison_queue` table. Proofmark picks them up, runs the comparison pipeline, and stores the JSON report in the same row.

## Architecture

```
PostgreSQL                    Proofmark serve
+-----------------+           +-----------------------+
| comparison_queue|  poll     | Main thread            |
|  Pending tasks  | <------> |   idle shutdown timer   |
|  Running tasks  |           |                        |
|  Succeeded/Failed|          | Worker threads (N)     |
+-----------------+           |   claim -> run -> mark |
                              +-----------------------+
```

- **Main thread**: Spawns worker threads, handles signals, monitors idle shutdown.
- **Worker threads**: Each independently polls for tasks, claims atomically (SKIP LOCKED), runs comparison, writes result.
- **Idle shutdown**: If all workers are idle for the configured duration (default 8 hours), the service shuts down cleanly.

## Components

| Document | Covers |
|---|---|
| [app-config.md](app-config.md) | AppConfig, DatabaseSettings, PathSettings, QueueSettings, env vars, settings file |
| [queue-runner.md](queue-runner.md) | Queue table schema, worker loop, task lifecycle, path token expansion, idle shutdown |
