/**
 * Stats Page 脚本
 * 负责：数据加载、摘要卡片、图表绘制、明细表格、导出功能。
 */

// ─────────────────────────────────────────────
// 工具函数
// ─────────────────────────────────────────────

function formatTime(ms) {
  const totalSec = Math.floor(ms / 1000);
  const h = Math.floor(totalSec / 3600);
  const m = Math.floor((totalSec % 3600) / 60);
  const s = totalSec % 60;
  if (h > 0 && m > 0) return `${h}h ${m}m`;
  if (h > 0) return `${h}h`;
  if (m > 0) return `${m}m ${s}s`;
  return `${s}s`;
}

function toDateStr(date) {
  const y = date.getFullYear();
  const m = String(date.getMonth() + 1).padStart(2, '0');
  const d = String(date.getDate()).padStart(2, '0');
  return `${y}-${m}-${d}`;
}

function dateFromStr(str) {
  const [y, m, d] = str.split('-').map(Number);
  return new Date(y, m - 1, d);
}

/** 生成 [from, to] 之间所有日期字符串（YYYY-MM-DD） */
function dateRange(fromStr, toStr) {
  const result = [];
  const cur = dateFromStr(fromStr);
  const end = dateFromStr(toStr);
  while (cur <= end) {
    result.push(toDateStr(cur));
    cur.setDate(cur.getDate() + 1);
  }
  return result;
}

function domainInitial(domain) {
  return (domain.replace(/^www\./, '')[0] || '?').toUpperCase();
}

// ─────────────────────────────────────────────
// 数据加载
// ─────────────────────────────────────────────

/**
 * 从 chrome.storage.local 读取指定日期范围内的数据，
 * 按域名合并，返回数组：[{ domain, totalTime, recentUrls }]
 */
async function loadData(fromStr, toStr) {
  const dates = dateRange(fromStr, toStr);
  const keys = dates.map((d) => `stats:${d}`);
  const stored = await chrome.storage.local.get(keys);

  // 按域名合并
  const merged = {}; // { domain: { totalTime, urlMap: { url: {title, time, lastVisit} } } }

  for (const key of keys) {
    const dayStats = stored[key] || {};
    for (const [domain, info] of Object.entries(dayStats)) {
      if (!merged[domain]) {
        merged[domain] = { totalTime: 0, urlMap: {} };
      }
      merged[domain].totalTime += info.totalTime || 0;

      // 合并 URL 记录
      for (const urlEntry of info.recentUrls || []) {
        const existing = merged[domain].urlMap[urlEntry.url];
        if (existing) {
          existing.time += urlEntry.time || 0;
          if (urlEntry.lastVisit > existing.lastVisit) {
            existing.lastVisit = urlEntry.lastVisit;
            existing.title = urlEntry.title || existing.title;
          }
        } else {
          merged[domain].urlMap[urlEntry.url] = {
            url: urlEntry.url,
            title: urlEntry.title || urlEntry.url,
            time: urlEntry.time || 0,
            lastVisit: urlEntry.lastVisit || '',
          };
        }
      }
    }
  }

  // 转换为数组，recentUrls 按时长排序
  return Object.entries(merged)
    .map(([domain, data]) => ({
      domain,
      totalTime: data.totalTime,
      recentUrls: Object.values(data.urlMap).sort((a, b) => b.time - a.time),
    }))
    .sort((a, b) => b.totalTime - a.totalTime);
}

// ─────────────────────────────────────────────
// 摘要卡片
// ─────────────────────────────────────────────

function renderCards(entries, fromStr, toStr) {
  const totalMs = entries.reduce((s, e) => s + e.totalTime, 0);
  const totalUrls = entries.reduce((s, e) => s + e.recentUrls.length, 0);
  const top = entries[0];

  document.getElementById('cardTotal').textContent = formatTime(totalMs);
  document.getElementById('cardSites').textContent = entries.length;
  document.getElementById('cardUrls').textContent = totalUrls;

  if (fromStr === toStr) {
    const d = dateFromStr(fromStr);
    const days = ['日', '一', '二', '三', '四', '五', '六'];
    document.getElementById('cardDateRange').textContent =
      `${d.getMonth() + 1}月${d.getDate()}日 周${days[d.getDay()]}`;
  } else {
    document.getElementById('cardDateRange').textContent = `${fromStr} ~ ${toStr}`;
  }

  if (top) {
    document.getElementById('cardTop').textContent = top.domain;
    document.getElementById('cardTopTime').textContent = formatTime(top.totalTime);
  } else {
    document.getElementById('cardTop').textContent = '--';
    document.getElementById('cardTopTime').textContent = '--';
  }
}

