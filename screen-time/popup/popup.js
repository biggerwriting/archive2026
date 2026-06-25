/**
 * Popup 脚本
 * 读取今日统计数据并渲染到弹窗中。
 */

// ── 工具函数 ────────────────────────────────────────────

/** 格式化毫秒 → 易读字符串 */
function formatTime(ms) {
  const totalSec = Math.floor(ms / 1000);
  const h = Math.floor(totalSec / 3600);
  const m = Math.floor((totalSec % 3600) / 60);
  const s = totalSec % 60;
  if (h > 0) return `${h}h ${m}m`;
  if (m > 0) return `${m}m ${s}s`;
  return `${s}s`;
}

/** 获取今天的 storage key */
function todayKey() {
  const d = new Date();
  const y = d.getFullYear();
  const mo = String(d.getMonth() + 1).padStart(2, '0');
  const day = String(d.getDate()).padStart(2, '0');
  return `stats:${y}-${mo}-${day}`;
}

/** 格式化日期显示 */
function formatDate(d) {
  const days = ['日', '一', '二', '三', '四', '五', '六'];
  return `${d.getMonth() + 1}月${d.getDate()}日 周${days[d.getDay()]}`;
}

/** 获取域名首字母（favicon 加载失败时的占位） */
function domainInitial(domain) {
  return (domain.replace(/^www\./, '')[0] || '?').toUpperCase();
}

// ── 渲染 ───────────────────────────────────────────────

function renderEmpty() {
  document.getElementById('siteList').innerHTML = `
    <div class="empty">
      <div class="empty-icon">🌊</div>
      今天还没有记录<br>浏览几个网页后再来看看吧
    </div>`;
  document.getElementById('totalTime').textContent = '0s';
}

function renderSites(dayStats) {
  // 转换为数组并排序
  const entries = Object.entries(dayStats)
    .map(([domain, info]) => ({ domain, ...info }))
    .sort((a, b) => b.totalTime - a.totalTime);

  if (entries.length === 0) {
    renderEmpty();
    return;
  }

  // 总时长
  const totalMs = entries.reduce((sum, e) => sum + e.totalTime, 0);
  document.getElementById('totalTime').textContent = formatTime(totalMs);

  // 最大值（用于计算进度条比例）
  const maxMs = entries[0].totalTime;

  // 只显示前 8 名
  const top = entries.slice(0, 8);

  const listEl = document.getElementById('siteList');
  listEl.innerHTML = '';

  top.forEach((entry, idx) => {
    const pct = Math.max(4, Math.round((entry.totalTime / maxMs) * 100));
    const faviconUrl = `https://www.google.com/s2/favicons?domain=${entry.domain}&sz=32`;

    const item = document.createElement('div');
    item.className = 'site-item';
    item.title = entry.domain;
    item.innerHTML = `
      <span class="site-rank">${idx + 1}</span>
      <img
        class="favicon"
        src="${faviconUrl}"
        alt=""
        onerror="this.style.display='none';this.nextElementSibling.style.display='flex';"
      />
      <div class="favicon-placeholder" style="display:none;">${domainInitial(entry.domain)}</div>
      <div class="site-info">
        <div class="site-domain">${entry.domain}</div>
        <div class="site-bar-wrap">
          <div class="site-bar" style="width:${pct}%"></div>
        </div>
      </div>
      <span class="site-time">${formatTime(entry.totalTime)}</span>
    `;
    listEl.appendChild(item);
  });
}

// ── 初始化 ─────────────────────────────────────────────

async function init() {
  // 日期显示
  document.getElementById('dateBadge').textContent = formatDate(new Date());

  // 读取今日数据
  const key = todayKey();
  const result = await chrome.storage.local.get(key);
  const dayStats = result[key] || {};

  renderSites(dayStats);

  // 打开完整统计页
  document.getElementById('btnStats').addEventListener('click', (e) => {
    e.preventDefault();
    chrome.tabs.create({ url: chrome.runtime.getURL('stats/stats.html') });
    window.close();
  });
}

init();
