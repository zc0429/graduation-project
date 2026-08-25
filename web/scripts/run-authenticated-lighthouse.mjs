import path from 'node:path'
import { mkdirSync } from 'node:fs'
import { chromium } from 'playwright'
import { launch } from 'chrome-launcher'
import lighthouse from 'lighthouse'
import desktopConfig from 'lighthouse/core/config/desktop-config.js'

const baseURL = process.env.LIGHTHOUSE_BASE_URL || 'http://127.0.0.1:4176'
const username = process.env.LIGHTHOUSE_USERNAME
const password = process.env.LIGHTHOUSE_PASSWORD

if (!username || !password) {
  throw new Error('LIGHTHOUSE_USERNAME and LIGHTHOUSE_PASSWORD are required')
}

const userDataDir = path.resolve('test-results', `lighthouse-cdp-${Date.now()}`)
mkdirSync(userDataDir, { recursive: true })

const chrome = await launch({
  chromeFlags: ['--headless=new', '--disable-gpu', '--no-sandbox', '--window-size=1440,1000'],
  userDataDir,
})

let browser
try {
  browser = await chromium.connectOverCDP(`http://127.0.0.1:${chrome.port}`)
  const context = browser.contexts()[0] || await browser.newContext()
  const page = context.pages()[0] || await context.newPage()

  await page.goto(`${baseURL}/login`)
  await page.getByLabel('用户名').fill(username)
  await page.getByLabel('密码', { exact: true }).fill(password)
  await page.getByRole('button', { name: '进入知错工作台' }).click()
  await page.waitForURL(/\/$/)
  await page.waitForLoadState('networkidle')

  const result = await lighthouse(
    `${baseURL}/`,
    { port: chrome.port, output: 'json', logLevel: 'silent' },
    desktopConfig,
  )
  if (!result) throw new Error('Lighthouse returned no result')

  const { lhr } = result
  const summary = {
    finalUrl: lhr.finalDisplayedUrl,
    performance: Math.round((lhr.categories.performance?.score || 0) * 100),
    accessibility: Math.round((lhr.categories.accessibility?.score || 0) * 100),
    fcpMs: Math.round(lhr.audits['first-contentful-paint'].numericValue || 0),
    lcpMs: Math.round(lhr.audits['largest-contentful-paint'].numericValue || 0),
    tbtMs: Math.round(lhr.audits['total-blocking-time'].numericValue || 0),
    cls: lhr.audits['cumulative-layout-shift'].numericValue || 0,
  }
  process.stdout.write(`${JSON.stringify(summary)}\n`)
} finally {
  await browser?.close().catch(() => undefined)
  try {
    chrome.kill()
  } catch {
    // Chrome may already be closed by the CDP connection.
  }
}
