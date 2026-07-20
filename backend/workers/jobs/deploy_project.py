from __future__ import annotations

from backend.pipelines.deploy_pipeline.public import DeployBuildStageInput, deploy_pipeline

JOB_TYPE = "deploy_project"

_REQUIRED_BUILD_PAYLOAD_FIELDS = ("repository_path", "build_command", "output_directory")


def _optional_str(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _payload_has_build_stage_fields(payload: dict[str, object]) -> bool:
    return all(_optional_str(payload.get(field)) for field in _REQUIRED_BUILD_PAYLOAD_FIELDS)


def _payload_environment(value: object) -> dict[str, str]:
    if not isinstance(value, dict):
        return {}
    return {
        str(key): str(item)
        for key, item in value.items()
        if key is not None and item is not None
    }


def _payload_timeout_seconds(value: object) -> int:
    if value is None:
        return 600
    try:
        return int(value)
    except (TypeError, ValueError):
        return 600


def _build_stage_input(deployment_id: str, payload: dict[str, object]) -> DeployBuildStageInput | None:
    """Create worker-owned build-stage input only when checkout/build data exists.

    Current deploy jobs are still queued with deployment_id/project_id/user_id only.
    This helper preserves skeleton behavior until repository checkout provides a
    repository_path and analysis-derived build settings.
    """

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
    build_input = _build_stage_input(deployment_id, payload)

    if build_input is not None:
        build_result = deploy_pipeline.execute_build_stage(build_input)
        if build_result.status != "succeeded":
            return

    await deploy_pipeline.execute_deployment(deployment_id)
