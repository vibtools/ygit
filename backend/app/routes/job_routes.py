from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.dependencies.auth import require_user
from backend.core.database import get_db_session
from backend.core.responses import success_response
from backend.engines.auth_engine.schemas import CurrentUser
from backend.workers.public import job_system

router = APIRouter(prefix="/jobs", tags=["Jobs"])


@router.get("/{job_id}")
async def get_job(
    job_id: str,
    request: Request,
    user: CurrentUser = Depends(require_user),
    db: AsyncSession = Depends(get_db_session),
):
    job = await job_system.get_job_for_user(db, user_id=user.id, job_id=job_id)
    return success_response(
        {"job": job.model_dump(mode="json")},
        meta={"trace_id": getattr(request.state, "trace_id", None)},
    )
