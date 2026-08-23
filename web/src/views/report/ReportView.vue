<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref } from 'vue'
import type { EChartsType } from 'echarts/core'
import { Refresh } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import AsyncState from '@/components/AsyncState.vue'
import MasteryIndicator from '@/components/MasteryIndicator.vue'
import PageHeader from '@/components/PageHeader.vue'
import PaperPanel from '@/components/PaperPanel.vue'
import { reportApi, type WeeklyReport } from '@/api'
import { useUserStore } from '@/store/user'
import { toApiError } from '@/utils/api-error'

const store = useUserStore()
const report = ref<WeeklyReport | null>(null)
const loading = ref(true)
const generating = ref(false)
const loadError = ref('')
const generateError = ref('')
const chartError = ref('')
const chartsLoading = ref(false)

const newQuestionsChartRef = ref<HTMLElement>()
const practicesChartRef = ref<HTMLElement>()

let newQuestionsChart: EChartsType | undefined
let practicesChart: EChartsType | undefined
let chartResizeObserver: ResizeObserver | undefined
let chartRenderVersion = 0
let unmounted = false
let chartEnginePromise: Promise<typeof import('echarts/core')> | undefined

const isTeacher = computed(() => store.role === 'teacher')

const pageDescription = computed(() =>
  isTeacher.value
    ? '查看系统现有接口返回的全站聚合学习数据；当前没有班级或课程绑定。'
    : '把本周错题、复习与练习放在同一页复盘，找到下一步最值得投入的知识点。',
)

const weekLabel = computed(() => {
  if (!report.value?.weekStart) return '数据更新后显示统计周期'
  return `${report.value.weekStart.replaceAll('-', '.')} 起的一周`
})

const reviewRate = computed(() => {
  if (!report.value || report.value.reviewTotalCount <= 0) return 0
  return normalizePercent((report.value.reviewFinishedCount / report.value.reviewTotalCount) * 100)
})

const masteryAverage = computed(() => normalizePercent(report.value?.masteryAvg ?? 0))

const hasReportData = computed(() => {
  const value = report.value
  if (!value) return false
  return value.totalQuestionCount > 0
    || value.newQuestionCount > 0
    || value.reviewTotalCount > 0
    || value.knowledgeMastery.some((item) => item.questionCount > 0)
    || value.dailyNewQuestions.some((item) => item.count > 0)
    || value.dailyPractices.some((item) => item.count > 0)
})

const weakPoints = computed(() => report.value?.weakPoints.slice(0, 5) ?? [])

const questionTrendSummary = computed(() => describeTrend(report.value?.dailyNewQuestions ?? [], '录入错题'))
const practiceTrendSummary = computed(() => describeTrend(report.value?.dailyPractices ?? [], '完成练习'))

function normalizePercent(value: number) {
  return Math.min(100, Math.max(0, Math.round(Number(value) || 0)))
}

function formatDay(value: string) {
  const parts = value.split('-')
  return parts.length >= 3 ? `${parts.at(-2)}/${parts.at(-1)}` : value
}

function describeTrend(items: { date: string; count: number }[], action: string) {
  if (items.length === 0) return `本周暂无${action}数据。`
  const total = items.reduce((sum, item) => sum + item.count, 0)
  const peak = items.reduce((current, item) => (item.count > current.count ? item : current), items[0])
  if (!peak || total === 0) return `本周${action}记录为 0。`
  return `本周共${action} ${total} 次，${formatDay(peak.date)}最多，为 ${peak.count} 次。`
}

function chartColor(variable: string, fallback: string) {
  return getComputedStyle(document.documentElement).getPropertyValue(variable).trim() || fallback
}

async function loadChartEngine() {
  chartEnginePromise ??= Promise.all([
    import('echarts/core'),
    import('echarts/charts'),
    import('echarts/components'),
    import('echarts/renderers'),
  ]).then(([core, charts, components, renderers]) => {
    core.use([
      charts.BarChart,
      charts.LineChart,
      components.GridComponent,
      components.TooltipComponent,
      renderers.CanvasRenderer,
    ])
    return core
  })
  return chartEnginePromise
}

function disposeCharts() {
  chartResizeObserver?.disconnect()
  chartResizeObserver = undefined
  newQuestionsChart?.dispose()
  practicesChart?.dispose()
  newQuestionsChart = undefined
  practicesChart = undefined
}

