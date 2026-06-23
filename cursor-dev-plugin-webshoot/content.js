let originalScrollY = 0;

function getPageMetrics() {
  const doc = document.documentElement;
  const body = document.body;
  const totalHeight = Math.max(
    doc.scrollHeight,
    body ? body.scrollHeight : 0,
    doc.offsetHeight,
    body ? body.offsetHeight : 0
  );
  const pageWidth = Math.max(doc.clientWidth, window.innerWidth);
  return {
    totalHeight,
    viewportHeight: window.innerHeight,
    pageWidth,
    devicePixelRatio: window.devicePixelRatio || 1
  };
}

function scrollToY(y) {
  window.scrollTo({ top: y, left: 0, behavior: "auto" });
}

function getAbsoluteUrl(url) {
  try {
    return new URL(url, window.location.href).href;
  } catch (_e) {
    return url || "";
  }
}

function normalizeText(text) {
  return (text || "").replace(/\s+\n/g, "\n").replace(/[ \t]+/g, " ").replace(/\n{3,}/g, "\n\n").trim();
}

const SKIP_TAGS = new Set([
  "script",
  "style",
  "noscript",
  "svg",
  "canvas",
  "form",
  "input",
  "textarea",
  "button",
  "select",
  "option",
  "iframe",
  "video",
  "audio"
]);

function findLanguageFromClass(el) {
  const className = (el?.className || "").toString();
  const m = className.match(/language-([a-zA-Z0-9_-]+)/);
  return m?.[1] || "";
}

function inlineMarkdown(node) {
  if (!node) return "";
  if (node.nodeType === Node.TEXT_NODE) {
    return node.textContent || "";
  }
  if (node.nodeType !== Node.ELEMENT_NODE) return "";

  const el = node;
  const tag = el.tagName.toLowerCase();
  if (SKIP_TAGS.has(tag)) return "";

  const children = () => [...el.childNodes].map(inlineMarkdown).join("");

  if (tag === "br") return "\n";
  if (tag === "a") {
    const href = getAbsoluteUrl(el.getAttribute("href") || "");
    const text = normalizeText(children());
    if (text) return `[${text}](${href})`;
    return href ? `[${href}](${href})` : "";
  }
  if (tag === "strong" || tag === "b") {
    const text = normalizeText(children());
    return text ? `**${text}**` : "";
  }
  if (tag === "em" || tag === "i") {
    const text = normalizeText(children());
    return text ? `*${text}*` : "";
  }
  if (tag === "code") {
    const text = normalizeText(el.textContent || "");
    // Inline code; pre>code is handled at block-level.
    return text ? `\`${text}\`` : "";
  }
  if (tag === "img") {
    const alt = el.getAttribute("alt") || "";
    const src = getAbsoluteUrl(el.getAttribute("src") || "");
    if (!src) return "";
    return `![${alt}](${src})`;
  }

  return children();
}

function pickMainNode() {
  const prefer = document.querySelector("article") || document.querySelector("main");
  if (prefer) return prefer;

  const candidates = [...document.body.querySelectorAll("article,main,section,div")].slice(0, 120);
  let best = null;
  let bestScore = 0;

  for (const el of candidates) {
    if (!el || !(el instanceof HTMLElement)) continue;
    const tag = el.tagName.toLowerCase();
    if (tag === "div" && el.childElementCount === 0) continue;

    // Skip obvious chrome elements.
    if (el.closest("nav,aside,header,footer")) continue;

    const text = normalizeText(el.innerText || "");
    const textLen = text.length;
    if (textLen < 200) continue;

    const headingCount = el.querySelectorAll("h1,h2,h3,h4,h5,h6").length;
    const score = textLen + headingCount * 500;
    if (score > bestScore) {
      bestScore = score;
      best = el;
    }
  }

  return best || document.body;
}

