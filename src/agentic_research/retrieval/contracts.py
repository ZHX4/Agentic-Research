"""Stable contracts for scientific retrieval providers."""

from abc import ABC, abstractmethod

from pydantic import BaseModel, Field, model_validator

from agentic_research.schemas import Paper


class SearchQuery(BaseModel):
    text: str = Field(min_length=1)
    year_from: int | None = Field(default=None, ge=1900, le=2200)
    year_to: int | None = Field(default=None, ge=1900, le=2200)
    limit: int = Field(default=20, ge=1, le=1000)
    temporal_cutoff: int | None = Field(default=None, ge=1900, le=2200)

    @model_validator(mode="after")
    def validate_year_window(self) -> "SearchQuery":
        if self.year_from is not None and self.year_to is not None:
            if self.year_from > self.year_to:
                raise ValueError("year_from must be less than or equal to year_to")
        if self.temporal_cutoff is not None:
            if self.year_from is not None and self.year_from > self.temporal_cutoff:
                raise ValueError("year_from cannot exceed temporal_cutoff")
            if self.year_to is not None and self.year_to > self.temporal_cutoff:
                raise ValueError("year_to cannot exceed temporal_cutoff")
        return self


class SearchHit(BaseModel):
    paper: Paper
    score: float = Field(ge=0)
    source: str = Field(min_length=1)
    retrieval_reason: str | None = None


class LiteratureRetriever(ABC):
    name: str

    @abstractmethod
    def search(self, query: SearchQuery) -> list[SearchHit]:
        raise NotImplementedError
