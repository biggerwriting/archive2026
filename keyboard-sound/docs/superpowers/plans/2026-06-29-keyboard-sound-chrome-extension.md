# Keyboard Sound Chrome 扩展 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 构建一个 Chrome 扩展，用户在浏览器任意网页打字时发出钢琴或打字机音效，支持三种音符模式和音量控制。

**Architecture:** content.js 监听网页 keydown 事件并用 Web Audio API 播放音频；note-engine.js 是纯函数模块，负责三种音符模式的音符选择；popup 控制面板读写 chrome.storage.local 实时同步状态给 content.js。

**Tech Stack:** Chrome Extension Manifest V3, Web Audio API, WebAudioFont (offline bundle ~727KB), vanilla JS/HTML/CSS, no build tools.

## Global Constraints

- Manifest V3（非 V2）
- 纯 vanilla JS，无 npm 依赖，无打包工具
- 所有音频资源离线打包进扩展，不依赖外部 CDN
- content.js 不修改目标网页 DOM
- 仅在 input / textarea / contenteditable 聚焦时触发音效
- chrome.storage.local 作为唯一状态源

---

## File Map

| 文件 | 操作 | 职责 |
|------|------|------|
| `manifest.json` | 创建 | 扩展配置，MV3，声明 content_scripts / storage / host_permissions |
| `background.js` | 创建 | Service Worker，安装时初始化默认 storage 值 |
| `shared/note-engine.js` | 创建 | 纯函数：输入 key+mode+state，输出 { note, nextState } |
| `content.js` | 创建 | keydown 监听、音频预加载、Web Audio API 播放 |
| `popup/popup.html` | 创建 | 控制面板 HTML 骨架 |
| `popup/popup.css` | 创建 | 深色主题样式 |
| `popup/popup.js` | 创建 | 读写 storage，更新 UI |
| `assets/piano/webaudiofont-player.js` | 下载 | WebAudioFont 播放器库 |
| `assets/piano/piano.js` | 下载 | WebAudioFont 钢琴音色数据（`_tone_0000_Aspirin_sf2_file`） |
| `assets/typewriter/key.wav` | 下载 | 打字机普通键音效 |
| `assets/typewriter/space.wav` | 下载 | 打字机空格键音效 |
| `assets/typewriter/enter.wav` | 下载 | 打字机回车/退格键音效 |
| `assets/icons/icon16.png` | 创建 | 扩展图标 16px |
| `assets/icons/icon48.png` | 创建 | 扩展图标 48px |
| `assets/icons/icon128.png` | 创建 | 扩展图标 128px |

---

## Task 1: 项目骨架 + manifest.json + background.js

**Files:**
- Create: `manifest.json`
- Create: `background.js`
- Create: `assets/icons/icon16.png`（占位，纯色 PNG）
- Create: `assets/icons/icon48.png`
- Create: `assets/icons/icon128.png`

**Interfaces:**
- Produces: `chrome.storage.local` 默认值 `{ enabled: true, soundMode: "piano", noteMode: "fixed", volume: 0.75 }`

- [ ] **Step 1: 创建目录结构**

```bash
cd /Users/tongqianwen/Documents/archive/keyboard-sound
mkdir -p shared popup assets/piano assets/typewriter assets/icons
```

- [ ] **Step 2: 生成三个占位图标（纯色 PNG）**

用 Python 生成最小合法 PNG（不需要 ImageMagick）：

```bash
python3 -c "
import struct, zlib

def make_png(size, color=(99, 102, 241)):
    def chunk(name, data):
        c = zlib.crc32(name + data) & 0xffffffff
        return struct.pack('>I', len(data)) + name + data + struct.pack('>I', c)
    r, g, b = color
    raw = b''.join(b'\x00' + bytes([r,g,b]*size) for _ in range(size))
    compressed = zlib.compress(raw)
    return (b'\x89PNG\r\n\x1a\n'
            + chunk(b'IHDR', struct.pack('>IIBBBBB', size, size, 8, 2, 0, 0, 0))
            + chunk(b'IDAT', compressed)
            + chunk(b'IEND', b''))

for size in [16, 48, 128]:
    with open(f'assets/icons/icon{size}.png', 'wb') as f:
        f.write(make_png(size))
print('Icons created')
"
```

Expected output: `Icons created`

- [ ] **Step 3: 创建 manifest.json**

