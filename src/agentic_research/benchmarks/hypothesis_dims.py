"""Seven-dimension hypothesis assessment (no overall quality score).

Records textual vs scientific diversity explicitly. The benchmark can
compare hypotheses per dimension but must not collapse them into an
artificial single score.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

DIMENSIONS: tuple[str, ...] = (
    "research_question_distinct",
    "causal_mechanism_distinct",
    "intervention_distinct",
    "design_controls_distinct",
    "falsification_criterion_distinct",
    "predicted_observations_distinct",
    "assumptions_identified",
)


class HypothesisDimensionRating(BaseModel):
    """Human rating of one hypothesis on the seven audit dimensions."""

    model_config = ConfigDict(extra="forbid")

    hypothesis_id: str = Field(min_length=1)
    annotator_id: str = Field(min_length=1)
    research_question_distinct: bool = False
    causal_mechanism_distinct: bool = False
    intervention_distinct: bool = False
    design_controls_distinct: bool = False
    falsification_criterion_distinct: bool = False
    predicted_observations_distinct: bool = False
    assumptions_identified: bool = False
    rationale: str = Field(min_length=1)
    textual_vs_scientific_note: str = Field(min_length=1)

    def distinct_count(self) -> int:
        return sum(
            [
                self.research_question_distinct,
                self.causal_mechanism_distinct,
                self.intervention_distinct,
                self.design_controls_distinct,
                self.falsification_criterion_distinct,
                self.predicted_observations_distinct,
                self.assumptions_identified,
            ]
        )
