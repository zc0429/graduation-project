<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ArrowRight, Bell, Reading } from '@element-plus/icons-vue'
import { announcementApi, messageApi, reviewPlanApi, reportApi, type Announcement, type ReviewPlanItem } from '@/api'
import { useUserStore } from '@/store/user'

const router = useRouter()
const store = useUserStore()

const todayPlans = ref<ReviewPlanItem[]>([])
const announcements = ref<Announcement[]>([])
const unread = ref(0)
const masteryAvg = ref(0)
const totalQuestions = ref(0)
const loading = ref(true)

const subjectNameMap: Record<number, string> = { 1: '数学', 2: '物理', 3: '英语' }

onMounted(async () => {
  try {
    const tasks: Promise<unknown>[] = [
      announcementApi.list().then((d) => (announcements.value = d.slice(0, 5))),
      messageApi.unreadCount().then((d) => (unread.value = d)),
    ]
    if (store.role === 'student') {
      tasks.push(reviewPlanApi.today().then((d) => (todayPlans.value = d)))
      tasks.push(
        reportApi.weekly().then((d) => {
          masteryAvg.value = d.masteryAvg
          totalQuestions.value = d.totalQuestionCount
        }),
      )
    }
    await Promise.allSettled(tasks)
  } finally {
    loading.value = false
  }
})

function masteryClass(m?: number) {
  if (m == null) return ''
  if (m < 40) return 'mastery-low'
  if (m < 70) return 'mastery-mid'
  return 'mastery-high'
}
</script>

<template>
  <div v-loading="loading">
    <div class="welcome paper-card">
      <div>
        <h2 class="page-title">{{ store.nickname }}，欢迎回来</h2>
        <p class="page-subtitle" style="margin: 0">
          <template v-if="store.role === 'student'">今天也要按计划复习错题，坚持闭环：录入 → 解析 → 推荐 → 复习 → 反馈。</template>
          <template v-else-if="store.role === 'teacher'">在学情报告页查看各科目错题分布与掌握度概况。</template>
          <template v-else>在左侧菜单维护用户、科目、知识点与公告。</template>
        </p>
      </div>
      <el-button v-if="store.role === 'student'" type="primary" @click="router.push('/question/create')">
        录入错题
      </el-button>
    </div>

    <el-row v-if="store.role === 'student'" :gutter="16" class="stat-row">
      <el-col :span="8">
        <div class="paper-card hoverable stat-card" @click="router.push('/review')">
          <div class="stat-label">今日待复习</div>
          <div class="stat-num">{{ todayPlans.length }}<span class="stat-unit">道</span></div>
        </div>
      </el-col>
      <el-col :span="8">
        <div class="paper-card hoverable stat-card" @click="router.push('/question/list')">
          <div class="stat-label">错题总数</div>
          <div class="stat-num">{{ totalQuestions }}<span class="stat-unit">道</span></div>
        </div>
      </el-col>
      <el-col :span="8">
        <div class="paper-card hoverable stat-card" @click="router.push('/report')">
          <div class="stat-label">平均掌握度</div>
          <div class="stat-num" :class="masteryClass(masteryAvg)">{{ masteryAvg }}<span class="stat-unit">%</span></div>
        </div>
      </el-col>
    </el-row>

    <el-row :gutter="16">
      <el-col :span="store.role === 'student' ? 14 : 24">
        <div v-if="store.role === 'student'" class="paper-card">
          <div class="section-head">
            <el-icon color="#0f766e"><Reading /></el-icon>
            <span class="section-title">今日复习任务</span>
            <el-link type="primary" :underline="false" @click="router.push('/review')">
              全部<el-icon><ArrowRight /></el-icon>
            </el-link>
          </div>
          <el-empty v-if="todayPlans.length === 0" description="今日暂无到期复习任务" :image-size="72" />
          <div v-for="p in todayPlans.slice(0, 4)" :key="p.id" class="plan-item" @click="router.push('/review')">
            <el-tag size="small" effect="plain">{{ subjectNameMap[p.subjectId || 0] || '题目' }}</el-tag>
            <span class="plan-stem">{{ p.stemSummary }}</span>
            <span class="plan-stage num">第 {{ p.reviewStage }} 轮</span>
          </div>
        </div>
      </el-col>
      <el-col :span="store.role === 'student' ? 10 : 24">
        <div class="paper-card">
          <div class="section-head">
            <el-icon color="#d97706"><Bell /></el-icon>
            <span class="section-title">最新公告</span>
            <el-link type="primary" :underline="false" @click="router.push('/announcement')">
              全部<el-icon><ArrowRight /></el-icon>
            </el-link>
          </div>
          <el-empty v-if="announcements.length === 0" description="暂无公告" :image-size="72" />
          <div v-for="a in announcements" :key="a.id" class="ann-item" @click="router.push('/announcement')">
            <span class="ann-title">{{ a.title }}</span>
            <span class="ann-time num">{{ a.createTime.slice(0, 10) }}</span>
          </div>
        </div>
      </el-col>
    </el-row>
  </div>
</template>

<style scoped>
.welcome {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
}

.stat-row {
  margin-bottom: 16px;
}

.stat-card {
  cursor: pointer;
  text-align: center;
}

.stat-label {
  font-size: 13px;
  color: var(--wb-ink-secondary);
  margin-bottom: 6px;
}

.stat-num {
  font-size: 30px;
  font-weight: 700;
  color: var(--wb-primary);
}

.stat-unit {
  font-size: 13px;
  font-weight: 400;
  color: var(--wb-ink-secondary);
  margin-left: 4px;
}

.section-head {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 14px;
}

.section-title {
  font-size: 15px;
  font-weight: 600;
  flex: 1;
}

.plan-item,
.ann-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 8px;
  border-radius: 8px;
  cursor: pointer;
  transition: background 0.15s ease;
}

.plan-item:hover,
.ann-item:hover {
  background: var(--el-color-primary-light-9);
}

.plan-stem,
.ann-title {
  flex: 1;
  font-size: 13px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.plan-stage,
.ann-time {
  font-size: 12px;
  color: var(--wb-ink-secondary);
  flex-shrink: 0;
}
</style>
