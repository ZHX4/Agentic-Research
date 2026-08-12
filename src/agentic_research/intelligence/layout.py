"""Layout-aware PDF primitives for scientific paper reconstruction."""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import fitz

from agentic_research.schemas.paper_intelligence import BoundingBox, FigureRecord, TableRecord


@dataclass(frozen=True)
class TextBlock:
    block_id: str
    page: int
    bbox: BoundingBox
    text: str
    font_size: float
    bold: bool
    block_type: str = "text"


def _bbox(values: tuple[float, float, float, float]) -> BoundingBox:
    return BoundingBox(x0=values[0], y0=values[1], x1=values[2], y1=values[3])


def iter_text_blocks(path: Path) -> list[TextBlock]:
    """Extract ordered text blocks with layout metadata from a PDF."""
    blocks: list[TextBlock] = []
    with fitz.open(path) as document:
        for page_index, page in enumerate(document):
            payload: dict[str, Any] = page.get_text("dict", sort=True)
            for block_index, raw in enumerate(payload.get("blocks", [])):
                if raw.get("type") != 0:
                    continue
                lines = raw.get("lines", [])
                text_parts: list[str] = []
                sizes: list[float] = []
                bold = False
                for line in lines:
                    for span in line.get("spans", []):
                        value = str(span.get("text", ""))
                        if value.strip():
                            text_parts.append(value)
                            sizes.append(float(span.get("size", 0.0)))
                            font = str(span.get("font", "")).lower()
                            if "bold" in font or "black" in font:
                                bold = True
                text = " ".join("".join(text_parts).split())
                if not text:
                    continue
                digest = hashlib.sha1(
                    f"{page_index + 1}|{block_index}|{raw.get('bbox')}|{text}".encode("utf-8")
                ).hexdigest()[:16]
                blocks.append(
                    TextBlock(
                        block_id=f"b-{digest}",
                        page=page_index + 1,
                        bbox=_bbox(tuple(raw.get("bbox", (0, 0, 0, 0)))),
                        text=text,
                        font_size=max(sizes, default=0.0),
                        bold=bold,
                    )
                )
    return blocks


def extract_tables(path: Path, paper_id: str) -> list[TableRecord]:
    """Extract native PDF tables using PyMuPDF's current table detector."""
    tables: list[TableRecord] = []
    with fitz.open(path) as document:
        for page_index, page in enumerate(document):
            try:
                finder = page.find_tables()
            except (AttributeError, RuntimeError, ValueError):
                continue
            for index, table in enumerate(finder.tables):
                rows = [[str(cell or "").strip() for cell in row] for row in table.extract()]
                if not rows:
                    continue
                digest = hashlib.sha1(
                    f"{paper_id}|{page_index + 1}|{index}|{rows}".encode("utf-8")
                ).hexdigest()[:16]
                markdown = _table_to_markdown(rows)
                tables.append(
                    TableRecord(
                        table_id=f"tbl-{digest}",
                        paper_id=paper_id,
                        page=page_index + 1,
                        bbox=_bbox(tuple(table.bbox)),
                        rows=rows,
                        markdown=markdown,
                        extraction_confidence=_table_confidence(rows),
                    )
                )
    return tables


def extract_figures(path: Path, paper_id: str) -> list[FigureRecord]:
    """Extract embedded image occurrences and nearby figure captions."""
    figures: list[FigureRecord] = []
    with fitz.open(path) as document:
        for page_index, page in enumerate(document):
            image_infos = page.get_image_info(hashes=True, xrefs=True)
            if not image_infos:
                continue
            text_blocks = iter_page_blocks(page)
            for index, image in enumerate(image_infos):
                rects = page.get_image_rects(image.get("xref", 0)) if image.get("xref") else []
                bbox_values = tuple(rects[0]) if rects else tuple(image.get("bbox", (0, 0, 0, 0)))
                caption = _nearest_caption(text_blocks, bbox_values)
                digest_bytes = image.get("digest")
                digest = digest_bytes.hex() if isinstance(digest_bytes, bytes) else None
                identity = hashlib.sha1(
                    f"{paper_id}|{page_index + 1}|{index}|{digest}|{bbox_values}".encode("utf-8")
                ).hexdigest()[:16]
                figures.append(
                    FigureRecord(
                        figure_id=f"fig-{identity}",
                        paper_id=paper_id,
                        page=page_index + 1,
                        bbox=_bbox(bbox_values),
                        image_digest=digest,
                        image_xref=image.get("xref"),
                        caption=caption,
                        extraction_confidence=0.92 if caption else 0.75,
                    )
                )
    return figures


def iter_page_blocks(page: fitz.Page) -> list[TextBlock]:
    payload: dict[str, Any] = page.get_text("dict", sort=True)
    blocks: list[TextBlock] = []
    for block_index, raw in enumerate(payload.get("blocks", [])):
        if raw.get("type") != 0:
            continue
        parts: list[str] = []
        sizes: list[float] = []
        for line in raw.get("lines", []):
            for span in line.get("spans", []):
                text = str(span.get("text", ""))
                if text.strip():
                    parts.append(text)
                    sizes.append(float(span.get("size", 0.0)))
        text = " ".join("".join(parts).split())
        if not text:
            continue
        blocks.append(
            TextBlock(
                block_id=f"p{page.number + 1}-b{block_index}",
                page=page.number + 1,
                bbox=_bbox(tuple(raw.get("bbox", (0, 0, 0, 0)))),
                text=text,
                font_size=max(sizes, default=0.0),
                bold=False,
            )
        )
    return blocks


def _nearest_caption(blocks: list[TextBlock], image_bbox: tuple[float, float, float, float]) -> str | None:
    x0, y0, x1, y1 = image_bbox
    candidates: list[tuple[float, str]] = []
    for block in blocks:
        text = block.text
        if not re.match(r"^(figure|fig\.)\s*\d+\b", text, flags=re.IGNORECASE):
            continue
        distance = min(abs(block.bbox.y0 - y1), abs(y0 - block.bbox.y1)) + abs(block.bbox.x0 - x0) * 0.05
        if distance < 120:
            candidates.append((distance, text))
    return min(candidates, default=(0, None), key=lambda item: item[0])[1]


def _table_to_markdown(rows: list[list[str]]) -> str:
    if not rows:
        return ""
    width = max(len(row) for row in rows)
    normalized = [row + [""] * (width - len(row)) for row in rows]
    lines = ["| " + " | ".join(normalized[0]) + " |", "| " + " | ".join(["---"] * width) + " |"]
    lines.extend("| " + " | ".join(row) + " |" for row in normalized[1:])
    return "\n".join(lines)


def _table_confidence(rows: list[list[str]]) -> float:
    if not rows:
        return 0.0
    widths = {len(row) for row in rows}
    nonempty = sum(bool(cell.strip()) for row in rows for cell in row)
    total = sum(len(row) for row in rows)
    regularity = 1.0 if len(widths) == 1 else 0.65
    density = nonempty / total if total else 0.0
    return round(min(1.0, 0.55 * regularity + 0.45 * density), 3)
