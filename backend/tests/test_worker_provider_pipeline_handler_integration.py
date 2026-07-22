from __future__ import annotations

import inspect
from types import SimpleNamespace

import pytest

from backend.workers.jobs import (
    deploy_project,
    redeploy_project,
)
from backend.workers.runner.dispatcher import (
    JobDispatcher,
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


@pytest.mark.asyncio
async def test_deploy_handler_uses_db_owned_binding_result(
    monkeypatch,
) -> None:
    db = FakeDB()
    pipeline = CompletedPipeline()
    bound_context = object()
    binding_calls: list[
        tuple[object, object]
    ] = []
    payload = {
        "deployment_id": "deployment-1",
        "project_id": "project-1",
    }
    original_payload = dict(payload)

    async def bind(
        received_db,
        received_context,
        *,
        provider_execution_enabled,
    ):
        assert (
            provider_execution_enabled
            is False
        )
        binding_calls.append(
            (
                received_db,
                received_context,
            )
        )
        return SimpleNamespace(
            pipeline=pipeline,
            context=bound_context,
            provider_execution_enabled=False,
        )

    monkeypatch.setattr(
        deploy_project,
        "build_provider_pipeline_binding",
        bind,
    )

    await deploy_project.run(
        payload,
        db=db,
    )

    assert len(binding_calls) == 1
    assert binding_calls[0][0] is db
    assert (
        binding_calls[0][1].deployment_id
        == "deployment-1"
    )
    assert pipeline.calls == [
        (
            "deploy",
            "deployment-1",
            bound_context,
            None,
        )
    ]
    assert payload == original_payload


@pytest.mark.asyncio
async def test_redeploy_handler_uses_db_owned_binding_result(
    monkeypatch,
) -> None:
    db = FakeDB()
    pipeline = CompletedPipeline()
    bound_context = object()
    binding_calls: list[
        tuple[object, object]
    ] = []
    payload = {
        "deployment_id": "deployment-2",
        "source_deployment_id": (
            "deployment-source"
        ),
        "project_id": "project-1",
    }
    original_payload = dict(payload)

    async def bind(
        received_db,
        received_context,
        *,
        provider_execution_enabled,
    ):
        assert (
            provider_execution_enabled
            is False
        )
        binding_calls.append(
            (
                received_db,
                received_context,
            )
        )
        return SimpleNamespace(
            pipeline=pipeline,
            context=bound_context,
            provider_execution_enabled=False,
        )

    monkeypatch.setattr(
        redeploy_project,
        "build_provider_pipeline_binding",
        bind,
    )

    await redeploy_project.run(
        payload,
        db=db,
    )

    assert len(binding_calls) == 1
    assert binding_calls[0][0] is db
    assert (
        binding_calls[0][1]
        .source_deployment_id
        == "deployment-source"
    )
    assert pipeline.calls == [
        (
            "redeploy",
            "deployment-2",
            bound_context,
            "deployment-source",
        )
    ]
    assert payload == original_payload


@pytest.mark.asyncio
async def test_direct_deploy_call_without_db_preserves_legacy_path(
    monkeypatch,
) -> None:
    pipeline = CompletedPipeline()
    binding_calls: list[object] = []

    async def bind(*args, **kwargs):
        binding_calls.append(
            (
                args,
                kwargs,
            )
        )
        raise AssertionError(
            "binding must not run without worker DB"
        )

    monkeypatch.setattr(
        deploy_project,
        "deploy_pipeline",
        pipeline,
    )
    monkeypatch.setattr(
        deploy_project,
        "build_provider_pipeline_binding",
        bind,
    )

    await deploy_project.run(
        {
            "deployment_id": "deployment-3",
        }
    )

    assert binding_calls == []
    assert pipeline.calls[0][0] == "deploy"


def test_dispatcher_detects_both_handlers_as_db_aware(
) -> None:
    dispatcher = JobDispatcher()

    for job_type in (
        deploy_project.JOB_TYPE,
        redeploy_project.JOB_TYPE,
    ):
        handler = dispatcher.handlers[
            job_type
        ]
        parameters = inspect.signature(
            handler
        ).parameters

        assert "db" in parameters
        assert (
            parameters["db"].kind
            == inspect.Parameter.KEYWORD_ONLY
        )


def test_handler_sources_cannot_enable_provider_execution(
) -> None:
    from pathlib import Path

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
            "build_provider_pipeline_binding"
            in source
        )
        assert (
            "provider_execution_enabled=True"
            not in source
        )
        assert (
            '"provider_enabled"'
            not in source
        )
        assert "os.getenv(" not in source
        assert "get_settings(" not in source
        assert "backend.providers" not in source
        assert "cloudflare_provider" not in source
