const API = "/api/v1";
const state = { projects: [], deployments: [], accounts: [], status: null };

const $ = (selector) => document.querySelector(selector);
const $$ = (selector) => Array.from(document.querySelectorAll(selector));

const viewMeta = {
  dashboard: ["Dashboard", "Paste a Git repository, analyze it, connect accounts, and deploy to your own Cloudflare Pages."],
  projects: ["Projects", "Create, inspect, and deploy Git-backed projects."],
  deployments: ["Deployments", "Track queued, running, completed, and failed deployments."],
  "connected-accounts": ["Connected Accounts", "Connect GitHub and Cloudflare without exposing raw provider tokens."],
  "github-repositories": ["GitHub Repositories", "Review imported repositories and use one to create another YGIT project."],
  templates: ["Templates", "Beta starter templates for supported repository types."],
  settings: ["Settings", "MVP-safe defaults and platform constraints."],
  "feature-preview": ["Feature Preview", "Future capabilities are grouped here to keep the MVP dashboard clean."],
};

async function fetchJson(path, options = {}) {
  const response = await fetch(`${API}${path}`, {
    credentials: "include",
    headers: { "Content-Type": "application/json", ...(options.headers || {}) },
    ...options,
  });
  const contentType = response.headers.get("content-type") || "";
  const body = contentType.includes("application/json") ? await response.json() : null;
  if (!response.ok || body?.success === false) {
    const error = body?.error || { code: `HTTP_${response.status}`, message: "Request failed." };
    throw new Error(`${error.code}: ${error.message}`);
  }
  return body?.data ?? body;
}

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function two(value) {
  const n = Number(value || 0);
  return n < 10 ? `0${n}` : String(n);
}

function formatAccountDate(value) {
  const parsed = Date.parse(value || "");
  if (!Number.isFinite(parsed)) return "Not available";
  return new Intl.DateTimeFormat(undefined, {
    dateStyle: "medium",
  }).format(new Date(parsed));
}

