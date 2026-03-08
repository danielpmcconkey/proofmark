# Proofmark --- Test Architecture and BDD Scenarios

**Version:** 1.0
**Date:** 2026-02-28
**Status:** Draft --- Pending Dan's Review + Adversarial Review
**Preceding Artifact:** BRD v1.0
**Next Artifact:** Adversarial review of this document, then test data management

---

## Part 1: Test Architecture

### 1.1 Organization

Tests are organized by **feature area**, not by pipeline stage or reader type. Each feature area maps to one or more BRD sections. Feature areas are:

| Feature Area | BRD Sections | Description |
|---|---|---|
| `parquet_reader` | 3.4, 3.5, 4 (Step 1) | Loading and assembling parquet part files |
| `csv_reader` | 3.4, 4 (Step 1) | Loading CSV with header/trailer handling |
| `column_classification` | 5, 7 | Tier 1/2/3 behavior including tolerance math |
| `null_handling` | 8 | Null representation across formats |
| `hash_sort_diff` | 4 (Steps 2-5) | Exclusion, hashing, sorting, row-level diff |
| `strictness` | 9 | Line break and encoding strict/normalize modes |
| `report_output` | 11 | Report structure, content, pass/fail logic |
| `cli` | 12 | Exit codes, output destination, config flag |
| `config_validation` | 6 | YAML parsing, required fields, schema enforcement |
| `row_count` | 4 (Step 5), 11 | Row count mismatch detection |

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
    test_column_classification.py
    test_null_handling.py
    test_hash_sort_diff.py
    test_strictness.py
    test_report_output.py
    test_cli.py
    test_config_validation.py
    test_row_count.py
```

### 1.2 Test Fixtures

Test data lives in `tests/fixtures/` and is version-controlled. No generated fixtures at test time --- everything is deterministic and reviewable.

**Parquet fixtures** (`tests/fixtures/parquet/`):

```
parquet/
    identical_3part_vs_1part/
        source_a/                   # 3 part files, same data
            part-00000.parquet
            part-00001.parquet
            part-00002.parquet
        source_b/                   # 1 part file, coalesced
            part-00000.parquet
    identical_simple/
        source_a/
            part-00000.parquet
        source_b/
            part-00000.parquet
    data_mismatch/
        source_a/
            part-00000.parquet
        source_b/
            part-00000.parquet
    empty_directory/
        source_a/                   # Empty
        source_b/
            part-00000.parquet
    with_nulls/
        source_a/
            part-00000.parquet
        source_b/
            part-00000.parquet
    row_count_mismatch/
        source_a/
            part-00000.parquet      # 100 rows
        source_b/
            part-00000.parquet      # 99 rows
    different_row_order/
        source_a/
            part-00000.parquet      # Rows in order A
        source_b/
            part-00000.parquet      # Same rows, different order
    duplicate_rows/
        source_a/
            part-00000.parquet      # Contains 2 identical rows
        source_b/
            part-00000.parquet      # Contains 1 of that row
```

**CSV fixtures** (`tests/fixtures/csv/`):

```
csv/
    simple_match/
        source_a.csv                # Header + data, no trailer
        source_b.csv
    with_trailer_match/
        source_a.csv                # Header + data + trailer row
        source_b.csv
    data_mismatch/
        source_a.csv
        source_b.csv
    header_mismatch/
        source_a.csv                # Different header text
        source_b.csv
    trailer_mismatch/
        source_a.csv                # Different trailer row count/checksum
        source_b.csv
    null_representations/
        source_a.csv                # Empty field ,,
        source_b.csv                # Literal NULL
    crlf_vs_lf/
        source_a.csv                # CRLF line endings
        source_b.csv                # LF line endings
    encoding_latin1/
        source_a.csv                # UTF-8
        source_b.csv                # Latin-1
