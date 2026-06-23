const STORE_KEY = "lastCapture";
const STORE_KEY_MD = "lastMarkdown";

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

async function getActiveTab() {
  const tabs = await chrome.tabs.query({ active: true, currentWindow: true });
  if (!tabs.length || !tabs[0].id) {
    throw new Error("未找到当前活动标签页");
  }
  return tabs[0];
}

async function ensureContentScript(tabId) {
  try {
    await chrome.tabs.sendMessage(tabId, { type: "PING" });
  } catch (_error) {
    await chrome.scripting.executeScript({
      target: { tabId },
      files: ["content.js"]
    });
  }
}

async function sendMessageToTab(tabId, payload) {
  return chrome.tabs.sendMessage(tabId, payload);
}

async function captureVisible(windowId) {
  return chrome.tabs.captureVisibleTab(windowId, { format: "png" });
}

async function openPreviewPage() {
  await chrome.tabs.create({ url: chrome.runtime.getURL("preview.html") });
}

async function openMarkdownPage() {
  await chrome.tabs.create({ url: chrome.runtime.getURL("markdown.html") });
}

async function saveCapture(data) {
  await chrome.storage.local.set({ [STORE_KEY]: data });
}

async function captureVisibleFlow() {
  const tab = await getActiveTab();
  const imageDataUrl = await captureVisible(tab.windowId);
  await saveCapture({
    mode: "visible",
    createdAt: Date.now(),
    imageDataUrl
  });
  await openPreviewPage();
}

async function captureFullPageFlow() {
  const tab = await getActiveTab();
  const tabId = tab.id;
  await ensureContentScript(tabId);

  const initResp = await sendMessageToTab(tabId, { type: "INIT_CAPTURE" });
  if (!initResp?.ok) {
    throw new Error("无法初始化整页截图");
  }

  const { metrics, originalScrollY } = initResp;
  const { totalHeight, viewportHeight, pageWidth, devicePixelRatio } = metrics;
  const scrollPoints = [];
  for (let y = 0; y < totalHeight; y += viewportHeight) {
    scrollPoints.push(y);
  }
  if (scrollPoints.length === 0) {
    scrollPoints.push(0);
  }

  const frames = [];
  try {
    for (const y of scrollPoints) {
      const scrollResp = await sendMessageToTab(tabId, { type: "SCROLL_TO", y });
      const actualY = scrollResp?.actualY ?? y;
      await sleep(400);
      const imageDataUrl = await captureVisible(tab.windowId);
      frames.push({
        y: actualY,
        imageDataUrl
      });
    }
  } finally {
    await sendMessageToTab(tabId, { type: "RESTORE_SCROLL", y: originalScrollY });
  }

  await saveCapture({
    mode: "full",
    createdAt: Date.now(),
    totalHeight,
    viewportHeight,
    pageWidth,
    devicePixelRatio,
    frames
  });
  await openPreviewPage();
}

async function exportMarkdownFlow() {
  const tab = await getActiveTab();
  const tabId = tab.id;
  await ensureContentScript(tabId);

  const resp = await sendMessageToTab(tabId, { type: "EXTRACT_MARKDOWN" });
  if (!resp?.ok) {
    throw new Error(resp?.error || "解析 Markdown 失败");
  }

  await chrome.storage.local.set({ [STORE_KEY_MD]: resp.markdown || "" });
  await openMarkdownPage();
}

chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.type === "CAPTURE_VISIBLE") {
    captureVisibleFlow()
      .then(() => sendResponse({ ok: true }))
      .catch((error) => sendResponse({ ok: false, error: error.message }));
    return true;
  }

  if (message.type === "CAPTURE_FULL_PAGE") {
    captureFullPageFlow()
      .then(() => sendResponse({ ok: true }))
      .catch((error) => sendResponse({ ok: false, error: error.message }));
    return true;
  }

  if (message.type === "EXPORT_MARKDOWN") {
    exportMarkdownFlow()
      .then(() => sendResponse({ ok: true }))
      .catch((error) => sendResponse({ ok: false, error: error.message }));
    return true;
  }
});
