const statusEl = document.getElementById("status");
const toolbarEl = document.getElementById("toolbar");
const listEl = document.getElementById("list");
const folderInput = document.getElementById("folderName");

let currentImages = [];

function setStatus(text, isError) {
  statusEl.textContent = text;
  statusEl.classList.toggle("error", Boolean(isError));
}

function isHttpPage(url) {
  try {
    const u = new URL(url);
    return u.protocol === "http:" || u.protocol === "https:";
  } catch {
    return false;
  }
}

function injectAndCollect(tabId) {
  return new Promise((resolve, reject) => {
    chrome.scripting.executeScript(
      {
        target: { tabId },
        files: ["content.js"],
      },
      () => {
        if (chrome.runtime.lastError) {
          reject(new Error(chrome.runtime.lastError.message));
          return;
        }
        chrome.tabs.sendMessage(tabId, { type: "COLLECT_IMAGES" }, (resp) => {
          if (chrome.runtime.lastError) {
            reject(new Error(chrome.runtime.lastError.message));
            return;
          }
          if (!resp || !resp.ok) {
            reject(new Error((resp && resp.error) || "收集失败"));
            return;
          }
          resolve(resp.images || []);
        });
      }
    );
  });
}

function defaultZipBasename() {
  const d = new Date();
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, "0");
  const day = String(d.getDate()).padStart(2, "0");
  return `PageImages_${y}${m}${day}`;
}

const ZIP_ORIGINS = ["<all_urls>"];

function ensureHostPermissionForZip() {
  return new Promise((resolve) => {
    chrome.permissions.contains({ origins: ZIP_ORIGINS }, (has) => {
      if (chrome.runtime.lastError) {
        resolve(false);
        return;
      }
      if (has) {
        resolve(true);
        return;
      }
      chrome.permissions.request({ origins: ZIP_ORIGINS }, (granted) => {
        if (chrome.runtime.lastError) {
          resolve(false);
          return;
        }
        resolve(Boolean(granted));
      });
    });
  });
}

function renderList(images) {
  listEl.innerHTML = "";
  images.forEach((item, index) => {
    const li = document.createElement("li");
    li.className = "list-item";

    const check = document.createElement("input");
    check.type = "checkbox";
    check.className = "item-check";
    check.dataset.index = String(index);
    check.checked = true;

    const thumbWrap = document.createElement("div");
    thumbWrap.className = "thumb-wrap";
    const img = document.createElement("img");
    img.alt = "";
    img.referrerPolicy = "no-referrer";
    img.loading = "lazy";
    img.src = item.url;
    img.onerror = () => {
      img.remove();
      const ph = document.createElement("div");
      ph.className = "thumb-placeholder";
      ph.textContent = "无预览";
      thumbWrap.appendChild(ph);
    };
    thumbWrap.appendChild(img);

    const meta = document.createElement("div");
    meta.className = "meta";
    const urlSpan = document.createElement("span");
    urlSpan.className = "meta-url";
    urlSpan.textContent = item.url;
    meta.appendChild(urlSpan);
    if (item.alt) {
      const altSpan = document.createElement("div");
      altSpan.className = "meta-alt";
      altSpan.textContent = item.alt;
      meta.appendChild(altSpan);
    }

    li.appendChild(check);
    li.appendChild(thumbWrap);
    li.appendChild(meta);
    listEl.appendChild(li);
  });
}

function getSelectedUrls() {
  const checks = listEl.querySelectorAll(".item-check:checked");
  const urls = [];
  checks.forEach((c) => {
    const i = Number(c.dataset.index);
    if (currentImages[i]) urls.push(currentImages[i].url);
  });
  return urls;
}

async function loadImages() {
  toolbarEl.hidden = true;
  listEl.hidden = true;
  setStatus("正在加载…");

  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  if (!tab || !tab.id) {
    setStatus("无法获取当前标签页。", true);
    return;
  }
  if (!tab.url || !isHttpPage(tab.url)) {
    setStatus("仅支持 http/https 页面（不支持 chrome:// 等系统页）。", true);
    return;
  }

  try {
    const images = await injectAndCollect(tab.id);
    currentImages = images;
    if (images.length === 0) {
      setStatus("当前页未找到图片。");
      return;
    }
    if (!folderInput.value.trim()) {
      folderInput.placeholder = defaultZipBasename();
    }
    setStatus(`共 ${images.length} 张，勾选后点击下载。`);
    renderList(images);
    toolbarEl.hidden = false;
    listEl.hidden = false;
  } catch (e) {
    setStatus(e.message || String(e), true);
  }
}

document.getElementById("btnRefresh").addEventListener("click", () => {
  loadImages();
});

document.getElementById("btnSelectAll").addEventListener("click", () => {
  listEl.querySelectorAll(".item-check").forEach((c) => {
    c.checked = true;
  });
});

document.getElementById("btnSelectNone").addEventListener("click", () => {
  listEl.querySelectorAll(".item-check").forEach((c) => {
    c.checked = false;
  });
});

document.getElementById("btnDownload").addEventListener("click", async () => {
  const urls = getSelectedUrls();
  if (urls.length === 0) {
    setStatus("请先勾选要下载的图片。", true);
    return;
  }

  if (urls.length >= 2) {
    const granted = await ensureHostPermissionForZip();
    if (!granted) {
      setStatus("打包 ZIP 需要授权「访问所有网站上的数据」，请在提示中允许，或改为一次只下载一张。", true);
      return;
    }
  }

  const folderName = folderInput.value.trim() || defaultZipBasename();

  chrome.runtime.sendMessage(
    {
      type: "DOWNLOAD_IMAGES",
      urls,
      folderName,
    },
    (resp) => {
      if (chrome.runtime.lastError) {
        setStatus(chrome.runtime.lastError.message, true);
        return;
      }
      if (!resp || !resp.ok) {
        let msg = "下载失败。";
        if (resp && resp.error) msg = resp.error;
        else if (resp && resp.mode === "zip" && typeof resp.zippedCount === "number") {
          msg = `ZIP 失败（已装入 ${resp.zippedCount} 张，失败 ${resp.failedCount || 0}）。`;
        }
        setStatus(msg, true);
        return;
      }
      if (resp.mode === "zip") {
        let msg = `已开始下载 ZIP，内含 ${resp.zippedCount} 张图片。`;
        if (resp.partial && resp.failedCount) {
          msg += ` 有 ${resp.failedCount} 张无法抓取，已跳过。`;
        }
        setStatus(msg);
      } else {
        setStatus("已开始下载。");
      }
    }
  );
});

loadImages();
