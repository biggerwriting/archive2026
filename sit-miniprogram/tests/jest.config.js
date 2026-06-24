// tests/jest.config.js
module.exports = {
  testEnvironment: 'node',
  moduleNameMapper: {
    '^wx$': '<rootDir>/__mocks__/wx.js',
  },
  // 让 tests/ 里的文件可以 require('../miniprogram/...')
  modulePaths: ['<rootDir>/..'],
  transform: {
    '^.+\\.js$': 'babel-jest',
  },
}
