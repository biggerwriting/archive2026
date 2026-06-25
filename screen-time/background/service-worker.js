/**
 * Screen Time Tracker - Background Service Worker
 *
 * 状态机：
 *   activeSession = null | { tabId, url, domain, title, startTime }
 *   windowFocused = boolean
 *
 * 事件链：
 *   Tab 切换   → endSession → startSession(新 tab)
 *   窗口失焦   → endSession，windowFocused = false
 *   窗口聚焦   → windowFocused = true → startSession(当前 tab)
 *   URL 变化   → endSession → startSession(同 tab 新 URL)
 *   Tab 关闭   → endSession
 *   Alarm 30s  → flushSession（保存进度，不结束计时）
 */

// ─────────────────────────────────────────────
// 运行时状态（Service Worker 重启后会重置）
// ─────────────────────────────────────────────
let activeSession = null; // 当前正在计时的会话
let windowFocused = true; // 当前 Chrome 窗口是否有焦点

// ─────────────────────────────────────────────
// 工具函数
// ─────────────────────────────────────────────

/** 从 URL 提取域名，失败返回 null */
function extractDomain(url) {
  try {
    const { hostname } = new URL(url);
    return hostname || null;
  } catch {
    return null;
  }
}

/** 判断 URL 是否需要跳过（系统页、扩展页等） */
function shouldSkipUrl(url) {
  if (!url) return true;
  const skip = ['chrome://', 'chrome-extension://', 'edge://', 'about:', 'data:', 'javascript:'];
  return skip.some((prefix) => url.startsWith(prefix));
}

/** 获取今天（按 startTime 所在日期）的 storage key */
function dateKey(timestamp) {
  const d = new Date(timestamp);
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, '0');
  const day = String(d.getDate()).padStart(2, '0');
  return `stats:${y}-${m}-${day}`;
}

/** 格式化毫秒 → 可读字符串（内部调试用） */
function fmtMs(ms) {
  const s = Math.floor(ms / 1000);
  const m = Math.floor(s / 60);
  const h = Math.floor(m / 60);
  if (h > 0) return `${h}h ${m % 60}m`;
  if (m > 0) return `${m}m ${s % 60}s`;
  return `${s}s`;
}

// ─────────────────────────────────────────────
// 核心计时逻辑
// ─────────────────────────────────────────────

/**
 * 结束当前会话：计算经过时间并写入 storage。
 * elapsed 不足 1 秒的记录丢弃（防止切换噪音）。
 */
async function endSession() {
  if (!activeSession) return;

  const session = activeSession;
  activeSession = null;

  const elapsed = Date.now() - session.startTime;
  if (elapsed < 1000) return; // 忽略 < 1s 的停留

  const key = dateKey(session.startTime);
  const stored = await chrome.storage.local.get(key);
  const dayStats = stored[key] || {};

  const { domain } = session;
  if (!dayStats[domain]) {
    dayStats[domain] = { totalTime: 0, recentUrls: [] };
  }

  // 累加域名总时长
  dayStats[domain].totalTime += elapsed;

  // 更新该 URL 的记录
  const urls = dayStats[domain].recentUrls;
  const existing = urls.find((u) => u.url === session.url);
  if (existing) {
    existing.time += elapsed;
    existing.lastVisit = new Date().toISOString();
    existing.title = session.title || existing.title; // 更新标题（可能变化）
  } else {
    urls.unshift({
      url: session.url,
      title: session.title || session.url,
      time: elapsed,
      lastVisit: new Date().toISOString(),
    });
  }

  // 每个域名最多保留 10 条 URL 记录（按插入顺序，最新在前）
  if (urls.length > 10) {
    dayStats[domain].recentUrls = urls.slice(0, 10);
  }

  await chrome.storage.local.set({ [key]: dayStats });
  console.log(`[ScreenTime] 保存 ${domain} +${fmtMs(elapsed)}，总计 ${fmtMs(dayStats[domain].totalTime)}`);
}

/**
 * 开始对某个 tab 计时。
 * 自动读取最新的 tab 信息（URL、标题）。
 */
async function startSession(tabId) {
  let tab;
  try {
    tab = await chrome.tabs.get(tabId);
  } catch {
    return; // Tab 可能已关闭
  }

  if (!tab || shouldSkipUrl(tab.url)) return;

  const domain = extractDomain(tab.url);
  if (!domain) return;

  activeSession = {
    tabId,
    url: tab.url,
    domain,
    title: tab.title || tab.url,
    startTime: Date.now(),
  };
  console.log(`[ScreenTime] 开始计时: ${domain}`);
}

