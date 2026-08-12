import pytest
from pydantic import ValidationError

from agentic_research.agents.contracts import AgentContext, AgentResult
from agentic_research.retrieval.contracts import SearchQuery


def test_agent_context_is_structured() -> None:
    context = AgentContext(run_id="run-1", research_goal="Find gaps")
    assert context.inputs == {}
    assert context.evidence_ids == []

    with pytest.raises(ValidationError):
        AgentContext.model_validate(
            {"run_id": "run-1", "research_goal": "Find gaps", "unexpected": True}
        )


def test_agent_result_is_structured() -> None:
    result = AgentResult(agent="gap-hunter", status="ok")
    assert result.outputs == {}

    with pytest.raises(ValidationError):
        AgentResult.model_validate(
            {"agent": "gap-hunter", "status": "ok", "unexpected": True}
        )


def test_search_query_defaults_and_bounds() -> None:
    query = SearchQuery(text="retrieval")
    assert query.limit == 20

    with pytest.raises(ValidationError):
        SearchQuery(text="retrieval", limit=0)

    with pytest.raises(ValidationError):
        SearchQuery(text="retrieval", limit=1001)


def test_search_query_year_invariants() -> None:
    with pytest.raises(ValidationError):
        SearchQuery(text="x", year_from=2025, year_to=2024)

    with pytest.raises(ValidationError):
        SearchQuery(text="x", year_from=2025, temporal_cutoff=2024)

    with pytest.raises(ValidationError):
        SearchQuery(text="x", year_to=2025, temporal_cutoff=2024)
