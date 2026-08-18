<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { MagicStick, Refresh } from '@element-plus/icons-vue'
import {
  aiApi,
  kpApi,
  practiceApi,
  questionApi,
  recommendApi,
  subjectApi,
  variantApi,
  type AiAnalysis,
  type KpNode,
  type Question,
  type Subject,
  type VariantQuestion,
} from '@/api'

const route = useRoute()
const router = useRouter()
const questionId = Number(route.params.id)

const question = ref<Question>()
const analysis = ref<AiAnalysis | null>(null)
const similarQuestions = ref<Question[]>([])
const variants = ref<VariantQuestion[]>([])
const subjects = ref<Subject[]>([])
const allKpTree = ref<KpNode[]>([])
const analyzing = ref(false)
const generating = ref(false)
const loadingSimilar = ref(false)

let pollTimer: ReturnType<typeof setInterval> | undefined

/* 作答对话框 */
const practiceVisible = ref(false)
const practiceForm = ref({ target: {} as { questionId?: number; variantId?: number }, userAnswer: '', isCorrect: 1, duration: undefined as number | undefined })
const practiceTitle = ref('')

const analysisStatus = computed(() => analysis.value?.status)

function subjectName(id?: number) {
  return subjects.value.find((s) => s.id === id)?.name || '-'
}

function kpName(id?: number) {
  if (!id) return '未归类'
  for (const root of allKpTree.value) {
    if (root.id === id) return root.name
    for (const c of root.children) if (c.id === id) return c.name
  }
  return '未归类'
}

function referenceIds(): number[] {
  try {
    return JSON.parse(analysis.value?.referenceIds || '[]')
  } catch {
    return []
  }
}

async function loadAll() {
  const [q, a] = await Promise.all([
    questionApi.detail(questionId),
    aiApi.analysis(questionId).catch(() => null),
  ])
  question.value = q
  analysis.value = a
  if (a?.status === 0) startPolling()
  loadSimilar()
  loadVariants()
}

async function loadSimilar() {
  loadingSimilar.value = true
  try {
    similarQuestions.value = await recommendApi.similar(questionId)
  } finally {
    loadingSimilar.value = false
  }
}

async function loadVariants() {
  variants.value = await variantApi.list(questionId)
}

function startPolling() {
  stopPolling()
  analyzing.value = true
  pollTimer = setInterval(async () => {
    const a = await aiApi.analysis(questionId)
    analysis.value = a
    if (a && a.status !== 0) {
      stopPolling()
      if (a.status === 1) {
        ElMessage.success('AI 解析完成')
        question.value = await questionApi.detail(questionId)
        loadSimilar()
      } else {
        ElMessage.error('解析失败，可重新触发')
      }
    }
  }, 2000)
}

function stopPolling() {
  analyzing.value = false
  if (pollTimer) clearInterval(pollTimer)
  pollTimer = undefined
}

async function triggerAnalyze() {
  await aiApi.analyze(questionId)
  analysis.value = { ...(analysis.value || {}), status: 0 } as AiAnalysis
  startPolling()
}

async function generateVariants() {
  generating.value = true
  try {
    const list = await variantApi.generate(questionId)
    ElMessage.success(`已生成 ${list.length} 道变式题`)
    await loadVariants()
  } finally {
    generating.value = false
  }
}

async function handleDelete() {
  await ElMessageBox.confirm('删除后将级联清理解析、变式题与复习计划，确认删除？', '删除错题', { type: 'warning' })
  await questionApi.remove(questionId)
  ElMessage.success('已删除')
  router.push('/question/list')
}

function openPractice(target: { questionId?: number; variantId?: number }, title: string) {
  practiceForm.value = { target, userAnswer: '', isCorrect: 1, duration: undefined }
  practiceTitle.value = title
  practiceVisible.value = true
}

