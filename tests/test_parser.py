"""
Tests for LLM and offline document parsing and end-to-end processing pipeline.
"""

from pathlib import Path
from app.main import process_document
from app.models import DecisionStatus
from app.parser import parse_freight_document


def test_offline_parser_on_sample_document():
    """Verify that the parser extracts all fields accurately from the assignment's sample text."""
    sample_text = Path("data/sample_document.txt").read_text(encoding="utf-8")
    doc, meta = parse_freight_document(sample_text, force_mock=True)

    assert doc.carrier_name == "Apex Logistics Solutions LLC"
    assert doc.load_number == "LD-994821"
    assert doc.pickup_location.city == "Dallas"
    assert doc.pickup_location.state == "TX"
    assert doc.pickup_location.zip == "75201"
    assert doc.delivery_location.city == "Atlanta"
    assert doc.delivery_location.state == "GA"
    assert doc.delivery_location.zip == "30303"
    assert doc.total_linehaul_rate == 2200.0
    assert doc.fuel_surcharge == 350.0
    assert doc.total_pay == 2800.0
    assert doc.weight_lbs == 46800


def test_end_to_end_sample_document_pipeline():
    """
    End-to-end integration test on the provided assignment document.
    Must correctly extract fields, catch RATE_MISMATCH error, catch OVERWEIGHT_LOAD warning,
    and output FLAGGED_FOR_HUMAN_REVIEW status.
    """
    sample_text = Path("data/sample_document.txt").read_text(encoding="utf-8")
    result = process_document(sample_text, force_mock=True)

    assert result.status == DecisionStatus.FLAGGED_FOR_HUMAN_REVIEW
    assert "RATE_MISMATCH" in result.validation.error_codes
    assert "OVERWEIGHT_LOAD" in result.validation.warning_codes
    assert result.data.carrier_name == "Apex Logistics Solutions LLC"
    assert result.data.load_number == "LD-994821"


def test_end_to_end_valid_document_pipeline():
    """
    End-to-end integration test on a clean rate confirmation.
    Must validate cleanly and return APPROVED status.
    """
    valid_text = Path("data/valid_document.txt").read_text(encoding="utf-8")
    result = process_document(valid_text, force_mock=True)

    assert result.status == DecisionStatus.APPROVED
    assert len(result.validation.errors) == 0
    assert len(result.validation.warnings) == 0


def test_end_to_end_incomplete_document_pipeline():
    """
    End-to-end integration test on an incomplete document.
    Must flag INCOMPLETE_DATA and route to FLAGGED_FOR_HUMAN_REVIEW.
    """
    incomplete_text = Path("data/incomplete_document.txt").read_text(encoding="utf-8")
    result = process_document(incomplete_text, force_mock=True)

    assert result.status == DecisionStatus.FLAGGED_FOR_HUMAN_REVIEW
    assert "INCOMPLETE_DATA" in result.validation.error_codes
