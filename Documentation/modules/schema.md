# schema.py

Schema validation. Compares LHS and RHS schemas before any data comparison.

**Source**: `src/proofmark/schema.py`

## `validate_schema(lhs_schema, rhs_schema, reader_type) -> list[str]`

Returns a list of mismatch description strings. Empty list means schemas match.

### Checks (in order)

1. **Column count**: If LHS and RHS have different numbers of columns, returns immediately with a count mismatch message. No further checks are possible.
2. **Column names**: Positional comparison. Each mismatched name produces a message with position index and both names.
3. **Column types** (Parquet only): If names all match, compares type strings from the Arrow schema. CSV has no type information, so this step is skipped.

### Short-Circuit Behavior

If `validate_schema` returns a non-empty list, the pipeline builds a `build_schema_fail_report()` and returns immediately. No hashing, diffing, or correlation happens. The report contains the schema mismatch messages and a FAIL result with 0% match.
