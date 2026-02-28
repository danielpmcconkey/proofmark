"""
Proofmark Test Fixture Generator

Generates all test fixtures defined in Documentation/QualityAssurance/test-architecture.md.
Run once during test data management (SDLC step 4). Output is committed to version control.

Usage:
    python tests/fixtures/generate_fixtures.py

Fixtures are deterministic. Running this script twice produces identical output.
"""

import os
import shutil
from decimal import Decimal, ROUND_HALF_UP, ROUND_HALF_EVEN
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq
import yaml


FIXTURES_DIR = Path(__file__).parent
PARQUET_DIR = FIXTURES_DIR / "parquet"
CSV_DIR = FIXTURES_DIR / "csv"
CONFIGS_DIR = FIXTURES_DIR / "configs"


def clean_and_create(path: Path):
    """Remove and recreate a directory."""
    if path.exists():
        shutil.rmtree(path)
    path.mkdir(parents=True)


def write_parquet(directory: Path, filename: str, table: pa.Table):
    """Write a parquet file to directory/filename."""
    directory.mkdir(parents=True, exist_ok=True)
    pq.write_table(table, directory / filename)


def write_csv(filepath: Path, content: str, encoding: str = "utf-8", newline: str = "\n"):
    """Write a CSV file with explicit encoding and line ending control."""
    filepath.parent.mkdir(parents=True, exist_ok=True)
    # Write in binary mode to control line endings exactly
    lines = content.split("\n")
    with open(filepath, "wb") as f:
        for i, line in enumerate(lines):
            f.write(line.encode(encoding))
            if i < len(lines) - 1:
                f.write(newline.encode("ascii"))


def write_yaml(filepath: Path, data: dict):
    """Write a YAML config file."""
    filepath.parent.mkdir(parents=True, exist_ok=True)
    with open(filepath, "w") as f:
        yaml.dump(data, f, default_flow_style=False, sort_keys=False)


# ---------------------------------------------------------------------------
# Parquet Fixtures
# ---------------------------------------------------------------------------

def gen_parquet_identical_3part_vs_1part():
    """3 part files on LHS, 1 coalesced on RHS. Same data."""
    schema = pa.schema([
        ("account_id", pa.int64()),
        ("balance", pa.float64()),
        ("status", pa.string()),
    ])

    rows = [
        {"account_id": 1001, "balance": 5000.00, "status": "active"},
        {"account_id": 1002, "balance": 3200.50, "status": "active"},
        {"account_id": 1003, "balance": 0.00, "status": "closed"},
    ]

    base = PARQUET_DIR / "identical_3part_vs_1part"

    # LHS: 3 part files, one row each
    for i, row in enumerate(rows):
        t = pa.table({k: [v] for k, v in row.items()}, schema=schema)
        write_parquet(base / "lhs", f"part-{i:05d}.parquet", t)

    # RHS: 1 part file, all rows
    t = pa.table({k: [r[k] for r in rows] for k in rows[0]}, schema=schema)
    write_parquet(base / "rhs", "part-00000.parquet", t)


def gen_parquet_identical_simple():
    """Matching 1-part files on both sides."""
    schema = pa.schema([
        ("id", pa.int64()),
        ("name", pa.string()),
        ("amount", pa.float64()),
    ])
    t = pa.table({
        "id": [1, 2],
        "name": ["Alice", "Bob"],
        "amount": [100.00, 200.00],
    }, schema=schema)

    base = PARQUET_DIR / "identical_simple"
    write_parquet(base / "lhs", "part-00000.parquet", t)
    write_parquet(base / "rhs", "part-00000.parquet", t)


def gen_parquet_data_mismatch():
    """One row differs between LHS and RHS."""
    schema = pa.schema([
        ("account_id", pa.int64()),
        ("balance", pa.float64()),
    ])

    lhs = pa.table({
        "account_id": [1001, 1002],
        "balance": [5000.00, 3200.50],
    }, schema=schema)

    rhs = pa.table({
        "account_id": [1001, 1002],
        "balance": [5000.00, 3200.99],
    }, schema=schema)

    base = PARQUET_DIR / "data_mismatch"
    write_parquet(base / "lhs", "part-00000.parquet", lhs)
    write_parquet(base / "rhs", "part-00000.parquet", rhs)