function formatRelativeTime(value) {
  const parsed = Date.parse(value || "");
  if (!Number.isFinite(parsed)) return "Not checked yet";

  const seconds = Math.max(0, Math.round((Date.now() - parsed) / 1000));
  if (seconds < 60) return "just now";

  const minutes = Math.floor(seconds / 60);
  if (minutes < 60) return `${minutes} min ago`;

  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours} hr ago`;

  const days = Math.floor(hours / 24);
  if (days < 30) return `${days} day${days === 1 ? "" : "s"} ago`;

  return formatAccountDate(value);
}

function providerAvatar(provider) {
  if (provider === "github") {
    return `<span class="provider-avatar provider-avatar-github" aria-hidden="true">
      <svg viewBox="0 0 24 24"><path d="M12 2.8a9.2 9.2 0 0 0-2.9 17.9c.5.1.7-.2.7-.5v-1.8c-2.9.6-3.5-1.2-3.5-1.2-.5-1.2-1.2-1.5-1.2-1.5-.9-.7.1-.7.1-.7 1.1.1 1.6 1.1 1.6 1.1.9 1.6 2.5 1.1 3 .8.1-.7.4-1.1.7-1.3-2.3-.3-4.7-1.2-4.7-5.1 0-1.1.4-2.1 1.1-2.8-.1-.3-.5-1.3.1-2.7 0 0 .9-.3 3 1.1a10.2 10.2 0 0 1 5.4 0c2.1-1.4 3-1.1 3-1.1.6 1.4.2 2.4.1 2.7.7.7 1.1 1.7 1.1 2.8 0 4-2.4 4.8-4.7 5.1.4.3.7 1 .7 2v2.6c0 .3.2.6.7.5A9.2 9.2 0 0 0 12 2.8Z"/></svg>
    </span>`;
  }

  return `<span class="provider-avatar provider-avatar-cloudflare" aria-hidden="true">
    <svg viewBox="0 0 24 24"><path d="M7.2 17.5h10.9a3.3 3.3 0 0 0 .5-6.6A5.9 5.9 0 0 0 7.4 9.1a4.2 4.2 0 0 0-.2 8.4Z"/><path d="M4.5 17.5h2.7"/></svg>
  </span>`;
}

function githubImportedRepositories() {
  const repositories = new Map();

  state.projects.forEach((project) => {
    const repositoryUrl = String(
      project?.repository_url ||
      project?.repository?.url ||
      ""
    ).trim();

    if (!repositoryUrl || !repositoryUrl.toLowerCase().includes("github.com/")) {
      return;
    }

    const key = repositoryUrl.replace(/\.git$/i, "").toLowerCase();
    const existing = repositories.get(key);

    if (existing) {
      existing.projectCount += 1;
      return;
    }

    repositories.set(key, {
      url: repositoryUrl,
      name: repositoryNameFromUrl(repositoryUrl),
      projectCount: 1,
    });
  });

  return [...repositories.values()].sort((left, right) =>
    left.name.localeCompare(right.name)
  );
}

function repositoryNameFromUrl(repositoryUrl) {
  const normalized = String(repositoryUrl || "")
    .replace(/\.git$/i, "")
    .replace(/\/$/, "");
  const segments = normalized.split("/").filter(Boolean);
  return segments.slice(-2).join("/") || "GitHub repository";
}

function repositoryProjectName(repositoryUrl) {
  const repositoryName = repositoryNameFromUrl(repositoryUrl).split("/").pop();
  return String(repositoryName || "GitHub Project")
    .replaceAll("-", " ")
    .replaceAll("_", " ")
    .replace(/\b\w/g, (character) => character.toUpperCase());
}

function repositoryProjectSlug(repositoryUrl) {
  const repositoryName = repositoryNameFromUrl(repositoryUrl).split("/").pop();
  return String(repositoryName || "github-project")
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "")
    .slice(0, 63) || "github-project";
}


function projectStatusView(status) {
  const normalized = String(status || "draft").toLowerCase();
  const map = {
    draft: ["Draft", "neutral", "Repository is waiting for analysis."],
    repository_attached: ["Repository linked", "info", "Repository metadata is connected."],
    analysis_ready: ["Analysis ready", "warning", "Analysis completed, but deployment is not ready yet."],
    deploy_ready: ["Deploy ready", "success", "Project passed deployment readiness checks."],
    deployed: ["Live", "success", "Website is live."],
    failed: ["Failed", "danger", "Project needs attention."],
    deleted: ["Deleted", "neutral", "Project has been removed."],
  };
  const [label, tone, copy] = map[normalized] || [normalized.replaceAll("_", " "), "neutral", "Status is available."];
  return { label, tone, copy };
}

function isProjectDeployReady(project) {
  return project?.status === "deploy_ready" || project?.status === "deployed";
}

function friendlyErrorMessage(error) {
  const raw =
    typeof error === "string"
      ? error
      : error?.message || String(error || "");

  const messages = {
    DEPLOYMENT_PROJECT_NOT_READY:
      "Deployment is blocked. Review the current deployment blockers.",
    DEPLOYMENT_ANALYSIS_REQUIRED:
      "Repository Analysis must complete before deployment.",
    DEPLOYMENT_GITHUB_NOT_CONNECTED:
      "Connect the GitHub App installation before deployment.",
    DEPLOYMENT_CLOUDFLARE_NOT_CONNECTED:
      "Connect the Cloudflare account before deployment.",
    DEPLOYMENT_ALREADY_RUNNING:
      "A deployment is already queued or running for this Project.",
    DEPLOYMENT_QUEUE_FAILED:
      "YGIT could not queue the deployment. The Project was not changed.",
    AUTH_REQUIRED:
      "Your session has expired. Sign in again.",
  };

  const matched = Object.entries(messages).find(([code]) =>
    raw.includes(code)
  );

  if (matched) return matched[1];

  if (
    error instanceof TypeError ||
    raw.includes("Failed to fetch") ||
    raw.includes("NetworkError")
  ) {
    return "YGIT could not be reached. Check the connection and try again.";
  }

  if (raw.includes(":")) {
    return raw.split(":").slice(1).join(":").trim() || raw;
  }

  return raw || "Request failed. Please try again.";
}

function setView(view) {
  const safeView = viewMeta[view] ? view : "dashboard";
  const [title, subtitle] = viewMeta[safeView];
  $("#view-title").textContent = title;
  $("#view-subtitle").textContent = subtitle;
  $("[data-view-panel=\"" + safeView + "\"]")?.classList.remove("hidden");
  $$('[data-view-panel]').forEach((panel) => panel.classList.toggle("hidden", panel.dataset.viewPanel !== safeView));
  $$('[data-view]').forEach((link) => link.classList.toggle("active", link.dataset.view === safeView));
  location.hash = safeView;
}


function showSystemAlert(message, tone = "warning") {
  const alert = $("#system-alert");
  alert.textContent = friendlyErrorMessage(message);
  alert.dataset.tone = tone;
  alert.classList.remove("hidden");
}

function normalizeMetricStatus(value) {
  return String(value || "").trim().toLowerCase();
}

function titleCaseMetric(value) {
  return String(value || "")
    .replaceAll("_", " ")
    .replaceAll("-", " ")
    .split(/\s+/)
    .filter(Boolean)
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ");
}

function deploymentMetricTimestamp(deployment) {
  const candidates = [
    deployment?.updated_at,
    deployment?.completed_at,
    deployment?.started_at,
    deployment?.queued_at,
    deployment?.created_at,
  ]
    .map((value) => Date.parse(value || ""))
    .filter((value) => Number.isFinite(value));

  return candidates.length ? Math.max(...candidates) : 0;
}

function latestDeploymentMetric() {
  return [...state.deployments]
    .sort(
      (left, right) =>
        deploymentMetricTimestamp(right) -
        deploymentMetricTimestamp(left)
    )[0] || null;
}

function formatMetricTimestamp(timestamp) {
  if (!timestamp) return "Timestamp unavailable";

  return new Intl.DateTimeFormat(undefined, {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(timestamp));
}

function projectFrameworkName(project) {
  const candidates = [
    project?.framework,
    project?.detected_framework,
    project?.analysis?.framework,
    project?.analysis_result?.framework,
  ];

  const detected = candidates.find(
    (value) => String(value || "").trim()
  );

  return detected
    ? titleCaseMetric(detected)
    : null;
}

function frameworkUsageMetric() {
  const frameworks = state.projects
    .map(projectFrameworkName)
    .filter(Boolean);

  if (!frameworks.length) {
    return {
      value: "Pending",
      note: "Available after repository analysis",
      tone: "muted",
    };
  }

  const counts = new Map();

  frameworks.forEach((framework) => {
    counts.set(
      framework,
      (counts.get(framework) || 0) + 1
    );
  });

  const [topFramework, topCount] = [...counts.entries()]
    .sort((left, right) => {
      if (right[1] !== left[1]) {
        return right[1] - left[1];
      }

      return left[0].localeCompare(right[0]);
    })[0];

  return {
    value: topFramework,
    note: `${topCount} of ${frameworks.length} detected projects`,
    tone: "primary",
  };
}

function platformStatusMetric() {
  if (!state.status) {
    return {
      value: "Unknown",
      note: "Status endpoint unavailable",
      tone: "muted",
    };
  }

  const message =
    state.status.message ||
    state.status.summary ||
    "Platform status endpoint responded";

  if (state.status.maintenance === true) {
    return {
      value: "Maintenance",
      note: message,
      tone: "warning",
    };
  }

  const rawStatus = normalizeMetricStatus(
    state.status.status ||
    state.status.overall_status ||
    state.status.state
  );

  const degraded =
    state.status.healthy === false ||
    ["degraded", "unhealthy", "failed", "error"]
      .some((value) => rawStatus.includes(value));

  if (degraded) {
    return {
      value: "Degraded",
      note: message,
      tone: "error",
    };
  }

  return {
    value: rawStatus
      ? titleCaseMetric(rawStatus)
      : "Operational",
    note: message,
    tone: "success",
  };
}

function queueStatusMetric() {
  const activeStatuses = new Set([
    "pending",
    "queued",
    "running",
    "retry_waiting",
  ]);

  const activeCount = state.deployments.filter(
    (deployment) =>
      activeStatuses.has(
        normalizeMetricStatus(deployment.status)
      )
  ).length;

  const failedCount = state.deployments.filter(
    (deployment) =>
      normalizeMetricStatus(deployment.status) === "failed"
  ).length;

  if (activeCount) {
    return {
      value: "Active",
      note: `${activeCount} queued or running deployments`,
      tone: "warning",
    };
  }

  return {
    value: "Idle",
    note: failedCount
      ? `${failedCount} failed in loaded history`
      : "No queued or running deployments",
    tone: "muted",
  };
}

function deploymentMetricTone(status) {
  const normalized = normalizeMetricStatus(status);

  if (["completed", "success"].includes(normalized)) {
    return "success";
  }

  if (normalized === "failed") {
    return "error";
  }

  if (
    ["pending", "queued", "running", "retry_waiting"]
      .includes(normalized)
  ) {
    return "warning";
  }

  return "muted";
}

function setDashboardMetric(
  valueId,
  noteId,
  value,
  note,
  tone = "muted"
) {
  const valueNode = $(`#${valueId}`);
  const noteNode = $(`#${noteId}`);

  if (!valueNode) return;

  valueNode.textContent = value;
  valueNode.classList.remove(
    "is-primary",
    "is-success",
    "is-warning",
    "is-error",
    "is-muted"
  );
  valueNode.classList.add(`is-${tone}`);

  if (noteNode) {
    noteNode.textContent = note;
  }
}

