# Proofmark --- Test Architecture and BDD Scenarios

**Version:** 2.3
**Date:** 2026-03-06
**Status:** Draft --- Pending Dan's Review + Adversarial Review
**Preceding Artifact:** BRD v3.1 (FSD audit revision, 2026-02-28)
**Next Artifact:** Adversarial review of this document, then test data management
**Revision:** v2.3 — Added queue runner integration test coverage (Part 3). 12 integration tests across 5 test classes against live PostgreSQL. 66 BDD scenarios unchanged.

---

## Part 1: Test Architecture

### 1.1 Organization

Tests are organized by **feature area**, not by pipeline stage or reader type. Each feature area maps to one or more BRD v3 sections and BR IDs. Feature areas are:

| Feature Area | BRD v3 Sections | Key BR IDs | Description |
|---|---|---|---|
| `parquet_reader` | 3.4, 3.5, 4 (Step 1) | BR-3.7 through BR-3.9, BR-3.15, BR-3.16 | Loading and assembling parquet part files |
| `csv_reader` | 3.4, 4 (Step 1) | BR-3.10 through BR-3.14 | Loading CSV with header/trailer handling |
| `schema_validation` | 4 (Step 2) | BR-4.9 through BR-4.13 | Column count, name, and type validation |
| `column_classification` | 5, 7 | BR-5.1 through BR-5.10, BR-7.1 through BR-7.8 | EXCLUDED/STRICT/FUZZY behavior including tolerance math |
| `null_handling` | 8 | BR-8.1 through BR-8.4 | Null representation across formats |
| `hash_sort_diff` | 4 (Steps 3-6) | BR-4.14 through BR-4.22 | Exclusion, hashing, sorting, row-level diff |
| `line_break_check` | 4 (Pre-check) | BR-4.1 through BR-4.6 | CSV line break detection and FAIL flag |
| `encoding` | 9 | BR-9.1 through BR-9.5 | Encoding configuration and error handling |
| `report_output` | 11 | BR-11.1 through BR-11.26 | Report structure, content, match %, pass/fail logic |
| `cli` | 12 | BR-12.1 through BR-12.13 | Exit codes, --left/--right/--output paths, config flag |
| `config_validation` | 6 | BR-6.1 through BR-6.8 | YAML parsing, required fields, schema enforcement |
| `row_count` | 4 (Step 6), 11 | BR-4.18 through BR-4.20, BR-11.17 | Row count mismatch detection |
| `queue_runner` | FSD Section 11 | FSD-11.1 through FSD-11.13 | PostgreSQL queue runner: init, claim, mark, workers, SKIP LOCKED |

This maps cleanly to a directory structure under `tests/`:

```
tests/
    conftest.py                     # Shared fixtures, markers, helpers
    fixtures/                       # All test data (see 1.2)
        parquet/
        csv/
        configs/
    test_parquet_reader.py
    test_csv_reader.py
    test_schema_validation.py
    test_column_classification.py
    test_null_handling.py
    test_hash_sort_diff.py
    test_line_break_check.py
    test_encoding.py
    test_report_output.py
    test_cli.py
    test_config_validation.py
    test_row_count.py
    test_queue.py                    # Queue runner integration tests (requires PostgreSQL)
```

### 1.2 Test Fixtures

Test data lives in `tests/fixtures/` and is version-controlled. No generated fixtures at test time --- everything is deterministic and reviewable.

**Parquet fixtures** (`tests/fixtures/parquet/`):

```
parquet/
    identical_3part_vs_1part/
        lhs/                         # 3 part files, same data
            part-00000.parquet
            part-00001.parquet
            part-00002.parquet
        rhs/                         # 1 part file, coalesced
            part-00000.parquet
    identical_simple/
        lhs/
            part-00000.parquet
        rhs/
            part-00000.parquet
    data_mismatch/
        lhs/
            part-00000.parquet
        rhs/
            part-00000.parquet
    empty_directory/
        lhs/                         # Empty
        rhs/
            part-00000.parquet
    with_nulls/
        lhs/
            part-00000.parquet
        rhs/
            part-00000.parquet
    row_count_mismatch/
        lhs/
            part-00000.parquet       # 100 rows
        rhs/
            part-00000.parquet       # 99 rows
    different_row_order/
        lhs/
            part-00000.parquet       # Rows in order A
        rhs/
            part-00000.parquet       # Same rows, different order
    duplicate_rows/
        lhs/
            part-00000.parquet       # Contains 2 identical rows
        rhs/
            part-00000.parquet       # Contains 1 of that row
    zero_rows/
        lhs/
            part-00000.parquet       # Schema only, 0 data rows
        rhs/
            part-00000.parquet       # Schema only, 0 data rows
    schema_mismatch_column_count/
        lhs/
            part-00000.parquet       # 3 columns
        rhs/
            part-00000.parquet       # 2 columns
    schema_mismatch_column_name/
        lhs/
            part-00000.parquet       # Column: status
        rhs/
            part-00000.parquet       # Column: state
    schema_mismatch_column_type/
        lhs/
            part-00000.parquet       # balance: float64
        rhs/
            part-00000.parquet       # balance: int32
```

**CSV fixtures** (`tests/fixtures/csv/`):

```
csv/
    simple_match/
        lhs.csv                      # Header + data, no trailer
        rhs.csv
    with_trailer_match/
        lhs.csv                      # Header + data + trailer row
        rhs.csv
    data_mismatch/
        lhs.csv
        rhs.csv
    header_mismatch/
        lhs.csv                      # Different header text
        rhs.csv
    trailer_mismatch/
        lhs.csv                      # Different trailer row count/checksum
        rhs.csv
    null_representations/
        lhs.csv                      # Empty field ,,
        rhs.csv                      # Literal NULL
    crlf_vs_lf/
        lhs.csv                      # CRLF line endings
        rhs.csv                      # LF line endings
    matching_line_breaks/
        lhs.csv                      # Both LF
        rhs.csv
    encoding_utf8/
        lhs.csv                      # UTF-8 with multi-byte chars (é, ñ, etc.)
        rhs.csv                      # UTF-8 with same characters
    encoding_invalid/
        lhs.csv                      # UTF-8 with multi-byte chars
        rhs.csv                      # Same file (encoding mismatch is config-driven, not data-driven)
```

**Config fixtures** (`tests/fixtures/configs/`):

```
configs/
    parquet_default.yaml
    parquet_with_exclusions.yaml
    parquet_with_fuzzy.yaml
    csv_simple.yaml
    csv_with_trailer.yaml
    csv_with_encoding.yaml
    mixed_classifications.yaml
    threshold_99_percent.yaml
    invalid_missing_reader.yaml
    invalid_unknown_reader.yaml
    invalid_fuzzy_no_tolerance_type.yaml
    invalid_fuzzy_no_tolerance_value.yaml
    invalid_missing_comparison_target.yaml
```

