import { mkdir, writeFile } from 'node:fs/promises'
import path from 'node:path'
import { fileURLToPath } from 'node:url'
import {
  expect,
  test,
  type APIRequestContext,
  type Page,
} from '@playwright/test'

type JsonRecord = Record<string, unknown>

interface RestEnvelope<T> {
  code: number
  message: string
  data: T
}

interface Session {
  token: string
  user: { id: number; username: string; role: string }
}

interface EvidenceQuestion {
  id: number
  userId: number
  subjectId: number
  knowledgePointId?: number
  stem: string
  answer?: string
  source?: string
  difficulty?: number
  mastery: number
}

interface EvidenceAnalysis {
  id: number
  questionId: number
  knowledgePointId?: number
  errorCause?: string
  analysis?: string
  referenceIds?: string
  llmModel?: string
  status: 0 | 1 | 2
}

interface EvidenceVariant {
  id: number
  questionId: number
  stem: string
  answer?: string
  difficulty?: number
}

const enabled = process.env.RUN_REAL_AI_E2E?.toLowerCase() === 'true'
const evidenceUsername = process.env.REAL_AI_E2E_USERNAME || 'glm_evidence_20260826'
const evidencePassword = process.env.REAL_AI_E2E_PASSWORD || ''
const seedPassword = process.env.REAL_AI_E2E_SEED_PASSWORD || ''
const evidenceTag = process.env.REAL_AI_E2E_TAG || 'real-glm-evidence-20260826'
const evidenceNickname = '真实 GLM 演示学生'
const expectedModel = 'glm-4.7-flash'
const modelGapMs = Math.max(0, Number(process.env.REAL_AI_E2E_MODEL_GAP_MS || 90_000))
const reuseEvidence = process.env.REAL_AI_E2E_REUSE?.toLowerCase() === 'true'
const screenshotDir = fileURLToPath(
  new URL('../../../docs/thesis/screenshots/real-glm/', import.meta.url),
)
const runtimeResultDir = fileURLToPath(new URL('../../test-results/real-ai/', import.meta.url))

const referenceInputs = [
  {
    stem: '已知二次函数 y=x²-4x+3，求它的顶点坐标、对称轴与最小值。',
    answer: '配方得 y=(x-2)²-1，顶点为 (2,-1)，对称轴为 x=2，最小值为 -1。',
    source: `${evidenceTag}-reference-1`,
  },
]

const targetInput = {
  stem: '已知二次函数 y=x²-6x+5，学生配方后写成 y=(x-3)²+5，并判断顶点为 (3,5)。求正确顶点与最小值，并分析这一步错在哪里。',
  answer: 'y=(x-3)²-4，所以顶点为 (3,-4)，最小值为 -4；错误是配方时遗漏了补入 9 后应减去 9。',
  source: `${evidenceTag}-target`,
}

