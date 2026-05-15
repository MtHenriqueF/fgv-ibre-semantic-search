from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient

from backend.main import app


pytestmark = pytest.mark.anyio


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


@pytest.fixture
async def client() -> AsyncClient:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as api_client:
        yield api_client


async def test_health_endpoint(client: AsyncClient) -> None:
    response = await client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": "fgv-ibre-semantic-search",
    }


async def test_search_endpoint_uses_semantic_service(
    client: AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_search_semantic(
        query: str,
        top_k: int,
        filters: dict[str, str] | None,
        min_similarity: float | None,
    ) -> dict:
        return {
            "query": query,
            "search_type": "semantic",
            "top_k": top_k,
            "filters": filters,
            "min_similarity": min_similarity,
            "results": [
                {
                    "rank": 1,
                    "article_id": 6,
                    "chunk_id": "article_6_chunk_0",
                    "chunk_index": 0,
                    "titulo": "Copom inicia ciclo de corte e reduz Selic para 13,25%",
                    "data": "2023-08-02",
                    "ano": 2023,
                    "mes": 8,
                    "fonte": "Valor Econômico",
                    "content_quality": "ok",
                    "document": "Copom inicia ciclo de corte e reduz Selic.",
                    "distance": 0.18,
                    "similarity": 0.82,
                }
            ],
        }

    monkeypatch.setattr(
        "backend.services.search_service.search_semantic",
        fake_search_semantic,
    )

    response = await client.post(
        "/api/search",
        json={
            "query": "mudanças na taxa de juros",
            "top_k": 5,
            "min_similarity": 0.35,
            "filters": {"fonte": "Valor Econômico"},
        },
    )

    assert response.status_code == 200
    assert response.json()["filters"] == {"fonte": "Valor Econômico"}
    assert response.json()["results"][0]["article_id"] == 6


async def test_metadata_endpoint_returns_filter_options(client: AsyncClient) -> None:
    response = await client.get("/api/metadata")

    assert response.status_code == 200
    assert "Banco Central do Brasil" in response.json()["fontes"]
    assert response.json()["date_min"] == "2023-07-31"
    assert response.json()["date_max"] == "2023-09-05"


async def test_document_endpoint_returns_clean_document(client: AsyncClient) -> None:
    response = await client.get("/api/documents/6")

    assert response.status_code == 200
    assert response.json()["article_id"] == 6
    assert response.json()["content_quality"] == "ok"


async def test_document_endpoint_returns_404_for_unknown_article(client: AsyncClient) -> None:
    response = await client.get("/api/documents/999")

    assert response.status_code == 404
    assert "article_id=999" in response.json()["detail"]


async def test_evaluation_endpoint_returns_metrics_and_relevance_grades(
    client: AsyncClient,
) -> None:
    response = await client.get("/api/evaluation")

    assert response.status_code == 200
    payload = response.json()
    assert payload["search_type"] == "semantic"
    assert payload["metrics_summary"]["mean_mrr"] == 1.0
    assert payload["queries"][0]["results"][0]["chunk_id"] == "article_1_chunk_0"
    assert payload["queries"][0]["results"][0]["relevance_grade"] == 3


async def test_search_examples_endpoint_enriches_chunk_metadata(
    client: AsyncClient,
) -> None:
    response = await client.get("/api/search/examples")

    assert response.status_code == 200
    first_result = response.json()["examples"][0]["results"][0]
    assert first_result["chunk_id"] == "article_1_chunk_0"
    assert first_result["chunk_index"] == 0