```

**Config fixtures** (`tests/fixtures/configs/`):

```
configs/
    parquet_default_strict.yaml
    parquet_with_tier1_exclusions.yaml
    parquet_with_tier3_tolerances.yaml
    csv_simple.yaml
    csv_with_trailer.yaml
    csv_normalize_line_breaks.yaml
    csv_normalize_encoding.yaml
    mixed_tiers.yaml
    threshold_99_percent.yaml
    invalid_missing_reader.yaml
    invalid_unknown_reader.yaml
    invalid_tier3_no_tolerance_type.yaml
    invalid_tier3_no_tolerance_value.yaml
    invalid_missing_sources.yaml
```

### 1.3 Test Data Strategy

Per BRD Section 14 (Decision 15), test data must exercise realistic variance between "original" and "rewritten" outputs. For Proofmark's own test suite, this means:

- **Parquet fixtures**: Generated using `pyarrow` with deliberate schema and value differences where needed. The generation script is checked in and reviewable, but the fixtures themselves are also checked in so tests don't depend on runtime generation.
- **CSV fixtures**: Hand-crafted where precision matters (null representations, line endings, encoding). Generated for larger row counts.
- **Tolerance test data**: Created with different rounding libraries/modes per Decision 15. Source A uses `ROUND_HALF_UP`, source B uses `ROUND_HALF_EVEN` for the same input values. This produces realistic floating-point variance, not hand-tweaked numbers.
- **Fixture generation script**: A standalone script at `tests/fixtures/generate_fixtures.py` that produces all fixture files. The script is part of the test infrastructure, not the application. It runs once during test data management (SDLC step 4), and its output is committed.

### 1.4 BRD Traceability Matrix

Every BDD scenario below includes a `[BRD x.x]` reference. The full traceability:

| BRD Section | Feature Area(s) | Scenario Count |
|---|---|---|
| 3.4 Two Readers | parquet_reader, csv_reader | 7 |
| 3.5 Parquet Part Files | parquet_reader | 3 |
| 4 Comparison Pipeline | hash_sort_diff, row_count | 5 |
| 5 Column Classification | column_classification | 6 |
| 6 Configuration | config_validation | 5 |
| 7 Tolerance Specification | column_classification | 4 |
| 8 Null Handling | null_handling | 4 |
| 9 Line Break and Encoding | strictness | 4 |
| 11 Report Output | report_output | 5 |
| 12 CLI Interface | cli | 5 |

Total: 48 BDD scenarios across 10 feature areas.

### 1.5 pytest Conventions

**Markers:**

```python
@pytest.mark.parquet       # Requires parquet fixtures
@pytest.mark.csv           # Requires CSV fixtures
@pytest.mark.slow          # Tests with large fixture files (run separately in CI)
@pytest.mark.cli           # End-to-end CLI invocation tests
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
    """Factory fixture: builds a YAML config file in tmp_path, returns path."""

@pytest.fixture
def run_comparison():
    """Invokes the comparison pipeline programmatically. Returns report dict."""

@pytest.fixture
def run_cli(tmp_path):
    """Invokes proofmark CLI as subprocess. Returns (exit_code, stdout, stderr)."""
```

**Fixture naming:** Fixtures that provide paths end in `_dir` or `_path`. Fixtures that provide data end in `_data`. Factory fixtures are verbs (`run_comparison`, `build_config`).

**Test naming:** `test_{what_is_being_tested}_{expected_outcome}`. Examples:
- `test_parquet_3parts_vs_1part_passes`
- `test_csv_data_mismatch_fails_with_detail`
- `test_tier3_absolute_within_tolerance_passes`

---

## Part 2: BDD Scenarios

### Feature: Parquet Reader

#### Scenario: Identical data across different part file counts passes [BRD 3.5]

```gherkin
Given a parquet source_a directory with 3 part files containing rows:
    | account_id | balance  | status |
    | 1001       | 5000.00  | active |
    | 1002       | 3200.50  | active |
    | 1003       | 0.00     | closed |
