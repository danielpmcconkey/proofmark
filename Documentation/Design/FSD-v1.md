# Proofmark Functional Specification Document

**Version:** 1.0
**Date:** 2026-02-28
**Status:** Draft — Pending Dan's Approval
**Upstream:** BRD v3 (128 BR IDs, approved), Test Architecture v2 (60 BDD scenarios)

---

## 1. Architecture Overview

Proofmark is a CLI tool that compares two file-based dataset outputs (LHS and RHS) and produces a JSON equivalence report. It implements a hash-sort-diff pipeline for order-independent comparison with configurable column classification (STRICT / FUZZY / EXCLUDED).

### 1.1 Design Principles

| Principle | Description | BR |
|-----------|-------------|-----|
| Single comparison target | One config, one comparison, one report per invocation | BR-3.1, BR-12.5 |
| Portability | Zero platform-specific knowledge. Could be sold to any enterprise | BR-3.2 |
| No target relationships | No dependency modeling between comparison targets | BR-3.3, BR-3.4 |
| File-to-file only | No database in the loop | BR-3.5 |
| Default-strict | Every column is STRICT unless explicitly classified otherwise | BR-5.5, BR-5.9 |
| Attestation, not certification | Equivalence to original, not absolute correctness | BR-1.1 |

### 1.2 High-Level Data Flow

```
CLI args
  → Config loader → Config validator
  → Reader(LHS) → Reader(RHS)
  → [CSV only: Line break check]
  → Schema validator
  → Column excluder + Hash engine
  → Sort → Diff engine (+ tolerance comparator)
  → Mismatch correlator
  → Report generator
  → JSON output (file or stdout)
  → Exit code (0 = PASS, 1 = FAIL, 2 = ERROR)
```

---

## 2. Project Structure

```
proofmark/
├── pyproject.toml
├── src/
│   └── proofmark/
│       ├── __init__.py          # Package init, __version__
│       ├── __main__.py          # python -m proofmark entry point
│       ├── cli.py               # Argument parsing, exit code handling
│       ├── config.py            # YAML config loading + validation
│       ├── readers/
│       │   ├── __init__.py      # create_reader() factory
│       │   ├── base.py          # BaseReader ABC, ReaderResult, SchemaInfo
│       │   ├── parquet.py       # ParquetReader
│       │   └── csv_reader.py    # CsvReader (named to avoid stdlib collision)
│       ├── pipeline.py          # Orchestrator: wires all modules together
│       ├── schema.py            # Schema validation (column count/name/type)
│       ├── hasher.py            # Column exclusion, value concat, MD5 hashing
│       ├── diff.py              # Hash grouping, multiset comparison
│       ├── tolerance.py         # FUZZY absolute/relative tolerance checks
│       ├── correlator.py        # Unmatched row pairing by column similarity
│       └── report.py            # JSON report assembly + serialization
├── tests/
│   ├── conftest.py              # Shared fixtures, paths, helpers
│   ├── test_cli.py              # CLI argument and exit code tests
│   ├── test_config.py           # Config validation tests
│   ├── test_parquet_reader.py   # Parquet reader tests
│   ├── test_csv_reader.py       # CSV reader tests
│   ├── test_schema.py           # Schema validation tests
│   ├── test_hasher.py           # Hash engine tests
│   ├── test_diff.py             # Diff engine tests
│   ├── test_tolerance.py        # Tolerance comparator tests
│   ├── test_correlator.py       # Mismatch correlator tests
│   ├── test_report.py           # Report generation tests
│   ├── test_pipeline.py         # End-to-end pipeline tests
│   └── fixtures/                # (existing — 97 fixtures)
└── Documentation/               # (existing)
```

---

## 3. Dependencies

```toml
[project]
name = "proofmark"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = [
    "pyarrow>=14.0",
    "pyyaml>=6.0",
]

[project.scripts]
proofmark = "proofmark.cli:main"

[project.optional-dependencies]
dev = [
    "pytest>=7.0",
    "pytest-cov>=4.0",
]

[build-system]
requires = ["setuptools>=68.0"]
build-backend = "setuptools.backends._legacy:_Backend"

[tool.setuptools.packages.find]
where = ["src"]
```

**Rationale:** Minimal dependency footprint. `pyarrow` for parquet reading (no alternative). `pyyaml` for config parsing. No pandas — list-of-dicts is sufficient for a comparison tool and avoids a heavy transitive dependency. Standard library covers everything else (`hashlib`, `csv`, `json`, `argparse`, `pathlib`).

---

## 4. Data Model

All types are defined as frozen dataclasses (immutable after creation). Type hints use Python 3.11+ syntax (`list[X]` not `List[X]`, `X | None` not `Optional[X]`).

### 4.1 Configuration Types — `config.py`

```python
from dataclasses import dataclass, field
from enum import Enum


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
    reason: str                          # Required [BR-5.3]


@dataclass(frozen=True)
class FuzzyColumn:
    name: str
    tolerance: float                     # Required [BR-7.7]
    tolerance_type: ToleranceType        # Required [BR-7.6]
    reason: str                          # Required [BR-5.8]


@dataclass(frozen=True)
class ComparisonConfig:
    comparison_target: str               # Required [BR-6.6]
    reader: ReaderType                   # Required [BR-3.6]
    encoding: str = "utf-8"              # Default UTF-8 [BR-9.1]
    threshold: float = 100.0             # Default 100% [BR-11.23]
    csv: CsvSettings | None = None       # Present when reader=csv
    excluded_columns: tuple[ExcludedColumn, ...] = ()
    fuzzy_columns: tuple[FuzzyColumn, ...] = ()
    # All columns not in excluded or fuzzy are STRICT [BR-5.5]
```

### 4.2 Reader Output Types — `readers/base.py`

```python
@dataclass(frozen=True)
class SchemaInfo:
    column_names: tuple[str, ...]
    column_types: dict[str, str]         # Parquet: pyarrow type names. CSV: empty dict.


@dataclass(frozen=True)
class ReaderResult:
    schema: SchemaInfo
    rows: list[dict[str, Any]]           # Data rows as {column_name: value}
    header_lines: tuple[str, ...] | None # CSV only: raw header line strings [BR-3.11]
    trailer_lines: tuple[str, ...] | None # CSV only: raw trailer line strings [BR-3.11]
    line_break_style: str | None         # CSV only: "LF" or "CRLF" [BR-4.1]
```

### 4.3 Pipeline Internal Types — `hasher.py`, `diff.py`, `correlator.py`

