"""Reader factory. [FSD-5.3.1]"""
from proofmark.config import ComparisonConfig, ReaderType, CsvSettings
from proofmark.readers.base import BaseReader


def create_reader(config: ComparisonConfig) -> BaseReader:
    """Return the appropriate reader based on config."""
    if config.reader == ReaderType.CSV:
        from proofmark.readers.csv_reader import CsvReader
        return CsvReader(config.csv or CsvSettings())
    else:
        from proofmark.readers.parquet import ParquetReader
        return ParquetReader()
