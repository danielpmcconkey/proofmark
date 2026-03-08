# correlator.py

Mismatch correlator. Pairs unmatched rows from LHS and RHS by column similarity, helping developers identify which rows almost matched and where they differ.

**Source**: `src/proofmark/correlator.py`

## `correlate(unmatched_lhs, unmatched_rhs, column_names) -> CorrelationResult`

### Algorithm

1. **Empty check**: If either side is empty, all rows from the other side go to uncorrelated lists.
2. **Sort**: Both sides sorted by content for determinism.
3. **Similarity matrix**: For each LHS/RHS pair, compute `matching_columns / total_columns`. Track which columns differ.
4. **Greedy pairing**: Sort all pairs by descending score (ties broken by position). Walk through, skip used rows, pair if score > 0.5. All pairs get `confidence: "high"`.
5. **Uncorrelated**: Remaining unpaired rows go to `uncorrelated_lhs` / `uncorrelated_rhs`.

### `CorrelationResult`

```python
@dataclass(frozen=True)
class CorrelationResult:
    correlated_pairs: list[CorrelatedPair]
    uncorrelated_lhs: list[str]      # unhashed_content strings
    uncorrelated_rhs: list[str]
```

### `CorrelatedPair`

```python
@dataclass(frozen=True)
class CorrelatedPair:
    lhs_row: str                     # unhashed_content
    rhs_row: str
    confidence: str                  # Always "high" (>50% match)
    differing_columns: list[str]     # Column names that differ
```

### Key Behaviors

- Threshold is strictly > 0.5 (not >=). Exactly 50% match does not correlate.
- Greedy algorithm: highest-scoring pair wins. A row can only be paired once.
- Column comparison uses `row_data` dict values (non-excluded columns only).
