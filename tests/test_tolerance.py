"""Tolerance comparator tests — BDD scenarios 16-18, 24-25, 34-38. [FSD Appendix A]"""
import pytest

from proofmark import ConfigError
from proofmark.config import ToleranceType
from proofmark.tolerance import FuzzyFailure, check_fuzzy


class TestFuzzyAbsoluteWithinTolerance:
    """Scenario 16: FUZZY absolute tolerance within threshold passes [BR-7.1, BR-7.2]"""

    def test_within_absolute_tolerance_passes(self):
        result = check_fuzzy("interest", 100.005, 100.004, 0.01, ToleranceType.ABSOLUTE)
        assert result is None

    def test_exact_match_passes(self):
        result = check_fuzzy("interest", 100.00, 100.00, 0.01, ToleranceType.ABSOLUTE)
        assert result is None


class TestFuzzyRelativeWithinTolerance:
    """Scenario 17: FUZZY relative tolerance within threshold passes [BR-7.1, BR-7.3]"""

    def test_within_relative_tolerance_passes(self):
        # |1000000.00 - 1000000.50| / max(|1000000.00|, |1000000.50|) = 0.0000005 <= 0.001
        result = check_fuzzy("market_value", 1000000.00, 1000000.50, 0.001, ToleranceType.RELATIVE)
        assert result is None


class TestFuzzyToleranceExceeded:
    """Scenario 18: FUZZY tolerance exceeded reports mismatch with delta [BR-7.1, BR-11.9]"""

    def test_absolute_tolerance_exceeded(self):
        result = check_fuzzy("interest", 100.00, 100.05, 0.01, ToleranceType.ABSOLUTE)
        assert isinstance(result, FuzzyFailure)
        assert result.column == "interest"
        assert result.actual_delta == pytest.approx(0.05)
        assert result.tolerance == 0.01
        assert result.tolerance_type == "absolute"

    def test_failure_includes_both_values(self):
        result = check_fuzzy("interest", 100.00, 100.05, 0.01, ToleranceType.ABSOLUTE)
        assert result.lhs_value == 100.00
        assert result.rhs_value == 100.05


class TestFuzzyNullVsNull:
    """Scenario 24: FUZZY null vs null matches [BR-8.1, BR-4.21]"""

    def test_null_vs_null_passes(self):
        result = check_fuzzy("balance", None, None, 0.01, ToleranceType.ABSOLUTE)
        assert result is None

    def test_null_vs_null_relative_passes(self):
        result = check_fuzzy("balance", None, None, 0.01, ToleranceType.RELATIVE)
        assert result is None


class TestFuzzyNullVsNonNull:
    """Scenario 25: FUZZY null vs non-null is a mismatch [BR-8.1, BR-4.21]"""

    def test_null_vs_value_fails(self):
        result = check_fuzzy("balance", None, 100.00, 0.01, ToleranceType.ABSOLUTE)
        assert isinstance(result, FuzzyFailure)
        assert result.actual_delta == 100.0

    def test_value_vs_null_fails(self):
        result = check_fuzzy("balance", 100.00, None, 0.01, ToleranceType.ABSOLUTE)
        assert isinstance(result, FuzzyFailure)
        assert result.actual_delta == 100.0


class TestBothValuesZeroRelative:
    """Scenario 34: Both values zero with relative tolerance [BR-7.4]"""

    def test_both_zero_passes(self):
        result = check_fuzzy("delta", 0.0, 0.0, 0.01, ToleranceType.RELATIVE)
        assert result is None


class TestOneValueZeroRelative:
    """Scenario 35: One value zero, other non-zero with relative tolerance [BR-7.5]"""

    def test_zero_vs_nonzero_fails(self):
        # |0.0 - 0.0001| / max(0.0, 0.0001) = 1.0 > 0.01
        result = check_fuzzy("delta", 0.0, 0.0001, 0.01, ToleranceType.RELATIVE)
        assert isinstance(result, FuzzyFailure)
        assert result.actual_delta == pytest.approx(1.0)

    def test_nonzero_vs_zero_fails(self):
        result = check_fuzzy("delta", 0.0001, 0.0, 0.01, ToleranceType.RELATIVE)
        assert isinstance(result, FuzzyFailure)
        assert result.actual_delta == pytest.approx(1.0)