```python
# hasher.py
@dataclass(frozen=True)
class HashedRow:
    hash_key: str                        # MD5 hex digest of STRICT columns [BR-4.16]
    unhashed_content: str                # All non-excluded columns, pipe-delimited [BR-4.15]
    fuzzy_values: dict[str, Any]         # {column_name: value} for FUZZY columns
    row_data: dict[str, Any]             # Full row data (non-excluded columns only)


# diff.py
@dataclass(frozen=True)
class UnmatchedRow:
    side: str                            # "lhs" or "rhs"
    content: str                         # Unhashed concatenated content [BR-11.9]
    row_data: dict[str, Any]             # Column values for correlation


@dataclass(frozen=True)
class FuzzyFailure:
    column: str
    lhs_value: float
    rhs_value: float
    tolerance: float
    tolerance_type: str                  # "absolute" or "relative"
    actual_delta: float                  # [BR-11.9]


@dataclass(frozen=True)
class HashGroupResult:
    hash_value: str
    lhs_count: int
    rhs_count: int
    status: str                          # "MATCH" or "COUNT_MISMATCH" [BR-4.19]
    matched_count: int                   # min(lhs_count, rhs_count) [BR-11.14]
    surplus_rows: list[UnmatchedRow]     # Rows from the larger side
    fuzzy_failures: list[FuzzyFailure]   # From matched pairs [BR-4.21]


@dataclass
class DiffResult:
    hash_groups: list[HashGroupResult]   # Groups with issues only [BR-11.20]
    all_unmatched_lhs: list[UnmatchedRow]
    all_unmatched_rhs: list[UnmatchedRow]
    all_fuzzy_failures: list[FuzzyFailure]
    total_matched: int                   # Sum of (matched_count × 2) across groups
    total_lhs: int                       # Total LHS row count
    total_rhs: int                       # Total RHS row count


# correlator.py
@dataclass(frozen=True)
class CorrelatedPair:
    lhs_content: str
    rhs_content: str
    confidence: str                      # "high" [BR-11.10]
    differing_columns: list[str]


@dataclass(frozen=True)
class CorrelationResult:
    correlated_pairs: list[CorrelatedPair]   # [BR-11.10]
    uncorrelated_lhs: list[str]              # [BR-11.11]
    uncorrelated_rhs: list[str]              # [BR-11.11]
```

### 4.4 Report Types — `report.py`

```python
@dataclass(frozen=True)
class ComparisonSummary:
    row_count_lhs: int                   # [BR-11.5]
    row_count_rhs: int                   # [BR-11.5]
    match_count: int                     # [BR-11.5]
    mismatch_count: int                  # [BR-11.5]
    match_percentage: float              # [BR-11.13–18]
    result: str                          # "PASS" or "FAIL" [BR-11.25–26]
    threshold: float                     # [BR-11.5]
    line_break_mismatch: bool | None     # CSV only [BR-11.5, BR-4.5]


@dataclass(frozen=True)
class HeaderTrailerResult:
    position: int                        # 0-indexed within the header/trailer block
    lhs: str                             # Raw line content
    rhs: str
    match: bool                          # Exact string match [BR-3.13]
```

---

## 5. Module Specifications

### 5.1 CLI — `cli.py`

**Purpose:** Parse command-line arguments, invoke the pipeline, write output, exit with the appropriate code.

**Public API:**
```python
def main() -> None:
    """Entry point. Parses args, runs pipeline, writes report, exits."""
```

**CLI Signature [BR-12.1–4]:**
```
proofmark compare --config <path> --left <path> --right <path> [--output <path>]
```

| Flag | Required | Description | BR |
|------|----------|-------------|-----|
| `--config` | Yes | Path to YAML config file | BR-12.1 |
| `--left` | Yes | LHS path (file for CSV, directory for parquet) | BR-12.2 |
| `--right` | Yes | RHS path (same semantics as `--left`) | BR-12.3 |
| `--output` | No | Output file path. Omitted → stdout | BR-12.4 |

**Exit Codes [BR-12.6–8]:**

| Code | Meaning | Trigger |
|------|---------|---------|
| 0 | PASS | Comparison result is PASS |
| 1 | FAIL | Comparison result is FAIL (data mismatch, schema mismatch, line break mismatch, FUZZY tolerance exceeded) |
| 2 | ERROR | Invalid config, file not found, encoding error, parse failure |

**Behavior:**
1. Parse args with `argparse`. Missing required args → `argparse` handles with exit code 2.
2. Call `pipeline.run(config_path, lhs_path, rhs_path)`.
3. Serialize the returned report dict to JSON.
4. Write to `--output` file or stdout [BR-12.4]. Same JSON format either way.
5. `sys.exit()` with code based on report result.

**Error handling:** All exceptions from the pipeline are caught at this level.
- `ConfigError` → exit 2.
- `FileNotFoundError` → exit 2.
- `EncodingError` → exit 2.
- `SchemaMismatchError` → the pipeline returns a FAIL report (not an exception). Exit 1.
- Unexpected exceptions → print to stderr, exit 2.

**Not supported (MVP) [BR-12.10–13]:** No verbosity flags, no batch mode, no dry-run, no CLI overrides of config values.

---

### 5.2 Configuration — `config.py`

**Purpose:** Parse a YAML config file, validate all fields, return a typed `ComparisonConfig`.

**Public API:**
```python
def load_config(config_path: Path) -> ComparisonConfig:
    """Load and validate a YAML config file.

    Raises ConfigError on any validation failure.
    """


class ConfigError(Exception):
    """Invalid configuration. Results in exit code 2."""
```

**Validation Rules:**

| Rule | Error Condition | BR |
|------|----------------|-----|
| `comparison_target` required | Missing or empty | BR-6.6 |
| `reader` required | Missing | BR-6.6 |
| `reader` value | Not `"csv"` or `"parquet"` | BR-3.6 |
| FUZZY `tolerance_type` required | Missing on any FUZZY column | BR-7.6 |
| FUZZY `tolerance` required | Missing on any FUZZY column | BR-7.7 |
| FUZZY `tolerance_type` value | Not `"absolute"` or `"relative"` | BR-7.1 |
| EXCLUDED `reason` required | Missing on any EXCLUDED column | BR-5.3 |
| FUZZY `reason` required | Missing on any FUZZY column | BR-5.8 |
| No duplicate classifications | Same column in both EXCLUDED and FUZZY lists | BR-5.1 |
| `threshold` range | Must be 0.0 ≤ threshold ≤ 100.0 | BR-11.22 |
| YAML parseable | File is not valid YAML | BR-6.5 |

