"""ChromaDB vector store indexing for news chunks."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

try:
    from .config import CHROMA_COLLECTION_NAME, CHROMA_DB_DIR, CHUNKS_PATH
    from .embeddings import generate_embeddings
except ImportError:
    from config import CHROMA_COLLECTION_NAME, CHROMA_DB_DIR, CHUNKS_PATH
    from embeddings import generate_embeddings


CHROMA_METADATA_FIELDS = [
    "article_id",
    "chunk_id",
    "chunk_index",
    "titulo",
    "data",
    "date_int",
    "ano",
    "mes",
    "fonte",
    "content_quality",
]


def load_chunks(path: Path = CHUNKS_PATH) -> list[dict[str, Any]]:
    """Load chunks from JSON Lines."""
    if not path.exists():
        raise FileNotFoundError(f"Chunks file not found: {path}")

    chunks: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as file:
        for line in file:
            line = line.strip()
            if line:
                chunks.append(json.loads(line))

    return chunks


def prepare_chroma_payload(
    chunks: list[dict[str, Any]],
) -> tuple[list[str], list[str], list[dict[str, Any]]]:
    """Prepare ids, documents and metadatas for ChromaDB insertion."""
    ids: list[str] = []
    documents: list[str] = []
    metadatas: list[dict[str, Any]] = []

    for chunk in chunks:
        chunk_id = str(chunk["chunk_id"])
        document = str(chunk["document"])
        metadata = {field: _chroma_metadata_value(chunk.get(field)) for field in CHROMA_METADATA_FIELDS}

        ids.append(chunk_id)
        documents.append(document)
        metadatas.append(metadata)

    return ids, documents, metadatas


def _chroma_metadata_value(value: Any) -> str | int | float | bool:
    """Convert metadata values to Chroma-compatible scalar values."""
    if value is None:
        return ""
    if isinstance(value, str | int | float | bool):
        return value
    return str(value)


def get_chroma_client(persist_directory: Path = CHROMA_DB_DIR) -> Any:
    """Create a persistent ChromaDB client."""
    import chromadb

    persist_directory.mkdir(parents=True, exist_ok=True)
    return chromadb.PersistentClient(path=str(persist_directory))


def get_or_create_collection(
    client: Any,
    collection_name: str = CHROMA_COLLECTION_NAME,
) -> Any:
    """Create a collection configured for cosine distance, with version fallback."""
    try:
        from chromadb.api.collection_configuration import (
            CreateCollectionConfiguration,
            HnswConfiguration,
        )

        configuration = CreateCollectionConfiguration(
            hnsw=HnswConfiguration(space="cosine")
        )
        return client.get_or_create_collection(
            name=collection_name,
            configuration=configuration,
        )
    except (ImportError, TypeError, ValueError):
        return client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"},
        )


def delete_collection_if_exists(
    client: Any,
    collection_name: str = CHROMA_COLLECTION_NAME,
) -> None:
    """Delete a collection if it already exists."""
    existing_collections = client.list_collections()
    existing_names = {
        collection if isinstance(collection, str) else collection.name
        for collection in existing_collections
    }

    if collection_name in existing_names:
        client.delete_collection(collection_name)


def index_chunks(
    chunks: list[dict[str, Any]],
    persist_directory: Path = CHROMA_DB_DIR,
    collection_name: str = CHROMA_COLLECTION_NAME,
    rebuild: bool = True,
) -> Any:
    """Index chunks in ChromaDB, generating embeddings from the document field."""
    if not chunks:
        raise ValueError("Cannot index an empty chunk list.")

    client = get_chroma_client(persist_directory)
    if rebuild:
        delete_collection_if_exists(client, collection_name)

    collection = get_or_create_collection(client, collection_name)
    ids, documents, metadatas = prepare_chroma_payload(chunks)
    embeddings = generate_embeddings(documents)

    collection.add(
        ids=ids,
        documents=documents,
        embeddings=embeddings,
        metadatas=metadatas,
    )

    return collection


def rebuild_vector_store(
    chunks_path: Path = CHUNKS_PATH,
    persist_directory: Path = CHROMA_DB_DIR,
    collection_name: str = CHROMA_COLLECTION_NAME,
) -> Any:
    """Rebuild the local ChromaDB collection from chunks.jsonl."""
    chunks = load_chunks(chunks_path)
    return index_chunks(
        chunks,
        persist_directory=persist_directory,
        collection_name=collection_name,
        rebuild=True,
    )


def main() -> None:
    collection = rebuild_vector_store()
    print(f"Indexação vetorial concluída. Coleção: {collection.name}")
    print(f"ChromaDB salvo em: {CHROMA_DB_DIR}")


if __name__ == "__main__":
    main()
