"""Proofmark — ETL output equivalence comparison tool."""

__version__ = "0.1.0"


class ProofmarkError(Exception):
    """Base exception for all Proofmark errors."""


class ConfigError(ProofmarkError):
    """Invalid configuration file. Exit code 2."""


class ReaderError(ProofmarkError):
    """Reader-level failures (missing files, empty directories). Exit code 2."""


class EncodingError(ReaderError):
    """File cannot be decoded with configured encoding. Exit code 2."""
