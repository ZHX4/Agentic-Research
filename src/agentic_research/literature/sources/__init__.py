"""Literature source adapters."""

from .arxiv import ArxivAdapter
from .openalex import OpenAlexAdapter
from .semantic_scholar import SemanticScholarAdapter

__all__ = ["ArxivAdapter", "OpenAlexAdapter", "SemanticScholarAdapter"]
