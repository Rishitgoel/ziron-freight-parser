"""
Unit tests for the FastAPI REST API and Web endpoints in app/web.py.
"""

from fastapi.testclient import TestClient
from app.web import app

client = TestClient(app)


def test_health_check_endpoint():
    """GET /api/v1/health should return status healthy."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["product"] == "LoadPilot"


def test_dashboard_html_endpoint():
    """GET / should return 200 OK with HTML content."""
    response = client.get("/")
    assert response.status_code == 200
    assert "<!DOCTYPE html>" in response.text
    assert "Ziron Labs" in response.text
    assert "LoadPilot" in response.text


def test_api_parse_sample_document():
    """POST /api/v1/parse with sample document should flag RATE_MISMATCH and OVERWEIGHT_LOAD."""
    raw_sample = """
    ===================================================
    FREIGHT RATE CONFIRMATION & ORDER AGREEMENT
    ===================================================
    Ref #: LD-994821
    Carrier: Apex Logistics Solutions LLC
    Date: 10/12/2025
    PICKUP DETAILS:
    Origin: Distribution Center 4, Dallas, TX 75201
    DROP-OFF DETAILS:
    Destination: Warehouse B, Atlanta, GA 30303
    CARGO DETAILS:
    Total Weight: 46,800 lbs
    FINANCIAL AGREEMENT:
    Linehaul Rate: $2,200.00
    Fuel Surcharge (FSC): $350.00
    Total Agreed Amount: $2,800.00
    """
    response = client.post(
        "/api/v1/parse",
        json={"raw_text": raw_sample, "force_mock": True},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "FLAGGED_FOR_HUMAN_REVIEW"
    assert any(e["code"] == "RATE_MISMATCH" for e in payload["validation"]["errors"])
    assert any(w["code"] == "OVERWEIGHT_LOAD" for w in payload["validation"]["warnings"])


def test_api_parse_empty_text_returns_400():
    """POST /api/v1/parse with empty string should return 400 Bad Request."""
    response = client.post("/api/v1/parse", json={"raw_text": "   "})
    assert response.status_code == 400
    assert "cannot be empty" in response.json()["detail"]
