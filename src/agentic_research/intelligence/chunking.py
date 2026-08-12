"""Section-aware deterministic chunking."""

from __future__ import annotations

import hashlib
import re

from agentic_research.intelligence.layout import TextBlock
from agentic_research.intelligence.sections import assign_section
from agentic_research.schemas.paper_intelligence import Section, TextChunk

_SENTENCE = re.compile(r"(?<=[.!?])\s+(?=[A-Z0-9(])")


def _sentences(text: str) -> list[str]:
    clean = re.sub(r"\s+", " ", text).strip()
    if not clean:
        return []
    return [part.strip() for part in _SENTENCE.split(clean) if part.strip()]


def chunk_blocks(
    paper_id: str,
    blocks: list[TextBlock],
    sections: list[Section],
    *,
    target_chars: int = 1800,
    max_chars: int = 2600,
) -> list[TextChunk]:
    if target_chars < 200 or max_chars < target_chars:
        raise ValueError("max_chars must be >= target_chars >= 200")

    chunks: list[TextChunk] = []
    buffer: list[TextBlock] = []
    size = 0

    def flush() -> None:
        nonlocal buffer, size
        if not buffer:
            return
        text_parts: list[str] = []
        for block in buffer:
            if text_parts:
                text_parts.append("\n\n")
            text_parts.append(block.text)
        text = "".join(text_parts).strip()
        if not text:
            buffer = []
            size = 0
            return
        section = assign_section(buffer[0], sections)
        digest = hashlib.sha1(
            f"{paper_id}|{buffer[0].block_id}|{buffer[-1].block_id}|{text}".encode("utf-8")
        ).hexdigest()[:16]
        chunks.append(
            TextChunk(
                chunk_id=f"chunk-{digest}",
                paper_id=paper_id,
                section_id=section.section_id if section else None,
                section_title=section.title if section else None,
                text=text,
                page_start=buffer[0].page,
                page_end=buffer[-1].page,
                block_ids=[block.block_id for block in buffer],
            )
        )
        buffer = []
        size = 0

    previous_section_id: str | None = None
    for block in blocks:
        section = assign_section(block, sections)
        current_section_id = section.section_id if section else None
        if buffer and current_section_id != previous_section_id:
            flush()
        for sentence in _sentences(block.text) or [block.text]:
            sentence_len = len(sentence)
            if buffer and size + sentence_len + 2 > max_chars:
                flush()
            if not buffer and sentence_len > max_chars:
                start = 0
                while start < sentence_len:
                    end = min(start + max_chars, sentence_len)
                    piece = sentence[start:end].strip()
                    if piece:
                        synthetic = TextBlock(
                            block_id=f"{block.block_id}:{start}",
                            page=block.page,
                            bbox=block.bbox,
                            text=piece,
                            font_size=block.font_size,
                            bold=block.bold,
                        )
                        buffer.append(synthetic)
                        size = len(piece)
                        flush()
                    start = end
                previous_section_id = current_section_id
                continue
            synthetic = TextBlock(
                block_id=block.block_id,
                page=block.page,
                bbox=block.bbox,
                text=sentence,
                font_size=block.font_size,
                bold=block.bold,
            )
            buffer.append(synthetic)
            size += sentence_len + 2
            previous_section_id = current_section_id
            if size >= target_chars:
                flush()
    flush()
    return chunks
