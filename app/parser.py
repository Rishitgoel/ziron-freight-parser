"""
LLM Document Parsing & Schema Enforcement module.
Uses OpenAI Structured Outputs with Pydantic v2 to enforce strict schema adherence.
Includes an offline deterministic fallback extractor for zero-API-key evaluation and testing.
"""

import os
import re
import time
from typing import Optional, Tuple
from dotenv import load_dotenv
from openai import OpenAI, OpenAIError

from app.models import FreightDocument, Location

load_dotenv()

SYSTEM_EXTRACTION_PROMPT = """You are an expert freight logistics data extraction system.
Extract structured information from the provided operational freight document strictly conforming to the schema.

RULES:
1. Extract ONLY information explicitly stated in the document.
2. DO NOT infer, guess, or calculate missing values.
3. If any field is missing or ambiguous, return null for that field.
4. Preserve load and reference numbers exactly as written (e.g. 'LD-994821').
5. Extract city, 2-letter state code, and ZIP code string separately for pickup and delivery locations.
6. Parse monetary amounts as pure float numbers without currency symbols ($) or commas.
7. Map 'Total Agreed Amount' or gross compensation to 'total_pay'.
8. Parse cargo weight as an integer number of pounds (lbs).
"""


def _mock_deterministic_extractor(raw_text: str) -> FreightDocument:
    """
    Deterministic rule-based extractor used as a fallback when running offline
    or when no OpenAI API key is configured. Enables instant testing and evaluation.
    """
    # Extract Carrier
    carrier_match = re.search(r"Carrier:\s*([^\r\n]+)", raw_text, re.IGNORECASE)
    carrier_name = carrier_match.group(1).strip() if carrier_match and carrier_match.group(1).strip() else None

    # Extract Load Number / Ref #
    load_match = re.search(r"(?:Ref\s*#|Load\s*#|Order\s*#):\s*([A-Za-z0-9\-_]+)", raw_text, re.IGNORECASE)
    load_number = load_match.group(1).strip() if load_match else None
    if load_number and "PENDING" in load_number.upper():
        load_number = None

    # Extract Pickup Location (e.g., Dallas, TX 75201)
    pickup_loc = None
    pickup_section = re.search(r"PICKUP DETAILS:.*?(?=DROP-OFF|CARGO|$)", raw_text, re.DOTALL | re.IGNORECASE)
    if pickup_section:
        pickup_match = re.search(
            r"([A-Za-z\s]+),\s*([A-Z]{2})\s+([0-9]{5}(?:-[0-9]{4})?)",
            pickup_section.group(0),
        )
        if pickup_match:
            pickup_loc = Location(
                city=pickup_match.group(1).strip().split(",")[-1].strip(),
                state=pickup_match.group(2).strip(),
                zip=pickup_match.group(3).strip(),
            )
        else:
            # Partial match check
            city_match = re.search(r"Origin:\s*([^,\r\n]+)", pickup_section.group(0))
            if city_match:
                pickup_loc = Location(city=city_match.group(1).strip(), state=None, zip=None)

    # Extract Delivery Location (e.g., Atlanta, GA 30303)
    delivery_loc = None
    delivery_section = re.search(r"DROP-OFF DETAILS:.*?(?=CARGO|FINANCIAL|$)", raw_text, re.DOTALL | re.IGNORECASE)
    if delivery_section:
        delivery_match = re.search(
            r"([A-Za-z\s]+),\s*([A-Z]{2})\s+([0-9]{5}(?:-[0-9]{4})?)",
            delivery_section.group(0),
        )
        if delivery_match:
            delivery_loc = Location(
                city=delivery_match.group(1).strip().split(",")[-1].strip(),
                state=delivery_match.group(2).strip(),
                zip=delivery_match.group(3).strip(),
            )
        else:
            city_match = re.search(r"Destination:\s*([^,\r\n]+)", delivery_section.group(0))
            if city_match:
                delivery_loc = Location(city=city_match.group(1).strip(), state=None, zip=None)

    # Extract Linehaul Rate
    linehaul_match = re.search(r"Linehaul\s*(?:Rate)?:\s*\$?([0-9,]+(?:\.[0-9]{2})?)", raw_text, re.IGNORECASE)
    linehaul_rate = (
        float(linehaul_match.group(1).replace(",", "")) if linehaul_match else None
    )

    # Extract Fuel Surcharge
    fuel_match = re.search(r"Fuel\s*Surcharge\s*(?:\(FSC\))?:\s*\$?([0-9,]+(?:\.[0-9]{2})?)", raw_text, re.IGNORECASE)
    fuel_surcharge = (
        float(fuel_match.group(1).replace(",", "")) if fuel_match else None
    )

    # Extract Total Agreed Amount
    total_match = re.search(r"Total\s*(?:Agreed)?\s*(?:Amount|Pay):\s*\$?([0-9,]+(?:\.[0-9]{2})?)", raw_text, re.IGNORECASE)
    total_pay = (
        float(total_match.group(1).replace(",", "")) if total_match else None
    )

    # Extract Cargo Weight
    weight_match = re.search(r"(?:Total\s*)?Weight:\s*([0-9,]+)\s*lbs", raw_text, re.IGNORECASE)
    weight_lbs = (
        int(weight_match.group(1).replace(",", "")) if weight_match else None
    )

    return FreightDocument(
        carrier_name=carrier_name,
        load_number=load_number,
        pickup_location=pickup_loc,
        delivery_location=delivery_loc,
        total_linehaul_rate=linehaul_rate,
        fuel_surcharge=fuel_surcharge,
        total_pay=total_pay,
        weight_lbs=weight_lbs,
    )


