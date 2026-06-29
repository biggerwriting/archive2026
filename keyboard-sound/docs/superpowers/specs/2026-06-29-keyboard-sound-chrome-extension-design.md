# Keyboard Sound Chrome 扩展 — 设计文档

**日期：** 2026-06-29  
**状态：** 已确认，待实现  

---

## 1. 项目概述

一个 Chrome 扩展，当用户在浏览器任意网页上打字时，自动播放钢琴键或打字机按键音效，提升工作趣味性。用户可通过插件图标弹出的控制面板切换音色、音符模式和音量。

---

## 2. 整体架构

```
keyboard-sound/
├── manifest.json          # Chrome 扩展配置（Manifest V3）
├── background.js          # Service Worker：状态初始化
├── content.js             # 注入每个网页：监听 keydown 事件 + 播放音频
├── popup/
│   ├── popup.html         # 点击图标弹出的控制面板
│   ├── popup.js           # 控制面板交互逻辑
│   └── popup.css          # 控制面板样式
├── shared/
│   └── note-engine.js     # 音符选择逻辑（三种模式，纯函数）
└── assets/
    ├── piano/             # WebAudioFont 钢琴音色数据文件（离线打包）
    ├── typewriter/        # 打字机 WAV 音效
    │   ├── key.wav        # 普通字母/数字键
    │   ├── space.wav      # 空格键
    │   └── enter.wav      # 回车/退格键
    └── icons/             # 扩展图标（16/48/128px）
```

### 数据流

```
[用户在网页打字]
    │
    └─► content.js keydown 事件
            │
            ├─► 过滤：仅在 input / textarea / contenteditable 聚焦时触发
            │
            ├─► 读取本地缓存状态（音色、模式、音量、开关）
            │
            ├─► [钢琴模式] note-engine.js → 选出音符名（如 E4）
            │       └─► Web Audio API → 播放对应钢琴采样
            │
            └─► [打字机模式] 判断键类型 → 播放 key.wav / space.wav / enter.wav
```

### 状态管理

所有状态存储在 `chrome.storage.local`：

| 字段 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `enabled` | boolean | `true` | 插件总开关 |
| `soundMode` | string | `"piano"` | 音色模式：`"piano"` / `"typewriter"` |
| `noteMode` | string | `"fixed"` | 音符模式：`"fixed"` / `"sequential"` / `"random"` |
| `volume` | number | `0.75` | 音量，范围 0-1 |

- content.js 启动时读取一次，之后监听 `chrome.storage.onChanged` 实时同步，无需消息传递。
- popup.js 直接读写 `chrome.storage.local`，变更即时生效。

---

## 3. 核心模块详解

### 3.1 content.js — 按键监听与音频播放

- 在 `document` 捕获阶段监听 `keydown` 事件
- **触发条件**：`document.activeElement` 为 `<input>`、`<textarea>` 或带 `contenteditable` 属性的元素
- 启动时预加载所有音频资源到 `AudioBuffer`（避免首次播放延迟）
- 每次按键创建新的 `AudioBufferSourceNode`，支持多音符同时重叠播放
- 通过 `GainNode` 控制音量

### 3.2 note-engine.js — 三种音符模式（纯函数模块）

| 模式 | key | 逻辑描述 |
|------|-----|----------|
| 固定映射 | `fixed` | A-Z 固定映射到 C4-B5（26个音），数字 0-9 映射 C3-B3（10个音） |
| 顺序循环 | `sequential` | 维护全局指针，每次按键取 C 大调音阶下一个音，到头循环 |
| 随机和谐 | `random` | 每次从 C 大调 7 个音（C D E F G A B）的 C4-B5 范围内随机选一个 |

接口：
```js
// 输入：按键信息 + 当前模式 + 当前状态（sequential 模式需要指针）
// 输出：音符名字符串，如 "C4"、"E4"、"G5"
getNoteForKey(key, mode, state) → { note: "E4", nextState: {...} }
```

### 3.3 音频资源

**钢琴音色**
- 使用 WebAudioFont 的 `acoustic_grand_piano` 音色
- 将音色 JS 数据文件下载后打包进扩展 `assets/piano/`（完全离线，无 CSP 问题）
- 覆盖范围：C3-B5，共 3 个八度（约 25 个采样文件）

**打字机音效**
- 从 freesound.org 下载 CC0 授权音效，打包进 `assets/typewriter/`
- `key.wav`：普通字母/数字按键，清脆短促的机械声
- `space.wav`：空格键，更宽更沉的机械声
- `enter.wav`：回车/退格键，更重更饱满的机械声

### 3.4 manifest.json 权限

```json
{
  "manifest_version": 3,
  "permissions": ["storage"],
  "host_permissions": ["<all_urls>"],
  "content_scripts": [{
    "matches": ["<all_urls>"],
    "js": ["shared/note-engine.js", "content.js"]
  }]
}
```

---

## 4. Popup UI 设计

### 布局（宽 280px）

```
┌─────────────────────────────┐
│  🎹 Keyboard Sound    [●ON] │  ← 标题 + 主开关
├─────────────────────────────┤
│  音色                        │
│  [🎹 钢琴]  [⌨️ 打字机]      │
├─────────────────────────────┤
│  音符模式  (钢琴模式下显示)   │
│  [固定映射] [顺序循环] [随机] │
├─────────────────────────────┤
│  音量                        │
│  🔈 ──────●────── 🔊  75%   │
└─────────────────────────────┘
```

### 交互规则

- 主开关关闭时，下方所有控件置灰不可操作
- 切换到打字机模式时，"音符模式"区域淡出隐藏
- 所有状态变更即时写入 `chrome.storage.local`，无需保存按钮
- 深色主题，与浏览器扩展 popup 的深色模式兼容

---

## 5. 文件职责边界

| 文件 | 职责 | 不做什么 |
|------|------|----------|
| `content.js` | 监听按键、播放音频、缓存状态 | 不修改网页 DOM，不处理音符逻辑 |
| `note-engine.js` | 纯函数，输入键+模式，输出音符名 | 不接触 Audio API，不读 storage |
| `popup.js` | 读写 storage，更新 UI | 不直接控制 content.js |
| `background.js` | 扩展安装时初始化默认 storage 值 | 不做持续运行的任务 |

---

## 6. 不在本期范围内

- Firefox / Safari 扩展支持
- 多音色切换（木琴、合成器等）
- 自定义音效上传
- 网站黑白名单（在所有网页生效）
- 键程动画或视觉反馈
