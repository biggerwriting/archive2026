// miniprogram/app.js
App({
  onLaunch() {
    // 基础库版本检测
    const systemInfo = wx.getSystemInfoSync()
    const parts = (systemInfo.SDKVersion || '0.0.0').split('.').map(Number)
    const [major, minor] = parts
    if (major < 2 || (major === 2 && minor < 20)) {
      wx.showModal({
        title: '版本过低',
        content: '坐姿检测功能需要微信基础库 2.20.0 及以上，请更新微信后再使用',
        showCancel: false,
      })
    }

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
