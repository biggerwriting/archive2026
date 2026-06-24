// tests/services/PostureService.test.js
// 只测 analyzePosture 纯函数，不需要 wx mock
const { analyzePosture } = require('miniprogram/services/PostureService')

// 工具：构造关键点数组
function makePoints(headY, lShY, rShY, score = 0.9) {
  // 14 个点，只有 HEAD(0), L_SHOULDER(2), R_SHOULDER(3) 需要真实值
  const pts = Array(14).fill(null).map(() => ({ x: 0.5, y: 0.5, score: 0.9 }))
  pts[0] = { x: 0.5, y: headY,  score }
  pts[2] = { x: 0.4, y: lShY,   score }
  pts[3] = { x: 0.6, y: rShY,   score }
  return pts
}

const THRESHOLD = 0.18  // normal 档

describe('analyzePosture', () => {
  test('端正坐姿：头比肩高出足够距离', () => {
    // shMidY = 0.5, headY = 0.25 → dist = 0.25 > 0.18
    const pts = makePoints(0.25, 0.5, 0.5)
    expect(analyzePosture(pts, THRESHOLD)).toBe('good')
  })

  test('弓腰：头肩距小于阈值', () => {
    // shMidY = 0.5, headY = 0.4 → dist = 0.1 < 0.18
    const pts = makePoints(0.40, 0.5, 0.5)
    expect(analyzePosture(pts, THRESHOLD)).toBe('hunching')
  })

  test('趴着：鼻子低于肩中点', () => {
    // headY = 0.7 > shMidY = 0.5
    const pts = makePoints(0.70, 0.5, 0.5)
    expect(analyzePosture(pts, THRESHOLD)).toBe('lying')
  })

  test('置信度不足返回 unknown', () => {
    const pts = makePoints(0.25, 0.5, 0.5, 0.3)  // score < 0.5
    expect(analyzePosture(pts, THRESHOLD)).toBe('unknown')
  })

  test('关键点缺失返回 unknown', () => {
    expect(analyzePosture([], THRESHOLD)).toBe('unknown')
  })

  test('宽松阈值（0.12）下同样的弓腰姿势判为 good', () => {
    // dist = 0.15，宽松阈值 0.12 → good
    const pts = makePoints(0.35, 0.5, 0.5)
    expect(analyzePosture(pts, 0.12)).toBe('good')
  })

  test('严格阈值（0.24）下中等距离判为 hunching', () => {
    // dist = 0.20，严格阈值 0.24 → hunching
    const pts = makePoints(0.30, 0.5, 0.5)
    expect(analyzePosture(pts, 0.24)).toBe('hunching')
  })
})