/**
 * 刷新当前会话（定期存档，不结束计时）：
 * 把已经过去的时间存入 storage，然后重置 startTime 为当前时刻，
 * 避免 Service Worker 被终止时丢失超过 30s 的数据。
 */
async function flushSession() {
  if (!activeSession) return;

  // 快照当前会话，然后模拟"结束 + 立刻重新开始"
  const snapshot = { ...activeSession };
  await endSession();
  // 恢复会话（用相同 tab/url/domain，startTime 重置为现在）
  activeSession = {
    tabId: snapshot.tabId,
    url: snapshot.url,
    domain: snapshot.domain,
    title: snapshot.title,
    startTime: Date.now(),
  };
}

// ─────────────────────────────────────────────
// Chrome 事件监听
// ─────────────────────────────────────────────

/** Tab 切换 */
chrome.tabs.onActivated.addListener(async ({ tabId }) => {
  await endSession();
  if (windowFocused) {
    await startSession(tabId);
  }
});

/** 窗口焦点变化（最小化、切换应用等） */
chrome.windows.onFocusChanged.addListener(async (windowId) => {
  if (windowId === chrome.windows.WINDOW_ID_NONE) {
    // 所有 Chrome 窗口都失去焦点
    windowFocused = false;
    await endSession();
  } else {
    // 某个窗口获得焦点
    windowFocused = true;
    const [tab] = await chrome.tabs.query({ active: true, windowId });
    if (tab) {
      await startSession(tab.id);
    }
  }
});

/**
 * Tab URL/标题更新（页面加载完成）
 * 只处理"当前活跃 tab"的 complete 状态，且 URL 有变化时才重新计时。
 */
chrome.tabs.onUpdated.addListener(async (tabId, changeInfo, tab) => {
  if (changeInfo.status !== 'complete') return;
  if (!activeSession || activeSession.tabId !== tabId) return;
  if (tab.url === activeSession.url) {
    // 仅标题刷新（SPA 内部导航可能不触发 complete，忽略）
    activeSession.title = tab.title || activeSession.title;
    return;
  }
  // URL 已变化：结束旧页面计时，开始新页面计时
  await endSession();
  if (windowFocused) {
    await startSession(tabId);
  }
});

/** Tab 关闭 */
chrome.tabs.onRemoved.addListener(async (tabId) => {
  if (activeSession && activeSession.tabId === tabId) {
    await endSession();
  }
});

/** 定时刷新（每 30 秒存档一次，防止 SW 被系统终止） */
chrome.alarms.onAlarm.addListener(async ({ name }) => {
  if (name === 'flush') {
    await flushSession();
  }
});

// ─────────────────────────────────────────────
// 初始化
// ─────────────────────────────────────────────

/** 扩展安装 / 更新时 */
chrome.runtime.onInstalled.addListener(async () => {
  // 创建定时刷新 alarm（idempotent）
  await chrome.alarms.create('flush', { periodInMinutes: 0.5 });
  // 开始跟踪当前 tab
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  if (tab) await startSession(tab.id);
  console.log('[ScreenTime] 扩展已安装/更新，开始记录');
});

/**
 * Service Worker 启动时（被系统终止后重新唤醒）：
 * 确保 flush alarm 存在，并尝试恢复对当前 tab 的追踪。
 */
(async () => {
  // 确保 alarm 存在（SW 重启后 alarm 持久化在 Chrome 侧，不需要重建，但可检查）
  const existing = await chrome.alarms.get('flush');
  if (!existing) {
    await chrome.alarms.create('flush', { periodInMinutes: 0.5 });
  }

  // 获取当前有焦点的窗口和活跃 tab
  try {
    const windows = await chrome.windows.getAll({ populate: false });
    const focused = windows.find((w) => w.focused);
    if (focused) {
      windowFocused = true;
      const [tab] = await chrome.tabs.query({ active: true, windowId: focused.id });
      if (tab && !shouldSkipUrl(tab.url)) {
        await startSession(tab.id);
        console.log('[ScreenTime] SW 恢复，重新开始计时');
      }
    } else {
      windowFocused = false;
    }
  } catch (err) {
    console.warn('[ScreenTime] SW 初始化失败:', err);
  }
})();
