from __future__ import annotations

import hmac
import inspect

from collections.abc import Callable
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession

from backend.engines.auth_engine.connected_accounts_module.public import (
    ConnectedAccountsPublicService,
    connected_accounts_service,
)
from backend.engines.auth_engine.connected_accounts_module.schemas import (
    ResolvedProviderCredential,
)
from backend.pipelines.deploy_pipeline.public import (
    DeployBuildStageInput,
    DeploymentPipelineContext,
    ProviderTokenReference,
    build_provider_execution_plan,
)
from backend.workers.errors import (
    WorkerCloudflareCredentialAcquisitionBlockedError,
)
from backend.workers.git_checkout import GitCheckoutRequest


_REQUIRED_BUILD_PAYLOAD_FIELDS = (
    "repository_path",
    "build_command",
    "output_directory",
)


def optional_str(
    value: object,
) -> str | None:
    if value is None:
        return None

    text = str(value).strip()
    return text or None


def payload_has_build_stage_fields(
    payload: dict[str, object],
) -> bool:
    return all(
        optional_str(payload.get(field))
        for field in _REQUIRED_BUILD_PAYLOAD_FIELDS
    )


def payload_needs_worker_workspace(
    payload: dict[str, object],
) -> bool:
    return (
        optional_str(
            payload.get("repository_path")
        )
        is None
        and optional_str(
            payload.get("build_command")
        )
        is not None
        and optional_str(
            payload.get("output_directory")
        )
        is not None
    )


def repository_contains_checkout(
    repository_path: Path,
) -> bool:
    try:
        return (
            repository_path.is_dir()
            and any(repository_path.iterdir())
        )
    except OSError:
        return False


def payload_timeout_seconds(
    value: object,
) -> int:
    if value is None:
        return 600

    try:
        return int(value)
    except (TypeError, ValueError):
        return 600


def payload_checkout_ref(
    payload: dict[str, object],
) -> str | None:
    return (
        optional_str(payload.get("git_ref"))
        or optional_str(payload.get("branch"))
    )


def payload_checkout_timeout_seconds(
    value: object,
) -> int:
    if value is None:
        return 180

    try:
        return int(value)
    except (TypeError, ValueError):
        return 180


def payload_environment(
    value: object,
) -> dict[str, str]:
    if not isinstance(value, dict):
        return {}

    return {
        str(key): str(item)
        for key, item in value.items()
        if key is not None
        and item is not None
    }


def payload_with_workspace_if_checkout_ready(
    deployment_id: str,
    payload: dict[str, object],
    *,
    checkout_runner: Callable[
        [GitCheckoutRequest],
        object,
    ],
    workspace_preparer: Callable[
        [str],
        object,
    ],
) -> dict[str, object]:
    """Prepare workspace and checkout when build input requires it."""

    if not payload_needs_worker_workspace(
        payload
    ):
        return payload

    runtime_payload = dict(payload)

    workspace = workspace_preparer(
        deployment_id
    )

    runtime_payload["workspace_path"] = str(
        workspace.workspace_path
    )
    runtime_payload["artifacts_path"] = str(
        workspace.artifacts_path
    )

    repository_url = optional_str(
        payload.get("repository_url")
    )

    checkout_exists = repository_contains_checkout(
        workspace.repository_path
    )

    if repository_url and not checkout_exists:
        checkout_result = checkout_runner(
            GitCheckoutRequest(
                repository_url=repository_url,
                destination_path=(
                    workspace.repository_path
                ),
                ref=payload_checkout_ref(
                    payload
                ),
                timeout_seconds=(
                    payload_checkout_timeout_seconds(
                        payload.get(
                            "checkout_timeout_seconds"
                        )
                    )
                ),
            )
        )

        commit_sha = optional_str(
            getattr(
                checkout_result,
                "commit_sha",
                None,
            )
        )

        if commit_sha:
            runtime_payload[
                "commit_sha"
            ] = commit_sha

    if repository_contains_checkout(
        workspace.repository_path
    ):
        runtime_payload[
            "repository_path"
        ] = str(
            workspace.repository_path
        )

    return runtime_payload


def build_stage_input(
    deployment_id: str,
    payload: dict[str, object],
) -> DeployBuildStageInput | None:
    """Create build input only when checkout and build data are complete."""

    if not payload_has_build_stage_fields(
        payload
    ):
        return None

    return DeployBuildStageInput(
        deployment_id=deployment_id,
        repository_path=str(
            payload["repository_path"]
        ),
        package_manager=optional_str(
            payload.get("package_manager")
        ),
        build_command=str(
            payload["build_command"]
        ),
        output_directory=str(
            payload["output_directory"]
        ),
        root_directory=(
            optional_str(
                payload.get("root_directory")
            )
            or "."
        ),
        install_command=optional_str(
            payload.get("install_command")
        ),
        timeout_seconds=payload_timeout_seconds(
            payload.get("timeout_seconds")
        ),
        environment=payload_environment(
            payload.get("environment")
        ),
    )


def provider_token_reference(
    value: object,
    *,
    expected_provider: str,
) -> ProviderTokenReference | None:
    """Validate a secret-safe provider reference from a job payload."""

    if value is None:
        return None

    if not isinstance(value, dict):
        raise ValueError(
            "Provider reference must be a mapping."
        )

    reference = ProviderTokenReference.model_validate(
        value
    )

    if reference.provider != expected_provider:
        raise ValueError(
            "Provider reference does not match "
            "the expected provider."
        )

    reference_value = optional_str(
        reference.token_secret_ref
    )

    if reference_value is None:
        raise ValueError(
            "Provider reference is empty."
        )

    allowed_prefixes = {
        "github": (
            "github_app_installation:",
            "github_token_ref_",
        ),
        "cloudflare": (
            "cloudflare_oauth_account:",
            "cloudflare_token_ref_",
        ),
    }

    prefixes = allowed_prefixes.get(
        expected_provider
    )

    if (
        prefixes is None
        or not reference_value.startswith(
            prefixes
        )
    ):
        raise ValueError(
            "Provider reference format is not supported."
        )

    return reference


