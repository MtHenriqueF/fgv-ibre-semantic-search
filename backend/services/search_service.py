"""Thin service layer around semantic search."""

from __future__ import annotations

from typing import Any

from backend.schemas import SearchRequest
from src.search import search_semantic


def run_semantic_search(payload: SearchRequest) -> dict[str, Any]:
    filters = _filters_to_dict(payload)
    return search_semantic(
        query=payload.query,
        top_k=payload.top_k,
        filters=filters,
        min_similarity=payload.min_similarity,
    )


def _filters_to_dict(payload: SearchRequest) -> dict[str, str] | None:
    if payload.filters is None:
        return None

    filters = _model_dump(payload.filters, exclude_none=True)
    return filters or None


def _model_dump(model: Any, **kwargs: Any) -> dict[str, Any]:
    if hasattr(model, "model_dump"):
        return model.model_dump(**kwargs)
    return model.dict(**kwargs)
