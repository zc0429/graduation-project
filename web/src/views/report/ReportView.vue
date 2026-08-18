<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import * as echarts from 'echarts'
import { ElMessage } from 'element-plus'
import { Refresh } from '@element-plus/icons-vue'
import { reportApi, type WeeklyReport } from '@/api'
import { useUserStore } from '@/store/user'

const store = useUserStore()
const report = ref<WeeklyReport>()
const loading = ref(false)
const generating = ref(false)

const radarRef = ref<HTMLElement>()
const barRef = ref<HTMLElement>()
const lineRef = ref<HTMLElement>()
let radarChart: echarts.ECharts | undefined
let barChart: echarts.ECharts | undefined
let lineChart: echarts.ECharts | undefined

const reviewRate = computed(() => {
  if (!report.value || report.value.reviewTotalCount === 0) return 0
  return Math.round((report.value.reviewFinishedCount / report.value.reviewTotalCount) * 100)
})

function renderCharts() {
  if (!report.value) return
  const r = report.value

  radarChart ??= echarts.init(radarRef.value!)
  radarChart.setOption({
    tooltip: {},
    radar: {
      indicator: r.knowledgeMastery.map((k) => ({ name: k.name, max: 100 })),
      radius: '62%',
      splitArea: { areaStyle: { color: ['#f0fdfa', '#ffffff'] } },
    },
    series: [
      {
        type: 'radar',
        data: [
          {
            value: r.knowledgeMastery.map((k) => k.mastery),
            name: '知识点掌握度',
            areaStyle: { color: 'rgba(15,118,110,0.25)' },
            lineStyle: { color: '#0f766e' },
            itemStyle: { color: '#0f766e' },
          },
        ],
      },
    ],
  })

  barChart ??= echarts.init(barRef.value!)
  barChart.setOption({
    tooltip: {},
    grid: { left: 40, right: 16, top: 30, bottom: 28 },
    xAxis: { type: 'category', data: r.dailyNewQuestions.map((d) => d.date.slice(5)) },
    yAxis: { type: 'value', minInterval: 1 },
    series: [
      { type: 'bar', name: '新增错题', data: r.dailyNewQuestions.map((d) => d.count), itemStyle: { color: '#0f766e', borderRadius: [4, 4, 0, 0] }, barMaxWidth: 28 },
    ],
    legend: { top: 0 },
  })

  lineChart ??= echarts.init(lineRef.value!)
  lineChart.setOption({
    tooltip: { trigger: 'axis' },
    grid: { left: 40, right: 16, top: 30, bottom: 28 },
    xAxis: { type: 'category', data: r.dailyPractices.map((d) => d.date.slice(5)), boundaryGap: false },
    yAxis: { type: 'value', minInterval: 1 },
    series: [
      {
        type: 'line',
        name: '练习量',
        data: r.dailyPractices.map((d) => d.count),
        smooth: true,
        areaStyle: { color: 'rgba(217,119,6,0.15)' },
        lineStyle: { color: '#d97706' },
        itemStyle: { color: '#d97706' },
      },
    ],
  })
}

async function load() {
  loading.value = true
  try {
    report.value = await reportApi.weekly()
    setTimeout(renderCharts)
  } finally {
    loading.value = false
  }
}

async function generate() {
  generating.value = true
  try {
    report.value = await reportApi.generate()
    ElMessage.success('周报已生成，消息中心可查看通知')
    setTimeout(renderCharts)
  } finally {
    generating.value = false
  }
}

function handleResize() {
  radarChart?.resize()
  barChart?.resize()
  lineChart?.resize()
}

onMounted(async () => {
  await load()
  window.addEventListener('resize', handleResize)
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', handleResize)
  radarChart?.dispose()
  barChart?.dispose()
  lineChart?.dispose()
})
</script>

