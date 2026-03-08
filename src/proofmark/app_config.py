"""Centralized application configuration for Proofmark serve mode.

Single source of truth for all serve-mode settings. Sourcing strategy:

  - Compiled default:  dataclass field default
  - Environment var:   read once at construction, cached for process lifetime
  - Settings file:     YAML, loaded at startup, overlays defaults

All values are immutable after construction. Env vars are read once and held
in memory — no repeated lookups.
"""

import os
from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class PathSettings:
    def __post_init__(self):
        object.__setattr__(
            self, "_etl_root",
            os.environ.get("ETL_ROOT", ""),
        )
        object.__setattr__(
            self, "_etl_re_output",
            os.environ.get("ETL_RE_OUTPUT", ""),
        )

    @property
    def etl_root(self) -> str:
        return self._etl_root

    @property
    def etl_re_output(self) -> str:
        return self._etl_re_output

    def resolve(self, raw_path: str) -> str:
        """Replace {ETL_ROOT} and {ETL_RE_OUTPUT} tokens in a path string."""
        return (
            raw_path
            .replace("{ETL_ROOT}", self._etl_root)
            .replace("{ETL_RE_OUTPUT}", self._etl_re_output)
        )


@dataclass(frozen=True)
class DatabaseSettings:
    host: str = "localhost"
    username: str = "claude"
    database: str = "atc"

    def __post_init__(self):
        object.__setattr__(
            self, "_password",
            os.environ.get("ETL_DB_PASSWORD", ""),
        )

    @property
    def password(self) -> str:
        return self._password

    @property
    def dsn(self) -> str:
        return (
            f"host={self.host} dbname={self.database} "
            f"user={self.username} password={self._password}"
        )


@dataclass(frozen=True)
class QueueSettings:
    table: str = "control.proofmark_test_queue"
    workers: int = 5
    poll_interval_seconds: int = 5
    idle_shutdown_seconds: int = 28800  # 8 hours


@dataclass(frozen=True)
class AppConfig:
    paths: PathSettings = field(default_factory=PathSettings)
    database: DatabaseSettings = field(default_factory=DatabaseSettings)
    queue: QueueSettings = field(default_factory=QueueSettings)


def load_app_config(settings_path: Path | None = None) -> AppConfig:
    """Build AppConfig from defaults + env vars, overlaid with optional YAML.

    Env vars (read once, cached for process lifetime):
      - ETL_DB_PASSWORD: database password

    Settings file keys (all optional — omitted keys use defaults):
      database.host, database.username, database.database
      queue.table, queue.workers, queue.poll_interval_seconds,
      queue.idle_shutdown_seconds
    """
    if settings_path is None:
        return AppConfig()

    import yaml

    with open(settings_path) as f:
        raw = yaml.safe_load(f) or {}

    db_raw = raw.get("database", {})
    queue_raw = raw.get("queue", {})

    db = DatabaseSettings(
        host=db_raw.get("host", "localhost"),
        username=db_raw.get("username", "claude"),
        database=db_raw.get("database", "atc"),
    )

    queue = QueueSettings(
        table=queue_raw.get("table", "control.proofmark_test_queue"),
        workers=queue_raw.get("workers", 5),
        poll_interval_seconds=queue_raw.get("poll_interval_seconds", 5),
        idle_shutdown_seconds=queue_raw.get("idle_shutdown_seconds", 28800),
    )

    return AppConfig(database=db, queue=queue)
