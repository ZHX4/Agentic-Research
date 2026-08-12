"""Scientific decision policy layered on top of the Phase 5 search engine."""

from __future__ import annotations

from agentic_research.schemas.gap import GapCandidate, GapStatus
from agentic_research.schemas.phase5 import Counterevidence, GapVerificationResult, NoveltyVerificationConfig
from agentic_research.verification.novelty import NoveltyVerifier


def _world_key(value: str) -> str:
    return " ".join(value.casefold().split())


class AdversarialNoveltyVerifier(NoveltyVerifier):
    """Apply conservative decision rules to Phase 5 retrieval evidence."""

    def _local_exact_matches(self, candidate: GapCandidate, paper_ids: set[str]) -> set[str]:
        if self.world is None or not paper_ids:
            return set()
        methods: dict[str, set[str]] = {paper_id: set() for paper_id in paper_ids}
        datasets: dict[str, set[str]] = {paper_id: set() for paper_id in paper_ids}
        tasks: dict[str, set[str]] = {paper_id: set() for paper_id in paper_ids}
        field_map = {"has_method": methods, "has_dataset": datasets, "has_task": tasks}
        ordered_ids = sorted(paper_ids)
        placeholders = ",".join("?" for _ in ordered_ids)
        rows = self.world.connection.execute(
            f"""
            SELECT e.source_id, e.edge_type, n.label
            FROM edges e
            JOIN nodes n ON n.node_id=e.target_id
            WHERE e.source_id IN ({placeholders})
              AND e.edge_type IN ('has_method','has_dataset','has_task')
            ORDER BY e.source_id, e.edge_type, n.node_id
            """,
            ordered_ids,
        ).fetchall()
        for row in rows:
            paper_id = row["source_id"][len("paper:"):] if row["source_id"].startswith("paper:") else row["source_id"]
            if paper_id in paper_ids and row["edge_type"] in field_map:
                field_map[row["edge_type"]][paper_id].add(_world_key(row["label"]))
        candidate_method = _world_key(candidate.method or "")
        candidate_dataset = _world_key(candidate.dataset or "")
        candidate_task = _world_key(candidate.task or "")
        matches: set[str] = set()
        for paper_id in ordered_ids:
            if candidate_method and candidate_method not in methods[paper_id]:
                continue
            if candidate_dataset and candidate_dataset not in datasets[paper_id]:
                continue
            if candidate_task and candidate_task not in tasks[paper_id]:
                continue
            if candidate_method or candidate_dataset or candidate_task:
                matches.add(paper_id)
        return matches

    def verify(self, candidate: GapCandidate, config: NoveltyVerificationConfig | None = None) -> GapVerificationResult:
        cfg = config or NoveltyVerificationConfig()
        result = super().verify(candidate, cfg)
        prior_ids = {match.paper.paper_id for match in result.prior_work if match.source == "local-world-model"}
        local_exact = self._local_exact_matches(candidate, prior_ids)
        adjusted_matches = []
        exact_ids = set()
        for match in result.prior_work:
            if match.paper.paper_id in local_exact:
                adjusted = match.model_copy(
                    update={
                        "exact_combination": True,
                        "challenge_type": "direct",
                        "similarity": 1.0,
                        "rationale": "The local scientific world model explicitly contains the candidate method/dataset/task combination.",
                    }
                )
                adjusted_matches.append(adjusted)
                exact_ids.add(match.paper.paper_id)
            else:
                adjusted_matches.append(match)

        if not exact_ids:
            return result

        counterevidence = list(result.counterevidence)
        existing = {item.paper_id for item in counterevidence}
        for paper_id in sorted(exact_ids):
            if paper_id not in existing:
                counterevidence.append(
                    Counterevidence(
                        counterevidence_id=f"counter:{candidate.gap_id}:{paper_id}",
                        paper_id=paper_id,
                        source="local-world-model",
                        query="local-world-model graph exact-combination check",
                        claim="Exact method/dataset/task combination is present in the indexed world model.",
                        severity="high",
                        supports_gap=False,
                        rationale="Graph-level evidence directly contradicts the Phase 4 missing-combination candidate.",
                    )
                )

        confidence = min(0.99, max(result.confidence, 0.95))
        status = GapStatus.DISPROVED if cfg.allow_status_transition else GapStatus.CANDIDATE
        verified = result.verified_candidate.model_copy(
            update={
                "status": status,
                "confidence": confidence,
                "closest_prior_work_ids": [match.paper.paper_id for match in adjusted_matches[:10]],
                "counterevidence_ids": [item.counterevidence_id for item in counterevidence],
            }
        )
        return result.model_copy(
            update={
                "verdict": "disproved",
                "resulting_status": status,
                "confidence": confidence,
                "prior_work": adjusted_matches[:25],
                "counterevidence": counterevidence[:25],
                "nearest_prior_work_ids": [match.paper.paper_id for match in adjusted_matches[:10]],
                "rationale": "The local scientific world model explicitly contains the candidate combination; the candidate gap is therefore disproved within the indexed corpus.",
                "verified_candidate": verified,
            }
        )