async def acquire_cloudflare_deployment_credential(
    db: AsyncSession,
    context: DeploymentPipelineContext,
    *,
    connected_accounts: (
        ConnectedAccountsPublicService | None
    ) = None,
) -> ResolvedProviderCredential:
    """Acquire a runtime-only Cloudflare credential behind plan readiness."""

    plan = build_provider_execution_plan(
        context
    )

    if not plan.ready_to_execute:
        raise (
            WorkerCloudflareCredentialAcquisitionBlockedError(
                deployment_id=context.deployment_id,
                blockers=[
                    str(blocker)
                    for blocker in plan.blockers
                ],
            )
        )

    reference = context.cloudflare_token_ref
    user_id = optional_str(context.user_id)

    if reference is None or user_id is None:
        raise (
            WorkerCloudflareCredentialAcquisitionBlockedError(
                deployment_id=context.deployment_id,
                blockers=[
                    "credential_context_incomplete"
                ],
            )
        )

    service = (
        connected_accounts
        or connected_accounts_service
    )
    credential = (
        await service
        .acquire_cloudflare_deployment_credential(
            db,
            user_id=user_id,
            token_secret_ref=(
                reference.token_secret_ref
            ),
        )
    )

    if (
        credential.provider != "cloudflare"
        or not hmac.compare_digest(
            credential.token_secret_ref,
            reference.token_secret_ref,
        )
    ):
        raise (
            WorkerCloudflareCredentialAcquisitionBlockedError(
                deployment_id=context.deployment_id,
                blockers=[
                    "credential_reference_mismatch"
                ],
            )
        )

    return credential


def deployment_pipeline_context(
    deployment_id: str,
    payload: dict[str, object],
    *,
    build_result: object | None = None,
    source_deployment_id: str | None = None,
) -> DeploymentPipelineContext:
    """Build the secret-safe context passed to Deploy Pipeline."""

    artifact_path = None

    if (
        build_result is not None
        and getattr(
            build_result,
            "artifact_ready",
            False,
        )
        is True
    ):
        artifact_path = optional_str(
            getattr(
                build_result,
                "output_directory",
                None,
            )
        )

    provider_references = {
        "github_token_ref": provider_token_reference(
            payload.get("github_token_ref"),
            expected_provider="github",
        ),
        "cloudflare_token_ref": provider_token_reference(
            payload.get("cloudflare_token_ref"),
            expected_provider="cloudflare",
        ),
    }

    return DeploymentPipelineContext(
        deployment_id=deployment_id,
        project_id=optional_str(
            payload.get("project_id")
        ),
        cloudflare_project_name=optional_str(
            payload.get(
                "cloudflare_project_name"
            )
        ),
        user_id=optional_str(
            payload.get("user_id")
        ),
        repository_id=optional_str(
            payload.get("repository_id")
        ),
        analysis_id=optional_str(
            payload.get("analysis_id")
        ),
        domain_id=optional_str(
            payload.get("domain_id")
        ),
        source_deployment_id=(
            optional_str(source_deployment_id)
        ),
        repository_url=optional_str(
            payload.get("repository_url")
        ),
        branch=payload_checkout_ref(payload),
        commit_sha=optional_str(
            payload.get("commit_sha")
        ),
        repository_path=optional_str(
            payload.get("repository_path")
        ),
        workspace_path=optional_str(
            payload.get("workspace_path")
        ),
        artifacts_path=optional_str(
            payload.get("artifacts_path")
        ),
        artifact_path=artifact_path,
        framework=optional_str(
            payload.get("framework")
        ),
        package_manager=optional_str(
            payload.get("package_manager")
        ),
        build_command=optional_str(
            payload.get("build_command")
        ),
        output_directory=optional_str(
            payload.get("output_directory")
        ),
        trace_id=optional_str(
            payload.get("trace_id")
        ),
        **provider_references,
    )


def _accepts_context_keyword(
    method: object,
) -> bool:
    try:
        parameters = inspect.signature(
            method
        ).parameters.values()
    except (TypeError, ValueError):
        return False

    return any(
        parameter.name == "context"
        or parameter.kind
        == inspect.Parameter.VAR_KEYWORD
        for parameter in parameters
    )


async def execute_deployment_with_context(
    pipeline: object,
    deployment_id: str,
    *,
    context: DeploymentPipelineContext,
) -> object:
    """Call the new context API while preserving legacy test fakes."""

    method = getattr(
        pipeline,
        "execute_deployment",
    )

    if _accepts_context_keyword(method):
        return await method(
            deployment_id,
            context=context,
        )

    return await method(deployment_id)


async def execute_redeployment_with_context(
    pipeline: object,
    deployment_id: str,
    *,
    source_deployment_id: str | None,
    context: DeploymentPipelineContext,
) -> object:
    """Call redeploy with context and legacy fake compatibility."""

    method = getattr(
        pipeline,
        "execute_redeployment",
    )

    if _accepts_context_keyword(method):
        return await method(
            deployment_id,
            source_deployment_id=(
                source_deployment_id
            ),
            context=context,
        )

    return await method(
        deployment_id,
        source_deployment_id=(
            source_deployment_id
        ),
    )
