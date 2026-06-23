const visibleBtn = document.getElementById("visibleBtn");
const fullBtn = document.getElementById("fullBtn");
const exportMdBtn = document.getElementById("exportMdBtn");
const statusEl = document.getElementById("status");

function setLoading(isLoading, text) {
  visibleBtn.disabled = isLoading;
  fullBtn.disabled = isLoading;
  exportMdBtn.disabled = isLoading;
  statusEl.textContent = text || "";
}

async function sendCaptureRequest(type) {
  setLoading(true, "正在截图...");
  try {
    const response = await chrome.runtime.sendMessage({ type });
    if (!response || !response.ok) {
      throw new Error(response?.error || "截图失败");
    }
    setLoading(false, "已生成预览页");
    window.close();
  } catch (error) {
    setLoading(false, `失败: ${error.message}`);
  }
}

visibleBtn.addEventListener("click", () => sendCaptureRequest("CAPTURE_VISIBLE"));
fullBtn.addEventListener("click", () => sendCaptureRequest("CAPTURE_FULL_PAGE"));

async function exportMarkdown() {
  setLoading(true, "正在解析并生成 Markdown...");
  try {
    const response = await chrome.runtime.sendMessage({ type: "EXPORT_MARKDOWN" });
    if (!response || !response.ok) {
      throw new Error(response?.error || "导出失败");
    }
    setLoading(false, "已打开导出页");
    window.close();
  } catch (error) {
    setLoading(false, `失败: ${error.message}`);
  }
}

exportMdBtn.addEventListener("click", () => exportMarkdown());
