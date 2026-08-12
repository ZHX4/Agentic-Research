"""CLI for Phase 6 hypothesis reasoning."""
from __future__ import annotations

from pathlib import Path
from typing import Literal

import typer

from agentic_research.hypotheses.engine import run_hypothesis_reasoning
from agentic_research.schemas.gap import GapStatus
from agentic_research.schemas.phase5 import NoveltyVerificationReport
from agentic_research.schemas.phase6 import HypothesisConfig

app = typer.Typer(help="Agentic-Research Phase 6 hypothesis reasoning.")


@app.command(name="reason")
def reason(
    input: Path = typer.Option(..., exists=True, readable=True, help="Phase 5 NoveltyVerificationReport JSON."),
    output: Path = typer.Option(..., help="Phase 6 HypothesisRun JSON."),
    hypotheses_per_gap: int = typer.Option(6, min=1, max=50),
    max_composed_pairs: int = typer.Option(25, min=0, max=200),
    dedup_similarity_threshold: float = typer.Option(0.82, min=0, max=1),
    tournament_size: int = typer.Option(5, min=2, max=20),
    tournament_rounds: int = typer.Option(3, min=1, max=20),
    pareto_limit: int = typer.Option(12, min=1, max=100),
    keep_diverse_limit: int = typer.Option(20, min=1, max=200),
    evolve_top_k: int = typer.Option(6, min=1, max=50),
    max_evolution_generations: int = typer.Option(2, min=0, max=10),
    min_gap_status: Literal["survived", "weakened", "uncertain"] = typer.Option("survived"),
    allow_uncertain_gaps: bool = typer.Option(False),
    clustering_threshold: float = typer.Option(0.70, min=0, max=1),
) -> None:
    """Generate, reflect on, rank, evolve, and Pareto-select hypotheses."""
    report = NoveltyVerificationReport.model_validate_json(input.read_text(encoding="utf-8"))
    minimum = GapStatus(min_gap_status)
    if minimum == GapStatus.UNCERTAIN and not allow_uncertain_gaps:
        raise typer.BadParameter("--allow-uncertain-gaps is required when --min-gap-status=uncertain")
    cfg = HypothesisConfig(
        hypotheses_per_gap=hypotheses_per_gap,
        max_composed_pairs=max_composed_pairs,
        dedup_similarity_threshold=dedup_similarity_threshold,
        tournament_size=tournament_size,
        tournament_rounds=tournament_rounds,
        pareto_limit=pareto_limit,
        keep_diverse_limit=keep_diverse_limit,
        evolve_top_k=evolve_top_k,
        max_evolution_generations=max_evolution_generations,
        min_gap_status=minimum,
        allow_uncertain_gaps=allow_uncertain_gaps,
        clustering_threshold=clustering_threshold,
    )
    run = run_hypothesis_reasoning([result.verified_candidate for result in report.results], cfg)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(run.model_dump_json(indent=2), encoding="utf-8")
    typer.echo(f"Wrote {len(run.candidates)} hypothesis artifacts to {output}")


if __name__ == "__main__":
    app()
