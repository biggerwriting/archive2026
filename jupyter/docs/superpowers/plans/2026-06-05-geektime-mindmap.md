# 极客时间课程脑图 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 构建一个单 HTML 文件的交互式脑图工具，将 185+ 门极客时间课程以可折叠横向树可视化，支持状态标注、自定义标签、搜索过滤、JSON 导入/导出。

**Architecture:** 全部逻辑内嵌于 `geektime_mindmap.html`，分为五个 `<script>` 块：课程常量数据、状态管理、D3 树渲染、交互逻辑（菜单/标签/搜索/过滤）、导入导出。D3.js v7 通过 CDN 加载，无其他外部依赖。

**Tech Stack:** HTML5 + CSS3 (内嵌暗色主题) + D3.js v7 (CDN) + Vanilla JS (ES2020)

---

## 文件结构

```
geektime_mindmap.html          ← 唯一输出文件
  ├─ <head>
  │    └─ <style>              CSS：工具栏、侧边栏、SVG 画布、模态框、右键菜单
  ├─ <body>
  │    ├─ #toolbar             顶部工具栏
  │    ├─ #app                 主区（侧边栏 + SVG 画布）
  │    │    ├─ #sidebar        左侧过滤面板
  │    │    └─ #canvas         D3 渲染目标
  │    ├─ #context-menu        右键浮出菜单
  │    ├─ #tooltip             鼠标悬停提示
  │    ├─ #modal-note          备注编辑模态
  │    ├─ #modal-tag           自定义标签创建/编辑模态
  │    └─ #modal-import        导入确认模态
  └─ <script>
       ├─ Block A: COURSE_DATA  课程常量（所有 185 门，18 分类）
       ├─ Block B: state.js     运行时状态管理
       ├─ Block C: tree.js      D3 横向树渲染
       ├─ Block D: ui.js        菜单/标签/搜索/过滤/移动分类
       └─ Block E: io.js        导出/导入 JSON
```

---

## Task 1: HTML 骨架 + CSS

**Files:**
- Create: `geektime_mindmap.html`

- [ ] **Step 1: 创建 HTML 骨架**