function renderMetrics() {
  const projectCount = state.projects.length;
  const deploymentCount = state.deployments.length;

  const connectedCount = state.accounts.filter(
    (item) =>
      item.connected ||
      item.status === "connected"
  ).length;

  const completedStatuses = new Set([
    "completed",
    "success",
  ]);

  const terminalStatuses = new Set([
    "completed",
    "success",
    "failed",
    "cancelled",
  ]);

  const completedCount = state.deployments.filter(
    (deployment) =>
      completedStatuses.has(
        normalizeMetricStatus(deployment.status)
      )
  ).length;

  const terminalCount = state.deployments.filter(
    (deployment) =>
      terminalStatuses.has(
        normalizeMetricStatus(deployment.status)
      )
  ).length;

  const liveSites = state.deployments.filter(
    (deployment) =>
      deployment.deployment_url &&
      completedStatuses.has(
        normalizeMetricStatus(deployment.status)
      )
  ).length;

  const successPercent = terminalCount
    ? Math.round(
        (completedCount / terminalCount) * 100
      )
    : null;

  const latestDeployment = latestDeploymentMetric();
  const latestStatus = normalizeMetricStatus(
    latestDeployment?.status
  );

  const frameworkMetric = frameworkUsageMetric();
  const platformMetric = platformStatusMetric();
  const queueMetric = queueStatusMetric();

  setDashboardMetric(
    "metric-projects",
    "metric-projects-note",
    two(projectCount),
    projectCount
      ? "Loaded from Project Engine"
      : "No projects yet",
    projectCount ? "primary" : "muted"
  );

  setDashboardMetric(
    "metric-deployments",
    "metric-deployments-note",
    two(deploymentCount),
    deploymentCount
      ? "Loaded from deployment history"
      : "Worker ready",
    deploymentCount ? "primary" : "muted"
  );

  setDashboardMetric(
    "metric-success-rate",
    "metric-success-rate-note",
    successPercent === null
      ? "—"
      : `${successPercent}%`,
    terminalCount
      ? `${completedCount} successful of ${terminalCount} terminal deployments`
      : "No terminal deployments",
    successPercent === null
      ? "muted"
      : "success"
  );

  setDashboardMetric(
    "metric-accounts",
    "metric-accounts-note",
    two(connectedCount),
    `${connectedCount} of 2 providers connected`,
    connectedCount === 2
      ? "success"
      : "muted"
  );

  setDashboardMetric(
    "metric-live-sites",
    "metric-live-sites-note",
    two(liveSites),
    liveSites
      ? "Cloudflare Pages URLs available"
      : "No live site URL yet",
    liveSites
      ? "success"
      : "muted"
  );

  setDashboardMetric(
    "metric-last-deployment",
    "metric-last-deployment-note",
    latestDeployment
      ? titleCaseMetric(
          latestStatus || "unknown"
        )
      : "None",
    latestDeployment
      ? formatMetricTimestamp(
          deploymentMetricTimestamp(
            latestDeployment
          )
        )
      : "No deployment history",
    latestDeployment
      ? deploymentMetricTone(latestStatus)
      : "muted"
  );

  setDashboardMetric(
    "metric-framework-usage",
    "metric-framework-usage-note",
    frameworkMetric.value,
    frameworkMetric.note,
    frameworkMetric.tone
  );

  setDashboardMetric(
    "metric-platform-status",
    "metric-platform-status-note",
    platformMetric.value,
    platformMetric.note,
    platformMetric.tone
  );

  setDashboardMetric(
    "metric-queue-status",
    "metric-queue-status-note",
    queueMetric.value,
    queueMetric.note,
    queueMetric.tone
  );
}


function projectOpenErrorMessage(error) {
  const raw = String(error?.message || error || "");
  const mappings = {
    PROJECT_NOT_FOUND: "The Project could not be found or is no longer available.",
    REPOSITORY_NOT_FOUND: "Repository metadata is not available for this Project.",
    ANALYSIS_NOT_FOUND: "Repository Analysis details are not available for this Project.",
    AUTH_REQUIRED: "Your session has expired. Sign in again.",
  };

  const matched = Object.entries(mappings).find(([code]) =>
    raw.includes(code)
  );

  if (matched) return matched[1];

  if (
    error instanceof TypeError ||
    raw.includes("Failed to fetch") ||
    raw.includes("NetworkError")
  ) {
    return "YGIT could not be reached. Check the connection and try again.";
  }

  return "A Project detail could not be loaded. Existing Project data was preserved.";
}

function projectDetailField(label, value) {
  const displayValue =
    value === null ||
    value === undefined ||
    String(value).trim() === ""
      ? "Not available"
      : String(value);

  return `<div class="project-detail-field">
    <span>${escapeHtml(label)}</span>
    <strong>${escapeHtml(displayValue)}</strong>
  </div>`;
}

function projectDetailList(title, values, emptyCopy) {
  const items = Array.isArray(values)
    ? values
        .map((value) => String(value || "").trim())
        .filter(Boolean)
    : [];

  const body = items.length
    ? `<ul class="project-detail-list">${items
        .map((item) => `<li>${escapeHtml(item)}</li>`)
        .join("")}</ul>`
    : `<p class="muted">${escapeHtml(emptyCopy)}</p>`;

  return `<section class="project-detail-section">
    <h4>${escapeHtml(title)}</h4>
    ${body}
  </section>`;
}

function projectReadinessMessage(reason) {
  const messages = {
    repository_required: "Attach a repository before deployment.",
    analysis_required: "Repository Analysis must complete before deployment.",
    analysis_not_deploy_ready: "Repository Analysis found deployment blockers.",
    github_not_connected: "Connect the GitHub App installation.",
    cloudflare_not_connected: "Connect the Cloudflare account.",
  };

  return (
    messages[reason] ||
    String(reason || "Unknown readiness blocker").replaceAll("_", " ")
  );
}

function settledProjectValue(result, key) {
  if (result.status !== "fulfilled") return null;
  return result.value?.[key] || result.value || null;
}

async function loadProjectOpenContext(projectId) {
  const projectPayload = await fetchJson(
    `/projects/${encodeURIComponent(projectId)}`
  );
  const project = projectPayload?.project || projectPayload;

  const secondaryReads = [
    fetchJson(
      `/projects/${encodeURIComponent(projectId)}/readiness`
    ),
    project?.repository_id
      ? fetchJson(
          `/repositories/${encodeURIComponent(project.repository_id)}`
        )
      : Promise.resolve(null),
    project?.analysis_id
      ? fetchJson(
          `/repository-analysis/${encodeURIComponent(project.analysis_id)}`
        )
      : Promise.resolve(null),
  ];

  const [readinessResult, repositoryResult, analysisResult] =
    await Promise.allSettled(secondaryReads);

  const failures = [
    ["Readiness", readinessResult],
    ["Repository", repositoryResult],
    ["Analysis", analysisResult],
  ]
    .filter(([, result]) => result.status === "rejected")
    .map(
      ([label, result]) =>
        `${label}: ${projectOpenErrorMessage(result.reason)}`
    );

  return {
    project,
    readiness: settledProjectValue(readinessResult, "readiness"),
    repository: settledProjectValue(repositoryResult, "repository"),
    analysis: settledProjectValue(analysisResult, "analysis"),
    failures,
  };
}

