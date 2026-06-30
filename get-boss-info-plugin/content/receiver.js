/**
 * receiver.js — 运行在 isolated world（扩展沙箱上下文）
 *
 * 职责：
 *   1. 监听来自 interceptor.js 的 postMessage（所有 zhipin.com 请求）
 *   2. 将所有捕获到的 API URL 转发给 SW，方便在 SW 控制台查看
 *   3. 识别并解析职位相关的 API 响应，存入 chrome.storage.local.currentJob
 *
 * 调试：
 *   chrome://extensions → BOSS职位收集器 → 点「Service Worker」→ Console 面板
 */
(function () {
  'use strict';

  const MSG_TYPE = '__boss_net_intercept__';

  // ─────────────────────────────────────────────────
  // 向 Service Worker 发送消息（fire-and-forget，失败不报错）
  // ─────────────────────────────────────────────────
  function toSW(msg) {
    chrome.runtime.sendMessage(msg).catch(() => {
      // SW 可能正在休眠，忽略错误；
      // 在 chrome://extensions 点击「Service Worker」链接可唤醒它
    });
  }

  // ─────────────────────────────────────────────────
  // URL 关键词：命中时尝试解析职位数据
  // ─────────────────────────────────────────────────
  const JOB_URL_KEYWORDS = [
    '/wapi/zpgeek/job',       // 职位详情
    '/wapi/zpgeek/search',    // 搜索列表
    '/wapi/zpgeek/recommend', // 推荐职位
    '/wapi/zpgeek/friend',    // 好友在投
    '/wapi/zpgeek/geek/card', // 候选人相关
  ];

  function isJobRelatedUrl(url) {
    return JOB_URL_KEYWORDS.some((kw) => url.includes(kw));
  }

  // ─────────────────────────────────────────────────
  // 从 API 响应 JSON 中提取职位结构
  // BOSS直聘的 API 结构可能随时调整，这里兼容多种已知格式
  // ─────────────────────────────────────────────────
  function extractJob(url, json) {
    if (!json || json.code !== 0) return null;

    const zpData = json.zpData || json.data || {};

    // ── 格式 A：职位详情  /job/card.json 或 /job/detail.json ──
    const card =
      zpData.jobCard ||
      zpData.jobInfo ||
      zpData.job     ||
      json.job       ||
      null;

    if (card && card.jobName) {
      return normalizeJob(card, url);
    }

    // ── 格式 B：搜索列表（jobList 数组）──
    // 仅记录日志，不覆盖 currentJob（防止误保存整批列表）
    const list = zpData.jobList || zpData.list;
    if (Array.isArray(list) && list.length > 0) {
      toSW({ type: 'API_HIT', url, note: `列表 ${list.length} 条（不自动存储）` });
      return null;
    }

    return null;
  }

  /** 将不同格式的 job 对象统一为插件内部格式 */
  function normalizeJob(raw, sourceUrl) {
    const skills = raw.skills || raw.jobLabels || [];
    return {
      jobId:        raw.encryptJobId   || raw.jobId      || raw.securityId || '',
      title:        raw.jobName        || raw.positionName || '',
      company:      raw.brandName      || raw.companyName || raw.company   || '',
      salary:       raw.salaryDesc     || raw.salary      || '',
      location:     [raw.cityName, raw.areaDistrict].filter(Boolean).join(' '),
      experience:   raw.jobExperience  || raw.experience  || '',
      education:    raw.jobDegree      || raw.education   || '',
      companySize:  raw.brandScaleName || raw.scaleName   || '',
      companyStage: raw.brandStageName || raw.stageName   || '',
      tags:         Array.isArray(skills) ? skills.join('、') : '',
      jobUrl:       buildJobUrl(raw),
      capturedFrom: sourceUrl,
      capturedAt:   new Date().toISOString(),
    };
  }

  function buildJobUrl(raw) {
    const id = raw.encryptJobId || raw.jobId;
    if (!id) return window.location.href;
    return `https://www.zhipin.com/job_detail/${id}.html`;
  }

  // ─────────────────────────────────────────────────
  // 主监听：处理来自 interceptor 的 postMessage
  // ─────────────────────────────────────────────────
  window.addEventListener('message', (event) => {
    // 安全校验：只处理同窗口、带正确标记的消息
    if (event.source !== window) return;
    if (!event.data || event.data.type !== MSG_TYPE) return;

    const { url, status, body } = event.data;

    // ── 1. 把所有请求 URL 转发给 SW（调试用，看有哪些接口被调用）──
    //    只记录路径部分，避免日志过长
    const shortUrl = url.replace('https://www.zhipin.com', '');
    toSW({ type: 'API_HIT', url: shortUrl, note: `HTTP ${status}` });

    // ── 2. 仅对职位相关 URL 尝试解析 ──
    if (!isJobRelatedUrl(url)) return;

    let json;
    try {
      json = JSON.parse(body);
    } catch {
      toSW({ type: 'API_UNKNOWN', url: shortUrl, snippet: body.slice(0, 300) });
      return;
    }

    const job = extractJob(url, json);

    if (job) {
      // 写入 storage，popup 读取展示
      chrome.storage.local.set({ currentJob: job });
      // 转发给 SW 控制台展示
      toSW({ type: 'JOB_DETECTED', job });
    } else {
      // 命中关键词但未能解析出职位，把 body 前 300 字符发给 SW 辅助排查
      const snippet = typeof body === 'string' ? body.slice(0, 300) : '';
      toSW({ type: 'API_UNKNOWN', url: shortUrl, snippet });
    }
  });
})();
