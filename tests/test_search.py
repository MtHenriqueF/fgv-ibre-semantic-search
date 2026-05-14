from __future__ import annotations

import pytest

from src.config import CHROMA_COLLECTION_NAME
from src.search import build_chroma_where, search_semantic, validate_search_collection
from src.vector_store import get_chroma_client


def test_build_chroma_where_without_filters_returns_none() -> None:
    assert build_chroma_where(None) is None
    assert build_chroma_where({}) is None


def test_build_chroma_where_with_fonte_filter() -> None:
    assert build_chroma_where({"fonte": "Banco Central do Brasil"}) == {
        "fonte": "Banco Central do Brasil"
    }


def test_build_chroma_where_with_date_range_filter() -> None:
    assert build_chroma_where(
        {"date_start": "2023-08-01", "date_end": "2023-08-31"}
    ) == {
        "$and": [
            {"date_int": {"$gte": 20230801}},
            {"date_int": {"$lte": 20230831}},
        ]
    }


def test_search_semantic_with_valid_query_returns_results(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _patch_query_embedding(monkeypatch)

    response = search_semantic("mudanças na taxa de juros", top_k=3)

    assert response["search_type"] == "semantic"
    assert response["results"]


def test_search_result_contains_distance_and_similarity(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _patch_query_embedding(monkeypatch)

    response = search_semantic("mudanças na taxa de juros", top_k=3)
    first_result = response["results"][0]

    assert "distance" in first_result
    assert "similarity" in first_result
    assert first_result["similarity"] == pytest.approx(1 - first_result["distance"])


def test_min_similarity_filters_all_results(monkeypatch: pytest.MonkeyPatch) -> None:
    _patch_query_embedding(monkeypatch)

    response = search_semantic("receita de bolo de chocolate", top_k=5)
    max_similarity = max(result["similarity"] for result in response["results"])

    filtered = search_semantic(
        "receita de bolo de chocolate",
        top_k=5,
        min_similarity=max_similarity + 0.01,
    )

    assert filtered["results"] == []


def test_validate_search_collection_returns_indexed_documents() -> None:
    status = validate_search_collection()

    assert status["count"] > 0
    assert status["has_documents"] is True
    assert status["has_required_metadata"] is True
    assert status["returns_distances"] is True


def _patch_query_embedding(monkeypatch: pytest.MonkeyPatch) -> None:
    pytest.importorskip("chromadb")
    embedding = _sample_indexed_embedding()

    def fake_generate_embeddings(texts: list[str]) -> list[list[float]]:
        return [embedding for _ in texts]

    monkeypatch.setattr("src.search.generate_embeddings", fake_generate_embeddings)


def _sample_indexed_embedding() -> list[float]:
    client = get_chroma_client()
    collection = client.get_collection(CHROMA_COLLECTION_NAME)
    sample = collection.get(limit=1, include=["embeddings"])
    embeddings = sample.get("embeddings")

    if embeddings is None:
        pytest.skip("ChromaDB did not return sample embeddings.")
    if hasattr(embeddings, "tolist"):
        embeddings = embeddings.tolist()
    if not embeddings:
        pytest.skip("ChromaDB collection has no sample embeddings.")

    first_embedding = embeddings[0]
    if hasattr(first_embedding, "tolist"):
        first_embedding = first_embedding.tolist()
    return [float(value) for value in first_embedding]
