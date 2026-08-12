"""Literature intelligence primitives and provider adapters."""

from .identity import canonical_identity, deduplicate_papers, normalize_arxiv_id, normalize_doi
from .transport import HttpClient, RetryPolicy, RateLimiter

__all__ = [
    "HttpClient",
    "RateLimiter",
    "RetryPolicy",
    "canonical_identity",
    "deduplicate_papers",
    "normalize_arxiv_id",
    "normalize_doi",
]
