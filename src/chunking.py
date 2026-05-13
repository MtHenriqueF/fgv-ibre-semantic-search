"""Create text chunks from cleaned news articles."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

try:
    from .config import CHUNK_OVERLAP, CHUNK_SIZE, CHUNKS_PATH, CLEAN_NEWS_PATH
except ImportError:
    from config import CHUNK_OVERLAP, CHUNK_SIZE, CHUNKS_PATH, CLEAN_NEWS_PATH


CHUNK_SEPARATORS = ["\n\n", ". ", "! ", "? ", "; ", ", ", ".", "!", "?", " ", ""]


def date_to_int(date_value: str) -> int | None:
    if not date_value:
        return None

    normalized = date_value.replace("-", "")

    if not normalized.isdigit() or len(normalized) != 8:
        return None

    return int(normalized)


def load_clean_news(path: Path = CLEAN_NEWS_PATH) -> list[dict[str, Any]]:
    """Load cleaned news from JSON file."""
    if not path.exists():
        raise FileNotFoundError(f"Cleaned news file not found: {path}")

    with path.open("r", encoding="utf-8") as file:
        data = json.load(file)

    if not isinstance(data, list):
        raise ValueError("Expected cleaned news JSON to be a list of objects.")

    return data


def split_text_into_chunks(
    text: str,
    chunk_size: int = CHUNK_SIZE,
    chunk_overlap: int = CHUNK_OVERLAP,
) -> list[str]:
    """Split text with LangChain's recursive character splitter."""
    text = re.sub(r"\s+", " ", text or "").strip()
    if not text:
        return []

    try:
        from langchain_text_splitters import RecursiveCharacterTextSplitter
    except ImportError as exc:
        raise ImportError(
            "Install langchain-text-splitters to run chunking: "
            "python -m pip install langchain-text-splitters"
        ) from exc

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=CHUNK_SEPARATORS,
        length_function=len,
        is_separator_regex=False,
    )

    return [chunk.strip() for chunk in splitter.split_text(text) if chunk.strip()]


def build_document(titulo: str, texto_original_chunk: str) -> str:
    """Build natural text used for embeddings."""
    titulo = (titulo or "").strip()
    texto_original_chunk = (texto_original_chunk or "").strip()

    if titulo and texto_original_chunk:
        return f"{titulo}. {texto_original_chunk}"
    return titulo or texto_original_chunk


def create_chunks_from_articles(
    articles: list[dict[str, Any]],
    chunk_size: int = CHUNK_SIZE,
    chunk_overlap: int = CHUNK_OVERLAP,
) -> list[dict[str, Any]]:
    """Create chunk records with metadata preserved from cleaned articles."""
    chunks: list[dict[str, Any]] = []

    for article in articles:
        article_id = article.get("article_id")
        titulo = str(article.get("titulo", "")).strip()
        data = str(article.get("data", "")).strip()
        text_chunks = split_text_into_chunks(
            str(article.get("texto_limpo", "")),
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
        )

        for chunk_index, texto_original_chunk in enumerate(text_chunks):
            chunk_id = f"article_{article_id}_chunk_{chunk_index}"
            chunks.append(
                {
                    "chunk_id": chunk_id,
                    "article_id": article_id,
                    "chunk_index": chunk_index,
                    "document": build_document(titulo, texto_original_chunk),
                    "texto_original_chunk": texto_original_chunk,
                    "titulo": titulo,
                    "data": data,
                    "date_int": date_to_int(data),
                    "ano": article.get("ano"),
                    "mes": article.get("mes"),
                    "fonte": article.get("fonte"),
                    "content_quality": article.get("content_quality"),
                }
            )

    return chunks


def save_chunks_jsonl(chunks: list[dict[str, Any]], path: Path = CHUNKS_PATH) -> None:
    """Save chunks as JSON Lines."""
    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("w", encoding="utf-8") as file:
        for chunk in chunks:
            file.write(json.dumps(chunk, ensure_ascii=False) + "\n")


def run_chunking_pipeline(
    clean_path: Path = CLEAN_NEWS_PATH,
    chunks_path: Path = CHUNKS_PATH,
    chunk_size: int = CHUNK_SIZE,
    chunk_overlap: int = CHUNK_OVERLAP,
) -> list[dict[str, Any]]:
    """Load cleaned news, create chunks and save them to disk."""
    articles = load_clean_news(clean_path)
    chunks = create_chunks_from_articles(
        articles,
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
    )
    save_chunks_jsonl(chunks, chunks_path)
    return chunks


def main() -> None:
    chunks = run_chunking_pipeline()
    print(f"Chunking concluído. Chunks gerados: {len(chunks)}")
    print(f"Chunks salvos em: {CHUNKS_PATH}")


if __name__ == "__main__":
    main()
