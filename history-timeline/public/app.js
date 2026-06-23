const eventForm = document.getElementById("event-form");
const filterForm = document.getElementById("filter-form");
const eventList = document.getElementById("event-list");
const formMessage = document.getElementById("form-message");
const sourceList = document.getElementById("source-list");
const sourceTemplate = document.getElementById("source-item-template");
const addSourceBtn = document.getElementById("add-source-btn");
const resetFilterBtn = document.getElementById("reset-filter-btn");
const resultCount = document.getElementById("result-count");

function createSourceItem(type = "text", content = "") {
  const fragment = sourceTemplate.content.cloneNode(true);
  const row = fragment.querySelector(".source-item");
  const typeSelect = row.querySelector(".source-type");
  const contentInput = row.querySelector(".source-content");
  const removeBtn = row.querySelector(".remove-source-btn");

  typeSelect.value = type;
  contentInput.value = content;

  removeBtn.addEventListener("click", () => {
    row.remove();
  });

  sourceList.appendChild(fragment);
}

function collectSources() {
  return Array.from(sourceList.querySelectorAll(".source-item"))
    .map((row) => ({
      type: row.querySelector(".source-type").value,
      content: row.querySelector(".source-content").value.trim(),
    }))
    .filter((item) => item.content);
}

function sourceToDisplay(source) {
  const kindMap = {
    text: "文字",
    image: "图片",
    audio: "音频",
    video: "视频",
    file: "文件",
  };
  const kind = kindMap[source.type] || source.type;
  const isLink = /^https?:\/\//.test(source.content) || source.content.startsWith("/uploads/");
  if (isLink) {
    return `<li><strong>${kind}：</strong><a href="${source.content}" target="_blank" rel="noreferrer">${source.content}</a></li>`;
  }
  return `<li><strong>${kind}：</strong>${source.content}</li>`;
}

function renderEventCard(event) {
  const sourceHtml = (event.sources || []).length
    ? `<ul>${event.sources.map(sourceToDisplay).join("")}</ul>`
    : "<p class='empty-text'>暂无史料</p>";

  const tagsHtml = (event.tags || []).length
    ? event.tags.map((tag) => `<span class="tag">${tag}</span>`).join("")
    : "<span class='empty-text'>无标签</span>";

  return `
    <article class="event-card">
      <header>
        <h3>${event.title}</h3>
        <span class="time">${event.time}</span>
      </header>
      <div class="event-meta">
        <span class="meta-chip">地点 ${event.location}</span>
        <span class="meta-chip">人物 ${event.person}</span>
      </div>
      <p><strong>事件：</strong>${event.description}</p>
      <div><strong>标签：</strong>${tagsHtml}</div>
      <div class="source-block">
        <strong>史料：</strong>
        ${sourceHtml}
      </div>
    </article>
  `;
}

async function fetchEvents() {
  const formData = new FormData(filterForm);
  const query = new URLSearchParams();
  for (const [key, value] of formData.entries()) {
    if (String(value).trim() !== "") {
      query.set(key, value);
    }
  }

  const response = await fetch(`/api/events?${query.toString()}`);
  if (!response.ok) {
    throw new Error("查询失败");
  }
  const events = await response.json();
  resultCount.textContent = `共 ${events.length} 条`;
  if (!events.length) {
    eventList.innerHTML = "<p class='empty-text'>当前筛选条件下没有历史事件。</p>";
    return;
  }
  eventList.innerHTML = events
    .map((event, index) => `<div style="animation-delay:${Math.min(index * 70, 350)}ms">${renderEventCard(event)}</div>`)
    .join("");
}

async function submitEvent(evt) {
  evt.preventDefault();
  formMessage.textContent = "提交中...";
  formMessage.className = "";

  const formData = new FormData(eventForm);
  formData.set("sources", JSON.stringify(collectSources()));

  try {
    const response = await fetch("/api/events", {
      method: "POST",
      body: formData,
    });
    const result = await response.json();
    if (!response.ok) {
      throw new Error(result.message || "提交失败");
    }

    formMessage.textContent = "提交成功，已更新列表。";
    formMessage.className = "success";
    eventForm.reset();
    sourceList.innerHTML = "";
    createSourceItem();
    await fetchEvents();
  } catch (err) {
    formMessage.textContent = err.message || "提交失败";
    formMessage.className = "error";
  }
}

eventForm.addEventListener("submit", submitEvent);
filterForm.addEventListener("submit", async (evt) => {
  evt.preventDefault();
  await fetchEvents();
});

addSourceBtn.addEventListener("click", () => createSourceItem());
resetFilterBtn.addEventListener("click", async () => {
  filterForm.reset();
  await fetchEvents();
});

createSourceItem();
fetchEvents().catch(() => {
  eventList.innerHTML = "<p class='empty-text'>初始化加载失败，请稍后重试。</p>";
});
