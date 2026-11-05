import { expect, installMockSession, test, type MockRole } from './ui.fixture'

const cases: { role: MockRole; width: number; height: number; collapsed?: boolean }[] = [
  { role: 'admin', width: 1912, height: 948 },
  { role: 'student', width: 1912, height: 948 },
  { role: 'teacher', width: 1912, height: 948 },
  { role: 'admin', width: 1366, height: 600 },
  { role: 'admin', width: 1366, height: 420 },
  { role: 'admin', width: 1024, height: 768 },
  { role: 'admin', width: 390, height: 844 },
  { role: 'admin', width: 1912, height: 948, collapsed: true },
]

for (const scenario of cases) {
  test(`sidebar hover ${scenario.role} ${scenario.width}x${scenario.height}${scenario.collapsed ? ' collapsed' : ''}`, async ({ page }, testInfo) => {
    await page.setViewportSize({ width: scenario.width, height: scenario.height })
    await installMockSession(page, scenario.role)
    await page.goto('/')
    await expect(page.getByRole('heading').first()).toBeVisible()
    const sidebar = page.getByRole('complementary', { name: '主导航' })
    if (scenario.width <= 700) {
      await expect(sidebar).toBeHidden()
      await page.screenshot({ path: testInfo.outputPath('mobile.png') })
      return
    }
    await expect(sidebar).toBeVisible()
    if (scenario.collapsed) {
      await page.getByRole('button', { name: '折叠侧边导航' }).click()
      await expect(sidebar).toHaveCSS('width', '84px')
    }
    const nav = page.getByRole('navigation', { name: '功能目录' })
    for (const link of await nav.getByRole('link').all()) {
      await page.mouse.move(600, 100)
      const before = await link.boundingBox()
      await link.hover()
      const samples = await link.evaluate(async (element) => {
        const container = element.closest('nav')!
        const frames = []
        for (let frame = 0; frame < 15; frame++) {
          await new Promise<void>((resolve) => requestAnimationFrame(() => resolve()))
          frames.push({
            overflow: container.scrollWidth - container.clientWidth,
            height: container.clientHeight,
            x: element.getBoundingClientRect().x,
          })
        }
        return frames
      })
      expect(Math.max(...samples.map((sample) => sample.overflow)), 'hover must not create a horizontal scrollbar').toBeLessThanOrEqual(0)
      expect(Math.max(...samples.map((sample) => Math.abs(sample.x - before!.x))), 'hover target must stay under the pointer').toBeLessThanOrEqual(0.5)
      expect(new Set(samples.map((sample) => sample.height)).size, 'navigation height must not oscillate').toBe(1)
    }
    await nav.getByRole('link', { name: '个人中心' }).hover()
    const profile = await nav.getByRole('link', { name: '个人中心' }).boundingBox()
    const bounds = await nav.boundingBox()
    expect(profile!.y).toBeGreaterThanOrEqual(bounds!.y)
    expect(profile!.y + profile!.height).toBeLessThanOrEqual(bounds!.y + bounds!.height + 1)
    if (scenario.role === 'admin' && scenario.width === 1912 && !scenario.collapsed) {
      await page.screenshot({ path: testInfo.outputPath('desktop.png') })
    }
  })
}