```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>极客时间课程脑图</title>
  <script src="https://d3js.org/d3.v7.min.js"></script>
  <style>
    /* ── Reset ── */
    *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'PingFang SC', sans-serif;
      background: #0f172a; color: #e2e8f0;
      height: 100vh; overflow: hidden;
      display: flex; flex-direction: column;
    }

    /* ── Toolbar ── */
    #toolbar {
      display: flex; align-items: center; gap: 8px;
      padding: 8px 16px; height: 48px;
      background: #1e293b; border-bottom: 1px solid #334155;
      flex-shrink: 0; z-index: 50;
    }
    #toolbar .title { font-size: 15px; font-weight: 700; color: #f1f5f9; margin-right: 8px; }
    #toolbar .sep { width: 1px; height: 20px; background: #334155; margin: 0 4px; }
    #toolbar .stats { margin-left: auto; display: flex; gap: 12px; font-size: 12px; color: #64748b; }
    #toolbar .stats span { display: flex; align-items: center; gap: 4px; }

    /* ── Buttons ── */
    .btn {
      padding: 5px 12px; border-radius: 6px; border: none;
      cursor: pointer; font-size: 12px; font-weight: 500;
      transition: background 0.15s, opacity 0.15s;
    }
    .btn-primary { background: #3b82f6; color: #fff; }
    .btn-primary:hover { background: #2563eb; }
    .btn-secondary { background: #334155; color: #e2e8f0; }
    .btn-secondary:hover { background: #475569; }
    .btn-ghost { background: transparent; color: #94a3b8; border: 1px solid #334155; }
    .btn-ghost:hover { background: #1e293b; }
    .btn-danger { background: #7f1d1d; color: #fca5a5; }
    .btn-danger:hover { background: #991b1b; }

    /* ── App layout ── */
    #app { display: flex; flex: 1; overflow: hidden; }

    /* ── Sidebar ── */
    #sidebar {
      width: 240px; flex-shrink: 0;
      background: #1e293b; border-right: 1px solid #334155;
      overflow-y: auto; padding: 12px;
      display: flex; flex-direction: column; gap: 4px;
    }
    #sidebar .s-section { margin-top: 12px; }
    #sidebar .s-label {
      font-size: 10px; font-weight: 600; color: #64748b;
      text-transform: uppercase; letter-spacing: 0.08em;
      padding: 0 4px; margin-bottom: 6px;
    }
    .filter-row {
      display: flex; align-items: center; gap: 6px;
      padding: 5px 6px; border-radius: 5px; cursor: pointer;
      font-size: 12px; color: #cbd5e1;
      transition: background 0.1s;
    }
    .filter-row:hover { background: #334155; }
    .filter-row input[type="checkbox"] { accent-color: #3b82f6; cursor: pointer; }
    .filter-row .badge {
      margin-left: auto; font-size: 10px; color: #64748b;
      background: #334155; padding: 1px 5px; border-radius: 10px;
    }

    #search-wrap { position: relative; }
    #search-input {
      width: 100%; padding: 6px 28px 6px 10px;
      background: #0f172a; border: 1px solid #334155;
      border-radius: 6px; color: #e2e8f0; font-size: 12px;
      outline: none;
    }
    #search-input:focus { border-color: #3b82f6; }
    #search-clear {
      position: absolute; right: 8px; top: 50%; transform: translateY(-50%);
      cursor: pointer; color: #64748b; font-size: 14px; display: none;
    }

    /* ── Canvas ── */
    #canvas { flex: 1; overflow: hidden; position: relative; }
    #canvas svg { width: 100%; height: 100%; }

    /* ── D3 nodes ── */
    .node { cursor: pointer; }
    .node-cat rect {
      rx: 6; ry: 6; stroke-width: 2; fill-opacity: 0.15;
      transition: fill-opacity 0.15s;
    }
    .node-cat:hover rect { fill-opacity: 0.3; }
    .node-cat text { font-size: 12px; font-weight: 600; }
    .node-course circle { stroke-width: 2; transition: r 0.15s; }
    .node-course:hover circle { r: 7; }
    .node-course text { font-size: 11px; }
    .node-course.status-deleted text { text-decoration: line-through; opacity: 0.4; }
    .node-course.dimmed { opacity: 0.2; }
    .link { fill: none; stroke: #334155; stroke-width: 1.5; }
    .link-cat { stroke: #475569; stroke-width: 2; }

    /* ── Context menu ── */
    #context-menu {
      position: fixed; display: none;
      background: #1e293b; border: 1px solid #334155;
      border-radius: 8px; padding: 5px; min-width: 188px;
      box-shadow: 0 8px 32px rgba(0,0,0,0.5); z-index: 200;
    }
    .cm-item {
      display: flex; align-items: center; gap: 8px;
      padding: 7px 10px; border-radius: 5px; cursor: pointer;
      font-size: 13px; color: #e2e8f0;
      transition: background 0.1s;
    }
    .cm-item:hover { background: #334155; }
    .cm-item.active { color: #60a5fa; }
    .cm-item.danger { color: #f87171; }
    .cm-item.muted { color: #64748b; }
    .cm-sep { height: 1px; background: #334155; margin: 4px 0; }
    .cm-sub { position: relative; }
    .cm-sub-menu {
      display: none; position: absolute;
      left: 100%; top: -5px;
      background: #1e293b; border: 1px solid #334155;
      border-radius: 8px; padding: 5px; min-width: 170px;
      box-shadow: 0 8px 32px rgba(0,0,0,0.5); z-index: 201;
      max-height: 280px; overflow-y: auto;
    }
    .cm-sub:hover .cm-sub-menu { display: block; }

    /* ── Tooltip ── */
    #tooltip {
      position: fixed; display: none; pointer-events: none;
      background: #1e293b; border: 1px solid #334155;
      border-radius: 8px; padding: 10px 14px;
      font-size: 12px; max-width: 260px; z-index: 300;
      box-shadow: 0 4px 16px rgba(0,0,0,0.4);
    }
    #tooltip .tt-name { font-weight: 600; color: #f1f5f9; margin-bottom: 4px; }
    #tooltip .tt-note { color: #94a3b8; font-size: 11px; }
    #tooltip .tt-tags { display: flex; flex-wrap: wrap; gap: 4px; margin-top: 6px; }
    #tooltip .tt-tag {
      font-size: 10px; padding: 2px 6px; border-radius: 10px;
      background: #334155; color: #cbd5e1;
    }

    /* ── Modals ── */
    .modal-overlay {
      position: fixed; inset: 0; background: rgba(0,0,0,0.6);
      display: none; align-items: center; justify-content: center; z-index: 400;
    }
    .modal-overlay.open { display: flex; }
    .modal {
      background: #1e293b; border: 1px solid #334155;
      border-radius: 12px; padding: 24px; width: 420px;
      box-shadow: 0 16px 48px rgba(0,0,0,0.5);
    }
    .modal h3 { font-size: 15px; font-weight: 700; margin-bottom: 14px; }
    .modal label { font-size: 12px; color: #94a3b8; display: block; margin-bottom: 5px; }
    .modal input[type="text"], .modal textarea, .modal select {
      width: 100%; background: #0f172a; border: 1px solid #334155;
      border-radius: 6px; color: #e2e8f0; padding: 8px 10px;
      font-size: 13px; outline: none; margin-bottom: 12px;
    }
    .modal input[type="text"]:focus,
    .modal textarea:focus { border-color: #3b82f6; }
    .modal textarea { resize: vertical; min-height: 80px; font-family: inherit; }
    .modal-footer { display: flex; gap: 8px; justify-content: flex-end; margin-top: 4px; }
    .modal .course-meta { font-size: 12px; color: #64748b; margin-bottom: 12px; }

    /* color swatches for tag editor */
    .color-swatches { display: flex; gap: 8px; margin-bottom: 12px; }
    .swatch {
      width: 24px; height: 24px; border-radius: 50%; cursor: pointer;
      border: 2px solid transparent; transition: border-color 0.15s;
    }
    .swatch.selected { border-color: #fff; }

    /* import modal */
    .import-info { background: #0f172a; border-radius: 6px; padding: 10px 12px; margin-bottom: 14px; }
    .import-info p { font-size: 12px; color: #94a3b8; margin-bottom: 4px; }
    .import-info strong { color: #e2e8f0; }
    .import-mode { display: flex; flex-direction: column; gap: 8px; margin-bottom: 14px; }
    .import-mode label {
      display: flex; align-items: flex-start; gap: 8px;
      padding: 8px 10px; border-radius: 6px; border: 1px solid #334155;
      cursor: pointer; color: #e2e8f0; font-size: 13px;
    }
    .import-mode label:hover { background: #0f172a; }
    .import-mode label input { margin-top: 2px; accent-color: #3b82f6; }
    .import-mode .mode-desc { font-size: 11px; color: #64748b; display: block; }

    /* legend */
    #legend {
      position: absolute; bottom: 16px; right: 16px;
      background: #1e293b; border: 1px solid #334155;
      border-radius: 8px; padding: 10px 14px; font-size: 11px;
    }
    #legend .leg-row { display: flex; align-items: center; gap: 6px; margin-bottom: 3px; }
    #legend .leg-dot { width: 9px; height: 9px; border-radius: 50%; border: 2px solid; }
    #legend .leg-row:last-child { margin-bottom: 0; }

    /* tag pill in sidebar */
    .tag-pill {
      display: flex; align-items: center; justify-content: space-between;
      padding: 4px 6px; border-radius: 5px; font-size: 12px;
      background: #0f172a; border: 1px solid #334155; margin-bottom: 4px;
    }
    .tag-pill .tag-label { display: flex; align-items: center; gap: 5px; }
    .tag-pill .tag-actions { display: flex; gap: 4px; }
    .tag-pill .tag-act {
      background: none; border: none; cursor: pointer;
      color: #64748b; font-size: 11px; padding: 1px 3px;
    }
    .tag-pill .tag-act:hover { color: #e2e8f0; }

    /* custom tag checkbox with color dot */
    .filter-row .color-dot {
      width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0;
    }

    /* sidebar toggle */
    #sidebar-toggle {
      position: absolute; left: 240px; top: 50%; transform: translateY(-50%);
      z-index: 10; background: #334155; border: none; color: #94a3b8;
      width: 16px; height: 36px; cursor: pointer; border-radius: 0 4px 4px 0;
      font-size: 10px; display: flex; align-items: center; justify-content: center;
    }
    #sidebar-toggle:hover { background: #475569; }
  </style>
</head>
<body>

<!-- ── Toolbar ── -->
<div id="toolbar">
  <span class="title">🗺️ 极客时间课程脑图</span>
  <div class="sep"></div>
  <button class="btn btn-primary" onclick="exportJSON()">📤 导出 JSON</button>
  <button class="btn btn-secondary" onclick="document.getElementById('file-input').click()">📥 导入 JSON</button>
  <input type="file" id="file-input" accept=".json" style="display:none" onchange="handleFileImport(event)">
  <div class="sep"></div>
  <button class="btn btn-ghost" onclick="expandAll()">展开全部</button>
  <button class="btn btn-ghost" onclick="collapseAll()">收起全部</button>
  <button class="btn btn-ghost" onclick="resetView()">⊙ 重置视图</button>
  <div class="stats" id="stats-bar">
    <span id="stat-important">⭐ 0</span>
    <span id="stat-learning">📚 0</span>
    <span id="stat-done">✅ 0</span>
    <span id="stat-deleted">🗑️ 0</span>
    <span id="stat-total" style="color:#94a3b8">共 0</span>
  </div>
</div>

<!-- ── App ── -->
<div id="app">

  <!-- Sidebar -->
  <div id="sidebar">

    <!-- Search -->
    <div id="search-wrap">
      <input id="search-input" type="text" placeholder="🔍 搜索课程名或备注..." oninput="onSearch(this.value)" onkeydown="if(event.key==='Escape'){clearSearch()}">
      <span id="search-clear" onclick="clearSearch()">✕</span>
    </div>

    <!-- Status filters -->
    <div class="s-section">
      <div class="s-label">状态过滤</div>
      <label class="filter-row"><input type="checkbox" id="f-normal" checked onchange="applyFilters()"> ◯ 未标注</label>
      <label class="filter-row"><input type="checkbox" id="f-important" checked onchange="applyFilters()"> ⭐ 重点</label>
      <label class="filter-row"><input type="checkbox" id="f-learning" checked onchange="applyFilters()"> 📚 学习中</label>
      <label class="filter-row"><input type="checkbox" id="f-done" checked onchange="applyFilters()"> ✅ 已完成</label>
      <label class="filter-row"><input type="checkbox" id="f-deleted" onchange="applyFilters()"> 🗑️ 显示已删除</label>
    </div>

    <!-- Custom tag filters (populated dynamically) -->
    <div class="s-section" id="section-tag-filter" style="display:none">
      <div class="s-label">自定义标签</div>
      <div id="tag-filter-list"></div>
    </div>

    <!-- Category filters -->
    <div class="s-section">
      <div class="s-label">分类过滤</div>
      <label class="filter-row">
        <input type="checkbox" id="f-cat-all" checked onchange="toggleAllCats(this.checked)"> 全选
      </label>
      <div id="cat-filter-list"></div>
    </div>

    <!-- Tag management -->
    <div class="s-section" id="section-tag-mgmt">
      <div class="s-label">自定义标签管理</div>
      <div id="tag-mgmt-list"></div>
      <button class="btn btn-ghost" style="width:100%;margin-top:4px;font-size:12px" onclick="openTagModal(null, null)">+ 新建标签</button>
    </div>

    <!-- Reset filters -->
    <div style="margin-top: auto; padding-top: 12px;">
      <button class="btn btn-ghost" style="width:100%;font-size:12px" onclick="resetFilters()">重置所有过滤条件</button>
    </div>

  </div><!-- /sidebar -->

  <!-- Canvas -->
  <div id="canvas">
    <svg id="svg"></svg>
    <div id="legend">
      <div class="leg-row"><div class="leg-dot" style="background:#334155;border-color:#475569"></div> 未标注</div>
      <div class="leg-row"><div class="leg-dot" style="background:#92400e;border-color:#f59e0b"></div> ⭐ 重点</div>
      <div class="leg-row"><div class="leg-dot" style="background:#1e3a5f;border-color:#3b82f6"></div> 📚 学习中</div>
      <div class="leg-row"><div class="leg-dot" style="background:#14532d;border-color:#22c55e"></div> ✅ 已完成</div>
      <div class="leg-row"><div class="leg-dot" style="background:#450a0a;border-color:#ef4444"></div> 🗑️ 已删除</div>
    </div>
  </div>

</div><!-- /app -->

<!-- ── Context menu ── -->
<div id="context-menu">
  <div class="cm-item" id="cm-important" onclick="setStatus('important')">⭐ 标记重点</div>
  <div class="cm-item" id="cm-learning"  onclick="setStatus('learning')">📚 学习中</div>
  <div class="cm-item" id="cm-done"      onclick="setStatus('done')">✅ 已完成</div>
  <div class="cm-sep"></div>
  <div class="cm-item cm-sub">
    🏷️ 管理自定义标签 ▸
    <div class="cm-sub-menu" id="cm-tag-list"></div>
  </div>
  <div class="cm-item cm-sub">
    📂 移动到分类 ▸
    <div class="cm-sub-menu" id="cm-move-list"></div>
  </div>
  <div class="cm-item" onclick="openNoteModal()">📝 添加备注</div>
  <div class="cm-sep"></div>
  <div class="cm-item danger" onclick="setStatus('deleted')">🗑️ 删除课程</div>
  <div class="cm-item muted"  onclick="resetCourse()">↩️ 恢复默认</div>
</div>

<!-- ── Tooltip ── -->
<div id="tooltip">
  <div class="tt-name" id="tt-name"></div>
  <div class="tt-note" id="tt-note"></div>
  <div class="tt-tags" id="tt-tags"></div>
</div>

<!-- ── Note Modal ── -->
<div class="modal-overlay" id="modal-note">
  <div class="modal">
    <h3>📝 课程备注</h3>
    <div class="course-meta" id="note-course-name"></div>
    <label>备注内容</label>
    <textarea id="note-textarea" placeholder="记录学习计划、心得或优先级..."></textarea>
    <div class="modal-footer">
      <button class="btn btn-ghost" onclick="closeModal('modal-note')">取消</button>
      <button class="btn btn-primary" onclick="saveNote()">保存</button>
    </div>
  </div>
</div>

<!-- ── Tag Modal ── -->
<div class="modal-overlay" id="modal-tag">
  <div class="modal">
    <h3 id="tag-modal-title">🏷️ 新建标签</h3>
    <input type="hidden" id="tag-edit-id">
    <input type="hidden" id="tag-apply-course">
    <label>标签名称</label>
    <input type="text" id="tag-name-input" placeholder="例如：下周必看">
    <label>选择颜色</label>
    <div class="color-swatches" id="color-swatches"></div>
    <label>选择 Emoji（可选）</label>
    <input type="text" id="tag-emoji-input" placeholder="例如：🔥" maxlength="2">
    <div class="modal-footer">
      <button class="btn btn-ghost" onclick="closeModal('modal-tag')">取消</button>
      <button class="btn btn-primary" onclick="saveTag()">保存标签</button>
    </div>
  </div>
</div>

<!-- ── Import Modal ── -->
<div class="modal-overlay" id="modal-import">
  <div class="modal">
    <h3>📥 导入确认</h3>
    <div class="import-info" id="import-info"></div>
    <div class="import-mode">
      <label>
        <input type="radio" name="import-mode" value="merge" checked>
        <div>
          <strong>合并</strong>（推荐）
          <span class="mode-desc">以导入文件为准；当前有、导入没有的标注保留。</span>
        </div>
      </label>
      <label>
        <input type="radio" name="import-mode" value="overwrite">
        <div>
          <strong>覆盖</strong>
          <span class="mode-desc">完全替换为导入文件状态，当前所有标注将丢失。</span>
        </div>
      </label>
    </div>
    <div class="modal-footer">
      <button class="btn btn-ghost" onclick="closeModal('modal-import')">取消</button>
      <button class="btn btn-primary" onclick="confirmImport()">确认导入</button>
    </div>
  </div>
</div>

</body>
</html>
```

- [ ] **Step 2: 在浏览器中打开，验证骨架**

用 `open geektime_mindmap.html` 或双击文件打开。

期望：
- 顶部工具栏可见，包含所有按钮
- 左侧侧边栏可见，含搜索框和过滤区域
- 主区域为深色背景（无树图，因数据和 D3 尚未添加）
- 无 JS 报错（开发者工具 Console 干净）

