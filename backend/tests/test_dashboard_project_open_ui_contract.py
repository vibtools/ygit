from pathlib import Path


HTML = Path("frontend/dashboard/index.html")
APP = Path("frontend/dashboard/assets/app.js")
CSS = Path("frontend/dashboard/assets/styles.css")
SPEC = Path("DASHBOARD_PROJECT_OPEN_UI_SPEC.md")
ANALYSIS_SCHEMA = Path(
    "backend/engines/repository_analysis_engine/schemas.py"
)


def app_source() -> str:
    return APP.read_text(encoding="utf-8")


def test_project_detail_panel_is_present() -> None:
    html = HTML.read_text(encoding="utf-8")

    assert 'id="project-detail-panel"' in html
    assert 'id="project-detail-title"' in html
    assert 'id="project-detail-status"' in html
    assert 'id="project-detail-content"' in html
    assert 'id="close-project-detail"' in html


def test_open_button_is_bound_to_real_handler() -> None:
    source = app_source()

    assert (
        "openProject(button.dataset.projectId, button)"
        in source
    )
    assert "async function openProject(" in source
    assert (
        '$$("[data-project-id]")'
        in source
    )


def test_open_flow_reads_backend_project_context() -> None:
    source = app_source()

    for marker in (
        "`/projects/${encodeURIComponent(projectId)}`",
        "`/projects/${encodeURIComponent(projectId)}/readiness`",
        "`/repositories/${encodeURIComponent(project.repository_id)}`",
        "`/repository-analysis/${encodeURIComponent(project.analysis_id)}`",
    ):
        assert marker in source


def test_secondary_reads_are_partial_failure_safe() -> None:
    source = app_source()

    assert "Promise.allSettled" in source
    assert (
        "Project details are partially available."
        in source
    )
    assert (
        "Existing Project data was preserved."
        in source
    )


def test_open_flow_is_read_only() -> None:
    source = app_source()
    open_flow = source.split(
        "function projectOpenErrorMessage(",
        1,
    )[1].split(
        "function projectCard(project)",
        1,
    )[0]

    for forbidden in (
        'method: "POST"',
        'method: "PATCH"',
        'method: "DELETE"',
        "requestDeploy(",
        "createProject(",
        "recalculate",
    ):
        assert forbidden not in open_flow


def test_backend_values_are_escaped_before_rendering() -> None:
    source = app_source()

    assert "function projectDetailField(" in source
    assert "escapeHtml(label)" in source
    assert "escapeHtml(displayValue)" in source
    assert "escapeHtml(item)" in source


def test_project_open_action_remains_independent_from_deploy_action() -> None:
    source = app_source()
    open_flow = source.split(
        "function projectOpenErrorMessage(",
        1,
    )[1].split(
        "function deployReadinessMessage(readiness) {",
        1,
    )[0]

    assert "async function openProject(" in open_flow
    assert "loadProjectOpenContext(" in open_flow
    assert 'method: "POST"' not in open_flow
    assert "requestDeploy(" not in open_flow
    assert "loadProjectDeployReadiness(" not in open_flow


def test_project_detail_styles_are_present() -> None:
    css = CSS.read_text(encoding="utf-8")

    for marker in (
        ".project-detail-panel",
        ".project-detail-grid",
        ".project-detail-section",
        ".project-detail-list",
        ".project-detail-status",
    ):
        assert marker in css


def test_open_ui_spec_locks_read_only_boundary() -> None:
    source = SPEC.read_text(encoding="utf-8")

    assert "This action is read-only." in source
    assert "change Deploy button behavior" in source
    assert "later independent patch" in source

def test_analysis_items_use_safe_object_formatter() -> None:
    source = app_source()
    formatter = source.split(
        "function projectDetailItemText(value) {",
        1,
    )[1].split(
        "function projectDetailList(title, values, emptyCopy) {",
        1,
    )[0]
    detail_list = source.split(
        "function projectDetailList(title, values, emptyCopy) {",
        1,
    )[1].split(
        "function projectReadinessMessage(reason) {",
        1,
    )[0]

    assert ".map(projectDetailItemText)" in detail_list
    assert '.map((value) => String(value || "").trim())' not in detail_list
    assert 'typeof value === "object"' in formatter
    assert "Unspecified analysis detail." in formatter


def test_object_formatter_prefers_human_readable_fields_and_code() -> None:
    source = app_source()
    formatter = source.split(
        "function projectDetailItemText(value) {",
        1,
    )[1].split(
        "function projectDetailList(title, values, emptyCopy) {",
        1,
    )[0]

    for marker in (
        "value.message",
        "value.detail",
        "value.reason",
        "value.description",
        "value.title",
        "value.name",
        "value.code",
        "message.toLowerCase().includes(code.toLowerCase())",
        'code.replaceAll("_", " ")',
    ):
        assert marker in formatter


def test_object_formatter_does_not_dump_unknown_objects() -> None:
    source = app_source()
    formatter = source.split(
        "function projectDetailItemText(value) {",
        1,
    )[1].split(
        "function projectDetailList(title, values, emptyCopy) {",
        1,
    )[0]

    for forbidden in (
        "JSON.stringify",
        "Object.values",
        "Object.entries",
        "[object Object]",
    ):
        assert forbidden not in formatter


def test_analysis_warning_schema_matches_formatter_contract() -> None:
    source = ANALYSIS_SCHEMA.read_text(encoding="utf-8")
    warning = source.split(
        "class AnalysisWarning(BaseModel):",
        1,
    )[1].split(
        "class AnalysisRecommendation(BaseModel):",
        1,
    )[0]
    record = source.split(
        "class AnalysisRecord(BaseModel):",
        1,
    )[1].split(
        "class AnalysisDetail(AnalysisRecord):",
        1,
    )[0]

    assert "code: str" in warning
    assert "message: str" in warning
    assert "warnings: list[dict[str, Any]] | None = None" in record
    assert "errors: list[dict[str, Any]] | None = None" in record


def test_open_spec_locks_structured_analysis_item_formatting() -> None:
    source = SPEC.read_text(encoding="utf-8")

    assert "Version: 1.1" in source
    assert "structured objects" in source
    assert "`Unspecified analysis detail.`" in source
    assert "never render `[object Object]`" in source
    assert "never dump arbitrary object properties" in source
