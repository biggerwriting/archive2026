// miniprogram/utils/storage.js

/**
 * 数据层适配器。
 * 当前实现：wx.setStorage（本地）。
 * 切换云同步时只改此文件，接口不变。
 */
export const storage = {
  /**
   * 读取 storage。key 不存在时 resolve(null)，而非 reject，
   * 使调用处的 `|| {}` / `|| []` 兜底能正常生效，避免产生 unhandled rejection。
   * @returns {Promise<any>}
   */
  get(key) {
    return new Promise((resolve) => {
      wx.getStorage({ key, success: res => resolve(res.data), fail: () => resolve(null) })
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