function renderProjectOpenContext(context) {
  const panel = $("#project-detail-panel");
  const title = $("#project-detail-title");
  const status = $("#project-detail-status");
  const content = $("#project-detail-content");

  if (!panel || !title || !status || !content) return;

  const project = context.project || {};
  const repository = context.repository || {};
  const analysis = context.analysis || {};
  const readiness = context.readiness || {};
  const blockingReasons = Array.isArray(readiness.blocking_reasons)
    ? readiness.blocking_reasons.map(projectReadinessMessage)
    : [];

  title.textContent =
    project.name ||
    project.slug ||
    project.id ||
    "Project";

  if (context.failures.length) {
    status.textContent =
      "Project details are partially available. Existing Project data was preserved.";
    status.dataset.tone = "warning";
  } else if (readiness.deploy_ready === true) {
    status.textContent =
      "Project details loaded. Deploy Engine reports this Project as ready.";
    status.dataset.tone = "success";
  } else {
    status.textContent =
      "Project details loaded. Deployment prerequisites are shown below.";
    status.dataset.tone = "warning";
  }

  const analysisWarnings = Array.isArray(analysis.warnings)
    ? analysis.warnings
    : [];
  const analysisErrors = Array.isArray(analysis.errors)
    ? analysis.errors
    : [];

  content.innerHTML = `
    <div class="project-detail-grid">
      ${projectDetailField("Project ID", project.id)}
      ${projectDetailField("Project status", project.status)}
      ${projectDetailField("Slug", project.slug)}
      ${projectDetailField(
        "Repository URL",
        repository.repository_url || project.repository_id
      )}
      ${projectDetailField("Default branch", repository.default_branch)}
      ${projectDetailField("Visibility", repository.visibility)}
      ${projectDetailField(
        "Latest commit",
        repository.latest_commit_sha
      )}
      ${projectDetailField("Framework", analysis.framework)}
      ${projectDetailField("Package manager", analysis.package_manager)}
      ${projectDetailField("Build command", analysis.build_command)}
      ${projectDetailField("Output directory", analysis.output_directory)}
      ${projectDetailField("Analysis score", analysis.score)}
      ${projectDetailField(
        "Deploy ready",
        readiness.deploy_ready === true ? "Yes" : "No"
      )}
    </div>
    ${projectDetailList(
      "Deployment readiness",
      blockingReasons,
      readiness.deploy_ready === true
        ? "No deployment blockers reported."
        : "Readiness details are not available."
    )}
    ${projectDetailList(
      "Analysis warnings",
      analysisWarnings,
      "No Analysis warnings reported."
    )}
    ${projectDetailList(
      "Analysis errors",
      analysisErrors,
      "No Analysis errors reported."
    )}
    ${projectDetailList(
      "Partial read notices",
      context.failures,
      "All requested Project details loaded."
    )}
  `;

  panel.classList.remove("hidden");
  panel.scrollIntoView({
    behavior: "smooth",
    block: "nearest",
  });
}

async function openProject(projectId, button = null) {
  if (!projectId) return;

  const panel = $("#project-detail-panel");
  const status = $("#project-detail-status");
  const originalLabel = button?.textContent || "Open";

  if (button) {
    button.disabled = true;
    button.textContent = "Opening...";
    button.setAttribute("aria-busy", "true");
  }

  panel?.classList.remove("hidden");

  if (status) {
    status.textContent =
      "Loading Project, Repository, Analysis, and readiness...";
    status.dataset.tone = "neutral";
  }

  try {
    const context = await loadProjectOpenContext(projectId);
    renderProjectOpenContext(context);
  } catch (error) {
    const message = projectOpenErrorMessage(error);
    showSystemAlert(message, "warning");

    if (status) {
      status.textContent = message;
      status.dataset.tone = "danger";
    }
  } finally {
    if (button) {
      button.disabled = false;
      button.textContent = originalLabel;
      button.removeAttribute("aria-busy");
    }
  }
}


function deployReadinessMessage(readiness) {
  if (readiness?.deploy_ready === true) {
    return "Deploy Engine readiness checks passed.";
  }

  const reasons = Array.isArray(readiness?.blocking_reasons)
    ? readiness.blocking_reasons
    : [];

  if (!reasons.length) {
    return "Deployment is blocked by an unspecified readiness check.";
  }

  return reasons
    .map(projectReadinessMessage)
    .join(" ");
}

async function loadProjectDeployReadiness(projectId) {
  const payload = await fetchJson(
    `/projects/${encodeURIComponent(projectId)}/readiness`
  );

  return payload?.readiness || payload;
}

function setDeployButtonBusy(button, busy, label = null) {
  if (!button) return;

  if (busy) {
    if (!button.dataset.originalLabel) {
      button.dataset.originalLabel =
        button.textContent || "Deploy";
    }

    button.disabled = true;
    button.setAttribute("aria-busy", "true");

    if (label) {
      button.textContent = label;
    }

    return;
  }

  button.disabled = false;
  button.removeAttribute("aria-busy");

  if (button.dataset.originalLabel) {
    button.textContent = button.dataset.originalLabel;
    delete button.dataset.originalLabel;
  }
}


function projectCard(project) {
  const status = project.status || "draft";
  const statusView = projectStatusView(status);
  const deployReady = isProjectDeployReady(project);
  const repositoryRef =
    project.repository_url ||
    project.repository_id ||
    "Repository pending";
  const deployLabel =
    deployReady ? "Deploy" : "Review & Deploy";

  return `<article class="list-item project-card ${escapeHtml(status)}">
    <div class="project-card-main">
      <div class="project-card-title-row">
        <strong>${escapeHtml(project.name || project.slug || project.id)}</strong>
        <span class="pill status-badge ${escapeHtml(statusView.tone)}">${escapeHtml(statusView.label)}</span>
      </div>
      <p class="project-meta">${escapeHtml(project.slug || "no slug")} · ${escapeHtml(repositoryRef)}</p>
      <p class="project-readiness">${escapeHtml(statusView.copy)}</p>
    </div>
    <div class="form-actions project-actions">
      <button class="secondary-button deploy-button" data-deploy-project="${escapeHtml(project.id)}" data-project-status="${escapeHtml(status)}" type="button" title="YGIT checks current backend readiness before deployment">${deployLabel}</button>
      <button class="secondary-button" data-project-id="${escapeHtml(project.id)}" type="button">Open</button>
    </div>
  </article>`;
}

function emptyProjectState() {
  return `<div class="empty-state"><p class="eyebrow">Empty State</p><h3>No projects yet</h3><p class="muted">Create a project by pasting a GitHub repository URL. YGIT will analyze it before deployment.</p><button class="primary-button" data-open-project-form type="button">Create Project</button></div>`;
}

