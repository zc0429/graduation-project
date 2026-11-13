import { expect, test as base, type Page, type Route } from '@playwright/test'

export type MockRole = 'student' | 'teacher' | 'admin'

type JsonRecord = Record<string, unknown>

export interface ApiRequestLog {
  method: string
  pathname: string
  search: string
  authorization: string
  body: JsonRecord
}

export interface MockApiState {
  requests: ApiRequestLog[]
  expiredRoles: MockRole[]
  loginError: string
  failNext: Record<string, string>
  recognitionDelayMs: number
  recognitionResult: JsonRecord
  users: JsonRecord[]
  subjects: JsonRecord[]
  knowledgeTree: JsonRecord[]
  questions: JsonRecord[]
  analyses: Record<number, JsonRecord | null>
  analysisPollsRemaining: Record<number, number>
  variants: JsonRecord[]
  reviewPlans: JsonRecord[]
  practices: JsonRecord[]
  messages: JsonRecord[]
  announcements: JsonRecord[]
  report: JsonRecord
  nextQuestionId: number
  nextSubjectId: number
  nextKnowledgeId: number
  nextPracticeId: number
  nextAnnouncementId: number
}

const sessionUsers = {
  student: {
    id: 301,
    username: 'student_ui',
    nickname: '学习者',
    role: 'student',
    className: '软件工程 1 班',
    email: 'student@example.test',
  },
  teacher: {
    id: 302,
    username: 'teacher_ui',
    nickname: '胡老师',
    role: 'teacher',
    email: 'teacher@example.test',
  },
  admin: {
    id: 303,
    username: 'admin_ui',
    nickname: '管理员',
    role: 'admin',
    email: 'admin@example.test',
  },
} satisfies Record<MockRole, JsonRecord>

