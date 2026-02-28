"""Hash engine — column exclusion, value concat, MD5 hashing. [FSD-5.5]"""
import hashlib
from dataclasses import dataclass
from typing import Any

NULL_SENTINEL = "__PROOFMARK_NULL__"


@dataclass(frozen=True)
class HashedRow:
    hash_key: str
    unhashed_content: str
    fuzzy_values: dict[str, Any]
    row_data: dict[str, Any]


def _value_to_string(value: Any) -> str:
    """Convert a value to its string representation for hashing.

    [FSD-5.5.3, FSD-5.5.4, FSD-5.5.5]
    """
    if value is None:
        return NULL_SENTINEL
    return str(value)


def hash_rows(
    rows: list[dict[str, Any]],
    excluded_names: set[str],
    fuzzy_names: set[str],
    column_order: tuple[str, ...],
) -> list[HashedRow]:
    """Apply exclusions, compute hash keys, build HashedRow objects.

    [FSD-5.5.1 through FSD-5.5.11]
    """
    # Identify column sets in schema order [FSD-5.5.2]
    strict_columns = [
        c for c in column_order
        if c not in excluded_names and c not in fuzzy_names
    ]
    fuzzy_columns_ordered = [
        c for c in column_order
        if c in fuzzy_names
    ]
    non_excluded_columns = [
        c for c in column_order
        if c not in excluded_names
    ]

    result: list[HashedRow] = []
    for row in rows:
        # Hash input: STRICT columns only [FSD-5.5.6]
        strict_values = [_value_to_string(row.get(c)) for c in strict_columns]
        hash_input = "\x00".join(strict_values)

        # Compute MD5 [FSD-5.5.7]
        hash_key = hashlib.md5(hash_input.encode("utf-8")).hexdigest()

        # Unhashed content: all non-excluded columns [FSD-5.5.8]
        all_values = [_value_to_string(row.get(c)) for c in non_excluded_columns]
        unhashed_content = "|".join(all_values)

        # Extract FUZZY values [FSD-5.5.9]
        fuzzy_values = {c: row.get(c) for c in fuzzy_columns_ordered}

        # Row data: all non-excluded columns [FSD-5.5.10]
        row_data = {c: row.get(c) for c in non_excluded_columns}

        result.append(HashedRow(
            hash_key=hash_key,
            unhashed_content=unhashed_content,
            fuzzy_values=fuzzy_values,
            row_data=row_data,
        ))

    return result