def gen_parquet_empty_directory():
    """LHS is empty, RHS has data."""
    schema = pa.schema([
        ("account_id", pa.int64()),
        ("balance", pa.float64()),
    ])
    t = pa.table({
        "account_id": [1001],
        "balance": [5000.00],
    }, schema=schema)

    base = PARQUET_DIR / "empty_directory"
    (base / "lhs").mkdir(parents=True, exist_ok=True)  # empty
    write_parquet(base / "rhs", "part-00000.parquet", t)


def gen_parquet_with_nulls():
    """Both sides have null values in a column."""
    schema = pa.schema([
        ("id", pa.int64()),
        ("notes", pa.string()),
    ])

    # null vs null (should match)
    lhs = pa.table({
        "id": [1, 2],
        "notes": ["hello", None],
    }, schema=schema)

    rhs = pa.table({
        "id": [1, 2],
        "notes": ["hello", None],
    }, schema=schema)

    base = PARQUET_DIR / "with_nulls"
    write_parquet(base / "lhs", "part-00000.parquet", lhs)
    write_parquet(base / "rhs", "part-00000.parquet", rhs)


def gen_parquet_null_vs_empty_string():
    """LHS has null, RHS has empty string. Should mismatch."""
    schema = pa.schema([
        ("id", pa.int64()),
        ("notes", pa.string()),
    ])

    lhs = pa.table({
        "id": [1],
        "notes": [None],
    }, schema=schema)

    rhs = pa.table({
        "id": [1],
        "notes": [""],
    }, schema=schema)

    base = PARQUET_DIR / "null_vs_empty_string"
    write_parquet(base / "lhs", "part-00000.parquet", lhs)
    write_parquet(base / "rhs", "part-00000.parquet", rhs)


def gen_parquet_row_count_mismatch():
    """LHS has 100 rows, RHS has 99."""
    schema = pa.schema([
        ("account_id", pa.int64()),
        ("balance", pa.float64()),
    ])

    lhs = pa.table({
        "account_id": list(range(1001, 1101)),
        "balance": [float(i * 100) for i in range(100)],
    }, schema=schema)

    rhs = pa.table({
        "account_id": list(range(1001, 1100)),
        "balance": [float(i * 100) for i in range(99)],
    }, schema=schema)

    base = PARQUET_DIR / "row_count_mismatch"
    write_parquet(base / "lhs", "part-00000.parquet", lhs)
    write_parquet(base / "rhs", "part-00000.parquet", rhs)


def gen_parquet_different_row_order():
    """Same rows, different order."""
    schema = pa.schema([
        ("account_id", pa.int64()),
        ("balance", pa.float64()),
    ])

    lhs = pa.table({
        "account_id": [1001, 1002, 1003],
        "balance": [5000.00, 3200.50, 0.00],
    }, schema=schema)

    rhs = pa.table({
        "account_id": [1003, 1001, 1002],
        "balance": [0.00, 5000.00, 3200.50],
    }, schema=schema)

    base = PARQUET_DIR / "different_row_order"
    write_parquet(base / "lhs", "part-00000.parquet", lhs)
    write_parquet(base / "rhs", "part-00000.parquet", rhs)


def gen_parquet_duplicate_rows():
    """LHS has 2 identical rows, RHS has 1. Multiset mismatch."""
    schema = pa.schema([
        ("account_id", pa.int64()),
        ("balance", pa.float64()),
    ])

    lhs = pa.table({
        "account_id": [1001, 1001],
        "balance": [5000.00, 5000.00],
    }, schema=schema)

    rhs = pa.table({
        "account_id": [1001],
        "balance": [5000.00],
    }, schema=schema)

    base = PARQUET_DIR / "duplicate_rows"
    write_parquet(base / "lhs", "part-00000.parquet", lhs)
    write_parquet(base / "rhs", "part-00000.parquet", rhs)


def gen_parquet_zero_rows():
    """Both sides have schema but zero data rows."""
    schema = pa.schema([
        ("account_id", pa.int64()),
        ("balance", pa.float64()),
        ("status", pa.string()),
    ])

    t = pa.table({
        "account_id": pa.array([], type=pa.int64()),
        "balance": pa.array([], type=pa.float64()),
        "status": pa.array([], type=pa.string()),
    }, schema=schema)

    base = PARQUET_DIR / "zero_rows"
    write_parquet(base / "lhs", "part-00000.parquet", t)
    write_parquet(base / "rhs", "part-00000.parquet", t)


