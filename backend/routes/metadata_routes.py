"""Metadata routes used to populate frontend filters."""

from fastapi import APIRouter, HTTPException, status

from backend.schemas import MetadataResponse
from backend.services import metadata_service


router = APIRouter(prefix="/api", tags=["metadata"])


@router.get("/metadata", response_model=MetadataResponse)
async def metadata() -> dict:
    try:
        return metadata_service.get_metadata_options()
    except FileNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Processed data file not found: {exc.filename}",
        ) from exc
