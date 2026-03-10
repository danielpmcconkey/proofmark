"""Parquet reader tests — BDD scenarios 1-4. [FSD Appendix A]"""
from pathlib import Path

import pytest

from proofmark import ReaderError
from proofmark.readers.parquet import ParquetReader


@pytest.fixture
def reader():
    return ParquetReader()


class TestIdentical3PartVs1Part:
    """Scenario 1: Identical data across different part file counts passes
    [BR-3.15, BR-3.16]"""

    def test_3parts_vs_1part_same_data(self, reader, parquet_fixtures):
        lhs = reader.read(parquet_fixtures / "identical_3part_vs_1part" / "lhs", "utf-8")
        rhs = reader.read(parquet_fixtures / "identical_3part_vs_1part" / "rhs", "utf-8")

        assert len(lhs.rows) == 3
        assert len(rhs.rows) == 3
        assert lhs.schema.column_names == rhs.schema.column_names
        assert lhs.schema.column_names == ("account_id", "balance", "status")

    def test_3parts_assembled_correctly(self, reader, parquet_fixtures):
        lhs = reader.read(parquet_fixtures / "identical_3part_vs_1part" / "lhs", "utf-8")
        account_ids = sorted(row["account_id"] for row in lhs.rows)
        assert account_ids == [1001, 1002, 1003]

    def test_csv_fields_null_for_parquet(self, reader, parquet_fixtures):
        result = reader.read(parquet_fixtures / "identical_simple" / "lhs", "utf-8")
        assert result.header_lines is None
        assert result.trailer_lines is None
        assert result.line_break_style is None


class TestIdenticalSimple:
    """Scenario 2: Identical data in matching part file counts passes
    [BR-3.7, BR-3.8, BR-3.9]"""

    def test_identical_simple_data(self, reader, parquet_fixtures):
        lhs = reader.read(parquet_fixtures / "identical_simple" / "lhs", "utf-8")
        rhs = reader.read(parquet_fixtures / "identical_simple" / "rhs", "utf-8")

        assert len(lhs.rows) == 2
        assert len(rhs.rows) == 2
        assert lhs.schema.column_names == ("id", "name", "amount")


class TestDataMismatch:
    """Scenario 3: Data difference detected [BR-3.7, BR-11.9]"""

    def test_reads_differing_data(self, reader, parquet_fixtures):
        lhs = reader.read(parquet_fixtures / "data_mismatch" / "lhs", "utf-8")
        rhs = reader.read(parquet_fixtures / "data_mismatch" / "rhs", "utf-8")

        # Both have 2 rows but different data
        assert len(lhs.rows) == 2
        assert len(rhs.rows) == 2

        # Second row differs
        assert lhs.rows[1]["balance"] == 3200.50
        assert rhs.rows[1]["balance"] == 3200.99

    def test_schema_types_extracted(self, reader, parquet_fixtures):
        result = reader.read(parquet_fixtures / "data_mismatch" / "lhs", "utf-8")
        assert "account_id" in result.schema.column_types
        assert "balance" in result.schema.column_types


class TestEmptyDirectory:
    """Scenario 4: Edge cases for directory input [BR-3.15, BR-4.7]"""

    def test_nonexistent_directory_raises(self, reader, tmp_path):
        with pytest.raises(FileNotFoundError):
            reader.read(tmp_path / "nonexistent", "utf-8")

    def test_file_instead_of_directory_raises(self, reader, parquet_fixtures):
        # Point at a parquet file instead of a directory
        file_path = parquet_fixtures / "identical_simple" / "lhs" / "part-00000.parquet"
        with pytest.raises(ReaderError, match="expects a directory"):
            reader.read(file_path, "utf-8")