async function submitPractice() {
  await practiceApi.submit({
    ...practiceForm.value.target,
    userAnswer: practiceForm.value.userAnswer || undefined,
    isCorrect: practiceForm.value.isCorrect,
    duration: practiceForm.value.duration,
  })
  ElMessage.success('作答已记录，掌握度已更新')
  practiceVisible.value = false
  question.value = await questionApi.detail(questionId)
}

onMounted(async () => {
  subjects.value = await subjectApi.list()
  allKpTree.value = await kpApi.tree()
  await loadAll()
})

onBeforeUnmount(stopPolling)
</script>

<template>
  <div v-if="question">
    <div class="head-row">
      <div>
        <h2 class="page-title">错题详情</h2>
        <p class="page-subtitle">
          <el-tag size="small">{{ subjectName(question.subjectId) }}</el-tag>
          <el-tag size="small" type="success" effect="plain" style="margin-left: 6px">
            {{ kpName(question.knowledgePointId) }}
          </el-tag>
          <span class="num meta-text">掌握度 {{ question.mastery }} · 难度 {{ question.difficulty ? '★'.repeat(question.difficulty) : '待评估' }}</span>
        </p>
      </div>
      <div>
        <el-button @click="openPractice({ questionId: question.id }, '重做错题')">重做本题</el-button>
        <el-button type="danger" plain @click="handleDelete">删除</el-button>
      </div>
    </div>

    <div class="paper-card">
      <div class="block-title">题目</div>
      <div class="stem">{{ question.stem }}</div>
      <el-image v-if="question.imageUrl" :src="question.imageUrl" fit="contain" class="q-image" :preview-src-list="[question.imageUrl]" />
      <el-divider />
      <div class="block-title">答案</div>
      <div class="answer">{{ question.answer || '未填写' }}</div>
      <div class="meta-text" style="margin-top: 10px">来源：{{ question.source || '未标注' }} · 录入于 {{ question.createTime }}</div>
    </div>

    <div class="paper-card">
      <div class="block-head">
        <span class="block-title">AI 解析</span>
        <el-button
          v-if="analysisStatus !== 0"
          size="small"
          type="primary"
          plain
          :icon="Refresh"
          @click="triggerAnalyze"
        >
          {{ analysisStatus === 1 ? '重新解析' : '触发解析' }}
        </el-button>
      </div>
      <div v-if="analysisStatus === 0 || analyzing" class="analyzing">
        <el-icon class="is-loading" color="#0f766e"><MagicStick /></el-icon>
        AI 正在解析中，请稍候（通常 2 秒内完成）…
      </div>
      <template v-else-if="analysis && analysis.status === 1">
        <el-descriptions :column="2" border size="small" class="analysis-desc">
          <el-descriptions-item label="归类知识点">{{ kpName(analysis.knowledgePointId) }}</el-descriptions-item>
          <el-descriptions-item label="分析模型">
            <el-tag size="small" effect="plain" type="warning">{{ analysis.llmModel }}</el-tag>
          </el-descriptions-item>
        </el-descriptions>
        <div class="sub-title">错因分析</div>
        <p class="block-text">{{ analysis.errorCause }}</p>
        <div class="sub-title">解析内容</div>
        <p class="block-text" style="white-space: pre-line">{{ analysis.analysis }}</p>
        <div v-if="referenceIds().length > 0" class="ref-tip">
          本解析参考了本地题库中 {{ referenceIds().length }} 道相似题（ID：{{ referenceIds().join('、') }}）
        </div>
      </template>
      <el-result v-else-if="analysis && analysis.status === 2" icon="error" title="解析失败" sub-title="可点击右上角按钮重新触发解析" />
      <el-empty v-else description="尚未解析，点击右上角「触发解析」" :image-size="80" />
    </div>

    <div class="paper-card" v-loading="loadingSimilar">
      <div class="block-title">相似题推荐（同知识点 · 相近难度 Top 5）</div>
      <el-empty v-if="similarQuestions.length === 0" description="暂无相似题" :image-size="72" />
      <div v-for="sq in similarQuestions" :key="sq.id" class="similar-item" @click="router.push(`/question/${sq.id}`)">
        <span class="similar-stem">{{ sq.stem }}</span>
        <span class="num meta-text">难度 {{ sq.difficulty ? '★'.repeat(sq.difficulty) : '-' }}</span>
      </div>
    </div>

    <div class="paper-card">
      <div class="block-head">
        <span class="block-title">变式题（{{ variants.length }}）</span>
        <el-button size="small" type="primary" :loading="generating" :icon="MagicStick" @click="generateVariants">
          生成变式题
        </el-button>
      </div>
      <el-empty v-if="variants.length === 0" description="暂无变式题，点击右上角生成" :image-size="72" />
      <el-collapse v-else accordion>
        <el-collapse-item v-for="(v, i) in variants" :key="v.id" :name="v.id">
          <template #title>
            <span class="variant-title">变式 {{ i + 1 }} · 难度 {{ v.difficulty ? '★'.repeat(v.difficulty) : '-' }}</span>
          </template>
          <p class="block-text">{{ v.stem }}</p>
          <p class="block-text answer-text">答案：{{ v.answer || '未提供' }}</p>
          <el-button size="small" @click="openPractice({ variantId: v.id }, `作答变式 ${i + 1}`)">作答并记录</el-button>
        </el-collapse-item>
      </el-collapse>
    </div>

    <el-dialog v-model="practiceVisible" :title="practiceTitle" width="520px">
      <el-form label-position="top">
        <el-form-item label="我的作答">
          <el-input v-model="practiceForm.userAnswer" type="textarea" :rows="3" placeholder="填写你的答案" />
        </el-form-item>
        <el-form-item label="作答结果（自评）">
          <el-radio-group v-model="practiceForm.isCorrect">
            <el-radio :value="1">答对了</el-radio>
            <el-radio :value="0">答错了</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="用时（秒，选填）">
          <el-input-number v-model="practiceForm.duration" :min="0" :max="7200" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="practiceVisible = false">取消</el-button>
        <el-button type="primary" @click="submitPractice">提交记录</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.head-row {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
}