function renderProjects() {
  const html = state.projects.length ? state.projects.map(projectCard).join("") : emptyProjectState();
  $("#project-list").innerHTML = html;
  $("#dashboard-project-list").innerHTML = state.projects.length ? state.projects.slice(0, 4).map(projectCard).join("") : emptyProjectState();
  $$('[data-deploy-project]').forEach((button) => button.addEventListener('click', () => requestDeploy(button.dataset.deployProject, button)));
  $$("[data-project-id]").forEach((button) => button.addEventListener("click", () => openProject(button.dataset.projectId, button)));
  $$('[data-open-project-form]').forEach((button) => button.addEventListener('click', () => { setView("projects"); $("#project-form").classList.remove("hidden"); }));
  renderMetrics();
}

function deploymentEmptyState() {
  return `<div class="empty-state deployment-empty-state">
    <div class="deployment-empty-layout">
      <div class="deployment-empty-illustration" aria-hidden="true">
        <svg viewBox="0 0 520 340" role="presentation" focusable="false">
          <defs>
            <linearGradient id="deployment-card-fill" x1="0" y1="0" x2="1" y2="1">
              <stop offset="0" stop-color="#172235"/>
              <stop offset="1" stop-color="#0b1220"/>
            </linearGradient>
            <linearGradient id="deployment-flow-line" x1="0" y1="0" x2="1" y2="0">
              <stop offset="0" stop-color="#3b82f6"/>
              <stop offset="1" stop-color="#38bdf8"/>
            </linearGradient>
          </defs>
          <rect x="42" y="38" width="436" height="264" rx="24" fill="url(#deployment-card-fill)" stroke="rgba(148,163,184,.24)"/>
          <circle cx="76" cy="72" r="6" fill="#ef4444" opacity=".75"/>
          <circle cx="98" cy="72" r="6" fill="#f59e0b" opacity=".75"/>
          <circle cx="120" cy="72" r="6" fill="#10b981" opacity=".75"/>
          <path d="M64 98h392" stroke="rgba(148,163,184,.18)"/>
          <path d="M112 208h294" stroke="url(#deployment-flow-line)" stroke-width="4" stroke-linecap="round"/>
          <path d="m394 196 16 12-16 12" fill="none" stroke="#38bdf8" stroke-width="4" stroke-linecap="round" stroke-linejoin="round"/>
          <g transform="translate(76 142)">
            <rect width="82" height="94" rx="16" fill="#101a2b" stroke="rgba(59,130,246,.48)"/>
            <path d="M24 30h34M24 45h26M24 60h34" stroke="#93c5fd" stroke-width="4" stroke-linecap="round"/>
          </g>
          <g transform="translate(188 142)">
            <rect width="82" height="94" rx="16" fill="#101a2b" stroke="rgba(56,189,248,.40)"/>
            <circle cx="31" cy="37" r="12" fill="none" stroke="#7dd3fc" stroke-width="4"/>
            <path d="M48 57h13M54.5 50.5v13" stroke="#7dd3fc" stroke-width="4" stroke-linecap="round"/>
          </g>
          <g transform="translate(300 142)">
            <rect width="82" height="94" rx="16" fill="#101a2b" stroke="rgba(16,185,129,.42)"/>
            <path d="M41 24v39M27 49l14 14 14-14M24 74h34" fill="none" stroke="#6ee7b7" stroke-width="4" stroke-linecap="round" stroke-linejoin="round"/>
          </g>
          <circle cx="424" cy="208" r="28" fill="rgba(16,185,129,.16)" stroke="rgba(16,185,129,.55)"/>
          <path d="m412 208 8 8 17-20" fill="none" stroke="#6ee7b7" stroke-width="5" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
      </div>
      <div class="deployment-empty-copy">
        <p class="eyebrow">Deployment path</p>
        <h3>No deployments yet.</h3>
        <p class="muted">Complete the deployment path once and every queued, running, completed, or failed deployment will appear here.</p>
        <div class="deployment-empty-flow" aria-label="Deployment onboarding flow">
          <span><b>1</b><strong>Create a project</strong></span>
          <i aria-hidden="true">→</i>
          <span><b>2</b><strong>Connect GitHub</strong></span>
          <i aria-hidden="true">→</i>
          <span><b>3</b><strong>Deploy</strong></span>
          <i aria-hidden="true">→</i>
          <span><b>4</b><strong>Website Live</strong></span>
        </div>
        <div class="form-actions deployment-empty-actions">
          <button class="primary-button" data-deployment-empty-view="projects" type="button">Create Project</button>
          <button class="secondary-button" data-deployment-empty-view="connected-accounts" type="button">Connect Accounts</button>
        </div>
      </div>
    </div>
  </div>`;
}

function renderDeployments() {
  const target = $("#deployment-list");
  if (!state.deployments.length) {
    target.innerHTML = deploymentEmptyState();
    renderMetrics();
    return;
  }
  target.innerHTML = state.deployments.map((deployment) => `<div class="list-item">
    <header><strong>${escapeHtml(deployment.id || deployment.deployment_id)}</strong><span class="pill ${deployment.status === "completed" ? "success" : deployment.status === "failed" ? "danger" : "warning"}">${escapeHtml(deployment.status || "queued")}</span></header>
    <p>${escapeHtml(deployment.deployment_url || deployment.failure_summary || "Deployment is awaiting pipeline result.")}</p>
  </div>`).join("");
  renderMetrics();
}

function dashboardAccountScopeValue(
  scopes,
  prefix,
  fallback = "Not reported"
) {
  const matched = scopes.find((scope) =>
    String(scope).startsWith(prefix)
  );

  if (!matched) return fallback;

  const value = String(matched)
    .slice(prefix.length)
    .replaceAll("_", " ")
    .trim();

  if (!value) return fallback;

  return value.replace(/\b\w/g, (character) =>
    character.toUpperCase()
  );
}

function dashboardAccountPermissionSummary(
  scopes,
  provider
) {
  const excludedPrefixes =
    provider === "github"
      ? ["github_app:", "repositories:"]
      : [];

  const visible = scopes.filter(
    (scope) =>
      !excludedPrefixes.some((prefix) =>
        String(scope).startsWith(prefix)
      )
  );

  if (!visible.length) {
    return "Not reported";
  }

  const first = visible.slice(0, 2);
  const remaining = visible.length - first.length;
  const summary = first.join(", ");

  return remaining > 0
    ? `${summary} +${remaining}`
    : summary;
}

function dashboardAccountFact(label, value) {
  return `<div class="dashboard-account-fact">
    <span>${escapeHtml(label)}</span>
    <strong title="${escapeHtml(value)}">${escapeHtml(value)}</strong>
  </div>`;
}

