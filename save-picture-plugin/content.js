(function () {
  if (globalThis.__BATCH_IMG_DL_INSTALLED__) {
    return;
  }
  globalThis.__BATCH_IMG_DL_INSTALLED__ = true;

  function parseSrcset(srcset) {
    if (!srcset || typeof srcset !== "string") return [];
    const urls = [];
    for (const part of srcset.split(",")) {
      const trimmed = part.trim();
      if (!trimmed) continue;
      const urlPart = trimmed.split(/\s+/)[0];
      if (urlPart) {
        try {
          urls.push(new URL(urlPart, document.baseURI).href);
        } catch {
          /* ignore */
        }
      }
    }
    return urls;
  }

  function normalizeUrl(href) {
    if (!href || typeof href !== "string") return null;
    const t = href.trim();
    if (!t || t.startsWith("javascript:")) return null;
    try {
      return new URL(t, document.baseURI).href;
    } catch {
      return null;
    }
  }

  function collectImages() {
    const seen = new Set();
    const items = [];

    function add(url, meta) {
      const u = normalizeUrl(url);
      if (!u) return;
      if (seen.has(u)) return;
      seen.add(u);
      items.push({ url: u, alt: meta.alt || "", width: meta.width ?? 0, height: meta.height ?? 0 });
    }

    for (const img of document.querySelectorAll("img")) {
      const alt = img.getAttribute("alt") || "";
      const w = img.naturalWidth || img.width || 0;
      const h = img.naturalHeight || img.height || 0;
      if (img.currentSrc) {
        add(img.currentSrc, { alt, width: w, height: h });
      } else if (img.src) {
        add(img.src, { alt, width: w, height: h });
      }
      const srcset = img.getAttribute("srcset");
      if (srcset) {
        for (const u of parseSrcset(srcset)) {
          add(u, { alt, width: w, height: h });
        }
      }
    }

    for (const source of document.querySelectorAll("picture source[srcset]")) {
      const srcset = source.getAttribute("srcset");
      if (srcset) {
        for (const u of parseSrcset(srcset)) {
          add(u, { alt: "", width: 0, height: 0 });
        }
      }
    }

    return items;
  }

  chrome.runtime.onMessage.addListener((msg, _sender, sendResponse) => {
    if (msg && msg.type === "COLLECT_IMAGES") {
      try {
        sendResponse({ ok: true, images: collectImages() });
      } catch (e) {
        sendResponse({ ok: false, error: String(e && e.message ? e.message : e) });
      }
      return true;
    }
    return false;
  });
})();