def parse_freight_document(
    raw_text: str,
    api_key: Optional[str] = None,
    model: Optional[str] = None,
    force_mock: bool = False,
) -> Tuple[FreightDocument, dict]:
    """
    Parses unstructured operational text into a strict typed FreightDocument schema.

    Uses OpenAI's beta.chat.completions.parse API with response_format=FreightDocument,
    which activates strict JSON Schema constrained decoding at the LLM level.

    Args:
        raw_text: Unstructured text from rate con, invoice, or load agreement.
        api_key: OpenAI API key (defaults to OPENAI_API_KEY environment variable).
        model: Model name (defaults to OPENAI_MODEL env var or 'gpt-4o-mini').
        force_mock: If True, bypasses LLM and uses deterministic offline extractor.

    Returns:
        Tuple of (FreightDocument, execution_metadata_dict).
    """
    start_time = time.perf_counter()
    effective_key = api_key or os.getenv("OPENAI_API_KEY")
    use_mock_env = os.getenv("USE_MOCK_PARSER", "false").lower() in ("true", "1", "yes")

    # If mock forced or no valid key is provided, use deterministic offline parser
    if force_mock or use_mock_env or not effective_key or effective_key == "your_openai_api_key_here":
        doc = _mock_deterministic_extractor(raw_text)
        duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
        metadata = {
            "parser_engine": "deterministic_offline_fallback",
            "model": "offline-rule-parser",
            "processing_time_ms": duration_ms,
            "structured_output_mode": "mock_pydantic",
        }
        return doc, metadata

    selected_model = model or os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    try:
        client = OpenAI(api_key=effective_key)

        completion = client.beta.chat.completions.parse(
            model=selected_model,
            messages=[
                {"role": "system", "content": SYSTEM_EXTRACTION_PROMPT},
                {"role": "user", "content": raw_text},
            ],
            response_format=FreightDocument,
            temperature=0.0,
        )

        parsed_doc: Optional[FreightDocument] = completion.choices[0].message.parsed
        if parsed_doc is None:
            raise ValueError("OpenAI parser returned empty parsed document.")

        duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
        metadata = {
            "parser_engine": "openai_structured_outputs",
            "model": selected_model,
            "processing_time_ms": duration_ms,
            "structured_output_mode": "json_schema_constrained",
            "usage": {
                "prompt_tokens": completion.usage.prompt_tokens if completion.usage else 0,
                "completion_tokens": completion.usage.completion_tokens if completion.usage else 0,
                "total_tokens": completion.usage.total_tokens if completion.usage else 0,
            },
        }
        return parsed_doc, metadata

    except OpenAIError as exc:
        # Fallback gracefully with error notice
        doc = _mock_deterministic_extractor(raw_text)
        duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
        metadata = {
            "parser_engine": "fallback_after_api_error",
            "error_detail": str(exc),
            "model": "fallback-offline",
            "processing_time_ms": duration_ms,
        }
        return doc, metadata
