"""
Unit tests for data contracts and Pydantic schemas in app/models.py.
"""

from app.models import (
    DecisionResult,
    DecisionStatus,
    FreightDocument,
    Location,
    ValidationIssue,
    ValidationResult,
    ValidationSeverity,
)


def test_location_preserves_leading_zeros_in_zip():
    """ZIP codes must be strings to prevent dropping leading zeros (e.g., Boston 02108)."""
    loc = Location(city="Boston", state="MA", zip="02108")
    assert loc.zip == "02108"
    assert loc.is_complete() is True


def test_location_incomplete_check():
    """is_complete() should return False if city, state, or zip is missing."""
    loc_missing_zip = Location(city="Dallas", state="TX", zip=None)
    assert loc_missing_zip.is_complete() is False

    loc_empty_state = Location(city="Dallas", state="", zip="75201")
    assert loc_empty_state.is_complete() is False


def test_freight_document_instantiation():
    """FreightDocument schema must correctly parse all required fields."""
    doc = FreightDocument(
        carrier_name="Apex Logistics Solutions LLC",
        load_number="LD-994821",
        pickup_location=Location(city="Dallas", state="TX", zip="75201"),
        delivery_location=Location(city="Atlanta", state="GA", zip="30303"),
        total_linehaul_rate=2200.0,
        fuel_surcharge=350.0,
        total_pay=2800.0,
        weight_lbs=46800,
    )
    assert doc.carrier_name == "Apex Logistics Solutions LLC"
    assert doc.total_linehaul_rate == 2200.0
    assert doc.weight_lbs == 46800


def test_validation_result_helpers():
    """ValidationResult should properly compute helper lists and flags."""
    err = ValidationIssue(
        code="RATE_MISMATCH",
        message="Math mismatch",
        severity=ValidationSeverity.ERROR,
    )
    warn = ValidationIssue(
        code="OVERWEIGHT_LOAD",
        message="Overweight",
        severity=ValidationSeverity.WARNING,
    )

    result = ValidationResult(is_valid=False, errors=[err], warnings=[warn])

    assert result.is_valid is False
    assert result.error_codes == ["RATE_MISMATCH"]
    assert result.warning_codes == ["OVERWEIGHT_LOAD"]
    assert result.all_codes == ["RATE_MISMATCH", "OVERWEIGHT_LOAD"]