function dashboardAccountCard(provider) {
  const account = state.accounts.find(
    (item) => item.provider === provider
  );
  const connected =
    account?.connected ||
    account?.status === "connected";
  const status = String(
    account?.status ||
    (connected ? "connected" : "disconnected")
  ).toLowerCase();
  const statusLabel = status
    .replaceAll("_", " ")
    .replace(/\b\w/g, (character) =>
      character.toUpperCase()
    );
  const accountName =
    account?.account_name ||
    account?.provider_account_name ||
    "Not connected";
  const scopes = Array.isArray(account?.scopes)
    ? account.scopes.map((scope) => String(scope))
    : [];
  const lastSync = connected
    ? formatRelativeTime(account?.last_checked_at)
    : "—";
  const permissionSummary =
    dashboardAccountPermissionSummary(
      scopes,
      provider
    );
  const statusTone = connected
    ? "success"
    : status === "error"
      ? "danger"
      : status === "reconnect_required"
        ? "warning"
        : "neutral";

  const facts =
    provider === "github"
      ? [
          dashboardAccountFact(
            "Username",
            accountName
          ),
          dashboardAccountFact(
            "Repository Access",
            dashboardAccountScopeValue(
              scopes,
              "repositories:"
            )
          ),
          dashboardAccountFact(
            "Scopes",
            permissionSummary
          ),
          dashboardAccountFact(
            "Last Sync",
            lastSync
          ),
        ]
      : [
          dashboardAccountFact(
            "Account",
            accountName
          ),
          dashboardAccountFact(
            "Token Status",
            connected
              ? "Active"
              : statusLabel
          ),
          dashboardAccountFact(
            "Permissions",
            permissionSummary
          ),
          dashboardAccountFact(
            "Last Sync",
            lastSync
          ),
        ];

  const label =
    provider === "github"
      ? "GitHub"
      : "Cloudflare";

  return `<article class="dashboard-provider-card dashboard-provider-card-${provider}">
    <header class="dashboard-provider-card-header">
      <div class="dashboard-provider-title">
        ${providerAvatar(provider)}
        <strong>${label}</strong>
      </div>
      <span class="dashboard-provider-status ${statusTone}">
        <i aria-hidden="true"></i>
        ${escapeHtml(statusLabel)}
      </span>
    </header>
    <div class="dashboard-account-facts">
      ${facts.join("")}
    </div>
    <footer class="dashboard-provider-card-footer">
      <button
        class="secondary-button compact-button"
        type="button"
        data-dashboard-account-manage="${provider}"
      >Manage</button>
    </footer>
  </article>`;
}


function accountCard(provider) {
  const account = state.accounts.find((item) => item.provider === provider);
  const connected = account?.connected || account?.status === "connected";
  const label = provider === "github" ? "GitHub" : "Cloudflare";
  const accountName = escapeHtml(
    account?.account_name ||
    account?.provider_account_name ||
    "Account not connected"
  );
  const status = String(account?.status || "disconnected").toLowerCase();
  const statusLabel = status
    .replaceAll("_", " ")
    .replace(/\b\w/g, (character) => character.toUpperCase());
  const statusTone = connected
    ? "success"
    : status === "error"
      ? "danger"
      : status === "reconnect_required"
        ? "warning"
        : "neutral";
  const manageUrl = provider === "github"
    ? "https://github.com/settings/installations"
    : "https://dash.cloudflare.com";
  const manageLabel = provider === "github"
    ? "Manage on GitHub"
    : "Manage on Cloudflare";
  const connectLabel = !connected && account ? "Reconnect" : "Connect";
  const statusCopy = connected ? "Status: Connected" : `Status: ${statusLabel}`;
  const scopes = Array.isArray(account?.scopes) ? account.scopes : [];
  const scopeHtml = scopes.length
    ? scopes.map((scope) => `<span class="scope-chip">${escapeHtml(scope)}</span>`).join("")
    : `<span class="scope-chip scope-chip-muted">No scopes reported</span>`;
  const repositories = provider === "github"
    ? githubImportedRepositories()
    : [];
  const repositoryLabel = `${repositories.length} ${repositories.length === 1 ? "repository" : "repositories"} imported`;
  const repositorySummary = provider === "github" && connected
    ? `<div class="account-repository-summary">
        <span>${repositoryLabel}</span>
        <button class="ghost-button compact-button" type="button" data-view-github-repositories>View List</button>
      </div>`
    : "";

  const actions = connected
    ? `<div class="form-actions account-actions">
        <button class="danger-button compact-button" type="button" data-disconnect-provider="${provider}">Disconnect</button>
        <a class="provider-manage-link" href="${manageUrl}" target="_blank" rel="noreferrer">${manageLabel}</a>
      </div>`
    : `<div class="form-actions account-actions">
        <a class="primary-button" href="${API}/connected-accounts/${provider}/connect">${connectLabel}</a>
      </div>`;

  return `<article class="account-card" id="${provider}-account-card">
    <header class="account-card-header">
      ${providerAvatar(provider)}
      <div class="account-identity">
        <strong>${label}</strong>
        <span>${accountName}</span>
      </div>
      <span class="pill ${statusTone} account-status-badge" aria-label="${escapeHtml(statusCopy)}">${escapeHtml(statusLabel)}</span>
    </header>
    <div class="account-metadata-grid">
      <div>
        <span>Connection date</span>
        <strong>${connected ? escapeHtml(formatAccountDate(account?.connected_at)) : "—"}</strong>
      </div>
      <div>
        <span>Last sync</span>
        <strong>${connected ? escapeHtml(formatRelativeTime(account?.last_checked_at)) : "—"}</strong>
      </div>
    </div>
    <div class="account-scope-block">
      <span class="account-meta-label">Scopes</span>
      <div class="scope-list">${scopeHtml}</div>
    </div>
    ${repositorySummary}
    ${actions}
  </article>`;
}

function renderGitHubRepositories() {
  const target = $("#github-repository-list");
  if (!target) return;

  const repositories = githubImportedRepositories();

  if (!repositories.length) {
    target.innerHTML = `<div class="empty-state">
      <p class="eyebrow">Imported repositories</p>
      <h3>No GitHub repositories imported yet</h3>
      <p class="muted">Create a project with a GitHub repository URL. Imported repositories will appear here for quick reuse.</p>
      <button class="primary-button" data-use-empty-repository type="button">Create Project</button>
    </div>`;
    return;
  }

  target.innerHTML = repositories.map((repository) => `<article class="repository-browser-card">
    <div class="repository-browser-identity">
      ${providerAvatar("github")}
      <div>
        <strong>${escapeHtml(repository.name)}</strong>
        <span>${escapeHtml(repository.url)}</span>
      </div>
    </div>
    <div class="repository-browser-meta">
      <span>${repository.projectCount} ${repository.projectCount === 1 ? "project" : "projects"} using this repository</span>
      <button
        class="primary-button compact-button"
        type="button"
        data-use-repository-url="${escapeHtml(repository.url)}"
      >Use this repository</button>
    </div>
  </article>`).join("");
}

function renderAccounts() {
  const fullHtml = ["github", "cloudflare"]
    .map(accountCard)
    .join("");
  const dashboardHtml = ["github", "cloudflare"]
    .map(dashboardAccountCard)
    .join("");

  $("#connected-account-grid").innerHTML = fullHtml;

  const dashboardTarget = $("#dashboard-account-grid");
  if (dashboardTarget) {
    dashboardTarget.innerHTML = dashboardHtml;
  }

  $$("[data-dashboard-account-manage]")
    .forEach((button) =>
      button.addEventListener("click", () =>
        setView("connected-accounts")
      )
    );

  renderGitHubRepositories();
  renderMetrics();
}


