"""CLI for Phase 5 adversarial gap verification."""

from __future__ import annotations

from pathlib import Path

import typer

from agentic_research.literature.factory import build_literature_service
from agentic_research.literature.settings import LiteratureSettings
from agentic_research.schemas.phase4 import GapDiscoveryResult
from agentic_research.schemas.phase5 import NoveltyVerificationConfig
from agentic_research.verification.policy import AdversarialNoveltyVerifier
from agentic_research.world_model.store import ScientificWorldModel

app = typer.Typer(help="Agentic-Research Phase 5 adversarial novelty verifier.")


@app.command(name="verify-gaps")
def verify_gaps(
    input: Path = typer.Option(..., exists=True, readable=True, help="Phase 4 GapDiscoveryResult JSON."),
    output: Path = typer.Option(..., help="Phase 5 NoveltyVerificationReport JSON."),
    database: Path | None = typer.Option(None, exists=True, readable=True, help="Optional Phase 3 world-model database."),
    temporal_cutoff: int | None = typer.Option(None, min=1900, max=2200),
    external_results_per_query: int = typer.Option(10, min=1, max=100),
    local_results_per_query: int = typer.Option(10, min=1, max=100),
    max_queries_per_gap: int = typer.Option(12, min=1, max=50),
    min_direct_similarity: float = typer.Option(0.92, min=0, max=1),
    near_match_similarity: float = typer.Option(0.72, min=0, max=1),
    min_broad_searches: int = typer.Option(3, min=1, max=50),
    no_external: bool = typer.Option(False, help="Disable configured external scholarly providers."),
    no_local: bool = typer.Option(False, help="Disable local world-model search."),
    no_status_transition: bool = typer.Option(False, help="Keep candidates at status=candidate even after verification."),
) -> None:
    """Challenge Phase 4 candidates against configured literature sources."""
    discovery = GapDiscoveryResult.model_validate_json(input.read_text(encoding="utf-8"))
    config = NoveltyVerificationConfig(
        external_results_per_query=external_results_per_query,
        local_results_per_query=local_results_per_query,
        max_queries_per_gap=max_queries_per_gap,
        min_direct_similarity=min_direct_similarity,
        near_match_similarity=near_match_similarity,
        min_broad_searches=min_broad_searches,
        temporal_cutoff=temporal_cutoff if temporal_cutoff is not None else discovery.temporal_cutoff,
        include_external=not no_external,
        include_local=not no_local,
        allow_status_transition=not no_status_transition,
    )

    if config.include_local and database is None:
        raise typer.BadParameter("--database is required unless --no-local is supplied")

    settings = LiteratureSettings()
    service = build_literature_service(settings) if config.include_external else None
    world = ScientificWorldModel(database) if config.include_local and database is not None else None

    try:
        verifier = AdversarialNoveltyVerifier(world=world, literature_service=service)
        report = verifier.verify_batch(discovery.candidates, config)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(report.model_dump_json(indent=2), encoding="utf-8")
        typer.echo(f"Wrote {len(report.results)} Phase 5 verification results to {output}")
    finally:
        if world is not None:
            world.close()
        if service is not None:
            service.close()


if __name__ == "__main__":
    app()
