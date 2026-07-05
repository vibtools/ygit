from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from backend.engines.repository_engine.internal.service import RepositoryInternalService
from backend.engines.repository_engine.schemas import (
    ParsedRepositoryUrl,
    RepositoryAnalysisInput,
    RepositoryDetail,
    RepositoryMetadataInput,
    RepositoryValidateInput,
    RepositoryValidationResult,
)


class RepositoryPublicService:
    """Public Repository Engine API. Other layers must not import internal services directly."""

    def __init__(self, internal: RepositoryInternalService | None = None) -> None:
        self._internal = internal or RepositoryInternalService()

    async def parse_repository_url(self, repository_url: str) -> ParsedRepositoryUrl:
        return await self._internal.parse_repository_url(repository_url)

    async def validate_repository_url(self, input_data: RepositoryValidateInput) -> RepositoryValidationResult:
        return await self._internal.validate_repository_url(input_data)

    async def fetch_repository_metadata(
        self,
        db: AsyncSession,
        *,
        user_id: str,
        input_data: RepositoryMetadataInput,
    ) -> RepositoryDetail:
        return await self._internal.fetch_repository_metadata(db, user_id=user_id, input_data=input_data)

    async def get_repository_metadata(self, db: AsyncSession, *, user_id: str, repository_id: str) -> RepositoryDetail:
        return await self._internal.get_repository_metadata(db, user_id=user_id, repository_id=repository_id)

    async def prepare_analysis_input(self, db: AsyncSession, *, user_id: str, repository_id: str) -> RepositoryAnalysisInput:
        return await self._internal.prepare_analysis_input(db, user_id=user_id, repository_id=repository_id)


repository_service = RepositoryPublicService()