### 1.3 Test Data Strategy

Per BRD Section 15 and the ATC POC3 Alignment document (Section 6), test data must exercise realistic variance between "original" and "rewritten" outputs. For Proofmark's own test suite, this means:

- **Parquet fixtures**: Generated using `pyarrow` with deliberate schema and value differences where needed. The generation script is checked in and reviewable, but the fixtures themselves are also checked in so tests don't depend on runtime generation.
- **CSV fixtures**: Hand-crafted where precision matters (null representations, line endings, encoding). Generated for larger row counts.
- **Tolerance test data**: Created with different rounding libraries/modes. LHS uses `ROUND_HALF_UP`, RHS uses `ROUND_HALF_EVEN` for the same input values. This produces realistic floating-point variance, not hand-tweaked numbers.
- **Fixture generation script**: A standalone script at `tests/fixtures/generate_fixtures.py` that produces all fixture files. The script is part of the test infrastructure, not the application. It runs once during test data management (SDLC step 4), and its output is committed.

### 1.4 BRD Traceability Matrix

Every BDD scenario below includes `[BR-x.x]` references to specific BRD v3 requirements. The full traceability:

| BRD v3 Section | Feature Area(s) | Scenario Count |
|---|---|---|
| 3.4 Two Readers | parquet_reader, csv_reader | 7 |
| 3.5 Parquet Part Files | parquet_reader | 3 |
| 4 Comparison Pipeline (Pre-check) | line_break_check | 3 |
| 4 Comparison Pipeline (Step 1) | parquet_reader, csv_reader | 2 |
| 4 Comparison Pipeline (Step 2) | schema_validation | 4 |
| 4 Comparison Pipeline (Steps 3-6) | hash_sort_diff, row_count | 6 |
| 5 Column Classification | column_classification | 6 |
| 5 Column Classification (validation) | config_validation | 3 |
| 6 Configuration | config_validation | 8 |
| 7 Tolerance Specification | column_classification, tolerance_edge_cases | 5 |
| 8 Null Handling | null_handling | 6 |
| 9 Encoding | encoding | 2 |
| 11 Report Output | report_output | 9 |
| 12 CLI Interface | cli | 5 |

Total: 66 BDD scenarios across 12 feature areas, plus 12 integration tests for the queue runner (Part 3).

### 1.5 Match Percentage Formula

BRD v3.1 defines the match percentage explicitly (BR-11.13 through BR-11.18). This formula governs all report scenarios:

- **Per hash group**: hash-matched pairs = `min(lhs_count, rhs_count)`. If FUZZY columns exist, pairs failing FUZZY validation are reclassified as unmatched. Final matched for group = `(hash-matched pairs - fuzzy-failed pairs) × 2`
- **Surplus per group**: `|lhs_count - rhs_count|` from count mismatch, PLUS `fuzzy-failed pairs × 2`
- **Rows unique to one side**: 0 matched, all surplus
- **Total rows**: `lhs_row_count + rhs_row_count`
- **Match %**: `total_matched / total_rows`
- **Report match_count**: single-counted = `total_matched / 2` (the number of matched row pairs, not the double-counted internal value)
- **Report mismatch_count**: `max(lhs_row_count, rhs_row_count) - match_count`
- **Special case**: When `total_rows = 0` (both sides have zero data rows), match % = 100.0 by definition. Both sides produced equivalent output (nothing). This is PASS.

**Example (hash mismatch):** LHS has 100 rows, RHS has 100 rows. 99 hash groups match (1 on each side). 1 hash group exists only on LHS, 1 only on RHS.
- Matched: 99 × 2 = 198
- Surplus: 1 (LHS only) + 1 (RHS only) = 2
- Total rows: 100 + 100 = 200
- Match %: 198 / 200 = 99.0%
- Report: match_count: 99, mismatch_count: 1

**Example (FUZZY mismatch):** LHS has 100 rows, RHS has 100 rows. All 100 hash groups match (1:1). 3 pairs fail FUZZY tolerance.
- Matched: (100 - 3) × 2 = 194
- Surplus: 3 × 2 = 6
- Total rows: 200
- Match %: 194 / 200 = 97.0%
- Report: match_count: 97, mismatch_count: 3

### 1.6 PASS/FAIL Conditions

BRD v3.1 defines PASS as ALL of the following (BR-11.25):

1. Match % >= configured threshold (governs ALL row-level equivalence — both hash-level mismatches and FUZZY tolerance violations reduce match %)
2. No schema mismatch (auto-fail)
3. No line break style mismatch (CSV only) (auto-fail)
4. No header mismatch (CSV only) (auto-fail)
5. No trailer mismatch (CSV only) (auto-fail)

FAIL is anything else (BR-11.26). FUZZY tolerance violations are first-class mismatches that reduce match_count and match_percentage — they are NOT a separate pass/fail gate. The four auto-fail conditions are structural problems that cannot be meaningfully captured by a percentage.

### 1.7 pytest Conventions

**Markers:**

```python
@pytest.mark.parquet       # Requires parquet fixtures
@pytest.mark.csv           # Requires CSV fixtures
@pytest.mark.slow          # Tests with large fixture files (run separately in CI)
@pytest.mark.cli           # End-to-end CLI invocation tests
@pytest.mark.queue         # Requires PostgreSQL for queue runner tests
```

**conftest.py patterns:**

```python
# Root conftest.py provides:
# - Path fixtures for test data directories
# - Config builder helpers (generate valid YAML configs programmatically)
# - Report parsing helpers (load JSON report, assert on structure)
# - Temporary directory fixtures for output files

@pytest.fixture
def fixtures_dir():
    """Root path to tests/fixtures/."""

@pytest.fixture
def parquet_fixtures(fixtures_dir):
    """Path to tests/fixtures/parquet/."""

@pytest.fixture
def csv_fixtures(fixtures_dir):
    """Path to tests/fixtures/csv/."""

@pytest.fixture
def config_fixtures(fixtures_dir):
    """Path to tests/fixtures/configs/."""

@pytest.fixture
def tmp_config(tmp_path):
    """Factory fixture: builds a YAML config file in tmp_path, returns path.
    Config defines HOW to compare (reader, classifications, tolerances,
    encoding, threshold). Does NOT include LHS/RHS paths (those are CLI args)."""

@pytest.fixture
def run_comparison():
    """Invokes the comparison pipeline programmatically.
    Accepts config_path, lhs_path, rhs_path. Returns report dict."""

@pytest.fixture
def run_cli(tmp_path):
    """Invokes proofmark CLI as subprocess.
    Runs: proofmark compare --config <path> --left <path> --right <path>
    Returns (exit_code, stdout, stderr)."""
```

