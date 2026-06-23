const STORAGE_KEY = "todo-app-items";

const form = document.querySelector("#todo-form");
const input = document.querySelector("#todo-input");
const list = document.querySelector("#todo-list");
const pendingCount = document.querySelector("#pending-count");
const completedCount = document.querySelector("#completed-count");

let todos = loadTodos();

render();

form.addEventListener("submit", (event) => {
  event.preventDefault();
  const text = input.value.trim();
  if (!text) return;

  todos.unshift({
    id: crypto.randomUUID(),
    text,
    completed: false,
  });

  input.value = "";
  saveAndRender();
});

list.addEventListener("click", (event) => {
  const item = event.target.closest(".todo-item");
  if (!item) return;

  const todoId = item.dataset.id;

  if (event.target.matches('input[type="checkbox"]')) {
    const todo = todos.find((entry) => entry.id === todoId);
    if (!todo) return;
    todo.completed = event.target.checked;
    saveAndRender();
    return;
  }

  if (event.target.matches(".delete-btn")) {
    todos = todos.filter((entry) => entry.id !== todoId);
    saveAndRender();
  }
});

function render() {
  list.innerHTML = "";

  if (todos.length === 0) {
    const empty = document.createElement("li");
    empty.className = "empty-state";
    empty.textContent = "还没有任务，开始添加第一个吧。";
    list.appendChild(empty);
  } else {
    const fragment = document.createDocumentFragment();

    todos.forEach((todo) => {
      const li = document.createElement("li");
      li.className = `todo-item${todo.completed ? " completed" : ""}`;
      li.dataset.id = todo.id;

      li.innerHTML = `
        <input type="checkbox" aria-label="标记任务完成" ${todo.completed ? "checked" : ""} />
        <span class="todo-text"></span>
        <button type="button" class="delete-btn">删除</button>
      `;

      li.querySelector(".todo-text").textContent = todo.text;
      fragment.appendChild(li);
    });

    list.appendChild(fragment);
  }

  updateCounts();
}

function updateCounts() {
  const completed = todos.filter((todo) => todo.completed).length;
  const pending = todos.length - completed;

  pendingCount.textContent = `未完成：${pending}`;
  completedCount.textContent = `已完成：${completed}`;
}

function loadTodos() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return [];

    const parsed = JSON.parse(raw);
    if (!Array.isArray(parsed)) return [];

    return parsed
      .filter((item) => item && typeof item.text === "string")
      .map((item) => ({
        id: typeof item.id === "string" ? item.id : crypto.randomUUID(),
        text: item.text.trim(),
        completed: Boolean(item.completed),
      }))
      .filter((item) => item.text.length > 0);
  } catch (error) {
    console.error("读取本地任务失败:", error);
    return [];
  }
}

function saveAndRender() {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(todos));
  render();
}
