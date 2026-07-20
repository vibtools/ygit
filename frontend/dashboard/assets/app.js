const API = "/api/v1";
const state = { projects: [], deployments: [], accounts: [], status: null };

const $ = (selector) => document.querySelector(selector);
const $$ = (selector) => Array.from(document.querySelectorAll(selector));

const viewMeta = {
  dashboard: ["Dashboard", "Paste a Git repository, analyze it, connect accounts, and deploy to your own Cloudflare Pages."],
  projects: ["Projects", "Create, inspect, and deploy Git-backed projects."],
  deployments: ["Deployments", "Track queued, running, completed, and failed deployments."],
  "connected-accounts": ["Connected Accounts", "Connect GitHub and Cloudflare without exposing raw provider tokens."],
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
  const raw = typeof error === "string" ? error : error?.message || String(error || "");
  if (raw.includes("DEPLOYMENT_PROJECT_NOT_READY")) {
    return "This project has been analyzed, but it is not deploy-ready yet. Review the repository analysis before deployment.";
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

function renderMetrics() {
  const projectCount = state.projects.length;
  const deploymentCount = state.deployments.length;
  const connectedCount = state.accounts.filter((item) => item.connected || item.status === "connected").length;
  const completedCount = state.deployments.filter((item) => item.status === "completed" || item.status === "success").length;
  const liveSites = state.deployments.filter((item) => item.deployment_url && (item.status === "completed" || item.status === "success")).length;
  $("#metric-projects").textContent = two(projectCount);
  $("#metric-projects-note").textContent = projectCount ? "+0 this week" : "No projects yet";
  $("#metric-deployments").textContent = two(deploymentCount);
  $("#metric-deployments-note").textContent = deploymentCount ? "Loaded from history" : "Worker ready";
  $("#metric-accounts").textContent = two(connectedCount);
  $("#metric-live-sites").textContent = two(liveSites);
  $("#metric-success-rate").textContent = deploymentCount ? `${Math.round((completedCount / deploymentCount) * 100)}%` : "—";
}


function projectCard(project) {
  const status = project.status || "draft";
  const statusView = projectStatusView(status);
  const deployReady = isProjectDeployReady(project);
  const repositoryRef = project.repository_url || project.repository_id || "Repository pending";
  const deployAttrs = deployReady ? "" : 'disabled aria-disabled="true" title="Repository analysis is not deploy-ready yet"';
  const deployLabel = deployReady ? "Deploy" : "Deploy locked";

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
      <button class="secondary-button deploy-button ${deployReady ? "" : "is-disabled"}" data-deploy-project="${escapeHtml(project.id)}" data-project-status="${escapeHtml(status)}" type="button" ${deployAttrs}>${deployLabel}</button>
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
  $$('[data-deploy-project]:not([disabled])').forEach((button) => button.addEventListener('click', () => requestDeploy(button.dataset.deployProject)));
  $$('[data-open-project-form]').forEach((button) => button.addEventListener('click', () => { setView("projects"); $("#project-form").classList.remove("hidden"); }));
  renderMetrics();
}

function renderDeployments() {
  const target = $("#deployment-list");
  if (!state.deployments.length) {
    target.innerHTML = `<div class="empty-state"><p class="eyebrow">Empty State</p><h3>No deployment history yet</h3><p class="muted">Deployments will appear after a project runs through the worker and Deploy Pipeline.</p></div>`;
    renderMetrics();
    return;
  }
  target.innerHTML = state.deployments.map((deployment) => `<div class="list-item">
    <header><strong>${escapeHtml(deployment.id || deployment.deployment_id)}</strong><span class="pill ${deployment.status === "completed" ? "success" : deployment.status === "failed" ? "danger" : "warning"}">${escapeHtml(deployment.status || "queued")}</span></header>
    <p>${escapeHtml(deployment.deployment_url || deployment.failure_summary || "Deployment is awaiting pipeline result.")}</p>
  </div>`).join("");
  renderMetrics();
}

function accountCard(provider) {
  const account = state.accounts.find((item) => item.provider === provider);
  const connected = account?.connected || account?.status === "connected";
  const label = provider === "github" ? "GitHub" : "Cloudflare";
  const accountName = escapeHtml(account?.account_name || account?.provider_account_name || "account");
  const manageUrl = provider === "github" ? "https://github.com/settings/installations" : "https://dash.cloudflare.com";
  const manageLabel = provider === "github" ? "Manage on GitHub" : "Manage on Cloudflare";
  const connectLabel = !connected && account ? "Reconnect" : "Connect";
  const statusCopy = connected ? `Status: Connected · ${accountName}` : "Status: Not connected";

  const actions = connected
    ? `<div class="form-actions account-actions">
        <button class="danger-button" type="button" data-disconnect-provider="${provider}">Disconnect</button>
        <a class="provider-manage-link" href="${manageUrl}" target="_blank" rel="noreferrer">${manageLabel}</a>
      </div>`
    : `<div class="form-actions account-actions">
        <a class="primary-button" href="${API}/connected-accounts/${provider}/connect">${connectLabel}</a>
      </div>`;

  return `<article class="account-card" id="${provider}-account-card">
    <strong>${label}</strong>
    <span>${statusCopy}</span>
    ${actions}
  </article>`;
}

function renderAccounts() {
  const html = ["github", "cloudflare"].map(accountCard).join("");
  $("#connected-account-grid").innerHTML = html;
  $("#dashboard-account-grid").innerHTML = html;
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


async function requestDeploy(projectId) {
  if (!projectId) return;

  const project = state.projects.find((item) => item.id === projectId);
  if (project && !isProjectDeployReady(project)) {
    showSystemAlert("DEPLOYMENT_PROJECT_NOT_READY", "warning");
    return;
  }

  try {
    await fetchJson(`/projects/${encodeURIComponent(projectId)}/deploy`, { method: "POST", body: JSON.stringify({}) });
    showSystemAlert("Deployment queued. Worker events will appear in deployment history.", "success");
    await loadDeployments();
  } catch (error) {
    showSystemAlert(error, "warning");
  }
}

function bindUi() {
  $$('[data-view]').forEach((link) => link.addEventListener("click", (event) => { event.preventDefault(); setView(link.dataset.view); }));
  $$('[data-view-trigger]').forEach((button) => button.addEventListener("click", () => setView(button.dataset.viewTrigger)));
  $("#new-project-button").addEventListener("click", () => { setView("projects"); $("#project-form").classList.remove("hidden"); });
  $("#open-project-form").addEventListener("click", () => $("#project-form").classList.remove("hidden"));
  $("#cancel-project-form").addEventListener("click", () => $("#project-form").classList.add("hidden"));
  $("#project-form").addEventListener("submit", createProject);
  $("#refresh-deployments").addEventListener("click", loadDeployments);
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