---

## Task 2: 课程数据常量（Block A）

**Files:**
- Modify: `geektime_mindmap.html` — 在 `</body>` 前插入 `<script>` Block A

- [ ] **Step 1: 插入课程数据常量**

在 `</body>` 前添加：

```html
<script>
// ════════════════════════════════════════════════
// Block A: COURSE_DATA — 所有课程原始数据（只读）
// ════════════════════════════════════════════════
const COURSE_DATA = [
  { id:'cat_lang', name:'编程语言', icon:'💻', courses:[
    {id:'lang_01',name:'Tony Bai · Go 语言第一课',group:'Go'},
    {id:'lang_02',name:'Go 语言核心36讲',group:'Go'},
    {id:'lang_03',name:'Go 并发编程实战课',group:'Go'},
    {id:'lang_04',name:'Go 语言项目开发实战',group:'Go'},
    {id:'lang_05',name:'Java核心技术面试精讲',group:'Java'},
    {id:'lang_06',name:'Java并发编程实战',group:'Java'},
    {id:'lang_07',name:'Java性能调优实战',group:'Java'},
    {id:'lang_08',name:'Java业务开发常见错误100例',group:'Java'},
    {id:'lang_09',name:'深入剖析 Java 新特性',group:'Java'},
    {id:'lang_10',name:'深入拆解Java虚拟机',group:'Java'},
    {id:'lang_11',name:'Python核心技术与实战',group:'Python'},
    {id:'lang_12',name:'Python自动化办公实战课',group:'Python'},
    {id:'lang_13',name:'陈天 · Rust 编程第一课',group:'Rust'},
    {id:'lang_14',name:'深入 C 语言和程序运行原理',group:'C/C++'},
    {id:'lang_15',name:'罗剑锋的C++实战笔记',group:'C/C++'},
    {id:'lang_16',name:'现代C++实战30讲',group:'C/C++'},
    {id:'lang_17',name:'朱涛 · Kotlin 编程第一课',group:'Kotlin'},
    {id:'lang_18',name:'JavaScript核心原理解析',group:'JS'},
  ]},
  { id:'cat_fe', name:'前端 & 移动端', icon:'🖥️', courses:[
    {id:'fe_01',name:'重学前端',group:'Web'},
    {id:'fe_02',name:'React Hooks 核心原理与实战',group:'Web'},
    {id:'fe_03',name:'玩转 Vue 3 全家桶',group:'Web'},
    {id:'fe_04',name:'图解 Google V8',group:'Web'},
    {id:'fe_05',name:'WebAssembly入门课',group:'Web'},
    {id:'fe_06',name:'浏览器工作原理与实践',group:'Web'},
    {id:'fe_07',name:'React Native 新架构实战课',group:'跨平台'},
    {id:'fe_08',name:'Flutter核心技术与实战',group:'跨平台'},
    {id:'fe_09',name:'Android开发高手课',group:'移动原生'},
    {id:'fe_10',name:'iOS开发高手课',group:'移动原生'},
  ]},
  { id:'cat_db', name:'数据库', icon:'🗄️', courses:[
    {id:'db_01',name:'MySQL 必知必会',group:'关系型'},
    {id:'db_02',name:'MySQL实战45讲',group:'关系型'},
    {id:'db_03',name:'SQL必知必会',group:'关系型'},
    {id:'db_04',name:'Redis核心技术与实战',group:'NoSQL'},
    {id:'db_05',name:'Redis源码剖析与实战',group:'NoSQL'},
    {id:'db_06',name:'etcd实战课',group:'分布式存储'},
    {id:'db_07',name:'分布式数据库30讲',group:'分布式存储'},
    {id:'db_08',name:'后端存储实战课',group:'分布式存储'},
  ]},
  { id:'cat_cloud', name:'分布式 & 云原生', icon:'☁️', courses:[
    {id:'cloud_01',name:'深入剖析Kubernetes',group:'容器编排'},
    {id:'cloud_02',name:'容器实战高手课',group:'容器编排'},
    {id:'cloud_03',name:'Spring Cloud 微服务项目实战',group:'微服务'},
    {id:'cloud_04',name:'从0开始学微服务',group:'微服务'},
    {id:'cloud_05',name:'Service Mesh实践指南',group:'Service Mesh'},
    {id:'cloud_06',name:'Serverless入门课',group:'Serverless'},
    {id:'cloud_07',name:'深入浅出云计算',group:'云计算'},
    {id:'cloud_08',name:'分布式技术原理与算法解析',group:'分布式理论'},
    {id:'cloud_09',name:'分布式协议与算法实战',group:'分布式理论'},
    {id:'cloud_10',name:'分布式金融架构课',group:'分布式理论'},
    {id:'cloud_11',name:'深入浅出分布式技术原理',group:'分布式理论'},
  ]},
  { id:'cat_arch', name:'架构设计', icon:'🏗️', courses:[
    {id:'arch_01',name:'从0开始学架构',group:'方法论'},
    {id:'arch_02',name:'郭东白的架构课',group:'方法论'},
    {id:'arch_03',name:'许式伟的架构课',group:'方法论'},
    {id:'arch_04',name:'周志明的软件架构课',group:'方法论'},
    {id:'arch_05',name:'高并发系统设计40问',group:'高并发'},
    {id:'arch_06',name:'李智慧 · 高并发架构实战课',group:'高并发'},
    {id:'arch_07',name:'如何设计一个秒杀系统',group:'实战案例'},
    {id:'arch_08',name:'手把手带你搭建秒杀系统',group:'实战案例'},
    {id:'arch_09',name:'架构实战案例解析',group:'实战案例'},
    {id:'arch_10',name:'DDD实战课',group:'领域建模'},
    {id:'arch_11',name:'如何落地业务建模',group:'领域建模'},
  ]},
  { id:'cat_mw', name:'消息队列 & 中间件', icon:'⚙️', courses:[
    {id:'mw_01',name:'Kafka核心技术与实战',group:'消息队列'},
    {id:'mw_02',name:'Kafka核心源码解读',group:'消息队列'},
    {id:'mw_03',name:'消息队列高手课',group:'消息队列'},
    {id:'mw_04',name:'即时消息技术剖析与实战',group:'消息队列'},
    {id:'mw_05',name:'RPC实战与核心原理',group:'RPC'},
    {id:'mw_06',name:'深入浅出gRPC',group:'RPC'},
    {id:'mw_07',name:'OpenResty从入门到实战',group:'网关'},
    {id:'mw_08',name:'深入拆解Tomcat & Jetty',group:'应用服务器'},
    {id:'mw_09',name:'Spring编程常见错误50例',group:'框架'},
  ]},
  { id:'cat_bigdata', name:'大数据', icon:'📊', courses:[
    {id:'bd_01',name:'从0开始学大数据',group:'平台'},
    {id:'bd_02',name:'大规模数据处理实战',group:'平台'},
    {id:'bd_03',name:'大数据经典论文解读',group:'平台'},
    {id:'bd_04',name:'Spark性能调优实战',group:'Spark'},
    {id:'bd_05',name:'零基础入门 Spark',group:'Spark'},
    {id:'bd_06',name:'数据中台实战课',group:'数据分析'},
    {id:'bd_07',name:'数据分析实战45讲',group:'数据分析'},
    {id:'bd_08',name:'数据分析思维课',group:'数据分析'},
  ]},
  { id:'cat_ai', name:'AI & 机器学习', icon:'🤖', courses:[
    {id:'ai_01',name:'人工智能基础课',group:'基础'},
    {id:'ai_02',name:'机器学习40讲',group:'机器学习'},
    {id:'ai_03',name:'零基础实战机器学习',group:'机器学习'},
    {id:'ai_04',name:'PyTorch 深度学习实战',group:'深度学习'},
    {id:'ai_05',name:'AI技术内参',group:'深度学习'},
    {id:'ai_06',name:'深度学习推荐系统实战',group:'推荐系统'},
    {id:'ai_07',name:'推荐系统三十六式',group:'推荐系统'},
    {id:'ai_08',name:'成为AI产品经理',group:'AI产品'},
  ]},
  { id:'cat_os', name:'操作系统 & 网络', icon:'🐧', courses:[
    {id:'os_01',name:'趣谈Linux操作系统',group:'Linux'},
    {id:'os_02',name:'Linux内核技术实战课',group:'Linux'},
    {id:'os_03',name:'Linux性能优化实战',group:'Linux'},
    {id:'os_04',name:'操作系统实战45讲',group:'Linux'},
    {id:'os_05',name:'eBPF 核心技术与实战',group:'Linux'},
    {id:'os_06',name:'趣谈网络协议',group:'网络'},
    {id:'os_07',name:'透视HTTP协议',group:'网络'},
    {id:'os_08',name:'网络编程实战',group:'网络'},
    {id:'os_09',name:'网络排查案例课',group:'网络'},
  ]},
  { id:'cat_cs', name:'计算机基础', icon:'🧮', courses:[
    {id:'cs_01',name:'深入浅出计算机组成原理',group:'组成原理'},
    {id:'cs_02',name:'编程高手必学的内存知识',group:'内存'},
    {id:'cs_03',name:'数据结构与算法之美',group:'算法'},
    {id:'cs_04',name:'动态规划面试宝典',group:'算法'},
    {id:'cs_05',name:'业务开发算法 50 讲',group:'算法'},
    {id:'cs_06',name:'检索技术核心20讲',group:'算法'},
    {id:'cs_07',name:'编译原理之美',group:'编译'},
    {id:'cs_08',name:'编译原理实战课',group:'编译'},
    {id:'cs_09',name:'程序员的数学基础课',group:'数学'},
    {id:'cs_10',name:'重学线性代数',group:'数学'},
  ]},
  { id:'cat_perf', name:'性能优化', icon:'⚡', courses:[
    {id:'perf_01',name:'系统性能调优必知必会',group:'通用'},
    {id:'perf_02',name:'性能优化高手课',group:'通用'},
    {id:'perf_03',name:'性能工程高手课',group:'通用'},
    {id:'perf_04',name:'高楼的性能工程实战课',group:'通用'},
    {id:'perf_05',name:'性能测试实战30讲',group:'压测'},
    {id:'perf_06',name:'全链路压测实战 30 讲',group:'压测'},
    {id:'perf_07',name:'容量保障核心技术与实战',group:'压测'},
  ]},
  { id:'cat_test', name:'测试 & 质量', icon:'🧪', courses:[
    {id:'test_01',name:'程序员的测试课',group:'综合'},
    {id:'test_02',name:'软件测试52讲',group:'综合'},
    {id:'test_03',name:'接口测试入门课',group:'综合'},
    {id:'test_04',name:'自动化测试高手课',group:'自动化'},
    {id:'test_05',name:'徐昊·TDD 项目实战 70 讲',group:'TDD'},
    {id:'test_06',name:'A|B测试从0到1',group:'AB测试'},
  ]},
  { id:'cat_sec', name:'安全', icon:'🔐', courses:[
    {id:'sec_01',name:'安全攻防技能30讲',group:'安全'},
    {id:'sec_02',name:'Web 漏洞挖掘实战',group:'安全'},
    {id:'sec_03',name:'反爬虫兵法演绎 20 讲',group:'安全'},
    {id:'sec_04',name:'OAuth 2.0实战课',group:'认证授权'},
    {id:'sec_05',name:'实用密码学',group:'密码学'},
  ]},
  { id:'cat_devops', name:'工程效能 & DevOps', icon:'🚀', courses:[
    {id:'devops_01',name:'DevOps实战笔记',group:'DevOps'},
    {id:'devops_02',name:'持续交付36讲',group:'CI/CD'},
    {id:'devops_03',name:'研发效率破局之道',group:'效能'},
    {id:'devops_04',name:'赵成的运维体系管理课',group:'运维'},
    {id:'devops_05',name:'SRE实战手册',group:'SRE'},
    {id:'devops_06',name:'遗留系统现代化实战',group:'系统改造'},
  ]},
  { id:'cat_code', name:'代码质量 & 工程', icon:'📐', courses:[
    {id:'code_01',name:'代码精进之路',group:'编码实践'},
    {id:'code_02',name:'代码之丑',group:'编码实践'},
    {id:'code_03',name:'设计模式之美',group:'设计模式'},
    {id:'code_04',name:'软件工程之美',group:'工程方法'},
    {id:'code_05',name:'软件设计之美',group:'工程方法'},
    {id:'code_06',name:'10x程序员工作法',group:'工程方法'},
    {id:'code_07',name:'左耳听风',group:'工程方法'},
    {id:'code_08',name:'全栈工程师修炼指南',group:'工程方法'},
    {id:'code_09',name:'Vim 实用技巧必知必会',group:'工具'},
    {id:'code_10',name:'正则表达式入门课',group:'工具'},
    {id:'code_11',name:'手把手带你写一个 Web 框架',group:'实战'},
    {id:'code_12',name:'手把手带你写一门编程语言',group:'实战'},
  ]},
  { id:'cat_mgmt', name:'技术管理 & 职场', icon:'👔', courses:[
    {id:'mgmt_01',name:'技术管理实战36讲',group:'管理'},
    {id:'mgmt_02',name:'技术管理案例课',group:'管理'},
    {id:'mgmt_03',name:'技术领导力实战笔记',group:'管理'},
    {id:'mgmt_04',name:'乔新亮的CTO成长复盘',group:'管理'},
    {id:'mgmt_05',name:'朱赟的技术管理课',group:'管理'},
    {id:'mgmt_06',name:'黄勇的OKR实战笔记',group:'效率'},
    {id:'mgmt_07',name:'流程型组织15讲',group:'效率'},
    {id:'mgmt_08',name:'项目管理实战20讲',group:'效率'},
    {id:'mgmt_09',name:'大厂晋升指南',group:'职场'},
    {id:'mgmt_10',name:'面试现场',group:'职场'},
    {id:'mgmt_11',name:'后端技术面试38讲',group:'职场'},
    {id:'mgmt_12',name:'技术面试官识人手册',group:'职场'},
    {id:'mgmt_13',name:'职场求生攻略',group:'职场'},
    {id:'mgmt_14',name:'程序员进阶攻略',group:'职场'},
  ]},
  { id:'cat_product', name:'产品 & 设计', icon:'🎨', courses:[
    {id:'prod_01',name:'邱岳的产品实战',group:'产品'},
    {id:'prod_02',name:'邱岳的产品手记',group:'产品'},
    {id:'prod_03',name:'苏杰的产品创新课',group:'产品'},
    {id:'prod_04',name:'硅谷产品实战36讲',group:'产品'},
    {id:'prod_05',name:'大厂广告产品心法',group:'产品'},
    {id:'prod_06',name:'用户体验设计实战课',group:'设计'},
    {id:'prod_07',name:'基于人因的用户体验设计课',group:'设计'},
    {id:'prod_08',name:'体验设计案例课',group:'设计'},
    {id:'prod_09',name:'跟月影学可视化',group:'可视化'},
    {id:'prod_10',name:'从0开始做增长',group:'增长运营'},
    {id:'prod_11',name:'To B市场品牌实战课',group:'增长运营'},
  ]},
  { id:'cat_other', name:'非技术 & 兴趣', icon:'🌱', courses:[
    {id:'oth_01',name:'如何成为学习高手',group:'学习方法'},
    {id:'oth_02',name:'跟着高手学复盘',group:'学习方法'},
    {id:'oth_03',name:'人人都用得上的写作课',group:'写作表达'},
    {id:'oth_04',name:'讲好故事',group:'写作表达'},
    {id:'oth_05',name:'编辑训练营',group:'写作表达'},
    {id:'oth_06',name:'视觉笔记入门课',group:'写作表达'},
    {id:'oth_07',name:'如何读懂一首诗',group:'写作表达'},
    {id:'oth_08',name:'如何看懂一幅画',group:'写作表达'},
    {id:'oth_09',name:'程序员的个人财富课',group:'职业财富'},
    {id:'oth_10',name:'白话法律42讲',group:'职业财富'},
    {id:'oth_11',name:'超级访谈：对话汤峥嵘',group:'访谈'},
    {id:'oth_12',name:'超级访谈：对话张雪峰',group:'访谈'},
    {id:'oth_13',name:'互联网人的英语私教课',group:'语言'},
    {id:'oth_14',name:'人人都能学会的编程入门课',group:'语言'},
    {id:'oth_15',name:'从0打造音视频直播系统',group:'音视频'},
    {id:'oth_16',name:'搞定音频技术',group:'音视频'},
    {id:'oth_17',name:'攻克视频技术',group:'音视频'},
    {id:'oth_18',name:'说透5G',group:'科技科普'},
    {id:'oth_19',name:'说透低代码',group:'科技科普'},
    {id:'oth_20',name:'说透敏捷',group:'科技科普'},
    {id:'oth_21',name:'说透区块链',group:'科技科普'},
    {id:'oth_22',name:'深入浅出区块链',group:'科技科普'},
    {id:'oth_23',name:'说透数字化转型',group:'科技科普'},
    {id:'oth_24',name:'说透芯片',group:'科技科普'},
    {id:'oth_25',name:'说透中台',group:'科技科普'},
    {id:'oth_26',name:'物联网开发实战',group:'科技科普'},
    {id:'oth_27',name:'从0开始学游戏开发',group:'游戏'},
    {id:'oth_28',name:'打造爆款短视频',group:'创作'},
    {id:'oth_29',name:'爱上跑步',group:'健康兴趣'},
    {id:'oth_30',name:'恋爱必修课',group:'健康兴趣'},
    {id:'oth_31',name:'手把手教你玩音乐',group:'健康兴趣'},
    {id:'oth_32',name:'摄影入门课',group:'健康兴趣'},
    {id:'oth_33',name:'手机摄影',group:'健康兴趣'},
    {id:'oth_34',name:'去无方向的信',group:'健康兴趣'},
    {id:'oth_35',name:'如何做好一场技术演讲',group:'演讲'},
  ]},
];

// 每个分类的主题色（与分类顺序一一对应）
const CAT_COLORS = [
  '#6366f1','#06b6d4','#f59e0b','#8b5cf6','#3b82f6',
  '#f97316','#22c55e','#a855f7','#10b981','#64748b',
  '#ef4444','#14b8a6','#84cc16','#ec4899','#0ea5e9',
  '#f43f5e','#e879f9','#4ade80'
];

// 快速查找：catId → color
const CAT_COLOR_MAP = {};
COURSE_DATA.forEach((cat, i) => { CAT_COLOR_MAP[cat.id] = CAT_COLORS[i]; });
</script>
```

