# Configuration

Proofmark has two distinct configuration systems:

1. **Comparison config** -- YAML file describing a single comparison (reader type, column classifications, thresholds). Referenced by `config_path` in the queue table.
2. **AppConfig** -- Serve-mode settings (database connection, queue parameters, path tokens). See [control/app-config.md](control/app-config.md).

This document covers comparison config. For AppConfig, see the link above.

## Comparison Config (YAML)

Each comparison task requires a YAML config file, referenced by the `config_path` column in the queue table.

### Required Fields

| Field | Type | Description |
|---|---|---|
| `comparison_target` | string | Human-readable name for this comparison (echoed in report metadata) |
| `reader` | string | `"parquet"` or `"csv"` |

### Optional Fields

| Field | Type | Default | Description |
|---|---|---|---|
| `encoding` | string | `"utf-8"` | Character encoding for CSV files |
| `threshold` | float | `100.0` | Minimum match percentage for PASS (0.0 to 100.0) |
| `csv` | object | `header_rows: 0, trailer_rows: 0` | CSV-specific settings |
| `columns` | object | (none) | Column classification overrides |

### CSV Settings

Only relevant when `reader: csv`.

```yaml
csv:
  header_rows: 1     # Number of header lines (first header row = column names)
  trailer_rows: 0     # Number of trailing control lines
```

When `header_rows: 0`, column names are auto-generated as positional indices (`"0"`, `"1"`, `"2"`, ...).

### Column Classifications

By default, all columns are STRICT (exact match). Override per-column:

```yaml
columns:
  excluded:
    - name: run_id
      reason: "Non-deterministic UUID assigned at runtime"

  fuzzy:
    - name: interest_accrued
      tolerance: 0.01
      tolerance_type: absolute    # or "relative"
      reason: "Rounding variance between ROUND_HALF_UP and ROUND_HALF_EVEN"
```

**EXCLUDED** columns require:
- `name`: Column name (must exist in schema)
- `reason`: Why this column is excluded (echoed in report)

**FUZZY** columns require:
- `name`: Column name
- `tolerance`: Non-negative float
- `tolerance_type`: `"absolute"` or `"relative"`
- `reason`: Why fuzzy matching is needed

**Validation rules:**
- A column cannot appear in both `excluded` and `fuzzy` lists
- `tolerance` must be >= 0.0
- `threshold` must be between 0.0 and 100.0
- FUZZY columns must contain numeric data at runtime (non-numeric raises `ConfigError`)

### Tolerance Types

**Absolute**: `|lhs - rhs| <= tolerance`

**Relative**: `|lhs - rhs| / max(|lhs|, |rhs|) <= tolerance`

Edge cases:
- Both values zero: always passes (both types)
- One value zero, other non-zero with relative: `delta / max = |non_zero| / |non_zero| = 1.0` (usually fails)
- Null vs null: passes
- Null vs non-null: always fails

### Full Example

```yaml
comparison_target: daily_account_balances
reader: parquet
threshold: 99.5
columns:
  excluded:
    - name: etl_run_id
      reason: "Non-deterministic UUID"
    - name: load_timestamp
      reason: "Runtime timestamp differs between runs"
  fuzzy:
    - name: accrued_interest
      tolerance: 0.01
      tolerance_type: absolute
      reason: "Banker's rounding vs half-up rounding"
    - name: market_value
      tolerance: 0.001
      tolerance_type: relative
      reason: "Float precision at large magnitudes"
```

## Environment Variables

| Variable | Used By | Description |
|---|---|---|
| `ETL_DB_PASSWORD` | AppConfig (serve mode) | PostgreSQL password |
| `ETL_ROOT` | PathSettings (serve mode) | Base path for `{ETL_ROOT}` token expansion |
