# 坐姿检测微信小程序 实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 构建一个基于微信 VisionKit 的坐姿检测小程序，实时提醒用户调整坐姿、按时休息，并通过勋章体系激励良好习惯。

**Architecture:** 服务层分离——PostureService 封装 VisionKit、SessionStore 管理计时与勋章、AlertService 控制提醒策略；四个页面仅负责 UI 渲染，不含业务逻辑；所有数据读写通过 `storage.js` 适配器，预留云同步接口。

**Tech Stack:** 微信小程序原生（WXML / WXSS / JS）、微信 VisionKit humanBody 2D 追踪（基础库 ≥ 2.20.0）、wx.createInnerAudioContext、Canvas 2D API、Jest（服务层单元测试）

**Spec:** `docs/superpowers/specs/2026-06-16-posture-miniprogram-design.md`

---

## 文件结构总览

```
sit/
├── miniprogram/                     ← 小程序根目录
│   ├── app.js
│   ├── app.json                     ← TabBar、页面注册、权限声明
│   ├── app.wxss                     ← 全局样式（字体、颜色变量）
│   ├── project.config.json
│   ├── assets/
│   │   └── audio/
│   │       ├── posture_bad.mp3      ← 「请调整坐姿，抬头挺胸」
│   │       ├── lying_down.mp3       ← 「请不要趴着，小心眼睛近视」
│   │       ├── take_break.mp3       ← 「已持续坐了 X 分钟，站起来活动一下吧」
│   │       ├── badge_earned.mp3     ← 「恭喜解锁勋章」（通用）
│   │       └── posture_good.mp3     ← 「很好，继续保持」
│   ├── pages/
│   │   ├── monitor/   index.{js,wxml,wxss,json}
│   │   ├── stats/     index.{js,wxml,wxss,json}
│   │   ├── badges/    index.{js,wxml,wxss,json}
│   │   └── settings/  index.{js,wxml,wxss,json}
│   ├── services/
│   │   ├── PostureService.js        ← VisionKit 封装 + 判姿算法
│   │   ├── SessionStore.js          ← 计时状态机 + 勋章触发
│   │   └── AlertService.js          ← 语音/震动/静音策略 + 防抖
│   └── utils/
│       ├── constants.js             ← 阈值、关键点索引、勋章定义
│       └── storage.js               ← wx.setStorage 适配器
└── tests/                           ← Jest 单元测试（纯 JS 逻辑）
    ├── package.json
    ├── jest.config.js
    ├── __mocks__/
    │   └── wx.js                    ← wx API mock
    ├── utils/
    │   └── storage.test.js
    └── services/
        ├── PostureService.test.js
        ├── SessionStore.test.js
        └── AlertService.test.js
```

---

## Task 1：项目脚手架

**Files:**
- Create: `miniprogram/app.json`
- Create: `miniprogram/app.js`
- Create: `miniprogram/app.wxss`
- Create: `miniprogram/project.config.json`
- Create: `miniprogram/pages/monitor/index.{js,wxml,wxss,json}`（空壳）
- Create: `miniprogram/pages/stats/index.{js,wxml,wxss,json}`（空壳）
- Create: `miniprogram/pages/badges/index.{js,wxml,wxss,json}`（空壳）
- Create: `miniprogram/pages/settings/index.{js,wxml,wxss,json}`（空壳）

