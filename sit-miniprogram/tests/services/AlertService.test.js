// tests/services/AlertService.test.js
const wxMock = require('../__mocks__/wx')
global.wx = wxMock

jest.useFakeTimers()

const AlertService = require('miniprogram/services/AlertService').default

const mockAudio = { src: '', play: jest.fn(), stop: jest.fn(), destroy: jest.fn() }
wxMock.createInnerAudioContext.mockReturnValue(mockAudio)

beforeEach(() => {
  AlertService._reset()
  jest.clearAllMocks()
  mockAudio.play.mockClear()
  mockAudio.stop.mockClear()
  wxMock.vibrateShort.mockClear()
  wxMock.vibrateLong.mockClear()
})

describe('voice 模式', () => {
  test('fire(posture_bad) 播放对应音频（TTS）', () => {
    AlertService.setMode('voice')
    AlertService.fire('posture_bad')
    // TTS mock returns filename '/tmp/tts_mock.mp3' via success callback
    expect(mockAudio.src).toBe('/tmp/tts_mock.mp3')
    expect(mockAudio.play).toHaveBeenCalledTimes(1)
  })

  test('防抖：30 秒内同类型提醒只播放一次', () => {
    AlertService.setMode('voice')
    AlertService.fire('posture_bad')
    AlertService.fire('posture_bad')
    expect(mockAudio.play).toHaveBeenCalledTimes(1)
  })

  test('防抖过期后可再次播放', () => {
    AlertService.setMode('voice')
    AlertService.fire('posture_bad')
    AlertService._lastAlertAt['posture_bad'] -= 31 * 1000
    AlertService.fire('posture_bad')
    expect(mockAudio.play).toHaveBeenCalledTimes(2)
  })
})

describe('vibration 模式', () => {
  test('fire(posture_bad) 调用 vibrateShort', () => {
    AlertService.setMode('vibration')
    AlertService.fire('posture_bad')
    expect(wxMock.vibrateShort).toHaveBeenCalled()
  })

  test('fire(take_break) 调用 vibrateLong', () => {
    AlertService.setMode('vibration')
    AlertService.fire('take_break')
    expect(wxMock.vibrateLong).toHaveBeenCalledTimes(1)
  })
})

describe('silent 模式', () => {
  test('fire 不触发任何 wx 调用', () => {
    AlertService.setMode('silent')
    AlertService.fire('posture_bad')
    expect(mockAudio.play).not.toHaveBeenCalled()
    expect(wxMock.vibrateShort).not.toHaveBeenCalled()
  })
})

describe('无 cooldown 类型', () => {
  test('badge_earned 无防抖，可连续触发', () => {
    AlertService.setMode('voice')
    AlertService.fire('badge_earned')
    AlertService.fire('badge_earned')
    expect(mockAudio.play).toHaveBeenCalledTimes(2)
  })
})
