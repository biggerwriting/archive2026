importScripts("vendor/jszip.min.js");

const INVALID_PATH_CHARS = /[/\\:*?"<>|]/g;

function sanitizeSegment(name, fallback) {
  const s = String(name || "")
    .replace(INVALID_PATH_CHARS, "_")
    .replace(/^\.+/, "")
    .trim()
    .slice(0, 120);
  return s || fallback;
}

function extFromContentType(header) {
  if (!header || typeof header !== "string") return "";
  const primary = header.split(";")[0].trim().toLowerCase();
  switch (primary) {
    case "image/jpeg":
    case "image/jpg":
      return ".jpg";
    case "image/png":
      return ".png";
    case "image/webp":
      return ".webp";
    case "image/gif":
      return ".gif";
    default:
      return "";
  }
}

function guessExtensionFromUrl(url) {
  try {
    const u = new URL(url);
    let path = u.pathname;
    const q = path.indexOf("?");
    if (q >= 0) path = path.slice(0, q);
    const base = path.split("/").pop() || "";
    const dot = base.lastIndexOf(".");
    if (dot >= 0 && dot < base.length - 1) {
      const ext = base.slice(dot + 1).toLowerCase().replace(/[^a-z0-9]/g, "");
      if (ext.length >= 1 && ext.length <= 5) return "." + ext;
    }
  } catch {
    /* ignore */
  }
  return "";
}

function baseNameFromUrl(url, index) {
  try {
    const u = new URL(url);
    let path = u.pathname;
    const seg = path.split("/").filter(Boolean).pop() || "image";
    const q = seg.indexOf("?");
    const name = (q >= 0 ? seg.slice(0, q) : seg).slice(0, 80);
    const cleaned = sanitizeSegment(name, `image_${index}`);
    if (cleaned.includes(".")) return cleaned;
    return cleaned + guessExtensionFromUrl(url);
  } catch {
    return `image_${index}.bin`;
  }
}

function downloadSingle(url, sendResponse) {
  const pad = "001";
  const base = baseNameFromUrl(url, 1);
  const filename = sanitizeSegment(base, `${pad}_image`);
  chrome.downloads.download({ url, filename, saveAs: false }, (downloadId) => {
    if (chrome.runtime.lastError || downloadId === undefined) {
      sendResponse({
        ok: false,
        mode: "single",
        error: chrome.runtime.lastError ? chrome.runtime.lastError.message : "download failed",
      });
    } else {
      sendResponse({ ok: true, mode: "single" });
    }
  });
}

function downloadZip(urls, safeBasename, sendResponse) {
  const zip = new JSZip();
  const failed = [];

  (async () => {
    for (let i = 0; i < urls.length; i++) {
      const url = urls[i];
      const pad = String(i + 1).padStart(3, "0");
      const base = baseNameFromUrl(url, i + 1);
      try {
        const res = await fetch(url);
        if (!res.ok) {
          failed.push({ url, reason: `HTTP ${res.status}` });
          continue;
        }
        const m = base.match(/\.([a-z0-9]{1,6})$/i);
        let stem = m ? base.slice(0, -m[0].length) : base;
        if (!stem) stem = `image_${i + 1}`;
        let urlExt = m ? "." + m[1].toLowerCase() : "";
        if (urlExt === ".jpeg") urlExt = ".jpg";
        const ext =
          extFromContentType(res.headers.get("content-type")) || urlExt || guessExtensionFromUrl(url);
        const entryName = `${pad}_${sanitizeSegment(stem, `image_${i + 1}`)}${ext}`;
        const buf = await res.arrayBuffer();
        zip.file(entryName, buf);
      } catch (e) {
        failed.push({ url, reason: String(e && e.message ? e.message : e) });
      }
    }

    const zippedCount = urls.length - failed.length;
    if (zippedCount === 0) {
      sendResponse({
        ok: false,
        mode: "zip",
        error: "全部抓取失败，无法生成 ZIP",
        zippedCount: 0,
        failedCount: failed.length,
        failed,
      });
      return;
    }

    try {
      // Avoid generateAsync({type:"blob"}) and zip.file(..., Blob): JSZip/browser paths can call URL.createObjectURL, which MV3 service workers often lack.
      const base64 = await zip.generateAsync({ type: "base64" });
      const dataUrl = "data:application/zip;base64," + base64;
      const zipName = sanitizeSegment(`${safeBasename}.zip`, "images.zip");
      chrome.downloads.download({ url: dataUrl, filename: zipName, saveAs: false }, (downloadId) => {
        if (chrome.runtime.lastError || downloadId === undefined) {
          sendResponse({
            ok: false,
            mode: "zip",
            error: chrome.runtime.lastError ? chrome.runtime.lastError.message : "ZIP 下载失败",
            zippedCount,
            failedCount: failed.length,
            failed,
          });
        } else {
          sendResponse({
            ok: true,
            mode: "zip",
            zippedCount,
            failedCount: failed.length,
            partial: failed.length > 0,
            failed: failed.length > 0 ? failed : undefined,
          });
        }
      });
    } catch (e) {
      sendResponse({
        ok: false,
        mode: "zip",
        error: String(e && e.message ? e.message : e),
        zippedCount: 0,
        failedCount: failed.length,
        failed,
      });
    }
  })();
}

chrome.runtime.onMessage.addListener((msg, _sender, sendResponse) => {
  if (!msg || msg.type !== "DOWNLOAD_IMAGES") {
    return false;
  }

  const urls = Array.isArray(msg.urls) ? msg.urls.filter((u) => typeof u === "string" && u) : [];
  if (urls.length === 0) {
    sendResponse({ ok: false, error: "没有可下载的地址" });
    return false;
  }

  const defaultBasename = `PageImages_${new Date().toISOString().slice(0, 10).replace(/-/g, "")}`;
  const rawName = msg.folderName;
  let safeBasename = sanitizeSegment(rawName, defaultBasename);
  safeBasename = safeBasename.replace(/\.zip$/i, "");

  if (urls.length === 1) {
    downloadSingle(urls[0], sendResponse);
    return true;
  }

  downloadZip(urls, safeBasename, sendResponse);
  return true;
});
