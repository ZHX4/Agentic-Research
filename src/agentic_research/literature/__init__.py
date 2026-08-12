"""Literature intelligence primitives and provider adapters."""

from .factory import build_literature_service
from .identity import canonical_identity, deduplicate_papers, normalize_arxiv_id, normalize_doi
from .service import LiteratureService
from .settings import LiteratureSettings
from .transport import HttpClient, RateLimiter, RetryPolicy

__all__ = [
    "HttpClient",
    "LiteratureService",
    "LiteratureSettings",
    "RateLimiter",
    "RetryPolicy",
    "build_literature_service",
    "canonical_identity",
    "deduplicate_papers",
    "normalize_arxiv_id",
    "normalize_doi",
]
