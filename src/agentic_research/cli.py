"""Command-line interface for the deterministic research-agent foundation."""

import json
from pathlib import Path

import typer
from rich import print
from rich.table import Table

from agentic_research.gaps import detect_missing_combinations
from agentic_research.ingestion.jsonl import load_papers
from agentic_research.schemas import Paper

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
    print("\\n[dim]These are candidates only; no novelty claim has been made.[/dim]")


@app.command()
def gaps(
    input: Path = typer.Option(..., exists=True, readable=True, help="Input JSONL paper corpus."),
    output: Path = typer.Option(..., help="Output JSON file for candidate gaps."),
) -> None:
    """Detect candidate missing method/dataset combinations from a paper corpus."""
    papers = list(load_papers(input))
    result = detect_missing_combinations(papers)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps([item.model_dump(mode="json") for item in result], indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    print(f"Wrote {len(result)} candidate gaps to {output}")


@app.command()
def validate(input: Path = typer.Option(..., exists=True, readable=True)) -> None:
    """Validate a JSONL corpus against the canonical Paper schema."""
    papers = list(load_papers(input))
    print(f"Validated {len(papers)} papers.")


if __name__ == "__main__":
    app()
