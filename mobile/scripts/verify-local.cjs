// Runs the compiled request code with a WeChat transport adapter backed by real HTTP.
const assert = require('node:assert/strict')
const { execFileSync } = require('node:child_process')
const { cpSync, mkdtempSync, rmSync } = require('node:fs')
const { tmpdir } = require('node:os')
const { join } = require('node:path')

const build = join(__dirname, '../dist/build/mp-weixin')
const databaseContainer = process.env.MOBILE_TEST_DB_CONTAINER
const noop = () => {}
const storage = new Map()
let route = 'pages/login/index'
let relaunches = 0

function installWeChatAdapter() {
  Object.assign(globalThis, {
    App: noop,
    Page: noop,
    Component: noop,
    Behavior: noop,
    getCurrentPages: () => [{ route }],
    wx: {
      onAppShow: noop,
      onAppHide: noop,
      getAccountInfoSync: () => ({ miniProgram: { appId: 'touristappid' } }),
      getSystemInfoSync: () => ({ platform: 'devtools', SDKVersion: '3.0.0' }),
      getStorageSync: (key) => storage.get(key),
      setStorageSync: (key, value) => storage.set(key, value),
      removeStorageSync: (key) => storage.delete(key),
      reLaunch({ url, success, complete }) {
        relaunches += 1
        route = url.slice(1)
        success?.({})
        complete?.({})
      },
      request({ url, method, data, header, timeout, success, fail, complete }) {
        const target = new URL(url)
        const init = {
          method,
          headers: { ...header, Referer: 'https://servicewechat.com/touristappid/0/page-frame.html' },
          signal: AbortSignal.timeout(timeout),
        }
        if (method === 'GET') {
          for (const [key, value] of Object.entries(data || {})) target.searchParams.set(key, value)
        } else if (data !== undefined) {
          init.body = JSON.stringify(data)
        }
        fetch(target, init)
          .then(async (res) => {
            const result = { statusCode: res.status, data: await res.json(), errMsg: 'request:ok' }
            console.log(`${method} ${target.pathname}${target.search} HTTP ${res.status} code=${result.data.code}`)
            success(result)
            complete?.(result)
          })
          .catch((err) => fail({ errMsg: `request:fail ${err.name}` }))
        return { abort: noop }
      },
    },
  })
}

function sql(statement) {
  return execFileSync('docker', [
    'exec', databaseContainer, 'sh', '-c',
    'MYSQL_PWD="$MYSQL_PASSWORD" mysql -u "$MYSQL_USER" "$MYSQL_DATABASE" --batch --skip-column-names --default-character-set=utf8mb4 -e "$1"',
    'mysql', statement,
  ], { encoding: 'utf8' }).trim()
}