<template>
  <div>
    <div class="head-row">
      <div>
        <h2 class="page-title">学情报告</h2>
        <p class="page-subtitle">
          本周（{{ report?.weekStart }} 起）学习数据汇总{{ store.role === 'teacher' ? '（教师视角：全科目聚合）' : '' }}。
        </p>
      </div>
      <el-button type="primary" plain :icon="Refresh" :loading="generating" @click="generate">手动生成本周周报</el-button>
    </div>

    <el-row :gutter="16" class="stat-row" v-loading="loading">
      <el-col :span="6">
        <div class="paper-card stat-card">
          <div class="stat-label">本周新增错题</div>
          <div class="stat-num">{{ report?.newQuestionCount ?? 0 }}<span class="stat-unit">道</span></div>
        </div>
      </el-col>
      <el-col :span="6">
        <div class="paper-card stat-card">
          <div class="stat-label">错题总数</div>
          <div class="stat-num">{{ report?.totalQuestionCount ?? 0 }}<span class="stat-unit">道</span></div>
        </div>
      </el-col>
      <el-col :span="6">
        <div class="paper-card stat-card">
          <div class="stat-label">复习完成率</div>
          <div class="stat-num">{{ reviewRate }}<span class="stat-unit">%</span></div>
        </div>
      </el-col>
      <el-col :span="6">
        <div class="paper-card stat-card">
          <div class="stat-label">平均掌握度</div>
          <div class="stat-num accent">{{ report?.masteryAvg ?? 0 }}<span class="stat-unit">%</span></div>
        </div>
      </el-col>
    </el-row>

    <el-row :gutter="16">
      <el-col :span="10">
        <div class="paper-card chart-card">
          <div class="chart-title">知识点掌握度雷达图</div>
          <div ref="radarRef" class="chart" />
        </div>
      </el-col>
      <el-col :span="14">
        <div class="paper-card chart-card">
          <div class="chart-title">本周每日新增错题</div>
          <div ref="barRef" class="chart" />
        </div>
      </el-col>
    </el-row>
    <el-row :gutter="16">
      <el-col :span="14">
        <div class="paper-card chart-card">
          <div class="chart-title">本周每日练习量趋势</div>
          <div ref="lineRef" class="chart" />
        </div>
      </el-col>
      <el-col :span="10">
        <div class="paper-card chart-card">
          <div class="chart-title">薄弱知识点 Top 5</div>
          <el-empty v-if="!report?.weakPoints?.length" description="暂无数据" :image-size="72" />
          <div v-for="(w, i) in report?.weakPoints" :key="w.knowledgePointId" class="weak-item">
            <span class="weak-rank num">{{ i + 1 }}</span>
            <span class="weak-name">{{ w.name }}</span>
            <el-progress
              :percentage="Math.round(w.mastery)"
              :stroke-width="8"
              :color="w.mastery < 40 ? '#dc2626' : w.mastery < 70 ? '#d97706' : '#16a34a'"
              style="flex: 1"
            />
            <span class="num weak-count">{{ w.questionCount }} 题</span>
          </div>
        </div>
      </el-col>
    </el-row>
  </div>
</template>

<style scoped>
.head-row {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
}

.stat-row {
  margin-bottom: 16px;
}

.stat-card {
  text-align: center;
}

.stat-label {
  font-size: 13px;
  color: var(--wb-ink-secondary);
  margin-bottom: 6px;
}

.stat-num {
  font-size: 28px;
  font-weight: 700;
  color: var(--wb-primary);
  font-family: 'IBM Plex Sans', 'Consolas', sans-serif;
}

.stat-num.accent {
  color: var(--wb-accent);
}

.stat-unit {
  font-size: 13px;
  font-weight: 400;
  color: var(--wb-ink-secondary);
  margin-left: 4px;
}

.chart-card {
  margin-bottom: 16px;
}

.chart-title {
  font-size: 14px;
  font-weight: 600;
  margin-bottom: 8px;
}

.chart {
  height: 280px;
}

.weak-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 0;
}

.weak-rank {
  width: 22px;
  height: 22px;
  border-radius: 6px;
  background: var(--el-color-primary-light-9);
  color: var(--wb-primary);
  font-size: 12px;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
}

.weak-name {
  width: 88px;
  font-size: 13px;
}

.weak-count {
  font-size: 12px;
  color: var(--wb-ink-secondary);
  width: 40px;
  text-align: right;
}
</style>
