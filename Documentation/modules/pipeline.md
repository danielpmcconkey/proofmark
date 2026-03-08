# pipeline.py

Orchestrator module. The only place that imports from all other modules. Implements the full comparison pipeline in `run()` and the PASS/FAIL decision in `_determine_result()`.

**Source**: `src/proofmark/pipeline.py`

## `run(config_path, lhs_path, rhs_path) -> dict`

Executes the complete comparison pipeline. Returns a JSON-serializable report dict.

### Pipeline Steps

1. **Load config** -- `config.load_config()` parses and validates the YAML file.
2. **Read data** -- `readers.create_reader()` dispatches to CSV or Parquet reader. Both sides are read.
3. **Line break check** (CSV only) -- Compares `line_break_style` between LHS and RHS.
4. **Schema validation** -- `schema.validate_schema()` checks column counts, names, types. If mismatches are found, the pipeline short-circuits with `build_schema_fail_report()` and returns immediately.
5. **Header/trailer comparison** (CSV only) -- `compare_lines()` does positional string equality on header and trailer lines.
6. **Hash** -- `hasher.hash_rows()` produces `HashedRow` objects for each side.
7. **Diff** -- `diff.diff()` groups by hash, counts matches/mismatches, runs FUZZY validation.
8. **Correlate** -- `correlator.correlate()` pairs unmatched rows by column similarity.
9. **Compute summary** -- Match percentage, match/mismatch counts, PASS/FAIL result.
10. **Build report** -- `report.build_report()` assembles the final JSON dict.

## `_determine_result(total_rows, total_matched, threshold, line_break_mismatch, header_comparison, trailer_comparison) -> str`

Returns `"PASS"` or `"FAIL"`.

**Threshold check**: `required_matched = ceil(total_rows * threshold / 100.0)`. Passes if `total_matched >= required_matched`. Zero total rows always passes.

**Auto-fail conditions** (any one triggers FAIL even if threshold passes):
- `line_break_mismatch is True`
- Any `header_comparison` entry with `match == False`
- Any `trailer_comparison` entry with `match == False`

Note: Schema mismatches are not checked here -- they short-circuit the pipeline before `_determine_result` is called.

## `compare_lines(lhs_lines, rhs_lines) -> list[HeaderTrailerResult]`

Positional string comparison of header or trailer lines. Returns one `HeaderTrailerResult` per line pair. If either input is `None`, returns an empty list.

Uses exact string equality (not CSV-parsed equality). `"a,b,c"` vs `'"a","b","c"'` is a mismatch.

## Match Percentage Formula

```
total_rows = total_lhs + total_rhs
total_matched = matched_pairs * 2  (double-counted, one per side)
match_percentage = (total_matched / total_rows) * 100.0
match_count = total_matched // 2
mismatch_count = max(total_lhs, total_rhs) - match_count
```