test.describe('真实 GLM 浏览器业务闭环与论文证据', () => {
  test.skip(!enabled, '仅在显式设置 RUN_REAL_AI_E2E=true 时调用真实模型')

  test('完成真实分析、RAG、相似题、变式、练习与角色页面取证', async ({ page, request }) => {
    expect(evidencePassword, '必须通过 REAL_AI_E2E_PASSWORD 注入演示学生密码').not.toBe('')
    expect(seedPassword, '必须通过 REAL_AI_E2E_SEED_PASSWORD 注入种子角色密码').not.toBe('')

    await assertBackendReady(request)
    await mkdir(screenshotDir, { recursive: true })
    await mkdir(runtimeResultDir, { recursive: true })

    await page.goto('/login')
    await expect(page.getByRole('heading', { name: '回到学习桌' })).toBeVisible()
    await capture(page, '01-login.png')

    await ensureEvidenceAccount(request)
    const studentSession = await login(page, evidenceUsername, evidencePassword)
    expect(studentSession.user.role).toBe('student')

    const subjects = await apiCall<JsonRecord[]>(request, '/api/subject/list', studentSession.token)
    const math = subjects.find((item) => item.name === '数学')
    expect(math, '正式环境必须存在数学科目').toBeTruthy()
    const mathSubjectId = Number(math!.id)

    const references: EvidenceQuestion[] = []
    for (const input of referenceInputs) {
      const question = await ensureQuestion(request, studentSession, mathSubjectId, input)
      await ensureRealAnalysis(request, studentSession, question.id)
      references.push(await getQuestion(request, studentSession.token, question.id))
      await page.waitForTimeout(modelGapMs)
    }

    let target = await findQuestionBySource(request, studentSession.token, targetInput.source)
    await page.goto('/question/create')
    await expect(page.getByRole('heading', { name: '录入一道值得重做的题' })).toBeVisible()
    await page.getByLabel('科目').click()
    await page.getByRole('option', { name: '数学' }).click()
    await page.getByLabel('来源（选填）').fill(targetInput.source)
    await page.getByRole('textbox', { name: '题干', exact: true }).fill(targetInput.stem)
    await page.getByLabel('正确答案或订正（选填）').fill(targetInput.answer)
    await capture(page, '03-question-create.png')

    if (!target) {
      await page.getByRole('button', { name: '保存并启动解析' }).click()
      await expect(page).toHaveURL(/\/question\/\d+$/)
      const targetId = Number(new URL(page.url()).pathname.split('/').at(-1))
      target = await getQuestion(request, studentSession.token, targetId)
    } else {
      await page.goto(`/question/${target.id}`)
    }

    const analysis = await ensureRealAnalysis(request, studentSession, target.id, !reuseEvidence)
    target = await getQuestion(request, studentSession.token, target.id)
    assertRealAnalysis(target, analysis)

    const knowledgeTree = await apiCall<JsonRecord[]>(
      request,
      `/api/knowledge-point/tree?subjectId=${mathSubjectId}`,
      studentSession.token,
    )
    expect(collectKnowledgeIds(knowledgeTree)).toContain(analysis.knowledgePointId)

    const referenceIds = parsePositiveIds(analysis.referenceIds)
    expect(referenceIds.length, 'RAG 至少应命中一条同账号参考题').toBeGreaterThan(0)
    const referencedQuestions = await Promise.all(
      referenceIds.map((id) => getQuestion(request, studentSession.token, id)),
    )
    expect(referencedQuestions.every((item) => item.userId === studentSession.user.id)).toBe(true)
    expect(referencedQuestions.every((item) => item.id !== target!.id)).toBe(true)
    expect(referenceIds.every((id) => references.some((item) => item.id === id))).toBe(true)

    await page.goto('/')
    await expect(page.getByRole('heading', { name: /先把今天的两件事做好/ })).toBeVisible()
    await capture(page, '02-student-home.png')

    await page.goto('/question/list')
    await expect(page.getByText(targetInput.stem, { exact: true })).toBeVisible()
    await capture(page, '04-question-list.png')

    await page.goto(`/question/${target.id}`)
    await expect(page.getByText('已完成', { exact: true })).toBeVisible()
    await expect(page.getByText(expectedModel, { exact: true })).toBeVisible()

    await page.getByRole('tab', { name: 'RAG 参考' }).click()
    for (const referenceId of referenceIds) {
      await expect(page.getByText(`参考题 ID ${referenceId}`, { exact: true })).toBeVisible()
    }
    await capture(page, '06-rag-references.png')

    await page.getByRole('tab', { name: /相似题/ }).click()
    await expect(page.locator('.similar-list button').first()).toBeVisible()
    const similar = await apiCall<EvidenceQuestion[]>(
      request,
      `/api/recommend/similar?questionId=${target.id}`,
      studentSession.token,
    )
    expect(similar.length).toBeGreaterThan(0)
    expect(similar.every((item) => item.userId === studentSession.user.id)).toBe(true)
    expect(similar.every((item) => item.id !== target!.id)).toBe(true)
    await capture(page, '07-similar-questions.png')

    await page.getByRole('tab', { name: /AI 变式题/ }).click()
    await page.waitForTimeout(modelGapMs)
    const existingVariants = await apiCall<EvidenceVariant[]>(
      request,
      `/api/variant/list?questionId=${target.id}`,
      studentSession.token,
    )
    let generated: EvidenceVariant[]
    if (reuseEvidence && existingVariants.length >= 3) {
      generated = existingVariants.slice(-3)
    } else {
      const generationResponse = page.waitForResponse((response) => (
        response.url().includes(`/api/variant/generate/${target!.id}`)
        && response.request().method() === 'POST'
      ))
      await page.getByRole('button', { name: '生成变式题' }).click()
      const generatedEnvelope = await (await generationResponse).json() as RestEnvelope<EvidenceVariant[]>
      expect(generatedEnvelope.code).toBe(0)
      generated = generatedEnvelope.data
    }
    assertVariants(generated, target.id)
    await expect(page.locator('.variant-list article')).toHaveCount(
      reuseEvidence ? existingVariants.length : existingVariants.length + 3,
    )
    const storedVariants = await apiCall<EvidenceVariant[]>(
      request,
      `/api/variant/list?questionId=${target.id}`,
      studentSession.token,
    )
    expect(storedVariants.map((item) => item.id)).toEqual(expect.arrayContaining(generated.map((item) => item.id)))
    await capture(page, '08-variants.png')

    const masteryBefore = reuseEvidence ? Math.max(0, target.mastery - 15) : target.mastery
    if (!reuseEvidence) {
      const generatedCard = page.locator('.variant-list article').nth(existingVariants.length)
      await generatedCard.getByRole('button', { name: '作答并记录' }).click()
      const practiceDialog = page.getByRole('dialog', { name: /作答变式/ })
      await practiceDialog.getByLabel('我的作答').fill('先完成配方，再检查常数项并回代验证。')
      await practiceDialog.getByText('答对了', { exact: true }).click()
      await practiceDialog.getByLabel('用时（秒，可选）').fill('86')
      await practiceDialog.getByRole('button', { name: '提交练习记录' }).click()
      await expect(practiceDialog).toBeHidden()
    }

    target = await getQuestion(request, studentSession.token, target.id)
    const masteryAfter = target.mastery
    expect(masteryAfter).toBe(Math.min(100, masteryBefore + 15))
    const practicePage = await apiCall<{ records: JsonRecord[] }>(
      request,
      '/api/practice/page?pageNum=1&pageSize=10',
      studentSession.token,
    )
    const practiceRecord = practicePage.records.find((item) => Number(item.variantId) === generated[0].id)
    expect(practiceRecord).toMatchObject({ isCorrect: 1 })

    await page.getByRole('tab', { name: 'AI 智能解析' }).click()
    await expect(page.getByText(`${masteryAfter}%`, { exact: true })).toBeVisible()
    await capture(page, '05-question-detail-glm.png')

    await page.goto('/review')
    await expect(page.getByRole('heading', { name: '复习计划工作台' })).toBeVisible()
    const duePlans = await apiCall<JsonRecord[]>(request, '/api/review-plan/today', studentSession.token)
    await capture(page, '09-review-plan.png')

    await page.goto('/report')
    await expect(page.getByRole('heading', { name: '学情报告' })).toBeVisible()
    await expect(page.getByText('知识点掌握度', { exact: true })).toBeVisible()
    await capture(page, '10-student-report.png')

    await logout(page)
    await login(page, 'teacher', seedPassword)
    await page.goto('/report')
    await expect(page.getByRole('heading', { name: '学情报告' })).toBeVisible()
    await capture(page, '11-teacher-report.png')

    await logout(page)
    await login(page, 'admin', seedPassword)
    await page.goto('/admin/user')
    await expect(page.getByRole('heading', { name: '用户管理' })).toBeVisible()
    await expect(page.getByRole('strong').filter({ hasText: evidenceUsername })).toBeVisible()
    await capture(page, '12-admin-users.png')

    const screenshots = [
      '01-login.png',
      '02-student-home.png',
      '03-question-create.png',
      '04-question-list.png',
      '05-question-detail-glm.png',
      '06-rag-references.png',
      '07-similar-questions.png',
      '08-variants.png',
      '09-review-plan.png',
      '10-student-report.png',
      '11-teacher-report.png',
      '12-admin-users.png',
    ]
    const summary = {
      executedAt: new Date().toISOString(),
      provider: 'glm',
      chatModel: expectedModel,
      embeddingModel: 'embedding-3',
      embeddingDimensions: 1024,
      accountType: 'isolated-formal-evidence-student',
      accountDataRetained: true,
      reusedExistingEvidence: reuseEvidence,
      questionId: target.id,
      analysis: {
        status: analysis.status,
        errorCauseChinese: containsChinese(analysis.errorCause),
        analysisChinese: containsChinese(analysis.analysis),
        knowledgePointId: analysis.knowledgePointId,
        difficulty: target.difficulty,
        llmModel: analysis.llmModel,
        embeddingExposedToBrowser: false,
        embeddingVerification: 'database-audit-required',
      },
      rag: {
        referenceIds,
        allOwnedByEvidenceStudent: referencedQuestions.every((item) => item.userId === studentSession.user.id),
      },
      similar: {
        questionIds: similar.map((item) => item.id),
        allOwnedByEvidenceStudent: similar.every((item) => item.userId === studentSession.user.id),
      },
      variants: {
        generatedCount: generated.length,
        generatedIds: generated.map((item) => item.id),
        databaseReadback: generated.every((item) => storedVariants.some((stored) => stored.id === item.id)),
      },
      practice: {
        recordId: Number(practiceRecord?.id),
        isCorrect: Number(practiceRecord?.isCorrect),
        masteryBefore,
        masteryAfter,
      },
      review: {
        duePlanCount: duePlans.length,
        note: duePlans.length ? '页面展示到期或逾期计划' : '新建正式证据数据的首个复习节点尚未到期',
      },
      screenshots,
    }
    await writeFile(
      path.join(runtimeResultDir, 'summary.json'),
      `${JSON.stringify(summary, null, 2)}\n`,
      'utf8',
    )
  })
})