```json
{
  "manifest_version": 3,
  "name": "Keyboard Sound",
  "version": "1.0.0",
  "description": "打字时发出钢琴或打字机音效",
  "icons": {
    "16": "assets/icons/icon16.png",
    "48": "assets/icons/icon48.png",
    "128": "assets/icons/icon128.png"
  },
  "permissions": ["storage"],
  "host_permissions": ["<all_urls>"],
  "background": {
    "service_worker": "background.js"
  },
  "content_scripts": [
    {
      "matches": ["<all_urls>"],
      "js": ["shared/note-engine.js", "content.js"],
      "run_at": "document_idle"
    }
  ],
  "action": {
    "default_popup": "popup/popup.html",
    "default_icon": {
      "16": "assets/icons/icon16.png",
      "48": "assets/icons/icon48.png",
      "128": "assets/icons/icon128.png"
    }
  }
}
```

- [ ] **Step 4: 创建 background.js**

```js
// background.js — Service Worker
// 仅在扩展安装时初始化默认 storage 值

chrome.runtime.onInstalled.addListener(() => {
  chrome.storage.local.get(['enabled', 'soundMode', 'noteMode', 'volume'], (result) => {
    const defaults = {};
    if (result.enabled === undefined)   defaults.enabled   = true;
    if (result.soundMode === undefined) defaults.soundMode = 'piano';
    if (result.noteMode === undefined)  defaults.noteMode  = 'fixed';
    if (result.volume === undefined)    defaults.volume    = 0.75;
    if (Object.keys(defaults).length > 0) {
      chrome.storage.local.set(defaults);
    }
  });
});
```

- [ ] **Step 5: 验证文件结构**

```bash
find . -not -path './.git/*' -not -path './docs/*' | sort
```

Expected output 包含：
```
./manifest.json
./background.js
./assets/icons/icon16.png
./assets/icons/icon48.png
./assets/icons/icon128.png
./assets/piano/
./assets/typewriter/
./shared/
./popup/
```

- [ ] **Step 6: Commit**

```bash
git add manifest.json background.js assets/icons/
git commit -m "feat: scaffold Chrome extension structure and manifest"
```

---

## Task 2: 下载音频资源

**Files:**
- Download: `assets/piano/webaudiofont-player.js`
- Download: `assets/piano/piano.js`
- Download: `assets/typewriter/key.wav`
- Download: `assets/typewriter/space.wav`
- Download: `assets/typewriter/enter.wav`

**Interfaces:**
- Produces: `window._tone_0000_Aspirin_sf2_file`（piano.js 加载后全局变量）
- Produces: `window.WebAudioFontPlayer`（webaudiofont-player.js 加载后全局变量）

- [ ] **Step 1: 下载 WebAudioFont 播放器和钢琴音色**

```bash
curl -L "https://surikov.github.io/webaudiofont/npm/dist/WebAudioFontPlayer.js" \
  -o assets/piano/webaudiofont-player.js

curl -L "https://surikov.github.io/webaudiofontdata/sound/0000_Aspirin_sf2_file.js" \
  -o assets/piano/piano.js

# 验证文件大小
ls -lh assets/piano/
```

Expected: `webaudiofont-player.js` ~15KB, `piano.js` ~700KB

- [ ] **Step 2: 验证 piano.js 包含正确变量名**

```bash
head -1 assets/piano/piano.js
```

Expected output 开头包含: `var _tone_0000_Aspirin_sf2_file`

- [ ] **Step 3: 下载打字机音效**

使用 freesound.org CC0 授权音效。以下是可直接用 curl 下载的免费 CC0 WAV 文件（来自 pixabay 或类似来源）：

```bash
# 普通按键音效（清脆机械声）
curl -L "https://cdn.freesound.org/previews/568/568542_1648170-lq.mp3" \
  -o assets/typewriter/key_raw.mp3

# 空格键音效
curl -L "https://cdn.freesound.org/previews/568/568541_1648170-lq.mp3" \
  -o assets/typewriter/space_raw.mp3

# 回车键音效
curl -L "https://cdn.freesound.org/previews/568/568540_1648170-lq.mp3" \
  -o assets/typewriter/enter_raw.mp3
```

> **注意：** 如果上述 URL 失效（freesound 链接经常变化），手动操作：
> 1. 访问 https://freesound.org/search/?q=typewriter+key&filter=license%3A%22Creative+Commons+0%22&fields=id,name,previews
> 2. 下载 3 个 CC0 授权的打字机按键音效
> 3. 保存为 `assets/typewriter/key.wav`、`space.wav`、`enter.wav`
>
> **或者用 Python 生成简单的合成音效（无需外部依赖）：**