**Fixture naming:** Fixtures that provide paths end in `_dir` or `_path`. Fixtures that provide data end in `_data`. Factory fixtures are verbs (`run_comparison`, `build_config`).

**Test naming:** `test_{what_is_being_tested}_{expected_outcome}`. Examples:
- `test_parquet_3parts_vs_1part_passes`
- `test_csv_data_mismatch_fails_with_detail`
- `test_fuzzy_absolute_within_tolerance_passes`

---

## Part 2: BDD Scenarios

### Feature: Parquet Reader

#### Scenario: Identical data across different part file counts passes [BR-3.15, BR-3.16]

```gherkin
Given a parquet LHS directory with 3 part files containing rows:
    | account_id | balance  | status |
    | 1001       | 5000.00  | active |
    | 1002       | 3200.50  | active |
    | 1003       | 0.00     | closed |
And a parquet RHS directory with 1 part file containing the same 3 rows
And a config with reader "parquet" and no column overrides
When I run the comparison with --left and --right pointing to those directories
Then the result is PASS
And the report summary shows row_count_lhs: 3, row_count_rhs: 3, match_count: 3, mismatch_count: 0
And match_percentage is 100.0
```

#### Scenario: Identical data in matching part file counts passes [BR-3.7, BR-3.8, BR-3.9]

```gherkin
Given a parquet LHS directory with 1 part file containing rows:
    | id | name    | amount |
    | 1  | Alice   | 100.00 |
    | 2  | Bob     | 200.00 |
And a parquet RHS directory with 1 part file containing the same 2 rows
And a config with reader "parquet" and no column overrides
When I run the comparison
Then the result is PASS
And the report summary shows match_count: 2, mismatch_count: 0
```

#### Scenario: Data difference detected and reported with detail [BR-3.7, BR-11.9]

```gherkin
Given a parquet LHS directory with 1 part file containing rows:
    | account_id | balance |
    | 1001       | 5000.00 |
    | 1002       | 3200.50 |
And a parquet RHS directory with 1 part file containing rows:
    | account_id | balance |
    | 1001       | 5000.00 |
    | 1002       | 3200.99 |
And a config with reader "parquet" and no column overrides
When I run the comparison
Then the result is FAIL
And the report summary shows match_count: 1, mismatch_count: 1
And the mismatches section contains a hash group with lhs_count: 1, rhs_count: 0
And a hash group with lhs_count: 0, rhs_count: 1
```

#### Scenario: Empty LHS directory produces an error [BR-3.15, BR-4.7]

```gherkin
Given a parquet LHS directory containing no parquet files
And a parquet RHS directory with 1 part file containing 1 row
And a config with reader "parquet"
When I run the comparison
Then the result is an error (exit code 2)
And the error message indicates LHS contains no parquet files
```

---

### Feature: CSV Reader

#### Scenario: Simple CSV with header, data matches [BR-3.10, BR-3.11]

```gherkin
Given a CSV LHS file with content:
    account_id,balance,status
    1001,5000.00,active
    1002,3200.50,active
And a CSV RHS file with identical content
And a config with reader "csv", header_rows: 1, trailer_rows: 0
When I run the comparison
Then the result is PASS
And the report summary shows match_count: 2, mismatch_count: 0
```

#### Scenario: CSV with trailing control record, data matches [BR-3.11, BR-3.13]

```gherkin
Given a CSV LHS file with content:
    account_id,balance,status
    1001,5000.00,active
    1002,3200.50,active
    TRAILER|2|2026-02-28
And a CSV RHS file with identical content
And a config with reader "csv", header_rows: 1, trailer_rows: 1
When I run the comparison
Then the result is PASS
And the report summary shows match_count: 2, mismatch_count: 0
And the header_trailer_comparison section shows all headers and trailers match
```

#### Scenario: CSV header row difference detected [BR-3.13, BR-3.14]

```gherkin
Given a CSV LHS file with header row "account_id,balance,status"
And a CSV RHS file with header row "account_id,balance,state"
And both files have identical data rows
And a config with reader "csv", header_rows: 1, trailer_rows: 0
When I run the comparison
Then the result is FAIL
And the report header_trailer_comparison indicates a header mismatch: row 1 differs between LHS and RHS
```

#### Scenario: CSV trailer row difference detected [BR-3.13, BR-3.14]

```gherkin
Given a CSV LHS file with trailer row "TRAILER|2|2026-02-28"
And a CSV RHS file with trailer row "TRAILER|2|2026-02-27"
And both files have identical header and data rows
And a config with reader "csv", header_rows: 1, trailer_rows: 1
When I run the comparison
Then the result is FAIL
And the report header_trailer_comparison indicates a trailer mismatch between LHS and RHS
```

#### Scenario: CSV data mismatch in body [BR-3.10, BR-11.9]

```gherkin
Given a CSV LHS file with content:
    account_id,balance
    1001,5000.00
    1002,3200.50
And a CSV RHS file with content:
    account_id,balance
    1001,5000.00
    1002,3200.99
And a config with reader "csv", header_rows: 1, trailer_rows: 0
When I run the comparison
Then the result is FAIL
And the report summary shows match_count: 1, mismatch_count: 1
And the mismatches section contains unmatched hash groups for the differing rows
```

---

### Feature: Schema Validation

#### Scenario: Matching schemas pass validation [BR-4.9]

```gherkin
Given a parquet LHS directory with columns: account_id (int64), balance (float64), status (string)
And a parquet RHS directory with columns: account_id (int64), balance (float64), status (string)
And a config with reader "parquet"
When I run the comparison
Then schema validation passes
And the comparison proceeds to the hash-sort-diff pipeline
```

#### Scenario: Column count mismatch fails with exit code 1 [BR-4.9, BR-4.10]

```gherkin
Given a parquet LHS directory with columns: account_id, balance, status
And a parquet RHS directory with columns: account_id, balance
And a config with reader "parquet"
When I run the comparison
Then the result is FAIL (exit code 1)
And the report indicates a schema mismatch: LHS has 3 columns, RHS has 2 columns
```

#### Scenario: Column name mismatch fails with exit code 1 [BR-4.9, BR-4.11]

```gherkin
Given a parquet LHS directory with columns: account_id, balance, status
And a parquet RHS directory with columns: account_id, balance, state
And a config with reader "parquet"
When I run the comparison
Then the result is FAIL (exit code 1)
And the report indicates a schema mismatch: column name "status" vs "state"
```

#### Scenario: Column type mismatch fails with exit code 1 (parquet only) [BR-4.12, BR-4.13]

```gherkin
Given a parquet LHS directory with column balance typed as float64
And a parquet RHS directory with column balance typed as int32
And a config with reader "parquet"
When I run the comparison
Then the result is FAIL (exit code 1)
And the report indicates a schema mismatch: column "balance" type float64 vs int32
Note: CSV schema validation is limited to column count and header names per BR-4.13
```