function observeChartSizes() {
  chartResizeObserver?.disconnect()
  chartResizeObserver = new ResizeObserver(() => {
    newQuestionsChart?.resize()
    practicesChart?.resize()
  })
  if (newQuestionsChartRef.value) chartResizeObserver.observe(newQuestionsChartRef.value)
  if (practicesChartRef.value) chartResizeObserver.observe(practicesChartRef.value)
}

async function renderCharts() {
  const value = report.value
  const version = ++chartRenderVersion
  disposeCharts()
  chartError.value = ''

  if (!value || !hasReportData.value || (value.dailyNewQuestions.length === 0 && value.dailyPractices.length === 0)) {
    chartsLoading.value = false
    return
  }

  chartsLoading.value = true
  try {
    const engine = await loadChartEngine()
    await nextTick()
    if (unmounted || version !== chartRenderVersion) return

    const inkSoft = chartColor('--ink-soft', '#52616d')
    const line = chartColor('--line', 'rgba(37, 78, 102, 0.16)')
    const navy = chartColor('--navy', '#18344a')
    const cinnabar = chartColor('--cinnabar', '#b74332')
    const jade = chartColor('--jade', '#168172')

    if (value.dailyNewQuestions.length > 0 && newQuestionsChartRef.value) {
      newQuestionsChart = engine.init(newQuestionsChartRef.value)
      newQuestionsChart.setOption({
        animationDuration: 450,
        tooltip: { trigger: 'axis' },
        grid: { left: 36, right: 12, top: 18, bottom: 30, containLabel: true },
        xAxis: {
          type: 'category',
          data: value.dailyNewQuestions.map((item) => formatDay(item.date)),
          axisLine: { lineStyle: { color: line } },
          axisLabel: { color: inkSoft, fontSize: 11 },
          axisTick: { show: false },
        },
        yAxis: {
          type: 'value',
          minInterval: 1,
          axisLabel: { color: inkSoft, fontSize: 11 },
          splitLine: { lineStyle: { color: line, type: 'dashed' } },
        },
        series: [{
          type: 'bar',
          name: '新增错题',
          data: value.dailyNewQuestions.map((item) => item.count),
          barMaxWidth: 26,
          itemStyle: { color: cinnabar, borderRadius: [7, 7, 2, 2] },
          emphasis: { itemStyle: { color: navy } },
        }],
      })
    }

    if (value.dailyPractices.length > 0 && practicesChartRef.value) {
      practicesChart = engine.init(practicesChartRef.value)
      practicesChart.setOption({
        animationDuration: 450,
        tooltip: { trigger: 'axis' },
        grid: { left: 36, right: 12, top: 18, bottom: 30, containLabel: true },
        xAxis: {
          type: 'category',
          boundaryGap: false,
          data: value.dailyPractices.map((item) => formatDay(item.date)),
          axisLine: { lineStyle: { color: line } },
          axisLabel: { color: inkSoft, fontSize: 11 },
          axisTick: { show: false },
        },
        yAxis: {
          type: 'value',
          minInterval: 1,
          axisLabel: { color: inkSoft, fontSize: 11 },
          splitLine: { lineStyle: { color: line, type: 'dashed' } },
        },
        series: [{
          type: 'line',
          name: '练习量',
          data: value.dailyPractices.map((item) => item.count),
          smooth: 0.35,
          symbol: 'circle',
          symbolSize: 7,
          lineStyle: { width: 3, color: jade },
          itemStyle: { color: jade, borderColor: '#fffdf8', borderWidth: 2 },
          areaStyle: { color: 'rgba(22, 129, 114, 0.13)' },
        }],
      })
    }

    observeChartSizes()
  } catch (error) {
    if (version === chartRenderVersion) {
      chartError.value = toApiError(error, '趋势图绘制失败').message
      disposeCharts()
    }
  } finally {
    if (version === chartRenderVersion) chartsLoading.value = false
  }
}

async function load() {
  loading.value = true
  loadError.value = ''
  generateError.value = ''
  let loaded = false
  try {
    report.value = await reportApi.weekly()
    loaded = true
  } catch (error) {
    report.value = null
    loadError.value = toApiError(error, '学情报告加载失败').message
  } finally {
    loading.value = false
  }
  if (loaded) await renderCharts()
}

