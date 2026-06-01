const $ = (selector) => document.querySelector(selector);

let state = null;

const statusText = {
  assigned: "배정됨",
  planned: "계획됨",
  needs_review: "검토 필요",
  needs_evidence: "증거 필요",
  closed: "완료",
  closed_blocked: "차단 종료",
  accepted: "승인됨",
  rejected: "반려됨",
  pending: "대기",
  ok: "정상",
  none: "없음",
};

const commandText = {
  "company.brief": "브리프 갱신",
  "company.session.end": "세션 종료",
  "company.plan": "작업 주문 생성",
  "unity.check": "Unity 점검",
  "capture.screen": "화면 캡처",
  "feedback.new": "새 피드백",
  "feedback.process": "피드백 처리",
  "asset.new": "에셋 브리프 생성",
  "asset.status": "에셋 상태 변경",
  "gdx.probe": "gdx1 연결 확인",
  "gdx.sync": "gdx1 동기화",
  "gdx.runServer": "gdx1 서버 실행",
  "gdx.runBots": "gdx1 봇 실행",
  "gdx.collectLogs": "gdx1 로그 수집",
};

async function api(path, options = {}) {
  const response = await fetch(path, options);
  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || `${response.status} ${response.statusText}`);
  }
  return response.json();
}

async function loadState() {
  state = await api("/api/state");
  render();
}

function render() {
  const updatedAt = formatDate(state.company?.state?.updated_at);
  $("#subtitle").textContent = `${state.project} · ${state.root}`;
  $("#stateStamp").textContent = updatedAt ? `갱신 ${updatedAt}` : "갱신 시간 없음";
  $("#briefPreview").textContent = state.memory?.currentBrief || state.memory?.currentContext || "아직 생성된 브리프가 없습니다.";
  renderRecommendation();
  renderStats();
  renderSession();
  renderAgents();
  renderTasks();
  renderFeedback();
  renderAssets();
  renderRuns();
}

function renderRecommendation() {
  const activeSession = state.company?.state?.active_session;
  const openTasks = state.company?.openTasks || [];
  const gdx = state.company?.state?.gdx1 || {};
  const sshOk = gdx.ssh === "ok";

  let message = "새 제작 세션을 시작하고, 목표를 작업 주문으로 나누세요.";
  let tone = "good";

  if (activeSession) {
    message = `진행 중인 세션 ${activeSession}이 있습니다. 작업 보고와 검증 증거를 먼저 확인하세요.`;
    tone = "warn";
  } else if (openTasks.length > 0) {
    message = `열린 작업 ${openTasks.length}개가 남아 있습니다. 담당 에이전트, 증거, 검증 상태를 먼저 정리하세요.`;
    tone = "warn";
  } else if (!sshOk) {
    message = "gdx1 SSH 상태가 정상으로 확인되지 않았습니다. 연결 확인 후 동기화를 진행하세요.";
    tone = "bad";
  }

  $("#nextAction").textContent = message;
  $("#stateStamp").className = `tag ${tone}`;
}

function renderStats() {
  const dirty = dirtyCount(state.git?.dirty);
  const companyState = state.company?.state || {};
  const openTasks = state.company?.openTasks?.length || 0;
  const locks = state.company?.locks?.length || 0;
  const gdx = companyState.gdx1 || {};
  const activeSession = companyState.active_session || "없음";
  const gitHead = state.git?.head || "알 수 없음";

  const stats = [
    ["Git", gitHead],
    ["변경 파일", dirty === 0 ? "깨끗함" : `${dirty}개`],
    ["세션", activeSession],
    ["열린 작업", `${openTasks}개`],
    ["파일 잠금", `${locks}개`],
    ["gdx1", gdx.ssh === "ok" ? "SSH 정상" : translate(gdx.ssh || "unknown")],
  ];

  $("#stats").innerHTML = stats.map(([label, value]) => `
    <div class="stat">
      <span>${esc(label)}</span>
      <strong>${esc(value)}</strong>
    </div>
  `).join("");

  $("#gdxSummary").textContent = gdx.ssh === "ok" ? "SSH 정상" : translate(gdx.ssh || "미확인");
}

function renderSession() {
  const activeSession = state.company?.state?.active_session;
  $("#sessionState").textContent = activeSession ? "진행 중" : "대기 중";
}

function renderAgents() {
  const agents = state.company?.agents || [];
  $("#agentCount").textContent = `${agents.length}명`;
  $("#agentsList").innerHTML = agents.map((agent) => item(
    agent.id,
    agent.profile || "프로필 없음",
    agent.writes_by_default ? "기본 쓰기 권한" : "요청 시 쓰기 권한",
    agent.writes_by_default ? "write" : "review",
    agent.writes_by_default ? "warn" : ""
  )).join("") || empty("등록된 에이전트가 없습니다.");
}

function renderTasks() {
  const tasks = state.company?.tasks || [];
  const openTasks = state.company?.openTasks || [];
  $("#taskCount").textContent = `열림 ${openTasks.length} / 전체 ${tasks.length}`;

  const ordered = [...tasks].sort((a, b) => taskWeight(a) - taskWeight(b));
  $("#tasksList").innerHTML = ordered.slice(0, 10).map((task) => {
    const agent = task.assigned_agent || task.suggested_agent || "미배정";
    const evidence = task.evidence?.length || 0;
    const meta = `${task.id} · 담당 ${agent} · 증거 ${evidence}개`;
    const tone = task.status === "closed" ? "good" : task.status === "closed_blocked" ? "bad" : "warn";
    return item(task.request || task.id, task.required_evidence || "필요 증거 없음", meta, translate(task.status), tone);
  }).join("") || empty("아직 생성된 작업이 없습니다.");

  const locks = state.company?.locks || [];
  $("#locksList").innerHTML = locks.map((lock) => item(
    lock.path,
    lock.owner || "소유자 미확인",
    lock.task_id || "작업 없음",
    "lock",
    "warn"
  )).join("") || empty("현재 잠긴 파일이 없습니다.");
}