---

### Feature: Column Classification

#### Scenario: All columns default to STRICT when no column config provided [BR-5.5, BR-5.9]

```gherkin
Given a parquet LHS and RHS with matching columns: account_id, balance, status
And a config with no columns section
When I run the comparison
Then all columns are classified as STRICT in the report's column_classification section
And the comparison uses byte-level exact match for every column
```

#### Scenario: EXCLUDED column dropped before hashing [BR-5.2, BR-5.3, BR-4.14]

```gherkin
Given a parquet LHS with rows:
    | run_id                               | account_id | balance |
    | a1b2c3d4-e5f6-7890-abcd-ef1234567890 | 1001       | 5000.00 |
And a parquet RHS with rows:
    | run_id                               | account_id | balance |
    | ffffffff-ffff-ffff-ffff-ffffffffffff | 1001       | 5000.00 |
And a config with excluded columns: [{name: run_id, reason: "Non-deterministic UUID"}]
When I run the comparison
Then the result is PASS
And the report column_classification shows run_id as EXCLUDED with reason "Non-deterministic UUID"
And the mismatches section is empty
```

#### Scenario: FUZZY absolute tolerance within threshold passes [BR-7.1, BR-7.2]

```gherkin
Given a parquet LHS with rows:
    | account_id | interest_accrued |
    | 1001       | 100.005          |
And a parquet RHS with rows:
    | account_id | interest_accrued |
    | 1001       | 100.004          |
And a config with fuzzy columns:
    [{name: interest_accrued, tolerance: 0.01, tolerance_type: absolute, reason: "Rounding variance"}]
When I run the comparison
Then the result is PASS
And the report summary shows mismatch_count: 0
```

#### Scenario: FUZZY relative tolerance within threshold passes [BR-7.1, BR-7.3]

```gherkin
Given a parquet LHS with rows:
    | account_id | market_value |
    | 1001       | 1000000.00   |
And a parquet RHS with rows:
    | account_id | market_value |
    | 1001       | 1000000.50   |
And a config with fuzzy columns:
    [{name: market_value, tolerance: 0.001, tolerance_type: relative, reason: "Scales with magnitude"}]
When I run the comparison
Then the result is PASS
Because |1000000.00 - 1000000.50| / max(|1000000.00|, |1000000.50|) = 0.0000005, which is <= 0.001
```

#### Scenario: FUZZY tolerance exceeded reports mismatch with delta [BR-7.1, BR-11.9]

```gherkin
Given a parquet LHS with rows:
    | account_id | interest_accrued |
    | 1001       | 100.00           |
And a parquet RHS with rows:
    | account_id | interest_accrued |
    | 1001       | 100.05           |
And a config with fuzzy columns:
    [{name: interest_accrued, tolerance: 0.01, tolerance_type: absolute, reason: "Rounding variance"}]
When I run the comparison
Then the result is FAIL
And the mismatches section contains an entry with:
    column: "interest_accrued"
    value_lhs: "100.00"
    value_rhs: "100.05"
    tolerance: 0.01
    tolerance_type: "absolute"
    actual_delta: 0.05
```

#### Scenario: Mixed classification on same target [BR-5.1, BR-5.5]

```gherkin
Given a parquet LHS with rows:
    | run_id    | account_id | balance | interest_accrued |
    | uuid-aaa  | 1001       | 5000.00 | 100.005          |
And a parquet RHS with rows:
    | run_id    | account_id | balance | interest_accrued |
    | uuid-bbb  | 1001       | 5000.00 | 100.004          |
And a config with:
    excluded: [{name: run_id, reason: "Non-deterministic UUID"}]
    fuzzy: [{name: interest_accrued, tolerance: 0.01, tolerance_type: absolute, reason: "Rounding"}]
When I run the comparison
Then the result is PASS
And the report column_classification shows:
    run_id as EXCLUDED
    account_id as STRICT (default)
    balance as STRICT (default)
    interest_accrued as FUZZY
And the mismatches section is empty
```

---

### Feature: Null Handling

#### Scenario: Parquet null vs null matches [BR-8.1]

```gherkin
Given a parquet LHS with a row where column "notes" is null (native parquet null)
And a parquet RHS with a row where column "notes" is null (native parquet null)
And a config with reader "parquet" and no column overrides
When I run the comparison
Then the result is PASS
And the row with the null column is counted as a match
```

#### Scenario: Parquet null vs empty string is a mismatch [BR-8.1, BR-8.4]

```gherkin
Given a parquet LHS with a row where column "notes" is null (native parquet null)
And a parquet RHS with a row where column "notes" is "" (empty string)
And a config with reader "parquet" and no column overrides
When I run the comparison
Then the result is FAIL
And the mismatches section contains an entry with column "notes", value_lhs: null, value_rhs: ""
```

#### Scenario: CSV empty field vs literal "NULL" is a mismatch [BR-8.2, BR-8.3]

```gherkin
Given a CSV LHS with content:
    id,status
    1,
And a CSV RHS with content:
    id,status
    1,NULL
And a config with reader "csv", header_rows: 1, trailer_rows: 0
When I run the comparison
Then the result is FAIL
And the mismatches section contains an entry with column "status"
Because byte-level comparison treats empty field and literal "NULL" as different values
```

#### Scenario: CSV different null-like representations are all distinct [BR-8.2]

```gherkin
Given a CSV LHS with content:
    id,value
    1,NULL
And a CSV RHS with content:
    id,value
    1,null
And a config with reader "csv", header_rows: 1, trailer_rows: 0
When I run the comparison
Then the result is FAIL
Because "NULL" and "null" are different byte sequences
```

#### Scenario: Parquet null vs null in FUZZY column matches [BR-8.1, BR-4.21]

```gherkin
Given a parquet LHS with rows:
    | account_id | balance |
    | 1001       | None    |
And a parquet RHS with rows:
    | account_id | balance |
    | 1001       | None    |
And a config with fuzzy columns:
    [{name: balance, tolerance: 0.01, tolerance_type: absolute, reason: "Rounding"}]
When I run the comparison
Then the result is PASS
And the FUZZY tolerance check is skipped for the null-vs-null pair
Because both values are null — no numeric comparison is needed [FSD-5.7.8]
```

#### Scenario: Parquet null vs non-null in FUZZY column is a mismatch [BR-8.1, BR-4.21]

```gherkin
Given a parquet LHS with rows:
    | account_id | balance |
    | 1001       | None    |
And a parquet RHS with rows:
    | account_id | balance |
    | 1001       | 100.00  |
And a config with fuzzy columns:
    [{name: balance, tolerance: 0.01, tolerance_type: absolute, reason: "Rounding"}]
When I run the comparison
Then the result is FAIL
And the mismatches section contains a FUZZY failure for column "balance"
And actual_delta equals abs(100.00) = 100.0
And match_count: 0, mismatch_count: 1, match_percentage: 0.0
Because null vs non-null is a FUZZY failure regardless of tolerance [FSD-5.7.8]
```

