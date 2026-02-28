"""Diff engine tests — BDD scenarios 26-27, 64-66. [FSD Appendix A]"""
import pytest

from proofmark.config import FuzzyColumn, ToleranceType
from proofmark.diff import DiffResult, UnmatchedRow, diff
from proofmark.hasher import HashedRow, hash_rows


def _make_hashed_rows(rows, excluded=None, fuzzy=None, columns=None):
    """Helper to hash rows with given classifications."""
    excluded = excluded or set()
    fuzzy = fuzzy or set()
    columns = columns or tuple(rows[0].keys()) if rows else ()
    return hash_rows(rows, excluded, fuzzy, columns)


class TestRowOrderIndependence:
    """Scenario 26: Same data, different order passes [BR-4.17, BR-4.18]"""

    def test_different_order_produces_no_mismatches(self):
        lhs_data = [
            {"account_id": 1001, "balance": 5000.00},
            {"account_id": 1002, "balance": 3200.50},
            {"account_id": 1003, "balance": 0.00},
        ]
        rhs_data = [
            {"account_id": 1003, "balance": 0.00},
            {"account_id": 1001, "balance": 5000.00},
            {"account_id": 1002, "balance": 3200.50},
        ]
        cols = ("account_id", "balance")
        lhs = _make_hashed_rows(lhs_data, columns=cols)
        rhs = _make_hashed_rows(rhs_data, columns=cols)

        result = diff(lhs, rhs, ())
        assert result.total_matched == 6  # 3 pairs * 2
        assert len(result.all_unmatched_lhs) == 0
        assert len(result.all_unmatched_rhs) == 0
        assert len(result.hash_groups) == 0  # No groups with issues


class TestDuplicateRowsMultiset:
    """Scenario 27: Duplicate rows — multiset comparison [BR-4.22]"""

    def test_duplicate_multiset_mismatch(self):
        lhs_data = [
            {"account_id": 1001, "balance": 5000.00},
            {"account_id": 1001, "balance": 5000.00},
        ]
        rhs_data = [
            {"account_id": 1001, "balance": 5000.00},
        ]
        cols = ("account_id", "balance")
        lhs = _make_hashed_rows(lhs_data, columns=cols)
        rhs = _make_hashed_rows(rhs_data, columns=cols)

        result = diff(lhs, rhs, ())
        # matched = min(2,1) * 2 = 2, total = 2+1 = 3
        assert result.total_matched == 2
        assert result.total_lhs == 2
        assert result.total_rhs == 1
        assert len(result.all_unmatched_lhs) == 1
        assert len(result.all_unmatched_rhs) == 0

    def test_duplicate_match_percentage(self):
        """Per formula: matched=2, total=3, match%=66.7%"""
        lhs_data = [
            {"account_id": 1001, "balance": 5000.00},
            {"account_id": 1001, "balance": 5000.00},
        ]
        rhs_data = [
            {"account_id": 1001, "balance": 5000.00},
        ]
        cols = ("account_id", "balance")
        lhs = _make_hashed_rows(lhs_data, columns=cols)
        rhs = _make_hashed_rows(rhs_data, columns=cols)
        result = diff(lhs, rhs, ())
        total_rows = result.total_lhs + result.total_rhs
        match_pct = (result.total_matched / total_rows) * 100.0
        assert match_pct == pytest.approx(66.67, abs=0.01)


class TestRowCountMismatch:
    """Scenario 64: Different row counts between LHS and RHS [BR-4.18, BR-4.20, BR-11.17]"""

    def test_row_count_mismatch(self):
        # 100 LHS, 99 RHS (first 99 match)
        lhs_data = [{"account_id": i, "balance": float(i * 100)} for i in range(100)]
        rhs_data = [{"account_id": i, "balance": float(i * 100)} for i in range(99)]
        cols = ("account_id", "balance")
        lhs = _make_hashed_rows(lhs_data, columns=cols)
        rhs = _make_hashed_rows(rhs_data, columns=cols)

        result = diff(lhs, rhs, ())
        assert result.total_lhs == 100
        assert result.total_rhs == 99
        # 99 matched pairs * 2 = 198
        assert result.total_matched == 198
        assert len(result.all_unmatched_lhs) == 1
        assert len(result.all_unmatched_rhs) == 0

    def test_row_count_mismatch_percentage(self):
        """Per formula: matched=198, total=199, match%=99.5%"""
        lhs_data = [{"account_id": i, "balance": float(i * 100)} for i in range(100)]
        rhs_data = [{"account_id": i, "balance": float(i * 100)} for i in range(99)]
        cols = ("account_id", "balance")
        lhs = _make_hashed_rows(lhs_data, columns=cols)
        rhs = _make_hashed_rows(rhs_data, columns=cols)
        result = diff(lhs, rhs, ())
        total_rows = result.total_lhs + result.total_rhs
        match_pct = (result.total_matched / total_rows) * 100.0
        assert match_pct == pytest.approx(99.497, abs=0.01)


