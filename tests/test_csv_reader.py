"""CSV reader tests — BDD scenarios 5-9. [FSD Appendix A]"""
from pathlib import Path

import pytest

from proofmark import EncodingError, ReaderError
from proofmark.config import CsvSettings
from proofmark.readers.csv_reader import CsvReader


@pytest.fixture
def simple_reader():
    return CsvReader(CsvSettings(header_rows=1, trailer_rows=0))


@pytest.fixture
def trailer_reader():
    return CsvReader(CsvSettings(header_rows=1, trailer_rows=1))


class TestSimpleCsvMatch:
    """Scenario 5: Simple CSV with header, data matches [BR-3.10, BR-3.11]"""

    def test_simple_csv_reads_correctly(self, simple_reader, csv_fixtures):
        result = simple_reader.read(csv_fixtures / "simple_match" / "lhs.csv", "utf-8")
        assert len(result.rows) == 2
        assert result.schema.column_names == ("account_id", "balance", "status")
        assert result.rows[0]["account_id"] == "1001"
        assert result.rows[0]["balance"] == "5000.00"

    def test_header_extracted(self, simple_reader, csv_fixtures):
        result = simple_reader.read(csv_fixtures / "simple_match" / "lhs.csv", "utf-8")
        assert result.header_lines is not None
        assert "account_id" in result.header_lines[0]

    def test_line_break_style_detected(self, simple_reader, csv_fixtures):
        result = simple_reader.read(csv_fixtures / "simple_match" / "lhs.csv", "utf-8")
        assert result.line_break_style in ("LF", "CRLF")

    def test_column_types_empty_for_csv(self, simple_reader, csv_fixtures):
        result = simple_reader.read(csv_fixtures / "simple_match" / "lhs.csv", "utf-8")
        assert result.schema.column_types == {}


class TestCsvWithTrailer:
    """Scenario 6: CSV with trailing control record, data matches [BR-3.11, BR-3.13]"""

    def test_trailer_separated_from_data(self, trailer_reader, csv_fixtures):
        result = trailer_reader.read(
            csv_fixtures / "with_trailer_match" / "lhs.csv", "utf-8"
        )
        assert len(result.rows) == 2
        assert result.trailer_lines is not None
        assert len(result.trailer_lines) == 1
        assert "TRAILER" in result.trailer_lines[0]

    def test_header_preserved(self, trailer_reader, csv_fixtures):
        result = trailer_reader.read(
            csv_fixtures / "with_trailer_match" / "lhs.csv", "utf-8"
        )
        assert result.header_lines is not None
        assert len(result.header_lines) == 1


class TestCsvHeaderMismatch:
    """Scenario 7: CSV header row difference detected [BR-3.13, BR-3.14]"""

    def test_header_difference_readable(self, simple_reader, csv_fixtures):
        lhs = simple_reader.read(csv_fixtures / "header_mismatch" / "lhs.csv", "utf-8")
        rhs = simple_reader.read(csv_fixtures / "header_mismatch" / "rhs.csv", "utf-8")
        # Headers differ: status vs state
        assert lhs.header_lines != rhs.header_lines


class TestCsvTrailerMismatch:
    """Scenario 8: CSV trailer row difference detected [BR-3.13, BR-3.14]"""

    def test_trailer_difference_readable(self, trailer_reader, csv_fixtures):
        lhs = trailer_reader.read(csv_fixtures / "trailer_mismatch" / "lhs.csv", "utf-8")
        rhs = trailer_reader.read(csv_fixtures / "trailer_mismatch" / "rhs.csv", "utf-8")
        assert lhs.trailer_lines != rhs.trailer_lines
        assert "2026-02-28" in lhs.trailer_lines[0]
        assert "2026-02-27" in rhs.trailer_lines[0]


class TestCsvDataMismatch:
    """Scenario 9: CSV data mismatch in body [BR-3.10, BR-11.9]"""

    def test_data_mismatch_reads(self, simple_reader, csv_fixtures):
        lhs = simple_reader.read(csv_fixtures / "data_mismatch" / "lhs.csv", "utf-8")
        rhs = simple_reader.read(csv_fixtures / "data_mismatch" / "rhs.csv", "utf-8")
        assert len(lhs.rows) == 2
        assert len(rhs.rows) == 2
        assert lhs.rows[1]["balance"] == "3200.50"
        assert rhs.rows[1]["balance"] == "3200.99"


class TestCsvEdgeCases:
    """Additional reader edge case tests."""

    def test_nonexistent_file_raises(self, simple_reader, tmp_path):
        with pytest.raises(FileNotFoundError):
            simple_reader.read(tmp_path / "nonexistent.csv", "utf-8")

    def test_crlf_detected(self, simple_reader, csv_fixtures):
        result = simple_reader.read(csv_fixtures / "crlf_vs_lf" / "lhs.csv", "utf-8")
        assert result.line_break_style == "CRLF"

    def test_lf_detected(self, simple_reader, csv_fixtures):
        result = simple_reader.read(csv_fixtures / "crlf_vs_lf" / "rhs.csv", "utf-8")
        assert result.line_break_style == "LF"

    def test_too_few_lines_for_header_trailer_raises(self, tmp_path):
        """File with insufficient lines for header+trailer config."""
        path = tmp_path / "short.csv"
        path.write_text("only_one_line\n")
        reader = CsvReader(CsvSettings(header_rows=1, trailer_rows=1))
        with pytest.raises(ReaderError, match="config requires"):
            reader.read(path, "utf-8")


class TestCsvNoHeader:
    """H-07: header_rows=0 generates positional column names. [FSD-5.3.17]"""

    def test_no_header_positional_columns(self, tmp_path):
        path = tmp_path / "no_header.csv"
        path.write_text("1001,5000.00,active\n1002,3200.50,closed\n")
        reader = CsvReader(CsvSettings(header_rows=0, trailer_rows=0))
        result = reader.read(path, "utf-8")
        assert result.schema.column_names == ("0", "1", "2")
        assert len(result.rows) == 2
        assert result.rows[0]["0"] == "1001"
        assert result.rows[0]["1"] == "5000.00"
        assert result.header_lines is None

    def test_no_header_no_data(self, tmp_path):
        """Empty file with no header config produces empty result."""
        path = tmp_path / "empty.csv"
        path.write_text("")
        reader = CsvReader(CsvSettings(header_rows=0, trailer_rows=0))
        result = reader.read(path, "utf-8")
        assert result.schema.column_names == ()
        assert len(result.rows) == 0