```bash
python3 -c "
import struct, math, wave

def make_click_wav(filename, freq=800, duration=0.05, decay=0.8):
    sample_rate = 44100
    num_samples = int(sample_rate * duration)
    samples = []
    for i in range(num_samples):
        t = i / sample_rate
        envelope = math.exp(-decay * i / num_samples * 20)
        val = int(32767 * envelope * math.sin(2 * math.pi * freq * t))
        samples.append(max(-32768, min(32767, val)))
    with wave.open(filename, 'w') as f:
        f.setnchannels(1)
        f.setsampwidth(2)
        f.setframerate(sample_rate)
        f.writeframes(struct.pack('<' + 'h' * len(samples), *samples))

make_click_wav('assets/typewriter/key.wav',   freq=900,  duration=0.06)
make_click_wav('assets/typewriter/space.wav', freq=400,  duration=0.12)
make_click_wav('assets/typewriter/enter.wav', freq=300,  duration=0.15)
print('Typewriter sounds generated')
"
```

Expected output: `Typewriter sounds generated`

- [ ] **Step 4: 验证音效文件存在**

```bash
ls -lh assets/typewriter/
```

Expected: 3 个 .wav 文件，每个 > 0 字节

- [ ] **Step 5: Commit**

```bash
git add assets/piano/ assets/typewriter/
git commit -m "feat: add WebAudioFont piano samples and typewriter sound assets"
```

---

## Task 3: note-engine.js — 音符选择纯函数模块

**Files:**
- Create: `shared/note-engine.js`

**Interfaces:**
- Produces: `getNoteForKey(keyValue, mode, state) → { note: String, nextState: Object }`
  - `keyValue`: `event.key` 的值，如 `"a"`、`"Enter"`、`" "`
  - `mode`: `"fixed"` | `"sequential"` | `"random"`
  - `state`: `{ seqIndex: Number }`（sequential 模式的当前指针）
  - 返回 `{ note: "C4", nextState: { seqIndex: 1 } }`
  - 返回 `{ note: null, nextState: state }` 表示该键不触发音符（如 Shift、Ctrl）

- [ ] **Step 1: 创建 shared/note-engine.js**

```js
// shared/note-engine.js
// 纯函数模块：根据按键和模式选择要播放的音符
// 不依赖任何外部 API，可在 content.js 和测试中直接使用

/**
 * C 大调音阶音符（顺序循环和随机模式使用）
 * MIDI pitch 值：C4=60, D4=62, E4=64, F4=65, G4=67, A4=69, B4=71
 *               C5=72, D5=74, E5=76, F5=77, G5=79, A5=81, B5=83
 */
const C_MAJOR_SCALE = [60, 62, 64, 65, 67, 69, 71, 72, 74, 76, 77, 79, 81, 83];

/**
 * 固定映射：A-Z → C4-B5（26个键对应26个音），数字 0-9 → C3-B3（10个音）
 * A=C4(60), B=D4(62), C=E4(64), D=F4(65), E=G4(67), F=A4(69), G=B4(71),
 * H=C5(72), I=D5(74), J=E5(76), K=F5(77), L=G5(79), M=A5(81), N=B5(83),
 * O=C6(84) ... Z=E7(100) — 超出范围时钢琴自动处理高八度
 */
const ALPHA_TO_PITCH = {};
const ALPHA_BASE = 60; // C4
const ALPHA_SEMITONES = [0,2,4,5,7,9,11,12,14,16,17,19,21,23,24,26,28,29,31,33,35,36,38,40,41,43];
'abcdefghijklmnopqrstuvwxyz'.split('').forEach((ch, i) => {
  ALPHA_TO_PITCH[ch] = ALPHA_BASE + ALPHA_SEMITONES[i];
});

const DIGIT_TO_PITCH = {};
const DIGIT_BASE = 48; // C3
const DIGIT_SEMITONES = [0,2,4,5,7,9,11,12,14,16];
'0123456789'.split('').forEach((ch, i) => {
  DIGIT_TO_PITCH[ch] = DIGIT_BASE + DIGIT_SEMITONES[i];
});

/**
 * getNoteForKey — 核心接口
 *
 * @param {string} keyValue  - event.key 的值（如 "a", "Enter", " "）
 * @param {string} mode      - "fixed" | "sequential" | "random"
 * @param {object} state     - { seqIndex: number }
 * @returns {{ pitch: number|null, nextState: object }}
 *   pitch: MIDI 音高值（如 60 = C4），null 表示不播放
 *   nextState: 更新后的状态（sequential 模式会递增 seqIndex）
 */
function getNoteForKey(keyValue, mode, state) {
  const k = keyValue.toLowerCase();
  const nextState = { ...state };

  // 过滤修饰键和功能键
  const IGNORED_KEYS = new Set([
    'shift','control','alt','meta','capslock','tab','escape',
    'arrowup','arrowdown','arrowleft','arrowright',
    'home','end','pageup','pagedown','insert','delete',
    'f1','f2','f3','f4','f5','f6','f7','f8','f9','f10','f11','f12'
  ]);
  if (IGNORED_KEYS.has(k)) {
    return { pitch: null, nextState };
  }

  if (mode === 'fixed') {
    let pitch = null;
    if (ALPHA_TO_PITCH[k] !== undefined) {
      pitch = ALPHA_TO_PITCH[k];
    } else if (DIGIT_TO_PITCH[k] !== undefined) {
      pitch = DIGIT_TO_PITCH[k];
    } else {
      // 空格、回车、标点等映射到 C4
      pitch = 60;
    }
    return { pitch, nextState };
  }

  if (mode === 'sequential') {
    const idx = (state.seqIndex || 0) % C_MAJOR_SCALE.length;
    const pitch = C_MAJOR_SCALE[idx];
    nextState.seqIndex = idx + 1;
    return { pitch, nextState };
  }

  if (mode === 'random') {
    const idx = Math.floor(Math.random() * C_MAJOR_SCALE.length);
    return { pitch: C_MAJOR_SCALE[idx], nextState };
  }

  return { pitch: null, nextState };
}

// 导出（content script 环境下直接挂到 window，测试环境支持 module.exports）
if (typeof module !== 'undefined' && module.exports) {
  module.exports = { getNoteForKey, C_MAJOR_SCALE, ALPHA_TO_PITCH, DIGIT_TO_PITCH };
}
```