class TestZeroRows:
    """Scenario 65: Both sides have zero data rows — PASS [BR-4.18, BR-11.13, BR-11.18]"""

    def test_zero_rows_both_sides(self):
        result = diff([], [], ())
        assert result.total_matched == 0
        assert result.total_lhs == 0
        assert result.total_rhs == 0
        # Match percentage should be 100.0 by definition
        total_rows = result.total_lhs + result.total_rhs
        if total_rows == 0:
            match_pct = 100.0
        else:
            match_pct = (result.total_matched / total_rows) * 100.0
        assert match_pct == 100.0


class TestSameRowCountAllMatch:
    """Scenario 66: Same row count, all rows match [BR-4.18]"""

    def test_perfect_match(self):
        data = [{"id": i, "val": float(i)} for i in range(50)]
        cols = ("id", "val")
        lhs = _make_hashed_rows(data, columns=cols)
        rhs = _make_hashed_rows(data, columns=cols)

        result = diff(lhs, rhs, ())
        assert result.total_matched == 100  # 50 * 2
        assert result.total_lhs == 50
        assert result.total_rhs == 50
        assert len(result.hash_groups) == 0  # No issues


class TestFuzzyInDiff:
    """FUZZY validation within the diff engine [FSD-5.6.6]"""

    def test_fuzzy_failure_reclassifies_as_unmatched(self):
        """Hash matches but FUZZY tolerance exceeded → pair becomes unmatched."""
        # Both rows have account_id=1001 (STRICT), different balance (FUZZY)
        lhs_data = [{"account_id": 1001, "balance": 100.00}]
        rhs_data = [{"account_id": 1001, "balance": 100.50}]
        cols = ("account_id", "balance")
        lhs = hash_rows(lhs_data, set(), {"balance"}, cols)
        rhs = hash_rows(rhs_data, set(), {"balance"}, cols)

        fuzzy_cols = (FuzzyColumn(
            name="balance", tolerance=0.01,
            tolerance_type=ToleranceType.ABSOLUTE, reason="test",
        ),)
        result = diff(lhs, rhs, fuzzy_cols)

        # Hash groups match, but FUZZY fails → matched=0
        assert result.total_matched == 0
        assert len(result.all_fuzzy_failures) == 1
        assert len(result.all_unmatched_lhs) == 1
        assert len(result.all_unmatched_rhs) == 1

    def test_fuzzy_pass_counts_as_matched(self):
        """Hash matches and FUZZY within tolerance → pair is matched."""
        lhs_data = [{"account_id": 1001, "balance": 100.000}]
        rhs_data = [{"account_id": 1001, "balance": 100.005}]
        cols = ("account_id", "balance")
        lhs = hash_rows(lhs_data, set(), {"balance"}, cols)
        rhs = hash_rows(rhs_data, set(), {"balance"}, cols)

        fuzzy_cols = (FuzzyColumn(
            name="balance", tolerance=0.01,
            tolerance_type=ToleranceType.ABSOLUTE, reason="test",
        ),)
        result = diff(lhs, rhs, fuzzy_cols)

        assert result.total_matched == 2  # 1 pair * 2
        assert len(result.all_fuzzy_failures) == 0


class TestOnlyIssueGroupsIncluded:
    """FSD-5.6.8: Only groups with issues appear in hash_groups."""

    def test_clean_groups_not_in_output(self):
        data = [
            {"id": 1, "val": "a"},
            {"id": 2, "val": "b"},
        ]
        cols = ("id", "val")
        lhs = _make_hashed_rows(data, columns=cols)
        rhs = _make_hashed_rows(data, columns=cols)
        result = diff(lhs, rhs, ())
        assert len(result.hash_groups) == 0

    def test_mismatch_group_in_output(self):
        lhs_data = [{"id": 1, "val": "a"}]
        rhs_data = [{"id": 1, "val": "a"}, {"id": 1, "val": "a"}]
        cols = ("id", "val")
        lhs = _make_hashed_rows(lhs_data, columns=cols)
        rhs = _make_hashed_rows(rhs_data, columns=cols)
        result = diff(lhs, rhs, ())
        assert len(result.hash_groups) == 1
        assert result.hash_groups[0].status == "COUNT_MISMATCH"