def gen_parquet_schema_mismatch_column_count():
    """LHS has 3 columns, RHS has 2."""
    lhs = pa.table({
        "account_id": [1001],
        "balance": [5000.00],
        "status": ["active"],
    })

    rhs = pa.table({
        "account_id": [1001],
        "balance": [5000.00],
    })

    base = PARQUET_DIR / "schema_mismatch_column_count"
    write_parquet(base / "lhs", "part-00000.parquet", lhs)
    write_parquet(base / "rhs", "part-00000.parquet", rhs)


def gen_parquet_schema_mismatch_column_name():
    """LHS has 'status', RHS has 'state'."""
    lhs = pa.table({
        "account_id": [1001],
        "balance": [5000.00],
        "status": ["active"],
    })

    rhs = pa.table({
        "account_id": [1001],
        "balance": [5000.00],
        "state": ["active"],
    })

    base = PARQUET_DIR / "schema_mismatch_column_name"
    write_parquet(base / "lhs", "part-00000.parquet", lhs)
    write_parquet(base / "rhs", "part-00000.parquet", rhs)


def gen_parquet_schema_mismatch_column_type():
    """LHS balance is float64, RHS balance is int32."""
    lhs = pa.table({
        "account_id": pa.array([1001], type=pa.int64()),
        "balance": pa.array([5000.00], type=pa.float64()),
    })

    rhs = pa.table({
        "account_id": pa.array([1001], type=pa.int64()),
        "balance": pa.array([5000], type=pa.int32()),
    })

    base = PARQUET_DIR / "schema_mismatch_column_type"
    write_parquet(base / "lhs", "part-00000.parquet", lhs)
    write_parquet(base / "rhs", "part-00000.parquet", rhs)


def gen_parquet_excluded_column():
    """UUIDs differ but other data matches. For EXCLUDED column testing."""
    schema = pa.schema([
        ("run_id", pa.string()),
        ("account_id", pa.int64()),
        ("balance", pa.float64()),
    ])

    lhs = pa.table({
        "run_id": ["a1b2c3d4-e5f6-7890-abcd-ef1234567890"],
        "account_id": [1001],
        "balance": [5000.00],
    }, schema=schema)

    rhs = pa.table({
        "run_id": ["ffffffff-ffff-ffff-ffff-ffffffffffff"],
        "account_id": [1001],
        "balance": [5000.00],
    }, schema=schema)

    base = PARQUET_DIR / "excluded_column"
    write_parquet(base / "lhs", "part-00000.parquet", lhs)
    write_parquet(base / "rhs", "part-00000.parquet", rhs)


def gen_parquet_fuzzy_absolute():
    """Values differ within absolute tolerance. ROUND_HALF_UP vs ROUND_HALF_EVEN."""
    schema = pa.schema([
        ("account_id", pa.int64()),
        ("interest_accrued", pa.float64()),
    ])

    # Simulate different rounding: 100.005 rounded to 3 decimal places
    # ROUND_HALF_UP: 100.005 -> 100.005 (kept as-is for fixture)
    # ROUND_HALF_EVEN: 100.004 (banker's rounding variant)
    lhs = pa.table({
        "account_id": [1001],
        "interest_accrued": [100.005],
    }, schema=schema)

    rhs = pa.table({
        "account_id": [1001],
        "interest_accrued": [100.004],
    }, schema=schema)

    base = PARQUET_DIR / "fuzzy_absolute_within"
    write_parquet(base / "lhs", "part-00000.parquet", lhs)
    write_parquet(base / "rhs", "part-00000.parquet", rhs)


def gen_parquet_fuzzy_absolute_exceeded():
    """Values differ beyond absolute tolerance."""
    schema = pa.schema([
        ("account_id", pa.int64()),
        ("interest_accrued", pa.float64()),
    ])

    lhs = pa.table({
        "account_id": [1001],
        "interest_accrued": [100.00],
    }, schema=schema)

    rhs = pa.table({
        "account_id": [1001],
        "interest_accrued": [100.05],
    }, schema=schema)

    base = PARQUET_DIR / "fuzzy_absolute_exceeded"
    write_parquet(base / "lhs", "part-00000.parquet", lhs)
    write_parquet(base / "rhs", "part-00000.parquet", rhs)


def gen_parquet_fuzzy_relative():
    """Values differ within relative tolerance."""
    schema = pa.schema([
        ("account_id", pa.int64()),
        ("market_value", pa.float64()),
    ])

    lhs = pa.table({
        "account_id": [1001],
        "market_value": [1000000.00],
    }, schema=schema)

    rhs = pa.table({
        "account_id": [1001],
        "market_value": [1000000.50],
    }, schema=schema)

    base = PARQUET_DIR / "fuzzy_relative_within"
    write_parquet(base / "lhs", "part-00000.parquet", lhs)
    write_parquet(base / "rhs", "part-00000.parquet", rhs)


