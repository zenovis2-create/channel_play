let state = null;

const $ = (id) => document.getElementById(id);

async function api(path, options = {}) {
  const response = await fetch(path, options);
  const data = await response.json();
  if (!response.ok || data.ok === false) {
    throw new Error(data.error || `Request failed: ${response.status}`);
  }
  return data;
}

async function loadState() {
  state = await api('/api/state');
  render();
}

function render() {
  $('subtitle').textContent = `${state.root} · ${state.git.head}`;
  renderStats();
  renderAgents();
  renderTasks();
  renderFeedback();
  renderAssets();
  renderRuns();
  $('briefPreview').textContent = state.memory.currentBrief || state.memory.currentContext || 'No memory brief generated.';
}

function renderStats() {
  const gdx = state.company.state.gdx1 || {};
  const stats = [
    ['Git', state.git.head],
    ['Dirty', String(state.git.dirty.length)],
    ['Session', state.company.state.active_session || 'none'],
    ['Open Tasks', String(state.company.openTasks.length)],
    ['Locks', String(state.company.locks.length)],
    ['gdx1', `${gdx.network || 'unknown'} / ${gdx.ssh || 'unknown'}`],
  ];
  $('stats').innerHTML = stats.map(([k, v]) => `<div class="stat"><b>${esc(k)}</b><span>${esc(v)}</span></div>`).join('');
}

function renderAgents() {
  $('agentCount').textContent = `${state.company.agents.length} agents`;
  $('agentsList').innerHTML = state.company.agents.map(agent => item(
    agent.id,
    agent.profile,
    agent.writes_by_default ? 'writer' : 'role'
  )).join('') || empty('No agents registered.');
}

function renderTasks() {
  $('tasksList').innerHTML = state.company.tasks.map(task => item(
    `${task.id} · ${task.status}`,
    task.request || '',
    `agent ${task.assigned_agent || task.suggested_agent || 'unassigned'}`
  )).join('') || empty('No tasks.');
  $('locksList').innerHTML = state.company.locks.map(lock => item(
    lock.path,
    `owner ${lock.owner}`,
    `task ${lock.task_id}`
  )).join('') || empty('No locks.');
}

function renderFeedback() {
  $('feedbackList').innerHTML = state.feedback.map(feedback => item(
    `${feedback.id} · ${feedback.status}`,
    feedback.path,
    `scene ${feedback.scene}`
  )).join('') || empty('No feedback records.');
}

function renderAssets() {
  $('assetList').innerHTML = state.assets.map(asset => item(
    `${asset.id} · ${asset.status}`,
    asset.brief || '',
    asset.scene_screenshot ? `screenshot ${asset.scene_screenshot}` : `source ${asset.source_license || 'TBD'}`
  )).join('') || empty('No assets.');
}

function renderRuns() {
  $('runsList').innerHTML = state.runs.map(run => item(run.name, run.file || run.path, run.path)).join('') || empty('No runs.');
}

function item(title, body, meta) {
  return `<div class="item"><strong>${esc(title || '')}</strong><span>${esc(body || '')}</span><small>${esc(meta || '')}</small></div>`;
}

function empty(text) {
  return `<div class="item"><span>${esc(text)}</span></div>`;
}

async function runCommand(command, payload = {}) {
  $('console').textContent = `Running ${command}...`;
  try {
    const result = await api('/api/command', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ command, payload }),
    });
    $('console').textContent = [
      `$ ${result.command}`,
      `exit ${result.exit}`,
      '',
      result.stdout || '',
      result.stderr ? `\n[stderr]\n${result.stderr}` : '',
    ].join('\n').trim();
    await loadState();
  } catch (error) {
    $('console').textContent = `Error: ${error.message}`;
  }
}

async function loadFile() {
  const path = $('filePath').value.trim();
  if (!path) return;
  try {
    const data = await api(`/api/file?path=${encodeURIComponent(path)}`);
    $('filePreview').textContent = data.content;
  } catch (error) {
    $('filePreview').textContent = `Error: ${error.message}`;
  }
}

function bind() {
  document.querySelectorAll('[data-command]').forEach(button => {
    button.addEventListener('click', () => runCommand(button.dataset.command));
  });
  $('reload').addEventListener('click', loadState);
  $('startSession').addEventListener('click', () => runCommand('company.session.start', { goal: $('sessionGoal').value }));
  $('planTask').addEventListener('click', () => runCommand('company.plan', { request: $('planRequest').value }));
  $('processFeedback').addEventListener('click', () => runCommand('feedback.process', { path: $('feedbackPath').value }));
  $('createAsset').addEventListener('click', () => runCommand('asset.new', { assetId: $('assetId').value }));
  $('acceptAsset').addEventListener('click', () => runCommand('asset.status', { assetId: $('assetId').value, status: 'accepted' }));
  $('loadFile').addEventListener('click', loadFile);
}

function esc(value) {
  return String(value)
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
    .replaceAll("'", '&#039;');
}

bind();
loadState().catch(error => {
  $('console').textContent = `Load failed: ${error.message}`;
});
