/**
 * popup.js — 弹出面板逻辑
 *
 * 数据全部来自 chrome.storage.local：
 *   currentJob  : receiver.js 检测到的最新职位（单个对象）
 *   savedJobs   : 用户手动保存的职位列表（数组）
 */

// ── DOM 引用 ──────────────────────────────────────────────
const $ = (id) => document.getElementById(id);

const elTotalCount  = $('totalCount');
const elCurrentCard = $('currentJobCard');
const elCurrentEmpty= $('currentEmpty');
const elCurrentInfo = $('currentInfo');
const elJobTitle    = $('jobTitle');
const elJobMeta     = $('jobMeta');
const elJobTags     = $('jobTags');
const elBtnSave     = $('btnSave');
const elSaveTip     = $('saveTip');
const elDupTip      = $('dupTip');
const elJobList     = $('jobList');
const elListEmpty   = $('listEmpty');
const elBtnExport   = $('btnExport');
const elBtnClear    = $('btnClear');

// ── 状态 ──────────────────────────────────────────────────
let currentJob  = null;
let savedJobs   = [];

// ── 初始化 ────────────────────────────────────────────────
chrome.storage.local.get({ currentJob: null, savedJobs: [] }, (data) => {
  currentJob = data.currentJob;
  savedJobs  = data.savedJobs || [];
  renderCurrentJob();
  renderSavedList();
});

// 监听 storage 变化（当 receiver.js 检测到新职位时实时更新）
chrome.storage.onChanged.addListener((changes, area) => {
  if (area !== 'local') return;
  if (changes.currentJob) {
    currentJob = changes.currentJob.newValue;
    renderCurrentJob();
  }
  if (changes.savedJobs) {
    savedJobs = changes.savedJobs.newValue || [];
    renderSavedList();
  }
});

// ── 渲染：当前职位卡片 ─────────────────────────────────────
function renderCurrentJob() {
  hideTips();

  if (!currentJob || !currentJob.title) {
    elCurrentEmpty.classList.remove('hidden');
    elCurrentInfo.classList.add('hidden');
    elBtnSave.disabled = true;
    return;
  }

  elCurrentEmpty.classList.add('hidden');
  elCurrentInfo.classList.remove('hidden');

  elJobTitle.textContent = currentJob.title;
  elJobMeta.innerHTML = buildMetaLines(currentJob);
  renderTags(elJobTags, currentJob.tags);
  elBtnSave.disabled = false;
}

function buildMetaLines(job) {
  const parts = [];
  const line1 = [job.company, job.salary].filter(Boolean).join('&nbsp;&nbsp;|&nbsp;&nbsp;');
  const line2 = [job.location, job.experience, job.education].filter(Boolean).join('&nbsp;·&nbsp;');
  if (line1) parts.push(`<span style="color:#333;font-weight:500">${line1}</span>`);
  if (line2) parts.push(`<span>${line2}</span>`);
  if (job.companySize || job.companyStage) {
    const sz = [job.companySize, job.companyStage].filter(Boolean).join('&nbsp;/&nbsp;');
    parts.push(`<span style="color:#aaa">${sz}</span>`);
  }
  return parts.join('<br>');
}

function renderTags(container, tagsStr) {
  container.innerHTML = '';
  if (!tagsStr) return;
  tagsStr.split('、').slice(0, 6).forEach((tag) => {
    const span = document.createElement('span');
    span.className = 'tag';
    span.textContent = tag.trim();
    container.appendChild(span);
  });
}

