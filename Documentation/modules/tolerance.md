# tolerance.py

FUZZY tolerance comparator. Checks whether two numeric values are within a configured tolerance.

**Source**: `src/proofmark/tolerance.py`

## `check_fuzzy(column_name, lhs_value, rhs_value, tolerance, tolerance_type) -> FuzzyFailure | None`

Returns `None` if the values are within tolerance (pass). Returns a `FuzzyFailure` if tolerance is exceeded.

### Comparison Logic

**Null handling** (checked first):
- Both null: pass (return `None`)
- One null, one non-null: fail (delta = absolute value of the non-null)

**Numeric conversion**: Both values are cast to `float`. Non-numeric values raise `ConfigError` (this is a misconfiguration, not a data issue).

**Both zero**: Always passes regardless of tolerance type.

**Absolute tolerance**: `|lhs - rhs| <= tolerance`

**Relative tolerance**: `|lhs - rhs| / max(|lhs|, |rhs|) <= tolerance`

### `FuzzyFailure`

```python
@dataclass(frozen=True)
class FuzzyFailure:
    column: str
    lhs_value: Any
    rhs_value: Any
    tolerance: float
    tolerance_type: str      # "absolute" or "relative"
    actual_delta: float      # The computed delta that exceeded tolerance
```

### Edge Cases

| Scenario | Absolute | Relative |
|---|---|---|
| Both zero | Pass | Pass |
| One zero, one 0.0001 | delta=0.0001 | delta=1.0 (usually fails) |
| Negative values | Uses `abs(lhs - rhs)` | Uses `abs` on both values |
| String numeric values | Converted to float | Converted to float |
| Exact boundary (delta == tolerance) | Pass | Pass |