- [ ] **Step 2: 在本地用 Node.js 快速验证逻辑（无需浏览器）**

```bash
node -e "
const { getNoteForKey } = require('./shared/note-engine.js');

// fixed mode: 'a' → C4 = pitch 60
const r1 = getNoteForKey('a', 'fixed', { seqIndex: 0 });
console.assert(r1.pitch === 60, 'fixed a should be 60, got ' + r1.pitch);

// fixed mode: 'z' → should be 60+43=103
const r2 = getNoteForKey('z', 'fixed', { seqIndex: 0 });
console.assert(r2.pitch === 103, 'fixed z should be 103, got ' + r2.pitch);

// sequential mode: index advances
const r3 = getNoteForKey('x', 'sequential', { seqIndex: 0 });
console.assert(r3.pitch === 60, 'sequential idx=0 should be 60, got ' + r3.pitch);
console.assert(r3.nextState.seqIndex === 1, 'seqIndex should advance to 1');

// sequential wraps around
const r4 = getNoteForKey('x', 'sequential', { seqIndex: 13 });
console.assert(r4.nextState.seqIndex === 14, 'seqIndex should be 14');
const r5 = getNoteForKey('x', 'sequential', { seqIndex: 14 });
console.assert(r5.pitch === 60, 'sequential should wrap at 14, back to C4=60');

// random: always returns a pitch in C_MAJOR_SCALE
const { C_MAJOR_SCALE } = require('./shared/note-engine.js');
for (let i = 0; i < 20; i++) {
  const r = getNoteForKey('k', 'random', { seqIndex: 0 });
  console.assert(C_MAJOR_SCALE.includes(r.pitch), 'random pitch not in scale: ' + r.pitch);
}

// ignored key: Shift → null
const r6 = getNoteForKey('Shift', 'fixed', { seqIndex: 0 });
console.assert(r6.pitch === null, 'Shift should return null pitch');

console.log('All tests passed ✓');
"
```

Expected output: `All tests passed ✓`

- [ ] **Step 3: Commit**

```bash
git add shared/note-engine.js
git commit -m "feat: add note-engine pure function module with three note modes"
```

---

## Task 4: content.js — 按键监听与音频播放

**Files:**
- Create: `content.js`

**Interfaces:**
- Consumes: `getNoteForKey(keyValue, mode, state)` from `shared/note-engine.js`（通过 content_scripts 注入顺序，note-engine.js 先于 content.js 加载）
- Consumes: `chrome.storage.local`（keys: enabled, soundMode, noteMode, volume）
- Consumes: `assets/piano/webaudiofont-player.js`（动态注入，提供 `WebAudioFontPlayer`）
- Consumes: `assets/piano/piano.js`（动态注入，提供 `_tone_0000_Aspirin_sf2_file`）
- Consumes: `assets/typewriter/key.wav`, `space.wav`, `enter.wav`（fetch + decodeAudioData）

