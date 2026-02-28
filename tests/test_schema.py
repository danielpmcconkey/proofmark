"""Schema validation tests — BDD scenarios 10-13. [FSD Appendix A]"""
import pytest

from proofmark.config import ReaderType
from proofmark.readers.base import SchemaInfo
from proofmark.schema import validate_schema


class TestMatchingSchemas:
    """Scenario 10: Matching schemas pass validation [BR-4.9]"""

    def test_identical_schemas_pass(self):
        schema = SchemaInfo(
            column_names=("account_id", "balance", "status"),
            column_types={"account_id": "int64", "balance": "float64", "status": "string"},
        )
        mismatches = validate_schema(schema, schema, ReaderType.PARQUET)
        assert mismatches == []

    def test_csv_schemas_skip_type_check(self):
        lhs = SchemaInfo(column_names=("a", "b"), column_types={})
        rhs = SchemaInfo(column_names=("a", "b"), column_types={})
        mismatches = validate_schema(lhs, rhs, ReaderType.CSV)
        assert mismatches == []


class TestColumnCountMismatch:
    """Scenario 11: Column count mismatch [BR-4.9, BR-4.10]"""

    def test_different_column_counts(self):
        lhs = SchemaInfo(
            column_names=("account_id", "balance", "status"),
            column_types={"account_id": "int64", "balance": "float64", "status": "string"},
        )
        rhs = SchemaInfo(
            column_names=("account_id", "balance"),
            column_types={"account_id": "int64", "balance": "float64"},
        )
        mismatches = validate_schema(lhs, rhs, ReaderType.PARQUET)
        assert len(mismatches) == 1
        assert "LHS has 3 columns" in mismatches[0]
        assert "RHS has 2 columns" in mismatches[0]


class TestColumnNameMismatch:
    """Scenario 12: Column name mismatch [BR-4.9, BR-4.11]"""

    def test_different_column_names(self):
        lhs = SchemaInfo(
            column_names=("account_id", "balance", "status"),
            column_types={"account_id": "int64", "balance": "float64", "status": "string"},
        )
        rhs = SchemaInfo(
            column_names=("account_id", "balance", "state"),
            column_types={"account_id": "int64", "balance": "float64", "state": "string"},
        )
        mismatches = validate_schema(lhs, rhs, ReaderType.PARQUET)
        assert len(mismatches) == 1
        assert '"status"' in mismatches[0]
        assert '"state"' in mismatches[0]


class TestColumnTypeMismatch:
    """Scenario 13: Column type mismatch (parquet only) [BR-4.12, BR-4.13]"""

    def test_different_column_types_parquet(self):
        lhs = SchemaInfo(
            column_names=("account_id", "balance"),
            column_types={"account_id": "int64", "balance": "float64"},
        )
        rhs = SchemaInfo(
            column_names=("account_id", "balance"),
            column_types={"account_id": "int64", "balance": "int32"},
        )
        mismatches = validate_schema(lhs, rhs, ReaderType.PARQUET)
        assert len(mismatches) == 1
        assert "balance" in mismatches[0]
        assert "float64" in mismatches[0]
        assert "int32" in mismatches[0]

    def test_csv_skips_type_check(self):
        """CSV schema validation is limited to column count and names [BR-4.13]"""
        lhs = SchemaInfo(
            column_names=("a", "b"),
            column_types={},
        )
        rhs = SchemaInfo(
            column_names=("a", "b"),
            column_types={},
        )
        mismatches = validate_schema(lhs, rhs, ReaderType.CSV)
        assert mismatches == []