And a parquet source_b directory with 1 part file containing the same 3 rows
And a config with reader "parquet" and no column overrides
When I run the comparison
Then the result is PASS
And the report summary shows row_count_a: 3, row_count_b: 3, match_count: 3, mismatch_count: 0
And match_percentage is 100.0
```

#### Scenario: Identical data in matching part file counts passes [BRD 3.4]

```gherkin
Given a parquet source_a directory with 1 part file containing rows:
    | id | name    | amount |
    | 1  | Alice   | 100.00 |
    | 2  | Bob     | 200.00 |
And a parquet source_b directory with 1 part file containing the same 2 rows
And a config with reader "parquet" and no column overrides
When I run the comparison
Then the result is PASS
And the report summary shows match_count: 2, mismatch_count: 0
```

#### Scenario: Data difference detected and reported with detail [BRD 3.4, 11]

```gherkin
Given a parquet source_a directory with 1 part file containing rows:
    | account_id | balance |
    | 1001       | 5000.00 |
    | 1002       | 3200.50 |
And a parquet source_b directory with 1 part file containing rows:
    | account_id | balance |
    | 1001       | 5000.00 |
    | 1002       | 3200.99 |
And a config with reader "parquet" and no column overrides
When I run the comparison
Then the result is FAIL
And the report summary shows match_count: 1, mismatch_count: 1
And the mismatches section contains an entry with column "balance", value_a "3200.50", value_b "3200.99"
```

#### Scenario: Empty source directory produces an error [BRD 3.5]

```gherkin
Given a parquet source_a directory containing no parquet files
And a parquet source_b directory with 1 part file containing 1 row
And a config with reader "parquet"
When I run the comparison
Then the result is an error
And the error message indicates source_a contains no parquet files
```

---

### Feature: CSV Reader

#### Scenario: Simple CSV with header, data matches [BRD 3.4]

```gherkin
Given a CSV source_a file with content:
    account_id,balance,status
    1001,5000.00,active
    1002,3200.50,active
And a CSV source_b file with identical content
And a config with reader "csv", header_rows: 1, trailer_rows: 0
When I run the comparison
Then the result is PASS
And the report summary shows match_count: 2, mismatch_count: 0
```

#### Scenario: CSV with trailing control record, data matches [BRD 3.4]

```gherkin
Given a CSV source_a file with content:
    account_id,balance,status
    1001,5000.00,active
    1002,3200.50,active
    TRAILER|2|2026-02-28
And a CSV source_b file with identical content
And a config with reader "csv", header_rows: 1, trailer_rows: 1
When I run the comparison
Then the result is PASS
And the report summary shows match_count: 2, mismatch_count: 0
```

#### Scenario: CSV header row difference detected [BRD 3.4]

```gherkin
Given a CSV source_a file with header row "account_id,balance,status"
And a CSV source_b file with header row "account_id,balance,state"
And both files have identical data rows
And a config with reader "csv", header_rows: 1, trailer_rows: 0
When I run the comparison
Then the result is FAIL
And the report indicates a header mismatch: row 1 differs between sources
```

#### Scenario: CSV trailer row difference detected [BRD 3.4]

```gherkin
Given a CSV source_a file with trailer row "TRAILER|2|2026-02-28"
And a CSV source_b file with trailer row "TRAILER|2|2026-02-27"
And both files have identical header and data rows
And a config with reader "csv", header_rows: 1, trailer_rows: 1
When I run the comparison
Then the result is FAIL
And the report indicates a trailer mismatch between sources
```

#### Scenario: CSV data mismatch in body [BRD 3.4, 11]

```gherkin
Given a CSV source_a file with content:
    account_id,balance
    1001,5000.00
    1002,3200.50
And a CSV source_b file with content:
    account_id,balance
    1001,5000.00
    1002,3200.99