- [ ] **Step 2: 验证数据加载**

打开浏览器控制台，执行：

```js
console.log('分类数:', COURSE_DATA.length);        // 期望: 18
console.log('总课程:', COURSE_DATA.reduce((s,c)=>s+c.courses.length,0)); // 期望: ~185
console.log('第1类第1门:', COURSE_DATA[0].courses[0].name); // 期望: "Tony Bai · Go 语言第一课"
```

期望：三条输出均正确，无 undefined。

---

## Task 3: 状态管理（Block B）

**Files:**
- Modify: `geektime_mindmap.html` — Block A 之后插入 Block B

- [ ] **Step 1: 插入状态管理代码**

紧接 Block A 的 `</script>` 后新增：

```html
<script>
// ════════════════════════════════════════════════
// Block B: State Management
// ════════════════════════════════════════════════

// 运行时课程状态：{ [courseId]: { status, customTagIds, note, startedAt, doneAt } }
let courseState = {};

// 自定义标签定义：{ [tagId]: { id, label, color, emoji } }
let customTags = {};

// 运行时分类数据（可被"移动到分类"操作修改，初始从 COURSE_DATA 深拷贝）
let runtimeCategories = [];

// 过滤器状态
let filters = {
  search: '',
  statuses: new Set(['normal','important','learning','done']),  // deleted 默认不显示
  tagIds: new Set(),   // 空集 = 不按标签过滤
  catIds: new Set(),   // 空集 = 显示全部
};

// 初始化运行时数据（从 COURSE_DATA 深拷贝，保留原始顺序）
function initState() {
  runtimeCategories = COURSE_DATA.map(cat => ({
    ...cat,
    courses: cat.courses.map(c => ({ ...c })),
  }));
  runtimeCategories.forEach(cat => {
    cat.courses.forEach(c => {
      courseState[c.id] = { status:'normal', customTagIds:[], note:'', startedAt:null, doneAt:null };
    });
  });
  filters.catIds = new Set(runtimeCategories.map(c => c.id));
}

// ── 状态读写 ──────────────────────────────────────

function getState(courseId) {
  return courseState[courseId] || { status:'normal', customTagIds:[], note:'', startedAt:null, doneAt:null };
}

function setState(courseId, patch) {
  const prev = getState(courseId);
  const next = { ...prev, ...patch };
  // 自动打时间戳
  if (patch.status === 'learning' && prev.status !== 'learning') next.startedAt = todayStr();
  if (patch.status === 'done'     && prev.status !== 'done')     next.doneAt    = todayStr();
  courseState[courseId] = next;
}

function todayStr() {
  return new Date().toISOString().slice(0, 10);
}

// ── 标签管理 ──────────────────────────────────────

function createTag({ label, color, emoji }) {
  const id = 'tag_' + Date.now();
  customTags[id] = { id, label, color, emoji: emoji || '' };
  return id;
}

function updateTag(id, patch) {
  if (customTags[id]) customTags[id] = { ...customTags[id], ...patch };
}

function deleteTag(tagId) {
  delete customTags[tagId];
  // 从所有课程中移除该标签
  Object.keys(courseState).forEach(cid => {
    courseState[cid].customTagIds = courseState[cid].customTagIds.filter(t => t !== tagId);
  });
}

function toggleCourseTag(courseId, tagId) {
  const st = getState(courseId);
  const ids = st.customTagIds || [];
  const next = ids.includes(tagId) ? ids.filter(t => t !== tagId) : [...ids, tagId];
  setState(courseId, { customTagIds: next });
}

// ── 分类移动 ──────────────────────────────────────

function moveCourse(courseId, targetCatId) {
  let course = null;
  // 从原分类移除
  runtimeCategories.forEach(cat => {
    const idx = cat.courses.findIndex(c => c.id === courseId);
    if (idx !== -1) { [course] = cat.courses.splice(idx, 1); }
  });
  // 加入目标分类
  if (course) {
    const target = runtimeCategories.find(c => c.id === targetCatId);
    if (target) target.courses.push(course);
  }
}

// ── 统计 ──────────────────────────────────────────

function calcStats() {
  const s = { total:0, important:0, learning:0, done:0, deleted:0 };
  runtimeCategories.forEach(cat => {
    cat.courses.forEach(c => {
      s.total++;
      const st = getState(c.id).status;
      if (s[st] !== undefined) s[st]++;
    });
  });
  return s;
}

function updateStatsBar() {
  const s = calcStats();
  document.getElementById('stat-important').textContent = `⭐ ${s.important}`;
  document.getElementById('stat-learning').textContent  = `📚 ${s.learning}`;
  document.getElementById('stat-done').textContent      = `✅ ${s.done}`;
  document.getElementById('stat-deleted').textContent   = `🗑️ ${s.deleted}`;
  document.getElementById('stat-total').textContent     = `共 ${s.total}`;
}

// ── 可见性判断（过滤 + 搜索）──────────────────────

function isCourseVisible(course) {
  const st = getState(course.id);
  // deleted 独立开关
  if (st.status === 'deleted' && !filters.statuses.has('deleted')) return false;
  // 状态过滤
  if (st.status !== 'deleted' && !filters.statuses.has(st.status)) return false;
  // 自定义标签过滤（OR）
  if (filters.tagIds.size > 0) {
    const hasTag = st.customTagIds.some(tid => filters.tagIds.has(tid));
    if (!hasTag) return false;
  }
  // 搜索
  if (filters.search) {
    const q = filters.search.toLowerCase();
    const nameMatch = course.name.toLowerCase().includes(q);
    const noteMatch = st.note.toLowerCase().includes(q);
    if (!nameMatch && !noteMatch) return false;
  }
  return true;
}
</script>
```