def gen_parquet_fuzzy_zero_edge():
    """Both values zero — relative tolerance edge case."""
    schema = pa.schema([
        ("account_id", pa.int64()),
        ("delta", pa.float64()),
    ])

    t = pa.table({
        "account_id": [1001],
        "delta": [0.0],
    }, schema=schema)

    base = PARQUET_DIR / "fuzzy_both_zero"
    write_parquet(base / "lhs", "part-00000.parquet", t)
    write_parquet(base / "rhs", "part-00000.parquet", t)


def gen_parquet_fuzzy_one_zero():
    """One value zero, other non-zero — relative tolerance edge case."""
    schema = pa.schema([
        ("account_id", pa.int64()),
        ("delta", pa.float64()),
    ])

    lhs = pa.table({
        "account_id": [1001],
        "delta": [0.0],
    }, schema=schema)

    rhs = pa.table({
        "account_id": [1001],
        "delta": [0.0001],
    }, schema=schema)

    base = PARQUET_DIR / "fuzzy_one_zero"
    write_parquet(base / "lhs", "part-00000.parquet", lhs)
    write_parquet(base / "rhs", "part-00000.parquet", rhs)


def gen_parquet_mixed_classification():
    """EXCLUDED + STRICT + FUZZY columns in one target."""
    schema = pa.schema([
        ("run_id", pa.string()),
        ("account_id", pa.int64()),
        ("balance", pa.float64()),
        ("interest_accrued", pa.float64()),
    ])

    lhs = pa.table({
        "run_id": ["uuid-aaa"],
        "account_id": [1001],
        "balance": [5000.00],
        "interest_accrued": [100.005],
    }, schema=schema)

    rhs = pa.table({
        "run_id": ["uuid-bbb"],
        "account_id": [1001],
        "balance": [5000.00],
        "interest_accrued": [100.004],
    }, schema=schema)

    base = PARQUET_DIR / "mixed_classification"
    write_parquet(base / "lhs", "part-00000.parquet", lhs)
    write_parquet(base / "rhs", "part-00000.parquet", rhs)


def gen_parquet_excluded_ordering():
    """EXCLUDED columns don't affect hash ordering. Different UUIDs, different row order."""
    schema = pa.schema([
        ("uuid", pa.string()),
        ("account_id", pa.int64()),
        ("balance", pa.float64()),
    ])

    lhs = pa.table({
        "uuid": ["aaa-111", "aaa-222"],
        "account_id": [1001, 1002],
        "balance": [5000.00, 3200.50],
    }, schema=schema)

    rhs = pa.table({
        "uuid": ["bbb-999", "bbb-888"],
        "account_id": [1002, 1001],
        "balance": [3200.50, 5000.00],
    }, schema=schema)

    base = PARQUET_DIR / "excluded_ordering"
    write_parquet(base / "lhs", "part-00000.parquet", lhs)
    write_parquet(base / "rhs", "part-00000.parquet", rhs)


def gen_parquet_fuzzy_fail_despite_hash_match():
    """FUZZY column exceeds tolerance but hash groups match (only STRICT col in hash)."""
    schema = pa.schema([
        ("account_id", pa.int64()),
        ("balance", pa.float64()),
    ])

    lhs = pa.table({
        "account_id": [1001],
        "balance": [100.00],
    }, schema=schema)

    rhs = pa.table({
        "account_id": [1001],
        "balance": [100.50],
    }, schema=schema)

    base = PARQUET_DIR / "fuzzy_fail_hash_match"
    write_parquet(base / "lhs", "part-00000.parquet", lhs)
    write_parquet(base / "rhs", "part-00000.parquet", rhs)


def gen_parquet_correlation_high_confidence():
    """Rows share most columns — good correlation candidate."""
    schema = pa.schema([
        ("account_id", pa.int64()),
        ("balance", pa.float64()),
        ("status", pa.string()),
    ])

    lhs = pa.table({
        "account_id": [1001, 1002],
        "balance": [5000.00, 3200.50],
        "status": ["active", "active"],
    }, schema=schema)

    rhs = pa.table({
        "account_id": [1001, 1002],
        "balance": [5000.00, 3200.99],
        "status": ["active", "active"],
    }, schema=schema)

    base = PARQUET_DIR / "correlation_high_confidence"
    write_parquet(base / "lhs", "part-00000.parquet", lhs)
    write_parquet(base / "rhs", "part-00000.parquet", rhs)


