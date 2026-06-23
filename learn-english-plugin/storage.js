(function (global) {
  const STORAGE_KEY = "words";

  function normalizeWhitespace(text) {
    return (text || "").replace(/\s+/g, " ").trim();
  }

  function normalizeWord(rawWord) {
    const cleaned = (rawWord || "")
      .trim()
      .replace(/^[^A-Za-z]+|[^A-Za-z]+$/g, "")
      .toLowerCase();
    return cleaned;
  }

  function isValidWord(word) {
    return /^[a-z]+(?:['-][a-z]+)*$/.test(word);
  }

  function sanitizeSentence(sentence) {
    return normalizeWhitespace(sentence).slice(0, 500);
  }

  async function getWordStore() {
    const result = await chrome.storage.local.get([STORAGE_KEY]);
    return result[STORAGE_KEY] || {};
  }

  async function setWordStore(store) {
    await chrome.storage.local.set({ [STORAGE_KEY]: store });
  }

  async function addWordSentence(rawWord, rawSentence, meta = {}) {
    const word = normalizeWord(rawWord);
    const sentence = sanitizeSentence(rawSentence);

    if (!word || !isValidWord(word)) {
      throw new Error("Please select a single English word.");
    }
    if (!sentence) {
      throw new Error("Unable to capture sentence from selection.");
    }

    const store = await getWordStore();
    const now = Date.now();
    const existing = store[word];

    const nextEntry = existing
      ? {
          ...existing,
          updatedAt: now,
          sourceUrl: meta.url || existing.sourceUrl || "",
          sourceTitle: meta.title || existing.sourceTitle || ""
        }
      : {
          word,
          sentences: [],
          createdAt: now,
          updatedAt: now,
          sourceUrl: meta.url || "",
          sourceTitle: meta.title || ""
        };

    const hasSentence = nextEntry.sentences.some(
      (item) => item.toLowerCase() === sentence.toLowerCase()
    );
    if (!hasSentence) {
      nextEntry.sentences.push(sentence);
      nextEntry.updatedAt = now;
    }

    store[word] = nextEntry;
    await setWordStore(store);
    return nextEntry;
  }

  async function listEntries() {
    const store = await getWordStore();
    return Object.values(store).sort((a, b) => b.updatedAt - a.updatedAt);
  }

  function escapeMarkdownCell(value) {
    return String(value || "")
      .replace(/\|/g, "\\|")
      .replace(/\n/g, "<br>");
  }

  function generateMarkdown(entries) {
    const lines = [];
    lines.push("# English Wordbook");
    lines.push("");
    lines.push(`Generated at: ${new Date().toLocaleString()}`);
    lines.push("");
    lines.push("| 单词 | 句子 |");
    lines.push("| --- | --- |");

    if (!entries.length) {
      lines.push("| _无_ | _无_ |");
      return lines.join("\n");
    }

    entries.forEach((entry) => {
      const sentenceCell = entry.sentences.map(escapeMarkdownCell).join("<br>");
      lines.push(`| ${escapeMarkdownCell(entry.word)} | ${sentenceCell} |`);
    });

    return lines.join("\n");
  }

  global.WordStorage = {
    addWordSentence,
    listEntries,
    generateMarkdown
  };
})(typeof window !== "undefined" ? window : self);