- [ ] **Step 2: 验证状态管理**

控制台执行（页面刷新后，数据已初始化之前的 initState 尚未调用，这里先手动测试）：

```js
initState();
setState('lang_01', { status: 'important' });
console.log(getState('lang_01').status);   // 期望: "important"
const tid = createTag({ label: '测试', color: '#3b82f6', emoji: '🔥' });
toggleCourseTag('lang_01', tid);
console.log(getState('lang_01').customTagIds.includes(tid)); // 期望: true
toggleCourseTag('lang_01', tid);
console.log(getState('lang_01').customTagIds.length);        // 期望: 0
console.log(calcStats().total);  // 期望: ~185
```

---

## Task 4: D3 横向树渲染（Block C）

**Files:**
- Modify: `geektime_mindmap.html` — Block B 后插入 Block C

- [ ] **Step 1: 插入 D3 渲染核心代码**

```html
<script>
// ════════════════════════════════════════════════
// Block C: D3 Tree Rendering
// ════════════════════════════════════════════════

const NODE_HEIGHT = 22;   // 每个课程节点的垂直间距
const CAT_PADDING = 14;   // 分类节点上下额外间距
const X_STEP_CAT  = 180;  // 根→分类 水平距离
const X_STEP_COURSE = 220; // 分类→课程 水平距离

let svgEl, gMain, zoomBehavior;
// 记录各分类的展开状态（默认全部收起）
const expandedCats = new Set();

// ── 初始化 SVG ────────────────────────────────────

function initSVG() {
  const container = document.getElementById('canvas');
  svgEl = d3.select('#svg')
    .attr('width',  container.clientWidth)
    .attr('height', container.clientHeight);

  zoomBehavior = d3.zoom()
    .scaleExtent([0.1, 3])
    .on('zoom', e => gMain.attr('transform', e.transform));

  svgEl.call(zoomBehavior);
  svgEl.on('dblclick.zoom', null); // 禁用双击缩放，留给重置视图

  gMain = svgEl.append('g').attr('class', 'g-main');

  // 双击画布空白处重置视图
  svgEl.on('dblclick', (e) => {
    if (e.target === svgEl.node() || e.target.tagName === 'svg') resetView();
  });
}

// ── 构建树形数据 ──────────────────────────────────

function buildTreeData() {
  const visibleCats = runtimeCategories.filter(cat => {
    if (!filters.catIds.has(cat.id)) return false;
    // 分类内有可见课程，或分类本身未被过滤时才显示
    if (filters.search || filters.tagIds.size > 0) {
      return cat.courses.some(c => isCourseVisible(c));
    }
    return true;
  });

  return {
    id: 'root',
    name: '极客时间',
    type: 'root',
    children: visibleCats.map(cat => {
      const visibleCourses = cat.courses.filter(c => isCourseVisible(c));
      return {
        id: cat.id,
        name: `${cat.icon} ${cat.name}`,
        type: 'category',
        color: CAT_COLOR_MAP[cat.id],
        courseCount: cat.courses.filter(c => getState(c.id).status !== 'deleted').length,
        totalCount: cat.courses.length,
        // 展开时显示课程，收起时子节点为空
        children: expandedCats.has(cat.id) ? visibleCourses.map(course => ({
          id: course.id,
          name: course.name,
          type: 'course',
          status: getState(course.id).status,
          customTagIds: getState(course.id).customTagIds,
          note: getState(course.id).note,
        })) : [],
      };
    }),
  };
}

// ── 主渲染函数 ────────────────────────────────────

function render() {
  gMain.selectAll('*').remove();

  const data = buildTreeData();
  if (!data.children.length) return;

  // 用自定义布局手动计算坐标（比 d3.tree 更好控制节点间距）
  const nodes = [];
  const links = [];

  // 根节点坐标
  const rootNode = { ...data, x: 0, y: 0 };
  nodes.push(rootNode);

  // 为每个分类和其课程分配 x/y
  let yOffset = 0;
  data.children.forEach(cat => {
    const catCourses = cat.children || [];
    const catHeight = Math.max(
      NODE_HEIGHT,
      catCourses.length * NODE_HEIGHT + CAT_PADDING * 2
    );
    const catY = yOffset + catHeight / 2;
    const catNode = { ...cat, x: X_STEP_CAT, y: catY };
    nodes.push(catNode);
    links.push({ source: rootNode, target: catNode, type: 'cat' });

    // 课程节点
    let courseY = yOffset + CAT_PADDING;
    catCourses.forEach(course => {
      const courseNode = { ...course, x: X_STEP_CAT + X_STEP_COURSE, y: courseY + NODE_HEIGHT / 2 };
      nodes.push(courseNode);
      links.push({ source: catNode, target: courseNode, type: 'course' });
      courseY += NODE_HEIGHT;
    });

    yOffset += catHeight;
  });

  // ── 绘制连线 ──────────────────────────────────

  const linkGen = d3.linkHorizontal()
    .x(d => d.x)
    .y(d => d.y);

  gMain.append('g').attr('class', 'links')
    .selectAll('path')
    .data(links)
    .join('path')
    .attr('class', d => d.type === 'cat' ? 'link link-cat' : 'link')
    .attr('d', d => linkGen({ source: { x: d.source.x, y: d.source.y }, target: { x: d.target.x, y: d.target.y } }))
    .attr('stroke', d => {
      if (d.type === 'cat') return d.target.color || '#475569';
      const st = d.target.status;
      return STATUS_STYLE[st]?.stroke || STATUS_STYLE.normal.stroke;
    })
    .attr('opacity', 0.6);

  // ── 绘制节点 ──────────────────────────────────

  const nodeG = gMain.append('g').attr('class', 'nodes')
    .selectAll('g')
    .data(nodes)
    .join('g')
    .attr('class', d => `node node-${d.type}${d.type==='course' ? ' status-'+d.status : ''}`)
    .attr('transform', d => `translate(${d.x},${d.y})`);

  // 根节点
  const rootG = nodeG.filter(d => d.type === 'root');
  rootG.append('circle').attr('r', 28).attr('fill', '#0f172a').attr('stroke', '#f59e0b').attr('stroke-width', 2.5);
  rootG.append('text').attr('text-anchor','middle').attr('dy','0.35em')
    .attr('fill','#f59e0b').attr('font-size','13px').attr('font-weight','700')
    .text('极客时间');

  // 分类节点
  const catG = nodeG.filter(d => d.type === 'category');
  catG.append('rect')
    .attr('x', -4).attr('y', -13)
    .attr('width', d => measureText(d.name) + 24)
    .attr('height', 26)
    .attr('rx', 6).attr('ry', 6)
    .attr('fill', d => d.color)
    .attr('fill-opacity', 0.15)
    .attr('stroke', d => d.color)
    .attr('stroke-width', 1.5);
  catG.append('text')
    .attr('x', 8).attr('dy', '0.35em')
    .attr('fill', d => d.color)
    .attr('font-size', '12px').attr('font-weight', '600')
    .text(d => d.name);
  // 课程计数徽章
  catG.append('text')
    .attr('x', d => measureText(d.name) + 28)
    .attr('dy', '0.35em')
    .attr('fill', d => d.color + '99')
    .attr('font-size', '10px')
    .text(d => {
      const isOpen = expandedCats.has(d.id);
      return isOpen ? `${d.courseCount}门 ▾` : `${d.courseCount}门 ▸`;
    });
  // 点击展开/收起
  catG.style('cursor', 'pointer')
    .on('click', (e, d) => { e.stopPropagation(); toggleCat(d.id); });

  // 课程节点
  const courseG = nodeG.filter(d => d.type === 'course');
  courseG.append('circle')
    .attr('r', 5)
    .attr('fill', d => STATUS_STYLE[d.status]?.fill || STATUS_STYLE.normal.fill)
    .attr('stroke', d => STATUS_STYLE[d.status]?.stroke || STATUS_STYLE.normal.stroke)
    .attr('stroke-width', 1.5);
  // 自定义标签描边（最多显示第一个）
  courseG.filter(d => d.customTagIds && d.customTagIds.length > 0)
    .append('circle')
    .attr('r', 7)
    .attr('fill', 'none')
    .attr('stroke', d => {
      const tag = customTags[d.customTagIds[0]];
      return tag ? tag.color : 'transparent';
    })
    .attr('stroke-width', 1.5)
    .attr('stroke-dasharray', '3 2');

  courseG.append('text')
    .attr('x', 10).attr('dy', '0.35em')
    .attr('fill', d => STATUS_STYLE[d.status]?.text || STATUS_STYLE.normal.text)
    .attr('font-size', '11px')
    .attr('text-decoration', d => d.status === 'deleted' ? 'line-through' : 'none')
    .text(d => truncate(d.name, 26));

  // 状态图标
  courseG.filter(d => STATUS_STYLE[d.status]?.icon)
    .append('text')
    .attr('x', -12).attr('dy', '0.35em')
    .attr('font-size', '9px').attr('text-anchor', 'middle')
    .text(d => STATUS_STYLE[d.status].icon);

  // 备注小圆点
  courseG.filter(d => d.note && d.note.length > 0)
    .append('circle')
    .attr('cx', 0).attr('cy', -8)
    .attr('r', 3)
    .attr('fill', '#a78bfa');

  // 课程交互
  courseG
    .style('cursor', 'pointer')
    .on('click',       (e, d) => { e.stopPropagation(); showContextMenu(e, d); })
    .on('contextmenu', (e, d) => { e.preventDefault(); showContextMenu(e, d); })
    .on('mouseenter',  (e, d) => showTooltip(e, d))
    .on('mouseleave',  ()     => hideTooltip());

  updateStatsBar();
}

// ── 工具函数 ──────────────────────────────────────

const STATUS_STYLE = {
  normal:    { fill:'#1e293b', stroke:'#475569', text:'#94a3b8', icon:'' },
  important: { fill:'#92400e', stroke:'#f59e0b', text:'#fbbf24', icon:'⭐' },
  learning:  { fill:'#1e3a5f', stroke:'#3b82f6', text:'#60a5fa', icon:'📚' },
  done:      { fill:'#14532d', stroke:'#22c55e', text:'#4ade80', icon:'✅' },
  deleted:   { fill:'#1c0a0a', stroke:'#ef4444', text:'#6b7280', icon:'🗑️' },
};

const _canvas = document.createElement('canvas');
const _ctx = _canvas.getContext('2d');
_ctx.font = '12px -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif';
function measureText(str) { return _ctx.measureText(str).width; }

function truncate(str, maxLen) {
  return str.length > maxLen ? str.slice(0, maxLen) + '…' : str;
}

// ── 展开/收起 ─────────────────────────────────────

function toggleCat(catId) {
  if (expandedCats.has(catId)) expandedCats.delete(catId);
  else expandedCats.add(catId);
  render();
}

function expandAll()  { runtimeCategories.forEach(c => expandedCats.add(c.id)); render(); }
function collapseAll(){ expandedCats.clear(); render(); }
function resetView()  {
  const h = document.getElementById('canvas').clientHeight;
  svgEl.transition().duration(500)
    .call(zoomBehavior.transform, d3.zoomIdentity.translate(60, h / 2).scale(0.9));
}
</script>
```

