# 坐姿检测微信小程序 — 设计文档

**日期：** 2026-06-16  
**状态：** 已通过设计评审，待实现  
**参考：** 现有 `check_posture.py`（MediaPipe Tasks API，Python 版核心算法）

---

## 1. 背景与目标

开发一款面向**学生和上班族**的微信小程序，利用前置摄像头实时检测坐姿，帮助用户养成良好习惯、保护眼睛与脊椎。

**核心功能：**
1. 实时坐姿检测（端正 / 弓腰 / 趴着），姿势变差时给出提醒
2. 计时统计：端正坐姿时长、弓腰时长、趴着时长
3. 45 分钟连续坐姿后提醒休息
4. 里程碑勋章体系，激励用户做到劳逸结合
5. 提醒方式：默认语音播报，可切换震动或静音

**不在本版本范围内：** 云同步、用户账号体系、排行榜（预留接口，后续迭代）

---

## 2. 技术选型

| 能力 | 方案 | 理由 |
|------|------|------|
| 姿态检测 | 微信 VisionKit（基础库 ≥ 2.20.0）`humanBody` tracking | 内置能力，零模型下载，低延迟，隐私友好 |
| 数据持久化 | `wx.setStorage`（本地） | MVP 优先，通过 `storage.js` 适配器预留云同步接口 |
| 语音提醒 | `wx.createInnerAudioContext` 播放本地 mp3 | 不依赖网络，延迟低 |
| 震动提醒 | `wx.vibrateShort` / `wx.vibrateLong` | 系统 API，无需权限 |
| 图表 | 微信内置 Canvas 2D API（折线图/环形图手绘） | 避免引入第三方库 |

**设备使用场景：** 手机/平板立在桌上，前置摄像头正对用户上半身。

---

## 3. 架构设计

```
┌─────────────────────────────────────────────────────────┐
│                    WeChat Mini Program                   │
├────────────────────┬───────────────────┬────────────────┤
│  pages/            │  services/        │  utils/        │
│  ├─ monitor/       │  ├─ PostureService│  ├─ storage.js │
│  ├─ stats/         │  ├─ SessionStore  │  └─ constants  │
│  ├─ badges/        │  └─ AlertService  │                │
│  └─ settings/      │                   │                │
└────────────────────┴───────────────────┴────────────────┘
         │                   │                   │
         └──── 调用 / 订阅 ──┘                   │
                             │                   │
                     ┌───────┴──────┐            │
                     │  wx.Storage  │◄───────────┘
                     └──────────────┘
                             ▲
               wx.createVKSession (humanBody)
```

**分层原则：**
- Pages 层只负责 UI 渲染，不含业务逻辑
- Services 层处理所有检测、计时、提醒逻辑，与 UI 解耦
- `utils/storage.js` 作为数据层适配器，上层不直接调用 `wx.setStorage`

---

## 4. 服务层详细设计

### 4.1 PostureService.js

封装 VisionKit 会话，对外暴露坐姿状态流。

**公开接口：**
```js
PostureService.start()                    // 启动 VKSession，开始推理
PostureService.stop()                     // 停止并释放摄像头
PostureService.onPostureChange(callback)  // 注册状态变更监听
// callback({ type: 'good'|'hunching'|'lying', keypoints, timestamp })
```

**判姿算法（移植自 check_posture.py）：**

使用 VisionKit `humanBody` 模式返回的关键点（COCO 17点格式，归一化坐标 0–1）：

```js
const KEYPOINTS = { NOSE: 0, L_SHOULDER: 5, R_SHOULDER: 6 }

function analyzePosture(keypoints, threshold) {
  const nose  = keypoints[KEYPOINTS.NOSE]
  const lSh   = keypoints[KEYPOINTS.L_SHOULDER]
  const rSh   = keypoints[KEYPOINTS.R_SHOULDER]
  const shMidY = (lSh.y + rSh.y) / 2
  const dist   = shMidY - nose.y   // 正值 = 头在肩上方

  if (nose.score < 0.6 || lSh.score < 0.6 || rSh.score < 0.6) {
    return 'unknown'   // 置信度不足，不做判断
  }
  if (nose.y > shMidY)      return 'lying'
  if (dist < threshold)     return 'hunching'
  return 'good'
}
```