async function generate() {
  generating.value = true
  generateError.value = ''
  try {
    report.value = await reportApi.generate()
    await renderCharts()
    ElMessage.success('本周报告已生成，消息中心可查看通知')
  } catch (error) {
    generateError.value = toApiError(error, '本周报告生成失败').message
  } finally {
    generating.value = false
  }
}

onMounted(load)

onBeforeUnmount(() => {
  unmounted = true
  chartRenderVersion += 1
  disposeCharts()
})
</script>

<template>
  <div class="report-page">
    <PageHeader eyebrow="每周复盘" title="学情报告" :description="pageDescription">
      <div class="week-stamp" aria-label="当前统计周期">{{ weekLabel }}</div>
      <template #actions>
        <el-button
          type="primary"
          plain
          :icon="Refresh"
          :loading="generating"
          :disabled="loading"
          @click="generate"
        >
          生成本周报告
        </el-button>
      </template>
    </PageHeader>

    <PaperPanel v-if="isTeacher" variant="annotation" class="scope-note" role="note">
      <strong>教师数据范围</strong>
      <p>仅展示全站聚合学习数据。当前后端没有班级或课程绑定，因此本页不提供班级选择，也不表示班级学情。</p>
    </PaperPanel>

    <div v-if="generateError" class="inline-alert" role="alert">
      <span>{{ generateError }}</span>
      <button type="button" :disabled="generating" @click="generate">重新生成</button>
    </div>

    <PaperPanel v-if="loading" class="state-panel">
      <AsyncState status="loading" title="正在汇总本周学习记录" description="错题、复习与练习数据正在装订成一页报告。" />
    </PaperPanel>

    <PaperPanel v-else-if="loadError" class="state-panel">
      <AsyncState
        status="error"
        title="学情报告暂时没有加载出来"
        :description="loadError"
        retry-label="重新加载"
        @retry="load"
      />
    </PaperPanel>

    <PaperPanel v-else-if="!hasReportData" class="state-panel" variant="lined">
      <AsyncState
        status="empty"
        title="本周还没有形成学习记录"
        description="录入错题、完成复习或提交练习后，这里会生成可复盘的周度证据。"
      >
        <template #action>
          <el-button type="primary" :loading="generating" @click="generate">生成本周报告</el-button>
        </template>
      </AsyncState>
    </PaperPanel>

    <template v-else-if="report">
      <section class="stats-grid" aria-label="本周关键指标">
        <PaperPanel as="article" class="stat-card is-cinnabar">
          <span class="stat-index" aria-hidden="true">01</span>
          <span class="stat-label">本周新增错题</span>
          <strong class="stat-value num">{{ report.newQuestionCount }}<small>道</small></strong>
          <p>本周新进入错题闭环的题目</p>
        </PaperPanel>

        <PaperPanel as="article" class="stat-card">
          <span class="stat-index" aria-hidden="true">02</span>
          <span class="stat-label">错题累计</span>
          <strong class="stat-value num">{{ report.totalQuestionCount }}<small>道</small></strong>
          <p>当前报告范围内的错题总量</p>
        </PaperPanel>

        <PaperPanel as="article" class="stat-card is-jade">
          <span class="stat-index" aria-hidden="true">03</span>
          <span class="stat-label">复习完成</span>
          <strong class="stat-value num">{{ report.reviewFinishedCount }}<small>/ {{ report.reviewTotalCount }}</small></strong>
          <MasteryIndicator :value="reviewRate" label="复习完成率" compact />
        </PaperPanel>

        <PaperPanel as="article" class="stat-card is-amber">
          <span class="stat-index" aria-hidden="true">04</span>
          <span class="stat-label">平均掌握度</span>
          <strong class="stat-value num">{{ masteryAverage }}<small>%</small></strong>
          <MasteryIndicator :value="masteryAverage" label="平均掌握度" compact :show-label="false" />
        </PaperPanel>
      </section>

      <section class="insight-grid" aria-label="知识点掌握情况">
        <PaperPanel class="knowledge-panel" variant="lined">
          <div class="panel-heading">
            <div>
              <span class="panel-kicker">掌握证据</span>
              <h2>知识点掌握度</h2>
            </div>
            <span class="panel-count num">{{ report.knowledgeMastery.length }} 个知识点</span>
          </div>

          <AsyncState
            v-if="report.knowledgeMastery.length === 0"
            status="empty"
            compact
            title="暂无知识点掌握数据"
            description="完成带知识点归类的错题练习后再查看。"
          />
          <ol v-else class="knowledge-list">
            <li v-for="(item, index) in report.knowledgeMastery" :key="item.knowledgePointId">
              <span class="knowledge-order num" aria-hidden="true">{{ String(index + 1).padStart(2, '0') }}</span>
              <div class="knowledge-copy">
                <div class="knowledge-name-row">
                  <strong>{{ item.name }}</strong>
                  <span>{{ item.questionCount }} 道相关错题</span>
                </div>
                <MasteryIndicator :value="item.mastery" :label="`${item.name}掌握度`" />
              </div>
            </li>
          </ol>
        </PaperPanel>

        <PaperPanel class="weak-panel" variant="annotation">
          <div class="panel-heading compact-heading">
            <div>
              <span class="panel-kicker">优先校正</span>
              <h2>薄弱知识点</h2>
            </div>
          </div>
          <p class="weak-intro">优先从低掌握度知识点开始复习，避免被错题总量带偏。</p>
          <AsyncState
            v-if="weakPoints.length === 0"
            status="empty"
            compact
            title="暂未识别薄弱点"
            description="当前数据不足，继续完成练习后再判断。"
          />
          <ol v-else class="weak-list">
            <li v-for="(item, index) in weakPoints" :key="item.knowledgePointId">
              <span class="weak-rank num">{{ index + 1 }}</span>
              <div>
                <strong>{{ item.name }}</strong>
                <span>{{ item.questionCount }} 道错题</span>
              </div>
              <span class="weak-score num">{{ normalizePercent(item.mastery) }}%</span>
            </li>
          </ol>
        </PaperPanel>
      </section>

      <div v-if="chartError" class="chart-alert" role="alert">
        <span>趋势图暂时没有绘制出来：{{ chartError }}。下方数据表仍可正常查看。</span>
        <button type="button" @click="renderCharts">重绘图表</button>
      </div>

      <section class="trend-grid" aria-label="本周学习趋势">
        <PaperPanel class="trend-panel">
          <div class="panel-heading compact-heading">
            <div>
              <span class="panel-kicker">录入节奏</span>
              <h2>每日新增错题</h2>
            </div>
          </div>

          <AsyncState
            v-if="report.dailyNewQuestions.length === 0"
            status="empty"
            compact
            title="暂无每日错题数据"
            description="本周录入错题后将显示趋势。"
          />
          <template v-else>
            <div class="chart-stage" :aria-busy="chartsLoading">
              <div v-if="chartsLoading" class="chart-loading" role="status">正在绘制趋势…</div>
              <div ref="newQuestionsChartRef" class="chart-canvas" aria-hidden="true" />
            </div>
            <p class="chart-summary">{{ questionTrendSummary }}</p>
            <details class="data-details">
              <summary>查看每日错题数据表</summary>
              <div class="table-scroll">
                <table>
                  <caption class="sr-only">本周每日新增错题数量</caption>
                  <thead><tr><th scope="col">日期</th><th scope="col">新增错题</th></tr></thead>
                  <tbody>
                    <tr v-for="item in report.dailyNewQuestions" :key="item.date">
                      <td>{{ item.date }}</td><td class="num">{{ item.count }} 道</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </details>
          </template>
        </PaperPanel>

        <PaperPanel class="trend-panel">
          <div class="panel-heading compact-heading">
            <div>
              <span class="panel-kicker">练习反馈</span>
              <h2>每日练习量</h2>
            </div>
          </div>

          <AsyncState
            v-if="report.dailyPractices.length === 0"
            status="empty"
            compact
            title="暂无每日练习数据"
            description="提交错题或变式题练习后将显示趋势。"
          />
          <template v-else>
            <div class="chart-stage" :aria-busy="chartsLoading">
              <div v-if="chartsLoading" class="chart-loading" role="status">正在绘制趋势…</div>
              <div ref="practicesChartRef" class="chart-canvas" aria-hidden="true" />
            </div>
            <p class="chart-summary">{{ practiceTrendSummary }}</p>
            <details class="data-details">
              <summary>查看每日练习数据表</summary>
              <div class="table-scroll">
                <table>
                  <caption class="sr-only">本周每日练习数量</caption>
                  <thead><tr><th scope="col">日期</th><th scope="col">练习次数</th></tr></thead>
                  <tbody>
                    <tr v-for="item in report.dailyPractices" :key="item.date">
                      <td>{{ item.date }}</td><td class="num">{{ item.count }} 次</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </details>
          </template>
        </PaperPanel>
      </section>
    </template>
  </div>
