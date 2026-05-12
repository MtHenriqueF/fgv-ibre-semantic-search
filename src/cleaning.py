# src/cleaning.py

from __future__ import annotations

import csv
import html
import json
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from bs4 import BeautifulSoup

try:
    from .config import CLEANING_REPORT_PATH, CLEAN_NEWS_PATH, RAW_NEWS_PATH
except ImportError:
    from config import CLEANING_REPORT_PATH, CLEAN_NEWS_PATH, RAW_NEWS_PATH


@dataclass
class CleaningStats:
    article_id: int
    titulo: str
    fonte: str
    data: str
    raw_chars: int
    clean_chars: int
    reduction_pct: float
    content_quality: str
    warnings: list[str]


def load_raw_news(path: Path = RAW_NEWS_PATH) -> list[dict[str, Any]]:
    """Load raw news from JSON file."""
    if not path.exists():
        raise FileNotFoundError(f"Raw data file not found: {path}")

    with path.open("r", encoding="utf-8") as file:
        data = json.load(file)

    if not isinstance(data, list):
        raise ValueError("Expected raw news JSON to be a list of objects.")

    return data


def decode_html_entities(text: str) -> str:
    """Decode HTML entities such as &agrave;, &ccedil;, &nbsp;."""
    return html.unescape(text or "")


def strip_html_tags(text: str) -> str:
    """Remove HTML tags while preserving readable spacing."""
    soup = BeautifulSoup(text or "", "html.parser")

    # Remove script/style if they ever appear.
    for tag in soup(["script", "style"]):
        tag.decompose()

    return soup.get_text(separator=" ")


def remove_urls(text: str) -> str:
    """Remove raw URLs left after stripping anchor tags."""
    text = re.sub(r"https?://\S+", " ", text)
    text = re.sub(r"www\.\S+", " ", text)
    return text


def remove_embedded_metadata(text: str) -> str:
    """
    Remove common publication metadata embedded in the body.

    Examples in the dataset:
    - Publicado em: 02/08/2023 às 20h15
    - 23/08/2023 - 18h45 | Mercados
    - 25/08/2023 — Nota à Imprensa
    - Fonte: MDIC —
    """

    patterns = [
        # Publicado em: 02/08/2023 às 20h15
        r"\bPublicado em:\s*\d{2}/\d{2}/\d{4}(?:\s*(?:às|as)\s*\d{1,2}h\d{2})?\b",

        # 23/08/2023 - 18h45 | Mercados
        r"^\s*\d{2}/\d{2}/\d{4}\s*[-–—]\s*\d{1,2}h\d{2}(?:\s*\|\s*[^.?!\d]+?)?\s+(?=[A-ZÁÀÂÃÉÊÍÓÔÕÚÇ])",

        # 25/08/2023 — Nota à Imprensa
        r"^\s*\d{2}/\d{2}/\d{4}\s*[—–-]\s*Nota\s+à\s+Imprensa\s*",

        # Date alone at beginning: 07/08/2023
        r"^\s*\d{2}/\d{2}/\d{4}\s*",

        # Fonte: MDIC —
        r"\bFonte:\s*[^—\n]+[—-]?\s*",
    ]

    cleaned = text
    for pattern in patterns:
        cleaned = re.sub(pattern, " ", cleaned, flags=re.IGNORECASE)

    return cleaned


def normalize_whitespace(text: str) -> str:
    """Normalize repeated spaces, tabs and line breaks."""
    text = text.replace("\xa0", " ")
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def clean_text(raw_text: str) -> str:
    """
    Full text cleaning pipeline:
    HTML entity decoding → HTML tag removal → URL removal
    → metadata removal → whitespace normalization.
    """
    text = decode_html_entities(raw_text)
    text = strip_html_tags(text)
    text = remove_urls(text)
    text = remove_embedded_metadata(text)
    text = normalize_whitespace(text)
    return text


