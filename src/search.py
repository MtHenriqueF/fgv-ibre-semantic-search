"""Semantic search over the local ChromaDB collection."""

from __future__ import annotations

import argparse
import json
from collections.abc import Mapping
from typing import Any

try:
    from .chunking import date_to_int
    from .config import CHROMA_COLLECTION_NAME, DEFAULT_TOP_K
    from .embeddings import generate_embeddings
    from .vector_store import CHROMA_METADATA_FIELDS, get_chroma_client
except ImportError:
    from chunking import date_to_int
    from config import CHROMA_COLLECTION_NAME, DEFAULT_TOP_K
    from embeddings import generate_embeddings
    from vector_store import CHROMA_METADATA_FIELDS, get_chroma_client


REQUIRED_SEARCH_METADATA = set(CHROMA_METADATA_FIELDS)


def build_chroma_where(filters: dict[str, Any] | None) -> dict[str, Any] | None:
    """Build a ChromaDB metadata filter from user-facing filter names."""
    if not filters:
        return None

    conditions: list[dict[str, Any]] = []

    fonte = _clean_filter_value(filters.get("fonte"))
    if fonte is not None:
        conditions.append({"fonte": fonte})

    content_quality = _clean_filter_value(filters.get("content_quality"))
    if content_quality is not None:
        conditions.append({"content_quality": content_quality})

    date_start = filters.get("date_start")
    date_end = filters.get("date_end")

    start_int = (
        _parse_filter_date(date_start, "date_start")
        if _has_filter_value(date_start)
        else None
    )
    end_int = (
        _parse_filter_date(date_end, "date_end")
        if _has_filter_value(date_end)
        else None
    )

    if start_int is not None and end_int is not None and start_int > end_int:
        raise ValueError("date_start must be less than or equal to date_end.")

    if start_int is not None:
        conditions.append({"date_int": {"$gte": start_int}})
    if end_int is not None:
        conditions.append({"date_int": {"$lte": end_int}})

    if not conditions:
        return None
    if len(conditions) == 1:
        return conditions[0]
    return {"$and": conditions}


def search_semantic(
    query: str,
    top_k: int = DEFAULT_TOP_K,
    filters: dict[str, Any] | None = None,
    min_similarity: float | None = None,
) -> dict[str, Any]:
    """Search the local ChromaDB collection using an embedding of the query."""
    query = (query or "").strip()
    if not query:
        raise ValueError("Query must not be empty.")
    if top_k <= 0:
        raise ValueError("top_k must be greater than zero.")

    collection = _get_existing_collection()
    count = collection.count()
    if count == 0:
        return format_chroma_results(
            raw_results={},
            query=query,
            top_k=top_k,
            filters=filters,
            min_similarity=min_similarity,
        )

    where = build_chroma_where(filters)
    query_embedding = generate_embeddings([query])[0]

    raw_results = collection.query(
        query_embeddings=[query_embedding],
        n_results=min(top_k, count),
        where=where,
        include=["documents", "metadatas", "distances"],
    )

    return format_chroma_results(
        raw_results=raw_results,
        query=query,
        top_k=top_k,
        filters=filters,
        min_similarity=min_similarity,
    )


