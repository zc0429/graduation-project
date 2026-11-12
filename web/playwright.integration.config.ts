import { defineConfig, devices } from '@playwright/test'

const baseURL = 'http://127.0.0.1:4175'

export default defineConfig({
  testDir: './e2e/integration',
  fullyParallel: false,
  workers: 1,
  timeout: 60_000,
  expect: {
    timeout: 12_000,
  },
  reporter: 'line',
  outputDir: 'test-results/integration',
  use: {
    launchOptions: process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE ? { executablePath: process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE } : {},
    ...devices['Desktop Chrome'],
    baseURL,
    viewport: { width: 1440, height: 1000 },
    actionTimeout: 12_000,
    navigationTimeout: 25_000,
    colorScheme: 'light',
    trace: 'retain-on-failure',
    screenshot: 'only-on-failure',
    video: 'off',
  },
  webServer: {
    command: 'npm run dev -- --host 127.0.0.1 --port 4175 --strictPort',
    url: baseURL,
    reuseExistingServer: false,
    timeout: 120_000,
  },
})
