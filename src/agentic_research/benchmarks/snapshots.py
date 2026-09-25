"""Frozen provider-snapshot format for PEFT-30.

Live provider results must never automatically become benchmark truth.
A snapshot preserves enough context to reproduce a provider-dependent
evaluation without querying the live service again.
"""

from __future__ import annotations

import hashlib
import json
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

ProviderName = Literal["openalex", "semantic_scholar", "arxiv"]


def _canonical(obj: object) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode(
        "utf-8"
    )


class ProviderSnapshot(BaseModel):
    """One frozen provider query response (normalized, not raw bytes)."""

    model_config = ConfigDict(extra="forbid")

    provider: ProviderName
    query: str = Field(min_length=1)
    collected_at_utc: str = Field(min_length=1)
    result_ids: list[str] = Field(default_factory=list)
    result_count: int = Field(ge=0)
    request_params: dict[str, str | int | float | bool] = Field(default_factory=dict)
    temporal_filter: str = Field(min_length=1)
    payload_hash: str = Field(pattern=r"^[0-9a-f]{64}$")

    def compute_hash(self) -> str:
        payload = {
            "provider": self.provider,
            "query": self.query,
            "result_ids": sorted(self.result_ids),
            "request_params": self.request_params,
            "temporal_filter": self.temporal_filter,
        }
        return hashlib.sha256(_canonical(payload)).hexdigest()


def build_snapshot(
    *,
    provider: ProviderName,
    query: str,
    collected_at_utc: str,
    result_ids: list[str],
    request_params: dict[str, str | int | float | bool] | None = None,
    temporal_filter: str,
) -> ProviderSnapshot:
    params = request_params or {}
    payload = {
        "provider": provider,
        "query": query,
        "result_ids": sorted(result_ids),
        "request_params": params,
        "temporal_filter": temporal_filter,
    }
    digest = hashlib.sha256(_canonical(payload)).hexdigest()
    return ProviderSnapshot(
        provider=provider,
        query=query,
        collected_at_utc=collected_at_utc,
        result_ids=sorted(result_ids),
        result_count=len(result_ids),
        request_params=params,
        temporal_filter=temporal_filter,
        payload_hash=digest,
    )


def validate_snapshot(snapshot: ProviderSnapshot) -> list[str]:
    problems: list[str] = []
    if snapshot.compute_hash() != snapshot.payload_hash:
        problems.append("payload_hash mismatch")
    if snapshot.result_count != len(snapshot.result_ids):
        problems.append("result_count must equal len(result_ids)")
    return problems
