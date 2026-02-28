"""End-to-end pipeline tests — BDD scenarios 22-23, 29-33, 41-42, 44, 45.
[FSD Appendix A]"""
import pytest

from proofmark import ConfigError
from proofmark.pipeline import run


class TestLineBreakMismatch:
    """Scenario 29: Mismatched line breaks set FAIL flag [BR-4.1, BR-4.2, BR-4.4, BR-4.5]"""

    def test_crlf_vs_lf_fails(self, csv_fixtures, config_fixtures):
        report = run(
            config_fixtures / "csv_simple.yaml",
            csv_fixtures / "crlf_vs_lf" / "lhs.csv",
            csv_fixtures / "crlf_vs_lf" / "rhs.csv",
        )
        assert report["summary"]["result"] == "FAIL"
        assert report["summary"]["line_break_mismatch"] is True
        # Data still matches — match_percentage should be 100.0
        assert report["summary"]["match_percentage"] == 100.0

    def test_comparison_continues_despite_line_break_mismatch(self, csv_fixtures, config_fixtures):
        """The full comparison runs even with line break mismatch [BR-4.4]."""
        report = run(
            config_fixtures / "csv_simple.yaml",
            csv_fixtures / "crlf_vs_lf" / "lhs.csv",
            csv_fixtures / "crlf_vs_lf" / "rhs.csv",
        )
        # Summary should still have full data comparison results
        assert "match_count" in report["summary"]
        assert "mismatch_count" in report["summary"]


class TestMatchingLineBreaks:
    """Scenario 30: Matching line breaks produce no flag [BR-4.1]"""

    def test_matching_line_breaks_pass(self, csv_fixtures, config_fixtures):
        report = run(
            config_fixtures / "csv_simple.yaml",
            csv_fixtures / "matching_line_breaks" / "lhs.csv",
            csv_fixtures / "matching_line_breaks" / "rhs.csv",
        )
        assert report["summary"]["result"] == "PASS"
        assert report["summary"]["line_break_mismatch"] is False


class TestLineBreakNotApplicableToParquet:
    """Scenario 31: Line break check does not apply to parquet [BR-4.6]"""

    def test_parquet_no_line_break_field(self, parquet_fixtures, config_fixtures):
        report = run(
            config_fixtures / "parquet_default.yaml",
            parquet_fixtures / "identical_simple" / "lhs",
            parquet_fixtures / "identical_simple" / "rhs",
        )
        assert "line_break_mismatch" not in report["summary"]


class TestEncodingCorrect:
    """Scenario 32: Configured encoding reads files correctly [BR-9.1, BR-9.4]"""

    def test_utf8_encoding_reads_correctly(self, csv_fixtures, config_fixtures):
        report = run(
            config_fixtures / "csv_with_encoding.yaml",
            csv_fixtures / "encoding_utf8" / "lhs.csv",
            csv_fixtures / "encoding_utf8" / "rhs.csv",
        )
        assert report["summary"]["result"] == "PASS"


class TestEncodingInvalid:
    """Scenario 33: Invalid encoding produces error [BR-9.2]"""

    def test_ascii_encoding_on_utf8_file_raises(self, csv_fixtures, config_fixtures):
        from proofmark import EncodingError
        with pytest.raises(EncodingError):
            run(
                config_fixtures / "csv_encoding_ascii.yaml",
                csv_fixtures / "encoding_invalid" / "lhs.csv",
                csv_fixtures / "encoding_invalid" / "rhs.csv",
            )


class TestCsvHeaderMismatchPipeline:
    """Scenario 22: CSV header difference causes FAIL [BR-3.13, BR-3.14]

    Note: When headers differ in column names, schema validation catches
    the column name mismatch first (Step 3 in pipeline, before Step 4
    header/trailer comparison). This is correct per FSD-5.10.4 — schema
    validation short-circuits the pipeline.
    """

    def test_header_mismatch_fails_via_schema(self, csv_fixtures, config_fixtures):
        report = run(
            config_fixtures / "csv_simple.yaml",
            csv_fixtures / "header_mismatch" / "lhs.csv",
            csv_fixtures / "header_mismatch" / "rhs.csv",
        )
        assert report["summary"]["result"] == "FAIL"
        # Schema validation catches the column name difference
        assert report["mismatches"]["schema_mismatches"] is not None
        assert len(report["mismatches"]["schema_mismatches"]) >= 1


