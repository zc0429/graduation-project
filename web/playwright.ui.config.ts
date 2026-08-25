import { defineConfig, devices } from '@playwright/test'

const baseURL = 'http://127.0.0.1:4174'

export default defineConfig({
  testDir: './e2e/smoke',
  fullyParallel: false,
  workers: 1,
  timeout: 30_000,
  expect: {
    timeout: 10_000,
  },
  reporter: 'line',
  outputDir: 'test-results/ui-smoke',
  use: {
    baseURL,
    actionTimeout: 10_000,
    navigationTimeout: 20_000,
    colorScheme: 'light',
    trace: 'retain-on-failure',
    screenshot: 'only-on-failure',
    video: 'off',
  },
  webServer: {
    command: 'npm run dev -- --host 127.0.0.1 --port 4174 --strictPort',
    url: baseURL,
    reuseExistingServer: false,
    timeout: 120_000,
  },
  projects: [
    {
      name: 'chromium-desktop',
      testIgnore: '**/browser-smoke.spec.ts',
      use: {
        ...devices['Desktop Chrome'],
        viewport: { width: 1600, height: 1200 },
      },
    },
    {
      name: 'chromium-laptop',
      testMatch: '**/responsive.spec.ts',
      use: {
        ...devices['Desktop Chrome'],
        viewport: { width: 1280, height: 800 },
      },
    },
    {
      name: 'chromium-tablet',
      testMatch: '**/responsive.spec.ts',
      use: {
        ...devices['Desktop Chrome'],
        viewport: { width: 820, height: 1180 },
      },
    },
    {
      name: 'chromium-mobile',
      testMatch: '**/responsive.spec.ts',
      use: {
        ...devices['Desktop Chrome'],
        viewport: { width: 390, height: 844 },
      },
    },
    {
      name: 'chrome-stable',
      use: {
        ...devices['Desktop Chrome'],
        channel: 'chrome',
        viewport: { width: 1600, height: 1200 },
      },
    },
    {
      name: 'edge-stable',
      use: {
        ...devices['Desktop Chrome'],
        channel: 'msedge',
        viewport: { width: 1600, height: 1200 },
      },
    },
    {
      name: 'firefox-smoke',
      testMatch: '**/browser-smoke.spec.ts',
      use: {
        ...devices['Desktop Firefox'],
        viewport: { width: 1600, height: 1200 },
      },
    },
  ],
})
