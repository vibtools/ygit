from __future__ import annotations

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.dependencies.auth import require_user
from backend.core.database import get_db_session
from backend.core.responses import success_response
from backend.engines.auth_engine.schemas import CurrentUser
from backend.engines.repository_engine.public import repository_service
from backend.engines.repository_engine.schemas import RepositoryMetadataInput, RepositoryValidateInput

router = APIRouter(prefix="/repositories", tags=["Repositories"])


@router.post("/validate")
async def validate_repository(
    input_data: RepositoryValidateInput,
    user: CurrentUser = Depends(require_user),
):
    result = await repository_service.validate_repository_url(input_data)
    return success_response(result.model_dump(mode="json"))


@router.post("/metadata", status_code=status.HTTP_201_CREATED)
async def fetch_metadata(
    input_data: RepositoryMetadataInput,
    user: CurrentUser = Depends(require_user),
    db: AsyncSession = Depends(get_db_session),
):
    repository = await repository_service.fetch_repository_metadata(db, user_id=user.id, input_data=input_data)
    return success_response({"repository": repository.model_dump(mode="json")}, status_code=status.HTTP_201_CREATED)


@router.get("/{repository_id}")
async def get_repository(
    repository_id: str,
    user: CurrentUser = Depends(require_user),
    db: AsyncSession = Depends(get_db_session),
):
    repository = await repository_service.get_repository_metadata(db, user_id=user.id, repository_id=repository_id)
    return success_response({"repository": repository.model_dump(mode="json")})
