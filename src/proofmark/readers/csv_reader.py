"""CSV reader. [FSD-5.3.3]"""
import csv as csv_module
import io
from pathlib import Path
from typing import Any

from proofmark import EncodingError, ReaderError
from proofmark.config import CsvSettings
from proofmark.readers.base import BaseReader, ReaderResult, SchemaInfo


class CsvReader(BaseReader):
    def __init__(self, csv_settings: CsvSettings):
        self.csv_settings = csv_settings

    def read(self, path: Path, encoding: str) -> ReaderResult:
        """Read CSV file with header/trailer separation.

        [FSD-5.3.11 through FSD-5.3.19]
        """
        if not path.exists():
            raise FileNotFoundError(f"File does not exist: {path}")

        # Step 1: Line break detection from raw bytes [FSD-5.3.11]
        raw_bytes = path.read_bytes()
        line_break_style = "CRLF" if b"\r\n" in raw_bytes else "LF"

        # Step 2: Decode [FSD-5.3.12]
        try:
            text = raw_bytes.decode(encoding)
        except (UnicodeDecodeError, LookupError) as e:
            raise EncodingError(
                f"Failed to decode {path.name} with encoding '{encoding}': {e}"
            ) from e

        # Step 3: Normalize line breaks internally [FSD-5.3.13]
        text = text.replace("\r\n", "\n")

        # Step 4: Split into lines [FSD-5.3.14]
        lines = text.split("\n")
        # Drop trailing empty line
        if lines and lines[-1] == "":
            lines = lines[:-1]

        # Step 5: Separate segments [FSD-5.3.15]
        header_count = self.csv_settings.header_rows
        trailer_count = self.csv_settings.trailer_rows

        if len(lines) < header_count + trailer_count:
            raise ReaderError(
                f"File has {len(lines)} lines but config requires "
                f"{header_count} header + {trailer_count} trailer rows"
            )

        header_lines_raw = tuple(lines[:header_count]) if header_count > 0 else ()
        if trailer_count > 0:
            trailer_lines_raw = tuple(lines[-trailer_count:])
            data_lines = lines[header_count:-trailer_count]
        else:
            trailer_lines_raw = ()
            data_lines = lines[header_count:]

        # Step 7: Extract column names [FSD-5.3.17]
        if header_count >= 1:
            reader = csv_module.reader(io.StringIO(header_lines_raw[0]))
            column_names = tuple(next(reader))
        else:
            # Positional naming
            if data_lines:
                reader = csv_module.reader(io.StringIO(data_lines[0]))
                first_row = next(reader)
                column_names = tuple(str(i) for i in range(len(first_row)))
            else:
                column_names = ()

        # Step 6: Parse data rows [FSD-5.3.16]
        rows: list[dict[str, Any]] = []
        data_text = "\n".join(data_lines)
        if data_text.strip():
            reader = csv_module.reader(io.StringIO(data_text))
            for row_values in reader:
                row_dict = {}
                for i, col_name in enumerate(column_names):
                    row_dict[col_name] = row_values[i] if i < len(row_values) else ""
                rows.append(row_dict)

        # Step 8: Build schema [FSD-5.3.18]
        schema = SchemaInfo(column_names=column_names, column_types={})

        # Step 9: Return [FSD-5.3.19]
        return ReaderResult(
            schema=schema,
            rows=rows,
            header_lines=header_lines_raw if header_lines_raw else None,
            trailer_lines=trailer_lines_raw if trailer_lines_raw else None,
            line_break_style=line_break_style,
        )
