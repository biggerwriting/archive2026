// miniprogram/services/PostureService.js
import { HUNCH_THRESHOLD, KP, KP_HEAD, SKELETON_CONNECTIONS, ABSENT_PAUSE_SECS } from '../utils/constants'

/**
 * PostureService
 * 封装 VisionKit body 会话，对外暴露坐姿状态流。
 *
 * 用法：
 *   PostureService.start()
 *   PostureService.onPostureChange(({ type, keypoints }) => { ... })
 *   PostureService.stop()
 */
const PostureService = {
  _session:        null,
  _listeners:      [],
  _lastType:       null,
  _absentTimer:    null,
  _absentSeconds:  0,
  _sensitivity:    'normal',

  /** 设置灵敏度，必须在 start() 前调用 */
  setSensitivity(sensitivity) {
    this._sensitivity = sensitivity
  },

  /** 注册坐姿变更监听器 */
  onPostureChange(callback) {
    this._listeners.push(callback)
  },

  /** 移除所有监听器 */
  offPostureChange() {
    this._listeners = []
  },

  /**
   * 启动 VisionKit body 会话（摄像头实时检测模式）。
   * body mode:1 独占摄像头，不支持同时使用 <camera> 组件或 setCanvas。
   * canvas 仅供页面叠加骨架线（黑色背景）。
   */
  start() {
    if (this._session) return

    // ⚠️ track key 必须用 'body'，不是 'humanBody'（官方文档确认）
    // 参考：https://developers.weixin.qq.com/miniprogram/dev/framework/open-ability/visionkit/body.html
    this._session = wx.createVKSession({
      track: { body: { mode: 1 } },   // 2D 人体姿态追踪，mode:1=摄像头实时
    })

    this._session.start((err) => {
      if (err) {
        // err 可能是数字（直接的错误码）或对象 {errCode, errMsg}
        // 常见码：10=无摄像头权限，20001=设备不支持，20003=后端异常
        const code = (err && typeof err === 'object') ? err.errCode : err
        console.error('[PostureService] VKSession 启动失败，errCode:', code, err)
        this._emit({ type: 'error', error: { errCode: code } })
        return
      }
      console.log('[PostureService] VKSession 启动成功，开启 RAF 循环')
      this._startLoop()   // ← 启动 requestAnimationFrame 循环，驱动帧处理
    })

    this._session.on('updateAnchors', (anchors) => {
      if (!anchors || anchors.length === 0) return
      this._absentSeconds = 0
      clearTimeout(this._absentTimer)
      this._absentTimer = null

      const anchor = anchors[0]
      const points = anchor.points || []

      const type = analyzePosture(points, HUNCH_THRESHOLD[this._sensitivity])
      if (type !== this._lastType) {
        this._lastType = type
        this._emit({ type, keypoints: points })
      }
    })

    // 人体离开摄像头时触发（官方文档标准事件，比空数组判断更可靠）
    this._session.on('removeAnchors', () => {
      this._handleAbsent()
    })
  },

  /** 停止会话，释放摄像头 */
  stop() {
    if (this._session) {
      this._session.stop()
      this._session = null
    }
    this._lastType = null
    this._absentSeconds = 0
    clearTimeout(this._absentTimer)
    this._absentTimer = null
  },

  _emit(event) {
    this._listeners.forEach(fn => fn(event))
  },

  /**
   * requestAnimationFrame 循环——VisionKit 需要持续调用才会处理摄像头帧、
   * 触发 updateAnchors 事件并渲染摄像头画面到 Canvas。
   */
  _startLoop() {
    const loop = () => {
      if (!this._session) return          // 已 stop()，退出循环
      this._session.requestAnimationFrame(loop)
    }
    this._session.requestAnimationFrame(loop)
  },

  _handleAbsent() {
    // 连续检测不到人体 ABSENT_PAUSE_SECS 秒 → 发出 absent 事件
    if (!this._absentTimer) {
      this._absentTimer = setTimeout(() => {
        this._lastType = 'absent'
        this._emit({ type: 'absent', keypoints: [] })
        this._absentTimer = null
      }, ABSENT_PAUSE_SECS * 1000)
    }
  },
}

/**
 * 纯函数：根据关键点判断坐姿类型。
 * 独立导出，便于单元测试。
 *
 * @param {Array<{x:number, y:number, score:number}>} points 归一化坐标 [0,1]
 * @param {number} threshold 弓腰判定阈值
 * @returns {'good'|'hunching'|'lying'|'unknown'}
 */
export function analyzePosture(points, threshold) {
  const MIN_SCORE = 0.5
  // KP_HEAD = KP.NOSE (索引0)，置信度比 KP.HEAD(17, 头顶) 更稳定
  const head  = points[KP_HEAD]
  const lSh   = points[KP.L_SHOULDER]
  const rSh   = points[KP.R_SHOULDER]

  if (!head || !lSh || !rSh) return 'unknown'
  if (head.score < MIN_SCORE || lSh.score < MIN_SCORE || rSh.score < MIN_SCORE) {
    return 'unknown'
  }

  const shMidY = (lSh.y + rSh.y) / 2
  const dist   = shMidY - head.y   // 正值 = 头在肩上方

  if (head.y > shMidY)      return 'lying'     // 趴着：头低于肩中点
  if (dist < threshold)     return 'hunching'  // 弓腰：头肩距不足
  return 'good'
}

export default PostureService
