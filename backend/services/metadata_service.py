"""Metadata aggregation for frontend filters."""

from __future__ import annotations

from typing import Any

from src.chunking import load_clean_news


def get_metadata_options() -> dict[str, Any]:
    articles = _load_clean_news()
    fontes = sorted(
        {
            str(article["fonte"])
            for article in articles
            if article.get("fonte")
        }
    )
    dates = sorted(
        {
            str(article["data"])
            for article in articles
            if article.get("data")
        }
    )
    content_quality = sorted(
        {
            str(article["content_quality"])
            for article in articles
            if article.get("content_quality")
        }
    )

    return {
        "fontes": fontes,
        "date_min": dates[0] if dates else None,
        "date_max": dates[-1] if dates else None,
        "content_quality": content_quality,
    }


def _load_clean_news() -> list[dict[str, Any]]:
    return load_clean_news()