// ─────────────────────────────────────────────
// Canvas 横向条形图
// ─────────────────────────────────────────────

/** 调色板（渐变起止色对） */
const PALETTE = [
  ['#6366f1', '#8b5cf6'],
  ['#3b82f6', '#6366f1'],
  ['#8b5cf6', '#ec4899'],
  ['#06b6d4', '#3b82f6'],
  ['#10b981', '#06b6d4'],
  ['#f59e0b', '#ef4444'],
  ['#ef4444', '#f97316'],
  ['#f97316', '#eab308'],
  ['#84cc16', '#10b981'],
  ['#ec4899', '#f43f5e'],
];

function drawChart(entries) {
  const canvas = document.getElementById('chart');
  const top = entries.slice(0, 10);
  if (top.length === 0) {
    canvas.style.display = 'none';
    return;
  }
  canvas.style.display = 'block';

  const dpr = window.devicePixelRatio || 1;
  const W = canvas.parentElement.clientWidth - 40; // 减去 padding
  const BAR_H = 20;
  const GAP = 10;
  const LABEL_W = 140;
  const TIME_W = 60;
  const PADDING_V = 8;
  const H = (BAR_H + GAP) * top.length + PADDING_V * 2;

  canvas.width = W * dpr;
  canvas.height = H * dpr;
  canvas.style.width = W + 'px';
  canvas.style.height = H + 'px';

  const ctx = canvas.getContext('2d');
  ctx.scale(dpr, dpr);

  const maxTime = top[0].totalTime;
  const barAreaW = W - LABEL_W - TIME_W - 16;

  ctx.clearRect(0, 0, W, H);

  top.forEach((entry, i) => {
    const y = PADDING_V + i * (BAR_H + GAP);
    const barW = Math.max(2, (entry.totalTime / maxTime) * barAreaW);

    // 标签
    ctx.font = `500 12px -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif`;
    ctx.fillStyle = '#c4c4d4';
    ctx.textBaseline = 'middle';
    ctx.textAlign = 'right';
    const label = entry.domain.length > 18
      ? entry.domain.slice(0, 17) + '…'
      : entry.domain;
    ctx.fillText(label, LABEL_W - 8, y + BAR_H / 2);

    // 背景轨道
    ctx.fillStyle = '#1e1e30';
    const rx = LABEL_W;
    roundRect(ctx, rx, y, barAreaW, BAR_H, 4);
    ctx.fill();

    // 渐变色条
    const [c1, c2] = PALETTE[i % PALETTE.length];
    const grad = ctx.createLinearGradient(rx, 0, rx + barW, 0);
    grad.addColorStop(0, c1);
    grad.addColorStop(1, c2);
    ctx.fillStyle = grad;
    roundRect(ctx, rx, y, barW, BAR_H, 4);
    ctx.fill();

    // 时间标签
    ctx.font = `600 11px -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif`;
    ctx.fillStyle = '#6366f1';
    ctx.textAlign = 'left';
    ctx.fillText(formatTime(entry.totalTime), LABEL_W + barAreaW + 8, y + BAR_H / 2);
  });
}

function roundRect(ctx, x, y, w, h, r) {
  ctx.beginPath();
  ctx.moveTo(x + r, y);
  ctx.lineTo(x + w - r, y);
  ctx.quadraticCurveTo(x + w, y, x + w, y + r);
  ctx.lineTo(x + w, y + h - r);
  ctx.quadraticCurveTo(x + w, y + h, x + w - r, y + h);
  ctx.lineTo(x + r, y + h);
  ctx.quadraticCurveTo(x, y + h, x, y + h - r);
  ctx.lineTo(x, y + r);
  ctx.quadraticCurveTo(x, y, x + r, y);
  ctx.closePath();
}

// ─────────────────────────────────────────────
// 明细表格
// ─────────────────────────────────────────────

let sortCol = 'totalTime';
let sortAsc = false;
let currentEntries = [];