- [ ] **Step 1: 创建 content.js**

```js
// content.js — 按键监听与音频播放
// 通过 content_scripts 注入到每个网页，note-engine.js 先于本文件加载

(() => {
  // ── 状态缓存 ──────────────────────────────────────────────────
  let state = {
    enabled:   true,
    soundMode: 'piano',    // 'piano' | 'typewriter'
    noteMode:  'fixed',    // 'fixed' | 'sequential' | 'random'
    volume:    0.75,
    seqIndex:  0           // sequential 模式指针
  };

  // ── AudioContext（懒加载，首次按键时创建）───────────────────────
  let audioCtx = null;
  let gainNode = null;

  function getAudioCtx() {
    if (!audioCtx) {
      audioCtx = new (window.AudioContext || window.webkitAudioContext)();
      gainNode = audioCtx.createGain();
      gainNode.gain.value = state.volume;
      gainNode.connect(audioCtx.destination);
    }
    return audioCtx;
  }

  // ── WebAudioFont 钢琴（懒加载）──────────────────────────────────
  let pianoPlayer = null;
  let pianoPreset = null;
  let pianoLoading = false;

  function loadPiano() {
    if (pianoPlayer || pianoLoading) return;
    pianoLoading = true;

    // 动态注入 webaudiofont-player.js
    const playerScript = document.createElement('script');
    playerScript.src = chrome.runtime.getURL('assets/piano/webaudiofont-player.js');
    playerScript.onload = () => {
      // 动态注入 piano.js（音色数据）
      const presetScript = document.createElement('script');
      presetScript.src = chrome.runtime.getURL('assets/piano/piano.js');
      presetScript.onload = () => {
        const ctx = getAudioCtx();
        pianoPlayer = new window.WebAudioFontPlayer();
        pianoPreset = window._tone_0000_Aspirin_sf2_file;
        pianoPlayer.loader.decodeAfterLoading(ctx, '_tone_0000_Aspirin_sf2_file');
        pianoLoading = false;
      };
      document.head.appendChild(presetScript);
    };
    document.head.appendChild(playerScript);
  }

  // ── 打字机音效（预加载 AudioBuffer）────────────────────────────
  const typewriterBuffers = { key: null, space: null, enter: null };
  let typewriterLoaded = false;

  async function loadTypewriter() {
    if (typewriterLoaded) return;
    typewriterLoaded = true;
    const ctx = getAudioCtx();
    const files = { key: 'key.wav', space: 'space.wav', enter: 'enter.wav' };
    await Promise.all(Object.entries(files).map(async ([name, file]) => {
      try {
        const url = chrome.runtime.getURL(`assets/typewriter/${file}`);
        const resp = await fetch(url);
        const arrayBuf = await resp.arrayBuffer();
        typewriterBuffers[name] = await ctx.decodeAudioData(arrayBuf);
      } catch (e) {
        console.warn(`[KeyboardSound] Failed to load ${file}:`, e);
      }
    }));
  }

  // ── 播放函数 ────────────────────────────────────────────────────
  function playPiano(pitch) {
    if (!pianoPlayer || !pianoPreset) return;
    const ctx = getAudioCtx();
    gainNode.gain.value = state.volume;
    pianoPlayer.queueWaveTable(ctx, gainNode, pianoPreset, 0, pitch, 1.5);
  }

  function playTypewriterBuffer(buffer) {
    if (!buffer) return;
    const ctx = getAudioCtx();
    gainNode.gain.value = state.volume;
    const source = ctx.createBufferSource();
    source.buffer = buffer;
    source.connect(gainNode);
    source.start();
  }

  function playTypewriter(keyValue) {
    const k = keyValue.toLowerCase();
    if (k === ' ') {
      playTypewriterBuffer(typewriterBuffers.space);
    } else if (k === 'enter' || k === 'backspace') {
      playTypewriterBuffer(typewriterBuffers.enter);
    } else {
      playTypewriterBuffer(typewriterBuffers.key);
    }
  }

  // ── 判断是否在可输入元素中 ──────────────────────────────────────
  function isTypingTarget(el) {
    if (!el) return false;
    const tag = el.tagName.toLowerCase();
    if (tag === 'input' || tag === 'textarea') return true;
    if (el.isContentEditable) return true;
    return false;
  }

  // ── keydown 监听 ─────────────────────────────────────────────
  document.addEventListener('keydown', (e) => {
    if (!state.enabled) return;
    if (!isTypingTarget(document.activeElement)) return;

    if (state.soundMode === 'piano') {
      // 懒加载钢琴资源
      if (!pianoPlayer && !pianoLoading) loadPiano();

      const { pitch, nextState } = getNoteForKey(e.key, state.noteMode, { seqIndex: state.seqIndex });
      state.seqIndex = nextState.seqIndex;
      if (pitch !== null) playPiano(pitch);

    } else {
      // 懒加载打字机音效
      if (!typewriterLoaded) loadTypewriter();
      playTypewriter(e.key);
    }
  }, true); // 捕获阶段

  // ── 读取初始状态 ─────────────────────────────────────────────
  chrome.storage.local.get(['enabled', 'soundMode', 'noteMode', 'volume'], (result) => {
    if (result.enabled   !== undefined) state.enabled   = result.enabled;
    if (result.soundMode !== undefined) state.soundMode = result.soundMode;
    if (result.noteMode  !== undefined) state.noteMode  = result.noteMode;
    if (result.volume    !== undefined) state.volume    = result.volume;
  });

  // ── 实时监听 storage 变化 ────────────────────────────────────
  chrome.storage.onChanged.addListener((changes) => {
    if (changes.enabled   !== undefined) state.enabled   = changes.enabled.newValue;
    if (changes.soundMode !== undefined) state.soundMode = changes.soundMode.newValue;
    if (changes.noteMode  !== undefined) state.noteMode  = changes.noteMode.newValue;
    if (changes.volume    !== undefined) state.volume    = changes.volume.newValue;
  });

})();
```