class TestHeaderAutoFailBypassesSchema:
    """H-02: Header literal difference detected even when parsed column names match.

    Headers like 'account_id,balance,status' and '"account_id","balance","status"'
    parse to the same column names (schema passes), but the literal header strings
    differ — triggering an auto-fail via compare_lines. [BR-3.13, BR-3.14]
    """

    def test_header_quoting_difference_fails(self, csv_fixtures, config_fixtures):
        report = run(
            config_fixtures / "csv_simple.yaml",
            csv_fixtures / "header_quoting_mismatch" / "lhs.csv",
            csv_fixtures / "header_quoting_mismatch" / "rhs.csv",
        )
        assert report["summary"]["result"] == "FAIL"
        # Schema should PASS — column names are identical after parsing
        assert report["mismatches"]["schema_mismatches"] is None
        # Header comparison should show the mismatch
        assert report["header_comparison"] is not None
        assert any(not h["match"] for h in report["header_comparison"])


class TestCsvTrailerMismatchPipeline:
    """Scenario 23: CSV trailer difference causes FAIL [BR-3.13, BR-3.14]"""

    def test_trailer_mismatch_fails(self, csv_fixtures, config_fixtures):
        report = run(
            config_fixtures / "csv_with_trailer.yaml",
            csv_fixtures / "trailer_mismatch" / "lhs.csv",
            csv_fixtures / "trailer_mismatch" / "rhs.csv",
        )
        assert report["summary"]["result"] == "FAIL"
        assert report["trailer_comparison"] is not None
        has_mismatch = any(
            not t["match"] for t in report["trailer_comparison"]
        )
        assert has_mismatch


class TestCsvNullRepresentations:
    """Scenario 22 (null): CSV empty field vs literal NULL is a mismatch [BR-8.2, BR-8.3]"""

    def test_empty_vs_null_string_mismatch(self, csv_fixtures, config_fixtures):
        report = run(
            config_fixtures / "csv_simple.yaml",
            csv_fixtures / "null_representations" / "lhs.csv",
            csv_fixtures / "null_representations" / "rhs.csv",
        )
        assert report["summary"]["result"] == "FAIL"
        assert report["summary"]["mismatch_count"] >= 1


class TestCsvNullCaseSensitivity:
    """Scenario 23 (null): NULL vs null are different byte sequences [BR-8.2]"""

    def test_null_vs_null_case_mismatch(self, csv_fixtures, config_fixtures):
        report = run(
            config_fixtures / "csv_simple.yaml",
            csv_fixtures / "null_case_sensitivity" / "lhs.csv",
            csv_fixtures / "null_case_sensitivity" / "rhs.csv",
        )
        assert report["summary"]["result"] == "FAIL"


class TestParquetNullHandlingPipeline:
    """Parquet null handling through the full pipeline."""

    def test_null_vs_null_passes(self, parquet_fixtures, config_fixtures):
        report = run(
            config_fixtures / "parquet_default.yaml",
            parquet_fixtures / "with_nulls" / "lhs",
            parquet_fixtures / "with_nulls" / "rhs",
        )
        assert report["summary"]["result"] == "PASS"

    def test_null_vs_empty_string_fails(self, parquet_fixtures, config_fixtures):
        report = run(
            config_fixtures / "parquet_default.yaml",
            parquet_fixtures / "null_vs_empty_string" / "lhs",
            parquet_fixtures / "null_vs_empty_string" / "rhs",
        )
        assert report["summary"]["result"] == "FAIL"


class TestExcludedColumnPipeline:
    """Scenario 15 integration: EXCLUDED columns via pipeline."""

    def test_excluded_column_passes(self, parquet_fixtures, config_fixtures):
        report = run(
            config_fixtures / "parquet_with_exclusions.yaml",
            parquet_fixtures / "excluded_column" / "lhs",
            parquet_fixtures / "excluded_column" / "rhs",
        )
        assert report["summary"]["result"] == "PASS"
        # Verify classification in report
        classifications = {
            c["name"]: c["classification"]
            for c in report["column_classifications"]
        }
        assert classifications["run_id"] == "EXCLUDED"
        assert classifications["account_id"] == "STRICT"


