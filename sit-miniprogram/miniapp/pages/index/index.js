// ============================================================
// 坐姿检测 - 微信小程序版
// 从 sit/check_posture.py 的 MediaPipe + OpenCV 方案迁移
// 使用微信原生 VisionKit 替代 MediaPipe
// ============================================================

// ── 配置参数（与 Python 版完全一致）────────────────────
const HUNCH_THRESHOLD = 0.18   // 头肩归一化距离，低于此值判定弓腰
const ALERT_SECONDS   = 3.0    // 连续弓腰超过 N 秒才报警
const FRAME_INTERVAL   = 200   // 检测间隔 (ms)，移动端不宜太密

// ── VisionKit 关键点索引（微信人体追踪 32 点）──────────
// 与 MediaPipe 33 点索引不同，需要重新映射
const KEYPOINT = {
  NOSE:         0,
  LEFT_EYE:     1,
  RIGHT_EYE:    2,
  LEFT_EAR:     3,
  RIGHT_EAR:    4,
  LEFT_SHOULDER:  5,
  RIGHT_SHOULDER: 6,
  LEFT_ELBOW:   7,
  RIGHT_ELBOW:  8,
  LEFT_WRIST:   9,
  RIGHT_WRIST:  10,
  LEFT_HIP:     11,
  RIGHT_HIP:    12,
  LEFT_KNEE:    13,
  RIGHT_KNEE:   14,
  LEFT_ANKLE:   15,
  RIGHT_ANKLE:  16,
}

// 骨架连接线（用于绘制，与 Python CONNECTIONS 对应）
const CONNECTIONS = [
  [KEYPOINT.NOSE, KEYPOINT.LEFT_SHOULDER],
  [KEYPOINT.NOSE, KEYPOINT.RIGHT_SHOULDER],
  [KEYPOINT.LEFT_SHOULDER, KEYPOINT.RIGHT_SHOULDER],
  [KEYPOINT.LEFT_SHOULDER, KEYPOINT.LEFT_HIP],
  [KEYPOINT.RIGHT_SHOULDER, KEYPOINT.RIGHT_HIP],
  [KEYPOINT.LEFT_HIP, KEYPOINT.RIGHT_HIP],
  [KEYPOINT.LEFT_HIP, KEYPOINT.LEFT_KNEE],
  [KEYPOINT.RIGHT_HIP, KEYPOINT.RIGHT_KNEE],
  [KEYPOINT.LEFT_KNEE, KEYPOINT.LEFT_ANKLE],
  [KEYPOINT.RIGHT_KNEE, KEYPOINT.RIGHT_ANKLE],
]

