"""Semantic-search routes."""

from fastapi import APIRouter, HTTPException, status

from backend.schemas import SearchExamplesResponse, SearchRequest, SearchResponse
from backend.services import evaluation_service, search_service


router = APIRouter(prefix="/api/search", tags=["search"])


@router.post("", response_model=SearchResponse)
async def search(payload: SearchRequest) -> dict:
    try:
        return search_service.run_semantic_search(payload)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc


@router.get("/examples", response_model=SearchExamplesResponse)
async def search_examples() -> dict:
    return evaluation_service.get_search_examples()
