"""Hash engine tests — BDD scenarios 14-16, 19-21, 26-28. [FSD Appendix A]"""
import hashlib

import pytest

from proofmark.hasher import HashedRow, hash_rows, NULL_SENTINEL


class TestAllColumnsDefaultStrict:
    """Scenario 14: All columns default to STRICT when no column config [BR-5.5, BR-5.9]"""

    def test_all_strict_hashing(self):
        rows = [
            {"account_id": 1001, "balance": 5000.00, "status": "active"},
        ]
        result = hash_rows(
            rows,
            excluded_names=set(),
            fuzzy_names=set(),
            column_order=("account_id", "balance", "status"),
        )
        assert len(result) == 1
        row = result[0]
        # All columns should be in the hash
        expected_input = "1001\x005000.0\x00active"
        expected_hash = hashlib.md5(expected_input.encode("utf-8")).hexdigest()
        assert row.hash_key == expected_hash
        assert row.fuzzy_values == {}

    def test_unhashed_content_includes_all(self):
        rows = [{"a": 1, "b": 2, "c": 3}]
        result = hash_rows(rows, set(), set(), ("a", "b", "c"))
        assert result[0].unhashed_content == "1|2|3"


class TestExcludedColumnDropped:
    """Scenario 15: EXCLUDED column dropped before hashing [BR-5.2, BR-5.3, BR-4.14]"""

    def test_excluded_column_not_in_hash(self):
        rows = [
            {"run_id": "uuid-aaa", "account_id": 1001, "balance": 5000.00},
            {"run_id": "uuid-bbb", "account_id": 1001, "balance": 5000.00},
        ]
        result1 = hash_rows(
            [rows[0]], {"run_id"}, set(), ("run_id", "account_id", "balance")
        )
        result2 = hash_rows(
            [rows[1]], {"run_id"}, set(), ("run_id", "account_id", "balance")
        )
        # Different run_ids should produce same hash
        assert result1[0].hash_key == result2[0].hash_key

    def test_excluded_column_not_in_row_data(self):
        rows = [{"run_id": "uuid", "account_id": 1001, "balance": 5000.00}]
        result = hash_rows(rows, {"run_id"}, set(), ("run_id", "account_id", "balance"))
        assert "run_id" not in result[0].row_data
        assert "account_id" in result[0].row_data

    def test_excluded_not_in_unhashed_content(self):
        rows = [{"run_id": "uuid", "account_id": 1001, "balance": 5000.00}]
        result = hash_rows(rows, {"run_id"}, set(), ("run_id", "account_id", "balance"))
        assert "uuid" not in result[0].unhashed_content
        assert "1001" in result[0].unhashed_content


class TestFuzzyAbsoluteWithin:
    """Scenario 16: FUZZY column handling in hasher [BR-7.1, BR-7.2]"""

    def test_fuzzy_column_excluded_from_hash(self):
        """FUZZY columns are not part of the hash key — only STRICT columns are."""
        rows = [{"account_id": 1001, "interest": 100.005}]
        result_strict = hash_rows(rows, set(), set(), ("account_id", "interest"))
        result_fuzzy = hash_rows(rows, set(), {"interest"}, ("account_id", "interest"))
        # With interest as FUZZY, hash should only be on account_id
        expected_fuzzy_input = "1001"
        expected_hash = hashlib.md5(expected_fuzzy_input.encode("utf-8")).hexdigest()
        assert result_fuzzy[0].hash_key == expected_hash
        assert result_fuzzy[0].hash_key != result_strict[0].hash_key

    def test_fuzzy_values_extracted(self):
        rows = [{"account_id": 1001, "interest": 100.005}]
        result = hash_rows(rows, set(), {"interest"}, ("account_id", "interest"))
        assert result[0].fuzzy_values == {"interest": 100.005}


