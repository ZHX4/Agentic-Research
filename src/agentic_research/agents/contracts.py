"""Stable interfaces for long-running research agents."""

from abc import ABC, abstractmethod
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class AgentContext(BaseModel):
    model_config = ConfigDict(extra="allow")

    run_id: str
    research_goal: str
    inputs: dict[str, Any] = Field(default_factory=dict)
    evidence_ids: list[str] = Field(default_factory=list)


class AgentResult(BaseModel):
    model_config = ConfigDict(extra="allow")

    agent: str
    status: str
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
