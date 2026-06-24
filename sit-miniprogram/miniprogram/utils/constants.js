// miniprogram/utils/constants.js

// ── 判姿阈值（头肩距离，归一化 [0,1]）────────────────────────
// VisionKit 坐标已归一化，与 check_posture.py 逻辑一致
export const HUNCH_THRESHOLD = {
  loose:  0.12,
  normal: 0.18,
  strict: 0.24,
}

// ── VisionKit body 关键点索引（官方23点定义，COCO 顺序）────────
// 官方文档：https://developers.weixin.qq.com/miniprogram/dev/framework/open-ability/visionkit/body.html
// ⚠️  track key 必须是 'body'，不是 'humanBody'
// ⚠️  首次运行时建议打印 anchor.points 核对实际顺序是否与此一致
export const KP = {
  NOSE:        0,  // 鼻子（用作头部参考点）
  L_EYE:       1,  // 左眼
  R_EYE:       2,  // 右眼
  L_EAR:       3,  // 左耳
  R_EAR:       4,  // 右耳
  L_SHOULDER:  5,  // 左肩 ← 坐姿分析关键点
  R_SHOULDER:  6,  // 右肩 ← 坐姿分析关键点
  L_ELBOW:     7,  // 左肘
  R_ELBOW:     8,  // 右肘
  L_WRIST:     9,  // 左腕
  R_WRIST:     10, // 右腕
  L_HIP:       11, // 左髋
  R_HIP:       12, // 右髋
  L_KNEE:      13, // 左膝
  R_KNEE:      14, // 右膝
  L_ANKLE:     15, // 左踝
  R_ANKLE:     16, // 右踝
  HEAD:        17, // 头顶（部分版本有，score 可能较低）
  NECK:        18, // 颈部（部分版本有）
  // 19-22: 脚趾等，不参与坐姿分析
}

// analyzePosture 用 NOSE 作头部参考（索引0，置信度最稳定）
export const KP_HEAD = KP.NOSE

// ── 骨架连接线（用于 Canvas 绘制）────────────────────────────
export const SKELETON_CONNECTIONS = [
  // 躯干
  [KP.L_SHOULDER, KP.R_SHOULDER],
  [KP.L_SHOULDER, KP.L_HIP],
  [KP.R_SHOULDER, KP.R_HIP],
  [KP.L_HIP,      KP.R_HIP],
  // 左臂
  [KP.L_SHOULDER, KP.L_ELBOW],
  [KP.L_ELBOW,    KP.L_WRIST],
  // 右臂
  [KP.R_SHOULDER, KP.R_ELBOW],
  [KP.R_ELBOW,    KP.R_WRIST],
  // 左腿
  [KP.L_HIP,      KP.L_KNEE],
  [KP.L_KNEE,     KP.L_ANKLE],
  // 右腿
  [KP.R_HIP,      KP.R_KNEE],
  [KP.R_KNEE,     KP.R_ANKLE],
  // 头部到肩
  [KP.NOSE,       KP.L_SHOULDER],
  [KP.NOSE,       KP.R_SHOULDER],
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