And a config with reader "csv", header_rows: 1, trailer_rows: 0
When I run the comparison
Then the result is FAIL
And the report summary shows match_count: 1, mismatch_count: 1
And the mismatches section contains an entry with column "balance", value_a "3200.50", value_b "3200.99"
```

---

### Feature: Column Classification

#### Scenario: All columns default to tier 2 when no column config provided [BRD 5]

```gherkin
Given a parquet source with columns: account_id, balance, status
And a config with no columns section
When I run the comparison
Then all columns are classified as tier 2 in the report's column_classification section
And the comparison uses exact match for every column
```

#### Scenario: Tier 1 column excluded before hashing [BRD 5, 4]

```gherkin
Given a parquet source_a with rows:
    | run_id                               | account_id | balance |
    | a1b2c3d4-e5f6-7890-abcd-ef1234567890 | 1001       | 5000.00 |
And a parquet source_b with rows:
    | run_id                               | account_id | balance |
    | ffffffff-ffff-ffff-ffff-ffffffffffff | 1001       | 5000.00 |
And a config with tier_1 columns: [{name: run_id, reason: "Non-deterministic UUID"}]
When I run the comparison
Then the result is PASS
And the report column_classification shows run_id as tier 1 with reason "Non-deterministic UUID"
And the mismatches section is empty
```

#### Scenario: Tier 3 absolute tolerance within threshold passes [BRD 7]

```gherkin
Given a parquet source_a with rows:
    | account_id | interest_accrued |
    | 1001       | 100.005          |
And a parquet source_b with rows:
    | account_id | interest_accrued |
    | 1001       | 100.004          |
And a config with tier_3 columns:
    [{name: interest_accrued, tolerance: 0.01, tolerance_type: absolute, reason: "Rounding variance"}]
When I run the comparison
Then the result is PASS
And the report summary shows mismatch_count: 0
```

#### Scenario: Tier 3 relative tolerance within threshold passes [BRD 7]

```gherkin
Given a parquet source_a with rows:
    | account_id | market_value |
    | 1001       | 1000000.00   |
And a parquet source_b with rows:
    | account_id | market_value |
    | 1001       | 1000000.50   |
And a config with tier_3 columns:
    [{name: market_value, tolerance: 0.001, tolerance_type: relative, reason: "Scales with magnitude"}]
When I run the comparison
Then the result is PASS
Because |1000000.00 - 1000000.50| / max(|1000000.00|, |1000000.50|) = 0.0000005, which is <= 0.001
```

#### Scenario: Tier 3 tolerance exceeded reports mismatch with delta [BRD 7, 11]

```gherkin
Given a parquet source_a with rows:
    | account_id | interest_accrued |
    | 1001       | 100.00           |
And a parquet source_b with rows:
    | account_id | interest_accrued |
    | 1001       | 100.05           |
And a config with tier_3 columns:
    [{name: interest_accrued, tolerance: 0.01, tolerance_type: absolute, reason: "Rounding variance"}]
When I run the comparison
Then the result is FAIL
And the mismatches section contains an entry with:
    column: "interest_accrued"
    value_a: "100.00"
    value_b: "100.05"
    tolerance: 0.01
    tolerance_type: "absolute"
    actual_delta: 0.05
```

#### Scenario: Mixed tier classification on same target [BRD 5, 7]

```gherkin
Given a parquet source_a with rows:
    | run_id    | account_id | balance | interest_accrued |
    | uuid-aaa  | 1001       | 5000.00 | 100.005          |
And a parquet source_b with rows:
    | run_id    | account_id | balance | interest_accrued |
    | uuid-bbb  | 1001       | 5000.00 | 100.004          |
And a config with:
    tier_1: [{name: run_id, reason: "Non-deterministic UUID"}]
    tier_3: [{name: interest_accrued, tolerance: 0.01, tolerance_type: absolute, reason: "Rounding"}]
