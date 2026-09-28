# Ziron Labs - Freight Document Intelligence & Automated Decision Pipeline

[![CI](https://github.com/Rishitgoel/ziron-freight-parser/actions/workflows/ci.yml/badge.svg)](https://github.com/Rishitgoel/ziron-freight-parser/actions)
![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)
![Pydantic v2](https://img.shields.io/badge/Pydantic-v2.12-emerald.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-REST%20API-009688.svg)
![License MIT](https://img.shields.io/badge/license-MIT-purple.svg)

A lightweight, production-grade Python service that parses unstructured operational freight documents (rate confirmations, load tenders, invoices) into strictly typed JSON, validates the data against deterministic logistics business rules, and executes an automated workflow routing decision. Includes an **interactive LoadPilot-styled web triage dashboard**, a **FastAPI REST API**, and a **CLI interface**.

---

## Architecture & Guiding Philosophy

```
Raw Freight Document
        │
        ▼
┌─────────────────────────┐
│     Document Parser     │  ◄── OpenAI Structured Outputs (gpt-4o-mini)
│ (Extracts Typed Schema) │      or Offline Fallback Extractor
└───────────┬─────────────┘
            │
            ▼
┌─────────────────────────┐
│     Pydantic Schema     │  ◄── Canonical FreightDocument & Nested Location
│ (Contract Verification) │      Strict Typing & String ZIP Preservation
└───────────┬─────────────┘
            │
            ▼
┌─────────────────────────┐
│    Validation Engine    │  ◄── 100% Deterministic Python Logic
│  (Business Logic Rules) │      • Decimal Financial Math Check (RATE_MISMATCH)
└───────────┬─────────────┘      • Legal Gross Weight Check (OVERWEIGHT_LOAD)
            │                    • Required Field Completeness (INCOMPLETE_DATA)
            ▼
┌─────────────────────────┐
│     Decision Engine     │  ◄── State Machine & Audit Summary
│  (Automated Routing)    │      • APPROVED  (Straight-Through Processing)
└─────────────────────────┘      • FLAGGED_FOR_HUMAN_REVIEW (Itemized Triage)
```

### Core Tenet: *"LLM extracts. Python decides."*
* The LLM's **sole responsibility** is converting unstructured, messy document text into typed data conforming to a canonical schema.
* The LLM is **never** asked to perform financial math, determine compliance, or decide whether a shipment is approved.
* All business rules, monetary calculations, weight checks, and workflow state transitions remain **100% deterministic, testable Python code**.

---

## Repository Structure

```
ziron-freight-parser/
├── .github/
│   └── workflows/
│       └── ci.yml             # GitHub Actions CI workflow (Python 3.11, 3.12, 3.13)
├── app/
│   ├── __init__.py
│   ├── models.py              # Canonical Pydantic schemas (FreightDocument, Location, DecisionResult)
│   ├── parser.py              # OpenAI Structured Outputs parser + deterministic offline fallback
│   ├── validator.py           # Deterministic validation engine (Decimal math, weight, completeness)
│   ├── decision.py            # Workflow state routing & audit summary generator
│   ├── web.py                 # FastAPI application & LoadPilot interactive triage dashboard
│   └── main.py                # Pipeline orchestrator and Rich CLI entrypoint
├── data/
│   ├── sample_document.txt    # Provided assignment document (triggers mismatch & overweight)
│   ├── valid_document.txt     # Clean rate confirmation (passes with APPROVED status)
│   └── incomplete_document.txt# Edge case document missing load numbers & locations
├── outputs/
│   ├── sample_output.json     # Clean canonical JSON output from the sample document
│   └── terminal_output.txt    # Formatted terminal output log
├── tests/
│   ├── __init__.py
│   ├── test_models.py         # Schema validation, string ZIP preservation, and helpers
│   ├── test_validator.py      # Unit tests for rate mismatch, overweight load, and completeness
│   ├── test_decision.py       # Unit tests for decision state machine and telemetry
│   ├── test_parser.py         # Integration tests across sample, clean, and incomplete documents
│   └── test_web.py            # Integration tests for FastAPI endpoints and healthcheck
├── Dockerfile                 # Multi-stage production container definition
├── docker-compose.yml         # One-command containerized execution
├── .env.example               # Environment variables template
├── .gitignore                 # Python gitignore
├── requirements.txt           # Locked dependencies (pydantic, openai, fastapi, uvicorn, pytest, rich)
└── README.md                  # System documentation & architecture notes
```

---

## Setup & Installation

### Prerequisites
* **Python 3.10+** (tested on Python 3.13)
* Git

### 1. Clone the Repository
```bash
git clone https://github.com/Rishitgoel/ziron-freight-parser.git
cd ziron-freight-parser
```

### 2. Create and Activate a Virtual Environment
```bash
# On Linux / macOS:
python3 -m venv venv
source venv/bin/activate

# On Windows (PowerShell):
python -m venv venv
.\venv\Scripts\Activate.ps1
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure API Keys
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```
Edit `.env` to provide your OpenAI API key:
```env
OPENAI_API_KEY=sk-proj-your_actual_key_here
OPENAI_MODEL=gpt-4o-mini
USE_MOCK_PARSER=false
```

> **Note on Zero-API-Key Evaluation:**  
> If an OpenAI API key is not configured or if `USE_MOCK_PARSER=true`, the application automatically falls back to an internal **deterministic offline parser**. This guarantees that reviewers and automated CI/CD pipelines can evaluate the entire end-to-end pipeline and test suite immediately without incurring token costs or needing external credentials.

---

## How to Run the Pipeline

### 1. Launch the Interactive LoadPilot Web Dashboard & REST API
```bash
python -m app.web
```
* **Interactive Web Dashboard:** Open [http://localhost:8000](http://localhost:8000) in your browser.
  * Styled directly with the official **Ziron Labs design system** (brand gradient `#3b6dff` -> `#5b4bff` -> `#7c3aed`, dark slate `#090d16`, glassmorphic cards).
  * Includes one-click preset buttons: **Sample Doc (Flagged)**, **Clean Load (Approved)**, and **Incomplete Doc**.
  * Shows live discrepancy cards, gross weight meters, raw JSON drawers, and human-in-the-loop action buttons.
* **Interactive Swagger API Documentation:** Open [http://localhost:8000/docs](http://localhost:8000/docs).
* **REST API Endpoint (`POST /api/v1/parse`):**
  ```bash
  curl -X POST http://localhost:8000/api/v1/parse \
       -H "Content-Type: application/json" \
       -d '{"raw_text": "...", "force_mock": true}'
  ```

### 2. Run via Docker Compose (Optional)
```bash
docker compose up --build
```

### 3. Run CLI Against the Provided Sample Document
```bash
python -m app.main --file data/sample_document.txt --output outputs/sample_output.json
```

### 4. Run CLI in Offline / Mock Mode (Bypass API)
```bash
python -m app.main --file data/sample_document.txt --mock
```

### 5. Run Against Clean and Incomplete Documents
```bash
# Clean document (APPROVED):
python -m app.main --file data/valid_document.txt --output outputs/valid_output.json

# Incomplete document (INCOMPLETE_DATA):
python -m app.main --file data/incomplete_document.txt --output outputs/incomplete_output.json
```

---

## Running the Automated Test Suite

The repository includes a comprehensive `pytest` test suite with 24 unit and integration tests covering Pydantic models, boundary cases, financial math, web endpoints, and decision routing:

```bash
pytest -v
```

Output:
```
============================= test session starts =============================
collected 24 items

tests/test_decision.py::test_decision_approved_when_clean PASSED         [  4%]
tests/test_decision.py::test_decision_flagged_on_errors PASSED           [  8%]
tests/test_decision.py::test_decision_flagged_on_warnings PASSED         [ 12%]
tests/test_decision.py::test_decision_metadata_preservation PASSED       [ 16%]
tests/test_models.py::test_location_preserves_leading_zeros_in_zip PASSED [ 20%]
tests/test_models.py::test_location_incomplete_check PASSED              [ 25%]
tests/test_models.py::test_freight_document_instantiation PASSED         [ 29%]
tests/test_models.py::test_validation_result_helpers PASSED              [ 33%]
tests/test_parser.py::test_offline_parser_on_sample_document PASSED      [ 37%]
tests/test_parser.py::test_end_to_end_sample_document_pipeline PASSED    [ 41%]
tests/test_parser.py::test_end_to_end_valid_document_pipeline PASSED     [ 45%]
tests/test_parser.py::test_end_to_end_incomplete_document_pipeline PASSED [ 50%]
tests/test_validator.py::test_valid_document PASSED                      [ 54%]
tests/test_validator.py::test_rate_mismatch_detected PASSED              [ 58%]
tests/test_validator.py::test_overweight_load_warning PASSED             [ 62%]
tests/test_validator.py::test_weight_limit_boundaries PASSED             [ 66%]
tests/test_validator.py::test_missing_load_number PASSED                 [ 70%]
tests/test_validator.py::test_incomplete_location_fields PASSED          [ 75%]
tests/test_validator.py::test_financial_decimal_precision PASSED         [ 79%]
tests/test_validator.py::test_multiple_simultaneous_issues PASSED        [ 83%]
tests/test_web.py::test_health_check_endpoint PASSED                     [ 87%]
tests/test_web.py::test_dashboard_html_endpoint PASSED                   [ 91%]
tests/test_web.py::test_api_parse_sample_document PASSED                 [ 95%]
tests/test_web.py::test_api_parse_empty_text_returns_400 PASSED          [100%]

============================= 24 passed in 7.74s ==============================
```

---

## Sample Execution Output

### Terminal Output on Sample Document

```
Reading document from: data\sample_document.txt (771 chars)
Running extraction and validation pipeline...

+-----------------------------------------------------------------------------+
|   FLAGGED FOR HUMAN REVIEW    Ziron Freight Intelligence Automated Decision |
+-----------------------------------------------------------------------------+
+-------------------------------- Audit Trail --------------------------------+
| Decision Summary:                                                           |
| Document flagged for human review due to 1 blocking error(s) and 1          |
| warning(s): [RATE_MISMATCH] Financial mismatch: Linehaul ($2,200.00) + Fuel |
| Surcharge ($350.00) = $2,550.00, which does not match Total Agreed Pay      |
| ($2,800.00). Discrepancy: $250.00. | [OVERWEIGHT_LOAD] Load weight 46,800   |
| lbs exceeds standard legal highway threshold of 45,000 lbs. Overweight      |
| permits or specialized multi-axle equipment required.                       |
+-----------------------------------------------------------------------------+
                  Extracted Document Data                  
+---------------------------------------------------------+
| Field                    | Extracted Value              |
|--------------------------+------------------------------|
| Carrier Name             | Apex Logistics Solutions LLC |
| Load / Ref #             | LD-994821                    |
| Pickup Location          | Dallas, TX 75201             |
| Delivery Location        | Atlanta, GA 30303            |
| Linehaul Rate            | $2,200.00                    |
| Fuel Surcharge (FSC)     | $350.00                      |
| Total Agreed Pay         | $2,800.00                    |
| Cargo Weight             | 46,800 lbs                   |
+---------------------------------------------------------+
                         Validation Anomalies Detected                         
+-----------------------------------------------------------------------------+
| Severity     | Code                 | Description                           |
|--------------+----------------------+---------------------------------------|
| ERROR        | RATE_MISMATCH        | Financial mismatch: Linehaul          |
|              |                      | ($2,200.00) + Fuel Surcharge          |
|              |                      | ($350.00) = $2,550.00, which does not |
|              |                      | match Total Agreed Pay ($2,800.00).   |
|              |                      | Discrepancy: $250.00.                 |
| WARNING      | OVERWEIGHT_LOAD      | Load weight 46,800 lbs exceeds        |
|              |                      | standard legal highway threshold of   |
|              |                      | 45,000 lbs. Overweight permits or     |
|              |                      | specialized multi-axle equipment      |
|              |                      | required.                             |
+-----------------------------------------------------------------------------+
Engine: deterministic_offline_fallback | Model: offline-rule-parser | Latency: 1.45 ms

Clean structured output saved to: outputs\sample_output.json
```

### Clean JSON Output (`outputs/sample_output.json`)

```json
{
  "status": "FLAGGED_FOR_HUMAN_REVIEW",
  "summary": "Document flagged for human review due to 1 blocking error(s) and 1 warning(s): [RATE_MISMATCH] Financial mismatch: Linehaul ($2,200.00) + Fuel Surcharge ($350.00) = $2,550.00, which does not match Total Agreed Pay ($2,800.00). Discrepancy: $250.00. | [OVERWEIGHT_LOAD] Load weight 46,800 lbs exceeds standard legal highway threshold of 45,000 lbs. Overweight permits or specialized multi-axle equipment required.",
  "data": {
    "carrier_name": "Apex Logistics Solutions LLC",
    "load_number": "LD-994821",
    "pickup_location": {
      "city": "Dallas",
      "state": "TX",
      "zip": "75201"
    },
    "delivery_location": {
      "city": "Atlanta",
      "state": "GA",
      "zip": "30303"
    },
    "total_linehaul_rate": 2200.0,
    "fuel_surcharge": 350.0,
    "total_pay": 2800.0,
    "weight_lbs": 46800
  },
  "validation": {
    "is_valid": false,
    "errors": [
      {
        "code": "RATE_MISMATCH",
        "message": "Financial mismatch: Linehaul ($2,200.00) + Fuel Surcharge ($350.00) = $2,550.00, which does not match Total Agreed Pay ($2,800.00). Discrepancy: $250.00.",
        "severity": "ERROR",
        "field": "total_pay"
      }
    ],
    "warnings": [
      {
        "code": "OVERWEIGHT_LOAD",
        "message": "Load weight 46,800 lbs exceeds standard legal highway threshold of 45,000 lbs. Overweight permits or specialized multi-axle equipment required.",
        "severity": "WARNING",
        "field": "weight_lbs"
      }
    ]
  },
  "metadata": {
    "parser_engine": "deterministic_offline_fallback",
    "model": "offline-rule-parser",
    "processing_time_ms": 1.45,
    "structured_output_mode": "mock_pydantic"
  }
}
```

---

## Architecture Note

### 1. Ensuring Strict JSON Output from the LLM

To ensure 100% adherence to our data contract, this service avoids raw text prompting or fragile post-hoc regular expressions. Instead, it utilizes **OpenAI's Structured Outputs engine (`client.beta.chat.completions.parse`)** with direct **Pydantic v2 schemas**. Under the hood, OpenAI's API translates the Pydantic model into a strict JSON Schema and uses constrained decoding (grammar-based sampling) during token generation, physically preventing the model from producing invalid JSON, hallucinated keys, or missing required attributes. 

Additionally, domain-specific design choices were embedded directly into the schema:
* `Location` is isolated as a nested Pydantic model containing `city`, `state`, and `zip`.
* `zip` is modeled strictly as a `str` rather than an `int` to prevent numeric truncation of leading zeros (e.g. converting Boston ZIP `02108` to `2108`).
* All fields default to `Optional[T] = None` paired with a strict zero-hallucination prompt (*"If a value is missing or ambiguous, return null; do not infer"*). This prevents the LLM from fabricating logistics information to satisfy schema requirements, allowing our downstream validation engine to catch missing fields cleanly as `INCOMPLETE_DATA`.
* Finally, while the schema exposes floats to conform with API contracts, internal financial checks cast values to Python's `Decimal` type to prevent IEEE 754 floating-point rounding errors (e.g., `$0.10 + $0.20 != $0.30`).

### 2. Scaling to 100,000 Messy PDF Documents Per Day

Processing 100,000 documents per day equates to an average throughput of ~1.16 documents per second, with peak business-hour surges reaching 5–10 documents per second (~200 million tokens per day). At this scale, synchronous HTTP pipelines fail due to provider rate limits, network timeouts, and unpredictable document lengths. 

To achieve enterprise-grade scale and resilience, we would evolve this system into an **event-driven, decoupled microservices architecture**:

```
┌──────────────┐      S3 Event      ┌──────────────┐
│  AWS S3/GCS  │ ─────────────────► │  Amazon SQS  │
│  (Doc Lake)  │                    │ (Work Queue) │
└──────────────┘                    └──────┬───────┘
                                           │
                        ┌──────────────────┴──────────────────┐
                        ▼                                     ▼
             ┌─────────────────────┐               ┌─────────────────────┐
             │  Fast OCR / Layout  │               │   MinHash / Dedupe  │
             │ (Docling/Textract)  │               │   (Redis Cache Hit) │
             └──────────┬──────────┘               └──────────┬──────────┘
                        │                                     │
                        ▼                                     ▼
             ┌─────────────────────┐               ┌─────────────────────┐
             │ Tiered Model Router │               │ Validation Engine   │
             │ (gpt-4o-mini/vLLM)  │               │ (Deterministic)     │
             └──────────┬──────────┘               └──────────┬──────────┘
                        │                                     │
                        └──────────────────┬──────────────────┘
                                           │
                                  ┌────────┴────────┐
                                  ▼                 ▼
                             [APPROVED]     [HUMAN REVIEW]
                              (TMS STP)       (Ziron UI)
                                  │
                                  ▼
                        [Dead Letter Queue] (3x Retry Failures)
```

1. **Decoupled Queue & Autoscaling Workers:**  
   Incoming documents (from email, SFTP, or APIs) are immediately saved to an immutable S3 document lake. An S3 `ObjectCreated` event triggers an Amazon SQS queue. A containerized worker pool (running on Kubernetes with KEDA or AWS ECS) consumes tasks, autoscaling horizontally based on SQS queue depth (`ApproximateNumberOfMessagesVisible`). If OpenAI experiences latency or 429 throttling, the queue buffers the workload without dropping documents.
2. **Tiered Hybrid Extraction & Cost Optimization:**  
   Rather than passing 100,000 documents directly to expensive frontier models, documents pass through a tiered routing system:
   * **Tier 0 (Deterministic Regex / Layout Cache):** Standard, recurring broker templates (e.g. C.H. Robinson, TQL) are parsed deterministically at $0.00 compute cost.
   * **Tier 1 (Lightweight LLM):** Unstructured text and digital PDFs are routed to `gpt-4o-mini` or self-hosted quantized models (`Qwen2.5-7B` on vLLM).
   * **Tier 2 (OpenAI Batch API):** Non-urgent freight bills and PODs are submitted to OpenAI's Batch API for an immediate **50% cost discount**.
   * **Deduplication:** A MinHash/SHA-256 fingerprint is calculated across normalized document text against Redis; resubmitted documents are served from cache instantly.
3. **Dead Letter Queues (DLQ) & Human-in-the-Loop (HITL) Workflow:**  
   Unparseable or corrupted PDFs are retried up to three times with exponential backoff and jitter before being pushed to an SQS Dead Letter Queue (DLQ) paired with Datadog/CloudWatch alerts. Documents cleanly passing validation (`APPROVED`) achieve straight-through processing (STP) directly into the downstream TMS (target 80%+ STP rate). Documents with discrepancies (`RATE_MISMATCH`, `OVERWEIGHT_LOAD`) are routed directly to an operations triage dashboard (such as Ziron LoadPilot) where human brokers can review visual side-by-side diffs and override or correct the load in seconds.