class TestFuzzyPipeline:
    """FUZZY tolerance through the full pipeline."""

    def test_fuzzy_within_tolerance_passes(self, parquet_fixtures, config_fixtures):
        report = run(
            config_fixtures / "parquet_with_fuzzy.yaml",
            parquet_fixtures / "fuzzy_absolute_within" / "lhs",
            parquet_fixtures / "fuzzy_absolute_within" / "rhs",
        )
        assert report["summary"]["result"] == "PASS"

    def test_fuzzy_exceeded_tolerance_fails(self, parquet_fixtures, config_fixtures):
        report = run(
            config_fixtures / "parquet_with_fuzzy.yaml",
            parquet_fixtures / "fuzzy_absolute_exceeded" / "lhs",
            parquet_fixtures / "fuzzy_absolute_exceeded" / "rhs",
        )
        assert report["summary"]["result"] == "FAIL"
        assert report["summary"]["mismatch_count"] >= 1
        # Fuzzy failure should be in mismatches
        assert len(report["mismatches"]["hash_groups"]) >= 1
        has_fuzzy = any(
            hg["fuzzy_failures"]
            for hg in report["mismatches"]["hash_groups"]
        )
        assert has_fuzzy


class TestMixedClassificationPipeline:
    """Scenario 19 integration: Mixed EXCLUDED + STRICT + FUZZY."""

    def test_mixed_classification_passes(self, parquet_fixtures, config_fixtures):
        report = run(
            config_fixtures / "mixed_classifications.yaml",
            parquet_fixtures / "mixed_classification" / "lhs",
            parquet_fixtures / "mixed_classification" / "rhs",
        )
        assert report["summary"]["result"] == "PASS"
        classifications = {
            c["name"]: c["classification"]
            for c in report["column_classifications"]
        }
        assert classifications["run_id"] == "EXCLUDED"
        assert classifications["account_id"] == "STRICT"
        assert classifications["balance"] == "STRICT"
        assert classifications["interest_accrued"] == "FUZZY"


class TestRowOrderPipeline:
    """Scenario 26 integration: Row order independence."""

    def test_different_order_passes(self, parquet_fixtures, config_fixtures):
        report = run(
            config_fixtures / "parquet_default.yaml",
            parquet_fixtures / "different_row_order" / "lhs",
            parquet_fixtures / "different_row_order" / "rhs",
        )
        assert report["summary"]["result"] == "PASS"
        assert report["summary"]["match_count"] == 3


class TestDuplicateRowsPipeline:
    """Scenario 27 integration: Duplicate rows multiset."""

    def test_duplicate_rows_fail(self, parquet_fixtures, config_fixtures):
        report = run(
            config_fixtures / "parquet_default.yaml",
            parquet_fixtures / "duplicate_rows" / "lhs",
            parquet_fixtures / "duplicate_rows" / "rhs",
        )
        assert report["summary"]["result"] == "FAIL"
        assert report["summary"]["row_count_lhs"] == 2
        assert report["summary"]["row_count_rhs"] == 1


class TestThresholdPass:
    """Scenario 41: Threshold below 100% with mismatches within threshold passes [BR-11.22]"""

    def test_threshold_99_passes_with_1pct_mismatch(self, parquet_fixtures, config_fixtures):
        report = run(
            config_fixtures / "threshold_99_percent.yaml",
            parquet_fixtures / "threshold_pass" / "lhs",
            parquet_fixtures / "threshold_pass" / "rhs",
        )
        assert report["summary"]["result"] == "PASS"
        assert report["summary"]["match_percentage"] < 100.0
        # Mismatches should still be in report [BR-11.24]
        assert report["summary"]["mismatch_count"] >= 1


class TestThreshold100Fail:
    """Scenario 42: Threshold 100% with any mismatch fails [BR-11.23, BR-11.25]"""

    def test_threshold_100_fails_with_any_mismatch(self, parquet_fixtures, config_fixtures):
        report = run(
            config_fixtures / "parquet_default.yaml",  # threshold=100 (default)
            parquet_fixtures / "threshold_fail" / "lhs",
            parquet_fixtures / "threshold_fail" / "rhs",
        )
        assert report["summary"]["result"] == "FAIL"
        assert report["summary"]["match_percentage"] < 100.0


