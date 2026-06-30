/**
 * interceptor.js — 运行在 MAIN world（页面真实 window 上下文）
 *
 * 职责：
 *   1. 在页面脚本执行之前，劫持 window.fetch 和 XMLHttpRequest
 *   2. 将所有响应通过 postMessage 中继给 isolated world 的 receiver.js
 *   3. 不做任何业务逻辑判断，只负责透传
 *
 * 注意：此脚本与 receiver.js 运行在不同的 JS 沙箱，
 *       唯一通信方式是 window.postMessage。
 */
(function () {
  'use strict';

  /** 消息标记，避免与页面自身的 postMessage 混淆 */
  const MSG_TYPE = '__boss_net_intercept__';

  // ─────────────────────────────────────────────────
  // 1. 劫持 window.fetch
  // ─────────────────────────────────────────────────
  const _origFetch = window.fetch;

  window.fetch = async function (input, init) {
    const url =
      typeof input === 'string'
        ? input
        : input instanceof URL
        ? input.href
        : input?.url || '';

    // 先正常发出请求，拿到原始 response
    const response = await _origFetch.apply(this, arguments);

    // 克隆一份读取 body（原始 response 依然可被页面正常消费）
    const clone = response.clone();
    clone
      .text()
      .then((body) => {
        window.postMessage(
          { type: MSG_TYPE, url, status: response.status, body },
          '*'
        );
      })
      .catch(() => {
        /* 忽略读取失败（如 streaming response） */
      });

    return response;
  };

  // ─────────────────────────────────────────────────
  // 2. 劫持 XMLHttpRequest（部分旧接口使用 XHR）
  // ─────────────────────────────────────────────────
  const _origOpen = XMLHttpRequest.prototype.open;
  const _origSend = XMLHttpRequest.prototype.send;

  XMLHttpRequest.prototype.open = function (method, url) {
    // 记录 url 供 send 阶段使用
    this.__interceptUrl__ = typeof url === 'string' ? url : String(url);
    return _origOpen.apply(this, arguments);
  };

  XMLHttpRequest.prototype.send = function () {
    const capturedUrl = this.__interceptUrl__ || '';

    this.addEventListener('load', function () {
      window.postMessage(
        {
          type: MSG_TYPE,
          url: capturedUrl,
          status: this.status,
          body: this.responseText,
        },
        '*'
      );
    });

    return _origSend.apply(this, arguments);
  };
})();
