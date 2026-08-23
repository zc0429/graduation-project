import { defineConfig, devices } from '@playwright/test'

export default defineConfig({
  testDir: './e2e',
  fullyParallel: false,
  workers: 1,
  timeout: 240_000,
  expect: {
    timeout: 15_000,
  },
  reporter: 'line',
  outputDir: 'test-results',
  use: {
    baseURL: process.env.PLAYWRIGHT_BASE_URL || 'http://localhost:5173',
    actionTimeout: 15_000,
    navigationTimeout: 30_000,
    viewport: { width: 1600, height: 1200 },
    trace: 'retain-on-failure',
  },
  projects: [
    {
      name: 'chromium',
      use: {
        ...devices['Desktop Chrome'],
        viewport: { width: 1600, height: 1200 },
      },
    },
  ],
})
