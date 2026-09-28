"""
Main Pipeline Orchestrator and CLI for the Ziron Labs Freight Document Parser.
Runs the complete workflow:
  Raw Document -> LLM Structured Parsing -> Business Rule Validation -> Decision Output
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Optional

from app.decision import make_decision
from app.models import DecisionResult, DecisionStatus
from app.parser import parse_freight_document
from app.validator import validate_document

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
    from rich import print as rprint
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False


def process_document(
    raw_text: str,
    api_key: Optional[str] = None,
    model: Optional[str] = None,
    force_mock: bool = False,
) -> DecisionResult:
    """
    Executes the end-to-end freight document processing pipeline.

    Stages:
      1. Parse raw unstructured document text into FreightDocument Pydantic model.
      2. Run deterministic business rules (Math, Weight, Incomplete Data).
      3. Compute automated routing decision (APPROVED vs FLAGGED_FOR_HUMAN_REVIEW).

    Args:
        raw_text: Messy document text.
        api_key: Optional OpenAI API key.
        model: Optional model name.
        force_mock: Optional flag to use offline deterministic parser.

    Returns:
        DecisionResult containing status, summary, structured data, and audit details.
    """
    # 1. Parsing Tier (LLM Extracts)
    document, metadata = parse_freight_document(
        raw_text=raw_text,
        api_key=api_key,
        model=model,
        force_mock=force_mock,
    )

    # 2. Validation Tier (Python Decides)
    validation = validate_document(document)

    # 3. Decision Tier (Automated State Routing)
    decision = make_decision(
        document=document,
        validation=validation,
        metadata=metadata,
        flag_on_warnings=True,
    )

    return decision


def display_results_rich(result: DecisionResult) -> None:
    """Renders formatted visual terminal output using the Rich library."""
    console = Console()

    # Determine status color
    if result.status == DecisionStatus.APPROVED:
        status_color = "bold green"
        badge = "[bold white on green]  APPROVED  [/bold white on green]"
    else:
        status_color = "bold red"
        badge = "[bold white on red]  FLAGGED FOR HUMAN REVIEW  [/bold white on red]"

    console.print()
    console.print(Panel(
        f"{badge}  [bold]Ziron Freight Intelligence Automated Decision[/bold]",
        style=status_color,
        expand=False,
    ))

    # Summary Panel
    console.print(Panel(
        f"[bold]Decision Summary:[/bold]\n{result.summary}",
        title="Audit Trail",
        border_style="yellow" if result.status != DecisionStatus.APPROVED else "green",
    ))

    # Structured Data Table
    table = Table(title="Extracted Document Data", show_header=True, header_style="bold cyan")
    table.add_column("Field", style="dim", width=24)
    table.add_column("Extracted Value", style="bold white")

    data = result.data
    table.add_row("Carrier Name", str(data.carrier_name or "[italic red]MISSING[/italic red]"))
    table.add_row("Load / Ref #", str(data.load_number or "[italic red]MISSING[/italic red]"))

    pickup_str = (
        f"{data.pickup_location.city}, {data.pickup_location.state} {data.pickup_location.zip}"
        if data.pickup_location and data.pickup_location.is_complete()
        else f"[italic red]{data.pickup_location or 'MISSING'}[/italic red]"
    )
    delivery_str = (
        f"{data.delivery_location.city}, {data.delivery_location.state} {data.delivery_location.zip}"
        if data.delivery_location and data.delivery_location.is_complete()
        else f"[italic red]{data.delivery_location or 'MISSING'}[/italic red]"
    )

    table.add_row("Pickup Location", pickup_str)
    table.add_row("Delivery Location", delivery_str)
    table.add_row("Linehaul Rate", f"${data.total_linehaul_rate:,.2f}" if data.total_linehaul_rate is not None else "[red]MISSING[/red]")
    table.add_row("Fuel Surcharge (FSC)", f"${data.fuel_surcharge:,.2f}" if data.fuel_surcharge is not None else "[red]MISSING[/red]")
    table.add_row("Total Agreed Pay", f"${data.total_pay:,.2f}" if data.total_pay is not None else "[red]MISSING[/red]")
    table.add_row("Cargo Weight", f"{data.weight_lbs:,} lbs" if data.weight_lbs is not None else "[red]MISSING[/red]")

    console.print(table)

    # Validation Findings Table
    if result.validation.errors or result.validation.warnings:
        v_table = Table(title="Validation Anomalies Detected", show_header=True, header_style="bold red")
        v_table.add_column("Severity", width=12)
        v_table.add_column("Code", style="bold yellow", width=20)
        v_table.add_column("Description", style="white")

        for err in result.validation.errors:
            v_table.add_row("[bold red]ERROR[/bold red]", err.code, err.message)
        for warn in result.validation.warnings:
            v_table.add_row("[bold yellow]WARNING[/bold yellow]", warn.code, warn.message)

        console.print(v_table)

    # Telemetry
    if result.metadata:
        console.print(
            f"[dim]Engine: {result.metadata.get('parser_engine')} | "
            f"Model: {result.metadata.get('model')} | "
            f"Latency: {result.metadata.get('processing_time_ms')} ms[/dim]\n"
        )


def main():
    parser = argparse.ArgumentParser(
        description="Ziron Labs Freight Document Parsing & Automated Decision Pipeline."
    )
    parser.add_argument(
        "--file",
        "-f",
        type=str,
        default="data/sample_document.txt",
        help="Path to the raw freight document text file (default: data/sample_document.txt)",
    )
    parser.add_argument(
        "--output",
        "-o",
        type=str,
        default="outputs/sample_output.json",
        help="Path to save the resulting JSON payload (default: outputs/sample_output.json)",
    )
    parser.add_argument(
        "--mock",
        action="store_true",
        help="Force using the deterministic offline parser (bypasses OpenAI API)",
    )
    parser.add_argument(
        "--model",
        type=str,
        default=None,
        help="Specify OpenAI model (e.g. gpt-4o-mini or gpt-4o)",
    )

    args = parser.parse_args()

    doc_path = Path(args.file)
    if not doc_path.exists():
        print(f"Error: Input file not found at '{doc_path}'.", file=sys.stderr)
        sys.exit(1)

    raw_text = doc_path.read_text(encoding="utf-8")

    print(f"Reading document from: {doc_path} ({len(raw_text)} chars)")
    print("Running extraction and validation pipeline...\n")

    result = process_document(
        raw_text=raw_text,
        model=args.model,
        force_mock=args.mock,
    )

    # Render Terminal Output
    if RICH_AVAILABLE:
        display_results_rich(result)
    else:
        print("--- AGENT DECISION ---")
        print(json.dumps(result.model_dump(), indent=2))

    # Save Canonical JSON Output
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result.model_dump(), f, indent=2)

    print(f"Clean structured output saved to: {output_path}")


if __name__ == "__main__":
    main()