function defaultState(): MockApiState {
  return {
    requests: [],
    expiredRoles: [],
    loginError: '',
    failNext: {},
    recognitionDelayMs: 0,
    recognitionResult: {
      subjectId: 11,
      subjectName: '数学',
      stem: '已知函数 f(x) = x² - 5x + 6，求方程 f(x) = 0 的解。',
      studentAnswer: 'x = 3',
      source: '高一数学课堂练习',
    },
    users: [
      { ...sessionUsers.admin, createTime: '2026-08-01 09:00:00' },
      { ...sessionUsers.teacher, createTime: '2026-08-02 09:00:00' },
      { ...sessionUsers.student, createTime: '2026-08-03 09:00:00' },
      {
        id: 304,
        username: 'second_student',
        nickname: '待注销学生',
        role: 'student',
        className: '软件工程 2 班',
        createTime: '2026-08-04 09:00:00',
      },
    ],
    subjects: [
      { id: 11, name: '数学', code: 'MATH', sort: 1, createTime: '2026-08-01 08:00:00' },
      { id: 12, name: '英语', code: 'ENGLISH', sort: 2, createTime: '2026-08-01 08:05:00' },
    ],
    knowledgeTree: [
      {
        id: 101,
        subjectId: 11,
        name: '函数',
        children: [
          { id: 102, subjectId: 11, name: '函数单调性', children: [] },
          { id: 103, subjectId: 11, name: '函数零点', children: [] },
        ],
      },
      {
        id: 111,
        subjectId: 12,
        name: '阅读理解',
        children: [{ id: 112, subjectId: 12, name: '主旨判断', children: [] }],
      },
    ],
    questions: [
      {
        id: 201,
        userId: 301,
        subjectId: 11,
        knowledgePointId: 102,
        stem: '已知函数在区间上单调递增，求参数的取值范围。',
        answer: '利用导数在区间内非负建立不等式。',
        source: '期中试卷 · 第 18 题',
        difficulty: 4,
        mastery: 46,
        createTime: '2026-08-20 10:00:00',
        updateTime: '2026-08-20 10:00:00',
      },
      {
        id: 202,
        userId: 301,
        subjectId: 12,
        knowledgePointId: 112,
        stem: '阅读短文并判断作者的主要观点。',
        answer: '作者主张通过证据校正判断。',
        source: '周练 · 阅读 B',
        difficulty: 3,
        mastery: 71,
        createTime: '2026-08-19 15:00:00',
        updateTime: '2026-08-19 15:00:00',
      },
    ],
    analyses: {
      201: {
        id: 501,
        questionId: 201,
        knowledgePointId: 102,
        errorCause: '忽略了区间端点与导数符号的共同约束。',
        analysis: '先求导，再把单调递增转化为导数在目标区间内非负。',
        referenceIds: '[202]',
        llmModel: 'mock-model',
        status: 1,
        createTime: '2026-08-20 10:01:00',
      },
      202: null,
    },
    analysisPollsRemaining: {},
    variants: [
      {
        id: 701,
        questionId: 201,
        stem: '若函数在给定区间单调递减，参数应满足什么条件？',
        answer: '令导数在区间内不大于零并处理端点。',
        difficulty: 4,
        createTime: '2026-08-20 10:02:00',
      },
    ],
    reviewPlans: [
      {
        id: 801,
        questionId: 201,
        reviewStage: 2,
        planDate: '2000-01-01',
        status: 2,
        subjectId: 11,
        stemSummary: '函数单调性与参数范围',
        mastery: 46,
      },
      {
        id: 802,
        questionId: 202,
        reviewStage: 1,
        planDate: '2999-01-01',
        status: 0,
        subjectId: 12,
        stemSummary: '阅读理解主旨判断',
        mastery: 71,
      },
    ],
    practices: [
      {
        id: 901,
        questionId: 201,
        userAnswer: '先求导并讨论最小值。',
        isCorrect: 1,
        duration: 95,
        createTime: '2026-08-21 19:20:00',
      },
      {
        id: 902,
        variantId: 701,
        userAnswer: '符号方向判断错误。',
        isCorrect: 0,
        duration: 80,
        createTime: '2026-08-22 19:20:00',
      },
    ],
    messages: [
      {
        id: 1001,
        type: 'review_remind',
        title: '有 1 道逾期错题待复习',
        content: '建议先重做，再完成本轮复习。',
        isRead: 0,
        createTime: '2026-08-23 08:00:00',
      },
      {
        id: 1002,
        type: 'report',
        title: '本周学情报告已生成',
        content: '可以查看掌握度与薄弱知识点。',
        isRead: 1,
        createTime: '2026-08-22 20:00:00',
      },
    ],
    announcements: [
      {
        id: 1101,
        title: '本周完成错题复盘',
        content: '请在周日之前完成到期复习。',
        publisherId: 303,
        createTime: '2026-08-22 09:00:00',
      },
    ],
    report: {
      weekStart: '2026-08-17',
      newQuestionCount: 3,
      totalQuestionCount: 12,
      reviewFinishedCount: 4,
      reviewTotalCount: 6,
      masteryAvg: 63,
      knowledgeMastery: [
        { knowledgePointId: 102, name: '函数单调性', mastery: 46, questionCount: 5 },
        { knowledgePointId: 112, name: '主旨判断', mastery: 71, questionCount: 3 },
      ],
      weakPoints: [{ knowledgePointId: 102, name: '函数单调性', mastery: 46, questionCount: 5 }],
      dailyNewQuestions: [
        { date: '2026-08-17', count: 0 },
        { date: '2026-08-18', count: 1 },
        { date: '2026-08-19', count: 0 },
        { date: '2026-08-20', count: 2 },
      ],
      dailyPractices: [
        { date: '2026-08-17', count: 1 },
        { date: '2026-08-18', count: 2 },
        { date: '2026-08-19', count: 1 },
        { date: '2026-08-20', count: 3 },
      ],
    },
    nextQuestionId: 203,
    nextSubjectId: 13,
    nextKnowledgeId: 120,
    nextPracticeId: 903,
    nextAnnouncementId: 1102,
  }
}

function bodyRecord(route: Route): JsonRecord {
  try {
    const value = route.request().postDataJSON()
    return value && typeof value === 'object' ? value as JsonRecord : {}
  } catch {
    return {}
  }
}

