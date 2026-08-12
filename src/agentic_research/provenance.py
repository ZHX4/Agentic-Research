"""Research provenance contracts.

The long-term system will store these edges in a durable provenance graph.
"""

from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, Field


class ProvenanceEdge(BaseModel):
    source_id: str
    target_id: str
    relation: Literal[
        "supports",
        "contradicts",
        "derived_from",
        "retrieved_for",
        "tested_by",
        "generated_from",
        "reviewed_by",
    ]
    agent: str
    confidence: float = Field(ge=0, le=1)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: dict[str, str] = Field(default_factory=dict)
