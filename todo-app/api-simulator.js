const MIN_API_DELAY_MS = 10000;
const MAX_API_DELAY_MS = 40000;
const RATE_LIMIT_PER_MINUTE = 30;
const RATE_LIMIT_WINDOW_MS = 60 * 1000;

const callOnceBtn = document.querySelector("#call-once-btn");
const callTenBtn = document.querySelector("#call-ten-btn");
const statusText = document.querySelector("#status-text");
const activeCount = document.querySelector("#active-count");
const queuedCount = document.querySelector("#queued-count");
const recentCount = document.querySelector("#recent-count");
const logList = document.querySelector("#log-list");

let requestTimestamps = [];
let activeCalls = 0;
let queuedCalls = 0;
let rateLimitLock = Promise.resolve();

renderMetrics("空闲");

callOnceBtn.addEventListener("click", () => {
  void invokeSimulatedApi("手动单次调用");
});

callTenBtn.addEventListener("click", () => {
  for (let i = 1; i <= 10; i += 1) {
    void invokeSimulatedApi(`并发批量调用 #${i}`);
  }
});

async function invokeSimulatedApi(source) {
  queuedCalls += 1;
  renderMetrics("排队中");

  const requestId = crypto.randomUUID().slice(0, 8);
  addLog(`请求 ${requestId} 已入队，来源：${source}`);

  await reserveRateLimitSlot(requestId);
  queuedCalls -= 1;
  activeCalls += 1;

  const delay = getRandomDelay(MIN_API_DELAY_MS, MAX_API_DELAY_MS);
  renderMetrics("处理中");
  addLog(`请求 ${requestId} 开始处理，预计耗时 ${Math.round(delay / 1000)} 秒`);

  try {
    await sleep(delay);
    addLog(`请求 ${requestId} 成功返回，实际耗时 ${Math.round(delay / 1000)} 秒`);
  } catch (error) {
    addLog(`请求 ${requestId} 失败：${String(error)}`, true);
  } finally {
    activeCalls -= 1;
    pruneExpiredTimestamps();
    renderMetrics(activeCalls > 0 || queuedCalls > 0 ? "处理中" : "空闲");
  }
}

async function reserveRateLimitSlot(requestId) {
  const reservation = rateLimitLock.then(async () => {
    await waitForRateLimitSlot(requestId);
    requestTimestamps.push(Date.now());
    pruneExpiredTimestamps();
  });

  rateLimitLock = reservation.catch(() => {});
  return reservation;
}

async function waitForRateLimitSlot(requestId) {
  pruneExpiredTimestamps();

  while (requestTimestamps.length >= RATE_LIMIT_PER_MINUTE) {
    const waitMs = Math.max(
      RATE_LIMIT_WINDOW_MS - (Date.now() - requestTimestamps[0]) + 20,
      200
    );
    addLog(
      `请求 ${requestId} 命中限频，等待约 ${Math.ceil(waitMs / 1000)} 秒后重试`,
      true
    );
    renderMetrics("限频等待");
    await sleep(waitMs);
    pruneExpiredTimestamps();
  }
}

function pruneExpiredTimestamps() {
  const now = Date.now();
  requestTimestamps = requestTimestamps.filter(
    (time) => now - time < RATE_LIMIT_WINDOW_MS
  );
}

function renderMetrics(status) {
  pruneExpiredTimestamps();
  statusText.textContent = `状态：${status}`;
  activeCount.textContent = `处理中：${activeCalls}`;
  queuedCount.textContent = `排队中：${queuedCalls}`;
  recentCount.textContent = `60 秒内调用数：${requestTimestamps.length} / ${RATE_LIMIT_PER_MINUTE}`;
}

function addLog(message, warning = false) {
  const item = document.createElement("li");
  item.className = `log-item${warning ? " warning" : ""}`;

  const now = new Date();
  const time = now.toLocaleTimeString("zh-CN", { hour12: false });
  item.innerHTML = `<strong>[${time}]</strong> ${message}`;

  logList.prepend(item);
}

function getRandomDelay(min, max) {
  return Math.floor(Math.random() * (max - min + 1)) + min;
}

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}
