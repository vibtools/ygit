from __future__ import annotations

from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from backend.engines.auth_engine.connected_accounts_module.errors import ProviderNotConnectedError
from backend.engines.auth_engine.connected_accounts_module.public import (
    ConnectedAccountsPublicService,
    connected_accounts_service,
)
from backend.engines.deploy_engine.errors import (
    DeploymentAccessDeniedError,
    DeploymentAlreadyRunningError,
    DeploymentAnalysisRequiredError,
    DeploymentCloudflareNotConnectedError,
    DeploymentGithubNotConnectedError,
    DeploymentNotFoundError,
    DeploymentProjectNotReadyError,
    DeploymentQueueFailedError,
    DeploymentStatusTransitionInvalidError,
)
from backend.engines.deploy_engine.repository import DeploymentRepository
from backend.engines.deploy_engine.schemas import (
    DeployReadyResult,
    DeploymentCancelled,
    DeploymentDetail,
    DeploymentJobRef,
    DeploymentQueued,
    DeploymentRecord,
    DeploymentRequestInput,
    RedeployRequestInput,
)
from backend.engines.project_engine.public import ProjectPublicService, project_service
from backend.engines.repository_analysis_engine.public import (
    RepositoryAnalysisPublicService,
    repository_analysis_service,
)
from backend.engines.repository_engine.public import (
    RepositoryPublicService,
    repository_service,
)
from backend.workers.queue.client import QueueClient
from backend.workers.queue.schemas import JobPayload


