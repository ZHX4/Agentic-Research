"""PEFT-30 annotation schemas and double-annotation workflow.

Labels are fixed vocabularies from the validation protocol. The
adjudicated record preserves A, B, disagreement, adjudication, final
label, and dissent note -- the final label never overwrites the
independent ratings.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

GapLabel = Literal[
    "valid_opportunity",
    "already_addressed",
    "partially_addressed",
    "ambiguous",
    "unsupported",
]

NoveltyLabel = Literal[
    "direct_prior",
    "near_equivalent",
    "related_not_disqualifying",
    "no_disqualifying_found",
    "insufficient_evidence",
]

GAP_LABELS: tuple[str, ...] = (
    "valid_opportunity",
    "already_addressed",
    "partially_addressed",
    "ambiguous",
    "unsupported",
)

NOVELTY_LABELS: tuple[str, ...] = (
    "direct_prior",
    "near_equivalent",
    "related_not_disqualifying",
    "no_disqualifying_found",
    "insufficient_evidence",
)


class SingleAnnotation(BaseModel):
    """One independent rating by one annotator."""

    model_config = ConfigDict(extra="forbid")

    case_id: str = Field(min_length=1)
    annotator_id: str = Field(min_length=1)
    label: str = Field(min_length=1)
    evidence_refs: list[str] = Field(default_factory=list)
    quoted_passages: list[str] = Field(default_factory=list)
    rationale: str = Field(min_length=1)
    source_paper_ids: list[str] = Field(default_factory=list)
    temporal_context: str = Field(min_length=1)
    confidence: float | None = Field(default=None, ge=0, le=1)


class AdjudicatedAnnotation(BaseModel):
    """Preserved double-annotation trail plus adjudication."""

    model_config = ConfigDict(extra="forbid")

    case_id: str = Field(min_length=1)
    kind: Literal["gap", "novelty"] = "gap"
    annotation_a: SingleAnnotation
    annotation_b: SingleAnnotation
    disagreement: bool = False
    adjudicator_id: str = Field(min_length=1)
    adjudicated_label: str = Field(min_length=1)
    final_label: str = Field(min_length=1)
    dissent_note: str | None = None

    @model_validator(mode="after")
    def validate_trail(self) -> AdjudicatedAnnotation:
        ids = {self.annotation_a.case_id, self.annotation_b.case_id, self.case_id}
        if len(ids) != 1:
            raise ValueError("All case_id values must match")
        if self.annotation_a.annotator_id == self.annotation_b.annotator_id:
            raise ValueError("Annotations A and B require distinct annotators")
        expected_disagreement = self.annotation_a.label != self.annotation_b.label
        if self.disagreement != expected_disagreement:
            raise ValueError("disagreement flag must match A/B label equality")
        allowed = GAP_LABELS if self.kind == "gap" else NOVELTY_LABELS
        for label in (
            self.annotation_a.label,
            self.annotation_b.label,
            self.adjudicated_label,
            self.final_label,
        ):
            if label not in allowed:
                raise ValueError(f"Label {label!r} not allowed for kind {self.kind!r}")
        return self


def build_adjudicated(
    annotation_a: SingleAnnotation,
    annotation_b: SingleAnnotation,
    *,
    kind: Literal["gap", "novelty"],
    adjudicator_id: str,
    adjudicated_label: str,
    dissent_note: str | None = None,
) -> AdjudicatedAnnotation:
    return AdjudicatedAnnotation(
        case_id=annotation_a.case_id,
        kind=kind,
        annotation_a=annotation_a,
        annotation_b=annotation_b,
        disagreement=annotation_a.label != annotation_b.label,
        adjudicator_id=adjudicator_id,
        adjudicated_label=adjudicated_label,
        final_label=adjudicated_label,
        dissent_note=dissent_note,
    )
