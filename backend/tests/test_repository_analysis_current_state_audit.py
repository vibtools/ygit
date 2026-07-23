from pathlib import Path

ANALYSIS_SERVICE = Path(
    "backend/engines/repository_analysis_engine/internal/service.py"
)
QUICK_ANALYSIS = Path(
    "backend/engines/repository_analysis_engine/internal/quick_analysis.py"
)
READINESS = Path(
    "backend/engines/repository_analysis_engine/internal/deploy_readiness.py"
)
FILE_INDEX = Path(
    "backend/engines/repository_analysis_engine/internal/file_index.py"
)
DEEP_ANALYSIS = Path(
    "backend/engines/repository_analysis_engine/internal/deep_analysis.py"
)
REPOSITORY_SERVICE = Path(
    "backend/engines/repository_engine/internal/service.py"
)
GITHUB_CLIENT = Path(
    "backend/providers/github_provider/client.py"
)
PROJECT_SERVICE = Path(
    "backend/engines/project_engine/internal/service.py"
)
ANALYSIS_ROUTES = Path(
    "backend/app/routes/repository_analysis_routes.py"
)
AUDIT = Path(
    "REPOSITORY_ANALYSIS_CURRENT_STATE_AUDIT.md"
)
PROJECT_STATUS = Path("PROJECT_STATUS.md")


def compact(source: str) -> str:
    return " ".join(source.split())


def test_audit_document_has_version_status_and_revision_history() -> None:
    source = AUDIT.read_text(encoding="utf-8")

    assert "Version: 1.0" in source
    assert "Status: Approved Current-State Audit" in source
    assert "Implementation Change: None" in source
    assert "## Revision History" in source


def test_quick_analysis_depends_on_file_tree_snapshot() -> None:
    source = QUICK_ANALYSIS.read_text(encoding="utf-8")

    assert "extract_file_paths(repository.file_tree_snapshot)" in source
    assert "detect_framework(files)" in source
    assert "detect_package_manager(files)" in source
    assert "evaluate_deploy_readiness(" in source


def test_file_index_contract_matches_documented_keys() -> None:
    source = FILE_INDEX.read_text(encoding="utf-8")

    for marker in (
        '"path", "name", "file", "filename"',
        '"files", "tree", "items", "children", "paths"',
    ):
        assert marker in source

    audit = AUDIT.read_text(encoding="utf-8")
    for key in (
        "path",
        "name",
        "file",
        "filename",
        "files",
        "tree",
        "items",
        "children",
        "paths",
    ):
        assert key in audit


def test_github_metadata_current_gap_is_documented() -> None:
    source = GITHUB_CLIENT.read_text(encoding="utf-8")
    metadata = source.split(
        "async def get_repository_metadata(",
        1,
    )[1].split(
        "def _app_headers(",
        1,
    )[0]
    compact_metadata = compact(metadata)
    audit = AUDIT.read_text(encoding="utf-8")

    assert "latest_commit_sha=None" in compact_metadata
    assert "file_tree_snapshot=" in metadata
    assert '{"default_branch": default_branch}' in metadata
    assert "if default_branch else None" in compact_metadata
    assert '"Authorization"' not in metadata
    assert "no pinned commit SHA" in audit
    assert "no actual file tree" in audit


def test_repository_analysis_input_passes_stored_snapshot() -> None:
    source = REPOSITORY_SERVICE.read_text(encoding="utf-8")
    prepared = source.split(
        "async def prepare_analysis_input(",
        1,
    )[1].split(
        "def to_summary(",
        1,
    )[0]

    assert "latest_commit_sha=detail.latest_commit_sha" in compact(
        prepared
    )
    assert "file_tree_snapshot=detail.file_tree_snapshot" in compact(
        prepared
    )


def test_readiness_is_fail_closed_for_unknown_or_dynamic_input() -> None:
    source = READINESS.read_text(encoding="utf-8")

    for marker in (
        'framework.framework == "unknown"',
        "output_directory.output_directory is None",
        'static_dynamic.render_mode == "dynamic"',
        "build_command.build_command is None",
    ):
        assert marker in source

    assert "deploy_ready=not blocking" in compact(source)


def test_project_creation_attaches_initial_repository_and_analysis() -> None:
    source = PROJECT_SERVICE.read_text(encoding="utf-8")
    create = source.split(
        "async def create_project(",
        1,
    )[1].split(
        "async def list_projects(",
        1,
    )[0]

    assert "run_quick_analysis(" in create
    assert "project_id=record.id" in create
    assert "attach_repository_analysis(" in create
    assert "analysis_id=analysis_detail.id" in create
    assert "deploy_ready=analysis_detail.deploy_ready" in create


def test_recalculation_and_deep_queue_gaps_are_documented() -> None:
    service = ANALYSIS_SERVICE.read_text(encoding="utf-8")
    recalculate = service.split(
        "async def recalculate_analysis(",
        1,
    )[1]
    deep = DEEP_ANALYSIS.read_text(encoding="utf-8")
    routes = ANALYSIS_ROUTES.read_text(encoding="utf-8")
    audit = AUDIT.read_text(encoding="utf-8")

    assert "repository_id=existing.repository_id" in compact(
        recalculate
    )
    assert "project_id=" not in recalculate
    assert "attach_repository_analysis(" not in recalculate
    assert 'job_type="repository_analysis_deep"' in compact(deep)
    assert '@router.post("/deep"' in routes
    assert "does not reattach the new result to the Project" in audit
    assert "Deep Analysis is currently a queue boundary" in audit


def test_project_status_links_audit_and_states_remaining_work() -> None:
    source = PROJECT_STATUS.read_text(encoding="utf-8")

    assert "REPOSITORY_ANALYSIS_CURRENT_STATE_AUDIT.md" in source
    assert "live tree acquisition incomplete" in source
    assert "Project reattachment after recalculation" in source
    assert "Full suite:" in source
    assert "passed, 1 warning" in source
    assert "Full suite: 554 passed, 1 warning" not in source