function renderTimeline() {
  const hasRepository = state.projects.some((p) => p.repository_id || p.repository_url);
  const hasAnalysis = state.projects.some((p) => p.analysis_id || ["analysis_ready", "deploy_ready", "deployed"].includes(p.status));
  const hasDeployReady = state.projects.some((p) => p.status === "deploy_ready" || p.status === "deployed");
  const hasGithub = state.accounts.some((a) => a.provider === "github" && (a.connected || a.status === "connected"));
  const hasCloudflare = state.accounts.some((a) => a.provider === "cloudflare" && (a.connected || a.status === "connected"));
  const hasDeployment = state.deployments.length > 0;
  const hasLiveSite = state.deployments.some((d) => d.deployment_url && (d.status === "completed" || d.status === "success"));

  const steps = [
    ["Repository connected", hasRepository, "A GitHub repository reference is attached to the project."],
    ["Analysis completed", hasAnalysis, hasDeployReady ? "Framework and build settings passed readiness checks." : "Analysis ran; deployment readiness is still pending."],
    ["Accounts connected", hasGithub && hasCloudflare, "GitHub and Cloudflare accounts are linked."],
    ["Deploy ready", hasDeployReady, "Project is eligible for Cloudflare Pages deployment."],
    ["Deploying", hasDeployment, "Deployment events will appear when the worker starts."],
    ["Website live", hasLiveSite, "A public Cloudflare Pages URL is available."],
  ];

  const firstOpen = steps.findIndex(([, done]) => !done);
  $("#deployment-timeline").innerHTML = steps
    .map(([label, done, copy], index) => `<div class="timeline-step ${done ? "done" : index === firstOpen ? "active" : ""}"><div><span class="timeline-dot"></span>${index < steps.length - 1 ? "<span class=\"timeline-line\"></span>" : ""}</div><div class="timeline-copy"><strong>${label}</strong><span>${copy}</span></div></div>`)
    .join("");
}

async function loadStatus() {
  try {
    const data = await fetchJson("/platform/status");
    state.status = data;
    if (data.maintenance) showSystemAlert(data.message || "YGIT is currently in maintenance mode.");
  } catch (_) {
    // Authenticated status may require a session. Keep the dashboard usable as a shell.
  }
}

async function loadProjects() {
  try {
    const data = await fetchJson("/projects?page=1&page_size=20");
    state.projects = data.items || data.projects || [];
  } catch (_) {
    state.projects = [];
  }
  renderProjects();
  renderGitHubRepositories();
  renderTimeline();
}

async function loadAccounts() {
  try {
    const data = await fetchJson("/connected-accounts");
    state.accounts = data.accounts || data.items || [];
  } catch (_) {
    state.accounts = [];
  }
  renderAccounts();
  renderTimeline();
}

async function loadDeployments() {
  const deployments = [];
  for (const project of state.projects.slice(0, 5)) {
    try {
      const data = await fetchJson(`/projects/${encodeURIComponent(project.id)}/deployments?page=1&page_size=5`);
      deployments.push(...(data.items || data.deployments || []));
    } catch (_) {}
  }
  state.deployments = deployments;
  renderDeployments();
  renderTimeline();
}


async function createProject(event) {
  event.preventDefault();
  const status = $("#project-form-status");
  status.textContent = "Importing repository and running analysis...";
  const payload = { name: $("#project-name").value, repository_url: $("#repository-url").value, slug: $("#project-slug").value };

  try {
    const project = await fetchJson("/projects", { method: "POST", body: JSON.stringify(payload) });
    const view = projectStatusView(project?.status || "analysis_ready");
    status.textContent = project?.status === "deploy_ready"
      ? "Project created. Ready to deploy."
      : `Project created. ${view.copy}`;
    $("#project-form").reset();
    await loadProjects();
  } catch (error) {
    status.textContent = friendlyErrorMessage(error);
  }
}


async function requestDeploy(projectId, button = null) {
  if (!projectId) return;

  setDeployButtonBusy(button, true, "Checking...");

  try {
    const readiness =
      await loadProjectDeployReadiness(projectId);

    if (!readiness?.deploy_ready) {
      const blockerMessage =
        deployReadinessMessage(readiness);

      try {
        const context =
          await loadProjectOpenContext(projectId);
        context.readiness = readiness;
        renderProjectOpenContext(context);
      } catch (_) {
        // Readiness remains authoritative even if optional detail reads fail.
      }

      showSystemAlert(
        `Deployment blocked. ${blockerMessage}`,
        "warning"
      );
      return;
    }

    setDeployButtonBusy(
      button,
      true,
      "Queueing..."
    );

    await fetchJson(
      `/projects/${encodeURIComponent(projectId)}/deploy`,
      {
        method: "POST",
        body: JSON.stringify({}),
      }
    );

    showSystemAlert(
      "Deployment queued. Worker events will appear in deployment history.",
      "success"
    );

    await loadDeployments();
  } catch (error) {
    showSystemAlert(error, "warning");
  } finally {
    setDeployButtonBusy(button, false);
  }
}

function bindUi() {
  $$('[data-view]').forEach((link) => link.addEventListener("click", (event) => { event.preventDefault(); setView(link.dataset.view); }));
  $$('[data-view-trigger]').forEach((button) => button.addEventListener("click", () => setView(button.dataset.viewTrigger)));
  $("#new-project-button").addEventListener("click", () => { setView("projects"); $("#project-form").classList.remove("hidden"); });
  $("#open-project-form").addEventListener("click", () => $("#project-form").classList.remove("hidden"));
  $("#cancel-project-form").addEventListener("click", () => $("#project-form").classList.add("hidden"));
  $("#project-form").addEventListener("submit", createProject);
  $("#close-project-detail")?.addEventListener("click", () => $("#project-detail-panel")?.classList.add("hidden"));
  $("#refresh-deployments").addEventListener("click", loadDeployments);
  document.addEventListener("click", (event) => {
    const trigger = event.target.closest("[data-deployment-empty-view]");
    if (!trigger) return;

    const targetView = trigger.dataset.deploymentEmptyView;
    if (!viewMeta[targetView]) return;

    setView(targetView);

    if (targetView === "projects") {
      $("#project-form")?.classList.remove("hidden");
    }
  });

  document.addEventListener("click", (event) => {
    const listTrigger = event.target.closest("[data-view-github-repositories]");
    if (listTrigger) {
      event.preventDefault();
      renderGitHubRepositories();
      setView("github-repositories");
      return;
    }

    const emptyTrigger = event.target.closest("[data-use-empty-repository]");
    if (emptyTrigger) {
      event.preventDefault();
      setView("projects");
      $("#project-form")?.classList.remove("hidden");
      $("#repository-url")?.focus();
      return;
    }

    const repositoryTrigger = event.target.closest("[data-use-repository-url]");
    if (!repositoryTrigger) return;

    event.preventDefault();
    const repositoryUrl = repositoryTrigger.dataset.useRepositoryUrl;
    if (!repositoryUrl) return;

    setView("projects");
    $("#project-form")?.classList.remove("hidden");

    const repositoryInput = $("#repository-url");
    const nameInput = $("#project-name");
    const slugInput = $("#project-slug");

    if (repositoryInput) repositoryInput.value = repositoryUrl;
    if (nameInput && !nameInput.value.trim()) {
      nameInput.value = repositoryProjectName(repositoryUrl);
    }
    if (slugInput && !slugInput.value.trim()) {
      slugInput.value = repositoryProjectSlug(repositoryUrl);
    }

    nameInput?.focus();
  });
}

