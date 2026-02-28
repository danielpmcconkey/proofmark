"""FUZZY tolerance comparator. [FSD-5.7]"""
from dataclasses import dataclass
from typing import Any

from proofmark import ConfigError
from proofmark.config import ToleranceType


@dataclass(frozen=True)
class FuzzyFailure:
    column: str
    lhs_value: Any
    rhs_value: Any
    tolerance: float
    tolerance_type: str
    actual_delta: float


def check_fuzzy(
    column_name: str,
    lhs_value: Any,
    rhs_value: Any,
    tolerance: float,
    tolerance_type: ToleranceType,
) -> FuzzyFailure | None:
    """Check if two values are within tolerance.

    Returns None if within tolerance (pass).
    Returns FuzzyFailure if tolerance exceeded (fail).
    [FSD-5.7.1 through FSD-5.7.8]
    """
    # Null handling [FSD-5.7.8]
    lhs_is_null = lhs_value is None
    rhs_is_null = rhs_value is None

    if lhs_is_null and rhs_is_null:
        return None  # Both null = match

    if lhs_is_null or rhs_is_null:
        # Null vs non-null = FUZZY failure
        non_null_val = rhs_value if lhs_is_null else lhs_value
        try:
            actual_delta = abs(float(non_null_val))
        except (ValueError, TypeError):
            actual_delta = 0.0
        return FuzzyFailure(
            column=column_name,
            lhs_value=lhs_value,
            rhs_value=rhs_value,
            tolerance=tolerance,
            tolerance_type=tolerance_type.value,
            actual_delta=actual_delta,
        )

    # Convert to float [FSD-5.7.5]
    try:
        lhs_f = float(lhs_value)
    except (ValueError, TypeError) as e:
        raise ConfigError(
            f"FUZZY column \"{column_name}\" contains non-numeric value "
            f"\"{lhs_value}\""
        ) from e
    try:
        rhs_f = float(rhs_value)
    except (ValueError, TypeError) as e:
        raise ConfigError(
            f"FUZZY column \"{column_name}\" contains non-numeric value "
            f"\"{rhs_value}\""
        ) from e

    delta = abs(lhs_f - rhs_f)

    # Both zero [FSD-5.7.3]
    if lhs_f == 0.0 and rhs_f == 0.0:
        return None  # delta is 0, always passes

    if tolerance_type == ToleranceType.ABSOLUTE:
        # [FSD-5.7.1]
        actual_delta = delta
        passes = delta <= tolerance
    else:
        # Relative [FSD-5.7.2]
        denominator = max(abs(lhs_f), abs(rhs_f))
        if denominator == 0.0:
            actual_delta = 0.0
            passes = True
        else:
            actual_delta = delta / denominator
            passes = actual_delta <= tolerance

    if passes:
        return None

    return FuzzyFailure(
        column=column_name,
        lhs_value=lhs_value,
        rhs_value=rhs_value,
        tolerance=tolerance,
        tolerance_type=tolerance_type.value,
        actual_delta=actual_delta,
    )