class TestNonNumericFuzzyData:
    """Scenario 38: Non-numeric FUZZY column data produces ConfigError [BR-4.21, FSD-5.7.5]"""

    def test_non_numeric_lhs_raises_config_error(self):
        with pytest.raises(ConfigError, match='FUZZY column "status".*non-numeric.*"active"'):
            check_fuzzy("status", "active", "active", 0.01, ToleranceType.ABSOLUTE)

    def test_non_numeric_rhs_raises_config_error(self):
        with pytest.raises(ConfigError, match='FUZZY column "status".*non-numeric'):
            check_fuzzy("status", 100.0, "active", 0.01, ToleranceType.ABSOLUTE)


class TestNegativeAbsoluteTolerance:
    """Scenario 36: Negative values with absolute tolerance [BR-7.1, BR-7.2]"""

    def test_negative_within_tolerance_passes(self):
        result = check_fuzzy("pnl", -500.00, -500.005, 0.01, ToleranceType.ABSOLUTE)
        assert result is None

    def test_negative_exceeds_tolerance_fails(self):
        result = check_fuzzy("pnl", -500.00, -500.05, 0.01, ToleranceType.ABSOLUTE)
        assert isinstance(result, FuzzyFailure)
        assert result.actual_delta == pytest.approx(0.05)

    def test_mixed_sign_exceeds_tolerance(self):
        """One positive, one negative — large absolute difference."""
        result = check_fuzzy("pnl", 100.0, -100.0, 0.01, ToleranceType.ABSOLUTE)
        assert isinstance(result, FuzzyFailure)
        assert result.actual_delta == pytest.approx(200.0)

    def test_both_negative_exact_match(self):
        result = check_fuzzy("pnl", -1000.0, -1000.0, 0.01, ToleranceType.ABSOLUTE)
        assert result is None


class TestNegativeRelativeTolerance:
    """Scenario 37: Negative values with relative tolerance [BR-7.1, BR-7.3]"""

    def test_negative_within_relative_passes(self):
        # |-1000.00 - (-1000.50)| / max(|-1000.00|, |-1000.50|) = 0.5/1000.5 ≈ 0.0005 <= 0.001
        result = check_fuzzy("pnl", -1000.00, -1000.50, 0.001, ToleranceType.RELATIVE)
        assert result is None

    def test_negative_exceeds_relative_fails(self):
        # |-100.0 - (-200.0)| / max(100.0, 200.0) = 100/200 = 0.5 > 0.01
        result = check_fuzzy("pnl", -100.0, -200.0, 0.01, ToleranceType.RELATIVE)
        assert isinstance(result, FuzzyFailure)
        assert result.actual_delta == pytest.approx(0.5)

    def test_mixed_sign_relative_fails(self):
        # |100.0 - (-100.0)| / max(100.0, 100.0) = 200/100 = 2.0 > 0.01
        result = check_fuzzy("pnl", 100.0, -100.0, 0.01, ToleranceType.RELATIVE)
        assert isinstance(result, FuzzyFailure)
        assert result.actual_delta == pytest.approx(2.0)


class TestAbsoluteEdgeCases:
    """Additional absolute tolerance edge cases."""

    def test_exact_boundary_passes(self):
        """Delta exactly equal to tolerance should pass."""
        # Use values that produce exact delta in float arithmetic
        result = check_fuzzy("val", 0.0, 0.01, 0.01, ToleranceType.ABSOLUTE)
        assert result is None

    def test_just_over_boundary_fails(self):
        result = check_fuzzy("val", 100.00, 100.02, 0.01, ToleranceType.ABSOLUTE)
        assert isinstance(result, FuzzyFailure)


class TestRelativeEdgeCases:
    """Additional relative tolerance edge cases."""

    def test_large_values_within_relative(self):
        """Large values with small relative difference."""
        # |1e9 - 1e9+1| / 1e9 = 1e-9, well within 0.001
        result = check_fuzzy("val", 1e9, 1e9 + 1, 0.001, ToleranceType.RELATIVE)
        assert result is None

    def test_string_numeric_values_work(self):
        """String representations of numbers should be converted."""
        result = check_fuzzy("val", "100.00", "100.005", 0.01, ToleranceType.ABSOLUTE)
        assert result is None
