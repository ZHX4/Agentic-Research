"""Command-line interface for Agentic-Research."""

from __future__ import annotations

import json
from pathlib import Path

import typer
from rich import print
from rich.table import Table

from agentic_research.gaps import detect_missing_combinations
from agentic_research.ingestion.jsonl import load_papers
from agentic_research.intelligence.calibration import CalibrationExample, IsotonicCalibrator, IsotonicModel, calibration_report
from agentic_research.intelligence.pipeline import extract_paper_intelligence
from agentic_research.literature.factory import build_literature_service
from agentic_research.literature.fulltext import FullTextAcquirer, FullTextManifest, parse_full_text
from agentic_research.literature.settings import LiteratureSettings
from agentic_research.literature.transport import HttpClient, RateLimiter
from agentic_research.retrieval.contracts import SearchQuery
from agentic_research.schemas import Paper
from agentic_research.storage.jsonl import JsonlStore

app = typer.Typer(help="Agentic-Research scientific discovery toolkit.")


@app.command()
def demo() -> None:
    """Run the offline demo gap-discovery pipeline."""
    path = Path("data/demo/papers.jsonl")
    papers = list(load_papers(path))
    gaps = detect_missing_combinations(papers)
    table = Table(title="Candidate research gaps")
    table.add_column("Task")
    table.add_column("Method")
    table.add_column("Dataset")
    table.add_column("Confidence", justify="right")
    for gap in gaps:
        table.add_row(gap.task or "", gap.method or "", gap.dataset or "", f"{gap.confidence:.2f}")
    print(table)
    print("\n[dim]These are candidates only; no novelty claim has been made.[/dim]")


@app.command()
def gaps(
    input: Path = typer.Option(..., exists=True, readable=True, help="Input JSONL paper corpus."),
    output: Path = typer.Option(..., help="Output JSON file for candidate gaps."),
) -> None:
    """Detect candidate missing method/dataset combinations from a paper corpus."""
    papers = list(load_papers(input))
    result = detect_missing_combinations(papers)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps([item.model_dump(mode="json") for item in result], indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Wrote {len(result)} candidate gaps to {output}")


@app.command()
def validate(input: Path = typer.Option(..., exists=True, readable=True)) -> None:
    """Validate a JSONL corpus against the canonical Paper schema."""
    papers = list(load_papers(input))
    print(f"Validated {len(papers)} papers.")


@app.command(name="search")
def literature_search(
    text: str = typer.Argument(..., help="Scientific search query."),
    limit: int = typer.Option(20, min=1, max=1000, help="Maximum unique papers to return."),
    year_from: int | None = typer.Option(None, min=1900, max=2200),
    year_to: int | None = typer.Option(None, min=1900, max=2200),
    temporal_cutoff: int | None = typer.Option(None, min=1900, max=2200),
    output: Path | None = typer.Option(None, help="Optional JSON output path."),
) -> None:
    """Search configured scholarly sources and deduplicate the results."""
    query = SearchQuery(text=text, limit=limit, year_from=year_from, year_to=year_to, temporal_cutoff=temporal_cutoff)
    with build_literature_service(LiteratureSettings()) as service:
        hits = service.search(query)
    payload = [
        {"source": hit.source, "score": hit.score, "retrieval_reason": hit.retrieval_reason, "paper": hit.paper.model_dump(mode="json")}
        for hit in hits
    ]
    if output:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"Wrote {len(payload)} unique papers to {output}")
    else:
        print(json.dumps(payload, indent=2, ensure_ascii=False))


