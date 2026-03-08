# report.py

JSON report assembly. Builds the final report dict from pipeline results.

**Source**: `src/proofmark/report.py`

## Report Structure

```json
{
  "metadata": {
    "timestamp": "2026-01-15T12:00:00Z",
    "proofmark_version": "0.1.0",
    "comparison_target": "daily_balances",
    "config_path": "/path/to/config.yaml"
  },
  "config": { /* raw YAML config echoed back */ },
  "column_classifications": [
    {
      "name": "account_id",
      "classification": "STRICT",
      "reason": null,
      "tolerance": null,
      "tolerance_type": null
    }
  ],
  "summary": {
    "row_count_lhs": 100,
    "row_count_rhs": 100,
    "match_count": 99,
    "mismatch_count": 1,
    "match_percentage": 99.0,
    "result": "PASS",
    "threshold": 99.0,
    "line_break_mismatch": false  // CSV only, omitted for Parquet
  },
  "header_comparison": [ /* CSV only, null for Parquet */ ],
  "trailer_comparison": [ /* CSV only, null for Parquet */ ],
  "mismatches": {
    "schema_mismatches": null,
    "hash_groups": [ /* only groups with issues */ ],
    "correlation": {
      "correlated_pairs": [],
      "uncorrelated_lhs": [],
      "uncorrelated_rhs": []
    }
  },
  "attestation": "Output equivalence certifies equivalence to the original, NOT correctness..."
}
```

## Functions

### `build_report(...) -> dict`

Assembles the full report from pipeline results. Includes all sections. Mismatches are always shown regardless of PASS/FAIL result.

### `build_schema_fail_report(...) -> dict`

Builds a FAIL report for schema mismatch. Used when schema validation short-circuits the pipeline. Contains `schema_mismatches` list, empty hash groups, 0% match, and the attestation.

### `serialize_report(report) -> str`

Serializes the report dict to formatted JSON (2-space indent). Uses `default=str` for any non-standard types.

## Key Behaviors

- **Config echo**: The raw YAML dict is included in the report as-is, so the reader can see the exact config used.
- **Column classifications**: Listed in schema order, with classification, reason, and tolerance for each column.
- **`line_break_mismatch`**: Included in `summary` only for CSV. Omitted entirely for Parquet.
- **Attestation**: Fixed string reminding that PASS means equivalence, not correctness.
- **Mismatches always shown**: Even on PASS, any mismatches are reported (relevant for threshold < 100%).
