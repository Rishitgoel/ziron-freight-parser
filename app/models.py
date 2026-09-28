"""
Data contracts and Pydantic schemas for the Freight Document Processing Pipeline.
"""

from enum import Enum
from typing import Any, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class Location(BaseModel):
    """Represents a geographic facility location with discrete city, state, and ZIP."""
    model_config = ConfigDict(str_strip_whitespace=True)

    city: Optional[str] = Field(
        default=None,
        description="City name (e.g. Dallas, Atlanta)",
    )
    state: Optional[str] = Field(
        default=None,
        description="2-letter US State abbreviation (e.g. TX, GA)",
    )
    zip: Optional[str] = Field(
        default=None,
        description="Postal ZIP code formatted as string to preserve leading zeros (e.g. '75201', '02108')",
    )

    def is_complete(self) -> bool:
        """Returns True if city, state, and zip are all non-empty strings."""
        return bool(self.city and self.state and self.zip)


class FreightDocument(BaseModel):
    """
    Canonical schema for extracted freight operational documents (rate confirmations, load tenders).
    Matches the schema requirements of the Ziron Labs assessment.
    """
    model_config = ConfigDict(str_strip_whitespace=True)

    carrier_name: Optional[str] = Field(
        default=None,
        description="Legal carrier company name executing the shipment",
    )
    load_number: Optional[str] = Field(
        default=None,
        description="Load identifier, order reference number, or tender ID",
    )
    pickup_location: Optional[Location] = Field(
        default=None,
        description="Origin shipping facility location",
    )
    delivery_location: Optional[Location] = Field(
        default=None,
        description="Destination consignee facility location",
    )
    total_linehaul_rate: Optional[float] = Field(
        default=None,
        description="Base linehaul transportation cost in USD",
    )
    fuel_surcharge: Optional[float] = Field(
        default=None,
        description="Fuel surcharge amount (FSC) in USD",
    )
    total_pay: Optional[float] = Field(
        default=None,
        description="Total agreed amount or gross pay in USD",
    )
    weight_lbs: Optional[int] = Field(
        default=None,
        description="Gross cargo weight in pounds (lbs)",
    )


class ValidationSeverity(str, Enum):
    """Severity classification for validation findings."""
    ERROR = "ERROR"
    WARNING = "WARNING"


class ValidationIssue(BaseModel):
    """Represents a single business rule anomaly or constraint failure."""
    code: str = Field(description="Unique machine-readable issue code (e.g., RATE_MISMATCH)")
    message: str = Field(description="Human-readable explanation of the issue")
    severity: ValidationSeverity = Field(
        default=ValidationSeverity.ERROR,
        description="Severity level: ERROR (blocking) or WARNING (advisory)",
    )
    field: Optional[str] = Field(
        default=None,
        description="Optional field path associated with the issue",
    )


class ValidationResult(BaseModel):
    """Summary of business rule engine execution results."""
    is_valid: bool = Field(
        description="True if no blocking ERROR level issues were detected"
    )
    errors: List[ValidationIssue] = Field(
        default_factory=list,
        description="List of blocking errors preventing automated processing",
    )
    warnings: List[ValidationIssue] = Field(
        default_factory=list,
        description="List of non-blocking operational warnings requiring attention",
    )

    @property
    def error_codes(self) -> List[str]:
        return [e.code for e in self.errors]

    @property
    def warning_codes(self) -> List[str]:
        return [w.code for w in self.warnings]

    @property
    def all_codes(self) -> List[str]:
        return self.error_codes + self.warning_codes


class DecisionStatus(str, Enum):
    """Final automated decision status for downstream routing."""
    APPROVED = "APPROVED"
    FLAGGED_FOR_HUMAN_REVIEW = "FLAGGED_FOR_HUMAN_REVIEW"


class DecisionResult(BaseModel):
    """The complete response payload containing the automated decision, data, and audit trail."""
    status: DecisionStatus = Field(
        description="Final routing outcome: APPROVED or FLAGGED_FOR_HUMAN_REVIEW"
    )
    summary: str = Field(
        description="Human-readable summary explanation of the decision"
    )
    data: FreightDocument = Field(
        description="Clean, structured freight document data"
    )
    validation: ValidationResult = Field(
        description="Detailed validation issues breakdown"
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Execution metadata such as model used, latency, and timestamp",
    )
