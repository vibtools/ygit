from pathlib import Path


APP = Path("frontend/dashboard/assets/app.js")
SPEC = Path("DASHBOARD_PROJECT_DEPLOY_UI_SPEC.md")


def app_source() -> str:
    return APP.read_text(encoding="utf-8")


def compact_js(source: str) -> str:
    return " ".join(source.split())


def request_deploy_source() -> str:
    source = app_source()
    return source.split(
        "async function requestDeploy(projectId, button = null) {",
        1,
    )[1].split(
        "function bindUi() {",
        1,
    )[0]


def project_card_source() -> str:
    source = app_source()
    return source.split(
        "function projectCard(project) {",
        1,
    )[1].split(
        "function emptyProjectState() {",
        1,
    )[0]


def test_project_cards_offer_deploy_review_action() -> None:
    card = project_card_source()
    compact = compact_js(card)

    assert 'const deployLabel = deployReady ? "Deploy" : "Review & Deploy";' in compact
    assert 'data-deploy-project=' in card
    assert 'disabled aria-disabled="true"' not in card
    assert "Deploy locked" not in card


def test_all_deploy_buttons_are_bound_with_button_context() -> None:
    source = app_source()

    assert "$$('[data-deploy-project]')" in source
    assert (
        "requestDeploy("
        "button.dataset.deployProject, "
        "button"
        ")"
        in source
    )


def test_deploy_checks_fresh_backend_readiness_first() -> None:
    request = request_deploy_source()

    readiness_index = request.index(
        "loadProjectDeployReadiness("
    )
    deploy_index = request.index(
        "`/projects/${encodeURIComponent(projectId)}/deploy`"
    )

    assert readiness_index < deploy_index
    assert "if (!readiness?.deploy_ready)" in request


def test_blocked_readiness_never_sends_deployment_post() -> None:
    request = request_deploy_source()
    blocked = request.split(
        "if (!readiness?.deploy_ready) {",
        1,
    )[1].split(
        "setDeployButtonBusy(",
        1,
    )[0]

    assert "return;" in blocked
    assert 'method: "POST"' not in blocked
    assert "renderProjectOpenContext(context)" in blocked
    assert "deployReadinessMessage(readiness)" in blocked


def test_deployment_post_remains_backend_authorized() -> None:
    request = request_deploy_source()
    compact = compact_js(request)

    assert (
        "await fetchJson( "
        "`/projects/${encodeURIComponent(projectId)}/deploy`,"
        in compact
    )
    assert 'method: "POST"' in request
    assert "body: JSON.stringify({})" in request


def test_button_busy_state_prevents_duplicate_submission() -> None:
    source = app_source()
    request = request_deploy_source()
    compact = compact_js(request)

    assert "function setDeployButtonBusy(" in source
    assert 'button.setAttribute("aria-busy", "true")' in source
    assert "button.disabled = true" in source
    assert "button.disabled = false" in source
    assert 'setDeployButtonBusy(button, true, "Checking...")' in compact
    assert 'setDeployButtonBusy( button, true, "Queueing..." )' in compact
    assert "setDeployButtonBusy(button, false)" in compact


def test_known_deployment_errors_have_safe_messages() -> None:
    source = app_source()

    for marker in (
        "DEPLOYMENT_PROJECT_NOT_READY",
        "DEPLOYMENT_ANALYSIS_REQUIRED",
        "DEPLOYMENT_GITHUB_NOT_CONNECTED",
        "DEPLOYMENT_CLOUDFLARE_NOT_CONNECTED",
        "DEPLOYMENT_ALREADY_RUNNING",
        "DEPLOYMENT_QUEUE_FAILED",
    ):
        assert marker in source

    assert "Review the current deployment blockers" in source


def test_deploy_failure_does_not_clear_project_state() -> None:
    request = request_deploy_source()

    assert "state.projects = []" not in request
    assert "deleteProject" not in request
    assert 'method: "DELETE"' not in request
    assert 'method: "PATCH"' not in request
    assert 'showSystemAlert(error, "warning")' in request


def test_deploy_ui_spec_locks_server_authority() -> None:
    source = SPEC.read_text(encoding="utf-8")

    assert "A fresh Deploy Engine readiness response is the authority." in source
    assert "do not send a deployment POST" in source
    assert "The existing Project Open action remains read-only." in source
