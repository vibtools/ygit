from __future__ import annotations

from types import SimpleNamespace

import pytest

from backend.workers import worker as worker_module
from backend.workers.jobs import (
    deploy_project,
    redeploy_project,
)
from backend.workers.provider_execution_policy import (
    WorkerProviderExecutionPolicy,
)
from backend.workers.runner.dispatcher import (
    JobDispatcher,
)
from backend.workers.worker import WorkerRuntime


DISABLED_POLICY = WorkerProviderExecutionPolicy(
    mode="disabled",
    enabled=False,
    provider=None,
    source="server_settings",
)

CLOUDFLARE_POLICY = WorkerProviderExecutionPolicy(
    mode="cloudflare",
    enabled=True,
    provider="cloudflare",
    source="server_settings",
)


@pytest.fixture(autouse=True)
def stub_deployment_history_runtime(
    monkeypatch,
) -> None:
    async def completed(
        db,
        deployment_id,
    ) -> bool:
        _ = db
        _ = deployment_id
        return False

    async def no_op(*args, **kwargs) -> None:
        _ = args
        _ = kwargs

    for module in (
        deploy_project,
        redeploy_project,
    ):
        monkeypatch.setattr(
            module,
            "deployment_history_completed",
            completed,
        )
        monkeypatch.setattr(
            module,
            "mark_deployment_started",
            no_op,
        )
        monkeypatch.setattr(
            module,
            "persist_pipeline_result_history",
            no_op,
        )
        monkeypatch.setattr(
            module,
            "persist_deployment_failure_safely",
            no_op,
        )


class FakeDB:
    pass


class CompletedPipeline:
    def __init__(self) -> None:
        self.calls: list[
            tuple[str, str, object, str | None]
        ] = []

    async def execute_deployment(
        self,
        deployment_id: str,
        *,
        context,
    ):
        self.calls.append(
            (
                "deploy",
                deployment_id,
                context,
                None,
            )
        )
        return SimpleNamespace(
            status="completed",
            stage="completed",
            metadata={
                "provider_calls_executed": True,
            },
        )

    async def execute_redeployment(
        self,
        deployment_id: str,
        source_deployment_id: str | None = None,
        *,
        context,
    ):
        self.calls.append(
            (
                "redeploy",
                deployment_id,
                context,
                source_deployment_id,
            )
        )
        return SimpleNamespace(
            status="completed",
            stage="completed",
            metadata={
                "provider_calls_executed": True,
            },
        )


@pytest.mark.parametrize(
    (
        "mode",
        "expected_enabled",
        "expected_provider",
    ),
    [
        (
            "disabled",
            False,
            None,
        ),
        (
            "cloudflare",
            True,
            "cloudflare",
        ),
    ],
)
def test_worker_runtime_resolves_policy_from_server_settings(
    monkeypatch,
    mode,
    expected_enabled,
    expected_provider,
) -> None:
    monkeypatch.setattr(
        worker_module,
        "get_settings",
        lambda: SimpleNamespace(
            worker_provider_execution_mode=mode
        ),
    )

    runtime = WorkerRuntime(
        worker_id="worker-policy",
        queue_name="default",
        repository=SimpleNamespace(),
    )

    policy = (
        runtime.dispatcher
        .provider_execution_policy
    )

    assert policy is not None
    assert policy.enabled is expected_enabled
    assert policy.provider == expected_provider
    assert policy.source == "server_settings"


def test_custom_dispatcher_preserves_legacy_construction_without_settings(
    monkeypatch,
) -> None:
    custom_dispatcher = SimpleNamespace()

    def fail_settings_lookup():
        raise AssertionError(
            "settings must not resolve for an injected dispatcher"
        )

    monkeypatch.setattr(
        worker_module,
        "get_settings",
        fail_settings_lookup,
    )

    runtime = WorkerRuntime(
        worker_id="worker-custom",
        queue_name="default",
        repository=SimpleNamespace(),
        dispatcher=custom_dispatcher,
    )

    assert runtime.dispatcher is custom_dispatcher


def test_worker_runtime_rejects_ambiguous_dispatcher_and_policy(
) -> None:
    with pytest.raises(
        ValueError,
        match=(
            "dispatcher and provider_execution_policy "
            "cannot be combined"
        ),
    ):
        WorkerRuntime(
            worker_id="worker-ambiguous",
            queue_name="default",
            repository=SimpleNamespace(),
            dispatcher=SimpleNamespace(),
            provider_execution_policy=(
                DISABLED_POLICY
            ),
        )