def gen_parquet_correlation_low_confidence():
    """Rows share no columns — fallback to separate unmatched lists."""
    schema = pa.schema([
        ("account_id", pa.int64()),
        ("balance", pa.float64()),
        ("status", pa.string()),
    ])

    lhs = pa.table({
        "account_id": [1001, 9999],
        "balance": [5000.00, 0.01],
        "status": ["active", "closed"],
    }, schema=schema)

    rhs = pa.table({
        "account_id": [1001, 8888],
        "balance": [5000.00, 99999.00],
        "status": ["active", "pending"],
    }, schema=schema)

    base = PARQUET_DIR / "correlation_low_confidence"
    write_parquet(base / "lhs", "part-00000.parquet", lhs)
    write_parquet(base / "rhs", "part-00000.parquet", rhs)


def gen_parquet_threshold_pass():
    """100 rows each side, 1 differs. For threshold 99.0% scenario (PASS)."""
    schema = pa.schema([
        ("account_id", pa.int64()),
        ("balance", pa.float64()),
    ])

    ids = list(range(1001, 1101))
    balances = [float(i * 100) for i in range(100)]

    lhs = pa.table({
        "account_id": ids,
        "balance": balances,
    }, schema=schema)

    # Last row differs
    rhs_balances = balances[:-1] + [balances[-1] + 0.01]
    rhs = pa.table({
        "account_id": ids,
        "balance": rhs_balances,
    }, schema=schema)

    base = PARQUET_DIR / "threshold_pass"
    write_parquet(base / "lhs", "part-00000.parquet", lhs)
    write_parquet(base / "rhs", "part-00000.parquet", rhs)


def gen_parquet_threshold_fail():
    """1000 rows each side, 1 differs. For threshold 100.0% scenario (FAIL)."""
    schema = pa.schema([
        ("account_id", pa.int64()),
        ("balance", pa.float64()),
    ])

    ids = list(range(1001, 2001))
    balances = [float(i * 10) for i in range(1000)]

    lhs = pa.table({
        "account_id": ids,
        "balance": balances,
    }, schema=schema)

    rhs_balances = balances[:-1] + [balances[-1] + 0.01]
    rhs = pa.table({
        "account_id": ids,
        "balance": rhs_balances,
    }, schema=schema)

    base = PARQUET_DIR / "threshold_fail"
    write_parquet(base / "lhs", "part-00000.parquet", lhs)
    write_parquet(base / "rhs", "part-00000.parquet", rhs)


def gen_parquet_threshold_boundary():
    """200 rows each side, 2 differ. For threshold 99.0% boundary scenario (PASS)."""
    schema = pa.schema([
        ("account_id", pa.int64()),
        ("balance", pa.float64()),
    ])

    ids = list(range(1001, 1201))
    balances = [float(i * 50) for i in range(200)]

    lhs = pa.table({
        "account_id": ids,
        "balance": balances,
    }, schema=schema)

    # Last 2 rows differ
    rhs_balances = balances[:-2] + [b + 0.01 for b in balances[-2:]]
    rhs = pa.table({
        "account_id": ids,
        "balance": rhs_balances,
    }, schema=schema)

    base = PARQUET_DIR / "threshold_boundary"
    write_parquet(base / "lhs", "part-00000.parquet", lhs)
    write_parquet(base / "rhs", "part-00000.parquet", rhs)


# ---------------------------------------------------------------------------
# CSV Fixtures
# ---------------------------------------------------------------------------

def gen_csv_simple_match():
    """Header + data, no trailer. Identical on both sides."""
    content = "account_id,balance,status\n1001,5000.00,active\n1002,3200.50,active\n"
    base = CSV_DIR / "simple_match"
    write_csv(base / "lhs.csv", content)
    write_csv(base / "rhs.csv", content)


def gen_csv_with_trailer_match():
    """Header + data + trailer. Identical on both sides."""
    content = "account_id,balance,status\n1001,5000.00,active\n1002,3200.50,active\nTRAILER|2|2026-02-28\n"
    base = CSV_DIR / "with_trailer_match"
    write_csv(base / "lhs.csv", content)
    write_csv(base / "rhs.csv", content)


def gen_csv_data_mismatch():
    """Data differs in body."""
    lhs = "account_id,balance\n1001,5000.00\n1002,3200.50\n"
    rhs = "account_id,balance\n1001,5000.00\n1002,3200.99\n"
    base = CSV_DIR / "data_mismatch"
    write_csv(base / "lhs.csv", lhs)
    write_csv(base / "rhs.csv", rhs)


