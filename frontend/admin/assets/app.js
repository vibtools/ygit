const API = "/api/v1";
const state = { overview: null, queue: null, system: null, deployments: [], users: [], auditLogs: [], settings: null };

const $ = (selector) => document.querySelector(selector);
const $$ = (selector) => Array.from(document.querySelectorAll(selector));

async function fetchJson(path) {
  const response = await fetch(`${API}${path}`, { credentials: "include", headers: { "Content-Type": "application/json" } });
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

function titleFor(view) {
  return view.split("-").map((part) => part.charAt(0).toUpperCase() + part.slice(1)).join(" ");
}

function setView(view) {
  $("#view-title").textContent = titleFor(view);
  $$('[data-view]').forEach((link) => link.classList.toggle('active', link.dataset.view === view));
  $$('[data-view-panel]').forEach((panel) => {
    const names = panel.dataset.viewPanel.split(' ');
    panel.classList.toggle('hidden', !names.includes(view));
  });
  location.hash = view;
}

function showAuthMessage(error) {
  const alert = $('#auth-alert');
  alert.textContent = `${error.message} Use an account with ygit_admin, ygit_support, or ygit_readonly role.`;
  alert.classList.remove('hidden');
}

function renderOverview() {
  const healthGrid = $('#health-grid');
  const overview = state.overview;
  if (!overview) return;
  $('#metric-api').textContent = overview.health.find((h) => h.name === 'api')?.status || '—';
  $('#metric-queue').textContent = overview.metrics.find((m) => m.key === 'queue')?.value || '—';
  $('#metric-worker').textContent = overview.health.find((h) => h.name === 'worker')?.status || '—';
  $('#metric-audit').textContent = 'immutable';
  healthGrid.innerHTML = overview.health.map((item) => `
    <div class="status-card">
      <strong>${escapeHtml(item.name)}</strong>
      <span class="pill ${escapeHtml(item.status)}">${escapeHtml(item.status)}</span>
      <p>${escapeHtml(item.description)}</p>
    </div>
  `).join('');
}

function renderQueue() {
  const target = $('#queue-list');
  if (!state.queue) return;
  target.innerHTML = state.queue.queues.map((item) => `
    <div class="list-item">
      <header><strong>${escapeHtml(item.label)}</strong><span class="pill ${escapeHtml(item.status)}">${escapeHtml(item.status)}</span></header>
      <p>${escapeHtml(item.description)}</p>
    </div>
  `).join('') + `<div class="list-item"><header><strong>Retry Policy</strong><span class="pill configured">configured</span></header><p>Max attempts: ${escapeHtml(state.queue.retry_policy.max_attempts)} · Owner: ${escapeHtml(state.queue.retry_policy.owner)}</p></div>`;
}

function renderSystem() {
  const target = $('#system-grid');
  if (!state.system) return;
  const providerChecks = state.system.provider_checks || {};
  const cards = [
    ['API', state.system.api],
    ['Database', state.system.database],
    ['Redis', state.system.redis],
    ['Worker', state.system.worker],
    ['Queue', state.system.queue],
    ['GitHub Provider', providerChecks.github],
    ['Cloudflare Provider', providerChecks.cloudflare],
  ];
  target.innerHTML = cards.map(([label, status]) => `
    <div class="monitor-card"><strong>${escapeHtml(label)}</strong><span class="pill ${escapeHtml(status)}">${escapeHtml(status || 'unknown')}</span></div>
  `).join('');
}

function renderList(targetSelector, items, emptyTitle) {
  const target = $(targetSelector);
  if (!items.length) {
    target.innerHTML = `<div class="list-item"><header><strong>${escapeHtml(emptyTitle)}</strong><span class="pill">empty</span></header><p>No live rows loaded in this runtime.</p></div>`;
    return;
  }
  target.innerHTML = items.map((item) => `
    <div class="list-item">
      <header><strong>${escapeHtml(item.id || item.event_name || item.email || item.source || 'record')}</strong><span class="pill ${escapeHtml(item.status || (item.immutable ? 'ok' : ''))}">${escapeHtml(item.status || (item.immutable ? 'immutable' : 'summary'))}</span></header>
      <p>${escapeHtml(item.message || item.target_type || 'Safe operational summary.')}</p>
    </div>
  `).join('');
}

function renderSettings() {
  const target = $('#settings-list');
  if (!state.settings) return;
  const entries = [
    ['Maintenance banner', state.settings.maintenance_banner ? 'enabled' : 'disabled'],
    ['Registration', state.settings.registration_enabled ? 'enabled' : 'disabled'],
    ['Repository providers', state.settings.allowed_repository_providers.join(', ')],
    ['Deployment providers', state.settings.allowed_deployment_providers.join(', ')],
    ['Templates Beta', state.settings.templates_beta_enabled ? 'enabled' : 'disabled'],
    ['Sensitive config', state.settings.sensitive_config_location],
    ['MVP mutation', state.settings.mutable_in_mvp ? 'enabled' : 'read-only'],
  ];
  target.innerHTML = entries.map(([key, value]) => `<span>${escapeHtml(key)}</span><strong>${escapeHtml(value)}</strong>`).join('');
}

async function loadOverview() {
  try {
    const data = await fetchJson('/admin/overview');
    state.overview = data.overview;
    renderOverview();
  } catch (error) { showAuthMessage(error); }
}
async function loadQueue() {
  try { const data = await fetchJson('/admin/queue/status'); state.queue = data.queue; renderQueue(); } catch (error) { showAuthMessage(error); }
}
async function loadSystem() {
  try { const data = await fetchJson('/admin/system-monitoring'); state.system = data.system; renderSystem(); } catch (error) { showAuthMessage(error); }
}
async function loadDeployments() {
  try { const data = await fetchJson('/admin/deployments'); state.deployments = data.items || []; renderList('#deployment-list', state.deployments, 'No deployments loaded'); } catch (error) { showAuthMessage(error); }
}
async function loadUsers() {
  try { const data = await fetchJson('/admin/users'); state.users = data.items || []; renderList('#user-list', state.users, 'No users loaded'); } catch (error) { showAuthMessage(error); }
}
async function loadAuditLogs() {
  try { const data = await fetchJson('/admin/audit-logs'); state.auditLogs = data.items || []; renderList('#audit-list', state.auditLogs, 'No audit logs loaded'); } catch (error) { showAuthMessage(error); }
}
async function loadSettings() {
  try { const data = await fetchJson('/admin/settings'); state.settings = data.settings; renderSettings(); } catch (error) { showAuthMessage(error); }
}

function bindUi() {
  $$('[data-view]').forEach((link) => link.addEventListener('click', (event) => { event.preventDefault(); setView(link.dataset.view); }));
  $('#refresh-health').addEventListener('click', loadOverview);
  $('#refresh-queue').addEventListener('click', loadQueue);
  $('#refresh-system').addEventListener('click', loadSystem);
  $('#refresh-deployments').addEventListener('click', loadDeployments);
  $('#refresh-users').addEventListener('click', loadUsers);
  $('#refresh-audit').addEventListener('click', loadAuditLogs);
  $('#refresh-settings').addEventListener('click', loadSettings);
}

async function boot() {
  bindUi();
  setView((location.hash || '#overview').replace('#', '') || 'overview');
  await loadOverview();
  await loadQueue();
  await loadSystem();
  await loadDeployments();
  await loadUsers();
  await loadAuditLogs();
  await loadSettings();
}

document.addEventListener('DOMContentLoaded', boot);
