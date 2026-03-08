# diff.py

Diff engine. Groups rows by hash, performs multiset comparison, and runs FUZZY validation on hash-matched pairs.

**Source**: `src/proofmark/diff.py`

## `diff(lhs_rows, rhs_rows, fuzzy_columns) -> DiffResult`

### Algorithm

1. **Group by hash**: Build `{hash_key: [HashedRow]}` maps for both sides.
2. **For each unique hash key**:
   - Count LHS and RHS rows in the group.
   - Matched count = `min(lhs_count, rhs_count)`.
   - Status = `"MATCH"` if counts equal, else `"COUNT_MISMATCH"`.
   - Surplus rows (the difference) become `UnmatchedRow` objects.
3. **FUZZY validation** (if fuzzy columns configured):
   - Sort matched pairs deterministically for pairing.
   - For each pair, check all FUZZY columns via `tolerance.check_fuzzy()`.
   - If any FUZZY check fails, the pair is reclassified as unmatched (both sides). Matched count decrements.
4. **Filter output**: Only hash groups with issues (count mismatch or fuzzy failures) appear in `hash_groups`.
5. **Accumulate totals**: `total_matched` counts both sides (multiply pairs by 2).

### `DiffResult`

```python
@dataclass
class DiffResult:
    hash_groups: list[HashGroupResult]        # Only groups with issues
    all_unmatched_lhs: list[UnmatchedRow]
    all_unmatched_rhs: list[UnmatchedRow]
    all_fuzzy_failures: list[FuzzyFailure]
    total_matched: int                         # Double-counted (pairs * 2)
    total_lhs: int
    total_rhs: int
```

### `UnmatchedRow`

```python
@dataclass(frozen=True)
class UnmatchedRow:
    side: str              # "lhs" or "rhs"
    content: str           # unhashed_content from HashedRow
    row_data: dict[str, Any]  # Column values for correlator
```

### Key Behaviors

- Clean groups (perfect match, no fuzzy failures) are omitted from `hash_groups` -- only issues are reported.
- FUZZY failures reclassify both sides of a pair as unmatched, feeding them into the correlator.
- `total_matched` is double-counted by design (one count per side per matched pair). The pipeline divides by 2 for `match_count`.
- Deterministic FUZZY pairing: rows within a hash group are sorted by fuzzy values then by unhashed content before pairing.