**Parsing logic:**
1. Read file contents. YAML parse error → `ConfigError`.
2. Extract `comparison_target` (required string).
3. Extract `reader` (required: `"csv"` or `"parquet"`).
4. Extract `encoding` (optional, default `"utf-8"`) [BR-9.1].
5. Extract `threshold` (optional, default `100.0`) [BR-11.23].
6. If `reader == "csv"`: extract `csv.header_rows` (default 0), `csv.trailer_rows` (default 0) [BR-3.11].
7. Extract `columns.excluded` list. Validate each entry has `name` and `reason`.
8. Extract `columns.fuzzy` list. Validate each entry has `name`, `tolerance`, `tolerance_type`, `reason`.
9. Cross-check: no column name appears in both excluded and fuzzy lists [BR-5.1].
10. Return `ComparisonConfig`.

**What config does NOT contain [BR-6.6–8]:** File paths. The CLI provides `--left` and `--right`. This separation is critical — same config for Tuesday's run and Wednesday's run. If config changes mid-window, go back to start date and re-run all [BR-6.8].

**Reference YAML schema (from BRD):**
```yaml
comparison_target: daily_balance_feed
reader: csv
csv:
  header_rows: 1
  trailer_rows: 1
encoding: utf-8
threshold: 100.0
columns:
  excluded:
    - name: run_id
      reason: Non-deterministic UUID assigned at runtime
  fuzzy:
    - name: interest_accrued
      tolerance: 0.01
      tolerance_type: absolute
      reason: Floating point rounding between computation engines
```

---

### 5.3 Readers

#### 5.3.1 Base Reader — `readers/base.py`

```python
from abc import ABC, abstractmethod


class BaseReader(ABC):
    @abstractmethod
    def read(self, path: Path, encoding: str) -> ReaderResult:
        """Read input data from path. Return normalized ReaderResult."""
```

**Factory — `readers/__init__.py`:**
```python
def create_reader(config: ComparisonConfig) -> BaseReader:
    """Return the appropriate reader based on config.

    CsvReader receives csv_settings via constructor.
    ParquetReader takes no constructor args.
    """
```

CSV-specific settings (`CsvSettings`) are injected via the `CsvReader` constructor, not through the `read()` method signature. This keeps the `BaseReader` ABC clean.

#### 5.3.2 Parquet Reader — `readers/parquet.py`

**Purpose:** Read all parquet part files from a directory, assemble into one logical table [BR-3.7–9, BR-3.15–16].

```python
class ParquetReader(BaseReader):
    def read(self, path: Path, encoding: str) -> ReaderResult:
        """Read *.parquet from directory, assemble into single logical table.

        Args:
            path: Directory containing parquet part files [BR-3.7]
            encoding: Ignored for parquet (binary format)

        Returns:
            ReaderResult with schema, rows, and null CSV-specific fields

        Raises:
            FileNotFoundError: If path doesn't exist or isn't a directory
            ReaderError: If directory contains no .parquet files [BR-3.15]
            ReaderError: If any part file is unreadable
        """
```

**Behavior:**
1. Validate `path` is an existing directory.
2. Glob `path/*.parquet` — collect all parquet files [BR-3.8].
3. If no files found → `ReaderError` (exit 2).
4. Read each file with `pyarrow.parquet.read_table()`.
5. Concatenate all tables with `pyarrow.concat_tables()` [BR-3.9, BR-3.15].
6. Extract schema: column names (in order) and column types as pyarrow type name strings (e.g. `"int64"`, `"float64"`, `"string"`, `"bool"`) [BR-4.12].
7. Convert to `list[dict[str, Any]]` via `table.to_pydict()` reshaped row-wise.
8. Return `ReaderResult` with `header_lines=None`, `trailer_lines=None`, `line_break_style=None`.

**Part file assembly [BR-3.16]:** 3 part files with 100 rows each must compare identically to 1 part file with 300 rows. This is guaranteed by the concat-then-compare approach — the pipeline never sees part file boundaries.

#### 5.3.3 CSV Reader — `readers/csv_reader.py`

**Purpose:** Read a CSV file, separating header rows, trailer rows, and data rows [BR-3.10–14].

```python
class CsvReader(BaseReader):
    def __init__(self, csv_settings: CsvSettings):
        self.csv_settings = csv_settings

    def read(self, path: Path, encoding: str) -> ReaderResult:
        """Read CSV file with header/trailer separation.

        Args:
            path: File path [BR-3.10]
            encoding: Character encoding [BR-9.1]

        Returns:
            ReaderResult with rows, schema, headers, trailers, line_break_style

        Raises:
            FileNotFoundError: If path doesn't exist
            EncodingError: If file can't be decoded with configured encoding [BR-9.2]
            ReaderError: If file has fewer lines than header_rows + trailer_rows
        """
```

**Behavior:**
1. **Line break detection [BR-4.1]:** Read raw bytes. If `b"\r\n"` is present → `line_break_style = "CRLF"`. Otherwise → `line_break_style = "LF"`.
2. **Decode [BR-9.1]:** Open file with configured encoding. Decode failure → `EncodingError` (exit 2) [BR-9.2].
3. **Normalize for splitting [BR-4.3]:** Internally normalize line breaks to `\n` for consistent row splitting. This normalization is internal only — it does not alter the line break mismatch detection from step 1.
4. **Split into lines:** Split on `\n` after normalization. Drop trailing empty line if present (artifact of trailing newline).
5. **Separate segments [BR-3.11]:**
   - Header lines: first `header_rows` lines (raw strings, preserved for comparison) [BR-3.13].
   - Trailer lines: last `trailer_rows` lines (raw strings, preserved for comparison) [BR-3.13].
   - Data lines: everything between header and trailer [BR-3.12].
   - If total lines < `header_rows + trailer_rows` → `ReaderError` (exit 2).
6. **Parse data rows:** Use Python `csv.reader` on data lines [BR-14.1].
7. **Extract column names:** If `header_rows >= 1`, parse the first header line with `csv.reader` to get column names. If `header_rows == 0`, name columns positionally: `"0"`, `"1"`, `"2"`, etc.
8. **Build schema:** `SchemaInfo` with column names and empty `column_types` dict [BR-4.13] (type validation is parquet-only).
9. **Convert data rows** to `list[dict[str, Any]]` keyed by column name.
10. Return `ReaderResult`.

---

### 5.4 Schema Validator — `schema.py`

**Purpose:** Compare LHS and RHS schemas. Any difference = automatic FAIL [BR-4.9].

**Public API:**
```python
def validate_schema(
    lhs_schema: SchemaInfo,
    rhs_schema: SchemaInfo,
    reader_type: ReaderType,
) -> list[str]:
    """Compare schemas. Returns list of mismatch descriptions.

    Empty list = schemas match.
    Non-empty = schema mismatch, comparison should FAIL [BR-4.9].
    """
```

