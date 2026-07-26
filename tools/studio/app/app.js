const $ = (selector) => document.querySelector(selector);

let state = null;
let liveActivity = null;
let recentActivity = null;
let selectedTaskId = "";
let selectedArtifactPath = "";
let previewRequestPath = "";
let activeJobId = "";
let jobPollTimer = null;
let executionToken = "";
let executionTokenHeader = "X-Channel-Play-Token";
let searchState = null;
let activeStudioView = localStorage.getItem("channelPlayStudioView") || "focus";

const ORCHESTRATOR_MIN_VISIBLE_MS = 1200;
const studioViews = {
  focus: "작업",
  board: "팀",
  library: "기억",
  system: "시스템",
};

const statusText = {
  assigned: "배정됨",
  planned: "계획됨",
  needs_scope: "범위 필요",
  needs_review: "검토 필요",
  needs_evidence: "완료 대기",
  evidence_attached: "증거 연결됨",
  blocked: "차단됨",
  closed: "완료",
  closed_blocked: "차단 종료",
  accepted: "승인됨",
  rejected: "반려됨",
  dry_run: "드라이런",
  reviewed: "리뷰 완료",
  failed: "실패",
  timeout: "시간 초과",
  running: "진행 중",
  queued: "대기열",
  succeeded: "완료",
  cancelled: "취소됨",
  simworld_start_blocked: "시작 차단",
  not_started: "시작 안 함",
  passed: "통과",
  proof_refresh_passed: "증거 갱신 통과",
  proof_refresh_collected: "증거 수집됨",
  proof_refresh_partial: "부분 통과",
  proof_refresh_incomplete: "증거 부족",
  proof_refresh_failed: "갱신 실패",
  available: "사용 가능",
  missing: "없음",
  disabled: "비활성",
  configured_but_failed: "설정 오류",
  import_failed: "임포트 실패",
  auth_missing: "인증 필요",
  needs_config: "설정 필요",
  needs_simworld_install: "SimWorld 설치 필요",
  pending: "대기",
  ok: "정상",
  none: "없음",
  ready: "제작 가능",
  forge_ready: "Forge 준비됨",
  ready_for_image_generation: "이미지 생성 가능",
  waiting_for_gpt_image: "GPT Image 대기",
  waiting_for_concept_image: "콘셉트 이미지 대기",
  waiting_for_model_runtime: "모델 런타임 대기",
  waiting_for_mesh: "메시 대기",
  waiting_for_cubepart_output: "CubePart 출력 대기",
  waiting_for_clean_fbx: "정리된 FBX 대기",
  waiting_for_prefab: "Unity 프리팹 대기",
  waiting_for_scene_evidence: "장면 증거 대기",
  needs_work: "점검 필요",
  server_blocked: "서버 소크 보류",
  needs_capture: "캡처 필요",
  needs_asset: "에셋 필요",
  worker_blocked: "워커 대기",
  handoff_ready: "핸드오프 준비됨",
  empty: "비어 있음",
  perfect: "완벽",
  active: "진행 중",
  complete: "완료",
};

const commandText = {
  "orchestrator.run": "오케스트레이터 자동 진행",
  "company.brief": "브리프 갱신",
  "company.session.end": "세션 종료",
  "company.plan": "작업 주문 생성",
  "company.workers.probe": "워커 전체 점검",
  "company.models.refresh": "모델 추천 갱신",
  "company.review": "리뷰 체크포인트",
  "company.verify": "완료 처리",
  "company.advance": "작업 자동 진행",
  "company.goal.set": "목표 설정",
  "company.goal.run": "Goal Engine 실행",
  "company.goal.status": "Goal Engine 상태",
  "agent.adapters": "AI 어댑터 확인",
  "agent.run": "AI 에이전트 실행",
  "agent.review": "AI 리뷰 실행",
  "unity.check": "Unity 점검",
  "unity.compile": "Unity 컴파일",
  "unity.playtest": "플레이테스트 스모크",
  "unity.simCheck": "Unity 시뮬레이션 점검",
  "unity.semanticCheck": "Unity 에셋 의미 검증",
  "unity.agentPlaytestPyramid": "피라미드 에이전트 플레이테스트",
  "unity.simReviewLatest": "시뮬레이션 리뷰",
  "unity.simReplayLatest": "시뮬레이션 리플레이",
  "unity.simCompare": "시뮬레이션 비교",
  "unity.build.mac": "Mac 개발 빌드",
  "unity.build.linuxServer": "Linux 서버 빌드",
  "game.status": "게임 제작 상태",
  "game.productionCheck": "게임 제작 전체 점검",
  "game.feedbackLoop": "플레이-캡처-피드백 루프",
  "game.serverHandoff": "x86 서버 핸드오프",
  "simworld.probe": "gdx1 SimWorld 점검",
  "simworld.doctor": "gdx1 SimWorld Doctor",
  "simworld.installBaseDryRun": "SimWorld Base 설치 확인",
  "simworld.routePlan": "SimWorld 경로 계획",
  "simworld.startServer": "SimWorld UE 시작",
  "simworld.workerGuide": "x86 워커 설정 가이드",
  "simAgent.packet": "외부 에이전트 패킷",
  "simAgent.runCodex": "Codex 브리지 실행",
  "simAgent.runOpenClaw": "OpenClaw 브리지 실행",
  "simAgent.liveCheckAll": "외부 AI Live 검증",
  "simAcceptance.check": "최종 검수",
  "simAcceptance.proofRefresh": "Unity 증거 갱신",
  "simAcceptance.handoff": "인수인계 패키지",
  "asset.semanticPack": "에셋 의미 팩 생성",
  "capture.screen": "화면 캡처",
  "feedback.new": "새 피드백",
  "feedback.process": "피드백 처리",
  "asset.new": "에셋 브리프 생성",
  "asset.prepare": "에셋 파이프라인 준비",
  "asset.status": "에셋 상태 변경",
  "asset.forge": "Asset Forge 생성",
  "asset.image3d": "Image→Blender 생성",
  "gdx.probe": "gdx1 연결 확인",
  "gdx.sync": "gdx1 동기화",
  "gdx.runServer": "gdx1 서버 실행 검증",
  "gdx.runBots": "gdx1 봇 실행 검증",
  "gdx.collectLogs": "gdx1 로그 수집",
};

async function api(path, options = {}) {
  const merged = { ...options };
  const method = String(merged.method || "GET").toUpperCase();
  const headers = { ...(merged.headers || {}) };
  if (method !== "GET" && executionToken) {
    headers[executionTokenHeader] = executionToken;
  }
  if (Object.keys(headers).length) {
    merged.headers = headers;
  }
  const response = await fetch(path, merged);
  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || `${response.status} ${response.statusText}`);
  }
  return response.json();
}

async function loadState() {
  state = await api("/api/state");
  executionToken = state.security?.executionToken || executionToken;
  executionTokenHeader = state.security?.tokenHeader || executionTokenHeader;
  render();
}

function render() {
  const updatedAt = formatDate(state.company?.state?.updated_at);
  $("#subtitle").textContent = `${state.project} · ${updatedAt ? `갱신 ${updatedAt}` : "상태 확인 중"}`;
  $("#stateStamp").textContent = updatedAt ? `갱신 ${updatedAt}` : "갱신 시간 없음";
  renderMemory();
  renderMissionDock();
  renderGameProduction();
  renderInspector();
  renderRecommendation();
  renderCommandCenter();
  renderSimulationRun();
  renderConversationStream();
  renderJobLedger();
  renderTaskTracker();
  renderSearch();
  renderGoal();
  renderStats();
  renderOrchestration();
  renderAgentOSAbsorption();
  renderSession();
  renderAdapters();
  renderAgents();
  renderTasks();
  renderFeedback();
  renderAssets();
  renderAssetForge();
  renderWorkers();
  renderRuntime();
  renderModelCookbook();
  renderRuns();
  applyStudioView(activeStudioView);
}

function renderMissionDock() {
  const tasks = state.company?.tasks || [];
  const openTasks = state.company?.openTasks || [];
  const task = trackerTask() || latestTask(tasks);
  const latest = state.jobs?.[0] || null;
  const agents = state.company?.agents || [];
  const workers = state.workers?.workers || [];
  const activeWorkers = workers.filter((worker) => worker.enabled && worker.status === "available").length;
  const runtime = state.runtime || {};
  const runner = runtime.hostRunner || {};
  const gdx = state.company?.state?.gdx1 || {};
  const game = state.gameProduction || {};
  const gameReady = game.readiness || {};
  const receipt = latest?.receipt?.path || (task ? latestReceiptPath(task) : "");
  const activeAgent = task ? taskAgent(task) : "chief_orchestrator";

  $("#focusMissionTitle").textContent = task?.request || "새 요청을 입력하세요";
  $("#focusMissionMeta").textContent = task
    ? `${task.id || "작업"} · ${displayTaskStatus(task)} · ${taskAgent(task)}`
    : `${openTasks.length}개 열린 작업 · 오케스트레이터 대기`;

  $("#focusAgentSummary").textContent = task ? `${activeAgent} 진행 중` : `${agents.length}명 팀 대기`;
  $("#focusAgentMeta").textContent = task
    ? `${toolForAgent(activeAgent)} · 열린 작업 ${openTasks.length}개 · worker ${activeWorkers}/${workers.length}`
    : `${activeWorkers}/${workers.length} worker 활성`;

  $("#focusSystemSummary").textContent = runtime.containerized
    ? `Docker · ${translateRuntime(runner.status || "pending")}`
    : `Local · ${translateRuntime(runner.status || "local")}`;
  $("#focusSystemMeta").textContent = [
    gameReady.total ? `Game ${gameReady.passed}/${gameReady.total}` : "",
    runtime.dockerSocketMounted ? "Docker socket 노출" : "Docker socket 차단",
    runner.message || "",
    gdx.ssh ? `gdx1 ${translate(gdx.ssh)}` : "",
  ].filter(Boolean).join(" · ") || "시스템 상태 없음";

  $("#focusResultSummary").textContent = latest
    ? `${commandText[latest.commandName] || latest.commandName || "작업"} · ${jobDisplayStatus(latest)}`
    : resultLabel(task || {});
  $("#focusResultMeta").textContent = receipt || "아직 receipt가 없습니다.";
}

function renderGameProduction() {
  const game = state.gameProduction || {};
  const readiness = game.readiness || {};
  const checks = game.checks || [];
  const unity = game.unity || {};
  const gdx = game.gdx || {};
  const remote = game.remote || {};
  const capture = game.capture || {};
  const mvp = game.mvp || {};
  const next = game.nextBestAction || {};
  const perfection = game.perfectionGate || {};
  const passed = Number(readiness.passed || 0);
  const total = Number(readiness.total || checks.length || 0);
  const ready = total > 0 && passed === total;

  const stateNode = $("#gameReadinessState");
  if (!stateNode) return;
  stateNode.textContent = total ? `${passed}/${total} ${ready ? "준비됨" : "점검 필요"}` : "대기";
  stateNode.className = `tag ${ready ? "good" : "warn"}`;

  $("#gameReadinessSummary").innerHTML = [
    gameMetric("MVP", `${unity.scenes || 0} scenes`, `${unity.gameplayScripts || 0} gameplay · ${unity.prefabs || 0} prefabs`),
    gameMetric("Unity", runSummary(unity.playtest) || runSummary(unity.compile) || "증거 대기", unity.build?.path || "Mac 빌드 기록 대기"),
    gameMetric("gdx1", `${runSummary(gdx) || "probe 대기"} · ${gdxOpsLabel(gdx)}`, remoteSummary(remote)),
    gameMetric("피드백", capture.summary || "캡처 대기", capture.path || "캡처 후 주석/피드백으로 전환"),
  ].join("");

  const perfect = perfection.status === "perfect";
  $("#gamePerfectionGate").innerHTML = perfection.total ? `
    <div class="game-perfect-summary ${perfect ? "good" : "warn"}">
      <span>완성 판정</span>
      <strong>${esc(perfection.answer || translate(perfection.status || "pending"))}</strong>
      <small>${esc(`${perfection.passed || 0}/${perfection.total || 0} · ${perfection.scope || ""}`)}</small>
    </div>
    <div class="game-perfect-checks">
      ${(perfection.checks || []).map((check) => `
        <button type="button" class="${check.passed ? "good" : "warn"}" disabled>
          <span>${esc(check.label || "check")}</span>
          <strong>${esc(check.passed ? "통과" : "대기")}</strong>
          <small>${esc(check.detail || "")}</small>
        </button>
      `).join("")}
    </div>
  ` : "";

  $("#gameNextAction").innerHTML = next.label ? `
    <div class="game-next-copy ${esc(toneForStatus(next.status))}">
      <span>다음 액션</span>
      <strong>${esc(next.label)}</strong>
      <small>${esc(next.reason || "")}</small>
    </div>
    ${next.command && next.command !== "asset.prepare" ? `<button type="button" data-command="${esc(next.command)}" data-command-payload="${esc(JSON.stringify(next.payload || {}))}">${esc(commandText[next.command] || next.command)}</button>` : ""}
  ` : "";

  $("#gameProductionChecks").innerHTML = checks.map((check) => `
    <button type="button" class="game-check-card ${check.passed ? "good" : "warn"}" data-game-artifact-path="${esc(check.path || "")}" ${check.path ? "" : "disabled"}>
      <span>${esc(check.label || "검증")}</span>
      <strong>${esc(check.passed ? "통과" : "대기")}</strong>
      <small>${esc(check.path || "아직 증거 없음")}</small>
    </button>
  `).join("") || empty("검증 항목이 없습니다.");

  const loops = game.optimizationLoops || [];
  $("#gameOptimizationLoops").innerHTML = loops.map((loop) => `
    <button type="button" class="game-loop-card ${esc(toneForStatus(loop.status))}" data-game-artifact-path="${esc(loop.evidence || "")}" ${loop.evidence ? "" : "disabled"}>
      <span>${esc(loop.label || "최적화 루프")}</span>
      <strong>${esc(translate(loop.status || "pending"))}</strong>
      <small>${esc(loop.summary || loop.nextAction || "상태 대기")}</small>
      <em>${esc(loop.evidence || loop.nextAction || "")}</em>
    </button>
  `).join("") || empty("최적화 루프 상태가 없습니다.");

  const artifacts = [
    ["컴파일", unity.compile?.path],
    ["플레이테스트", unity.playtest?.path],
    ["Mac 빌드", unity.build?.path],
    ["gdx1", gdx.path],
    ["gdx 서버", remote.server?.path],
    ["gdx 봇", remote.bots?.path],
    ["Linux 서버 빌드", remote.linuxServerBuild?.path],
    ["캡처", capture.path],
    ["MVP 스펙", mvp.spec],
  ].filter(([, path]) => path);
  $("#gameProductionArtifacts").innerHTML = artifacts.map(([label, path]) => `
    <button type="button" data-game-artifact-path="${esc(path)}">
      <span>${esc(label)}</span>
      <strong>${esc(path)}</strong>
    </button>
  `).join("") || empty("아직 표시할 제작 증거가 없습니다.");
}