async function assertBackendReady(request: APIRequestContext) {
  const response = await request.get('/api/health')
  expect(response.ok(), '真实 GLM 后端必须先在 8080 端口启动').toBe(true)
}

async function ensureEvidenceAccount(request: APIRequestContext) {
  const response = await request.post('/api/auth/register', {
    data: {
      username: evidenceUsername,
      password: evidencePassword,
      nickname: evidenceNickname,
    },
  })
  expect(response.ok()).toBe(true)
  const body = await response.json() as RestEnvelope<number | null>
  if (body.code !== 0 && body.message !== '用户名已存在') {
    throw new Error(`演示学生账号准备失败：${body.message}`)
  }
}

async function login(page: Page, username: string, password: string): Promise<Session> {
  await page.goto('/login')
  await page.getByLabel('用户名').fill(username)
  await page.getByLabel('密码', { exact: true }).fill(password)
  await page.getByRole('button', { name: '进入知错工作台' }).click()
  await expect(page).toHaveURL(/\/$/)
  return page.evaluate(() => {
    const token = localStorage.getItem('token') || ''
    const user = JSON.parse(localStorage.getItem('user') || '{}') as Session['user']
    return { token, user }
  })
}

async function logout(page: Page) {
  await page.evaluate(() => {
    localStorage.removeItem('token')
    localStorage.removeItem('user')
  })
}

