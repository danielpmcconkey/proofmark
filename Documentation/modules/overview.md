# Modules Overview

The comparison pipeline is a linear chain of modules. Each one has a focused responsibility and well-defined inputs/outputs.

## Data Flow

```
config.py -> readers/ -> schema.py -> hasher.py -> diff.py -> correlator.py -> report.py
                                         ^                                        |
                                         |                                        v
                                    tolerance.py                          JSON report dict
```

`pipeline.py` orchestrates this chain. It is the only module that imports from all others.

## Module Index

| Module | Responsibility | Key Types |
|---|---|---|
| [pipeline.md](pipeline.md) | Orchestrator -- wires all modules together | `run()`, `_determine_result()` |
| [readers.md](readers.md) | Data loading (CSV, Parquet) | `ReaderResult`, `SchemaInfo`, `BaseReader` |
| [hasher.md](hasher.md) | Column exclusion, value concatenation, MD5 hashing | `HashedRow`, `hash_rows()` |
| [diff.md](diff.md) | Hash grouping, multiset comparison, FUZZY validation | `DiffResult`, `diff()` |
| [tolerance.md](tolerance.md) | Numeric tolerance comparison (absolute/relative) | `FuzzyFailure`, `check_fuzzy()` |
| [correlator.md](correlator.md) | Unmatched row pairing by column similarity | `CorrelationResult`, `correlate()` |
| [schema.md](schema.md) | Schema validation (column count, names, types) | `validate_schema()` |
| [report.md](report.md) | JSON report assembly | `build_report()`, `serialize_report()` |

## Exception Hierarchy

Defined in `__init__.py`:

```
ProofmarkError
  ConfigError          # Invalid config. Exit code 2.
  ReaderError          # Reader failures (missing files, empty dirs). Exit code 2.
    EncodingError      # File decode failure. Exit code 2.
```
