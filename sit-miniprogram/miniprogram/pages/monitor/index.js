// miniprogram/pages/monitor/index.js
import PostureService from '../../services/PostureService'
import SessionStore   from '../../services/SessionStore'
import AlertService   from '../../services/AlertService'
import { storage }    from '../../utils/storage'
import { SKELETON_CONNECTIONS } from '../../utils/constants'

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
    detecting:        false,
    postureType:      'unknown',
    statusIcon:       '👤',
    statusText:       '点击开始检测',
    streakTime:       '00:00',
    todayGoodTime:    '00:00',
    todayBadTime:     '00:00',
    breakCountdown:   '--:--',
    breakProgress:    0,
    showBreakOverlay: false,
    sittingMins:      0,
    newBadge:         null,
  },

  _tickTimer:  null,
  _settings:   null,
  _canvas:     null,
  _ctx:        null,
  _canvasW:    0,
  _canvasH:    0,

  async onLoad() {
    this._settings = (await storage.get('settings')) || {
      alertMode: 'voice', sensitivity: 'normal',
      sittingLimitMins: 45, hunchAlertDelaySecs: 3,
    }
    AlertService.setMode(this._settings.alertMode)
    PostureService.setSensitivity(this._settings.sensitivity)
    await SessionStore.init(this._settings)
  },

  onUnload() { this._stopDetecting() },
  onHide()   { this._stopDetecting() },

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

  _startDetecting() {
    // wx.authorize 在 VisionKit 场景下不可靠（部分机型不弹框）。
    // 改为：查当前授权状态 → 若曾明确拒绝则引导去设置，否则直接启动。
    // VKSession.start() 会在首次使用时自动触发系统摄像头权限弹框。
    wx.getSetting({
      success: (res) => {
        if (res.authSetting['scope.camera'] === false) {
          // 用户之前明确拒绝过 → 引导去设置页重新开启
          wx.showModal({
            title: '需要摄像头权限',
            content: '坐姿检测需要摄像头，请在「设置」中开启摄像头权限后重试',
            confirmText: '去设置',
            cancelText: '取消',
            success: (modalRes) => { if (modalRes.confirm) wx.openSetting() },
          })
        } else {
          // 未授权（首次）或已授权 → 直接启动，VKSession 自动弹权限框
          this._doStart()
        }
      },
      fail: () => this._doStart(),  // getSetting 失败也直接尝试
    })
  },

  _doStart() {
    this.setData({ detecting: true })
    this._bindServices()
    SessionStore.start()

    // 先拿到 Canvas 节点供骨架线叠加绘制（摄像头画面由 <camera> 组件渲染，不需传给 VKSession）
    wx.createSelectorQuery()
      .select('#vk-canvas')
      .fields({ node: true, size: true })
      .exec(([res]) => {
        if (!res) {
          console.error('[monitor] 找不到 #vk-canvas，请确认 WXML 已渲染')
          return
        }
        const canvas  = res.node
        const ctx     = canvas.getContext('2d')
        canvas.width  = res.width
        canvas.height = res.height
        this._canvas  = canvas
        this._ctx     = ctx
        this._canvasW = res.width
        this._canvasH = res.height

        // 启动 VKSession（2D 模式不接收 canvas，摄像头由 <camera> 组件负责）
        PostureService.start()
        this._startSkeletonDraw()
      })

    this._tickTimer = setInterval(() => this._updateUI(), 1000)
  },

  async _stopDetecting() {
    clearInterval(this._tickTimer)
    this._tickTimer = null
    PostureService.stop()
    PostureService.offPostureChange()
    SessionStore.offEvent()
    await SessionStore.stop()
    this.setData({
      detecting: false, postureType: 'unknown',
      statusIcon: '👤', statusText: '点击开始检测', streakTime: '00:00',
    })
  },

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

  _updateUI() {
    const s = SessionStore
    const sittingLimit = (this._settings?.sittingLimitMins || 45) * 60
    const progress  = Math.min(100, Math.round(s._sittingSecs / sittingLimit * 100))
    const remaining = Math.max(0, sittingLimit - s._sittingSecs)

    this.setData({
      streakTime:     fmtTime(s._currentStreak),
      todayGoodTime:  fmtTime(s._goodSecs),
      todayBadTime:   fmtTime(s._hunchSecs + s._lyingSecs),
      breakProgress:  progress,
      breakCountdown: fmtTime(remaining),
    })
  },

  _startSkeletonDraw() {
    if (!PostureService._session) return
    let _loggedOnce = false  // 只打印一次关键点，用于核对索引顺序

    PostureService._session.on('updateAnchors', (anchors) => {
      const ctx = this._ctx
      if (!ctx) return
      ctx.clearRect(0, 0, this._canvasW, this._canvasH)
      if (!anchors || anchors.length === 0) return

      const pts = anchors[0].points
      if (!pts || pts.length === 0) return

      // 首次检测到人体时打印关键点，用于核对 constants.js 中 KP 索引是否正确
      // 确认无误后可删除这段 log
      if (!_loggedOnce) {
        _loggedOnce = true
        console.log('[骨架调试] 关键点数量:', pts.length)
        pts.forEach((p, i) => console.log(`  [${i}] x=${p.x?.toFixed(3)} y=${p.y?.toFixed(3)} score=${p.score?.toFixed(2)}`))
      }

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
