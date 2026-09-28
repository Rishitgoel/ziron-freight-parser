"""
Unit tests for the business logic validation engine in app/validator.py.
Covers:
  - Financial Math Check (RATE_MISMATCH)
  - Gross Weight Limit Check (OVERWEIGHT_LOAD)
  - Missing and Incomplete Data (INCOMPLETE_DATA)
  - Decimal arithmetic precision
"""

from app.models import FreightDocument, Location
from app.validator import validate_document


def test_valid_document():
    """A clean document with correct math and legal weight should pass with 0 errors and 0 warnings."""
    doc = FreightDocument(
        carrier_name="Swift Transport Solutions LLC",
        load_number="LD-104928",
        pickup_location=Location(city="Chicago", state="IL", zip="60601"),
        delivery_location=Location(city="Columbus", state="OH", zip="43215"),
        total_linehaul_rate=2000.0,
        fuel_surcharge=400.0,
        total_pay=2400.0,
        weight_lbs=38500,
    )
    result = validate_document(doc)

    assert result.is_valid is True
    assert len(result.errors) == 0
    assert len(result.warnings) == 0


def test_rate_mismatch_detected():
    """
    Sample document test case:
    Linehaul $2,200.00 + FSC $350.00 = $2,550.00 != Total Pay $2,800.00.
    Must trigger RATE_MISMATCH error.
    """
    doc = FreightDocument(
        carrier_name="Apex Logistics Solutions LLC",
        load_number="LD-994821",
        pickup_location=Location(city="Dallas", state="TX", zip="75201"),
        delivery_location=Location(city="Atlanta", state="GA", zip="30303"),
        total_linehaul_rate=2200.0,
        fuel_surcharge=350.0,
        total_pay=2800.0,
        weight_lbs=40000,
    )
    result = validate_document(doc)

    assert result.is_valid is False
    assert "RATE_MISMATCH" in result.error_codes
    assert any("2,550.00" in e.message and "2,800.00" in e.message for e in result.errors)


def test_overweight_load_warning():
    """
    Sample document test case:
    Cargo weight 46,800 lbs exceeds standard legal limit of 45,000 lbs.
    Must trigger OVERWEIGHT_LOAD warning.
    """
    doc = FreightDocument(
        carrier_name="Apex Logistics Solutions LLC",
        load_number="LD-994821",
        pickup_location=Location(city="Dallas", state="TX", zip="75201"),
        delivery_location=Location(city="Atlanta", state="GA", zip="30303"),
        total_linehaul_rate=2000.0,
        fuel_surcharge=400.0,
        total_pay=2400.0,
        weight_lbs=46800,
    )
    result = validate_document(doc)

    assert "OVERWEIGHT_LOAD" in result.warning_codes
    assert any("46,800" in w.message for w in result.warnings)


def test_weight_limit_boundaries():
    """Exactly 45,000 lbs is legal; 45,001 lbs triggers warning."""
    base_kwargs = dict(
        carrier_name="Carrier Co",
        load_number="LD-100",
        pickup_location=Location(city="Dallas", state="TX", zip="75201"),
        delivery_location=Location(city="Atlanta", state="GA", zip="30303"),
        total_linehaul_rate=1000.0,
        fuel_surcharge=200.0,
        total_pay=1200.0,
    )

    doc_boundary = FreightDocument(**base_kwargs, weight_lbs=45000)
    assert "OVERWEIGHT_LOAD" not in validate_document(doc_boundary).warning_codes

    doc_over = FreightDocument(**base_kwargs, weight_lbs=45001)
    assert "OVERWEIGHT_LOAD" in validate_document(doc_over).warning_codes


def test_missing_load_number():
    """Missing or empty load_number triggers INCOMPLETE_DATA."""
    doc = FreightDocument(
        carrier_name="Apex Logistics Solutions LLC",
        load_number=None,
        pickup_location=Location(city="Dallas", state="TX", zip="75201"),
        delivery_location=Location(city="Atlanta", state="GA", zip="30303"),
        total_linehaul_rate=2000.0,
        fuel_surcharge=400.0,
        total_pay=2400.0,
        weight_lbs=35000,
    )
    result = validate_document(doc)

    assert result.is_valid is False
    assert "INCOMPLETE_DATA" in result.error_codes
    assert any("load_number" in e.message for e in result.errors)


def test_incomplete_location_fields():
    """A pickup or delivery location missing ZIP or state triggers INCOMPLETE_DATA."""
    doc = FreightDocument(
        carrier_name="Apex Logistics Solutions LLC",
        load_number="LD-994821",
        pickup_location=Location(city="Dallas", state="TX", zip=None),  # Missing ZIP
        delivery_location=Location(city="Atlanta", state="", zip="30303"),  # Empty state
        total_linehaul_rate=2000.0,
        fuel_surcharge=400.0,
        total_pay=2400.0,
        weight_lbs=35000,
    )
    result = validate_document(doc)

    assert result.is_valid is False
    assert "INCOMPLETE_DATA" in result.error_codes
    assert any("pickup_location.zip" in e.message for e in result.errors)
    assert any("delivery_location.state" in e.message for e in result.errors)


def test_financial_decimal_precision():
    """Ensure financial calculations with cents do not suffer from float representation error."""
    # In standard float: 100.10 + 200.20 == 300.30 is False (300.30000000000007 != 300.3)
    doc = FreightDocument(
        carrier_name="Precision Logistics LLC",
        load_number="LD-PRECISION",
        pickup_location=Location(city="Dallas", state="TX", zip="75201"),
        delivery_location=Location(city="Atlanta", state="GA", zip="30303"),
        total_linehaul_rate=100.10,
        fuel_surcharge=200.20,
        total_pay=300.30,
        weight_lbs=30000,
    )
    result = validate_document(doc)

    # Decimal arithmetic handles this without false positive RATE_MISMATCH
    assert "RATE_MISMATCH" not in result.error_codes
    assert result.is_valid is True


def test_multiple_simultaneous_issues():
    """Combined test: missing fields, rate mismatch, and overweight load in single document."""
    doc = FreightDocument(
        carrier_name="",  # Incomplete
        load_number=None,  # Incomplete
        pickup_location=None,  # Incomplete
        delivery_location=Location(city="Atlanta", state="GA", zip="30303"),
        total_linehaul_rate=2200.0,
        fuel_surcharge=350.0,
        total_pay=2800.0,  # Mismatch ($2,550 vs $2,800)
        weight_lbs=48000,  # Overweight
    )
    result = validate_document(doc)

    assert result.is_valid is False
    assert "INCOMPLETE_DATA" in result.error_codes
    assert "RATE_MISMATCH" in result.error_codes
    assert "OVERWEIGHT_LOAD" in result.warning_codes