async function apiCall<T>(
  request: APIRequestContext,
  url: string,
  token: string,
  options: { method?: 'GET' | 'POST'; data?: unknown } = {},
): Promise<T> {
  const response = await request.fetch(url, {
    method: options.method || 'GET',
    data: options.data,
    headers: { Authorization: `Bearer ${token}` },
  })
  expect(response.ok(), `${options.method || 'GET'} ${url} 应返回 HTTP 2xx`).toBe(true)
  const body = await response.json() as RestEnvelope<T>
  if (body.code !== 0) throw new Error(`${options.method || 'GET'} ${url} 失败：${body.message}`)
  return body.data
}

async function findQuestionBySource(request: APIRequestContext, token: string, source: string) {
  const page = await apiCall<{ records: EvidenceQuestion[] }>(
    request,
    '/api/question/page?pageNum=1&pageSize=100',
    token,
  )
  return page.records.find((item) => item.source === source)
}

async function ensureQuestion(
  request: APIRequestContext,
  session: Session,
  subjectId: number,
  input: { stem: string; answer: string; source: string },
) {
  const existing = await findQuestionBySource(request, session.token, input.source)
  if (existing) return existing
  const id = await apiCall<number>(request, '/api/question', session.token, {
    method: 'POST',
    data: { subjectId, ...input },
  })
  return getQuestion(request, session.token, id)
}

