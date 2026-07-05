from __future__ import annotations

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.dependencies.auth import require_user
from backend.core.database import get_db_session
from backend.core.responses import success_response
from backend.engines.auth_engine.schemas import CurrentUser
from backend.engines.domain_engine.public import domain_service
from backend.engines.domain_engine.schemas import DomainCheckInput

router = APIRouter(prefix="/domains", tags=["Domains"])


@router.post("/check")
async def check_slug_availability(
    input_data: DomainCheckInput,
    user: CurrentUser = Depends(require_user),
    db: AsyncSession = Depends(get_db_session),
):
    _ = user
    result = await domain_service.check_slug_availability(db, input_data=input_data)
    return success_response(result.model_dump(mode="json"), status_code=status.HTTP_200_OK)
