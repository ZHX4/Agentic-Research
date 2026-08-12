from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from agentic_research.provenance import ProvenanceEdge


def test_provenance_edge_accepts_known_relation() -> None:
    created_at = datetime.now(timezone.utc)
    edge = ProvenanceEdge(
        source_id="paper:p1",
        target_id="claim:c1",
        relation="supports",
        agent="paper-analyzer",
        confidence=0.9,
        created_at=created_at,
    )

    assert edge.relation == "supports"
    assert edge.created_at == created_at


def test_provenance_edge_rejects_unknown_relation() -> None:
    with pytest.raises(ValidationError):
        ProvenanceEdge(
            source_id="paper:p1",
            target_id="claim:c1",
            relation="invented_relation",
            agent="paper-analyzer",
            confidence=0.9,
        )