def classify_content_quality(clean_text_value: str) -> tuple[str, list[str]]:
    """Classify content quality and return warnings."""
    warnings: list[str] = []
    n_chars = len(clean_text_value)

    if n_chars == 0:
        warnings.append("empty_text_after_cleaning")
        return "empty", warnings

    if n_chars < 50:
        warnings.append("very_short_text")
        return "very_short", warnings

    if n_chars < 120:
        warnings.append("short_text")
        return "short", warnings

    return "ok", warnings


def parse_date_parts(date_value: str) -> tuple[int | None, int | None]:
    """Extract year and month from YYYY-MM-DD."""
    try:
        parsed = datetime.strptime(date_value, "%Y-%m-%d")
        return parsed.year, parsed.month
    except ValueError:
        return None, None


def clean_news_item(item: dict[str, Any]) -> tuple[dict[str, Any], CleaningStats]:
    """Clean and enrich one raw news item."""
    article_id = int(item["id"])
    titulo = str(item.get("titulo", "")).strip()
    raw_text = str(item.get("texto", ""))
    data = str(item.get("data", "")).strip()
    fonte = str(item.get("fonte", "")).strip()

    clean_text_value = clean_text(raw_text)
    ano, mes = parse_date_parts(data)
    content_quality, warnings = classify_content_quality(clean_text_value)

    raw_chars = len(raw_text)
    clean_chars = len(clean_text_value)
    reduction_pct = round(100 * (1 - clean_chars / raw_chars), 2) if raw_chars else 0.0

    cleaned_item = {
        "article_id": article_id,
        "titulo": titulo,
        "texto_limpo": clean_text_value,
        "data": data,
        "ano": ano,
        "mes": mes,
        "fonte": fonte,
        "content_quality": content_quality,
    }

    stats = CleaningStats(
        article_id=article_id,
        titulo=titulo,
        fonte=fonte,
        data=data,
        raw_chars=raw_chars,
        clean_chars=clean_chars,
        reduction_pct=reduction_pct,
        content_quality=content_quality,
        warnings=warnings,
    )

    return cleaned_item, stats


def save_clean_news(cleaned_news: list[dict[str, Any]], path: Path = CLEAN_NEWS_PATH) -> None:
    """Save cleaned news as JSON."""
    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("w", encoding="utf-8") as file:
        json.dump(cleaned_news, file, ensure_ascii=False, indent=2)


def save_cleaning_report(stats: list[CleaningStats], path: Path = CLEANING_REPORT_PATH) -> None:
    """Save cleaning report as CSV."""
    path.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = [
        "article_id",
        "titulo",
        "fonte",
        "data",
        "raw_chars",
        "clean_chars",
        "reduction_pct",
        "content_quality",
        "warnings",
    ]

    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()

        for item in stats:
            writer.writerow(
                {
                    "article_id": item.article_id,
                    "titulo": item.titulo,
                    "fonte": item.fonte,
                    "data": item.data,
                    "raw_chars": item.raw_chars,
                    "clean_chars": item.clean_chars,
                    "reduction_pct": item.reduction_pct,
                    "content_quality": item.content_quality,
                    "warnings": ";".join(item.warnings),
                }
            )


def run_cleaning_pipeline(
    raw_path: Path = RAW_NEWS_PATH,
    clean_path: Path = CLEAN_NEWS_PATH,
    report_path: Path = CLEANING_REPORT_PATH,
) -> list[dict[str, Any]]:
    """Run full cleaning pipeline and save outputs."""
    raw_news = load_raw_news(raw_path)

    cleaned_news: list[dict[str, Any]] = []
    cleaning_stats: list[CleaningStats] = []

    for item in raw_news:
        cleaned_item, stats = clean_news_item(item)
        cleaned_news.append(cleaned_item)
        cleaning_stats.append(stats)

    save_clean_news(cleaned_news, clean_path)
    save_cleaning_report(cleaning_stats, report_path)

    return cleaned_news


def main() -> None:
    cleaned_news = run_cleaning_pipeline()
    print(f"Limpeza concluída. Notícias processadas: {len(cleaned_news)}")
    print(f"Dados limpos salvos em: {CLEAN_NEWS_PATH}")
    print(f"Relatório de limpeza salvo em: {CLEANING_REPORT_PATH}")


if __name__ == "__main__":
    main()
