"""Compare embedding models using the existing manual relevance judgments."""

from __future__ import annotations

import csv
import json
import re
from pathlib import Path
from statistics import mean
from typing import Any

try:
    from .config import (
        CHROMA_COLLECTION_NAME,
        DEFAULT_TOP_K,
        OUTPUTS_DIR,
        VECTOR_STORE_DIR,
    )
    from .embeddings import generate_embeddings, load_embedding_model
    from .evaluate import (
        dedupe_article_ids,
        load_relevance_judgments,
        mrr,
        ndcg_at_k,
        precision_at_k,
        recall_at_k,
    )
    from .vector_store import (
        delete_collection_if_exists,
        get_chroma_client,
        get_or_create_collection,
        load_chunks,
        prepare_chroma_payload,
    )
except ImportError:
    from config import CHROMA_COLLECTION_NAME, DEFAULT_TOP_K, OUTPUTS_DIR, VECTOR_STORE_DIR
    from embeddings import generate_embeddings, load_embedding_model
    from evaluate import (
        dedupe_article_ids,
        load_relevance_judgments,
        mrr,
        ndcg_at_k,
        precision_at_k,
        recall_at_k,
    )
    from vector_store import (
        delete_collection_if_exists,
        get_chroma_client,
        get_or_create_collection,
        load_chunks,
        prepare_chroma_payload,
    )


MODELS_TO_COMPARE = [
    "intfloat/multilingual-e5-small",
    "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
]

MODEL_COMPARISON_DIR = VECTOR_STORE_DIR / "model_comparison"
EMBEDDING_EVALUATION_PATH = OUTPUTS_DIR / "embedding_evaluation.csv"


def model_slug(model_name: str) -> str:
    """Return a filesystem-safe slug for a model name."""
    return re.sub(r"[^a-z0-9]+", "_", model_name.lower()).strip("_")


def format_document_for_model(model_name: str, document: str) -> str:
    """Apply model-specific document formatting when required."""
    if model_name == "intfloat/multilingual-e5-small":
        return f"passage: {document}"
    return document


def format_query_for_model(model_name: str, query: str) -> str:
    """Apply model-specific query formatting when required."""
    if model_name == "intfloat/multilingual-e5-small":
        return f"query: {query}"
    return query


def evaluate_embedding_model(model_name: str, top_k: int = DEFAULT_TOP_K) -> list[dict[str, Any]]:
    """Evaluate one embedding model against the existing qrels."""
    model = load_embedding_model(model_name)
    collection = _build_model_collection(model_name, model=model)
    rows: list[dict[str, Any]] = []

    for item in load_relevance_judgments():
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

        query_embedding = generate_embeddings(
            [format_query_for_model(model_name, query)],
            model=model,
            model_name=model_name,
        )[0]
        raw_results = collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            include=["metadatas"],
        )
        metadatas = _first_query_list(raw_results.get("metadatas"))
        retrieved_article_ids = dedupe_article_ids(
            [
                int(metadata["article_id"])
                for metadata in metadatas
                if metadata.get("article_id") is not None
            ]
        )
        retrieved_chunk_ids = [
            str(metadata["chunk_id"])
            for metadata in metadatas
            if metadata.get("chunk_id")
        ]

        rows.append(
            {
                "model_name": model_name,
                "query": query,
                "top_k": top_k,
                "precision_at_3": round(precision_at_k(retrieved_article_ids, relevant_ids, 3), 6),
                "recall_at_5": round(recall_at_k(retrieved_article_ids, relevant_ids, 5), 6),
                "mrr": round(mrr(retrieved_article_ids, relevant_ids), 6),
                "ndcg_at_5": round(ndcg_at_k(retrieved_article_ids, relevance_scores, 5), 6),
                "retrieved_article_ids": json.dumps(retrieved_article_ids),
                "retrieved_chunk_ids": json.dumps(retrieved_chunk_ids),
            }
        )

    return rows


def compare_embedding_models(
    models: list[str] | None = None,
    top_k: int = DEFAULT_TOP_K,
) -> list[dict[str, Any]]:
    """Compare models and save one summary CSV row per model."""
    model_names = models or MODELS_TO_COMPARE
    detailed_rows = [
        row
        for model_name in model_names
        for row in evaluate_embedding_model(model_name, top_k=top_k)
    ]
    summary_rows = summarize_model_results(detailed_rows)
    save_embedding_evaluation_summary(summary_rows)
    return summary_rows


def summarize_model_results(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Aggregate per-query rows into one row per model."""
    grouped: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        grouped.setdefault(str(row["model_name"]), []).append(row)

    summary_rows: list[dict[str, Any]] = []
    for model_name, model_rows in grouped.items():
        summary_rows.append(
            {
                "model_name": model_name,
                "mean_precision_at_3": round(mean(row["precision_at_3"] for row in model_rows), 6),
                "mean_recall_at_5": round(mean(row["recall_at_5"] for row in model_rows), 6),
                "mean_mrr": round(mean(row["mrr"] for row in model_rows), 6),
                "mean_ndcg_at_5": round(mean(row["ndcg_at_5"] for row in model_rows), 6),
                "arithmetic_mean": round(
                    mean(
                        [
                            mean(row["precision_at_3"] for row in model_rows),
                            mean(row["recall_at_5"] for row in model_rows),
                            mean(row["mrr"] for row in model_rows),
                            mean(row["ndcg_at_5"] for row in model_rows),
                        ]
                    ),
                    6,
                ),
            }
        )

    return summary_rows


def save_embedding_evaluation_summary(
    rows: list[dict[str, Any]],
    path: Path = EMBEDDING_EVALUATION_PATH,
) -> None:
    """Save the model-level comparison CSV requested for this experiment."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "model_name",
        "mean_precision_at_3",
        "mean_recall_at_5",
        "mean_mrr",
        "mean_ndcg_at_5",
        "arithmetic_mean",
    ]
    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _build_model_collection(model_name: str, model: Any) -> Any:
    chunks = load_chunks()
    persist_directory = MODEL_COMPARISON_DIR / model_slug(model_name)
    client = get_chroma_client(persist_directory)
    delete_collection_if_exists(client, CHROMA_COLLECTION_NAME)
    collection = get_or_create_collection(client, CHROMA_COLLECTION_NAME)

    ids, documents, metadatas = prepare_chroma_payload(chunks)
    embeddings = generate_embeddings(
        [format_document_for_model(model_name, document) for document in documents],
        model=model,
        model_name=model_name,
    )
    collection.add(
        ids=ids,
        documents=documents,
        embeddings=embeddings,
        metadatas=metadatas,
    )
    return collection


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


def main() -> None:
    summary_rows = compare_embedding_models()
    print(f"Compared models: {len(summary_rows)}")
    print(f"Saved summary to: {EMBEDDING_EVALUATION_PATH}")


if __name__ == "__main__":
    main()
