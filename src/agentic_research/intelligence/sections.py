"""Section detection and hierarchy reconstruction."""

from __future__ import annotations

import re

from agentic_research.intelligence.layout import TextBlock
from agentic_research.schemas.paper_intelligence import Section

_NUMBERED = re.compile(r"^(?P<num>\d+(?:\.\d+)*)[.)]?\s+(?P<title>.+)$")
_KNOWN = {
    "abstract",
    "introduction",
    "background",
    "related work",
    "literature review",
    "method",
    "methods",
    "methodology",
    "approach",
    "materials and methods",
    "experiments",
    "experimental setup",
    "results",
    "discussion",
    "conclusion",
    "conclusions",
    "limitations",
    "future work",
    "references",
    "appendix",
    "supplementary material",
}


def normalize_heading(title: str) -> str:
    title = re.sub(r"\s+", " ", title).strip().lower()
    title = re.sub(r"^\d+(?:\.\d+)*[.)]?\s*", "", title)
    return title


def heading_level(block: TextBlock, median_font_size: float) -> int | None:
    title = block.text.strip()
    normalized = normalize_heading(title)
    if not normalized or len(title) > 180 or title.endswith((".", ";", ",")):
        return None
    match = _NUMBERED.match(title)
    if normalized in _KNOWN:
        return 1
    if match:
        depth = len(match.group("num").split("."))
        return min(depth, 6)
    if block.bold and block.font_size >= median_font_size * 1.08 and len(title.split()) <= 12:
        return 1
    if block.font_size >= median_font_size * 1.18 and len(title.split()) <= 10:
        return 1
    return None


def detect_sections(paper_id: str, blocks: list[TextBlock]) -> list[Section]:
    """Create deterministic hierarchical sections from layout blocks.

    This is intentionally conservative: ambiguous lines remain body text.
    """
    if not blocks:
        return []
    sizes = sorted(block.font_size for block in blocks if block.font_size > 0)
    median = sizes[len(sizes) // 2] if sizes else 10.0
    sections: list[Section] = []
    stack: list[Section] = []

    for order, block in enumerate(blocks):
        level = heading_level(block, median)
        if level is None:
            continue
        while stack and stack[-1].level >= level:
            stack.pop()
        parent = stack[-1].section_id if stack else None
        section_id = f"sec-{paper_id}-{len(sections) + 1:04d}"
        section = Section(
            section_id=section_id,
            paper_id=paper_id,
            title=block.text,
            normalized_title=normalize_heading(block.text),
            level=level,
            order=order,
            parent_section_id=parent,
            page_start=block.page,
            page_end=block.page,
        )
        sections.append(section)
        stack.append(section)

    for index, section in enumerate(sections):
        next_page = blocks[0].page if index + 1 >= len(sections) else next(
            (b.page for b in blocks if b.text == sections[index + 1].title and b.page >= (section.page_start or 1)),
            section.page_start or 1,
        )
        section.page_end = max(section.page_start or 1, next_page)

    return sections


def assign_section(block: TextBlock, sections: list[Section]) -> Section | None:
    candidates = [
        section
        for section in sections
        if (section.page_start or 1) <= block.page
        and (section.page_end or section.page_start or 1) >= block.page
    ]
    if not candidates:
        return None
    return max(candidates, key=lambda section: section.order)