function renderTable(entries) {
  currentEntries = entries;
  const totalMs = entries.reduce((s, e) => s + e.totalTime, 0);
  const tbody = document.getElementById('tableBody');

  if (entries.length === 0) {
    tbody.innerHTML = `<tr><td colspan="5"><div class="empty-state">
      <div class="empty-icon">🌊</div>
      所选日期范围内暂无数据
    </div></td></tr>`;
    return;
  }

  // 根据当前排序列和方向排序
  const sorted = [...entries].sort((a, b) => {
    let va = a[sortCol] ?? a.domain;
    let vb = b[sortCol] ?? b.domain;
    if (typeof va === 'string') return sortAsc ? va.localeCompare(vb) : vb.localeCompare(va);
    return sortAsc ? va - vb : vb - va;
  });

  // 为每行计算占比（基于原始 totalMs，不受排序影响）
  tbody.innerHTML = '';
  sorted.forEach((entry, idx) => {
    const pct = totalMs > 0 ? ((entry.totalTime / totalMs) * 100).toFixed(1) : '0.0';
    const barPct = totalMs > 0 ? Math.max(2, Math.round((entry.totalTime / totalMs) * 100)) : 2;
    const faviconUrl = `https://www.google.com/s2/favicons?domain=${entry.domain}&sz=32`;

    const tr = document.createElement('tr');
    tr.innerHTML = `
      <td class="td-rank">${idx + 1}</td>
      <td class="td-domain">
        <div class="domain-wrap">
          <img class="favicon" src="${faviconUrl}" alt=""
            onerror="this.style.display='none';this.nextElementSibling.style.display='flex';" />
          <div class="favicon-fallback" style="display:none;">${domainInitial(entry.domain)}</div>
          <span class="domain-name">${entry.domain}</span>
        </div>
      </td>
      <td class="td-time">${formatTime(entry.totalTime)}</td>
      <td class="td-bar">
        <div class="bar-wrap" style="margin-top:8px">
          <div class="bar-fill" style="width:${barPct}%"></div>
        </div>
      </td>
      <td class="td-pct">${pct}%</td>
      <td class="td-urls">${renderUrlCell(entry)}</td>
    `;
    tbody.appendChild(tr);
  });
}

function renderUrlCell(entry) {
  const urls = entry.recentUrls;
  if (!urls || urls.length === 0) return '<span style="color:#4b4b6b;font-size:11px;">无记录</span>';

  const id = `urls-${entry.domain.replace(/\./g, '-')}`;
  const preview = urls[0].title.length > 30 ? urls[0].title.slice(0, 29) + '…' : urls[0].title;
  const more = urls.length > 1 ? ` +${urls.length - 1} 条` : '';

  const urlItems = urls.map(
    (u) => `
    <div class="url-item">
      <span class="url-title" title="${u.url}">${u.title || u.url}</span>
      <span class="url-time">${formatTime(u.time)}</span>
    </div>`
  ).join('');

  return `
    <div class="url-toggle" onclick="toggleUrls('${id}', this)">
      ▶ ${preview}${more}
    </div>
    <div class="url-list" id="${id}">
      ${urlItems}
    </div>`;
}

function toggleUrls(id, btn) {
  const el = document.getElementById(id);
  if (!el) return;
  const open = el.classList.toggle('open');
  btn.textContent = btn.textContent.replace(open ? '▶' : '▼', open ? '▼' : '▶');
}

// 排序
document.querySelectorAll('thead th[data-col]').forEach((th) => {
  th.addEventListener('click', () => {
    const col = th.dataset.col;
    if (sortCol === col) {
      sortAsc = !sortAsc;
    } else {
      sortCol = col;
      sortAsc = col === 'domain';
    }
    document.querySelectorAll('thead th').forEach((t) => t.classList.remove('sorted'));
    th.classList.add('sorted');
    th.textContent = th.textContent.replace(/ [↑↓]$/, '') +
      (sortAsc ? ' ↑' : ' ↓');
    renderTable(currentEntries);
  });
});

// ─────────────────────────────────────────────
// 导出功能
// ─────────────────────────────────────────────

