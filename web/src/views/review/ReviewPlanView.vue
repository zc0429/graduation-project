<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Check, Right } from '@element-plus/icons-vue'
import { reviewPlanApi, type ReviewPlanItem } from '@/api'

const router = useRouter()
const plans = ref<ReviewPlanItem[]>([])
const loading = ref(false)

const subjectNameMap: Record<number, string> = { 1: '数学', 2: '物理', 3: '英语' }

async function load() {
  loading.value = true
  try {
    plans.value = await reviewPlanApi.today()
  } finally {
    loading.value = false
  }
}

async function finish(p: ReviewPlanItem) {
  await reviewPlanApi.finish(p.id)
  ElMessage.success(`已完成第 ${p.reviewStage} 轮复习`)
  await load()
}

function isOverdue(p: ReviewPlanItem) {
  return p.status === 2
}

function masteryClass(m?: number) {
  if (m == null) return ''
  if (m < 40) return 'mastery-low'
  if (m < 70) return 'mastery-mid'
  return 'mastery-high'
}

onMounted(load)
</script>

<template>
  <div>
    <h2 class="page-title">复习计划</h2>
    <p class="page-subtitle">依据艾宾浩斯遗忘曲线在录入后第 1/2/4/7/15 天自动生成复习任务；到期与逾期任务在此汇总。</p>
    <div class="paper-card" v-loading="loading">
      <el-empty v-if="plans.length === 0" description="暂无到期复习任务，新录入的错题将自动排入复习计划" :image-size="96" />
      <div v-for="p in plans" :key="p.id" class="plan-row">
        <div class="plan-date num" :class="{ overdue: isOverdue(p) }">
          <div class="date-day">{{ p.planDate.slice(5).replace('-', '/') }}</div>
          <div class="date-tag">{{ isOverdue(p) ? '已逾期' : '今日' }}</div>
        </div>
        <div class="plan-main">
          <div class="plan-tags">
            <el-tag size="small">{{ subjectNameMap[p.subjectId || 0] || '题目' }}</el-tag>
            <el-tag size="small" type="warning" effect="plain">第 {{ p.reviewStage }} / 5 轮</el-tag>
            <span class="num mastery" :class="masteryClass(p.mastery)">掌握度 {{ p.mastery ?? 0 }}</span>
          </div>
          <div class="plan-stem">{{ p.stemSummary }}</div>
        </div>
        <div class="plan-actions">
          <el-button size="small" :icon="Right" @click="router.push(`/question/${p.questionId}`)">去重做</el-button>
          <el-button size="small" type="primary" :icon="Check" @click="finish(p)">完成复习</el-button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.plan-row {
  display: flex;
  align-items: center;
  gap: 18px;
  padding: 14px 8px;
  border-bottom: 1px solid var(--wb-border);
}

.plan-row:last-child {
  border-bottom: none;
}

.plan-date {
  width: 64px;
  text-align: center;
  flex-shrink: 0;
}

.date-day {
  font-size: 18px;
  font-weight: 700;
  color: var(--wb-primary);
}

.date-tag {
  font-size: 11px;
  color: var(--wb-ink-secondary);
}

.plan-date.overdue .date-day {
  color: var(--wb-mastery-low);
}

.plan-main {
  flex: 1;
  min-width: 0;
}

.plan-tags {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 6px;
}

.mastery {
  font-size: 12px;
  margin-left: 4px;
}

.plan-stem {
  font-size: 13px;
  color: var(--wb-ink);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.plan-actions {
  display: flex;
  gap: 8px;
  flex-shrink: 0;
}
</style>