@pytest.mark.asyncio
async def test_dispatcher_passes_exact_policy_as_trusted_context(
) -> None:
    dispatcher = JobDispatcher(
        provider_execution_policy=(
            CLOUDFLARE_POLICY
        )
    )
    received: dict[str, object] = {}
    payload = {
        "deployment_id": "deployment-policy-1",
    }
    original_payload = dict(payload)
    db = FakeDB()

    async def handler(
        received_payload,
        *,
        db,
        provider_execution_policy,
    ) -> None:
        received["payload"] = received_payload
        received["db"] = db
        received["policy"] = (
            provider_execution_policy
        )

    dispatcher.handlers = {
        "policy-aware": handler,
    }

    await dispatcher.dispatch(
        "policy-aware",
        payload,
        db=db,
    )

    assert received["payload"] is payload
    assert received["db"] is db
    assert (
        received["policy"]
        is CLOUDFLARE_POLICY
    )
    assert payload == original_payload


@pytest.mark.asyncio
async def test_job_payload_cannot_override_disabled_dispatcher_policy(
) -> None:
    dispatcher = JobDispatcher(
        provider_execution_policy=(
            DISABLED_POLICY
        )
    )
    received: list[
        WorkerProviderExecutionPolicy
    ] = []
    payload = {
        "deployment_id": "deployment-policy-2",
        "worker_provider_execution_mode": (
            "cloudflare"
        ),
        "provider_execution_enabled": True,
        "provider_enabled": True,
    }
    original_payload = dict(payload)

    async def handler(
        received_payload,
        *,
        provider_execution_policy,
    ) -> None:
        assert received_payload is payload
        received.append(
            provider_execution_policy
        )

    dispatcher.handlers = {
        "payload-policy-attempt": handler,
    }

    await dispatcher.dispatch(
        "payload-policy-attempt",
        payload,
    )

    assert received == [DISABLED_POLICY]
    assert payload == original_payload


@pytest.mark.asyncio
async def test_deploy_handler_passes_enabled_policy_to_fake_binding(
    monkeypatch,
) -> None:
    pipeline = CompletedPipeline()
    bound_context = object()
    enabled_values: list[bool] = []

    async def bind(
        db,
        context,
        *,
        provider_execution_enabled,
    ):
        _ = db
        _ = context
        enabled_values.append(
            provider_execution_enabled
        )
        return SimpleNamespace(
            pipeline=pipeline,
            context=bound_context,
            provider_execution_enabled=(
                provider_execution_enabled
            ),
        )

    monkeypatch.setattr(
        deploy_project,
        "build_provider_pipeline_binding",
        bind,
    )

    await deploy_project.run(
        {
            "deployment_id": "deployment-policy-3",
        },
        db=FakeDB(),
        provider_execution_policy=(
            CLOUDFLARE_POLICY
        ),
    )

    assert enabled_values == [True]
    assert pipeline.calls == [
        (
            "deploy",
            "deployment-policy-3",
            bound_context,
            None,
        )
    ]


@pytest.mark.asyncio
async def test_redeploy_handler_passes_disabled_policy_to_fake_binding(
    monkeypatch,
) -> None:
    pipeline = CompletedPipeline()
    bound_context = object()
    enabled_values: list[bool] = []

    async def bind(
        db,
        context,
        *,
        provider_execution_enabled,
    ):
        _ = db
        _ = context
        enabled_values.append(
            provider_execution_enabled
        )
        return SimpleNamespace(
            pipeline=pipeline,
            context=bound_context,
            provider_execution_enabled=(
                provider_execution_enabled
            ),
        )

    monkeypatch.setattr(
        redeploy_project,
        "build_provider_pipeline_binding",
        bind,
    )

    await redeploy_project.run(
        {
            "deployment_id": "deployment-policy-4",
            "source_deployment_id": (
                "deployment-source"
            ),
        },
        db=FakeDB(),
        provider_execution_policy=(
            DISABLED_POLICY
        ),
    )

    assert enabled_values == [False]
    assert pipeline.calls == [
        (
            "redeploy",
            "deployment-policy-4",
            bound_context,
            "deployment-source",
        )
    ]


def test_policy_handoff_sources_preserve_runtime_boundaries(
) -> None:
    from pathlib import Path

    worker_source = Path(
        "backend/workers/worker.py"
    ).read_text(
        encoding="utf-8"
    )
    dispatcher_source = Path(
        "backend/workers/runner/"
        "dispatcher.py"
    ).read_text(
        encoding="utf-8"
    )

    assert "get_settings()" in worker_source
    assert (
        "resolve_worker_provider_execution_policy"
        in worker_source
    )
    assert (
        "provider_execution_policy"
        in dispatcher_source
    )

    for path in (
        Path(
            "backend/workers/jobs/"
            "deploy_project.py"
        ),
        Path(
            "backend/workers/jobs/"
            "redeploy_project.py"
        ),
    ):
        source = path.read_text(
            encoding="utf-8"
        )

        assert (
            "provider_execution_enabled_by_policy"
            in source
        )
        assert "get_settings(" not in source
        assert "os.getenv(" not in source
        assert (
            'payload.get("provider_execution'
            not in source
        )
        assert (
            'payload["provider_execution'
            not in source
        )
        assert "backend.providers" not in source
        assert "cloudflare_provider" not in source
