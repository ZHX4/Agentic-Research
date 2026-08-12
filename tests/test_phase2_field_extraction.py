from agentic_research.intelligence.extraction import extract_fields
from agentic_research.schemas import Section, TextChunk


def test_fields_extract_candidate_entities_not_full_sentences() -> None:
    sections = [Section(section_id="s1", paper_id="p1", title="Methods", normalized_title="methods", level=1, order=0)]
    chunks = [
        TextChunk(
            chunk_id="c1",
            paper_id="p1",
            section_id="s1",
            section_title="Methods",
            text="We propose a Retrieval Fusion method using Hybrid Encoder. We evaluate on the WikiQA dataset.",
        )
    ]
    fields = extract_fields(chunks, sections)
    assert fields["methods"]
    assert all(len(value) < 120 for value in fields["methods"])
    assert all(value != chunks[0].text for value in fields["methods"])