// ── 渲染：已保存列表 ──────────────────────────────────────
function renderSavedList() {
  const count = savedJobs.length;
  elTotalCount.textContent = `${count} 条`;
  elBtnExport.disabled = count === 0;
  elBtnClear.disabled  = count === 0;

  elJobList.innerHTML = '';

  if (count === 0) {
    elJobList.appendChild(elListEmpty);
    elListEmpty.classList.remove('hidden');
    return;
  }

  elListEmpty.classList.add('hidden');

  // 最新保存的在最上面
  [...savedJobs].reverse().forEach((job, revIdx) => {
    const realIdx = savedJobs.length - 1 - revIdx;
    const item = document.createElement('div');
    item.className = 'job-item';
    item.innerHTML = `
      <div class="job-item-info">
        <div class="job-item-title" title="${esc(job.title)}">${esc(job.title)}</div>
        <div class="job-item-sub">${esc(job.company)} &nbsp;·&nbsp; ${esc(job.salary)} &nbsp;·&nbsp; ${esc(job.location)}</div>
      </div>
      <button class="job-item-del" title="删除" data-idx="${realIdx}">✕</button>
    `;
    elJobList.appendChild(item);
  });

  // 单条删除
  elJobList.querySelectorAll('.job-item-del').forEach((btn) => {
    btn.addEventListener('click', () => deleteJob(parseInt(btn.dataset.idx)));
  });
}

function esc(str = '') {
  return str
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

// ── 保存职位 ──────────────────────────────────────────────
elBtnSave.addEventListener('click', () => {
  if (!currentJob) return;
  hideTips();

  // 去重检查（按 jobId 或 url）
  const isDup = savedJobs.some(
    (j) => (j.jobId && j.jobId === currentJob.jobId) ||
            (j.jobUrl && j.jobUrl === currentJob.jobUrl)
  );

  if (isDup) {
    elDupTip.classList.remove('hidden');
    return;
  }

  const toSave = { ...currentJob, savedAt: new Date().toISOString() };
  savedJobs = [...savedJobs, toSave];
  chrome.storage.local.set({ savedJobs }, () => {
    renderSavedList();
    elSaveTip.classList.remove('hidden');
    setTimeout(() => elSaveTip.classList.add('hidden'), 2000);
  });
});

// ── 删除单条 ──────────────────────────────────────────────
function deleteJob(idx) {
  savedJobs = savedJobs.filter((_, i) => i !== idx);
  chrome.storage.local.set({ savedJobs });
}

// ── 导出 CSV ──────────────────────────────────────────────
elBtnExport.addEventListener('click', () => {
  if (savedJobs.length === 0) return;

  const headers = [
    '职位名称', '公司名称', '薪资', '工作地点',
    '经验要求', '学历要求', '公司规模', '公司融资阶段',
    '技能标签', '职位链接', '保存时间',
  ];

  const rows = savedJobs.map((j) => [
    j.title, j.company, j.salary, j.location,
    j.experience, j.education, j.companySize, j.companyStage,
    j.tags, j.jobUrl, j.savedAt,
  ].map(csvCell));

  const csv = [headers.map(csvCell), ...rows]
    .map((row) => row.join(','))
    .join('\r\n');

  // 添加 UTF-8 BOM，Excel 打开中文不乱码
  const bom = '﻿';
  const blob = new Blob([bom + csv], { type: 'text/csv;charset=utf-8;' });
  const url  = URL.createObjectURL(blob);

  const a = document.createElement('a');
  a.href     = url;
  a.download = `boss职位_${formatDate(new Date())}.csv`;
  a.click();

  URL.revokeObjectURL(url);
});

/** 处理 CSV 单元格：含逗号/引号/换行时加双引号包裹 */
function csvCell(val = '') {
  const str = String(val).replace(/\r?\n/g, ' ');
  if (str.includes(',') || str.includes('"') || str.includes('\n')) {
    return '"' + str.replace(/"/g, '""') + '"';
  }
  return str;
}

function formatDate(d) {
  return [
    d.getFullYear(),
    String(d.getMonth() + 1).padStart(2, '0'),
    String(d.getDate()).padStart(2, '0'),
  ].join('');
}

// ── 清空全部 ──────────────────────────────────────────────
elBtnClear.addEventListener('click', () => {
  if (!confirm(`确认清空全部 ${savedJobs.length} 条职位记录？`)) return;
  savedJobs = [];
  chrome.storage.local.set({ savedJobs });
});

// ── 工具 ──────────────────────────────────────────────────
function hideTips() {
  elSaveTip.classList.add('hidden');
  elDupTip.classList.add('hidden');
}
