from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from backend.engines.repository_engine.errors import (
    RepositoryAccessDeniedError,
    RepositoryDefaultBranchMissingError,
    RepositoryMetadataFetchFailedError,
    RepositoryNotFoundError,
)
from backend.engines.repository_engine.internal.validators import parse_github_repository_url
from backend.engines.repository_engine.repository import RepositoryMetadataRepository
from backend.engines.repository_engine.schemas import (
    ParsedRepositoryUrl,
    RepositoryAnalysisInput,
    RepositoryDetail,
    RepositoryMetadataInput,
    RepositoryProviderMetadata,
    RepositoryRecord,
    RepositorySummary,
    RepositoryValidateInput,
    RepositoryValidationResult,
)
from backend.providers.github_provider.client import GitHubProviderClient
from backend.providers.github_provider.errors import GitHubProviderError, GitHubRepositoryNotFoundError


class RepositoryInternalService:
    def __init__(
        self,
        repository: RepositoryMetadataRepository | None = None,
        github_provider: GitHubProviderClient | None = None,
    ) -> None:
        self.repository = repository or RepositoryMetadataRepository()
        self.github_provider = github_provider or GitHubProviderClient()

    async def parse_repository_url(self, repository_url: str) -> ParsedRepositoryUrl:
        return parse_github_repository_url(repository_url)

    async def validate_repository_url(self, input_data: RepositoryValidateInput) -> RepositoryValidationResult:
        parsed = await self.parse_repository_url(input_data.repository_url)
        return RepositoryValidationResult(
            valid=True,
            provider=parsed.provider,
            owner=parsed.owner,
            repo=parsed.repo,
            normalized_url=parsed.normalized_url,
        )

    async def fetch_repository_metadata(
        self,
        db: AsyncSession,
        *,
        user_id: str,
        input_data: RepositoryMetadataInput,
    ) -> RepositoryDetail:
        parsed = await self.parse_repository_url(input_data.repository_url)
        try:
            provider_result = await self.github_provider.get_repository_metadata(owner=parsed.owner, repo=parsed.repo)
        except GitHubRepositoryNotFoundError as exc:
            raise RepositoryNotFoundError() from exc
        except GitHubProviderError as exc:
            raise RepositoryMetadataFetchFailedError() from exc

        provider_metadata = RepositoryProviderMetadata(
            provider="github",
            repository_url=parsed.normalized_url,
            owner=provider_result.owner,
            name=provider_result.name,
            default_branch=provider_result.default_branch,
            visibility=provider_result.visibility,
            latest_commit_sha=provider_result.latest_commit_sha,
            file_tree_snapshot=provider_result.file_tree_snapshot,
            metadata=provider_result.metadata,
        )
        if provider_metadata.default_branch is None:
            raise RepositoryDefaultBranchMissingError()
        record = await self.repository.upsert_metadata(db, user_id=user_id, provider_metadata=provider_metadata)
        await db.commit()
        return self.to_detail(record)

    async def get_repository_metadata(self, db: AsyncSession, *, user_id: str, repository_id: str) -> RepositoryDetail:
        model = await self.repository.get_active_by_id(db, repository_id)
        if model is None:
            raise RepositoryNotFoundError()
        if model.user_id != user_id:
            raise RepositoryAccessDeniedError()
        return self.to_detail(self.repository.to_record(model))

    async def prepare_analysis_input(self, db: AsyncSession, *, user_id: str, repository_id: str) -> RepositoryAnalysisInput:
        detail = await self.get_repository_metadata(db, user_id=user_id, repository_id=repository_id)
        return RepositoryAnalysisInput(
            repository_id=detail.id,
            provider=detail.provider,
            repository_url=detail.repository_url,
            owner=detail.owner,
            repo=detail.name,
            default_branch=detail.default_branch,
            visibility=detail.visibility,
            latest_commit_sha=detail.latest_commit_sha,
            file_tree_snapshot=detail.file_tree_snapshot,
        )

    def to_summary(self, record: RepositoryRecord) -> RepositorySummary:
        return RepositorySummary(**record.model_dump())

    def to_detail(self, record: RepositoryRecord) -> RepositoryDetail:
        return RepositoryDetail(**record.model_dump())