@app.command()
def acquire(
    input: Path = typer.Option(..., exists=True, readable=True, help="Input JSONL paper corpus."),
    output: Path = typer.Option(..., help="Output JSONL acquisition manifest."),
    output_dir: Path = typer.Option(Path("artifacts/fulltext"), help="Directory for downloaded files."),
) -> None:
    """Acquire available open full text and write acquisition manifests."""
    settings = LiteratureSettings()
    client = HttpClient(
        user_agent=settings.user_agent,
        timeout_seconds=settings.request_timeout_seconds,
        rate_limiter=RateLimiter(settings.arxiv_min_interval_seconds),
    )
    store = JsonlStore(output)
    acquirer = FullTextAcquirer(client=client, output_dir=output_dir)
    try:
        count = 0
        for paper in load_papers(input):
            if not paper.metadata.get("open_access_pdf_url") and not paper.arxiv_id and paper.url is None:
                manifest = FullTextManifest(
                    paper_id=paper.paper_id,
                    source="none",
                    requested_url=None,
                    media_type="unknown",
                    status="not_found",
                    error="No candidate full-text URL is available",
                )
            else:
                manifest = acquirer.acquire(paper)
            store.append(manifest)
            count += 1
        print(f"Wrote {count} full-text manifests to {output}")
    finally:
        client.close()


@app.command()
def parse(
    manifest: Path = typer.Option(..., exists=True, readable=True, help="JSONL full-text manifest."),
    output: Path = typer.Option(..., help="Output JSONL parsed documents."),
) -> None:
    """Parse successfully acquired PDF/HTML documents from a manifest."""
    manifests = JsonlStore(manifest).read(FullTextManifest)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8") as handle:
        count = 0
        for item in manifests:
            if item.status != "downloaded":
                continue
            handle.write(parse_full_text(item).model_dump_json() + "\n")
            count += 1
    print(f"Parsed {count} documents into {output}")


@app.command()
def analyze(
    paper: Path = typer.Option(..., exists=True, readable=True, help="JSON file containing one canonical Paper."),
    pdf: Path = typer.Option(..., exists=True, readable=True, help="PDF file to analyze."),
    output: Path = typer.Option(..., help="Output JSON containing Paper and StructuredExtraction."),
    calibration_model: Path | None = typer.Option(None, exists=True, readable=True, help="Optional isotonic calibration model JSON."),
) -> None:
    """Run the deterministic Phase 2 paper-intelligence pipeline on one PDF."""
    paper_obj = Paper.model_validate_json(paper.read_text(encoding="utf-8"))
    calibrator = None
    if calibration_model is not None:
        calibrator = IsotonicCalibrator.from_model(
            IsotonicModel.model_validate_json(calibration_model.read_text(encoding="utf-8"))
        )
    enriched, extraction = extract_paper_intelligence(paper_obj, pdf, calibrator=calibrator)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps({"paper": enriched.model_dump(mode="json"), "extraction": extraction.model_dump(mode="json")}, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    print(f"Wrote Phase 2 extraction to {output}")


@app.command()
def calibrate(
    input: Path = typer.Option(..., exists=True, readable=True, help="JSONL with raw_confidence and correct fields."),
    output: Path = typer.Option(..., help="Output calibration report JSON."),
    bins: int = typer.Option(10, min=1, max=100),
) -> None:
    """Measure extraction confidence calibration on labeled examples."""
    examples = [CalibrationExample.model_validate(json.loads(line)) for line in input.read_text(encoding="utf-8").splitlines() if line.strip()]
    report = calibration_report(examples, bins=bins)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(report.model_dump_json(indent=2), encoding="utf-8")
    print(f"Wrote calibration report for {len(examples)} examples to {output}")


@app.command(name="fit-calibrator")
def fit_calibrator(
    input: Path = typer.Option(..., exists=True, readable=True, help="JSONL with raw_confidence and correct fields."),
    output: Path = typer.Option(..., help="Output isotonic calibration model JSON."),
) -> None:
    """Fit and persist an isotonic calibrator from labeled extraction examples."""
    examples = [CalibrationExample.model_validate(json.loads(line)) for line in input.read_text(encoding="utf-8").splitlines() if line.strip()]
    model = IsotonicCalibrator.fit(examples).to_model()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(model.model_dump_json(indent=2), encoding="utf-8")
    print(f"Wrote calibration model for {len(examples)} examples to {output}")


if __name__ == "__main__":
    app()
