from __future__ import annotations

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.dependencies.auth import require_user
from backend.core.database import get_db_session
from backend.core.responses import success_response
from backend.engines.auth_engine.schemas import CurrentUser
from backend.engines.repository_analysis_engine.public import repository_analysis_service
from backend.engines.repository_analysis_engine.schemas import AnalysisInput, AnalysisRecalculateInput

router = APIRouter(prefix="/repository-analysis", tags=["Repository Analysis"])


@router.post("/quick")
async def run_quick_analysis(
    input_data: AnalysisInput,
    user: CurrentUser = Depends(require_user),
    db: AsyncSession = Depends(get_db_session),
):
    analysis = await repository_analysis_service.run_quick_analysis(db, user_id=user.id, repository_id=input_data.repository_id)
    return success_response({"analysis": analysis.model_dump(mode="json")})


@router.post("/deep", status_code=status.HTTP_202_ACCEPTED)
async def queue_deep_analysis(
    input_data: AnalysisInput,
    user: CurrentUser = Depends(require_user),
    db: AsyncSession = Depends(get_db_session),
):
    job = await repository_analysis_service.queue_deep_analysis(db, user_id=user.id, repository_id=input_data.repository_id)
    return success_response({"job": job.model_dump(mode="json")}, status_code=status.HTTP_202_ACCEPTED)


@router.get("/{analysis_id}")
async def get_analysis(
    analysis_id: str,
    user: CurrentUser = Depends(require_user),
    db: AsyncSession = Depends(get_db_session),
):
    analysis = await repository_analysis_service.get_analysis_result(db, user_id=user.id, analysis_id=analysis_id)
    return success_response({"analysis": analysis.model_dump(mode="json")})


@router.post("/{analysis_id}/recalculate")
async def recalculate_analysis(
    analysis_id: str,
    input_data: AnalysisRecalculateInput | None = None,
    user: CurrentUser = Depends(require_user),
    db: AsyncSession = Depends(get_db_session),
):
    _ = input_data
    analysis = await repository_analysis_service.recalculate_analysis(db, user_id=user.id, analysis_id=analysis_id)
    return success_response({"analysis": analysis.model_dump(mode="json")})