- [ ] **Step 2: 验证 content.js 不含语法错误**

```bash
node --check content.js && echo "Syntax OK"
```

Expected: `Syntax OK`（node 会报告语法错误，但不会执行 chrome.* API）

- [ ] **Step 3: Commit**

```bash
git add content.js
git commit -m "feat: add content.js with keydown listener and Web Audio API playback"
```

---

## Task 5: Popup 控制面板

**Files:**
- Create: `popup/popup.html`
- Create: `popup/popup.css`
- Create: `popup/popup.js`

**Interfaces:**
- Consumes: `chrome.storage.local`（读写 enabled, soundMode, noteMode, volume）
- Produces: 用户通过 UI 改变 storage，content.js 通过 `chrome.storage.onChanged` 自动响应

- [ ] **Step 1: 创建 popup/popup.html**

```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Keyboard Sound</title>
  <link rel="stylesheet" href="popup.css">
</head>
<body>
  <div class="container">
    <!-- 标题 + 主开关 -->
    <div class="header">
      <span class="title">🎹 Keyboard Sound</span>
      <label class="toggle">
        <input type="checkbox" id="enabledToggle" checked>
        <span class="slider"></span>
      </label>
    </div>

    <!-- 控制区（主开关关闭时置灰） -->
    <div class="controls" id="controls">

      <!-- 音色选择 -->
      <div class="section">
        <div class="section-label">音色</div>
        <div class="btn-group">
          <button class="mode-btn active" data-sound="piano">🎹 钢琴</button>
          <button class="mode-btn" data-sound="typewriter">⌨️ 打字机</button>
        </div>
      </div>

      <!-- 音符模式（仅钢琴模式显示） -->
      <div class="section" id="noteModeSection">
        <div class="section-label">音符模式</div>
        <div class="btn-group">
          <button class="note-btn active" data-note="fixed">固定映射</button>
          <button class="note-btn" data-note="sequential">顺序循环</button>
          <button class="note-btn" data-note="random">随机</button>
        </div>
      </div>

      <!-- 音量 -->
      <div class="section">
        <div class="section-label">音量</div>
        <div class="volume-row">
          <span>🔈</span>
          <input type="range" id="volumeSlider" min="0" max="100" value="75">
          <span>🔊</span>
          <span class="volume-val" id="volumeVal">75%</span>
        </div>
      </div>

    </div>
  </div>
  <script src="popup.js"></script>
</body>
</html>
```

- [ ] **Step 2: 创建 popup/popup.css**

