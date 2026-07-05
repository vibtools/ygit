const API = "/api/v1";
const state = {
  projects: [],
  deployments: [],
  accounts: [],
  status: null,
};

const $ = (selector) => document.querySelector(selector);
const $$ = (selector) => Array.from(document.querySelectorAll(selector));

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

function setView(view) {
  const title = view.split("-").map((part) => part.charAt(0).toUpperCase() + part.slice(1)).join(" ");
  $("#view-title").textContent = title;
  $$("[data-view]").forEach((link) => link.classList.toggle("active", link.dataset.view === view));
  $$("[data-view-panel]").forEach((panel) => {
    const names = panel.dataset.viewPanel.split(" ");
    const show = names.includes(view) || (view === "dashboard" && panel.id === "dashboard-view");
    panel.classList.toggle("hidden", !show && !["dashboard-view", "metric-grid"].includes(panel.id));
  });
  const previewViews = new Set(["ai", "marketplace", "plugins", "teams", "analytics"]);
  if (previewViews.has(view)) {
    $("#preview-title").textContent = `${title} — Coming Soon`;
    $("#preview-copy").textContent = `${title} is a future feature and is intentionally outside this MVP implementation scope.`;
  }
  location.hash = view;
}

function renderProjects() {
  const target = $("#project-list");
  if (!state.projects.length) {
    target.innerHTML = `<div class="list-item"><header><strong>No projects yet</strong><span class="pill">empty</span></header><p>Create a project by pasting a GitHub repository URL.</p></div>`;
    $("#metric-projects").textContent = "0";
    return;
  }
  $("#metric-projects").textContent = String(state.projects.length);
  target.innerHTML = state.projects.map((project) => `
    <div class="list-item">
      <header><strong>${escapeHtml(project.name || project.slug || project.id)}</strong><span class="pill">${escapeHtml(project.status || "draft")}</span></header>
      <p>${escapeHtml(project.slug || "no-slug")} · ${escapeHtml(project.repository_url || project.repository_id || "repository pending")}</p>
      <div class="form-actions">
        <button class="secondary-button" data-deploy-project="${escapeHtml(project.id)}" type="button">Deploy</button>
        <button class="secondary-button" data-project-id="${escapeHtml(project.id)}" type="button">Open</button>
      </div>
    </div>
  `).join("");
  $$('[data-deploy-project]').forEach((button) => button.addEventListener('click', () => requestDeploy(button.dataset.deployProject)));
}

function renderDeployments() {
  const target = $("#deployment-list");
  if (!state.deployments.length) {
    target.innerHTML = `<div class="list-item"><header><strong>No deployment history loaded</strong><span class="pill">polling ready</span></header><p>Deployments will appear after a project deploys through the worker and Deploy Pipeline.</p></div>`;
    $("#metric-deployments").textContent = "0";
    return;
  }
  $("#metric-deployments").textContent = String(state.deployments.length);
  target.innerHTML = state.deployments.map((deployment) => `
    <div class="list-item">
      <header><strong>${escapeHtml(deployment.id || deployment.deployment_id)}</strong><span class="pill ${deployment.status === "completed" ? "success" : deployment.status === "failed" ? "danger" : "warning"}">${escapeHtml(deployment.status || "queued")}</span></header>
      <p>${escapeHtml(deployment.deployment_url || deployment.failure_summary || "Deployment is awaiting pipeline result.")}</p>
    </div>
  `).join("");
}

function renderAccounts() {
  const target = $("#connected-account-grid");
  const providers = ["github", "cloudflare"];
  target.innerHTML = providers.map((provider) => {
    const account = state.accounts.find((item) => item.provider === provider);
    const connected = account?.connected || account?.status === "connected";
    return `
      <div>
        <strong>${provider === "github" ? "GitHub" : "Cloudflare"}</strong>
        <span>${connected ? `Connected as ${escapeHtml(account.account_name || account.provider_account_name || "account")}` : "Not connected"}</span>
        <div class="form-actions" style="margin-top: 12px;">
          <a class="${connected ? "secondary-button" : "primary-button"}" href="${API}/connected-accounts/${provider}/connect">${connected ? "Reconnect" : "Connect"}</a>
        </div>
      </div>`;
  }).join("");
}

async function loadStatus() {
  try {
    const data = await fetchJson("/platform/status");
    state.status = data;
    $("#metric-worker").textContent = data.worker_status || "ok";
    $("#metric-queue").textContent = data.queue_status || "ok";
    const alert = $("#system-alert");
    if (data.maintenance) {
      alert.textContent = data.message || "YGIT is currently in maintenance mode.";
      alert.classList.remove("hidden");
    } else {
      alert.classList.add("hidden");
    }
  } catch (error) {
    $("#metric-worker").textContent = "auth";
    $("#metric-queue").textContent = "auth";
  }
}

async function loadProjects() {
  try {
    const data = await fetchJson("/projects?page=1&page_size=20");
    state.projects = data.items || data.projects || [];
  } catch (error) {
    state.projects = [];
  }
  renderProjects();
}

async function loadAccounts() {
  try {
    const data = await fetchJson("/connected-accounts");
    state.accounts = data.accounts || [];
  } catch (error) {
    state.accounts = [];
  }
  renderAccounts();
}

async function loadDeployments() {
  const deployments = [];
  for (const project of state.projects.slice(0, 5)) {
    try {
      const data = await fetchJson(`/projects/${encodeURIComponent(project.id)}/deployments?page=1&page_size=5`);
      deployments.push(...(data.items || data.deployments || []));
    } catch (_) {
      // Project-level deployment lists require auth and live DB; ignore in static dashboard shell.
    }
  }
  state.deployments = deployments;
  renderDeployments();
}

async function createProject(event) {
  event.preventDefault();
  const status = $("#project-form-status");
  status.textContent = "Creating project…";
  const payload = {
    name: $("#project-name").value,
    repository_url: $("#repository-url").value,
    slug: $("#project-slug").value,
  };
  try {
    await fetchJson("/projects", { method: "POST", body: JSON.stringify(payload) });
    status.textContent = "Project created.";
    $("#project-form").reset();
    await loadProjects();
  } catch (error) {
    status.textContent = error.message;
  }
}

async function requestDeploy(projectId) {
  if (!projectId) return;
  try {
    await fetchJson(`/projects/${encodeURIComponent(projectId)}/deploy`, { method: "POST", body: JSON.stringify({}) });
    await loadDeployments();
  } catch (error) {
    const alert = $("#system-alert");
    alert.textContent = error.message;
    alert.classList.remove("hidden");
  }
}

function bindUi() {
  $$("[data-view]").forEach((link) => link.addEventListener("click", (event) => {
    event.preventDefault();
    setView(link.dataset.view);
  }));
  $$("[data-view-trigger]").forEach((button) => button.addEventListener("click", () => setView(button.dataset.viewTrigger)));
  $("#quick-create").addEventListener("click", () => { setView("projects"); $("#project-form").classList.remove("hidden"); });
  $("#open-project-form").addEventListener("click", () => $("#project-form").classList.remove("hidden"));
  $("#cancel-project-form").addEventListener("click", () => $("#project-form").classList.add("hidden"));
  $("#project-form").addEventListener("submit", createProject);
  $("#refresh-deployments").addEventListener("click", loadDeployments);
}

async function boot() {
  bindUi();
  const initialView = (location.hash || "#dashboard").replace("#", "");
  setView(initialView || "dashboard");
  await loadStatus();
  await loadProjects();
  await loadAccounts();
  await loadDeployments();
}

document.addEventListener("DOMContentLoaded", boot);
