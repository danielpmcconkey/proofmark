"""Diff engine — hash grouping, multiset comparison. [FSD-5.6]"""
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any

from proofmark.config import FuzzyColumn
from proofmark.hasher import HashedRow
from proofmark.tolerance import FuzzyFailure, check_fuzzy


@dataclass(frozen=True)
class UnmatchedRow:
    side: str
    content: str
    row_data: dict[str, Any]


@dataclass(frozen=True)
class HashGroupResult:
    hash_value: str
    lhs_count: int
    rhs_count: int
    status: str
    matched_count: int
    surplus_rows: tuple[UnmatchedRow, ...]
    fuzzy_failures: tuple[FuzzyFailure, ...]


@dataclass
class DiffResult:
    """Mutable by design — built incrementally."""
    hash_groups: list[HashGroupResult]
    all_unmatched_lhs: list[UnmatchedRow]
    all_unmatched_rhs: list[UnmatchedRow]
    all_fuzzy_failures: list[FuzzyFailure]
    total_matched: int
    total_lhs: int
    total_rhs: int


def _null_safe_sort_val(v: Any) -> tuple:
    """Null-safe sort key. [FSD-5.6.7]"""
    if v is None:
        return (0, 0.0)
    try:
        return (1, float(v))
    except (ValueError, TypeError):
        return (1, str(v))


def diff(
    lhs_rows: list[HashedRow],
    rhs_rows: list[HashedRow],
    fuzzy_columns: tuple[FuzzyColumn, ...],
) -> DiffResult:
    """Sort, group, and diff hashed rows. [FSD-5.6.1 through FSD-5.6.9]"""
    # Group by hash [FSD-5.6.1]
    lhs_groups: dict[str, list[HashedRow]] = defaultdict(list)
    rhs_groups: dict[str, list[HashedRow]] = defaultdict(list)

    for row in lhs_rows:
        lhs_groups[row.hash_key].append(row)
    for row in rhs_rows:
        rhs_groups[row.hash_key].append(row)

    # All unique hash keys [FSD-5.6.2]
    all_keys = set(lhs_groups.keys()) | set(rhs_groups.keys())

    result_groups: list[HashGroupResult] = []
    all_unmatched_lhs: list[UnmatchedRow] = []
    all_unmatched_rhs: list[UnmatchedRow] = []
    all_fuzzy_failures: list[FuzzyFailure] = []
    total_matched = 0

    for key in sorted(all_keys):
        lhs_list = lhs_groups.get(key, [])
        rhs_list = rhs_groups.get(key, [])
        lhs_count = len(lhs_list)
        rhs_count = len(rhs_list)

        # [FSD-5.6.3]
        hash_matched_count = min(lhs_count, rhs_count)

        # [FSD-5.6.4]
        status = "MATCH" if lhs_count == rhs_count else "COUNT_MISMATCH"

        # Surplus rows [FSD-5.6.5]
        surplus_rows: list[UnmatchedRow] = []
        if lhs_count > rhs_count:
            for row in lhs_list[rhs_count:]:
                ur = UnmatchedRow(side="lhs", content=row.unhashed_content, row_data=row.row_data)
                surplus_rows.append(ur)
                all_unmatched_lhs.append(ur)
        elif rhs_count > lhs_count:
            for row in rhs_list[lhs_count:]:
                ur = UnmatchedRow(side="rhs", content=row.unhashed_content, row_data=row.row_data)
                surplus_rows.append(ur)
                all_unmatched_rhs.append(ur)

        # FUZZY validation [FSD-5.6.6]
        group_fuzzy_failures: list[FuzzyFailure] = []
        matched_count = hash_matched_count

        if hash_matched_count > 0 and fuzzy_columns:
            # Sort for deterministic pairing [FSD-5.6.7]
            def sort_key(row: HashedRow) -> tuple:
                fuzzy_part = tuple(
                    _null_safe_sort_val(row.fuzzy_values.get(col.name))
                    for col in fuzzy_columns
                )
                return (fuzzy_part, row.unhashed_content)

            lhs_matched = sorted(lhs_list[:hash_matched_count], key=sort_key)
            rhs_matched = sorted(rhs_list[:hash_matched_count], key=sort_key)

            for i in range(hash_matched_count):
                pair_failures: list[FuzzyFailure] = []
                for fc in fuzzy_columns:
                    lhs_val = lhs_matched[i].fuzzy_values.get(fc.name)
                    rhs_val = rhs_matched[i].fuzzy_values.get(fc.name)
                    failure = check_fuzzy(
                        fc.name, lhs_val, rhs_val,
                        fc.tolerance, fc.tolerance_type,
                    )
                    if failure:
                        pair_failures.append(failure)

                if pair_failures:
                    # [FSD-5.6.6a] Reclassify as unmatched
                    group_fuzzy_failures.extend(pair_failures)
                    matched_count -= 1
                    lhs_ur = UnmatchedRow(
                        side="lhs",
                        content=lhs_matched[i].unhashed_content,
                        row_data=lhs_matched[i].row_data,
                    )
                    rhs_ur = UnmatchedRow(
                        side="rhs",
                        content=rhs_matched[i].unhashed_content,
                        row_data=rhs_matched[i].row_data,
                    )
                    surplus_rows.append(lhs_ur)
                    surplus_rows.append(rhs_ur)
                    all_unmatched_lhs.append(lhs_ur)
                    all_unmatched_rhs.append(rhs_ur)

            all_fuzzy_failures.extend(group_fuzzy_failures)

        # [FSD-5.6.8] Only include groups with issues
        if status == "COUNT_MISMATCH" or group_fuzzy_failures:
            result_groups.append(HashGroupResult(
                hash_value=key,
                lhs_count=lhs_count,
                rhs_count=rhs_count,
                status=status,
                matched_count=matched_count,
                surplus_rows=tuple(surplus_rows),
                fuzzy_failures=tuple(group_fuzzy_failures),
            ))

        # [FSD-5.6.9]
        total_matched += matched_count * 2

    total_lhs = sum(len(lhs_groups[k]) for k in lhs_groups)
    total_rhs = sum(len(rhs_groups[k]) for k in rhs_groups)

    return DiffResult(
        hash_groups=result_groups,
        all_unmatched_lhs=all_unmatched_lhs,
        all_unmatched_rhs=all_unmatched_rhs,
        all_fuzzy_failures=all_fuzzy_failures,
        total_matched=total_matched,
        total_lhs=total_lhs,
        total_rhs=total_rhs,
    )