function gameMetric(label, value, detail) {
  return `
    <div class="game-metric">
      <span>${esc(label)}</span>
      <strong>${esc(value || "대기")}</strong>
      <small>${esc(detail || "")}</small>
    </div>
  `;
}

function runSummary(run) {
  return run?.summary || "";
}

function remoteSummary(remote) {
  return [
    `server-soak ${translate(remote.status || "pending")}`,
    remote.server?.summary ? `server ${remote.server.summary}` : "server runner 대기",
    remote.bots?.summary ? `bots ${remote.bots.summary}` : "bot runner 대기",
  ].join(" · ");
}

function gdxOpsLabel(gdx) {
  return runSummary(gdx) ? "AI/ops 가능" : "probe 필요";
}

function renderInspector() {
  if (!$("#inspectorMode")) return;
  const tasks = state.company?.tasks || [];
  const openTasks = state.company?.openTasks || [];
  const task = trackerTask() || latestTask(tasks);
  const latest = state.jobs?.[0] || null;
  const activeJob = activeJobId ? (state.jobs || []).find((job) => job.id === activeJobId) : null;
  const job = activeJob || latest;
  const runtime = state.runtime || {};
  const runner = runtime.hostRunner || {};
  const gdx = state.company?.state?.gdx1 || {};
  const game = state.gameProduction?.readiness || {};
  const workers = state.workers?.workers || [];
  const activeWorkers = workers.filter((worker) => worker.enabled && worker.status === "available").length;
  const artifacts = task
    ? taskArtifacts(task).filter((artifact) => artifact.path && artifact.exists !== false).slice(0, 5)
    : job?.receipt?.path
      ? [{ label: "최근 receipt", path: job.receipt.path, kind: "receipt", exists: true }]
      : [];
  const memory = state.memory || {};
  const next = task ? taskNextAction(task) : null;

  $("#inspectorMode").textContent = studioViews[activeStudioView] || "미션";
  $("#inspectorThreadTitle").textContent = task?.request || "새 요청 대기";
  $("#inspectorThreadMeta").textContent = task
    ? `${task.id || "작업"} · ${displayTaskStatus(task)} · ${taskAgent(task)}`
    : `열린 작업 ${openTasks.length}개 · 최근 job ${latest?.id || "없음"}`;
  $("#inspectorNextAction").innerHTML = task ? `
    <button type="button" data-inspector-focus-task="${esc(task.id || "")}">작업 보기</button>
    ${next ? `<button type="button" data-inspector-mode="board">상세 보드</button>` : ""}
  ` : `<button type="button" data-inspector-mode="focus">요청 입력</button>`;

  $("#inspectorHealth").innerHTML = [
    healthChip("Studio", runtime.containerized ? "Docker" : "Local", runtime.containerized ? "good" : "warn"),
    healthChip("Runner", translateRuntime(runner.status || "local"), runner.status === "available" || runner.status === "local" ? "good" : "warn"),
    healthChip("gdx1", translate(gdx.ssh || "unknown"), gdx.ssh === "ok" ? "good" : "warn"),
    healthChip("Game", game.total ? `${game.passed}/${game.total}` : "대기", game.total && game.passed === game.total ? "good" : "warn"),
    healthChip("Workers", `${activeWorkers}/${workers.length}`, activeWorkers ? "good" : "warn"),
  ].join("");

  const events = (job?.events || []).slice(-4).reverse();
  $("#inspectorActivity").innerHTML = job ? `
    <div class="mini-job ${esc(jobDisplayTone(job))}">
      <strong>${esc(commandText[job.commandName] || job.commandName || job.id)}</strong>
      <small>${esc(job.id)} · ${esc(jobDisplayStatus(job))}</small>
    </div>
    ${events.map((event) => `
      <div class="mini-event">
        <span>${esc(formatDate(event.time))}</span>
        <p>${esc(event.message || event.type || "")}</p>
      </div>
    `).join("")}
  ` : emptyMini("실행 기록 없음");

  $("#inspectorArtifacts").innerHTML = artifacts.map((artifact) => `
    <button type="button" class="mini-artifact" data-inspector-artifact-path="${esc(artifact.path)}">
      <strong>${esc(artifact.label || artifact.kind || "결과물")}</strong>
      <small>${esc(artifact.path)}</small>
    </button>
  `).join("") || emptyMini("표시할 결과물 없음");

  $("#inspectorMemory").innerHTML = [
    memoryLink("Current Brief", "memory/company/current_brief.md"),
    memory.projectBrainPath ? memoryLink("Project Brain", memory.projectBrainPath) : "",
    memory.userProfilePath ? memoryLink("User Profile", memory.userProfilePath) : "",
  ].filter(Boolean).join("") || emptyMini("공유 기억 없음");
}

function healthChip(label, value, tone) {
  return `
    <div class="health-chip ${esc(tone || "")}">
      <span>${esc(label)}</span>
      <strong>${esc(value || "미확인")}</strong>
    </div>
  `;
}

function memoryLink(label, path) {
  return `
    <button type="button" class="memory-link" data-inspector-memory-path="${esc(path)}">
      <strong>${esc(label)}</strong>
      <small>${esc(path)}</small>
    </button>
  `;
}

