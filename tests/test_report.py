"""Report generation tests — BDD scenarios 39-45. [FSD Appendix A]"""
import json

import pytest

from proofmark.config import (
    ComparisonConfig,
    ExcludedColumn,
    FuzzyColumn,
    ReaderType,
    ToleranceType,
)
from proofmark.correlator import CorrelationResult
from proofmark.diff import DiffResult, UnmatchedRow
from proofmark.readers.base import SchemaInfo
from proofmark.report import (
    ATTESTATION,
    ComparisonSummary,
    HeaderTrailerResult,
    build_report,
    build_schema_fail_report,
    serialize_report,
)
from proofmark.tolerance import FuzzyFailure


@pytest.fixture
def basic_config():
    return ComparisonConfig(
        comparison_target="test_target",
        reader=ReaderType.PARQUET,
    )


@pytest.fixture
def basic_schema():
    return SchemaInfo(
        column_names=("account_id", "balance", "status"),
        column_types={"account_id": "int64", "balance": "float64", "status": "string"},
    )


@pytest.fixture
def empty_diff():
    return DiffResult(
        hash_groups=[],
        all_unmatched_lhs=[],
        all_unmatched_rhs=[],
        all_fuzzy_failures=[],
        total_matched=6,
        total_lhs=3,
        total_rhs=3,
    )


@pytest.fixture
def empty_correlation():
    return CorrelationResult(
        correlated_pairs=[],
        uncorrelated_lhs=[],
        uncorrelated_rhs=[],
    )


class TestReportStructure:
    """Scenario 39: Report contains required metadata and structure [BR-11.1 through BR-11.5]"""

    def test_report_has_metadata(self, basic_config, basic_schema, empty_diff, empty_correlation):
        summary = ComparisonSummary(
            row_count_lhs=3, row_count_rhs=3,
            match_count=3, mismatch_count=0,
            match_percentage=100.0, result="PASS",
            threshold=100.0, line_break_mismatch=None,
        )
        report = build_report(
            config_path="/path/to/config.yaml",
            config=basic_config,
            config_raw={"comparison_target": "test_target", "reader": "parquet"},
            schema=basic_schema,
            summary=summary,
            header_comparison=None,
            trailer_comparison=None,
            diff_result=empty_diff,
            correlation=empty_correlation,
        )
        assert "metadata" in report
        assert "timestamp" in report["metadata"]
        assert "proofmark_version" in report["metadata"]
        assert report["metadata"]["comparison_target"] == "test_target"
        assert report["metadata"]["config_path"] == "/path/to/config.yaml"

    def test_report_has_config_echo(self, basic_config, basic_schema, empty_diff, empty_correlation):
        summary = ComparisonSummary(
            row_count_lhs=3, row_count_rhs=3,
            match_count=3, mismatch_count=0,
            match_percentage=100.0, result="PASS",
            threshold=100.0, line_break_mismatch=None,
        )
        raw = {"comparison_target": "test_target", "reader": "parquet"}
        report = build_report(
            "/path", basic_config, raw, basic_schema, summary,
            None, None, empty_diff, empty_correlation,
        )
        assert report["config"] == raw

    def test_report_has_column_classifications(self, basic_config, basic_schema, empty_diff, empty_correlation):
        summary = ComparisonSummary(
            row_count_lhs=3, row_count_rhs=3,
            match_count=3, mismatch_count=0,
            match_percentage=100.0, result="PASS",
            threshold=100.0, line_break_mismatch=None,
        )
        report = build_report(
            "/path", basic_config, {}, basic_schema, summary,
            None, None, empty_diff, empty_correlation,
        )
        assert "column_classifications" in report
        assert len(report["column_classifications"]) == 3
        # All STRICT by default
        for cc in report["column_classifications"]:
            assert cc["classification"] == "STRICT"

    def test_report_has_summary(self, basic_config, basic_schema, empty_diff, empty_correlation):
        summary = ComparisonSummary(
            row_count_lhs=3, row_count_rhs=3,
            match_count=3, mismatch_count=0,
            match_percentage=100.0, result="PASS",
            threshold=100.0, line_break_mismatch=None,
        )
        report = build_report(
            "/path", basic_config, {}, basic_schema, summary,
            None, None, empty_diff, empty_correlation,
        )
        s = report["summary"]
        assert s["row_count_lhs"] == 3
        assert s["row_count_rhs"] == 3
        assert s["match_count"] == 3
        assert s["mismatch_count"] == 0
        assert s["match_percentage"] == 100.0
        assert s["result"] == "PASS"
        assert s["threshold"] == 100.0

    def test_report_has_mismatches_section(self, basic_config, basic_schema, empty_diff, empty_correlation):
        summary = ComparisonSummary(
            row_count_lhs=3, row_count_rhs=3,
            match_count=3, mismatch_count=0,
            match_percentage=100.0, result="PASS",
            threshold=100.0, line_break_mismatch=None,
        )
        report = build_report(
            "/path", basic_config, {}, basic_schema, summary,
            None, None, empty_diff, empty_correlation,
        )
        assert "mismatches" in report
        assert report["mismatches"]["schema_mismatches"] is None
        assert report["mismatches"]["hash_groups"] == []

    def test_report_has_attestation(self, basic_config, basic_schema, empty_diff, empty_correlation):
        summary = ComparisonSummary(
            row_count_lhs=3, row_count_rhs=3,
            match_count=3, mismatch_count=0,
            match_percentage=100.0, result="PASS",
            threshold=100.0, line_break_mismatch=None,
        )
        report = build_report(
            "/path", basic_config, {}, basic_schema, summary,
            None, None, empty_diff, empty_correlation,
        )
        assert report["attestation"] == ATTESTATION