- [ ] **Step 1: 安装微信开发者工具**

  下载并安装 [微信开发者工具](https://developers.weixin.qq.com/miniprogram/dev/devtools/download.html)。
  在工具中新建项目：
  - 目录选 `sit/miniprogram`
  - 不使用云开发
  - 基础模板（空项目）

  > 完成后 `miniprogram/` 目录会生成基础文件，后续步骤替换其内容。

- [ ] **Step 2: 写 `app.json`**

  ```json
  {
    "pages": [
      "pages/monitor/index",
      "pages/stats/index",
      "pages/badges/index",
      "pages/settings/index"
    ],
    "window": {
      "backgroundTextStyle": "light",
      "navigationBarBackgroundColor": "#1a1a2e",
      "navigationBarTitleText": "坐姿卫士",
      "navigationBarTextStyle": "white"
    },
    "tabBar": {
      "color": "#86868b",
      "selectedColor": "#0a84ff",
      "backgroundColor": "#ffffff",
      "list": [
        { "pagePath": "pages/monitor/index", "text": "检测", "iconPath": "assets/icons/monitor.png", "selectedIconPath": "assets/icons/monitor-active.png" },
        { "pagePath": "pages/stats/index",   "text": "统计", "iconPath": "assets/icons/stats.png",   "selectedIconPath": "assets/icons/stats-active.png" },
        { "pagePath": "pages/badges/index",  "text": "勋章", "iconPath": "assets/icons/badges.png",  "selectedIconPath": "assets/icons/badges-active.png" },
        { "pagePath": "pages/settings/index","text": "设置", "iconPath": "assets/icons/settings.png","selectedIconPath": "assets/icons/settings-active.png" }
      ]
    },
    "permission": {
      "scope.camera": { "desc": "坐姿检测需要使用摄像头" }
    },
    "requiredPrivateInfos": ["chooseAddress"],
    "sitemapLocation": "sitemap.json",
    "lazyCodeLoading": "requiredComponents",
    "__usePrivacyCheck__": true
  }
  ```

  > **注意：** TabBar 图标需要自备 PNG 文件（40×40px）放在 `assets/icons/`。开发阶段可用任意占位图。

- [ ] **Step 3: 写 `app.js`**

  ```js
  // miniprogram/app.js
  App({
    onLaunch() {
      // 初始化默认设置（首次安装时写入）
      const { storage } = require('./utils/storage')
      storage.get('settings').then(s => {
        if (!s) {
          storage.set('settings', {
            alertMode:           'voice',
            sensitivity:         'normal',
            sittingLimitMins:    45,
            hunchAlertDelaySecs: 3,
          })
        }
      })
    },
  })
  ```

- [ ] **Step 4: 写 `app.wxss`**（全局颜色变量）

  ```css
  /* miniprogram/app.wxss */
  page {
    --color-good:    #34c759;
    --color-hunch:   #ff9f0a;
    --color-lying:   #ff3b30;
    --color-accent:  #0a84ff;
    --color-bg:      #f5f5f7;
    --color-surface: #ffffff;
    --color-label:   #86868b;
    font-family: -apple-system, system-ui, sans-serif;
    background: var(--color-bg);
  }
  ```

- [ ] **Step 5: 创建四个页面空壳**

  每个页面的 `index.json` 内容：
  ```json
  { "usingComponents": {} }
  ```

  每个页面的 `index.js` 内容（以 monitor 为例，其余同）：
  ```js
  Page({ data: {} })
  ```

  每个页面的 `index.wxml` 内容（以 monitor 为例）：
  ```xml
  <view>monitor 页面占位</view>
  ```

- [ ] **Step 6: 在微信开发者工具中编译，确认 TabBar 四个 Tab 可点击切换**

  预期：底部 TabBar 显示四个 Tab，切换正常，无报错。

- [ ] **Step 7: 提交**

  ```bash
  cd /Users/tongqianwen/ExpProjects/learn/jupyter/sit
  git add miniprogram/
  git commit -m "feat: 小程序项目脚手架（TabBar + 页面空壳）"
  ```

---

## Task 2：`utils/constants.js`

**Files:**
- Create: `miniprogram/utils/constants.js`

- [ ] **Step 1: 写 `constants.js`**

  ```js
  // miniprogram/utils/constants.js

  // ── 判姿阈值（头肩距离，归一化 [0,1]）────────────────────────
  // VisionKit 坐标已归一化，与 check_posture.py 逻辑一致
  export const HUNCH_THRESHOLD = {
    loose:  0.12,
    normal: 0.18,
    strict: 0.24,
  }

  // ── VisionKit humanBody 关键点索引 ────────────────────────────
  // ⚠️  微信 VisionKit humanBody 2D 模式返回 14 个关键点，顺序如下。
  //    开发时请在 DevTools 打印 anchor.points 确认实际顺序，
  //    与官方文档 https://developers.weixin.qq.com/miniprogram/dev/api/ai/visionkit/ 核对。
  export const KP = {
    HEAD:        0,  // 头顶（或鼻子，视版本而定）
    NECK:        1,
    L_SHOULDER:  2,
    R_SHOULDER:  3,
    L_ELBOW:     4,
    R_ELBOW:     5,
    L_WRIST:     6,
    R_WRIST:     7,
    L_HIP:       8,
    R_HIP:       9,
    L_KNEE:      10,
    R_KNEE:      11,
    L_ANKLE:     12,
    R_ANKLE:     13,
  }

  // ── 骨架连接线（用于 Canvas 绘制）────────────────────────────
  export const SKELETON_CONNECTIONS = [
    [KP.HEAD,       KP.NECK],
    [KP.NECK,       KP.L_SHOULDER],
    [KP.NECK,       KP.R_SHOULDER],
    [KP.L_SHOULDER, KP.R_SHOULDER],
    [KP.L_SHOULDER, KP.L_HIP],
    [KP.R_SHOULDER, KP.R_HIP],
    [KP.L_HIP,      KP.R_HIP],
  ]

  // ── 告警防抖（秒）────────────────────────────────────────────
  export const ALERT_COOLDOWN_SECS = {
    posture_bad: 30,
    lying_down:  30,
    posture_good: 60,
  }

  // ── 用户离场判定（连续检测不到人体的秒数）──────────────────
  export const ABSENT_PAUSE_SECS = 10

  // ── 勋章定义 ─────────────────────────────────────────────────
  export const BADGE_DEFS = [
    {
      id:          'first_session',
      name:        '初次体验',
      icon:        '🎯',
      description: '完成第一次检测（≥ 1 分钟）',
    },
    {
      id:          'first_break',
      name:        '第一次休息',
      icon:        '☕',
      description: '坐满 45 分钟后站起来活动',
    },
    {
      id:          'good_30min',
      name:        '坚持 30 分钟',
      icon:        '⏱',
      description: '单次连续端正坐姿 ≥ 30 分钟',
    },
    {
      id:          'good_10h',
      name:        '坚持 10 小时',
      icon:        '🏆',
      description: '累计端正坐姿 ≥ 10 小时',
    },
    {
      id:          'eye_protector',
      name:        '护眼卫士',
      icon:        '👁',
      description: '连续 7 个有效使用日趴着时长均 < 10 分钟',
    },
    {
      id:          'rest_10',
      name:        '劳逸达人',
      icon:        '💪',
      description: '累计主动休息 10 次',
    },
    {
      id:          'perfect_day',
      name:        '姿势大师',
      icon:        '🥋',
      description: '单日弓腰 + 趴着总时长 < 5 分钟',
    },
    {
      id:          'early_bird',
      name:        '早起护脊',
      icon:        '🌅',
      description: '早上 8 点前完成一次检测（≥ 1 分钟）',
    },
  ]
  ```

- [ ] **Step 2: 提交**

  ```bash
  git add miniprogram/utils/constants.js
  git commit -m "feat: utils/constants.js — 阈值、关键点索引、勋章定义"
  ```

---

## Task 3：`utils/storage.js` + 单元测试

**Files:**
- Create: `miniprogram/utils/storage.js`
- Create: `tests/package.json`
- Create: `tests/jest.config.js`
- Create: `tests/__mocks__/wx.js`
- Create: `tests/utils/storage.test.js`

- [ ] **Step 1: 初始化测试环境**

  ```bash
  mkdir -p tests/__mocks__ tests/utils tests/services
  cd tests
  npm init -y
  npm install --save-dev jest
  ```

- [ ] **Step 2: 写 `tests/jest.config.js`**

  ```js
  // tests/jest.config.js
  module.exports = {
    testEnvironment: 'node',
    moduleNameMapper: {
      '^wx$': '<rootDir>/__mocks__/wx.js',
    },
    // 让 tests/ 里的文件可以 require('../miniprogram/...')
    modulePaths: ['<rootDir>/..'],
  }
  ```

- [ ] **Step 3: 写 `tests/__mocks__/wx.js`**

  ```js
  // tests/__mocks__/wx.js
  const store = {}

  const wx = {
    getStorageSync: jest.fn((key) => store[key] ?? null),
    setStorageSync: jest.fn((key, val) => { store[key] = val }),
    getStorage: jest.fn(({ key, success, fail }) => {
      try { success({ data: store[key] ?? null }) } catch(e) { fail && fail(e) }
    }),
    setStorage: jest.fn(({ key, data, success, fail }) => {
      try { store[key] = data; success && success() } catch(e) { fail && fail(e) }
    }),
    vibrateShort:  jest.fn(),
    vibrateLong:   jest.fn(),
    createInnerAudioContext: jest.fn(() => ({
      src:        '',
      play:       jest.fn(),
      stop:       jest.fn(),
      destroy:    jest.fn(),
    })),
    createVKSession: jest.fn(),
    // 测试间重置 store
    __resetStore: () => Object.keys(store).forEach(k => delete store[k]),
  }

  global.wx = wx
  module.exports = wx
  ```

- [ ] **Step 4: 写 `miniprogram/utils/storage.js`**

  ```js
  // miniprogram/utils/storage.js

  /**
   * 数据层适配器。
   * 当前实现：wx.setStorage（本地）。
   * 切换云同步时只改此文件，接口不变。
   */
  export const storage = {
    /** @returns {Promise<any>} */
    get(key) {
      return new Promise((resolve, reject) => {
        wx.getStorage({ key, success: res => resolve(res.data), fail: reject })
      })
    },

    /** @returns {Promise<void>} */
    set(key, value) {
      return new Promise((resolve, reject) => {
        wx.setStorage({ key, data: value, success: resolve, fail: reject })
      })
    },

    /**
     * 追加或更新 sessions 数组中的当日记录。
     * @param {object} dayRecord  必须包含 { date: 'YYYY-MM-DD' }
     * @returns {Promise<void>}
     */
    async append(dayRecord) {
      const sessions = (await this.get('sessions')) || []
      const idx = sessions.findIndex(s => s.date === dayRecord.date)
      if (idx >= 0) {
        sessions[idx] = { ...sessions[idx], ...dayRecord }
      } else {
        sessions.push(dayRecord)
      }
      // 只保留最近 90 天
      const trimmed = sessions.slice(-90)
      return this.set('sessions', trimmed)
    },
  }
  ```

- [ ] **Step 5: 写 `tests/utils/storage.test.js`**

  ```js
  // tests/utils/storage.test.js
  const wxMock = require('../__mocks__/wx')
  // 设置 global.wx 供 storage.js 使用
  global.wx = wxMock

  // Jest 模块解析需要 .js 后缀或 package.json 配置
  const { storage } = require('../miniprogram/utils/storage')

  beforeEach(() => wxMock.__resetStore())

  describe('storage.get / storage.set', () => {
    test('set 后 get 取回相同值', async () => {
      await storage.set('testKey', { foo: 42 })
      const val = await storage.get('testKey')
      expect(val).toEqual({ foo: 42 })
    })

    test('get 不存在的 key 返回 null', async () => {
      const val = await storage.get('nonexistent')
      expect(val).toBeNull()
    })
  })

  describe('storage.append', () => {
    const today = '2026-06-16'

    test('首次 append 新增记录', async () => {
      await storage.append({ date: today, goodSecs: 100 })
      const sessions = await storage.get('sessions')
      expect(sessions).toHaveLength(1)
      expect(sessions[0]).toMatchObject({ date: today, goodSecs: 100 })
    })

    test('同日 append 合并而非重复插入', async () => {
      await storage.append({ date: today, goodSecs: 100 })
      await storage.append({ date: today, goodSecs: 200, hunchSecs: 10 })
      const sessions = await storage.get('sessions')
      expect(sessions).toHaveLength(1)
      expect(sessions[0]).toMatchObject({ goodSecs: 200, hunchSecs: 10 })
    })

    test('超过 90 条时截断到最近 90 条', async () => {
      const existing = Array.from({ length: 90 }, (_, i) => ({
        date: `2025-01-${String(i + 1).padStart(2, '0')}`,
        goodSecs: i,
      }))
      await storage.set('sessions', existing)
      await storage.append({ date: '2026-06-16', goodSecs: 999 })
      const sessions = await storage.get('sessions')
      expect(sessions).toHaveLength(90)
      expect(sessions[sessions.length - 1].goodSecs).toBe(999)
    })
  })
  ```

- [ ] **Step 6: 运行测试，确认通过**

  ```bash
  cd tests && npx jest utils/storage.test.js --verbose
  ```

  预期输出：
  ```
  PASS utils/storage.test.js
    storage.get / storage.set
      ✓ set 后 get 取回相同值
      ✓ get 不存在的 key 返回 null
    storage.append
      ✓ 首次 append 新增记录
      ✓ 同日 append 合并而非重复插入
      ✓ 超过 90 条时截断到最近 90 条
  Tests: 5 passed
  ```

- [ ] **Step 7: 提交**

  ```bash
  cd /Users/tongqianwen/ExpProjects/learn/jupyter/sit
  git add miniprogram/utils/storage.js tests/
  git commit -m "feat: storage.js 适配器 + Jest 测试环境 + 5 个测试通过"
  ```

---

## Task 4：`PostureService.js` — 判姿算法 + 单元测试

**Files:**
- Create: `miniprogram/services/PostureService.js`
- Create: `tests/services/PostureService.test.js`

- [ ] **Step 1: 写 `PostureService.js`**

  ```js
  // miniprogram/services/PostureService.js
  import { HUNCH_THRESHOLD, KP, SKELETON_CONNECTIONS, ABSENT_PAUSE_SECS } from '../utils/constants'

  /**
   * PostureService
   * 封装 VisionKit humanBody 会话，对外暴露坐姿状态流。
   *
   * 用法：
   *   PostureService.start()
   *   PostureService.onPostureChange(({ type, keypoints }) => { ... })
   *   PostureService.stop()
   */
  const PostureService = {
    _session:        null,
    _listeners:      [],
    _lastType:       null,
    _absentTimer:    null,
    _absentSeconds:  0,
    _sensitivity:    'normal',

    /** 设置灵敏度，必须在 start() 前调用 */
    setSensitivity(sensitivity) {
      this._sensitivity = sensitivity
    },

    /** 注册坐姿变更监听器 */
    onPostureChange(callback) {
      this._listeners.push(callback)
    },

    /** 移除所有监听器 */
    offPostureChange() {
      this._listeners = []
    },

    /** 启动 VisionKit 会话 */
    start() {
      if (this._session) return

      this._session = wx.createVKSession({
        track: { humanBody: { mode: 1 } },   // 2D 人体姿态追踪
      })

      this._session.start((err) => {
        if (err) {
          console.error('[PostureService] VKSession start error:', err)
          this._emit({ type: 'error', error: err })
        }
      })

      this._session.on('updateAnchors', (anchors) => {
        if (!anchors || anchors.length === 0) {
          this._handleAbsent()
          return
        }
        this._absentSeconds = 0
        clearTimeout(this._absentTimer)
        this._absentTimer = null

        const anchor = anchors[0]
        const points = anchor.points || []

        const type = analyzePosture(points, HUNCH_THRESHOLD[this._sensitivity])
        if (type !== this._lastType) {
          this._lastType = type
          this._emit({ type, keypoints: points })
        }
      })
    },

    /** 停止会话，释放摄像头 */
    stop() {
      if (this._session) {
        this._session.stop()
        this._session = null
      }
      this._lastType = null
      this._absentSeconds = 0
      clearTimeout(this._absentTimer)
      this._absentTimer = null
    },

    _emit(event) {
      this._listeners.forEach(fn => fn(event))
    },

    _handleAbsent() {
      // 连续检测不到人体 ABSENT_PAUSE_SECS 秒 → 发出 absent 事件
      if (!this._absentTimer) {
        this._absentTimer = setTimeout(() => {
          this._lastType = 'absent'
          this._emit({ type: 'absent', keypoints: [] })
          this._absentTimer = null
        }, ABSENT_PAUSE_SECS * 1000)
      }
    },
  }

  /**
   * 纯函数：根据关键点判断坐姿类型。
   * 独立导出，便于单元测试。
   *
   * @param {Array<{x:number, y:number, score:number}>} points 归一化坐标 [0,1]
   * @param {number} threshold 弓腰判定阈值
   * @returns {'good'|'hunching'|'lying'|'unknown'}
   */
  export function analyzePosture(points, threshold) {
    const MIN_SCORE = 0.5
    const head  = points[KP.HEAD]
    const lSh   = points[KP.L_SHOULDER]
    const rSh   = points[KP.R_SHOULDER]

    if (!head || !lSh || !rSh) return 'unknown'
    if (head.score < MIN_SCORE || lSh.score < MIN_SCORE || rSh.score < MIN_SCORE) {
      return 'unknown'
    }

    const shMidY = (lSh.y + rSh.y) / 2
    const dist   = shMidY - head.y   // 正值 = 头在肩上方

    if (head.y > shMidY)      return 'lying'     // 趴着：头低于肩中点
    if (dist < threshold)     return 'hunching'  // 弓腰：头肩距不足
    return 'good'
  }

  export default PostureService
  ```

- [ ] **Step 2: 写 `tests/services/PostureService.test.js`**

  ```js
  // tests/services/PostureService.test.js
  // 只测 analyzePosture 纯函数，不需要 wx mock
  const { analyzePosture } = require('../miniprogram/services/PostureService')

  // 工具：构造关键点数组
  function makePoints(headY, lShY, rShY, score = 0.9) {
    // 14 个点，只有 HEAD(0), L_SHOULDER(2), R_SHOULDER(3) 需要真实值
    const pts = Array(14).fill(null).map(() => ({ x: 0.5, y: 0.5, score: 0.9 }))
    pts[0] = { x: 0.5, y: headY,  score }
    pts[2] = { x: 0.4, y: lShY,   score }
    pts[3] = { x: 0.6, y: rShY,   score }
    return pts
  }

  const THRESHOLD = 0.18  // normal 档

  describe('analyzePosture', () => {
    test('端正坐姿：头比肩高出足够距离', () => {
      // shMidY = 0.5, headY = 0.25 → dist = 0.25 > 0.18
      const pts = makePoints(0.25, 0.5, 0.5)
      expect(analyzePosture(pts, THRESHOLD)).toBe('good')
    })

    test('弓腰：头肩距小于阈值', () => {
      // shMidY = 0.5, headY = 0.4 → dist = 0.1 < 0.18
      const pts = makePoints(0.40, 0.5, 0.5)
      expect(analyzePosture(pts, THRESHOLD)).toBe('hunching')
    })

    test('趴着：鼻子低于肩中点', () => {
      // headY = 0.7 > shMidY = 0.5
      const pts = makePoints(0.70, 0.5, 0.5)
      expect(analyzePosture(pts, THRESHOLD)).toBe('lying')
    })

    test('置信度不足返回 unknown', () => {
      const pts = makePoints(0.25, 0.5, 0.5, 0.3)  // score < 0.5
      expect(analyzePosture(pts, THRESHOLD)).toBe('unknown')
    })

    test('关键点缺失返回 unknown', () => {
      expect(analyzePosture([], THRESHOLD)).toBe('unknown')
    })

    test('宽松阈值（0.12）下同样的弓腰姿势判为 good', () => {
      // dist = 0.15，宽松阈值 0.12 → good
      const pts = makePoints(0.35, 0.5, 0.5)
      expect(analyzePosture(pts, 0.12)).toBe('good')
    })

    test('严格阈值（0.24）下中等距离判为 hunching', () => {
      // dist = 0.20，严格阈值 0.24 → hunching
      const pts = makePoints(0.30, 0.5, 0.5)
      expect(analyzePosture(pts, 0.24)).toBe('hunching')
    })
  })
  ```

- [ ] **Step 3: 运行测试**

  ```bash
  cd tests && npx jest services/PostureService.test.js --verbose
  ```

  预期：7 个测试全部 PASS

- [ ] **Step 4: 提交**

  ```bash
  cd /Users/tongqianwen/ExpProjects/learn/jupyter/sit
  git add miniprogram/services/PostureService.js tests/services/PostureService.test.js
  git commit -m "feat: PostureService.js + analyzePosture 算法 + 7 个测试通过"
  ```

---

## Task 5：`SessionStore.js` + 单元测试

**Files:**
- Create: `miniprogram/services/SessionStore.js`
- Create: `tests/services/SessionStore.test.js`

- [ ] **Step 1: 写 `SessionStore.js`**

  ```js
  // miniprogram/services/SessionStore.js
  import { ABSENT_PAUSE_SECS, BADGE_DEFS } from '../utils/constants'
  import { storage } from '../utils/storage'

  /**
   * SessionStore
   * 管理当次检测会话的计时状态，触发休息提醒和勋章检查。
   *
   * 用法：
   *   SessionStore.init(settings)
   *   SessionStore.setPostureType('good')   // 由 PostureService 回调驱动
   *   SessionStore.onEvent(callback)        // 监听 break_due / badge_earned 事件
   *   SessionStore.stop()
   */
  const SessionStore = {
    // ── 配置 ──────────────────────────────────────────────────
    sittingLimitSecs:    45 * 60,
    hunchAlertDelaySecs: 3,

    // ── 状态 ──────────────────────────────────────────────────
    _goodSecs:       0,
    _hunchSecs:      0,
    _lyingSecs:      0,
    _sittingSecs:    0,   // goodSecs + hunchSecs + lyingSecs（累计坐着）
    _breaksTaken:    0,
    _currentStreak:  0,   // 当前连续端正秒数
    _bestStreak:     0,   // 本日最长连续端正秒数
    _currentType:    'unknown',
    _hunchContSecs:  0,   // 连续弓腰秒数
    _lyingContSecs:  0,   // 连续趴着秒数
    _absentSecs:     0,   // 连续缺席秒数（暂停计时）
    _paused:         false,
    _ticker:         null,
    _persistCounter: 0,
    _listeners:      [],
    _earnedIds:      new Set(),
    _today:          '',

    /** 初始化，传入 settings 对象 */
    async init(settings = {}) {
      this.sittingLimitSecs    = (settings.sittingLimitMins || 45) * 60
      this.hunchAlertDelaySecs = settings.hunchAlertDelaySecs || 3
      this._today = todayStr()

      // 加载已解锁勋章
      const badges = (await storage.get('badges')) || []
      this._earnedIds = new Set(badges.map(b => b.id))
    },

    onEvent(callback) {
      this._listeners.push(callback)
    },

    offEvent() {
      this._listeners = []
    },

    /** 由 PostureService.onPostureChange 驱动，每次坐姿变化时调用 */
    setPostureType(type) {
      this._currentType = type
      if (type !== 'absent') {
        this._paused = false
      }
    },

    /** 启动 1 秒 tick */
    start() {
      if (this._ticker) return
      this._ticker = setInterval(() => this._tick(), 1000)
    },

    /** 停止 tick，持久化最终数据 */
    async stop() {
      clearInterval(this._ticker)
      this._ticker = null
      await this._persist()
    },

    /** 用户确认休息（点击休息遮罩按钮后调用）*/
    confirmBreak() {
      this._sittingSecs = 0
      this._breaksTaken++
      this._checkMilestone('first_break')
      this._checkMilestone('rest_10')
    },

    // ── 内部 ──────────────────────────────────────────────────

    _tick() {
      const type = this._currentType

      if (type === 'absent' || type === 'unknown') {
        this._hunchContSecs = 0
        this._lyingContSecs = 0
        this._currentStreak = 0
        return  // 检测不到人，暂停计时
      }

      if (type === 'good') {
        this._goodSecs++
        this._sittingSecs++
        this._currentStreak++
        if (this._currentStreak > this._bestStreak) this._bestStreak = this._currentStreak
        this._hunchContSecs = 0
        this._lyingContSecs = 0
        this._checkMilestone('good_30min')
        this._checkMilestone('good_10h')
        this._checkMilestone('early_bird')
      } else if (type === 'hunching') {
        this._hunchSecs++
        this._sittingSecs++
        this._hunchContSecs++
        this._currentStreak = 0
        if (this._hunchContSecs === this.hunchAlertDelaySecs) {
          this._emit({ event: 'alert', alertType: 'posture_bad' })
        }
      } else if (type === 'lying') {
        this._lyingSecs++
        this._sittingSecs++
        this._lyingContSecs++
        this._currentStreak = 0
        if (this._lyingContSecs === 5) {
          this._emit({ event: 'alert', alertType: 'lying_down' })
        }
      }

      // 坐满休息提醒
      if (this._sittingSecs > 0 && this._sittingSecs % this.sittingLimitSecs === 0) {
        this._emit({ event: 'break_due', sittingMins: Math.round(this._sittingSecs / 60) })
      }

      // 每 60 秒持久化一次
      this._persistCounter++
      if (this._persistCounter >= 60) {
        this._persistCounter = 0
        this._persist()
      }

      this._checkMilestone('first_session')
    },

    _emit(payload) {
      this._listeners.forEach(fn => fn(payload))
    },

    async _checkMilestone(id) {
      if (this._earnedIds.has(id)) return

      let earned = false
      const totalGoodSecs = await this._totalGoodSecs()

      switch (id) {
        case 'first_session':
          earned = (this._goodSecs + this._hunchSecs + this._lyingSecs) >= 60
          break
        case 'first_break':
          earned = this._breaksTaken >= 1
          break
        case 'good_30min':
          earned = this._bestStreak >= 30 * 60
          break
        case 'good_10h':
          earned = totalGoodSecs >= 10 * 3600
          break
        case 'rest_10':
          earned = this._breaksTaken >= 10
          break
        case 'early_bird':
          earned = (new Date().getHours() < 8) && (this._goodSecs + this._hunchSecs + this._lyingSecs) >= 60
          break
        case 'perfect_day':
          // 在 stop() 后由外部调用检查当日数据，此处不做实时检查
          break
        case 'eye_protector':
          // 连续7个有效使用日趴着时长 < 10 分钟，在每日结束时检查
          break
      }

      if (earned) {
        this._earnedIds.add(id)
        const badges = (await storage.get('badges')) || []
        badges.push({ id, earnedAt: Date.now() })
        await storage.set('badges', badges)
        const def = BADGE_DEFS.find(b => b.id === id)
        this._emit({ event: 'badge_earned', badge: def })
      }
    },

    async _totalGoodSecs() {
      const sessions = (await storage.get('sessions')) || []
      return sessions.reduce((sum, s) => sum + (s.goodSecs || 0), 0) + this._goodSecs
    },

    async _persist() {
      const date = this._today
      await storage.append({
        date,
        goodSecs:          this._goodSecs,
        hunchSecs:         this._hunchSecs,
        lyingSecs:         this._lyingSecs,
        breaksTaken:       this._breaksTaken,
        longestGoodStreak: this._bestStreak,
      })
    },
  }

  function todayStr() {
    const d = new Date()
    return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2,'0')}-${String(d.getDate()).padStart(2,'0')}`
  }

  export default SessionStore
  ```

- [ ] **Step 2: 写 `tests/services/SessionStore.test.js`**

  ```js
  // tests/services/SessionStore.test.js
  const wxMock = require('../__mocks__/wx')
  global.wx = wxMock

  // Jest fake timers
  jest.useFakeTimers()

  const SessionStore = require('../miniprogram/services/SessionStore').default

  beforeEach(async () => {
    wxMock.__resetStore()
    // 重置 SessionStore 内部状态
    Object.assign(SessionStore, {
      _goodSecs: 0, _hunchSecs: 0, _lyingSecs: 0,
      _sittingSecs: 0, _breaksTaken: 0,
      _currentStreak: 0, _bestStreak: 0,
      _hunchContSecs: 0, _lyingContSecs: 0,
      _currentType: 'unknown', _ticker: null,
      _persistCounter: 0, _listeners: [], _earnedIds: new Set(),
    })
    await SessionStore.init({ sittingLimitMins: 45, hunchAlertDelaySecs: 3 })
  })

  afterEach(() => {
    clearInterval(SessionStore._ticker)
    SessionStore._ticker = null
    jest.clearAllTimers()
  })

  describe('基础计时', () => {
    test('good 姿势每 tick 增加 goodSecs', () => {
      SessionStore.setPostureType('good')
      SessionStore._tick()
      SessionStore._tick()
      expect(SessionStore._goodSecs).toBe(2)
      expect(SessionStore._sittingSecs).toBe(2)
    })

    test('hunching 姿势每 tick 增加 hunchSecs', () => {
      SessionStore.setPostureType('hunching')
      SessionStore._tick()
      expect(SessionStore._hunchSecs).toBe(1)
    })

    test('absent 时不计时', () => {
      SessionStore.setPostureType('absent')
      SessionStore._tick()
      SessionStore._tick()
      expect(SessionStore._goodSecs).toBe(0)
      expect(SessionStore._sittingSecs).toBe(0)
    })
  })

  describe('提醒触发', () => {
    test('连续弓腰 3 秒后发出 posture_bad 事件', () => {
      const events = []
      SessionStore.onEvent(e => events.push(e))
      SessionStore.setPostureType('hunching')
      SessionStore._tick(); SessionStore._tick(); SessionStore._tick()
      expect(events).toContainEqual({ event: 'alert', alertType: 'posture_bad' })
    })

    test('连续趴着 5 秒后发出 lying_down 事件', () => {
      const events = []
      SessionStore.onEvent(e => events.push(e))
      SessionStore.setPostureType('lying')
      for (let i = 0; i < 5; i++) SessionStore._tick()
      expect(events).toContainEqual({ event: 'alert', alertType: 'lying_down' })
    })

    test('坐满 sittingLimitSecs 后发出 break_due 事件', () => {
      const events = []
      SessionStore.onEvent(e => events.push(e))
      SessionStore.sittingLimitSecs = 3   // 测试用：3 秒触发
      SessionStore.setPostureType('good')
      for (let i = 0; i < 3; i++) SessionStore._tick()
      expect(events.some(e => e.event === 'break_due')).toBe(true)
    })
  })

  describe('勋章里程碑', () => {
    test('检测满 60 秒后解锁 first_session', async () => {
      const events = []
      SessionStore.onEvent(e => events.push(e))
      SessionStore.setPostureType('good')
      for (let i = 0; i < 60; i++) await SessionStore._tick()
      // 等待 _checkMilestone 的 async 完成
      await Promise.resolve()
      expect(events.some(e => e.event === 'badge_earned' && e.badge.id === 'first_session')).toBe(true)
    })

    test('confirmBreak 后解锁 first_break', async () => {
      const events = []
      SessionStore.onEvent(e => events.push(e))
      SessionStore.confirmBreak()
      await Promise.resolve()
      expect(events.some(e => e.event === 'badge_earned' && e.badge.id === 'first_break')).toBe(true)
    })
  })
  ```

- [ ] **Step 3: 运行测试**

  ```bash
  cd tests && npx jest services/SessionStore.test.js --verbose
  ```

  预期：8 个测试全部 PASS

- [ ] **Step 4: 提交**

  ```bash
  cd /Users/tongqianwen/ExpProjects/learn/jupyter/sit
  git add miniprogram/services/SessionStore.js tests/services/SessionStore.test.js
  git commit -m "feat: SessionStore.js 计时状态机 + 8 个测试通过"
  ```

---

## Task 6：`AlertService.js` + 单元测试

**Files:**
- Create: `miniprogram/services/AlertService.js`
- Create: `tests/services/AlertService.test.js`

- [ ] **Step 1: 写 `AlertService.js`**

  ```js
  // miniprogram/services/AlertService.js
  import { ALERT_COOLDOWN_SECS } from '../utils/constants'

  const AUDIO_FILES = {
    posture_bad:  '/assets/audio/posture_bad.mp3',
    lying_down:   '/assets/audio/lying_down.mp3',
    take_break:   '/assets/audio/take_break.mp3',
    badge_earned: '/assets/audio/badge_earned.mp3',
    posture_good: '/assets/audio/posture_good.mp3',
  }

  const AlertService = {
    _mode:         'voice',      // 'voice' | 'vibration' | 'silent'
    _lastAlertAt:  {},           // { alertType: timestamp }
    _audioCtx:     null,

    setMode(mode) {
      this._mode = mode
    },

    /** 触发提醒。alertType 对应 AUDIO_FILES 的 key */
    fire(alertType) {
      if (this._mode === 'silent') return

      // 防抖检查
      const cooldown = (ALERT_COOLDOWN_SECS[alertType] || 0) * 1000
      const now = Date.now()
      if (cooldown > 0 && this._lastAlertAt[alertType] && now - this._lastAlertAt[alertType] < cooldown) {
        return
      }
      this._lastAlertAt[alertType] = now

      if (this._mode === 'voice') {
        this._playAudio(alertType)
      } else if (this._mode === 'vibration') {
        this._vibrate(alertType)
      }
    },

    _playAudio(alertType) {
      if (!AUDIO_FILES[alertType]) return
      if (!this._audioCtx) {
        this._audioCtx = wx.createInnerAudioContext()
      }
      this._audioCtx.stop()
      this._audioCtx.src = AUDIO_FILES[alertType]
      this._audioCtx.play()
    },

    _vibrate(alertType) {
      if (alertType === 'take_break') {
        wx.vibrateLong()
      } else {
        wx.vibrateShort()
        setTimeout(() => wx.vibrateShort(), 300)
      }
    },

    /** 测试间重置（仅测试使用）*/
    _reset() {
      this._mode = 'voice'
      this._lastAlertAt = {}
      this._audioCtx = null
    },
  }

  export default AlertService
  ```

- [ ] **Step 2: 写 `tests/services/AlertService.test.js`**

  ```js
  // tests/services/AlertService.test.js
  const wxMock = require('../__mocks__/wx')
  global.wx = wxMock

  jest.useFakeTimers()

  const AlertService = require('../miniprogram/services/AlertService').default

  const mockAudio = { src: '', play: jest.fn(), stop: jest.fn(), destroy: jest.fn() }
  wxMock.createInnerAudioContext.mockReturnValue(mockAudio)

  beforeEach(() => {
    AlertService._reset()
    jest.clearAllMocks()
    mockAudio.play.mockClear()
    mockAudio.stop.mockClear()
    wxMock.vibrateShort.mockClear()
    wxMock.vibrateLong.mockClear()
  })

  describe('voice 模式', () => {
    test('fire(posture_bad) 播放对应音频', () => {
      AlertService.setMode('voice')
      AlertService.fire('posture_bad')
      expect(mockAudio.src).toBe('/assets/audio/posture_bad.mp3')
      expect(mockAudio.play).toHaveBeenCalledTimes(1)
    })

    test('防抖：30 秒内同类型提醒只播放一次', () => {
      AlertService.setMode('voice')
      AlertService.fire('posture_bad')
      AlertService.fire('posture_bad')   // 立即第二次，应被拦截
      expect(mockAudio.play).toHaveBeenCalledTimes(1)
    })

    test('防抖过期后可再次播放', () => {
      AlertService.setMode('voice')
      AlertService.fire('posture_bad')
      // 模拟 31 秒过去
      AlertService._lastAlertAt['posture_bad'] -= 31 * 1000
      AlertService.fire('posture_bad')
      expect(mockAudio.play).toHaveBeenCalledTimes(2)
    })
  })

  describe('vibration 模式', () => {
    test('fire(posture_bad) 调用 vibrateShort', () => {
      AlertService.setMode('vibration')
      AlertService.fire('posture_bad')
      expect(wxMock.vibrateShort).toHaveBeenCalled()
    })

    test('fire(take_break) 调用 vibrateLong', () => {
      AlertService.setMode('vibration')
      AlertService.fire('take_break')
      expect(wxMock.vibrateLong).toHaveBeenCalledTimes(1)
    })
  })

  describe('silent 模式', () => {
    test('fire 不触发任何 wx 调用', () => {
      AlertService.setMode('silent')
      AlertService.fire('posture_bad')
      expect(mockAudio.play).not.toHaveBeenCalled()
      expect(wxMock.vibrateShort).not.toHaveBeenCalled()
    })
  })
  ```

- [ ] **Step 3: 运行测试**

  ```bash
  cd tests && npx jest services/AlertService.test.js --verbose
  ```

  预期：7 个测试全部 PASS

- [ ] **Step 4: 所有服务层测试一次性跑通**

  ```bash
  cd tests && npx jest --verbose
  ```

  预期：20 个测试全部 PASS（5 + 7 + 8 + 7 - 分 3 个文件）

- [ ] **Step 5: 提交**

  ```bash
  cd /Users/tongqianwen/ExpProjects/learn/jupyter/sit
  git add miniprogram/services/AlertService.js tests/services/AlertService.test.js
  git commit -m "feat: AlertService.js 提醒策略 + 7 个测试通过，服务层 20 测试全绿"
  ```

---

## Task 7：monitor 页面 — WXML / WXSS 骨架

**Files:**
- Modify: `miniprogram/pages/monitor/index.wxml`
- Modify: `miniprogram/pages/monitor/index.wxss`

- [ ] **Step 1: 写 `pages/monitor/index.wxml`**

  ```xml
  <!-- miniprogram/pages/monitor/index.wxml -->
  <view class="container">

    <!-- 坐姿状态卡片 -->
    <view class="status-card status-{{postureType}}">
      <text class="status-icon">{{statusIcon}}</text>
      <text class="status-text">{{statusText}}</text>
      <text class="status-timer">已坚持 {{streakTime}}</text>
    </view>

    <!-- VisionKit Canvas 预览 -->
    <view class="canvas-wrap">
      <canvas type="2d" id="vk-canvas" class="vk-canvas"
              bindtouchstart="" />
      <view wx:if="{{!detecting}}" class="canvas-placeholder">
        <text>📷 点击「开始检测」启动摄像头</text>
      </view>
    </view>

    <!-- 今日数据栏 -->
    <view class="stats-row">
      <view class="stat-item">
        <text class="stat-value good">{{todayGoodTime}}</text>
        <text class="stat-label">今日端正</text>
      </view>
      <view class="stat-item">
        <text class="stat-value bad">{{todayBadTime}}</text>
        <text class="stat-label">弓腰/趴着</text>
      </view>
    </view>

    <!-- 45 分钟进度条 -->
    <view class="break-progress">
      <view class="progress-header">
        <text class="progress-label">距下次休息</text>
        <text class="progress-value">{{breakCountdown}}</text>
      </view>
      <view class="progress-bar-bg">
        <view class="progress-bar-fill" style="width:{{breakProgress}}%" />
      </view>
    </view>

    <!-- 开始 / 停止按钮 -->
    <view class="btn-detect {{detecting ? 'btn-stop' : 'btn-start'}}"
          bindtap="onToggleDetect">
      <text>{{detecting ? '⏹ 停止检测' : '▶️ 开始检测'}}</text>
    </view>

  </view>

  <!-- 休息遮罩 -->
  <view wx:if="{{showBreakOverlay}}" class="break-overlay">
    <view class="break-modal">
      <text class="break-emoji">🧘</text>
      <text class="break-title">该休息了！</text>
      <text class="break-desc">已持续坐了 {{sittingMins}} 分钟\n站起来活动一下吧 🚶</text>
      <view class="break-btn" bindtap="onConfirmBreak">好的，我去活动</view>
    </view>
  </view>

  <!-- 勋章解锁弹出 -->
  <view wx:if="{{newBadge}}" class="badge-popup" bindtap="onDismissBadge">
    <text class="badge-popup-icon">{{newBadge.icon}}</text>
    <text class="badge-popup-name">解锁勋章：{{newBadge.name}}</text>
    <text class="badge-popup-hint">点击关闭</text>
  </view>
  ```

- [ ] **Step 2: 写 `pages/monitor/index.wxss`**

  ```css
  /* miniprogram/pages/monitor/index.wxss */
  .container {
    display: flex;
    flex-direction: column;
    padding: 16rpx 24rpx;
    gap: 16rpx;
    min-height: 100vh;
    background: var(--color-bg);
  }

  /* ── 状态卡片 ── */
  .status-card {
    border-radius: 16rpx;
    padding: 24rpx;
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 8rpx;
    border: 4rpx solid transparent;
    transition: border-color 0.3s;
  }
  .status-good    { background: #e8f7ee; border-color: var(--color-good); }
  .status-hunching { background: #fff8ec; border-color: var(--color-hunch); }
  .status-lying   { background: #fef0ee; border-color: var(--color-lying); }
  .status-unknown { background: #f0f0f0; border-color: #ccc; }
  .status-absent  { background: #f0f0f0; border-color: #ccc; }

  .status-icon { font-size: 48rpx; }
  .status-text { font-size: 36rpx; font-weight: 700; }
  .status-good    .status-text { color: #1a7a3a; }
  .status-hunching .status-text { color: #b06000; }
  .status-lying   .status-text { color: #c0281a; }
  .status-timer { font-size: 24rpx; color: var(--color-label); }

  /* ── Canvas ── */
  .canvas-wrap {
    position: relative;
    width: 100%;
    aspect-ratio: 4/3;
    background: #1a1a2e;
    border-radius: 16rpx;
    overflow: hidden;
  }
  .vk-canvas { width: 100%; height: 100%; }
  .canvas-placeholder {
    position: absolute; inset: 0;
    display: flex; align-items: center; justify-content: center;
  }
  .canvas-placeholder text { color: #aaa; font-size: 28rpx; }

  /* ── 数据栏 ── */
  .stats-row {
    display: flex; gap: 16rpx;
  }
  .stat-item {
    flex: 1; background: var(--color-surface);
    border-radius: 12rpx; padding: 16rpx;
    display: flex; flex-direction: column; align-items: center; gap: 6rpx;
  }
  .stat-value { font-size: 36rpx; font-weight: 700; }
  .stat-value.good { color: var(--color-good); }
  .stat-value.bad  { color: var(--color-hunch); }
  .stat-label { font-size: 22rpx; color: var(--color-label); }

  /* ── 进度条 ── */
  .break-progress { background: var(--color-surface); border-radius: 12rpx; padding: 16rpx; }
  .progress-header { display: flex; justify-content: space-between; margin-bottom: 12rpx; }
  .progress-label { font-size: 24rpx; color: var(--color-label); }
  .progress-value { font-size: 24rpx; font-weight: 600; }
  .progress-bar-bg { background: #e5e5e7; border-radius: 6rpx; height: 12rpx; }
  .progress-bar-fill { background: var(--color-accent); border-radius: 6rpx; height: 12rpx; transition: width 1s linear; }

  /* ── 按钮 ── */
  .btn-detect {
    border-radius: 16rpx; padding: 28rpx;
    text-align: center; font-size: 32rpx; font-weight: 600; color: #fff;
  }
  .btn-start { background: var(--color-accent); }
  .btn-stop  { background: var(--color-lying); }

  /* ── 休息遮罩 ── */
  .break-overlay {
    position: fixed; inset: 0;
    background: rgba(0,60,160,0.7);
    display: flex; align-items: center; justify-content: center;
    z-index: 100;
  }
  .break-modal {
    background: #fff; border-radius: 24rpx; padding: 48rpx 40rpx;
    display: flex; flex-direction: column; align-items: center; gap: 16rpx;
    width: 80%;
  }
  .break-emoji { font-size: 72rpx; }
  .break-title { font-size: 40rpx; font-weight: 700; }
  .break-desc  { font-size: 28rpx; color: var(--color-label); text-align: center; white-space: pre-line; }
  .break-btn   { margin-top: 16rpx; background: var(--color-accent); color: #fff; border-radius: 12rpx; padding: 20rpx 48rpx; font-size: 30rpx; font-weight: 600; }

  /* ── 勋章弹出 ── */
  .badge-popup {
    position: fixed; bottom: 120rpx; left: 50%; transform: translateX(-50%);
    background: rgba(0,0,0,0.85); border-radius: 16rpx; padding: 24rpx 40rpx;
    display: flex; flex-direction: column; align-items: center; gap: 8rpx;
    z-index: 101;
  }
  .badge-popup-icon { font-size: 48rpx; }
  .badge-popup-name { color: #ffd700; font-size: 28rpx; font-weight: 700; }
  .badge-popup-hint { color: #aaa; font-size: 22rpx; }
  ```

- [ ] **Step 3: 在微信开发者工具中预览 monitor 页面**

  预期：页面显示占位状态卡片、深色 Canvas 区、数据栏、进度条、「开始检测」按钮，无报错。

- [ ] **Step 4: 提交**

  ```bash
  git add miniprogram/pages/monitor/
  git commit -m "feat: monitor 页面 WXML/WXSS 骨架"
  ```

---

## Task 8：monitor 页面 — JS 逻辑（接入三个 Service）

**Files:**
- Modify: `miniprogram/pages/monitor/index.js`

- [ ] **Step 1: 写 `pages/monitor/index.js`**

  ```js
  // miniprogram/pages/monitor/index.js
  import PostureService from '../../services/PostureService'
  import SessionStore   from '../../services/SessionStore'
  import AlertService   from '../../services/AlertService'
  import { storage }    from '../../utils/storage'

  // ── 辅助：秒 → "MM:SS" ──────────────────────────────────
  function fmtTime(secs) {
    const m = Math.floor(secs / 60)
    const s = secs % 60
    return `${String(m).padStart(2,'0')}:${String(s).padStart(2,'0')}`
  }

  const STATUS_MAP = {
    good:     { icon: '🧍', text: '端正坐姿' },
    hunching: { icon: '😕', text: '注意弓腰！' },
    lying:    { icon: '😟', text: '别趴着！' },
    absent:   { icon: '👻', text: '未检测到人' },
    unknown:  { icon: '👤', text: '正在识别…' },
  }

  Page({
    data: {
      detecting:       false,
      postureType:     'unknown',
      statusIcon:      '👤',
      statusText:      '点击开始检测',
      streakTime:      '00:00',
      todayGoodTime:   '00:00',
      todayBadTime:    '00:00',
      breakCountdown:  '--:--',
      breakProgress:   0,
      showBreakOverlay: false,
      sittingMins:     0,
      newBadge:        null,
    },

    _tickTimer: null,
    _settings:  null,

    // ── 生命周期 ──────────────────────────────────────────
    async onLoad() {
      this._settings = (await storage.get('settings')) || {
        alertMode: 'voice', sensitivity: 'normal',
        sittingLimitMins: 45, hunchAlertDelaySecs: 3,
      }
      AlertService.setMode(this._settings.alertMode)
      PostureService.setSensitivity(this._settings.sensitivity)
      await SessionStore.init(this._settings)
    },

    onUnload() {
      this._stopDetecting()
    },

    onHide() {
      this._stopDetecting()
    },

    // ── 用户操作 ──────────────────────────────────────────
    onToggleDetect() {
      if (this.data.detecting) {
        this._stopDetecting()
      } else {
        this._startDetecting()
      }
    },

    onConfirmBreak() {
      SessionStore.confirmBreak()
      this.setData({ showBreakOverlay: false })
    },

    onDismissBadge() {
      this.setData({ newBadge: null })
    },

    // ── 检测启停 ──────────────────────────────────────────
    _startDetecting() {
      wx.authorize({ scope: 'scope.camera',
        success: () => {
          this.setData({ detecting: true })
          this._initCanvas()
          this._bindServices()
          SessionStore.start()
          PostureService.start()
          this._tickTimer = setInterval(() => this._updateUI(), 1000)
        },
        fail: () => {
          wx.showModal({
            title: '需要摄像头权限',
            content: '坐姿检测需要使用摄像头，请在设置中开启',
            confirmText: '去设置',
            success: (res) => { if (res.confirm) wx.openSetting() },
          })
        },
      })
    },

    async _stopDetecting() {
      PostureService.stop()
      PostureService.offPostureChange()
      SessionStore.offEvent()
      clearInterval(this._tickTimer)
      await SessionStore.stop()
      this.setData({ detecting: false, postureType: 'unknown',
        statusIcon: '👤', statusText: '点击开始检测', streakTime: '00:00' })
    },

    // ── Service 事件绑定 ──────────────────────────────────
    _bindServices() {
      PostureService.onPostureChange(({ type }) => {
        SessionStore.setPostureType(type)
        const m = STATUS_MAP[type] || STATUS_MAP.unknown
        this.setData({ postureType: type, statusIcon: m.icon, statusText: m.text })
      })

      SessionStore.onEvent((payload) => {
        if (payload.event === 'alert') {
          AlertService.fire(payload.alertType)
        } else if (payload.event === 'break_due') {
          AlertService.fire('take_break')
          this.setData({ showBreakOverlay: true, sittingMins: payload.sittingMins })
        } else if (payload.event === 'badge_earned') {
          AlertService.fire('badge_earned')
          this.setData({ newBadge: payload.badge })
          setTimeout(() => this.setData({ newBadge: null }), 4000)
        }
      })
    },

    // ── 每秒更新 UI 数字 ──────────────────────────────────
    _updateUI() {
      const s = SessionStore
      const sittingLimit = (this._settings?.sittingLimitMins || 45) * 60
      const progress = Math.min(100, Math.round(s._sittingSecs / sittingLimit * 100))
      const remaining = Math.max(0, sittingLimit - s._sittingSecs)

      this.setData({
        streakTime:     fmtTime(s._currentStreak),
        todayGoodTime:  fmtTime(s._goodSecs),
        todayBadTime:   fmtTime(s._hunchSecs + s._lyingSecs),
        breakProgress:  progress,
        breakCountdown: fmtTime(remaining),
      })
    },

    // ── Canvas 初始化 + 骨架绘制 ─────────────────────────
    _initCanvas() {
      wx.createSelectorQuery().select('#vk-canvas').fields({ node: true, size: true })
        .exec(([res]) => {
          if (!res) return
          const canvas = res.node
          const ctx    = canvas.getContext('2d')
          canvas.width  = res.width
          canvas.height = res.height
          this._canvas = canvas
          this._ctx    = ctx
          this._canvasW = res.width
          this._canvasH = res.height
          // 将 canvas 传给 VKSession 用于摄像头渲染
          PostureService._session && PostureService._session.canvas && PostureService._session.canvas(canvas)
          this._startSkeleton()
        })
    },

    _startSkeleton() {
      const { SKELETON_CONNECTIONS } = require('../../utils/constants')
      if (!PostureService._session) return

      PostureService._session.on('updateAnchors', (anchors) => {
        const ctx = this._ctx
        if (!ctx) return
        ctx.clearRect(0, 0, this._canvasW, this._canvasH)
        if (!anchors || anchors.length === 0) return

        const pts = anchors[0].points
        if (!pts) return

        // 骨架连接线
        ctx.strokeStyle = 'rgba(78,205,196,0.8)'
        ctx.lineWidth   = 2
        SKELETON_CONNECTIONS.forEach(([a, b]) => {
          if (!pts[a] || !pts[b]) return
          ctx.beginPath()
          ctx.moveTo(pts[a].x * this._canvasW, pts[a].y * this._canvasH)
          ctx.lineTo(pts[b].x * this._canvasW, pts[b].y * this._canvasH)
          ctx.stroke()
        })

        // 关键点圆点
        ctx.fillStyle = 'rgba(50,150,255,0.9)'
        pts.forEach(pt => {
          if (!pt || pt.score < 0.4) return
          ctx.beginPath()
          ctx.arc(pt.x * this._canvasW, pt.y * this._canvasH, 4, 0, Math.PI * 2)
          ctx.fill()
        })
      })
    },
  })
  ```

- [ ] **Step 2: 在微信开发者工具中真机预览（或模拟器 + 摄像头）**

  验证：
  - 点击「开始检测」后请求摄像头权限
  - Canvas 区显示摄像头画面 + 骨架叠加
  - 状态卡片随坐姿变化颜色
  - 数据栏计时器每秒递增
  - 调整坐姿到弓腰位置，约 3 秒后触发语音提醒

- [ ] **Step 3: 提交**

  ```bash
  git add miniprogram/pages/monitor/index.js
  git commit -m "feat: monitor 页面 JS — 接入 PostureService / SessionStore / AlertService"
  ```

---

## Task 9：stats 页面

**Files:**
- Modify: `miniprogram/pages/stats/index.{js,wxml,wxss}`

- [ ] **Step 1: 写 `pages/stats/index.wxml`**

  ```xml
  <!-- miniprogram/pages/stats/index.wxml -->
  <view class="container">
    <!-- Tab 切换 -->
    <view class="tab-bar">
      <view class="tab {{tab==='today'?'tab-active':''}}" bindtap="switchTab" data-tab="today">今日</view>
      <view class="tab {{tab==='week'?'tab-active':''}}"  bindtap="switchTab" data-tab="week">本周</view>
    </view>

    <!-- 环形图 + 图例 -->
    <view class="ring-wrap">
      <canvas type="2d" id="ring-canvas" class="ring-canvas" />
      <view class="ring-legend">
        <view class="legend-item"><text class="dot good" />端正 {{goodTime}}</view>
        <view class="legend-item"><text class="dot hunch" />弓腰 {{hunchTime}}</view>
        <view class="legend-item"><text class="dot lying" />趴着 {{lyingTime}}</view>
      </view>
    </view>

    <!-- 柱状图 -->
    <view class="bar-section">
      <text class="section-title">近 7 天端正坐姿（分钟）</text>
      <canvas type="2d" id="bar-canvas" class="bar-canvas" />
    </view>

    <!-- 数字摘要 -->
    <view class="summary-row">
      <view class="summary-item">
        <text class="summary-val">{{totalGoodH}}</text>
        <text class="summary-label">今日端正（小时）</text>
      </view>
      <view class="summary-item">
        <text class="summary-val">{{bestStreakMin}}</text>
        <text class="summary-label">最长连续（分钟）</text>
      </view>
      <view class="summary-item">
        <text class="summary-val">{{breaksTaken}}</text>
        <text class="summary-label">今日休息次数</text>
      </view>
    </view>
  </view>
  ```

- [ ] **Step 2: 写 `pages/stats/index.js`**

  ```js
  // miniprogram/pages/stats/index.js
  import { storage } from '../../utils/storage'

  function todayStr() {
    const d = new Date()
    return `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}-${String(d.getDate()).padStart(2,'0')}`
  }

  function fmtHours(secs) { return (secs / 3600).toFixed(1) }
  function fmtMins(secs)  { return String(Math.round(secs / 60)) }
  function fmtMMSS(secs)  {
    const m = Math.floor(secs / 60), s = secs % 60
    return `${String(m).padStart(2,'0')}:${String(s).padStart(2,'0')}`
  }

  Page({
    data: {
      tab: 'today',
      goodTime: '00:00', hunchTime: '00:00', lyingTime: '00:00',
      totalGoodH: '0.0', bestStreakMin: '0', breaksTaken: '0',
    },

    async onShow() {
      await this._loadData()
      this._drawRing()
      this._drawBar()
    },

    switchTab(e) {
      this.setData({ tab: e.currentTarget.dataset.tab })
      this._loadData().then(() => { this._drawRing(); this._drawBar() })
    },

    async _loadData() {
      const sessions = (await storage.get('sessions')) || []
      const today    = todayStr()

      if (this.data.tab === 'today') {
        const day = sessions.find(s => s.date === today) || {}
        this.setData({
          goodTime:     fmtMMSS(day.goodSecs  || 0),
          hunchTime:    fmtMMSS(day.hunchSecs || 0),
          lyingTime:    fmtMMSS(day.lyingSecs || 0),
          totalGoodH:   fmtHours(day.goodSecs || 0),
          bestStreakMin: fmtMins(day.longestGoodStreak || 0),
          breaksTaken:  String(day.breaksTaken || 0),
        })
        this._ringData = [day.goodSecs||0, day.hunchSecs||0, day.lyingSecs||0]
        this._barData  = sessions.slice(-7).map(s => Math.round((s.goodSecs||0)/60))
      } else {
        // 本周：最近 7 天汇总
        const week = sessions.slice(-7)
        const g = week.reduce((a,s) => a + (s.goodSecs||0), 0)
        const h = week.reduce((a,s) => a + (s.hunchSecs||0), 0)
        const l = week.reduce((a,s) => a + (s.lyingSecs||0), 0)
        this.setData({
          goodTime:  fmtMMSS(g), hunchTime: fmtMMSS(h), lyingTime: fmtMMSS(l),
          totalGoodH: fmtHours(g),
          bestStreakMin: fmtMins(Math.max(...week.map(s=>s.longestGoodStreak||0))),
          breaksTaken: String(week.reduce((a,s)=>a+(s.breaksTaken||0),0)),
        })
        this._ringData = [g, h, l]
        this._barData  = week.map(s => Math.round((s.goodSecs||0)/60))
      }
    },

    _drawRing() {
      wx.createSelectorQuery().select('#ring-canvas').fields({ node:true, size:true }).exec(([r]) => {
        if (!r) return
        const canvas = r.node, ctx = canvas.getContext('2d')
        canvas.width = r.width; canvas.height = r.height
        const W = r.width, H = r.height, cx = W/2, cy = H/2, radius = Math.min(W,H)*0.4

        const [good, hunch, lying] = this._ringData || [0,0,0]
        const total = good + hunch + lying || 1
        const colors = ['#34c759','#ff9f0a','#ff3b30']
        const vals   = [good, hunch, lying]

        ctx.clearRect(0,0,W,H)
        let start = -Math.PI / 2
        vals.forEach((v, i) => {
          const angle = (v / total) * Math.PI * 2
          ctx.beginPath()
          ctx.moveTo(cx, cy)
          ctx.arc(cx, cy, radius, start, start + angle)
          ctx.fillStyle = colors[i]
          ctx.fill()
          start += angle
        })
        // 中心白圆（环形效果）
        ctx.beginPath()
        ctx.arc(cx, cy, radius * 0.6, 0, Math.PI * 2)
        ctx.fillStyle = '#fff'
        ctx.fill()
      })
    },

    _drawBar() {
      wx.createSelectorQuery().select('#bar-canvas').fields({ node:true, size:true }).exec(([r]) => {
        if (!r) return
        const canvas = r.node, ctx = canvas.getContext('2d')
        canvas.width = r.width; canvas.height = r.height
        const W = r.width, H = r.height
        const data = this._barData || []
        const maxVal = Math.max(...data, 1)
        const barW = W / (data.length * 1.5)
        const gap  = barW * 0.5

        ctx.clearRect(0,0,W,H)
        data.forEach((v, i) => {
          const barH = (v / maxVal) * (H - 30)
          const x = i * (barW + gap) + gap
          ctx.fillStyle = i === data.length - 1 ? '#0a84ff' : '#34c759'
          ctx.fillRect(x, H - barH - 20, barW, barH)
        })
      })
    },
  })
  ```

- [ ] **Step 3: 写 `pages/stats/index.wxss`**（精简版）

  ```css
  /* miniprogram/pages/stats/index.wxss */
  .container { padding: 24rpx; display:flex; flex-direction:column; gap:24rpx; }
  .tab-bar { display:flex; background:#e5e5e7; border-radius:12rpx; }
  .tab { flex:1; text-align:center; padding:16rpx; font-size:28rpx; color:#86868b; border-radius:10rpx; }
  .tab-active { background:#fff; color:#0a84ff; font-weight:600; box-shadow:0 1rpx 4rpx rgba(0,0,0,.1); }
  .ring-wrap { display:flex; align-items:center; gap:24rpx; background:#fff; border-radius:16rpx; padding:24rpx; }
  .ring-canvas { width:200rpx; height:200rpx; }
  .ring-legend { display:flex; flex-direction:column; gap:12rpx; }
  .legend-item { display:flex; align-items:center; gap:8rpx; font-size:26rpx; }
  .dot { width:16rpx; height:16rpx; border-radius:50%; display:inline-block; }
  .dot.good { background:#34c759; } .dot.hunch { background:#ff9f0a; } .dot.lying { background:#ff3b30; }
  .bar-section { background:#fff; border-radius:16rpx; padding:24rpx; }
  .section-title { font-size:26rpx; color:#86868b; display:block; margin-bottom:16rpx; }
  .bar-canvas { width:100%; height:200rpx; }
  .summary-row { display:flex; gap:16rpx; }
  .summary-item { flex:1; background:#fff; border-radius:12rpx; padding:20rpx; text-align:center; }
  .summary-val { font-size:40rpx; font-weight:700; color:#0a84ff; display:block; }
  .summary-label { font-size:22rpx; color:#86868b; }
  ```

- [ ] **Step 4: 在微信开发者工具预览，确认环形图和柱状图渲染正常**

- [ ] **Step 5: 提交**

  ```bash
  git add miniprogram/pages/stats/
  git commit -m "feat: stats 页面 — 环形图 + 柱状图 + 数字摘要"
  ```

---

## Task 10：badges 页面

**Files:**
- Modify: `miniprogram/pages/badges/index.{js,wxml,wxss}`

- [ ] **Step 1: 写 `pages/badges/index.wxml`**

  ```xml
  <!-- miniprogram/pages/badges/index.wxml -->
  <view class="container">
    <view class="header">
      <text class="progress-text">已获得 {{earned}} / {{total}} 枚</text>
    </view>
    <view class="grid">
      <view wx:for="{{badges}}" wx:key="id"
            class="badge-card {{item.earned ? 'badge-earned' : 'badge-locked'}}">
        <text class="badge-icon">{{item.icon}}</text>
        <text class="badge-name">{{item.name}}</text>
        <text class="badge-date" wx:if="{{item.earned}}">{{item.dateStr}}</text>
        <text class="badge-desc" wx:if="{{!item.earned}}">{{item.description}}</text>
      </view>
    </view>
  </view>
  ```

- [ ] **Step 2: 写 `pages/badges/index.js`**

  ```js
  // miniprogram/pages/badges/index.js
  import { storage } from '../../utils/storage'
  import { BADGE_DEFS } from '../../utils/constants'

  Page({
    data: { badges: [], earned: 0, total: BADGE_DEFS.length },

    async onShow() {
      const earnedArr = (await storage.get('badges')) || []
      const earnedMap = new Map(earnedArr.map(b => [b.id, b.earnedAt]))

      const badges = BADGE_DEFS.map(def => {
        const at = earnedMap.get(def.id)
        const d  = at ? new Date(at) : null
        return {
          ...def,
          earned:  !!at,
          dateStr: d ? `${d.getMonth()+1}月${d.getDate()}日 获得` : '',
        }
      })

      this.setData({ badges, earned: earnedArr.length })
    },
  })
  ```

- [ ] **Step 3: 写 `pages/badges/index.wxss`**

  ```css
  /* miniprogram/pages/badges/index.wxss */
  .container { padding:24rpx; }
  .header { text-align:center; margin-bottom:24rpx; }
  .progress-text { font-size:28rpx; color:#86868b; }
  .grid { display:grid; grid-template-columns:1fr 1fr; gap:16rpx; }
  .badge-card { border-radius:16rpx; padding:24rpx; display:flex; flex-direction:column; align-items:center; gap:8rpx; }
  .badge-earned { background:#fdf6e3; border:3rpx solid #ff9f0a; }
  .badge-locked  { background:#f0f0f0; border:3rpx solid #ddd; opacity:0.55; }
  .badge-icon { font-size:56rpx; }
  .badge-name { font-size:26rpx; font-weight:700; text-align:center; }
  .badge-earned .badge-name { color:#b06000; }
  .badge-date { font-size:22rpx; color:#b06000; opacity:.8; }
  .badge-desc { font-size:22rpx; color:#86868b; text-align:center; line-height:1.4; }
  ```

- [ ] **Step 4: 提交**

  ```bash
  git add miniprogram/pages/badges/
  git commit -m "feat: badges 页面 — 勋章网格（已解锁/未解锁）"
  ```

---

## Task 11：settings 页面

**Files:**
- Modify: `miniprogram/pages/settings/index.{js,wxml,wxss}`

- [ ] **Step 1: 写 `pages/settings/index.wxml`**

  ```xml
  <!-- miniprogram/pages/settings/index.wxml -->
  <view class="container">

    <view class="section">
      <text class="section-label">提醒方式</text>
      <view class="segment">
        <view class="seg-item {{alertMode==='voice'?'seg-active':''}}"     bindtap="setAlertMode" data-val="voice">🔊 语音</view>
        <view class="seg-item {{alertMode==='vibration'?'seg-active':''}}" bindtap="setAlertMode" data-val="vibration">📳 震动</view>
        <view class="seg-item {{alertMode==='silent'?'seg-active':''}}"    bindtap="setAlertMode" data-val="silent">🔇 静音</view>
      </view>
    </view>

    <view class="section">
      <text class="section-label">检测灵敏度</text>
      <view class="segment">
        <view class="seg-item {{sensitivity==='loose'?'seg-active':''}}"  bindtap="setSensitivity" data-val="loose">宽松</view>
        <view class="seg-item {{sensitivity==='normal'?'seg-active':''}}" bindtap="setSensitivity" data-val="normal">标准</view>
        <view class="seg-item {{sensitivity==='strict'?'seg-active':''}}" bindtap="setSensitivity" data-val="strict">严格</view>
      </view>
    </view>

    <view class="section">
      <text class="section-label">坐满提醒（分钟）</text>
      <view class="stepper">
        <view class="step-btn" bindtap="decSittingLimit">−</view>
        <text class="step-val">{{sittingLimitMins}}</text>
        <view class="step-btn" bindtap="incSittingLimit">+</view>
      </view>
    </view>

    <view class="section">
      <text class="section-label">连续弓腰提醒（秒）</text>
      <view class="stepper">
        <view class="step-btn" bindtap="decHunchDelay">−</view>
        <text class="step-val">{{hunchAlertDelaySecs}}</text>
        <view class="step-btn" bindtap="incHunchDelay">+</view>
      </view>
    </view>

  </view>
  ```

- [ ] **Step 2: 写 `pages/settings/index.js`**

  ```js
  // miniprogram/pages/settings/index.js
  import { storage } from '../../utils/storage'

  Page({
    data: {
      alertMode:           'voice',
      sensitivity:         'normal',
      sittingLimitMins:    45,
      hunchAlertDelaySecs: 3,
    },

    async onLoad() {
      const s = (await storage.get('settings')) || {}
      this.setData({
        alertMode:           s.alertMode           || 'voice',
        sensitivity:         s.sensitivity         || 'normal',
        sittingLimitMins:    s.sittingLimitMins    || 45,
        hunchAlertDelaySecs: s.hunchAlertDelaySecs || 3,
      })
    },

    async _save() {
      await storage.set('settings', {
        alertMode:           this.data.alertMode,
        sensitivity:         this.data.sensitivity,
        sittingLimitMins:    this.data.sittingLimitMins,
        hunchAlertDelaySecs: this.data.hunchAlertDelaySecs,
      })
    },

    setAlertMode(e)   { this.setData({ alertMode: e.currentTarget.dataset.val });   this._save() },
    setSensitivity(e) { this.setData({ sensitivity: e.currentTarget.dataset.val }); this._save() },

    incSittingLimit() { if (this.data.sittingLimitMins < 90) { this.setData({ sittingLimitMins: this.data.sittingLimitMins + 5 }); this._save() } },
    decSittingLimit() { if (this.data.sittingLimitMins > 20) { this.setData({ sittingLimitMins: this.data.sittingLimitMins - 5 }); this._save() } },

    incHunchDelay()   { if (this.data.hunchAlertDelaySecs < 10) { this.setData({ hunchAlertDelaySecs: this.data.hunchAlertDelaySecs + 1 }); this._save() } },
    decHunchDelay()   { if (this.data.hunchAlertDelaySecs > 1)  { this.setData({ hunchAlertDelaySecs: this.data.hunchAlertDelaySecs - 1 }); this._save() } },
  })
  ```

- [ ] **Step 3: 写 `pages/settings/index.wxss`**

  ```css
  /* miniprogram/pages/settings/index.wxss */
  .container { padding:24rpx; display:flex; flex-direction:column; gap:24rpx; }
  .section { background:#fff; border-radius:16rpx; padding:24rpx; }
  .section-label { font-size:26rpx; font-weight:600; color:#86868b; text-transform:uppercase; letter-spacing:1rpx; display:block; margin-bottom:16rpx; }
  .segment { display:flex; background:#e5e5e7; border-radius:12rpx; }
  .seg-item { flex:1; text-align:center; padding:16rpx; font-size:28rpx; color:#86868b; border-radius:10rpx; }
  .seg-active { background:#fff; color:#0a84ff; font-weight:600; box-shadow:0 1rpx 4rpx rgba(0,0,0,.12); }
  .stepper { display:flex; align-items:center; justify-content:center; gap:40rpx; }
  .step-btn { width:72rpx; height:72rpx; border-radius:50%; background:#e5e5e7; display:flex; align-items:center; justify-content:center; font-size:40rpx; color:#333; }
  .step-val { font-size:56rpx; font-weight:700; min-width:80rpx; text-align:center; }
  ```

- [ ] **Step 4: 提交**

  ```bash
  git add miniprogram/pages/settings/
  git commit -m "feat: settings 页面 — 提醒方式 / 灵敏度 / 步进器"
  ```

---

## Task 12：音频资源 + 最终集成验证

**Files:**
- Create: `miniprogram/assets/audio/*.mp3`

- [ ] **Step 1: 获取音频文件**

  选择以下任一方式：

  **方式 A（推荐，快速）：** 使用微信小程序内置 TTS（文字转语音）动态生成，无需 mp3 文件。
  修改 `AlertService._playAudio`：

  ```js
  // 将 AlertService._playAudio 替换为以下内容
  _playAudio(alertType) {
    const texts = {
      posture_bad:  '请调整坐姿，抬头挺胸',
      lying_down:   '请不要趴着，小心眼睛近视',
      take_break:   '已持续坐了很久，站起来活动一下吧',
      badge_earned: '恭喜你，解锁了新勋章',
      posture_good: '很好，继续保持',
    }
    const text = texts[alertType]
    if (!text) return
    if (!this._audioCtx) this._audioCtx = wx.createInnerAudioContext()
    // wx.textToSpeech 是微信 AI 开放接口，需在 app.json 中申请
    wx.textToSpeech({
      lang: 'zh_CN', speed: 1.0, volume: 1.0, text,
      success: (res) => {
        this._audioCtx.stop()
        this._audioCtx.src = res.filename
        this._audioCtx.play()
      },
    })
  },
  ```

  **方式 B（离线）：** 录制或从免费音频网站（如 freesound.org、讯飞开放平台 TTS 下载）获取 5 个 mp3，放到 `miniprogram/assets/audio/`。

- [ ] **Step 2: 在 `app.json` 中声明 TTS 权限（如使用方式 A）**

  ```json
  // 在 app.json 的 "permission" 中追加：
  "scope.record": { "desc": "语音提醒需要录音权限" }
  ```

  > 实际上 `wx.textToSpeech` 不需要录音权限，但建议在小程序后台「开发 → 接口设置」中确认 AI 语音合成权限已开启。

- [ ] **Step 3: 端到端冒烟测试（微信开发者工具 + 真机）**

  按以下步骤逐一验证：

  1. **启动**：打开小程序 → monitor 页 → 点击「开始检测」→ 同意摄像头权限
  2. **正常坐姿**：保持端正 → 状态卡片显示绿色「端正坐姿」→ 计时器递增
  3. **弓腰测试**：身体前倾 3 秒 → 状态变橙色 → 语音播报「请调整坐姿」
  4. **趴着测试**：低头 5 秒 → 状态变红 → 语音播报「请不要趴着」
  5. **休息提醒**：临时将 `sittingLimitMins` 设为 1，等 1 分钟 → 弹出蓝色遮罩 → 点击确认 → 计时重置
  6. **勋章解锁**：检测满 1 分钟 → 底部弹出「初次体验」勋章 → badges 页出现金色卡片
  7. **设置生效**：进入 settings 页 → 切换为震动模式 → 回到 monitor → 弓腰 3 秒 → 手机震动
  8. **统计展示**：进入 stats 页 → 环形图 + 柱状图显示今日数据

- [ ] **Step 4: 最终提交**

  ```bash
  git add miniprogram/assets/ miniprogram/services/AlertService.js
  git commit -m "feat: 音频资源 + 完成端到端冒烟测试"
  ```

---

## 自查：Spec 覆盖确认

| Spec 需求 | 覆盖任务 |
|-----------|---------|
| 实时坐姿检测（端正/弓腰/趴着） | Task 4 analyzePosture + Task 8 |
| 姿势变差时提醒 | Task 6 AlertService + Task 8 SessionStore 事件 |
| 端正/弓腰/趴着计时统计 | Task 5 SessionStore._tick |
| 45 分钟休息提醒 + 遮罩 | Task 5 break_due 事件 + Task 8 遮罩 |
| 里程碑勋章体系（8枚） | Task 5 checkMilestone + Task 10 badges 页 |
| 语音默认/震动/静音切换 | Task 6 AlertService + Task 11 settings |
| storage.js 云同步预留接口 | Task 3 |
| 灵敏度三档 | Task 2 constants + Task 4 analyzePosture + Task 11 |
| 数据统计 stats 页 | Task 9 |
| 用户缺席自动暂停 | Task 4 PostureService._handleAbsent |
| 摄像头权限引导 | Task 8 _startDetecting |
| 基础库版本检测 | ⚠️ **未覆盖** → 见下方补充任务 |

---

## 补充 Task：基础库版本检测

在 `app.js` 的 `onLaunch` 中追加：

```js
// miniprogram/app.js onLaunch 内追加
const systemInfo = wx.getSystemInfoSync()
const [major, minor] = (systemInfo.SDKVersion || '0.0.0').split('.').map(Number)
if (major < 2 || (major === 2 && minor < 20)) {
  wx.showModal({
    title: '版本过低',
    content: '坐姿检测功能需要微信基础库 2.20.0 及以上，请更新微信后再使用',
    showCancel: false,
  })
}
```

```bash
git add miniprogram/app.js
git commit -m "feat: 基础库版本检测（要求 ≥ 2.20.0）"
```
