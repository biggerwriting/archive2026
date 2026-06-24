// miniprogram/services/AlertService.js
import { ALERT_COOLDOWN_SECS } from '../utils/constants'

const AlertService = {
  _mode:         'voice',
  _lastAlertAt:  {},
  _audioCtx:     null,

  setMode(mode) {
    this._mode = mode
  },

  fire(alertType) {
    if (this._mode === 'silent') return

    const cooldown = (ALERT_COOLDOWN_SECS[alertType] || 0) * 1000
    const now = Date.now()
    if (cooldown > 0 && this._lastAlertAt[alertType] &&
        now - this._lastAlertAt[alertType] < cooldown) {
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
    const texts = {
      posture_bad:  '请调整坐姿，抬头挺胸',
      lying_down:   '请不要趴着，小心眼睛近视',
      take_break:   '已持续坐了很久，站起来活动一下吧',
      badge_earned: '恭喜你，解锁了新勋章',
      posture_good: '很好，继续保持',
    }
    const text = texts[alertType]
    if (!text) return
    if (!this._audioCtx) {
      this._audioCtx = wx.createInnerAudioContext()
    }
    wx.textToSpeech({
      lang:   'zh_CN',
      speed:  1.0,
      volume: 1.0,
      text,
      success: (res) => {
        this._audioCtx.stop()
        this._audioCtx.src = res.filename
        this._audioCtx.play()
      },
      fail: (err) => {
        console.warn('[AlertService] TTS failed:', err)
      },
    })
  },

  _vibrate(alertType) {
    if (alertType === 'take_break') {
      wx.vibrateLong()
    } else {
      wx.vibrateShort()
      setTimeout(() => wx.vibrateShort(), 300)
    }
  },

  _reset() {
    this._mode = 'voice'
    this._lastAlertAt = {}
    this._audioCtx = null
  },
}

export default AlertService