class TestMismatchesShownRegardlessOfPassFail:
    """Scenario 40: All mismatches shown regardless of pass/fail stamp [BR-11.24]"""

    def test_mismatches_shown_on_pass(self, basic_schema, empty_correlation):
        """Even when result is PASS, mismatches are included.

        Scenario: 100 LHS, 100 RHS, 99 match, 1 surplus LHS (hash only on LHS).
        total_matched = 99 * 2 = 198. match_count = 99. mismatch_count = 1.
        match_percentage = 198/200 * 100 = 99.0. threshold=99% → PASS.
        """
        config = ComparisonConfig(
            comparison_target="test", reader=ReaderType.PARQUET, threshold=99.0,
        )
        from proofmark.diff import HashGroupResult
        surplus = UnmatchedRow(side="lhs", content="extra|row", row_data={})
        hg = HashGroupResult(
            hash_value="abc123", lhs_count=1, rhs_count=0,
            status="COUNT_MISMATCH", matched_count=0,
            surplus_rows=[surplus],
            fuzzy_failures=[],
        )
        diff_result = DiffResult(
            hash_groups=[hg],
            all_unmatched_lhs=[surplus],
            all_unmatched_rhs=[],
            all_fuzzy_failures=[],
            total_matched=198,
            total_lhs=100,
            total_rhs=100,
        )
        summary = ComparisonSummary(
            row_count_lhs=100, row_count_rhs=100,
            match_count=99, mismatch_count=1,
            match_percentage=99.0, result="PASS",
            threshold=99.0, line_break_mismatch=None,
        )
        report = build_report(
            "/path", config, {}, basic_schema, summary,
            None, None, diff_result, empty_correlation,
        )
        # Mismatches should NOT be suppressed even on PASS
        assert len(report["mismatches"]["hash_groups"]) == 1
        assert report["mismatches"]["hash_groups"][0]["status"] == "COUNT_MISMATCH"
        assert len(report["mismatches"]["hash_groups"][0]["surplus_rows"]) == 1


class TestColumnClassificationInReport:
    """Scenario 42: Column classification with justifications echoed [BR-11.4, BR-5.3, BR-5.8]"""

    def test_classifications_echoed(self, empty_diff, empty_correlation):
        config = ComparisonConfig(
            comparison_target="test",
            reader=ReaderType.PARQUET,
            excluded_columns=(
                ExcludedColumn(name="run_id", reason="Non-deterministic UUID"),
            ),
            fuzzy_columns=(
                FuzzyColumn(
                    name="interest", tolerance=0.01,
                    tolerance_type=ToleranceType.ABSOLUTE,
                    reason="Spark vs ADF rounding",
                ),
            ),
        )
        schema = SchemaInfo(
            column_names=("run_id", "account_id", "balance", "interest"),
            column_types={},
        )
        summary = ComparisonSummary(
            row_count_lhs=1, row_count_rhs=1,
            match_count=1, mismatch_count=0,
            match_percentage=100.0, result="PASS",
            threshold=100.0, line_break_mismatch=None,
        )
        report = build_report(
            "/path", config, {}, schema, summary,
            None, None, empty_diff, empty_correlation,
        )
        cc = report["column_classifications"]
        assert cc[0]["name"] == "run_id"
        assert cc[0]["classification"] == "EXCLUDED"
        assert cc[0]["reason"] == "Non-deterministic UUID"
        assert cc[1]["classification"] == "STRICT"
        assert cc[3]["name"] == "interest"
        assert cc[3]["classification"] == "FUZZY"
        assert cc[3]["tolerance"] == 0.01


class TestSchemaFailReport:
    """FSD-7.10: Schema mismatch report structure."""

    def test_schema_fail_report_structure(self):
        config = ComparisonConfig(
            comparison_target="test", reader=ReaderType.PARQUET,
        )
        report = build_schema_fail_report(
            config_path="/path",
            config=config,
            config_raw={"reader": "parquet"},
            schema_mismatches=["Column count mismatch: LHS 3, RHS 2"],
            lhs_row_count=10,
            rhs_row_count=10,
            line_break_mismatch=None,
        )
        assert report["summary"]["result"] == "FAIL"
        assert report["summary"]["match_count"] == 0
        assert report["summary"]["match_percentage"] == 0.0
        assert report["mismatches"]["schema_mismatches"] == [
            "Column count mismatch: LHS 3, RHS 2"
        ]
        assert report["attestation"] == ATTESTATION