</template>

<style scoped>
.report-page {
  width: 100%;
}

.week-stamp {
  display: inline-flex;
  align-items: center;
  min-height: 30px;
  margin-top: 13px;
  padding: 5px 11px;
  border: 1px solid var(--line);
  border-radius: 4px 12px 12px 12px;
  background: rgba(255, 253, 248, 0.72);
  color: var(--ink-soft);
  font-family: var(--font-mono);
  font-size: 11px;
}

.scope-note {
  max-width: 760px;
  margin: -5px 0 24px;
}

.scope-note strong {
  color: var(--cinnabar-dark);
  font-family: var(--font-serif);
  font-size: 15px;
}

.scope-note p {
  margin: 6px 0 0;
  color: var(--ink-soft);
  font-size: 12px;
  line-height: 1.75;
}

.state-panel {
  min-height: 360px;
}

.inline-alert,
.chart-alert {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 18px;
  margin-bottom: 18px;
  padding: 12px 15px;
  border: 1px solid rgba(183, 67, 50, 0.25);
  border-radius: 10px;
  background: var(--cinnabar-pale);
  color: var(--cinnabar-dark);
  font-size: 12px;
  line-height: 1.6;
}

.inline-alert button,
.chart-alert button,
.data-details summary {
  border: 0;
  background: transparent;
  color: inherit;
  cursor: pointer;
  font-weight: 800;
}