When I run the comparison
Then the result is PASS
And the report column_classification shows:
    run_id as tier 1
    account_id as tier 2 (default)
    balance as tier 2 (default)
    interest_accrued as tier 3
And the mismatches section is empty
```

---

### Feature: Null Handling

#### Scenario: Parquet null vs null matches [BRD 8]

```gherkin
Given a parquet source_a with a row where column "notes" is null (native parquet null)
And a parquet source_b with a row where column "notes" is null (native parquet null)
And a config with reader "parquet" and no column overrides
When I run the comparison
Then the result is PASS
And the row with the null column is counted as a match
```

#### Scenario: Parquet null vs empty string is a mismatch [BRD 8]

```gherkin
Given a parquet source_a with a row where column "notes" is null (native parquet null)
And a parquet source_b with a row where column "notes" is "" (empty string)
And a config with reader "parquet" and no column overrides
When I run the comparison
Then the result is FAIL
And the mismatches section contains an entry with column "notes", value_a: null, value_b: ""
```

#### Scenario: CSV empty field vs literal "NULL" is a mismatch [BRD 8]

```gherkin
Given a CSV source_a with content:
    id,status
    1,
And a CSV source_b with content:
    id,status
    1,NULL
And a config with reader "csv", header_rows: 1, trailer_rows: 0
When I run the comparison
Then the result is FAIL
And the mismatches section contains an entry with column "status"
Because byte-level comparison treats empty field and literal "NULL" as different values
```

#### Scenario: CSV different null-like representations are all distinct [BRD 8]

```gherkin
Given a CSV source_a with content:
    id,value
    1,NULL
And a CSV source_b with content:
    id,value
    1,null
And a config with reader "csv", header_rows: 1, trailer_rows: 0
When I run the comparison
Then the result is FAIL
Because "NULL" and "null" are different byte sequences
```

---

### Feature: Hash and Sort Pipeline

#### Scenario: Row order independence --- same data, different order passes [BRD 4]

```gherkin
Given a parquet source_a with rows:
    | account_id | balance |
    | 1001       | 5000.00 |
    | 1002       | 3200.50 |
    | 1003       | 0.00    |
And a parquet source_b with the same rows in a different order:
    | account_id | balance |
    | 1003       | 0.00    |
    | 1001       | 5000.00 |
    | 1002       | 3200.50 |
And a config with reader "parquet" and no column overrides
When I run the comparison
Then the result is PASS
And the report summary shows match_count: 3, mismatch_count: 0
```

#### Scenario: Duplicate rows --- multiset comparison [BRD 4]

```gherkin
Given a parquet source_a with rows:
    | account_id | balance |
    | 1001       | 5000.00 |
    | 1001       | 5000.00 |
And a parquet source_b with rows:
    | account_id | balance |
    | 1001       | 5000.00 |
And a config with reader "parquet" and no column overrides
When I run the comparison
Then the result is FAIL
And the report summary shows row_count_a: 2, row_count_b: 1
Because multiset comparison requires identical row multiplicity
```

#### Scenario: Tier 1 exclusion does not affect hash-based ordering [BRD 4, 5]

```gherkin
Given a parquet source_a with rows:
    | uuid       | account_id | balance |
    | aaa-111    | 1001       | 5000.00 |
    | aaa-222    | 1002       | 3200.50 |
And a parquet source_b with rows (different UUIDs, different order):
    | uuid       | account_id | balance |
    | bbb-999    | 1002       | 3200.50 |
    | bbb-888    | 1001       | 5000.00 |