**灵敏度档位对应阈值：**
| 档位 | `HUNCH_THRESHOLD` |
|------|------------------|
| 宽松 | 0.12 |
| 标准（默认） | 0.18 |
| 严格 | 0.24 |

### 4.2 SessionStore.js

驱动所有计时逻辑，维护会话状态，触发勋章检查。

**内部状态：**
```js
{
  status:       'idle' | 'detecting' | 'resting',
  goodSecs:      0,       // 本次会话端正累计
  hunchSecs:     0,       // 弓腰累计
  lyingSecs:     0,       // 趴着累计
  currentStreak: 0,       // 当前连续端正秒数
  sittingSecs:   0,       // 坐着总计（goodSecs + hunchSecs + lyingSecs）
  breaksTaken:   0        // 本次会话休息次数
}
```

**Tick 逻辑（每秒执行）：**
1. 按当前 `postureType` 累加对应计数器
2. `sittingSecs` 达到 `sittingLimitMins × 60` → 触发休息提醒，重置 `sittingSecs`，`breaksTaken++`
3. 检查勋章里程碑（见第 6 节）
4. 每 60 秒调用 `storage.js` 持久化当日记录

**用户休息检测：** VisionKit 检测不到人体（`unknown` 状态持续 ≥ 10 秒）视为用户已离开，自动暂停计时。

### 4.3 AlertService.js

管理所有提醒的策略与防抖。

**提醒类型与参数：**

| 类型 | 触发条件 | 最小触发间隔 | 语音文本 |
|------|---------|-------------|---------|
| `posture_bad` | 连续弓腰 ≥ `hunchAlertDelaySecs` | 30s | 「请调整坐姿，抬头挺胸」 |
| `lying_down` | 连续趴着 ≥ 5s | 30s | 「请不要趴着，小心眼睛近视」 |
| `take_break` | 坐满 `sittingLimitMins` 分钟 | 无限制 | 「已持续坐了 X 分钟，站起来活动一下吧」 |
| `badge_earned` | 勋章解锁 | 无限制 | 「恭喜解锁勋章：{name}」 |
| `posture_good` | hunching/lying → good（可选） | 60s | 「很好，继续保持」 |

**提醒模式切换：**
- `voice`：播放对应 mp3（`/assets/audio/`）
- `vibration`：`wx.vibrateShort` × 2（坐姿提醒）/ `wx.vibrateLong`（休息提醒）
- `silent`：仅更新 UI 状态卡片颜色，不发声不震动

---

## 5. 页面设计

### TabBar 导航
底部 4 个 Tab：📷 检测 · 📊 统计 · 🏅 勋章 · ⚙️ 设置

### 5.1 monitor 页（主页）

**布局（从上到下）：**
1. **状态卡片**：大字显示坐姿类型 + 当前连续端正时长；颜色：绿（端正）/ 橙（弓腰）/ 红（趴着）
2. **摄像头预览区**：VisionKit `wx.createVKSession` 渲染到 Canvas，骨架关键点连线叠加绘制（不使用 `<camera>` 组件，VKSession 自行管理摄像头）
3. **今日数据栏**：端正时长 / 弓腰趴着时长（两格）
4. **45 分钟进度条**：显示距下次休息剩余时间
5. **开始/停止按钮**

**全屏休息遮罩：** 坐满 45 分钟时弹出蓝色半透明遮罩，显示「该休息了！已坐 X 分钟」，用户点击「好的，我去活动」后消失并重置计时。

### 5.2 stats 页（统计）

- 今日 / 本周 Tab 切换
- 环形图：端正 / 弓腰 / 趴着时长占比（Canvas 手绘）
- 柱状图：近 7 天端正坐姿分钟数（Canvas 手绘）
- 数字摘要：今日端正总时长、最长连续端正时长、休息次数

### 5.3 badges 页（勋章）

- 进度标题：「已获得 X / 8 枚」
- 2 列网格：已解锁（亮色 + 获得日期） / 未解锁（灰色 + 解锁条件描述）

### 5.4 settings 页（设置）

