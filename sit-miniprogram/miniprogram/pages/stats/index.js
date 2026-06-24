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
    const today = todayStr()
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
      const week = sessions.slice(-7)
      const g = week.reduce((a,s) => a + (s.goodSecs||0), 0)
      const h = week.reduce((a,s) => a + (s.hunchSecs||0), 0)
      const l = week.reduce((a,s) => a + (s.lyingSecs||0), 0)
      this.setData({
        goodTime: fmtMMSS(g), hunchTime: fmtMMSS(h), lyingTime: fmtMMSS(l),
        totalGoodH:   fmtHours(g),
        bestStreakMin: fmtMins(Math.max(0, ...week.map(s=>s.longestGoodStreak||0))),
        breaksTaken:  String(week.reduce((a,s)=>a+(s.breaksTaken||0),0)),
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
      const W = r.width, H = r.height
      const cx = W/2, cy = H/2, radius = Math.min(W,H)*0.4
      const [good, hunch, lying] = this._ringData || [0,0,0]
      const total = good + hunch + lying || 1
      const colors = ['#34c759','#ff9f0a','#ff3b30']
      const vals   = [good, hunch, lying]
      ctx.clearRect(0,0,W,H)
      let start = -Math.PI / 2
      vals.forEach((v, i) => {
        const angle = (v / total) * Math.PI * 2
        ctx.beginPath(); ctx.moveTo(cx, cy)
        ctx.arc(cx, cy, radius, start, start + angle)
        ctx.fillStyle = colors[i]; ctx.fill()
        start += angle
      })
      ctx.beginPath()
      ctx.arc(cx, cy, radius * 0.6, 0, Math.PI * 2)
      ctx.fillStyle = '#fff'; ctx.fill()
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
