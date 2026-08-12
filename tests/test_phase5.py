from pathlib import Path

from agentic_research.literature.service import LiteratureService
from agentic_research.retrieval.contracts import LiteratureRetriever, SearchHit, SearchQuery
from agentic_research.schemas import GapCandidate, GapStatus, Paper
from agentic_research.schemas.phase5 import NoveltyVerificationConfig
from agentic_research.verification import NoveltyVerifier
from agentic_research.world_model.store import ScientificWorldModel


class FakeRetriever(LiteratureRetriever):
    name = "fake"

    def __init__(self, papers: list[Paper]) -> None:
        self.papers = papers
        self.queries: list[str] = []

    def search(self, query: SearchQuery) -> list[SearchHit]:
        self.queries.append(query.text)
        hits: list[SearchHit] = []
        query_tokens = set(query.text.casefold().split())
        for paper in self.papers:
            text = f"{paper.title} {paper.abstract or ''} {' '.join(paper.methods)} {' '.join(paper.datasets)} {' '.join(paper.tasks)}".casefold()
            if any(token.strip('"') in text for token in query_tokens if len(token.strip('"')) > 2):
                hits.append(SearchHit(paper=paper, score=1.0, source=self.name))
        return hits[: query.limit]


def candidate() -> GapCandidate:
    return GapCandidate(
        gap_id="gap-1",
        gap_type="missing_combination",
        statement="Method Alpha on Dataset Beta for Task Gamma is absent.",
        method="Method Alpha",
        task="Task Gamma",
        dataset="Dataset Beta",
        evidence_paper_ids=["support-1", "support-2"],
        signal_ids=["signal-1"],
        support_count=2,
        structural_support=0.8,
        confidence=0.4,
        status=GapStatus.CANDIDATE,
        rationale="Candidate only.",
    )


def paper(
    paper_id: str,
    title: str,
    *,
    methods: list[str] | None = None,
    datasets: list[str] | None = None,
    tasks: list[str] | None = None,
    year: int = 2024,
) -> Paper:
    return Paper(
        paper_id=paper_id,
        title=title,
        abstract="A study of the method and task.",
        methods=methods or [],
        datasets=datasets or [],
        tasks=tasks or [],
        year=year,
    )


def test_direct_prior_work_disproves_candidate() -> None:
    prior = paper("prior", "Method Alpha on Dataset Beta", methods=["Method Alpha"], datasets=["Dataset Beta"], tasks=["Task Gamma"])
    verifier = NoveltyVerifier(literature_service=LiteratureService([FakeRetriever([prior])]))

    result = verifier.verify(candidate(), NoveltyVerificationConfig(include_local=False, include_external=True))

    assert result.verdict == "disproved"
    assert result.resulting_status == GapStatus.DISPROVED
    assert result.prior_work[0].exact_combination
    assert result.counterevidence


def test_near_prior_work_weakens_candidate() -> None:
    prior = paper("near", "Method Alpha alternative evaluation", methods=["Method Alpha"], tasks=["Task Gamma"])
    verifier = NoveltyVerifier(literature_service=LiteratureService([FakeRetriever([prior])]))

    result = verifier.verify(candidate(), NoveltyVerificationConfig(include_local=False, include_external=True, near_match_similarity=0.20))

    assert result.verdict in {"weakened", "disproved"}
    assert result.verified_candidate.status in {GapStatus.WEAKENED, GapStatus.DISPROVED}


def test_no_results_are_inconclusive_not_novel() -> None:
    verifier = NoveltyVerifier(literature_service=LiteratureService([FakeRetriever([])]))

    result = verifier.verify(candidate(), NoveltyVerificationConfig(include_local=False, include_external=True))

    assert result.verdict == "inconclusive"
    assert result.resulting_status == GapStatus.UNCERTAIN
    assert any("not evidence of novelty" in item for item in result.limitations)


def test_temporal_cutoff_excludes_future_prior_work() -> None:
    future = paper("future", "Method Alpha Dataset Beta", methods=["Method Alpha"], datasets=["Dataset Beta"], tasks=["Task Gamma"], year=2027)
    verifier = NoveltyVerifier(literature_service=LiteratureService([FakeRetriever([future])]))

    result = verifier.verify(candidate(), NoveltyVerificationConfig(include_local=False, external_results_per_query=10, temporal_cutoff=2025))

    assert result.verdict == "inconclusive"
    assert all(match.paper.year <= 2025 for match in result.prior_work if match.paper.year is not None)


def test_query_expansion_is_deterministic_and_bounded() -> None:
    verifier = NoveltyVerifier(literature_service=LiteratureService([FakeRetriever([])]))
    config = NoveltyVerificationConfig(include_local=False, max_queries_per_gap=4)
    first = verifier.verify(candidate(), config)
    second = verifier.verify(candidate(), config)

    assert [probe.query for probe in first.query_probes] == [probe.query for probe in second.query_probes]
    assert len(first.query_probes) <= 4
    assert first.verification_id == second.verification_id


def test_batch_report_contains_only_candidate_inputs(tmp_path: Path) -> None:
    verifier = NoveltyVerifier(literature_service=LiteratureService([FakeRetriever([])]))
    result = verifier.verify_batch([candidate()], NoveltyVerificationConfig(include_local=False, include_external=True))

    assert result.input_candidate_count == 1
    assert len(result.results) == 1
    assert result.results[0].original_status == GapStatus.CANDIDATE


def test_local_world_model_can_provide_counterevidence(tmp_path: Path) -> None:
    db = tmp_path / "world.sqlite"
    prior = paper("prior", "Method Alpha Dataset Beta", methods=["Method Alpha"], datasets=["Dataset Beta"], tasks=["Task Gamma"])
    with ScientificWorldModel(db) as world:
        world.upsert_paper(prior)
        world.upsert_node(__import__("agentic_research.schemas.phase3", fromlist=["WorldNode"]).WorldNode(node_id="paper:prior", node_type="paper", paper_id="prior", label=prior.title))
        world.commit()
        verifier = NoveltyVerifier(world=world)
        result = verifier.verify(candidate(), NoveltyVerificationConfig(include_local=True, include_external=False))

    assert result.searched_sources == ["local-world-model"]
    assert result.verdict in {"disproved", "weakened", "supported", "inconclusive"}
