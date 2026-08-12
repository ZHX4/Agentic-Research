"""Stable interfaces for long-running research agents."""

from abc import ABC, abstractmethod
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class AgentContext(BaseModel):
    """Structured state supplied to an agent."""

    model_config = ConfigDict(extra="forbid")

    run_id: str = Field(min_length=1)
    research_goal: str = Field(min_length=1)
    inputs: dict[str, Any] = Field(default_factory=dict)
    evidence_ids: list[str] = Field(default_factory=list)


class AgentResult(BaseModel):
    """Structured result returned by an agent."""

    model_config = ConfigDict(extra="forbid")

    agent: str = Field(min_length=1)
    status: str = Field(min_length=1)
    outputs: dict[str, Any] = Field(default_factory=dict)
    evidence_ids: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class ResearchAgent(ABC):
    """Framework-independent agent contract.

    Agents consume structured state and return structured state. Free-form chat
    between agents is deliberately not part of the core contract.
    """

    name: str

    @abstractmethod
    def run(self, context: AgentContext) -> AgentResult:
        raise NotImplementedError
