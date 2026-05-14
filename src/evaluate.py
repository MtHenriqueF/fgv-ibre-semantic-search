"""Ranking metrics for semantic search evaluation."""

from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path
from typing import Any

try:
    from .config import (
        EVALUATION_QUERIES_PATH,
        EVALUATION_RESULTS_PATH,
        RELEVANCE_JUDGMENTS_PATH,
        SEARCH_EXAMPLES_PATH,
    )
    from .search import search_semantic
except ImportError:
    from config import (
        EVALUATION_QUERIES_PATH,
        EVALUATION_RESULTS_PATH,
        RELEVANCE_JUDGMENTS_PATH,
        SEARCH_EXAMPLES_PATH,
    )
    from search import search_semantic


def precision_at_k(retrieved_ids: list[int], relevant_ids: set[int], k: int) -> float:
    """Calculate Precision@k using binary relevance."""
    if k <= 0:
        return 0.0
    retrieved_at_k = retrieved_ids[:k]
    hits = sum(1 for article_id in retrieved_at_k if article_id in relevant_ids)
    return hits / k


def recall_at_k(retrieved_ids: list[int], relevant_ids: set[int], k: int) -> float:
    """Calculate Recall@k using binary relevance."""
    if k <= 0 or not relevant_ids:
        return 0.0
    retrieved_at_k = retrieved_ids[:k]
    hits = sum(1 for article_id in retrieved_at_k if article_id in relevant_ids)
    return hits / len(relevant_ids)


def mrr(retrieved_ids: list[int], relevant_ids: set[int]) -> float:
    """Calculate reciprocal rank for the first relevant result."""
    for rank, article_id in enumerate(retrieved_ids, start=1):
        if article_id in relevant_ids:
            return 1 / rank
    return 0.0


def ndcg_at_k(
    retrieved_ids: list[int],
    relevance_scores: dict[int, int],
    k: int,
) -> float:
    """Calculate nDCG@k using graded relevance scores."""
    if k <= 0:
        return 0.0

    dcg = _dcg([relevance_scores.get(article_id, 0) for article_id in retrieved_ids[:k]])
    ideal_relevances = sorted(relevance_scores.values(), reverse=True)[:k]
    ideal_dcg = _dcg(ideal_relevances)

    if ideal_dcg == 0:
        return 0.0
    return dcg / ideal_dcg


def dedupe_article_ids(article_ids: list[int]) -> list[int]:
    """Deduplicate article ids while preserving ranking order."""
    seen: set[int] = set()
    deduped: list[int] = []

    for article_id in article_ids:
        if article_id in seen:
            continue
        seen.add(article_id)
        deduped.append(article_id)

    return deduped


def evaluate_semantic_search(top_k: int = 5) -> list[dict[str, Any]]:
    """Evaluate semantic search for queries with manual relevance judgments."""
    judgments = load_relevance_judgments()
    rows: list[dict[str, Any]] = []

    for item in judgments:
        query = str(item["query"])
        relevance_scores = {
            int(article_id): int(score)
            for article_id, score in item.get("relevance", {}).items()
        }
        relevant_ids = {
            article_id
            for article_id, score in relevance_scores.items()
            if score > 0
        }

        response = search_semantic(query=query, top_k=top_k)
        retrieved_article_ids = dedupe_article_ids(
            [
                int(result["article_id"])
                for result in response["results"]
                if result.get("article_id") is not None
            ]
        )

        rows.append(
            {
                "query": query,
                "search_type": "semantic",
                "top_k": top_k,
                "precision_at_3": round(
                    precision_at_k(retrieved_article_ids, relevant_ids, 3),
                    6,
                ),
                "recall_at_5": round(
                    recall_at_k(retrieved_article_ids, relevant_ids, 5),
                    6,
                ),
                "mrr": round(mrr(retrieved_article_ids, relevant_ids), 6),
                "ndcg_at_5": round(
                    ndcg_at_k(retrieved_article_ids, relevance_scores, 5),
                    6,
                ),
                "retrieved_article_ids": json.dumps(retrieved_article_ids),
            }
        )

    save_evaluation_results(rows)
    return rows


def generate_search_examples(top_k: int = 5) -> list[dict[str, Any]]:
    """Run the mandatory queries and save compact search examples."""
    examples: list[dict[str, Any]] = []

    for query in load_evaluation_queries():
        response = search_semantic(query=query, top_k=top_k)
        examples.append(
            {
                "query": query,
                "search_type": "semantic",
                "top_k": top_k,
                "results": [
                    {
                        "rank": result["rank"],
                        "article_id": result["article_id"],
                        "titulo": result["titulo"],
                        "fonte": result["fonte"],
                        "data": result["data"],
                        "distance": result["distance"],
                        "similarity": result["similarity"],
                    }
                    for result in response["results"]
                ],
            }
        )

    save_search_examples(examples)
    return examples


def load_evaluation_queries(path: Path = EVALUATION_QUERIES_PATH) -> list[str]:
    """Load mandatory challenge queries."""
    with path.open("r", encoding="utf-8") as file:
        data = json.load(file)

    if not isinstance(data, list):
        raise ValueError("Evaluation queries must be a JSON list.")

    return [str(query) for query in data]


def load_relevance_judgments(path: Path = RELEVANCE_JUDGMENTS_PATH) -> list[dict[str, Any]]:
    """Load manual relevance judgments."""
    with path.open("r", encoding="utf-8") as file:
        data = json.load(file)

    if not isinstance(data, list):
        raise ValueError("Relevance judgments must be a JSON list.")

    return data


def save_evaluation_results(
    rows: list[dict[str, Any]],
    path: Path = EVALUATION_RESULTS_PATH,
) -> None:
    """Save evaluation metrics as CSV."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "query",
        "search_type",
        "top_k",
        "precision_at_3",
        "recall_at_5",
        "mrr",
        "ndcg_at_5",
        "retrieved_article_ids",
    ]

    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def save_search_examples(
    examples: list[dict[str, Any]],
    path: Path = SEARCH_EXAMPLES_PATH,
) -> None:
    """Save compact search examples as JSON."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as file:
        json.dump(examples, file, ensure_ascii=False, indent=2)


def _dcg(relevances: list[int]) -> float:
    return sum(
        ((2**relevance) - 1) / math.log2(rank + 1)
        for rank, relevance in enumerate(relevances, start=1)
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate semantic search rankings.")
    parser.add_argument("--top-k", type=int, default=5)
    args = parser.parse_args()

    rows = evaluate_semantic_search(top_k=args.top_k)
    generate_search_examples(top_k=args.top_k)

    print(f"Evaluation rows: {len(rows)}")
    print(f"Saved metrics to: {EVALUATION_RESULTS_PATH}")
    print(f"Saved search examples to: {SEARCH_EXAMPLES_PATH}")


if __name__ == "__main__":
    main()
