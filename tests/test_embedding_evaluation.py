from __future__ import annotations

from src.embedding_evaluation import (
    format_document_for_model,
    format_query_for_model,
    model_slug,
    summarize_model_results,
)


def test_model_slug_is_filesystem_safe() -> None:
    assert model_slug("intfloat/multilingual-e5-small") == "intfloat_multilingual_e5_small"


def test_e5_uses_expected_prefixes() -> None:
    model_name = "intfloat/multilingual-e5-small"

    assert format_document_for_model(model_name, "documento") == "passage: documento"
    assert format_query_for_model(model_name, "consulta") == "query: consulta"


def test_minilm_keeps_text_unchanged() -> None:
    model_name = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"

    assert format_document_for_model(model_name, "documento") == "documento"
    assert format_query_for_model(model_name, "consulta") == "consulta"


def test_summarize_model_results_calculates_metric_means() -> None:
    rows = [
        {
            "model_name": "model-a",
            "precision_at_3": 1.0,
            "recall_at_5": 0.5,
            "mrr": 1.0,
            "ndcg_at_5": 0.75,
        },
        {
            "model_name": "model-a",
            "precision_at_3": 0.5,
            "recall_at_5": 1.0,
            "mrr": 0.5,
            "ndcg_at_5": 0.25,
        },
    ]

    [summary] = summarize_model_results(rows)

    assert summary == {
        "model_name": "model-a",
        "mean_precision_at_3": 0.75,
        "mean_recall_at_5": 0.75,
        "mean_mrr": 0.75,
        "mean_ndcg_at_5": 0.5,
        "arithmetic_mean": 0.6875,
    }