And a config with tier_1: [{name: uuid, reason: "Non-deterministic"}]
When I run the comparison
Then the result is PASS
Because UUIDs are excluded before hashing, so hash-sort ordering is based on account_id and balance only
```

---

### Feature: Strictness Settings

#### Scenario: Line breaks strict mode --- CRLF vs LF is a mismatch [BRD 9]

```gherkin
Given a CSV source_a file with CRLF line endings
And a CSV source_b file with LF line endings
And both files have identical field values
And a config with reader "csv", line_breaks: "strict"
When I run the comparison
Then the result is FAIL
Because CRLF and LF are different byte sequences in strict mode
```

#### Scenario: Line breaks normalize mode --- CRLF vs LF matches [BRD 9]

```gherkin
Given a CSV source_a file with CRLF line endings
And a CSV source_b file with LF line endings
And both files have identical field values
And a config with reader "csv", line_breaks: "normalize"
When I run the comparison
Then the result is PASS
Because line break normalization treats CRLF and LF as equivalent
```

#### Scenario: Encoding strict mode --- different encodings mismatch [BRD 9]

```gherkin
Given a CSV source_a file encoded in UTF-8 containing the character 'e' with acute accent
And a CSV source_b file encoded in Latin-1 containing the same character
And a config with reader "csv", encoding: "strict"
When I run the comparison
Then the result is FAIL
Because the byte representations differ between UTF-8 and Latin-1 in strict mode
```

#### Scenario: Encoding normalize mode --- different encodings match [BRD 9]

```gherkin
Given a CSV source_a file encoded in UTF-8 containing the character 'e' with acute accent
And a CSV source_b file encoded in Latin-1 containing the same character
And a config with reader "csv", encoding: "normalize"
When I run the comparison
Then the result is PASS
Because both files are decoded to a common encoding and the characters are equivalent
```

---

### Feature: Tolerance Edge Cases

#### Scenario: Both values zero with relative tolerance matches [BRD 7]

```gherkin
Given a parquet source_a with rows:
    | account_id | delta |
    | 1001       | 0.0   |
And a parquet source_b with rows:
    | account_id | delta |
    | 1001       | 0.0   |
And a config with tier_3 columns:
    [{name: delta, tolerance: 0.01, tolerance_type: relative, reason: "Zero edge case"}]
When I run the comparison
Then the result is PASS
Because both values are zero, delta is zero
```

#### Scenario: One value zero, other non-zero with relative tolerance [BRD 7]

```gherkin
Given a parquet source_a with rows:
    | account_id | delta  |
    | 1001       | 0.0    |
And a parquet source_b with rows:
    | account_id | delta  |
    | 1001       | 0.0001 |
And a config with tier_3 columns:
    [{name: delta, tolerance: 0.01, tolerance_type: relative, reason: "Zero edge case"}]
When I run the comparison
Then the result is FAIL
Because |0.0 - 0.0001| / max(|0.0|, |0.0001|) = 1.0, which exceeds tolerance 0.01
And the mismatches section contains an entry with actual_delta showing the relative difference
```

#### Scenario: Tolerance type missing on tier 3 column errors [BRD 7, 6]

```gherkin
Given a config YAML with a tier_3 column entry:
    - name: interest_accrued
      tolerance: 0.01
      reason: "Rounding variance"
And tolerance_type is NOT specified
When I attempt to parse the config
Then the result is an error (exit code 2)
And the error message indicates tolerance_type is required for tier 3 column "interest_accrued"
```

#### Scenario: Tolerance value missing on tier 3 column errors [BRD 7, 6]

```gherkin
Given a config YAML with a tier_3 column entry:
    - name: interest_accrued
      tolerance_type: absolute
      reason: "Rounding variance"