def gen_csv_header_mismatch():
    """Different header column name."""
    lhs = "account_id,balance,status\n1001,5000.00,active\n"
    rhs = "account_id,balance,state\n1001,5000.00,active\n"
    base = CSV_DIR / "header_mismatch"
    write_csv(base / "lhs.csv", lhs)
    write_csv(base / "rhs.csv", rhs)


def gen_csv_trailer_mismatch():
    """Identical data but different trailer."""
    lhs = "account_id,balance\n1001,5000.00\nTRAILER|1|2026-02-28\n"
    rhs = "account_id,balance\n1001,5000.00\nTRAILER|1|2026-02-27\n"
    base = CSV_DIR / "trailer_mismatch"
    write_csv(base / "lhs.csv", lhs)
    write_csv(base / "rhs.csv", rhs)


def gen_csv_null_representations():
    """Empty field vs literal NULL."""
    lhs = "id,status\n1,\n"
    rhs = "id,status\n1,NULL\n"
    base = CSV_DIR / "null_representations"
    write_csv(base / "lhs.csv", lhs)
    write_csv(base / "rhs.csv", rhs)


def gen_csv_null_case_sensitivity():
    """NULL vs null — different byte sequences."""
    lhs = "id,value\n1,NULL\n"
    rhs = "id,value\n1,null\n"
    base = CSV_DIR / "null_case_sensitivity"
    write_csv(base / "lhs.csv", lhs)
    write_csv(base / "rhs.csv", rhs)


def gen_csv_crlf_vs_lf():
    """CRLF on LHS, LF on RHS. Same field values."""
    content_fields = "account_id,balance\n1001,5000.00\n1002,3200.50\n"
    base = CSV_DIR / "crlf_vs_lf"
    write_csv(base / "lhs.csv", content_fields, newline="\r\n")
    write_csv(base / "rhs.csv", content_fields, newline="\n")


def gen_csv_matching_line_breaks():
    """Both LF. No line break mismatch."""
    content = "account_id,balance\n1001,5000.00\n1002,3200.50\n"
    base = CSV_DIR / "matching_line_breaks"
    write_csv(base / "lhs.csv", content, newline="\n")
    write_csv(base / "rhs.csv", content, newline="\n")


def gen_csv_encoding_utf8():
    """Both UTF-8 with multi-byte characters."""
    content = "id,name\n1,caf\u00e9\n2,r\u00e9sum\u00e9\n"
    base = CSV_DIR / "encoding_utf8"
    write_csv(base / "lhs.csv", content, encoding="utf-8")
    write_csv(base / "rhs.csv", content, encoding="utf-8")


def gen_csv_encoding_invalid():
    """UTF-8 content that will fail if read as ASCII."""
    content = "id,name\n1,caf\u00e9\n2,r\u00e9sum\u00e9\n"
    base = CSV_DIR / "encoding_invalid"
    write_csv(base / "lhs.csv", content, encoding="utf-8")
    write_csv(base / "rhs.csv", content, encoding="utf-8")


# ---------------------------------------------------------------------------
# Config Fixtures (YAML)
# ---------------------------------------------------------------------------