Page({
  data: {
    isRunning: false,
    isHunching: false,
    statusText: '准备检测',
    dist: '0.000',
    threshold: HUNCH_THRESHOLD.toFixed(2),
    barWidth: 0,
    hunchSecs: '0.0',
  },

  // ── Canvas 引用 ──────────────────────────────────
  canvas: null,
  ctx: null,
  canvasWidth: 0,
  canvasHeight: 0,

  // ── VisionKit 会话 ───────────────────────────────
  vkSession: null,

  // ── 计时状态（与 Python 的 hunch_start/hunch_secs 对应）──
  hunchStart: null,
  lastFrameTime: 0,

  // ── 页面生命周期 ────────────────────────────────
  onLoad() {
    this.initCanvas()
  },

  onUnload() {
    this.stopMonitor()
  },

  // ── 初始化 Canvas（用于绘制骨架）─────────────────
  initCanvas() {
    const query = wx.createSelectorQuery()
    query.select('#skeletonCanvas')
      .fields({ node: true, size: true })
      .exec((res) => {
        if (!res[0]) return
        const canvas = res[0].node
        const ctx = canvas.getContext('2d')
        const dpr = wx.getSystemInfoSync().pixelRatio

        canvas.width = res[0].width * dpr
        canvas.height = res[0].height * dpr
        ctx.scale(dpr, dpr)

        this.canvas = canvas
        this.ctx = ctx
        this.canvasWidth = res[0].width
        this.canvasHeight = res[0].height
      })
  },

  // ── 开始检测 ─────────────────────────────────────
  async startMonitor() {
    // 1. 请求摄像头权限
    try {
      await this.requestCameraAuth()
    } catch (e) {
      wx.showModal({
        title: '需要摄像头权限',
        content: '请在设置中开启摄像头权限',
        showCancel: false,
      })
      return
    }

    // 2. 初始化 VisionKit 人体追踪
    try {
      await this.initVisionKit()
    } catch (e) {
      console.error('VisionKit 初始化失败:', e)
      wx.showModal({
        title: '设备不支持',
        content: '当前设备不支持人体追踪，请使用 iOS/Android 最新版微信',
        showCancel: false,
      })
      return
    }

    this.setData({
      isRunning: true,
      statusText: '检测中...',
    })
  },

  // ── 停止检测 ─────────────────────────────────────
  stopMonitor() {
    if (this.vkSession) {
      this.vkSession.destroy()
      this.vkSession = null
    }
    this.hunchStart = null
    this.clearCanvas()
    this.setData({
      isRunning: false,
      isHunching: false,
      statusText: '已停止',
      dist: '0.000',
      barWidth: 0,
      hunchSecs: '0.0',
    })
  },

  // ── 请求摄像头权限 ──────────────────────────────
  requestCameraAuth() {
    return new Promise((resolve, reject) => {
      wx.authorize({
        scope: 'scope.camera',
        success: resolve,
        fail: () => {
          // 引导用户去设置页开启
          wx.showModal({
            title: '需要摄像头权限',
            content: '坐姿检测需要使用摄像头实时分析姿态',
            success: (res) => {
              if (res.confirm) {
                wx.openSetting({
                  success: (settingRes) => {
                    if (settingRes.authSetting['scope.camera']) {
                      resolve()
                    } else {
                      reject(new Error('用户拒绝摄像头权限'))
                    }
                  },
                  fail: reject,
                })
              } else {
                reject(new Error('用户取消'))
              }
            },
          })
        },
      })
    })
  },

  // ── 初始化 VisionKit（替代 MediaPipe）────────────
  initVisionKit() {
    return new Promise((resolve, reject) => {
      try {
        const session = wx.createVKSession({
          track: {
            body: {
              mode: 2,   // 全身模式，32 个关键点
            },
          },
        })

        // 监听人体追踪更新
        session.on('update', (frame) => {
          this.handleBodyFrame(frame)
        })

        // 启动会话
        session.start((err) => {
          if (err) {
            reject(err)
            return
          }
          this.vkSession = session
          resolve()
        })
      } catch (e) {
        reject(e)
      }
    })
  },

  // ── 处理每帧人体数据（核心！对应 Python run() 主循环）──
  handleBodyFrame(frame) {
    const now = Date.now()

    // 帧率控制（移动端省电）
    if (now - this.lastFrameTime < FRAME_INTERVAL) return
    this.lastFrameTime = now

    // 获取关键点
    const bodies = frame.body || []
    if (bodies.length === 0) {
      this.clearCanvas()
      this.setData({ statusText: '未检测到人体' })
      return
    }

    // 取第一个人（对应 Python result.pose_landmarks[0]）
    const person = bodies[0]
    const keypoints = person.keypoints

    if (!keypoints || keypoints.length < 17) {
      this.clearCanvas()
      return
    }

    // ── 姿势分析（对应 Python analyze_posture）─────────
    const { isHunching, dist } = this.analyzePosture(keypoints)

    // ── 计时逻辑（对应 Python 的 hunch_start 计时）────
    if (isHunching) {
      if (this.hunchStart === null) {
        this.hunchStart = now
      }
      const hunchSecs = ((now - this.hunchStart) / 1000)

      // 超过 3 秒 → 震动提醒（对应 Python 的 print 报警）
      if (hunchSecs > ALERT_SECONDS) {
        this.doAlert(hunchSecs)
      }

      this.setData({
        isHunching: true,
        hunchSecs: hunchSecs.toFixed(1),
      })
    } else {
      this.hunchStart = null
      this.setData({
        isHunching: false,
        hunchSecs: '0.0',
      })
    }

    // 更新距离 + 进度条（对应 Python draw_feedback 中的进度条）
    this.setData({
      dist: dist.toFixed(3),
      statusText: isHunching ? '⚠  弓腰中，请调整坐姿！' : '✓ 坐姿良好',
      barWidth: Math.min(Math.max(dist / 0.35 * 200, 0), 200),
    })

    // ── 绘制骨架（对应 Python draw_skeleton + draw_feedback）──
    this.drawSkeleton(keypoints, isHunching, dist)
  },

  // ── 坐姿判断算法（Python analyze_posture 的 JS 翻译）──
  // 原 Python:
  //   nose   = get_pt(landmarks, IDX_NOSE)
  //   sh_mid = (get_pt(11) + get_pt(12)) / 2
  //   dist   = sh_mid[1] - nose[1]
  //   is_hunching = dist < HUNCH_THRESHOLD or nose[1] > sh_mid[1]
  analyzePosture(keypoints) {
    const nose = keypoints[KEYPOINT.NOSE]
    const lSh  = keypoints[KEYPOINT.LEFT_SHOULDER]
    const rSh  = keypoints[KEYPOINT.RIGHT_SHOULDER]

    // 关键点不可见或置信度太低，跳过
    if (!nose || !lSh || !rSh) return { isHunching: false, dist: 1.0 }
    if (nose.confidence < 0.5 || lSh.confidence < 0.5 || rSh.confidence < 0.5) {
      return { isHunching: false, dist: 1.0 }
    }

    const shMidY = (lSh.y + rSh.y) / 2

    // y 轴：VisionKit 的 y 从下到上是 0→1，但我们的逻辑用归一化坐标
    // dist = 肩中点 y - 鼻 y，正值 = 头在肩膀上方
    const dist = shMidY - nose.y
    const noseBelow = nose.y > shMidY  // 鼻子低于肩膀 = 严重趴伏

    const isHunching = dist < HUNCH_THRESHOLD || noseBelow
    return { isHunching, dist }
  },

  // ── 报警（对应 Python 的 print 报警）─────────────
  doAlert(hunchSecs) {
    // 震动提醒（每 2 秒震一次，避免太频繁）
    if (Math.floor(hunchSecs) % 2 === 0) {
      wx.vibrateLong()
    }
  },

  // ── 绘制骨架（对应 Python draw_skeleton + draw_feedback）──
  drawSkeleton(keypoints, isHunching) {
    if (!this.ctx || !this.canvasWidth) return

    const ctx = this.ctx
    const w = this.canvasWidth
    const h = this.canvasHeight

    ctx.clearRect(0, 0, w, h)

    // 连线（对应 Python 的 cv2.line）
    ctx.strokeStyle = isHunching ? 'rgba(255,80,80,0.8)' : 'rgba(0,200,120,0.6)'
    ctx.lineWidth = 2
    ctx.beginPath()
    for (const [i, j] of CONNECTIONS) {
      const a = keypoints[i]
      const b = keypoints[j]
      if (!a || !b) continue
      if (a.confidence < 0.4 || b.confidence < 0.4) continue
      // VisionKit y 轴方向：需要通过 canvas 高度减去来翻转
      ctx.moveTo(a.x * w, h - a.y * h)
      ctx.lineTo(b.x * w, h - b.y * h)
    }
    ctx.stroke()

    // 圆点（对应 Python 的 cv2.circle）
    const color = isHunching ? 'rgba(255,71,87,0.9)' : 'rgba(0,200,150,0.9)'
    const drawKeys = [
      KEYPOINT.NOSE,
      KEYPOINT.LEFT_SHOULDER, KEYPOINT.RIGHT_SHOULDER,
      KEYPOINT.LEFT_HIP, KEYPOINT.RIGHT_HIP,
      KEYPOINT.LEFT_KNEE, KEYPOINT.RIGHT_KNEE,
      KEYPOINT.LEFT_ANKLE, KEYPOINT.RIGHT_ANKLE,
    ]
    for (const idx of drawKeys) {
      const pt = keypoints[idx]
      if (!pt || pt.confidence < 0.4) continue
      ctx.fillStyle = color
      ctx.beginPath()
      ctx.arc(pt.x * w, h - pt.y * h, 5, 0, Math.PI * 2)
      ctx.fill()
    }

    // 边界高亮（对应 Python cv2.rectangle 红框）
    if (isHunching) {
      ctx.strokeStyle = 'rgba(255,71,87,1)'
      ctx.lineWidth = 6
      ctx.strokeRect(0, 0, w, h)
    }
  },

  // ── 清空画布 ─────────────────────────────────────
  clearCanvas() {
    if (this.ctx && this.canvasWidth) {
      this.ctx.clearRect(0, 0, this.canvasWidth, this.canvasHeight)
    }
  },

  // ── 摄像头错误处理 ──────────────────────────────
  onCameraError(e) {
    console.error('摄像头错误:', e.detail)
    wx.showToast({ title: '摄像头异常', icon: 'error' })
  },
})