And tolerance (the numeric value) is NOT specified
When I attempt to parse the config
Then the result is an error (exit code 2)
And the error message indicates tolerance value is required for tier 3 column "interest_accrued"
```

---

### Feature: Report Output

#### Scenario: Report contains required metadata and structure [BRD 11]

```gherkin
Given any valid comparison that runs to completion
When I examine the JSON report
Then the report contains a "metadata" section with: timestamp, proofmark_version, comparison_target, config_path
And the report contains a "config_echo" section with the full configuration used
And the report contains a "column_classification" section listing tier 1, tier 2, and tier 3 columns
And the report contains a "summary" section with: row_count_a, row_count_b, match_count, mismatch_count, match_percentage, result, threshold
And the report contains a "mismatches" section (empty list if no mismatches)
```

#### Scenario: All mismatches shown regardless of pass/fail stamp [BRD 11]

```gherkin
Given a parquet comparison target with 100 rows where 1 row has a data mismatch
And a config with threshold: 99.0
When I run the comparison
Then the result is PASS (99% match >= 99% threshold)
And the report summary shows match_percentage: 99.0
And the mismatches section contains exactly 1 entry with the specific mismatch detail
And the mismatches section is NOT suppressed by the PASS result
```

#### Scenario: Threshold 100% with any mismatch fails [BRD 11]

```gherkin
Given a parquet comparison target with 1000 rows where 1 row has a data mismatch
And a config with threshold: 100.0 (or threshold omitted, since 100.0 is the default)
When I run the comparison
Then the result is FAIL
And the report summary shows match_percentage: 99.9
And the mismatches section contains the 1 mismatch entry
```

#### Scenario: Threshold below 100% with mismatches within threshold passes [BRD 11]

```gherkin
Given a parquet comparison target with 200 rows where 2 rows have data mismatches
And a config with threshold: 99.0
When I run the comparison
Then the result is PASS
And the report summary shows match_percentage: 99.0, match_count: 198, mismatch_count: 2
And the mismatches section contains exactly 2 entries
```

#### Scenario: Column classification with justifications echoed in report [BRD 11, 5]

```gherkin
Given a config with:
    tier_1: [{name: run_id, reason: "Non-deterministic UUID assigned at runtime"}]
    tier_3: [{name: interest_accrued, tolerance: 0.01, tolerance_type: absolute, reason: "Spark vs ADF rounding"}]
And columns account_id and balance exist but are not in the config (tier 2 by default)
When I run a comparison and examine the report
Then the column_classification section shows:
    tier_1: run_id with reason "Non-deterministic UUID assigned at runtime"
    tier_2: account_id, balance
    tier_3: interest_accrued with reason "Spark vs ADF rounding", tolerance 0.01, tolerance_type "absolute"
```

---

### Feature: CLI Interface

#### Scenario: Exit code 0 on PASS [BRD 12]

```gherkin
Given a valid config pointing to identical parquet sources
When I run `proofmark compare --config path/to/config.yaml`
Then the process exit code is 0
And stdout contains a valid JSON report with result: "PASS"
```

#### Scenario: Exit code 1 on FAIL [BRD 12]

```gherkin
Given a valid config pointing to parquet sources with data mismatches
When I run `proofmark compare --config path/to/config.yaml`
Then the process exit code is 1
And stdout contains a valid JSON report with result: "FAIL"
```

#### Scenario: Exit code 2 on error [BRD 12]

```gherkin
Given a config file that references a source_a path that does not exist
When I run `proofmark compare --config path/to/config.yaml`
Then the process exit code is 2
And stderr contains an error message indicating the missing file
And stdout does not contain a JSON report
```

#### Scenario: Output to file with --output flag [BRD 12]

```gherkin
Given a valid config pointing to identical parquet sources
When I run `proofmark compare --config path/to/config.yaml --output /tmp/report.json`
Then the process exit code is 0
And /tmp/report.json contains a valid JSON report with result: "PASS"
And stdout is empty (report goes to file, not stdout)
```

#### Scenario: Config flag is required [BRD 12]

```gherkin
When I run `proofmark compare` without a --config flag
Then the process exit code is 2
And stderr contains a usage error indicating --config is required
```

---

### Feature: Configuration Validation

#### Scenario: Valid YAML config parses without error [BRD 6]

```gherkin
Given a YAML config file with all required fields:
    comparison_target: "test_target"
    reader: "parquet"
    source_a: "/path/to/source_a"
    source_b: "/path/to/source_b"
