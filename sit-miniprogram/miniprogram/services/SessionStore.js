// miniprogram/services/SessionStore.js
import { BADGE_DEFS } from '../utils/constants'
import { storage } from '../utils/storage'

/**
 * SessionStore
 * 管理当次检测会话的计时状态，触发休息提醒和勋章检查。
 *
 * 用法：
 *   await SessionStore.init(settings)
 *   SessionStore.setPostureType('good')   // 由 PostureService 回调驱动
 *   SessionStore.onEvent(callback)        // 监听 alert / break_due / badge_earned 事件
 *   SessionStore.start()
 *   await SessionStore.stop()
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
        // 在每日结束时检查，此处不做实时检查
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