---

### Feature: Hash and Sort Pipeline

#### Scenario: Row order independence --- same data, different order passes [BR-4.17, BR-4.18]

```gherkin
Given a parquet LHS with rows:
    | account_id | balance |
    | 1001       | 5000.00 |
    | 1002       | 3200.50 |
    | 1003       | 0.00    |
And a parquet RHS with the same rows in a different order:
    | account_id | balance |
    | 1003       | 0.00    |
    | 1001       | 5000.00 |
    | 1002       | 3200.50 |
And a config with reader "parquet" and no column overrides
When I run the comparison
Then the result is PASS
And the report summary shows match_count: 3, mismatch_count: 0
```

#### Scenario: Duplicate rows --- multiset comparison [BR-4.22]

```gherkin
Given a parquet LHS with rows:
    | account_id | balance |
    | 1001       | 5000.00 |
    | 1001       | 5000.00 |
And a parquet RHS with rows:
    | account_id | balance |
    | 1001       | 5000.00 |
And a config with reader "parquet" and no column overrides
When I run the comparison
Then the result is FAIL
And the report summary shows row_count_lhs: 2, row_count_rhs: 1
Because multiset comparison requires identical row multiplicity
Per match formula: matched = min(2,1) × 2 = 2, total = 2 + 1 = 3, match % = 66.7%
```

#### Scenario: EXCLUDED columns do not affect hash-based ordering [BR-4.14, BR-4.16]

```gherkin
Given a parquet LHS with rows:
    | uuid       | account_id | balance |
    | aaa-111    | 1001       | 5000.00 |
    | aaa-222    | 1002       | 3200.50 |
And a parquet RHS with rows (different UUIDs, different order):
    | uuid       | account_id | balance |
    | bbb-999    | 1002       | 3200.50 |
    | bbb-888    | 1001       | 5000.00 |
And a config with excluded: [{name: uuid, reason: "Non-deterministic"}]
When I run the comparison
Then the result is PASS
Because UUIDs are excluded before hashing, so hash-sort ordering is based on account_id and balance only
```

---

### Feature: Line Break Check

#### Scenario: Mismatched line breaks set FAIL flag but comparison continues [BR-4.1, BR-4.2, BR-4.4, BR-4.5]

```gherkin
Given a CSV LHS file with CRLF line endings
And a CSV RHS file with LF line endings
And both files have identical field values
And a config with reader "csv"
When I run the comparison
Then the result is FAIL
And the report summary shows line_break_mismatch: true
And the report summary still shows the full match percentage from the data comparison
Because line break mismatch is a file-level FAIL flag; the comparison runs to completion regardless
```

#### Scenario: Matching line breaks produce no flag [BR-4.1]

```gherkin
Given a CSV LHS file with LF line endings
And a CSV RHS file with LF line endings
And both files have identical field values
And a config with reader "csv"
When I run the comparison
Then the result is PASS
And the report summary shows line_break_mismatch: false (or field absent)
```

#### Scenario: Line break check does not apply to parquet [BR-4.6]

```gherkin
Given a parquet LHS directory with identical data to the RHS directory
And a config with reader "parquet"
When I run the comparison
Then the result is PASS
And the report summary does not contain a line_break_mismatch field
```

---

### Feature: Encoding

#### Scenario: Configured encoding reads files correctly [BR-9.1, BR-9.4]

```gherkin
Given a CSV LHS file encoded in UTF-8 containing the character 'e' with acute accent
And a CSV RHS file encoded in UTF-8 containing the same character
And a config with reader "csv", encoding: "utf-8"
When I run the comparison
Then the result is PASS
Because both files are read with the same configured encoding
```

#### Scenario: Invalid encoding produces error [BR-9.2]

```gherkin
Given a CSV LHS file encoded in UTF-8 containing multi-byte characters
And a config with reader "csv", encoding: "ascii"
When I run the comparison
Then the result is an error (exit code 2)
And the error message indicates an encoding failure
```

---

### Feature: Tolerance Edge Cases

#### Scenario: Both values zero with relative tolerance matches [BR-7.4]

```gherkin
Given a parquet LHS with rows:
    | account_id | delta |
    | 1001       | 0.0   |
And a parquet RHS with rows:
    | account_id | delta |
    | 1001       | 0.0   |
And a config with fuzzy columns:
    [{name: delta, tolerance: 0.01, tolerance_type: relative, reason: "Zero edge case"}]
When I run the comparison
Then the result is PASS
Because both values are zero, delta is zero
```

#### Scenario: One value zero, other non-zero with relative tolerance [BR-7.5]

```gherkin
Given a parquet LHS with rows:
    | account_id | delta  |
    | 1001       | 0.0    |
And a parquet RHS with rows:
    | account_id | delta  |
    | 1001       | 0.0001 |
And a config with fuzzy columns:
    [{name: delta, tolerance: 0.01, tolerance_type: relative, reason: "Zero edge case"}]
When I run the comparison
Then the result is FAIL
Because |0.0 - 0.0001| / max(|0.0|, |0.0001|) = 1.0, which exceeds tolerance 0.01
And the mismatches section contains an entry with actual_delta showing the relative difference
```

#### Scenario: Tolerance type missing on FUZZY column errors [BR-7.6, BR-6.5]

```gherkin
Given a config YAML with a fuzzy column entry:
    - name: interest_accrued
      tolerance: 0.01
      reason: "Rounding variance"
And tolerance_type is NOT specified
When I attempt to parse the config
Then the result is an error (exit code 2)
And the error message indicates tolerance_type is required for FUZZY column "interest_accrued"
```

#### Scenario: Tolerance value missing on FUZZY column errors [BR-7.7, BR-6.5]

```gherkin
Given a config YAML with a fuzzy column entry:
    - name: interest_accrued
      tolerance_type: absolute
      reason: "Rounding variance"
And tolerance (the numeric value) is NOT specified
When I attempt to parse the config
Then the result is an error (exit code 2)
And the error message indicates tolerance value is required for FUZZY column "interest_accrued"
```

#### Scenario: Non-numeric FUZZY column data produces ConfigError at runtime [BR-4.21, FSD-5.7.5]

```gherkin
Given a parquet LHS with rows:
    | account_id | status |
    | 1001       | active |
And a parquet RHS with rows:
    | account_id | status |
    | 1001       | active |
And a config with fuzzy columns:
    [{name: status, tolerance: 0.01, tolerance_type: absolute, reason: "Rounding"}]
When I run the comparison
Then the process exit code is 2
And stderr contains a ConfigError indicating FUZZY column "status" contains non-numeric value "active"
Because FUZZY columns must contain numeric data for tolerance comparison [FSD-5.7.5]
Note: The float() conversion raises ValueError internally; the tolerance module catches and wraps it as ConfigError
```

