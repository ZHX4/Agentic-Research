from pathlib import Path

from agentic_research.literature.fulltext import FullTextManifest
from agentic_research.literature.service import LiteratureService
from agentic_research.retrieval.contracts import LiteratureRetriever, SearchHit, SearchQuery
from agentic_research.schemas import GapCandidate, GapStatus, Paper
from agentic_research.schemas.phase3 import WorldNode
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
        for item in self.papers:
            text = f"{item.title} {item.abstract or ''} {' '.join(item.methods)} {' '.join(item.datasets)} {' '.join(item.tasks)}".casefold()
            if any(token.strip('"') in text for token in query_tokens if len(token.strip('"')) > 2):
                hits.append(SearchHit(paper=item, score=1.0, source=self.name))
        return hits[: query.limit]


class FakeFullTextAcquirer:
    def __init__(self, tmp_path: Path, html_by_paper: dict[str, str]) -> None:
        self.tmp_path = tmp_path
        self.html_by_paper = html_by_paper

    def acquire(self, paper: Paper) -> FullTextManifest:
        text = self.html_by_paper.get(paper.paper_id)
        if text is None:
            return FullTextManifest(
                paper_id=paper.paper_id,
                source="fake",
                requested_url="https://example.com/missing",
                media_type="unknown",
                status="not_found",
                error="No fixture",
            )
        path = self.tmp_path / f"{paper.paper_id}.html"
        path.write_text(f"<html><body><p>{text}</p></body></html>", encoding="utf-8")
        return FullTextManifest(
            paper_id=paper.paper_id,
            source="fake",
            requested_url="https://example.com/paper",
            final_url="https://example.com/paper",
            media_type="text/html",
            status="downloaded",
            local_path=str(path),
            sha256="a" * 64,
            byte_size=path.stat().st_size,
        )


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
    year: int | None = 2024,
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
    prior = paper(
        "prior",
        "Unrelated title wording",
        methods=["Method Alpha"],
        datasets=["Dataset Beta"],
        tasks=["Task Gamma"],
    )
    verifier = NoveltyVerifier(literature_service=LiteratureService([FakeRetriever([prior])]))

    result = verifier.verify(candidate(), NoveltyVerificationConfig(include_local=False, include_external=True))

    assert result.verdict == "disproved"
    assert result.resulting_status == GapStatus.DISPROVED
    assert result.prior_work[0].exact_combination
    assert result.counterevidence


def test_near_prior_work_weakens_candidate() -> None:
    prior = paper("near", "Method Alpha alternative evaluation", methods=["Method Alpha"], tasks=["Task Gamma"])
    verifier = NoveltyVerifier(literature_service=LiteratureService([FakeRetriever([prior])]))

    result = verifier.verify(
        candidate(),
        NoveltyVerificationConfig(include_local=False, include_external=True, near_match_similarity=0.20),
    )

    assert result.verdict in {"weakened", "disproved"}
    assert result.verified_candidate.status in {GapStatus.WEAKENED, GapStatus.DISPROVED}


def test_no_results_are_inconclusive_not_novel() -> None:
    verifier = NoveltyVerifier(literature_service=LiteratureService([FakeRetriever([])]))

    result = verifier.verify(candidate(), NoveltyVerificationConfig(include_local=False, include_external=True))

    assert result.verdict == "inconclusive"
    assert result.resulting_status == GapStatus.UNCERTAIN
    assert any("not evidence of novelty" in item for item in result.limitations)


def test_temporal_cutoff_excludes_future_and_unknown_year_prior_work() -> None:
    future = paper(
        "future", "Future", methods=["Method Alpha"], datasets=["Dataset Beta"], tasks=["Task Gamma"], year=2027
    )
    unknown = paper(
        "unknown", "Unknown year", methods=["Method Alpha"], datasets=["Dataset Beta"], tasks=["Task Gamma"], year=None
    )
    verifier = NoveltyVerifier(literature_service=LiteratureService([FakeRetriever([future, unknown])]))

    result = verifier.verify(
        candidate(),
        NoveltyVerificationConfig(include_local=False, external_results_per_query=10, temporal_cutoff=2025),
    )

    assert result.verdict == "inconclusive"
    assert not result.prior_work


