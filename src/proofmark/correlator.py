"""Mismatch correlator — unmatched row pairing by column similarity. [FSD-5.8]"""
import heapq
from dataclasses import dataclass

from proofmark.diff import UnmatchedRow


@dataclass(frozen=True)
class CorrelatedPair:
    lhs_row: str
    rhs_row: str
    confidence: str
    differing_columns: list[str]


@dataclass(frozen=True)
class CorrelationResult:
    correlated_pairs: list[CorrelatedPair]
    uncorrelated_lhs: list[str]
    uncorrelated_rhs: list[str]


def correlate(
    unmatched_lhs: list[UnmatchedRow],
    unmatched_rhs: list[UnmatchedRow],
    column_names: list[str],
) -> CorrelationResult:
    """Pair unmatched rows by column similarity. [FSD-5.8.1 through FSD-5.8.7]"""
    # [FSD-5.8.1]
    if not unmatched_lhs or not unmatched_rhs:
        return CorrelationResult(
            correlated_pairs=[],
            uncorrelated_lhs=[r.content for r in unmatched_lhs],
            uncorrelated_rhs=[r.content for r in unmatched_rhs],
        )

    # [FSD-5.8.2] Sort for determinism
    sorted_lhs = sorted(unmatched_lhs, key=lambda r: r.content)
    sorted_rhs = sorted(unmatched_rhs, key=lambda r: r.content)

    # [FSD-5.8.3] Build similarity scores, keeping only candidates above threshold
    num_cols = len(column_names) if column_names else 1
    # Heap entries: (-score, i, j, differing) — negated score for max-heap via min-heap
    heap: list[tuple[float, int, int, list[str]]] = []

    for i, lhs_row in enumerate(sorted_lhs):
        for j, rhs_row in enumerate(sorted_rhs):
            matching = 0
            differing: list[str] = []
            for col in column_names:
                if lhs_row.row_data.get(col) == rhs_row.row_data.get(col):
                    matching += 1
                else:
                    differing.append(col)
            score = matching / num_cols
            if score > 0.5:
                heapq.heappush(heap, (-score, i, j, differing))

    # [FSD-5.8.4] Greedy pairing, highest score first
    used_lhs: set[int] = set()
    used_rhs: set[int] = set()
    pairs: list[CorrelatedPair] = []

    while heap:
        neg_score, i, j, differing = heapq.heappop(heap)
        if i in used_lhs or j in used_rhs:
            continue
        pairs.append(CorrelatedPair(
            lhs_row=sorted_lhs[i].content,
            rhs_row=sorted_rhs[j].content,
            confidence="high",
            differing_columns=differing,
        ))
        used_lhs.add(i)
        used_rhs.add(j)

    # [FSD-5.8.5] Remaining rows are uncorrelated
    uncorrelated_lhs = [
        sorted_lhs[i].content for i in range(len(sorted_lhs)) if i not in used_lhs
    ]
    uncorrelated_rhs = [
        sorted_rhs[j].content for j in range(len(sorted_rhs)) if j not in used_rhs
    ]

    return CorrelationResult(
        correlated_pairs=pairs,
        uncorrelated_lhs=uncorrelated_lhs,
        uncorrelated_rhs=uncorrelated_rhs,
    )
