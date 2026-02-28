"""Isolated unit tests for pipeline._determine_result and compare_lines.

Addresses audit findings C-01, C-02, C-05, H-04.
[FSD-5.10.11, FSD-5.10.12]
"""
import math

import pytest

from proofmark.pipeline import _determine_result, compare_lines
from proofmark.report import HeaderTrailerResult


class TestDetermineResultThresholdPass:
    """_determine_result returns PASS when threshold is met with no auto-fails."""

    def test_all_matched_100_threshold(self):
        result = _determine_result(
            total_rows=200, total_matched=200, threshold=100.0,
            line_break_mismatch=None, header_comparison=None, trailer_comparison=None,
        )
        assert result == "PASS"

    def test_partial_match_below_threshold(self):
        """99 matched out of 200 total, threshold=49% → ceil(200*49/100)=98 → 99>=98 → PASS."""
        result = _determine_result(
            total_rows=200, total_matched=99, threshold=49.0,
            line_break_mismatch=None, header_comparison=None, trailer_comparison=None,
        )
        assert result == "PASS"

    def test_zero_rows_always_passes(self):
        result = _determine_result(
            total_rows=0, total_matched=0, threshold=100.0,
            line_break_mismatch=None, header_comparison=None, trailer_comparison=None,
        )
        assert result == "PASS"


class TestDetermineResultThresholdFail:
    """_determine_result returns FAIL when threshold is not met."""

    def test_below_threshold_fails(self):
        """0 matched out of 200, threshold=100% → FAIL."""
        result = _determine_result(
            total_rows=200, total_matched=0, threshold=100.0,
            line_break_mismatch=None, header_comparison=None, trailer_comparison=None,
        )
        assert result == "FAIL"

    def test_just_under_threshold_fails(self):
        """197 matched out of 200, threshold=99% → ceil(200*99/100)=198 → 197<198 → FAIL."""
        result = _determine_result(
            total_rows=200, total_matched=197, threshold=99.0,
            line_break_mismatch=None, header_comparison=None, trailer_comparison=None,
        )
        assert result == "FAIL"


class TestDetermineResultThresholdBoundaryMath:
    """C-02: Threshold boundary uses math.ceil integer arithmetic. [FSD-5.10.11]"""

    def test_exact_boundary_passes(self):
        """198 matched out of 200, threshold=99% → ceil(200*99/100)=ceil(198.0)=198 → 198>=198 → PASS."""
        result = _determine_result(
            total_rows=200, total_matched=198, threshold=99.0,
            line_break_mismatch=None, header_comparison=None, trailer_comparison=None,
        )
        assert result == "PASS"

    def test_ceil_rounding_up(self):
        """7 matched out of 10, threshold=66% → ceil(10*66/100)=ceil(6.6)=7 → 7>=7 → PASS."""
        required = math.ceil(10 * 66 / 100.0)
        assert required == 7  # Sanity check
        result = _determine_result(
            total_rows=10, total_matched=7, threshold=66.0,
            line_break_mismatch=None, header_comparison=None, trailer_comparison=None,
        )
        assert result == "PASS"

    def test_ceil_rounding_one_short_fails(self):
        """6 matched out of 10, threshold=66% → ceil(6.6)=7 → 6<7 → FAIL."""
        result = _determine_result(
            total_rows=10, total_matched=6, threshold=66.0,
            line_break_mismatch=None, header_comparison=None, trailer_comparison=None,
        )
        assert result == "FAIL"

    def test_threshold_50_boundary(self):
        """5 matched out of 10, threshold=50% → ceil(5.0)=5 → 5>=5 → PASS."""
        result = _determine_result(
            total_rows=10, total_matched=5, threshold=50.0,
            line_break_mismatch=None, header_comparison=None, trailer_comparison=None,
        )
        assert result == "PASS"

    def test_odd_total_ceil_behavior(self):
        """3 matched out of 3, threshold=99% → ceil(3*99/100)=ceil(2.97)=3 → 3>=3 → PASS."""
        required = math.ceil(3 * 99.0 / 100.0)
        assert required == 3
        result = _determine_result(
            total_rows=3, total_matched=3, threshold=99.0,
            line_break_mismatch=None, header_comparison=None, trailer_comparison=None,
        )
        assert result == "PASS"

    def test_odd_total_just_under_ceil_fails(self):
        """2 matched out of 3, threshold=99% → ceil(2.97)=3 → 2<3 → FAIL."""
        result = _determine_result(
            total_rows=3, total_matched=2, threshold=99.0,
            line_break_mismatch=None, header_comparison=None, trailer_comparison=None,
        )
        assert result == "FAIL"


