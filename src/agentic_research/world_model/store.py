"""Persistent SQLite scientific world model for Phase 3."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Iterable

from agentic_research.schemas import Evidence, Paper
from agentic_research.schemas.paper_intelligence import StructuredExtraction
from agentic_research.schemas.phase3 import TraversalResult, WorldEdge, WorldNode

_SCHEMA = """
PRAGMA foreign_keys=ON;
CREATE TABLE IF NOT EXISTS papers (
  paper_id TEXT PRIMARY KEY,
  title TEXT NOT NULL,
  year INTEGER,
  source TEXT,
  doi TEXT,
  arxiv_id TEXT,
  metadata_json TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS nodes (
  node_id TEXT PRIMARY KEY,
  node_type TEXT NOT NULL,
  paper_id TEXT,
  label TEXT NOT NULL,
  payload_json TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS edges (
  edge_id TEXT PRIMARY KEY,
  source_id TEXT NOT NULL,
  target_id TEXT NOT NULL,
  edge_type TEXT NOT NULL,
  payload_json TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS chunks (
  chunk_id TEXT PRIMARY KEY,
  paper_id TEXT NOT NULL,
  title TEXT NOT NULL,
  text TEXT NOT NULL,
  section TEXT,
  page_start INTEGER,
  page_end INTEGER,
  year INTEGER,
  source TEXT,
  vector BLOB,
  vector_dim INTEGER
);
CREATE VIRTUAL TABLE IF NOT EXISTS chunks_fts USING fts5(
  chunk_id UNINDEXED,
  paper_id UNINDEXED,
  text,
  section,
  title,
  tokenize='unicode61'
);
CREATE INDEX IF NOT EXISTS idx_chunks_paper ON chunks(paper_id);
CREATE INDEX IF NOT EXISTS idx_nodes_paper ON nodes(paper_id);
CREATE INDEX IF NOT EXISTS idx_edges_source ON edges(source_id);
CREATE INDEX IF NOT EXISTS idx_edges_target ON edges(target_id);
CREATE INDEX IF NOT EXISTS idx_chunks_year ON chunks(year);
"""


class ScientificWorldModel:
    """SQLite-backed graph plus searchable chunk store."""

    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.connection = sqlite3.connect(self.path)
        self.connection.row_factory = sqlite3.Row
        try:
            self.connection.executescript(_SCHEMA)
        except sqlite3.DatabaseError as exc:
            self.connection.close()
            raise RuntimeError("SQLite FTS5 is required for the Phase 3 world model") from exc

    def close(self) -> None:
        self.connection.close()

    def __enter__(self) -> "ScientificWorldModel":
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    def upsert_paper(self, paper: Paper) -> None:
        source = str(paper.metadata.get("source")) if paper.metadata.get("source") else None
        self.connection.execute(
            """INSERT INTO papers(paper_id,title,year,source,doi,arxiv_id,metadata_json)
               VALUES(?,?,?,?,?,?,?)
               ON CONFLICT(paper_id) DO UPDATE SET title=excluded.title,year=excluded.year,
               source=excluded.source,doi=excluded.doi,arxiv_id=excluded.arxiv_id,metadata_json=excluded.metadata_json""",
            (paper.paper_id, paper.title, paper.year, source, paper.doi, paper.arxiv_id, json.dumps(paper.metadata, ensure_ascii=False)),
        )

    def upsert_node(self, node: WorldNode) -> None:
        self.connection.execute(
            """INSERT INTO nodes(node_id,node_type,paper_id,label,payload_json) VALUES(?,?,?,?,?)
               ON CONFLICT(node_id) DO UPDATE SET node_type=excluded.node_type,paper_id=excluded.paper_id,
               label=excluded.label,payload_json=excluded.payload_json""",
            (node.node_id, node.node_type, node.paper_id, node.label, json.dumps(node.payload, ensure_ascii=False)),
        )

    def upsert_edge(self, edge: WorldEdge) -> None:
        self.connection.execute(
            """INSERT INTO edges(edge_id,source_id,target_id,edge_type,payload_json) VALUES(?,?,?,?,?)
               ON CONFLICT(edge_id) DO UPDATE SET source_id=excluded.source_id,target_id=excluded.target_id,
               edge_type=excluded.edge_type,payload_json=excluded.payload_json""",
            (edge.edge_id, edge.source_id, edge.target_id, edge.edge_type, json.dumps(edge.payload, ensure_ascii=False)),
        )

    def upsert_chunk(
        self,
        *,
        chunk_id: str,
        paper_id: str,
        title: str,
        text: str,
        section: str | None,
        page_start: int | None,
        page_end: int | None,
        year: int | None,
        source: str | None,
        vector: list[float] | None,
    ) -> None:
        vector_blob: bytes | None = None
        dim: int | None = None
        if vector is not None:
            import struct
            vector_blob = struct.pack(f"<{len(vector)}f", *vector)
            dim = len(vector)
        self.connection.execute(
            """INSERT INTO chunks(chunk_id,paper_id,title,text,section,page_start,page_end,year,source,vector,vector_dim)
               VALUES(?,?,?,?,?,?,?,?,?,?,?)
               ON CONFLICT(chunk_id) DO UPDATE SET paper_id=excluded.paper_id,title=excluded.title,text=excluded.text,
               section=excluded.section,page_start=excluded.page_start,page_end=excluded.page_end,year=excluded.year,
               source=excluded.source,vector=excluded.vector,vector_dim=excluded.vector_dim""",
            (chunk_id, paper_id, title, text, section, page_start, page_end, year, source, vector_blob, dim),
        )
        self.connection.execute("DELETE FROM chunks_fts WHERE chunk_id=?", (chunk_id,))
        self.connection.execute(
            "INSERT INTO chunks_fts(chunk_id,paper_id,text,section,title) VALUES(?,?,?,?,?)",
            (chunk_id, paper_id, text, section or "", title),
        )

    def commit(self) -> None:
        self.connection.commit()

    def get_node(self, node_id: str) -> WorldNode | None:
        row = self.connection.execute("SELECT * FROM nodes WHERE node_id=?", (node_id,)).fetchone()
        if row is None:
            return None
        return WorldNode(node_id=row["node_id"], node_type=row["node_type"], paper_id=row["paper_id"], label=row["label"], payload=json.loads(row["payload_json"]))

    def traverse(self, start_node_id: str, *, depth: int = 1, edge_types: set[str] | None = None) -> TraversalResult:
        if depth < 0:
            raise ValueError("depth must be non-negative")
        visited = {start_node_id}
        frontier = {start_node_id}
        edge_ids: set[str] = set()
        for _ in range(depth):
            if not frontier:
                break
            placeholders = ",".join("?" for _ in frontier)
            params: list[object] = list(frontier)
            query = f"SELECT edge_id,source_id,target_id,edge_type FROM edges WHERE source_id IN ({placeholders}) OR target_id IN ({placeholders})"
            params.extend(frontier)
            rows = self.connection.execute(query, params).fetchall()
            next_frontier: set[str] = set()
            for row in rows:
                if edge_types and row["edge_type"] not in edge_types:
                    continue
                edge_ids.add(row["edge_id"])
                for node_id in (row["source_id"], row["target_id"]):
                    if node_id not in visited:
                        visited.add(node_id)
                        next_frontier.add(node_id)
            frontier = next_frontier
        return TraversalResult(start_node_id=start_node_id, depth=depth, node_ids=sorted(visited), edge_ids=sorted(edge_ids))

    def lexical_search(self, query: str, *, limit: int, filters: dict[str, object] | None = None) -> list[sqlite3.Row]:
        tokens = [token.replace('"', "") for token in query.split() if token.replace('"', "")]
        if not tokens:
            return []
        fts_query = " OR ".join(f'"{token}"' for token in tokens)
        conditions = ["1=1"]
        params: list[object] = [fts_query]
        if filters:
            if filters.get("year_from") is not None:
                conditions.append("c.year >= ?"); params.append(filters["year_from"])
            if filters.get("year_to") is not None:
                conditions.append("c.year <= ?"); params.append(filters["year_to"])
            if filters.get("temporal_cutoff") is not None:
                conditions.append("c.year IS NOT NULL AND c.year <= ?"); params.append(filters["temporal_cutoff"])
            if filters.get("paper_ids"):
                ids = list(filters["paper_ids"])
                placeholders = ",".join("?" for _ in ids)
                conditions.append(f"c.paper_id IN ({placeholders})")
                params.extend(ids)
            if filters.get("sources"):
                sources = list(filters["sources"])
                placeholders = ",".join("?" for _ in sources)
                conditions.append(f"c.source IN ({placeholders})")
                params.extend(sources)
        sql = f"""SELECT c.*, bm25(chunks_fts) AS rank
                  FROM chunks_fts JOIN chunks c ON c.chunk_id=chunks_fts.chunk_id
                  WHERE chunks_fts MATCH ? AND {' AND '.join(conditions)}
                  ORDER BY rank ASC, c.chunk_id ASC LIMIT ?"""
        params.append(limit)
        return self.connection.execute(sql, params).fetchall()

    def dense_candidates(self, *, filters: dict[str, object] | None = None) -> list[sqlite3.Row]:
        conditions = ["vector IS NOT NULL"]
        params: list[object] = []
        if filters:
            if filters.get("year_from") is not None:
                conditions.append("year >= ?"); params.append(filters["year_from"])
            if filters.get("year_to") is not None:
                conditions.append("year <= ?"); params.append(filters["year_to"])
            if filters.get("temporal_cutoff") is not None:
                conditions.append("year IS NOT NULL AND year <= ?"); params.append(filters["temporal_cutoff"])
            if filters.get("paper_ids"):
                ids = list(filters["paper_ids"])
                placeholders = ",".join("?" for _ in ids)
                conditions.append(f"paper_id IN ({placeholders})"); params.extend(ids)
            if filters.get("sources"):
                sources = list(filters["sources"])
                placeholders = ",".join("?" for _ in sources)
                conditions.append(f"source IN ({placeholders})"); params.extend(sources)
        return self.connection.execute(f"SELECT * FROM chunks WHERE {' AND '.join(conditions)}", params).fetchall()

    def index_extraction(self, paper: Paper, extraction: StructuredExtraction, vectors: dict[str, list[float]] | None = None) -> None:
        self.upsert_paper(paper)
        self.upsert_node(WorldNode(node_id=f"paper:{paper.paper_id}", node_type="paper", paper_id=paper.paper_id, label=paper.title, payload={"year": paper.year}))
        for section in extraction.sections:
            self.upsert_node(WorldNode(node_id=section.section_id, node_type="section", paper_id=paper.paper_id, label=section.title, payload={"level": section.level, "page_start": section.page_start, "page_end": section.page_end}))
            self.upsert_edge(WorldEdge(edge_id=f"contains:{paper.paper_id}:{section.section_id}", source_id=f"paper:{paper.paper_id}", target_id=section.section_id, edge_type="contains"))
        for chunk in extraction.chunks:
            section_label = chunk.section_title or ""
            self.upsert_chunk(chunk_id=chunk.chunk_id, paper_id=paper.paper_id, title=paper.title, text=chunk.text, section=section_label, page_start=chunk.page_start, page_end=chunk.page_end, year=paper.year, source=str(paper.metadata.get("source")) if paper.metadata.get("source") else None, vector=(vectors or {}).get(chunk.chunk_id))
            self.upsert_node(WorldNode(node_id=chunk.chunk_id, node_type="chunk", paper_id=paper.paper_id, label=chunk.text[:160], payload={"section_id": chunk.section_id, "page_start": chunk.page_start, "page_end": chunk.page_end}))
            if chunk.section_id:
                self.upsert_edge(WorldEdge(edge_id=f"contains:{chunk.section_id}:{chunk.chunk_id}", source_id=chunk.section_id, target_id=chunk.chunk_id, edge_type="contains"))
        for claim, evidence in zip(extraction.claims, extraction.evidence, strict=True):
            self.upsert_node(WorldNode(node_id=claim.claim_id, node_type="claim", paper_id=paper.paper_id, label=claim.text, payload={"chunk_id": claim.chunk_id, "raw_confidence": claim.raw_confidence}))
            self.upsert_node(WorldNode(node_id=evidence.evidence_id, node_type="evidence", paper_id=paper.paper_id, label=evidence.claim, payload={"section": evidence.section, "page": evidence.page, "quote": evidence.quote, "source_locator": evidence.source_locator, "confidence": evidence.confidence}))
            self.upsert_edge(WorldEdge(edge_id=f"claim-evidence:{claim.claim_id}:{evidence.evidence_id}", source_id=claim.claim_id, target_id=evidence.evidence_id, edge_type="supports"))
        for ref in extraction.references:
            self.upsert_node(WorldNode(node_id=ref.reference_id, node_type="reference", paper_id=paper.paper_id, label=ref.title or ref.raw_text[:160], payload=ref.model_dump(mode="json")))
        for edge in extraction.citation_edges:
            target = edge.cited_paper_id or edge.cited_reference_id
            self.upsert_edge(WorldEdge(edge_id=edge.edge_id, source_id=f"paper:{paper.paper_id}", target_id=target, edge_type="cites", payload={"confidence": edge.confidence, "marker": edge.marker, "context_chunk_id": edge.citation_context_chunk_id}))
        for field, node_type, edge_type in (("methods", "method", "has_method"), ("datasets", "dataset", "has_dataset"), ("metrics", "metric", "has_metric"), ("baselines", "baseline", "has_baseline"), ("tasks", "task", "has_task")):
            for value in getattr(paper, field):
                normalized = " ".join(value.lower().split())
                node_id = f"{node_type}:{hash(normalized)}"
                self.upsert_node(WorldNode(node_id=node_id, node_type=node_type, paper_id=None, label=value, payload={"normalized": normalized}))
                self.upsert_edge(WorldEdge(edge_id=f"{edge_type}:{paper.paper_id}:{node_id}", source_id=f"paper:{paper.paper_id}", target_id=node_id, edge_type=edge_type))
        self.connection.commit()