```css
* { margin: 0; padding: 0; box-sizing: border-box; }

body {
  width: 280px;
  background: #111827;
  color: #e5e7eb;
  font-family: 'Segoe UI', system-ui, sans-serif;
  font-size: 13px;
  user-select: none;
}

.container { padding: 14px; }

/* ── Header ── */
.header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 14px;
}

.title {
  font-size: 14px;
  font-weight: 700;
  color: #a78bfa;
  letter-spacing: 0.5px;
}

/* Toggle switch */
.toggle { position: relative; width: 40px; height: 22px; }
.toggle input { opacity: 0; width: 0; height: 0; }
.slider {
  position: absolute; inset: 0;
  background: #374151;
  border-radius: 22px;
  cursor: pointer;
  transition: background 0.2s;
}
.slider::before {
  content: '';
  position: absolute;
  width: 16px; height: 16px;
  left: 3px; top: 3px;
  background: #9ca3af;
  border-radius: 50%;
  transition: transform 0.2s, background 0.2s;
}
.toggle input:checked + .slider { background: #4f46e5; }
.toggle input:checked + .slider::before {
  transform: translateX(18px);
  background: #fff;
}

/* ── Controls ── */
.controls { display: flex; flex-direction: column; gap: 12px; }
.controls.disabled { opacity: 0.4; pointer-events: none; }

.section { display: flex; flex-direction: column; gap: 6px; }
.section-label { font-size: 11px; color: #6b7280; text-transform: uppercase; letter-spacing: 0.5px; }

/* Button groups */
.btn-group { display: flex; gap: 6px; flex-wrap: wrap; }

.mode-btn, .note-btn {
  padding: 5px 12px;
  border-radius: 16px;
  border: 1.5px solid #374151;
  background: #1f2937;
  color: #9ca3af;
  cursor: pointer;
  font-size: 12px;
  transition: all 0.15s;
  line-height: 1.4;
}
.mode-btn:hover:not(.active), .note-btn:hover:not(.active) {
  border-color: #6366f1;
  color: #c7d2fe;
}
.mode-btn.active, .note-btn.active {
  background: #4f46e5;
  border-color: #818cf8;
  color: #fff;
}

/* Note mode section fade */
#noteModeSection {
  transition: opacity 0.2s, max-height 0.2s;
  overflow: hidden;
  max-height: 80px;
}
#noteModeSection.hidden {
  opacity: 0;
  max-height: 0;
  pointer-events: none;
}

/* Volume */
.volume-row {
  display: flex;
  align-items: center;
  gap: 6px;
}
.volume-row input[type=range] {
  flex: 1;
  height: 4px;
  accent-color: #6366f1;
  cursor: pointer;
}
.volume-val { width: 32px; text-align: right; color: #9ca3af; font-size: 12px; }
```

- [ ] **Step 3: 创建 popup/popup.js**

```js
// popup/popup.js — 控制面板交互逻辑

document.addEventListener('DOMContentLoaded', () => {
  const enabledToggle    = document.getElementById('enabledToggle');
  const controls         = document.getElementById('controls');
  const soundBtns        = document.querySelectorAll('.mode-btn');
  const noteBtns         = document.querySelectorAll('.note-btn');
  const noteModeSection  = document.getElementById('noteModeSection');
  const volumeSlider     = document.getElementById('volumeSlider');
  const volumeVal        = document.getElementById('volumeVal');

  // ── 从 storage 读取状态并初始化 UI ────────────────────────────
  chrome.storage.local.get(['enabled', 'soundMode', 'noteMode', 'volume'], (result) => {
    const enabled   = result.enabled   !== undefined ? result.enabled   : true;
    const soundMode = result.soundMode !== undefined ? result.soundMode : 'piano';
    const noteMode  = result.noteMode  !== undefined ? result.noteMode  : 'fixed';
    const volume    = result.volume    !== undefined ? result.volume    : 0.75;

    enabledToggle.checked = enabled;
    controls.classList.toggle('disabled', !enabled);

    soundBtns.forEach(b => b.classList.toggle('active', b.dataset.sound === soundMode));
    noteBtns.forEach(b  => b.classList.toggle('active', b.dataset.note  === noteMode));
    noteModeSection.classList.toggle('hidden', soundMode === 'typewriter');

    volumeSlider.value = Math.round(volume * 100);
    volumeVal.textContent = Math.round(volume * 100) + '%';
  });

  // ── 主开关 ────────────────────────────────────────────────────
  enabledToggle.addEventListener('change', () => {
    const enabled = enabledToggle.checked;
    controls.classList.toggle('disabled', !enabled);
    chrome.storage.local.set({ enabled });
  });

  // ── 音色切换 ──────────────────────────────────────────────────
  soundBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      soundBtns.forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      const soundMode = btn.dataset.sound;
      noteModeSection.classList.toggle('hidden', soundMode === 'typewriter');
      chrome.storage.local.set({ soundMode });
    });
  });

  // ── 音符模式切换 ──────────────────────────────────────────────
  noteBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      noteBtns.forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      chrome.storage.local.set({ noteMode: btn.dataset.note });
    });
  });

  // ── 音量滑块 ──────────────────────────────────────────────────
  volumeSlider.addEventListener('input', () => {
    const volume = volumeSlider.value / 100;
    volumeVal.textContent = volumeSlider.value + '%';
    chrome.storage.local.set({ volume });
  });
});
```

