"""Configuration loading and validation. [FSD-5.2]"""
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

import yaml

from proofmark import ConfigError


class ReaderType(Enum):
    PARQUET = "parquet"
    CSV = "csv"


class ToleranceType(Enum):
    ABSOLUTE = "absolute"
    RELATIVE = "relative"


@dataclass(frozen=True)
class CsvSettings:
    header_rows: int = 0
    trailer_rows: int = 0


@dataclass(frozen=True)
class ExcludedColumn:
    name: str
    reason: str


@dataclass(frozen=True)
class FuzzyColumn:
    name: str
    tolerance: float
    tolerance_type: ToleranceType
    reason: str


@dataclass(frozen=True)
class ComparisonConfig:
    comparison_target: str
    reader: ReaderType
    encoding: str = "utf-8"
    threshold: float = 100.0
    csv: CsvSettings | None = None
    excluded_columns: tuple[ExcludedColumn, ...] = ()
    fuzzy_columns: tuple[FuzzyColumn, ...] = ()


def load_config(config_path: Path) -> tuple[ComparisonConfig, dict]:
    """Load and validate a YAML config file.

    Returns (typed config, raw YAML dict for report echo).
    Raises ConfigError on any validation failure. [FSD-5.2.1]
    """
    try:
        with open(config_path, "r") as f:
            raw = yaml.safe_load(f)
    except yaml.YAMLError as e:
        raise ConfigError(f"Invalid YAML: {e}") from e

    if not isinstance(raw, dict):
        raise ConfigError("Config file must contain a YAML mapping")

    # comparison_target required [FSD-5.2.2]
    comparison_target = raw.get("comparison_target")
    if not comparison_target:
        raise ConfigError("'comparison_target' is a required field")

    # reader required [FSD-5.2.3, FSD-5.2.4]
    reader_str = raw.get("reader")
    if not reader_str:
        raise ConfigError("'reader' is a required field")
    try:
        reader = ReaderType(reader_str)
    except ValueError:
        valid = ", ".join(f'"{r.value}"' for r in ReaderType)
        raise ConfigError(
            f'"{reader_str}" is not a valid reader type. Valid types: {valid}'
        )

    # encoding [FSD-5.2.13 step 4]
    encoding = raw.get("encoding", "utf-8")

    # threshold [FSD-5.2.11]
    threshold = raw.get("threshold", 100.0)
    if not isinstance(threshold, (int, float)):
        raise ConfigError("'threshold' must be a number")
    threshold = float(threshold)
    if threshold < 0.0 or threshold > 100.0:
        raise ConfigError("'threshold' must be between 0.0 and 100.0")

    # csv settings [FSD-5.2.13 step 6]
    csv_settings = None
    if reader == ReaderType.CSV:
        csv_raw = raw.get("csv", {})
        if csv_raw:
            csv_settings = CsvSettings(
                header_rows=csv_raw.get("header_rows", 0),
                trailer_rows=csv_raw.get("trailer_rows", 0),
            )
        else:
            csv_settings = CsvSettings()

    # columns [FSD-5.2.13 steps 7-9]
    columns_raw = raw.get("columns", {})
    excluded_list = columns_raw.get("excluded", []) if columns_raw else []
    fuzzy_list = columns_raw.get("fuzzy", []) if columns_raw else []

    # Parse excluded columns [FSD-5.2.8]
    excluded_columns = []
    for entry in (excluded_list or []):
        name = entry.get("name")
        if not name:
            raise ConfigError("EXCLUDED column entry missing 'name'")
        reason = entry.get("reason")
        if not reason:
            raise ConfigError(
                f"'reason' is required for EXCLUDED column \"{name}\""
            )
        excluded_columns.append(ExcludedColumn(name=name, reason=reason))

    # Parse fuzzy columns [FSD-5.2.5, FSD-5.2.6, FSD-5.2.7, FSD-5.2.9]
    fuzzy_columns = []
    for entry in (fuzzy_list or []):
        name = entry.get("name")
        if not name:
            raise ConfigError("FUZZY column entry missing 'name'")
        reason = entry.get("reason")
        if not reason:
            raise ConfigError(
                f"'reason' is required for FUZZY column \"{name}\""
            )
        tolerance_val = entry.get("tolerance")
        if tolerance_val is None:
            raise ConfigError(
                f"'tolerance' is required for FUZZY column \"{name}\""
            )
        tolerance_val = float(tolerance_val)
        if tolerance_val < 0.0:
            raise ConfigError(
                f"'tolerance' must be >= 0.0 for FUZZY column \"{name}\""
            )
        ttype_str = entry.get("tolerance_type")
        if not ttype_str:
            raise ConfigError(
                f"'tolerance_type' is required for FUZZY column \"{name}\""
            )
        try:
            ttype = ToleranceType(ttype_str)
        except ValueError:
            raise ConfigError(
                f'"{ttype_str}" is not a valid tolerance_type. '
                f'Valid types: "absolute", "relative"'
            )
        fuzzy_columns.append(FuzzyColumn(
            name=name,
            tolerance=tolerance_val,
            tolerance_type=ttype,
            reason=reason,
        ))

    # Cross-check: no duplicate classifications [FSD-5.2.10]
    excluded_names = {c.name for c in excluded_columns}
    fuzzy_names = {c.name for c in fuzzy_columns}
    overlap = excluded_names & fuzzy_names
    if overlap:
        col = sorted(overlap)[0]
        raise ConfigError(
            f"Column \"{col}\" appears in multiple classification lists"
        )

    config = ComparisonConfig(
        comparison_target=comparison_target,
        reader=reader,
        encoding=encoding,
        threshold=threshold,
        csv=csv_settings,
        excluded_columns=tuple(excluded_columns),
        fuzzy_columns=tuple(fuzzy_columns),
    )

    return config, raw
