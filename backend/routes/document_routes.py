"""Document-detail routes."""

from fastapi import APIRouter, HTTPException, status

from backend.schemas import DocumentResponse
from backend.services import document_service


router = APIRouter(prefix="/api/documents", tags=["documents"])


@router.get("/{article_id}", response_model=DocumentResponse)
async def document(article_id: int) -> dict:
    try:
        return document_service.get_document_by_article_id(article_id)
    except document_service.DocumentNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except FileNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Processed data file not found: {exc.filename}",
        ) from exc