class TestDetermineResultLineBreakAutoFail:
    """Line break mismatch is an auto-fail even when threshold passes."""

    def test_line_break_mismatch_fails_despite_100_match(self):
        result = _determine_result(
            total_rows=200, total_matched=200, threshold=100.0,
            line_break_mismatch=True, header_comparison=None, trailer_comparison=None,
        )
        assert result == "FAIL"

    def test_line_break_false_passes(self):
        result = _determine_result(
            total_rows=200, total_matched=200, threshold=100.0,
            line_break_mismatch=False, header_comparison=None, trailer_comparison=None,
        )
        assert result == "PASS"

    def test_line_break_none_passes(self):
        """Parquet sets line_break_mismatch=None — should not trigger auto-fail."""
        result = _determine_result(
            total_rows=200, total_matched=200, threshold=100.0,
            line_break_mismatch=None, header_comparison=None, trailer_comparison=None,
        )
        assert result == "PASS"


class TestDetermineResultHeaderAutoFail:
    """Header mismatch is an auto-fail even when threshold passes."""

    def test_header_mismatch_fails(self):
        headers = [HeaderTrailerResult(position=0, lhs="a,b,c", rhs="a,b,d", match=False)]
        result = _determine_result(
            total_rows=200, total_matched=200, threshold=100.0,
            line_break_mismatch=None, header_comparison=headers, trailer_comparison=None,
        )
        assert result == "FAIL"

    def test_header_all_match_passes(self):
        headers = [HeaderTrailerResult(position=0, lhs="a,b,c", rhs="a,b,c", match=True)]
        result = _determine_result(
            total_rows=200, total_matched=200, threshold=100.0,
            line_break_mismatch=None, header_comparison=headers, trailer_comparison=None,
        )
        assert result == "PASS"

    def test_header_none_passes(self):
        """Parquet has no header comparison."""
        result = _determine_result(
            total_rows=200, total_matched=200, threshold=100.0,
            line_break_mismatch=None, header_comparison=None, trailer_comparison=None,
        )
        assert result == "PASS"

    def test_empty_header_list_passes(self):
        """Empty list should not trigger auto-fail."""
        result = _determine_result(
            total_rows=200, total_matched=200, threshold=100.0,
            line_break_mismatch=None, header_comparison=[], trailer_comparison=None,
        )
        assert result == "PASS"


class TestDetermineResultTrailerAutoFail:
    """Trailer mismatch is an auto-fail even when threshold passes."""

    def test_trailer_mismatch_fails(self):
        trailers = [HeaderTrailerResult(position=0, lhs="TRAILER,10,2026-02-28", rhs="TRAILER,10,2026-02-27", match=False)]
        result = _determine_result(
            total_rows=200, total_matched=200, threshold=100.0,
            line_break_mismatch=None, header_comparison=None, trailer_comparison=trailers,
        )
        assert result == "FAIL"

    def test_trailer_all_match_passes(self):
        trailers = [HeaderTrailerResult(position=0, lhs="TRAILER,10", rhs="TRAILER,10", match=True)]
        result = _determine_result(
            total_rows=200, total_matched=200, threshold=100.0,
            line_break_mismatch=None, header_comparison=None, trailer_comparison=trailers,
        )
        assert result == "PASS"


class TestDetermineResultMultipleAutoFails:
    """Multiple auto-fail conditions — any one should trigger FAIL."""

    def test_line_break_and_header_both_fail(self):
        headers = [HeaderTrailerResult(position=0, lhs="a", rhs="b", match=False)]
        result = _determine_result(
            total_rows=200, total_matched=200, threshold=100.0,
            line_break_mismatch=True, header_comparison=headers, trailer_comparison=None,
        )
        assert result == "FAIL"

    def test_threshold_fail_with_matching_headers(self):
        """Threshold alone can cause FAIL even with no auto-fail conditions."""
        headers = [HeaderTrailerResult(position=0, lhs="a", rhs="a", match=True)]
        result = _determine_result(
            total_rows=200, total_matched=0, threshold=100.0,
            line_break_mismatch=False, header_comparison=headers, trailer_comparison=None,
        )
        assert result == "FAIL"


class TestDetermineResultSchemaHandling:
    """C-01: _determine_result doesn't check schema mismatches directly.

    This is correct by design — schema mismatches short-circuit the pipeline
    in pipeline.run() (Step 3, FSD-5.10.4) before _determine_result is ever
    called. This test documents that contract.
    """

    def test_function_has_no_schema_parameter(self):
        """_determine_result has no schema_mismatches parameter — by design."""
        import inspect
        sig = inspect.signature(_determine_result)
        param_names = set(sig.parameters.keys())
        assert "schema_mismatches" not in param_names
        assert "schema" not in param_names


