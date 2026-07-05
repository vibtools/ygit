from __future__ import annotations

JOB_TYPE = "repository_analysis_deep"


async def run(payload: dict[str, object]) -> None:
    """Deep repository analysis job boundary.

    Durable deep analysis execution remains delegated to Repository Analysis
    Engine public APIs in a later runtime/data-fixture phase. This handler is
    intentionally provider-free and does not write analysis tables directly.
    """
    _repository_id = str(payload["repository_id"])
    _user_id = str(payload["user_id"])
