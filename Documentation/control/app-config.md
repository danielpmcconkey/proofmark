# AppConfig

Centralized configuration for serve mode. Single source of truth for database connection, queue parameters, and path resolution.

**Source**: `src/proofmark/app_config.py`

## Design

All settings are frozen dataclasses. Environment variables are read once at construction time and cached for the process lifetime -- no repeated lookups. An optional YAML settings file can overlay defaults.

```python
AppConfig
  paths: PathSettings        # ETL_ROOT, ETL_RE_OUTPUT tokens
  database: DatabaseSettings # host, username, database, password
  queue: QueueSettings       # table, workers, poll interval, idle shutdown
```

## `load_app_config(settings_path=None) -> AppConfig`

Builds the config. If no settings file is provided, returns defaults with env vars. If a settings file is provided, its values overlay the defaults.

## PathSettings

Reads environment variables for path token expansion:

| Env Var | Property | Used For |
|---|---|---|
| `ETL_ROOT` | `paths.etl_root` | `{ETL_ROOT}` token in queue task paths |
| `ETL_RE_OUTPUT` | `paths.etl_re_output` | `{ETL_RE_OUTPUT}` token in queue task paths |

### `paths.resolve(raw_path) -> str`

Replaces `{ETL_ROOT}` and `{ETL_RE_OUTPUT}` tokens in a path string with the cached env var values. See [queue-runner.md](queue-runner.md) for how this is used.

## DatabaseSettings

| Field | Default | Source |
|---|---|---|
| `host` | `"localhost"` | Settings file or default |
| `username` | `"claude"` | Settings file or default |
| `database` | `"atc"` | Settings file or default |
| `password` | (empty string) | `ETL_DB_PASSWORD` env var |

`database.dsn` property returns the libpq connection string: `host=... dbname=... user=... password=...`

The password is never stored in config files. It is only sourced from the `ETL_DB_PASSWORD` environment variable.

## QueueSettings

| Field | Default | Description |
|---|---|---|
| `table` | `"comparison_queue"` | Queue table name (can include schema prefix) |
| `workers` | `5` | Number of worker threads |
| `poll_interval_seconds` | `5` | Seconds between polls when idle |
| `idle_shutdown_seconds` | `28800` | Seconds of total idleness before auto-shutdown (8 hours) |

## Settings File (YAML)

All keys are optional. Omitted keys use defaults.

```yaml
database:
  host: db.example.com
  username: proofmark_svc
  database: etl_prod

queue:
  table: control.comparison_queue
  workers: 3
  poll_interval_seconds: 10
  idle_shutdown_seconds: 3600
```

Note: `paths` is not configurable via the settings file. Path tokens are sourced exclusively from environment variables.