**Checks (in order):**

| Check | Applies To | BR |
|-------|-----------|-----|
| Column count differs | Both readers | BR-4.10 |
| Column name differs (positional comparison) | Both readers | BR-4.11 |
| Column type differs | Parquet only | BR-4.12, BR-4.13 |

**Behavior:**
1. Compare `len(lhs_schema.column_names)` vs `len(rhs_schema.column_names)`. Different → add mismatch description.
2. If counts match: compare column names positionally. Each name mismatch → add description.
3. If `reader_type == PARQUET` and counts match: compare column types positionally. Each type mismatch → add description (e.g. `"Column 'balance': float64 vs int32"`) [BR-4.12].

**On mismatch:** The pipeline generates a FAIL report with schema mismatch details in lieu of running the comparison. No further pipeline steps execute. Exit code 1.

---

### 5.5 Hash Engine — `hasher.py`

**Purpose:** Drop EXCLUDED columns, concatenate row values into string representations, compute MD5 hash keys [BR-4.14–16].

**Public API:**
```python
def hash_rows(
    rows: list[dict[str, Any]],
    excluded_names: set[str],
    fuzzy_names: set[str],
    column_order: tuple[str, ...],
) -> list[HashedRow]:
    """Apply exclusions, compute hash keys, build HashedRow objects.

    Args:
        rows: Data rows from a reader.
        excluded_names: Column names classified as EXCLUDED.
        fuzzy_names: Column names classified as FUZZY.
        column_order: Schema-order column names (determines concat order).

    Returns:
        List of HashedRow, one per input row.
    """
```

**Algorithm per row:**

1. **Exclude [BR-4.14]:** Remove all columns in `excluded_names`. They do not exist from this point forward.
2. **Identify column sets:**
   - `strict_columns`: columns in `column_order` that are NOT in `excluded_names` and NOT in `fuzzy_names`. These are STRICT [BR-5.5].
   - `fuzzy_columns`: columns in `column_order` that are in `fuzzy_names`.
   - `non_excluded_columns`: `strict_columns + fuzzy_columns` in schema order.
