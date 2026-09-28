"""
Decision Engine for the Freight Document Pipeline.
Maps validation outcomes to operational statuses (APPROVED vs FLAGGED_FOR_HUMAN_REVIEW).
"""

from typing import Any, Optional
from app.models import (
    DecisionResult,
    DecisionStatus,
    FreightDocument,
    ValidationResult,
)


def make_decision(
    document: FreightDocument,
    validation: ValidationResult,
    metadata: Optional[dict[str, Any]] = None,
    flag_on_warnings: bool = True,
) -> DecisionResult:
    """
    Evaluates the validation findings and computes the final workflow status and audit summary.

    Policy:
      - If no errors and no warnings exist: APPROVED.
      - If errors exist (e.g. RATE_MISMATCH, INCOMPLETE_DATA): FLAGGED_FOR_HUMAN_REVIEW.
      - If warnings exist (e.g. OVERWEIGHT_LOAD) and flag_on_warnings is True:
        FLAGGED_FOR_HUMAN_REVIEW (since 'no errors/warnings exist' is required for straight approval).

    Args:
        document: The extracted FreightDocument.
        validation: The ValidationResult from validate_document().
        metadata: Execution telemetry (model, processing time, etc.).
        flag_on_warnings: Whether advisory warnings require human sign-off (default: True).

    Returns:
        DecisionResult containing status, human-readable summary, cleaned data, and audit trail.
    """
    issues_summary: list[str] = []

    # Compile error messages
    for err in validation.errors:
        issues_summary.append(f"[{err.code}] {err.message}")

    # Compile warning messages
    for warn in validation.warnings:
        issues_summary.append(f"[{warn.code}] {warn.message}")

    if validation.errors:
        status = DecisionStatus.FLAGGED_FOR_HUMAN_REVIEW
        summary = (
            f"Document flagged for human review due to {len(validation.errors)} blocking error(s)"
            f"{f' and {len(validation.warnings)} warning(s)' if validation.warnings else ''}: "
            + " | ".join(issues_summary)
        )
    elif validation.warnings and flag_on_warnings:
        status = DecisionStatus.FLAGGED_FOR_HUMAN_REVIEW
        summary = (
            f"Document flagged for human review due to {len(validation.warnings)} operational warning(s): "
            + " | ".join(issues_summary)
        )
    else:
        status = DecisionStatus.APPROVED
        summary = "Document successfully parsed and verified. All validation checks passed (0 errors, 0 warnings)."

    return DecisionResult(
        status=status,
        summary=summary,
        data=document,
        validation=validation,
        metadata=metadata or {},
    )
