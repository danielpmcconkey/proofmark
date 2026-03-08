# Readers

The `readers/` package provides data loading for CSV and Parquet formats behind a common interface.

**Source**: `src/proofmark/readers/`

## Architecture

```
BaseReader (ABC)
  CsvReader       -- reads a single CSV file
  ParquetReader   -- reads a directory of .parquet part files
```

`create_reader(config)` is the factory function. It inspects `config.reader` (`ReaderType.CSV` or `ReaderType.PARQUET`) and returns the appropriate reader.

## Common Types

### `SchemaInfo`

```python
@dataclass(frozen=True)
class SchemaInfo:
    column_names: tuple[str, ...]    # Ordered column names
    column_types: dict[str, str]     # Column name -> type string (Parquet only, empty dict for CSV)
```

### `ReaderResult`

```python
@dataclass(frozen=True)
class ReaderResult:
    schema: SchemaInfo
    rows: list[dict[str, Any]]           # Each row is {column_name: value}
    header_lines: tuple[str, ...] | None # Raw header lines (CSV only)
    trailer_lines: tuple[str, ...] | None
    line_break_style: str | None         # "LF" or "CRLF" (CSV only)
```

For Parquet, `header_lines`, `trailer_lines`, and `line_break_style` are always `None`.

## CSV Reader

**Source**: `src/proofmark/readers/csv_reader.py`

Reads a single CSV file with configurable header/trailer line counts.

### Processing Steps

1. **Line break detection**: Read raw bytes, check for `\r\n`. Sets `line_break_style` to `"CRLF"` or `"LF"`.
2. **Decode**: Decode bytes with configured encoding. Raises `EncodingError` on failure.
3. **Normalize**: Replace `\r\n` with `\n` internally.
4. **Split**: Split on `\n`, drop trailing empty line.
5. **Segment**: Separate header lines, trailer lines, and data lines based on `CsvSettings.header_rows` and `CsvSettings.trailer_rows`. Raises `ReaderError` if file has fewer lines than required.
6. **Column names**: If `header_rows >= 1`, parse first header line as CSV to extract column names. If `header_rows == 0`, generate positional names (`"0"`, `"1"`, ...) from the first data row.
7. **Parse data**: Parse data lines as CSV, map to column name dicts.
8. **Return**: `ReaderResult` with schema, rows, headers, trailers, line break style.

### Key Behaviors

- All CSV values are strings (no type inference)
- `header_lines` is `None` when `header_rows == 0` (not empty tuple)
- Empty fields are empty strings, not `None`

## Parquet Reader

**Source**: `src/proofmark/readers/parquet.py`

Reads all `*.parquet` files from a directory and concatenates them into a single logical table.

### Processing Steps

1. **Validate**: Path must exist and be a directory.
2. **Glob**: Find `*.parquet` files, sorted by name.
3. **Read and concatenate**: Read each file with PyArrow, concatenate tables. Raises `ReaderError` on incompatible schemas across part files.
4. **Extract schema**: Column names and types from the Arrow schema.
5. **Convert**: Convert to list of dicts via `to_pydict()`.
6. **Return**: `ReaderResult` with schema, rows, and `None` for CSV-specific fields.

### Key Behaviors

- Parquet preserves native types (int, float, string, None)
- Column types are included in `SchemaInfo.column_types`
- Empty directory (no `.parquet` files) raises `ReaderError`
- File path (instead of directory) raises `ReaderError`
