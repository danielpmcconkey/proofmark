"""Parquet reader. [FSD-5.3.2]"""
from pathlib import Path
from typing import Any

import pyarrow as pa
import pyarrow.parquet as pq

from proofmark import ReaderError
from proofmark.readers.base import BaseReader, ReaderResult, SchemaInfo


class ParquetReader(BaseReader):
    def read(self, path: Path, encoding: str) -> ReaderResult:
        """Read *.parquet from directory, assemble into single logical table.

        [FSD-5.3.3 through FSD-5.3.10]
        """
        # Validate path is a directory [FSD-5.3.3]
        if not path.exists():
            raise FileNotFoundError(f"Path does not exist: {path}")
        if not path.is_dir():
            raise ReaderError(f"Parquet reader expects a directory, got: {path}")

        # Glob for parquet files [FSD-5.3.4]
        parquet_files = sorted(path.glob("*.parquet"))
        if not parquet_files:
            raise ReaderError(f"No parquet files found in: {path}")

        # Read and concatenate [FSD-5.3.6]
        tables = []
        for pf in parquet_files:
            try:
                tables.append(pq.read_table(pf))
            except Exception as e:
                raise ReaderError(f"Failed to read parquet file {pf.name}: {e}") from e

        try:
            combined = pa.concat_tables(tables)
        except pa.ArrowInvalid as e:
            raise ReaderError(
                f"Incompatible schemas across part files in {path}: {e}"
            ) from e

        # Extract schema [FSD-5.3.7]
        schema = combined.schema
        column_names = tuple(schema.names)
        column_types = {
            field.name: str(field.type) for field in schema
        }

        # Convert to list of dicts [FSD-5.3.8]
        pydict = combined.to_pydict()
        num_rows = combined.num_rows
        rows: list[dict[str, Any]] = []
        for i in range(num_rows):
            rows.append({col: pydict[col][i] for col in column_names})

        # Return with null CSV fields [FSD-5.3.9]
        return ReaderResult(
            schema=SchemaInfo(column_names=column_names, column_types=column_types),
            rows=rows,
            header_lines=None,
            trailer_lines=None,
            line_break_style=None,
        )