- 提醒方式：语音 / 震动 / 静音（Segment）
- 检测灵敏度：宽松 / 标准 / 严格（Segment）
- 坐满提醒分钟数：步进器（默认 45，范围 20–90）
- 连续弓腰触发提醒秒数：步进器（默认 3，范围 1–10）

---

## 6. 勋章体系

触发时机：每次 SessionStore tick 后由 `checkMilestones()` 检查，已解锁的跳过。

| ID | 名称 | 图标 | 触发条件 |
|----|------|------|---------|
| `first_session` | 初次体验 | 🎯 | 完成首次检测（连续 ≥ 1 分钟） |
| `first_break` | 第一次休息 | ☕ | 坐满 45 分钟后，VisionKit 连续 10s 检测不到人体（视为用户已站起） |
| `good_30min` | 坚持30分钟 | ⏱ | 单次连续端正坐姿 ≥ 30 分钟 |
| `good_10h` | 坚持10小时 | 🏆 | 累计端正坐姿 ≥ 10 小时（跨天） |
| `eye_protector` | 护眼卫士 | 👁 | 连续 7 个「有效使用日」（当日使用 ≥ 30 分钟）每天趴着时长均 < 10 分钟 |
| `rest_10` | 劳逸达人 | 💪 | 累计主动休息 10 次 |
| `perfect_day` | 姿势大师 | 🥋 | 单日弓腰 + 趴着总时长 < 5 分钟 |
| `early_bird` | 早起护脊 | 🌅 | 早上 8 点前完成一次检测（≥ 1 分钟） |

---

## 7. 数据模型

全部通过 `utils/storage.js` 读写，Key 如下：

### `sessions`（Array，保留最近 90 天）
```js
{
  date:              'YYYY-MM-DD',   // 主键
  goodSecs:           number,        // 端正累计秒数
  hunchSecs:          number,        // 弓腰累计秒数
  lyingSecs:          number,        // 趴着累计秒数
  breaksTaken:        number,        // 主动休息次数
  longestGoodStreak:  number         // 当日最长连续端正秒数
}
```

### `badges`（Array）
```js
{ id: string, earnedAt: number /* Unix 时间戳 */ }
```

### `settings`（Object）
```js
{
  alertMode:           'voice' | 'vibration' | 'silent',  // 默认 'voice'
  sensitivity:         'loose' | 'normal' | 'strict',     // 默认 'normal'
  sittingLimitMins:    number,    // 默认 45
  hunchAlertDelaySecs: number     // 默认 3
}
```

### `utils/storage.js` 接口（云同步预留）
```js
export const storage = {
  get(key),               // → Promise<value>
  set(key, value),        // → Promise<void>
  append(key, item),      // sessions 专用，追加或更新当日记录
}
// 当前实现：wx.getStorage / wx.setStorage
// 云同步时：替换为 wx.cloud.database 调用，接口不变
```

---

## 8. 文件结构

```
miniprogram/
├── app.js / app.json / app.wxss
├── assets/
│   └── audio/
│       ├── posture_bad.mp3
│       ├── lying_down.mp3
│       ├── take_break.mp3
│       ├── badge_earned.mp3
│       └── posture_good.mp3
├── pages/
│   ├── monitor/    (index.js / index.wxml / index.wxss / index.json)
│   ├── stats/
│   ├── badges/
│   └── settings/
├── services/
│   ├── PostureService.js
│   ├── SessionStore.js
│   └── AlertService.js
└── utils/
    ├── storage.js          ← 数据层适配器
    └── constants.js        ← 阈值、勋章定义等常量
```

---

## 9. 错误处理

| 场景 | 处理方式 |
|------|---------|
| 用户拒绝摄像头权限 | 弹出引导弹窗说明用途，提供「去设置开启」按钮 |
| VisionKit 不支持（基础库 < 2.20.0）| 启动时检测版本，提示用户更新微信 |
| 长时间未检测到人体 | 10s 后自动暂停计时，显示「未检测到人，已暂停」 |
| Storage 写入失败 | 静默忽略，下次 tick 重试；不影响检测主流程 |

---

## 10. 后续迭代方向（本版本不实现）

- 微信云开发：多设备数据同步
- 家长模式：家长查看孩子的统计数据
- 学校/班级排行榜
- 自定义语音包
- Apple Watch / 手环震动联动
