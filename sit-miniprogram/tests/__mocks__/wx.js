// tests/__mocks__/wx.js
const store = {}

const wx = {
  getStorageSync: jest.fn((key) => store[key] ?? null),
  setStorageSync: jest.fn((key, val) => { store[key] = val }),
  getStorage: jest.fn(({ key, success, fail }) => {
    try { success({ data: store[key] ?? null }) } catch(e) { fail && fail(e) }
  }),
  setStorage: jest.fn(({ key, data, success, fail }) => {
    try { store[key] = data; success && success() } catch(e) { fail && fail(e) }
  }),
  textToSpeech: jest.fn(({ success }) => {
    success && success({ filename: '/tmp/tts_mock.mp3' })
  }),
  vibrateShort:  jest.fn(),
  vibrateLong:   jest.fn(),
  createInnerAudioContext: jest.fn(() => ({
    src:        '',
    play:       jest.fn(),
    stop:       jest.fn(),
    destroy:    jest.fn(),
  })),
  createVKSession: jest.fn(),
  // 测试间重置 store
  __resetStore: () => Object.keys(store).forEach(k => delete store[k]),
}

global.wx = wx
module.exports = wx