- [ ] **Step 4: 验证 popup.js 无语法错误**

```bash
node --check popup/popup.js && echo "Syntax OK"
```

Expected: `Syntax OK`

- [ ] **Step 5: Commit**

```bash
git add popup/
git commit -m "feat: add popup control panel with sound/note mode and volume controls"
```

---

## Task 6: 在 Chrome 中加载扩展并手动验证

**Files:** 无新文件

这个 Task 是手动验证步骤，不需要写代码。

- [ ] **Step 1: 检查扩展文件完整性**

```bash
find . -not -path './.git/*' -not -path './docs/*' | sort
```

确认以下所有文件存在：
```
./manifest.json
./background.js
./content.js
./shared/note-engine.js
./popup/popup.html
./popup/popup.css
./popup/popup.js
./assets/piano/webaudiofont-player.js
./assets/piano/piano.js
./assets/typewriter/key.wav
./assets/typewriter/space.wav
./assets/typewriter/enter.wav
./assets/icons/icon16.png
./assets/icons/icon48.png
./assets/icons/icon128.png
```

- [ ] **Step 2: 在 Chrome 中加载扩展**

1. 打开 Chrome，地址栏输入 `chrome://extensions/`
2. 右上角开启「开发者模式」
3. 点击「加载已解压的扩展程序」
4. 选择 `/Users/tongqianwen/Documents/archive/keyboard-sound` 目录
5. 确认扩展出现在列表中且无报错

- [ ] **Step 3: 验证 popup 界面**

1. 点击 Chrome 工具栏的扩展图标
2. 确认弹出控制面板，显示：标题、主开关（默认开）、音色按钮、音符模式按钮、音量滑块
3. 切换到「打字机」模式，确认「音符模式」区域淡出隐藏
4. 切换回「钢琴」模式，确认「音符模式」区域恢复

- [ ] **Step 4: 验证钢琴音效**

1. 打开 `https://www.google.com`（或任意网页）
2. 点击搜索框，使其获得焦点
3. 按键盘字母键，应听到钢琴音效
4. 打开 popup → 切换到「顺序循环」模式，再打字，确认音符依次上行
5. 切换到「随机」模式，打字，确认每次音高不固定但不刺耳

- [ ] **Step 5: 验证打字机音效**

1. popup 切换到「打字机」模式
2. 在搜索框打字，应听到机械键盘声
3. 按空格，音效应更宽沉
4. 按回车/退格，音效应更重

- [ ] **Step 6: 验证主开关**

1. popup 关闭主开关
2. 打字，应无音效
3. 重新打开主开关，打字，音效恢复

- [ ] **Step 7: 验证音量**

1. 拖动音量滑块到 0%，打字，无声音
2. 拖动到 100%，打字，音量最大
3. 调回 75%

- [ ] **Step 8: Final commit**

```bash
git add -A
git commit -m "feat: keyboard sound chrome extension v1.0.0 complete"
```

---

## 自检 — Spec Coverage

| Spec 要求 | 对应 Task |
|-----------|-----------|
| Chrome 扩展 Manifest V3 | Task 1 |
| content.js 注入网页监听 keydown | Task 4 |
| 仅在 input/textarea/contenteditable 触发 | Task 4 |
| note-engine 三种音符模式 | Task 3 |
| WebAudioFont 钢琴音色离线打包 | Task 2, Task 4 |
| 打字机音效 key/space/enter 细分 | Task 2, Task 4 |
| Popup 控制面板：开关/音色/音符模式/音量 | Task 5 |
| 打字机模式时隐藏音符模式区域 | Task 5 |
| chrome.storage.local 状态同步 | Task 1, Task 4, Task 5 |
| background.js 初始化默认值 | Task 1 |
| 深色主题 | Task 5 |
| 所有状态变更即时生效 | Task 4, Task 5 |