When I parse the config
Then no validation error is raised
And the config object has comparison_target "test_target", reader "parquet"
```

#### Scenario: Missing required field produces error [BRD 6]

```gherkin
Given a YAML config file missing the "reader" field
When I attempt to parse the config
Then a validation error is raised indicating "reader" is a required field
```

#### Scenario: Unknown reader type produces error [BRD 6]

```gherkin
Given a YAML config file with reader: "excel"
When I attempt to parse the config
Then a validation error is raised indicating "excel" is not a valid reader type
And the error message lists valid reader types: "csv", "parquet"
```

#### Scenario: Tier 3 column without tolerance_type produces error [BRD 6, 7]

```gherkin
Given a YAML config file with a tier_3 column:
    - name: balance
      tolerance: 0.01
      reason: "Rounding"
And tolerance_type is not present
When I attempt to parse the config
Then a validation error is raised indicating tolerance_type is required for tier 3 column "balance"
```

#### Scenario: Tier 3 column without tolerance value produces error [BRD 6, 7]

```gherkin
Given a YAML config file with a tier_3 column:
    - name: balance
      tolerance_type: absolute
      reason: "Rounding"
And tolerance (numeric value) is not present
When I attempt to parse the config
Then a validation error is raised indicating tolerance is required for tier 3 column "balance"
```

---

### Feature: Row Count

#### Scenario: Different row counts between sources fails [BRD 4, 11]

```gherkin
Given a parquet source_a with 100 rows
And a parquet source_b with 99 rows (first 99 rows match source_a)
And a config with reader "parquet" and no column overrides
When I run the comparison
Then the result is FAIL
And the report summary shows row_count_a: 100, row_count_b: 99
And the mismatch count reflects the unmatched row
```

#### Scenario: Same row count, all rows match [BRD 4]

```gherkin
Given a parquet source_a with 50 rows
And a parquet source_b with the same 50 rows
And a config with reader "parquet" and no column overrides
When I run the comparison
Then the result is PASS
And the report summary shows row_count_a: 50, row_count_b: 50, match_count: 50, mismatch_count: 0
```

---

## Appendix: Design Decisions Influencing Test Architecture

### Why tests are feature-based, not pipeline-stage-based

The pipeline (load, exclude, hash, sort, diff, report) is an implementation detail. If we restructure the pipeline internals, we don't want every test file to move. Feature-based organization means tests survive refactors. A test about tier 3 tolerance doesn't care whether the tolerance check happens in a "diff" module or a "compare" module --- it cares about the observable output.

### Why fixtures are checked in, not generated at test time

1. **Reviewability.** Dan reviews every test case. He needs to see the fixture data, not a generation script he has to mentally execute.
2. **Determinism.** No risk of floating-point differences across platforms or library versions affecting fixture generation.
3. **Speed.** Generating parquet files at test time is wasted work for every test run.
4. **Auditability.** The fixture is the test input. It's an artifact. It belongs in version control.

The generation script exists for reproducibility --- if fixtures need to be regenerated, the script is there. But the fixtures themselves are the source of truth for tests.

### Why CLI tests use subprocess invocation

CLI scenarios test the external interface --- exit codes, stdout/stderr, file creation. These must exercise the actual CLI entry point as a user would invoke it. Internal API tests (`run_comparison` fixture) test the comparison pipeline without process overhead. Both are needed; they test different contracts.

### Scenarios intentionally NOT included

The following are out of scope per `Documentation/out-of-scope.md` and BRD Section 17:

- Database source comparison (PostgreSQL, Oracle, SQL Server, Synapse)
- Salesforce-specific comparison
- XML, JSON, EBCDIC, binary format readers
- Evidence package assembly
- Batch/orchestration mode
- PII/PCI stripping from reports
- Verbosity flags
- Hash algorithm configurability
- CSV dialect configuration (delimiter, quote char, escape char)