class DeployInternalService:
    """Deploy Engine business workflow.

    Boundary note: this service intentionally does not import GitHub Provider or
    Cloudflare Provider. Deployment execution belongs to Deploy Pipeline.
    """

    def __init__(
        self,
        *,
        repository: DeploymentRepository | None = None,
        project_public_service: ProjectPublicService | None = None,
        analysis_public_service: RepositoryAnalysisPublicService | None = None,
        repository_public_service: RepositoryPublicService | None = None,
        connected_accounts_public_service: ConnectedAccountsPublicService | None = None,
        queue_client: QueueClient | None = None,
    ) -> None:
        self.repository = repository or DeploymentRepository()
        self.project_service = project_public_service or project_service
        self.analysis_service = analysis_public_service or repository_analysis_service
        self.repository_service = repository_public_service or repository_service
        self.connected_accounts = connected_accounts_public_service or connected_accounts_service
        self.queue_client = queue_client or QueueClient()

    async def validate_deploy_ready(self, db: AsyncSession, *, user_id: str, project_id: str) -> DeployReadyResult:
        project = await self.project_service.get_project(db, user_id=user_id, project_id=project_id)
        blocking_reasons: list[str] = []

        if not project.repository_id:
            blocking_reasons.append("repository_required")
        if not project.analysis_id:
            blocking_reasons.append("analysis_required")
        if blocking_reasons:
            return DeployReadyResult(
                project_id=project_id,
                repository_id=project.repository_id or "",
                analysis_id=project.analysis_id or "",
                github_connected=False,
                cloudflare_connected=False,
                deploy_ready=False,
                blocking_reasons=blocking_reasons,
            )

        analysis = await self.analysis_service.get_analysis_result(db, user_id=user_id, analysis_id=project.analysis_id)
        if not analysis.deploy_ready:
            blocking_reasons.append("analysis_not_deploy_ready")

        github_connected = await self._is_provider_connected(db, user_id=user_id, provider="github")
        cloudflare_connected = await self._is_provider_connected(db, user_id=user_id, provider="cloudflare")
        if not github_connected:
            blocking_reasons.append("github_not_connected")
        if not cloudflare_connected:
            blocking_reasons.append("cloudflare_not_connected")

        return DeployReadyResult(
            project_id=project_id,
            repository_id=project.repository_id,
            analysis_id=project.analysis_id,
            github_connected=github_connected,
            cloudflare_connected=cloudflare_connected,
            deploy_ready=not blocking_reasons,
            blocking_reasons=blocking_reasons,
        )

    async def request_deployment(
        self,
        db: AsyncSession,
        *,
        user_id: str,
        project_id: str,
        input_data: DeploymentRequestInput | None = None,
        trace_id: str | None = None,
    ) -> DeploymentQueued:
        _ = input_data
        project = await self.project_service.get_project(db, user_id=user_id, project_id=project_id)
        if not project.repository_id:
            raise DeploymentProjectNotReadyError("Project repository is required before deployment.")
        if not project.analysis_id:
            raise DeploymentAnalysisRequiredError()

        analysis = await self.analysis_service.get_analysis_result(db, user_id=user_id, analysis_id=project.analysis_id)
        if not analysis.deploy_ready:
            raise DeploymentProjectNotReadyError("Repository analysis is not deploy-ready.")

        github_account = await self._require_provider(
            db,
            user_id=user_id,
            provider="github",
        )
        cloudflare_account = await self._require_provider(
            db,
            user_id=user_id,
            provider="cloudflare",
        )

        provider_configuration = (
            self._provider_reference_configuration(
                github_account,
                cloudflare_account,
            )
        )

        repository_configuration = await self._repository_checkout_configuration(
            db,
            user_id=user_id,
            repository_id=project.repository_id,
        )
        build_configuration = self._build_configuration_from_analysis(analysis)

        deployment = await self.repository.create_queued_deployment(
            db,
            user_id=user_id,
            project_id=project.id,
            repository_id=project.repository_id,
            analysis_id=project.analysis_id,
            requested_by="user",
        )
        job = await self._enqueue_deployment_job(
            db=db,
            deployment_id=deployment.id,
            project_id=project.id,
            user_id=user_id,
            repository_id=deployment.repository_id,
            analysis_id=deployment.analysis_id,
            domain_id=deployment.domain_id,
            source_deployment_id=(
                deployment.source_deployment_id
            ),
            job_type="deploy_project",
            trace_id=trace_id,
            build_configuration=build_configuration,
            repository_configuration=repository_configuration,
            provider_configuration=provider_configuration,
        )
        deployment = await self.repository.attach_job_id(db, deployment_id=deployment.id, job_id=job.id)
        await db.commit()
        return DeploymentQueued(deployment=self.to_detail(deployment), job=job)

    async def request_redeploy(
        self,
        db: AsyncSession,
        *,
        user_id: str,
        deployment_id: str,
        input_data: RedeployRequestInput | None = None,
        trace_id: str | None = None,
    ) -> DeploymentQueued:
        _ = input_data
        source_model = await self.repository.get_by_id(db, deployment_id)
        if source_model is None:
            raise DeploymentNotFoundError()
        source = self.repository.to_record(source_model)
        if source.user_id != user_id:
            raise DeploymentAccessDeniedError()
        if source.status in {"queued", "running"}:
            raise DeploymentAlreadyRunningError()

        github_account = await self._require_provider(
            db,
            user_id=user_id,
            provider="github",
        )
        cloudflare_account = await self._require_provider(
            db,
            user_id=user_id,
            provider="cloudflare",
        )

        provider_configuration = (
            self._provider_reference_configuration(
                github_account,
                cloudflare_account,
            )
        )

        analysis = await self.analysis_service.get_analysis_result(
            db,
            user_id=user_id,
            analysis_id=source.analysis_id,
        )
        repository_configuration = await self._repository_checkout_configuration(
            db,
            user_id=user_id,
            repository_id=source.repository_id,
        )
        build_configuration = self._build_configuration_from_analysis(analysis)

        deployment = await self.repository.create_queued_deployment(
            db,
            user_id=user_id,
            project_id=source.project_id,
            repository_id=source.repository_id,
            analysis_id=source.analysis_id,
            domain_id=source.domain_id,
            requested_by="user",
            source_deployment_id=source.id,
        )
        job = await self._enqueue_deployment_job(
            db=db,
            deployment_id=deployment.id,
            project_id=deployment.project_id,
            user_id=user_id,
            repository_id=deployment.repository_id,
            analysis_id=deployment.analysis_id,
            domain_id=deployment.domain_id,
            source_deployment_id=(
                deployment.source_deployment_id
            ),
            job_type="redeploy_project",
            trace_id=trace_id,
            build_configuration=build_configuration,
            repository_configuration=repository_configuration,
            provider_configuration=provider_configuration,
        )
        deployment = await self.repository.attach_job_id(db, deployment_id=deployment.id, job_id=job.id)
        await db.commit()
        return DeploymentQueued(deployment=self.to_detail(deployment), job=job)

    async def cancel_deployment(self, db: AsyncSession, *, user_id: str, deployment_id: str) -> DeploymentCancelled:
        model = await self.repository.get_by_id(db, deployment_id)
        if model is None:
            raise DeploymentNotFoundError()
        if model.user_id != user_id:
            raise DeploymentAccessDeniedError()
        if model.status not in {"queued", "running"}:
            raise DeploymentStatusTransitionInvalidError()
        await self.repository.mark_cancelled(db, deployment=model)
        await db.commit()
        return DeploymentCancelled(deployment_id=deployment_id)

    async def get_deployment(self, db: AsyncSession, *, user_id: str, deployment_id: str) -> DeploymentDetail:
        model = await self.repository.get_by_id(db, deployment_id)
        if model is None:
            raise DeploymentNotFoundError()
        record = self.repository.to_record(model)
        if record.user_id != user_id:
            raise DeploymentAccessDeniedError()
        return self.to_detail(record)

    async def _require_provider(
        self,
        db: AsyncSession,
        *,
        user_id: str,
        provider: str,
    ) -> object:
        try:
            return await self.connected_accounts.require_provider_connected(
                db,
                user_id=user_id,
                provider=provider,
            )
        except ProviderNotConnectedError as exc:
            if provider == "github":
                raise DeploymentGithubNotConnectedError() from exc
            if provider == "cloudflare":
                raise DeploymentCloudflareNotConnectedError() from exc
            raise

    def _provider_reference_configuration(
        self,
        github_account: object,
        cloudflare_account: object,
    ) -> dict[str, object]:
        return {
            "github_token_ref": (
                self._provider_reference_payload(
                    github_account,
                    expected_provider="github",
                )
            ),
            "cloudflare_token_ref": (
                self._provider_reference_payload(
                    cloudflare_account,
                    expected_provider="cloudflare",
                )
            ),
        }

    def _provider_reference_payload(
        self,
        account: object,
        *,
        expected_provider: str,
    ) -> dict[str, object]:
        provider = str(
            getattr(
                account,
                "provider",
                "",
            )
            or ""
        ).strip().lower()

        reference_value = str(
            getattr(
                account,
                "token_secret_ref",
                "",
            )
            or ""
        ).strip()

        if (
            provider != expected_provider
            or not reference_value
        ):
            if expected_provider == "github":
                raise DeploymentGithubNotConnectedError()

            raise DeploymentCloudflareNotConnectedError()

        result: dict[str, object] = {
            "provider": provider,
            "token_secret_ref": reference_value,
        }

        account_name = str(
            getattr(
                account,
                "provider_account_name",
                "",
            )
            or ""
        ).strip()

        if account_name:
            result["account_name"] = account_name

        return result

    async def _is_provider_connected(self, db: AsyncSession, *, user_id: str, provider: str) -> bool:
        try:
            await self.connected_accounts.require_provider_connected(db, user_id=user_id, provider=provider)
        except ProviderNotConnectedError:
            return False
        return True

    async def _repository_checkout_configuration(
        self,
        db: AsyncSession,
        *,
        user_id: str,
        repository_id: str,
    ) -> dict[str, object]:
        """Return worker-safe checkout metadata through Repository Engine public API."""

        repository = await self.repository_service.get_repository_metadata(
            db,
            user_id=user_id,
            repository_id=repository_id,
        )

        repository_url = str(repository.repository_url).strip()
        if not repository_url:
            raise DeploymentProjectNotReadyError(
                "Project repository metadata does not contain a checkout URL."
            )

        configuration: dict[str, object] = {
            "repository_url": repository_url,
        }

        default_branch = str(repository.default_branch or "").strip()
        if default_branch:
            configuration["git_ref"] = default_branch

        return configuration

    def _build_configuration_from_analysis(self, analysis: object) -> dict[str, object]:
        """Extract worker-safe build settings from repository analysis.

        This intentionally excludes checkout/workspace paths. Repository checkout
        and workspace ownership belong to the worker checkout stage.
        """

        configuration: dict[str, object] = {}
        for key in (
            "framework",
            "package_manager",
            "build_command",
            "output_directory",
        ):
            value = getattr(analysis, key, None)
            if value is None:
                continue
            text = str(value).strip()
            if text:
                configuration[key] = text

        if "build_command" in configuration and "output_directory" in configuration:
            configuration.setdefault("root_directory", ".")

        return configuration

    async def _enqueue_deployment_job(
        self,
        *,
        db: AsyncSession,
        deployment_id: str,
        project_id: str,
        user_id: str,
        repository_id: str,
        analysis_id: str,
        domain_id: str | None,
        source_deployment_id: str | None,
        job_type: str,
        trace_id: str | None,
        build_configuration: dict[str, object] | None = None,
        repository_configuration: dict[str, object] | None = None,
        provider_configuration: dict[str, object] | None = None,
    ) -> DeploymentJobRef:
        try:
            job_trace_id = (
                trace_id
                or f"trace_{uuid4().hex}"
            )

            payload_data: dict[str, object] = {
                "deployment_id": deployment_id,
                "project_id": project_id,
                "user_id": user_id,
                "repository_id": repository_id,
                "analysis_id": analysis_id,
                "trace_id": job_trace_id,
            }

            if domain_id:
                payload_data[
                    "domain_id"
                ] = domain_id

            if source_deployment_id:
                payload_data[
                    "source_deployment_id"
                ] = source_deployment_id

            payload_data.update(
                build_configuration or {}
            )
            payload_data.update(
                repository_configuration or {}
            )
            payload_data.update(
                provider_configuration or {}
            )

            payload = JobPayload(
                job_type=job_type,
                payload=payload_data,
                trace_id=job_trace_id,
            )
            try:
                job = await self.queue_client.enqueue(payload, db=db)
            except TypeError:
                # Compatibility for unit-test fake queue clients that implement
                # the previous one-argument QueueClient contract.
                job = await self.queue_client.enqueue(payload)
        except Exception as exc:
            raise DeploymentQueueFailedError() from exc
        return DeploymentJobRef(id=job.id, type=job_type)  # type: ignore[arg-type]

    def to_detail(self, record: DeploymentRecord) -> DeploymentDetail:
        return DeploymentDetail(**record.model_dump())