3. **Value-to-string conversion:**
   - Non-null values: `str(value)`.
   - Null/None values (parquet): the literal string `"__PROOFMARK_NULL__"`. This sentinel is chosen to be unambiguous against any plausible data value [BR-8.1, BR-8.4].
   - CSV values: used as-is (they're already strings). No null normalization [BR-8.2].
4. **Hash input [BR-4.16]:** Concatenate STRICT column string values in schema order, separated by `\x00` (null byte). This separator prevents collision between values like `["ab", "c"]` and `["a", "bc"]`.
5. **Compute hash [BR-10.1]:** `hashlib.md5(hash_input.encode("utf-8")).hexdigest()`.
6. **Unhashed content [BR-4.15]:** Concatenate ALL non-excluded column string values in schema order, separated by `|` (pipe). This is for human-readable report output. The pipe separator is for display only.
7. **Extract FUZZY values:** `{col_name: original_value for col_name in fuzzy_columns}`.
8. **Build `HashedRow`** with `hash_key`, `unhashed_content`, `fuzzy_values`, `row_data` (all non-excluded columns).

**Column ordering determinism:** All operations iterate columns in schema order (the order they appear in `column_order`). This guarantees identical hashes regardless of Python dict ordering.

---

### 5.6 Diff Engine — `diff.py`

**Purpose:** Group rows by hash, compare group counts (multiset comparison), identify matched/unmatched rows, trigger FUZZY validation [BR-4.17–22].

**Public API:**
```python
def diff(
    lhs_rows: list[HashedRow],
    rhs_rows: list[HashedRow],
    fuzzy_columns: tuple[FuzzyColumn, ...],
) -> DiffResult:
    """Sort, group, and diff hashed rows.

    Returns DiffResult with per-group results, all unmatched rows,
    all fuzzy failures, and match count totals.
    """
```

**Algorithm:**

1. **Group by hash [BR-4.17]:**
   - Build `lhs_groups: dict[str, list[HashedRow]]` — key is `hash_key`.
   - Build `rhs_groups: dict[str, list[HashedRow]]` — same structure.

2. **Iterate all unique hash keys [BR-4.18]:** Union of keys from both dicts.

3. **Per hash key:**
   - `lhs_list = lhs_groups.get(key, [])`, `rhs_list = rhs_groups.get(key, [])`.
   - `lhs_count = len(lhs_list)`, `rhs_count = len(rhs_list)`.
   - `matched_count = min(lhs_count, rhs_count)` [BR-11.14].
   - **Status:** `"MATCH"` if `lhs_count == rhs_count`, else `"COUNT_MISMATCH"` [BR-4.19, BR-4.20].
   - **Surplus rows:** If `lhs_count > rhs_count` → last `(lhs_count - rhs_count)` LHS rows are surplus (as `UnmatchedRow`, side=`"lhs"`). Vice versa for RHS surplus [BR-4.20].
   - **FUZZY validation [BR-4.21]:** If `matched_count > 0` and `len(fuzzy_columns) > 0`:
     - Sort both sides' first `matched_count` rows by their FUZZY values (lexicographic on `tuple(str(row.fuzzy_values[col.name]) for col in fuzzy_columns)`) for deterministic pairing.
     - Pair row-by-row: `lhs_list[i]` with `rhs_list[i]` for `i` in `0..matched_count-1`.
     - For each pair, call `tolerance.check_fuzzy()` on each FUZZY column.
     - Collect any `FuzzyFailure` results.
   - **Include in output hash_groups list only if:** status is `"COUNT_MISMATCH"` OR there are FUZZY failures. Groups where everything matches are omitted [BR-11.20].

4. **Accumulate totals:**
   - `total_matched = sum(matched_count * 2 for each group)` — counted on both sides [BR-11.14].
   - `total_lhs = sum(lhs_count for each group)` (should equal `len(lhs_rows)`).
   - `total_rhs = sum(rhs_count for each group)` (should equal `len(rhs_rows)`).
   - Collect all `UnmatchedRow` from all groups into `all_unmatched_lhs` and `all_unmatched_rhs`.
   - Collect all `FuzzyFailure` from all groups into `all_fuzzy_failures`.

5. **Return `DiffResult`.**

**Match percentage [BR-11.13–18]:**
```python
total_rows = total_lhs + total_rhs
if total_rows == 0:
    match_percentage = 100.0    # Both sides empty = PASS [zero-row edge case]
else:
    match_percentage = (total_matched / total_rows) * 100.0
```

**Example [BR-11.18]:** LHS=5000 rows, RHS=5001 rows. One RHS row has a unique hash. `total_matched = 10000`. `total_rows = 10001`. `match_percentage = 99.99%`.

---

### 5.7 Tolerance Comparator — `tolerance.py`

**Purpose:** Evaluate FUZZY column value pairs against configured tolerances [BR-7.1–8].

**Public API:**
```python
def check_fuzzy(
    column_name: str,
    lhs_value: Any,
    rhs_value: Any,
    tolerance: float,
    tolerance_type: ToleranceType,
) -> FuzzyFailure | None:
    """Check if two values are within tolerance.

    Returns None if within tolerance (pass).
    Returns FuzzyFailure if tolerance exceeded (fail).

    Raises:
        ValueError: If values cannot be converted to float.
    """
```

**Absolute tolerance [BR-7.2]:**
```python
lhs_f, rhs_f = float(lhs_value), float(rhs_value)
delta = abs(lhs_f - rhs_f)
passes = delta <= tolerance
# actual_delta for report = delta
```

**Relative tolerance [BR-7.3]:**
```python
lhs_f, rhs_f = float(lhs_value), float(rhs_value)
delta = abs(lhs_f - rhs_f)
denominator = max(abs(lhs_f), abs(rhs_f))
```

**Edge cases:**
- **Both values zero [BR-7.4]:** `delta = 0`. Short-circuit to pass. `actual_delta = 0.0`. For relative: avoids `0/0`.
- **One value zero, other non-zero [BR-7.5]:** Relative formula naturally handles this. `|0 - 0.0001| / max(0, 0.0001) = 1.0`. Fails any reasonable tolerance. No special-casing needed.
- **Non-numeric FUZZY value:** `float()` conversion raises `ValueError`. Pipeline treats this as exit code 2 — a FUZZY column must contain numeric data.

**Return value:** On failure, `FuzzyFailure` includes:
- `actual_delta`: For absolute — the raw delta. For relative — `delta / denominator`.

**No "percentage" type [BR-7.8]:** Relative tolerance of `0.01` IS 1%. No ambiguity.

---

### 5.8 Mismatch Correlator — `correlator.py`

**Purpose:** Attempt to pair unmatched rows from different hash groups by column similarity [BR-11.10–12].

This runs AFTER the diff engine. Unmatched rows from COUNT_MISMATCH groups and single-side-only groups are collected and the correlator attempts to pair LHS rows with RHS rows that share most column values.

**Public API:**
```python
def correlate(
    unmatched_lhs: list[UnmatchedRow],
    unmatched_rhs: list[UnmatchedRow],
    column_names: list[str],
) -> CorrelationResult:
    """Pair unmatched rows by column similarity.

    Deterministic: sorted input, greedy highest-similarity-first pairing.
    """
```

**Algorithm:**

1. If either list is empty → return `CorrelationResult` with empty pairs and all rows uncorrelated.
2. **Sort both lists** by `content` (alphabetical) for determinism.
3. **Build similarity matrix:** For each `(lhs_i, rhs_j)` pair:
   - Compare column values: `lhs_row.row_data[col] == rhs_row.row_data[col]` for each column in `column_names`.
   - `score = matching_columns / len(column_names)`.
4. **Greedy pairing** (highest score first):
   a. Find the `(i, j)` pair with the highest `score`.
   b. If `score > 0.5` → **high confidence pair** [BR-11.10]:
      - Create `CorrelatedPair` with `confidence="high"`, `differing_columns` = list of columns that don't match.
      - Remove both rows from candidate pools.
      - Repeat from (a).
   c. If best remaining score ≤ 0.5 → stop pairing.
5. All remaining LHS rows → `uncorrelated_lhs` (as unhashed content strings) [BR-11.11].
6. All remaining RHS rows → `uncorrelated_rhs` [BR-11.11].

**Confidence threshold:** > 50% of non-excluded columns matching = "high" confidence. This is a deterministic, conservative heuristic for common cases (e.g., two rows differing by one column out of five). Full fuzzy matching is vendor-build territory [BR-11.12].

**Complexity:** O(L × R × C) where L = unmatched LHS count, R = unmatched RHS count, C = column count. Acceptable for MVP volumes.

---

### 5.9 Report Generator — `report.py`

**Purpose:** Assemble all comparison results into a JSON report [BR-11.1].

**Public API:**
```python
def build_report(
    config_path: str,
    config: ComparisonConfig,
    config_raw: dict,
    schema: SchemaInfo,
    summary: ComparisonSummary,
    header_comparison: list[HeaderTrailerResult] | None,
    trailer_comparison: list[HeaderTrailerResult] | None,
    diff_result: DiffResult,
    correlation: CorrelationResult,
) -> dict:
    """Assemble the final report as a JSON-serializable dict."""


def build_schema_fail_report(
    config_path: str,
    config: ComparisonConfig,
    config_raw: dict,
    schema_mismatches: list[str],
    lhs_row_count: int,
    rhs_row_count: int,
) -> dict:
    """Build a FAIL report for schema mismatch (no diff data)."""


def serialize_report(report: dict) -> str:
    """Serialize report dict to formatted JSON string.

    Uses json.dumps with indent=2 and sort_keys=False
    (preserve insertion order for readability).
    """
```

**Column classifications in report [BR-11.4]:**

Built by combining schema column names with config classifications. For each column in schema order:
- If in `excluded_columns` → classification `"EXCLUDED"`, include reason.
- If in `fuzzy_columns` → classification `"FUZZY"`, include reason, tolerance, tolerance_type.
- Otherwise → classification `"STRICT"`, reason is null [BR-5.5].

**Report JSON structure:** See Section 7 for the complete schema.

---

### 5.10 Pipeline Orchestrator — `pipeline.py`

**Purpose:** Wire all modules together in the correct order. This is the single coordination point.

**Public API:**
```python
def run(config_path: Path, lhs_path: Path, rhs_path: Path) -> dict:
    """Execute the full comparison pipeline.

    Returns a JSON-serializable report dict.
    The caller (CLI) determines exit code from report["summary"]["result"].

    Raises:
        ConfigError: Invalid config (exit 2)
        EncodingError: CSV encoding failure (exit 2)
        ReaderError: File/directory problems (exit 2)
    """
```

**Pipeline steps (in order):**

```
Step 0: Load & validate config
  config, config_raw = config.load_config(config_path)
  On failure: ConfigError → exit 2

Step 1: Create reader & load data [BR-4.7]
  reader = create_reader(config)
  lhs_result = reader.read(lhs_path, config.encoding)
  rhs_result = reader.read(rhs_path, config.encoding)
  On encoding failure: EncodingError → exit 2 [BR-4.8]
  On file not found: FileNotFoundError → exit 2
  On empty parquet dir: ReaderError → exit 2

Step 2: Line break check — CSV only [BR-4.1–6]
  if config.reader == CSV:
      line_break_mismatch = (lhs_result.line_break_style != rhs_result.line_break_style)
  else:
      line_break_mismatch = None  # Not applicable to parquet [BR-4.6]
  Continue regardless of result [BR-4.4]

Step 3: Schema validation [BR-4.9]
  schema_mismatches = validate_schema(
      lhs_result.schema, rhs_result.schema, config.reader
  )
  If mismatches:
      return build_schema_fail_report(...)  # FAIL report, exit 1
      No further pipeline steps execute.

Step 4: Header/trailer comparison — CSV only [BR-3.13–14]
  if config.reader == CSV:
      header_comparison = compare_lines(lhs_result.header_lines, rhs_result.header_lines)
      trailer_comparison = compare_lines(lhs_result.trailer_lines, rhs_result.trailer_lines)
  else:
      header_comparison = None
      trailer_comparison = None
  Cross-file comparison only [BR-11.7]. No internal consistency checks [BR-11.8].

Step 5: Hash [BR-4.14–16]
  excluded_names = {col.name for col in config.excluded_columns}
  fuzzy_names = {col.name for col in config.fuzzy_columns}
  lhs_hashed = hash_rows(lhs_result.rows, excluded_names, fuzzy_names, lhs_result.schema.column_names)
  rhs_hashed = hash_rows(rhs_result.rows, excluded_names, fuzzy_names, rhs_result.schema.column_names)

Step 6: Diff [BR-4.17–22]
  diff_result = diff(lhs_hashed, rhs_hashed, config.fuzzy_columns)

Step 7: Correlate unmatched rows [BR-11.10–12]
  non_excluded_columns = [c for c in lhs_result.schema.column_names if c not in excluded_names]
  correlation = correlate(
      diff_result.all_unmatched_lhs,
      diff_result.all_unmatched_rhs,
      non_excluded_columns,
  )

Step 8: Compute summary
  match_percentage = compute_match_percentage(diff_result)  # See §5.6
  result = determine_result(match_percentage, config.threshold,
                            diff_result.all_fuzzy_failures,
                            line_break_mismatch)  # See §5.10.1

Step 9: Build report [BR-11.1]
  summary = ComparisonSummary(
      row_count_lhs=diff_result.total_lhs,
      row_count_rhs=diff_result.total_rhs,
      match_count=...,
      mismatch_count=...,
      match_percentage=match_percentage,
      result=result,
      threshold=config.threshold,
      line_break_mismatch=line_break_mismatch,
  )
  return build_report(...)
```

#### 5.10.1 PASS/FAIL Determination [BR-11.25–26]

```python
result = "PASS" if ALL of the following:
    match_percentage >= config.threshold     # [BR-11.22]
    len(all_fuzzy_failures) == 0             # All FUZZY within tolerance
    line_break_mismatch is not True          # No line break difference (CSV) [BR-4.2]
    len(schema_mismatches) == 0              # Schemas match [BR-4.9]
else:
    result = "FAIL"
```

A comparison can have 100% hash-level match and still FAIL if a FUZZY column exceeds tolerance [test scenario 42] or line breaks differ [test scenario 41].

#### 5.10.2 `compare_lines` helper

```python
def compare_lines(
    lhs_lines: tuple[str, ...] | None,
    rhs_lines: tuple[str, ...] | None,
) -> list[HeaderTrailerResult]:
    """Compare header or trailer lines positionally.

    Exact string match per position [BR-3.13].
    If line counts differ, missing lines compared against empty string.
    """
```

---

## 6. Cross-Cutting Concerns

### 6.1 Null Handling

**Parquet [BR-8.1]:** Pyarrow provides native null support. Null is null — distinct from empty string. In the hash engine, null values are represented as the sentinel string `"__PROOFMARK_NULL__"` for concatenation and hashing. Two nulls in the same column position produce the same hash contribution [BR-8.4].

**CSV [BR-8.2–3]:** Byte-level comparison. No null equivalence, no null normalization. An empty field (`,,`), the literal `"NULL"`, the literal `"null"`, and the literal `""` are four distinct values. They hash differently. The rewrite process is responsible for matching the original's null representation.

### 6.2 Column Ordering

All operations that iterate over columns use **schema order** — the order columns appear in the reader's output. This ensures:
- Hash computation is deterministic (same column concat order every time).
- Unhashed content strings are deterministic.
- Column classifications in the report are in a predictable, stable order.

### 6.3 Encoding [BR-9.1–5]

- Both LHS and RHS are always read with the **same** encoding setting [BR-9.4].
- Default: UTF-8 [BR-9.1]. Configurable via config `encoding` field.
- Invalid encoding (file can't be decoded) → `EncodingError` → exit 2 [BR-9.2].
- No encoding detection. No encoding normalization [BR-9.3].
- The rewrite process is responsible for producing output in the expected encoding [BR-9.5].

### 6.4 Header/Trailer Comparison [BR-3.13–14, BR-11.6–8]

- Compared **independently** from the hash-sort-diff pipeline [BR-3.13].
- Comparison is exact literal string match, positional (first header vs first header, etc.).
- Both results appear in the report [BR-3.14, BR-11.6].
- Cross-file comparison only (LHS trailer vs RHS trailer). No internal consistency validation (e.g., trailer claims 5000 rows but data has 4999) [BR-11.7, BR-11.8]. This is consistent with the attestation disclaimer — Proofmark certifies equivalence, not correctness.
- Header/trailer mismatches do **NOT** independently cause FAIL. They do not appear in the PASS/FAIL conditions [BR-11.25]. They are reported for human review.

### 6.5 Zero-Row Edge Case

When both LHS and RHS have zero data rows:
- `total_rows = 0`.
- `match_percentage = 100.0` by definition — nothing to mismatch [test scenario 59].
- Result: PASS (assuming no other failure conditions).
- Schema validation still runs — schemas can mismatch even with zero rows.

### 6.6 Attestation [BR-1.1]

Every report includes the fixed attestation string:

> Output equivalence certifies equivalence to the original, NOT correctness in an absolute sense. If the original has a bug and the rewrite faithfully reproduces it, Proofmark reports PASS.

Not configurable. Always present.

### 6.7 Line Break Checking [BR-4.1–6]

- **Pre-comparison check (CSV only):** Before any data processing, compare line break styles between LHS and RHS [BR-4.1].
- **Detection method:** Read file as raw bytes. Presence of `\r\n` → `"CRLF"`. Otherwise → `"LF"`.
- **On mismatch [BR-4.2]:** Set `line_break_mismatch = True`. This contributes to FAIL [BR-11.25].
- **Continue regardless [BR-4.4]:** The full comparison runs. Report includes both the match rate AND the line break mismatch flag [BR-4.5].
- **Internal normalization [BR-4.3]:** Both files are normalized to `\n` internally for row splitting. This does not affect the mismatch flag (which was set from raw bytes).
- **Parquet [BR-4.6]:** Line break check does not apply. `line_break_mismatch` is `None` in the report.

### 6.8 Hash Algorithm [BR-10.1–2]

- MVP uses MD5. Fast, good distribution, collision risk irrelevant for comparison hash (we're not doing security).
- Algorithm name is NOT surfaced in report output [BR-10.2]. This is an implementation detail.

---

## 7. Report JSON Schema

This is the complete JSON structure that `report.py` produces. Every field maps to a BR requirement.

```json
{
  "metadata": {
    "timestamp": "2026-02-28T14:30:00Z",
    "proofmark_version": "0.1.0",
    "comparison_target": "daily_balance_feed",
    "config_path": "/path/to/config.yaml"
  },

  "config": {
    "comparison_target": "daily_balance_feed",
    "reader": "csv",
    "encoding": "utf-8",
    "threshold": 99.5,
    "csv": {
      "header_rows": 1,
      "trailer_rows": 1
    },
    "columns": {
      "excluded": [
        {"name": "run_id", "reason": "Non-deterministic UUID"}
      ],
      "fuzzy": [
        {
          "name": "interest_accrued",
          "tolerance": 0.01,
          "tolerance_type": "absolute",
          "reason": "FP rounding between engines"
        }
      ]
    }
  },

  "column_classifications": [
    {
      "name": "account_id",
      "classification": "STRICT",
      "reason": null,
      "tolerance": null,
      "tolerance_type": null
    },
    {
      "name": "run_id",
      "classification": "EXCLUDED",
      "reason": "Non-deterministic UUID",
      "tolerance": null,
      "tolerance_type": null
    },
    {
      "name": "balance",
      "classification": "STRICT",
      "reason": null,
      "tolerance": null,
      "tolerance_type": null
    },
    {
      "name": "interest_accrued",
      "classification": "FUZZY",
      "reason": "FP rounding between engines",
      "tolerance": 0.01,
      "tolerance_type": "absolute"
    }
  ],

  "summary": {
    "row_count_lhs": 5000,
    "row_count_rhs": 5001,
    "match_count": 5000,
    "mismatch_count": 1,
    "match_percentage": 99.99,
    "result": "PASS",
    "threshold": 99.5,
    "line_break_mismatch": false
  },

  "header_comparison": [
    {
      "position": 0,
      "lhs": "account_id,run_id,balance,interest_accrued",
      "rhs": "account_id,run_id,balance,interest_accrued",
      "match": true
    }
  ],

  "trailer_comparison": [
    {
      "position": 0,
      "lhs": "TRAILER|5000|2026-02-28",
      "rhs": "TRAILER|5001|2026-02-27",
      "match": false
    }
  ],

  "mismatches": {
    "hash_groups": [
      {
        "hash_value": "a1b2c3d4e5f67890abcdef1234567890",
        "lhs_count": 2,
        "rhs_count": 1,
        "status": "COUNT_MISMATCH",
        "matched_count": 1,
        "surplus_rows": [
          {
            "side": "lhs",
            "content": "1003|3200.50|active"
          }
        ],
        "fuzzy_failures": []
      },
      {
        "hash_value": "f6e5d4c3b2a10987654321fedcba0987",
        "lhs_count": 1,
        "rhs_count": 1,
        "status": "MATCH",
        "matched_count": 1,
        "surplus_rows": [],
        "fuzzy_failures": [
          {
            "column": "interest_accrued",
            "lhs_value": 100.005,
            "rhs_value": 100.05,
            "tolerance": 0.01,
            "tolerance_type": "absolute",
            "actual_delta": 0.045
          }
        ]
      }
    ],
    "correlation": {
      "correlated_pairs": [
        {
          "lhs_row": "1001|3200.50|active",
          "rhs_row": "1001|3200.99|active",
          "confidence": "high",
          "differing_columns": ["balance"]
        }
      ],
      "uncorrelated_lhs": [],
      "uncorrelated_rhs": [
        "1099|500.00|pending"
      ]
    }
  },

  "attestation": "Output equivalence certifies equivalence to the original, NOT correctness in an absolute sense. If the original has a bug and the rewrite faithfully reproduces it, Proofmark reports PASS."
}
```

**Field rules:**
- `header_comparison`, `trailer_comparison`: present for CSV, `null` for parquet [BR-11.6].
- `summary.line_break_mismatch`: present for CSV, `null` for parquet [BR-4.6].
- `mismatches.hash_groups`: only groups with issues. Fully matched groups omitted [BR-11.20].
- `mismatches.correlation`: always present (may have empty lists).
- `attestation`: always present, fixed text [BR-1.1].
- `config`: full echo of the raw YAML content as parsed [BR-11.3].
- `metadata.proofmark_version`: from package metadata (`importlib.metadata.version("proofmark")`).
- `metadata.timestamp`: ISO 8601 UTC at report generation time.

**Schema mismatch report:** When schema validation fails, the report has the same top-level structure but:
- `summary.result` = `"FAIL"`.
- `summary.match_count` = 0, `mismatch_count` = 0, `match_percentage` = 0.0.
- `mismatches` = `{"schema_mismatches": ["Column count: LHS=5, RHS=4", ...], "hash_groups": [], "correlation": {"correlated_pairs": [], "uncorrelated_lhs": [], "uncorrelated_rhs": []}}`.
- No header/trailer comparison (pipeline didn't get that far).

---

## 8. Error Handling

### 8.1 Exception Hierarchy

```python
class ProofmarkError(Exception):
    """Base exception for all Proofmark errors."""

class ConfigError(ProofmarkError):
    """Invalid configuration file. Exit code 2."""

class ReaderError(ProofmarkError):
    """Reader-level failures (missing files, empty directories). Exit code 2."""

class EncodingError(ReaderError):
    """File cannot be decoded with configured encoding. Exit code 2."""
```

### 8.2 Error-to-Exit-Code Mapping

| Error | Source | Exit Code | Report Generated? |
|-------|--------|-----------|-------------------|
| `ConfigError` | `config.load_config()` | 2 | No |
| `FileNotFoundError` | Reader, CLI | 2 | No |
| `ReaderError` (empty dir, parse fail) | Reader | 2 | No |
| `EncodingError` | CSV reader | 2 | No |
| Schema mismatch | `schema.validate_schema()` | 1 | Yes (FAIL report) |
| Comparison FAIL | Pipeline | 1 | Yes (FAIL report) |
| Comparison PASS | Pipeline | 0 | Yes (PASS report) |
| `ValueError` (non-numeric FUZZY) | `tolerance.check_fuzzy()` | 2 | No |
| Unexpected exception | Any | 2 | No |

### 8.3 Error Output

- Exit code 2 errors: Print a human-readable error message to stderr. No JSON output.
- Exit code 1 (schema mismatch, comparison FAIL): Full JSON report to stdout or `--output` file. The report itself documents the failure.
- Exit code 0: Full JSON report.

---

## 9. BR Traceability Index

Every BR ID from the BRD v3 is accounted for below. Module assignments show where each requirement is implemented.

| BR Range | Module(s) | FSD Section |
|----------|-----------|-------------|
| BR-1.1 | report.py | §5.9, §6.6 |
| BR-2.1–2.7 | (scope definition — no module) | §1.1 |
| BR-3.1–3.2 | pipeline.py, cli.py | §1.1, §5.1 |
| BR-3.3–3.4 | pipeline.py | §1.1 |
| BR-3.5 | pipeline.py | §1.1 |
| BR-3.6 | config.py, readers/__init__.py | §5.2, §5.3.1 |
| BR-3.7–3.9 | readers/parquet.py | §5.3.2 |
| BR-3.10–3.14 | readers/csv_reader.py, pipeline.py | §5.3.3, §5.10 |
| BR-3.15–3.16 | readers/parquet.py | §5.3.2 |
| BR-3.17–3.18 | (terminology — no code) | — |
| BR-4.1–4.6 | pipeline.py, readers/csv_reader.py | §5.10, §6.7 |
| BR-4.7–4.8 | pipeline.py, readers/* | §5.10 |
| BR-4.9–4.13 | schema.py | §5.4 |
| BR-4.14–4.16 | hasher.py | §5.5 |
| BR-4.17–4.22 | diff.py | §5.6 |
| BR-4.23 | report.py | §5.9 |
| BR-5.1 | config.py | §5.2 |
| BR-5.2–5.3 | config.py, hasher.py | §5.2, §5.5 |
| BR-5.4–5.5 | hasher.py, config.py | §5.5, §5.2 |
| BR-5.6–5.8 | config.py, tolerance.py | §5.2, §5.7 |
| BR-5.9–5.10 | config.py, report.py | §5.2, §5.9 |
| BR-6.1–6.5 | config.py | §5.2 |
| BR-6.6–6.8 | config.py, cli.py | §5.2, §5.1 |
| BR-7.1–7.8 | tolerance.py, config.py | §5.7, §5.2 |
| BR-8.1–8.4 | hasher.py | §5.5, §6.1 |
| BR-9.1–9.5 | readers/csv_reader.py, pipeline.py | §5.3.3, §6.3 |
| BR-10.1–10.2 | hasher.py | §5.5, §6.8 |
| BR-11.1–11.5 | report.py | §5.9, §7 |
| BR-11.6–11.8 | report.py, pipeline.py | §5.9, §6.4 |
| BR-11.9 | report.py, diff.py | §5.9, §5.6, §7 |
| BR-11.10–11.12 | correlator.py | §5.8 |
| BR-11.13–11.18 | diff.py, pipeline.py | §5.6 |
| BR-11.19–11.21 | report.py | §5.9, §7 |
| BR-11.22–11.26 | pipeline.py, report.py | §5.10.1 |
| BR-12.1–12.4 | cli.py | §5.1 |
| BR-12.5 | cli.py, pipeline.py | §5.1 |
| BR-12.6–12.8 | cli.py | §5.1 |
| BR-12.9 | cli.py | §5.1 |
| BR-12.10–12.13 | (not supported in MVP) | §5.1 |
| BR-13.1 | (out of scope) | — |
| BR-14.1 | readers/csv_reader.py | §5.3.3 |
| BR-16.1 | (out of scope) | — |

---

## 10. TAR Register Alignment

This FSD advances the following TAR register items:

| TAR Item | Coverage |
|----------|----------|
| T-01: Comparison Engine Core | §5.5 (hasher), §5.6 (diff), §5.7 (tolerance) |
| T-02: Parquet Reader | §5.3.2 |
| T-03: CSV Reader (Simple) | §5.3.3 |
| T-04: CSV Trailing Control Record | §5.3.3 (trailer_rows), §6.4 |
| T-05: Per-Job Config Schema | §5.2 |
| T-06: Report Generator | §5.9, §7 |
| T-12: TDD/BDD Test Suite | §2 (test file structure maps to 60 BDD scenarios) |
| AC-01: Proofmark Maturity | This document IS the functional specification |
| AC-24: Attestation Problem | §6.6 (fixed attestation text in every report) |
| AC-25: Information Isolation | §1.1 (portability test — zero platform knowledge) |

---

## Appendix A: Test File Mapping

Each test file maps to one or more feature areas from the Test Architecture v2. Test scenarios are referenced by number from that document.

| Test File | Feature Area | Scenarios | Fixture Directories |
|-----------|-------------|-----------|-------------------|
| `test_parquet_reader.py` | parquet_reader | 1–4 | `parquet/identical_*`, `parquet/data_mismatch`, `parquet/empty_directory` |
| `test_csv_reader.py` | csv_reader | 5–9 | `csv/simple_match`, `csv/with_trailer_match`, `csv/header_mismatch`, `csv/trailer_mismatch`, `csv/data_mismatch` |
| `test_schema.py` | schema_validation | 10–13 | `parquet/schema_mismatch_*` |
| `test_hasher.py` | column_classification, hash_sort_diff | 14–16, 19, 24–26 | `parquet/excluded_*`, `parquet/fuzzy_*`, `parquet/different_row_order`, `parquet/mixed_classification` |
| `test_diff.py` | hash_sort_diff, row_count | 24–25, 58–60 | `parquet/different_row_order`, `parquet/duplicate_rows`, `parquet/row_count_mismatch`, `parquet/zero_rows` |
| `test_tolerance.py` | column_classification (FUZZY) | 16–18, 32–35 | `parquet/fuzzy_*` |
| `test_correlator.py` | report_output (correlation) | 43–44 | `parquet/correlation_*` |
| `test_report.py` | report_output | 36–42 | Various |
| `test_config.py` | config_validation | 50–57 | `configs/*` |
| `test_cli.py` | cli | 45–49 | Various |
| `test_pipeline.py` | (end-to-end) | 27–31, 38–39, 41, 42 | `csv/crlf_vs_lf`, `csv/encoding_*`, `parquet/threshold_*` |
