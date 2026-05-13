from pathlib import Path

import pytest

from src.chunking import create_chunks_from_articles, date_to_int, save_chunks_jsonl
from src.vector_store import get_chroma_client, get_or_create_collection, prepare_chroma_payload


def test_date_to_int() -> None:
    assert date_to_int("2023-08-07") == 20230807
    assert date_to_int("") is None
    assert date_to_int("data-invalida") is None


def test_create_chunks_with_required_fields(tmp_path: Path) -> None:
    articles = [
        {
            "article_id": 8,
            "titulo": "Exportações brasileiras somam recorde em julho",
            "texto_limpo": "As exportações brasileiras totalizaram US$ 32,4 bilhões em julho.",
            "data": "2023-08-07",
            "ano": 2023,
            "mes": 8,
            "fonte": "MDIC",
            "content_quality": "ok",
        }
    ]

    chunks = create_chunks_from_articles(articles)
    output_path = tmp_path / "chunks.jsonl"
    save_chunks_jsonl(chunks, output_path)

    assert output_path.exists()
    assert len(chunks) == 1

    chunk = chunks[0]
    assert chunk["date_int"] == 20230807
    assert chunk["document"] == (
        "Exportações brasileiras somam recorde em julho. "
        "As exportações brasileiras totalizaram US$ 32,4 bilhões em julho."
    )

    required_fields = {
        "chunk_id",
        "article_id",
        "chunk_index",
        "document",
        "texto_original_chunk",
        "titulo",
        "data",
        "date_int",
        "ano",
        "mes",
        "fonte",
        "content_quality",
    }
    assert required_fields.issubset(chunk)


def test_prepare_chroma_payload_includes_date_int() -> None:
    chunks = create_chunks_from_articles(
        [
            {
                "article_id": 1,
                "titulo": "Copom mantém Selic",
                "texto_limpo": "O Copom manteve a taxa básica de juros.",
                "data": "2023-08-02",
                "ano": 2023,
                "mes": 8,
                "fonte": "Banco Central do Brasil",
                "content_quality": "ok",
            }
        ]
    )

    ids, documents, metadatas = prepare_chroma_payload(chunks)

    assert ids == ["article_1_chunk_0"]
    assert documents == ["Copom mantém Selic. O Copom manteve a taxa básica de juros."]
    assert metadatas[0]["date_int"] == 20230802
    assert "texto_original_chunk" not in metadatas[0]


def test_chromadb_can_create_local_test_collection(tmp_path: Path) -> None:
    pytest.importorskip("chromadb")

    client = get_chroma_client(tmp_path / "chroma_db")
    collection = get_or_create_collection(client, "test_fgv_ibre_news_chunks")

    assert collection.name == "test_fgv_ibre_news_chunks"
