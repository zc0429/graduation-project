<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ArrowRight, Calendar, EditPen, Grid, Reading } from '@element-plus/icons-vue'
import {
  announcementApi,
  kpApi,
  questionApi,
  reportApi,
  reviewPlanApi,
  subjectApi,
  userApi,
  type KpNode,
  type Question,
  type ReviewPlanItem,
  type Subject,
  type WeeklyReport,
} from '@/api'
import AsyncState from '@/components/AsyncState.vue'
import MasteryIndicator from '@/components/MasteryIndicator.vue'
import PageHeader from '@/components/PageHeader.vue'
import PaperPanel from '@/components/PaperPanel.vue'
import { useUserStore } from '@/store/user'

const router = useRouter()
const route = useRoute()
const store = useUserStore()
const loading = ref(true)
const loadError = ref('')
const partialFailures = ref(0)
type SourceKey = 'subjects' | 'plans' | 'report' | 'questions' | 'users' | 'knowledge' | 'announcements'
type LoadTask = { key: SourceKey; run: Promise<unknown> }
const failedSources = ref<Set<SourceKey>>(new Set())
const report = ref<WeeklyReport>()
const plans = ref<ReviewPlanItem[]>([])
const recentQuestions = ref<Question[]>([])
const subjects = ref<Subject[]>([])
const adminStats = ref<Record<'users' | 'subjects' | 'knowledge' | 'announcements', number | undefined>>({
  users: undefined,
  subjects: undefined,
  knowledge: undefined,
  announcements: undefined,
})

const overdueCount = computed(() => plans.value.filter((item) => item.status === 2 || item.planDate < today()).length)
const todayCount = computed(() => Math.max(0, plans.value.length - overdueCount.value))
const weakPoints = computed(() => report.value?.weakPoints.slice(0, 5) || [])

function today() {
  return new Date().toLocaleDateString('sv-SE')
}

function subjectName(id?: number) {
  return subjects.value.find((item) => item.id === id)?.name || '未标注科目'
}

function countKnowledge(nodes: KpNode[]): number {
  return nodes.reduce((sum, node) => sum + 1 + countKnowledge(node.children || []), 0)
}

function sourceFailed(key: SourceKey) {
  return failedSources.value.has(key)
}

async function settle(tasks: LoadTask[]) {
  const results = await Promise.allSettled(tasks.map((task) => task.run))
  failedSources.value = new Set(results.flatMap((result, index) => result.status === 'rejected' ? [tasks[index].key] : []))
  partialFailures.value = results.filter((item) => item.status === 'rejected').length
  if (partialFailures.value === tasks.length) throw new Error('工作台数据暂时无法加载，请检查网络后重试。')
}

async function load() {
  loading.value = true
  loadError.value = ''
  partialFailures.value = 0
  failedSources.value = new Set()
  report.value = undefined
  plans.value = []
  recentQuestions.value = []
  subjects.value = []
  adminStats.value = { users: undefined, subjects: undefined, knowledge: undefined, announcements: undefined }
  try {
    if (store.role === 'student') {
      await settle([
        { key: 'subjects', run: subjectApi.list().then((data) => { subjects.value = data }) },
        { key: 'plans', run: reviewPlanApi.today().then((data) => { plans.value = data }) },
        { key: 'report', run: reportApi.weekly().then((data) => { report.value = data }) },
        { key: 'questions', run: questionApi.page({ pageNum: 1, pageSize: 3 }).then((data) => { recentQuestions.value = data.records }) },
      ])
    } else if (store.role === 'teacher') {
      await settle([{ key: 'report', run: reportApi.weekly().then((data) => { report.value = data }) }])
    } else {
      await settle([
        { key: 'subjects', run: subjectApi.list().then((data) => { subjects.value = data; adminStats.value.subjects = data.length }) },
        { key: 'announcements', run: announcementApi.list().then((data) => { adminStats.value.announcements = data.length }) },
        { key: 'users', run: userApi.page({ pageNum: 1, pageSize: 1 }).then((data) => { adminStats.value.users = data.total }) },
        { key: 'knowledge', run: kpApi.tree().then((data: KpNode[]) => { adminStats.value.knowledge = countKnowledge(data) }) },
      ])
    }
  } catch (error) {
    loadError.value = error instanceof Error ? error.message : '工作台数据暂时无法加载。'
  } finally {
    loading.value = false
  }
}

onMounted(load)
</script>

