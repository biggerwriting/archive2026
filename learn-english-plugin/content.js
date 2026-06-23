const ADD_WORD_MESSAGE = "TRIGGER_ADD_WORD";
const FALLBACK_KEY = {
  altKey: true,
  shiftKey: true,
  code: "KeyA"
};

function getSelectedWord() {
  const selection = window.getSelection();
  if (!selection) return "";
  return selection.toString().trim();
}

function getTextContextFromSelection(selection) {
  if (!selection || selection.rangeCount === 0) return "";
  const range = selection.getRangeAt(0);
  let node = range.commonAncestorContainer;

  if (node.nodeType === Node.TEXT_NODE) {
    node = node.parentElement;
  }
  if (!node) return "";

  const textContent =
    node.innerText ||
    node.textContent ||
    (node.parentElement ? node.parentElement.innerText || node.parentElement.textContent : "");
  return (textContent || "").replace(/\s+/g, " ").trim();
}

function extractSentenceFromSelection(selectedText) {
  const selection = window.getSelection();
  const context = getTextContextFromSelection(selection);
  if (!context) return selectedText;

  const normalizedSelection = selectedText.toLowerCase();
  const sentences = context
    .split(/(?<=[.!?。！？])\s+/)
    .map((item) => item.trim())
    .filter(Boolean);

  const hit = sentences.find((sentence) =>
    sentence.toLowerCase().includes(normalizedSelection)
  );

  if (hit) return hit;
  return context.slice(0, 500);
}

function showToast(message, isError = false) {
  const id = "__wordbook_toast__";
  let toast = document.getElementById(id);
  if (!toast) {
    toast = document.createElement("div");
    toast.id = id;
    toast.style.cssText = [
      "position:fixed",
      "right:16px",
      "bottom:16px",
      "padding:10px 12px",
      "border-radius:8px",
      "font-size:13px",
      "z-index:2147483647",
      "color:#fff",
      "background:rgba(17,24,39,0.92)",
      "box-shadow:0 4px 16px rgba(0,0,0,0.2)"
    ].join(";");
    document.body.appendChild(toast);
  }

  toast.textContent = message;
  toast.style.background = isError ? "rgba(153,27,27,0.92)" : "rgba(17,24,39,0.92)";
  toast.style.display = "block";

  window.clearTimeout(toast.__hideTimer);
  toast.__hideTimer = window.setTimeout(() => {
    toast.style.display = "none";
  }, 1800);
}

async function saveCurrentSelection() {
  const selectedText = getSelectedWord();
  if (!selectedText) {
    showToast("请先选中一个英文单词", true);
    return;
  }

  const sentence = extractSentenceFromSelection(selectedText);
  try {
    const entry = await window.WordStorage.addWordSentence(selectedText, sentence, {
      url: location.href,
      title: document.title
    });
    showToast(`已保存: ${entry.word}`);
  } catch (error) {
    showToast(error.message || "保存失败", true);
  }
}

chrome.runtime.onMessage.addListener((message) => {
  if (message && message.type === ADD_WORD_MESSAGE) {
    saveCurrentSelection();
  }
});

document.addEventListener("keydown", (event) => {
  const isFallbackShortcut =
    event.altKey === FALLBACK_KEY.altKey &&
    event.shiftKey === FALLBACK_KEY.shiftKey &&
    event.code === FALLBACK_KEY.code;

  if (!isFallbackShortcut || event.repeat) return;
  event.preventDefault();
  saveCurrentSelection();
});