function numberValue(value: unknown, fallback = 0) {
  const result = Number(value)
  return Number.isFinite(result) ? result : fallback
}

function stringValue(value: unknown) {
  return typeof value === 'string' ? value : ''
}

function roleFromAuthorization(value: string): MockRole | undefined {
  const match = value.match(/^Bearer ui-(student|teacher|admin)-token$/)
  return match?.[1] as MockRole | undefined
}

async function json(route: Route, data: unknown, message = 'UI fixture') {
  await route.fulfill({
    status: 200,
    contentType: 'application/json; charset=utf-8',
    body: JSON.stringify({ code: 0, message, data }),
  })
}

async function jsonError(route: Route, message: string, code = 500) {
  await route.fulfill({
    status: 200,
    contentType: 'application/json; charset=utf-8',
    body: JSON.stringify({ code, message, data: null }),
  })
}

function pageData(records: JsonRecord[], pageNum: number, pageSize: number) {
  const start = (pageNum - 1) * pageSize
  return {
    records: records.slice(start, start + pageSize),
    total: records.length,
    current: pageNum,
    size: pageSize,
    pages: Math.max(1, Math.ceil(records.length / pageSize)),
  }
}

function findKnowledgeNode(nodes: JsonRecord[], id: number): JsonRecord | undefined {
  for (const node of nodes) {
    if (numberValue(node.id) === id) return node
    const found = findKnowledgeNode((node.children as JsonRecord[] | undefined) || [], id)
    if (found) return found
  }
  return undefined
}

function removeKnowledgeNode(nodes: JsonRecord[], id: number): boolean {
  const index = nodes.findIndex((node) => numberValue(node.id) === id)
  if (index >= 0) {
    nodes.splice(index, 1)
    return true
  }
  return nodes.some((node) => removeKnowledgeNode((node.children as JsonRecord[] | undefined) || [], id))
}

