const bodyEl = document.getElementById("wordbook-body");
const emptyTipEl = document.getElementById("empty-tip");
const refreshBtn = document.getElementById("refresh-btn");
const exportBtn = document.getElementById("export-btn");

function createSentenceList(sentences) {
  const list = document.createElement("ul");
  list.className = "sentence-list";

  sentences.forEach((sentence) => {
    const li = document.createElement("li");
    li.textContent = sentence;
    list.appendChild(li);
  });

  return list;
}

function render(entries) {
  bodyEl.innerHTML = "";
  const isEmpty = entries.length === 0;
  emptyTipEl.style.display = isEmpty ? "block" : "none";

  if (isEmpty) return;

  entries.forEach((entry) => {
    const tr = document.createElement("tr");

    const wordTd = document.createElement("td");
    wordTd.textContent = entry.word;
    wordTd.className = "word-cell";

    const sentenceTd = document.createElement("td");
    sentenceTd.appendChild(createSentenceList(entry.sentences));

    tr.appendChild(wordTd);
    tr.appendChild(sentenceTd);
    bodyEl.appendChild(tr);
  });
}

async function loadEntries() {
  const entries = await window.WordStorage.listEntries();
  render(entries);
  return entries;
}

function download(filename, content) {
  const blob = new Blob([content], { type: "text/markdown;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
}

function getExportFilename() {
  const date = new Date();
  const y = date.getFullYear();
  const m = String(date.getMonth() + 1).padStart(2, "0");
  const d = String(date.getDate()).padStart(2, "0");
  return `english-wordbook-${y}-${m}-${d}.md`;
}

async function exportMarkdown() {
  const entries = await window.WordStorage.listEntries();
  const markdown = window.WordStorage.generateMarkdown(entries);
  download(getExportFilename(), markdown);
}

refreshBtn.addEventListener("click", () => {
  loadEntries();
});

exportBtn.addEventListener("click", () => {
  exportMarkdown();
});

loadEntries();