<template>
  <div class="home-page">
    <p v-if="route.query.notice === 'forbidden'" class="permission-notice" role="alert">当前账号没有访问上一页面的权限，已返回可用工作台。前端菜单仅控制展示，服务端权限仍是最终边界。</p>
    <PageHeader
      :eyebrow="store.role === 'student' ? '今日学习工作台' : store.role === 'teacher' ? '全站聚合学情' : '系统数据工作台'"
      :title="store.role === 'student' ? `${store.nickname}，先把今天的两件事做好。` : store.role === 'teacher' ? `${store.nickname}，查看全站聚合学情。` : `${store.nickname}，维护当前有效数据。`"
      :description="store.role === 'student' ? '录入一道刚做错的题，完成到期复习；剩下的趋势与反馈交给系统整理。' : store.role === 'teacher' ? '当前后端没有班级、课程或学生绑定；以下只展示真实可用的全站聚合指标。' : '管理员只处理后端已支持的用户、科目、知识点和公告边界。'"
    >
      <template v-if="store.role !== 'student'" #actions>
        <el-button v-if="store.role === 'teacher'" :icon="ArrowRight" @click="router.push('/report')">打开完整报告</el-button>
        <el-button v-else type="primary" :icon="Grid" @click="router.push('/admin/user')">进入数据管理</el-button>
      </template>
    </PageHeader>

    <div v-if="partialFailures && !loadError" class="partial-notice" role="status"><span>部分数据未加载，对应区域已标为暂不可用。</span><el-button size="small" @click="load">刷新重试</el-button></div>
    <AsyncState v-if="loading" status="loading" title="正在整理今日工作台" description="正在读取当前账号可访问的数据。" />
    <AsyncState v-else-if="loadError" status="error" title="工作台加载失败" :description="loadError" @retry="load" />

    <template v-else-if="store.role === 'student'">
      <section class="student-hero">
        <PaperPanel variant="lined" class="focus-board">
          <div class="focus-date"><strong>{{ new Date().getDate().toString().padStart(2, '0') }}</strong><span>{{ new Date().toLocaleDateString('zh-CN', { month: '2-digit', weekday: 'short' }) }}</span></div>
          <p class="panel-kicker">今日学习焦点</p>
          <h2 v-if="!sourceFailed('plans')">先处理 <em>{{ overdueCount }}</em> 道逾期题，<br>再完成 <em>{{ todayCount }}</em> 道今日复习。</h2>
          <h2 v-else>复习任务暂时不可用，<br>仍可继续录入和整理错题。</h2>
          <p>{{ sourceFailed('plans') ? '任务数量没有被当作 0 展示，请刷新后重试。' : '每次重做后请根据实际结果自评，掌握度会随练习更新。' }}</p>
          <div class="hero-actions">
            <el-button type="primary" :icon="EditPen" @click="router.push('/question/create')">录入错题</el-button>
            <el-button class="jade-button" :icon="Calendar" @click="router.push('/review')">{{ sourceFailed('plans') ? '打开复习计划' : `今日复习 · ${plans.length}` }}</el-button>
          </div>
        </PaperPanel>
        <PaperPanel class="mastery-board" :class="{ 'is-unavailable': sourceFailed('report') }">
          <AsyncState v-if="sourceFailed('report')" status="error" compact title="本周反馈暂不可用" description="其他可用数据仍会正常展示。" @retry="load" />
          <template v-else>
            <MasteryIndicator :value="report?.masteryAvg ?? 0" label="本周平均掌握度" />
            <p>错题总数 {{ report?.totalQuestionCount ?? 0 }} 道，本周完成 {{ report?.reviewFinishedCount ?? 0 }} / {{ report?.reviewTotalCount ?? 0 }} 次复习。</p>
            <el-button text @click="router.push('/report')">查看本周反馈<el-icon><ArrowRight /></el-icon></el-button>
          </template>
        </PaperPanel>
      </section>

      <section class="student-grid">
        <PaperPanel variant="lined" class="review-sheet">
          <div class="panel-heading"><h2><el-icon><Reading /></el-icon>到期复习清单</h2><el-button text @click="router.push('/review')">查看全部<el-icon><ArrowRight /></el-icon></el-button></div>
          <AsyncState v-if="sourceFailed('plans')" status="error" compact title="复习清单暂不可用" description="任务数量未按 0 处理。" @retry="load" />
          <AsyncState v-else-if="plans.length === 0" status="empty" compact title="今天没有到期任务" description="新录入的错题会自动进入 1/2/4/7/15 天复习节奏。" />
          <button v-for="(plan, index) in plans.slice(0, 4)" :key="plan.id" class="task-row" type="button" @click="router.push(`/question/${plan.questionId}`)">
            <span class="task-index">{{ index + 1 }}</span><span><strong>{{ plan.stemSummary || `错题 #${plan.questionId}` }}</strong><small>{{ subjectName(plan.subjectId) }} · 第 {{ plan.reviewStage }} / 5 轮</small></span><em :class="{ overdue: plan.status === 2 || plan.planDate < today() }">{{ plan.status === 2 || plan.planDate < today() ? '已逾期' : '今日' }}</em>
          </button>
        </PaperPanel>

        <div class="side-stack">
          <PaperPanel>
            <div class="panel-heading"><h2>本周练习</h2><span v-if="!sourceFailed('report')" class="data-tag">{{ report?.dailyPractices.reduce((sum, item) => sum + item.count, 0) ?? 0 }} 次</span></div>
            <AsyncState v-if="sourceFailed('report')" status="error" compact title="练习趋势暂不可用" @retry="load" />
            <div v-else class="mini-bars" role="img" :aria-label="`近七日练习量：${report?.dailyPractices.map((item) => item.count).join('、') || '暂无'}`">
              <i v-for="item in report?.dailyPractices || []" :key="item.date" :style="{ height: `${Math.max(8, item.count * 14)}px` }"><span>{{ item.date.slice(5) }}</span></i>
            </div>
          </PaperPanel>
          <PaperPanel variant="annotation"><strong>学习批注</strong><p>错题数量不是目标。能否在下一轮复习中独立答对，才是更有价值的反馈。</p></PaperPanel>
        </div>
      </section>

      <PaperPanel variant="lined" class="recent-panel">
        <div class="panel-heading"><h2>近期错题</h2><el-button text @click="router.push('/question/list')">打开错题本<el-icon><ArrowRight /></el-icon></el-button></div>
        <AsyncState v-if="sourceFailed('questions')" status="error" compact title="近期错题暂不可用" description="不会把加载失败显示成空错题本。" @retry="load" />
        <AsyncState v-else-if="recentQuestions.length === 0" status="empty" compact title="还没有错题记录" description="录入第一道题后，会在这里显示。" />
        <div v-else class="recent-grid">
          <button v-for="question in recentQuestions" :key="question.id" type="button" class="recent-card" @click="router.push(`/question/${question.id}`)">
            <span>{{ subjectName(question.subjectId) }}</span><MasteryIndicator :value="question.mastery" compact :show-label="false" /><strong>{{ question.stem }}</strong><small>{{ question.source || '来源未标注' }} · {{ question.createTime.slice(0, 10) }}</small>
          </button>
        </div>
      </PaperPanel>
    </template>

    <template v-else-if="store.role === 'teacher'">
      <section class="overview-strip">
        <div><span>本周新增错题</span><strong>{{ report?.newQuestionCount || 0 }}</strong><em>道</em></div>
        <div><span>有效错题总量</span><strong>{{ report?.totalQuestionCount || 0 }}</strong><em>道</em></div>
        <div><span>复习完成</span><strong>{{ report?.reviewFinishedCount || 0 }}</strong><em>/ {{ report?.reviewTotalCount || 0 }}</em></div>
        <div><span>平均掌握度</span><strong>{{ report?.masteryAvg || 0 }}</strong><em>%</em></div>
      </section>
      <section class="teacher-grid">
        <PaperPanel>
          <div class="panel-heading"><h2>薄弱知识点</h2><span class="data-tag">全站 Top 5</span></div>
          <AsyncState v-if="weakPoints.length === 0" status="empty" compact title="暂无薄弱点数据" />
          <div v-for="(point, index) in weakPoints" :key="point.knowledgePointId" class="weak-row"><span>{{ index + 1 }}</span><strong>{{ point.name }}</strong><MasteryIndicator :value="point.mastery" compact :show-label="false" /><em>{{ point.questionCount }} 题</em></div>
        </PaperPanel>
        <PaperPanel variant="annotation"><strong>范围说明</strong><p>这些指标来自周报接口返回的全站聚合字段；当前没有班级选择、学生钻取或科目分组能力。</p></PaperPanel>
      </section>
    </template>

    <template v-else>
      <section class="overview-strip admin-overview">
        <div><span>有效用户</span><strong>{{ sourceFailed('users') ? '—' : adminStats.users }}</strong><em>人</em></div>
        <div><span>启用科目</span><strong>{{ sourceFailed('subjects') ? '—' : adminStats.subjects }}</strong><em>门</em></div>
        <div><span>知识点</span><strong>{{ sourceFailed('knowledge') ? '—' : adminStats.knowledge }}</strong><em>个</em></div>
        <div><span>当前公告</span><strong>{{ sourceFailed('announcements') ? '—' : adminStats.announcements }}</strong><em>条</em></div>
      </section>
      <section class="admin-grid">
        <PaperPanel>
          <div class="panel-heading"><h2>管理入口</h2><span class="data-tag">真实接口</span></div>
          <div class="management-grid">
            <button type="button" @click="router.push('/admin/user')"><strong>用户管理</strong><span>查询与逻辑注销</span></button>
            <button type="button" @click="router.push('/admin/subject')"><strong>科目管理</strong><span>新增与编辑</span></button>
            <button type="button" @click="router.push('/admin/knowledge')"><strong>知识点管理</strong><span>两级结构增删</span></button>
            <button type="button" @click="router.push('/announcement')"><strong>公告管理</strong><span>查看与发布</span></button>
          </div>
        </PaperPanel>
        <PaperPanel variant="annotation"><strong>权限边界</strong><p>当前后端不支持角色分配、账号恢复、科目删除、公告编辑或下线，因此正式界面不会展示这些动作。</p></PaperPanel>
      </section>
    </template>
  </div>