.inline-alert button,
.chart-alert button {
  flex: 0 0 auto;
  text-decoration: underline;
  text-underline-offset: 3px;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 14px;
  margin-bottom: 18px;
}

.stat-card {
  min-height: 184px;
}

.stat-card::after {
  position: absolute;
  right: -26px;
  bottom: -32px;
  width: 100px;
  height: 100px;
  border: 18px solid rgba(24, 52, 74, 0.04);
  border-radius: 50%;
  content: '';
}

.stat-card.is-cinnabar::after {
  border-color: rgba(183, 67, 50, 0.07);
}

.stat-card.is-jade::after {
  border-color: rgba(22, 129, 114, 0.07);
}

.stat-card.is-amber::after {
  border-color: rgba(184, 119, 35, 0.08);
}

.stat-index {
  position: absolute;
  top: 18px;
  right: 20px;
  color: var(--line-strong);
  font-size: 11px;
}

.stat-label {
  display: block;
  color: var(--ink-soft);
  font-size: 11px;
  font-weight: 800;
  letter-spacing: 0.08em;
}

.stat-value {
  position: relative;
  z-index: 1;
  display: block;
  margin: 13px 0 10px;
  color: var(--navy);
  font-size: clamp(29px, 3vw, 42px);
  line-height: 1;
}

.is-cinnabar .stat-value {
  color: var(--cinnabar-dark);
}

.is-jade .stat-value {
  color: var(--jade-dark);
}

.is-amber .stat-value {
  color: var(--amber);
}

.stat-value small {
  margin-left: 5px;
  font-family: var(--font-body);
  font-size: 12px;
  font-weight: 700;
}

.stat-card > p {
  position: relative;
  z-index: 1;
  margin: 0;
  color: var(--ink-faint);
  font-size: 11px;
  line-height: 1.6;
}

.stat-card :deep(.mastery-indicator) {
  position: relative;
  z-index: 1;
}

.insight-grid {
  display: grid;
  grid-template-columns: minmax(0, 1.55fr) minmax(280px, 0.75fr);
  gap: 18px;
  margin-bottom: 18px;
}

.panel-heading {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 18px;
  margin-bottom: 22px;
}

.compact-heading {
  margin-bottom: 12px;
}

.panel-kicker {
  display: block;
  margin-bottom: 5px;
  color: var(--cinnabar-dark);
  font-size: 10px;
  font-weight: 800;
  letter-spacing: 0.14em;
}

.panel-heading h2 {
  margin: 0;
  color: var(--navy);
  font-family: var(--font-serif);
  font-size: 20px;
}

.panel-count {
  padding-top: 5px;
  color: var(--ink-faint);
  font-size: 11px;
}

.knowledge-list,
.weak-list {
  padding: 0;
  margin: 0;
  list-style: none;
}