class TestSerializeReport:
    """Report serialization."""

    def test_serialize_produces_valid_json(self, basic_config, basic_schema, empty_diff, empty_correlation):
        summary = ComparisonSummary(
            row_count_lhs=3, row_count_rhs=3,
            match_count=3, mismatch_count=0,
            match_percentage=100.0, result="PASS",
            threshold=100.0, line_break_mismatch=None,
        )
        report = build_report(
            "/path", basic_config, {}, basic_schema, summary,
            None, None, empty_diff, empty_correlation,
        )
        json_str = serialize_report(report)
        parsed = json.loads(json_str)
        assert parsed["summary"]["result"] == "PASS"

    def test_fuzzy_failure_with_null_serializes(self, basic_config, basic_schema, empty_correlation):
        """F-05: FUZZY failure with null lhs_value serializes correctly in JSON."""
        from proofmark.diff import HashGroupResult
        ff = FuzzyFailure(
            column="balance", lhs_value=None, rhs_value=100.0,
            tolerance=0.01, tolerance_type="absolute", actual_delta=100.0,
        )
        hg = HashGroupResult(
            hash_value="abc123", lhs_count=1, rhs_count=1,
            status="MATCH", matched_count=0,
            surplus_rows=[
                UnmatchedRow(side="lhs", content="1001|__PROOFMARK_NULL__", row_data={}),
                UnmatchedRow(side="rhs", content="1001|100.0", row_data={}),
            ],
            fuzzy_failures=[ff],
        )
        diff_result = DiffResult(
            hash_groups=[hg],
            all_unmatched_lhs=[], all_unmatched_rhs=[],
            all_fuzzy_failures=[ff],
            total_matched=0, total_lhs=1, total_rhs=1,
        )
        summary = ComparisonSummary(
            row_count_lhs=1, row_count_rhs=1,
            match_count=0, mismatch_count=1,
            match_percentage=0.0, result="FAIL",
            threshold=100.0, line_break_mismatch=None,
        )
        report = build_report(
            "/path", basic_config, {}, basic_schema, summary,
            None, None, diff_result, empty_correlation,
        )
        json_str = serialize_report(report)
        parsed = json.loads(json_str)
        ff_out = parsed["mismatches"]["hash_groups"][0]["fuzzy_failures"][0]
        assert ff_out["lhs_value"] is None
        assert ff_out["rhs_value"] == 100.0
        assert ff_out["actual_delta"] == 100.0


class TestLineBreakInReport:
    """Line break mismatch field in report."""

    def test_csv_includes_line_break_field(self, basic_schema, empty_diff, empty_correlation):
        config = ComparisonConfig(
            comparison_target="test", reader=ReaderType.CSV,
        )
        summary = ComparisonSummary(
            row_count_lhs=3, row_count_rhs=3,
            match_count=3, mismatch_count=0,
            match_percentage=100.0, result="PASS",
            threshold=100.0, line_break_mismatch=False,
        )
        report = build_report(
            "/path", config, {}, basic_schema, summary,
            [], [], empty_diff, empty_correlation,
        )
        assert "line_break_mismatch" in report["summary"]
        assert report["summary"]["line_break_mismatch"] is False

    def test_parquet_omits_line_break_field(self, basic_config, basic_schema, empty_diff, empty_correlation):
        summary = ComparisonSummary(
            row_count_lhs=3, row_count_rhs=3,
            match_count=3, mismatch_count=0,
            match_percentage=100.0, result="PASS",
            threshold=100.0, line_break_mismatch=None,
        )
        report = build_report(
            "/path", basic_config, {}, basic_schema, summary,
            None, None, empty_diff, empty_correlation,
        )
        assert "line_break_mismatch" not in report["summary"]


class TestHeaderTrailerInReport:
    """Header/trailer comparison in report."""

    def test_header_comparison_included(self, basic_schema, empty_diff, empty_correlation):
        config = ComparisonConfig(
            comparison_target="test", reader=ReaderType.CSV,
        )
        summary = ComparisonSummary(
            row_count_lhs=1, row_count_rhs=1,
            match_count=1, mismatch_count=0,
            match_percentage=100.0, result="PASS",
            threshold=100.0, line_break_mismatch=False,
        )
        headers = [HeaderTrailerResult(position=0, lhs="a,b,c", rhs="a,b,c", match=True)]
        report = build_report(
            "/path", config, {}, basic_schema, summary,
            headers, None, empty_diff, empty_correlation,
        )
        assert report["header_comparison"] is not None
        assert len(report["header_comparison"]) == 1
        assert report["header_comparison"][0]["match"] is True

    def test_parquet_has_null_header_trailer(self, basic_config, basic_schema, empty_diff, empty_correlation):
        summary = ComparisonSummary(
            row_count_lhs=1, row_count_rhs=1,
            match_count=1, mismatch_count=0,
            match_percentage=100.0, result="PASS",
            threshold=100.0, line_break_mismatch=None,
        )
        report = build_report(
            "/path", basic_config, {}, basic_schema, summary,
            None, None, empty_diff, empty_correlation,
        )
        assert report["header_comparison"] is None
        assert report["trailer_comparison"] is None