.paper-card {
  margin-bottom: 16px;
}

.block-title {
  font-size: 15px;
  font-weight: 600;
  margin-bottom: 10px;
}

.block-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.sub-title {
  font-size: 13px;
  font-weight: 600;
  color: var(--wb-primary);
  margin: 12px 0 6px;
}

.stem {
  font-size: 15px;
  line-height: 1.8;
}

.answer,
.block-text {
  font-size: 14px;
  line-height: 1.8;
  color: var(--wb-ink);
  margin: 0;
}

.q-image {
  max-width: 360px;
  max-height: 220px;
  margin-top: 12px;
  border: 1px solid var(--wb-border);
  border-radius: 8px;
}

.meta-text {
  font-size: 12px;
  color: var(--wb-ink-secondary);
  margin-left: 8px;
}

.analyzing {
  display: flex;
  align-items: center;
  gap: 8px;
  color: var(--wb-primary);
  font-size: 14px;
  padding: 12px 0;
}

.analysis-desc {
  margin-bottom: 6px;
}

.ref-tip {
  margin-top: 12px;
  font-size: 12px;
  color: var(--wb-accent);
  background: #fffbeb;
  border: 1px solid #fde68a;
  border-radius: 6px;
  padding: 8px 12px;
}

.similar-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  padding: 10px 8px;
  border-radius: 8px;
  cursor: pointer;
  transition: background 0.15s ease;
}

.similar-item:hover {
  background: var(--el-color-primary-light-9);
}

.similar-stem {
  font-size: 13px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.variant-title {
  font-size: 13px;
  font-weight: 600;
}

.answer-text {
  color: var(--wb-ink-secondary);
  margin: 8px 0;
}
</style>
