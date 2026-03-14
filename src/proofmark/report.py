"""Report generator — JSON report assembly. [FSD-5.9]"""
import json
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from importlib.metadata import PackageNotFoundError, version

from proofmark.config import ComparisonConfig
from proofmark.correlator import CorrelationResult
from proofmark.diff import DiffResult
from proofmark.readers.base import SchemaInfo


@dataclass(frozen=True)
class ComparisonSummary:
    row_count_lhs: int
    row_count_rhs: int
    match_count: int
    mismatch_count: int
    match_percentage: float
    result: str
    threshold: float
    line_break_mismatch: bool | None


@dataclass(frozen=True)
class HeaderTrailerResult:
    position: int
    lhs: str
    rhs: str
    match: bool


ATTESTATION = (
    "Output equivalence certifies equivalence to the original, NOT correctness "
    "in an absolute sense. If the original has a bug and the rewrite faithfully "
    "reproduces it, Proofmark reports PASS."
)


def _get_version() -> str:
    try:
        return version("proofmark")
    except PackageNotFoundError:
        return "0.1.0"


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
    """Assemble the final report as a JSON-serializable dict. [FSD-5.9.1]"""
    # Metadata [FSD-7.1]
    metadata = {
        "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "proofmark_version": _get_version(),
        "comparison_target": config.comparison_target,
        "config_path": config_path,
    }

    # Column classifications [FSD-5.9.1, FSD-7.3]
    excluded_map = {c.name: c for c in config.excluded_columns}
    fuzzy_map = {c.name: c for c in config.fuzzy_columns}
    column_classifications = []
    for col_name in schema.column_names:
        if col_name in excluded_map:
            ec = excluded_map[col_name]
            column_classifications.append({
                "name": col_name,
                "classification": "EXCLUDED",
                "reason": ec.reason,
                "tolerance": None,
                "tolerance_type": None,
            })
        elif col_name in fuzzy_map:
            fc = fuzzy_map[col_name]
            column_classifications.append({
                "name": col_name,
                "classification": "FUZZY",
                "reason": fc.reason,
                "tolerance": fc.tolerance,
                "tolerance_type": fc.tolerance_type.value,
            })
        else:
            column_classifications.append({
                "name": col_name,
                "classification": "STRICT",
                "reason": None,
                "tolerance": None,
                "tolerance_type": None,
            })

    # Summary
    summary_dict = {
        "row_count_lhs": summary.row_count_lhs,
        "row_count_rhs": summary.row_count_rhs,
        "match_count": summary.match_count,
        "mismatch_count": summary.mismatch_count,
        "match_percentage": summary.match_percentage,
        "result": summary.result,
        "threshold": summary.threshold,
    }
    if summary.line_break_mismatch is not None:
        summary_dict["line_break_mismatch"] = summary.line_break_mismatch

    # Header/trailer comparison [FSD-7.4]
    header_comp_out = None
    if header_comparison is not None:
        header_comp_out = [
            {"position": h.position, "lhs": h.lhs, "rhs": h.rhs, "match": h.match}
            for h in header_comparison
        ]

    trailer_comp_out = None
    if trailer_comparison is not None:
        trailer_comp_out = [
            {"position": t.position, "lhs": t.lhs, "rhs": t.rhs, "match": t.match}
            for t in trailer_comparison
        ]

    # Mismatches [FSD-7.6, FSD-7.7]
    hash_groups_out = []
    for hg in diff_result.hash_groups:
        hash_groups_out.append({
            "hash_value": hg.hash_value,
            "lhs_count": hg.lhs_count,
            "rhs_count": hg.rhs_count,
            "status": hg.status,
            "matched_count": hg.matched_count,
            "surplus_rows": [
                {"side": sr.side, "content": sr.content}
                for sr in hg.surplus_rows
            ],
            "fuzzy_failures": [
                {
                    "column": ff.column,
                    "lhs_value": ff.lhs_value,
                    "rhs_value": ff.rhs_value,
                    "tolerance": ff.tolerance,
                    "tolerance_type": ff.tolerance_type,
                    "actual_delta": ff.actual_delta,
                }
                for ff in hg.fuzzy_failures
            ],
        })

    # Correlation [FSD-7.8]
    correlation_out = {
        "correlated_pairs": [
            {
                "lhs_row": cp.lhs_row,
                "rhs_row": cp.rhs_row,
                "confidence": cp.confidence,
                "differing_columns": cp.differing_columns,
            }
            for cp in correlation.correlated_pairs
        ],
        "uncorrelated_lhs": correlation.uncorrelated_lhs,
        "uncorrelated_rhs": correlation.uncorrelated_rhs,
    }

    mismatches = {
        "schema_mismatches": None,
        "hash_groups": hash_groups_out,
        "correlation": correlation_out,
    }

    report = {
        "metadata": metadata,
        "config": config_raw,
        "column_classifications": column_classifications,
        "summary": summary_dict,
        "header_comparison": header_comp_out,
        "trailer_comparison": trailer_comp_out,
        "mismatches": mismatches,
        "attestation": ATTESTATION,
    }

    return report


def build_schema_fail_report(
    config_path: str,
    config: ComparisonConfig,
    config_raw: dict,
    schema_mismatches: list[str],
    lhs_row_count: int,
    rhs_row_count: int,
    line_break_mismatch: bool | None,
) -> dict:
    """Build a FAIL report for schema mismatch. [FSD-7.10]"""
    metadata = {
        "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "proofmark_version": _get_version(),
        "comparison_target": config.comparison_target,
        "config_path": config_path,
    }

    summary_dict = {
        "row_count_lhs": lhs_row_count,
        "row_count_rhs": rhs_row_count,
        "match_count": 0,
        "mismatch_count": 0,
        "match_percentage": 0.0,
        "result": "FAIL",
        "threshold": config.threshold,
    }
    if line_break_mismatch is not None:
        summary_dict["line_break_mismatch"] = line_break_mismatch

    mismatches = {
        "schema_mismatches": schema_mismatches,
        "hash_groups": [],
        "correlation": {
            "correlated_pairs": [],
            "uncorrelated_lhs": [],
            "uncorrelated_rhs": [],
        },
    }

    report = {
        "metadata": metadata,
        "config": config_raw,
        "column_classifications": [],
        "summary": summary_dict,
        "header_comparison": None,
        "trailer_comparison": None,
        "mismatches": mismatches,
        "attestation": ATTESTATION,
    }

    return report


def serialize_report(report: dict) -> str:
    """Serialize report dict to formatted JSON. [FSD-5.9.4]"""
    return json.dumps(report, indent=2, default=str)