def format_chroma_results(
    raw_results: dict[str, Any],
    query: str,
    top_k: int,
    filters: dict[str, Any] | None,
    min_similarity: float | None,
) -> dict[str, Any]:
    """Convert ChromaDB's nested query response into the project response shape."""
    documents = _first_query_list(raw_results.get("documents"))
    metadatas = _first_query_list(raw_results.get("metadatas"))
    distances = _first_query_list(raw_results.get("distances"))
    ids = _first_query_list(raw_results.get("ids"))

    results: list[dict[str, Any]] = []
    for index, document in enumerate(documents):
        metadata = _metadata_at(metadatas, index)
        distance = _float_at(distances, index)
        similarity = 1 - distance if distance is not None else None

        if min_similarity is not None and (
            similarity is None or similarity < min_similarity
        ):
            continue

        chunk_id = metadata.get("chunk_id") or _value_at(ids, index)
        results.append(
            {
                "rank": len(results) + 1,
                "article_id": _to_int(metadata.get("article_id")),
                "chunk_id": chunk_id,
                "chunk_index": _to_int(metadata.get("chunk_index")),
                "titulo": metadata.get("titulo", ""),
                "data": metadata.get("data", ""),
                "ano": _to_int(metadata.get("ano")),
                "mes": _to_int(metadata.get("mes")),
                "fonte": metadata.get("fonte", ""),
                "content_quality": metadata.get("content_quality", ""),
                "document": document,
                "distance": _round_score(distance),
                "similarity": _round_score(similarity),
            }
        )

    return {
        "query": query,
        "search_type": "semantic",
        "top_k": top_k,
        "filters": filters,
        "min_similarity": min_similarity,
        "results": results,
    }


def validate_search_collection() -> dict[str, Any]:
    """Validate that the persisted ChromaDB collection is ready for semantic search."""
    status: dict[str, Any] = {
        "collection_name": CHROMA_COLLECTION_NAME,
        "count": 0,
        "has_documents": False,
        "has_required_metadata": False,
        "returns_distances": False,
        "distance_metric": "unknown",
        "hnsw_config_detected": False,
        "notes": "",
    }

    try:
        collection = _get_existing_collection()
    except Exception as exc:  # pragma: no cover - depends on local Chroma state.
        status["notes"] = f"Collection could not be loaded: {exc}"
        return status

    count = collection.count()
    status["count"] = count
    status["has_documents"] = count > 0

    metric, detected, notes = _detect_distance_metric(collection)
    status["distance_metric"] = metric
    status["hnsw_config_detected"] = detected
    status["notes"] = notes

    if count == 0:
        return status

    sample = collection.get(limit=1, include=["documents", "metadatas", "embeddings"])
    sample_metadata = _metadata_at(sample.get("metadatas") or [], 0)
    status["has_required_metadata"] = REQUIRED_SEARCH_METADATA.issubset(sample_metadata)

    sample_embedding = _first_embedding(sample.get("embeddings"))
    if sample_embedding is None:
        sample_documents = sample.get("documents") or []
        if sample_documents:
            sample_embedding = generate_embeddings([sample_documents[0]])[0]

    if sample_embedding is not None:
        query_result = collection.query(
            query_embeddings=[sample_embedding],
            n_results=1,
            include=["distances"],
        )
        distances = _first_query_list(query_result.get("distances"))
        status["returns_distances"] = bool(distances) and distances[0] is not None

    return status


def _get_existing_collection(collection_name: str = CHROMA_COLLECTION_NAME) -> Any:
    client = get_chroma_client()
    try:
        return client.get_collection(collection_name)
    except Exception as exc:
        raise RuntimeError(
            f"ChromaDB collection '{collection_name}' was not found. "
            "Run `python -m src.vector_store` or `python run_pipeline.py` first."
        ) from exc


def _clean_filter_value(value: Any) -> str | None:
    if not _has_filter_value(value):
        return None
    return str(value).strip()


def _has_filter_value(value: Any) -> bool:
    return value is not None and str(value).strip() != ""


def _parse_filter_date(value: Any, field_name: str) -> int:
    if isinstance(value, int):
        date_value = value if len(str(value)) == 8 else None
    else:
        date_value = date_to_int(str(value).strip())

    if date_value is None:
        raise ValueError(f"{field_name} must use YYYY-MM-DD or YYYYMMDD format.")

    return date_value


def _first_query_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if hasattr(value, "tolist"):
        value = value.tolist()
    if not value:
        return []
    first = value[0]
    if hasattr(first, "tolist"):
        first = first.tolist()
    return first or []


