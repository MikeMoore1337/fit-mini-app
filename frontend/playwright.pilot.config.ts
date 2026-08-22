import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: './tests/pilot',
  outputDir: '../.artifacts/tests/playwright-49e',
  fullyParallel: false,
  retries: 0,
  reporter: 'list',
  use: {
    ...devices['Desktop Chrome'],
    baseURL: 'http://127.0.0.1:4174',
    hasTouch: true,
    trace: 'retain-on-failure',
  },
  webServer: {
    command: 'node ./node_modules/vite/bin/vite.js --host 127.0.0.1 --port 4174',
    url: 'http://127.0.0.1:4174/',
    reuseExistingServer: true,
  },
});