async function run(directory) {
  cpSync(build, directory, { recursive: true })
  const { apiBaseUrl } = require(join(directory, 'config.js'))
  assert.ok(['127.0.0.1', 'localhost', '[::1]'].includes(new URL(apiBaseUrl).hostname), 'Use a local API build')
  assert.ok(databaseContainer, 'Set MOBILE_TEST_DB_CONTAINER to the isolated MySQL container')
  assert.equal(sql('SELECT DATABASE()'), 'wrongbook_mobile', 'Use the isolated wrongbook_mobile database')
  const tableCount = sql('SELECT COUNT(*) FROM information_schema.tables WHERE table_schema=DATABASE()')
  assert.equal(tableCount, '11')
  console.log(`MYSQL ${sql('SELECT VERSION()')} tables=${tableCount}`)
  installWeChatAdapter()
  const api = require(join(directory, 'api/student.js'))
  const session = require(join(directory, 'api/request.js'))
  const password = process.env.MOBILE_TEST_STUDENT_PASSWORD || '123456'
  const username = process.env.MOBILE_TEST_STUDENT_USERNAME || 'student'
  const teacherPassword = process.env.MOBILE_TEST_TEACHER_PASSWORD || '123456'

  await assert.rejects(api.login(username, 'invalid-password'))
  assert.equal(relaunches, 0)
  await assert.rejects(api.login('teacher', teacherPassword), { code: 403 })
  assert.ok(!session.storedToken())
  const student = await api.login(username, password)
  assert.equal(student.role, 'student')
  assert.equal((await api.profile()).id, student.id)
  route = 'pages/home/index'
  const subjects = await api.listSubjects()
  const [math, physics] = ['数学', '物理'].map((name) => subjects.find((subject) => subject.name === name))
  const before = await api.weeklyReport()
  const initialPage = await api.questions(1, 1, math.id)
  const today = new Date(Date.now() + 8 * 60 * 60 * 1000).toISOString().slice(0, 10)
  const countToday = (report) => report.dailyPractices.find((row) => row.date === today)?.count ?? 0
  const png = 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+/WfQAAAAASUVORK5CYII='

  const manualId = await api.saveQuestion({ subjectId: math.id, stem: '解方程 2x = 6', answer: 'x = 3' })
  const richId = await api.saveQuestion({ subjectId: math.id, stem: '<p>计算 x<sup>2</sup>，其中 x=2</p>', answer: '4', imageBase64: png })
  assert.ok(Number.isSafeInteger(manualId) && Number.isSafeInteger(richId))
  assert.equal(await api.question(manualId).then((item) => item.stem), '解方程 2x = 6')
  assert.equal(await api.question(richId).then((item) => item.imageUrl), png)
  const first = await api.questions(1, 1, math.id)
  const second = await api.questions(2, 1, math.id)
  assert.equal(first.total, initialPage.total + 2)
  assert.notEqual(first.records[0].id, second.records[0].id)
  assert.equal(first.records[0].subjectId, math.id)
  assert.equal(second.records[0].subjectId, math.id)
  assert.ok(!(await api.questions(1, 10, physics.id)).records.some((item) => item.id === manualId || item.id === richId))
  console.log(`QUESTIONS saved=${manualId},${richId} mathTotal=${first.total} pagesChecked=2 authenticatedImage=exact`)

  assert.equal((await api.nextPractice(manualId)).source, 'original')
  const originalRecord = await api.savePractice({ questionId: manualId, userAnswer: 'x = 3', isCorrect: 1 })
  assert.equal(await api.question(manualId).then((item) => item.mastery), 15)
  sql(`INSERT INTO variant_question (question_id, stem, answer, difficulty) VALUES
    (${manualId}, 'Solve 2x=8', 'x=4', 1), (${manualId}, 'Solve 2x=10', 'x=5', 1)`)
  const variant = await api.nextPractice(manualId)
  assert.equal(variant.source, 'existing')
  const variantRecord = await api.savePractice({ variantId: variant.variantId, userAnswer: variant.answer, isCorrect: 1 })
  const subsequent = await api.nextPractice(manualId)
  assert.equal(subsequent.source, 'existing')
  assert.notEqual(subsequent.variantId, variant.variantId)
  console.log(`PRACTICE originalRecord=${originalRecord} variantRecord=${variantRecord} variant=${variant.variantId} next=${subsequent.variantId}`)

  assert.equal(sql(`SELECT COUNT(*) FROM review_plan WHERE question_id=${manualId}`), '5')
  sql(`UPDATE review_plan SET plan_date=DATE(CONVERT_TZ(UTC_TIMESTAMP(), '+00:00', '+08:00'))
    WHERE question_id=${manualId} AND review_stage=1`)
  const plan = (await api.dueReviews()).find((item) => item.questionId === manualId)
  assert.equal(plan.planDate, today)
  const reviewRecord = await api.savePractice({ questionId: manualId, userAnswer: 'x = 3', isCorrect: 1 })
  await api.finishReview(plan.id)
  await assert.rejects(api.finishReview(plan.id), { code: 400, message: '该复习任务已完成' })
  assert.ok(!(await api.dueReviews()).some((item) => item.id === plan.id))
  assert.equal(sql(`SELECT status, finish_time IS NOT NULL FROM review_plan WHERE id=${plan.id}`), '1\t1')
  assert.equal(sql(`SELECT COUNT(*) FROM practice_record WHERE id IN (${originalRecord},${variantRecord},${reviewRecord})`), '3')
  console.log(`REVIEW plan=${plan.id} practiceRecord=${reviewRecord} completed=1 pendingList=false repeatedFinish=400`)

  const after = await api.weeklyReport()
  assert.equal(after.totalQuestionCount, before.totalQuestionCount + 2)
  assert.equal(countToday(after), countToday(before) + 3)
  console.log(`REPORT total=${after.totalQuestionCount} todayPractice=${countToday(after)}`)

  assert.equal(await api.readAnalysis(manualId), null)
  for (const [name, action] of [
    ['OCR', () => api.recognizeQuestion(png)],
    ['AI', () => api.startAnalysis(manualId)],
    ['KNOWLEDGE', () => api.readKnowledge(manualId)],
  ]) {
    try {
      const result = await action()
      console.log(`${name} accepted result=${result == null ? 'empty' : 'present'}`)
    } catch (error) {
      if (error.code !== 400) throw error
      console.log(`${name} unavailable code=${error.code} message=${error.message}`)
    }
  }

  session.saveToken('invalid-jwt')
  await assert.rejects(api.profile(), { code: 401 })
  assert.ok(!session.storedToken())
  assert.equal(relaunches, 1)
  assert.equal(route, 'pages/login/index')
  console.log('SESSION invalid JWT cleared; one login navigation')
  console.log('PASS real HTTP and MySQL core flows')
}

const directory = mkdtempSync(join(tmpdir(), 'wrongbook-mp-'))
run(directory)
  .catch((error) => { console.error(error); process.exitCode = 1 })
  .finally(() => rmSync(directory, { recursive: true, force: true }))
