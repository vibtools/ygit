from __future__ import annotations

from pathlib import Path


DOCKERFILE = Path("Dockerfile")
DOCKERIGNORE = Path(".dockerignore")
COMPOSE = Path("docker-compose.yml")


def dockerfile_text() -> str:
    return DOCKERFILE.read_text(
        encoding="utf-8"
    )


def test_runtime_image_copies_scripts_directory(
) -> None:
    source = dockerfile_text()

    assert "COPY scripts ./scripts" in source
    assert (
        source.index("COPY scripts ./scripts")
        < source.index(
            "RUN pip install"
        )
    )


def test_runtime_image_copies_live_runbook(
) -> None:
    source = dockerfile_text()

    assert (
        "COPY LIVE_DEPLOYMENT_RUNBOOK.md "
        "./LIVE_DEPLOYMENT_RUNBOOK.md"
        in source
    )


def test_dockerignore_allows_runtime_readiness_artifacts(
) -> None:
    ignored = {
        line.strip()
        for line in DOCKERIGNORE.read_text(
            encoding="utf-8"
        ).splitlines()
        if line.strip()
        and not line.lstrip().startswith("#")
    }

    assert "scripts" not in ignored
    assert "scripts/" not in ignored
    assert (
        "LIVE_DEPLOYMENT_RUNBOOK.md"
        not in ignored
    )


def test_api_and_worker_share_runtime_dockerfile(
) -> None:
    compose = COMPOSE.read_text(
        encoding="utf-8"
    )

    assert "ygit-api:" in compose
    assert "ygit-worker:" in compose
    assert compose.count(
        "dockerfile: Dockerfile"
    ) >= 2
