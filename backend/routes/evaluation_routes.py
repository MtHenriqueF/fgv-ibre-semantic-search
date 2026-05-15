"""Evaluation-mode routes."""

from fastapi import APIRouter

from backend.schemas import EvaluationResponse
from backend.services import evaluation_service


router = APIRouter(prefix="/api", tags=["evaluation"])


@router.get("/evaluation", response_model=EvaluationResponse)
async def evaluation() -> dict:
    return evaluation_service.get_evaluation_mode_payload()