function exportCsv(entries, fromStr, toStr) {
  const rows = [['域名', '总时长(秒)', '总时长(格式化)', 'URL', 'URL标题', 'URL时长(秒)']];
  for (const entry of entries) {
    const secs = Math.floor(entry.totalTime / 1000);
    if (entry.recentUrls.length === 0) {
      rows.push([entry.domain, secs, formatTime(entry.totalTime), '', '', '']);
    } else {
      entry.recentUrls.forEach((u, i) => {
        rows.push([
          i === 0 ? entry.domain : '',
          i === 0 ? secs : '',
          i === 0 ? formatTime(entry.totalTime) : '',
          u.url,
          u.title,
          Math.floor(u.time / 1000),
        ]);
      });
    }
  }

  const csv = rows
    .map((r) => r.map((c) => `"${String(c).replace(/"/g, '""')}"`).join(','))
    .join('\n');

  const bom = '﻿'; // UTF-8 BOM，使 Excel 正确识别中文
  download(`screen-time-${fromStr}-${toStr}.csv`, bom + csv, 'text/csv;charset=utf-8;');
}

function exportJson(entries, fromStr, toStr) {
  const data = {
    exportedAt: new Date().toISOString(),
    range: { from: fromStr, to: toStr },
    summary: {
      totalTime: entries.reduce((s, e) => s + e.totalTime, 0),
      totalSites: entries.length,
      totalUrls: entries.reduce((s, e) => s + e.recentUrls.length, 0),
    },
    sites: entries.map((e) => ({
      domain: e.domain,
      totalTime: e.totalTime,
      totalTimeFormatted: formatTime(e.totalTime),
      recentUrls: e.recentUrls,
    })),
  };
  download(
    `screen-time-${fromStr}-${toStr}.json`,
    JSON.stringify(data, null, 2),
    'application/json'
  );
}

function download(filename, content, mime) {
  const a = document.createElement('a');
  a.href = URL.createObjectURL(new Blob([content], { type: mime }));
  a.download = filename;
  a.click();
  setTimeout(() => URL.revokeObjectURL(a.href), 1000);
}

// ─────────────────────────────────────────────
// 主流程
// ─────────────────────────────────────────────

let currentFrom = '';
let currentTo = '';

async function query() {
  const fromStr = document.getElementById('dateFrom').value;
  const toStr = document.getElementById('dateTo').value;
  if (!fromStr || !toStr || fromStr > toStr) return;

  currentFrom = fromStr;
  currentTo = toStr;

  const entries = await loadData(fromStr, toStr);
  renderCards(entries, fromStr, toStr);
  drawChart(entries);
  renderTable(entries);
}

// 快速范围按钮
document.querySelectorAll('.quick-btn').forEach((btn) => {
  btn.addEventListener('click', () => {
    document.querySelectorAll('.quick-btn').forEach((b) => b.classList.remove('active'));
    btn.classList.add('active');

    const today = new Date();
    const todayStr = toDateStr(today);
    let from, to;

    switch (btn.dataset.range) {
      case 'today':
        from = to = todayStr;
        break;
      case 'yesterday': {
        const y = new Date(today);
        y.setDate(y.getDate() - 1);
        from = to = toDateStr(y);
        break;
      }
      case 'week': {
        const w = new Date(today);
        w.setDate(w.getDate() - 6);
        from = toDateStr(w);
        to = todayStr;
        break;
      }
      case 'month': {
        const m = new Date(today);
        m.setDate(m.getDate() - 29);
        from = toDateStr(m);
        to = todayStr;
        break;
      }
      case 'all': {
        from = '2020-01-01';
        to = todayStr;
        break;
      }
    }

    document.getElementById('dateFrom').value = from;
    document.getElementById('dateTo').value = to;
    query();
  });
});

document.getElementById('btnQuery').addEventListener('click', () => {
  document.querySelectorAll('.quick-btn').forEach((b) => b.classList.remove('active'));
  query();
});

document.getElementById('btnCsv').addEventListener('click', () => {
  exportCsv(currentEntries, currentFrom, currentTo);
});

document.getElementById('btnJson').addEventListener('click', () => {
  exportJson(currentEntries, currentFrom, currentTo);
});

// 窗口大小变化时重绘图表
window.addEventListener('resize', () => drawChart(currentEntries));

// 初始化：默认显示今天
function initDates() {
  const today = toDateStr(new Date());
  document.getElementById('dateFrom').value = today;
  document.getElementById('dateTo').value = today;
}

initDates();
query();