.knowledge-list {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px 22px;
}

.knowledge-list li {
  display: grid;
  grid-template-columns: 30px minmax(0, 1fr);
  gap: 10px;
  padding: 12px 0;
  border-bottom: 1px solid rgba(37, 78, 102, 0.11);
}

.knowledge-order {
  color: var(--cinnabar);
  font-size: 11px;
  font-weight: 800;
}

.knowledge-copy {
  min-width: 0;
}

.knowledge-name-row {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 9px;
}

.knowledge-name-row strong {
  overflow: hidden;
  color: var(--navy);
  font-size: 13px;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.knowledge-name-row span {
  flex: 0 0 auto;
  color: var(--ink-faint);
  font-size: 10px;
}

.weak-panel {
  align-self: start;
}

.weak-intro {
  margin: 0 0 14px;
  color: var(--ink-soft);
  font-size: 11px;
  line-height: 1.7;
}

.weak-list li {
  display: grid;
  grid-template-columns: 26px minmax(0, 1fr) auto;
  align-items: center;
  gap: 9px;
  padding: 11px 0;
  border-top: 1px dashed rgba(183, 67, 50, 0.22);
}

.weak-rank {
  display: grid;
  width: 24px;
  height: 24px;
  place-items: center;
  border: 1px solid rgba(183, 67, 50, 0.25);
  border-radius: 50%;
  color: var(--cinnabar-dark);
  font-size: 10px;
  font-weight: 800;
}

.weak-list strong,
.weak-list span {
  display: block;
}

.weak-list strong {
  color: var(--navy);
  font-size: 12px;
}

.weak-list div span {
  margin-top: 3px;
  color: var(--ink-faint);
  font-size: 10px;
}

.weak-score {
  color: var(--cinnabar-dark);
  font-size: 12px;
  font-weight: 800;
}

.trend-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 18px;
}

.trend-panel {
  min-width: 0;
}

.chart-stage {
  position: relative;
  min-height: 260px;
}

.chart-canvas {
  width: 100%;
  height: 260px;
}

.chart-loading {
  position: absolute;
  z-index: 2;
  inset: 0;
  display: grid;
  place-items: center;
  border-radius: 12px;
  background: rgba(255, 253, 248, 0.82);
  color: var(--jade-dark);
  font-size: 12px;
  font-weight: 700;
  backdrop-filter: blur(2px);
}

.chart-summary {
  margin: 8px 0 0;
  color: var(--ink-soft);
  font-size: 11px;
  line-height: 1.7;
}

.data-details {
  margin-top: 12px;
  border-top: 1px solid var(--line);
  color: var(--ink-soft);
}

.data-details summary {
  padding: 12px 0 2px;
  color: var(--navy);
  font-size: 11px;
  list-style-position: inside;
}

.table-scroll {
  overflow-x: auto;
  margin-top: 10px;
}

table {
  width: 100%;
  border-collapse: collapse;
  font-size: 11px;
}

th,
td {
  padding: 9px 10px;
  border-bottom: 1px solid rgba(37, 78, 102, 0.1);
  text-align: left;
}

th {
  background: rgba(238, 227, 211, 0.52);
  color: var(--navy);
  font-weight: 800;
}

td:last-child,
th:last-child {
  text-align: right;
}

@media (max-width: 1180px) {
  .stats-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .insight-grid {
    grid-template-columns: 1fr;
  }

  .weak-panel {
    transform: none;
  }

  .weak-list {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    column-gap: 20px;
  }
}

@media (max-width: 900px) {
  .knowledge-list,
  .trend-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 620px) {
  .scope-note {
    margin-top: 0;
  }

  .inline-alert,
  .chart-alert {
    align-items: flex-start;
    flex-direction: column;
    gap: 8px;
  }

  .stats-grid {
    grid-template-columns: 1fr;
  }

  .stat-card {
    min-height: 158px;
  }

  .weak-list {
    grid-template-columns: 1fr;
  }

  .panel-heading {
    gap: 10px;
  }

  .panel-heading h2 {
    font-size: 18px;
  }

  .knowledge-name-row {
    align-items: flex-start;
    flex-direction: column;
    gap: 4px;
  }

  .knowledge-name-row strong {
    white-space: normal;
  }

  .chart-stage,
  .chart-canvas {
    height: 230px;
    min-height: 230px;
  }
}
</style>
