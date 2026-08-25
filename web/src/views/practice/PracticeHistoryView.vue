<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ArrowRight, Refresh } from '@element-plus/icons-vue'
import { practiceApi, type PageData, type PracticeRecord } from '@/api'
import AsyncState from '@/components/AsyncState.vue'
import PageHeader from '@/components/PageHeader.vue'
import PaperPanel from '@/components/PaperPanel.vue'

const router = useRouter()
const loading = ref(true)
const error = ref('')
const pageNum = ref(1)
const page = ref<PageData<PracticeRecord>>({ records: [], total: 0, current: 1, size: 10 })
let requestVersion = 0

async function load() {
  const version = ++requestVersion
  loading.value = true
  error.value = ''
  try {
    const data = await practiceApi.page({ pageNum: pageNum.value, pageSize: 10 })
    if (version === requestVersion) page.value = data
  } catch (cause) {
    if (version === requestVersion) error.value = cause instanceof Error ? cause.message : '练习历史暂时无法加载。'
  } finally {
    if (version === requestVersion) loading.value = false
  }
}

function formatDuration(seconds?: number) {
  if (!seconds) return '未记录'
  if (seconds < 60) return `${seconds} 秒`
  return `${Math.floor(seconds / 60)} 分 ${seconds % 60} 秒`
}

onMounted(load)
</script>

<template>
  <div class="practice-history-page">
    <PageHeader eyebrow="练习反馈" title="练习历史" description="这里汇总你提交过的本题与变式题自评记录；后端暂不返回对应题干，因此不会伪装为逐题完整报告。">
      <template #actions><el-button :icon="Refresh" :loading="loading" @click="load">刷新</el-button></template>
    </PageHeader>

    <PaperPanel>
      <div class="history-toolbar">
        <strong>按提交时间倒序</strong>
        <span>共 {{ page.total }} 条记录</span>
      </div>

      <AsyncState v-if="loading" status="loading" compact title="正在读取练习历史" />
      <AsyncState v-else-if="error" status="error" compact title="加载失败" :description="error" @retry="load" />
      <AsyncState v-else-if="page.records.length === 0" status="empty" compact title="还没有练习记录" description="完成一次错题或变式题自评后，记录会出现在这里。" />
      <div v-else class="history-list">
        <article v-for="record in page.records" :key="record.id" class="history-item">
          <span class="result-seal" :class="record.isCorrect ? 'correct' : 'wrong'">{{ record.isCorrect ? '对' : '错' }}</span>
          <div class="history-copy">
            <strong>{{ record.questionId ? `错题 #${record.questionId}` : `变式题 #${record.variantId}` }}</strong>
            <p>{{ record.userAnswer || '未填写作答内容' }}</p>
            <small>{{ record.createTime }} · 用时 {{ formatDuration(record.duration) }}</small>
          </div>
          <el-button v-if="record.questionId" text @click="router.push(`/question/${record.questionId}`)">查看错题<el-icon><ArrowRight /></el-icon></el-button>
        </article>
      </div>

      <el-pagination v-if="page.total > page.size" v-model:current-page="pageNum" :page-size="page.size" :total="page.total" layout="prev, pager, next" class="history-pagination" @current-change="load" />
    </PaperPanel>
  </div>
</template>

<style scoped>
.practice-history-page{display:grid;gap:20px}.history-toolbar{display:flex;align-items:center;gap:8px;margin-bottom:18px;padding-bottom:15px;border-bottom:1px solid var(--line)}.history-toolbar>strong{color:var(--navy);font-size:12px}.history-toolbar>span{margin-left:auto;color:var(--ink-faint);font-size:11px}.history-list{display:grid}.history-item{display:grid;grid-template-columns:46px minmax(0,1fr) auto;align-items:center;gap:15px;padding:17px 2px;border-bottom:1px dashed var(--line)}.history-item:last-child{border-bottom:0}.result-seal{display:grid;place-items:center;width:38px;height:38px;border:2px solid currentColor;border-radius:50%;font:800 16px var(--font-display);transform:rotate(-4deg)}.result-seal.correct{color:var(--jade)}.result-seal.wrong{color:var(--cinnabar)}.history-copy strong{color:var(--navy);font-size:13px}.history-copy p{margin:5px 0;color:var(--ink-soft);font-size:12px;line-height:1.6}.history-copy small{color:var(--ink-faint);font:9px var(--font-mono)}.history-pagination{justify-content:flex-end;margin-top:20px}
@media(max-width:600px){.history-toolbar{flex-wrap:wrap}.history-toolbar>span{width:100%;margin-left:0}.history-item{grid-template-columns:40px minmax(0,1fr)}.history-item :deep(.el-button){grid-column:2;justify-self:start}.history-copy p{display:-webkit-box;overflow:hidden;-webkit-line-clamp:2;-webkit-box-orient:vertical}}
</style>
