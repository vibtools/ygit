from __future__ import annotations

from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.dependencies.auth import require_user
from backend.core.database import get_db_session
from backend.core.responses import success_response
from backend.engines.deploy_engine.public import deploy_service
from backend.engines.deploy_engine.schemas import DeploymentRequestInput
from backend.engines.deployment_history_engine.public import deployment_history_service
from backend.engines.domain_engine.public import domain_service
from backend.engines.auth_engine.schemas import CurrentUser
from backend.engines.domain_engine.schemas import DomainReserveInput
from backend.engines.project_engine.public import project_service
from backend.engines.project_engine.schemas import ProjectCreateInput, ProjectListFilters, ProjectUpdateInput

router = APIRouter(prefix="/projects", tags=["Projects"])


@router.get("")
async def list_projects(
    page: int = 1,
    page_size: int = 20,
    status_filter: str | None = Query(default=None, alias="status"),
    search: str | None = None,
    user: CurrentUser = Depends(require_user),
    db: AsyncSession = Depends(get_db_session),
):
    filters = ProjectListFilters(page=page, page_size=page_size, status=status_filter, search=search)
    result = await project_service.list_projects(db, user_id=user.id, filters=filters)
    return success_response(result.model_dump(mode="json"))


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_project(
    input_data: ProjectCreateInput,
    user: CurrentUser = Depends(require_user),
    db: AsyncSession = Depends(get_db_session),
):
    project = await project_service.create_project(db, user_id=user.id, input_data=input_data)
    return success_response({"project": project.model_dump(mode="json")}, status_code=status.HTTP_201_CREATED)


@router.get("/{project_id}")
async def get_project(
    project_id: str,
    user: CurrentUser = Depends(require_user),
    db: AsyncSession = Depends(get_db_session),
):
    project = await project_service.get_project(db, user_id=user.id, project_id=project_id)
    return success_response({"project": project.model_dump(mode="json")})


@router.patch("/{project_id}")
async def update_project(
    project_id: str,
    input_data: ProjectUpdateInput,
    user: CurrentUser = Depends(require_user),
    db: AsyncSession = Depends(get_db_session),
):
    project = await project_service.rename_project(db, user_id=user.id, project_id=project_id, input_data=input_data)
    return success_response({"project": project.model_dump(mode="json")})


@router.delete("/{project_id}")
async def delete_project(
    project_id: str,
    user: CurrentUser = Depends(require_user),
    db: AsyncSession = Depends(get_db_session),
):
    result = await project_service.delete_project(db, user_id=user.id, project_id=project_id)
    return success_response(result.model_dump(mode="json"))


@router.get("/{project_id}/readiness")
async def get_project_readiness(
    project_id: str,
    user: CurrentUser = Depends(require_user),
    db: AsyncSession = Depends(get_db_session),
):
    result = await deploy_service.validate_deploy_ready(
        db,
        user_id=user.id,
        project_id=project_id,
    )
    return success_response(
        {
            "readiness": result.model_dump(
                mode="json"
            )
        }
    )


@router.post("/{project_id}/deploy", status_code=status.HTTP_202_ACCEPTED)
async def deploy_project(
    project_id: str,
    request: Request,
    input_data: DeploymentRequestInput | None = None,
    user: CurrentUser = Depends(require_user),
    db: AsyncSession = Depends(get_db_session),
):
    trace_id = getattr(request.state, "trace_id", None)
    result = await deploy_service.request_deployment(
        db,
        user_id=user.id,
        project_id=project_id,
        input_data=input_data,
        trace_id=trace_id,
    )
    return success_response(result.model_dump(mode="json"), status_code=status.HTTP_202_ACCEPTED)


@router.get("/{project_id}/deployments")
async def list_project_deployments(
    project_id: str,
    page: int = 1,
    page_size: int = 20,
    user: CurrentUser = Depends(require_user),
    db: AsyncSession = Depends(get_db_session),
):
    result = await deployment_history_service.list_project_deployments(
        db,
        user_id=user.id,
        project_id=project_id,
        page=page,
        page_size=page_size,
    )
    return success_response(result.model_dump(mode="json"))


@router.post("/{project_id}/domain", status_code=status.HTTP_201_CREATED)
async def reserve_project_domain(
    project_id: str,
    input_data: DomainReserveInput,
    user: CurrentUser = Depends(require_user),
    db: AsyncSession = Depends(get_db_session),
):
    domain = await domain_service.reserve_project_slug(
        db,
        user_id=user.id,
        project_id=project_id,
        input_data=input_data,
    )
    return success_response({"domain": domain.model_dump(mode="json")}, status_code=status.HTTP_201_CREATED)


@router.get("/{project_id}/domain")
async def get_project_domain(
    project_id: str,
    user: CurrentUser = Depends(require_user),
    db: AsyncSession = Depends(get_db_session),
):
    domain = await domain_service.get_project_domain(db, user_id=user.id, project_id=project_id)
    return success_response({"domain": domain.model_dump(mode="json")})


@router.delete("/{project_id}/domain")
async def release_project_domain(
    project_id: str,
    user: CurrentUser = Depends(require_user),
    db: AsyncSession = Depends(get_db_session),
):
    result = await domain_service.release_project_domain(db, user_id=user.id, project_id=project_id)
    return success_response(result.model_dump(mode="json"))
