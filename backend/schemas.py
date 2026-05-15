"""Pydantic schemas exposed by the FastAPI backend."""

from __future__ import annotations

from pydantic import BaseModel, Field


class SearchFilters(BaseModel):
    fonte: str | None = None
    date_start: str | None = None
    date_end: str | None = None
    content_quality: str | None = None


class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1)
    top_k: int = Field(default=5, ge=1)
    min_similarity: float | None = None
    filters: SearchFilters | None = None


class SearchResult(BaseModel):
    rank: int
    article_id: int
    chunk_id: str
    chunk_index: int | None
    titulo: str
    data: str
    ano: int | None
    mes: int | None
    fonte: str
    content_quality: str | None
    document: str
    distance: float
    similarity: float


class SearchResponse(BaseModel):
    query: str
    search_type: str
    top_k: int
    min_similarity: float | None
    filters: dict[str, str] | None
    results: list[SearchResult]


class MetadataResponse(BaseModel):
    fontes: list[str]
    date_min: str | None
    date_max: str | None
    content_quality: list[str]


class DocumentResponse(BaseModel):
    article_id: int
    titulo: str
    texto_limpo: str
    data: str
    ano: int | None
    mes: int | None
    fonte: str
    content_quality: str | None


class SearchExampleResult(BaseModel):
    rank: int
    article_id: int
    chunk_id: str | None
    chunk_index: int | None
    titulo: str
    fonte: str
    data: str
    distance: float
    similarity: float


class SearchExample(BaseModel):
    query: str
    results: list[SearchExampleResult]


class SearchExamplesResponse(BaseModel):
    examples: list[SearchExample]


class EvaluationMetrics(BaseModel):
    precision_at_3: float
    recall_at_5: float
    mrr: float
    ndcg_at_5: float


class EvaluationMetricsSummary(BaseModel):
    mean_precision_at_3: float
    mean_recall_at_5: float
    mean_mrr: float
    mean_ndcg_at_5: float


class EvaluationResult(SearchExampleResult):
    relevance_grade: int


class EvaluationQuery(BaseModel):
    query: str
    metrics: EvaluationMetrics
    results: list[EvaluationResult]


class EvaluationResponse(BaseModel):
    search_type: str
    description: str
    metrics_summary: EvaluationMetricsSummary
    queries: list[EvaluationQuery]