async function boot() {
  bindUi();
  setView((location.hash || "#dashboard").replace("#", "") || "dashboard");
  await loadStatus();
  await loadProjects();
  await loadAccounts();
  await loadDeployments();
}

document.addEventListener("DOMContentLoaded", boot);


async function disconnectProvider(provider) {
  const label = provider === "github" ? "GitHub" : "Cloudflare";
  const confirmed = window.confirm(
    `Disconnect ${label} from YGIT? For GitHub, this also uninstalls the GitHub App from the connected account.`
  );

  if (!confirmed) {
    return;
  }

  const response = await fetch(`${API}/connected-accounts/${provider}`, {
    method: "DELETE",
    credentials: "include",
    headers: {
      Accept: "application/json",
    },
  });

  if (!response.ok) {
    const payload = await response.json().catch(() => ({}));
    throw new Error(payload?.error?.message || `Unable to disconnect ${label}.`);
  }

  if (typeof loadAccounts === "function") {
    await loadAccounts();
  } else {
    window.location.reload();
  }
}

function handleConnectedAccountDisconnect(event) {
  const button = event.target.closest("[data-disconnect-provider]");
  if (!button) {
    return;
  }

  event.preventDefault();
  const provider = button.dataset.disconnectProvider;
  if (!provider) {
    return;
  }

  disconnectProvider(provider).catch((error) => {
    alert(error.message || "Unable to disconnect provider.");
  });
}

document.addEventListener("click", handleConnectedAccountDisconnect);

const notificationsButton = $("#notifications-button");
if (notificationsButton) notificationsButton.addEventListener("click", () => showSystemAlert("No new notifications.", "success"));

/* Step 27C-3B dashboard metrics and deployment empty state */
(function () {
  const EXTRA_METRICS = [
    { label: 'Last Deployment', value: 'No deployments yet', helper: 'Most recent deploy activity', tone: 'muted' },
    { label: 'Framework Usage', value: 'Detect on import', helper: 'Framework and runtime breakdown', tone: 'primary' },
    { label: 'Platform Status', value: 'Healthy', helper: 'Core platform availability', tone: 'success' },
    { label: 'Queue Status', value: 'Idle', helper: 'Build and deploy queue', tone: 'muted' },
  ];

  function normalizeText(value) {
    return String(value || '').replace(/\s+/g, ' ').trim().toLowerCase();
  }

  function metricTitleSelectors() {
    return '.metric-title, .panel-title, [data-card-title], h3, h4, strong';
  }

  function findMetricsGrid() {
    return document.querySelector(
      '[data-dashboard-metrics], .dashboard-metrics, .metrics-grid, .stats-grid, .overview-grid, .dashboard-grid'
    );
  }

  function buildMetricCard(metric) {
    const card = document.createElement('article');
    card.className = 'metric-card dashboard-metric-card';
    card.setAttribute('data-ygit-extra-metric', normalizeText(metric.label));

    const header = document.createElement('div');
    header.className = 'dashboard-metric-header';

    const title = document.createElement('div');
    title.className = 'dashboard-metric-title';
    title.textContent = metric.label;

    const value = document.createElement('div');
    value.className = 'dashboard-metric-value';
    if (metric.tone) {
      value.classList.add('is-' + metric.tone);
    }
    value.textContent = metric.value;

    const helper = document.createElement('p');
    helper.className = 'dashboard-metric-helper';
    helper.textContent = metric.helper;

    header.appendChild(title);
    card.appendChild(header);
    card.appendChild(value);
    card.appendChild(helper);
    return card;
  }

  function ensureDashboardMetrics() {
    const grid = findMetricsGrid();
    if (!grid || grid.dataset.ygitDashboardMetricsEnhanced === 'true') {
      return;
    }

    grid.dataset.ygitDashboardMetricsEnhanced = 'true';

    const titles = Array.from(grid.querySelectorAll(metricTitleSelectors()));
    titles.forEach(function (node) {
      const normalized = normalizeText(node.textContent);
      if (normalized === 'success rate') {
        node.textContent = 'Deploy Success %';
      }
    });

    const existingLabels = new Set(
      Array.from(grid.querySelectorAll(metricTitleSelectors()))
        .map(function (node) { return normalizeText(node.textContent); })
        .filter(Boolean)
    );

    EXTRA_METRICS.forEach(function (metric) {
      const key = normalizeText(metric.label);
      if (!existingLabels.has(key)) {
        grid.appendChild(buildMetricCard(metric));
      }
    });
  }

  function findDeploymentEmptyTarget() {
    return document.querySelector(
      '[data-deployments-list], [data-page="deployments"] .panel-body, #deployments-view .panel-body, .deployment-list, .deployments-panel .panel-body'
    );
  }

  function deploymentEntriesPresent(target) {
    if (!target) {
      return false;
    }
    if (target.querySelector('.deployment-empty-state')) {
      return true;
    }
    if (target.querySelector('[data-deployment-row], .deployment-row, tbody tr, .timeline-item, .list-item')) {
      return true;
    }
    return false;
  }

  function renderDeploymentEmptyState() {
    const target = findDeploymentEmptyTarget();
    if (!target || deploymentEntriesPresent(target)) {
      return;
    }

    const state = document.createElement('section');
    state.className = 'deployment-empty-state';

    state.innerHTML =
      '<div class="deployment-empty-illustration" aria-hidden="true">' +
      '<svg viewBox="0 0 120 120" fill="none" role="presentation">' +
      '<rect x="18" y="18" width="84" height="84" rx="18" class="deployment-empty-frame"></rect>' +
      '<path d="M38 46h44" class="deployment-empty-line"></path>' +
      '<path d="M38 60h28" class="deployment-empty-line"></path>' +
      '<path d="M38 74h18" class="deployment-empty-line"></path>' +
      '<path d="M74 72l10 10 18-24" class="deployment-empty-check"></path>' +
      '</svg>' +
      '</div>' +
      '<div class="deployment-empty-copy">' +
      '<h3>No deployments yet.</h3>' +
      '<p>Create a project &rarr; Connect GitHub &rarr; Deploy &rarr; Website Live</p>' +
      '</div>';

    target.appendChild(state);
  }

  function initDashboardStep27C3B() {
    ensureDashboardMetrics();
    renderDeploymentEmptyState();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initDashboardStep27C3B);
  } else {
    initDashboardStep27C3B();
  }
})();
