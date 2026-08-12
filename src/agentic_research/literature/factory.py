"""Factory helpers for configured Phase 1 source adapters."""

from agentic_research.literature.service import LiteratureService
from agentic_research.literature.settings import LiteratureSettings
from agentic_research.literature.sources import ArxivAdapter, OpenAlexAdapter, SemanticScholarAdapter


def build_literature_service(settings: LiteratureSettings | None = None) -> LiteratureService:
    settings = settings or LiteratureSettings()
    adapters = []
    if settings.openalex_api_key:
        adapters.append(
            OpenAlexAdapter(
                api_key=settings.openalex_api_key,
                min_interval_seconds=settings.openalex_min_interval_seconds,
            )
        )
    adapters.append(
        SemanticScholarAdapter(
            api_key=settings.semantic_scholar_api_key,
            min_interval_seconds=settings.semantic_scholar_min_interval_seconds,
        )
    )
    adapters.append(ArxivAdapter(min_interval_seconds=settings.arxiv_min_interval_seconds))
    return LiteratureService(adapters)
