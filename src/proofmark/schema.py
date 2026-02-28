"""Schema validation. [FSD-5.4]"""
from proofmark.config import ReaderType
from proofmark.readers.base import SchemaInfo


def validate_schema(
    lhs_schema: SchemaInfo,
    rhs_schema: SchemaInfo,
    reader_type: ReaderType,
) -> list[str]:
    """Compare schemas. Returns list of mismatch descriptions.

    Empty list = schemas match. [FSD-5.4.1]
    """
    mismatches: list[str] = []

    # Column count [FSD-5.4.2]
    lhs_count = len(lhs_schema.column_names)
    rhs_count = len(rhs_schema.column_names)
    if lhs_count != rhs_count:
        mismatches.append(
            f"Column count mismatch: LHS has {lhs_count} columns, "
            f"RHS has {rhs_count} columns"
        )
        return mismatches  # Can't compare names/types if counts differ

    # Column names [FSD-5.4.3]
    for i, (lhs_name, rhs_name) in enumerate(
        zip(lhs_schema.column_names, rhs_schema.column_names)
    ):
        if lhs_name != rhs_name:
            mismatches.append(
                f"Column name mismatch at position {i}: "
                f"\"{lhs_name}\" vs \"{rhs_name}\""
            )

    # Column types (parquet only) [FSD-5.4.4]
    if reader_type == ReaderType.PARQUET and not mismatches:
        for col_name in lhs_schema.column_names:
            lhs_type = lhs_schema.column_types.get(col_name, "")
            rhs_type = rhs_schema.column_types.get(col_name, "")
            if lhs_type != rhs_type:
                mismatches.append(
                    f"Column \"{col_name}\" type mismatch: "
                    f"{lhs_type} vs {rhs_type}"
                )

    return mismatches
