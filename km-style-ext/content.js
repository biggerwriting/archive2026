const s = document.createElement("style");
s.textContent = `
    /* === 页面整体 === */
    html {
      font-size: 18px !important;
      overflow: hidden !important;
    }
    body {
      max-width: 37rem !important;
      margin: 0 auto !important;
      padding: 1.5rem 1.25rem !important;
      font-family: -apple-system, "PingFang SC", "Microsoft YaHei", "Helvetica Neue", Arial, sans-serif !important;
      color: #333 !important;
      background: #fff !important;
    }

    /* === 正文段落 === */
    p {
      line-height: 1.8 !important;
      letter-spacing: 0.02em !important;
      margin: 0 0 1.5rem !important;
      text-align: justify !important;
    }

    /* === 标题 === */
    h1 {
      font-size: 1.5rem !important;
      font-weight: 700 !important;
      color: #1a1a1a !important;
      line-height: 1.4 !important;
      margin: 0 0 2rem !important;
    }
    h2 {
      font-size: 1.375rem !important;
      font-weight: 700 !important;
      color: #1a1a1a !important;
      line-height: 1.4 !important;
      margin: 2.5rem 0 1rem !important;
    }
    h3 {
      font-size: 1.125rem !important;
      font-weight: 700 !important;
      color: #1a1a1a !important;
      line-height: 1.4 !important;
      margin: 2rem 0 0.75rem !important;
    }

    /* === 粗体 / 强调 === */
    strong, b {
      font-weight: 700 !important;
      color: #1a1a1a !important;
    }

    /* === 行内代码 === */
    code {
      font-family: Consolas, Monaco, "Courier New", monospace !important;
      font-size: 0.875rem !important;
      background: #f5f5f5 !important;
      color: #e83e8c !important;
      padding: 0.125rem 0.375rem !important;
      border-radius: 3px !important;
    }

    /* === 代码块 === */
    pre {
      background: #1e1e1e !important;
      color: #d4d4d4 !important;
      font-family: Consolas, Monaco, "Courier New", monospace !important;
      font-size: 0.875rem !important;
      line-height: 1.6 !important;
      padding: 1.25rem 1.5rem !important;
      border-radius: 6px !important;
      overflow-x: auto !important;
      margin: 0 0 1.5rem !important;
    }
    pre code {
      background: none !important;
      color: inherit !important;
      padding: 0 !important;
      border-radius: 0 !important;
      font-size: inherit !important;
    }

    /* === 引用块 === */
    blockquote {
      border-left: 4px solid #ff6600 !important;
      background: #fff9f5 !important;
      margin: 0 0 1.5rem !important;
      padding: 0.75rem 1.25rem !important;
      color: #555 !important;
    }
    blockquote p {
      margin: 0 !important;
    }

    /* === 图片 === */
    img {
      max-width: 100% !important;
      height: auto !important;
      display: block !important;
      margin: 0 auto 0.5rem !important;
      border-radius: 4px !important;
    }

    /* === 列表 === */
    ul, ol {
      line-height: 1.8 !important;
      margin: 0 0 1.5rem !important;
      padding-left: 1.5rem !important;
    }
    li {
      margin-bottom: 0.5rem !important;
    }

    /* === 分隔线 === */
    hr {
      border: none !important;
      border-top: 1px solid #ebebeb !important;
      margin: 2rem 0 !important;
    }

    /* === 链接 === */
    a {
      color: #ff6600 !important;
      text-decoration: none !important;
    }
    a:hover {
      text-decoration: underline !important;
    }
  `;
document.documentElement.appendChild(s);