class TestMixedClassification:
    """Scenario 19: Mixed classification on same target [BR-5.1, BR-5.5]"""

    def test_mixed_excluded_strict_fuzzy(self):
        rows = [{
            "run_id": "uuid-aaa",
            "account_id": 1001,
            "balance": 5000.00,
            "interest_accrued": 100.005,
        }]
        result = hash_rows(
            rows,
            excluded_names={"run_id"},
            fuzzy_names={"interest_accrued"},
            column_order=("run_id", "account_id", "balance", "interest_accrued"),
        )
        row = result[0]
        # Hash should be on STRICT columns only: account_id, balance
        expected_input = "1001\x005000.0"
        expected_hash = hashlib.md5(expected_input.encode("utf-8")).hexdigest()
        assert row.hash_key == expected_hash
        assert row.fuzzy_values == {"interest_accrued": 100.005}
        assert "run_id" not in row.row_data


class TestNullHandling:
    """Scenario 20-21: Null handling in hasher [BR-8.1, BR-8.4]"""

    def test_null_produces_sentinel_in_hash(self):
        rows = [{"id": 1, "notes": None}]
        result = hash_rows(rows, set(), set(), ("id", "notes"))
        assert NULL_SENTINEL in result[0].unhashed_content

    def test_null_vs_null_same_hash(self):
        rows1 = [{"id": 1, "notes": None}]
        rows2 = [{"id": 1, "notes": None}]
        r1 = hash_rows(rows1, set(), set(), ("id", "notes"))
        r2 = hash_rows(rows2, set(), set(), ("id", "notes"))
        assert r1[0].hash_key == r2[0].hash_key

    def test_null_vs_empty_string_different_hash(self):
        rows_null = [{"id": 1, "notes": None}]
        rows_empty = [{"id": 1, "notes": ""}]
        r1 = hash_rows(rows_null, set(), set(), ("id", "notes"))
        r2 = hash_rows(rows_empty, set(), set(), ("id", "notes"))
        assert r1[0].hash_key != r2[0].hash_key


class TestRowOrderIndependenceHash:
    """Scenario 26: Hashing is per-row, order doesn't affect individual hashes [BR-4.17]"""

    def test_same_row_produces_same_hash_regardless_of_position(self):
        row_a = {"account_id": 1001, "balance": 5000.00}
        row_b = {"account_id": 1002, "balance": 3200.50}
        result1 = hash_rows([row_a, row_b], set(), set(), ("account_id", "balance"))
        result2 = hash_rows([row_b, row_a], set(), set(), ("account_id", "balance"))
        hashes1 = sorted(r.hash_key for r in result1)
        hashes2 = sorted(r.hash_key for r in result2)
        assert hashes1 == hashes2


class TestDuplicateRowsHash:
    """Scenario 27: Duplicate rows produce same hash [BR-4.22]"""

    def test_duplicate_rows_same_hash(self):
        row = {"account_id": 1001, "balance": 5000.00}
        result = hash_rows([row, row], set(), set(), ("account_id", "balance"))
        assert result[0].hash_key == result[1].hash_key


class TestExcludedOrderingHash:
    """Scenario 28: EXCLUDED columns don't affect hash ordering [BR-4.14, BR-4.16]"""

    def test_excluded_doesnt_affect_hash(self):
        rows1 = [{"uuid": "aaa", "account_id": 1001, "balance": 5000.00}]
        rows2 = [{"uuid": "bbb", "account_id": 1001, "balance": 5000.00}]
        r1 = hash_rows(rows1, {"uuid"}, set(), ("uuid", "account_id", "balance"))
        r2 = hash_rows(rows2, {"uuid"}, set(), ("uuid", "account_id", "balance"))
        assert r1[0].hash_key == r2[0].hash_key


class TestColumnOrderDeterminism:
    """FSD-5.5.11: Column ordering determinism."""

    def test_schema_order_determines_hash(self):
        row = {"b": 2, "a": 1}
        r1 = hash_rows([row], set(), set(), ("a", "b"))
        r2 = hash_rows([row], set(), set(), ("b", "a"))
        # Different column order should produce different hashes
        assert r1[0].hash_key != r2[0].hash_key

    def test_null_byte_separator_prevents_collision(self):
        """Values like ["ab", "c"] and ["a", "bc"] should hash differently."""
        row1 = {"col1": "ab", "col2": "c"}
        row2 = {"col1": "a", "col2": "bc"}
        r1 = hash_rows([row1], set(), set(), ("col1", "col2"))
        r2 = hash_rows([row2], set(), set(), ("col1", "col2"))
        assert r1[0].hash_key != r2[0].hash_key