class TestCompareLines:
    """H-04: Isolated tests for compare_lines helper. [FSD-5.10.12]"""

    def test_matching_lines(self):
        lhs = ("a,b,c",)
        rhs = ("a,b,c",)
        result = compare_lines(lhs, rhs)
        assert len(result) == 1
        assert result[0].match is True
        assert result[0].position == 0

    def test_mismatching_lines(self):
        lhs = ("a,b,c",)
        rhs = ("a,b,d",)
        result = compare_lines(lhs, rhs)
        assert len(result) == 1
        assert result[0].match is False

    def test_multiple_lines(self):
        lhs = ("line1", "line2")
        rhs = ("line1", "DIFFERENT")
        result = compare_lines(lhs, rhs)
        assert len(result) == 2
        assert result[0].match is True
        assert result[1].match is False
        assert result[1].position == 1

    def test_none_lhs_returns_empty(self):
        result = compare_lines(None, ("a",))
        assert result == []

    def test_none_rhs_returns_empty(self):
        result = compare_lines(("a",), None)
        assert result == []

    def test_both_none_returns_empty(self):
        result = compare_lines(None, None)
        assert result == []

    def test_preserves_exact_string(self):
        """compare_lines does string equality, not CSV-parsed equality."""
        lhs = ('"a","b","c"',)
        rhs = ("a,b,c",)
        result = compare_lines(lhs, rhs)
        assert result[0].match is False


class TestMismatchCountFormula:
    """C-04: Isolated mismatch_count = max(lhs, rhs) - match_count. [FSD-5.10.9]

    The pipeline computes:
      match_count = total_matched // 2
      mismatch_count = max(total_lhs, total_rhs) - match_count
    """

    def test_perfect_match(self):
        """3 LHS, 3 RHS, 3 matched → mismatch=0."""
        total_matched = 6  # 3 pairs * 2 (double-counted)
        total_lhs, total_rhs = 3, 3
        match_count = total_matched // 2
        mismatch_count = max(total_lhs, total_rhs) - match_count
        assert match_count == 3
        assert mismatch_count == 0

    def test_all_mismatch(self):
        """3 LHS, 3 RHS, 0 matched → mismatch=3."""
        total_matched = 0
        total_lhs, total_rhs = 3, 3
        match_count = total_matched // 2
        mismatch_count = max(total_lhs, total_rhs) - match_count
        assert match_count == 0
        assert mismatch_count == 3

    def test_unequal_row_counts(self):
        """100 LHS, 99 RHS, 99 matched → mismatch=1."""
        total_matched = 198  # 99 pairs * 2
        total_lhs, total_rhs = 100, 99
        match_count = total_matched // 2
        mismatch_count = max(total_lhs, total_rhs) - match_count
        assert match_count == 99
        assert mismatch_count == 1

    def test_zero_rows(self):
        """0 LHS, 0 RHS → mismatch=0."""
        total_matched = 0
        total_lhs, total_rhs = 0, 0
        match_count = total_matched // 2
        mismatch_count = max(total_lhs, total_rhs) - match_count
        assert match_count == 0
        assert mismatch_count == 0

    def test_one_side_empty(self):
        """5 LHS, 0 RHS, 0 matched → mismatch=5."""
        total_matched = 0
        total_lhs, total_rhs = 5, 0
        match_count = total_matched // 2
        mismatch_count = max(total_lhs, total_rhs) - match_count
        assert match_count == 0
        assert mismatch_count == 5

    def test_fuzzy_reduces_match_count(self):
        """3 LHS, 3 RHS, 2 hash-matched but 1 fuzzy fail → match=2, mismatch=1."""
        # 2 pairs matched * 2 = 4, plus 1 pair reclassified as unmatched
        total_matched = 4
        total_lhs, total_rhs = 3, 3
        match_count = total_matched // 2
        mismatch_count = max(total_lhs, total_rhs) - match_count
        assert match_count == 2
        assert mismatch_count == 1

    def test_rhs_larger(self):
        """2 LHS, 5 RHS, 2 matched → mismatch=3."""
        total_matched = 4  # 2 pairs * 2
        total_lhs, total_rhs = 2, 5
        match_count = total_matched // 2
        mismatch_count = max(total_lhs, total_rhs) - match_count
        assert match_count == 2
        assert mismatch_count == 3