---

### Feature: Report Output

#### Scenario: Report contains required metadata and structure [BR-11.1 through BR-11.5]

```gherkin
Given any valid comparison that runs to completion
When I examine the JSON report
Then the report contains a "metadata" section with: timestamp, proofmark_version, comparison_target, config_path
And the report contains a "config_echo" section with the full configuration used
And the report contains a "column_classification" section listing EXCLUDED, STRICT, and FUZZY columns
And the report contains a "summary" section with: row_count_lhs, row_count_rhs, match_count, mismatch_count, match_percentage, result, threshold
And the report contains a "mismatches" section (empty list if no mismatches)
```

#### Scenario: All mismatches shown regardless of pass/fail stamp [BR-11.24]

```gherkin
Given a parquet comparison target where LHS and RHS each have 100 rows and 1 row differs
And a config with threshold: 99.0
When I run the comparison
Then the result is PASS
Per formula: matched = 99 × 2 = 198, total = 200, match % = 99.0% >= 99.0% threshold
And the mismatches section contains the unmatched hash groups
And the mismatches section is NOT suppressed by the PASS result
```

#### Scenario: Threshold 100% with any mismatch fails [BR-11.23, BR-11.25]

```gherkin
Given a parquet comparison target where LHS and RHS each have 1000 rows and 1 row differs
And a config with threshold: 100.0 (or threshold omitted, since 100.0 is the default)
When I run the comparison
Then the result is FAIL
Per formula: matched = 999 × 2 = 1998, total = 2000, match % = 99.9% < 100.0%
And the mismatches section contains the unmatched hash groups
```

#### Scenario: Threshold below 100% with mismatches within threshold passes [BR-11.22, BR-11.25]

```gherkin
Given a parquet comparison target where LHS and RHS each have 200 rows and 2 rows differ
And a config with threshold: 99.0
When I run the comparison
Then the result is PASS
Per formula: matched = 198 × 2 = 396, total = 400, match % = 99.0% >= 99.0%
And the mismatches section contains exactly the unmatched hash groups
```

#### Scenario: Column classification with justifications echoed in report [BR-11.4, BR-5.3, BR-5.8]

```gherkin
Given a config with:
    excluded: [{name: run_id, reason: "Non-deterministic UUID assigned at runtime"}]
    fuzzy: [{name: interest_accrued, tolerance: 0.01, tolerance_type: absolute, reason: "Spark vs ADF rounding"}]
And columns account_id and balance exist but are not in the config (STRICT by default)
When I run a comparison and examine the report
Then the column_classification section shows:
    EXCLUDED: run_id with reason "Non-deterministic UUID assigned at runtime"
    STRICT: account_id, balance
    FUZZY: interest_accrued with reason "Spark vs ADF rounding", tolerance 0.01, tolerance_type "absolute"
```

#### Scenario: Line break mismatch causes FAIL even with 100% data match [BR-11.25, BR-4.2]

```gherkin
Given a CSV LHS file with CRLF line endings
And a CSV RHS file with LF line endings
And both files have identical field values (all data matches perfectly)
And a config with reader "csv"
When I run the comparison
Then the result is FAIL
And the report summary shows match_percentage: 100.0
And the report summary shows line_break_mismatch: true
Because PASS requires no line break mismatch, even when all data matches
```

#### Scenario: FUZZY tolerance failure reduces match percentage [BR-11.25, BR-4.21]

```gherkin
Given a parquet LHS with rows:
    | account_id | balance |
    | 1001       | 100.00  |
And a parquet RHS with rows:
    | account_id | balance |
    | 1001       | 100.50  |
And a config with fuzzy columns:
    [{name: balance, tolerance: 0.01, tolerance_type: absolute, reason: "Rounding"}]
And account_id is STRICT (default)
When I run the comparison
Then the hash is computed on account_id only (balance is FUZZY, excluded from hash)
And the hash groups match (same account_id on both sides) — 1 pair at hash level
But |100.00 - 100.50| = 0.50 exceeds the absolute tolerance of 0.01
So the pair is reclassified as unmatched (FUZZY failure is a first-class mismatch)
And the report summary shows match_count: 0, mismatch_count: 1, match_percentage: 0.0
And the result is FAIL
And the mismatches section shows the FUZZY column failure with actual_delta: 0.50
Per match formula: hash-matched pairs = 1, fuzzy-failed pairs = 1, final matched = (1-1) × 2 = 0, total = 2, match % = 0.0%
```

#### Scenario: Mismatch correlation pairs rows differing in few columns [BR-11.10]

```gherkin
Given a parquet LHS with rows:
    | account_id | balance | status |
    | 1001       | 5000.00 | active |
    | 1002       | 3200.50 | active |
And a parquet RHS with rows:
    | account_id | balance | status |
    | 1001       | 5000.00 | active |
    | 1002       | 3200.99 | active |
And a config with reader "parquet" and no column overrides (all STRICT)
When I run the comparison
Then the result is FAIL
And the mismatches section correlates the unmatched LHS row (1002, 3200.50) with the unmatched RHS row (1002, 3200.99)
Because the rows share 2 of 3 column values, providing high correlation confidence
```

#### Scenario: Low correlation confidence falls back to separate lists [BR-11.11]

```gherkin
Given a parquet LHS with rows:
    | account_id | balance | status |
    | 1001       | 5000.00 | active |
    | 9999       | 0.01    | closed |
And a parquet RHS with rows:
    | account_id | balance | status |
    | 1001       | 5000.00 | active |
    | 8888       | 99999.00| pending|
And a config with reader "parquet" and no column overrides (all STRICT)
When I run the comparison
Then the result is FAIL
And the mismatches section presents unmatched LHS rows and unmatched RHS rows as separate lists
Because the unmatched rows share no column values, so correlation confidence is low
```

---

### Feature: CLI Interface

#### Scenario: Exit code 0 on PASS [BR-12.6]

```gherkin
Given a valid config and identical parquet LHS/RHS directories
When I run `proofmark compare --config path/to/config.yaml --left path/to/lhs --right path/to/rhs`
Then the process exit code is 0
And stdout contains a valid JSON report with result: "PASS"
```

#### Scenario: Exit code 1 on FAIL [BR-12.7]

```gherkin
Given a valid config and parquet LHS/RHS directories with data mismatches
When I run `proofmark compare --config path/to/config.yaml --left path/to/lhs --right path/to/rhs`
Then the process exit code is 1
And stdout contains a valid JSON report with result: "FAIL"
```

#### Scenario: Exit code 2 on error [BR-12.8]

```gherkin
Given a config file that references reader "parquet"
And the --left path does not exist
When I run `proofmark compare --config path/to/config.yaml --left /nonexistent --right path/to/rhs`
Then the process exit code is 2
And stderr contains an error message indicating the missing path
And stdout does not contain a JSON report
```

