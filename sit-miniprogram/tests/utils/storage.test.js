// tests/utils/storage.test.js
const wxMock = require('../__mocks__/wx')
global.wx = wxMock

const { storage } = require('miniprogram/utils/storage')

beforeEach(() => wxMock.__resetStore())

describe('storage.get / storage.set', () => {
  test('set 后 get 取回相同值', async () => {
    await storage.set('testKey', { foo: 42 })
    const val = await storage.get('testKey')
    expect(val).toEqual({ foo: 42 })
  })

  test('get 不存在的 key 返回 null', async () => {
    const val = await storage.get('nonexistent')
    expect(val).toBeNull()
  })
})

describe('storage.append', () => {
  const today = '2026-06-16'

  test('首次 append 新增记录', async () => {
    await storage.append({ date: today, goodSecs: 100 })
    const sessions = await storage.get('sessions')
    expect(sessions).toHaveLength(1)
    expect(sessions[0]).toMatchObject({ date: today, goodSecs: 100 })
  })

  test('同日 append 合并而非重复插入', async () => {
    await storage.append({ date: today, goodSecs: 100 })
    await storage.append({ date: today, goodSecs: 200, hunchSecs: 10 })
    const sessions = await storage.get('sessions')
    expect(sessions).toHaveLength(1)
    expect(sessions[0]).toMatchObject({ goodSecs: 200, hunchSecs: 10 })
  })

  test('超过 90 条时截断到最近 90 条', async () => {
    const existing = Array.from({ length: 90 }, (_, i) => ({
      date: `2025-01-${String(i + 1).padStart(2, '0')}`,
      goodSecs: i,
    }))
    await storage.set('sessions', existing)
    await storage.append({ date: '2026-06-16', goodSecs: 999 })
    const sessions = await storage.get('sessions')
    expect(sessions).toHaveLength(90)
    expect(sessions[sessions.length - 1].goodSecs).toBe(999)
  })
})
