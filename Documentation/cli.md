# CLI Reference

Proofmark exposes two subcommands: `compare` and `serve`.

## `proofmark compare`

Run a one-off comparison between two data sources.

```
proofmark compare --config CONFIG --left LEFT --right RIGHT [--output OUTPUT]
```

| Flag | Required | Description |
|---|---|---|
| `--config` | Yes | Path to YAML comparison config file |
| `--left` | Yes | LHS path -- file for CSV, directory for Parquet |
| `--right` | Yes | RHS path -- same semantics as `--left` |
| `--output` | No | Write JSON report to file instead of stdout |

### Exit Codes

| Code | Meaning |
|---|---|
| 0 | PASS -- equivalence met |
| 1 | FAIL -- mismatches detected or threshold not met |
| 2 | Error -- bad config, missing files, encoding errors, unexpected failures |

### Examples

```bash
# Compare parquet directories, report to stdout
proofmark compare \
  --config jobs/daily_balances.yaml \
  --left /data/original/daily_balances/ \
  --right /data/rewrite/daily_balances/

# Compare CSV files, write report to file
proofmark compare \
  --config jobs/transactions.yaml \
  --left /data/original/transactions.csv \
  --right /data/rewrite/transactions.csv \
  --output report.json
```

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
python -m proofmark compare --config ...
python -m proofmark serve ...
```

Both forms are equivalent. The `proofmark` console script is registered via `pyproject.toml`.
