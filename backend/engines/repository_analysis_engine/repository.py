from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.ids import new_id
from backend.engines.repository_analysis_engine.models import AnalysisResultModel
from backend.engines.repository_analysis_engine.schemas import AnalysisDetail, AnalysisRecord, QuickAnalysisResult


class AnalysisResultRepository:
    """Database repository owned by Repository Analysis Engine only."""

    async def get_active_by_id(self, db: AsyncSession, analysis_id: str) -> AnalysisResultModel | None:
        result = await db.execute(
            select(AnalysisResultModel).where(
                AnalysisResultModel.id == analysis_id,
                AnalysisResultModel.deleted_at.is_(None),
            )
        )
        return result.scalar_one_or_none()

    async def mark_existing_not_latest(self, db: AsyncSession, *, repository_id: str) -> None:
        await db.execute(
            update(AnalysisResultModel)
            .where(AnalysisResultModel.repository_id == repository_id, AnalysisResultModel.is_latest.is_(True))
            .values(is_latest=False, updated_at=datetime.now(timezone.utc))
        )

    async def create_quick_result(
        self,
        db: AsyncSession,
        *,
        user_id: str,
        repository_id: str,
        project_id: str | None,
        commit_sha: str | None,
        result: QuickAnalysisResult,
    ) -> AnalysisResultModel:
        await self.mark_existing_not_latest(db, repository_id=repository_id)
        model = AnalysisResultModel(
            id=new_id("analysis"),
            user_id=user_id,
            repository_id=repository_id,
            project_id=project_id,
            stage="quick",
            status="quick_completed",
            framework=result.framework.framework,
            package_manager=result.package_manager.package_manager,
            build_command=result.build_command.build_command,
            output_directory=result.output_directory.output_directory,
            deploy_ready=result.deploy_readiness.deploy_ready,
            score=result.repository_score.score,
            explanation=result.model_dump(mode="json"),
            warnings=[warning.model_dump(mode="json") for warning in result.warnings],
            errors=[{"message": reason} for reason in result.deploy_readiness.blocking_reasons],
            recommendations=[recommendation.model_dump(mode="json") for recommendation in result.recommendations],
            commit_sha=commit_sha,
            is_latest=True,
        )
        db.add(model)
        await db.flush()
        return model

    def to_record(self, model: AnalysisResultModel) -> AnalysisRecord:
        return AnalysisRecord(
            id=model.id,
            repository_id=model.repository_id,
            user_id=model.user_id,
            project_id=model.project_id,
            stage=model.stage,  # type: ignore[arg-type]
            status=model.status,  # type: ignore[arg-type]
            framework=model.framework,  # type: ignore[arg-type]
            package_manager=model.package_manager,  # type: ignore[arg-type]
            build_command=model.build_command,
            output_directory=model.output_directory,
            deploy_ready=model.deploy_ready,
            score=model.score,
            explanation=model.explanation,
            warnings=model.warnings,
            errors=model.errors,
            commit_sha=model.commit_sha,
            is_latest=model.is_latest,
            created_at=model.created_at,
            updated_at=model.updated_at,
            deleted_at=model.deleted_at,
        )

    def to_detail(self, model: AnalysisResultModel) -> AnalysisDetail:
        record = self.to_record(model)
        quick_analysis = None
        recommendations = []
        if isinstance(model.explanation, dict):
            try:
                quick_analysis = QuickAnalysisResult.model_validate(model.explanation)
                recommendations = quick_analysis.recommendations
            except Exception:
                quick_analysis = None
        return AnalysisDetail(**record.model_dump(), quick_analysis=quick_analysis, recommendations=recommendations)
