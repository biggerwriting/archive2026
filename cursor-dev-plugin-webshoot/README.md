# WebShoot Scroll Capture

> 一款轻量级 Chrome 浏览器扩展，支持**可视区域截图**、**整页滚动截图**和**网页转 Markdown 导出**，无需任何外部依赖。

---

## 目录

- [功能概览](#功能概览)
- [技术栈](#技术栈)
- [文件结构](#文件结构)
- [实现原理](#实现原理)
  - [可视区域截图](#1-可视区域截图)
  - [整页滚动截图](#2-整页滚动截图)
  - [网页转 Markdown](#3-网页转-markdown)
- [安装方法](#安装方法)
- [使用方法](#使用方法)
- [权限说明](#权限说明)
- [已知限制](#已知限制)

---

## 功能概览

| 功能 | 说明 |
|------|------|
| 📸 截图当前可视区域 | 捕获浏览器当前视窗内的内容，即时预览并下载 PNG |
| 📜 整页滚动截图 | 自动分段滚动页面，将所有截图帧拼接为完整长图 |
| 📝 导出为 Markdown | 提取页面主体内容，转换为结构化 Markdown 文本并下载 |

---

## 技术栈

| 层级 | 技术 |
|------|------|
| 扩展规范 | Chrome Extension **Manifest V3 (MV3)** |
| 后台脚本 | **Service Worker**（`background.js`） |
| 页面注入 | **Content Script**（`content.js`） |
| 图像合成 | **HTML5 Canvas API** |
| 数据存储 | **`chrome.storage.local`** |
| 文件下载 | **`chrome.downloads` API** |
| 截图捕获 | **`chrome.tabs.captureVisibleTab`** |
| 前端语言 | 原生 HTML / CSS / JavaScript（无任何框架依赖） |

---

## 文件结构

```
cursor-dev-plugin-webshoot/
├── manifest.json      # 扩展清单，声明权限与入口
├── background.js      # Service Worker：核心截图与导出逻辑
├── content.js         # Content Script：页面滚动控制与 DOM 解析
├── popup.html         # 弹出面板 HTML
├── popup.js           # 弹出面板交互逻辑
├── preview.html       # 截图预览页 HTML
├── preview.js         # 截图预览与 Canvas 合成逻辑
├── markdown.html      # Markdown 预览页 HTML
├── markdown.js        # Markdown 预览与下载逻辑
└── styles.css         # 共享样式
```

---

## 实现原理

### 1. 可视区域截图

**流程：**

```
用户点击按钮
  → popup.js 发送 CAPTURE_VISIBLE 消息
  → background.js 调用 chrome.tabs.captureVisibleTab()
  → 获得当前视窗的 PNG DataURL
  → 写入 chrome.storage.local
  → 新标签页打开 preview.html
  → preview.js 从 storage 读取数据，绘制到 <canvas>
  → 用户点击下载，调用 chrome.downloads.download()
```

**关键 API：**
- `chrome.tabs.captureVisibleTab(windowId, { format: "png" })` — 捕获当前可见视窗

---

### 2. 整页滚动截图

这是最复杂的功能，分为**采集**和**合成**两个阶段。

#### 采集阶段（background.js + content.js 协作）

```
background.js                         content.js（注入到目标页面）
     │                                       │
     │── INIT_CAPTURE ──────────────────────>│ 记录初始 scrollY
     │<─ { metrics, originalScrollY } ───────│ 返回页面尺寸信息
     │                                       │
     │  计算滚动点列表：[0, vh, 2*vh, ...]   │
     │                                       │
     │ for each scrollPoint:                 │
     │── SCROLL_TO { y } ───────────────────>│ window.scrollTo(y)
     │                 等待 120ms 后响应      │
     │<─ { actualY } ─────────────────────── │
     │  sleep(400ms)  ← 防止超出 API 限速    │
     │  captureVisibleTab() → 存入 frames[]  │
     │                                       │
     │── RESTORE_SCROLL ────────────────────>│ 还原原始 scrollY
```

> **限速说明：** Chrome 的 `captureVisibleTab` 限制为每秒最多 **2 次**调用（`MAX_CAPTURE_VISIBLE_TAB_CALLS_PER_SECOND`）。代码中通过 content.js 内 120ms 滚动稳定延迟 + background.js 内 400ms sleep，确保两次捕获间隔约 **520ms**，稳定运行在限速以内。

#### 合成阶段（preview.js）

```
读取 frames 数组（每帧含 y 坐标 + imageDataUrl）
  → 计算设备像素比（devicePixelRatio）换算真实像素高度
  → 创建完整尺寸的 <canvas>（宽 = 视窗宽，高 = 页面总高 × 像素比）
  → for each frame:
      drawY = frame.y × ratio
      ctx.drawImage(img, 0, 0, img.width, drawHeight, 0, drawY, ...)
  → 输出连续完整的长图
```

**页面尺寸获取（content.js）：**
```js
totalHeight = Math.max(
  document.documentElement.scrollHeight,
  document.body.scrollHeight,
  document.documentElement.offsetHeight,
  ...
)
```
取多个来源的最大值，兼容各类页面布局。

---

### 3. 网页转 Markdown

content.js 中实现了一个轻量级的 **HTML → Markdown 转换器**，无需引入第三方库。

#### 主内容区域识别（`pickMainNode`）

优先寻找语义化标签，避免抓取导航栏、侧边栏等噪音元素：

```
1. 优先选取 <article> 或 <main>
2. 若无，扫描页面前 120 个候选块级元素
3. 过滤掉 nav / aside / header / footer 内的元素
4. 按评分排序：score = 文本长度 + 标题数量 × 500
5. 选取得分最高的区域作为主内容节点
```

#### HTML 标签转换规则

| HTML 标签 | Markdown 输出 |
|-----------|--------------|
| `<h1>` ~ `<h6>` | `#` ~ `######` 标题 |
| `<p>` | 段落文本 + 空行 |
| `<strong>` / `<b>` | `**加粗**` |
| `<em>` / `<i>` | `*斜体*` |
| `<code>`（行内） | `` `代码` `` |
| `<pre><code>` | ` ```语言\n代码\n``` ` 围栏代码块 |
| `<a>` | `[文本](链接)` |
| `<img>` | `![alt](src)`，路径转绝对 URL |
| `<ul>` / `<ol>` | `- 项目` / `1. 项目`，支持嵌套缩进 |
| `<br>` | 换行 `\n` |
| `<script>` / `<style>` 等 | 直接跳过 |

#### 导出安全限制

- 单次导出上限 **100 万字符**，超出自动截断并提示 `[导出内容过长，已截断]`
- `chrome.storage.local` 单条数据上限约 5MB

---

## 安装方法

> 当前为开发者模式安装（未上架 Chrome 应用商店）。

1. 打开 Chrome 浏览器，地址栏输入：
   ```
   chrome://extensions
   ```
2. 打开右上角 **开发者模式** 开关
3. 点击 **加载已解压的扩展程序**
4. 选择本项目根目录（包含 `manifest.json` 的文件夹）
5. 扩展图标出现在工具栏，安装完成

> **更新代码后**：回到 `chrome://extensions`，点击扩展卡片上的刷新按钮（🔄）使改动生效。

---

## 使用方法

### 截图当前可视区域

1. 打开任意网页
2. 点击工具栏中的 **WebShoot** 图标
3. 点击 **「截图当前可视区域」**
4. 自动弹出预览页，确认后点击 **「下载 PNG」**

### 整页滚动截图

1. 打开目标网页，等待页面完全加载
2. 点击 **WebShoot** 图标
3. 点击 **「整页滚动截图」**（蓝色主按钮）
4. 扩展会自动滚动页面并逐帧截图（页面越长耗时越久）
5. 完成后自动弹出预览页，显示拼合后的完整长图
6. 点击 **「下载 PNG」** 保存

### 导出为 Markdown

1. 打开要提取内容的网页
2. 点击 **WebShoot** 图标
3. 点击 **「导出当前网页为 Markdown」**
4. 弹出预览页，显示提取的 Markdown 文本
5. 可直接复制，或点击 **「下载 .md」** 保存为文件

---

## 权限说明

| 权限 | 用途 |
|------|------|
| `activeTab` | 访问当前激活标签页信息 |
| `scripting` | 向页面注入 content.js |
| `tabs` | 获取标签页 ID、窗口 ID，调用 captureVisibleTab |
| `storage` | 临时存储截图帧数据和 Markdown 文本 |
| `downloads` | 触发 PNG / Markdown 文件下载 |
| `<all_urls>` | 允许在任意 URL 的页面上注入脚本 |

---

## 已知限制

| 限制 | 说明 |
|------|------|
| 整页截图耗时 | 每帧间隔约 520ms，100 屏的长页需约 52 秒 |
| 仅支持 Chrome | 使用 MV3 及 Chrome 专属 API，不兼容 Firefox |
| 特殊页面 | `chrome://` 协议页及扩展商店页面无法注入 content.js |
| 懒加载内容 | 快速滚动时部分懒加载图片/内容可能未完全渲染 |
| 固定元素叠影 | 带 sticky/fixed 元素的页面在长图中可能出现重复条带 |
| 存储上限 | 超大页面的截图帧数据可能超出 `storage.local` 5MB 限制 |
