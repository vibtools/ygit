from __future__ import annotations

from backend.workers.errors import WorkerDeploymentIncompleteError


def _result_label(value: object) -> str | None:
    raw_value = getattr(value, "value", value)

    if raw_value is None:
        return None

    text = str(raw_value).strip()
    return text or None


def require_completed_pipeline_result(
    *,
    deployment_id: str,
    result: object,
) -> None:
    """Require explicit proof that live provider execution completed."""

    status = _result_label(
        getattr(result, "status", None)
    ) or "missing"

    stage = _result_label(
        getattr(result, "stage", None)
    )

    metadata = getattr(result, "metadata", None)
    provider_calls_executed: bool | None = None

    if isinstance(metadata, dict):
        explicit_value = metadata.get(
            "provider_calls_executed"
        )

        if isinstance(explicit_value, bool):
            provider_calls_executed = explicit_value

    completed = (
        status == "completed"
        and provider_calls_executed is True
    )

    if completed:
        return

    raise WorkerDeploymentIncompleteError(
        deployment_id=deployment_id,
        pipeline_status=status,
        pipeline_stage=stage,
        provider_calls_executed=provider_calls_executed,
    )
