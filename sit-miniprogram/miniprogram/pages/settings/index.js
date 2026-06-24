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

  setAlertMode(e)   { this.setData({ alertMode:   e.currentTarget.dataset.val }); this._save() },
  setSensitivity(e) { this.setData({ sensitivity: e.currentTarget.dataset.val }); this._save() },

  incSittingLimit() { if (this.data.sittingLimitMins    < 90) { this.setData({ sittingLimitMins:    this.data.sittingLimitMins    + 5 }); this._save() } },
  decSittingLimit() { if (this.data.sittingLimitMins    > 20) { this.setData({ sittingLimitMins:    this.data.sittingLimitMins    - 5 }); this._save() } },
  incHunchDelay()   { if (this.data.hunchAlertDelaySecs < 10) { this.setData({ hunchAlertDelaySecs: this.data.hunchAlertDelaySecs + 1 }); this._save() } },
  decHunchDelay()   { if (this.data.hunchAlertDelaySecs >  1) { this.setData({ hunchAlertDelaySecs: this.data.hunchAlertDelaySecs - 1 }); this._save() } },
})
