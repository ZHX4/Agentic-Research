"""CLI for Phase 5 adversarial gap verification."""

from __future__ import annotations

from pathlib import Path

import typer

from agentic_research.literature.factory import build_literature_service
from agentic_research.literature.fulltext import FullTextAcquirer
from agentic_research.literature.settings import LiteratureSettings
from agentic_research.literature.transport import HttpClient, RateLimiter
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
    deep_verify: bool = typer.Option(True, help="Perform bounded full-text verification of top prior works."),
    max_deep_verifications: int = typer.Option(5, min=0, max=25),
    require_deep_verification_for_supported: bool = typer.Option(True, help="Require at least one successful full-text check before a supported verdict."),
    deep_verification_similarity_floor: float = typer.Option(0.45, min=0, max=1),
    fulltext_cache_dir: Path = typer.Option(Path("artifacts/phase5-fulltext"), help="Cache directory for bounded prior-work full text."),
    no_external: bool = typer.Option(False, help="Disable configured external scholarly providers."),
    no_local: bool = typer.Option(False, help="Disable local world-model search."),
    no_status_transition: bool = typer.Option(False, help="Keep candidates at status=candidate even after verification."),
) -> None:
    """Challenge Phase 4 candidates against configured literature sources and bounded full text."""
    if not no_local and database is None:
        raise typer.BadParameter("--database is required unless --no-local is supplied")

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
        deep_verify=deep_verify,
        max_deep_verifications=max_deep_verifications,
        require_deep_verification_for_supported=require_deep_verification_for_supported,
        deep_verification_similarity_floor=deep_verification_similarity_floor,
    )

    settings = LiteratureSettings()
    service = build_literature_service(settings) if config.include_external else None
    world = ScientificWorldModel(database) if config.include_local and database is not None else None
    fulltext_client: HttpClient | None = None
    fulltext_acquirer: FullTextAcquirer | None = None
    if config.deep_verify:
        fulltext_client = HttpClient(
            user_agent=settings.user_agent,
            timeout_seconds=settings.request_timeout_seconds,
            rate_limiter=RateLimiter(settings.fulltext_min_interval_seconds),
        )
        fulltext_acquirer = FullTextAcquirer(client=fulltext_client, output_dir=fulltext_cache_dir)

    try:
        verifier = AdversarialNoveltyVerifier(
            world=world,
            literature_service=service,
            fulltext_acquirer=fulltext_acquirer,
        )
        report = verifier.verify_batch(discovery.candidates, config)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(report.model_dump_json(indent=2), encoding="utf-8")
        typer.echo(f"Wrote {len(report.results)} Phase 5 verification results to {output}")
    finally:
        if fulltext_client is not None:
            fulltext_client.close()
        if world is not None:
            world.close()
        if service is not None:
            service.close()


if __name__ == "__main__":
    app()
