"""Read prepared evaluation artifacts for the frontend evaluation mode."""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

from src.config import CHUNKS_PATH, EVALUATION_RESULTS_PATH, SEARCH_EXAMPLES_PATH
from src.evaluate import load_relevance_judgments
from src.vector_store import load_chunks


DESCRIPTION = "Avaliação da busca semântica nas queries obrigatórias do desafio."
METRIC_FIELDS = ("precision_at_3", "recall_at_5", "mrr", "ndcg_at_5")


def get_evaluation_mode_payload() -> dict[str, Any]:
    metric_rows = _load_metric_rows()
    examples_by_query = {
        example["query"]: example
        for example in _load_search_examples()
    }
    relevance_by_query = _load_relevance_by_query()
    chunk_lookup = _load_chunk_lookup()

    queries = []
    for row in metric_rows:
        query = row["query"]
        relevance = relevance_by_query.get(query, {})
        example = examples_by_query.get(query, {"results": []})
        queries.append(
            {
                "query": query,
                "metrics": _extract_metrics(row),
                "results": [
                    _enrich_result(result, relevance, chunk_lookup)
                    for result in example.get("results", [])
                ],
            }
        )

    return {
        "search_type": "semantic",
        "description": DESCRIPTION,
        "metrics_summary": _build_metrics_summary(metric_rows),
        "queries": queries,
    }


def get_search_examples() -> dict[str, list[dict[str, Any]]]:
    chunk_lookup = _load_chunk_lookup()
    examples = []

    for example in _load_search_examples():
        examples.append(
            {
                "query": example["query"],
                "results": [
                    _enrich_result(result, {}, chunk_lookup, include_relevance=False)
                    for result in example.get("results", [])
                ],
            }
        )

    return {"examples": examples}


def _load_metric_rows(path: Path = EVALUATION_RESULTS_PATH) -> list[dict[str, Any]]:
    if not path.exists():
        return []

    with path.open("r", encoding="utf-8", newline="") as file:
        rows = list(csv.DictReader(file))

    parsed_rows = []
    for row in rows:
        parsed_rows.append(
            {
                "query": row["query"],
                "search_type": row["search_type"],
                "top_k": int(row["top_k"]),
                **{field: float(row[field]) for field in METRIC_FIELDS},
            }
        )

    return parsed_rows


def _load_search_examples(path: Path = SEARCH_EXAMPLES_PATH) -> list[dict[str, Any]]:
    if not path.exists():
        return []

    with path.open("r", encoding="utf-8") as file:
        data = json.load(file)

    return data if isinstance(data, list) else []


def _load_relevance_by_query() -> dict[str, dict[int, int]]:
    try:
        judgments = load_relevance_judgments()
    except FileNotFoundError:
        return {}

    return {
        str(item["query"]): {
            int(article_id): int(score)
            for article_id, score in item.get("relevance", {}).items()
        }
        for item in judgments
    }


def _load_chunk_lookup(path: Path = CHUNKS_PATH) -> dict[int, dict[str, Any]]:
    if not path.exists():
        return {}

    lookup: dict[int, dict[str, Any]] = {}
    for chunk in load_chunks(path):
        article_id = int(chunk["article_id"])
        lookup.setdefault(article_id, chunk)

    return lookup


def _build_metrics_summary(rows: list[dict[str, Any]]) -> dict[str, float]:
    if not rows:
        return {
            "mean_precision_at_3": 0.0,
            "mean_recall_at_5": 0.0,
            "mean_mrr": 0.0,
            "mean_ndcg_at_5": 0.0,
        }

    return {
        f"mean_{field}": round(
            sum(float(row[field]) for row in rows) / len(rows),
            6,
        )
        for field in METRIC_FIELDS
    }


def _extract_metrics(row: dict[str, Any]) -> dict[str, float]:
    return {field: float(row[field]) for field in METRIC_FIELDS}


def _enrich_result(
    result: dict[str, Any],
    relevance: dict[int, int],
    chunk_lookup: dict[int, dict[str, Any]],
    include_relevance: bool = True,
) -> dict[str, Any]:
    article_id = int(result["article_id"])
    chunk = chunk_lookup.get(article_id, {})
    enriched = {
        "rank": int(result["rank"]),
        "article_id": article_id,
        "chunk_id": result.get("chunk_id") or chunk.get("chunk_id"),
        "chunk_index": result.get("chunk_index", chunk.get("chunk_index")),
        "titulo": str(result["titulo"]),
        "fonte": str(result["fonte"]),
        "data": str(result["data"]),
        "distance": float(result["distance"]),
        "similarity": float(result["similarity"]),
    }

    if include_relevance:
        enriched["relevance_grade"] = relevance.get(article_id, 0)

    return enriched