function elementToMarkdown(el, depth) {
  if (!el || !(el instanceof HTMLElement)) return "";
  const tag = el.tagName.toLowerCase();
  if (SKIP_TAGS.has(tag)) return "";

  // Avoid duplicating code blocks when handling container recursion.
  if (tag === "pre") {
    const codeEl = el.querySelector("code");
    // Code blocks should preserve whitespace as much as possible.
    const rawText = codeEl ? codeEl.textContent : el.textContent || "";
    const raw = rawText.replace(/\r\n/g, "\n").replace(/\n$/, "");
    const lang = findLanguageFromClass(codeEl || el);
    const fenceLang = lang ? lang : "";
    return `\n\n\`\`\`${fenceLang}\n${raw}\n\`\`\`\n\n`;
  }

  if (tag === "h1" || tag === "h2" || tag === "h3" || tag === "h4" || tag === "h5" || tag === "h6") {
    const level = Number(tag.replace("h", "")) || 1;
    const text = normalizeText(inlineMarkdown(el));
    if (!text) return "";
    return `${"#".repeat(level)} ${text}\n\n`;
  }

  if (tag === "p") {
    const text = normalizeText(inlineMarkdown(el));
    if (!text) return "";
    return `${text}\n\n`;
  }

  if (tag === "img") {
    const text = normalizeText(inlineMarkdown(el));
    if (!text) return "";
    return `${text}\n\n`;
  }

  if (tag === "ul" || tag === "ol") {
    const ordered = tag === "ol";
    const indent = "  ".repeat(depth || 0);
    const items = [...el.children].filter((c) => c.tagName && c.tagName.toLowerCase() === "li");
    let out = "";
    for (let i = 0; i < items.length; i += 1) {
      const li = items[i];
      const marker = ordered ? `${i + 1}.` : "-";

      // Collect inline parts excluding nested lists.
      const inlineParts = [];
      let nestedLists = [];
      for (const child of [...li.childNodes]) {
        if (child.nodeType === Node.ELEMENT_NODE) {
          const childEl = child;
          const childTag = childEl.tagName.toLowerCase();
          if (childTag === "ul" || childTag === "ol") {
            nestedLists.push(childEl);
            continue;
          }
          if (SKIP_TAGS.has(childTag)) continue;
        }
        inlineParts.push(inlineMarkdown(child));
      }

      const inlineText = normalizeText(inlineParts.join(""));
      out += `${indent}${marker} ${inlineText}\n`;

      if (nestedLists.length) {
        for (const nested of nestedLists) {
          const nestedMd = elementToMarkdown(nested, (depth || 0) + 1).trimEnd();
          if (nestedMd) {
            // Keep nested indentation handled by its own depth.
            out += `${nestedMd}\n`;
          }
        }
      }
    }
    return `${out}\n`;
  }

  if (tag === "div" || tag === "section" || tag === "article" || tag === "main") {
    const parts = [];
    // Limit recursion to avoid extremely large pages.
    const children = [...el.children].slice(0, 1200);
    for (const child of children) {
      const childTag = child.tagName.toLowerCase();
      if (SKIP_TAGS.has(childTag)) continue;
      const md = elementToMarkdown(child, depth || 0);
      if (md) parts.push(md);
      if (parts.join("").length > 900_000) break;
    }
    return parts.join("");
  }

  // Fallback for unknown containers: recurse into children that look like content.
  const isBlockish = ["span", "section", "div", "article", "main"].includes(tag);
  if (isBlockish) {
    const parts = [];
    const children = [...el.children].slice(0, 800);
    for (const child of children) {
      const childTag = child.tagName.toLowerCase();
      if (SKIP_TAGS.has(childTag)) continue;
      const md = elementToMarkdown(child, depth || 0);
      if (md) parts.push(md);
      if (parts.join("").length > 900_000) break;
    }
    return parts.join("");
  }

  return "";
}

function extractMarkdownFromPage() {
  const root = pickMainNode();
  const md = elementToMarkdown(root, 0) || "";
  const cleaned = md
    .replace(/\n{3,}/g, "\n\n")
    .replace(/[ \t]+\n/g, "\n")
    .trim();

  // Guard: extremely large pages can exceed extension storage.
  if (cleaned.length > 1_000_000) {
    return `${cleaned.slice(0, 1_000_000)}\n\n[导出内容过长，已截断]`;
  }
  return cleaned;
}

chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.type === "PING") {
    sendResponse({ ok: true });
    return;
  }

  if (message.type === "INIT_CAPTURE") {
    originalScrollY = window.scrollY || window.pageYOffset || 0;
    sendResponse({ ok: true, metrics: getPageMetrics(), originalScrollY });
    return;
  }

  if (message.type === "SCROLL_TO") {
    scrollToY(message.y || 0);
    setTimeout(() => {
      sendResponse({
        ok: true,
        actualY: window.scrollY || window.pageYOffset || 0
      });
    }, 120);
    return true;
  }

  if (message.type === "RESTORE_SCROLL") {
    scrollToY(originalScrollY || 0);
    sendResponse({ ok: true });
    return;
  }

  if (message.type === "EXTRACT_MARKDOWN") {
    (async () => {
      try {
        const markdown = extractMarkdownFromPage();
        sendResponse({ ok: true, markdown });
      } catch (error) {
        sendResponse({ ok: false, error: error?.message || String(error) });
      }
    })();
    return true;
  }
});