def test_query_expansion_is_deterministic_and_bounded() -> None:
    verifier = NoveltyVerifier(literature_service=LiteratureService([FakeRetriever([])]))
    config = NoveltyVerificationConfig(include_local=False, max_queries_per_gap=4)
    first = verifier.verify(candidate(), config)
    second = verifier.verify(candidate(), config)

    assert [probe.query for probe in first.query_probes] == [probe.query for probe in second.query_probes]
    assert len(first.query_probes) <= 4
    assert first.verification_id == second.verification_id


def test_status_transition_can_be_disabled() -> None:
    prior = paper(
        "prior",
        "Prior",
        methods=["Method Alpha"],
        datasets=["Dataset Beta"],
        tasks=["Task Gamma"],
    )
    verifier = NoveltyVerifier(literature_service=LiteratureService([FakeRetriever([prior])]))

    result = verifier.verify(
        candidate(),
        NoveltyVerificationConfig(include_local=False, include_external=True, allow_status_transition=False),
    )

    assert result.verdict == "disproved"
    assert result.resulting_status == GapStatus.CANDIDATE
    assert result.verified_candidate.status == GapStatus.CANDIDATE


def test_batch_report_contains_only_candidate_inputs(tmp_path: Path) -> None:
    verifier = NoveltyVerifier(literature_service=LiteratureService([FakeRetriever([])]))
    result = verifier.verify_batch([candidate()], NoveltyVerificationConfig(include_local=False, include_external=True))

    assert result.input_candidate_count == 1
    assert len(result.results) == 1
    assert result.results[0].original_status == GapStatus.CANDIDATE


def test_local_world_model_exact_combination_disproves_candidate(tmp_path: Path) -> None:
    db = tmp_path / "world.sqlite"
    prior = paper(
        "prior",
        "Method Alpha Dataset Beta",
        methods=["Method Alpha"],
        datasets=["Dataset Beta"],
        tasks=["Task Gamma"],
    )
    with ScientificWorldModel(db) as world:
        world.upsert_paper(prior)
        world.upsert_node(WorldNode(node_id="paper:prior", node_type="paper", paper_id="prior", label=prior.title))
        world.upsert_chunk(
            chunk_id="chunk-prior",
            paper_id="prior",
            title=prior.title,
            text="Method Alpha evaluates Dataset Beta for Task Gamma.",
            section="Experiments",
            page_start=1,
            page_end=1,
            year=prior.year,
            source="local",
            vector=None,
            vector_model=None,
        )
        world.commit()
        verifier = NoveltyVerifier(world=world)
        result = verifier.verify(candidate(), NoveltyVerificationConfig(include_local=True, include_external=False, deep_verify=False))

    assert "local-world-model" in result.searched_sources
    assert result.verdict == "disproved"
    assert result.counterevidence


def test_external_fulltext_can_disprove_metadata_only_prior_work(tmp_path: Path) -> None:
    prior = paper("prior", "A differently titled study")
    acquirer = FakeFullTextAcquirer(
        tmp_path,
        {"prior": "We evaluate Method Alpha on Dataset Beta for Task Gamma in the experiments."},
    )
    verifier = NoveltyVerifier(
        literature_service=LiteratureService([FakeRetriever([prior])]),
        fulltext_acquirer=acquirer,
    )

    result = verifier.verify(
        candidate(),
        NoveltyVerificationConfig(
            include_local=False,
            include_external=True,
            deep_verify=True,
            max_deep_verifications=2,
            require_deep_verification_for_supported=True,
        ),
    )

    assert result.verdict == "disproved"
    assert any(check.status == "exact" and check.same_context_found for check in result.deep_evidence)
    assert result.prior_work[0].exact_combination


def test_missing_fulltext_prevents_supported_verdict(tmp_path: Path) -> None:
    prior = paper("prior", "Context only")
    acquirer = FakeFullTextAcquirer(tmp_path, {})
    verifier = NoveltyVerifier(
        literature_service=LiteratureService([FakeRetriever([prior])]),
        fulltext_acquirer=acquirer,
    )

    result = verifier.verify(
        candidate(),
        NoveltyVerificationConfig(
            include_local=False,
            include_external=True,
            deep_verify=True,
            max_deep_verifications=2,
            near_match_similarity=1.0,
            require_deep_verification_for_supported=True,
        ),
    )

    assert result.verdict == "inconclusive"
    assert any(check.status == "unavailable" for check in result.deep_evidence)
