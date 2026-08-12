"""Stable contracts for scientific retrieval providers."""

from abc import ABC, abstractmethod

from pydantic import BaseModel, Field

from agentic_research.schemas import Paper


class SearchQuery(BaseModel):
    text: str
    year_from: int | None = Field(default=None, ge=1900, le=2200)
    year_to: int | None = Field(default=None, ge=1900, le=2200)
    limit: int = Field(default=20, ge=1, le=1000)
    temporal_cutoff: int | None = Field(default=None, ge=1900, le=2200)


class SearchHit(BaseModel):
    paper: Paper
    score: float = Field(ge=0)
    source: str
    retrieval_reason: str | None = None


class LiteratureRetriever(ABC):
    name: str

    @abstractmethod
    def search(self, query: SearchQuery) -> list[SearchHit]:
        raise NotImplementedError
