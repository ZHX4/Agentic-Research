"""Persistent SQLite scientific world model for Phase 3."""

from __future__ import annotations

import hashlib
import json
import sqlite3
import struct
from pathlib import Path

from agentic_research.schemas import Paper
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
  vector_dim INTEGER,
  vector_model TEXT
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
CREATE INDEX IF NOT EXISTS idx_chunks_vector_model ON chunks(vector_model);
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
            columns = {row["name"] for row in self.connection.execute("PRAGMA table_info(chunks)").fetchall()}
            if "vector_model" not in columns:
                self.connection.execute("ALTER TABLE chunks ADD COLUMN vector_model TEXT")
                self.connection.commit()
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
        vector_model: str | None,
    ) -> None:
        vector_blob: bytes | None = None
        dimension: int | None = None
        if vector is not None:
            vector_blob = struct.pack(f"<{len(vector)}f", *vector)
            dimension = len(vector)
        self.connection.execute(
            """INSERT INTO chunks(chunk_id,paper_id,title,text,section,page_start,page_end,year,source,vector,vector_dim,vector_model)
               VALUES(?,?,?,?,?,?,?,?,?,?,?,?)
               ON CONFLICT(chunk_id) DO UPDATE SET paper_id=excluded.paper_id,title=excluded.title,text=excluded.text,
               section=excluded.section,page_start=excluded.page_start,page_end=excluded.page_end,year=excluded.year,
               source=excluded.source,vector=COALESCE(excluded.vector,chunks.vector),
               vector_dim=COALESCE(excluded.vector_dim,chunks.vector_dim),
               vector_model=COALESCE(excluded.vector_model,chunks.vector_model)""",
            (chunk_id, paper_id, title, text, section, page_start, page_end, year, source, vector_blob, dimension, vector_model),
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

    def traverse(self, start_node_id: str, *, depth: int = 1, edge_types: set[str] | None = None, direction: str = "both") -> TraversalResult:
        if depth < 0:
            raise ValueError("depth must be non-negative")
        if direction not in {"out", "in", "both"}:
            raise ValueError("direction must be out, in, or both")
        if self.get_node(start_node_id) is None:
            raise ValueError(f"Unknown start node: {start_node_id}")
        visited = {start_node_id}
        frontier = {start_node_id}
        edge_ids: set[str] = set()
        for _ in range(depth):
            if not frontier:
                break
            placeholders = ",".join("?" for _ in frontier)
            params: list[object] = []
            where_parts: list[str] = []
            if direction in {"out", "both"}:
                where_parts.append(f"source_id IN ({placeholders})")
                params.extend(frontier)
            if direction in {"in", "both"}:
                where_parts.append(f"target_id IN ({placeholders})")
                params.extend(frontier)
            query = f"SELECT edge_id,source_id,target_id,edge_type FROM edges WHERE ({' OR '.join(where_parts)})"
            rows = self.connection.execute(query, params).fetchall()
            next_frontier: set[str] = set()
            for row in rows:
                if edge_types and row["edge_type"] not in edge_types:
                    continue
                edge_ids.add(row["edge_id"])
                if direction == "out":
                    candidates = (row["target_id"],)
                elif direction == "in":
                    candidates = (row["source_id"],)
                else:
                    candidates = (row["source_id"], row["target_id"])
                for node_id in candidates:
                    if node_id not in visited:
                        visited.add(node_id)
                        next_frontier.add(node_id)
            frontier = next_frontier
        return TraversalResult(start_node_id=start_node_id, depth=depth, node_ids=sorted(visited), edge_ids=sorted(edge_ids))

    def lexical_search(self, query: str, *, limit: int, filters: dict[str, object] | None = None) -> list[sqlite3.Row]:
        if limit < 1:
            raise ValueError("limit must be positive")
        import re
        tokens = re.findall(r"[A-Za-z0-9][A-Za-z0-9_+-]{1,63}", query.lower())
        if not tokens:
            return []
        fts_query = " OR ".join(f'"{token.replace(chr(34), "")}"' for token in tokens)
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
                ids = list(filters["paper_ids"]); placeholders = ",".join("?" for _ in ids)
                conditions.append(f"c.paper_id IN ({placeholders})"); params.extend(ids)
            if filters.get("sources"):
                sources = list(filters["sources"]); placeholders = ",".join("?" for _ in sources)
                conditions.append(f"c.source IN ({placeholders})"); params.extend(sources)
        sql = f"SELECT c.*, bm25(chunks_fts) AS rank FROM chunks_fts JOIN chunks c ON c.chunk_id=chunks_fts.chunk_id WHERE chunks_fts MATCH ? AND {' AND '.join(conditions)} ORDER BY rank ASC, c.chunk_id ASC LIMIT ?"
        params.append(limit)
        return self.connection.execute(sql, params).fetchall()

    def dense_candidates(self, *, embedding_model: str, filters: dict[str, object] | None = None) -> list[sqlite3.Row]:
        conditions = ["vector IS NOT NULL", "vector_model = ?"]
        params: list[object] = [embedding_model]
        if filters:
            if filters.get("year_from") is not None:
                conditions.append("year >= ?"); params.append(filters["year_from"])
            if filters.get("year_to") is not None:
                conditions.append("year <= ?"); params.append(filters["year_to"])
            if filters.get("temporal_cutoff") is not None:
                conditions.append("year IS NOT NULL AND year <= ?"); params.append(filters["temporal_cutoff"])
            if filters.get("paper_ids"):
                ids = list(filters["paper_ids"]); placeholders = ",".join("?" for _ in ids)
                conditions.append(f"paper_id IN ({placeholders})"); params.extend(ids)
            if filters.get("sources"):
                sources = list(filters["sources"]); placeholders = ",".join("?" for _ in sources)
                conditions.append(f"source IN ({placeholders})"); params.extend(sources)
        return self.connection.execute(f"SELECT * FROM chunks WHERE {' AND '.join(conditions)}", params).fetchall()

    def index_extraction(self, paper: Paper, extraction: StructuredExtraction, vectors: dict[str, list[float]] | None = None, vector_model: str | None = None) -> None:
        self.upsert_paper(paper)
        paper_node_id = f"paper:{paper.paper_id}"
        self.upsert_node(WorldNode(node_id=paper_node_id, node_type="paper", paper_id=paper.paper_id, label=paper.title, payload={"year": paper.year, "doi": paper.doi, "arxiv_id": paper.arxiv_id}))
        for section in extraction.sections:
            self.upsert_node(WorldNode(node_id=section.section_id, node_type="section", paper_id=paper.paper_id, label=section.title, payload={"level": section.level, "page_start": section.page_start, "page_end": section.page_end}))
            self.upsert_edge(WorldEdge(edge_id=f"contains:{paper.paper_id}:{section.section_id}", source_id=paper_node_id, target_id=section.section_id, edge_type="contains"))
        for chunk in extraction.chunks:
            self.upsert_chunk(chunk_id=chunk.chunk_id, paper_id=paper.paper_id, title=paper.title, text=chunk.text, section=chunk.section_title, page_start=chunk.page_start, page_end=chunk.page_end, year=paper.year, source=str(paper.metadata.get("source")) if paper.metadata.get("source") else None, vector=(vectors or {}).get(chunk.chunk_id), vector_model=vector_model if chunk.chunk_id in (vectors or {}) else None)
            self.upsert_node(WorldNode(node_id=chunk.chunk_id, node_type="chunk", paper_id=paper.paper_id, label=chunk.text[:160], payload={"section_id": chunk.section_id, "page_start": chunk.page_start, "page_end": chunk.page_end}))
            if chunk.section_id:
                self.upsert_edge(WorldEdge(edge_id=f"contains:{chunk.section_id}:{chunk.chunk_id}", source_id=chunk.section_id, target_id=chunk.chunk_id, edge_type="contains"))
        evidence_by_id = {item.evidence_id: item for item in extraction.evidence}
        for claim in extraction.claims:
            self.upsert_node(WorldNode(node_id=claim.claim_id, node_type="claim", paper_id=paper.paper_id, label=claim.text, payload={"chunk_id": claim.chunk_id, "raw_confidence": claim.raw_confidence, "calibrated_confidence": claim.calibrated_confidence}))
        for evidence in extraction.evidence:
            self.upsert_node(WorldNode(node_id=evidence.evidence_id, node_type="evidence", paper_id=paper.paper_id, label=evidence.claim, payload={"section": evidence.section, "page": evidence.page, "quote": evidence.quote, "source_locator": evidence.source_locator, "confidence": evidence.confidence}))
        for link in extraction.claim_links:
            if link.evidence_id not in evidence_by_id:
                raise ValueError(f"Unknown evidence_id in claim link: {link.evidence_id}")
            self.upsert_edge(WorldEdge(edge_id=link.link_id, source_id=link.claim_id, target_id=link.evidence_id, edge_type=link.relation))
        for ref in extraction.references:
            self.upsert_node(WorldNode(node_id=ref.reference_id, node_type="reference", paper_id=paper.paper_id, label=ref.title or ref.raw_text[:160], payload=ref.model_dump(mode="json")))
        for edge in extraction.citation_edges:
            if edge.cited_paper_id:
                digest = hashlib.sha1(edge.cited_paper_id.encode("utf-8")).hexdigest()[:20]
                target_id = f"external-paper:{digest}"
                self.upsert_node(WorldNode(node_id=target_id, node_type="paper", paper_id=edge.cited_paper_id, label=edge.cited_paper_id, payload={"external": True, "identifier": edge.cited_paper_id}))
            else:
                target_id = edge.cited_reference_id
            self.upsert_edge(WorldEdge(edge_id=edge.edge_id, source_id=paper_node_id, target_id=target_id, edge_type="cites", payload={"confidence": edge.confidence, "marker": edge.marker, "context_chunk_id": edge.citation_context_chunk_id}))
        for author in paper.authors:
            normalized = " ".join(author.lower().split())
            digest = hashlib.sha1(normalized.encode("utf-8")).hexdigest()[:20]
            node_id = f"author:{digest}"
            self.upsert_node(WorldNode(node_id=node_id, node_type="author", paper_id=None, label=author, payload={"normalized": normalized}))
            self.upsert_edge(WorldEdge(edge_id=f"authored_by:{paper.paper_id}:{node_id}", source_id=paper_node_id, target_id=node_id, edge_type="authored_by"))
        for field, node_type, edge_type in (("methods", "method", "has_method"), ("datasets", "dataset", "has_dataset"), ("metrics", "metric", "has_metric"), ("baselines", "baseline", "has_baseline"), ("tasks", "task", "has_task")):
            for value in getattr(paper, field):
                normalized = " ".join(value.lower().split())
                digest = hashlib.sha1(normalized.encode("utf-8")).hexdigest()[:20]
                node_id = f"{node_type}:{digest}"
                self.upsert_node(WorldNode(node_id=node_id, node_type=node_type, paper_id=None, label=value, payload={"normalized": normalized}))
                self.upsert_edge(WorldEdge(edge_id=f"{edge_type}:{paper.paper_id}:{node_id}", source_id=paper_node_id, target_id=node_id, edge_type=edge_type))
        self.connection.commit()