def _metadata_at(metadatas: list[Any], index: int) -> dict[str, Any]:
    value = _value_at(metadatas, index)
    return dict(value) if isinstance(value, Mapping) else {}


def _value_at(values: list[Any], index: int) -> Any:
    if index >= len(values):
        return None
    value = values[index]
    if hasattr(value, "tolist"):
        value = value.tolist()
    return value


def _float_at(values: list[Any], index: int) -> float | None:
    value = _value_at(values, index)
    if value is None:
        return None
    return float(value)


def _to_int(value: Any) -> int | None:
    if value is None or value == "":
        return None
    return int(value)


def _round_score(value: float | None) -> float | None:
    if value is None:
        return None
    return round(float(value), 6)


def _first_embedding(embeddings: Any) -> list[float] | None:
    if embeddings is None:
        return None
    if hasattr(embeddings, "tolist"):
        embeddings = embeddings.tolist()
    if not embeddings:
        return None

    first = embeddings[0]
    if hasattr(first, "tolist"):
        first = first.tolist()

    return [float(value) for value in first]


def _detect_distance_metric(collection: Any) -> tuple[str, bool, str]:
    candidates: list[tuple[str, Any]] = []

    for attr_name in ("configuration", "_configuration", "config"):
        if hasattr(collection, attr_name):
            try:
                value = getattr(collection, attr_name)
                value = value() if callable(value) else value
                candidates.append((attr_name, value))
            except Exception:
                continue

    for source, candidate in candidates:
        metric = _find_metric_value(candidate)
        if metric:
            note_metric = "HNSW/cosine" if metric == "cosine" else f"HNSW/{metric}"
            return (
                metric,
                metric == "cosine",
                f"ChromaDB exposes {note_metric} configuration through collection {source}.",
            )

    metadata = getattr(collection, "metadata", None)
    metadata = metadata() if callable(metadata) else metadata
    metric = _find_metric_value(metadata)
    if metric:
        note_metric = "HNSW/cosine" if metric == "cosine" else f"HNSW/{metric}"
        return (
            metric,
            metric == "cosine",
            f"ChromaDB exposes {note_metric} configuration through collection metadata.",
        )

    return (
        "unknown",
        False,
        "ChromaDB did not expose HNSW/cosine configuration through the available API.",
    )


def _find_metric_value(value: Any) -> str | None:
    if value is None:
        return None

    if hasattr(value, "model_dump"):
        value = value.model_dump()
    elif hasattr(value, "dict"):
        value = value.dict()

    if isinstance(value, Mapping):
        for key, item in value.items():
            if key in {"space", "hnsw:space"} and item:
                return str(item)
            metric = _find_metric_value(item)
            if metric:
                return metric
        return None

    if isinstance(value, list | tuple):
        for item in value:
            metric = _find_metric_value(item)
            if metric:
                return metric
        return None

    if hasattr(value, "space"):
        space = getattr(value, "space")
        return str(space) if space else None

    return None


def _build_cli_filters(args: argparse.Namespace) -> dict[str, Any] | None:
    filters = {
        "fonte": args.fonte,
        "date_start": args.date_start,
        "date_end": args.date_end,
        "content_quality": args.content_quality,
    }
    return {key: value for key, value in filters.items() if _has_filter_value(value)} or None


def main() -> None:
    parser = argparse.ArgumentParser(description="Run semantic search over ChromaDB.")
    parser.add_argument("query", help="Free-text search query.")
    parser.add_argument("--top-k", type=int, default=DEFAULT_TOP_K)
    parser.add_argument("--fonte")
    parser.add_argument("--date-start")
    parser.add_argument("--date-end")
    parser.add_argument("--content-quality")
    parser.add_argument("--min-similarity", type=float)
    args = parser.parse_args()

    response = search_semantic(
        query=args.query,
        top_k=args.top_k,
        filters=_build_cli_filters(args),
        min_similarity=args.min_similarity,
    )
    print(json.dumps(response, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
