from pathlib import Path


def _project_service_source() -> str:
    return Path("backend/engines/project_engine/internal/service.py").read_text(encoding="utf-8")


def _project_repository_source() -> str:
    return Path("backend/engines/project_engine/repository.py").read_text(encoding="utf-8")


def _analysis_public_source() -> str:
    return Path("backend/engines/repository_analysis_engine/public.py").read_text(encoding="utf-8")


def _analysis_internal_source() -> str:
    return Path("backend/engines/repository_analysis_engine/internal/service.py").read_text(encoding="utf-8")


def _project_schema_source() -> str:
    return Path("backend/engines/project_engine/schemas.py").read_text(encoding="utf-8")


def test_project_create_input_accepts_repository_url() -> None:
    source = _project_schema_source()

    assert "repository_url: str | None" in source
    assert "Field(default=None, max_length=2048)" in source


def test_project_repository_can_attach_repository_and_analysis() -> None:
    source = _project_repository_source()

    assert "async def attach_repository_analysis(" in source
    assert 'project.status = "deploy_ready" if deploy_ready else "analysis_ready"' in source
    assert "project.repository_id = repository_id" in source
    assert "project.analysis_id = analysis_id" in source


def test_project_create_orchestrates_repository_metadata_and_quick_analysis() -> None:
    source = _project_service_source()

    assert "RepositoryMetadataInput(repository_url=input_data.repository_url)" in source
    assert "self.repository_service.fetch_repository_metadata(" in source
    assert "self.analysis_service.run_quick_analysis(" in source
    assert "project_id=record.id" in source
    assert "self.repository.attach_repository_analysis(" in source


def test_project_service_uses_public_engine_boundaries_only() -> None:
    source = _project_service_source()

    assert "from backend.engines.repository_engine.public import" in source
    assert "from backend.engines.repository_analysis_engine.public import" in source
    assert "repository_engine.internal" not in source
    assert "repository_analysis_engine.internal" not in source


def test_quick_analysis_accepts_optional_project_id() -> None:
    public_source = _analysis_public_source()
    internal_source = _analysis_internal_source()

    assert "project_id: str | None = None" in public_source
    assert "project_id: str | None = None" in internal_source
    assert "project_id=project_id" in internal_source