async function handleApiRoute(route: Route, state: MockApiState) {
  const request = route.request()
  const url = new URL(request.url())
  const method = request.method()
  const pathname = url.pathname
  const authorization = request.headers().authorization || ''
  const body = bodyRecord(route)
  state.requests.push({ method, pathname, search: url.search, authorization, body })

  const failureKey = `${method} ${pathname}`
  if (state.failNext[failureKey]) {
    const message = state.failNext[failureKey]
    delete state.failNext[failureKey]
    await jsonError(route, message)
    return
  }

  if (pathname === '/api/auth/register' && method === 'POST') {
    if (stringValue(body.username) === 'existing_user') {
      await jsonError(route, '用户名已存在', 409)
      return
    }
    await json(route, 305)
    return
  }

  if (pathname === '/api/auth/login' && method === 'POST') {
    if (state.loginError || stringValue(body.username) === 'bad_user') {
      await jsonError(route, state.loginError || '用户名或密码错误', 401)
      return
    }
    const username = stringValue(body.username)
    const role: MockRole = username.startsWith('teacher')
      ? 'teacher'
      : username.startsWith('admin')
        ? 'admin'
        : 'student'
    await json(route, { token: `ui-${role}-token`, user: sessionUsers[role] })
    return
  }

  const role = roleFromAuthorization(authorization)
  if (!role) {
    await jsonError(route, '登录状态已过期', 401)
    return
  }

  if (pathname === '/api/user/profile' && method === 'GET') {
    if (state.expiredRoles.includes(role)) {
      await jsonError(route, '登录状态已过期', 401)
      return
    }
    await json(route, sessionUsers[role])
    return
  }

  if (pathname === '/api/message/unread-count' && method === 'GET') {
    await json(route, state.messages.filter((item) => numberValue(item.isRead) === 0).length)
    return
  }

  if (pathname === '/api/subject/list' && method === 'GET') {
    await json(route, state.subjects)
    return
  }

  if (pathname === '/api/question-recognition/recognize' && method === 'POST') {
    if (state.recognitionDelayMs > 0) {
      await new Promise((resolve) => setTimeout(resolve, state.recognitionDelayMs))
    }
    await json(route, state.recognitionResult)
    return
  }

  if (pathname === '/api/subject' && method === 'POST') {
    state.subjects.push({
      id: state.nextSubjectId++,
      name: stringValue(body.name),
      code: stringValue(body.code),
      sort: numberValue(body.sort),
      createTime: '2026-08-23 12:00:00',
    })
    await json(route, numberValue(state.subjects.at(-1)?.id))
    return
  }

  const subjectMatch = pathname.match(/^\/api\/subject\/(\d+)$/)
  if (subjectMatch && method === 'PUT') {
    const subject = state.subjects.find((item) => numberValue(item.id) === Number(subjectMatch[1]))
    if (subject) Object.assign(subject, body)
    await json(route, null)
    return
  }

  if (pathname === '/api/knowledge-point/tree' && method === 'GET') {
    const subjectId = numberValue(url.searchParams.get('subjectId'))
    await json(
      route,
      subjectId ? state.knowledgeTree.filter((item) => numberValue(item.subjectId) === subjectId) : state.knowledgeTree,
    )
    return
  }

  if (pathname === '/api/knowledge-point' && method === 'POST') {
    const node: JsonRecord = {
      id: state.nextKnowledgeId++,
      subjectId: numberValue(body.subjectId),
      name: stringValue(body.name),
      children: [],
    }
    const parentId = numberValue(body.parentId)
    if (parentId === 0) state.knowledgeTree.push(node)
    else {
      const parent = findKnowledgeNode(state.knowledgeTree, parentId)
      const children = (parent?.children as JsonRecord[] | undefined) || []
      children.push(node)
      if (parent) parent.children = children
    }
    await json(route, numberValue(node.id))
    return
  }

  const knowledgeMatch = pathname.match(/^\/api\/knowledge-point\/(\d+)$/)
  if (knowledgeMatch && method === 'DELETE') {
    removeKnowledgeNode(state.knowledgeTree, Number(knowledgeMatch[1]))
    await json(route, null)
    return
  }

  if (pathname === '/api/question/page' && method === 'GET') {
    const subjectId = numberValue(url.searchParams.get('subjectId'))
    const knowledgeId = numberValue(url.searchParams.get('knowledgePointId'))
    const records = state.questions.filter((item) => (
      (!subjectId || numberValue(item.subjectId) === subjectId)
      && (!knowledgeId || numberValue(item.knowledgePointId) === knowledgeId)
    ))
    await json(route, pageData(
      records,
      numberValue(url.searchParams.get('pageNum'), 1),
      numberValue(url.searchParams.get('pageSize'), 10),
    ))
    return
  }

  if (pathname === '/api/question/export' && method === 'GET') {
    await route.fulfill({
      status: 200,
      headers: {
        'Content-Type': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        'Content-Disposition': "attachment; filename*=UTF-8''%E9%94%99%E9%A2%98%E6%9C%AC.xlsx",
      },
      body: 'PK UI fixture workbook',
    })
    return
  }

  if (pathname === '/api/question' && method === 'POST') {
    const id = state.nextQuestionId++
    state.questions.unshift({
      id,
      userId: numberValue(sessionUsers[role].id),
      subjectId: numberValue(body.subjectId),
      stem: stringValue(body.stem),
      answer: stringValue(body.answer),
      source: stringValue(body.source),
      mastery: 0,
      createTime: '2026-08-23 12:00:00',
      updateTime: '2026-08-23 12:00:00',
    })
    state.analyses[id] = null
    await json(route, id)
    return
  }

  const questionMatch = pathname.match(/^\/api\/question\/(\d+)$/)
  if (questionMatch) {
    const id = Number(questionMatch[1])
    const index = state.questions.findIndex((item) => numberValue(item.id) === id)
    if (method === 'GET') {
      if (index < 0) await jsonError(route, '错题不存在', 404)
      else await json(route, state.questions[index])
      return
    }
    if (method === 'PUT') {
      if (index >= 0) Object.assign(state.questions[index], body, { updateTime: '2026-08-23 12:30:00' })
      await json(route, null)
      return
    }
    if (method === 'DELETE') {
      if (index >= 0) state.questions.splice(index, 1)
      delete state.analyses[id]
      state.variants = state.variants.filter((item) => numberValue(item.questionId) !== id)
      await json(route, null)
      return
    }
  }

  const analyzeMatch = pathname.match(/^\/api\/ai\/analyze\/(\d+)$/)
  if (analyzeMatch && method === 'POST') {
    const id = Number(analyzeMatch[1])
    state.analyses[id] = { id: 500 + id, questionId: id, status: 0, createTime: '2026-08-23 12:01:00' }
    state.analysisPollsRemaining[id] = 1
    await json(route, null)
    return
  }

  const analysisMatch = pathname.match(/^\/api\/ai\/analysis\/(\d+)$/)
  if (analysisMatch && method === 'GET') {
    const id = Number(analysisMatch[1])
    const current = state.analyses[id]
    if (current && numberValue(current.status) === 0) {
      if ((state.analysisPollsRemaining[id] || 0) > 0) {
        state.analysisPollsRemaining[id] -= 1
        await json(route, current)
        return
      }
      const question = state.questions.find((item) => numberValue(item.id) === id)
      state.analyses[id] = {
        ...current,
        status: 1,
        knowledgePointId: numberValue(question?.knowledgePointId) || 102,
        errorCause: '重新检查后发现关键约束遗漏。',
        analysis: '按约束逐项验证并回代检查。',
        referenceIds: '[202]',
        llmModel: 'mock-model',
      }
    }
    await json(route, state.analyses[id] ?? null)
    return
  }

  if (pathname === '/api/recommend/similar' && method === 'GET') {
    const id = numberValue(url.searchParams.get('questionId'))
    await json(route, state.questions.filter((item) => numberValue(item.id) !== id).slice(0, 2))
    return
  }

  if (pathname === '/api/variant/list' && method === 'GET') {
    const id = numberValue(url.searchParams.get('questionId'))
    await json(route, state.variants.filter((item) => numberValue(item.questionId) === id).map(item => ({ ...item, practiced: state.practices.some(p => p.variantId === item.id) })))
    return
  }

  const generateVariantMatch = pathname.match(/^\/api\/variant\/generate\/(\d+)$/)
  if (generateVariantMatch && method === 'POST') {
    const questionId = Number(generateVariantMatch[1])
    const available = state.variants.filter(item => numberValue(item.questionId) === questionId && !state.practices.some(p => p.variantId === item.id))
    if (available.length) { await json(route, available); return }
    const generated = {
      id: 700 + state.variants.length + 1,
      questionId,
      stem: '改变区间端点后，重新判断函数单调性。',
      answer: '重新求区间内导数的最值。',
      difficulty: 4,
      createTime: '2026-08-23 12:05:00',
    }
    state.variants.push(generated)
    await json(route, [generated])
    return
  }

  if (pathname === '/api/practice' && method === 'POST') {
    const id = state.nextPracticeId++
    state.practices.unshift({ id, ...body, createTime: '2026-08-23 12:10:00' })
    const questionId = numberValue(body.questionId)
    const question = state.questions.find((item) => numberValue(item.id) === questionId)
    if (question) question.mastery = numberValue(body.isCorrect) === 1 ? 68 : 32
    await json(route, id)
    return
  }

  if (pathname === '/api/practice/page' && method === 'GET') {
    await json(route, pageData(
      state.practices,
      numberValue(url.searchParams.get('pageNum'), 1),
      numberValue(url.searchParams.get('pageSize'), 10),
    ))
    return
  }

  if (pathname === '/api/review-plan/today' && method === 'GET') {
    await json(route, state.reviewPlans)
    return
  }

  const reviewMatch = pathname.match(/^\/api\/review-plan\/(\d+)\/finish$/)
  if (reviewMatch && method === 'PUT') {
    const id = Number(reviewMatch[1])
    state.reviewPlans = state.reviewPlans.filter((item) => numberValue(item.id) !== id)
    await json(route, null)
    return
  }

  if (pathname === '/api/report/weekly' && method === 'GET') {
    await json(route, state.report)
    return
  }

  if (pathname === '/api/report/generate' && method === 'POST') {
    state.messages.unshift({
      id: 1099,
      type: 'report',
      title: '本周学情报告已重新生成',
      content: '最新汇总数据已更新。',
      isRead: 0,
      createTime: '2026-08-23 12:20:00',
    })
    await json(route, state.report)
    return
  }

  if (pathname === '/api/message/page' && method === 'GET') {
    const readFilter = url.searchParams.get('isRead')
    const records = readFilter === null
      ? state.messages
      : state.messages.filter((item) => numberValue(item.isRead) === Number(readFilter))
    await json(route, pageData(
      records,
      numberValue(url.searchParams.get('pageNum'), 1),
      numberValue(url.searchParams.get('pageSize'), 10),
    ))
    return
  }

  const messageMatch = pathname.match(/^\/api\/message\/(\d+)\/read$/)
  if (messageMatch && method === 'PUT') {
    const message = state.messages.find((item) => numberValue(item.id) === Number(messageMatch[1]))
    if (message) message.isRead = 1
    await json(route, null)
    return
  }

  if (pathname === '/api/announcement/list' && method === 'GET') {
    await json(route, state.announcements)
    return
  }

  if (pathname === '/api/announcement' && method === 'POST') {
    const id = state.nextAnnouncementId++
    state.announcements.unshift({
      id,
      title: stringValue(body.title),
      content: stringValue(body.content),
      publisherId: numberValue(sessionUsers[role].id),
      createTime: '2026-08-23 12:25:00',
    })
    await json(route, id)
    return
  }

  if (pathname === '/api/user/page' && method === 'GET') {
    const roleFilter = url.searchParams.get('role') || ''
    const keyword = (url.searchParams.get('keyword') || '').toLowerCase()
    const records = state.users.filter((item) => (
      (!roleFilter || item.role === roleFilter)
      && (!keyword || stringValue(item.username).toLowerCase().includes(keyword)
        || stringValue(item.nickname).toLowerCase().includes(keyword))
    ))
    await json(route, pageData(
      records,
      numberValue(url.searchParams.get('pageNum'), 1),
      numberValue(url.searchParams.get('pageSize'), 10),
    ))
    return
  }

  const userMatch = pathname.match(/^\/api\/user\/(\d+)$/)
  if (userMatch && method === 'DELETE') {
    const id = Number(userMatch[1])
    state.users = state.users.filter((item) => numberValue(item.id) !== id)
    await json(route, null)
    return
  }

  await jsonError(route, `未配置的测试接口：${method} ${pathname}`, 404)
}

