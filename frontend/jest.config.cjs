module.exports = {
  preset: 'ts-jest',
  testEnvironment: 'jsdom',
  setupFilesAfterEnv: ['<rootDir>/src/setupTests.ts'],
  moduleNameMapper: { '\\.(css|less|scss)$': '<rootDir>/src/styleMock.js' }
}
