"""Document lookup over cleaned processed news."""

from __future__ import annotations

from typing import Any

from src.chunking import load_clean_news


class DocumentNotFoundError(LookupError):
    """Raised when an article id is absent from processed news."""


def get_document_by_article_id(article_id: int) -> dict[str, Any]:
    for article in _load_clean_news():
        if int(article["article_id"]) == article_id:
            return article

    raise DocumentNotFoundError(f"Article with article_id={article_id} was not found.")


def _load_clean_news() -> list[dict[str, Any]]:
    return load_clean_news()
