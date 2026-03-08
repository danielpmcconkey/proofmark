# Testing

## Running Tests

```bash
# All tests (excluding queue tests which need PostgreSQL)
pytest

# Specific markers
pytest -m parquet
pytest -m csv
pytest -m cli

# Queue runner tests (require live PostgreSQL)
pytest -m queue

# With coverage
pytest --cov=proofmark --cov-report=term-missing
```

## Dependencies

```bash
pip install -e ".[dev]"         # pytest, pytest-cov
pip install -e ".[queue]"       # psycopg2 (for queue tests)
```

## Test Markers

Defined in `pyproject.toml`:

| Marker | Description |
|---|---|
| `parquet` | Requires parquet fixtures |
| `csv` | Requires CSV fixtures |
| `slow` | Tests with large fixture files |
| `cli` | End-to-end CLI invocation tests (subprocess) |
| `queue` | Requires live PostgreSQL connection |

## Test Organization

One test file per source module:

| Test File | Module Under Test | Coverage |
|---|---|---|
| `test_parquet_reader.py` | `readers/parquet.py` | Parquet reading, part file assembly, error cases |
| `test_csv_reader.py` | `readers/csv_reader.py` | CSV reading, header/trailer separation, encoding, edge cases |
| `test_config.py` | `config.py` | Config validation, all error paths |
| `test_hasher.py` | `hasher.py` | Column exclusion, FUZZY extraction, null sentinel, determinism |
| `test_diff.py` | `diff.py` | Row order independence, multiset, FUZZY reclassification |
| `test_tolerance.py` | `tolerance.py` | Absolute/relative tolerance, null handling, edge cases |
| `test_correlator.py` | `correlator.py` | High/low confidence pairing, greedy algorithm, empty inputs |
| `test_schema.py` | `schema.py` | Column count/name/type mismatch detection |
| `test_report.py` | `report.py` | Report structure, serialization, field presence |
| `test_determine_result.py` | `pipeline.py` | PASS/FAIL logic, threshold math, auto-fail conditions |
| `test_pipeline.py` | `pipeline.py` | End-to-end pipeline integration tests |
| `test_cli.py` | `cli.py` | Exit codes, output routing, error handling |
| `test_queue.py` | `queue.py` | Queue table init, task claiming, worker loops, concurrency |

## Fixtures

Test fixtures live in `tests/fixtures/` with three subdirectories:

- `parquet/` -- Parquet fixture directories (LHS/RHS pairs)
- `csv/` -- CSV fixture files (LHS/RHS pairs)
- `configs/` -- YAML config files for various test scenarios

**Fixture generation**: All fixtures are produced by `tests/fixtures/generate_fixtures.py`. The script is deterministic -- running it twice produces identical output. Generated fixtures are committed to version control.

```bash
python tests/fixtures/generate_fixtures.py
```

**Shared fixtures** in `conftest.py`:
- `fixtures_dir` / `parquet_fixtures` / `csv_fixtures` / `config_fixtures` -- path helpers
- `tmp_config` -- factory fixture that writes a YAML config dict to a temp file
- `run_comparison` -- invokes `pipeline.run()` directly
- `run_cli` -- invokes the CLI as a subprocess, returns `(exit_code, stdout, stderr)`

## Queue Tests

Queue tests (`test_queue.py`) require a live PostgreSQL instance. They use a dedicated test table (`control.proofmark_test_queue`) that is dropped and recreated on each test run. Connection is configured via `PROOFMARK_TEST_DSN` env var or built from `ETL_DB_PASSWORD`.

Tests are skipped automatically when the database is unreachable.

## Test Design

Tests follow BDD-style scenario naming from the original FSD Appendix A, with class names mapping to scenario descriptions. Each test class documents the business requirement it validates (e.g., `[BR-4.17]`, `[BR-11.22]`).

The test suite covers:
- Happy paths (identical data, fuzzy within tolerance)
- Failure paths (data mismatches, schema mismatches, threshold failures)
- Edge cases (zero rows, null handling, encoding errors, duplicate rows)
- Boundary conditions (exact threshold values, 50% correlation cutoff)
- Auto-fail conditions (line break mismatch, header/trailer differences)
