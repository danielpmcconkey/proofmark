"""Base reader types and ABC. [FSD-4.5, FSD-4.6]"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class SchemaInfo:
    column_names: tuple[str, ...]
    column_types: dict[str, str]


@dataclass(frozen=True)
class ReaderResult:
    schema: SchemaInfo
    rows: list[dict[str, Any]]
    header_lines: tuple[str, ...] | None
    trailer_lines: tuple[str, ...] | None
    line_break_style: str | None


class BaseReader(ABC):
    @abstractmethod
    def read(self, path: Path, encoding: str) -> ReaderResult:
        """Read input data from path. Return normalized ReaderResult."""