#### Scenario: Output to file with --output flag [BR-12.4]

```gherkin
Given a valid config and identical parquet LHS/RHS directories
When I run `proofmark compare --config path/to/config.yaml --left path/to/lhs --right path/to/rhs --output /tmp/report.json`
Then the process exit code is 0
And /tmp/report.json contains a valid JSON report with result: "PASS"
And stdout is empty (report goes to file, not stdout)
```

#### Scenario: Config flag is required [BR-12.1]

```gherkin
When I run `proofmark compare` without a --config flag
Then the process exit code is 2
And stderr contains a usage error indicating --config is required
```

---

### Feature: Configuration Validation

#### Scenario: Valid YAML config parses without error [BR-6.1 through BR-6.5]

```gherkin
Given a YAML config file with all required fields:
    comparison_target: "test_target"
    reader: "parquet"
When I parse the config
Then no validation error is raised
And the config object has comparison_target "test_target", reader "parquet"
```

#### Scenario: Missing required field produces error [BR-6.6]

```gherkin
Given a YAML config file missing the "reader" field
When I attempt to parse the config
Then a validation error is raised indicating "reader" is a required field
```

#### Scenario: Unknown reader type produces error [BR-3.6]

```gherkin
Given a YAML config file with reader: "excel"
When I attempt to parse the config
Then a validation error is raised indicating "excel" is not a valid reader type
And the error message lists valid reader types: "csv", "parquet"
```

#### Scenario: FUZZY column without tolerance_type produces error [BR-7.6]

```gherkin
Given a YAML config file with a fuzzy column:
    - name: balance
      tolerance: 0.01
      reason: "Rounding"
And tolerance_type is not present
When I attempt to parse the config
Then a validation error is raised indicating tolerance_type is required for FUZZY column "balance"
```

#### Scenario: FUZZY column without tolerance value produces error [BR-7.7]

```gherkin
Given a YAML config file with a fuzzy column:
    - name: balance
      tolerance_type: absolute
      reason: "Rounding"
And tolerance (numeric value) is not present
When I attempt to parse the config
Then a validation error is raised indicating tolerance is required for FUZZY column "balance"
```

#### Scenario: EXCLUDED column without reason produces error [BR-5.3, BR-6.6]

```gherkin
Given a YAML config file with an excluded column:
    - name: run_id
And reason is not present
When I attempt to parse the config
Then a validation error is raised indicating reason is required for EXCLUDED column "run_id"
```

#### Scenario: FUZZY column without reason produces error [BR-5.8, BR-6.6]

```gherkin
Given a YAML config file with a fuzzy column:
    - name: balance
      tolerance: 0.01
      tolerance_type: absolute
And reason is not present
When I attempt to parse the config
Then a validation error is raised indicating reason is required for FUZZY column "balance"
```

#### Scenario: Column appearing in both EXCLUDED and FUZZY lists produces error [BR-5.1]

```gherkin
Given a YAML config file with:
    excluded:
        - name: balance
          reason: "Non-deterministic"
    fuzzy:
        - name: balance
          tolerance: 0.01
          tolerance_type: absolute
          reason: "Rounding"
When I attempt to parse the config
Then a validation error is raised indicating column "balance" appears in multiple classification lists
Because BR-5.1 requires every column to belong to exactly one tier
```

#### Scenario: Threshold out of range produces error [BR-11.22, FSD-5.2.11]

```gherkin
Given a YAML config file with threshold: 101.0
When I attempt to parse the config
Then a validation error is raised indicating threshold must be between 0.0 and 100.0
Because BR-11.22 requires deterministic threshold comparison within a valid range
```

#### Scenario: Negative threshold produces error [BR-11.22, FSD-5.2.11]

```gherkin
Given a YAML config file with threshold: -5.0
When I attempt to parse the config
Then a validation error is raised indicating threshold must be between 0.0 and 100.0
```

#### Scenario: Negative FUZZY tolerance produces error [FSD-5.2.11a]

```gherkin
Given a YAML config file with a fuzzy column:
    - name: balance
      tolerance: -0.01
      tolerance_type: absolute
      reason: "Rounding"
When I attempt to parse the config
Then a validation error is raised indicating tolerance must be >= 0.0 for FUZZY column "balance"
Because a negative tolerance is nonsensical — it would reject all matches
```

---

### Feature: Row Count

#### Scenario: Different row counts between LHS and RHS [BR-4.18, BR-4.20, BR-11.17]

```gherkin
Given a parquet LHS with 100 rows
And a parquet RHS with 99 rows (first 99 rows match LHS)
And a config with reader "parquet" and no column overrides
When I run the comparison
Then the result is FAIL
And the report summary shows row_count_lhs: 100, row_count_rhs: 99
Per formula: matched = 99 × 2 = 198, total = 100 + 99 = 199, match % = 99.5%
And the mismatches section contains 1 unmatched hash group (LHS only)
```

#### Scenario: Both sides have zero data rows — PASS [BR-4.18, BR-11.13, BR-11.18]

```gherkin
Given a parquet LHS directory with 1 part file containing 0 data rows (schema only)
And a parquet RHS directory with 1 part file containing 0 data rows (schema only)
And matching schemas on both sides
And a config with reader "parquet" and no column overrides
When I run the comparison
Then the result is PASS
And the report summary shows row_count_lhs: 0, row_count_rhs: 0, match_count: 0, mismatch_count: 0
And match_percentage is 100.0
Because 0 rows on both sides is equivalence (both produced nothing); match % = 100.0 by definition when total_rows = 0
Note: This is a real scenario — ETL jobs that intentionally produce zero data rows with a trailer or manifest
```

#### Scenario: Same row count, all rows match [BR-4.18]

```gherkin
Given a parquet LHS with 50 rows
And a parquet RHS with the same 50 rows
And a config with reader "parquet" and no column overrides
When I run the comparison
Then the result is PASS
And the report summary shows row_count_lhs: 50, row_count_rhs: 50, match_count: 50, mismatch_count: 0
```

---

## Appendix: Design Decisions Influencing Test Architecture

### Why tests are feature-based, not pipeline-stage-based

The pipeline (load, validate schema, exclude, hash, sort, diff, report) is an implementation detail. If we restructure the pipeline internals, we don't want every test file to move. Feature-based organization means tests survive refactors. A test about FUZZY tolerance doesn't care whether the tolerance check happens in a "diff" module or a "compare" module --- it cares about the observable output.

### Why fixtures are checked in, not generated at test time

1. **Reviewability.** Dan reviews every test case. He needs to see the fixture data, not a generation script he has to mentally execute.
2. **Determinism.** No risk of floating-point differences across platforms or library versions affecting fixture generation.
3. **Speed.** Generating parquet files at test time is wasted work for every test run.
4. **Auditability.** The fixture is the test input. It's an artifact. It belongs in version control.