- [ ] **Step 2: 在 `initState()` 调用之后添加初始化入口**

在所有 Block 脚本之后（文件末尾 `</body>` 前）添加：

```html
<script>
// ── App 启动 ──────────────────────────────────────
window.addEventListener('DOMContentLoaded', () => {
  initState();
  buildSidebar();   // Task 5 中实现
  initSVG();
  resetView();
  render();
});
window.addEventListener('resize', () => {
  const c = document.getElementById('canvas');
  svgEl.attr('width', c.clientWidth).attr('height', c.clientHeight);
  render();
});
</script>
```

- [ ] **Step 3: 验证树图渲染**

刷新页面，期望：
- 根节点「极客时间」出现在左侧
- 18 个分类节点向右展开，每个带彩色圆角矩形和课程计数
- 点击任意分类节点展开，显示该分类课程列表
- 滚轮缩放、拖拽平移正常
- Console 无报错

---

## Task 5: 侧边栏动态构建（Block D Part 1）

**Files:**
- Modify: `geektime_mindmap.html` — Block C 后插入 Block D

- [ ] **Step 1: 插入侧边栏构建代码**

```html
<script>
// ════════════════════════════════════════════════
// Block D: UI Logic
// ════════════════════════════════════════════════

// ── 侧边栏：分类过滤列表 ─────────────────────────

function buildSidebar() {
  // 构建分类过滤复选框
  const catList = document.getElementById('cat-filter-list');
  catList.innerHTML = '';
  runtimeCategories.forEach(cat => {
    const label = document.createElement('label');
    label.className = 'filter-row';
    label.innerHTML = `
      <input type="checkbox" id="f-cat-${cat.id}" checked onchange="onCatFilterChange()">
      ${cat.icon} ${cat.name}
      <span class="badge">${cat.courses.length}</span>`;
    catList.appendChild(label);
  });
  refreshTagFilterList();
  refreshTagMgmtList();
}

function onCatFilterChange() {
  const allChecked = runtimeCategories.every(cat =>
    document.getElementById(`f-cat-${cat.id}`)?.checked
  );
  document.getElementById('f-cat-all').checked = allChecked;
  filters.catIds = new Set(
    runtimeCategories
      .filter(cat => document.getElementById(`f-cat-${cat.id}`)?.checked)
      .map(c => c.id)
  );
  render();
}

function toggleAllCats(checked) {
  runtimeCategories.forEach(cat => {
    const el = document.getElementById(`f-cat-${cat.id}`);
    if (el) el.checked = checked;
  });
  filters.catIds = checked ? new Set(runtimeCategories.map(c => c.id)) : new Set();
  render();
}

// ── 侧边栏：自定义标签过滤 ───────────────────────

function refreshTagFilterList() {
  const tagIds = Object.keys(customTags);
  const section = document.getElementById('section-tag-filter');
  section.style.display = tagIds.length ? '' : 'none';

  const list = document.getElementById('tag-filter-list');
  list.innerHTML = '';
  tagIds.forEach(tid => {
    const tag = customTags[tid];
    const label = document.createElement('label');
    label.className = 'filter-row';
    label.innerHTML = `
      <input type="checkbox" id="f-tag-${tid}" onchange="onTagFilterChange()">
      <span class="color-dot" style="background:${tag.color}"></span>
      ${tag.emoji} ${tag.label}`;
    list.appendChild(label);
  });
}

function onTagFilterChange() {
  filters.tagIds = new Set(
    Object.keys(customTags).filter(tid => document.getElementById(`f-tag-${tid}`)?.checked)
  );
  render();
}

// ── 侧边栏：标签管理列表 ─────────────────────────

function refreshTagMgmtList() {
  const list = document.getElementById('tag-mgmt-list');
  list.innerHTML = '';
  Object.values(customTags).forEach(tag => {
    const div = document.createElement('div');
    div.className = 'tag-pill';
    div.innerHTML = `
      <span class="tag-label">
        <span class="color-dot" style="background:${tag.color};width:10px;height:10px;border-radius:50%;display:inline-block"></span>
        ${tag.emoji} ${tag.label}
      </span>
      <span class="tag-actions">
        <button class="tag-act" onclick="openTagModal('${tag.id}', null)" title="编辑">✏️</button>
        <button class="tag-act" onclick="deleteTagAndRefresh('${tag.id}')" title="删除">🗑️</button>
      </span>`;
    list.appendChild(div);
  });
}

function deleteTagAndRefresh(tagId) {
  if (!confirm(`确定删除标签「${customTags[tagId]?.label}」？已打标签的课程将自动移除。`)) return;
  deleteTag(tagId);
  refreshTagFilterList();
  refreshTagMgmtList();
  render();
}

// ── 过滤应用 ──────────────────────────────────────

function applyFilters() {
  filters.statuses = new Set();
  if (document.getElementById('f-normal')?.checked)    filters.statuses.add('normal');
  if (document.getElementById('f-important')?.checked) filters.statuses.add('important');
  if (document.getElementById('f-learning')?.checked)  filters.statuses.add('learning');
  if (document.getElementById('f-done')?.checked)      filters.statuses.add('done');
  if (document.getElementById('f-deleted')?.checked)   filters.statuses.add('deleted');
  render();
}

function resetFilters() {
  ['f-normal','f-important','f-learning','f-done'].forEach(id => {
    const el = document.getElementById(id); if (el) el.checked = true;
  });
  const fd = document.getElementById('f-deleted'); if (fd) fd.checked = false;
  Object.keys(customTags).forEach(tid => {
    const el = document.getElementById(`f-tag-${tid}`); if (el) el.checked = false;
  });
  toggleAllCats(true);
  clearSearch();
  filters.statuses = new Set(['normal','important','learning','done']);
  filters.tagIds = new Set();
  render();
}
</script>
```

- [ ] **Step 2: 验证侧边栏**