</template>

<style scoped>
.home-page{display:grid;gap:20px}.permission-notice,.partial-notice{margin:0;padding:10px 14px;border-left:3px solid var(--amber);background:var(--amber-pale);color:#73501c;font-size:12px}.partial-notice{display:flex;align-items:center;justify-content:space-between;gap:12px}.permission-notice{border-left-color:var(--cinnabar);background:var(--cinnabar-pale);color:var(--cinnabar-dark)}.student-hero{display:grid;grid-template-columns:minmax(0,2fr) minmax(280px,.9fr);gap:20px}.focus-board{position:relative;min-height:285px;padding:35px 38px!important;overflow:hidden}.focus-board::after{content:'';position:absolute;width:210px;height:210px;right:-58px;bottom:-72px;border:22px solid rgba(22,129,114,.08);border-radius:50%;box-shadow:0 0 0 20px rgba(183,67,50,.045)}.panel-kicker{margin:0 0 20px;color:var(--ink-soft);font-size:12px;font-weight:800;letter-spacing:.12em}.focus-board h2{position:relative;z-index:1;max-width:680px;margin:0;color:var(--navy);font:800 clamp(30px,3vw,43px)/1.3 var(--font-display)}.focus-board h2 em{color:var(--cinnabar);font-style:normal}.focus-board>p:not(.panel-kicker){position:relative;z-index:1;color:var(--ink-soft);font-size:13px}.focus-date{position:absolute;right:25px;top:22px;display:grid;place-items:center;width:72px;height:72px;border:2px solid var(--cinnabar);border-radius:50%;color:var(--cinnabar);transform:rotate(2deg)}.focus-date strong{font:italic 18px var(--font-display)}.focus-date span{font-size:9px}.hero-actions{position:relative;z-index:1;display:flex;gap:10px;margin-top:24px}.jade-button{border-color:rgba(22,129,114,.35)!important;background:var(--jade-pale)!important;color:var(--jade-dark)!important}.mastery-board{display:flex;flex-direction:column;justify-content:center;min-height:285px;background:var(--navy)!important;color:#fff!important}.mastery-board :deep(.mastery-copy),.mastery-board p{color:#eef7f5!important}.mastery-board :deep(.mastery-copy strong){color:#9be5d8!important}.mastery-board :deep(.mastery-track){background:rgba(255,255,255,.2)}.mastery-board :deep(.mastery-track i){background:#75d5c6}.mastery-board p{margin:26px 0 8px;font-size:12px;line-height:1.7}.mastery-board :deep(.el-button){align-self:flex-start;color:#9be5d8}.mastery-board.is-unavailable{background:var(--paper-bright)!important;color:var(--ink)!important}.student-grid{display:grid;grid-template-columns:minmax(0,1.65fr) minmax(290px,1fr);gap:20px}.panel-heading{display:flex;align-items:center;justify-content:space-between;gap:12px;margin-bottom:15px}.panel-heading h2{display:flex;align-items:center;gap:8px;margin:0;color:var(--navy);font:800 18px var(--font-display)}.task-row{width:100%;display:grid;grid-template-columns:40px minmax(0,1fr) auto;align-items:center;gap:13px;padding:13px 4px;border:0;border-bottom:1px dashed var(--line);background:transparent;text-align:left;cursor:pointer}.task-index{display:grid;place-items:center;width:32px;height:32px;border:1px solid var(--cinnabar-light);border-radius:50%;color:var(--cinnabar);font-family:var(--font-display)}.task-row strong{display:block;color:var(--navy);font-size:13px}.task-row small{display:block;margin-top:4px;color:var(--ink-faint);font-size:10px}.task-row em{color:var(--jade-dark);font-size:11px;font-style:normal}.task-row em.overdue{color:var(--cinnabar)}.side-stack{display:grid;gap:20px}.mini-bars{height:150px;display:flex;align-items:flex-end;justify-content:space-around;gap:7px;padding:25px 10px 23px;border-bottom:1px solid var(--line)}.mini-bars i{position:relative;width:10%;min-height:8px;max-height:105px;border-radius:6px 6px 1px 1px;background:var(--jade);font-style:normal}.mini-bars span{position:absolute;left:50%;bottom:-20px;transform:translateX(-50%);color:var(--ink-faint);font:8px var(--font-mono)}.data-tag{padding:5px 9px;border:1px solid var(--jade-light);border-radius:999px;background:var(--jade-pale);color:var(--jade-dark);font-size:10px;font-weight:700}.recent-grid{display:grid;grid-template-columns:repeat(3,1fr);border:1px solid var(--line);border-radius:11px;overflow:hidden}.recent-card{display:grid;grid-template-columns:1fr auto;gap:11px;padding:18px;border:0;border-right:1px solid var(--line);background:transparent;text-align:left;cursor:pointer}.recent-card:last-child{border-right:0}.recent-card>span{color:var(--ink-soft);font-size:10px}.recent-card strong,.recent-card small{grid-column:1/-1}.recent-card strong{min-height:40px;color:var(--navy);font-size:13px;line-height:1.6}.recent-card small{color:var(--ink-faint);font-size:9px}.overview-strip{display:grid;grid-template-columns:repeat(4,1fr);overflow:hidden;border:1px solid var(--line-strong);border-radius:14px;background:var(--paper-bright)}.overview-strip>div{padding:24px;border-right:1px solid var(--line)}.overview-strip>div:last-child{border-right:0}.overview-strip span{display:block;color:var(--ink-faint);font-size:10px}.overview-strip strong{display:inline-block;margin-top:8px;color:var(--navy);font:800 29px var(--font-mono)}.overview-strip em{margin-left:5px;color:var(--ink-soft);font-size:10px;font-style:normal}.teacher-grid,.admin-grid{display:grid;grid-template-columns:minmax(0,1.5fr) minmax(320px,1fr);gap:20px}.weak-row{display:grid;grid-template-columns:28px minmax(110px,.7fr) minmax(160px,1.5fr) 55px;align-items:center;gap:12px;padding:11px 0;border-bottom:1px dashed var(--line)}.weak-row>span{display:grid;place-items:center;width:24px;height:24px;border-radius:50%;background:var(--cinnabar-pale);color:var(--cinnabar);font-size:10px}.weak-row strong{font-size:12px}.weak-row em{color:var(--ink-faint);font-size:10px;font-style:normal;text-align:right}.management-grid{display:grid;grid-template-columns:1fr 1fr;gap:12px}.management-grid button{min-height:120px;padding:20px;border:1px solid var(--line);border-radius:12px;background:var(--paper-bright);text-align:left;cursor:pointer}.management-grid button:hover{border-color:var(--jade);transform:translateY(-2px)}.management-grid strong,.management-grid span{display:block}.management-grid strong{color:var(--navy);font:800 16px var(--font-display)}.management-grid span{margin-top:9px;color:var(--ink-faint);font-size:11px}
@media(max-width:1050px){.student-hero,.student-grid,.teacher-grid,.admin-grid{grid-template-columns:1fr}.side-stack{grid-template-columns:1fr 1fr}.recent-grid{grid-template-columns:1fr}.recent-card{border-right:0;border-bottom:1px solid var(--line)}.recent-card:last-child{border-bottom:0}}
@media(max-width:700px){.focus-board{min-height:310px;padding:25px 20px!important}.focus-board h2{padding-right:40px;font-size:29px}.focus-date{right:12px;top:16px;width:58px;height:58px}.hero-actions{flex-wrap:wrap}.hero-actions :deep(.el-button){flex:1 1 140px}.side-stack{grid-template-columns:1fr}.overview-strip{grid-template-columns:1fr 1fr}.overview-strip>div:nth-child(2){border-right:0}.overview-strip>div{padding:17px}.management-grid{grid-template-columns:1fr 1fr}.weak-row{grid-template-columns:26px minmax(80px,1fr) 1.6fr}.weak-row em{display:none}.task-row{grid-template-columns:35px minmax(0,1fr)}.task-row em{grid-column:2}}
</style>
