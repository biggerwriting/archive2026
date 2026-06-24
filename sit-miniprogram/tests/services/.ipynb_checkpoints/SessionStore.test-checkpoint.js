// tests/services/SessionStore.test.js
const wxMock = require('../__mocks__/wx')
global.wx = wxMock

jest.useFakeTimers()

const SessionStore = require('miniprogram/services/SessionStore').default

function resetStore() {
  Object.assign(SessionStore, {
    _goodSecs: 0, _hunchSecs: 0, _lyingSecs: 0,
    _sittingSecs: 0, _breaksTaken: 0,
    _currentStreak: 0, _bestStreak: 0,
    _hunchContSecs: 0, _lyingContSecs: 0,
    _currentType: 'unknown', _ticker: null,
    _persistCounter: 0, _listeners: [], _earnedIds: new Set(),
    _today: '2026-06-16',
    sittingLimitSecs: 45 * 60,
    hunchAlertDelaySecs: 3,
  })
}

// 刷新所有挂起的 Promise 微任务（不推进 fake timer）
async function flushPromises() {
  // 多轮 Promise.resolve() 让链式 async/await 全部 settle
  for (let i = 0; i < 10; i++) {
    await Promise.resolve()
  }
}

beforeEach(async () => {
  wxMock.__resetStore()
  resetStore()
  await SessionStore.init({ sittingLimitMins: 45, hunchAlertDelaySecs: 3 })
})

afterEach(() => {
  clearInterval(SessionStore._ticker)
  SessionStore._ticker = null
  jest.clearAllTimers()
  SessionStore.offEvent()
})

describe('基础计时', () => {
  test('good 姿势每 tick 增加 goodSecs 和 sittingSecs', () => {
    SessionStore.setPostureType('good')
    SessionStore._tick()
    SessionStore._tick()
    expect(SessionStore._goodSecs).toBe(2)
    expect(SessionStore._sittingSecs).toBe(2)
  })

  test('hunching 姿势每 tick 增加 hunchSecs', () => {
    SessionStore.setPostureType('hunching')
    SessionStore._tick()
    expect(SessionStore._hunchSecs).toBe(1)
    expect(SessionStore._sittingSecs).toBe(1)
  })

  test('absent 时不计时，连续计数重置', () => {
    SessionStore.setPostureType('absent')
    SessionStore._tick()
    SessionStore._tick()
    expect(SessionStore._goodSecs).toBe(0)
    expect(SessionStore._sittingSecs).toBe(0)
  })

  test('good 后 hunching，连续端正计数重置', () => {
    SessionStore.setPostureType('good')
    SessionStore._tick()
    SessionStore._tick()
    expect(SessionStore._currentStreak).toBe(2)
    SessionStore.setPostureType('hunching')
    SessionStore._tick()
    expect(SessionStore._currentStreak).toBe(0)
  })
})

describe('提醒触发', () => {
  test('连续弓腰 3 秒后发出 posture_bad 事件', () => {
    const events = []
    SessionStore.onEvent(e => events.push(e))
    SessionStore.setPostureType('hunching')
    SessionStore._tick(); SessionStore._tick(); SessionStore._tick()
    expect(events).toContainEqual({ event: 'alert', alertType: 'posture_bad' })
  })

  test('连续趴着 5 秒后发出 lying_down 事件', () => {
    const events = []
    SessionStore.onEvent(e => events.push(e))
    SessionStore.setPostureType('lying')
    for (let i = 0; i < 5; i++) SessionStore._tick()
    expect(events).toContainEqual({ event: 'alert', alertType: 'lying_down' })
  })

  test('坐满 sittingLimitSecs 后发出 break_due 事件', () => {
    const events = []
    SessionStore.onEvent(e => events.push(e))
    SessionStore.sittingLimitSecs = 3   // 测试用：3 秒触发
    SessionStore.setPostureType('good')
    for (let i = 0; i < 3; i++) SessionStore._tick()
    expect(events.some(e => e.event === 'break_due')).toBe(true)
  })
})

describe('勋章里程碑', () => {
  test('检测满 60 秒后解锁 first_session', async () => {
    const events = []
    SessionStore.onEvent(e => events.push(e))
    SessionStore.setPostureType('good')
    for (let i = 0; i < 60; i++) SessionStore._tick()
    // 等待所有 async _checkMilestone 完成
    await flushPromises()
    expect(events.some(e => e.event === 'badge_earned' && e.badge.id === 'first_session')).toBe(true)
  })

  test('confirmBreak 后解锁 first_break', async () => {
    const events = []
    SessionStore.onEvent(e => events.push(e))
    SessionStore.confirmBreak()
    await flushPromises()
    expect(events.some(e => e.event === 'badge_earned' && e.badge.id === 'first_break')).toBe(true)
  })
})
