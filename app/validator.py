"""
Deterministic business logic validation engine for freight operational documents.
Adheres to the core architectural tenet: "LLM extracts. Python decides."
"""

from decimal import Decimal, InvalidOperation
from typing import List
from app.models import (
    FreightDocument,
    ValidationIssue,
    ValidationResult,
    ValidationSeverity,
)

STANDARD_HIGHWAY_WEIGHT_LIMIT_LBS = 45_000


def validate_document(doc: FreightDocument) -> ValidationResult:
    """
    Inspects an extracted FreightDocument against deterministic logistics business rules.

    Validation Rules:
      1. Missing Fields Check (INCOMPLETE_DATA - ERROR):
         Ensures required identifiers, locations (city/state/zip), financial rates, and weight are present.
      2. Financial Math Check (RATE_MISMATCH - ERROR):
         Verifies Linehaul Rate + Fuel Surcharge == Total Pay using Decimal arithmetic.
      3. Weight Limit Check (OVERWEIGHT_LOAD - WARNING):
         Flags loads exceeding the standard 45,000 lbs legal highway limit.

    Args:
        doc: The parsed FreightDocument instance.

    Returns:
        ValidationResult containing lists of errors and warnings.
    """
    errors: List[ValidationIssue] = []
    warnings: List[ValidationIssue] = []

    # --------------------------------------------------------------------------
    # Rule 1: Missing Fields / Completeness Check
    # --------------------------------------------------------------------------
    missing_fields: List[str] = []

    if not doc.carrier_name or not doc.carrier_name.strip():
        missing_fields.append("carrier_name")

    if not doc.load_number or not doc.load_number.strip():
        missing_fields.append("load_number")

    # Pickup Location Check
    if not doc.pickup_location:
        missing_fields.append("pickup_location")
    else:
        if not doc.pickup_location.city or not doc.pickup_location.city.strip():
            missing_fields.append("pickup_location.city")
        if not doc.pickup_location.state or not doc.pickup_location.state.strip():
            missing_fields.append("pickup_location.state")
        if not doc.pickup_location.zip or not doc.pickup_location.zip.strip():
            missing_fields.append("pickup_location.zip")

    # Delivery Location Check
    if not doc.delivery_location:
        missing_fields.append("delivery_location")
    else:
        if not doc.delivery_location.city or not doc.delivery_location.city.strip():
            missing_fields.append("delivery_location.city")
        if not doc.delivery_location.state or not doc.delivery_location.state.strip():
            missing_fields.append("delivery_location.state")
        if not doc.delivery_location.zip or not doc.delivery_location.zip.strip():
            missing_fields.append("delivery_location.zip")

    if doc.total_linehaul_rate is None:
        missing_fields.append("total_linehaul_rate")

    if doc.fuel_surcharge is None:
        missing_fields.append("fuel_surcharge")

    if doc.total_pay is None:
        missing_fields.append("total_pay")

    if doc.weight_lbs is None:
        missing_fields.append("weight_lbs")

    if missing_fields:
        errors.append(
            ValidationIssue(
                code="INCOMPLETE_DATA",
                message=f"Missing or incomplete required fields: {', '.join(missing_fields)}",
                severity=ValidationSeverity.ERROR,
                field="; ".join(missing_fields),
            )
        )

    # --------------------------------------------------------------------------
    # Rule 2: Financial Math Check (Decimal Precision)
    # --------------------------------------------------------------------------
    if (
        doc.total_linehaul_rate is not None
        and doc.fuel_surcharge is not None
        and doc.total_pay is not None
    ):
        try:
            linehaul = Decimal(str(doc.total_linehaul_rate))
            fuel = Decimal(str(doc.fuel_surcharge))
            total_pay = Decimal(str(doc.total_pay))

            expected_total = linehaul + fuel
            discrepancy = abs(expected_total - total_pay)

            # Check if sum deviates by more than $0.00 (or float epsilon)
            if discrepancy != Decimal("0"):
                errors.append(
                    ValidationIssue(
                        code="RATE_MISMATCH",
                        message=(
                            f"Financial mismatch: Linehaul (${linehaul:,.2f}) + "
                            f"Fuel Surcharge (${fuel:,.2f}) = ${expected_total:,.2f}, "
                            f"which does not match Total Agreed Pay (${total_pay:,.2f}). "
                            f"Discrepancy: ${discrepancy:,.2f}."
                        ),
                        severity=ValidationSeverity.ERROR,
                        field="total_pay",
                    )
                )
        except (InvalidOperation, ValueError) as err:
            errors.append(
                ValidationIssue(
                    code="RATE_MISMATCH",
                    message=f"Unable to perform rate calculation due to invalid financial value: {err}",
                    severity=ValidationSeverity.ERROR,
                    field="financials",
                )
            )

    # --------------------------------------------------------------------------
    # Rule 3: Gross Weight Limit Check
    # --------------------------------------------------------------------------
    if doc.weight_lbs is not None and doc.weight_lbs > STANDARD_HIGHWAY_WEIGHT_LIMIT_LBS:
        warnings.append(
            ValidationIssue(
                code="OVERWEIGHT_LOAD",
                message=(
                    f"Load weight {doc.weight_lbs:,} lbs exceeds standard legal highway "
                    f"threshold of {STANDARD_HIGHWAY_WEIGHT_LIMIT_LBS:,} lbs. "
                    f"Overweight permits or specialized multi-axle equipment required."
                ),
                severity=ValidationSeverity.WARNING,
                field="weight_lbs",
            )
        )

    is_valid = len(errors) == 0

    return ValidationResult(
        is_valid=is_valid,
        errors=errors,
        warnings=warnings,
    )