刷新页面，期望：
- 侧边栏分类过滤区出现 18 个分类复选框，每个带课程数徽章
- 取消勾选某个分类 → 树图对应分类消失
- 「取消全选」→ 树图清空，「全选」→ 恢复
- 状态过滤复选框勾选/取消生效

---

## Task 6: 搜索功能

**Files:**
- Modify: `geektime_mindmap.html` — Block D 中追加

- [ ] **Step 1: 追加搜索代码到 Block D**

```js
// ── 搜索 ──────────────────────────────────────────

function onSearch(value) {
  filters.search = value.trim();
  document.getElementById('search-clear').style.display = value ? 'block' : 'none';
  // 搜索时自动展开所有分类以显示匹配结果
  if (filters.search) {
    runtimeCategories.forEach(cat => {
      const hasMatch = cat.courses.some(c => isCourseVisible(c));
      if (hasMatch) expandedCats.add(cat.id);
    });
  }
  render();
}

function clearSearch() {
  const input = document.getElementById('search-input');
  input.value = '';
  document.getElementById('search-clear').style.display = 'none';
  filters.search = '';
  render();
}
```

- [ ] **Step 2: 验证搜索**

在搜索框输入「Redis」，期望：
- 只有包含"Redis"的课程可见
- 其所在分类自动展开
- 清空搜索框或按 Esc → 恢复全部

---

## Task 7: 右键菜单 + 状态操作

**Files:**
- Modify: `geektime_mindmap.html` — Block D 中追加

- [ ] **Step 1: 追加右键菜单代码**

```js
// ── 右键菜单 ──────────────────────────────────────

let ctxCourseId = null; // 当前右键的课程 ID

function showContextMenu(event, d) {
  event.stopPropagation();
  ctxCourseId = d.id;
  const menu = document.getElementById('context-menu');

  // 刷新状态高亮
  const st = getState(d.id).status;
  ['important','learning','done'].forEach(s => {
    document.getElementById(`cm-${s}`)?.classList.toggle('active', st === s);
  });

  // 刷新标签子菜单
  buildTagSubMenu(d.id);
  // 刷新移动分类子菜单
  buildMoveSubMenu(d.id);

  // 定位
  const x = Math.min(event.clientX, window.innerWidth  - 200);
  const y = Math.min(event.clientY, window.innerHeight - 240);
  menu.style.left    = x + 'px';
  menu.style.top     = y + 'px';
  menu.style.display = 'block';
}

function hideContextMenu() {
  document.getElementById('context-menu').style.display = 'none';
  ctxCourseId = null;
}

function setStatus(status) {
  if (!ctxCourseId) return;
  const prev = getState(ctxCourseId).status;
  // 再次点击同一状态 → 恢复 normal
  setState(ctxCourseId, { status: prev === status ? 'normal' : status });
  hideContextMenu();
  render();
}

function resetCourse() {
  if (!ctxCourseId) return;
  courseState[ctxCourseId] = { status:'normal', customTagIds:[], note:'', startedAt:null, doneAt:null };
  hideContextMenu();
  render();
}

// 全局点击关闭菜单
document.addEventListener('click', e => {
  if (!e.target.closest('#context-menu')) hideContextMenu();
});
```

- [ ] **Step 2: 验证右键菜单**

右键（或左键单击）任意课程节点，期望：
- 菜单弹出，定位在鼠标附近
- 点击「⭐ 标记重点」→ 节点变金色，再点击取消 → 复灰色
- 点击「🗑️ 删除课程」→ 节点默认消失（因 f-deleted 未勾选）
- 勾选「显示已删除」→ 已删除节点以删除线样式重新出现
- 点击「↩️ 恢复默认」→ 状态清空

---

## Task 8: 备注编辑

**Files:**
- Modify: `geektime_mindmap.html` — Block D 中追加

- [ ] **Step 1: 追加备注代码**

```js
// ── 备注 ──────────────────────────────────────────

function openNoteModal() {
  if (!ctxCourseId) return;
  hideContextMenu();
  const course = findCourse(ctxCourseId);
  document.getElementById('note-course-name').textContent = course?.name || ctxCourseId;
  document.getElementById('note-textarea').value = getState(ctxCourseId).note || '';
  openModal('modal-note');
}

function saveNote() {
  if (!ctxCourseId) return;
  const note = document.getElementById('note-textarea').value.trim();
  setState(ctxCourseId, { note });
  closeModal('modal-note');
  render();
}

// ── 通用 modal 工具 ───────────────────────────────

function openModal(id)  { document.getElementById(id).classList.add('open'); }
function closeModal(id) { document.getElementById(id).classList.remove('open'); }

// 点击遮罩关闭
document.querySelectorAll('.modal-overlay').forEach(el => {
  el.addEventListener('click', e => { if (e.target === el) closeModal(el.id); });
});

// ── 查找课程辅助 ──────────────────────────────────

function findCourse(courseId) {
  for (const cat of runtimeCategories) {
    const c = cat.courses.find(c => c.id === courseId);
    if (c) return c;
  }
  return null;
}
```

- [ ] **Step 2: 验证备注功能**

右键课程 → 「📝 添加备注」，期望：
- 弹出备注模态，显示课程名
- 输入备注文本点保存 → 模态关闭
- 再次右键同课程 → 弹出模态时输入框含已保存内容
- 有备注的课程在节点顶部显示紫色小圆点
- 悬停节点 → Tooltip 显示备注摘要

---

## Task 9: Tooltip

**Files:**
- Modify: `geektime_mindmap.html` — Block D 中追加

- [ ] **Step 1: 追加 Tooltip 代码**

```js
// ── Tooltip ──────────────────────────────────────

function showTooltip(event, d) {
  const tip = document.getElementById('tooltip');
  const st  = getState(d.id);
  document.getElementById('tt-name').textContent = d.name;
  document.getElementById('tt-note').textContent = st.note ? `备注：${st.note}` : '';

  const tagsEl = document.getElementById('tt-tags');
  tagsEl.innerHTML = '';
  (st.customTagIds || []).forEach(tid => {
    const tag = customTags[tid];
    if (!tag) return;
    const span = document.createElement('span');
    span.className = 'tt-tag';
    span.style.borderLeft = `3px solid ${tag.color}`;
    span.textContent = `${tag.emoji} ${tag.label}`;
    tagsEl.appendChild(span);
  });

  const x = Math.min(event.clientX + 12, window.innerWidth  - 280);
  const y = Math.min(event.clientY + 12, window.innerHeight - 100);
  tip.style.left    = x + 'px';
  tip.style.top     = y + 'px';
  tip.style.display = 'block';
}

function hideTooltip() {
  document.getElementById('tooltip').style.display = 'none';
}
```

- [ ] **Step 2: 验证 Tooltip**

鼠标悬停任意课程节点，期望：
- Tooltip 在鼠标右下方出现，显示课程名
- 移走鼠标 → Tooltip 消失
- 有备注的课程 Tooltip 显示备注内容

---

## Task 10: 自定义标签管理

**Files:**
- Modify: `geektime_mindmap.html` — Block D 中追加

- [ ] **Step 1: 追加自定义标签代码**

```js
// ── 自定义标签 ────────────────────────────────────

const TAG_PRESET_COLORS = ['#f59e0b','#3b82f6','#22c55e','#ef4444','#a855f7','#06b6d4'];
let tagModalCurrentColor = TAG_PRESET_COLORS[0];
let tagApplyToCourseId = null;

function openTagModal(editTagId, applyToCourseId) {
  hideContextMenu();
  tagApplyToCourseId = applyToCourseId;
  const isEdit = !!editTagId;
  document.getElementById('tag-modal-title').textContent = isEdit ? '✏️ 编辑标签' : '🏷️ 新建标签';
  document.getElementById('tag-edit-id').value  = editTagId || '';

  // 填充现有值或清空
  const tag = isEdit ? customTags[editTagId] : null;
  document.getElementById('tag-name-input').value  = tag?.label || '';
  document.getElementById('tag-emoji-input').value = tag?.emoji || '';
  tagModalCurrentColor = tag?.color || TAG_PRESET_COLORS[0];

  // 渲染色板
  const swatches = document.getElementById('color-swatches');
  swatches.innerHTML = '';
  TAG_PRESET_COLORS.forEach(color => {
    const div = document.createElement('div');
    div.className = 'swatch' + (color === tagModalCurrentColor ? ' selected' : '');
    div.style.background = color;
    div.onclick = () => {
      tagModalCurrentColor = color;
      swatches.querySelectorAll('.swatch').forEach(s => s.classList.remove('selected'));
      div.classList.add('selected');
    };
    swatches.appendChild(div);
  });

  openModal('modal-tag');
}

function saveTag() {
  const label = document.getElementById('tag-name-input').value.trim();
  if (!label) { alert('请输入标签名称'); return; }
  const emoji = document.getElementById('tag-emoji-input').value.trim();
  const editId = document.getElementById('tag-edit-id').value;

  let tagId;
  if (editId) {
    updateTag(editId, { label, color: tagModalCurrentColor, emoji });
    tagId = editId;
  } else {
    tagId = createTag({ label, color: tagModalCurrentColor, emoji });
  }

  // 若从课程右键菜单打开，立即应用到该课程
  if (tagApplyToCourseId && !editId) {
    toggleCourseTag(tagApplyToCourseId, tagId);
  }

  closeModal('modal-tag');
  refreshTagFilterList();
  refreshTagMgmtList();
  render();
}

// ── 右键菜单：标签子菜单 ──────────────────────────

function buildTagSubMenu(courseId) {
  const list = document.getElementById('cm-tag-list');
  list.innerHTML = '';
  const st = getState(courseId);

  Object.values(customTags).forEach(tag => {
    const checked = st.customTagIds.includes(tag.id);
    const item = document.createElement('div');
    item.className = 'cm-item' + (checked ? ' active' : '');
    item.innerHTML = `<span style="color:${tag.color}">${tag.emoji || '🏷️'}</span> ${tag.label} ${checked ? '✓' : ''}`;
    item.onclick = (e) => {
      e.stopPropagation();
      toggleCourseTag(courseId, tag.id);
      render();
      buildTagSubMenu(courseId); // 刷新子菜单勾选状态
    };
    list.appendChild(item);
  });

  // 新建标签入口
  const newItem = document.createElement('div');
  newItem.className = 'cm-item';
  newItem.innerHTML = '＋ 新建标签';
  newItem.onclick = (e) => { e.stopPropagation(); openTagModal(null, courseId); };
  if (Object.keys(customTags).length > 0) {
    const sep = document.createElement('div'); sep.className = 'cm-sep';
    list.appendChild(sep);
  }
  list.appendChild(newItem);
}
```

