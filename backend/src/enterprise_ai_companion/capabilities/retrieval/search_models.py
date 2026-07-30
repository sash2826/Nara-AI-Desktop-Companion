"""Shared data models for the search capability."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SearchResult:
    chunk_id: str
    document_id: str
    document_path: str
    chunk_index: int
    content: str
    score: float