The generation script exists for reproducibility --- if fixtures need to be regenerated, the script is there. But the fixtures themselves are the source of truth for tests.

### Why CLI tests use subprocess invocation

CLI scenarios test the external interface --- exit codes, stdout/stderr, file creation. These must exercise the actual CLI entry point as a user would invoke it. Internal API tests (`run_comparison` fixture) test the comparison pipeline without process overhead. Both are needed; they test different contracts.

### Why schema validation is a separate feature area

BRD v3 made schema validation an explicit pipeline step (Step 2, BR-4.9 through BR-4.13) with its own exit code behavior (exit code 1, same as data FAIL). In v1 this was implicit. The test architecture reflects this by giving schema validation its own feature area and test file, ensuring column count, name, and type mismatches are each tested independently.

### Why strictness is replaced by line_break_check and encoding

BRD v3 eliminated the configurable strict/normalize toggle for both line breaks and encoding:
- **Line breaks** are now an automatic pre-comparison check (BR-4.1 through BR-4.6). Mismatch sets a FAIL flag but the comparison runs to completion. No configuration needed or allowed.
- **Encoding** is now a single configured value applied to both sides (BR-9.1 through BR-9.5). No normalization across different encodings. The rewrite is responsible for matching the expected encoding.

This simplification removed 2 scenarios (normalize modes) and added 3 (line break pre-check) and 2 (encoding config/error), for a net gain of 3 scenarios but with clearer, more testable behavior.

### Scenarios intentionally NOT included

The following are out of scope per `Documentation/BusinessRequirements/out-of-scope.md` and BRD v3 Section 16:

- Database source comparison (PostgreSQL, Oracle, SQL Server, Synapse)
- Salesforce-specific comparison
- XML, JSON, EBCDIC, binary format readers
- Evidence package assembly
- Batch/orchestration mode
- PII/PCI stripping from reports
- Verbosity flags (BR-12.10)
- Hash algorithm configurability (MVP uses MD5 per BR-10.1)
- CSV dialect configuration (delimiter, quote char, escape char) (BR-14.1)
- Dry-run mode (BR-12.12)
- CLI flags that override config values (BR-12.13)

---

## Part 3: Queue Runner Integration Tests

Queue runner tests live in `test_queue.py` and are **integration tests**, not BDD scenarios. They require a live PostgreSQL instance and are skipped automatically when the database is unreachable. They do not follow the BDD scenario numbering from Part 2 because the queue runner is operational infrastructure, not a business requirement.

### 3.1 Test Infrastructure

**Database configuration:**
- DSN: controlled by `PROOFMARK_TEST_DSN` environment variable. Falls back to the ATC dev database (`host=172.18.0.1 dbname=atc user=claude password=claude`).
- Test table: `control.proofmark_test_queue` — isolated from any production queue table.
- `pytest.importorskip("psycopg2")` — skips the entire file if `psycopg2` is not installed.
- `@skip_no_db` marker — skips individual test classes if PostgreSQL is not reachable at test time.

**Test data:** Queue tests use existing comparison fixtures (`csv/simple_match/` + `configs/csv_simple.yaml`) for tasks that should succeed. Invalid paths (e.g., `/nonexistent/config.yaml`) are used for tasks that should fail.

**Setup/teardown:** Each test class drops and recreates the test table in `setup_method`. This ensures complete isolation between tests — no leftover state from prior runs.

### 3.2 Test Classes and Coverage

| Test Class | Tests | What It Covers | FSD |
|------------|-------|---------------|-----|
| `TestInitDb` | 2 | Table creation, idempotent re-creation | FSD-11.5, FSD-11.10 |
| `TestClaimTask` | 4 | Claim pending task, returns None when empty, skips Running tasks, FIFO ordering | FSD-11.7 |
| `TestMarkResults` | 2 | `mark_succeeded` stores report + result, `mark_failed` stores error message | FSD-11.9, FSD-11.12 |
| `TestWorkerLoop` | 3 | Single task processing, bad config handling (Failed status), multi-task sequential processing | FSD-11.6, FSD-11.9, FSD-11.12 |
| `TestSkipLocked` | 1 | 3 concurrent workers processing 6 tasks — no double-claims, all tasks processed exactly once | FSD-11.7 |

**Total: 12 integration tests across 5 test classes.**

### 3.3 Key Assertions

**`TestInitDb`:**
- `test_creates_table`: Queries `information_schema.columns` to verify the table exists with expected columns (`task_id`, `config_path`, `status`, `result_json`).
- `test_idempotent`: Calls `init_db()` twice — second call must not raise (uses `CREATE TABLE IF NOT EXISTS`).

**`TestClaimTask`:**
- `test_claims_pending_task`: Inserts a task, claims it, verifies returned task matches, confirms DB status is `Running`.
- `test_returns_none_when_empty`: Claims from empty table, asserts `None`.
- `test_skips_running_tasks`: Claims a task (transitions to `Running`), attempts a second claim, asserts `None`.
- `test_fifo_order`: Inserts two tasks, claims one, asserts the first-inserted task was claimed.

**`TestMarkResults`:**
- `test_mark_succeeded`: Claims a task, calls `mark_succeeded()` with a mock report, verifies `status = 'Succeeded'`, `result = 'PASS'`, and `result_json` contains the full report.
- `test_mark_failed`: Claims a task, calls `mark_failed()` with an error string, verifies `status = 'Failed'` and `error_message` is populated.

**`TestWorkerLoop`:**
- `test_processes_single_task`: Starts one worker thread, inserts one task, polls until completion, asserts `Succeeded` with `result = 'PASS'` and `result_json` populated.
- `test_handles_bad_config`: Inserts a task with a nonexistent config path, verifies worker marks it `Failed` with an error message.
- `test_processes_multiple_tasks`: Inserts 3 tasks, starts one worker, waits for all to reach `Succeeded`.

**`TestSkipLocked`:**
- `test_no_double_claim`: Inserts 6 tasks, starts 3 concurrent worker threads, waits for all 6 to complete. Asserts all 6 are `Succeeded` and 0 are `Running` (no stuck tasks from race conditions). This is the integration-level proof that `FOR UPDATE SKIP LOCKED` works correctly under concurrent load.

### 3.4 Running Queue Tests

Queue tests are excluded from default test runs when PostgreSQL is unreachable (via `skip_no_db`). To run them explicitly:

```bash
# With default DSN (ATC dev database)
pytest tests/test_queue.py -v

# With custom DSN
PROOFMARK_TEST_DSN="host=localhost dbname=testdb user=me" pytest tests/test_queue.py -v

# Skip queue tests even when DB is available
pytest --ignore=tests/test_queue.py
```
