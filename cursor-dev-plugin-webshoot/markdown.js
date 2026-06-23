const STORE_KEY_MD = "lastMarkdown";

const textarea = document.getElementById("markdownArea");
const metaEl = document.getElementById("meta");
const downloadBtn = document.getElementById("downloadBtn");

function setMeta(text) {
  metaEl.textContent = text || "";
}

function getTimestampName() {
  const date = new Date();
  const pad = (v) => String(v).padStart(2, "0");
  return `webshoot-${date.getFullYear()}${pad(date.getMonth() + 1)}${pad(date.getDate())}-${pad(date.getHours())}${pad(date.getMinutes())}${pad(date.getSeconds())}.md`;
}

async function downloadMarkdown(markdown) {
  const blob = new Blob([markdown], { type: "text/markdown;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  try {
    await chrome.downloads.download({
      url,
      filename: getTimestampName(),
      saveAs: true
    });
  } finally {
    URL.revokeObjectURL(url);
  }
}

async function boot() {
  try {
    const data = await chrome.storage.local.get(STORE_KEY_MD);
    const markdown = data[STORE_KEY_MD];
    if (!markdown) {
      throw new Error("未找到 Markdown 数据，请先在扩展里触发导出。");
    }

    textarea.value = markdown;
    textarea.setSelectionRange(0, 0);

    setMeta(`Markdown 已生成，长度: ${markdown.length} 字符`);
    downloadBtn.disabled = false;
  } catch (error) {
    textarea.value = "";
    setMeta(`错误: ${error.message}`);
  }
}

downloadBtn.addEventListener("click", async () => {
  downloadBtn.disabled = true;
  try {
    const markdown = textarea.value || "";
    if (!markdown.trim()) {
      throw new Error("没有可下载内容");
    }
    await downloadMarkdown(markdown);
    setMeta("下载已触发（可能需要等待保存对话框）。");
  } catch (error) {
    setMeta(`下载失败: ${error.message}`);
  } finally {
    downloadBtn.disabled = false;
  }
});

boot();