def gen_configs():
    """Generate all config YAML fixtures."""

    # Parquet, default (all STRICT, threshold 100%)
    write_yaml(CONFIGS_DIR / "parquet_default.yaml", {
        "comparison_target": "test_parquet_default",
        "reader": "parquet",
    })

    # Parquet with EXCLUDED columns
    write_yaml(CONFIGS_DIR / "parquet_with_exclusions.yaml", {
        "comparison_target": "test_parquet_exclusions",
        "reader": "parquet",
        "columns": {
            "excluded": [
                {"name": "run_id", "reason": "Non-deterministic UUID assigned at runtime"},
            ],
        },
    })

    # Parquet with FUZZY columns (absolute)
    write_yaml(CONFIGS_DIR / "parquet_with_fuzzy.yaml", {
        "comparison_target": "test_parquet_fuzzy",
        "reader": "parquet",
        "columns": {
            "fuzzy": [
                {
                    "name": "interest_accrued",
                    "tolerance": 0.01,
                    "tolerance_type": "absolute",
                    "reason": "Rounding variance between ROUND_HALF_UP and ROUND_HALF_EVEN",
                },
            ],
        },
    })

    # Parquet with FUZZY relative
    write_yaml(CONFIGS_DIR / "parquet_fuzzy_relative.yaml", {
        "comparison_target": "test_parquet_fuzzy_relative",
        "reader": "parquet",
        "columns": {
            "fuzzy": [
                {
                    "name": "market_value",
                    "tolerance": 0.001,
                    "tolerance_type": "relative",
                    "reason": "Scales with magnitude",
                },
            ],
        },
    })

    # CSV simple (no trailer)
    write_yaml(CONFIGS_DIR / "csv_simple.yaml", {
        "comparison_target": "test_csv_simple",
        "reader": "csv",
        "csv": {"header_rows": 1, "trailer_rows": 0},
    })

    # CSV with trailer
    write_yaml(CONFIGS_DIR / "csv_with_trailer.yaml", {
        "comparison_target": "test_csv_trailer",
        "reader": "csv",
        "csv": {"header_rows": 1, "trailer_rows": 1},
    })

    # CSV with explicit encoding
    write_yaml(CONFIGS_DIR / "csv_with_encoding.yaml", {
        "comparison_target": "test_csv_encoding",
        "reader": "csv",
        "csv": {"header_rows": 1, "trailer_rows": 0},
        "encoding": "utf-8",
    })

    # CSV with ASCII encoding (for invalid encoding test)
    write_yaml(CONFIGS_DIR / "csv_encoding_ascii.yaml", {
        "comparison_target": "test_csv_encoding_ascii",
        "reader": "csv",
        "csv": {"header_rows": 1, "trailer_rows": 0},
        "encoding": "ascii",
    })

    # Mixed classifications (EXCLUDED + FUZZY, rest STRICT)
    write_yaml(CONFIGS_DIR / "mixed_classifications.yaml", {
        "comparison_target": "test_mixed",
        "reader": "parquet",
        "columns": {
            "excluded": [
                {"name": "run_id", "reason": "Non-deterministic UUID"},
            ],
            "fuzzy": [
                {
                    "name": "interest_accrued",
                    "tolerance": 0.01,
                    "tolerance_type": "absolute",
                    "reason": "Rounding variance",
                },
            ],
        },
    })

    # Threshold 99%
    write_yaml(CONFIGS_DIR / "threshold_99_percent.yaml", {
        "comparison_target": "test_threshold_99",
        "reader": "parquet",
        "threshold": 99.0,
    })

    # FUZZY with balance as FUZZY, account_id as STRICT (for hash-match-but-fuzzy-fail)
    write_yaml(CONFIGS_DIR / "parquet_fuzzy_balance.yaml", {
        "comparison_target": "test_fuzzy_balance",
        "reader": "parquet",
        "columns": {
            "fuzzy": [
                {
                    "name": "balance",
                    "tolerance": 0.01,
                    "tolerance_type": "absolute",
                    "reason": "Rounding",
                },
            ],
        },
    })

    # FUZZY zero edge case
    write_yaml(CONFIGS_DIR / "parquet_fuzzy_relative_zero.yaml", {
        "comparison_target": "test_fuzzy_zero",
        "reader": "parquet",
        "columns": {
            "fuzzy": [
                {
                    "name": "delta",
                    "tolerance": 0.01,
                    "tolerance_type": "relative",
                    "reason": "Zero edge case",
                },
            ],
        },
    })

    # --- Invalid configs for config_validation tests ---

    # Missing reader
    write_yaml(CONFIGS_DIR / "invalid_missing_reader.yaml", {
        "comparison_target": "test_invalid",
    })

    # Unknown reader
    write_yaml(CONFIGS_DIR / "invalid_unknown_reader.yaml", {
        "comparison_target": "test_invalid",
        "reader": "excel",
    })

    # FUZZY missing tolerance_type
    write_yaml(CONFIGS_DIR / "invalid_fuzzy_no_tolerance_type.yaml", {
        "comparison_target": "test_invalid",
        "reader": "parquet",
        "columns": {
            "fuzzy": [
                {"name": "interest_accrued", "tolerance": 0.01, "reason": "Rounding variance"},
            ],
        },
    })

    # FUZZY missing tolerance value
    write_yaml(CONFIGS_DIR / "invalid_fuzzy_no_tolerance_value.yaml", {
        "comparison_target": "test_invalid",
        "reader": "parquet",
        "columns": {
            "fuzzy": [
                {"name": "interest_accrued", "tolerance_type": "absolute", "reason": "Rounding variance"},
            ],
        },
    })

    # Missing comparison_target
    write_yaml(CONFIGS_DIR / "invalid_missing_comparison_target.yaml", {
        "reader": "parquet",
    })

    # EXCLUDED missing reason
    write_yaml(CONFIGS_DIR / "invalid_excluded_no_reason.yaml", {
        "comparison_target": "test_invalid",
        "reader": "parquet",
        "columns": {
            "excluded": [
                {"name": "run_id"},
            ],
        },
    })

    # FUZZY missing reason
    write_yaml(CONFIGS_DIR / "invalid_fuzzy_no_reason.yaml", {
        "comparison_target": "test_invalid",
        "reader": "parquet",
        "columns": {
            "fuzzy": [
                {"name": "balance", "tolerance": 0.01, "tolerance_type": "absolute"},
            ],
        },
    })

    # Column in both EXCLUDED and FUZZY
    write_yaml(CONFIGS_DIR / "invalid_duplicate_classification.yaml", {
        "comparison_target": "test_invalid",
        "reader": "parquet",
        "columns": {
            "excluded": [
                {"name": "balance", "reason": "Non-deterministic"},
            ],
            "fuzzy": [
                {
                    "name": "balance",
                    "tolerance": 0.01,
                    "tolerance_type": "absolute",
                    "reason": "Rounding",
                },
            ],
        },
    })


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print("Generating Proofmark test fixtures...")
    print(f"Output directory: {FIXTURES_DIR}")

    # Clean fixture directories
    for d in [PARQUET_DIR, CSV_DIR, CONFIGS_DIR]:
        clean_and_create(d)

    # Parquet fixtures
    print("\n--- Parquet fixtures ---")
    generators = [
        gen_parquet_identical_3part_vs_1part,
        gen_parquet_identical_simple,
        gen_parquet_data_mismatch,
        gen_parquet_empty_directory,
        gen_parquet_with_nulls,
        gen_parquet_null_vs_empty_string,
        gen_parquet_row_count_mismatch,
        gen_parquet_different_row_order,
        gen_parquet_duplicate_rows,
        gen_parquet_zero_rows,
        gen_parquet_schema_mismatch_column_count,
        gen_parquet_schema_mismatch_column_name,
        gen_parquet_schema_mismatch_column_type,
        gen_parquet_excluded_column,
        gen_parquet_fuzzy_absolute,
        gen_parquet_fuzzy_absolute_exceeded,
        gen_parquet_fuzzy_relative,
        gen_parquet_fuzzy_zero_edge,
        gen_parquet_fuzzy_one_zero,
        gen_parquet_mixed_classification,
        gen_parquet_excluded_ordering,
        gen_parquet_fuzzy_fail_despite_hash_match,
        gen_parquet_correlation_high_confidence,
        gen_parquet_correlation_low_confidence,
        gen_parquet_threshold_pass,
        gen_parquet_threshold_fail,
        gen_parquet_threshold_boundary,
    ]
    for gen in generators:
        name = gen.__name__.replace("gen_parquet_", "")
        gen()
        print(f"  {name}")

    # CSV fixtures
    print("\n--- CSV fixtures ---")
    csv_generators = [
        gen_csv_simple_match,
        gen_csv_with_trailer_match,
        gen_csv_data_mismatch,
        gen_csv_header_mismatch,
        gen_csv_trailer_mismatch,
        gen_csv_null_representations,
        gen_csv_null_case_sensitivity,
        gen_csv_crlf_vs_lf,
        gen_csv_matching_line_breaks,
        gen_csv_encoding_utf8,
        gen_csv_encoding_invalid,
    ]
    for gen in csv_generators:
        name = gen.__name__.replace("gen_csv_", "")
        gen()
        print(f"  {name}")

    # Config fixtures
    print("\n--- Config fixtures ---")
    gen_configs()
    for f in sorted(CONFIGS_DIR.iterdir()):
        print(f"  {f.name}")

    # Summary
    parquet_count = sum(1 for _ in PARQUET_DIR.rglob("*.parquet"))
    csv_count = sum(1 for _ in CSV_DIR.rglob("*.csv"))
    config_count = sum(1 for _ in CONFIGS_DIR.rglob("*.yaml"))
    print(f"\n--- Summary ---")
    print(f"Parquet files: {parquet_count}")
    print(f"CSV files: {csv_count}")
    print(f"Config files: {config_count}")
    print(f"Total fixtures: {parquet_count + csv_count + config_count}")


if __name__ == "__main__":
    main()