async function getQuestion(request: APIRequestContext, token: string, id: number) {
  return apiCall<EvidenceQuestion>(request, `/api/question/${id}`, token)
}

async function ensureRealAnalysis(
  request: APIRequestContext,
  session: Session,
  questionId: number,
  force = false,
) {
  const existing = await apiCall<EvidenceAnalysis | null>(
    request,
    `/api/ai/analysis/${questionId}`,
    session.token,
  )
  if (!force && existing?.status === 1 && existing.llmModel === expectedModel) {
    return existing
  }
  await apiCall<null>(request, `/api/ai/analyze/${questionId}`, session.token, { method: 'POST' })
  return waitForAnalysis(request, session.token, questionId)
}

async function waitForAnalysis(request: APIRequestContext, token: string, questionId: number) {
  const deadline = Date.now() + 4 * 60_000
  while (Date.now() < deadline) {
    const analysis = await apiCall<EvidenceAnalysis | null>(
      request,
      `/api/ai/analysis/${questionId}`,
      token,
    )
    if (analysis?.status === 1) return analysis
    if (analysis?.status === 2) throw new Error(`错题 ${questionId} 的真实 GLM 分析失败`)
    await new Promise((resolve) => setTimeout(resolve, 2_000))
  }
  throw new Error(`错题 ${questionId} 的真实 GLM 分析在 4 分钟内未完成`)
}

function assertRealAnalysis(question: EvidenceQuestion, analysis: EvidenceAnalysis) {
  expect(analysis.status).toBe(1)
  expect(containsChinese(analysis.errorCause)).toBe(true)
  expect(containsChinese(analysis.analysis)).toBe(true)
  expect(Number.isSafeInteger(analysis.knowledgePointId) && Number(analysis.knowledgePointId) > 0).toBe(true)
  expect(Number.isInteger(question.difficulty) && Number(question.difficulty) >= 1 && Number(question.difficulty) <= 5).toBe(true)
  expect(analysis.llmModel).toBe(expectedModel)
}

function assertVariants(variants: EvidenceVariant[], questionId: number) {
  expect(variants).toHaveLength(3)
  for (const variant of variants) {
    expect(variant.questionId).toBe(questionId)
    expect(variant.stem.trim().length).toBeGreaterThan(0)
    expect((variant.answer || '').trim().length).toBeGreaterThan(0)
    expect(Number.isInteger(variant.difficulty) && Number(variant.difficulty) >= 1 && Number(variant.difficulty) <= 5).toBe(true)
  }
}

function containsChinese(value: unknown) {
  return typeof value === 'string' && /[\u3400-\u9fff]/u.test(value) && value.trim().length >= 4
}

function parsePositiveIds(value?: string) {
  try {
    const parsed = JSON.parse(value || '[]')
    if (!Array.isArray(parsed)) return []
    return parsed.map(Number).filter((id) => Number.isSafeInteger(id) && id > 0)
  } catch {
    return []
  }
}

function collectKnowledgeIds(nodes: JsonRecord[]): number[] {
  return nodes.flatMap((node) => [
    Number(node.id),
    ...collectKnowledgeIds((node.children as JsonRecord[] | undefined) || []),
  ])
}

async function capture(page: Page, filename: string) {
  await page.locator('.el-loading-mask:visible').waitFor({ state: 'detached' }).catch(() => undefined)
  await page.waitForTimeout(400)
  await page.screenshot({
    path: path.join(screenshotDir, filename),
    animations: 'disabled',
    caret: 'hide',
    fullPage: true,
  })
}
