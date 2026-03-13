# CLI Reference

Proofmark exposes a single subcommand: `serve`.

## `proofmark serve`

Start the queue runner. Polls PostgreSQL for pending comparison tasks, runs them, writes results back.

```
proofmark serve [--settings SETTINGS] [--init-db]
```

| Flag | Required | Description |
|---|---|---|
| `--settings` | No | Path to YAML settings file for serve mode. Defaults are built in. |
| `--init-db` | No | Create the queue table if it doesn't exist |

Requires the `queue` extra: `pip install proofmark[queue]` (provides `psycopg2`).

Runs until SIGINT/SIGTERM or idle shutdown threshold is reached. See [control/queue-runner.md](control/queue-runner.md) for operational details.

### Examples

```bash
# Start with defaults (localhost, database=atc, user=claude, 5 workers)
ETL_DB_PASSWORD=secret proofmark serve

# Start with custom settings and create the queue table
ETL_DB_PASSWORD=secret proofmark serve --settings /etc/proofmark/settings.yaml --init-db
```

## Running as Module

```bash
python -m proofmark serve ...
```

Both forms are equivalent. The `proofmark` console script is registered via `pyproject.toml`.
