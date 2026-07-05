from __future__ import annotations

from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.dependencies.auth import require_user
from backend.core.database import get_db_session
from backend.core.responses import success_response
from backend.engines.auth_engine.schemas import CurrentUser
from backend.engines.deploy_engine.public import deploy_service
from backend.engines.deploy_engine.schemas import RedeployRequestInput
from backend.engines.deployment_history_engine.public import deployment_history_service

router = APIRouter(prefix="/deployments", tags=["Deployments"])


@router.get("/{deployment_id}")
async def get_deployment(
    deployment_id: str,
    user: CurrentUser = Depends(require_user),
    db: AsyncSession = Depends(get_db_session),
):
    deployment = await deploy_service.get_deployment(db, user_id=user.id, deployment_id=deployment_id)
    return success_response({"deployment": deployment.model_dump(mode="json")})


@router.post("/{deployment_id}/redeploy", status_code=status.HTTP_202_ACCEPTED)
async def redeploy(
    deployment_id: str,
    request: Request,
    input_data: RedeployRequestInput | None = None,
    user: CurrentUser = Depends(require_user),
    db: AsyncSession = Depends(get_db_session),
):
    trace_id = getattr(request.state, "trace_id", None)
    result = await deploy_service.request_redeploy(
        db,
        user_id=user.id,
        deployment_id=deployment_id,
        input_data=input_data,
        trace_id=trace_id,
    )
    return success_response(result.model_dump(mode="json"), status_code=status.HTTP_202_ACCEPTED)


@router.post("/{deployment_id}/cancel")
async def cancel(
    deployment_id: str,
    user: CurrentUser = Depends(require_user),
    db: AsyncSession = Depends(get_db_session),
):
    result = await deploy_service.cancel_deployment(db, user_id=user.id, deployment_id=deployment_id)
    return success_response(result.model_dump(mode="json"))


@router.get("/{deployment_id}/logs")
async def logs(
    deployment_id: str,
    user: CurrentUser = Depends(require_user),
    db: AsyncSession = Depends(get_db_session),
):
    result = await deployment_history_service.get_deployment_logs(
        db,
        user_id=user.id,
        deployment_id=deployment_id,
    )
    return success_response(result.model_dump(mode="json"))
