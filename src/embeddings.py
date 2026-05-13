"""Embedding generation with sentence-transformers."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

try:
    from .config import EMBEDDING_MODEL_NAME
except ImportError:
    from config import EMBEDDING_MODEL_NAME


def load_embedding_model(model_name: str = EMBEDDING_MODEL_NAME) -> Any:
    """Load the configured sentence-transformers model."""
    from sentence_transformers import SentenceTransformer

    return SentenceTransformer(model_name)


def generate_embeddings(
    texts: Sequence[str],
    model: Any | None = None,
    model_name: str = EMBEDDING_MODEL_NAME,
    batch_size: int = 32,
) -> list[list[float]]:
    """Generate embeddings for a list of texts."""
    if model is None:
        model = load_embedding_model(model_name)

    try:
        embeddings = model.encode(
            list(texts),
            batch_size=batch_size,
            normalize_embeddings=True,
            show_progress_bar=False,
        )
    except TypeError:
        embeddings = model.encode(
            list(texts),
            batch_size=batch_size,
            show_progress_bar=False,
        )

    return [embedding.tolist() for embedding in embeddings]
