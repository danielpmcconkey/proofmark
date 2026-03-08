# Proofmark Overview

Proofmark is a Python tool for ETL output equivalence comparison. Given two sets of output files (CSV or Parquet), it determines whether they are equivalent -- accounting for excluded columns, fuzzy numeric tolerances, and configurable pass/fail thresholds.

## Two Modes

1. **`compare`** -- One-off CLI comparison. Takes a config YAML, left path, right path. Produces a JSON report on stdout (or to file). Exits 0 on PASS, 1 on FAIL, 2 on error.

2. **`serve`** -- Long-lived queue runner. Polls a PostgreSQL `comparison_queue` table for pending tasks, runs comparisons with a pool of worker threads, writes results back to the database. Shuts down on signal or after an idle timeout.

## Pipeline Architecture

The `compare` pipeline flows through these stages in order:

```
Config Load -> Read -> Schema Validate -> Header/Trailer Compare -> Hash -> Diff -> Correlate -> Report
```

1. **Config Load** (`config.py`): Parse YAML, validate fields, produce `ComparisonConfig`.
2. **Read** (`readers/`): Load data from CSV file or Parquet directory. Produce `ReaderResult` with rows, schema, and (for CSV) header/trailer lines and line break style.
3. **Schema Validate** (`schema.py`): Compare LHS/RHS column names, counts, types (Parquet only). Schema mismatch short-circuits the pipeline with an immediate FAIL report.
4. **Header/Trailer Compare** (`pipeline.py:compare_lines`): CSV only. Positional string comparison of header and trailer lines.
5. **Hash** (`hasher.py`): Per-row MD5 hash on STRICT columns only (excludes EXCLUDED and FUZZY columns from hash input). Extracts FUZZY values for later comparison.
6. **Diff** (`diff.py`): Group rows by hash, multiset comparison. Rows with matching hashes are paired; surplus rows become unmatched. FUZZY validation happens on hash-matched pairs -- failures reclassify pairs as unmatched.
7. **Correlate** (`correlator.py`): Pairs unmatched rows by column similarity (greedy, >50% match threshold). Remaining rows go to uncorrelated lists.
8. **Report** (`report.py`): Assemble JSON report with metadata, config echo, column classifications, summary, mismatches, correlation, and attestation.

## PASS/FAIL Determination

A comparison result is PASS if all of these hold:
- Match percentage meets the configured threshold (default 100%)
- No line break mismatch (CSV only)
- No header mismatch (CSV only)
- No trailer mismatch (CSV only)

Schema mismatches are caught before this logic and always produce FAIL.

## Column Classifications

Every column is classified as one of:
- **STRICT** (default): Included in hash. Exact match required.
- **EXCLUDED**: Dropped from hash and comparison entirely. Requires a `reason`.
- **FUZZY**: Excluded from hash but compared with numeric tolerance (absolute or relative). Requires `tolerance`, `tolerance_type`, and `reason`.

## Key Design Decisions

- **Row order independence**: Hash-based comparison is inherently order-independent.
- **Multiset semantics**: Duplicate rows are counted, not deduplicated. `[A, A]` vs `[A]` is a mismatch.
- **Null handling**: Nulls are represented as the sentinel `__PROOFMARK_NULL__` in hashing. Null vs null matches. Null vs empty string does not.
- **Attestation**: Every report includes a disclaimer that PASS means equivalence to the original, not correctness.

## Project Layout

```
src/proofmark/
  __init__.py          Exception hierarchy
  __main__.py          python -m proofmark entry
  cli.py               Argument parsing, subcommands
  config.py            Comparison config (YAML)
  app_config.py        Serve-mode config (AppConfig)
  pipeline.py          Orchestrator
  hasher.py            Hash engine
  diff.py              Diff engine
  tolerance.py         Fuzzy comparator
  correlator.py        Mismatch correlator
  schema.py            Schema validation
  report.py            JSON report builder
  readers/
    base.py            ABC, SchemaInfo, ReaderResult
    csv_reader.py      CSV reader
    parquet.py          Parquet reader

tests/
  conftest.py          Shared fixtures
  fixtures/            Generated test data (parquet, csv, configs)
  test_*.py            One test file per module

sql/
  queue_schema.sql     Queue table DDL (reference copy)
```
