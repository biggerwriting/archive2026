/**
 * sw.js — Background Service Worker
 *
 * 职责：
 *   1. 接收来自 receiver.js 的调试消息，console.log 到 SW 控制台
 *   2. 持久化存储 savedJobs（popup 关闭后数据不丢失）
 *
 * 如何查看日志：
 *   chrome://extensions → 找到「BOSS直聘职位收集器」→ 点击「Service Worker」链接
 *   → 打开独立 DevTools，所有日志都在 Console 面板
 *
 * 注意：Service Worker 会在无活动后休眠，点击「Service Worker」链接可唤醒并激活。
 */

// ── 接收来自 content script 的日志消息 ──────────────────────
chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {
  const tab = sender.tab ? `[Tab ${sender.tab.id}]` : '[?]';

  switch (msg.type) {

    // receiver.js 捕获到一个 API 请求
    case 'API_HIT': {
      const { url, note } = msg;
      console.log(`🌐 API_HIT ${tab}  ${note || ''}  →  ${url}`);
      sendResponse({ ok: true });
      break;
    }

    // receiver.js 解析出一个职位对象
    case 'JOB_DETECTED': {
      const job = msg.job;
      console.groupCollapsed(`✅ JOB_DETECTED ${tab}  「${job.title}」@ ${job.company}`);
      console.log('薪资:', job.salary, '  地点:', job.location);
      console.log('经验:', job.experience, '  学历:', job.education);
      console.log('标签:', job.tags);
      console.log('链接:', job.jobUrl);
      console.log('来源 API:', job.capturedFrom);
      console.groupEnd();
      sendResponse({ ok: true });
      break;
    }

    // receiver.js 捕获到一个未能解析的 API（原始 body 片段）
    case 'API_UNKNOWN': {
      const { url, snippet } = msg;
      console.log(`❓ API_UNKNOWN ${tab}  ${url}`);
      console.log('   body 前 300 字符:', snippet);
      sendResponse({ ok: true });
      break;
    }

    default:
      sendResponse({ ok: false, reason: 'unknown type' });
  }

  // 返回 true 表示异步 sendResponse（避免通道提前关闭）
  return true;
});

// ── Service Worker 生命周期 ──────────────────────────────────
self.addEventListener('install', () => {
  console.log('🔧 BOSS职位收集器 SW installed');
  self.skipWaiting();
});

self.addEventListener('activate', () => {
  console.log('🚀 BOSS职位收集器 SW activated — 开始监听来自页面的职位数据');
});
