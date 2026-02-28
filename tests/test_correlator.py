"""Mismatch correlator tests — BDD scenarios 46-47. [FSD Appendix A]"""
import pytest

from proofmark.correlator import CorrelatedPair, CorrelationResult, correlate
from proofmark.diff import UnmatchedRow


class TestHighConfidenceCorrelation:
    """Scenario 46: Mismatch correlation pairs rows differing in few columns [BR-11.10]"""

    def test_high_confidence_pairing(self):
        lhs = [UnmatchedRow(
            side="lhs",
            content="1002|3200.50|active",
            row_data={"account_id": 1002, "balance": 3200.50, "status": "active"},
        )]
        rhs = [UnmatchedRow(
            side="rhs",
            content="1002|3200.99|active",
            row_data={"account_id": 1002, "balance": 3200.99, "status": "active"},
        )]
        columns = ["account_id", "balance", "status"]

        result = correlate(lhs, rhs, columns)
        assert len(result.correlated_pairs) == 1
        pair = result.correlated_pairs[0]
        assert pair.confidence == "high"
        assert "balance" in pair.differing_columns
        assert len(pair.differing_columns) == 1

    def test_high_confidence_threshold(self):
        """Pairs sharing > 50% of columns should correlate."""
        lhs = [UnmatchedRow(
            side="lhs",
            content="1001|5000.00|active",
            row_data={"a": 1, "b": 2, "c": 3, "d": "x"},
        )]
        rhs = [UnmatchedRow(
            side="rhs",
            content="1001|5000.00|closed",
            row_data={"a": 1, "b": 2, "c": 3, "d": "y"},
        )]
        result = correlate(lhs, rhs, ["a", "b", "c", "d"])
        assert len(result.correlated_pairs) == 1  # 3/4 = 75% > 50%


class TestLowConfidenceCorrelation:
    """Scenario 47: Low correlation confidence falls back to separate lists [BR-11.11]"""

    def test_low_confidence_no_pairing(self):
        lhs = [UnmatchedRow(
            side="lhs",
            content="9999|0.01|closed",
            row_data={"account_id": 9999, "balance": 0.01, "status": "closed"},
        )]
        rhs = [UnmatchedRow(
            side="rhs",
            content="8888|99999.00|pending",
            row_data={"account_id": 8888, "balance": 99999.00, "status": "pending"},
        )]
        columns = ["account_id", "balance", "status"]

        result = correlate(lhs, rhs, columns)
        assert len(result.correlated_pairs) == 0
        assert len(result.uncorrelated_lhs) == 1
        assert len(result.uncorrelated_rhs) == 1

    def test_exactly_50_percent_does_not_correlate(self):
        """Score must be > 0.5, not >= 0.5."""
        lhs = [UnmatchedRow(
            side="lhs", content="a|b",
            row_data={"x": 1, "y": 2},
        )]
        rhs = [UnmatchedRow(
            side="rhs", content="c|d",
            row_data={"x": 1, "y": 99},
        )]
        result = correlate(lhs, rhs, ["x", "y"])
        # 1/2 = 0.5, not > 0.5 — should NOT correlate
        assert len(result.correlated_pairs) == 0


class TestEmptyInputs:
    """FSD-5.8.1: Empty inputs produce empty results."""

    def test_empty_lhs(self):
        rhs = [UnmatchedRow(side="rhs", content="a", row_data={"x": 1})]
        result = correlate([], rhs, ["x"])
        assert len(result.correlated_pairs) == 0
        assert len(result.uncorrelated_rhs) == 1

    def test_empty_rhs(self):
        lhs = [UnmatchedRow(side="lhs", content="a", row_data={"x": 1})]
        result = correlate(lhs, [], ["x"])
        assert len(result.correlated_pairs) == 0
        assert len(result.uncorrelated_lhs) == 1

    def test_both_empty(self):
        result = correlate([], [], [])
        assert len(result.correlated_pairs) == 0
        assert len(result.uncorrelated_lhs) == 0
        assert len(result.uncorrelated_rhs) == 0


class TestGreedyPairing:
    """FSD-5.8.4: Greedy highest-similarity-first pairing."""

    def test_best_pair_wins(self):
        """When multiple pairings are possible, highest score wins."""
        lhs = [
            UnmatchedRow(side="lhs", content="a", row_data={"x": 1, "y": 2, "z": 3}),
        ]
        rhs = [
            UnmatchedRow(side="rhs", content="b", row_data={"x": 1, "y": 2, "z": 99}),
            UnmatchedRow(side="rhs", content="c", row_data={"x": 1, "y": 99, "z": 99}),
        ]
        result = correlate(lhs, rhs, ["x", "y", "z"])
        assert len(result.correlated_pairs) == 1
        # Should pair with the one that has 2/3 match, not 1/3
        assert result.correlated_pairs[0].rhs_row == "b"
        assert len(result.uncorrelated_rhs) == 1
