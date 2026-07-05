from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.ids import new_id
from backend.engines.repository_engine.models import RepositoryMetadataModel
from backend.engines.repository_engine.schemas import RepositoryProviderMetadata, RepositoryRecord


class RepositoryMetadataRepository:
    """Database repository owned by Repository Engine only."""

    async def get_by_id(self, db: AsyncSession, repository_id: str) -> RepositoryMetadataModel | None:
        result = await db.execute(select(RepositoryMetadataModel).where(RepositoryMetadataModel.id == repository_id))
        return result.scalar_one_or_none()

    async def get_active_by_id(self, db: AsyncSession, repository_id: str) -> RepositoryMetadataModel | None:
        result = await db.execute(
            select(RepositoryMetadataModel).where(
                RepositoryMetadataModel.id == repository_id,
                RepositoryMetadataModel.deleted_at.is_(None),
            )
        )
        return result.scalar_one_or_none()

    async def get_by_user_and_normalized_url(
        self,
        db: AsyncSession,
        *,
        user_id: str,
        repository_url: str,
    ) -> RepositoryMetadataModel | None:
        result = await db.execute(
            select(RepositoryMetadataModel).where(
                RepositoryMetadataModel.user_id == user_id,
                RepositoryMetadataModel.repository_url == repository_url,
                RepositoryMetadataModel.deleted_at.is_(None),
            )
        )
        return result.scalar_one_or_none()

    async def upsert_metadata(
        self,
        db: AsyncSession,
        *,
        user_id: str,
        provider_metadata: RepositoryProviderMetadata,
    ) -> RepositoryRecord:
        existing = await self.get_by_user_and_normalized_url(
            db,
            user_id=user_id,
            repository_url=provider_metadata.repository_url,
        )
        now = datetime.now(timezone.utc)
        if existing is None:
            model = RepositoryMetadataModel(
                id=new_id("repo"),
                user_id=user_id,
                provider=provider_metadata.provider,
                repository_url=provider_metadata.repository_url,
                owner=provider_metadata.owner,
                name=provider_metadata.name,
                default_branch=provider_metadata.default_branch,
                visibility=provider_metadata.visibility,
                latest_commit_sha=provider_metadata.latest_commit_sha,
                file_tree_snapshot=provider_metadata.file_tree_snapshot,
                repository_metadata=provider_metadata.metadata,
                fetched_at=now,
            )
            db.add(model)
        else:
            model = existing
            model.default_branch = provider_metadata.default_branch
            model.visibility = provider_metadata.visibility
            model.latest_commit_sha = provider_metadata.latest_commit_sha
            model.file_tree_snapshot = provider_metadata.file_tree_snapshot
            model.repository_metadata = provider_metadata.metadata
            model.fetched_at = now
        await db.flush()
        return self.to_record(model)

    def to_record(self, model: RepositoryMetadataModel) -> RepositoryRecord:
        return RepositoryRecord(
            id=model.id,
            user_id=model.user_id,
            provider=model.provider,  # type: ignore[arg-type]
            repository_url=model.repository_url,
            owner=model.owner,
            name=model.name,
            default_branch=model.default_branch,
            visibility=model.visibility,  # type: ignore[arg-type]
            latest_commit_sha=model.latest_commit_sha,
            file_tree_snapshot=model.file_tree_snapshot,
            metadata=model.repository_metadata,
            fetched_at=model.fetched_at,
            created_at=model.created_at,
            updated_at=model.updated_at,
            deleted_at=model.deleted_at,
        )
