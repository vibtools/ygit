from __future__ import annotations

from pathlib import Path

from backend.pipelines.deploy_pipeline.public import DeployBuildStageInput, deploy_pipeline
from backend.workers.git_checkout import GitCheckoutRequest, run_git_checkout
from backend.workers.workspace import prepare_repository_workspace

JOB_TYPE = "deploy_project"

_REQUIRED_BUILD_PAYLOAD_FIELDS = ("repository_path", "build_command", "output_directory")


def _optional_str(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _payload_has_build_stage_fields(payload: dict[str, object]) -> bool:
    return all(_optional_str(payload.get(field)) for field in _REQUIRED_BUILD_PAYLOAD_FIELDS)


def _payload_needs_worker_workspace(payload: dict[str, object]) -> bool:
    return (
        _optional_str(payload.get("repository_path")) is None
        and _optional_str(payload.get("build_command")) is not None
        and _optional_str(payload.get("output_directory")) is not None
    )


def _repository_contains_checkout(repository_path: Path) -> bool:
    try:
        return repository_path.is_dir() and any(repository_path.iterdir())
    except OSError:
        return False


def _payload_timeout_seconds(value: object) -> int:
    if value is None:
        return 600
    try:
        return int(value)
    except (TypeError, ValueError):
        return 600


def _payload_checkout_ref(payload: dict[str, object]) -> str | None:
    return _optional_str(payload.get("git_ref")) or _optional_str(payload.get("branch"))


def _payload_checkout_timeout_seconds(value: object) -> int:
    if value is None:
        return 180
    try:
        return int(value)
    except (TypeError, ValueError):
        return 180


def _payload_with_workspace_if_checkout_ready(
    deployment_id: str,
    payload: dict[str, object],
) -> dict[str, object]:
    """Prepare worker workspace and run checkout only when repository_url exists."""

    if not _payload_needs_worker_workspace(payload):
        return payload

    runtime_payload = dict(payload)
    workspace = prepare_repository_workspace(deployment_id)

    runtime_payload["workspace_path"] = str(workspace.workspace_path)
    runtime_payload["artifacts_path"] = str(workspace.artifacts_path)

    repository_url = _optional_str(payload.get("repository_url"))
    if repository_url and not _repository_contains_checkout(workspace.repository_path):
        checkout_result = run_git_checkout(
            GitCheckoutRequest(
                repository_url=repository_url,
                destination_path=workspace.repository_path,
                ref=_payload_checkout_ref(payload),
                timeout_seconds=_payload_checkout_timeout_seconds(payload.get("checkout_timeout_seconds")),
            )
        )
        if checkout_result.commit_sha:
            runtime_payload["commit_sha"] = checkout_result.commit_sha

    if _repository_contains_checkout(workspace.repository_path):
        runtime_payload["repository_path"] = str(workspace.repository_path)

    return runtime_payload


def _payload_environment(value: object) -> dict[str, str]:
    if not isinstance(value, dict):
        return {}
    return {
        str(key): str(item)
        for key, item in value.items()
        if key is not None and item is not None
    }


def _build_stage_input(deployment_id: str, payload: dict[str, object]) -> DeployBuildStageInput | None:
    """Create worker-owned build-stage input only when checkout/build data exists."""

    if not _payload_has_build_stage_fields(payload):
        return None

    return DeployBuildStageInput(
        deployment_id=deployment_id,
        repository_path=str(payload["repository_path"]),
        package_manager=_optional_str(payload.get("package_manager")),
        build_command=str(payload["build_command"]),
        output_directory=str(payload["output_directory"]),
        root_directory=_optional_str(payload.get("root_directory")) or ".",
        install_command=_optional_str(payload.get("install_command")),
        timeout_seconds=_payload_timeout_seconds(payload.get("timeout_seconds")),
        environment=_payload_environment(payload.get("environment")),
    )


async def run(payload: dict[str, object]) -> None:
    """Run deployment through Deploy Pipeline.

    Worker job owns runtime dispatch only. It must not contain Cloudflare/GitHub
    provider logic and must not write deployment logs directly.
    """

    deployment_id = str(payload["deployment_id"])
    runtime_payload = _payload_with_workspace_if_checkout_ready(deployment_id, payload)
    build_input = _build_stage_input(deployment_id, runtime_payload)

    if build_input is not None:
        build_result = deploy_pipeline.execute_build_stage(build_input)
        if build_result.status != "succeeded":
            return

    await deploy_pipeline.execute_deployment(deployment_id)