- [ ] **Step 2: 验证自定义标签**

1. 侧边栏点击「+ 新建标签」，输入名称「本周重点」，选择蓝色，输入 emoji「📌」，保存
2. 期望：侧边栏标签管理出现「📌 本周重点」，标签过滤区出现对应复选框
3. 右键课程 → 管理自定义标签 → 选中该标签
4. 期望：节点出现蓝色虚线描边圆
5. 勾选侧边栏标签过滤「📌 本周重点」→ 只显示打了该标签的课程

---

## Task 11: 移动到分类

**Files:**
- Modify: `geektime_mindmap.html` — Block D 中追加

- [ ] **Step 1: 追加移动分类代码**

```js
// ── 移动到分类 ────────────────────────────────────

function buildMoveSubMenu(courseId) {
  const list = document.getElementById('cm-move-list');
  list.innerHTML = '';
  // 找到当前分类，用于标记
  let currentCatId = null;
  runtimeCategories.forEach(cat => {
    if (cat.courses.find(c => c.id === courseId)) currentCatId = cat.id;
  });

  runtimeCategories.forEach(cat => {
    const item = document.createElement('div');
    item.className = 'cm-item' + (cat.id === currentCatId ? ' active' : '');
    item.innerHTML = `${cat.icon} ${cat.name}`;
    if (cat.id === currentCatId) item.style.pointerEvents = 'none';
    else item.onclick = (e) => {
      e.stopPropagation();
      moveCourse(courseId, cat.id);
      hideContextMenu();
      // 刷新侧边栏分类数量
      buildSidebar();
      render();
    };
    list.appendChild(item);
  });
}
```

- [ ] **Step 2: 验证移动分类**

右键课程 → 「📂 移动到分类」→ 选择另一分类，期望：
- 课程从原分类消失，出现在新分类中（展开新分类可见）
- 原分类课程计数 -1，新分类 +1

---

## Task 12: 导出 JSON（Block E）

**Files:**
- Modify: `geektime_mindmap.html` — Block D 后插入 Block E

- [ ] **Step 1: 插入导出代码**

```html
<script>
// ════════════════════════════════════════════════
// Block E: Import / Export
// ════════════════════════════════════════════════

function exportJSON() {
  const stats = calcStats();
  const payload = {
    meta: {
      title: '极客时间课程脑图',
      version: '1.0',
      exportedAt: new Date().toISOString(),
    },
    customTags: Object.values(customTags),
    categories: runtimeCategories.map(cat => ({
      id: cat.id,
      name: cat.name,
      icon: cat.icon,
      courses: cat.courses.map(c => {
        const st = getState(c.id);
        return { id: c.id, name: c.name, group: c.group, ...st };
      }),
    })),
    stats,
  };

  const blob = new Blob([JSON.stringify(payload, null, 2)], { type: 'application/json' });
  const url  = URL.createObjectURL(blob);
  const a    = document.createElement('a');
  a.href     = url;
  a.download = `geektime_mindmap_${new Date().toISOString().slice(0,10)}.json`;
  a.click();
  URL.revokeObjectURL(url);
}
</script>
```

- [ ] **Step 2: 验证导出**

1. 右键几门课程，打上「重点」「学习中」标注
2. 点击「📤 导出 JSON」
3. 打开下载的 JSON，期望：
   - `meta.exportedAt` 为当前时间
   - `categories` 包含 18 个分类
   - 已标注课程的 `status` 字段正确
   - `stats` 中计数与工具栏一致

---

## Task 13: 导入 JSON

**Files:**
- Modify: `geektime_mindmap.html` — Block E 中追加

- [ ] **Step 1: 追加导入代码**

```js
// ── 导入 ──────────────────────────────────────────

let pendingImportData = null;

function handleFileImport(event) {
  const file = event.target.files[0];
  if (!file) return;
  const reader = new FileReader();
  reader.onload = e => {
    try {
      const data = JSON.parse(e.target.result);
      if (!data.categories) throw new Error('缺少 categories 字段');
      pendingImportData = data;
      showImportConfirm(data);
    } catch (err) {
      alert('❌ 导入失败：' + err.message);
    }
  };
  reader.readAsText(file);
  event.target.value = ''; // 允许重复选同一文件
}

function showImportConfirm(data) {
  const info = document.getElementById('import-info');
  const s = data.stats || {};
  const ts = data.meta?.exportedAt
    ? new Date(data.meta.exportedAt).toLocaleString('zh-CN')
    : '未知';
  info.innerHTML = `
    <p>导出时间：<strong>${ts}</strong></p>
    <p>⭐ ${s.important||0} &nbsp; 📚 ${s.learning||0} &nbsp; ✅ ${s.done||0} &nbsp; 🗑️ ${s.deleted||0} &nbsp; 共 ${s.total||'?'} 门</p>`;
  openModal('modal-import');
}

function confirmImport() {
  if (!pendingImportData) return;
  const mode = document.querySelector('input[name="import-mode"]:checked')?.value || 'merge';
  applyImport(pendingImportData, mode);
  pendingImportData = null;
  closeModal('modal-import');
}

function applyImport(data, mode) {
  // 1. 导入自定义标签
  if (data.customTags) {
    if (mode === 'overwrite') customTags = {};
    data.customTags.forEach(tag => { customTags[tag.id] = tag; });
  }

  // 2. 重建 runtimeCategories（以导入文件的分类归属为准）
  const newCats = data.categories.map(cat => ({
    ...cat,
    courses: (cat.courses || []).map(c => ({ id: c.id, name: c.name, group: c.group })),
  }));
  // 覆盖模式直接替换；合并模式也以导入分类结构为准（分类移动已持久化在 JSON 中）
  runtimeCategories = newCats;

  // 3. 恢复课程状态
  if (mode === 'overwrite') courseState = {};
  data.categories.forEach(cat => {
    cat.courses.forEach(c => {
      const imported = {
        status:       c.status       || 'normal',
        customTagIds: c.customTagIds || [],
        note:         c.note         || '',
        startedAt:    c.startedAt    || null,
        doneAt:       c.doneAt       || null,
      };
      if (mode === 'merge') {
        // 以导入为准（导入有记录时覆盖）
        const cur = courseState[c.id] || {};
        courseState[c.id] = { ...cur, ...imported };
      } else {
        courseState[c.id] = imported;
      }
    });
  });

  // 4. 刷新 UI
  filters.catIds = new Set(runtimeCategories.map(c => c.id));
  buildSidebar();
  render();
}
```

- [ ] **Step 2: 验证导入**

1. 先导出一份 JSON
2. 手动编辑 JSON：将某门课的 `status` 改为 `"important"`
3. 点击「📥 导入 JSON」选择修改后的文件
4. 确认弹框显示导出时间和统计
5. 选择「合并」导入
6. 期望：被修改的课程节点变为金色，其他标注保持不变

---

## Task 14: 最终整合与收尾

**Files:**
- Modify: `geektime_mindmap.html` — 检查并补齐遗漏项

- [ ] **Step 1: 确认 DOMContentLoaded 入口完整**

启动脚本确认包含：

```js
window.addEventListener('DOMContentLoaded', () => {
  initState();
  buildSidebar();
  initSVG();
  resetView();
  render();
});
```

- [ ] **Step 2: 全功能回归验证**

按顺序验证：

| # | 操作 | 期望 |
|---|------|------|
| 1 | 刷新页面 | 18 个分类节点正常显示，无 console 报错 |
| 2 | 点击「展开全部」| 所有课程节点展开，树形横向铺开 |
| 3 | 点击「收起全部」| 回到 18 个分类节点状态 |
| 4 | 搜索「Kafka」| 只有 Kafka 相关课程可见，分类自动展开 |
| 5 | 清空搜索 | 树图恢复 |
| 6 | 右键课程 → 标记重点 | 节点变金色，工具栏 ⭐ 计数 +1 |
| 7 | 右键课程 → 学习中 | 节点变蓝色 |
| 8 | 右键课程 → 已完成 | 节点变绿色，doneAt 已设置 |
| 9 | 右键课程 → 删除 | 节点消失（f-deleted 未勾选时） |
| 10 | 勾选「显示已删除」 | 已删除节点以删除线显示 |
| 11 | 右键 → 移动到分类 | 课程移入新分类 |
| 12 | 右键 → 添加备注 | 备注保存，节点出现紫点，Tooltip 显示备注 |
| 13 | 新建自定义标签 | 侧边栏标签管理和过滤区同步更新 |
| 14 | 标签过滤勾选 | 只显示打了该标签的课程 |
| 15 | 导出 JSON | 下载文件，内容格式正确 |
| 16 | 导入 JSON（合并） | 标注状态正确恢复 |
| 17 | 导入 JSON（覆盖） | 当前状态完全替换 |
| 18 | 双击空白处 | 视图重置到初始位置 |

- [ ] **Step 3: 提交**

```bash
cd /Users/tongqianwen/ExpProjects/learn/jupyter
git add geektime_mindmap.html
git commit -m "feat: 极客时间课程脑图 — 单文件 HTML，D3 横向树，支持标注/自定义标签/搜索过滤/JSON 导入导出"
```

---

## 自检结果

**Spec 覆盖率检查：**

| Spec 需求 | 对应 Task |
|-----------|-----------|
| 单文件 HTML | Task 1 |
| D3 横向可折叠树 | Task 4 |
| 展开/收起分类 | Task 4 |
| 18 分类 185+ 课程数据 | Task 2 |
| 状态管理（5种状态） | Task 3 |
| 节点颜色/图标随状态变化 | Task 4 |
| 右键菜单（状态/标签/移动/备注/删除/恢复） | Task 7 |
| Tooltip | Task 9 |
| 备注编辑 | Task 8 |
| 自定义标签（创建/编辑/删除/应用/过滤） | Task 10 |
| 移动到分类 | Task 11 |
| 搜索（课程名+备注，实时高亮展开） | Task 6 |
| 过滤面板（状态/标签/分类/显示已删除） | Task 5 |
| 统计栏 | Task 3, 4 |
| 导出 JSON | Task 12 |
| 导入 JSON（合并/覆盖/容错） | Task 13 |
| 缩放/平移/双击重置 | Task 4 |

无遗漏。
