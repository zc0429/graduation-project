import { defineConfig, devices } from '@playwright/test'

const enabled = process.env.RUN_REAL_AI_E2E?.toLowerCase() === 'true'
const baseURL = process.env.PLAYWRIGHT_REAL_AI_BASE_URL || 'http://127.0.0.1:4177'

export default defineConfig({
  testDir: './e2e/real-ai',
  fullyParallel: false,
  workers: 1,
  timeout: 15 * 60_000,
  expect: {
    timeout: 120_000,
  },
  reporter: 'line',
  outputDir: 'test-results/real-ai',
  use: {
    ...devices['Desktop Chrome'],
    baseURL,
    viewport: { width: 1600, height: 1200 },
    actionTimeout: 30_000,
    navigationTimeout: 45_000,
    colorScheme: 'light',
    trace: 'retain-on-failure',
    screenshot: 'only-on-failure',
    video: 'off',
  },
  webServer: enabled ? {
    command: 'npm run dev -- --host 127.0.0.1 --port 4177 --strictPort',
    url: baseURL,
    reuseExistingServer: false,
    timeout: 120_000,
  } : undefined,
})
