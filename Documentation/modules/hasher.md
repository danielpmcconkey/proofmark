# hasher.py

Hash engine. Handles column exclusion, value concatenation, and MD5 hashing.

**Source**: `src/proofmark/hasher.py`

## `hash_rows(rows, excluded_names, fuzzy_names, column_order) -> list[HashedRow]`

Produces a `HashedRow` for each input row dict.

### Column Sets

Given the schema's `column_order`, columns are partitioned:

- **STRICT** = columns not in `excluded_names` and not in `fuzzy_names`
- **FUZZY** = columns in `fuzzy_names` (ordered by schema position)
- **Non-excluded** = all columns except those in `excluded_names`

### Per-Row Processing

1. **Hash input**: Concatenate STRICT column values with `\x00` separator. Null values become the sentinel `__PROOFMARK_NULL__`. Compute MD5 hex digest.
2. **Unhashed content**: Concatenate all non-excluded column values with `|` separator (includes FUZZY columns). Used for display in mismatch reports.
3. **Fuzzy values**: Extract FUZZY column values into a dict for tolerance checking downstream.
4. **Row data**: All non-excluded column values as a dict. Used by the correlator for column-by-column similarity.

### `HashedRow`

```python
@dataclass(frozen=True)
class HashedRow:
    hash_key: str              # MD5 hex digest of STRICT columns
    unhashed_content: str      # Pipe-delimited non-excluded values
    fuzzy_values: dict[str, Any]  # {column_name: value} for FUZZY columns
    row_data: dict[str, Any]   # {column_name: value} for all non-excluded columns
```

### Key Behaviors

- Column order is determined by the schema, not the dict key order
- The `\x00` separator prevents value boundary collisions (`["ab", "c"]` vs `["a", "bc"]` hash differently)
- EXCLUDED columns are absent from `hash_key`, `unhashed_content`, and `row_data`
- FUZZY columns appear in `unhashed_content` and `row_data` but not in `hash_key`

### Null Sentinel

```python
NULL_SENTINEL = "__PROOFMARK_NULL__"
```

Used in hash input and unhashed content. Ensures null vs empty string produces different hashes.