class TestSchemaValidationPipeline:
    """Schema validation through the full pipeline."""

    def test_column_count_mismatch_fails(self, parquet_fixtures, config_fixtures):
        report = run(
            config_fixtures / "parquet_default.yaml",
            parquet_fixtures / "schema_mismatch_column_count" / "lhs",
            parquet_fixtures / "schema_mismatch_column_count" / "rhs",
        )
        assert report["summary"]["result"] == "FAIL"
        assert report["mismatches"]["schema_mismatches"] is not None

    def test_column_name_mismatch_fails(self, parquet_fixtures, config_fixtures):
        report = run(
            config_fixtures / "parquet_default.yaml",
            parquet_fixtures / "schema_mismatch_column_name" / "lhs",
            parquet_fixtures / "schema_mismatch_column_name" / "rhs",
        )
        assert report["summary"]["result"] == "FAIL"
        assert report["mismatches"]["schema_mismatches"] is not None

    def test_column_type_mismatch_fails(self, parquet_fixtures, config_fixtures):
        report = run(
            config_fixtures / "parquet_default.yaml",
            parquet_fixtures / "schema_mismatch_column_type" / "lhs",
            parquet_fixtures / "schema_mismatch_column_type" / "rhs",
        )
        assert report["summary"]["result"] == "FAIL"
        assert report["mismatches"]["schema_mismatches"] is not None


class TestZeroRowsPipeline:
    """Scenario 65 integration: Both sides zero rows — PASS."""

    def test_zero_rows_passes(self, parquet_fixtures, config_fixtures):
        report = run(
            config_fixtures / "parquet_default.yaml",
            parquet_fixtures / "zero_rows" / "lhs",
            parquet_fixtures / "zero_rows" / "rhs",
        )
        assert report["summary"]["result"] == "PASS"
        assert report["summary"]["row_count_lhs"] == 0
        assert report["summary"]["row_count_rhs"] == 0
        assert report["summary"]["match_percentage"] == 100.0


class TestRowCountMismatchPipeline:
    """Scenario 64 integration: Different row counts."""

    def test_row_count_mismatch(self, parquet_fixtures, config_fixtures):
        report = run(
            config_fixtures / "parquet_default.yaml",
            parquet_fixtures / "row_count_mismatch" / "lhs",
            parquet_fixtures / "row_count_mismatch" / "rhs",
        )
        assert report["summary"]["result"] == "FAIL"
        assert report["summary"]["row_count_lhs"] == 100
        assert report["summary"]["row_count_rhs"] == 99


class TestFuzzyFailReducesMatchPercentage:
    """Scenario 44: FUZZY tolerance failure reduces match percentage [BR-11.25, BR-4.21]"""

    def test_fuzzy_fail_reduces_match_pct(self, parquet_fixtures, config_fixtures):
        report = run(
            config_fixtures / "parquet_fuzzy_balance.yaml",
            parquet_fixtures / "fuzzy_fail_hash_match" / "lhs",
            parquet_fixtures / "fuzzy_fail_hash_match" / "rhs",
        )
        assert report["summary"]["result"] == "FAIL"
        assert report["summary"]["match_count"] == 0
        assert report["summary"]["mismatch_count"] == 1
        assert report["summary"]["match_percentage"] == 0.0


class TestLineBreakMismatchWith100PctData:
    """Scenario 43: Line break mismatch causes FAIL even with 100% data match [BR-11.25]"""

    def test_line_break_fail_with_perfect_data(self, csv_fixtures, config_fixtures):
        report = run(
            config_fixtures / "csv_simple.yaml",
            csv_fixtures / "crlf_vs_lf" / "lhs.csv",
            csv_fixtures / "crlf_vs_lf" / "rhs.csv",
        )
        assert report["summary"]["result"] == "FAIL"
        assert report["summary"]["match_percentage"] == 100.0
        assert report["summary"]["line_break_mismatch"] is True


class TestCorrelationPipeline:
    """Scenarios 46-47 integration: Correlation through the pipeline."""

    def test_high_confidence_correlation(self, parquet_fixtures, config_fixtures):
        report = run(
            config_fixtures / "parquet_default.yaml",
            parquet_fixtures / "correlation_high_confidence" / "lhs",
            parquet_fixtures / "correlation_high_confidence" / "rhs",
        )
        assert report["summary"]["result"] == "FAIL"
        correlation = report["mismatches"]["correlation"]
        assert len(correlation["correlated_pairs"]) >= 1
        assert correlation["correlated_pairs"][0]["confidence"] == "high"

    def test_low_confidence_falls_back(self, parquet_fixtures, config_fixtures):
        report = run(
            config_fixtures / "parquet_default.yaml",
            parquet_fixtures / "correlation_low_confidence" / "lhs",
            parquet_fixtures / "correlation_low_confidence" / "rhs",
        )
        assert report["summary"]["result"] == "FAIL"
        correlation = report["mismatches"]["correlation"]
        # No rows should be correlated — all columns differ
        assert len(correlation["correlated_pairs"]) == 0
        # Low confidence rows should be in uncorrelated lists
        total_uncorrelated = (
            len(correlation["uncorrelated_lhs"]) +
            len(correlation["uncorrelated_rhs"])
        )
        assert total_uncorrelated >= 1


