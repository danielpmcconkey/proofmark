"""Pipeline orchestrator — wires all modules together. [FSD-5.10]"""
import math
from pathlib import Path

from proofmark.config import ComparisonConfig, ReaderType, load_config
from proofmark.correlator import correlate
from proofmark.diff import diff
from proofmark.hasher import hash_rows
from proofmark.readers import create_reader
from proofmark.readers.base import SchemaInfo
from proofmark.report import (
    ComparisonSummary,
    HeaderTrailerResult,
    build_report,
    build_schema_fail_report,
)
from proofmark.schema import validate_schema


def compare_lines(
    lhs_lines: tuple[str, ...] | None,
    rhs_lines: tuple[str, ...] | None,
) -> list[HeaderTrailerResult]:
    """Compare header or trailer lines positionally. [FSD-5.10.12]"""
    if lhs_lines is None or rhs_lines is None:
        return []
    results = []
    for i, (l, r) in enumerate(zip(lhs_lines, rhs_lines)):
        results.append(HeaderTrailerResult(
            position=i,
            lhs=l,
            rhs=r,
            match=(l == r),
        ))
    return results


def _determine_result(
    total_rows: int,
    total_matched: int,
    threshold: float,
    line_break_mismatch: bool | None,
    header_comparison: list[HeaderTrailerResult] | None,
    trailer_comparison: list[HeaderTrailerResult] | None,
) -> str:
    """Determine PASS or FAIL. [FSD-5.10.11]"""
    # Threshold check (integer math) [FSD-5.10.11]
    if total_rows == 0:
        threshold_passes = True
    else:
        required_matched = math.ceil(total_rows * threshold / 100.0)
        threshold_passes = total_matched >= required_matched

    # Auto-fail conditions
    if not threshold_passes:
        return "FAIL"
    if line_break_mismatch is True:
        return "FAIL"
    if header_comparison:
        if any(not h.match for h in header_comparison):
            return "FAIL"
    if trailer_comparison:
        if any(not t.match for t in trailer_comparison):
            return "FAIL"

    return "PASS"


def run(config_path: Path, lhs_path: Path, rhs_path: Path) -> dict:
    """Execute the full comparison pipeline. [FSD-5.10.1 through FSD-5.10.10]"""
    # Step 0: Load config [FSD-5.10.1]
    config, config_raw = load_config(config_path)

    # Step 1: Load data [FSD-5.10.2]
    reader = create_reader(config)
    lhs_result = reader.read(lhs_path, config.encoding)
    rhs_result = reader.read(rhs_path, config.encoding)

    # Step 2: Line break check (CSV only) [FSD-5.10.3]
    if config.reader == ReaderType.CSV:
        line_break_mismatch = (
            lhs_result.line_break_style != rhs_result.line_break_style
        )
    else:
        line_break_mismatch = None

    # Step 3: Schema validation [FSD-5.10.4]
    schema_mismatches = validate_schema(
        lhs_result.schema, rhs_result.schema, config.reader
    )
    if schema_mismatches:
        return build_schema_fail_report(
            config_path=str(config_path),
            config=config,
            config_raw=config_raw,
            schema_mismatches=schema_mismatches,
            lhs_row_count=len(lhs_result.rows),
            rhs_row_count=len(rhs_result.rows),
            line_break_mismatch=line_break_mismatch,
        )

    # Step 4: Header/trailer comparison (CSV only) [FSD-5.10.5]
    if config.reader == ReaderType.CSV:
        header_comparison = compare_lines(
            lhs_result.header_lines, rhs_result.header_lines
        )
        trailer_comparison = compare_lines(
            lhs_result.trailer_lines, rhs_result.trailer_lines
        )
    else:
        header_comparison = None
        trailer_comparison = None

    # Step 5: Hash [FSD-5.10.6]
    excluded_names = {col.name for col in config.excluded_columns}
    fuzzy_names = {col.name for col in config.fuzzy_columns}
    lhs_hashed = hash_rows(
        lhs_result.rows, excluded_names, fuzzy_names,
        lhs_result.schema.column_names,
    )
    rhs_hashed = hash_rows(
        rhs_result.rows, excluded_names, fuzzy_names,
        rhs_result.schema.column_names,
    )

    # Capture what we still need, then free the reader results.
    # Deliberate memory management: reader results hold every raw row in
    # memory. For large dataset comparisons these can be hundreds of MB,
    # so we eagerly delete them once hashing is done.
    schema = lhs_result.schema
    non_excluded_columns = [
        c for c in schema.column_names if c not in excluded_names
    ]
    del lhs_result, rhs_result

    # Step 6: Diff [FSD-5.10.7]
    diff_result = diff(lhs_hashed, rhs_hashed, config.fuzzy_columns)

    # Deliberate memory management: hashed row lists can also be very
    # large. diff_result holds its own references to unmatched rows, so
    # we can safely drop the full hashed lists here.
    del lhs_hashed, rhs_hashed

    # Step 7: Correlate [FSD-5.10.8]
    correlation = correlate(
        diff_result.all_unmatched_lhs,
        diff_result.all_unmatched_rhs,
        non_excluded_columns,
    )

    # Step 8: Compute summary [FSD-5.10.9]
    total_rows = diff_result.total_lhs + diff_result.total_rhs
    if total_rows == 0:
        match_percentage = 100.0
    else:
        match_percentage = (diff_result.total_matched / total_rows) * 100.0

    match_count = diff_result.total_matched // 2
    mismatch_count = max(diff_result.total_lhs, diff_result.total_rhs) - match_count

    result = _determine_result(
        total_rows, diff_result.total_matched, config.threshold,
        line_break_mismatch, header_comparison, trailer_comparison,
    )

    # Step 9: Build report [FSD-5.10.10]
    summary = ComparisonSummary(
        row_count_lhs=diff_result.total_lhs,
        row_count_rhs=diff_result.total_rhs,
        match_count=match_count,
        mismatch_count=mismatch_count,
        match_percentage=match_percentage,
        result=result,
        threshold=config.threshold,
        line_break_mismatch=line_break_mismatch,
    )

    return build_report(
        config_path=str(config_path),
        config=config,
        config_raw=config_raw,
        schema=schema,
        summary=summary,
        header_comparison=header_comparison,
        trailer_comparison=trailer_comparison,
        diff_result=diff_result,
        correlation=correlation,
    )