function renderFeedback() {
  const feedback = state.feedback || [];
  $("#feedbackList").innerHTML = feedback.map((note) => item(
    note.id,
    note.path,
    `${translate(note.status || "pending")} · 장면 ${note.scene || "미지정"}`,
    note.status ? translate(note.status) : "대기",
    note.status === "closed" ? "good" : "warn"
  )).join("") || empty("등록된 피드백이 없습니다.");
}

function renderAssets() {
  const assets = state.assets || [];
  $("#assetList").innerHTML = assets.map((asset) => item(
    asset.id,
    asset.brief || "브리프 없음",
    `라이선스 ${asset.source_license || "미확인"} · ${formatDate(asset.updated_at || asset.created_at) || "날짜 없음"}`,
    translate(asset.status || "pending"),
    asset.status === "accepted" ? "good" : "warn"
  )).join("") || empty("등록된 에셋이 없습니다.");
}

function renderRuns() {
  const runs = state.runs || [];
  $("#runsList").innerHTML = runs.map((run) => item(
    run.name,
    run.file || run.path,
    "검증 자료",
    "run",
    ""
  )).join("") || empty("아직 실행 증거가 없습니다.");
}

function item(title, body, meta, badge = "", tone = "") {
  const badgeHtml = badge ? `<span class="pill ${esc(tone)}">${esc(badge)}</span>` : "";
  return `
    <div class="list-item">
      <div class="item-main">
        <strong>${esc(title || "제목 없음")}</strong>
        <span>${esc(body || "")}</span>
        <small>${esc(meta || "")}</small>
      </div>
      ${badgeHtml}
    </div>
  `;
}

function empty(message) {
  return `<div class="list-item empty">${esc(message)}</div>`;
}

async function runCommand(command, payload = {}) {
  const label = commandText[command] || command;
  $("#console").textContent = `실행 중: ${label}`;

  try {
    const result = await api("/api/command", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ command, payload }),
    });
    const commandLine = Array.isArray(result.command) ? result.command.join(" ") : "";
    $("#console").textContent = [
      commandLine ? `$ ${commandLine}` : label,
      result.stdout || "(표준 출력 없음)",
      result.stderr ? `\n[stderr]\n${result.stderr}` : "",
    ].join("\n").trim();
    await loadState();
  } catch (error) {
    $("#console").textContent = `오류: ${error.message}`;
  }
}

async function loadFile() {
  const path = $("#filePath").value.trim();
  if (!path) {
    $("#filePreview").textContent = "불러올 파일 경로를 입력하세요.";
    return;
  }

  $("#filePreview").textContent = "파일을 불러오는 중입니다.";
  try {
    const data = await api(`/api/file?path=${encodeURIComponent(path)}`);
    $("#filePreview").textContent = data.content || "(빈 파일)";
  } catch (error) {
    $("#filePreview").textContent = `오류: ${error.message}`;
  }
}

function bind() {
  document.querySelectorAll("[data-command]").forEach((button) => {
    button.addEventListener("click", () => runCommand(button.dataset.command));
  });

  $("#reload").addEventListener("click", loadState);
  $("#startSessionShortcut").addEventListener("click", () => $("#sessionGoal").focus());
  $("#startSession").addEventListener("click", () => {
    const goal = $("#sessionGoal").value.trim();
    if (!goal) {
      $("#console").textContent = "세션 목표를 입력하세요.";
      $("#sessionGoal").focus();
      return;
    }
    runCommand("company.session.start", { goal });
  });
  $("#planTask").addEventListener("click", () => {
    const request = $("#planRequest").value.trim();
    if (!request) {
      $("#console").textContent = "작업 요청을 입력하세요.";
      $("#planRequest").focus();
      return;
    }
    runCommand("company.plan", { request });
  });
  $("#processFeedback").addEventListener("click", () => {
    const path = $("#feedbackPath").value.trim();
    if (!path) {
      $("#console").textContent = "피드백 파일 경로를 입력하세요.";
      $("#feedbackPath").focus();
      return;
    }
    runCommand("feedback.process", { path });
  });
  $("#createAsset").addEventListener("click", () => {
    const assetId = $("#assetId").value.trim();
    if (!assetId) {
      $("#console").textContent = "에셋 ID를 입력하세요.";
      $("#assetId").focus();
      return;
    }
    runCommand("asset.new", { assetId });
  });
  $("#acceptAsset").addEventListener("click", () => {
    const assetId = $("#assetId").value.trim();
    if (!assetId) {
      $("#console").textContent = "에셋 ID를 입력하세요.";
      $("#assetId").focus();
      return;
    }
    runCommand("asset.status", { assetId, status: "accepted" });
  });
  $("#loadFile").addEventListener("click", loadFile);
}

function taskWeight(task) {
  if (task.status === "closed") return 3;
  if (task.status === "closed_blocked") return 4;
  return 1;
}

function dirtyCount(value) {
  if (Array.isArray(value)) return value.length;
  const text = String(value || "").trim();
  return text ? text.split(/\r?\n/).length : 0;
}

function translate(value) {
  return statusText[value] || value || "미확인";
}

function formatDate(value) {
  if (!value) return "";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return new Intl.DateTimeFormat("ko-KR", {
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  }).format(date);
}

function esc(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

bind();
loadState().catch((error) => {
  $("#subtitle").textContent = "상태를 불러오지 못했습니다.";
  $("#console").textContent = `오류: ${error.message}`;
});
