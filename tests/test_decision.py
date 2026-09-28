"""
Unit tests for the decision routing engine in app/decision.py.
"""

from app.decision import make_decision
from app.models import (
    DecisionStatus,
    FreightDocument,
    Location,
    ValidationIssue,
    ValidationResult,
    ValidationSeverity,
)


def _sample_doc() -> FreightDocument:
    return FreightDocument(
        carrier_name="Apex Logistics",
        load_number="LD-994821",
        pickup_location=Location(city="Dallas", state="TX", zip="75201"),
        delivery_location=Location(city="Atlanta", state="GA", zip="30303"),
        total_linehaul_rate=2200.0,
        fuel_surcharge=350.0,
        total_pay=2800.0,
        weight_lbs=46800,
    )


def test_decision_approved_when_clean():
    """Documents with zero errors and zero warnings are APPROVED."""
    doc = _sample_doc()
    clean_val = ValidationResult(is_valid=True, errors=[], warnings=[])

    decision = make_decision(doc, clean_val)
    assert decision.status == DecisionStatus.APPROVED
    assert "successfully parsed and verified" in decision.summary


def test_decision_flagged_on_errors():
    """Documents with blocking errors are FLAGGED_FOR_HUMAN_REVIEW."""
    doc = _sample_doc()
    error_val = ValidationResult(
        is_valid=False,
        errors=[
            ValidationIssue(
                code="RATE_MISMATCH",
                message="Rate mismatch: $2,550 vs $2,800",
                severity=ValidationSeverity.ERROR,
            )
        ],
        warnings=[],
    )

    decision = make_decision(doc, error_val)
    assert decision.status == DecisionStatus.FLAGGED_FOR_HUMAN_REVIEW
    assert "RATE_MISMATCH" in decision.summary
    assert "blocking error" in decision.summary


def test_decision_flagged_on_warnings():
    """Documents with warnings (e.g. overweight load) are FLAGGED_FOR_HUMAN_REVIEW when flag_on_warnings=True."""
    doc = _sample_doc()
    warn_val = ValidationResult(
        is_valid=True,
        errors=[],
        warnings=[
            ValidationIssue(
                code="OVERWEIGHT_LOAD",
                message="Weight 46,800 lbs exceeds 45,000 lbs",
                severity=ValidationSeverity.WARNING,
            )
        ],
    )

    decision = make_decision(doc, warn_val, flag_on_warnings=True)
    assert decision.status == DecisionStatus.FLAGGED_FOR_HUMAN_REVIEW
    assert "OVERWEIGHT_LOAD" in decision.summary
    assert "operational warning" in decision.summary


def test_decision_metadata_preservation():
    """Execution telemetry must be preserved in the final DecisionResult."""
    doc = _sample_doc()
    val = ValidationResult(is_valid=True, errors=[], warnings=[])
    meta = {"model": "gpt-4o-mini", "processing_time_ms": 320.5}

    decision = make_decision(doc, val, metadata=meta)
    assert decision.metadata["model"] == "gpt-4o-mini"
    assert decision.metadata["processing_time_ms"] == 320.5
