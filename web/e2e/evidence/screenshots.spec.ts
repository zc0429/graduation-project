import { mkdir } from 'node:fs/promises'
import path from 'node:path'
import { fileURLToPath } from 'node:url'
import type { Page } from '@playwright/test'
import { installMockSession, test, type MockRole } from '../smoke/ui.fixture'

type EvidenceTarget = 'desktop' | 'tablet' | 'mobile'

interface EvidenceCase {
  target: EvidenceTarget
  filename: string
  route: string
  role?: MockRole
}

const outputDir = fileURLToPath(
  new URL('../../../docs/design/vue-rebuild-screenshots/', import.meta.url),
)

const evidenceCases: EvidenceCase[] = [
  { target: 'desktop', filename: 'desktop-1600x1200-01-login.png', route: '/login' },
  { target: 'desktop', filename: 'desktop-1600x1200-02-student-home.png', route: '/', role: 'student' },
  {
    target: 'desktop',
    filename: 'desktop-1600x1200-03-question-detail.png',
    route: '/question/201',
    role: 'student',
  },
  { target: 'desktop', filename: 'desktop-1600x1200-04-teacher-report.png', route: '/report', role: 'teacher' },
  { target: 'desktop', filename: 'desktop-1600x1200-05-admin-users.png', route: '/admin/user', role: 'admin' },
  { target: 'tablet', filename: 'tablet-820x1180-01-student-home.png', route: '/', role: 'student' },
  {
    target: 'tablet',
    filename: 'tablet-820x1180-02-question-detail.png',
    route: '/question/201',
    role: 'student',
  },
  { target: 'mobile', filename: 'mobile-390x844-01-login.png', route: '/login' },
  { target: 'mobile', filename: 'mobile-390x844-02-student-home.png', route: '/', role: 'student' },
  {
    target: 'mobile',
    filename: 'mobile-390x844-03-question-detail.png',
    route: '/question/201',
    role: 'student',
  },
]

async function markAsMockEvidence(page: Page) {
  await page.evaluate(() => {
    const badge = document.createElement('div')
    badge.setAttribute('data-testid', 'mock-evidence-badge')
    badge.setAttribute('role', 'note')
    badge.textContent = 'Mock 演示数据 · 非真实 GLM 证据'
    Object.assign(badge.style, {
      position: 'fixed',
      left: '16px',
      bottom: '76px',
      zIndex: '99999',
      maxWidth: 'calc(100vw - 32px)',
      padding: '8px 12px',
      border: '1px solid #9b2f2f',
      borderRadius: '999px',
      background: 'rgba(255, 249, 238, 0.96)',
      color: '#7f2222',
      font: '600 13px/1.35 system-ui, sans-serif',
      letterSpacing: '0.02em',
      boxShadow: '0 6px 20px rgba(48, 38, 28, 0.16)',
      pointerEvents: 'none',
    })
    document.body.appendChild(badge)
  })
}

for (const evidence of evidenceCases) {
  test(`${evidence.target}：${evidence.filename}`, async ({ page }, testInfo) => {
    test.skip(testInfo.project.name !== `evidence-${evidence.target}`)

    await mkdir(outputDir, { recursive: true })
    if (evidence.role) await installMockSession(page, evidence.role)

    await page.goto(evidence.route)
    await page.locator('h1').first().waitFor({ state: 'visible' })
    await page.locator('.el-loading-mask:visible').waitFor({ state: 'detached' }).catch(() => undefined)
    await page.waitForTimeout(500)
    await markAsMockEvidence(page)

    await page.screenshot({
      path: path.join(outputDir, evidence.filename),
      animations: 'disabled',
      caret: 'hide',
      fullPage: true,
    })
  })
}
