const { defineConfig } = require('@playwright/test');

module.exports = defineConfig({
  testDir: '.',
  testMatch: '*.spec.js',
  workers: 1,
  timeout: 30000,
  expect: { timeout: 2000 },
  use: {
    baseURL: 'http://127.0.0.1:8765',
    permissions: ['camera'],
    launchOptions: {
      args: ['--use-fake-device-for-media-stream', '--use-fake-ui-for-media-stream'],
    },
  },
  webServer: {
    command: 'uv run --python 3.15.0 python serve.py',
    cwd: '.',
    url: 'http://127.0.0.1:8765',
    reuseExistingServer: false,
    timeout: 120000,
  },
});
