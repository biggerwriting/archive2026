const STORE_KEY = "lastCapture";
const canvas = document.getElementById("previewCanvas");
const metaEl = document.getElementById("meta");
const downloadBtn = document.getElementById("downloadBtn");

function loadImage(url) {
  return new Promise((resolve, reject) => {
    const img = new Image();
    img.onload = () => resolve(img);
    img.onerror = () => reject(new Error("图片加载失败"));
    img.src = url;
  });
}

function setMeta(text) {
  metaEl.textContent = text;
}

function getTimestampName() {
  const date = new Date();
  const pad = (v) => String(v).padStart(2, "0");
  return `webshoot-${date.getFullYear()}${pad(date.getMonth() + 1)}${pad(date.getDate())}-${pad(date.getHours())}${pad(date.getMinutes())}${pad(date.getSeconds())}.png`;
}

async function renderVisible(captureData) {
  const image = await loadImage(captureData.imageDataUrl);
  canvas.width = image.width;
  canvas.height = image.height;
  const ctx = canvas.getContext("2d");
  ctx.drawImage(image, 0, 0);
  setMeta(`模式: 可视区域 | 尺寸: ${image.width} x ${image.height}`);
}

async function renderFull(captureData) {
  if (!captureData.frames?.length) {
    throw new Error("没有可用帧数据");
  }

  const images = await Promise.all(captureData.frames.map((frame) => loadImage(frame.imageDataUrl)));
  const first = images[0];
  const ratio = first.height / captureData.viewportHeight;

  const targetWidth = first.width;
  const targetHeight = Math.max(1, Math.round(captureData.totalHeight * ratio));
  canvas.width = targetWidth;
  canvas.height = targetHeight;

  const ctx = canvas.getContext("2d");
  for (let i = 0; i < images.length; i += 1) {
    const img = images[i];
    const frame = captureData.frames[i];
    const drawY = Math.round(frame.y * ratio);
    if (drawY >= canvas.height) {
      continue;
    }

    const maxHeight = canvas.height - drawY;
    const drawHeight = Math.min(img.height, maxHeight);
    if (drawHeight <= 0) {
      continue;
    }

    ctx.drawImage(
      img,
      0,
      0,
      img.width,
      drawHeight,
      0,
      drawY,
      canvas.width,
      drawHeight
    );
  }

  setMeta(`模式: 整页滚动 | 帧数: ${images.length} | 尺寸: ${canvas.width} x ${canvas.height}`);
}

async function downloadCanvasPng() {
  const blob = await new Promise((resolve) => canvas.toBlob(resolve, "image/png"));
  if (!blob) {
    throw new Error("导出失败");
  }
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
    const data = await chrome.storage.local.get(STORE_KEY);
    const captureData = data[STORE_KEY];
    if (!captureData) {
      throw new Error("未找到截图数据，请重新截图");
    }

    if (captureData.mode === "visible") {
      await renderVisible(captureData);
    } else if (captureData.mode === "full") {
      await renderFull(captureData);
    } else {
      throw new Error("未知截图模式");
    }

    downloadBtn.disabled = false;
  } catch (error) {
    setMeta(`错误: ${error.message}`);
  }
}

downloadBtn.addEventListener("click", async () => {
  downloadBtn.disabled = true;
  try {
    await downloadCanvasPng();
  } catch (error) {
    setMeta(`下载失败: ${error.message}`);
  } finally {
    downloadBtn.disabled = false;
  }
});

boot();