function emptyMini(message) {
  return `<div class="mini-empty">${esc(message)}</div>`;
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

function renderCommandCenter() {
  const activeJob = activeJobId ? (state.jobs || []).find((job) => job.id === activeJobId) : null;
  if (activeJob && !activeJob.isTerminal) {
    $("#commandCenterState").textContent = translate(activeJob.status);
    $("#commandCenterState").className = `tag ${toneForStatus(activeJob.status)}`;
    $("#commandCenterSummary").innerHTML = `
      <strong>${esc(commandText[activeJob.commandName] || activeJob.commandName || "명령 실행")}</strong>
      <span>${esc(activeJob.id)} · ${esc(jobLatestEvent(activeJob) || "작업 원장에 기록 중")}</span>
      <small>${esc(activeJob.receipt?.path || "완료되면 receipt가 생성됩니다.")}</small>
    `;
    return;
  }

  const serverActive = state.activity?.activeCommand || {};
  if (serverActive.id && !serverActive.isTerminal) {
    $("#commandCenterState").textContent = translate(serverActive.status || "running");
    $("#commandCenterState").className = `tag ${toneForStatus(serverActive.status || "running")}`;
    $("#commandCenterSummary").innerHTML = `
      <strong>${esc(commandText[serverActive.commandName] || serverActive.commandName || "명령 실행")}</strong>
      <span>${esc(serverActive.id)} · ${esc(serverActive.event || "실행 이벤트 대기")}</span>
      <small>${esc(serverActive.command || serverActive.receipt || "명령 원장을 확인 중입니다.")}</small>
    `;
    return;
  }

  if (liveActivity?.command === "orchestrator.run") {
    $("#commandCenterState").textContent = "협업 대기";
    $("#commandCenterState").className = "tag warn";
    $("#commandCenterSummary").innerHTML = `
      <strong>오케스트레이터가 요청을 분해하고 있습니다.</strong>
      <span>${esc(liveActivity.request || "요청 처리 중")}</span>
      <small>작업 생성, 에이전트 배정, 리뷰, 완료 처리를 자동으로 진행합니다.</small>
    `;
    return;
  }

  const tasks = state.company?.tasks || [];
  const latest = latestTask(tasks);
  const openTasks = state.company?.openTasks || [];
  const status = latest?.status || "none";
  const verification = latest?.verification_status ? ` · 검증 ${translate(latest.verification_status)}` : "";
  const recentEvent = state.activity?.latestEvents?.[0];
  $("#commandCenterState").textContent = openTasks.length > 0 ? `${openTasks.length}개 진행 중` : "대기";
  $("#commandCenterState").className = `tag ${openTasks.length > 0 ? "warn" : "good"}`;
  $("#commandCenterSummary").innerHTML = latest ? `
    <strong>${esc(latest.id)} · ${esc(translate(status))}${esc(verification)}</strong>
    <span>${esc(latest.request || "요청 없음")}</span>
    <small>${esc(recentEvent ? `${recentEvent.commandName}: ${recentEvent.message}` : latest.last_agent_run || latest.report || latest.verification || "아직 산출물이 없습니다.")}</small>
  ` : "요청을 입력하면 진행 로그와 결과물이 이 화면에 바로 표시됩니다.";
}

function renderSimulationRun() {
  const node = $("#simulationRunPanel");
  if (!node) return;
  const run = state.sim?.latestRun || {};
  const proofCard = renderProofRefreshCard(state.sim?.proofRefresh || {});
  if (!run.exists) {
    node.innerHTML = `
      ${proofCard}
      <div class="sim-empty">
        <strong>에이전트 실행 증거 없음</strong>
        <span>먼저 scripted proof를 실행하세요.</span>
        <button type="button" data-sim-command="asset.semanticPack" data-asset-id="pyramid_temple_full_environment">의미 팩 생성</button>
        <button type="button" data-sim-command="unity.semanticCheck" data-asset-id="pyramid_temple_full_environment">의미 검증</button>
        <button type="button" data-sim-command="simworld.probe">gdx1 점검</button>
        <button type="button" data-sim-command="simworld.doctor">gdx1 Doctor</button>
        <button type="button" data-sim-command="simworld.installBaseDryRun">Base 설치 확인</button>
        <button type="button" data-sim-command="company.workers.probe">x86 워커 점검</button>
        <button type="button" data-sim-command="simworld.workerGuide">x86 설정 가이드</button>
        <button type="button" data-sim-command="simworld.routePlan">경로 계획</button>
        <button type="button" data-sim-command="simworld.startServer">UE 시작</button>
        <button type="button" data-sim-command="simAcceptance.proofRefresh" data-asset-id="pyramid_temple_full_environment">Unity 증거 갱신</button>
        <button type="button" data-sim-command="unity.agentPlaytestPyramid">피라미드 에이전트 실행</button>
      </div>
    `;
    return;
  }

  const counts = run.counts || {};
  const artifacts = run.artifacts || {};
  const latestFrame = run.frames?.latestRgb || run.frames?.firstRgb || "";
  const frameUrl = latestFrame ? `/artifact/${encodeURI(latestFrame)}` : "";
  const statusTone = run.routeCompletion ? "good" : "warn";
  const simEvents = Array.isArray(run.eventStream) ? run.eventStream : [];
  const eventRows = simEvents.map((event) => `
    <div class="sim-event-row ${toneForStatus(event.status || "ok")}">
      <strong>${esc(event.label || event.type || "event")}</strong>
      <span>${esc(event.target || "")}</span>
      <small>${esc(event.reason || event.status || "")}</small>
    </div>
  `).join("");
  const routeOrder = Array.isArray(run.command?.routeOrder) ? run.command.routeOrder : [];
  const allowedActions = Array.isArray(run.command?.allowedActions) ? run.command.allowedActions : [];
  const compareButton = run.previousRun
    ? `<button type="button" data-sim-command="unity.simCompare" data-run-dir-a="${esc(run.path)}" data-run-dir-b="${esc(run.previousRun)}">이전 run 비교</button>`
    : "";
  const artifactButtons = [
    ["receipt", "Receipt"],
    ["review", "Review"],
    ["sceneState", "Scene"],
    ["semanticLabels", "Labels"],
    ["actions", "Actions"],
    ["metrics", "Metrics"],
    ["trajectory", "Route"],
  ].map(([key, label]) => artifacts[key] ? `<button type="button" data-file-path="${esc(artifacts[key])}">${esc(label)}</button>` : "").join("");

  node.innerHTML = `
    ${proofCard}
    <div class="sim-run-grid">
      <div class="sim-frame">
        ${frameUrl ? `<img src="${esc(frameUrl)}" alt="Latest agent observation frame">` : empty("관측 프레임 없음")}
      </div>
      <div class="sim-run-body">
        <div class="sim-title-row">
          <div>
            <p class="eyebrow">Agent Run</p>
            <h3>${esc(run.environment || "pyramid-maze-v2")} · ${esc(run.agent || "scripted")}</h3>
          </div>
          <span class="tag ${statusTone}">${esc(translate(run.status || "unknown"))}</span>
        </div>
        <p class="sim-summary">${esc(run.summary || "")}</p>
        <div class="metric-strip">
          <span><strong>${Number(counts.rgb || 0)}</strong> RGB</span>
          <span><strong>${Number(counts.segmentation || 0)}</strong> SEG</span>
          <span><strong>${Number(counts.depth || 0)}</strong> DEPTH</span>
          <span><strong>${Number(counts.actions || 0)}</strong> ACTION</span>
          <span><strong>${Number(counts.metrics || 0)}</strong> METRIC</span>
        </div>
        <div class="sim-command-proof">
          <small>Route ${routeOrder.length || 0}: ${esc(routeOrder.slice(0, 4).join(" -> ") || "미기록")}${routeOrder.length > 4 ? " -> ..." : ""}</small>
          <small>Actions ${allowedActions.length || 0}: ${esc(allowedActions.join(", ") || "미기록")}</small>
        </div>
        <div class="sim-event-stream">
          ${eventRows || empty("최근 시뮬레이션 이벤트 없음")}
        </div>
        <div class="sim-actions">
          <button type="button" data-sim-command="unity.simCheck">Sim 점검</button>
          <button type="button" data-sim-command="asset.semanticPack" data-asset-id="pyramid_temple_full_environment">의미 팩</button>
          <button type="button" data-sim-command="unity.semanticCheck" data-asset-id="pyramid_temple_full_environment">의미 검증</button>
          <button type="button" data-sim-command="simworld.probe">gdx1 점검</button>
          <button type="button" data-sim-command="simworld.doctor">gdx1 Doctor</button>
          <button type="button" data-sim-command="simworld.installBaseDryRun">Base 설치 확인</button>
          <button type="button" data-sim-command="company.workers.probe">x86 워커 점검</button>
          <button type="button" data-sim-command="simworld.workerGuide">x86 설정 가이드</button>
          <button type="button" data-sim-command="simworld.routePlan">경로 계획</button>
          <button type="button" data-sim-command="simworld.startServer">UE 시작</button>
          <button type="button" data-sim-command="simAcceptance.proofRefresh" data-asset-id="pyramid_temple_full_environment">Unity 증거 갱신</button>
          <button type="button" data-sim-command="unity.agentPlaytestPyramid">다시 실행</button>
          <button type="button" data-sim-command="unity.simReviewLatest" data-run-dir="${esc(run.path)}">리뷰</button>
          <button type="button" data-sim-command="unity.simReplayLatest" data-run-dir="${esc(run.path)}">리플레이</button>
          ${compareButton}
          <button type="button" data-sim-command="simAgent.packet" data-run-dir="${esc(run.path)}">AI 패킷</button>
          <button type="button" data-sim-command="simAgent.runCodex" data-run-dir="${esc(run.path)}">Codex 브리지</button>
          <button type="button" data-sim-command="simAgent.runOpenClaw" data-run-dir="${esc(run.path)}">OpenClaw 브리지</button>
          <button type="button" data-sim-command="simAgent.liveCheckAll" data-run-dir="${esc(run.path)}">Live 검증</button>
          <button type="button" data-sim-command="simAcceptance.check">최종 검수</button>
          <button type="button" data-sim-command="simAcceptance.handoff">인수인계</button>
        </div>
        <div class="artifact-buttons">${artifactButtons}</div>
      </div>
    </div>
  `;
}

function renderProofRefreshCard(proof) {
  if (!proof.exists) return "";
  const counts = proof.counts || {};
  const artifacts = proof.artifacts || {};
  const steps = Array.isArray(proof.steps) ? proof.steps : [];
  const evidence = Array.isArray(proof.evidence) ? proof.evidence : [];
  const tone = proof.status === "proof_refresh_passed" || proof.status === "proof_refresh_collected"
    ? "good"
    : proof.status === "proof_refresh_partial" || proof.status === "proof_refresh_incomplete"
      ? "warn"
      : "bad";
  const artifactButtons = [
    ["receipt", "Proof Receipt"],
    ["bundle", "Proof JSON"],
  ].map(([key, label]) => artifacts[key] ? `<button type="button" data-file-path="${esc(artifacts[key])}">${esc(label)}</button>` : "").join("");
  const evidenceButtons = evidence.slice(0, 8).map((item) => item.path
    ? `<button type="button" data-file-path="${esc(item.path)}" class="${item.exists ? "" : "warn"}">${esc(item.key)}</button>`
    : "").join("");
  const failed = steps.filter((step) => step.status !== "passed" && step.status !== "skipped");
  const stepRows = steps.slice(0, 8).map((step) => `
    <span class="${esc(toneForStatus(step.status))}">
      <strong>${esc(step.id || "step")}</strong>
      ${esc(translate(step.status || "unknown"))}
    </span>
  `).join("");
  return `
    <div class="proof-card">
      <div class="sim-title-row">
        <div>
          <p class="eyebrow">Proof Bundle</p>
          <h3>${esc(proof.semanticAssetId || "pyramid_temple_full_environment")} · ${esc(proof.mode || "run")}</h3>
        </div>
        <span class="tag ${tone}">${esc(translate(proof.status || "unknown"))}</span>
      </div>
      <p class="sim-summary">${esc(proof.summary || "")}</p>
      <div class="metric-strip proof-metrics">
        <span><strong>${Number(counts.passed || 0)}</strong> PASS</span>
        <span><strong>${Number(counts.failed || 0)}</strong> FAIL</span>
        <span><strong>${Number(counts.steps || 0)}</strong> STEP</span>
        <span><strong>${Number(counts.evidenceReady || 0)}</strong> READY</span>
        <span><strong>${Number(counts.evidence || 0)}</strong> EVIDENCE</span>
      </div>
      <div class="proof-steps">${stepRows}</div>
      ${failed.length ? `<p class="proof-warning">${esc(failed.length)}개 단계 확인 필요</p>` : ""}
      <div class="artifact-buttons">
        ${artifactButtons}
        ${evidenceButtons}
        <button type="button" data-sim-command="simAcceptance.proofRefresh" data-asset-id="pyramid_temple_full_environment">Unity 증거 갱신</button>
      </div>
    </div>
  `;
}

function renderConversationStream() {
  const node = $("#conversationStream");
  const stateNode = $("#conversationState");
  if (!node || !stateNode || !state) return;

  const jobs = state.jobs || [];
  const activeJob = activeJobId ? jobs.find((job) => job.id === activeJobId) : null;
  const tasks = state.company?.tasks || [];
  const latest = latestTask(tasks);
  const messages = [];

  if (liveActivity?.request) {
    messages.push(conversationMessage({
      role: "user",
      title: "나",
      body: liveActivity.request,
      meta: `${commandText[liveActivity.command] || liveActivity.command} · ${translate(liveActivity.status)}`,
      tone: "user",
    }));
  } else if (latest?.request) {
    messages.push(conversationMessage({
      role: "user",
      title: "나",
      body: latest.request,
      meta: `${latest.id} · ${formatDate(latest.created_at || latest.updated_at) || "시간 없음"}`,
      tone: "user",
    }));
  }

  const focusJob = activeJob || jobs[0];
  if (focusJob) {
    messages.push(jobConversationMessage(focusJob, activeJob && !activeJob.isTerminal));
  }

  const activityEvents = Array.isArray(state.activity?.latestEvents) ? state.activity.latestEvents : [];
  if (activityEvents.length) {
    messages.push(conversationMessage({
      role: "tool",
      title: "최근 이벤트 스트림",
      body: activityEvents.slice(0, 4).map((event) => `${event.commandName || event.jobId}: ${event.message}`).join("\n"),
      meta: activityEvents[0]?.time || "이벤트 시간 없음",
      tone: toneForStatus(activityEvents[0]?.status || "pending"),
    }));
  }

  if (latest) {
    messages.push(taskConversationMessage(latest));
  }

  for (const job of jobs.slice(0, 4)) {
    if (job.id === focusJob?.id) continue;
    messages.push(jobConversationMessage(job, false, true));
  }

  stateNode.textContent = liveActivity ? "진행 중" : focusJob ? translate(focusJob.status) : "대기";
  stateNode.className = `tag ${toneForStatus(liveActivity?.status || focusJob?.status || "pending")}`;
  node.innerHTML = messages.join("") || empty("요청을 입력하면 이곳에 대화형 진행 기록이 쌓입니다.");
}

function taskConversationMessage(task) {
  const artifacts = taskArtifacts(task).filter((artifact) => artifact.path && artifact.exists !== false).slice(0, 4);
  const answer = task.answerSummary || {};
  const fallbackBody = [
    `${displayTaskStatus(task)} · 담당 ${taskAgent(task)}`,
    resultLabel(task),
    task.closed_at ? `완료 ${formatDate(task.closed_at)}` : "",
  ].filter(Boolean).join("\n");
  const body = answer.summary || fallbackBody;
  return conversationMessage({
    role: "assistant",
    title: answer.summary ? "오케스트레이터 답변" : "오케스트레이터",
    body,
    meta: `${task.id} · ${answer.path || task.required_evidence || "증거 기준 없음"}`,
    tone: displayTaskTone(task),
    actions: conversationArtifactButtons(artifacts),
  });
}

function jobConversationMessage(job, active = false, compact = false) {
  const event = jobLatestEvent(job) || job.receipt?.summary || "이벤트 대기";
  const receipt = job.receipt?.path ? [{ label: "Receipt", path: job.receipt.path }] : [];
  const body = compact
    ? event
    : [
        `${commandText[job.commandName] || job.commandName || job.id}`,
        event,
        job.taskId ? `연결 작업 ${job.taskId}` : "",
      ].filter(Boolean).join("\n");
  return conversationMessage({
    role: "tool",
    title: active ? "실행 중" : "실행 결과",
    body,
    meta: `${job.id} · ${jobDisplayStatus(job)} · ${formatDate(job.updatedAt || job.createdAt) || ""}`,
    tone: jobDisplayTone(job),
    actions: conversationArtifactButtons(receipt),
  });
}

function conversationMessage({ role, title, body, meta, tone, actions = "" }) {
  return `
    <div class="conversation-message ${esc(role)} ${esc(tone || "")}">
      <div class="conversation-avatar">${esc(role === "user" ? "나" : role === "tool" ? "실행" : "AI")}</div>
      <div class="conversation-bubble">
        <div class="conversation-meta">
          <strong>${esc(title || "")}</strong>
          <span>${esc(meta || "")}</span>
        </div>
        <p>${esc(body || "").replace(/\n/g, "<br>")}</p>
        ${actions}
      </div>
    </div>
  `;
}

function conversationArtifactButtons(artifacts) {
  return (artifacts || []).map((artifact) => `
    <button type="button" class="conversation-artifact" data-conversation-artifact-path="${esc(artifact.path)}">
      <span>${esc(artifact.label || artifact.kind || "결과물")}</span>
      <strong>${esc(artifact.path)}</strong>
    </button>
  `).join("");
}

function renderJobLedger() {
  const jobs = state.jobs || [];
  const latest = jobs[0];
  const stateNode = $("#jobLedgerState");
  const listNode = $("#jobLedger");
  if (!stateNode || !listNode) return;

  if (!jobs.length) {
    stateNode.textContent = "기록 없음";
    stateNode.className = "tag";
    listNode.innerHTML = empty("아직 실행 원장 기록이 없습니다.");
    return;
  }

  stateNode.textContent = latest ? jobDisplayStatus(latest) : "대기";
  stateNode.className = `tag ${jobDisplayTone(latest)}`;
  listNode.innerHTML = jobs.slice(0, 6).map((job) => `
    <div class="job-row ${esc(jobDisplayTone(job))}">
      <div>
        <strong>${esc(commandText[job.commandName] || job.commandName || job.id)}</strong>
        <span>${esc(job.id)} · ${esc(formatDate(job.updatedAt || job.createdAt) || "")}</span>
        <small>${esc(jobLatestEvent(job) || job.receipt?.summary || "이벤트 대기")}</small>
        ${job.receipt?.path ? `<em>${esc(job.receipt.path)}</em>` : ""}
      </div>
      <b>${esc(jobDisplayStatus(job))}</b>
    </div>
  `).join("");
}

function jobLatestEvent(job) {
  if (jobOutcome(job) === "blocked" && job?.receipt?.summary) {
    return job.receipt.summary;
  }
  const events = job?.events || [];
  return events.length ? events[events.length - 1].message || "" : "";
}

function renderTaskTracker() {
  const task = trackerTask();
  if (!task && isPendingWorkflowActivity()) {
    renderPendingTracker();
    return;
  }
  if (!task) {
    $("#trackerState").textContent = "대기";
    $("#trackerState").className = "tag";
    $("#trackerSummary").innerHTML = empty("아직 추적할 작업이 없습니다.");
    $("#productionCard").innerHTML = "";
    $("#trackerSteps").innerHTML = "";
    $("#trackerTimeline").innerHTML = empty("처리 기록이 없습니다.");
    $("#trackerArtifacts").innerHTML = empty("결과물이 없습니다.");
    $("#trackerPreviewTitle").textContent = "선택된 파일 없음";
    $("#trackerPreview").textContent = "작업을 선택하면 결과 파일을 보여줍니다.";
    return;
  }

  selectedTaskId = task.id || selectedTaskId;
  const status = task.status || "pending";
  $("#trackerState").textContent = displayTaskStatus(task);
  $("#trackerState").className = `tag ${toneForStatus(displayTaskTone(task))}`;

  const agent = taskAgent(task);
  const runCount = Array.isArray(task.agent_runs) ? task.agent_runs.length : 0;
  const evidenceCount = Array.isArray(task.evidence) ? task.evidence.length : 0;
  $("#trackerSummary").innerHTML = [
    trackerMetric("작업", task.id || "미확인", task.request || "요청 없음"),
    trackerMetric("담당", agent, `${toolForAgent(agent)} · ${task.last_tool || "역할 기본값"}`),
    trackerMetric("진행", translate(task.agent_status || task.status || "pending"), `${runCount}회 실행 · 증거 ${evidenceCount}개`),
    trackerMetric("결과", resultLabel(task), task.closed_at ? `완료 ${formatDate(task.closed_at)}` : `갱신 ${formatDate(task.updated_at || task.created_at) || "없음"}`),
  ].join("");
  renderProductionCard(task);

  $("#trackerSteps").innerHTML = trackerSteps(task).map((step) => `
    <div class="tracker-step ${esc(step.tone)}">
      <span>${esc(step.label)}</span>
      <strong>${esc(step.value)}</strong>
    </div>
  `).join("");

  $("#trackerTimeline").innerHTML = trackerTimeline(task).map((row) => `
    <div class="timeline-row ${esc(row.tone)}">
      <span>${esc(row.time || "")}</span>
      <div>
        <strong>${esc(row.title)}</strong>
        <small>${esc(row.body || "")}</small>
      </div>
      <em>${esc(row.badge || "")}</em>
    </div>
  `).join("") || empty("처리 기록이 없습니다.");

  const artifacts = taskArtifacts(task);
  if (!selectedArtifactPath || !artifacts.some((artifact) => artifact.path === selectedArtifactPath)) {
    selectedArtifactPath = defaultArtifactPath(task, artifacts);
  }
  $("#trackerArtifacts").innerHTML = artifacts.map((artifact) => `
    <button class="artifact-button ${artifact.path === selectedArtifactPath ? "active" : ""}" data-artifact-path="${esc(artifact.path)}" ${artifact.exists === false ? "disabled" : ""}>
      <span>${esc(artifact.label || artifact.kind || "결과물")}</span>
      <strong>${esc(artifact.path)}</strong>
      <small>${esc(artifactNote(artifact))}</small>
    </button>
  `).join("") || empty("결과물이 없습니다.");
  renderTrackerPreview(selectedArtifactPath);
}

function renderSearch() {
  const stateNode = $("#searchState");
  const summaryNode = $("#searchSummary");
  const resultsNode = $("#searchResults");
  if (!stateNode || !summaryNode || !resultsNode) return;

  if (!searchState) {
    stateNode.textContent = "대기";
    stateNode.className = "tag";
    resultsNode.innerHTML = empty("검색 결과가 없습니다.");
    return;
  }

  if (searchState.loading) {
    stateNode.textContent = "검색 중";
    stateNode.className = "tag warn";
    summaryNode.textContent = `${searchState.query || ""} 검색 인덱스를 확인하고 있습니다.`;
    resultsNode.innerHTML = empty("결과를 불러오는 중입니다.");
    return;
  }

  const count = searchState.count || 0;
  stateNode.textContent = `${count}건`;
  stateNode.className = `tag ${count ? "good" : "warn"}`;
  summaryNode.textContent = [
    searchState.indexPath ? `인덱스 ${searchState.indexPath}` : "",
    searchState.documentCount ? `${searchState.documentCount}개 문서` : "",
    searchState.indexedAt ? `갱신 ${formatDate(searchState.indexedAt)}` : "",
  ].filter(Boolean).join(" · ") || "검색 인덱스 정보가 없습니다.";

  resultsNode.innerHTML = (searchState.results || []).map((result) => `
    <button class="search-result" data-search-path="${esc(result.path)}" data-source-type="${esc(result.sourceType)}">
      <span>${esc(translateSourceType(result.sourceType))}</span>
      <strong>${esc(result.path)}</strong>
      <small>${esc(result.preview || result.title || "미리보기 없음")}</small>
      <em>${esc(formatDate(result.modifiedAt) || "")}</em>
    </button>
  `).join("") || empty("검색 결과가 없습니다.");
}

function renderPendingTracker() {
  $("#trackerState").textContent = "진행 중";
  $("#trackerState").className = "tag warn";
  $("#trackerSummary").innerHTML = [
    trackerMetric("작업", "생성 중", liveActivity?.request || "요청 처리 중"),
    trackerMetric("담당", "chief_orchestrator", "요청 분석"),
    trackerMetric("진행", "협업 대기", "작업 주문과 에이전트 배정 준비"),
    trackerMetric("결과", "대기", "완료 후 결과 파일이 표시됩니다."),
  ].join("");
  $("#productionCard").innerHTML = "";
  $("#trackerSteps").innerHTML = ["요청", "작업 주문", "에이전트", "리뷰", "검증", "결과"].map((label, index) => `
    <div class="tracker-step ${index === 0 ? "good" : "warn"}">
      <span>${esc(label)}</span>
      <strong>${index === 0 ? "접수" : "대기"}</strong>
    </div>
  `).join("");
  $("#trackerTimeline").innerHTML = `
    <div class="timeline-row warn">
      <span>${esc(formatDate(liveActivity?.startedAt))}</span>
      <div>
        <strong>명령 접수</strong>
        <small>${esc(liveActivity?.request || "요청 처리 중")}</small>
      </div>
      <em>진행 중</em>
    </div>
  `;
  $("#trackerArtifacts").innerHTML = empty("아직 결과물이 생성되지 않았습니다.");
  $("#trackerPreviewTitle").textContent = "선택된 파일 없음";
  $("#trackerPreview").textContent = "오케스트레이터가 작업을 생성하고 있습니다.";
}

function trackerMetric(label, value, detail) {
  return `
    <div class="tracker-metric">
      <span>${esc(label)}</span>
      <strong>${esc(value || "미확인")}</strong>
      <small>${esc(detail || "")}</small>
    </div>
  `;
}

function renderProductionCard(task) {
  const card = task.productionCard || fallbackProductionCard(task);
  const next = card.nextAction || {};
  $("#productionCard").innerHTML = `
    <div class="production-card-main">
      <div>
        <span>목표</span>
        <strong>${esc(card.goal || task.request || task.id || "작업 목표 없음")}</strong>
      </div>
      <div>
        <span>현재 단계</span>
        <strong>${esc(translate(card.stage || task.status || "pending"))}</strong>
      </div>
      <div>
        <span>완료 방식</span>
        <strong>${esc(card.completionMethod || resultLabel(task))}</strong>
      </div>
      <div>
        <span>다음 행동</span>
        <strong>${esc(next.label || taskNextAction(task)?.label || "상세 확인")}</strong>
      </div>
    </div>
    <div class="production-card-detail">
      <p><b>담당</b>${esc(card.agent || taskAgent(task))}</p>
      <p><b>협업</b>${esc((card.collaborators || []).join(", ") || "대기")}</p>
      <p><b>명령</b>${esc(card.runningCommand || "실행 중인 명령 없음")}</p>
      <p><b>최근 이벤트</b>${esc(card.lastHeartbeat || latestJobEvent(task) || "이벤트 없음")}</p>
      <p><b>Receipt</b>${esc(card.receiptPath || latestReceiptPath(task) || "아직 없음")}</p>
      <p><b>판단</b>${esc(next.reason || "현재 상태에 맞는 다음 버튼을 사용하세요.")}</p>
    </div>
  `;
}

function fallbackProductionCard(task) {
  const job = latestJob(task);
  const receipt = job?.receipt || {};
  return {
    goal: task.request || task.id,
    agent: taskAgent(task),
    collaborators: [task.suggested_reviewer || "critic_reviewer"],
    stage: job?.status || task.status || "pending",
    runningCommand: Array.isArray(job?.command) ? job.command.join(" ") : "",
    lastHeartbeat: latestJobEvent(task),
    artifactCount: taskArtifacts(task).length,
    verification: task.verification_status || receipt.verification?.status || "pending",
    receiptPath: receipt.path || "",
    nextAction: taskNextAction(task),
    completionMethod: task.closed_at ? "완료됨" : receipt.path ? "실행 receipt 생성됨" : "아직 완료되지 않음",
  };
}

function renderGoal() {
  const goal = state.company?.state?.integrated_goal || {};
  const engine = state.goals?.activeGoal || null;
  const scope = Array.isArray(goal.mvp_scope) ? goal.mvp_scope : [];
  const summary = $("#goalSummary");

  if (!goal.id) {
    summary.hidden = true;
    return;
  }

  summary.hidden = false;
  $("#goalTitle").textContent = goal.ko_title || goal.title || goal.id;
  $("#goalMeta").textContent = [
    goal.first_game_mode ? `첫 모드 ${goal.first_game_mode}` : "",
    goal.first_development_milestone || "",
  ].filter(Boolean).join(" · ");
  $("#goalScope").innerHTML = scope.slice(0, 4).map((itemText) => `<span>${esc(itemText)}</span>`).join("");

  const engineState = $("#goalEngineState");
  if (!engine) {
    $("#goalEngineTitle").textContent = "목표 없음";
    $("#goalEngineMeta").textContent = "목표를 설정하면 chief_orchestrator가 필요한 에이전트를 지휘합니다.";
    engineState.textContent = "대기";
    engineState.className = "";
    $("#goalEngineChecks").innerHTML = empty("아직 Goal Engine 작업이 없습니다.");
    $("#goalEngineReceipt").textContent = "receipt 없음";
    return;
  }

  const completion = engine.completion || {};
  const checks = completion.checks || [];
  $("#goalEngineTitle").textContent = engine.objective || engine.id || "목표";
  $("#goalEngineMeta").textContent = `${engine.id || ""} · ${completion.passed || 0}/${completion.total || 0} 검증 · 반복 ${engine.iterations || 0}/${engine.max_iterations || 0}`;
  engineState.textContent = translate(engine.status || completion.status || "active");
  engineState.className = toneForStatus(engine.status || completion.status || "active");
  $("#goalEngineChecks").innerHTML = checks.map((check) => `
    <button type="button" class="${esc(toneForStatus(check.status))}" data-goal-task-id="${esc(check.taskId || "")}" ${check.taskId ? "" : "disabled"}>
      <span>${esc(check.label || "단계")}</span>
      <strong>${esc(translate(check.status || "pending"))}</strong>
      <small>${esc(check.detail || check.answerPath || "")}</small>
    </button>
  `).join("") || empty("목표 작업 생성 대기");
  $("#goalEngineReceipt").textContent = engine.lastReceipt ? `최근 receipt: ${engine.lastReceipt}` : (engine.answer || "receipt 없음");
}

function renderMemory() {
  const memory = state.memory || {};
  $("#briefPreview").textContent = memory.currentBrief || memory.currentContext || "아직 생성된 브리프가 없습니다.";
  const brainNode = $("#projectBrainPreview");
  if (brainNode) {
    brainNode.textContent = memory.projectBrain || "Project Brain이 아직 없습니다.";
  }
  const standardsNode = $("#standardsList");
  if (standardsNode) {
    const standards = memory.standards || [];
    standardsNode.innerHTML = standards.map((standard) => `
      <button class="standard-button" data-memory-path="${esc(standard.path)}">
        <span>${esc(standard.title || standard.id)}</span>
        <strong>${esc(standard.path)}</strong>
        <small>${esc(standard.excerpt || "")}</small>
      </button>
    `).join("") || empty("등록된 standards가 없습니다.");
  }
  const metaNode = $("#brainMeta");
  if (metaNode) {
    metaNode.innerHTML = [
      memory.projectBrainPath ? `<span>${esc(memory.projectBrainPath)}</span>` : "",
      memory.userProfilePath ? `<span>${esc(memory.userProfilePath)}</span>` : "",
      memory.agentMemoryPath ? `<span>${esc(memory.agentMemoryPath)}</span>` : "",
    ].filter(Boolean).join("");
  }
}

function renderStats() {
  const dirty = dirtyCount(state.git?.dirty);
  const companyState = state.company?.state || {};
  const openTasks = state.company?.openTasks?.length || 0;
  const locks = state.company?.locks?.length || 0;
  const gdx = companyState.gdx1 || {};
  const adapters = Object.values(state.adapters?.tools || {});
  const availableAdapters = adapters.filter((tool) => tool.status === "available").length;
  const workers = state.workers?.workers || [];
  const activeWorkers = workers.filter((worker) => worker.enabled && worker.status === "available").length;
  const modelSummary = state.modelCookbook?.summary || {};
  const absorptionSummary = state.agentosAbsorption?.summary || {};
  const runtime = state.runtime || {};
  const game = state.gameProduction?.readiness || {};
  const activeSession = companyState.active_session || "없음";
  const gitHead = state.git?.head || "알 수 없음";

  const stats = [
    ["Git", gitHead],
    ["변경 파일", dirty === 0 ? "깨끗함" : `${dirty}개`],
    ["세션", activeSession],
    ["열린 작업", `${openTasks}개`],
    ["파일 잠금", `${locks}개`],
    ["gdx1", gdx.ssh === "ok" ? "SSH 정상" : translate(gdx.ssh || "unknown")],
    ["AI 도구", `${availableAdapters}/${adapters.length}`],
    ["워커", `${activeWorkers}/${workers.length}`],
    ["Studio", runtime.containerized ? "Docker" : "local"],
    ["Game", game.total ? `${game.passed}/${game.total}` : "대기"],
    ["모델 추천", `${modelSummary.verified ?? 0}/${modelSummary.total ?? 0}`],
    ["AgentOS 흡수", `${absorptionSummary.absorbed ?? 0}/${absorptionSummary.patterns ?? 0}`],
  ];

  $("#stats").innerHTML = stats.map(([label, value]) => `
    <div class="stat">
      <span>${esc(label)}</span>
      <strong>${esc(value)}</strong>
    </div>
  `).join("");

  const workerState = $("#workerFleetState");
  if (workerState) {
    workerState.textContent = `${activeWorkers}/${workers.length} 활성`;
    workerState.className = `tag ${activeWorkers ? "good" : "warn"}`;
  }
}

function renderOrchestration() {
  const activity = liveActivity || recentActivity;
  const companyState = state.company?.state || {};
  const tasks = state.company?.tasks || [];
  const openTasks = state.company?.openTasks || [];
  const hideLatestDuringWorkflow = isPendingWorkflowActivity();
  const focusTask = hideLatestDuringWorkflow ? null : taskById(activity?.taskId) || latestTask(openTasks) || latestTask(tasks);
  const agentId = focusTask ? taskAgent(focusTask) : "chief_orchestrator";
  const reviewerId = focusTask ? (focusTask.suggested_reviewer || "critic_reviewer") : "";
  const agentTool = activity?.tool || focusTask?.last_tool || toolForAgent(agentId);
  const evidenceCount = focusTask?.evidence?.length || 0;
  const commandBadge = activity ? translate(activity.status) : "대기";
  const commandTone = activity?.status === "running" ? "warn" : activity?.status === "failed" ? "bad" : "good";

  $("#orchestrationState").textContent = activity
    ? `${commandText[activity.command] || activity.command} · ${commandBadge}`
    : `${openTasks.length}개 열린 작업`;
  $("#orchestrationState").className = `tag ${commandTone}`;

  const stages = [
    {
      title: "명령 접수",
      main: activity ? (commandText[activity.command] || activity.command) : "대기 중",
      meta: activity ? activityMeta(activity) : "버튼 실행이나 작업 주문을 기다립니다.",
      badge: commandBadge,
      tone: commandTone,
    },
    {
      title: "오케스트레이터",
      main: "chief_orchestrator",
      meta: liveActivity?.command === "orchestrator.run" ? "요청을 분석하고 협업 대상을 준비합니다." : companyState.current_orchestrator_task || companyState.active_session || "작업 분해와 배정을 관리합니다.",
      badge: liveActivity?.command === "orchestrator.run" ? "협업 대기" : companyState.active_session ? "세션 중" : "대기",
      tone: liveActivity?.command === "orchestrator.run" || companyState.active_session ? "warn" : "good",
    },
    {
      title: "작업 주문",
      main: focusTask?.id || (liveActivity?.command === "orchestrator.run" ? "생성 중" : "작업 없음"),
      meta: focusTask?.request || (liveActivity?.command === "orchestrator.run" ? liveActivity.request || "요청을 작업 주문으로 변환 중입니다." : "작업 요청이 생성되면 여기에 표시됩니다."),
      badge: translate(focusTask?.status || "none"),
      tone: liveActivity?.command === "orchestrator.run" && !focusTask ? "warn" : toneForStatus(focusTask?.status),
    },
    {
      title: "담당 에이전트",
      main: focusTask ? agentId : "에이전트 배정 대기",
      meta: focusTask ? `도구 ${agentTool || "역할 기본값"} · ${agentFocus(agentId)}` : "오케스트레이터가 역할과 도구를 고르는 중입니다.",
      badge: focusTask ? translate(focusTask?.agent_status || "pending") : "협업 대기",
      tone: focusTask ? toneForStatus(focusTask?.agent_status) : "warn",
    },
    {
      title: "완료 처리",
      main: focusTask ? reviewerId || "체크포인트 대기" : "리뷰 대기",
      meta: focusTask ? `체크포인트 ${evidenceCount || (focusTask?.last_agent_run ? 1 : 0)}개 · 보고 ${focusTask?.last_agent_run || focusTask?.report || "없음"}` : "작업 생성 후 리뷰 체크포인트와 완료 처리를 이어갑니다.",
      badge: focusTask ? evidenceCount > 0 || focusTask?.last_agent_run ? "완료 가능" : "대기" : "대기",
      tone: focusTask ? evidenceCount > 0 || focusTask?.last_agent_run ? "good" : "warn" : "warn",
    },
  ];

  $("#orchestrationFlow").innerHTML = stages.map((stage, index) => [
    flowStage(stage),
    index < stages.length - 1 ? `<div class="flow-arrow" aria-hidden="true">></div>` : "",
  ].join("")).join("");

  renderAgentLanes(tasks);
  renderCollaborationLinks(tasks);
}

function renderAgentOSAbsorption() {
  const matrix = state.agentosAbsorption || {};
  const summary = matrix.summary || {};
  const patterns = matrix.patterns || [];
  const queue = matrix.next_build_queue || [];
  const sources = matrix.source_groups || [];
  const stateNode = $("#agentosAbsorptionState");
  if (!stateNode) return;

  const absorbed = Number(summary.absorbed ?? patterns.filter((item) => item.studio_status === "absorbed").length);
  const total = Number(summary.patterns ?? patterns.length);
  stateNode.textContent = `${absorbed}/${total} 흡수`;
  stateNode.className = `tag ${absorbed >= total && total > 0 ? "good" : "warn"}`;

  $("#agentosAbsorptionSummary").innerHTML = `
    <div>
      <span>연구 출처</span>
      <strong>${esc(summary.sources_reviewed || sources.length)}개</strong>
      <small>${esc(matrix.updated_at || "날짜 없음")} 기준</small>
    </div>
    <div>
      <span>흡수 상태</span>
      <strong>${esc(absorbed)} absorbed · ${esc(summary.partial || 0)} partial</strong>
      <small>${esc(summary.focus || "AgentOS 패턴을 Studio로 이전")}</small>
    </div>
    <div>
      <span>다음 작업</span>
      <strong>${esc(summary.next || queue.length)}개 큐</strong>
      <small>${esc(queue[0]?.title || "대기 중")}</small>
    </div>
  `;

  $("#agentosPatternList").innerHTML = patterns.map((pattern) => `
    <div class="absorption-card ${esc(toneForAbsorption(pattern.studio_status))}">
      <div>
        <strong>${esc(pattern.label || pattern.id)}</strong>
        <span>${esc(pattern.evidence || "")}</span>
        <small>${esc(pattern.studio_mapping || "")}</small>
      </div>
      <em>${esc(translateAbsorption(pattern.studio_status))}</em>
      <p>${esc(pattern.next_action || "")}</p>
    </div>
  `).join("") || empty("AgentOS 흡수 패턴이 없습니다.");

  $("#agentosQueueList").innerHTML = queue.map((item) => `
    <div class="absorption-card queue ${esc(priorityTone(item.priority))}">
      <div>
        <strong>${esc(item.id || "")} · ${esc(item.title || "")}</strong>
        <span>${esc(item.expected_result || "")}</span>
      </div>
      <em>${esc(item.priority || "P?")}</em>
    </div>
  `).join("") || empty("다음 구현 큐가 없습니다.");

  $("#agentosSourceCount").textContent = `source ${sources.length}`;
  $("#agentosVisualRules").innerHTML = (matrix.visual_rules || []).map((rule) => `
    <span>${esc(rule)}</span>
  `).join("") || empty("비주얼 규칙이 없습니다.");
}

function flowStage(stage) {
  return `
    <div class="flow-stage ${esc(stage.tone)}">
      <span>${esc(stage.title)}</span>
      <strong>${esc(stage.main)}</strong>
      <p>${esc(stage.meta)}</p>
      <em>${esc(stage.badge)}</em>
    </div>
  `;
}

function renderAgentLanes(tasks) {
  if (isPendingWorkflowActivity()) {
    $("#agentLanes").innerHTML = `
      <div class="agent-lane warn">
        <div>
          <strong>chief_orchestrator</strong>
          <span>routing</span>
        </div>
        <p>요청을 작업 주문으로 나누고 필요한 에이전트에게 넘길 준비를 하고 있습니다.</p>
        <div class="lane-chips"><span>협업 대기</span><span>작업 생성 중</span></div>
        <small>협업: agent_team, critic_reviewer</small>
      </div>
    `;
    return;
  }

  const agents = state.company?.agents || [];
  const openTasks = tasks.filter((task) => !["closed", "closed_blocked"].includes(task.status));
  const grouped = new Map();

  for (const task of openTasks) {
    const agentId = taskAgent(task);
    if (!grouped.has(agentId)) grouped.set(agentId, []);
    grouped.get(agentId).push(task);
  }

  const activeAgentIds = new Set([
    "chief_orchestrator",
    ...grouped.keys(),
    ...(liveActivity?.taskId ? [taskAgent(taskById(liveActivity.taskId) || {})] : []),
  ]);
  const visibleAgents = agents
    .filter((agent) => activeAgentIds.has(agent.id))
    .slice(0, 8);

  $("#agentLanes").innerHTML = visibleAgents.map((agent) => {
    const assigned = grouped.get(agent.id) || [];
    const collaborators = collaboratorsFor(agent.id, assigned);
    const latest = latestTask(assigned);
    const status = liveActivity && latest?.id === liveActivity.taskId ? liveActivity.status : latest?.agent_status || latest?.status || "pending";
    return `
      <div class="agent-lane ${esc(toneForStatus(status))}">
        <div>
          <strong>${esc(agent.id)}</strong>
          <span>${esc(toolForAgent(agent.id))}</span>
        </div>
        <p>${esc(agent.goal_setting?.focus || agent.profile || "역할 설명 없음")}</p>
        <div class="lane-chips">
          ${assigned.slice(0, 3).map((task) => `<span>${esc(task.id)} · ${esc(translate(task.status))}</span>`).join("") || "<span>대기</span>"}
        </div>
        <small>${esc(collaborators.length ? `협업: ${collaborators.join(", ")}` : "협업 대기")}</small>
      </div>
    `;
  }).join("") || empty("표시할 에이전트 임무가 없습니다.");
}

function renderCollaborationLinks(tasks) {
  if (isPendingWorkflowActivity()) {
    $("#collaborationLinks").innerHTML = [
      ["chief_orchestrator", "agent_team", "작업 배정 대기", "pending"],
      ["agent_team", "critic_reviewer", "리뷰 대기", "pending"],
      ["critic_reviewer", "completion", "완료 대기", "pending"],
    ].map(([from, to, label, taskId]) => `
      <div class="link-row">
        <span>${esc(from)}</span>
        <strong>${esc(label)}</strong>
        <span>${esc(to)}</span>
        <small>${esc(taskId)}</small>
      </div>
    `).join("");
    return;
  }

  const links = [];
  const ordered = [...tasks]
    .filter((task) => !["closed", "closed_blocked"].includes(task.status))
    .sort((a, b) => Date.parse(b.updated_at || b.created_at || 0) - Date.parse(a.updated_at || a.created_at || 0))
    .slice(0, 8);

  for (const task of ordered) {
    const agentId = taskAgent(task);
    const reviewerId = task.suggested_reviewer || "critic_reviewer";
    links.push(["chief_orchestrator", agentId, "작업 배정", task.id]);
    if (task.status === "needs_review" || (task.agent_runs || []).some((run) => run.mode === "review")) {
      links.push([agentId, reviewerId, "리뷰 요청", task.id]);
    }
    if ((task.evidence || []).length > 0 || task.last_agent_run) {
      links.push([agentId, "evidence_board", "증거 기록", task.id]);
    }
  }

  $("#collaborationLinks").innerHTML = links.slice(0, 10).map(([from, to, label, taskId]) => `
    <div class="link-row">
      <span>${esc(from)}</span>
      <strong>${esc(label)}</strong>
      <span>${esc(to)}</span>
      <small>${esc(taskId)}</small>
    </div>
  `).join("") || empty("아직 표시할 협업 링크가 없습니다.");
}

function renderSession() {
  const activeSession = state.company?.state?.active_session;
  $("#sessionState").textContent = activeSession ? "진행 중" : "대기 중";
}

function renderAdapters() {
  const tools = state.adapters?.tools || {};
  const names = Object.keys(tools).sort();
  const summary = state.adapters?.summary || {};
  $("#adapterCount").textContent = `${summary.available ?? names.length}/${summary.total ?? names.length} 정상`;
  $("#agentTool").innerHTML = [
    `<option value="">역할 기본값</option>`,
    ...names.map((name) => {
      const tool = tools[name];
      const disabled = tool.status !== "available" ? "disabled" : "";
      const label = `${name} · ${translate(tool.status || "missing")}`;
      return `<option value="${esc(name)}" ${disabled}>${esc(label)}</option>`;
    }),
  ].join("");
  const cards = names.map((name) => adapterCard(name, tools[name])).join("");
  const excluded = Object.entries(state.adapters?.excludedTools || {}).map(([name, tool]) => adapterExcludedCard(name, tool)).join("");
  $("#adaptersList").innerHTML = cards || empty("등록된 어댑터가 없습니다.");
  const excludedNode = $("#excludedAdaptersList");
  if (excludedNode) {
    excludedNode.innerHTML = excluded || empty("제외된 어댑터가 없습니다.");
  }
}

function adapterCard(name, tool) {
  const status = tool.status || (tool.enabled ? (tool.available ? "available" : "missing") : "disabled");
  const roles = Array.isArray(tool.defaultRoles) ? tool.defaultRoles : [];
  const rolesText = roles.length ? roles.join(", ") : "역할 기본값 없음";
  const version = tool.version || "버전 미확인";
  const lastError = tool.lastError || tool.disabledReason || "문제 없음";
  const executor = translateExecutor(tool.primaryExecutor || tool.execution || "cli");
  const sdkText = tool.sdkPackage
    ? `${tool.sdkPackage} · ${translate(tool.sdkStatus || "missing")}${tool.sdkVersion ? ` · ${tool.sdkVersion}` : ""}`
    : "사용 안 함";
  return `
    <div class="adapter-card ${esc(toneForStatus(status))}">
      <div class="adapter-card-head">
        <div>
          <strong>${esc(name)}</strong>
          <span>${esc(tool.description || "설명 없음")}</span>
        </div>
        <em>${esc(translate(status))}</em>
      </div>
      <div class="adapter-fields">
        <p><b>실행 파일</b>${esc(tool.executable || "없음")}</p>
        <p><b>실행 방식</b>${esc(executor)}</p>
        <p><b>Codex SDK</b>${esc(sdkText)}</p>
        <p><b>실제 경로</b>${esc(tool.resolvedPath || "찾지 못함")}</p>
        <p><b>버전</b>${esc(version)}</p>
        <p><b>기본 역할</b>${esc(rolesText)}</p>
        <p><b>마지막 점검</b>${esc(formatDate(tool.lastCheck) || "없음")}</p>
        <p><b>제한 시간</b>${esc(tool.timeoutSeconds ? `${tool.timeoutSeconds}s` : "미설정")}</p>
      </div>
      <div class="adapter-error ${lastError === "문제 없음" ? "good" : "bad"}">${esc(lastError)}</div>
    </div>
  `;
}

function adapterExcludedCard(name, tool) {
  return `
    <div class="adapter-card bad">
      <div class="adapter-card-head">
        <div>
          <strong>${esc(name)}</strong>
          <span>${esc(tool.disabled_reason || "사용하지 않도록 제외됨")}</span>
        </div>
        <em>${esc(translate(tool.status || "disabled"))}</em>
      </div>
    </div>
  `;
}

function renderAgents() {
  const agents = state.company?.agents || [];
  $("#agentCount").textContent = `${agents.length}명`;
  $("#agentsList").innerHTML = agents.map((agent) => {
    const setting = agent.goal_setting || {};
    const scopeCount = Array.isArray(setting.default_scope) ? setting.default_scope.length : 0;
    const outputCount = Array.isArray(setting.required_outputs) ? setting.required_outputs.length : 0;
    const permission = agent.writes_by_default ? "기본 쓰기" : "요청 시 쓰기";
    const tool = setting.tool || "역할 기본값";
    const scopes = Array.isArray(setting.default_scope) ? setting.default_scope.slice(0, 3) : [];
    const outputs = Array.isArray(setting.required_outputs) ? setting.required_outputs.slice(0, 3) : [];
    return `
      <div class="agent-stack-card ${agent.writes_by_default ? "warn" : "good"}">
        <div class="agent-stack-head">
          <strong>${esc(agent.id)}</strong>
          <span>${esc(tool)}</span>
        </div>
        <p>${esc(setting.focus || agent.profile || "역할 설명 없음")}</p>
        <div class="agent-stack-grid">
          <small>${esc(permission)}</small>
          <small>범위 ${scopeCount}</small>
          <small>산출물 ${outputCount}</small>
        </div>
        <div class="agent-stack-chips">
          ${scopes.map((scope) => `<span>${esc(scope)}</span>`).join("")}
          ${outputs.map((output) => `<span>${esc(output)}</span>`).join("")}
        </div>
      </div>
    `;
  }).join("") || empty("등록된 에이전트가 없습니다.");
}

function renderTasks() {
  const tasks = state.company?.tasks || [];
  const openTasks = state.company?.openTasks || [];
  $("#taskCount").textContent = `열림 ${openTasks.length} / 전체 ${tasks.length}`;

  const ordered = [...tasks].sort((a, b) => taskWeight(a) - taskWeight(b));
  $("#tasksList").innerHTML = ordered.slice(0, 10).map((task) => {
    const agent = task.assigned_agent || task.suggested_agent || "미배정";
    const evidence = task.evidence?.length || 0;
    const lastRun = task.agent_status ? `최근 ${translate(task.agent_status)}${task.last_tool ? `(${task.last_tool})` : ""}` : "";
    const meta = [task.id, `담당 ${agent}`, `증거 ${evidence}개`, lastRun].filter(Boolean).join(" · ");
    const tone = task.status === "closed" ? "good" : task.status === "closed_blocked" ? "bad" : "warn";
    return taskItem(task, task.request || task.id, task.required_evidence || "필요 증거 없음", meta, translate(task.status), tone);
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
  $("#feedbackList").innerHTML = feedback.map((note) => {
    const tone = note.status === "closed" ? "good" : "warn";
    const frameButton = note.frame && note.frame !== "TBD" ? `<button type="button" data-file-path="${esc(note.frame)}">Frame</button>` : "";
    const screenshotButton = note.screenshot && note.screenshot !== "TBD" ? `<button type="button" data-file-path="${esc(note.screenshot)}">Capture</button>` : "";
    return `
      <div class="feedback-card ${tone}">
        <div class="feedback-head">
          <strong>${esc(note.id)}</strong>
          <span class="pill ${tone}">${esc(translate(note.status || "pending"))}</span>
        </div>
        <p>${esc(note.request || "요청 변경 사항 미입력")}</p>
        <div class="feedback-grid">
          <small>Scene ${esc(note.scene || "TBD")}</small>
          <small>Run ${esc(note.run || "TBD")}</small>
          <small>Action ${esc(note.action || "TBD")}</small>
        </div>
        <div class="feedback-actions">
          <button type="button" data-file-path="${esc(note.path)}">Note</button>
          ${frameButton}
          ${screenshotButton}
          <button type="button" data-command-name="feedback.process" data-feedback-path="${esc(note.path)}">처리</button>
        </div>
      </div>
    `;
  }).join("") || empty("등록된 피드백이 없습니다.");
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

function renderAssetForge() {
  const stateNode = $("#assetForgeState");
  if (!stateNode) return;
  const forge = state.assetForge || {};
  const jobs = forge.jobs || [];
  const stages = forge.stages || [];
  stateNode.textContent = jobs.length ? `${jobs.length}개 job` : "대기";
  stateNode.className = `tag ${jobs.length ? "good" : "warn"}`;
  $("#assetForgeStageList").innerHTML = stages.map((stage) => `<span>${esc(forgeStageLabel(stage))}</span>`).join("") || empty("Forge 단계 없음");
  $("#assetForgeJobList").innerHTML = jobs.map((job) => {
    const stageLine = (job.pipeline || [])
      .map((step) => `${forgeStageLabel(step.stage)}:${translate(step.status || "pending")}`)
      .join(" · ");
    return `
      <button type="button" class="forge-job-card" data-memory-path="${esc(job.path || "")}">
        <span>${esc(forgeKindLabel(job.kind || "prop"))} · ${esc(translate(job.status || "pending"))}</span>
        <strong>${esc(job.asset_id || "asset")}</strong>
        <small>${esc(stageLine || "파이프라인 없음")}</small>
      </button>
    `;
  }).join("") || empty("생성된 Forge job이 없습니다.");

  const image3d = state.imageToBlender || {};
  const imageJobs = image3d.jobs || [];
  const imageList = $("#imageToBlenderJobList");
  if (imageList) {
    imageList.innerHTML = imageJobs.map((job) => {
      const stageLine = (job.pipeline || [])
        .map((step) => `${forgeStageLabel(step.stage)}:${translate(step.status || "pending")}`)
        .join(" · ");
      return `
        <button type="button" class="forge-job-card image3d-job-card" data-memory-path="${esc(job.path || "")}">
          <span>${esc(job.provider || "image3d")} · ${esc(translate(job.status || "pending"))}</span>
          <strong>${esc(job.asset_id || "asset")}</strong>
          <small>${esc(stageLine || "이미지→3D 파이프라인 없음")}</small>
        </button>
      `;
    }).join("") || empty("생성된 Image→Blender job이 없습니다.");
  }
}

function forgeKindLabel(kind) {
  return {
    zone: "지역/맵",
    background: "배경",
    prop: "오브젝트",
    character: "캐릭터",
  }[kind] || kind;
}

function forgeStageLabel(stage) {
  return {
    concept: "콘셉트",
    concept_image: "콘셉트 이미지",
    image_generation: "이미지",
    image_to_3d: "이미지→3D",
    part_schema: "파트 설계",
    cubepart: "CubePart",
    blender_cleanup: "Blender",
    unity_import: "Unity",
    gameplay_binding: "게임플레이",
    scene_binding: "씬 연결",
    qa: "검증",
  }[stage] || stage;
}

function renderWorkers() {
  const node = $("#workerFleetList");
  if (!node) return;
  const fleet = state.workers || {};
  const workers = fleet.workers || [];
  const updated = fleet.updated_at ? `갱신 ${formatDate(fleet.updated_at)}` : "아직 probe 없음";
  $("#workerFleetState").textContent = updated;
  $("#workerFleetState").className = `tag ${workers.some((worker) => worker.enabled) ? "good" : "warn"}`;
  node.innerHTML = workers.map((worker) => workerCard(worker)).join("") || empty("등록된 worker가 없습니다.");
}

function workerCard(worker) {
  const probe = worker.last_probe || {};
  const hardware = worker.hardware || {};
  const caps = (worker.capabilities || []).slice(0, 6).map((capability) => `<span>${esc(capability)}</span>`).join("");
  const jobs = (worker.recommended_jobs || []).slice(0, 5).map((job) => `<span>${esc(commandText[job] || job)}</span>`).join("");
  const details = [
    hardware.machine || hardware.host || hardware.executable || "",
    hardware.chip || hardware.remote || hardware.version || "",
    hardware.ram_gb ? `${hardware.ram_gb}GB RAM` : "",
    hardware.gpu ? `${hardware.gpu}${hardware.gpu_cores ? ` · ${hardware.gpu_cores} cores` : ""}` : "",
    hardware.backend || hardware.ssh || "",
  ].filter(Boolean).join(" · ");
  return `
    <div class="worker-card ${esc(toneForStatus(worker.status))}">
      <div class="worker-card-head">
        <div>
          <strong>${esc(worker.label || worker.id)}</strong>
          <span>${esc(worker.id)} · ${esc(worker.kind || "worker")}</span>
        </div>
        <em>${esc(worker.enabled ? translate(worker.status) : `비활성 · ${translate(worker.status)}`)}</em>
      </div>
      <p>${esc(details || "하드웨어 정보 없음")}</p>
      <div class="worker-chip-row">${caps || "<span>capability 없음</span>"}</div>
      <div class="worker-job-row">${jobs || "<span>추천 작업 없음</span>"}</div>
      <small>${esc(probe.checked_at ? `${formatDate(probe.checked_at)} · ${probe.summary || ""}` : "아직 probe 기록 없음")}</small>
    </div>
  `;
}

function renderRuntime() {
  const node = $("#runtimeSummary");
  if (!node) return;
  const runtime = state.runtime || {};
  const runner = runtime.hostRunner || {};
  const socketMounted = Boolean(runtime.dockerSocketMounted);
  const runnerStatus = runner.status || (runtime.executionMode === "host_runner" ? "pending" : "local");
  const stateNode = $("#runtimeState");
  stateNode.textContent = runtime.containerized ? `Docker · ${translateRuntime(runnerStatus)}` : `Local · ${translateRuntime(runnerStatus)}`;
  stateNode.className = `tag ${socketMounted ? "bad" : runnerStatus === "available" || runnerStatus === "local" ? "good" : "warn"}`;
  node.innerHTML = [
    runtimeCard(
      "Studio",
      runtime.containerized ? "Docker 컨테이너" : "로컬 프로세스",
      runtime.executionMode === "host_runner" ? "명령은 host-runner로 전달됩니다." : "명령은 현재 Studio 프로세스에서 실행됩니다.",
      runtime.containerized ? "good" : "warn"
    ),
    runtimeCard(
      "Host Runner",
      translateRuntime(runnerStatus),
      runner.message || runner.url || "host-runner 설정 없음",
      runnerStatus === "available" || runnerStatus === "local" ? "good" : "warn"
    ),
    runtimeCard(
      "Token",
      runner.tokenConfigured ? "설정됨" : "없음",
      runner.tokenFile || "token file 없음",
      runner.tokenConfigured ? "good" : "bad"
    ),
    runtimeCard(
      "Docker Socket",
      socketMounted ? "마운트됨" : "차단됨",
      runtime.security?.dockerSocketPolicy || "forbidden",
      socketMounted ? "bad" : "good"
    ),
  ].join("");
}

function runtimeCard(label, value, detail, tone) {
  return `
    <div class="runtime-card ${esc(tone || "")}">
      <span>${esc(label)}</span>
      <strong>${esc(value)}</strong>
      <small>${esc(detail || "")}</small>
    </div>
  `;
}

function renderModelCookbook() {
  const node = $("#modelCookbookList");
  if (!node) return;
  const cookbook = state.modelCookbook || {};
  const summary = cookbook.summary || {};
  const hardware = cookbook.hardware_profile || {};
  const gdx = cookbook.gdx1_probe || {};
  const useCases = cookbook.use_cases || [];
  const stateNode = $("#modelCookbookState");
  stateNode.textContent = `${summary.verified ?? 0}/${summary.total ?? useCases.length} 검증`;
  stateNode.className = `tag ${(summary.verified || 0) === (summary.total || useCases.length) ? "good" : "warn"}`;
  $("#modelCookbookSummary").innerHTML = `
    <div>
      <span>Mac Studio</span>
      <strong>${esc(hardware.chip || "Apple Silicon")} · ${esc(hardware.ram_gb || "64")}GB · ${esc(hardware.backend || "Metal")}</strong>
      <small>GPU budget ${esc(hardware.gpu_budget_gb || "48")}GB · ${esc(hardware.gpu || "GPU 미확인")}</small>
    </div>
    <div>
      <span>gdx1</span>
      <strong>${esc(gdx.enabled ? "사용 가능" : "사용 불가")} · ${esc(translate(gdx.status || "unknown"))}</strong>
      <small>${esc(gdx.last_probe?.summary || "probe 기록 없음")}</small>
    </div>
    <div>
      <span>검증</span>
      <strong>${esc(summary.verified ?? 0)} verified</strong>
      <small>pending ${esc(summary.model_pending ?? 0)} · blocked ${esc(summary.blocked ?? 0)} · missing ${esc(summary.runtime_missing ?? 0)}</small>
    </div>
  `;
  node.innerHTML = useCases.map((row) => modelUseCaseCard(row)).join("") || empty("등록된 model cookbook use case가 없습니다.");
}

function modelUseCaseCard(row) {
  const primary = row.primary || {};
  const fallback = row.fallback || {};
  return `
    <div class="model-card ${esc(toneForModelStatus(row.verification_status))}">
      <div class="model-card-head">
        <div>
          <strong>${esc(row.label || row.use_case)}</strong>
          <span>${esc(row.use_case || "")}</span>
        </div>
        <em>${esc(translateModelStatus(row.verification_status))}</em>
      </div>
      <div class="model-route-grid">
        ${modelRoute("Primary", primary)}
        ${modelRoute("Fallback", fallback)}
      </div>
      <p>${esc(row.reason || "")}</p>
    </div>
  `;
}

function modelRoute(label, route) {
  return `
    <div class="model-route">
      <span>${esc(label)}</span>
      <strong>${esc(route.runtime || "runtime 없음")} · ${esc(route.worker || "worker 없음")}</strong>
      <small>${esc(route.model || "model 없음")}</small>
      <em>${esc(translateModelStatus(route.verification_status))}${route.version ? ` · ${esc(route.version)}` : ""}</em>
    </div>
  `;
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

function taskItem(task, title, body, meta, badge = "", tone = "") {
  const closed = task.status === "closed" || task.status === "closed_blocked";
  const badgeHtml = badge ? `<span class="pill ${esc(tone)}">${esc(badge)}</span>` : "";
  const answerPath = taskAnswerPath(task);
  const runPath = answerPath ? `<small class="task-run-path">답변: ${esc(answerPath)}</small>` : "";
  const nextAction = taskNextAction(task);
  const nextReason = task.productionCard?.nextAction?.reason || "";
  const answerButton = answerPath ? `<button class="answer-action" data-task-action="answer" data-task-id="${esc(task.id)}">답변 보기</button>` : "";
  const nextButton = closed || !nextAction ? "" : `
    <button class="primary-action" data-task-action="${esc(nextAction.action)}" data-task-id="${esc(task.id)}">${esc(nextAction.label)}</button>
  `;
  const actions = `
    <div class="task-actions">
      ${answerButton}
      <button data-task-action="select" data-task-id="${esc(task.id)}">상세</button>
      ${nextButton}
    </div>
  `;
  return `
    <div class="list-item task-item">
      <div class="item-main">
        <strong>${esc(title || "제목 없음")}</strong>
        <span>${esc(body || "")}</span>
        <small>${esc(meta || "")}</small>
        ${nextReason ? `<small class="task-next-reason">다음 조치: ${esc(nextReason)}</small>` : ""}
      </div>
      <div class="item-side">
        ${badgeHtml}
        <small class="task-live-status" aria-live="polite"></small>
        ${runPath}
        ${actions}
      </div>
    </div>
  `;
}

function empty(message) {
  return `<div class="list-item empty">${esc(message)}</div>`;
}

async function runCommand(command, payload = {}) {
  const label = commandText[command] || command;
  const activity = beginActivity(command, payload);
  $("#console").textContent = `실행 중: ${label}`;

  try {
    const result = await api("/api/command", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ command, payload }),
    });
    if (result.jobId) {
      activeJobId = result.jobId;
      activity.jobId = result.jobId;
      activity.status = result.status || "queued";
      $("#console").textContent = [
        `${label} 작업을 시작했습니다.`,
        `Job: ${result.jobId}`,
        Array.isArray(result.command) ? `$ ${result.command.join(" ")}` : "",
      ].filter(Boolean).join("\n");
      if (state) {
        state.jobs = [minimalJobFromResult(command, result), ...(state.jobs || [])].filter(Boolean);
        renderCommandCenter();
        renderConversationStream();
        renderJobLedger();
        renderTaskTracker();
        renderOrchestration();
        renderInspector();
      }
      startJobPolling(result.jobId, activity);
      return;
    }
    const commandLine = Array.isArray(result.command) ? result.command.join(" ") : "";
    $("#console").textContent = [
      commandLine ? `$ ${commandLine}` : label,
      result.stdout || "(표준 출력 없음)",
      result.stderr ? `\n[stderr]\n${result.stderr}` : "",
    ].join("\n").trim();
    await keepActivityVisible(activity);
    finishActivity(activity, result.ok ? "ok" : "failed", result.stdout || result.stderr || "");
    await loadState();
  } catch (error) {
    await keepActivityVisible(activity);
    finishActivity(activity, "failed", error.message);
    $("#console").textContent = `오류: ${error.message}`;
  }
}

function minimalJobFromResult(command, result) {
  if (!result.jobId) return null;
  return {
    id: result.jobId,
    commandName: command,
    command: result.command || [],
    status: result.status || "queued",
    createdAt: new Date().toISOString(),
    updatedAt: new Date().toISOString(),
    events: [
      {
        time: new Date().toISOString(),
        type: "queued",
        message: "Studio에서 작업 시작을 접수했습니다.",
      },
    ],
  };
}

function startJobPolling(jobId, activity) {
  if (jobPollTimer) clearInterval(jobPollTimer);
  pollJob(jobId, activity);
  jobPollTimer = setInterval(() => pollJob(jobId, activity), 900);
}

async function pollJob(jobId, activity) {
  if (!jobId) return;
  try {
    const data = await api(`/api/jobs/${encodeURIComponent(jobId)}`);
    const job = data.job;
    mergeJob(job);
    updateActivityFromJob(activity, job);
    renderCommandCenter();
    renderConversationStream();
    renderJobLedger();
    renderTaskTracker();
    renderOrchestration();
    renderInspector();
    renderConsoleForJob(job);
    if (job.isTerminal) {
      if (jobPollTimer) clearInterval(jobPollTimer);
      jobPollTimer = null;
      activeJobId = "";
      if (job.taskId) {
        selectedTaskId = job.taskId;
        selectedArtifactPath = "";
      }
      await keepActivityVisible(activity);
      finishActivity(activity, job.ok ? "ok" : job.status, job.receipt?.summary || "");
      await loadState();
    }
  } catch (error) {
    if (jobPollTimer) clearInterval(jobPollTimer);
    jobPollTimer = null;
    finishActivity(activity, "failed", error.message);
    $("#console").textContent = `작업 상태 조회 오류: ${error.message}`;
  }
}

function mergeJob(job) {
  if (!job || !state) return;
  const jobs = state.jobs || [];
  const index = jobs.findIndex((item) => item.id === job.id);
  if (index >= 0) jobs[index] = job;
  else jobs.unshift(job);
  state.jobs = jobs
    .sort((a, b) => Date.parse(b.updatedAt || b.createdAt || 0) - Date.parse(a.updatedAt || a.createdAt || 0))
    .slice(0, 12);
}

function updateActivityFromJob(activity, job) {
  if (!activity || !job || liveActivity?.id !== activity.id) return;
  activity.status = job.status || activity.status;
  activity.jobId = job.id || activity.jobId;
  if (job.taskId) activity.taskId = job.taskId;
}

function renderConsoleForJob(job) {
  const events = (job.events || []).slice(-8);
  const commandLine = Array.isArray(job.command) ? job.command.join(" ") : "";
  $("#console").textContent = [
    `${translate(job.status)} · ${job.id}`,
    commandLine ? `$ ${commandLine}` : "",
    ...events.map((event) => `${formatDate(event.time)} [${event.type}] ${event.message}`),
    job.receipt?.path ? `\nReceipt: ${job.receipt.path}` : "",
    job.stderr && job.isTerminal ? `\n[stderr]\n${job.stderr}` : "",
  ].join("\n").trim();
}

function beginActivity(command, payload = {}) {
  const activity = {
    id: `${Date.now()}-${Math.random().toString(16).slice(2)}`,
    command,
    taskId: payload.taskId || "",
    tool: payload.tool || "",
    mode: command.endsWith(".review") ? "review" : command.endsWith(".run") ? "run" : "",
    request: payload.request || "",
    status: "running",
    startedAt: new Date().toISOString(),
    startedMs: Date.now(),
  };
  liveActivity = activity;
  if (state) {
    renderCommandCenter();
    renderConversationStream();
    renderTaskTracker();
    renderOrchestration();
    renderInspector();
  }
  return activity;
}

function finishActivity(activity, status, detail = "") {
  if (!activity || liveActivity?.id !== activity.id) return;
  recentActivity = {
    ...activity,
    status,
    detail,
    endedAt: new Date().toISOString(),
  };
  liveActivity = null;
  if (state) {
    renderCommandCenter();
    renderConversationStream();
    renderTaskTracker();
    renderOrchestration();
    renderInspector();
  }
}

function isPendingWorkflowActivity() {
  return liveActivity?.command === "orchestrator.run" && (!liveActivity.taskId || !taskById(liveActivity.taskId));
}

async function keepActivityVisible(activity) {
  if (!activity || activity.command !== "orchestrator.run") return;
  const elapsed = Date.now() - (activity.startedMs || Date.now());
  const remaining = ORCHESTRATOR_MIN_VISIBLE_MS - elapsed;
  if (remaining > 0) {
    await delay(remaining);
  }
}

function delay(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
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

async function runSearch(rebuild = false) {
  const query = $("#searchQuery").value.trim();
  if (!query) {
    $("#searchSummary").textContent = "검색어를 입력하세요.";
    $("#searchQuery").focus();
    return;
  }
  searchState = { query, loading: true };
  renderSearch();
  try {
    searchState = await api(`/api/search?q=${encodeURIComponent(query)}&limit=18&rebuild=${rebuild ? "1" : "0"}`);
  } catch (error) {
    searchState = { query, loading: false, count: 0, results: [] };
    $("#searchSummary").textContent = `검색 오류: ${error.message}`;
  }
  renderSearch();
}

function setStudioView(view, options = {}) {
  if (!studioViews[view]) view = "focus";
  activeStudioView = view;
  localStorage.setItem("channelPlayStudioView", view);
  applyStudioView(view);
  if (options.target) {
    requestAnimationFrame(() => {
      document.querySelector(options.target)?.scrollIntoView({ behavior: "smooth", block: "start" });
    });
  }
}

function applyStudioView(view) {
  if (!studioViews[view]) view = "focus";
  document.body.dataset.currentStudioView = view;
  document.querySelectorAll("[data-studio-view]").forEach((section) => {
    const views = String(section.dataset.studioView || "").split(/\s+/).filter(Boolean);
    section.hidden = !views.includes(view);
  });
  document.querySelectorAll("[data-studio-view-button]").forEach((button) => {
    const active = button.dataset.studioViewButton === view;
    button.classList.toggle("active", active);
    button.setAttribute("aria-selected", active ? "true" : "false");
  });
  document.querySelectorAll("[data-studio-nav]").forEach((link) => {
    link.classList.toggle("active", link.dataset.studioNav === view);
  });
  const inspectorMode = $("#inspectorMode");
  if (inspectorMode) {
    inspectorMode.textContent = studioViews[view] || "미션";
  }
}

function viewForHash(hash) {
  const id = String(hash || "").replace(/^#/, "");
  const target = id ? document.getElementById(id) : null;
  const section = target?.closest("[data-studio-view]");
  return section?.dataset.studioView?.split(/\s+/)[0] || "";
}

function bind() {
  document.querySelectorAll("[data-studio-view-button]").forEach((button) => {
    button.addEventListener("click", () => setStudioView(button.dataset.studioViewButton || "focus"));
  });
  document.querySelectorAll("[data-request-preset]").forEach((button) => {
    button.addEventListener("click", () => {
      $("#orchestratorRequest").value = button.dataset.requestPreset || "";
      $("#orchestratorRequest").focus();
    });
  });
  document.querySelectorAll("[data-forge-preset]").forEach((button) => {
    button.addEventListener("click", () => {
      const preset = parseCommandPayload(button.dataset.forgePreset || "{}");
      $("#forgeAssetId").value = preset.assetId || "";
      $("#forgeKind").value = preset.kind || "prop";
      $("#forgePrompt").value = preset.prompt || "";
      $("#forgePrompt").focus();
    });
  });
  document.querySelectorAll("[data-studio-nav]").forEach((link) => {
    link.addEventListener("click", () => {
      setStudioView(link.dataset.studioNav || viewForHash(link.hash) || "focus");
    });
  });
  window.addEventListener("hashchange", () => {
    const view = viewForHash(window.location.hash);
    if (view) setStudioView(view);
  });
  $(".inspector").addEventListener("click", (event) => {
    const modeButton = event.target.closest("[data-inspector-mode]");
    if (modeButton) {
      setStudioView(modeButton.dataset.inspectorMode || "focus", { target: "#command-center" });
      return;
    }
    const taskButton = event.target.closest("[data-inspector-focus-task]");
    if (taskButton) {
      selectedTaskId = taskButton.dataset.inspectorFocusTask || selectedTaskId;
      selectedArtifactPath = "";
      renderTaskTracker();
      setStudioView("focus", { target: "#task-tracker" });
      return;
    }
    const artifactButton = event.target.closest("[data-inspector-artifact-path]");
    if (artifactButton) {
      selectedArtifactPath = artifactButton.dataset.inspectorArtifactPath || "";
      renderTaskTracker();
      setStudioView("focus", { target: "#task-tracker" });
      return;
    }
    const memoryButton = event.target.closest("[data-inspector-memory-path]");
    if (memoryButton) {
      $("#filePath").value = memoryButton.dataset.inspectorMemoryPath || "";
      loadFile();
      setStudioView("library", { target: "#memory" });
    }
  });

  document.querySelectorAll("[data-command]").forEach((button) => {
    button.addEventListener("click", () => runCommand(button.dataset.command));
  });

  $("#reload").addEventListener("click", loadState);
  $("#runSearch").addEventListener("click", () => runSearch(false));
  $("#rebuildSearch").addEventListener("click", () => runSearch(true));
  $("#searchQuery").addEventListener("keydown", (event) => {
    if (event.key === "Enter") runSearch(false);
  });
  $("#searchResults").addEventListener("click", (event) => {
    const button = event.target.closest("[data-search-path]");
    if (!button) return;
    const path = button.dataset.searchPath || "";
    $("#filePath").value = path;
    if (button.dataset.sourceType === "screenshot") {
      $("#filePreview").textContent = `스크린샷 파일: ${path}\n이미지 파일은 현재 파일 미리보기 대신 경로를 연결합니다.`;
    } else {
      loadFile();
    }
    setStudioView("library");
    $("#memory").scrollIntoView({ behavior: "smooth", block: "start" });
  });
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
  $("#setGoal").addEventListener("click", () => {
    const objective = $("#goalObjective").value.trim();
    if (!objective) {
      $("#console").textContent = "목표를 입력하세요.";
      $("#goalObjective").focus();
      return;
    }
    runCommand("company.goal.set", { objective, maxIterations: 12 });
  });
  $("#runGoal").addEventListener("click", () => {
    runCommand("company.goal.run", {
      dryRun: $("#goalDryRun").checked,
      maxIterations: 12,
    });
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
  $("#feedback").addEventListener("click", (event) => {
    const fileButton = event.target.closest("[data-file-path]");
    if (fileButton) {
      $("#filePath").value = fileButton.dataset.filePath || "";
      loadFile();
      setStudioView("library", { target: "#memory" });
      return;
    }
    const commandButton = event.target.closest("[data-command-name]");
    if (!commandButton) return;
    const payload = {};
    if (commandButton.dataset.feedbackPath) payload.path = commandButton.dataset.feedbackPath;
    runCommand(commandButton.dataset.commandName, payload);
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
  $("#forgeCreate").addEventListener("click", () => {
    const assetId = $("#forgeAssetId").value.trim();
    if (!assetId) {
      $("#console").textContent = "Forge 에셋 ID를 입력하세요.";
      $("#forgeAssetId").focus();
      return;
    }
    runCommand("asset.forge", {
      assetId,
      kind: $("#forgeKind").value || "prop",
      prompt: $("#forgePrompt").value.trim(),
    });
  });
  $("#image3dCreate").addEventListener("click", () => {
    const assetId = $("#image3dAssetId").value.trim();
    if (!assetId) {
      $("#console").textContent = "Image→Blender 에셋 ID를 입력하세요.";
      $("#image3dAssetId").focus();
      return;
    }
    runCommand("asset.image3d", {
      assetId,
      provider: $("#image3dProvider").value || "trellis2",
      prompt: $("#image3dPrompt").value.trim(),
      sourceImage: $("#image3dSourceImage").value.trim(),
    });
  });
  $("#assetForgeJobList").addEventListener("click", (event) => {
    const button = event.target.closest("[data-memory-path]");
    if (!button) return;
    $("#filePath").value = button.dataset.memoryPath || "";
    loadFile();
    setStudioView("library", { target: "#memory" });
  });
  $("#imageToBlenderJobList").addEventListener("click", (event) => {
    const button = event.target.closest("[data-memory-path]");
    if (!button) return;
    $("#filePath").value = button.dataset.memoryPath || "";
    loadFile();
    setStudioView("library", { target: "#memory" });
  });
  $("#gameCreateAsset").addEventListener("click", () => {
    const assetId = $("#gameAssetId").value.trim();
    if (!assetId) {
      $("#console").textContent = "에셋 ID를 입력하세요.";
      $("#gameAssetId").focus();
      return;
    }
    $("#assetId").value = assetId;
    runCommand("asset.new", { assetId });
  });
  $("#gameAcceptAsset").addEventListener("click", () => {
    const assetId = $("#gameAssetId").value.trim();
    if (!assetId) {
      $("#console").textContent = "승인할 에셋 ID를 입력하세요.";
      $("#gameAssetId").focus();
      return;
    }
    $("#assetId").value = assetId;
    runCommand("asset.status", { assetId, status: "accepted" });
  });
  $("#gamePrepareAsset").addEventListener("click", () => {
    const assetId = $("#gameAssetId").value.trim();
    if (!assetId) {
      $("#console").textContent = "파이프라인을 준비할 에셋 ID를 입력하세요.";
      $("#gameAssetId").focus();
      return;
    }
    $("#assetId").value = assetId;
    runCommand("asset.prepare", { assetId });
  });
  $("#loadFile").addEventListener("click", loadFile);
  $("#task-tracker").addEventListener("click", (event) => {
    const button = event.target.closest("[data-artifact-path]");
    if (!button) return;
    selectedArtifactPath = button.dataset.artifactPath || "";
    renderTaskTracker();
  });
  $("#game-cockpit").addEventListener("click", (event) => {
    const button = event.target.closest("[data-game-artifact-path]");
    if (!button) return;
    const path = button.dataset.gameArtifactPath || "";
    if (!path) return;
    $("#filePath").value = path;
    loadFile();
    setStudioView("library", { target: "#memory" });
  });
  $("#gameNextAction").addEventListener("click", (event) => {
    const button = event.target.closest("[data-command]");
    if (!button) return;
    runCommand(button.dataset.command, parseCommandPayload(button.dataset.commandPayload || ""));
  });
  $("#memory").addEventListener("click", (event) => {
    const button = event.target.closest("[data-memory-path]");
    if (!button) return;
    $("#filePath").value = button.dataset.memoryPath || "";
    loadFile();
  });
  $("#orchestratorRun").addEventListener("click", () => {
    const request = $("#orchestratorRequest").value.trim();
    if (!request) {
      $("#console").textContent = "오케스트레이터에게 맡길 요청을 입력하세요.";
      $("#orchestratorRequest").focus();
      return;
    }
    runCommand("orchestrator.run", {
      request,
      dryRun: $("#orchestratorQuick").checked,
    });
  });
  $("#command-center").addEventListener("click", (event) => {
    const simButton = event.target.closest("[data-sim-command]");
    if (simButton) {
      const runDir = simButton.dataset.runDir || state.sim?.latestRun?.path || "";
      const runDirA = simButton.dataset.runDirA || "";
      const runDirB = simButton.dataset.runDirB || "";
      const assetId = simButton.dataset.assetId || "";
      const payload = {};
      if (runDir) payload.runDir = runDir;
      if (runDirA) payload.runDirA = runDirA;
      if (runDirB) payload.runDirB = runDirB;
      if (assetId) payload.assetId = assetId;
      runCommand(simButton.dataset.simCommand, payload);
      return;
    }
    const fileButton = event.target.closest("[data-file-path]");
    if (fileButton) {
      $("#filePath").value = fileButton.dataset.filePath || "";
      loadFile();
      setStudioView("library", { target: "#memory" });
      return;
    }
    const commandButton = event.target.closest("[data-command-name]");
    if (commandButton) {
      const payload = {};
      if (commandButton.dataset.feedbackPath) payload.path = commandButton.dataset.feedbackPath;
      runCommand(commandButton.dataset.commandName, payload);
      return;
    }
    const button = event.target.closest("[data-conversation-artifact-path]");
    if (!button) return;
    selectedArtifactPath = button.dataset.conversationArtifactPath || "";
    renderTaskTracker();
    $("#task-tracker").scrollIntoView({ behavior: "smooth", block: "start" });
  });
  $("#runAgent").addEventListener("click", () => runAgentCommand("agent.run"));
  $("#reviewAgent").addEventListener("click", () => runAgentCommand("agent.review"));
	  $("#tasksList").addEventListener("click", async (event) => {
	    const button = event.target.closest("[data-task-action]");
	    if (!button) return;
	    const taskId = button.dataset.taskId || "";
	    const action = button.dataset.taskAction || "run";
	    if (action === "select" || action === "answer") {
        const task = taskById(taskId);
	      selectedTaskId = taskId;
	      selectedArtifactPath = action === "answer" && task ? taskAnswerPath(task) : "";
	      renderTaskTracker();
	      $("#task-tracker").scrollIntoView({ behavior: "smooth", block: "start" });
	      return;
	    }
    const command = action === "advance" ? "company.advance" : action === "review" ? "company.review" : action === "verify" ? "company.verify" : "agent.run";
    const label = button.textContent.trim() || "다음 단계";
    markTaskPending(button, `${label} 요청됨. 완료되면 작업판 상태가 갱신됩니다.`);
    $("#agentTaskId").value = taskId;
    if (command.startsWith("agent.")) {
      await runAgentCommand(command, { taskId, tool: "", message: "" });
    } else if (command === "company.review") {
      await runCommand(command, { taskId, reviewerId: "critic_reviewer" });
    } else if (command === "company.advance") {
      await runCommand(command, { taskId });
    } else {
      await runCommand(command, { taskId });
    }
    await loadState().catch((error) => {
      $("#console").textContent = `상태 갱신 오류: ${error.message}`;
    });
	  });
  $("#goalEngineChecks").addEventListener("click", (event) => {
    const button = event.target.closest("[data-goal-task-id]");
    if (!button) return;
    selectedTaskId = button.dataset.goalTaskId || "";
    selectedArtifactPath = "";
    setStudioView("board", { target: "#task-tracker" });
    renderTaskTracker();
  });
	}

function runAgentCommand(command, override = {}) {
  const taskId = override.taskId || $("#agentTaskId").value.trim();
  if (!taskId) {
    $("#console").textContent = "실행할 작업 ID를 입력하세요.";
    $("#agentTaskId").focus();
    return;
  }
  return runCommand(command, {
    taskId,
    tool: override.tool ?? $("#agentTool").value,
    dryRun: $("#agentDryRun").checked,
    fullApproval: command === "agent.run",
    message: override.message ?? $("#agentMessage").value.trim(),
  });
}

function markTaskPending(button, message) {
  const card = button.closest(".task-item");
  if (!card) return;
  card.classList.add("is-running");
  card.setAttribute("aria-busy", "true");
  card.querySelectorAll("[data-task-action]").forEach((actionButton) => {
    actionButton.disabled = true;
  });
  const status = card.querySelector(".task-live-status");
  if (status) {
    status.textContent = message;
  }
}

function trackerTask() {
  if (liveActivity?.taskId) {
    const liveTask = taskById(liveActivity.taskId);
    if (liveTask) return liveTask;
  }
  const selected = taskById(selectedTaskId);
  if (selected) return selected;
  if (recentActivity?.taskId) {
    const recentTask = taskById(recentActivity.taskId);
    if (recentTask) return recentTask;
  }
  return latestTask(state.company?.tasks || []);
}

function resultLabel(task) {
  if (task.verification_status === "passed") return "검증 통과";
  if (task.status === "closed" && task.verification_status === "passed") return "완료됨";
  if (task.status === "closed") return "완료됨";
  if (task.status === "closed_blocked") return "차단 종료";
  if (task.status === "blocked") return "차단됨";
  if (task.verification_status === "pending") return "검증 대기";
  return translate(task.status || "pending");
}

function trackerSteps(task) {
  const artifacts = taskArtifacts(task);
  const latestRun = latestAgentRun(task, "run");
  const hasPlan = artifacts.some((artifact) => artifact.kind === "plan" && artifact.exists !== false);
  const hasRun = Boolean(latestRun);
  const hasReview = Boolean(task.review_status) || (task.agent_runs || []).some((run) => run.mode === "review") || artifacts.some((artifact) => artifact.path.includes("/reviews/"));
  const hasVerification = Boolean(task.verification_status || task.verification);
  const isClosed = ["closed", "closed_blocked"].includes(task.status) || task.verification_status === "passed";
  const runStatus = latestRun?.status || "";
  const isBad = ["blocked", "closed_blocked"].includes(task.status) || ["failed", "timeout", "blocked"].includes(runStatus || task.agent_status);
  return [
    stepData("요청", Boolean(task.created_at), task.created_at ? "접수" : "대기"),
    stepData("계획", hasPlan, hasPlan ? "작성됨" : translate(task.status || "대기")),
    stepData("에이전트 실행", hasRun, hasRun ? translate(runStatus || "ok") : "대기", isBad && hasRun),
    stepData("리뷰", hasReview, hasReview ? translate(task.review_status || "reviewed") : "대기"),
    stepData("검증", hasVerification, hasVerification ? translate(task.verification_status || "pending") : "대기", task.verification_status === "failed"),
    stepData("결과", isClosed, resultLabel(task), isBad && isClosed),
  ];
}

function latestAgentRun(task, mode) {
  return [...(task.agent_runs || [])]
    .filter((run) => !mode || run.mode === mode)
    .sort((a, b) => Date.parse(b.created_at || 0) - Date.parse(a.created_at || 0))[0] || null;
}

function stepData(label, done, value, bad = false) {
  return {
    label,
    value,
    tone: bad ? "bad" : done ? "good" : "warn",
  };
}

function trackerTimeline(task) {
  const rows = [];
  if (task.created_at) {
    rows.push({
      title: "요청 생성",
      body: task.request || task.id,
      time: formatDate(task.created_at),
      badge: displayTaskStatus(task),
      tone: toneForStatus(displayTaskTone(task)),
    });
  }
  const plan = taskArtifacts(task).find((artifact) => artifact.kind === "plan");
  if (plan?.exists) {
    rows.push({
      title: "계획 작성",
      body: plan.path,
      time: "",
      badge: "계획",
      tone: "good",
    });
  }
  for (const run of task.agent_runs || []) {
    rows.push({
      title: `${run.tool || "agent"} ${run.mode || "run"}`,
      body: run.path || "경로 없음",
      time: formatDate(run.created_at),
      badge: translate(run.status || "pending"),
      tone: toneForStatus(run.status),
    });
  }
  for (const job of task.jobs || []) {
    rows.push({
      title: `${commandText[job.commandName] || job.commandName || "job"} 실행`,
      body: job.receipt?.path || jobLatestEvent(job) || job.id,
      time: formatDate(job.updatedAt || job.createdAt),
      badge: translate(job.status || "pending"),
      tone: toneForStatus(job.status),
    });
    for (const event of (job.events || []).slice(-5)) {
      rows.push({
        title: `job ${event.type || "event"}`,
        body: event.message || "",
        time: formatDate(event.time),
        badge: job.id || "job",
        tone: toneForStatus(job.status),
      });
    }
  }
  for (const evidence of task.evidence || []) {
    rows.push({
      title: "증거 연결",
      body: `${evidence.path || "경로 없음"}${evidence.note ? ` · ${evidence.note}` : ""}`,
      time: formatDate(evidence.attached_at),
      badge: "증거",
      tone: "good",
    });
  }
  if (task.verification) {
    rows.push({
      title: "검증",
      body: task.verification,
      time: formatDate(task.updated_at),
      badge: translate(task.verification_status || "pending"),
      tone: toneForStatus(task.verification_status),
    });
  }
  if (task.closed_at) {
    rows.push({
      title: "종료",
      body: resultLabel(task),
      time: formatDate(task.closed_at),
      badge: displayTaskStatus(task),
      tone: toneForStatus(displayTaskTone(task)),
    });
  }
  return rows;
}

function taskArtifacts(task) {
  if (Array.isArray(task.artifacts)) return task.artifacts;
  return [
    task.work_order ? { kind: "plan", label: "작업 주문", path: task.work_order, exists: true } : null,
    task.last_agent_run ? { kind: "answer", label: "에이전트 답변", path: task.last_agent_run, exists: true } : null,
    task.report ? { kind: "report", label: "보고/리뷰", path: task.report, exists: true } : null,
    task.verification ? { kind: "verification", label: "검증 결과", path: task.verification, exists: true } : null,
    ...(task.evidence || []).map((evidence, index) => ({
      kind: "evidence",
      label: `증거 ${index + 1}`,
      path: evidence.path,
      note: evidence.note,
      exists: true,
    })),
  ].filter((artifact) => artifact?.path);
}

function defaultArtifactPath(task, artifacts) {
  const preferred = [
    taskAnswerPath(task),
    latestReceiptPath(task),
    (task.verification || ""),
    `memory/company/workflows/${task.id}-workflow.md`,
    task.report || "",
    task.last_agent_run || "",
  ].filter(Boolean);
  for (const path of preferred) {
    const match = artifacts.find((artifact) => artifact.path === path && artifact.exists !== false);
    if (match) return match.path;
  }
  return artifacts.find((artifact) => artifact.exists !== false)?.path || "";
}

function taskAnswerPath(task) {
  const artifacts = Array.isArray(task.artifacts) ? task.artifacts : [];
  const answer = artifacts.find((artifact) => artifact.kind === "answer" && artifact.path && artifact.exists !== false);
  return answer?.path || task.last_agent_run || "";
}

function latestJob(task) {
  return [...(task.jobs || [])]
    .sort((a, b) => Date.parse(b.updatedAt || b.createdAt || 0) - Date.parse(a.updatedAt || a.createdAt || 0))[0] || null;
}

function latestJobEvent(task) {
  const job = latestJob(task);
  return jobLatestEvent(job);
}

function latestReceiptPath(task) {
  const job = latestJob(task);
  return job?.receipt?.path || "";
}

function artifactNote(artifact) {
  if (artifact.status) return translate(artifact.status);
  return artifact.note || artifact.kind || "";
}

function renderTrackerPreview(path) {
  if (!path) {
    previewRequestPath = "";
    $("#trackerPreviewTitle").textContent = "선택된 파일 없음";
    $("#trackerPreview").textContent = "결과 파일이 없습니다.";
    return;
  }
  if (previewRequestPath === path && $("#trackerPreview").textContent !== "불러오는 중입니다.") return;
  previewRequestPath = path;
  $("#trackerPreviewTitle").textContent = path;
  $("#trackerPreview").textContent = "불러오는 중입니다.";
  api(`/api/file?path=${encodeURIComponent(path)}`)
    .then((data) => {
      if (previewRequestPath !== path) return;
      $("#trackerPreview").textContent = data.content || "(빈 파일)";
    })
    .catch((error) => {
      if (previewRequestPath !== path) return;
      $("#trackerPreview").textContent = `오류: ${error.message}`;
    });
}

function taskWeight(task) {
  if (task.status === "needs_review") return 0;
  if (task.status === "needs_evidence" || task.status === "evidence_attached") return 0.5;
  if (task.status === "closed") return 3;
  if (task.status === "closed_blocked") return 4;
  return 1;
}

function taskNextAction(task) {
  if (task.closed_at || task.verification_status === "passed") {
    return { action: "select", label: "완료 결과 확인" };
  }
  const serverAction = task.productionCard?.nextAction;
  if (serverAction?.command === "company.advance") {
    return { action: "advance", label: serverAction.label || "자동 진행" };
  }
  if (serverAction?.command === "company.verify") {
    return { action: "verify", label: serverAction.label || "완료 처리" };
  }
  if (serverAction?.command === "company.review") {
    return { action: "review", label: serverAction.label || "리뷰 진행" };
  }
  if (serverAction?.command === "agent.run") {
    return { action: "run", label: serverAction.label || "실행 -> 검토" };
  }
  if (task.status === "needs_review") {
    return { action: "advance", label: "자동 리뷰/검증" };
  }
  if (task.status === "needs_evidence" || task.status === "evidence_attached") {
    return { action: "advance", label: "자동 증거 검증" };
  }
  return { action: "run", label: "실행 -> 검토" };
}

function displayTaskStatus(task) {
  if (task.verification_status === "passed") return "검증 통과";
  const status = task.status || "pending";
  const verification = task.verification_status ? ` · 검증 ${translate(task.verification_status)}` : "";
  return `${translate(status)}${verification}`;
}

function displayTaskTone(task) {
  if (task.verification_status === "passed") return "succeeded";
  return task.status || "pending";
}

function taskById(taskId) {
  if (!taskId) return null;
  return (state.company?.tasks || []).find((task) => task.id === taskId) || null;
}

function latestTask(tasks) {
  return [...(tasks || [])].sort((a, b) => Date.parse(b.updated_at || b.created_at || 0) - Date.parse(a.updated_at || a.created_at || 0))[0] || null;
}

function taskAgent(task) {
  return task.assigned_agent || task.suggested_agent || "chief_orchestrator";
}

function agentEntry(agentId) {
  return (state.company?.agents || []).find((agent) => agent.id === agentId) || null;
}

function toolForAgent(agentId) {
  const agent = agentEntry(agentId);
  return agent?.goal_setting?.tool || state.adapters?.defaultTool || "codex";
}

function agentFocus(agentId) {
  const focus = agentEntry(agentId)?.goal_setting?.focus || "";
  return focus.length > 72 ? `${focus.slice(0, 72)}...` : focus || "역할 설정 없음";
}

function collaboratorsFor(agentId, tasks) {
  const collaborators = new Set();
  if (agentId !== "chief_orchestrator") collaborators.add("chief_orchestrator");
  for (const task of tasks) {
    const reviewer = task.suggested_reviewer || "critic_reviewer";
    if (reviewer && reviewer !== agentId) collaborators.add(reviewer);
  }
  return [...collaborators];
}

function activityMeta(activity) {
  return [
    activity.taskId ? `작업 ${activity.taskId}` : "",
    activity.tool ? `도구 ${activity.tool}` : "역할 기본 도구",
    activity.mode ? `모드 ${activity.mode}` : "",
    activity.startedAt ? `시작 ${formatDate(activity.startedAt)}` : "",
  ].filter(Boolean).join(" · ");
}

function toneForStatus(status) {
  if (["ok", "available", "accepted", "closed", "complete", "passed", "dry_run", "reviewed", "evidence_attached", "succeeded", "ready", "handoff_ready", "empty", "perfect", "proof_refresh_passed", "proof_refresh_collected"].includes(status)) return "good";
  if (["proof_refresh_partial", "proof_refresh_incomplete"].includes(status)) return "warn";
  if ([
    "failed",
    "timeout",
    "missing",
    "disabled",
    "blocked",
    "closed_blocked",
    "rejected",
    "cancelled",
    "configured_but_failed",
    "auth_missing",
    "proof_refresh_failed",
  ].includes(status)) return "bad";
  return "warn";
}

function jobOutcome(job) {
  const outcome = job?.receipt?.outcome || job?.receipt?.verification?.status || job?.status || "pending";
  if (["blocked", "simworld_start_blocked", "not_started", "needs_worker"].includes(outcome)) {
    return "blocked";
  }
  return outcome === "completed" ? "succeeded" : outcome;
}

function jobDisplayStatus(job) {
  return translate(jobOutcome(job));
}

function jobDisplayTone(job) {
  return toneForStatus(jobOutcome(job));
}

function parseCommandPayload(raw) {
  if (!raw) return {};
  try {
    const parsed = JSON.parse(raw);
    return parsed && typeof parsed === "object" && !Array.isArray(parsed) ? parsed : {};
  } catch {
    return {};
  }
}

function dirtyCount(value) {
  if (Array.isArray(value)) return value.length;
  const text = String(value || "").trim();
  return text ? text.split(/\r?\n/).length : 0;
}

function translate(value) {
  return statusText[value] || value || "미확인";
}

function translateExecutor(value) {
  return {
    codex_sdk: "Python SDK",
    cli_fallback: "CLI fallback",
    codex_auto: "SDK 우선",
    cli: "CLI",
    missing: "없음",
  }[value] || value || "미확인";
}

function translateSourceType(value) {
  return {
    doc: "문서",
    jobs: "작업 원장",
    review: "리뷰",
    run: "실행",
    screenshot: "스크린샷",
    session: "세션",
    task_board: "작업판",
  }[value] || value || "파일";
}

function translateModelStatus(value) {
  return {
    verified: "검증됨",
    model_pending: "모델 검증 대기",
    runtime_missing: "런타임 없음",
    worker_blocked: "워커 차단",
  }[value] || translate(value);
}

function toneForModelStatus(value) {
  if (value === "verified") return "good";
  if (value === "model_pending") return "warn";
  return "bad";
}

function translateAbsorption(value) {
  return {
    absorbed: "흡수됨",
    partial: "부분 흡수",
    next: "다음 작업",
    rejected: "제외",
  }[value] || translate(value);
}

function translateRuntime(value) {
  return {
    available: "연결됨",
    blocked: "차단됨",
    local: "로컬 실행",
    pending: "대기",
  }[value] || translate(value);
}

function toneForAbsorption(value) {
  if (value === "absorbed") return "good";
  if (value === "partial" || value === "next") return "warn";
  return "bad";
}

function priorityTone(value) {
  if (value === "P0" || value === "P1") return "warn";
  if (value === "P2") return "good";
  return "";
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

activeStudioView = viewForHash(window.location.hash) || activeStudioView;
bind();
loadState().catch((error) => {
  $("#subtitle").textContent = "상태를 불러오지 못했습니다.";
  $("#console").textContent = `오류: ${error.message}`;
});

setInterval(() => {
  if (document.visibilityState === "visible" && !liveActivity) {
    loadState().catch(() => {});
  }
}, 10000);