type UiFixtures = {
  mockApi: MockApiState
}

export const test = base.extend<UiFixtures>({
  mockApi: [
    async ({ page }, use) => {
      const state = defaultState()
      await page.route(/^https?:\/\/[^/]+\/api(?:\/|$)/, (route) => handleApiRoute(route, state))
      await page.emulateMedia({ colorScheme: 'light', reducedMotion: 'reduce' })
      await use(state)
    },
    { auto: true },
  ],
})

export async function installMockSession(page: Page, role: MockRole) {
  await page.addInitScript(
    ({ token, user }) => {
      localStorage.setItem('token', token)
      localStorage.setItem('user', JSON.stringify(user))
    },
    { token: `ui-${role}-token`, user: sessionUsers[role] },
  )
}

export function collectBrowserErrors(page: Page) {
  const errors: string[] = []
  page.on('pageerror', (error) => errors.push(error.message))
  page.on('console', (message) => {
    if (message.type() === 'error') errors.push(message.text())
  })
  return errors
}

export async function expectDocumentWithinViewport(page: Page) {
  const geometry = await page.evaluate(() => ({
    innerWidth: window.innerWidth,
    scrollWidth: document.documentElement.scrollWidth,
  }))
  expect(geometry.scrollWidth).toBeLessThanOrEqual(geometry.innerWidth + 1)
}

export { expect }