class TestExcludedOrderingPipeline:
    """Scenario 28 integration: EXCLUDED columns don't affect hash ordering."""

    def test_excluded_ordering_passes(self, parquet_fixtures, tmp_config):
        # excluded_ordering fixture has column "uuid", not "run_id"
        config_path = tmp_config({
            "comparison_target": "test_excluded_ordering",
            "reader": "parquet",
            "columns": {
                "excluded": [
                    {"name": "uuid", "reason": "Non-deterministic identifier"},
                ],
            },
        })
        report = run(
            config_path,
            parquet_fixtures / "excluded_ordering" / "lhs",
            parquet_fixtures / "excluded_ordering" / "rhs",
        )
        assert report["summary"]["result"] == "PASS"


class TestFuzzyRelativePipeline:
    """Scenario 17 integration: FUZZY relative tolerance."""

    def test_relative_within_tolerance_passes(self, parquet_fixtures, config_fixtures):
        report = run(
            config_fixtures / "parquet_fuzzy_relative.yaml",
            parquet_fixtures / "fuzzy_relative_within" / "lhs",
            parquet_fixtures / "fuzzy_relative_within" / "rhs",
        )
        assert report["summary"]["result"] == "PASS"


class TestFuzzyZeroEdgePipeline:
    """Scenario 34 integration: Both values zero with relative tolerance."""

    def test_both_zero_relative_passes(self, parquet_fixtures, config_fixtures):
        report = run(
            config_fixtures / "parquet_fuzzy_relative_zero.yaml",
            parquet_fixtures / "fuzzy_both_zero" / "lhs",
            parquet_fixtures / "fuzzy_both_zero" / "rhs",
        )
        assert report["summary"]["result"] == "PASS"


class TestThresholdBoundaryPipeline:
    """Scenario 42 boundary: Threshold at exact boundary."""

    def test_threshold_boundary_passes(self, parquet_fixtures, config_fixtures):
        """200 LHS, 200 RHS, 2 differ → 198 matched, 99.0% match, threshold=99% → PASS."""
        report = run(
            config_fixtures / "threshold_99_percent.yaml",
            parquet_fixtures / "threshold_boundary" / "lhs",
            parquet_fixtures / "threshold_boundary" / "rhs",
        )
        assert report["summary"]["result"] == "PASS"
        assert report["summary"]["match_count"] == 198
        assert report["summary"]["mismatch_count"] == 2
        assert report["summary"]["match_percentage"] == pytest.approx(99.0)


class TestNonNumericFuzzyColumnPipeline:
    """F-03: Non-numeric FUZZY column raises ConfigError through pipeline [BR-4.21, FSD-5.7.5]"""

    def test_string_column_as_fuzzy_raises(self, parquet_fixtures, tmp_config):
        config_path = tmp_config({
            "comparison_target": "test_non_numeric_fuzzy",
            "reader": "parquet",
            "columns": {
                "fuzzy": [{
                    "name": "name",
                    "tolerance": 0.01,
                    "tolerance_type": "absolute",
                    "reason": "Intentionally wrong — name is a string",
                }],
            },
        })
        with pytest.raises(ConfigError, match="non-numeric"):
            run(
                config_path,
                parquet_fixtures / "identical_simple" / "lhs",
                parquet_fixtures / "identical_simple" / "rhs",
            )


class TestFuzzyOneZeroPipeline:
    """F-06: One value zero, other non-zero with relative tolerance through pipeline [BR-7.5]"""

    def test_one_zero_relative_fails(self, parquet_fixtures, config_fixtures):
        report = run(
            config_fixtures / "parquet_fuzzy_relative_zero.yaml",
            parquet_fixtures / "fuzzy_one_zero" / "lhs",
            parquet_fixtures / "fuzzy_one_zero" / "rhs",
        )
        assert report["summary"]["result"] == "FAIL"
        assert report["summary"]["mismatch_count"] >= 1
